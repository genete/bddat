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
    _check_cierre_fase, _check_completitud_cierre, check_cierre_finalizadora_por_editor,
    check_invariante, check_vinculo_sellado,
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
from app.services.reformados import ultimo_reformado
from app.services import notificaciones as notif_svc
from app.services import destinatarios_notificacion as dest_svc

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
# Hook de NOTIFICAR (#657/#658/#712, rehecho en #928 — ADR-049 §B)
# ---------------------------------------------------------------------------

# Tipo de documento → canal: los seis justificantes con canal (previos y
# finales). JUSTIFICANTE_SEDE y ANUNCIO_PUBLICADO no están — ninguno crea fila
# por sí solo (la sede no es una notificación; el edicto es de #568, D15).
# Público: lo reutiliza api_expedientes.py (validación del preview, #712).
MAPA_CANAL_POR_TIPO_DOC = notif_svc.CANAL_POR_TIPO_DOC


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


def _tipo_codigo(doc) -> Optional[str]:
    return doc.tipo_doc.codigo if doc.tipo_doc else None


def _avisos_rol_incoherente(tarea) -> list[str]:
    """D17: un justificante previo vinculado como PRODUCIDO, o un justificante
    final como CONSUMIDO. No bloquea — BDDAT no verifica el carácter del
    documento (P5) — solo avisa. ANUNCIO_PUBLICADO se admite en los dos roles
    (el intermedio se consume, el definitivo se produce; #568)."""
    avisos = []
    for v in tarea.vinculos_documento:
        tipo = _tipo_codigo(v.documento)
        if v.rol == 'PRODUCIDO' and tipo in notif_svc.TIPOS_JUSTIFICANTE_PREVIO:
            avisos.append(
                f'«{tipo}» es un justificante previo y se ha vinculado como producido: '
                'debería vincularse como consumido (el producido es el justificante final).'
            )
        elif (v.rol == 'CONSUMIDO' and tipo in notif_svc.JUSTIFICANTES_FINALES
              and tipo != 'ANUNCIO_PUBLICADO'):
            avisos.append(
                f'«{tipo}» es un justificante final y se ha vinculado como consumido: '
                'debería vincularse como producido.'
            )
    return avisos


def _hook_notificar(tarea) -> Optional[dict]:
    """Hook de NOTIFICAR (#657/#658/#712; rehecho en #928, ADR-049 §B y §6 del
    issue; desde #967 ya no crea ni borra la fila, ADR-051 §B). Se llama en
    cada `editar_tarea` de una NOTIFICAR, con la tarea ya con sus vínculos
    resueltos: los consumidos (justificantes previos) importan tanto como el
    producido. La fila existe siempre: nace con la tarea (`crear_tarea`).

    - Docs con canal = vínculos cuyo tipo está en `MAPA_CANAL_POR_TIPO_DOC`.
      Canal: el del PRODUCIDO si lo tiene; si no, el de los previos.
    - Fila sin canal y algún doc con canal → fija el canal, para cualquier
      canal (no solo el parseable), `documento_id` = el PRODUCIDO si es un
      justificante final, e `identificador_envio` del parseo si lo hay.
    - Fila con canal → cotejo de canal y de remesa (#658/#712); `documento_id`
      sigue al PRODUCIDO.
    - En los dos casos, cotejo del NIF del justificante de Notifica con el del
      destinatario copiado (#967, ADR-051 §B).
    - Sin ningún doc con canal y `resultado IS NULL` → vacía lo que puso el
      primer justificante (D16; hasta #967 borraba la fila): sin justificante y
      sin resultado no hay constancia de nada. Con resultado se conserva.
    - **Nunca escribe `resultado`** (D2): lo fija el usuario con el PATCH; el
      parser solo lo propone (`parsear_documento`). Ni fechas: no existen.

    Avisos no bloqueantes (canal incoherente, remesa o NIF distintos, rol
    incoherente con el tipo): se devuelven al cliente y quedan en bitácora (D17).
    """
    if tarea.tipo_tarea.codigo != 'NOTIFICAR':
        return None

    avisos = _avisos_rol_incoherente(tarea)
    notif = Notificacion.query.filter_by(tarea_id=tarea.id).first()
    if notif is None:
        # No debería pasar desde #967: toda NOTIFICAR nace con su fila. Una
        # tarea anterior sin recrear no se repara aquí — el hook ya no crea filas.
        return _cerrar_avisos_notificar(tarea, avisos)

    con_canal = [
        (v.documento, MAPA_CANAL_POR_TIPO_DOC[_tipo_codigo(v.documento)])
        for v in tarea.vinculos_documento
        if _tipo_codigo(v.documento) in MAPA_CANAL_POR_TIPO_DOC
    ]

    if not con_canal:
        if notif.resultado is None:
            notif.canal = None
            notif.documento_id = None
            notif.identificador_envio = None
            notif.numero_intento = 1
            notif.sede_justificacion = None
        return _cerrar_avisos_notificar(tarea, avisos)

    producido = tarea.documento_producido
    canal_producido = MAPA_CANAL_POR_TIPO_DOC.get(_tipo_codigo(producido)) if producido else None
    canales = sorted({c for _, c in con_canal})
    canal = canal_producido or canales[0]
    if len(canales) > 1:
        avisos.append(
            'Los justificantes vinculados corresponden a canales distintos '
            f'({", ".join(canales)}). Se toma «{canal}».'
        )

    # El parseo solo sirve para `identificador_envio` (remesa): el del
    # justificante NOTIFICA producido si lo hay; si no, el de un previo NOTIFICA.
    doc_notifica = next(
        (d for d, c in sorted(con_canal, key=lambda dc: dc[0] is not producido) if c == 'NOTIFICA'),
        None,
    )
    parseo = parsear_documento_notifica(doc_notifica) if doc_notifica else None
    remesa = parseo.id_remesa if parseo else None

    documento_id = (producido.id if producido is not None
                    and _tipo_codigo(producido) in notif_svc.JUSTIFICANTES_FINALES else None)

    # Con representante, el justificante puede traer su NIF o el del
    # representado: los dos son de esta notificación.
    nif_justificante = parseo.identificador_destinatario if parseo else None
    nifs_de_la_ficha = {_normalizar_nif(n) for n in (
        notif.dest_nif, notif.en_nombre_de.nif if notif.en_nombre_de else None) if n}
    if (nif_justificante and nifs_de_la_ficha
            and _normalizar_nif(nif_justificante) not in nifs_de_la_ficha):
        avisos.append(
            f'El justificante vinculado va dirigido al NIF «{nif_justificante}», distinto '
            f'del destinatario registrado («{notif.dest_nif}»). Puede haberse vinculado '
            'el justificante de otro destinatario.'
        )

    if notif.canal is None:
        notif.canal = canal
        notif.documento_id = documento_id
        notif.identificador_envio = remesa
        notif.numero_intento = 1
        return _cerrar_avisos_notificar(tarea, avisos)

    # #712: el documento vinculado manda sobre el canal anotado — el canal se
    # deriva del tipo de documento, siempre disponible, haya o no parser.
    if canal != notif.canal:
        avisos.append(
            f'El documento vinculado corresponde al canal «{canal}», distinto '
            f'del registrado («{notif.canal}»). Se ha actualizado el canal.'
        )
        notif.canal = canal
        if canal != 'POSTAL':
            notif.numero_intento = 1  # ck_notificaciones_intento_postal (D14)

    if notif.identificador_envio and remesa and notif.identificador_envio != remesa:
        avisos.append(
            f'El justificante vinculado trae la remesa «{remesa}», distinta de '
            f'la registrada («{notif.identificador_envio}»). Puede haberse '
            'vinculado el justificante de otro expediente.'
        )

    notif.documento_id = documento_id
    notif.identificador_envio = notif.identificador_envio or remesa
    return _cerrar_avisos_notificar(tarea, avisos)


