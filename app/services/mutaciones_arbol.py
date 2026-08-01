"""
mutaciones_arbol.py — Servicio de mutaciones ESFTT para el árbol (ADR-016, S3b-0).

Funciones puras de dominio (sin request/jsonify) para Crear / Editar / Borrar
los cuatro niveles del árbol (solicitud, fase, trámite, tarea).

Extraídas literalmente de app/routes/api_bc.py (camino B, #500):
- api_bc delega aquí y mantiene su contrato HTTP intacto.
- Los endpoints JSON del árbol también llaman a estas funciones.

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
from app.models.tramites_organismos import TramiteOrganismo
from app.models.notificaciones import Notificacion
from app.services.assembler import build, build_sujeto
from app.services import bitacora as bitacora_svc
from app.services.motor_reglas import EvaluacionResult, PERMITIDO
from app.services.motor_modo_global import evaluar_con_modo_global as _evaluar
from app.services.invariantes_esftt import _check_cierre_fase, diagnostico_tramite_anterior
from app.services.requisitos import evaluar_requisitos
from app.services.rutas_esftt import mover_a_esftt, mover_a_pool
from app.services.parser_justificante_notifica import (
    parsear_justificante_notifica, parsear_justificante_notifica_zip,
)
from app.services.codigo_seguimiento import extraer_tarea_id
from app.services.extraccion_texto_documento import extraer_texto

log = logging.getLogger(__name__)

# Espejo de api_bc — mantener sincronizados hasta unificar (deuda conocida)
_CODIGOS_TRASLADO = frozenset({'CONSULTA_TRASLADO_ORGANISMO', 'CONSULTA_TRASLADO_TITULAR'})
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
# Hook #458 (movido desde api_bc; test_458 actualizado para importar de aquí)
# ---------------------------------------------------------------------------

def _hook_458_analizar_separata(tarea, id_producido):
    """Hook #458: al producir diagnóstico en CONSULTA_SEPARATA pasa el organismo a en_tramitacion."""
    if (id_producido is not None
            and tarea.tipo_tarea.codigo == 'ANALIZAR'
            and tarea.tramite.tipo_tramite.codigo == 'CONSULTA_SEPARATA'):
        vinculo = TramiteOrganismo.query.filter_by(tramite_id=tarea.tramite_id).first()
        if vinculo:
            vinculo.organismo_expediente.estado = 'en_tramitacion'


# ---------------------------------------------------------------------------
# Hook #657/#658 (ADR-034 §6): camino B — justificante definitivo
# ---------------------------------------------------------------------------

# Tipo de documento → canal (TIPOS_DOCUMENTOS_CATALOGO.md). Solo NOTIFICA tiene
# parser hoy (#655); el resto queda a la espera del "Registrar envío"/"Completar
# resultado" manual de NotificarEditor (#657).
_MAPA_CANAL_POR_TIPO_DOC = {
    'JUSTIFICANTE_NOTIFICA': 'NOTIFICA',
    'JUSTIFICANTE_BANDEJA':  'BANDEJA',
    'JUSTIFICANTE_SIR':      'SIR',
    'JUSTIFICANTE_POSTAL':   'POSTAL',
}


