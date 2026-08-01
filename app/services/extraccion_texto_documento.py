"""
Extracción de texto plano de un Documento local para buscar el código de
seguimiento embebido (#182), usado por #717 (vínculo CONSUMIDO del ELABORAR)
y en el futuro por #181 (preclasificación al incorporar).

RESPONSABILIDAD:
    Dado un Documento con fichero local, devolver su texto renderizado —
    nunca lanza: un formato no soportado, un fichero corrupto o una URL
    externa/bddat:// (sin fichero físico) devuelven cadena vacía, igual que
    `extraer_tarea_id('')` ya trata como "sin código" (codigo_seguimiento.py).

FORMATOS SOPORTADOS:
    .pdf — pypdf (ya dependencia, usado en tests/test_182_codigo_seguimiento.py)
    .odt — content.xml + styles.xml, todo el texto (el código vive en el pie,
           ver generador_escritos_odt.py::_inyectar_codigo). `itertext()` no
           necesita namespaces: basta con concatenar el texto de cada nodo.
    Cualquier otro formato (.docx incluido — R10: sus metadatos no sobreviven
    y su texto no lleva el código) devuelve ''.
"""
from __future__ import annotations

import logging
import zipfile

from lxml import etree

log = logging.getLogger(__name__)


def extraer_texto(doc) -> str:
    """Texto plano del fichero local de `doc`, o '' si no es extraíble."""
    url = doc.url or ''
    if '://' in url:
        return ''  # bddat:// o http(s):// — sin fichero físico que leer

    try:
        ruta = doc.ruta_absoluta()
    except ValueError:
        return ''

    ruta_lower = ruta.lower()
    if ruta_lower.endswith('.pdf'):
        return _extraer_pdf(ruta)
    if ruta_lower.endswith('.odt'):
        return _extraer_odt(ruta)
    return ''


def _extraer_pdf(ruta: str) -> str:
    try:
        import pypdf
        lector = pypdf.PdfReader(ruta)
        return '\n'.join(p.extract_text() or '' for p in lector.pages)
    except Exception:
        log.warning('No se pudo extraer texto del PDF %s', ruta, exc_info=True)
        return ''


def _extraer_odt(ruta: str) -> str:
    try:
        with zipfile.ZipFile(ruta) as z:
            partes = [z.read(n) for n in ('content.xml', 'styles.xml') if n in z.namelist()]
        trozos = []
        for parte in partes:
            root = etree.fromstring(parte)
            trozos.append(''.join(root.itertext()))
        return '\n'.join(trozos)
    except Exception:
        log.warning('No se pudo extraer texto del ODT %s', ruta, exc_info=True)
        return ''