def _bloqueo_sin_destinatario() -> EvaluacionResult:
    """Bloqueo forzable de una `NOTIFICAR` sin destinatario (ADR-051 §B). Mismo
    convenio que los invariantes: el mensaje va en `norma_compilada`."""
    return EvaluacionResult(
        permitido=False, nivel='BLOQUEAR', variables_trigger={},
        norma_compilada=(
            'Esta notificación no tiene destinatario: fija antes a quién se notifica. '
            'Si se fuerza con justificación, la notificación quedará sin destinatario '
            'para siempre.'
        ),
        url_norma='', puede_escapar=True,
    )


def _normalizar_nif(nif: str) -> str:
    return ''.join(c for c in nif.upper() if c.isalnum())


def _cerrar_avisos_notificar(tarea, avisos: list[str]) -> Optional[dict]:
    """Devuelve el dict de advertencia del hook de NOTIFICAR y deja constancia
    en bitácora (D17) con el formato de `_registrar_advertencia`. Hasta #928
    los avisos de canal y remesa solo llegaban al cliente, sin rastro."""
    if not avisos:
        return None
    motivo = ' '.join(avisos)
    bitacora_svc.registrar(
        current_user.id, 'ALTERAR', 'tareas', tarea.id,
        detalle={
            'advertencia': True,
            'motivo': motivo,
            'sujeto': build_sujeto(tarea.tramite.fase.solicitud.expediente, tarea.tramite),
        },
    )
    return {'motivo': motivo}


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

# El mismo texto para la ruta, la isla del árbol y el test.
MENSAJE_SIN_ANCLA_SOLICITUD = (
    'Toda solicitud necesita el escrito que la abre: elija del pool del expediente '
    'el documento de solicitud, del que cuelga el inicio del plazo para resolver.'
)


def _validar_ancla_solicitud(documento_id: Optional[int], expediente_id: int) -> Optional[str]:
    """Comprueba el ancla documental de una solicitud nueva, o dice qué falla.

    Las tres condiciones son independientes y cada una tiene su mensaje, porque el
    arreglo es distinto en cada caso: elegir un documento, elegir otro del
    expediente correcto, o ponerle fecha al que se eligió.
    """
    from app.models.documentos import Documento

    if not documento_id:
        return MENSAJE_SIN_ANCLA_SOLICITUD

    doc = Documento.query.get(documento_id)
    if doc is None or doc.expediente_id != expediente_id:
        return ('El documento elegido como escrito de solicitud no pertenece a este '
                'expediente.')

    if doc.fecha_administrativa is None:
        return ('El documento elegido no tiene fecha de registro de entrada, y es esa '
                'fecha la que inicia el plazo para resolver. Complétela en el pool '
                'antes de usarlo como escrito de solicitud.')

    return None


def crear_solicitud(expediente, tipos: list[TipoSolicitud], entidad_id: int,
                    *, documento_solicitud_id: Optional[int] = None,
                    representante_entidad_id: Optional[int] = None,
                    direccion_notificacion_id: Optional[int] = None,
                    justificacion: Optional[str] = None) -> ResultadoMutacion:
    """Crea una o varias solicitudes (multi-tipo). Valida motor para todos antes de persistir.

    Toda solicitud nace anclada a su escrito (#428). Es la segunda vía de alta —la
    primera es `app/services/alta_expediente.py`, para el expediente entero— y el
    invariante es el mismo: de la fecha administrativa de ese documento cuelga el
    inicio del plazo para resolver, así que sin él la solicitud nace `SIN_PLAZO` y
    nadie se entera. No se salta con `justificacion`: el bypass del motor (#324) es
    para las reglas de catálogo, no para la integridad documental.

    Aquí el expediente ya existe, así que el ancla se elige de su pool en vez de
    subirse con el alta. Se exige además que el documento **lleve fecha
    administrativa**: un ancla sin fecha no ancla nada, y dejarla pasar
    reproduciría el mismo agujero con la FK puesta.

    Con varios tipos, las solicitudes creadas comparten documento: un mismo escrito
    puede pedir varios actos administrativos.
    """
    exp_id = expediente.id

    if not entidad_id:
        return ResultadoMutacion(ok=False, error='El expediente no tiene titular asignado.')

    error_ancla = _validar_ancla_solicitud(documento_solicitud_id, exp_id)
    if error_ancla:
        return ResultadoMutacion(ok=False, error=error_ancla)

    # Representante de la solicitud (#967, ADR-051 §K): un autorizado del solicitante.
    error_rep = validar_representante(entidad_id, representante_entidad_id)
    if error_rep:
        return ResultadoMutacion(ok=False, error=error_rep)
    # Sede del solicitante (#989): la dirección del oficio.
    error_sede = validar_sede(entidad_id, direccion_notificacion_id)
    if error_sede:
        return ResultadoMutacion(ok=False, error=error_sede)

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
                            tipo_solicitud_id=tipo.id,
                            documento_solicitud_id=documento_solicitud_id,
                            representante_entidad_id=representante_entidad_id,
                            direccion_notificacion_id=direccion_notificacion_id)
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

    return ResultadoMutacion(ok=True, ids=[s.id for s in creadas],
                             advertencia=advertencia)


