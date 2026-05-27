"""
Generación on-demand de PDFs para certificados internos (bddat://).

Despacha por tipo de certificado y genera el PDF con reportlab.
Devuelve bytes — la ruta no escribe a disco (a diferencia de generador_cert.py).
"""
from __future__ import annotations

import io
import logging

log = logging.getLogger(__name__)


def generar_pdf_certificado(cert, expediente, tipo_cert: str) -> bytes:
    """
    Genera y devuelve el PDF del certificado como bytes.

    Args:
        cert:        Instancia de Certificado.
        expediente:  Instancia de Expediente.
        tipo_cert:   Código de TipoDocumento (ej: 'CERT_PLAZO_CUMPLIDO').

    Returns:
        Bytes del PDF generado.

    Lanza NotImplementedError si tipo_cert no tiene plantilla definida.
    """
    if tipo_cert == 'CERT_PLAZO_CUMPLIDO':
        return _pdf_plazo_cumplido(cert, expediente)
    if tipo_cert == 'CERT_FIN_IP_CONSULTAS':
        return _pdf_fin_ip_consultas(cert, expediente)
    raise NotImplementedError(f'Sin plantilla PDF para tipo {tipo_cert!r}')


def _pdf_plazo_cumplido(cert, expediente) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2.5 * cm, bottomMargin=2.5 * cm,
    )

    estilos = getSampleStyleSheet()
    estilo_cab = ParagraphStyle('Cab', parent=estilos['Heading2'], fontSize=10, spaceAfter=2)
    estilo_titulo = ParagraphStyle('Titulo', parent=estilos['Heading1'], fontSize=13, spaceAfter=8)
    estilo_normal = ParagraphStyle('Normal', parent=estilos['Normal'], fontSize=9, spaceAfter=3)
    estilo_pie = ParagraphStyle('Pie', parent=estilos['Normal'], fontSize=7,
                                textColor=colors.grey, spaceBefore=20)

    datos = cert.datos or {}
    numero_at = getattr(expediente, 'numero_at', '') or ''
    generado_en = cert.generado_en.strftime('%d/%m/%Y %H:%M') if cert.generado_en else ''

    fecha_venc = datos.get('fecha_vencimiento', '')
    fecha_inicio = datos.get('fecha_inicio_computo', '')
    plazo_valor = datos.get('plazo_valor', '')
    plazo_unidad = datos.get('plazo_unidad', '')
    normativa = datos.get('normativa', '')
    tipo_tramite = datos.get('tipo_tramite', '')

    _unidad_legible = {
        'DIAS_HABILES': 'días hábiles',
        'DIAS_NATURALES': 'días naturales',
        'MESES': 'meses',
        'ANOS': 'años',
    }
    unidad_str = _unidad_legible.get(str(plazo_unidad), str(plazo_unidad))

    filas_tabla = [
        ['Expediente', f'AT-{numero_at}'],
        ['Tipo de trámite', tipo_tramite],
        ['Plazo legal', f'{plazo_valor} {unidad_str}'],
        ['Normativa aplicable', normativa],
        ['Inicio del cómputo', fecha_inicio],
        ['Fecha de vencimiento', fecha_venc],
    ]

    tabla = Table(filas_tabla, colWidths=[5 * cm, 12 * cm])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))

    contenido = [
        Paragraph('Consejería de Industria, Energía y Minas', estilo_cab),
        Paragraph('Junta de Andalucía', estilo_cab),
        Spacer(1, 0.4 * cm),
        Paragraph('CERTIFICADO DE PLAZO CUMPLIDO', estilo_titulo),
        Spacer(1, 0.3 * cm),
        Paragraph(
            'El sistema BDDAT certifica que el plazo legal asociado a la tramitación '
            'del expediente indicado ha vencido conforme a los datos siguientes:',
            estilo_normal,
        ),
        Spacer(1, 0.3 * cm),
        tabla,
        Spacer(1, 0.6 * cm),
        Paragraph(
            'Este certificado ha sido generado automáticamente por el sistema de tramitación '
            'BDDAT en la fecha indicada y tiene carácter meramente informativo del estado del '
            'procedimiento.',
            estilo_normal,
        ),
        Paragraph(f'Generado: {generado_en}  ·  Certificado interno #{cert.id}', estilo_pie),
    ]

    doc.build(contenido)
    return buffer.getvalue()


def _pdf_fin_ip_consultas(cert, expediente) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2.5 * cm, bottomMargin=2.5 * cm,
    )

    estilos = getSampleStyleSheet()
    estilo_cab = ParagraphStyle('Cab', parent=estilos['Heading2'], fontSize=10, spaceAfter=2)
    estilo_titulo = ParagraphStyle('Titulo', parent=estilos['Heading1'], fontSize=13, spaceAfter=8)
    estilo_normal = ParagraphStyle('Normal', parent=estilos['Normal'], fontSize=9, spaceAfter=3)
    estilo_pie = ParagraphStyle('Pie', parent=estilos['Normal'], fontSize=7,
                                textColor=colors.grey, spaceBefore=20)

    datos = cert.datos or {}
    numero_at = getattr(expediente, 'numero_at', '') or ''
    generado_en = cert.generado_en.strftime('%d/%m/%Y %H:%M') if cert.generado_en else ''

    fases = datos.get('fases_habilitantes', [])
    fecha_fin_ultima = datos.get('fecha_fin_ultima_fase', '')

    _nombre_fase = {
        'INFORMACION_PUBLICA': 'Información Pública',
        'CONSULTAS': 'Consultas a Organismos',
    }

    filas_fases = [['Fase', 'Fecha de finalización']]
    for f in fases:
        filas_fases.append([
            _nombre_fase.get(f.get('codigo', ''), f.get('codigo', '')),
            f.get('fecha_fin') or '—',
        ])

    tabla = Table(filas_fases, colWidths=[9 * cm, 8 * cm])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f4f8')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))

    contenido = [
        Paragraph('Consejería de Industria, Energía y Minas', estilo_cab),
        Paragraph('Junta de Andalucía', estilo_cab),
        Spacer(1, 0.4 * cm),
        Paragraph('CERTIFICADO DE FIN DE INFORMACIÓN PÚBLICA Y CONSULTAS', estilo_titulo),
        Spacer(1, 0.3 * cm),
        Paragraph(f'Expediente: AT-{numero_at}', estilo_normal),
        Spacer(1, 0.3 * cm),
        Paragraph(
            'El sistema BDDAT certifica que las siguientes fases han concluido '
            'conforme al procedimiento establecido:',
            estilo_normal,
        ),
        Spacer(1, 0.3 * cm),
        tabla,
        Spacer(1, 0.4 * cm),
        Paragraph(
            f'Fecha de finalización de la última fase habilitante: {fecha_fin_ultima or "—"}',
            estilo_normal,
        ),
        Paragraph(f'Generado: {generado_en}  ·  Certificado interno #{cert.id}', estilo_pie),
    ]

    doc.build(contenido)
    return buffer.getvalue()
