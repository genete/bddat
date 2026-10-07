"""Qué se puede subir: la lista cerrada de ADR-050 §E, detectada por el contenido.

El formato sale de los primeros bytes (y, en los que son un ZIP, de su estructura), no
de la extensión ni del MIME que declara el navegador. Si no coincide con la extensión
del nombre, se rechaza: es señal de un fichero renombrado, y la diferencia importa
porque PDF e imágenes se sirven en el navegador (§E, «Al servirlos»): un HTML
renombrado a `.pdf` podría llevar JavaScript contra la propia BDDAT.

Lo que no está en la lista no se admite (`.doc`, `.xls`, correos, texto plano, KMZ,
SHP, DWG…): ampliarla es añadir aquí su detección cuando lleguen muestras reales.
El ZIP no se admite venga de donde venga (§E): los ficheros de dentro pueden tener
fechas administrativas distintas, y cada uno tiene que ser un documento.

`validar_fichero` es lo que llama el módulo de contenido al recibir cada fichero, antes
de enviar nada al almacén. Los mensajes de `FormatoNoAdmitido` van dirigidos a quien
sube el fichero.
"""
import os
import re
import zipfile
from typing import BinaryIO, NamedTuple

from app.services.almacenamiento.nombres import sanear_nombre

# Por fichero, no por petición (ADR-050 §E, §K). El administrador podrá bajarlo desde
# la configuración (fase 7), nunca subirlo por encima del límite del despliegue.
TAMANO_MAXIMO = 300 * 1024 * 1024

_LECTURA_CABECERA = 4096


class FormatoNoAdmitido(ValueError):
    """El fichero no se puede subir. El mensaje es para el usuario."""


class _Formato(NamedTuple):
    mime: str
    extensiones: frozenset


_PDF = _Formato('application/pdf', frozenset({'.pdf'}))
_ODT = _Formato('application/vnd.oasis.opendocument.text', frozenset({'.odt'}))
_ODS = _Formato('application/vnd.oasis.opendocument.spreadsheet', frozenset({'.ods'}))
_ODG = _Formato('application/vnd.oasis.opendocument.graphics', frozenset({'.odg'}))
_DOCX = _Formato(
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    frozenset({'.docx'}))
_XLSX = _Formato(
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    frozenset({'.xlsx'}))
_JPEG = _Formato('image/jpeg', frozenset({'.jpg', '.jpeg'}))
_PNG = _Formato('image/png', frozenset({'.png'}))
_TIFF = _Formato('image/tiff', frozenset({'.tif', '.tiff'}))
# XML, XAdES (.xsig) y CAdES (.csig, .p7s): «a confirmar con muestras reales» (§E).
_XML = _Formato('application/xml', frozenset({'.xml', '.xsig'}))
_CADES = _Formato('application/pkcs7-signature', frozenset({'.csig', '.p7s'}))

# Los MIME que otros módulos reconocen al leer el contenido por el formato de su fila de
# `ficheros` (los lectores de texto: #717 y #657). Los demás se quedan privados.
MIME_PDF = _PDF.mime
MIME_ODT = _ODT.mime

# `mimetype` de la primera entrada de un ODF (ODT, ODS, ODG: lo admitido en §E).
_ODF = {
    b'application/vnd.oasis.opendocument.text': _ODT,
    b'application/vnd.oasis.opendocument.spreadsheet': _ODS,
    b'application/vnd.oasis.opendocument.graphics': _ODG,
}

