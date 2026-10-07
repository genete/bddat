"""
Extracción de texto plano del contenido de un Documento para buscar el código de
seguimiento embebido (#182), usado por #717 (vínculo CONSUMIDO del ELABORAR)
y en el futuro por #181 (preclasificación al incorporar).

RESPONSABILIDAD:
    Dado un Documento, devolver su texto renderizado. El contenido se lo pide al
    módulo de contenido (ADR-050) y el formato lo decide el de la fila de `ficheros`,
    no la extensión del nombre.

    Devuelve cadena vacía, igual que `extraer_tarea_id('')` ya trata como "sin código"
    (codigo_seguimiento.py), cuando el documento no tiene nada que leer (un enlace
    http(s):// o un documento bddat://), cuando su formato no se soporta, o cuando un
    PDF u ODT no se puede interpretar (corrupto).

    **No devuelve '' cuando falla el almacén**: `AlmacenNoDisponible` (no contesta) y
    `ContenidoNoUtilizable` (ausente o dañado) se propagan. Devolver '' haría creer que
    el escrito no lleva el código, y #717 lo avisaría en falso sin derivar el vínculo.
    Por eso la lectura va fuera de los `try` de abajo: las funciones que interpretan el
    texto reciben bytes y no ven el almacén, así que no pueden tragarse ese error.

FORMATOS SOPORTADOS:
    PDF — pypdf (ya dependencia, usado en tests/test_182_codigo_seguimiento.py)
    ODT — content.xml + styles.xml, todo el texto (el código vive en el pie,
          ver generador_escritos_odt.py::_inyectar_codigo). `itertext()` no
          necesita namespaces: basta con concatenar el texto de cada nodo.
    Cualquier otro formato (DOCX incluido — R10: sus metadatos no sobreviven
    y su texto no lleva el código) devuelve ''.
"""
from __future__ import annotations

import io
import logging
import zipfile

from lxml import etree

from app.services.almacenamiento import contenido
from app.services.almacenamiento.formatos import MIME_ODT, MIME_PDF

log = logging.getLogger(__name__)


def extraer_texto(doc) -> str:
    """Texto plano del contenido de `doc`, o '' si no es extraíble."""
    if not contenido.tiene_contenido_propio(doc):
        return ''  # bddat:// o http(s):// — sin contenido que leer

    leido = contenido.leer(doc)  # AlmacenNoDisponible y ContenidoNoUtilizable se propagan
    if leido.formato == MIME_PDF:
        return _extraer_pdf(leido.datos, leido.nombre_fichero)
    if leido.formato == MIME_ODT:
        return _extraer_odt(leido.datos, leido.nombre_fichero)
    return ''


def _extraer_pdf(datos: bytes, nombre: str) -> str:
    try:
        import pypdf
        lector = pypdf.PdfReader(io.BytesIO(datos))
        return '\n'.join(p.extract_text() or '' for p in lector.pages)
    except Exception:
        log.warning('No se pudo extraer texto del PDF %s', nombre, exc_info=True)
        return ''


def _extraer_odt(datos: bytes, nombre: str) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(datos)) as z:
            partes = [z.read(n) for n in ('content.xml', 'styles.xml') if n in z.namelist()]
        trozos = []
        for parte in partes:
            root = etree.fromstring(parte)
            trozos.append(''.join(root.itertext()))
        return '\n'.join(trozos)
    except Exception:
        log.warning('No se pudo extraer texto del ODT %s', nombre, exc_info=True)
        return ''
