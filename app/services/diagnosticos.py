"""
Servicio de producción del documento de diagnóstico de la tarea ANALIZAR (#442).

Mismo patrón que app/services/certificados.py::crear_cert — documento interno
sin fichero físico, URI bddat://diagnosticos/{id} (ADR-006). A diferencia del
certificado, el contenido (resultado + defectos) lo aporta el técnico desde el
contenedor de la tarea ANALIZAR, no se calcula aquí.
"""
from __future__ import annotations

import logging
from typing import Optional

from flask_login import current_user

from app import db
from app.models.tareas import Tarea
from app.models.documentos import Documento
from app.models.documentos_tarea import DocumentoTarea
from app.models.diagnosticos import Diagnostico
from app.services import bitacora as bitacora_svc
from app.services.mutaciones_arbol import _hook_458_analizar_separata

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


def revertir_diagnostico(tarea: Tarea) -> None:
    """
    Elimina el documento de diagnóstico producido por `tarea` (y su vínculo
    PRODUCIDO), devolviendo la tarea a "Borrador defectos" (ADR-033 §5,
    enmienda ADR-005: el diagnóstico deja de ser inmutable de por vida).

    Lanza ValueError si la tarea no tiene documento producido.
    Lanza DiagnosticoConsumidoError si el documento está CONSUMIDO por otra
    tarea — puerta cerrada, no forzable con justificación (a diferencia de
    los bloqueos de motor).
    """
    doc = tarea.documento_producido
    if doc is None:
        raise ValueError(f'La tarea {tarea.id} no tiene documento producido')

    consumidores = [v.tarea for v in doc.vinculos_tarea if v.rol == 'CONSUMIDO']
    if consumidores:
        raise DiagnosticoConsumidoError(consumidores[0])

    diagnostico = doc.diagnostico
    vinculo_producido = next(v for v in doc.vinculos_tarea if v.rol == 'PRODUCIDO')

    if diagnostico is not None:
        db.session.delete(diagnostico)
    db.session.delete(vinculo_producido)
    db.session.flush()
    db.session.delete(doc)
    db.session.commit()
    log.info('Diagnóstico revertido para tarea %s (doc %s)', tarea.id, doc.id)


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