_FIRMAS_ZIP = (b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08')
# RAR, 7-Zip y gzip: comprimidos que, como el ZIP, el navegador avisa por extensión
# y el servidor rechaza por contenido.
_FIRMAS_COMPRIMIDO = (b'Rar!\x1a\x07', b'7z\xbc\xaf\x27\x1c', b'\x1f\x8b')

_RE_PRIMER_ELEMENTO = re.compile(rb'<(?![?!])\s*([A-Za-z_][\w.:-]*)')
# Prefijo del OID 1.2.840.113549.1.7 (PKCS#7 / CMS) en DER.
_OID_PKCS7 = b'\x06\x09\x2a\x86\x48\x86\xf7\x0d\x01\x07'

# GEMELO EN JS: `MENSAJE` en app/static/js/subida-comprimidos.js, el aviso del
# navegador al elegir un comprimido. Si cambia uno, cambiar el otro.
_MENSAJE_COMPRIMIDO = (
    'Los ficheros comprimidos (ZIP, RAR, 7z) no se admiten: descomprímelo y sube cada '
    'documento por separado, con su fecha administrativa.')
_MENSAJE_MACROS = (
    'Los documentos de Office con macros (DOCM, XLSM) no se admiten: '
    'guárdalo sin macros y vuelve a subirlo.')
_MENSAJE_FORMATOS = (
    'Formato no admitido. Se pueden subir PDF, ODT, ODS, ODG, DOCX, XLSX, JPEG, PNG, '
    'TIFF, XML y firmas CAdES.')


class _Rechazo(NamedTuple):
    """Lo que se reconoce y no se admite, con el mensaje que le corresponde."""
    mensaje: str


def validar_fichero(nombre: str, flujo: BinaryIO) -> str:
    """Comprueba tamaño y formato de un fichero recibido y devuelve su MIME.

    `nombre` es el que llega del navegador (para la extensión); `flujo` es binario y
    con `seek`, como el temporal en que el servidor web deja la subida. Se deja
    posicionado al principio. Lanza `FormatoNoAdmitido` si no se puede subir.
    """
    flujo.seek(0, os.SEEK_END)
    tamano = flujo.tell()
    flujo.seek(0)
    if tamano == 0:
        raise FormatoNoAdmitido('El fichero está vacío.')
    if tamano > TAMANO_MAXIMO:
        raise FormatoNoAdmitido(
            f'El fichero supera el tamaño máximo de {TAMANO_MAXIMO // (1024 * 1024)} MB.')

    cabecera = flujo.read(_LECTURA_CABECERA)
    flujo.seek(0)
    try:
        detectado = _detectar(cabecera, flujo)
    finally:
        flujo.seek(0)

    if isinstance(detectado, _Rechazo):
        raise FormatoNoAdmitido(detectado.mensaje)
    if detectado is None:
        raise FormatoNoAdmitido(_MENSAJE_FORMATOS)

    # La extensión del nombre tal como se va a guardar (saneado): «informe.pdf » y
    # «informe.pdf» son el mismo fichero.
    extension = os.path.splitext(sanear_nombre(nombre))[1].lower()
    if extension not in detectado.extensiones:
        raise FormatoNoAdmitido(
            f'El contenido no es lo que dice su extensión '
            f'({extension or "sin extensión"}): ¿se ha renombrado el fichero?')
    return detectado.mime


def es_visible_en_navegador(mime: str) -> bool:
    """PDF e imágenes se muestran en el navegador; el resto se descarga (§E)."""
    return mime == _PDF.mime or mime.startswith('image/')


def _detectar(cabecera: bytes, flujo: BinaryIO):
    """`_Formato` si es de la lista, `_Rechazo` si es algo reconocible que no se
    admite, `None` si no se reconoce."""
    if cabecera.startswith(b'%PDF-'):
        return _PDF
    if cabecera.startswith(b'\xff\xd8\xff'):
        return _JPEG
    if cabecera.startswith(b'\x89PNG\r\n\x1a\n'):
        return _PNG
    if cabecera.startswith((b'II*\x00', b'MM\x00*')):
        return _TIFF
    if cabecera.startswith(_FIRMAS_ZIP):
        return _clasificar_zip(flujo)
    if cabecera.startswith(_FIRMAS_COMPRIMIDO):
        return _Rechazo(_MENSAJE_COMPRIMIDO)
    if _es_cades(cabecera):
        return _CADES
    return _clasificar_xml(cabecera)


def _clasificar_zip(flujo: BinaryIO):
    """ODF, OOXML sin macros → su formato; Office con macros y cualquier otro ZIP → rechazo."""
    try:
        with zipfile.ZipFile(flujo) as z:
            entradas = z.infolist()
            nombres = {e.filename for e in entradas}
            # ODF: `mimetype` es la primera entrada (lo exige la especificación).
            if entradas and entradas[0].filename == 'mimetype':
                # Con tope: es un dato del fichero que llega de fuera, y un ZIP que
                # declare su `mimetype` gigante no debe descomprimirse entero aquí.
                with z.open(entradas[0]) as f:
                    tipo = f.read(100).strip()
                return _ODF.get(tipo, _Rechazo(_MENSAJE_FORMATOS))
            if '[Content_Types].xml' in nombres:
                if any(n.lower().endswith('vbaproject.bin') for n in nombres):
                    return _Rechazo(_MENSAJE_MACROS)
                if 'word/document.xml' in nombres:
                    return _DOCX
                if 'xl/workbook.xml' in nombres:
                    return _XLSX
                return _Rechazo(_MENSAJE_FORMATOS)
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError):
        # Estropeado, cifrado o con un método de compresión raro: un ZIP que no es de la lista.
        pass
    return _Rechazo(_MENSAJE_COMPRIMIDO)


def _es_cades(cabecera: bytes) -> bool:
    """Una firma CMS/PKCS#7 en DER: una secuencia ASN.1 que enseguida declara el OID
    de PKCS#7. Solo el byte inicial `0x30` no basta: es también el carácter «0»."""
    return (len(cabecera) > 2 and cabecera[0] == 0x30 and cabecera[1] in (0x80, 0x81, 0x82, 0x83, 0x84)
            and _OID_PKCS7 in cabecera[:64])


def _clasificar_xml(cabecera: bytes):
    """XML (y XAdES) sí; HTML y SVG, aunque lleven prólogo XML, no: pueden llevar
    JavaScript contra la propia BDDAT (§E)."""
    sin_bom = cabecera[3:] if cabecera.startswith(b'\xef\xbb\xbf') else cabecera
    if not sin_bom.startswith(b'<?xml'):
        return None
    primero = _RE_PRIMER_ELEMENTO.search(sin_bom)
    if primero and primero.group(1).split(b':')[-1].lower() in (b'html', b'svg'):
        return _Rechazo(_MENSAJE_FORMATOS)
    return _XML