def crear_fase(solicitud, tipo_fase, *, justificacion: Optional[str] = None) -> ResultadoMutacion:
    """Crea una fase de la solicitud.

    El sello de la instrucción (#838, ADR-043 §F) es lo único que se comprueba antes
    del motor, y va primero por lo mismo que en `crear_tramite`/`crear_tarea`: es
    puerta cerrada y no se salta con `justificacion`, así que el bloqueo que no se
    fuerza se evalúa antes que el que sí. Hasta aquí esta función no llamaba a
    `check_invariante` en absoluto —el sellado de ADR-036 no le aplica, porque una
    fase no cuelga de otra fase— y era el único `crear_*` sin ninguna precondición
    estructural.

    La fase nace enganchada a la versión vigente del proyecto (ADR-044 §E, R3 #895):
    el último reformado del expediente en este momento, o NULL si no hay ninguno.
    Lo decide el sistema, no el técnico —preguntarlo sería la columna `produce_edicion`
    que el ADR descartó—, y es lo que hace funcionar la regla de §F sin preguntar dos
    veces lo mismo: sin reformado nuevo la fase cae en la versión ya cubierta y se
    bloquea.
    """
    res_inv_crear = check_invariante('CREAR', 'FASE', solicitud.id,
                                     tipo_codigo=tipo_fase.codigo)
    if res_inv_crear:
        return ResultadoMutacion(ok=False, bloqueo=res_inv_crear)

    expediente = solicitud.expediente
    if justificacion is None:
        res_eval = _evaluar('CREAR', expediente,
                            objeto={'solicitud': solicitud, 'tipo_fase': tipo_fase})
        if not res_eval.permitido:
            return ResultadoMutacion(ok=False, bloqueo=res_eval)
    else:
        res_eval = PERMITIDO

    version_vigente = ultimo_reformado(expediente.id)
    # Por la relación (`solicitud=`), no por el FK a pelo (ADR-044 R5): así
    # SQLAlchemy sincroniza `solicitud.fases` en memoria al momento, sin
    # esperar a una consulta nueva. Con el FK a pelo, un `solicitud.fases` ya
    # cargado antes de este punto en la misma sesión —p. ej. `Solicitud.estado`
    # comprobado justo después de crear la fase— se queda con la colección
    # vieja y no ve la fase recién creada.
    fase = Fase(solicitud=solicitud, tipo_fase=tipo_fase,
               reformado_id=version_vigente.id if version_vigente else None)
    db.session.add(fase)
    db.session.flush()

    if tipo_fase.codigo in _FASES_QUE_REQUIEREN_CERT_IP_CONSULTAS:
        from app.services.cert_fin_ip_consultas import crear_cert_fin_ip_consultas
        crear_cert_fin_ip_consultas(expediente, solicitud, version_vigente)

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

    # Precedencia al crear (#823): puerta cerrada, antes del vocabulario y del
    # motor —ninguno de los dos se salta con `justificacion`, así que se
    # comprueban primero.
    res_inv_crear = check_invariante('CREAR', 'TRAMITE', fase.id,
                                     tipo_codigo=tipo_tramite.codigo)
    if res_inv_crear:
        return ResultadoMutacion(ok=False, bloqueo=res_inv_crear)

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


def crear_tarea(tramite, tipo_tarea, *, justificacion: Optional[str] = None,
                fuente: Optional[str] = None) -> ResultadoMutacion:
    """Crea una tarea del trámite.

    Una `NOTIFICAR` nace con su fila de `notificaciones` y su `fuente` (#967,
    ADR-051 §B): si el trámite tiene una sola fuente la toma; si tiene varias,
    o no están declaradas, hay que indicarla. Y nace ya con su destinatario si
    se sabe (#968, §D): el primero de su fuente a quien aún falta notificar.
    `fuente` se ignora en los demás tipos. Es el único camino de creación de
    tareas de la aplicación.
    """
    res_inv = check_invariante('MUTAR', 'TRAMITE', tramite.id)
    if res_inv:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)

    if tipo_tarea.codigo == 'NOTIFICAR':
        fuente, error_fuente = dest_svc.resolver_fuente(tramite, fuente)
        if error_fuente:
            return ResultadoMutacion(ok=False, error=error_fuente)

    # Precedencia al crear (#823): el ESPERAR_PLAZO exige el NOTIFICAR del propio
    # trámite completo. Va antes de `check_orden_tarea` a propósito — aquel es el
    # vocabulario ESFTT (forzable con justificación, ADR-037 §B) y este es puerta
    # cerrada; el bloqueo que no se salta se evalúa primero.
    res_inv_crear = check_invariante('CREAR', 'TAREA', tramite.id,
                                     tipo_codigo=tipo_tarea.codigo)
    if res_inv_crear:
        return ResultadoMutacion(ok=False, bloqueo=res_inv_crear)

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
    if tipo_tarea.codigo == 'NOTIFICAR':
        notif = Notificacion(tarea_id=tarea.id, fuente=fuente, numero_intento=1)
        db.session.add(notif)
        db.session.flush()
        esperado = dest_svc.siguiente_esperado(tramite, fuente)
        if esperado is not None:
            _copiar_destinatario(tarea, notif, dest_svc.como_destinatario(esperado),
                                 origen='AL_CREAR')

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

_NO_TOCAR = object()


def validar_representante(solicitante_id: int, representante_id: Optional[int]
                          ) -> Optional[str]:
    """Error del representante de una solicitud (ADR-051 §K), o `None` si vale
    o no se indica. Tiene que ser un autorizado activo del solicitante en
    `autorizados_titular`, y no el propio solicitante. No admite escape: si la
    entidad no está autorizada, se da de alta como autorizada desde la ficha
    del titular y después se elige. La usan las tres puertas: el alta de
    expediente, `crear_solicitud` y `editar_solicitud`."""
    if representante_id is None:
        return None
    from app.models.entidad import Entidad
    from app.models.autorizados_titular import AutorizadoTitular
    if db.session.get(Entidad, representante_id) is None:
        return f'Entidad representante {representante_id} no encontrada.'
    if representante_id == solicitante_id:
        return 'El representante no puede ser el propio solicitante.'
    autorizado = AutorizadoTitular.query.filter_by(
        titular_entidad_id=solicitante_id, autorizado_entidad_id=representante_id,
        activo=True,
    ).first()
    if autorizado is None:
        return ('El representante no figura como autorizado del solicitante. Dé de alta la '
                'autorización desde la ficha del titular y vuelva a elegirlo.')
    return None


