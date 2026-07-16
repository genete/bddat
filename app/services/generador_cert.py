"""
Generación de certificados de fase en PDF.

Usa reportlab (pure-Python, sin deps nativas) para producir el PDF.
El certificado es un snapshot inmutable de la auditoría del motor de reglas.

FLUJO:
    1. Persiste CertificadoFase (snapshot inmutable en BD).
    2. Genera PDF con reportlab.
    3. Guarda en ruta_destino_cert(expediente, tipo_cert).
    4. Crea Documento (tipo_doc = tipo_cert, url = ruta relativa a FILESYSTEM_BASE, ADR-032).
    5. Actualiza cert.ruta_pdf.
    Devuelve CertificadoFase creado.
"""
from __future__ import annotations

import logging
import os
from dataclasses import asdict
from datetime import UTC, date, datetime

log = logging.getLogger(__name__)


def generar_certificado_fase(expediente, fase, auditoria, tipo_cert: str):
    """
    Genera y persiste el certificado de fase.

    Args:
        expediente:  Instancia de Expediente.
        fase:        Instancia de Fase (ya con id — tras flush).
        auditoria:   AuditoriaResult del motor.
        tipo_cert:   Código de TipoDocumento con origen='INTERNO'
                     (ej: 'CERT_FIN_INSTRUCCION').

    Returns:
        CertificadoFase creado y con ruta_pdf rellena.
    """
    from app import db
    from app.models.certificados_fase import CertificadoFase
    from app.models.documentos import Documento
    from app.models.tipos_documentos import TipoDocumento
    from sqlalchemy.exc import OperationalError, ProgrammingError

    # 1. Serializar reglas (dataclasses → dicts)
    try:
        reglas_json = [asdict(r) for r in auditoria.reglas_evaluadas]
    except Exception:
        reglas_json = []

    # variables_ctx puede contener valores no serializables (date, etc.) → convertir
    variables_json = _serializar_variables(auditoria.variables_ctx)

    # 2. Persistir CertificadoFase (snapshot inmutable)
    cert = CertificadoFase(
        expediente_id=expediente.id,
        fase_id=fase.id if fase else None,
        tipo_cert=tipo_cert,
        fecha_generacion=datetime.now(UTC).replace(tzinfo=None),
        accion=auditoria.accion,
        sujeto=auditoria.sujeto,
        reglas_evaluadas=reglas_json,
        variables_ctx=variables_json,
    )
    db.session.add(cert)
    db.session.flush()  # obtener cert.id antes de generar el PDF

    # 3. Generar PDF
    try:
        ruta_pdf = _ruta_destino_cert(expediente, tipo_cert, cert.id)
        _generar_pdf(cert, expediente, auditoria, ruta_pdf)
    except Exception as exc:
        log.error('generador_cert: error generando PDF para %s (cert.id=%s): %s',
                  tipo_cert, cert.id, exc)
        return cert  # el cert existe aunque el PDF haya fallado

    # 4. Crear Documento apuntando al PDF
    try:
        from flask import current_app
        tipo_doc = TipoDocumento.query.filter_by(codigo=tipo_cert).first()
        # Documento.url siempre relativa a FILESYSTEM_BASE (ADR-032); cert.ruta_pdf
        # (más abajo) sigue siendo la ruta absoluta física, campo distinto.
        base = current_app.config['FILESYSTEM_BASE']
        ruta_relativa = os.path.relpath(ruta_pdf, base).replace(os.sep, '/')
        doc = Documento(
            expediente_id=expediente.id,
            tipo_doc_id=tipo_doc.id if tipo_doc else 1,
            url=ruta_relativa,
            tipo_contenido='application/pdf',
            fecha_administrativa=date.today(),
            asunto=f'Certificado {tipo_cert} — {expediente.numero_at}',
        )
        db.session.add(doc)
        db.session.flush()
    except (OperationalError, ProgrammingError) as exc:
        log.warning('generador_cert: no se pudo crear Documento para cert %s: %s', cert.id, exc)
        return cert

    # 5. Actualizar ruta_pdf en el cert
    cert.ruta_pdf = ruta_pdf
    return cert


def _ruta_destino_cert(expediente, tipo_cert: str, cert_id: int) -> str:
    """
    Ruta absoluta donde guardar el PDF del certificado.

    Estructura: FILESYSTEM_BASE / AT-{numero_at} / certificados / {tipo_cert}_{cert_id}.pdf
    """
    from flask import current_app
    base = current_app.config.get('FILESYSTEM_BASE', '')
    if not base:
        raise RuntimeError('FILESYSTEM_BASE no está configurado')

    directorio = os.path.join(base, f'AT-{expediente.numero_at}', 'certificados')
    os.makedirs(directorio, exist_ok=True)
    return os.path.join(directorio, f'{tipo_cert}_{cert_id}.pdf')


