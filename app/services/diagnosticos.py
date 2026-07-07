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
