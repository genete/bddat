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
    subsanación: su contenido ya se comunicó al titular, o una vuelta posterior lo
    superó (#714).

    `puede_escapar` distingue las dos: cerrada cuando el acto ya salió fuera y no se
    puede deshacer (notificado — LPACAP); forzable con justificación mientras todo
    queda en casa. El default del proyecto es dejar salida: obligar a justificar ya
    hace que el técnico se pare, y la justificación queda en bitácora.
    """

    def __init__(self, motivo: str, *, puede_escapar: bool):
        self.puede_escapar = puede_escapar
        super().__init__(motivo)


class MotivoIrreversible(NamedTuple):
    """Por qué no se revierte, y si el técnico puede forzarlo con justificación."""
    motivo: str
    puede_escapar: bool


def _motivo_diagnostico_superado(tarea: Tarea) -> Optional[MotivoIrreversible]:
    """Motivo por el que el diagnóstico de `tarea` ya no es reversible, o None (#714).

    Dos causas, ambas acotadas a la **cadena de subsanación**: fuera de ella los
    diagnósticos de una fase son paralelos —un `CONSULTA_SEPARATA` por organismo— y
    ninguno se apoya en otro, así que ni se superan ni se vuelcan en un requerimiento
    (mismo acotamiento que el invariante de cierre de #711, en espejo).

    1. **Ya comunicado al titular** (puerta cerrada). Existe una tarea NOTIFICAR
       posterior (por `id`, el único orden disponible) en la cadena con fila en
       `notificaciones`: el requerimiento salió y el diagnóstico es la evidencia
       congelada de lo que se le requirió. Se comprueba **primero** porque es la más
       restrictiva y lo normal es que ambas casen a la vez —hubo vuelta *porque* se
       notificó—: evaluar antes la forzable dejaría escapable un caso ya notificado.
    2. **Superado por una vuelta posterior** (forzable con justificación). No es el
       último ANALIZAR con diagnóstico de la cadena: la vuelta siguiente ya revisó lo
       mismo apoyándose en él. Se lee del mismo helper que usa `_check_cierre_fase`,
       para que lo que una regla da por superado la otra lo dé por irreversible. Aquí
       nada ha salido fuera: el camino limpio es revertir en orden inverso (la última
       vuelta primero), y el escape solo evita rehacer todo lo planificado después,
       dejando rastro en bitácora.

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
    """
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
    """
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
