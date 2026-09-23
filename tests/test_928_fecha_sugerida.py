"""
Tests #928 (N1 §10) — fecha sugerida por tipo al subir un justificante de
Notifica al pool.

Hoy el pool autorrellena la `fecha_administrativa` de un JUSTIFICANTE_NOTIFICA
con la puesta a disposición (origen del defecto de ADR-049 §G). El servidor
decide ahora qué fecha corresponde a cada tipo (`notificaciones.fecha_sugerida`)
y `POST .../documentos/parsear_justificante` la devuelve lista para poner.

PDF sintético (reportlab) con datos ficticios, misma receta que test_655.
"""
import io
from datetime import date

import pytest
from reportlab.pdfgen import canvas

from app.services.notificaciones import fecha_sugerida
from app.services.parser_justificante_notifica import _parsear_texto

TEXTO = """\
Sistema de Notificaciones Electrónicas
Datos de la notificación
ID remesa: 82541676
ID notificación: 87718678
Destinatario: EMPRESA EJEMPLO, S.A.  Identificador: A00000000
Estados de la notificación
Puesta a disposición: 28/05/26 11:46
Estado: Leída
Fecha de lectura: 01/06/26 11:16
Generación del informe
Fecha y hora de generación: 02/06/26 07:50
"""

TEXTO_RECHAZADA = TEXTO.replace('Estado: Leída', 'Estado: Rechazada').replace(
    'Fecha de lectura: 01/06/26 11:16\n', '')


def _pdf(texto):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    y = 800
    for linea in texto.splitlines():
        c.drawString(40, y, linea)
        y -= 14
    c.save()
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Servicio
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('tipo,esperada', [
    ('JUSTIFICANTE_NOTIFICA_DISPOSICION', date(2026, 5, 28)),  # puesta a disposición
    ('JUSTIFICANTE_NOTIFICA', date(2026, 6, 1)),               # lectura, no la puesta
    ('JUSTIFICANTE_SIR', None),
    (None, None),
])
def test_fecha_sugerida_por_tipo(tipo, esperada):
    assert fecha_sugerida(tipo, _parsear_texto(TEXTO)) == esperada


def test_fecha_sugerida_notifica_rechazada_sin_fecha_de_desenlace():
    """El parser actual solo lee la fecha de lectura; en una rechazada no hay
    ninguna que proponer hasta el parser completo — nunca la puesta a disposición."""
    assert fecha_sugerida('JUSTIFICANTE_NOTIFICA', _parsear_texto(TEXTO_RECHAZADA)) is None


def test_fecha_sugerida_parseo_no_reconocido():
    assert fecha_sugerida('JUSTIFICANTE_NOTIFICA', _parsear_texto('No es un justificante.')) is None


# ---------------------------------------------------------------------------
# Endpoint del pool
# ---------------------------------------------------------------------------

def _post(cliente, expediente_id, contenido, tipo=None):
    datos = {'fichero': (io.BytesIO(contenido), 'justificante.pdf')}
    if tipo is not None:
        datos['tipo_doc_codigo'] = tipo
    return cliente.post(f'/expedientes/{expediente_id}/documentos/parsear_justificante',
                        data=datos, content_type='multipart/form-data')


@pytest.mark.parametrize('tipo,esperada', [
    ('JUSTIFICANTE_NOTIFICA_DISPOSICION', '2026-05-28'),
    ('JUSTIFICANTE_NOTIFICA', '2026-06-01'),
    (None, None),
])
def test_endpoint_devuelve_fecha_sugerida(usuario_supervisor, expediente_seed, tipo, esperada):
    r = _post(usuario_supervisor, expediente_seed, _pdf(TEXTO), tipo)

    assert r.status_code == 200, r.get_data(as_text=True)
    d = r.get_json()
    assert d['reconocido'] is True
    assert d['fecha_sugerida'] == esperada


def test_endpoint_no_reconocido_sin_fecha(usuario_supervisor, expediente_seed):
    r = _post(usuario_supervisor, expediente_seed, _pdf('Nada que ver.'), 'JUSTIFICANTE_NOTIFICA')

    assert r.status_code == 200
    assert r.get_json() == {**r.get_json(), 'reconocido': False, 'fecha_sugerida': None}
