"""
Generación de certificados de fase en PDF.

Usa reportlab (pure-Python, sin deps nativas) para producir el PDF.
El certificado es un snapshot inmutable de la auditoría del motor de reglas.

FLUJO:
    1. Persiste CertificadoFase (snapshot inmutable en BD).
    2. Genera PDF con reportlab.
    3. Guarda en ruta_destino_cert(expediente, tipo_cert).
    4. Crea Documento (tipo_doc = tipo_cert, url = ruta relativa a FILESYSTEM_BASE, ADR-032),
       o completa el que el llamador ya creó (parámetro `documento`).
    5. Actualiza cert.ruta_pdf.
    Devuelve CertificadoFase creado.

DOS MODOS DE LLAMADA (#827):
    - Sin `documento`: el generador lo crea al final. Es el modo original (#373).
    - Con `documento`: el llamador lo creó antes y el generador solo lo completa.
      Lo necesita el emisor del CERT_FIN_INSTRUCCION, que tiene que anclar el
      Documento a la solicitud ANTES de auditar — si audita antes, la regla del
      art. 82.1 dispara (el certificado aún no consta) y el snapshot que este
      módulo congela saldría bloqueado por la propia regla que el certificado
      levanta. Ver app/services/cert_fin_instruccion.py.
"""
from __future__ import annotations

import logging
import os
from dataclasses import asdict
from datetime import UTC, date, datetime

log = logging.getLogger(__name__)


def generar_certificado_fase(expediente, fase, auditoria, tipo_cert: str, *,
                             documento=None, solicitud=None):
    """
    Genera y persiste el certificado de fase.

    Args:
        expediente:  Instancia de Expediente.
        fase:        Instancia de Fase (ya con id — tras flush), o None cuando el
                     certificado no es de una fase concreta: el CERT_FIN_INSTRUCCION
                     certifica la instrucción completa y se ancla a la solicitud
                     (ADR-043 §D), así que deja `CertificadoFase.fase_id` NULL.
        auditoria:   AuditoriaResult del motor.
        tipo_cert:   Código de TipoDocumento con origen='INTERNO'
                     (ej: 'CERT_FIN_INSTRUCCION').
        documento:   Documento ya creado por el llamador, que este servicio
                     completa (url, tipo de contenido, asunto) en vez de crear uno
                     nuevo. Ver el encabezado del módulo.
        solicitud:   Solicitud a la que pertenece el certificado, para identificarla
                     en el PDF. Sin ella el PDF solo nombra el expediente, que no
                     basta cuando tiene más de una solicitud.

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
        _generar_pdf(cert, expediente, auditoria, ruta_pdf, solicitud=solicitud)
    except Exception as exc:
        log.error('generador_cert: error generando PDF para %s (cert.id=%s): %s',
                  tipo_cert, cert.id, exc)
        return cert  # el cert existe aunque el PDF haya fallado

    # 4. Crear (o completar) el Documento que apunta al PDF
    try:
        from flask import current_app
        tipo_doc = TipoDocumento.query.filter_by(codigo=tipo_cert).first()
        # Documento.url siempre relativa a FILESYSTEM_BASE (ADR-032); cert.ruta_pdf
        # (más abajo) sigue siendo la ruta absoluta física, campo distinto.
        base = current_app.config['FILESYSTEM_BASE']
        ruta_relativa = os.path.relpath(ruta_pdf, base).replace(os.sep, '/')
        asunto = f'Certificado {tipo_cert} — {expediente.numero_at}'
        if documento is None:
            doc = Documento(
                expediente_id=expediente.id,
                tipo_doc_id=tipo_doc.id if tipo_doc else 1,
                url=ruta_relativa,
                tipo_contenido='application/pdf',
                fecha_administrativa=date.today(),
                asunto=asunto,
            )
            db.session.add(doc)
        else:
            # El llamador lo creó con url placeholder para poder anclarlo antes de
            # auditar; aquí recibe su destino real y los campos que solo se conocen
            # una vez generado el PDF.
            doc = documento
            doc.url = ruta_relativa
            doc.tipo_contenido = 'application/pdf'
            if doc.fecha_administrativa is None:
                doc.fecha_administrativa = date.today()
            if not doc.asunto:
                doc.asunto = asunto
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


def _generar_pdf(cert, expediente, auditoria, ruta_destino: str, *, solicitud=None) -> None:
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

    # Encabezado del certificado: el nombre real del tipo documental, no un
    # literal fijo — el generador tiene ya dos tipos de certificado que emitir y
    # heredará más, y ninguno debe salir con el título de otro.
    titulo = _titulo_cert(cert.tipo_cert)

    # El certificado es de una solicitud concreta (ADR-043 §D): sin nombrarla, dos
    # solicitudes del mismo expediente producirían PDFs indistinguibles.
    identificacion = [Paragraph(f'Expediente: AT-{referencia_exp}', estilo_normal)]
    if solicitud is not None:
        tipo_sol = getattr(solicitud, 'tipo_solicitud', None)
        siglas = getattr(tipo_sol, 'siglas', None) or 'sin tipo'
        identificacion.append(
            Paragraph(f'Solicitud: #{solicitud.id} — {siglas}', estilo_normal)
        )

    # Afirmación acorde con lo que la auditoría dice de verdad: si alguna regla
    # bloqueante quedó sin neutralizar, el certificado lo hace constar en vez de
    # declarar satisfecho lo que no lo está.
    if getattr(auditoria, 'permitido', True):
        declaracion = (
            'El sistema BDDAT certifica que el motor de reglas evaluó todas las condiciones '
            'reglamentarias aplicables y las encontró satisfechas. Las reglas evaluadas se '
            'detallan a continuación.'
        )
    else:
        declaracion = (
            'El sistema BDDAT deja constancia de las condiciones reglamentarias evaluadas por '
            'el motor de reglas en el momento de emitir este certificado. Alguna de ellas '
            'quedó sin satisfacer y se detalla como BLOQUEANTE en el cuadro siguiente.'
        )

    contenido = [
        Paragraph('Consejería de Industria, Energía y Minas', estilo_subtitulo),
        Paragraph('Junta de Andalucía', estilo_subtitulo),
        Spacer(1, 0.3 * cm),
        Paragraph(titulo, estilo_titulo),
        Spacer(1, 0.2 * cm),
        *identificacion,
        Paragraph(f'Fecha de generación: {fecha_str}', estilo_normal),
        Paragraph(f'Acción auditada: {cert.accion} / Sujeto: {cert.sujeto}', estilo_normal),
        Spacer(1, 0.5 * cm),
        Paragraph(declaracion, estilo_normal),
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


def _titulo_cert(tipo_cert: str) -> str:
    """Título del PDF: el nombre del TipoDocumento en mayúsculas, o el código si
    el catálogo no lo tiene (o la BD no está disponible al generarlo)."""
    from app.models.tipos_documentos import TipoDocumento
    from sqlalchemy.exc import OperationalError, ProgrammingError
    try:
        tipo_doc = TipoDocumento.query.filter_by(codigo=tipo_cert).first()
    except (OperationalError, ProgrammingError):
        tipo_doc = None
    nombre = (tipo_doc.nombre if tipo_doc else None) or tipo_cert
    return nombre.upper()


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
