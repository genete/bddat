"""
Servicio de producción del documento de diagnóstico de la tarea ANALIZAR (#442).

Mismo patrón que app/services/certificados.py::crear_cert — documento interno
sin fichero físico, URI bddat://diagnosticos/{id} (ADR-006). A diferencia del
certificado, el contenido (resultado + defectos) lo aporta el técnico desde el
contenedor de la tarea ANALIZAR, no se calcula aquí.
"""
from __future__ import annotations

import logging
from typing import NamedTuple, Optional

from flask_login import current_user

from app import db
from app.models.tareas import Tarea
from app.models.documentos import Documento
from app.models.documentos_tarea import DocumentoTarea
from app.models.diagnosticos import Diagnostico
from app.services import bitacora as bitacora_svc
from app.services.mutaciones_arbol import _hook_458_analizar_separata
from app.services.invariantes_esftt import (
    TRAMITES_CADENA_SUBSANACION,
    ultima_tarea_cadena_subsanacion,
    check_invariante,
)

log = logging.getLogger(__name__)


class DiagnosticoConsumidoError(Exception):
    """El documento de diagnóstico ya está vinculado como CONSUMIDO a otra tarea
    (un ELABORAR). Puerta cerrada (ADR-033 §5): no es soslayable con
    justificación, primero hay que deshacer esa vinculación."""

    def __init__(self, tarea_consumidora: Tarea):
        self.tarea_consumidora = tarea_consumidora
        nombre_tarea = tarea_consumidora.tipo_tarea.nombre if tarea_consumidora.tipo_tarea else 'una tarea'
        nombre_tramite = (
            tarea_consumidora.tramite.tipo_tramite.nombre
            if tarea_consumidora.tramite and tarea_consumidora.tramite.tipo_tramite
            else 'otro trámite'
        )
        super().__init__(
            f'El diagnóstico ya ha sido consumido por la tarea "{nombre_tarea}" '
            f'del trámite "{nombre_tramite}" (tarea {tarea_consumidora.id}). '
            f'Deshaz esa vinculación antes de revertir el diagnóstico.'
        )


class DiagnosticoSuperadoError(Exception):
    """El diagnóstico ya ha surtido efecto aguas abajo dentro de la cadena de
    subsanación: su contenido ya se comunicó al titular, una vuelta posterior lo
    superó (#714), o ya generó un escrito de requerimiento sin notificar todavía
    (#724).

    `puede_escapar` distingue cerrado de forzable: cerrada cuando el acto ya salió
    fuera y no se puede deshacer (notificado — LPACAP); forzable con justificación
    mientras todo queda en casa (superado por vuelta posterior, o escrito elaborado/
    firmado pendiente de notificar — #724: se pierde trabajo real sin dejar rastro
    si no se para al técnico). El default del proyecto es dejar salida: obligar a
    justificar ya hace que el técnico se pare, y la justificación queda en bitácora.
    """

    def __init__(self, motivo: str, *, puede_escapar: bool):
        self.puede_escapar = puede_escapar
        super().__init__(motivo)


class FaseCerradaError(Exception):
    """La fase de la tarea está cerrada (#720, ADR-036): producir o revertir un
    diagnóstico bajo una fase sellada no es una regla de negocio forzable — la
    única vía es reabrir la fase antes (`mutaciones_arbol.reabrir_fase`)."""

    def __init__(self, motivo: str):
        super().__init__(motivo)


class MotivoIrreversible(NamedTuple):
    """Por qué no se revierte, y si el técnico puede forzarlo con justificación."""
    motivo: str
    puede_escapar: bool