def validar_sede(solicitante_id: int, direccion_id: Optional[int]) -> Optional[str]:
    """Error de la sede de una solicitud (#989, ADR-051 §K), o `None` si vale o
    no se indica. La regla es `notificaciones.sede_invalida`; la usan las
    mismas tres puertas que `validar_representante`."""
    if direccion_id is None:
        return None
    from app.models.entidad import Entidad
    direccion = db.session.get(DireccionNotificacion, direccion_id)
    if direccion is None:
        return f'Dirección de notificación {direccion_id} no encontrada.'
    solicitante = db.session.get(Entidad, solicitante_id) if solicitante_id else None
    if solicitante is None:
        return 'La solicitud no tiene solicitante.'
    return notif_svc.sede_invalida(direccion, solicitante)


def editar_solicitud(sol, *, observaciones: Optional[str],
                     representante_entidad_id=_NO_TOCAR,
                     direccion_notificacion_id=_NO_TOCAR) -> ResultadoMutacion:
    """Observaciones, representante y sede de la solicitud (#967, #989, ADR-051
    §K). Representante y sede son opcionales; sin pasarlos no se tocan, `None`
    los quita. Solo se validan —y se avisa— cuando cambian: la ruta reenvía
    siempre el valor actual.

    Cambiarlos se admite siempre, sin bloquear (#989). Las `NOTIFICAR` al
    solicitante que aún no han salido se actualizan a la regla de §K; de las
    que ya salieron, y de los oficios que ya se prepararon con la sede
    anterior, se avisa según en qué punto estén. Nada se deshace solo: si el
    usuario quiere otra cosa, deshace lo que pueda mientras no haya salido.
    Los avisos van en `advertencia` (`motivo` es el texto para el usuario)."""
    if representante_entidad_id == sol.representante_entidad_id:
        representante_entidad_id = _NO_TOCAR
    if direccion_notificacion_id == sol.direccion_notificacion_id:
        direccion_notificacion_id = _NO_TOCAR
    cambia_representante = representante_entidad_id is not _NO_TOCAR
    cambia_sede = direccion_notificacion_id is not _NO_TOCAR

    avisos = []
    if cambia_representante:
        error = validar_representante(sol.entidad_id, representante_entidad_id)
        if error:
            return ResultadoMutacion(ok=False, error=error)
    if cambia_sede:
        error = validar_sede(sol.entidad_id, direccion_notificacion_id)
        if error:
            return ResultadoMutacion(ok=False, error=error)
    try:
        sol.observaciones = observaciones or None
        refresco = None
        if cambia_representante:
            sol.representante_entidad_id = representante_entidad_id
        if cambia_sede:
            sol.direccion_notificacion_id = direccion_notificacion_id
        if cambia_representante or cambia_sede:
            db.session.flush()
            db.session.expire(sol, ['representante', 'sede'])
            refresco = _refrescar_notificaciones_solicitante(sol)
            avisos.extend(refresco.avisos)
            if cambia_sede:
                avisos.extend(_avisos_oficios_solicitante(sol))
        db.session.commit()
        advertencia = None
        if avisos:
            advertencia = {'motivo': ' '.join(avisos), 'avisos': avisos}
            if refresco is not None:
                advertencia['refrescadas'] = refresco.refrescadas
                advertencia['ya_enviadas'] = refresco.ya_enviadas
        return ResultadoMutacion(ok=True, advertencia=advertencia)
    except Exception as e:
        db.session.rollback()
        return ResultadoMutacion(ok=False, error=str(e))


@dataclass
class _Refresco:
    refrescadas: list[int] = field(default_factory=list)
    ya_enviadas: list[int] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)


def _nombre_tramite(tramite) -> str:
    tt = tramite.tipo_tramite
    return (tt.nombre or tt.codigo) if tt else f'trámite {tramite.id}'


def _lista(nombres) -> str:
    """«A», «A y B», «A, B y C», sin repetir y en orden de aparición."""
    unicos = list(dict.fromkeys(nombres))
    return unicos[0] if len(unicos) == 1 else ', '.join(unicos[:-1]) + ' y ' + unicos[-1]


def _notificar_del_solicitante(sol):
    """Las `NOTIFICAR` de fuente `SOLICITANTE` de la solicitud, en orden."""
    for fase in sorted(sol.fases, key=lambda f: f.id):
        for tramite in sorted(fase.tramites, key=lambda t: t.id):
            for ta in sorted(tramite.tareas, key=lambda t: t.id):
                if (ta.tipo_tarea and ta.tipo_tarea.codigo == 'NOTIFICAR'
                        and ta.notificacion is not None
                        and ta.notificacion.fuente == 'SOLICITANTE'):
                    yield ta


def _refrescar_notificaciones_solicitante(sol) -> _Refresco:
    """Tras cambiar el representante o la sede (#989): las `NOTIFICAR` al
    solicitante con destinatario y sin justificante se actualizan a la regla
    de §K, y queda en bitácora (`FIJAR_DESTINATARIO`, `origen:
    'CAMBIO_SOLICITUD'`). Las que ya tienen justificante no se tocan —salieron
    así— y se cuentan si habrían cambiado. Las que no tienen destinatario
    (hueco o escape) se quedan como están: las rellena el botón. No hace
    commit. La clave de idempotencia es el solicitante, que no cambia, así que
    ninguna notificación pasa a sobrar."""
    from types import SimpleNamespace
    res = _Refresco()
    destino = notif_svc.destinatario_solicitante(sol)
    if destino is None:
        return res
    enviadas_en = []
    for ta in list(_notificar_del_solicitante(sol)):
        notif = ta.notificacion
        if notif.entidad_id is None:
            continue
        if notif_svc.tiene_justificante(ta):
            nueva = SimpleNamespace()
            notif_svc.copiar_destinatario(nueva, destino, ahora=None)
            if any(getattr(nueva, c) != getattr(notif, c) for c in _CAMPOS_DESTINATARIO):
                res.ya_enviadas.append(ta.id)
                enviadas_en.append(_nombre_tramite(ta.tramite))
            continue
        if _copiar_destinatario(ta, notif, destino, origen='CAMBIO_SOLICITUD'):
            res.refrescadas.append(ta.id)
        db.session.flush()
    if res.refrescadas:
        n = len(res.refrescadas)
        res.avisos.append(
            'Se ha actualizado la notificación al solicitante que aún no había salido.'
            if n == 1 else
            f'Se han actualizado {n} notificaciones al solicitante que aún no habían salido.')
    if res.ya_enviadas:
        res.avisos.append(
            f'La notificación de {_lista(enviadas_en)} ya salió con los datos anteriores y no '
            'se toca.' if len(res.ya_enviadas) == 1 else
            f'Las notificaciones de {_lista(enviadas_en)} ya salieron con los datos anteriores '
            'y no se tocan.')
    return res


