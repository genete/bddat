"""
Tests del parser de justificante Notifica-PNT (#655).

Los textos de muestra reproducen la estructura real de `Informe.pdf` (2
justificantes reales inspeccionados en la sesión de origen) pero con datos
ficticios — no se comiten PDFs reales con NIF/emails/teléfonos de terceros.
"""
import io

from reportlab.pdfgen import canvas

from app.services.parser_justificante_notifica import (
    parsear_justificante_notifica,
    _parsear_texto,
)

# Reproduce el caso real SIN código de expediente (la línea "Código de
# Expediente:" viene vacía, seguida de "Código de Expediente Normalizado:").
# Este es el caso que en la primera versión del parser arrastraba la palabra
# "Código" de la línea siguiente por culpa de un \s* que cruzaba el salto de
# línea — regresión cubierta aquí.
TEXTO_SIN_CODIGO_EXPEDIENTE = """\
Sistema de Notificaciones Electrónicas
Datos de la notificación
ID remesa: 82541676
ID notificación: 87718678
Remitente: Consejería de Industria, Energía y Minas
Destinatario: EMPRESA EJEMPLO, S.A.  Identificador: A00000000
Obligado a relacionarse electrónicamente: Si
Titular: EMPRESA EJEMPLO, S.A.  Id. de Titular: A00000000
Registro de salida: 202699900000000 - 28/05/2026 11:46:23
Procedimiento: 9588 - Autorización administrativa previa para instalaciones de producción
Centro directivo: A01041444 - Delegación Territorial Ejemplo
Código DIR3 del destinatario:  --- -
Asunto: Notificación de resolución
Código de Expediente:
Código de Expediente Normalizado:  ---
Emails de aviso: contacto@ejemplo.com;
Teléfonos de aviso:
Contenido de la notificación
Estados de la notificación
Puesta a disposición: 28/05/26 11:46
Estado: Leída
Fecha de lectura: 01/06/26 11:16
Leída por: EMPRESA EJEMPLO, S.A. (PUN)
Generación del informe
Fecha y hora de generación: 02/06/26 07:50
Puede verificar la integridad de una copia de este documento mediante la lectura del código QR adjunto o mediante el acceso
a la dirección https://ws050.juntadeandalucia.es/verificarFirma/ indicando el código de VERIFICACIÓN
FIRMADO POR AGENCIA DIGITAL DE ANDALUCÍA FECHA 02/06/2026
VERIFICACIÓN QFQGEJEMPLO0000000000000000 PÁGINA 1/1
"""

# Reproduce el caso real CON código de expediente relleno.
TEXTO_CON_CODIGO_EXPEDIENTE = TEXTO_SIN_CODIGO_EXPEDIENTE.replace(
    "Código de Expediente:\n", "Código de Expediente: AT-16398/26\n"
)

TEXTO_NO_RECONOCIDO = "Este documento no tiene nada que ver con Notifica-PNT.\n"


def test_parsea_estado_leida_y_deriva_resultado_correcta():
    r = _parsear_texto(TEXTO_SIN_CODIGO_EXPEDIENTE)
    assert r.estado_texto == "Leída"
    assert r.resultado == "CORRECTA"
    assert r.canal == "NOTIFICA"


def test_fechas_puesta_disposicion_y_lectura():
    r = _parsear_texto(TEXTO_SIN_CODIGO_EXPEDIENTE)
    assert r.fecha_puesta_disposicion.isoformat() == "2026-05-28T11:46:00"
    assert r.fecha_lectura.isoformat() == "2026-06-01T11:16:00"


def test_codigo_expediente_vacio_no_arrastra_linea_siguiente():
    """Regresión: 'Código de Expediente:' vacío no debe capturar
    'Código' de la línea 'Código de Expediente Normalizado:'."""
    r = _parsear_texto(TEXTO_SIN_CODIGO_EXPEDIENTE)
    assert r.codigo_expediente is None


def test_codigo_expediente_presente_se_extrae():
    r = _parsear_texto(TEXTO_CON_CODIGO_EXPEDIENTE)
    assert r.codigo_expediente == "AT-16398/26"


def test_verificacion_no_confunde_con_firmado_por():
    """Regresión: la línea de instrucciones también contiene la palabra
    'VERIFICACIÓN' sin código detrás — solo la línea final lo lleva."""
    r = _parsear_texto(TEXTO_SIN_CODIGO_EXPEDIENTE)
    assert r.verificacion == "QFQGEJEMPLO0000000000000000"


def test_campos_bonus_id_remesa_y_destinatario():
    r = _parsear_texto(TEXTO_SIN_CODIGO_EXPEDIENTE)
    assert r.id_remesa == "82541676"
    assert r.id_notificacion == "87718678"
    assert r.destinatario == "EMPRESA EJEMPLO, S.A."
    assert r.identificador_destinatario == "A00000000"


def test_texto_no_reconocido_no_lanza_excepcion_y_marca_no_reconocido():
    r = _parsear_texto(TEXTO_NO_RECONOCIDO)
    assert r.reconocido is False
    assert r.id_remesa is None
    assert r.estado_texto is None
    assert r.resultado is None


def test_to_dict_serializa_fechas_como_iso_e_incluye_reconocido():
    r = _parsear_texto(TEXTO_CON_CODIGO_EXPEDIENTE)
    d = r.to_dict()
    assert d["fecha_lectura"] == "2026-06-01T11:16:00"
    assert d["reconocido"] is True
    assert d["resultado"] == "CORRECTA"


def _generar_pdf_sintetico(lineas: list[str]) -> io.BytesIO:
    """PDF real y mínimo (no un mock) con una línea de texto por entrada,
    para probar el tramo de I/O real (pypdf.PdfReader) sin depender de un
    PDF de terceros con datos personales reales."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    y = 800
    for linea in lineas:
        c.drawString(40, y, linea)
        y -= 14
    c.save()
    buffer.seek(0)
    return buffer


def test_parsear_justificante_notifica_desde_pdf_real_sintetico():
    pdf = _generar_pdf_sintetico(TEXTO_CON_CODIGO_EXPEDIENTE.splitlines())
    r = parsear_justificante_notifica(pdf)
    assert r.reconocido is True
    assert r.resultado == "CORRECTA"
    assert r.codigo_expediente == "AT-16398/26"


def test_parsear_justificante_notifica_pdf_corrupto_no_lanza_excepcion():
    r = parsear_justificante_notifica(io.BytesIO(b"esto no es un PDF"))
    assert r.reconocido is False