def _hay_elaborar_producido_sin_notificar_en_cadena(tarea: Tarea) -> bool:
    """True si hay un ELABORAR posterior en la cadena de subsanación con documento
    ya producido (#724): el escrito de requerimiento que se apoya en este
    diagnóstico existe —redactado, quizá firmado— aunque todavía no se haya
    notificado.

    Simétrico a `_hay_notificacion_posterior_en_cadena`: mismo criterio de orden
    (`Tarea.id`, cadena de subsanación), pero mirando ELABORAR + `DocumentoTarea`
    PRODUCIDO en vez de NOTIFICAR + `Notificacion`. No comprueba si ya se notificó
    — eso lo resuelve `_hay_notificacion_posterior_en_cadena`, que se evalúa antes
    en `_motivo_diagnostico_superado` y manda si coincide (puerta cerrada gana).
    """
    from app.models.tramites import Tramite
    from app.models.tipos_tareas import TipoTarea
    from app.models.tipos_tramites import TipoTramite

    return db.session.query(
        db.session.query(Tarea.id)
        .join(Tramite, Tarea.tramite_id == Tramite.id)
        .join(TipoTarea, Tarea.tipo_tarea_id == TipoTarea.id)
        .join(TipoTramite, Tramite.tipo_tramite_id == TipoTramite.id)
        .join(DocumentoTarea, db.and_(
            DocumentoTarea.tarea_id == Tarea.id,
            DocumentoTarea.rol == 'PRODUCIDO',
        ))
        .filter(
            Tramite.fase_id == tarea.tramite.fase_id,
            Tarea.id > tarea.id,
            TipoTarea.codigo == 'ELABORAR',
            TipoTramite.codigo.in_(TRAMITES_CADENA_SUBSANACION),
        )
        .exists()
    ).scalar()


def _motivo_diagnostico_superado(tarea: Tarea) -> Optional[MotivoIrreversible]:
    """Motivo por el que el diagnóstico de `tarea` ya no es reversible, o None (#714).

    Tres causas, todas acotadas a la **cadena de subsanación**: fuera de ella los
    diagnósticos de una fase son paralelos —un `CONSULTA_SEPARATA` por organismo— y
    ninguno se apoya en otro, así que ni se superan ni se vuelcan en un requerimiento
    (mismo acotamiento que el invariante de cierre de #711, en espejo).

    1. **Ya comunicado al titular** (puerta cerrada). Existe una tarea NOTIFICAR
       posterior (por `id`, el único orden disponible) en la cadena con fila en
       `notificaciones`: el requerimiento salió y el diagnóstico es la evidencia
       congelada de lo que se le requirió. Se comprueba **primero** porque es la más
       restrictiva y lo normal es que ambas casen a la vez —hubo vuelta *porque* se
       notificó—: evaluar antes las forzables dejaría escapable un caso ya notificado.
    2. **Superado por una vuelta posterior** (forzable con justificación). No es el
       último ANALIZAR con diagnóstico de la cadena: la vuelta siguiente ya revisó lo
       mismo apoyándose en él. Se lee del mismo helper que usa `_check_cierre_fase`,
       para que lo que una regla da por superado la otra lo dé por irreversible. Aquí
       nada ha salido fuera: el camino limpio es revertir en orden inverso (la última
       vuelta primero), y el escape solo evita rehacer todo lo planificado después,
       dejando rastro en bitácora.
    3. **Progreso aguas abajo sin notificar** (forzable con justificación, #724).
       El ELABORAR de la vuelta que este diagnóstico desencadenó ya produjo el
       escrito —redactado, quizá firmado— pero aún no se ha notificado: hoy la
       reversión era libre ahí (solo confirmación destructiva) y se perdía ese
       trabajo sin rastro ni justificación. Se comprueba **después** de 1 y 2: si ya
       se notificó, manda la puerta cerrada; si hay vuelta posterior con su propio
       diagnóstico, ese es el motivo más informativo aunque este también sea cierto
       (el ELABORAR de esa vuelta posterior normalmente ya existe).

    Nota: la fila de `notificaciones` cuenta aunque `resultado` sea NULL — existe desde
    que se registra el envío (camino A de ADR-034), y `fecha_puesta_disposicion` es NOT
    NULL, de modo que su sola presencia ya significa que el escrito se puso a
    disposición.
    """
    tramite = tarea.tramite
    if tramite is None or tramite.tipo_tramite is None:
        return None
    if tramite.tipo_tramite.codigo not in TRAMITES_CADENA_SUBSANACION:
        return None

    if _hay_notificacion_posterior_en_cadena(tarea):
        return MotivoIrreversible(
            'El contenido de este diagnóstico ya se ha comunicado al titular en un '
            'requerimiento de subsanación notificado: es la evidencia congelada de lo '
            'que se le requirió y no puede deshacerse. Si el requerimiento era '
            'incorrecto, la vía es una nueva vuelta de subsanación, no borrar la '
            'evidencia.',
            puede_escapar=False,
        )

    ultima_id = ultima_tarea_cadena_subsanacion(tramite.fase_id)
    if ultima_id is not None and ultima_id != tarea.id:
        return MotivoIrreversible(
            'Este diagnóstico ha quedado superado por una vuelta de subsanación '
            'posterior, que ya revisó los mismos defectos apoyándose en él. El camino '
            'limpio es revertir antes el diagnóstico de la última vuelta; si aun así '
            'quieres revertir este, justifícalo.',
            puede_escapar=True,
        )

    if _hay_elaborar_producido_sin_notificar_en_cadena(tarea):
        return MotivoIrreversible(
            'El escrito de requerimiento que se apoya en este diagnóstico ya se ha '
            'redactado (o incluso firmado), aunque todavía no se ha notificado. '
            'Revertir el diagnóstico ahora destruye ese trabajo sin dejar rastro; si '
            'aun así quieres revertirlo, justifícalo.',
            puede_escapar=True,
        )

    return None