# Estado del oficio al solicitante → aviso cuando cambia la sede (#989), en
# singular y en plural.
_AVISO_OFICIO = {
    'PENDIENTE_REDACTAR': ('El oficio de {} está en redacción: si ya tiene borrador, lleva '
                           'la dirección anterior.',
                           'Los oficios de {} están en redacción: los que ya tengan borrador '
                           'llevan la dirección anterior.'),
    'PENDIENTE_FIRMA': ('El oficio de {} está a la firma con la dirección anterior.',
                        'Los oficios de {} están a la firma con la dirección anterior.'),
    'FIRMADO': ('El oficio de {} está firmado con la dirección anterior.',
                'Los oficios de {} están firmados con la dirección anterior.'),
    'NOTIFICADO': ('El oficio de {} ya se notificó con la dirección anterior.',
                   'Los oficios de {} ya se notificaron con la dirección anterior.'),
}


def _avisos_oficios_solicitante(sol) -> list[str]:
    """Oficios al solicitante ya preparados cuando cambia la sede (#989): la
    sede es la dirección del oficio, así que el que ya se redactó la lleva
    vieja. Se avisa según su estado —en redacción, a la firma, firmado o ya
    notificado—, sin bloquear ni tocar nada. Un cambio de representante no
    afecta al oficio, que va siempre al solicitante.

    Son los `ELABORAR` de los trámites que notifican al solicitante (fuente
    `SOLICITANTE`) y de la `ELABORACION` de la resolución, que va siempre a él."""
    from app.services.estado_dominio import estado_tarea
    notificados = {doc.id for ta in _notificar_del_solicitante(sol)
                   if notif_svc.tiene_justificante(ta)
                   for doc in notif_svc.documentos_a_notificar(ta)}
    por_estado = {clave: [] for clave in _AVISO_OFICIO}
    for fase in sorted(sol.fases, key=lambda f: f.id):
        for tramite in sorted(fase.tramites, key=lambda t: t.id):
            codigo = tramite.tipo_tramite.codigo if tramite.tipo_tramite else None
            if (codigo != 'ELABORACION'
                    and 'SOLICITANTE' not in (dest_svc.fuentes_del_tramite(tramite) or ())):
                continue
            for ta in sorted(tramite.tareas, key=lambda t: t.id):
                if not (ta.tipo_tarea and ta.tipo_tarea.codigo == 'ELABORAR'):
                    continue
                estado = estado_tarea(ta)
                if estado == 'FIN':
                    doc = ta.documento_producido
                    estado = 'NOTIFICADO' if doc is not None and doc.id in notificados else 'FIRMADO'
                if estado in por_estado:
                    por_estado[estado].append(_nombre_tramite(tramite))
    avisos = []
    for estado, (singular, plural) in _AVISO_OFICIO.items():
        tramites = por_estado[estado]
        if tramites:
            texto = plural if len(tramites) > 1 else singular
            avisos.append(texto.format(_lista(tramites)))
    return avisos


def fijar_destinatario(ta, *, entidad_id: Optional[int] = None,
                       en_nombre_de_entidad_id: Optional[int] = None,
                       direccion_id: Optional[int] = None) -> ResultadoMutacion:
    """Rellena o refresca el destinatario de una `NOTIFICAR` (#967, ADR-051 §B;
    #968, §D y §H): copia en su fila entidad, representación, nombre, NIF y
    dirección.

    Con el servicio de destinatarios (#968) solo admite a quien corresponde
    notificar por la fuente de la tarea: así no nace una notificación que sobre.

    - Sin `entidad_id`: refresca la que ya tiene, o toma el primero de su fuente
      a quien aún falta notificar.
    - Con `entidad_id` (y `en_nombre_de_entidad_id` si se notifica a un
      representante): en las fuentes que se eligen en el trámite (§L) es la
      elección del usuario, que queda en `tramites_destinatario` —salvo que el
      trámite tenga ELABORAR, donde se elige al elaborar el escrito—; en las
      demás tiene que ser alguien de la fuente, y su representación la decide
      la regla de la fuente (§K), no la petición.
    - `direccion_id`, una dirección del receptor que sustituye a la de su rol.
    - Trámite sin fuentes (una `NOTIFICAR` forzada fuera de la secuencia del
      catálogo): como en #967, cualquier entidad; sin ella, solo la fuente
      `SOLICITANTE` se resuelve sola.

    Se puede cambiar o refrescar mientras la tarea no tenga ningún
    justificante; desde el primero queda fijo. Tras un escape sin destinatario
    no admite rellenarlo.
    """
    if ta.tipo_tarea.codigo != 'NOTIFICAR':
        return ResultadoMutacion(ok=False, error='Solo una tarea NOTIFICAR tiene destinatario.')
    res_inv = check_invariante('MUTAR', 'TAREA', ta.id)
    if res_inv:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)
    notif = ta.notificacion
    if notif is None:
        return ResultadoMutacion(ok=False, error='La tarea no tiene ficha de notificación.')
    if notif_svc.tuvo_escape_sin_destinatario(ta):
        return ResultadoMutacion(
            ok=False, error='Esta notificación avanzó sin destinatario por escape justificado '
                            'y ya no admite fijarlo.')
    if notif_svc.tiene_justificante(ta):
        return ResultadoMutacion(
            ok=False, error='La notificación ya tiene un justificante: su destinatario queda fijo.')

    tramite = ta.tramite
    if en_nombre_de_entidad_id is not None and en_nombre_de_entidad_id == entidad_id:
        return ResultadoMutacion(ok=False, error='Una entidad no se representa a sí misma.')

    if dest_svc.fuentes_del_tramite(tramite) is None:
        destino, error = _destino_sin_fuentes(notif, tramite, entidad_id, en_nombre_de_entidad_id)
        if error:
            return ResultadoMutacion(ok=False, error=error)
    else:
        if entidad_id is not None and dest_svc.es_elegida_en_tramite(tramite, notif.fuente):
            if dest_svc.tiene_elaborar(tramite):
                return ResultadoMutacion(
                    ok=False, error='El destinatario de este trámite se elige al elaborar su '
                                    'escrito, no en la notificación.')
            titular_id = en_nombre_de_entidad_id or entidad_id
            representante_id = entidad_id if en_nombre_de_entidad_id is not None else None
            error = _elegir_destinatario(tramite, notif.fuente, titular_id, representante_id)
            if error:
                db.session.rollback()
                return ResultadoMutacion(ok=False, error=error)
            db.session.flush()

        if entidad_id is not None:
            titular_id = en_nombre_de_entidad_id or entidad_id
            esperado = next((e for e in _esperados(tramite, notif.fuente)
                             if e.titular_id == titular_id), None)
            if esperado is None:
                etiqueta = dest_svc.ETIQUETA_FUENTE.get(notif.fuente, notif.fuente)
                return ResultadoMutacion(
                    ok=False, error=f'La entidad {titular_id} no es a quien corresponde notificar '
                                    f'como {etiqueta} en este trámite.')
        else:
            esperado = (dest_svc.esperado_de(ta)
                        or dest_svc.siguiente_esperado(tramite, notif.fuente))
            if esperado is None:
                estado = dest_svc.estado_del_tramite(tramite)
                hueco = estado.huecos.get(notif.fuente) if estado else None
                return ResultadoMutacion(
                    ok=False, error=(f'No se sabe a quién notificar: {hueco}.' if hueco else
                                     'No queda nadie a quien notificar por esta fuente.'))
        destino = dest_svc.como_destinatario(esperado)

    if direccion_id is not None:
        direccion = db.session.get(DireccionNotificacion, direccion_id)
        if direccion is None or direccion.entidad_id != destino.entidad.id:
            db.session.rollback()
            return ResultadoMutacion(
                ok=False, error='La dirección indicada no es de la entidad destinataria.')
        destino = notif_svc.Destinatario(entidad=destino.entidad,
                                         en_nombre_de=destino.en_nombre_de, direccion=direccion)

    try:
        _copiar_destinatario(ta, notif, destino, origen='MANUAL', siempre=True)
        db.session.commit()
        return ResultadoMutacion(ok=True, ids=[notif.id])
    except Exception as e:
        db.session.rollback()
        return ResultadoMutacion(ok=False, error=str(e))


