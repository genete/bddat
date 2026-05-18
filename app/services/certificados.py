"""
Servicio de generación de certificados internos del motor (vínculo tarea).

Crea el Documento en el pool y lo vincula como PRODUCIDO en la tarea.
La inserción en la tabla `certificados` (bddat://) queda pendiente de #425:
hasta entonces el Documento se crea con url placeholder y fecha_administrativa=NULL
(bddat:// fuerza NULL en el validador @validates, ADR-006).
"""
from __future__ import annotations

import logging
from datetime import date

from app import db
from app.models.tareas import Tarea
from app.models.documentos import Documento
from app.models.documentos_tarea import DocumentoTarea

log = logging.getLogger(__name__)

# Placeholder hasta que #425 cree la tabla certificados.
_URL_PLACEHOLDER = 'bddat://certificados/0'

_TIPO_CERT_POR_TAREA = {
    'ESPERAR_PLAZO': 'CERT_PLAZO_CUMPLIDO',
}


def crear_cert(tarea: Tarea) -> Documento:
    """
    Genera el certificado correspondiente al tipo de tarea y lo vincula
    como PRODUCIDO en la tarea dada.

    Lanza ValueError si:
    - La tarea no tiene tipo reconocido para generación de certificado.
    - La tarea ya tiene un documento producido.
    - El plazo no ha vencido aún (para ESPERAR_PLAZO).

    Lanza NotImplementedError al resolver la url (bddat://certificados) hasta #425.
    """
    tipo_tarea = tarea.tipo_tarea.codigo if tarea.tipo_tarea else None
    tipo_doc_codigo = _TIPO_CERT_POR_TAREA.get(tipo_tarea)
    if tipo_doc_codigo is None:
        raise ValueError(
            f'No hay certificado definido para tarea de tipo {tipo_tarea!r}'
        )

    if tarea.documento_producido is not None:
        raise ValueError(
            f'La tarea {tarea.id} ya tiene documento producido'
        )

    _verificar_plazo_vencido(tarea)

    tipo_doc = _obtener_tipo_documento(tipo_doc_codigo)
    expediente_id = tarea.tramite.fase.solicitud.expediente_id

    doc = Documento(
        expediente_id=expediente_id,
        tipo_doc_id=tipo_doc.id,
        url=_URL_PLACEHOLDER,
    )
    db.session.add(doc)
    db.session.flush()  # obtener doc.id antes del commit

    vinculo = DocumentoTarea(tarea_id=tarea.id, documento_id=doc.id, rol='PRODUCIDO')
    db.session.add(vinculo)

    # TODO #425: crear registro en tabla certificados y actualizar doc.url
    #            con bddat://certificados/{cert.id}

    db.session.commit()
    log.info(
        'Certificado %s creado para tarea %s (doc %s)',
        tipo_doc_codigo, tarea.id, doc.id,
    )
    return doc


def _verificar_plazo_vencido(tarea: Tarea) -> None:
    """Lanza ValueError si el plazo de la tarea ESPERAR_PLAZO no ha vencido."""
    from app.services.seguimiento import _variables_esperar_plazo
    from app.services.plazos import obtener_estado_plazo

    variables = _variables_esperar_plazo(tarea)
    ep = obtener_estado_plazo(tarea, 'TAREA', variables=variables)
    if ep.fecha_limite is None:
        raise ValueError(
            f'No se puede calcular fecha de vencimiento para tarea {tarea.id}'
        )
    if ep.estado != 'VENCIDO':
        dias = ep.dias_restantes
        msg = f'{dias} día(s)' if dias is not None else 'plazo no vencido'
        raise ValueError(
            f'El plazo de la tarea {tarea.id} aún no ha vencido ({msg})'
        )


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