def motivo_bloqueo_reversion(tarea: Tarea) -> Optional[MotivoIrreversible]:
    """Por qué el diagnóstico producido de `tarea` no podría revertirse ahora
    mismo (o sería forzable), o None si es reversible sin más (#723, caso 3).

    Consultada por `api_expedientes._candado_diagnostico_producido` para
    redactar un motivo veraz cuando bloquea la mutación de un bloque con
    diagnóstico ya producido — hoy ese candado prometía "revierte el
    diagnóstico antes" incluso cuando la propia reversión estaba tan cerrada
    como la mutación. No se llama desde `revertir_diagnostico`: esa función
    sigue lanzando `DiagnosticoConsumidoError`/`DiagnosticoSuperadoError` tal
    cual estaba, sin tocar su contrato ya probado (#714).

    Mismo orden de prioridad que `revertir_diagnostico`: consumido antes que
    superado, porque es la causa más restrictiva y ambas pueden coincidir.
    Reutiliza el texto de `DiagnosticoConsumidoError` sin duplicarlo.
    """
    doc = tarea.documento_producido
    if doc is None:
        return None
    consumidores = [v.tarea for v in doc.vinculos_tarea if v.rol == 'CONSUMIDO']
    if consumidores:
        return MotivoIrreversible(str(DiagnosticoConsumidoError(consumidores[0])), puede_escapar=False)
    return _motivo_diagnostico_superado(tarea)


# =============================================================================
# Punto 2 (#724): modificar un check ya exigido en una vuelta notificada
# =============================================================================

_ETIQUETA_ORIGEN_CHECK = {
    'documental': 'este requisito documental',
    'tecnico': 'este ítem técnico',
    'requerimiento': 'este requerimiento',
}


def motivo_check_ya_exigido(origen: str, texto: str) -> str:
    """Mensaje del 422 forzable cuando se toca un check que ya figuraba en un
    diagnóstico notificado de una vuelta anterior (#724, criterio acordado con
    Carlos: "no son solo dos vueltas" — ver
    `invariantes_esftt.diagnosticos_notificados_cadena`, que recorre toda la
    cadena y se queda con la primera coincidencia, la vuelta notificada más
    reciente).

    Cubre la transición hacia el defecto (no-defecto → defecto): algo que se dio
    por corregido o por bueno y ahora se vuelve a marcar como pendiente. Tocar un
    ítem que sigue pendiente sin cambiar de sentido, o resolver uno pendiente, no
    pasa por aquí — no hay nada de lo que desdecirse.
    """
    etiqueta = _ETIQUETA_ORIGEN_CHECK.get(origen, 'este ítem')
    return (
        f'Se está volviendo a exigir {etiqueta} ya exigido y dado por corregido: '
        f'«{texto}». Debes justificar por qué se exige de nuevo.'
    )


