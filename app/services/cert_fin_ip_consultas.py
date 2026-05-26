"""
Generación del certificado CERT_FIN_IP_CONSULTAS.

Se emite automáticamente al crear la fase que lo necesita como habilitante
(RESOLUCION, AAU_AAUS_INTEGRADA). Verifica que las fases IP y CONSULTAS de la
solicitud estén finalizadas y deja el Documento en el pool con URI bddat://.
"""
from __future__ import annotations

import logging
from datetime import datetime

from app import db
from app.models.certificados import Certificado
from app.models.documentos import Documento

log = logging.getLogger(__name__)

_CODIGO = 'CERT_FIN_IP_CONSULTAS'
_FASES_HABILITANTES = ('INFORMACION_PUBLICA', 'CONSULTAS')


def crear_cert_fin_ip_consultas(expediente, solicitud) -> Certificado | None:
    """
    Genera el CERT_FIN_IP_CONSULTAS para la solicitud dada si no existe ya.

    Recoge las fases INFORMACION_PUBLICA y CONSULTAS finalizadas, calcula
    la fecha_fin_ultima_fase y persiste Certificado + Documento en el pool.

    Devuelve el Certificado creado, o el existente si ya había uno.
    Devuelve None si no hay fases habilitantes finalizadas (no debería ocurrir
    si el motor validó antes).
    """
    cert_existente = _buscar_existente(expediente.id, solicitud.id)
    if cert_existente:
        return cert_existente

    fases_info = _recoger_fases(solicitud)
    if not fases_info:
        log.warning(
            'crear_cert_fin_ip_consultas: sin fases habilitantes finalizadas '
            'para solicitud %s (expediente %s)', solicitud.id, expediente.id
        )
        return None

    datos = _construir_datos(fases_info)

    from app.models.tipos_documentos import TipoDocumento
    tipo_doc = TipoDocumento.query.filter_by(codigo=_CODIGO).first()
    if tipo_doc is None:
        raise RuntimeError(f'TipoDocumento {_CODIGO!r} no encontrado — ¿migración aplicada?')

    doc = Documento(
        expediente_id=expediente.id,
        tipo_doc_id=tipo_doc.id,
        url='bddat://certificados/0',
    )
    db.session.add(doc)
    db.session.flush()

    cert = Certificado(
        documento_id=doc.id,
        datos=datos,
        generado_en=datetime.utcnow(),
    )
    db.session.add(cert)
    db.session.flush()

    doc.url = f'bddat://certificados/{cert.id}'

    log.info(
        'CERT_FIN_IP_CONSULTAS creado: cert=%s doc=%s expediente=%s solicitud=%s',
        cert.id, doc.id, expediente.id, solicitud.id,
    )
    return cert


def _buscar_existente(expediente_id: int, solicitud_id: int) -> Certificado | None:
    """Devuelve el cert existente para este expediente si ya fue emitido."""
    from app.models.tipos_documentos import TipoDocumento
    tipo_doc = TipoDocumento.query.filter_by(codigo=_CODIGO).first()
    if tipo_doc is None:
        return None
    return (
        db.session.query(Certificado)
        .join(Documento, Certificado.documento_id == Documento.id)
        .filter(Documento.expediente_id == expediente_id,
                Documento.tipo_doc_id == tipo_doc.id)
        .first()
    )


def _recoger_fases(solicitud) -> list[dict]:
    """Devuelve lista de {codigo, fecha_fin} para fases habilitantes finalizadas."""
    resultado = []
    for fase in solicitud.fases:
        if not (fase.tipo_fase and fase.tipo_fase.codigo in _FASES_HABILITANTES):
            continue
        if not fase.finalizada:
            continue
        fecha_fin = None
        if fase.documento_resultado and fase.documento_resultado.fecha_administrativa:
            fecha_fin = fase.documento_resultado.fecha_administrativa.isoformat()
        resultado.append({'codigo': fase.tipo_fase.codigo, 'fase_id': fase.id,
                          'fecha_fin': fecha_fin})
    return resultado


def _construir_datos(fases_info: list[dict]) -> dict:
    """Construye el JSONB datos del certificado."""
    fechas = [f['fecha_fin'] for f in fases_info if f['fecha_fin']]
    fecha_fin_ultima = max(fechas) if fechas else None
    return {
        'fases_habilitantes': fases_info,
        'fecha_fin_ultima_fase': fecha_fin_ultima,
    }
