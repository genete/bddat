"""
Servicio de generación de certificados internos del motor (vínculo tarea).

Crea el Documento en el pool, inserta en la tabla certificados y vincula
el Documento como PRODUCIDO en la tarea. La URL final es bddat://certificados/{id}.
"""
from __future__ import annotations

import logging
from datetime import date, datetime

from app import db
from app.models.tareas import Tarea
from app.models.documentos import Documento
from app.models.documentos_tarea import DocumentoTarea

log = logging.getLogger(__name__)

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

    datos = _datos_plazo_vencido(tarea)

    tipo_doc = _obtener_tipo_documento(tipo_doc_codigo)
    expediente_id = tarea.tramite.fase.solicitud.expediente_id

    doc = Documento(
        expediente_id=expediente_id,
        tipo_doc_id=tipo_doc.id,
        url='bddat://certificados/0',  # placeholder hasta tener cert.id
        fecha_administrativa=date.fromisoformat(datos['fecha_vencimiento']),
    )
    db.session.add(doc)
    db.session.flush()

    from app.models.certificados import Certificado
    cert = Certificado(documento_id=doc.id, datos=datos, generado_en=datetime.utcnow())
    db.session.add(cert)
    db.session.flush()

    doc.url = f'bddat://certificados/{cert.id}'

    vinculo = DocumentoTarea(tarea_id=tarea.id, documento_id=doc.id, rol='PRODUCIDO')
    db.session.add(vinculo)

    db.session.commit()
    log.info(
        'Certificado %s creado para tarea %s (doc %s, cert %s)',
        tipo_doc_codigo, tarea.id, doc.id, cert.id,
    )
    return doc


def _datos_plazo_vencido(tarea: Tarea) -> dict:
    """
    Verifica que el plazo de la tarea ESPERAR_PLAZO ha vencido y construye
    el dict datos para el JSONB del certificado.

    Lanza ValueError si el plazo no ha vencido o no se puede calcular.
    """
    from app.services.plazos import (
        obtener_estado_plazo,
        _seleccionar_catalogo,
        _primer_consumido,
    )

    ep = obtener_estado_plazo(tarea, 'TAREA')

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

    catalogo = _seleccionar_catalogo(tarea, 'TAREA', {})

    # Dato de registro del certificado, no discriminador: qué trámite disparó la
    # espera. Se lee directo del ORM desde #785 — ya no hay dict de variables del
    # que sacarlo, porque el catálogo resuelve la posición por sí mismo.
    tipo_tramite = getattr(getattr(tarea.tramite, 'tipo_tramite', None), 'codigo', None)

    doc_inicio = _primer_consumido(tarea)
    fecha_inicio = (
        doc_inicio.fecha_administrativa.isoformat()
        if (doc_inicio and doc_inicio.fecha_administrativa)
        else None
    )

    return {
        'tarea_id': tarea.id,
        'fecha_vencimiento': ep.fecha_limite.isoformat(),
        'documento_inicio_id': doc_inicio.id if doc_inicio else None,
        'tipo_tramite': tipo_tramite,
        'normativa': catalogo.norma_origen if catalogo else None,
        'plazo_valor': catalogo.plazo_valor if catalogo else None,
        'plazo_unidad': catalogo.plazo_unidad if catalogo else None,
        'fecha_inicio_computo': fecha_inicio,
    }


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