def motivo_check_ya_exigido_lote(items: list) -> str:
    """Como `motivo_check_ya_exigido` pero para varios ítems tocados en una sola
    llamada (#724): solo `post_requerimientos` puede mutar varios a la vez —
    reemplaza la lista completa del shuttle en un único POST. `items` es una
    lista de textos ya afectados.
    """
    if len(items) == 1:
        return motivo_check_ya_exigido('requerimiento', items[0])
    listado = ', '.join(f'«{t}»' for t in items)
    return (
        f'Se están volviendo a exigir {len(items)} requerimientos ya exigidos y '
        f'dados por corregidos: {listado}. Debes justificar por qué se exigen de nuevo.'
    )


_CLAVE_ID_POR_ORIGEN = {'documental': 'requisito_id', 'tecnico': 'item_tecnico_id'}


def diagnostico_donde_se_exigio_item(tarea: Tarea, origen: str, item_id: int) -> Optional[dict]:
    """Defecto congelado (dict de `Diagnostico.defectos`) de la vuelta notificada
    más reciente de la cadena que ya exigía este ítem documental/técnico, o None
    (#724). `origen` ∈ {'documental', 'tecnico'} — el libre usa
    `diagnostico_donde_se_exigio_requerimiento` (su id no es estable, ver
    consolidacion_defectos._items_requerimiento).

    Fuera de la cadena de subsanación (paralelos, #711) no hay "vuelta anterior"
    de la que desdecirse: no aplica.
    """
    from app.services.invariantes_esftt import diagnosticos_notificados_cadena

    tramite = tarea.tramite
    if tramite is None or tramite.tipo_tramite is None:
        return None
    if tramite.tipo_tramite.codigo not in TRAMITES_CADENA_SUBSANACION:
        return None

    clave = _CLAVE_ID_POR_ORIGEN[origen]
    for diagnostico in diagnosticos_notificados_cadena(tramite):
        for defecto in (diagnostico.defectos or []):
            if defecto.get('origen') == origen and defecto.get(clave) == item_id:
                return defecto
    return None


def diagnostico_donde_se_exigio_requerimiento(
    tarea: Tarea, *, catalogo_requerimientos_id: Optional[int], texto: str,
) -> Optional[dict]:
    """Como `diagnostico_donde_se_exigio_item` pero para el eje de requerimientos
    libres (#724): la fila de `RequerimientoTarea` se borra y recrea entera en
    cada guardado del shuttle, así que su id no sirve de emparejamiento estable
    (ver nota en `consolidacion_defectos._items_requerimiento`). Empareja por
    `catalogo_requerimientos_id` cuando lo hay; si es texto libre (sin id de
    catálogo), por coincidencia exacta de texto — misma degradación ya aceptada
    para diagnósticos anteriores a #724 sin estos ids.
    """
    from app.services.invariantes_esftt import diagnosticos_notificados_cadena

    tramite = tarea.tramite
    if tramite is None or tramite.tipo_tramite is None:
        return None
    if tramite.tipo_tramite.codigo not in TRAMITES_CADENA_SUBSANACION:
        return None

    for diagnostico in diagnosticos_notificados_cadena(tramite):
        for defecto in (diagnostico.defectos or []):
            if defecto.get('origen') != 'requerimiento':
                continue
            if catalogo_requerimientos_id is not None:
                if defecto.get('catalogo_requerimientos_id') == catalogo_requerimientos_id:
                    return defecto
            elif defecto.get('catalogo_requerimientos_id') is None and defecto.get('texto') == texto:
                return defecto
    return None


