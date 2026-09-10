"""
Generación del certificado CERT_FIN_IP_CONSULTAS.

Se emite automáticamente al crear la fase que lo necesita como habilitante
(RESOLUCION, AAU_AAUS_INTEGRADA). Verifica que las fases IP y CONSULTAS de la
solicitud estén finalizadas y deja el Documento en el pool con URI bddat://.
"""
from __future__ import annotations

import logging
from datetime import date, datetime

from app import db
from app.models.certificados import Certificado
from app.models.documentos import Documento

log = logging.getLogger(__name__)

_CODIGO = 'CERT_FIN_IP_CONSULTAS'
_FASES_HABILITANTES = ('INFORMACION_PUBLICA', 'CONSULTAS')


def crear_cert_fin_ip_consultas(expediente, solicitud, version_vigente=None) -> Certificado | None:
    """
    Genera el CERT_FIN_IP_CONSULTAS de `solicitud` para la ronda `version_vigente`,
    si no existe ya.

    Recoge las fases INFORMACION_PUBLICA y CONSULTAS de esa misma ronda que estén
    finalizadas, calcula la fecha_fin_ultima_fase y persiste Certificado + Documento
    en el pool.

    `version_vigente` es el `ReformadoProyecto` que cubre la ronda (`None` = versión
    inicial) — el mismo que ya calcula `crear_fase` con `ultimo_reformado` (R3, ADR-044
    §E) en el momento de abrir la fase que dispara este certificado. Con reformados,
    cada ronda de AAU_AAUS_INTEGRADA necesita el suyo (RESOLUCION no se repite, R5);
    sin reformados, sigue habiendo como mucho uno por solicitud (ADR-044 R5).

    Devuelve el Certificado creado, o el existente de esta solicitud+ronda si ya
    había uno. Devuelve None si no hay fases habilitantes finalizadas en esta ronda
    (no debería ocurrir si el motor validó antes).
    """
    cert_existente = _buscar_existente(solicitud.id, version_vigente)
    if cert_existente:
        return cert_existente

    fases_info = _recoger_fases(solicitud, version_vigente)
    if not fases_info:
        log.warning(
            'crear_cert_fin_ip_consultas: sin fases habilitantes finalizadas '
            'para solicitud %s, ronda %s (expediente %s)',
            solicitud.id, version_vigente.id if version_vigente else 'inicial', expediente.id
        )
        return None

    datos = _construir_datos(fases_info)

    from app.models.tipos_documentos import TipoDocumento
    tipo_doc = TipoDocumento.query.filter_by(codigo=_CODIGO).first()
    if tipo_doc is None:
        raise RuntimeError(f'TipoDocumento {_CODIGO!r} no encontrado — ¿migración aplicada?')

    fecha_fin_str = datos.get('fecha_fin_ultima_fase')
    doc = Documento(
        expediente_id=expediente.id,
        tipo_doc_id=tipo_doc.id,
        url='bddat://certificados/0',
        fecha_administrativa=date.fromisoformat(fecha_fin_str) if fecha_fin_str else None,
    )
    db.session.add(doc)
    db.session.flush()

    cert = Certificado(
        documento_id=doc.id,
        solicitud_id=solicitud.id,
        reformado_id=version_vigente.id if version_vigente else None,
        datos=datos,
        generado_en=datetime.utcnow(),
    )
    db.session.add(cert)
    db.session.flush()

    doc.url = f'bddat://certificados/{cert.id}'

    log.info(
        'CERT_FIN_IP_CONSULTAS creado: cert=%s doc=%s expediente=%s solicitud=%s ronda=%s',
        cert.id, doc.id, expediente.id, solicitud.id,
        version_vigente.id if version_vigente else 'inicial',
    )
    return cert


def _buscar_existente(solicitud_id: int, version_vigente=None) -> Certificado | None:
    """Devuelve el cert existente de esta solicitud y esta ronda, si ya fue emitido.

    Scoped por `(solicitud_id, reformado_id)` (ADR-044 R5) — antes buscaba solo por
    `expediente_id + tipo_doc_id`, así que un expediente con dos solicitudes ya
    compartía certificado por error, y una ronda nueva por reformado reutilizaba el
    de la ronda anterior en vez de re-emitir el suyo.
    """
    return (
        db.session.query(Certificado)
        .filter(
            Certificado.solicitud_id == solicitud_id,
            Certificado.reformado_id == (version_vigente.id if version_vigente else None),
        )
        .first()
    )


def _recoger_fases(solicitud, version_vigente=None) -> list[dict]:
    """Devuelve lista de {codigo, fecha_fin} para las fases habilitantes finalizadas
    de la ronda `version_vigente` (`None` = versión inicial)."""
    reformado_id = version_vigente.id if version_vigente else None
    resultado = []
    for fase in solicitud.fases:
        if not (fase.tipo_fase and fase.tipo_fase.codigo in _FASES_HABILITANTES):
            continue
        if fase.reformado_id != reformado_id:
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