def _destino_sin_fuentes(notif, tramite, entidad_id, en_nombre_de_entidad_id):
    """(Destinatario, error) de una `NOTIFICAR` en un trámite sin fuentes
    declaradas: la vía de #967, a mano."""
    from app.models.entidad import Entidad
    if entidad_id is None:
        if notif.fuente != 'SOLICITANTE':
            return None, ('Indica la entidad destinataria: solo la notificación al '
                          'solicitante se resuelve sola.')
        destino = notif_svc.destinatario_solicitante(tramite.fase.solicitud)
        if destino is None:
            return None, 'La solicitud no tiene solicitante.'
        return destino, None
    entidad = db.session.get(Entidad, entidad_id)
    if entidad is None:
        return None, f'Entidad {entidad_id} no encontrada.'
    en_nombre_de = None
    if en_nombre_de_entidad_id is not None:
        en_nombre_de = db.session.get(Entidad, en_nombre_de_entidad_id)
        if en_nombre_de is None:
            return None, f'Entidad representada {en_nombre_de_entidad_id} no encontrada.'
    return notif_svc.Destinatario(entidad=entidad, en_nombre_de=en_nombre_de,
                                  direccion=notif_svc.direccion_de_rol(entidad.id, notif.fuente)), None


def _esperados(tramite, fuente) -> list:
    estado = dest_svc.estado_del_tramite(tramite)
    return [e for e in estado.esperados if e.fuente == fuente] if estado else []


# Las columnas del destinatario en `notificaciones`: las que escribe
# `notif_svc.copiar_destinatario` y con las que se decide si algo cambió.
_CAMPOS_DESTINATARIO = ('entidad_id', 'en_nombre_de_entidad_id', 'direccion_origen_id',
                        'dest_nombre', 'dest_nif', 'dest_direccion', 'dest_codigo_postal',
                        'dest_municipio', 'dest_provincia', 'dest_email', 'dest_dir3', 'dest_sir',
                        'dest_en_nombre_de_nombre', 'dest_en_nombre_de_nif')


def _copiar_destinatario(ta, notif, destino, *, origen: str, siempre: bool = False) -> bool:
    """Copia `destino` en la fila y lo deja en bitácora si cambió algo (o
    siempre, cuando lo pide el usuario). No hace commit. Devuelve si cambió.

    Al crear la tarea (`origen='AL_CREAR'`) no se anota: el acto es crearla, y
    `crear_tarea` tampoco anota las creaciones normales."""
    from datetime import datetime, timezone
    antes = tuple(getattr(notif, c) for c in _CAMPOS_DESTINATARIO)
    notif_svc.copiar_destinatario(notif, destino, ahora=datetime.now(timezone.utc))
    cambio = antes != tuple(getattr(notif, c) for c in _CAMPOS_DESTINATARIO)
    if origen != 'AL_CREAR' and (cambio or siempre):
        bitacora_svc.registrar(
            current_user.id, 'ALTERAR', 'notificaciones', notif.id,
            detalle={
                'accion': notif_svc.ACCION_FIJAR_DESTINATARIO,
                'origen': origen,
                'entidad_id': notif.entidad_id,
                'en_nombre_de_entidad_id': notif.en_nombre_de_entidad_id,
                'direccion_origen_id': notif.direccion_origen_id,
                'sujeto': build_sujeto(ta.tramite.fase.solicitud.expediente, ta.tramite),
            },
        )
    return cambio


# `bitacora.detalle.accion` al elegir el destinatario de un trámite (§L).
ACCION_ELEGIR_DESTINATARIO = 'ELEGIR_DESTINATARIO'