def _hay_notificacion_posterior_en_cadena(tarea: Tarea) -> bool:
    """True si en la cadena de subsanación de la fase hay una tarea NOTIFICAR posterior
    a `tarea` con notificación registrada.

    "Posterior" por `Tarea.id`, no por trámite: dentro de un mismo
    `REQUERIMIENTO_SUBSANACION` el NOTIFICAR es anterior al ANALIZAR —notifica el
    requerimiento de esa vuelta y se apoya en el diagnóstico de la vuelta ANTERIOR—,
    de modo que comparar por `id` de tarea distingue los dos casos sin más reglas.

    Supuesto conocido: el `id` refleja el orden del patrón FTT (`tramites_tareas.orden`)
    porque las tareas se crean siguiéndolo, no porque nada lo garantice — hoy la creación
    no consulta ese orden (#719). Si se creara el ANALIZAR antes que su NOTIFICAR, este
    check bloquearía de más. Cuando #719 aterrice, el criterio podrá apoyarse en el orden
    canónico en lugar del `id`.
    """
    from app.models.tramites import Tramite
    from app.models.tipos_tareas import TipoTarea
    from app.models.tipos_tramites import TipoTramite
    from app.models.notificaciones import Notificacion

    return db.session.query(
        db.session.query(Notificacion.id)
        .join(Tarea, Notificacion.tarea_id == Tarea.id)
        .join(Tramite, Tarea.tramite_id == Tramite.id)
        .join(TipoTarea, Tarea.tipo_tarea_id == TipoTarea.id)
        .join(TipoTramite, Tramite.tipo_tramite_id == TipoTramite.id)
        .filter(
            Tramite.fase_id == tarea.tramite.fase_id,
            Tarea.id > tarea.id,
            TipoTarea.codigo == 'NOTIFICAR',
            TipoTramite.codigo.in_(TRAMITES_CADENA_SUBSANACION),
        )
        .exists()
    ).scalar()


def revertir_diagnostico(tarea: Tarea, *, justificacion: Optional[str] = None) -> None:
    """
    Elimina el documento de diagnóstico producido por `tarea` (y su vínculo
    PRODUCIDO), devolviendo la tarea a "Borrador defectos" (ADR-033 §5,
    enmienda ADR-005: el diagnóstico deja de ser inmutable de por vida).

    Lanza ValueError si la tarea no tiene documento producido.
    Lanza DiagnosticoConsumidoError si el documento está CONSUMIDO por otra
    tarea — puerta cerrada, no forzable con justificación (a diferencia de
    los bloqueos de motor). ADR-033 §5 lo fija así porque hay una acción
    concreta a mano: deshacer esa vinculación.
    Lanza DiagnosticoSuperadoError si el diagnóstico ya surtió efecto dentro de
    la cadena de subsanación (#714): el check de CONSUMIDO por sí solo no
    protege nada mientras nada cree ese vínculo (#717).

    `justificacion`: vía de escape de los bloqueos forzables de
    `_motivo_diagnostico_superado` (mismo shape que los bloqueos de motor y que
    el gate de completitud de `crear_diagnostico`) — se registra en bitácora. No
    abre las puertas cerradas: lo ya notificado sigue sin poder revertirse.

    Lanza FaseCerradaError si la fase de la tarea está cerrada (#720): no
    bypasseable con `justificacion`, la única vía es reabrir la fase antes.
    """
    res_inv = check_invariante('MUTAR', 'TAREA', tarea.id)
    if res_inv is not None:
        raise FaseCerradaError(res_inv.motivo or res_inv.norma_compilada)

    doc = tarea.documento_producido
    if doc is None:
        raise ValueError(f'La tarea {tarea.id} no tiene documento producido')

    consumidores = [v.tarea for v in doc.vinculos_tarea if v.rol == 'CONSUMIDO']
    if consumidores:
        raise DiagnosticoConsumidoError(consumidores[0])

    bloqueo = _motivo_diagnostico_superado(tarea)
    if bloqueo is not None and not (bloqueo.puede_escapar and justificacion):
        raise DiagnosticoSuperadoError(bloqueo.motivo, puede_escapar=bloqueo.puede_escapar)

    diagnostico = doc.diagnostico
    vinculo_producido = next(v for v in doc.vinculos_tarea if v.rol == 'PRODUCIDO')

    if diagnostico is not None:
        db.session.delete(diagnostico)
    db.session.delete(vinculo_producido)
    db.session.flush()
    db.session.delete(doc)

    if bloqueo is not None:
        # Solo se llega aquí con bloqueo forzado: la reversión pasa por encima de una
        # salvaguarda y eso se audita. 'ALTERAR' por el mismo motivo que en
        # crear_diagnostico — ck_bitacora_operacion no admite otra cosa y lo que cambia
        # es el estado de la tarea, no una creación.
        bitacora_svc.registrar(
            current_user.id, 'ALTERAR', 'tareas', tarea.id,
            detalle={'escape': True, 'justificacion': justificacion,
                     'motivo': bloqueo.motivo},
        )

    db.session.commit()
    log.info('Diagnóstico revertido para tarea %s (doc %s)%s',
             tarea.id, doc.id, ' [forzado con justificación]' if bloqueo else '')


