"""#1007 (ADR-050 §E) — qué se puede subir: la lista cerrada, detectada por el contenido.

Fallo silencioso que evita: un HTML o un ejecutable renombrado a `.pdf` entra y se
sirve en el navegador; un ZIP entra como un documento con varios dentro bajo una sola
fecha administrativa; o el formato que se guarda en `ficheros.formato` sale mal y con
él se sirve el contenido con un tipo equivocado.

Sin BD ni app: `formatos` solo mira bytes.
"""
import io
import zipfile

import pytest

from app.services.almacenamiento import formatos
from app.services.almacenamiento.formatos import FormatoNoAdmitido, validar_fichero

PDF = b'%PDF-1.7\n1 0 obj\n<<>>\nendobj\n%%EOF'


def _zip(entradas, *, almacenar=False):
    memoria = io.BytesIO()
    with zipfile.ZipFile(memoria, 'w', zipfile.ZIP_STORED if almacenar else zipfile.ZIP_DEFLATED) as z:
        for nombre, contenido in entradas:
            z.writestr(nombre, contenido)
    return memoria.getvalue()


def _odf(mimetype: bytes) -> bytes:
    return _zip([('mimetype', mimetype), ('content.xml', b'<x/>')], almacenar=True)


def _ooxml(*partes):
    return _zip([('[Content_Types].xml', b'<Types/>'), *[(p, b'<x/>') for p in partes]])


_ODT = _odf(b'application/vnd.oasis.opendocument.text')
_DOCX = _ooxml('word/document.xml')
_DOCM = _ooxml('word/document.xml', 'word/vbaProject.bin')
_ZIP_CUALQUIERA = _zip([('uno.pdf', PDF), ('dos.pdf', PDF)])
_CMS = b'\x30\x82\x01\x00\x06\x09\x2a\x86\x48\x86\xf7\x0d\x01\x07\x02' + b'\x00' * 20

ADMITIDOS = [
    ('informe.pdf', PDF, 'application/pdf'),
    ('INFORME.PDF', PDF, 'application/pdf'),
    ('memoria.odt', _ODT, 'application/vnd.oasis.opendocument.text'),
    ('datos.ods', _odf(b'application/vnd.oasis.opendocument.spreadsheet'),
     'application/vnd.oasis.opendocument.spreadsheet'),
    ('plano.odg', _odf(b'application/vnd.oasis.opendocument.graphics'),
     'application/vnd.oasis.opendocument.graphics'),
    ('memoria.docx', _DOCX,
     'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
    ('datos.xlsx', _ooxml('xl/workbook.xml'),
     'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
    ('foto.jpg', b'\xff\xd8\xff\xe0' + b'\x00' * 10, 'image/jpeg'),
    ('foto.jpeg', b'\xff\xd8\xff\xe0' + b'\x00' * 10, 'image/jpeg'),
    ('plano.png', b'\x89PNG\r\n\x1a\n' + b'\x00' * 10, 'image/png'),
    ('escaneo.tif', b'II*\x00' + b'\x00' * 10, 'image/tiff'),
    ('datos.xml', b'<?xml version="1.0"?><raiz/>', 'application/xml'),
    ('firma.xsig', b'\xef\xbb\xbf<?xml version="1.0"?><ds:Signature xmlns:ds="x"/>', 'application/xml'),
    ('firma.p7s', _CMS, 'application/pkcs7-signature'),
]


@pytest.mark.parametrize('nombre, contenido, mime', ADMITIDOS, ids=[a[0] for a in ADMITIDOS])
def test_reconoce_cada_formato_de_la_lista_por_su_contenido(nombre, contenido, mime):
    flujo = io.BytesIO(contenido)

    assert validar_fichero(nombre, flujo) == mime
    assert flujo.tell() == 0, 'el flujo debe quedar al principio para que se pueda enviar'


RECHAZADOS = [
    ('html renombrado a pdf', 'informe.pdf', b'<html><script>alert(1)</script></html>'),
    ('ejecutable renombrado a png', 'foto.png', b'MZ\x90\x00\x03\x00\x00\x00' + b'\x00' * 20),
    ('svg con prólogo xml', 'mapa.xml',
     b'<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg"><script/></svg>'),
    ('xhtml con prólogo xml', 'pagina.xml', b'<?xml version="1.0"?><html xmlns="x"/>'),
    ('zip con su extensión', 'proyecto.zip', _ZIP_CUALQUIERA),
    ('zip renombrado a pdf', 'informe.pdf', _ZIP_CUALQUIERA),
    ('zip renombrado a docx', 'informe.docx', _ZIP_CUALQUIERA),
    ('rar', 'proyecto.rar', b'Rar!\x1a\x07\x00' + b'\x00' * 20),
    ('zip estropeado', 'informe.pdf', b'PK\x03\x04' + b'\x00' * 30),
    ('docx con macros', 'memoria.docx', _DOCM),
    ('docm', 'memoria.docm', _DOCM),
    ('odf que no es de la lista (presentación)', 'charla.odp',
     _odf(b'application/vnd.oasis.opendocument.presentation')),
    ('pdf con extensión de docx', 'informe.docx', PDF),
    ('docx con extensión de pdf', 'informe.pdf', _DOCX),
    ('pdf sin extensión', 'informe', PDF),
    ('formato desconocido', 'notas.txt', b'texto plano sin mas'),
]


@pytest.mark.parametrize('descripcion, nombre, contenido', RECHAZADOS, ids=[r[0] for r in RECHAZADOS])
def test_rechaza_lo_que_no_es_de_la_lista_o_no_coincide_con_su_extension(descripcion, nombre, contenido):
    with pytest.raises(FormatoNoAdmitido):
        validar_fichero(nombre, io.BytesIO(contenido))


def test_un_fichero_vacio_o_por_encima_del_tamano_maximo_se_rechaza(monkeypatch):
    """El límite se comprueba fichero a fichero al recibirlo, antes de enviar nada al almacén."""
    monkeypatch.setattr(formatos, 'TAMANO_MAXIMO', len(PDF) - 1)

    with pytest.raises(FormatoNoAdmitido, match='tamaño máximo'):
        validar_fichero('informe.pdf', io.BytesIO(PDF))
    with pytest.raises(FormatoNoAdmitido, match='vacío'):
        validar_fichero('informe.pdf', io.BytesIO(b''))