def _parsear_documento_notifica(doc: Documento):
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
    """Hook #657/#658: al fijar/cambiar documento_producido_id en una tarea NOTIFICAR,
    upsert de Notificacion buscando por tarea_id (nunca por identificador_envio,
    ADR-034 §6) + cotejo no bloqueante contra la remesa ya registrada (#658).

    Devuelve un dict de advertencia (cotejo fallido) para que el caller lo
    propague al cliente, o None. Sin parser para el canal del documento (todo
    salvo NOTIFICA hoy) solo actualiza documento_id si ya existe fila — sin
    fila previa y sin datos parseados no puede crearla (fecha_puesta_disposicion
    es NOT NULL): el usuario debe usar "Registrar envío"/"Completar resultado"
    a mano en NotificarEditor.
    """
    if id_producido is None or tarea.tipo_tarea.codigo != 'NOTIFICAR':
        return None

    doc = Documento.query.get(id_producido)
    tipo_codigo = doc.tipo_doc.codigo if doc.tipo_doc else None
    canal = _MAPA_CANAL_POR_TIPO_DOC.get(tipo_codigo)
    if canal is None:
        return None  # tipo de documento no es un justificante de notificación reconocido

    parseo = _parsear_documento_notifica(doc) if canal == 'NOTIFICA' else None

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

    advertencia = None
    if (parseo is not None and notif.identificador_envio and parseo.id_remesa
            and notif.identificador_envio != parseo.id_remesa):
        advertencia = {
            'motivo': (
                f'El justificante vinculado trae la remesa «{parseo.id_remesa}», '
                f'distinta de la registrada al notificar («{notif.identificador_envio}»). '
                'Puede haberse vinculado el justificante de otro expediente.'
            ),
        }

    notif.documento_id = doc.id
    if parseo is not None:
        notif.identificador_envio = notif.identificador_envio or parseo.id_remesa
        notif.resultado = parseo.resultado
        notif.fecha_resultado = parseo.fecha_lectura.date() if parseo.fecha_lectura else None

    return advertencia


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
    if not ya_vinculado:
        tarea.vinculos_documento.append(
            DocumentoTarea(documento_id=diagnostico.documento_id, rol='CONSUMIDO'))
    return None


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
    if tipo_tramite.codigo in _CODIGOS_TRASLADO:
        return ResultadoMutacion(
            ok=False,
            error='Los trámites de traslado se crean desde la acción específica de organismo',
        )

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

    if justificacion:
        sujeto = build_sujeto(expediente, tramite)
        bitacora_svc.registrar(
            current_user.id, 'CREAR', 'tareas', tarea.id,
            detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
        )
    elif res_eval.nivel == 'ADVERTIR':
        sujeto = build_sujeto(expediente, tramite)
        _registrar_advertencia('CREAR', 'tareas', tarea.id, sujeto, res_eval)

    db.session.commit()
    return ResultadoMutacion(ok=True, ids=[tarea.id], advertencia=_advertencia_dict(res_eval))


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
                observaciones: Optional[str]) -> ResultadoMutacion:
    if documento_resultado_id and fase.documento_resultado_id is None:
        doc = Documento.query.get(documento_resultado_id)
        if not doc or doc.expediente_id != fase.solicitud.expediente_id:
            return ResultadoMutacion(ok=False, error='Documento no válido para este expediente')

        if resultado_fase_id:
            from app.models.tipos_resultados_fases import TipoResultadoFase
            tipo_res = TipoResultadoFase.query.get(resultado_fase_id)
            if tipo_res:
                res_inv = _check_cierre_fase(fase.id, tipo_res.codigo)
                if res_inv:
                    return ResultadoMutacion(ok=False, bloqueo=res_inv)

    try:
        fase.resultado_fase_id = resultado_fase_id
        fase.documento_resultado_id = documento_resultado_id
        fase.observaciones = observaciones or None
        db.session.commit()
        return ResultadoMutacion(ok=True)
    except Exception as e:
        db.session.rollback()
        return ResultadoMutacion(ok=False, error=str(e))


def editar_tramite(tr, *, observaciones: Optional[str]) -> ResultadoMutacion:
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
                ta.vinculos_documento.remove(vinculo)
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
        _hook_458_analizar_separata(ta, documento_producido_id)
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
    """
    solicitud = tarea.tramite.fase.solicitud
    _, variables = build(solicitud.expediente, objeto=tarea)
    resultado = evaluar_requisitos(solicitud, variables)
    if resultado['error']:
        return

    deseados_ids = {it['documento'].id for it in resultado['items'] if it['documento'] is not None}
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
# BORRAR (cascada manual — idéntica a api_bc)
# ===========================================================================

def borrar_solicitud(sol, *, justificacion: Optional[str] = None) -> ResultadoMutacion:
    expediente = sol.expediente
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

    fase_ids = [f.id for f in Fase.query.filter_by(solicitud_id=sol.id).all()]
    if fase_ids:
        tram_ids = [t.id for t in Tramite.query.filter(Tramite.fase_id.in_(fase_ids)).all()]
        if tram_ids:
            Tarea.query.filter(Tarea.tramite_id.in_(tram_ids)).delete()
        Tramite.query.filter(Tramite.fase_id.in_(fase_ids)).delete()
    Fase.query.filter_by(solicitud_id=sol.id).delete()
    db.session.delete(sol)
    db.session.commit()
    return ResultadoMutacion(ok=True)


def borrar_fase(fase, *, justificacion: Optional[str] = None) -> ResultadoMutacion:
    expediente = fase.solicitud.expediente
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

    tram_ids = [t.id for t in Tramite.query.filter_by(fase_id=fase.id).all()]
    if tram_ids:
        Tarea.query.filter(Tarea.tramite_id.in_(tram_ids)).delete()
    Tramite.query.filter_by(fase_id=fase.id).delete()
    db.session.delete(fase)
    db.session.commit()
    return ResultadoMutacion(ok=True)


def borrar_tramite(tr, *, justificacion: Optional[str] = None) -> ResultadoMutacion:
    expediente = tr.fase.solicitud.expediente
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

    Tarea.query.filter_by(tramite_id=tr.id).delete()
    db.session.delete(tr)
    db.session.commit()
    return ResultadoMutacion(ok=True)


def borrar_tarea(ta, *, justificacion: Optional[str] = None) -> ResultadoMutacion:
    expediente = ta.tramite.fase.solicitud.expediente
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
