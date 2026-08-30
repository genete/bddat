"""
mutaciones_arbol.py — Servicio de mutaciones ESFTT para el árbol (ADR-016, S3b-0).

Funciones puras de dominio (sin request/jsonify) para Crear / Editar / Borrar
los cuatro niveles del árbol (solicitud, fase, trámite, tarea).

Extraídas literalmente de app/routes/api_bc.py (camino B, #500). Aquel blueprint
delegaba aquí manteniendo su contrato HTTP; se retiró en #577 al quedarse sin
consumidores, y los endpoints JSON del árbol (api_expedientes.py) son desde
entonces el único caller.

Nota: `resultado` en tareas NOTIFICAR es una @property computada desde Notificacion
y no es editable por este servicio — ver hallazgos S3b-0.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from app import db
from app.models.solicitudes import Solicitud
from app.models.fases import Fase
from app.models.tramites import Tramite
from app.models.tareas import Tarea
from app.models.documentos import Documento
from app.models.tipos_solicitudes import TipoSolicitud
from app.models.documentos_tarea import DocumentoTarea
from app.models.notificaciones import Notificacion
from app.models.organismos_expediente import OrganismoExpediente, VIAS_ORGANISMO, RESULTADOS_ORGANISMO
from app.models.direccion_notificacion import DireccionNotificacion
from app.services.assembler import build, build_sujeto
from app.services import bitacora as bitacora_svc
from app.services.motor_reglas import EvaluacionResult, PERMITIDO
from app.services.motor_modo_global import evaluar_con_modo_global as _evaluar
from app.services.invariantes_esftt import (
    _check_cierre_fase, _check_completitud_cierre, check_invariante,
    diagnostico_tramite_anterior, documento_disparo_comunicacion_admision,
    documentos_consumidos_otras_tareas_cadena,
    es_documento_critico, advertir_documentos_criticos_huerfanos,
)
from app.services.vocabulario_esftt import check_orden_tarea, check_vocabulario_tramite
from app.services.requisitos import evaluar_requisitos
from app.services.rutas_esftt import mover_a_esftt, mover_a_pool
from app.services.parser_justificante_notifica import (
    parsear_justificante_notifica, parsear_justificante_notifica_zip,
)
from app.services.codigo_seguimiento import extraer_tarea_id
from app.services.extraccion_texto_documento import extraer_texto

log = logging.getLogger(__name__)

_FASES_QUE_REQUIEREN_CERT_IP_CONSULTAS = frozenset({'RESOLUCION', 'AAU_AAUS_INTEGRADA'})


@dataclass
class ResultadoMutacion:
    """Retorno unificado de todas las funciones de mutación."""
    ok: bool
    ids: list[int] = field(default_factory=list)
    bloqueo: Optional[EvaluacionResult] = None
    advertencia: Optional[dict] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _advertencia_dict(res_eval: EvaluacionResult) -> Optional[dict]:
    if res_eval and res_eval.nivel == 'ADVERTIR':
        return {
            'motivo': res_eval.motivo,
            'norma_compilada': res_eval.norma_compilada,
            'url_norma': res_eval.url_norma,
        }
    return None


def _bloquea(res: Optional[EvaluacionResult], justificacion: Optional[str]) -> bool:
    """True si `res` debe cortar la operación (#723): sin bloqueo no hay nada que
    frenar; con bloqueo, solo se deja pasar cuando es forzable Y hay justificación."""
    return res is not None and not (res.puede_escapar and justificacion)


def _registrar_advertencia(operacion, tabla, registro_id, sujeto, res_eval: EvaluacionResult) -> None:
    """Bitácora para creaciones permitidas con advertencia (#616 feedback).

    Mismo criterio que el escape (detalle con sujeto), sin justificacion: el motor
    ya lo permite, solo avisa — no hay override que justificar, pero sí queda
    auditado igual que el bypass.
    """
    bitacora_svc.registrar(
        current_user.id, operacion, tabla, registro_id,
        detalle={
            'advertencia': True,
            'motivo': res_eval.motivo,
            'norma_compilada': res_eval.norma_compilada,
            'sujeto': sujeto,
        },
    )


# ---------------------------------------------------------------------------
# Hook #657/#658 (ADR-034 §6): camino B — justificante definitivo
# ---------------------------------------------------------------------------

# Tipo de documento → canal (TIPOS_DOCUMENTOS_CATALOGO.md). Solo NOTIFICA tiene
# parser hoy (#655); el resto queda a la espera del "Registrar puesta a
# disposición"/"Registrar notificación" manual de NotificarEditor (#657/#712).
# Público: lo reutiliza api_expedientes.py (validación del desplegable/preview, #712).
MAPA_CANAL_POR_TIPO_DOC = {
    'JUSTIFICANTE_NOTIFICA': 'NOTIFICA',
    'JUSTIFICANTE_BANDEJA':  'BANDEJA',
    'JUSTIFICANTE_SIR':      'SIR',
    'JUSTIFICANTE_POSTAL':   'POSTAL',
}


def parsear_documento_notifica(doc: Documento):
    """Parsea en disco el justificante NOTIFICA ya vinculado como producido.

    None si el documento no tiene fichero local (URL externa), la extensión
    no es .pdf/.zip, o el parser no reconoce el contenido — nunca lanza
    (mismo contrato que parsear_justificante_notifica*, #655).
    """
    if '://' in (doc.url or ''):
        return None
    try:
        ruta = doc.ruta_absoluta()
    except ValueError:
        return None

    ruta_lower = ruta.lower()
    if ruta_lower.endswith('.zip'):
        resultado = parsear_justificante_notifica_zip(ruta)
    elif ruta_lower.endswith('.pdf'):
        resultado = parsear_justificante_notifica(ruta)
    else:
        return None

    return resultado if resultado.reconocido else None


def _hook_657_notificar_resultado(tarea, id_producido) -> Optional[dict]:
    """Hook #657/#658/#712: al fijar/cambiar documento_producido_id en una tarea
    NOTIFICAR, upsert de Notificacion buscando por tarea_id (nunca por
    identificador_envio, ADR-034 §6) + cotejo no bloqueante contra la remesa
    (#658) y el canal (#712) ya registrados.

    Devuelve un dict de advertencia (cotejo fallido) para que el caller lo
    propague al cliente, o None. Sin parser para el canal del documento (todo
    salvo NOTIFICA hoy) solo actualiza documento_id/canal si ya existe fila —
    sin fila previa y sin datos parseados no puede crearla (fecha_puesta_disposicion
    es NOT NULL): el usuario debe usar "Registrar puesta a disposición"/
    "Registrar notificación" a mano en NotificarEditor.
    """
    if id_producido is None or tarea.tipo_tarea.codigo != 'NOTIFICAR':
        return None

    doc = Documento.query.get(id_producido)
    tipo_codigo = doc.tipo_doc.codigo if doc.tipo_doc else None
    canal = MAPA_CANAL_POR_TIPO_DOC.get(tipo_codigo)
    if canal is None:
        return None  # tipo de documento no es un justificante de notificación reconocido

    parseo = parsear_documento_notifica(doc) if canal == 'NOTIFICA' else None

    notif = Notificacion.query.filter_by(tarea_id=tarea.id).first()

    if notif is None:
        if parseo is None or parseo.fecha_puesta_disposicion is None:
            return None
        db.session.add(Notificacion(
            tarea_id=tarea.id, documento_id=doc.id, canal=canal,
            identificador_envio=parseo.id_remesa,
            fecha_puesta_disposicion=parseo.fecha_puesta_disposicion.date(),
            resultado=parseo.resultado,
            fecha_resultado=parseo.fecha_lectura.date() if parseo.fecha_lectura else None,
        ))
        return None

    avisos = []

    # #712: el documento vinculado manda sobre el canal anotado a mano —
    # mismo criterio que el cotejo de remesa, y no depende de que haya parser
    # (el canal se deriva del tipo de documento, siempre disponible).
    if canal != notif.canal:
        avisos.append(
            f'El documento vinculado corresponde al canal «{canal}», distinto '
            f'del registrado al notificar («{notif.canal}»). Se ha actualizado '
            'el canal.'
        )
        notif.canal = canal

    if (parseo is not None and notif.identificador_envio and parseo.id_remesa
            and notif.identificador_envio != parseo.id_remesa):
        avisos.append(
            f'El justificante vinculado trae la remesa «{parseo.id_remesa}», '
            f'distinta de la registrada al notificar («{notif.identificador_envio}»). '
            'Puede haberse vinculado el justificante de otro expediente.'
        )

    notif.documento_id = doc.id
    if parseo is not None:
        notif.identificador_envio = notif.identificador_envio or parseo.id_remesa
        notif.resultado = parseo.resultado
        notif.fecha_resultado = parseo.fecha_lectura.date() if parseo.fecha_lectura else None

    return {'motivo': ' '.join(avisos)} if avisos else None


# ---------------------------------------------------------------------------
# Hook #717: consumo real del diagnóstico por el ELABORAR de REQUERIMIENTO_SUBSANACION
# ---------------------------------------------------------------------------

def _hook_717_elaborar_consumido_diagnostico(tarea, id_producido) -> Optional[dict]:
    """Hook #717: al fijar por primera vez el documento producido de un ELABORAR
    de REQUERIMIENTO_SUBSANACION, deriva el vínculo CONSUMIDO sobre el
    diagnóstico que ese escrito volcó — mismo trámite anterior que usa
    ContextoSubsanacion (`diagnostico_tramite_anterior`) — acreditado con el
    código de seguimiento embebido (#182).

    Solo se llama cuando `id_producido` es NUEVO respecto al que tenía la tarea
    (ver editar_tarea): si el técnico ya deshizo el vínculo a mano (botón ✕ de
    la Despensa, la vía de "deshacer esa vinculación" que exige ADR-033 §5) y
    vuelve a guardar sin cambiar el producido, este hook no debe reponerlo.

    Sin token propio en el documento —o con el de otra tarea— un documento
    vinculado a mano no acredita el consumo (diseño del issue): no se deriva
    nada y se devuelve una advertencia no bloqueante para que el técnico lo
    sepa. Un diagnóstico favorable tampoco es consumible (ADR-033 §5): se
    ignora en silencio, no es nada que el técnico pueda corregir.

    Cuando SÍ deriva el vínculo también devuelve aviso (mismo canal, aunque no
    sea un problema): es una mutación en la trastienda —un documento nuevo
    aparece como CONSUMIDO de la tarea sin que el técnico lo haya arrastrado
    desde la Despensa— y debe enterarse de qué se hizo y por qué, no solo
    cuando algo falla.
    """
    if id_producido is None or tarea.tipo_tarea.codigo != 'ELABORAR':
        return None
    tramite = tarea.tramite
    if not tramite or not tramite.tipo_tramite or tramite.tipo_tramite.codigo != 'REQUERIMIENTO_SUBSANACION':
        return None

    doc = Documento.query.get(id_producido)
    if extraer_tarea_id(extraer_texto(doc)) != tarea.id:
        return {
            'motivo': (
                'El documento producido no lleva el código de seguimiento de esta '
                'tarea: el vínculo con el diagnóstico que este requerimiento '
                'subsana no se ha derivado automáticamente. Si corresponde, '
                'vincúlelo a mano desde la Despensa.'
            ),
        }

    diagnostico = diagnostico_tramite_anterior(tramite)
    if diagnostico is None or diagnostico.resultado != 'desfavorable':
        return None

    ya_vinculado = any(
        v.documento_id == diagnostico.documento_id and v.rol == 'CONSUMIDO'
        for v in tarea.vinculos_documento
    )
    if ya_vinculado:
        return None

    tarea.vinculos_documento.append(
        DocumentoTarea(documento_id=diagnostico.documento_id, rol='CONSUMIDO'))
    return {
        'motivo': (
            'Vinculación automática: el código de seguimiento acredita que este '
            'escrito subsana el diagnóstico desfavorable del trámite anterior, así '
            'que se ha añadido como documento consumido de esta tarea.'
        ),
    }


# ---------------------------------------------------------------------------
# Hook #776: disparo del plazo de ELABORAR de COMUNICACION_INICIO_ADMISION
# ---------------------------------------------------------------------------

def _hook_776_elaborar_consume_disparo_admision(tarea) -> Optional[dict]:
    """Hook #776: al crear la tarea ELABORAR de COMUNICACION_INICIO_ADMISION,
    vincula automáticamente como CONSUMIDO el documento cuya fecha_administrativa
    dispara el plazo del art. 21.4 LPACAP — la solicitud si no hubo
    requerimiento de subsanación previo en la fase, o la última subsanación
    si lo hubo (`documento_disparo_comunicacion_admision`, mismo criterio de
    "trámite anterior" que #717).

    A diferencia del DIAGNOSTICO de #717 —que es una elección de qué escrito
    redactar—, qué documento vincular aquí no exige juicio del técnico: está
    determinado por la historia de la fase, así que se deriva al crear la
    tarea sin esperar a que alguien lo arrastre desde la Despensa.

    Sin documento que vincular (degradación, p.ej. la solicitud aún sin
    documento registrado) no bloquea la creación de la tarea: el plazo
    quedará SIN_PLAZO hasta que exista el documento.
    """
    if not tarea.tipo_tarea or tarea.tipo_tarea.codigo != 'ELABORAR':
        return None
    tramite = tarea.tramite
    if not tramite or not tramite.tipo_tramite or tramite.tipo_tramite.codigo != 'COMUNICACION_INICIO_ADMISION':
        return None

    doc = documento_disparo_comunicacion_admision(tramite)
    if doc is None:
        return None

    tarea.vinculos_documento.append(
        DocumentoTarea(documento_id=doc.id, rol='CONSUMIDO'))
    return {
        'motivo': (
            'Vinculación automática: se ha marcado como consumido el documento '
            'que dispara el plazo del art. 21.4 LPACAP (la solicitud, o la '
            'última subsanación si hubo requerimiento).'
        ),
    }


# ===========================================================================
# CREAR
# ===========================================================================

def crear_solicitud(expediente, tipos: list[TipoSolicitud], entidad_id: int,
                    *, justificacion: Optional[str] = None) -> ResultadoMutacion:
    """Crea una o varias solicitudes (multi-tipo). Valida motor para todos antes de persistir."""
    exp_id = expediente.id

    if not entidad_id:
        return ResultadoMutacion(ok=False, error='El expediente no tiene titular asignado.')

    # Fase 1: evaluar motor para todos los tipos; si alguno bloquea, rechazar todo.
    # Se conserva la evaluación de cada tipo (evaluaciones) para poder auditar y
    # devolver la advertencia en Fase 2 sin re-evaluar contra el objeto ya persistido.
    evaluaciones: dict[int, EvaluacionResult] = {}
    if justificacion is None:
        for tipo in tipos:
            sol_stub = Solicitud(expediente_id=exp_id, entidad_id=entidad_id,
                                 tipo_solicitud_id=tipo.id)
            sol_stub.tipo_solicitud = tipo  # stub transiente — assembler compila sin flush
            res_eval = _evaluar('CREAR', expediente, objeto=sol_stub)
            if not res_eval.permitido:
                return ResultadoMutacion(ok=False, bloqueo=res_eval)
            evaluaciones[tipo.id] = res_eval

    # Fase 2: persistir
    creadas = []
    advertencia = None
    try:
        for tipo in tipos:
            sol = Solicitud(expediente_id=exp_id, entidad_id=entidad_id,
                            tipo_solicitud_id=tipo.id)
            db.session.add(sol)
            db.session.flush()
            res_eval = evaluaciones.get(tipo.id)
            if justificacion:
                sujeto = build_sujeto(expediente, sol)
                bitacora_svc.registrar(
                    current_user.id, 'CREAR', 'solicitudes', sol.id,
                    detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
                )
            elif res_eval and res_eval.nivel == 'ADVERTIR':
                sujeto = build_sujeto(expediente, sol)
                _registrar_advertencia('CREAR', 'solicitudes', sol.id, sujeto, res_eval)
                advertencia = _advertencia_dict(res_eval)  # multi-tipo: la última advertencia gana
            creadas.append(sol)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return ResultadoMutacion(ok=False, error=str(e))

    return ResultadoMutacion(ok=True, ids=[s.id for s in creadas], advertencia=advertencia)


def crear_fase(solicitud, tipo_fase, *, justificacion: Optional[str] = None) -> ResultadoMutacion:
    expediente = solicitud.expediente
    if justificacion is None:
        res_eval = _evaluar('CREAR', expediente,
                            objeto={'solicitud': solicitud, 'tipo_fase': tipo_fase})
        if not res_eval.permitido:
            return ResultadoMutacion(ok=False, bloqueo=res_eval)
    else:
        res_eval = PERMITIDO

    fase = Fase(solicitud_id=solicitud.id, tipo_fase_id=tipo_fase.id)
    db.session.add(fase)
    db.session.flush()

    if tipo_fase.codigo in _FASES_QUE_REQUIEREN_CERT_IP_CONSULTAS:
        from app.services.cert_fin_ip_consultas import crear_cert_fin_ip_consultas
        crear_cert_fin_ip_consultas(expediente, solicitud)

    if justificacion:
        sujeto = build_sujeto(expediente, {'solicitud': solicitud, 'tipo_fase': tipo_fase})
        bitacora_svc.registrar(
            current_user.id, 'CREAR', 'fases', fase.id,
            detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
        )
    elif res_eval.nivel == 'ADVERTIR':
        sujeto = build_sujeto(expediente, {'solicitud': solicitud, 'tipo_fase': tipo_fase})
        _registrar_advertencia('CREAR', 'fases', fase.id, sujeto, res_eval)

    db.session.commit()
    return ResultadoMutacion(ok=True, ids=[fase.id], advertencia=_advertencia_dict(res_eval))


def crear_tramite(fase, tipo_tramite, *, justificacion: Optional[str] = None) -> ResultadoMutacion:
    if not tipo_tramite.creacion_generica:
        return ResultadoMutacion(
            ok=False,
            error='Los trámites de traslado se crean desde la acción específica de organismo',
        )

    res_inv = check_invariante('MUTAR', 'FASE', fase.id)
    if res_inv:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)

    res_vocab = check_vocabulario_tramite(fase, tipo_tramite)
    if _bloquea(res_vocab, justificacion):
        return ResultadoMutacion(ok=False, bloqueo=res_vocab)

    expediente = fase.solicitud.expediente
    if justificacion is None:
        res_eval = _evaluar('CREAR', expediente,
                            objeto={'fase': fase, 'tipo_tramite': tipo_tramite})
        if not res_eval.permitido:
            return ResultadoMutacion(ok=False, bloqueo=res_eval)
    else:
        res_eval = PERMITIDO

    tramite = Tramite(fase_id=fase.id, tipo_tramite_id=tipo_tramite.id)
    db.session.add(tramite)
    db.session.flush()

    if justificacion:
        sujeto = build_sujeto(expediente, {'fase': fase, 'tipo_tramite': tipo_tramite})
        bitacora_svc.registrar(
            current_user.id, 'CREAR', 'tramites', tramite.id,
            detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
        )
    elif res_eval.nivel == 'ADVERTIR':
        sujeto = build_sujeto(expediente, {'fase': fase, 'tipo_tramite': tipo_tramite})
        _registrar_advertencia('CREAR', 'tramites', tramite.id, sujeto, res_eval)

    db.session.commit()
    return ResultadoMutacion(ok=True, ids=[tramite.id], advertencia=_advertencia_dict(res_eval))


def crear_tarea(tramite, tipo_tarea, *, justificacion: Optional[str] = None) -> ResultadoMutacion:
    res_inv = check_invariante('MUTAR', 'TRAMITE', tramite.id)
    if res_inv:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)

    res_orden = check_orden_tarea(tramite, tipo_tarea)
    if _bloquea(res_orden, justificacion):
        return ResultadoMutacion(ok=False, bloqueo=res_orden)

    expediente = tramite.fase.solicitud.expediente
    if justificacion is None:
        res_eval = _evaluar('CREAR', expediente,
                            objeto={'tramite': tramite, 'tipo_tarea': tipo_tarea})
        if not res_eval.permitido:
            return ResultadoMutacion(ok=False, bloqueo=res_eval)
    else:
        res_eval = PERMITIDO

    tarea = Tarea(tramite_id=tramite.id, tipo_tarea_id=tipo_tarea.id)
    db.session.add(tarea)
    db.session.flush()

    advertencia = _advertencia_dict(res_eval)
    if justificacion:
        sujeto = build_sujeto(expediente, tramite)
        bitacora_svc.registrar(
            current_user.id, 'CREAR', 'tareas', tarea.id,
            detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
        )
    elif res_eval.nivel == 'ADVERTIR':
        sujeto = build_sujeto(expediente, tramite)
        _registrar_advertencia('CREAR', 'tareas', tarea.id, sujeto, res_eval)

    advertencia = _hook_776_elaborar_consume_disparo_admision(tarea) or advertencia

    db.session.commit()
    return ResultadoMutacion(ok=True, ids=[tarea.id], advertencia=advertencia)


def crear_organismo(fase, entidad, *, via: str, documento_id: Optional[int] = None,
                     justificacion: Optional[str] = None) -> ResultadoMutacion:
    """Alta de un organismo consultado en una fase CONSULTAS (ADR-042 §C).

    No es "crear hijo" por despensa: `OrganismoExpediente` no es un nodo ESFTT
    tipado (ADR-042) — `entidad` llega ya resuelta por el caller, no un tipo de
    catálogo. `resultado` no es parámetro: se deriva de `via` (DISEÑO_CONSULTAS_
    ORGANISMOS.md §2 — `exonerado` es terminal desde el inicio para declaración
    responsable; NULL, ciclo en curso, para consulta ordinaria).
    """
    expediente = fase.solicitud.expediente

    res_inv = check_invariante('MUTAR', 'FASE', fase.id)
    if res_inv:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)

    if not entidad.rol_consultado:
        return ResultadoMutacion(ok=False, error='La entidad no tiene rol de organismo consultado')

    if via not in VIAS_ORGANISMO:
        return ResultadoMutacion(ok=False, error=f'via debe ser uno de {VIAS_ORGANISMO}')

    if via == 'declaracion_responsable' and not documento_id:
        return ResultadoMutacion(
            ok=False, error='documento_id es obligatorio para la vía declaracion_responsable')
    if via == 'consulta' and documento_id:
        return ResultadoMutacion(
            ok=False, error='documento_id solo aplica a la vía declaracion_responsable')

    if documento_id:
        doc = Documento.query.get(documento_id)
        if not doc or doc.expediente_id != expediente.id:
            return ResultadoMutacion(ok=False, error='Documento no válido para este expediente')

    if OrganismoExpediente.query.filter_by(fase_id=fase.id, organismo_id=entidad.id).first():
        return ResultadoMutacion(
            ok=False, error='Este organismo ya está registrado en esta ronda de consultas')

    # Dict, no la fase en sí: el motor solo necesita el sujeto de la fase — pasar
    # una instancia real de OrganismoExpediente confundiría a ExpedienteContext
    # (duck-typing por atributos, ver assembler.py: tiene `.fase` y no `.tramites`,
    # la misma forma que un Tramite).
    objeto_sujeto = {'fase': fase}
    if justificacion is None:
        res_eval = _evaluar('CREAR', expediente, objeto=objeto_sujeto)
        if not res_eval.permitido:
            return ResultadoMutacion(ok=False, bloqueo=res_eval)
    else:
        res_eval = PERMITIDO

    oe = OrganismoExpediente(
        expediente_id=expediente.id,
        fase_id=fase.id,
        organismo_id=entidad.id,
        via=via,
        documento_id=documento_id,
        resultado='exonerado' if via == 'declaracion_responsable' else None,
    )
    db.session.add(oe)
    db.session.flush()

    if justificacion:
        sujeto = build_sujeto(expediente, objeto_sujeto)
        bitacora_svc.registrar(
            current_user.id, 'CREAR', 'organismos_expediente', oe.id,
            detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
        )
    elif res_eval.nivel == 'ADVERTIR':
        sujeto = build_sujeto(expediente, objeto_sujeto)
        _registrar_advertencia('CREAR', 'organismos_expediente', oe.id, sujeto, res_eval)

    db.session.commit()
    return ResultadoMutacion(ok=True, ids=[oe.id], advertencia=_advertencia_dict(res_eval))


# ===========================================================================
# EDITAR
# ===========================================================================

def editar_solicitud(sol, *, observaciones: Optional[str]) -> ResultadoMutacion:
    try:
        sol.observaciones = observaciones or None
        db.session.commit()
        return ResultadoMutacion(ok=True)
    except Exception as e:
        db.session.rollback()
        return ResultadoMutacion(ok=False, error=str(e))


def editar_fase(fase, *, resultado_fase_id: Optional[int],
                documento_resultado_id: Optional[int],
                observaciones: Optional[str],
                justificacion: Optional[str] = None) -> ResultadoMutacion:
    """
    `justificacion` (#723): vía de escape de los bloqueos forzables del cierre
    —completitud "incompleto con contenido" y diagnóstico desfavorable vigente—,
    registrada en bitácora (una entrada por invariante saltado). No abre las
    puertas cerradas: fase/trámite vacíos siguen sin poder cerrarse (la vía es
    borrar), y el sellado de una fase ya cerrada tampoco se salta con esto.
    """
    # Sellado (#720, ADR-036 §6/§7): solo bloquea si la fase YA estaba cerrada al
    # entrar — el propio cierre (finalizada aún False → True) no se autobloquea.
    res_inv = check_invariante('MUTAR', 'FASE', fase.id)
    if res_inv:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)

    advertencia = None
    bloqueos_forzados = []
    if documento_resultado_id and fase.documento_resultado_id is None:
        doc = Documento.query.get(documento_resultado_id)
        if not doc or doc.expediente_id != fase.solicitud.expediente_id:
            return ResultadoMutacion(ok=False, error='Documento no válido para este expediente')

        # Completitud (#723): sin estructura no se pregunta ni por el resultado.
        res_completitud = _check_completitud_cierre(fase)
        if _bloquea(res_completitud, justificacion):
            return ResultadoMutacion(ok=False, bloqueo=res_completitud)
        if res_completitud:
            bloqueos_forzados.append(res_completitud)

        if resultado_fase_id:
            from app.models.tipos_resultados_fases import TipoResultadoFase
            tipo_res = TipoResultadoFase.query.get(resultado_fase_id)
            if tipo_res:
                res_cierre = _check_cierre_fase(fase.id, tipo_res.codigo)
                if _bloquea(res_cierre, justificacion):
                    return ResultadoMutacion(ok=False, bloqueo=res_cierre)
                if res_cierre:
                    bloqueos_forzados.append(res_cierre)

        # #738 punto 4: guarda temprana no bloqueante — documento(s) justificante en
        # el pool del expediente sin vincular a ninguna tarea. ADVERTIR, no BLOQUEAR:
        # el pool es del expediente completo, no de esta fase, así que el documento
        # suelto puede pertenecer legítimamente a otro trámite/fase.
        advertencia = advertir_documentos_criticos_huerfanos(fase.solicitud.expediente_id)

    try:
        fase.resultado_fase_id = resultado_fase_id
        fase.documento_resultado_id = documento_resultado_id
        fase.observaciones = observaciones or None
        db.session.flush()

        if bloqueos_forzados:
            sujeto = build_sujeto(fase.solicitud.expediente, fase)
            for b in bloqueos_forzados:
                bitacora_svc.registrar(
                    current_user.id, 'ALTERAR', 'fases', fase.id,
                    detalle={'escape': True, 'justificacion': justificacion,
                             'motivo': b.motivo or b.norma_compilada, 'sujeto': sujeto},
                )

        db.session.commit()
        return ResultadoMutacion(ok=True, advertencia=advertencia)
    except Exception as e:
        db.session.rollback()
        return ResultadoMutacion(ok=False, error=str(e))


def reabrir_fase(fase, *, justificacion: str) -> ResultadoMutacion:
    """Reabre una fase cerrada (#720, ADR-036): retira el sellado para poder
    corregir su interior. Acto consciente y auditado — `justificacion` siempre
    obligatoria, no existe reapertura silenciosa.

    Puerta cerrada sin bypass (ADR-036 §4, `_check_reabrir`): si la solicitud ya
    está resuelta y notificada, el acto ya salió fuera — la corrección exige un
    acto administrativo expreso, fuera de este servicio.
    """
    if not fase.finalizada:
        return ResultadoMutacion(ok=False, error='La fase no está cerrada.')
    if not justificacion:
        return ResultadoMutacion(ok=False, error='La reapertura de una fase requiere justificación.')

    res_inv = check_invariante('REABRIR', 'FASE', fase.id)
    if res_inv:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)

    expediente = fase.solicitud.expediente
    sujeto = build_sujeto(expediente, fase)

    try:
        fase.resultado_fase_id = None
        fase.documento_resultado_id = None
        db.session.flush()

        bitacora_svc.registrar(
            current_user.id, 'ALTERAR', 'fases', fase.id,
            detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto,
                     'accion': 'REABRIR'},
        )
        db.session.commit()
        return ResultadoMutacion(ok=True, ids=[fase.id])
    except Exception as e:
        db.session.rollback()
        return ResultadoMutacion(ok=False, error=str(e))


def editar_organismo(oe, *, via: str, resultado: Optional[str],
                      direccion_notificacion_id: Optional[int],
                      documento_id: Optional[int]) -> ResultadoMutacion:
    """Edita un organismo consultado: vía, resultado y datos de contacto.

    `organismo_id` (a qué entidad se consulta) no es editable — cambiarlo es
    dar de baja y dar de alta otro, no una edición. Sin `justificacion`: el
    único invariante que protege esta mutación (sellado de fase) no es
    forzable (`_check_mutar`, puerta cerrada — reabrir la fase es el único
    camino, igual que `editar_tramite`).
    """
    res_inv = check_invariante('MUTAR', 'ORGANISMO', oe.id)
    if res_inv:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)

    if via not in VIAS_ORGANISMO:
        return ResultadoMutacion(ok=False, error=f'via debe ser uno de {VIAS_ORGANISMO}')

    if via == 'declaracion_responsable':
        if not documento_id:
            return ResultadoMutacion(
                ok=False, error='documento_id es obligatorio para la vía declaracion_responsable')
        # Terminal desde el inicio (DISEÑO_CONSULTAS_ORGANISMOS.md §2) — el
        # resultado no lo decide el tramitador campo a campo, lo fija la vía.
        resultado = 'exonerado'
    else:
        if resultado == 'exonerado':
            return ResultadoMutacion(
                ok=False, error="resultado 'exonerado' solo aplica a la vía declaracion_responsable")
        if resultado is not None and resultado not in RESULTADOS_ORGANISMO:
            return ResultadoMutacion(ok=False, error=f'resultado debe ser uno de {RESULTADOS_ORGANISMO} o vacío')

    expediente = oe.expediente
    if documento_id:
        doc = Documento.query.get(documento_id)
        if not doc or doc.expediente_id != expediente.id:
            return ResultadoMutacion(ok=False, error='Documento no válido para este expediente')
    if direccion_notificacion_id:
        dn = DireccionNotificacion.query.get(direccion_notificacion_id)
        if not dn:
            return ResultadoMutacion(ok=False, error='Dirección de notificación no válida')

    try:
        oe.via = via
        oe.resultado = resultado
        oe.direccion_notificacion_id = direccion_notificacion_id
        oe.documento_id = documento_id
        db.session.commit()
        return ResultadoMutacion(ok=True)
    except Exception as e:
        db.session.rollback()
        return ResultadoMutacion(ok=False, error=str(e))


def editar_tramite(tr, *, observaciones: Optional[str]) -> ResultadoMutacion:
    res_inv = check_invariante('MUTAR', 'TRAMITE', tr.id)
    if res_inv:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)

    try:
        tr.observaciones = observaciones or None
        db.session.commit()
        return ResultadoMutacion(ok=True)
    except Exception as e:
        db.session.rollback()
        return ResultadoMutacion(ok=False, error=str(e))


def editar_tarea(ta, *, documentos_consumidos_ids: list[int],
                 documento_producido_id: Optional[int],
                 notas: Optional[str]) -> ResultadoMutacion:
    """Actualiza vínculos documentales + notas de la tarea.

    `resultado` (NOTIFICAR) es una @property de Notificacion — no editable aquí.

    Vínculos por diff, no clear()+recrear (#667): un guardado que no cambia
    los documentos no debe tocar sus filas DOCUMENTOS_TAREA — eso es lo que
    permite detectar de forma fiable "primera vinculación" (documento sin
    ningún vínculo previo) para disparar el movimiento físico a la carpeta
    ESFTT (ADR-032 §3), y "última desvinculación" para la vuelta a pool/.
    """
    res_inv = check_invariante('MUTAR', 'TAREA', ta.id)
    if res_inv:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)

    expediente = ta.tramite.fase.solicitud.expediente

    # Capturado ANTES del diff (#717): distingue "se acaba de fijar el producido"
    # de "ya lo tenía y se guarda por otro motivo" — ver _hook_717 más abajo.
    doc_producido_previo = ta.documento_producido
    id_producido_previo = doc_producido_previo.id if doc_producido_previo else None

    ids_todos = list(documentos_consumidos_ids) + (
        [documento_producido_id] if documento_producido_id else [])
    for doc_id in ids_todos:
        doc = Documento.query.get(doc_id)
        if not doc or doc.expediente_id != expediente.id:
            return ResultadoMutacion(ok=False, error='Documento no válido para este expediente')

    try:
        deseados = {(doc_id, 'CONSUMIDO') for doc_id in dict.fromkeys(documentos_consumidos_ids)}
        if documento_producido_id:
            deseados.add((documento_producido_id, 'PRODUCIDO'))

        actuales = {(v.documento_id, v.rol): v for v in ta.vinculos_documento}

        docs_a_liberar = []
        for clave, vinculo in actuales.items():
            if clave not in deseados:
                doc = vinculo.documento
                rol_liberado = vinculo.rol
                ta.vinculos_documento.remove(vinculo)
                # #738 punto 1: desvincular un justificante es hoy silencioso — el
                # vínculo estructural (DocumentoTarea) desaparece pero la fila
                # Notificacion puede seguir viva apuntando al mismo documento
                # (ADR-034). No se bloquea (el issue no cierra esta puerta: la
                # vinculación pudo hacerse por error), solo queda rastro.
                if es_documento_critico(doc):
                    bitacora_svc.registrar(
                        current_user.id, 'ALTERAR', 'tareas', ta.id,
                        detalle={
                            'accion': 'DESVINCULAR_DOCUMENTO_CRITICO',
                            'documento_id': doc.id,
                            'tipo_documento': doc.tipo_doc.codigo,
                            'rol': rol_liberado,
                            'sujeto': build_sujeto(expediente, ta.tramite),
                        },
                    )
                if not doc.vinculos_tarea:
                    docs_a_liberar.append(doc)
        db.session.flush()

        docs_a_encajar = []
        for doc_id, rol in deseados:
            if (doc_id, rol) not in actuales:
                doc = Documento.query.get(doc_id)
                if not doc.vinculos_tarea:
                    docs_a_encajar.append(doc)
                ta.vinculos_documento.append(DocumentoTarea(documento_id=doc_id, rol=rol))

        ta.notas = notas or None
        db.session.flush()

        for doc in docs_a_encajar:
            mover_a_esftt(doc, ta)
        for doc in docs_a_liberar:
            mover_a_pool(doc, expediente)

        # Tras mover_a_esftt (documento ya en su ubicación final) — el hook solo
        # lee el fichero, no depende de dónde esté, pero mantiene el orden lógico
        # "vínculos resueltos → efectos derivados" del resto de la función.
        advertencia = _hook_657_notificar_resultado(ta, documento_producido_id)

        # #717: solo en la transición a un producido NUEVO — mover_a_esftt ya
        # dejó el fichero en su ubicación final, necesaria para leer su texto.
        if documento_producido_id and documento_producido_id != id_producido_previo:
            advertencia = _hook_717_elaborar_consumido_diagnostico(ta, documento_producido_id) or advertencia

        db.session.flush()

        db.session.commit()
        return ResultadoMutacion(ok=True, advertencia=advertencia)
    except IntegrityError:
        db.session.rollback()
        return ResultadoMutacion(
            ok=False, error='Este documento ya está asignado como producido a otra tarea')
    except Exception as e:
        db.session.rollback()
        return ResultadoMutacion(ok=False, error=str(e))


def sincronizar_consumido_documental(tarea: Tarea) -> None:
    """
    Deriva los vínculos DocumentoTarea CONSUMIDO de una tarea ANALIZAR a partir
    de los documentos casados con sus requisitos documentales (ADR-033 §1,
    #677): casar un requisito ⇒ consumido derivado, sin gesto manual en la
    Despensa (oculta para ANALIZAR extendido, ver Inspector.jsx).

    Se llama tras vincular/desvincular_requisito_documental. Mismo patrón
    diff + movimiento físico que editar_tarea (ADR-032 §3): solo toca lo que
    cambia, nunca clear()+recrear — evita disparar mover_a_esftt/mover_a_pool
    en documentos que ya estaban en su sitio.

    `evaluar_requisitos` casa por solicitud, no por vuelta: en la cadena de
    subsanación se descarta lo que ya conste CONSUMIDO en otra tarea ANALIZAR
    de la misma cadena (#826) — un ANALIZAR analiza lo que llega nuevo, no
    re-analiza lo que ya analizó una vuelta anterior.
    """
    solicitud = tarea.tramite.fase.solicitud
    _, variables = build(solicitud.expediente, objeto=tarea)
    resultado = evaluar_requisitos(solicitud, variables)
    if resultado['error']:
        return

    deseados_ids = {it['documento'].id for it in resultado['items'] if it['documento'] is not None}
    deseados_ids -= documentos_consumidos_otras_tareas_cadena(tarea)
    actuales = {v.documento_id: v for v in tarea.vinculos_documento if v.rol == 'CONSUMIDO'}

    docs_a_liberar = []
    for doc_id, vinculo in actuales.items():
        if doc_id not in deseados_ids:
            doc = vinculo.documento
            tarea.vinculos_documento.remove(vinculo)
            if not doc.vinculos_tarea:
                docs_a_liberar.append(doc)
    db.session.flush()

    docs_a_encajar = []
    for doc_id in deseados_ids:
        if doc_id not in actuales:
            doc = Documento.query.get(doc_id)
            if not doc.vinculos_tarea:
                docs_a_encajar.append(doc)
            tarea.vinculos_documento.append(DocumentoTarea(documento_id=doc_id, rol='CONSUMIDO'))
    db.session.flush()

    for doc in docs_a_encajar:
        mover_a_esftt(doc, tarea)
    for doc in docs_a_liberar:
        mover_a_pool(doc, solicitud.expediente)

    db.session.commit()


# ===========================================================================
# BORRAR (hoja a hoja — sin cascada manual desde #722, guardia en check_invariante)
# ===========================================================================

def borrar_solicitud(sol, *, justificacion: Optional[str] = None) -> ResultadoMutacion:
    expediente = sol.expediente

    # Invariante (#722): nunca bypasseable con justificación, ver docstring de _check_borrar.
    res_inv = check_invariante('BORRAR', 'SOLICITUD', sol.id)
    if res_inv:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)

    if justificacion is None:
        res_eval = _evaluar('BORRAR', expediente, objeto=sol)
        if not res_eval.permitido:
            return ResultadoMutacion(ok=False, bloqueo=res_eval)

    if justificacion:
        sujeto = build_sujeto(expediente, sol)
        bitacora_svc.registrar(
            current_user.id, 'BORRAR', 'solicitudes', sol.id,
            detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
        )

    db.session.delete(sol)
    db.session.commit()
    return ResultadoMutacion(ok=True)


def borrar_fase(fase, *, justificacion: Optional[str] = None) -> ResultadoMutacion:
    expediente = fase.solicitud.expediente

    res_inv = check_invariante('BORRAR', 'FASE', fase.id)
    if res_inv:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)

    if justificacion is None:
        res_eval = _evaluar('BORRAR', expediente, objeto=fase)
        if not res_eval.permitido:
            return ResultadoMutacion(ok=False, bloqueo=res_eval)

    if justificacion:
        sujeto = build_sujeto(expediente, fase)
        bitacora_svc.registrar(
            current_user.id, 'BORRAR', 'fases', fase.id,
            detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
        )

    db.session.delete(fase)
    db.session.commit()
    return ResultadoMutacion(ok=True)


def borrar_tramite(tr, *, justificacion: Optional[str] = None) -> ResultadoMutacion:
    expediente = tr.fase.solicitud.expediente

    res_inv = check_invariante('MUTAR', 'TRAMITE', tr.id)
    if res_inv:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)

    res_inv = check_invariante('BORRAR', 'TRAMITE', tr.id)
    if res_inv:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)

    if justificacion is None:
        res_eval = _evaluar('BORRAR', expediente, objeto=tr)
        if not res_eval.permitido:
            return ResultadoMutacion(ok=False, bloqueo=res_eval)

    if justificacion:
        sujeto = build_sujeto(expediente, tr)
        bitacora_svc.registrar(
            current_user.id, 'BORRAR', 'tramites', tr.id,
            detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
        )

    db.session.delete(tr)
    db.session.commit()
    return ResultadoMutacion(ok=True)


def borrar_organismo(oe, *, justificacion: Optional[str] = None) -> ResultadoMutacion:
    expediente = oe.expediente

    res_inv = check_invariante('MUTAR', 'ORGANISMO', oe.id)
    if res_inv:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)

    res_inv = check_invariante('BORRAR', 'ORGANISMO', oe.id)
    if res_inv:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)

    objeto_sujeto = {'fase': oe.fase}  # dict, no oe (duck-typing, ver crear_organismo)
    if justificacion is None:
        res_eval = _evaluar('BORRAR', expediente, objeto=objeto_sujeto)
        if not res_eval.permitido:
            return ResultadoMutacion(ok=False, bloqueo=res_eval)

    if justificacion:
        sujeto = build_sujeto(expediente, objeto_sujeto)
        bitacora_svc.registrar(
            current_user.id, 'BORRAR', 'organismos_expediente', oe.id,
            detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
        )

    db.session.delete(oe)
    db.session.commit()
    return ResultadoMutacion(ok=True)


def borrar_tarea(ta, *, justificacion: Optional[str] = None) -> ResultadoMutacion:
    expediente = ta.tramite.fase.solicitud.expediente

    res_inv = check_invariante('MUTAR', 'TAREA', ta.id)
    if res_inv:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)

    res_inv = check_invariante('BORRAR', 'TAREA', ta.id)
    if res_inv:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)

    if justificacion is None:
        res_eval = _evaluar('BORRAR', expediente, objeto=ta)
        if not res_eval.permitido:
            return ResultadoMutacion(ok=False, bloqueo=res_eval)

    if justificacion:
        sujeto = build_sujeto(expediente, ta.tramite)
        bitacora_svc.registrar(
            current_user.id, 'BORRAR', 'tareas', ta.id,
            detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
        )

    db.session.delete(ta)
    db.session.commit()
    return ResultadoMutacion(ok=True)