def _elegir_destinatario(tramite, fuente, entidad_id, representante_id) -> Optional[str]:
    """Escribe la elección del usuario en `tramites_destinatario` (ADR-051 §L)
    y refresca las `NOTIFICAR` del trámite que aún no tienen justificante. No
    hace commit. Devuelve el error, o `None`."""
    from app.models.entidad import Entidad
    from app.models.tramites_destinatario import TramiteDestinatario

    if not dest_svc.es_elegida_en_tramite(tramite, fuente):
        return 'El destinatario de este trámite no se elige: sale de los datos del expediente.'
    entidad = db.session.get(Entidad, entidad_id)
    if entidad is None:
        return f'Entidad {entidad_id} no encontrada.'
    rol = dest_svc.ROL_ELEGIBLE.get(fuente)
    if rol == 'publicador' and not entidad.rol_publicador:
        return f'«{entidad.nombre_completo}» no tiene rol de publicador.'
    if rol == 'consultado' and not entidad.rol_consultado:
        return f'«{entidad.nombre_completo}» no tiene rol de organismo consultado.'
    if representante_id is not None:
        if representante_id == entidad_id:
            return 'Una entidad no se representa a sí misma.'
        if db.session.get(Entidad, representante_id) is None:
            return f'Entidad representante {representante_id} no encontrada.'

    fijadas = [ta for ta in tramite.tareas
               if ta.tipo_tarea and ta.tipo_tarea.codigo == 'NOTIFICAR'
               and ta.notificacion is not None and ta.notificacion.fuente == fuente
               and ta.notificacion.entidad_id is not None
               and notif_svc.tiene_justificante(ta)]
    if any((ta.notificacion.en_nombre_de_entidad_id or ta.notificacion.entidad_id) != entidad_id
           for ta in fijadas):
        return ('El trámite ya notificó a otro destinatario (tiene justificante): no se puede '
                'cambiar la elección.')

    fila = tramite.destinatario_elegido
    if fila is None:
        fila = TramiteDestinatario(tramite_id=tramite.id, entidad_id=entidad_id,
                                   representante_entidad_id=representante_id)
        db.session.add(fila)
    else:
        fila.entidad_id = entidad_id
        fila.representante_entidad_id = representante_id
    db.session.flush()
    db.session.refresh(tramite)
    bitacora_svc.registrar(
        current_user.id, 'ALTERAR', 'tramites', tramite.id,
        detalle={'accion': ACCION_ELEGIR_DESTINATARIO, 'fuente': fuente,
                 'entidad_id': entidad_id, 'representante_entidad_id': representante_id,
                 'sujeto': build_sujeto(tramite.fase.solicitud.expediente, tramite)},
    )

    for ta in sorted(tramite.tareas, key=lambda t: t.id):
        notif = ta.notificacion if ta.tipo_tarea and ta.tipo_tarea.codigo == 'NOTIFICAR' else None
        if (notif is None or notif.fuente != fuente or notif_svc.tiene_justificante(ta)
                or notif_svc.tuvo_escape_sin_destinatario(ta)):
            continue
        esperado = dest_svc.siguiente_esperado(tramite, fuente) or dest_svc.esperado_de(ta)
        if esperado is not None:
            _copiar_destinatario(ta, notif, dest_svc.como_destinatario(esperado),
                                 origen='ELECCION_TRAMITE')
            db.session.flush()
    return None


def registrar_destinatario_tramite(tramite, *, entidad_id: int,
                                   representante_entidad_id: Optional[int] = None
                                   ) -> ResultadoMutacion:
    """Guarda el destinatario que el usuario elige para un trámite (ADR-051 §L):
    desde el ELABORAR, al generar su escrito (§H), o desde su `NOTIFICAR` si no
    hay ELABORAR (`fijar_destinatario`). Solo en trámites cuya fuente se elige
    en el trámite. Refresca las `NOTIFICAR` del trámite sin justificante."""
    res_inv = check_invariante('MUTAR', 'TRAMITE', tramite.id)
    if res_inv:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)
    fuentes = dest_svc.fuentes_del_tramite(tramite) or ()
    if len(fuentes) != 1:
        return ResultadoMutacion(
            ok=False, error='Este trámite no tiene un destinatario único que elegir.')
    try:
        error = _elegir_destinatario(tramite, fuentes[0], entidad_id, representante_entidad_id)
        if error:
            db.session.rollback()
            return ResultadoMutacion(ok=False, error=error)
        db.session.commit()
        return ResultadoMutacion(ok=True, ids=[tramite.destinatario_elegido.id])
    except Exception as e:
        db.session.rollback()
        return ResultadoMutacion(ok=False, error=str(e))


@dataclass
class ResultadoPoblado:
    """Lo que hizo el botón «añadir las notificaciones que faltan» (§D)."""
    ok: bool
    creadas: list[int] = field(default_factory=list)
    rellenadas: list[int] = field(default_factory=list)
    refrescadas: list[int] = field(default_factory=list)
    pendientes: list[str] = field(default_factory=list)
    bloqueo: Optional[EvaluacionResult] = None
    error: Optional[str] = None