def crear_diagnostico(tarea: Tarea, resultado: str, defectos: list,
                       *, justificacion: Optional[str] = None) -> Documento:
    """
    Produce el documento de diagnóstico de una tarea ANALIZAR y lo vincula
    como PRODUCIDO.

    Un solo tiro por tarea: lanza ValueError si `tarea.documento_producido`
    ya existe (mismo criterio que crear_cert). `defectos` es la foto
    congelada del consolidado en el momento de producir (ver
    consolidacion_defectos.consolidar_defectos) — no se recalcula después.

    `justificacion`: vía de escape del gate de completitud (mismo shape que
    los bloqueos de motor en mutaciones_arbol.py) — si se informa, se
    registra en bitácora con detalle {'escape': True, 'justificacion': ...}.
    La decisión de exigirla (completo=False) la toma el llamador (ruta).

    Lanza FaseCerradaError si la fase de la tarea está cerrada (#720): no
    bypasseable con `justificacion`, la única vía es reabrir la fase antes.
    """
    res_inv = check_invariante('MUTAR', 'TAREA', tarea.id)
    if res_inv is not None:
        raise FaseCerradaError(res_inv.motivo or res_inv.norma_compilada)

    if tarea.documento_producido is not None:
        raise ValueError(f'La tarea {tarea.id} ya tiene documento producido')

    tipo_doc = _obtener_tipo_documento('DIAGNOSTICO')
    expediente_id = tarea.tramite.fase.solicitud.expediente_id

    doc = Documento(
        expediente_id=expediente_id,
        tipo_doc_id=tipo_doc.id,
        url='bddat://diagnosticos/0',  # placeholder hasta tener diagnostico.id
    )
    db.session.add(doc)
    db.session.flush()

    diagnostico = Diagnostico(documento_id=doc.id, resultado=resultado, defectos=defectos)
    db.session.add(diagnostico)
    db.session.flush()

    doc.url = f'bddat://diagnosticos/{diagnostico.id}'

    vinculo = DocumentoTarea(tarea_id=tarea.id, documento_id=doc.id, rol='PRODUCIDO')
    db.session.add(vinculo)

    _hook_458_analizar_separata(tarea, doc.id)

    if justificacion:
        # ck_bitacora_operacion solo admite CREAR/BORRAR/ALTERAR (001_bitacora.py).
        # Fijar el resultado saltando el gate de completitud es una alteración de
        # la tarea, no una creación — 'ALTERAR', igual que el resto del cuaderno.
        bitacora_svc.registrar(
            current_user.id, 'ALTERAR', 'tareas', tarea.id,
            detalle={'escape': True, 'justificacion': justificacion},
        )

    db.session.commit()
    log.info(
        'Diagnóstico producido para tarea %s (doc %s, diagnostico %s, resultado %s)',
        tarea.id, doc.id, diagnostico.id, resultado,
    )
    return doc


def _obtener_tipo_documento(codigo: str):
    from app.models.tipos_documentos import TipoDocumento
    from sqlalchemy.exc import OperationalError, ProgrammingError
    try:
        td = TipoDocumento.query.filter_by(codigo=codigo).first()
        if td is None:
            raise ValueError(f'TipoDocumento {codigo!r} no encontrado en catálogo')
        return td
    except (OperationalError, ProgrammingError) as exc:
        raise RuntimeError(f'BD no disponible al buscar TipoDocumento: {exc}') from exc