def _generar_pdf(cert, expediente, auditoria, ruta_destino: str) -> None:
    """Genera el PDF del certificado con reportlab y lo escribe en ruta_destino."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    )

    doc = SimpleDocTemplate(
        ruta_destino,
        pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2.5 * cm, bottomMargin=2.5 * cm,
    )

    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        'Titulo', parent=estilos['Heading1'], fontSize=13, spaceAfter=6
    )
    estilo_subtitulo = ParagraphStyle(
        'Subtitulo', parent=estilos['Heading2'], fontSize=10, spaceAfter=4
    )
    estilo_normal = ParagraphStyle(
        'Normal', parent=estilos['Normal'], fontSize=9, spaceAfter=3
    )
    estilo_pie = ParagraphStyle(
        'Pie', parent=estilos['Normal'], fontSize=7, textColor=colors.grey
    )

    referencia_exp = getattr(expediente, 'numero_at', '') or ''
    fecha_str = cert.fecha_generacion.strftime('%d/%m/%Y %H:%M') if cert.fecha_generacion else ''

    contenido = [
        Paragraph('Consejería de Industria, Energía y Minas', estilo_subtitulo),
        Paragraph('Junta de Andalucía', estilo_subtitulo),
        Spacer(1, 0.3 * cm),
        Paragraph(f'CERTIFICADO DE FIN DE INSTRUCCIÓN — {cert.tipo_cert}', estilo_titulo),
        Spacer(1, 0.2 * cm),
        Paragraph(f'Expediente: AT-{referencia_exp}', estilo_normal),
        Paragraph(f'Fecha de generación: {fecha_str}', estilo_normal),
        Paragraph(f'Acción auditada: {cert.accion} / Sujeto: {cert.sujeto}', estilo_normal),
        Spacer(1, 0.5 * cm),
        Paragraph(
            'El sistema BDDAT certifica que el motor de reglas evaluó todas las condiciones '
            'reglamentarias aplicables y las encontró satisfechas, autorizando la creación '
            'de la fase indicada. Las reglas evaluadas se detallan a continuación.',
            estilo_normal,
        ),
        Spacer(1, 0.5 * cm),
        Paragraph('Reglas evaluadas', estilo_subtitulo),
    ]

    # Tabla de reglas
    cabecera = [['Descripción', 'Norma', 'Efecto', 'Resultado']]
    filas = cabecera

    for regla in auditoria.reglas_evaluadas:
        if regla.disparada:
            resultado = 'NEUTRALIZADA' if regla.neutralizada else ('BLOQUEANTE' if regla.efecto == 'BLOQUEAR' else 'ADVERTENCIA')
        else:
            resultado = 'NO APLICA'
        filas.append([
            Paragraph(regla.descripcion or '—', estilo_normal),
            Paragraph(regla.norma_compilada or '—', estilo_normal),
            regla.efecto,
            resultado,
        ])

    if len(filas) == 1:
        filas.append(['(Sin reglas aplicables)', '', '', 'VERIFICADO'])

    ancho_col = [8 * cm, 5 * cm, 2.5 * cm, 2.5 * cm]
    tabla = Table(filas, colWidths=ancho_col, repeatRows=1)
    tabla.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR',    (0, 0), (-1, 0), colors.white),
        ('FONTSIZE',     (0, 0), (-1, 0), 9),
        ('FONTNAME',     (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN',        (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE',     (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f4f8')]),
        ('GRID',         (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('TOPPADDING',   (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    contenido.append(tabla)

    contenido += [
        Spacer(1, 1 * cm),
        Paragraph(
            f'Documento generado automáticamente por BDDAT el {fecha_str}. '
            'No requiere firma manual — su autenticidad se garantiza por el '
            'registro inmutable en la tabla certificados_fase.',
            estilo_pie,
        ),
    ]

    doc.build(contenido)


def _serializar_variables(variables: dict) -> dict:
    """Convierte valores no serializables (date, datetime) a str para JSON."""
    resultado = {}
    for k, v in variables.items():
        if isinstance(v, (date, datetime)):
            resultado[k] = v.isoformat()
        elif isinstance(v, (int, float, str, bool)) or v is None:
            resultado[k] = v
        else:
            resultado[k] = str(v)
    return resultado