def anadir_notificaciones_que_faltan(tramite) -> ResultadoPoblado:
    """El botón «añadir las notificaciones que faltan» (ADR-051 §D), el mismo
    en todos los trámites. Idempotente por (trámite, fuente, titular):

    1. Refresca la dirección de las `NOTIFICAR` con destinatario y sin
       justificante (todavía no se ha enviado nada).
    2. Rellena las `NOTIFICAR` con fuente y sin entidad.
    3. Crea una `NOTIFICAR` —por `crear_tarea`, con sus guardas— para cada uno
       a quien aún falta notificar.
    4. Si falta elegir a alguien y se elige en la propia `NOTIFICAR` (trámite
       sin ELABORAR), crea una vacía para elegirlo ahí; si se elige al
       elaborar, lo dice.

    No toca las que sobran: se corrige su origen y se borran a mano (§D).
    """
    from app.models.tipos_tareas import TipoTarea

    res_inv = check_invariante('MUTAR', 'TRAMITE', tramite.id)
    if res_inv:
        return ResultadoPoblado(ok=False, bloqueo=res_inv)
    if dest_svc.fuentes_del_tramite(tramite) is None:
        return ResultadoPoblado(ok=False, error='Este trámite no notifica a nadie según el '
                                                'catálogo de fuentes.')
    resultado = ResultadoPoblado(ok=True)
    try:
        for ta in sorted(tramite.tareas, key=lambda t: t.id):
            notif = ta.notificacion if ta.tipo_tarea and ta.tipo_tarea.codigo == 'NOTIFICAR' else None
            if (notif is None or notif_svc.tiene_justificante(ta)
                    or notif_svc.tuvo_escape_sin_destinatario(ta)):
                continue
            if notif.entidad_id is not None:
                esperado = dest_svc.esperado_de(ta)
                if esperado is not None and _copiar_destinatario(
                        ta, notif, dest_svc.como_destinatario(esperado), origen='BOTON'):
                    resultado.refrescadas.append(ta.id)
            else:
                esperado = dest_svc.siguiente_esperado(tramite, notif.fuente)
                if esperado is not None:
                    _copiar_destinatario(ta, notif, dest_svc.como_destinatario(esperado),
                                         origen='BOTON')
                    resultado.rellenadas.append(ta.id)
            db.session.flush()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return ResultadoPoblado(ok=False, error=str(e))

    tipo_notificar = TipoTarea.query.filter_by(codigo='NOTIFICAR').first()
    for _ in range(1000):   # tope defensivo: cada vuelta cubre a alguien o sale
        estado = dest_svc.estado_del_tramite(tramite)
        falta = next((f for f in estado.faltan if f.titular_id is not None), None)
        if falta is None:
            break
        res = crear_tarea(tramite, tipo_notificar, fuente=falta.fuente)
        if not res.ok:
            resultado.ok = False
            resultado.bloqueo, resultado.error = res.bloqueo, res.error
            return resultado
        resultado.creadas.extend(res.ids)
        nueva = db.session.get(Tarea, res.ids[0])
        if nueva.notificacion is None or nueva.notificacion.entidad_id is None:
            # No debería ocurrir: crear_tarea la rellena con el primero que falta.
            resultado.ok = False
            resultado.error = 'La notificación creada no recibió destinatario.'
            return resultado

    estado = dest_svc.estado_del_tramite(tramite)
    for falta in [f for f in estado.faltan if f.titular_id is None]:
        vacia = any(ta.notificacion is not None and ta.notificacion.fuente == falta.fuente
                    and ta.notificacion.entidad_id is None
                    for ta in tramite.tareas if ta.tipo_tarea and ta.tipo_tarea.codigo == 'NOTIFICAR')
        if (not vacia and dest_svc.es_elegida_en_tramite(tramite, falta.fuente)
                and not dest_svc.tiene_elaborar(tramite)):
            res = crear_tarea(tramite, tipo_notificar, fuente=falta.fuente)
            if not res.ok:
                resultado.ok = False
                resultado.bloqueo, resultado.error = res.bloqueo, res.error
                return resultado
            resultado.creadas.extend(res.ids)
    resultado.pendientes = dest_svc.motivos(tramite)
    return resultado


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

    Fases finalizadoras (#956, D6): aquí solo se editan el resultado y las
    observaciones, con la fase abierta. Fijar o cambiar `documento_resultado_id`
    es puerta cerrada: se cierran con su certificado de cierre
    (`cert_cierre_fase.emitir`), que no admite escape a nivel de fase (D2).
    """
    # Sellado (#720, ADR-036 §6/§7): solo bloquea si la fase YA estaba cerrada al
    # entrar — el propio cierre (finalizada aún False → True) no se autobloquea.
    res_inv = check_invariante('MUTAR', 'FASE', fase.id)
    if res_inv:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)

    if documento_resultado_id != fase.documento_resultado_id:
        res_editor = check_cierre_finalizadora_por_editor(fase)
        if res_editor:
            return ResultadoMutacion(ok=False, bloqueo=res_editor)

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

    En una fase finalizadora (#956) reabrir es deshacer su certificado de cierre:
    delega en `cert_cierre_fase.deshacer`, que además borra el certificado y su
    documento y lo deja en bitácora. Mismos checks y mismo contrato de retorno.
    """
    if fase.tipo_fase is not None and fase.tipo_fase.es_finalizadora:
        from app.services import cert_cierre_fase
        rev = cert_cierre_fase.deshacer(fase, justificacion=justificacion)
        if rev.bloqueo is not None:
            return ResultadoMutacion(ok=False, bloqueo=rev.bloqueo)
        if not rev.ok:
            return ResultadoMutacion(ok=False, error=rev.error)
        return ResultadoMutacion(ok=True, ids=[fase.id])

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
                 notas: Optional[str],
                 justificacion: Optional[str] = None) -> ResultadoMutacion:
    """Actualiza vínculos documentales + notas de la tarea.

    `resultado` (NOTIFICAR) es una @property de Notificacion — no editable aquí.

    Una `NOTIFICAR` sin destinatario no admite vínculos nuevos, consumidos ni
    producidos (#967, ADR-051 §B), y sin producido no se da por hecha. Se fuerza
    con `justificacion`: queda en bitácora como escape sobre la tarea y desde
    entonces la tarea queda sin destinatario para siempre. Desvincular sigue
    libre. `justificacion` no fuerza nada más.

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

    deseados = {(doc_id, 'CONSUMIDO') for doc_id in dict.fromkeys(documentos_consumidos_ids)}
    if documento_producido_id:
        deseados.add((documento_producido_id, 'PRODUCIDO'))
    actuales = {(v.documento_id, v.rol): v for v in ta.vinculos_documento}

    # Sello del cumplimiento (#947, ADR-049 §F, D4): el documento que cita el
    # CERT_CUMPLIMIENTO_FASE no se desvincula ni cambia de rol (cambiar el rol es
    # quitar un vínculo y poner otro). Antes de tocar nada, para no dejar el diff a
    # medias. Añadir documentos a la tarea sigue libre: el justificante final de
    # POSTAL o NOTIFICA llega después de emitir, a esta misma tarea.
    for clave, vinculo in actuales.items():
        if clave not in deseados:
            res_sello = check_vinculo_sellado(ta, vinculo.documento)
            if res_sello:
                return ResultadoMutacion(ok=False, bloqueo=res_sello)

    escape_sin_destinatario = False
    if (deseados - set(actuales)) and notif_svc.falta_destinatario(ta):
        if not justificacion:
            return ResultadoMutacion(ok=False, bloqueo=_bloqueo_sin_destinatario())
        escape_sin_destinatario = True

    try:
        if escape_sin_destinatario:
            bitacora_svc.registrar(
                current_user.id, 'ALTERAR', 'tareas', ta.id,
                detalle={
                    'escape': True,
                    'accion': notif_svc.ACCION_SIN_DESTINATARIO,
                    'justificacion': justificacion,
                    'sujeto': build_sujeto(expediente, ta.tramite),
                },
            )
        docs_a_liberar = []
        for clave, vinculo in actuales.items():
            if clave not in deseados:
                doc = vinculo.documento
                rol_liberado = vinculo.rol
                ta.vinculos_documento.remove(vinculo)
                # #738 punto 1: desvincular un justificante no se bloquea (la
                # vinculación pudo hacerse por error), solo queda rastro. La
                # fila Notificacion la resuelve después _hook_notificar (D16 de
                # #928: se borra si no queda justificante y no hay resultado).
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
        # "vínculos resueltos → efectos derivados" del resto de la función. En
        # cada guardado de una NOTIFICAR, no solo si cambia el producido (#928):
        # los consumidos (justificantes previos) también crean o borran la fila.
        advertencia = _hook_notificar(ta)

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
