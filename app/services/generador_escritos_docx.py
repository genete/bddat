"""
Motor de render de escritos en formato OOXML (.docx) — python-docx-template.

RESPONSABILIDAD:
    Rellenar una plantilla .docx con el contexto ya construido y devolver los
    bytes del documento resultante. Hermano de `generador_escritos_odt`, del
    que se diferencia en todo menos en la firma: aquí manda el modelo de
    docxtpl (Subdoc, InlineImage) y allí el de ODF.

    Como el ODT, recibe el contexto hecho (ADR-035 §6): no consulta la base de
    datos ni sabe qué es un expediente.

MOTOR QUE SE MANTIENE (ADR-035 §2, enmienda del 2026-11-02):
    El formato de referencia es .odt, pero el .docx sigue siendo un formato de
    plantilla válido: es el plan ante desastre si los puestos de la Junta pasan a
    Microsoft 365 y pierden LibreOffice. Retirarlo o no se decidirá cuando conteste
    la ADA (#1085).

SIN DISCO NI BD:
    Recibe la plantilla en bytes y una función que da el fragmento por nombre,
    como el motor .odt. Las imágenes de `img()` no tienen sitio en el almacén
    todavía (#1085): `img()` falla con un mensaje claro.

LOS DOS PARCHES:
    docxtpl/docxcompose insertan los subdocumentos *dentro* del párrafo del
    marcador, y OOXML no admite un <w:p> dentro de otro: Word descarta el
    contenido anidado sin avisar. De ahí `_elevar_parrafos_anidados` (cuerpo)
    y `_corregir_anidados_en_zip` (cabeceras y pies, que docxtpl renderiza en
    partes no accesibles desde el objeto Document). El motor ODT no necesita
    equivalente porque la inserción la escribimos nosotros y es a nivel de
    bloque.

DEPENDENCIA:
    pip install python-docx-template
"""

import io
import logging
import re
import zipfile
from typing import Callable

from docxtpl import DocxTemplate

logger = logging.getLogger(__name__)


# ======================================================================
# API pública
# ======================================================================

def generar_escrito_docx(plantilla: bytes, contexto: dict,
                         fragmento: Callable[[str], bytes] | None = None) -> bytes:
    """
    Renderiza una plantilla .docx con el contexto dado. No toca el disco ni la BD.

    Añade al contexto lo que solo existe en este formato: la función img()
    y los fragmentos como Subdoc.

    Args:
        plantilla: El contenido de la plantilla .docx.
        contexto:  Dict ya construido (escritos.construir_contexto).
        fragmento: Función que da el contenido (.docx) del fragmento con ese nombre. Si no
                   hay fragmento, es la que lanza: un fragmento ausente detiene la
                   generación (ADR-050 §J). None = no hay ninguno, y una plantilla que
                   cite uno falla.

    Returns:
        bytes — Contenido del .docx generado.

    Raises:
        LookupError  — la plantilla cita un fragmento que no hay.
        RuntimeError — la plantilla usa `img()`, que todavía no tiene sitio en el almacén.
    """
    tpl = DocxTemplate(io.BytesIO(plantilla))

    # img() existe para que una plantilla que la use falle con un mensaje claro y no con un
    # «'img' is undefined»: las imágenes (antes PLANTILLAS_BASE/recursos/) no tienen sitio
    # en el almacén (#1085).
    contexto['img'] = _imagen_sin_recursos

    # Fragmentos insertables: {{r NombreFragmento}} → tpl.new_subdoc(contenido)
    contexto.update(_cargar_fragmentos(tpl, plantilla, fragmento))

    tpl.render(contexto)

    # Párrafos anidados en el cuerpo: se corrigen en memoria antes de save()
    _elevar_parrafos_anidados(tpl.docx)

    # Devolver bytes sin escribir a disco (la escritura es responsabilidad del caller)
    buffer = io.BytesIO()
    tpl.save(buffer)

    # Y en cabeceras/pies, sobre el ZIP ya escrito
    return _corregir_anidados_en_zip(buffer.getvalue())


def validar_plantilla_docx(datos: bytes) -> str | None:
    """
    Comprueba que el contenido sea un .docx utilizable como plantilla: formato
    OOXML bien formado y sintaxis Jinja2 del XML ya parcheado por docxtpl.

    Returns:
        str  — Mensaje de error, listo para enseñar al supervisor.
        None — La plantilla es válida.
    """
    from docx import Document as DocxDocument
    from jinja2 import Environment

    try:
        DocxDocument(io.BytesIO(datos))
    except Exception as e:
        return f'No es un .docx válido: {e}'

    try:
        tpl = DocxTemplate(io.BytesIO(datos))
        tpl.init_docx()
        Environment().parse(tpl.patch_xml(tpl.get_xml()))
    except Exception as e:
        return str(e)

    return None


# ======================================================================
# Imágenes y fragmentos
# ======================================================================

def _imagen_sin_recursos(*args, **kwargs):
    """La `img()` de las plantillas .docx: las imágenes que insertaba (antes en
    PLANTILLAS_BASE/recursos/) no tienen sitio en el almacén (#1085, ADR-050 §J)."""
    raise RuntimeError(
        'Esta plantilla inserta una imagen con img(), y las imágenes de plantilla todavía '
        'no están disponibles en BDDAT. Avisa al supervisor.')


def _cargar_fragmentos(tpl, plantilla: bytes, fragmento: Callable[[str], bytes] | None) -> dict:
    """
    Detecta etiquetas {{r NombreFragmento}} en el XML de la plantilla y carga
    los subdocumentos correspondientes con `fragmento`.

    python-docx-template requiere que el contexto contenga un objeto Subdoc
    creado con tpl.new_subdoc(contenido) para cada {{r variable}}.

    Un fragmento que falta detiene la generación (ADR-050 §J): sin él el escrito
    saldría sin ese trozo y nadie lo notaría.
    """
    # Escanear todos los XML relevantes: body, cabeceras y pies de página
    _PARTES_ESCANEAR = re.compile(r'^word/(document|header\d*|footer\d*)\.xml$')
    nombres = set()
    with zipfile.ZipFile(io.BytesIO(plantilla)) as z:
        for nombre_parte in z.namelist():
            if _PARTES_ESCANEAR.match(nombre_parte):
                xml = z.read(nombre_parte).decode('utf-8', errors='replace')
                nombres.update(re.findall(r'\{\{r\s+(\w+)\s*\}\}', xml))

    resultado = {}
    for nombre in sorted(nombres):
        if fragmento is None:
            raise LookupError(f'La plantilla cita el fragmento «{nombre}» y no se ha dado ninguno.')
        resultado[nombre] = tpl.new_subdoc(io.BytesIO(fragmento(nombre)))

    return resultado


# ======================================================================
# Párrafos anidados — reparación de lo que rompe docxtpl/docxcompose
# ======================================================================

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def _corregir_anidados_en_zip(docx_bytes: bytes) -> bytes:
    """
    Parchea el ZIP del .docx resultante para corregir <w:p> anidados en las
    partes que docxtpl renderiza fuera del objeto Document en memoria:
    cabeceras (word/header*.xml) y pies de página (word/footer*.xml).

    Devuelve los bytes corregidos.
    """
    from lxml import etree

    _PARTES = re.compile(r'^word/(header|footer)\d*\.xml$')

    buf_in = io.BytesIO(docx_bytes)
    buf_out = io.BytesIO()

    with zipfile.ZipFile(buf_in, 'r') as zin, \
         zipfile.ZipFile(buf_out, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if _PARTES.match(item.filename):
                try:
                    root = etree.fromstring(data)
                    _elevar_en_contenedor(root, W)
                    data = etree.tostring(root, xml_declaration=True,
                                          encoding='UTF-8', standalone=True)
                except Exception as e:
                    logger.warning('No se pudo corregir %s: %s', item.filename, e)
            zout.writestr(item, data)

    return buf_out.getvalue()


def _elevar_parrafos_anidados(doc) -> None:
    """
    Corrige párrafos anidados (<w:p> dentro de <w:p>) que genera docxtpl/docxcompose
    al insertar subdocumentos. OOXML no permite anidamiento de párrafos: Word los
    descarta silenciosamente al renderizar.

    Procesa el body principal y los elementos de cabecera/pie de todas las secciones.
    """
    # Recoger todos los contenedores de párrafos: body + cabeceras + pies de página
    contenedores = [doc.element.body]
    for section in doc.sections:
        for part in (section.header, section.footer,
                     section.even_page_header, section.even_page_footer,
                     section.first_page_header, section.first_page_footer):
            try:
                if part and not part.is_linked_to_previous:
                    contenedores.append(part._element)
            except Exception:
                pass

    for contenedor in contenedores:
        _elevar_en_contenedor(contenedor, W)


def _elevar_en_contenedor(contenedor, W: str) -> None:
    """Eleva elementos de bloque anidados dentro de <w:p> en un contenedor OOXML.

    Trata <w:p> y <w:tbl> anidados — ambos son inválidos dentro de <w:p> y
    Word los descarta. Ocurre cuando el fragmento contiene párrafos o tablas.

    Procesa el contenedor dado (body, hdr, ftr o tc) y recursivamente las
    celdas de todas las tablas que contenga, para cubrir el caso en que el
    marcador {{r Fragmento}} está dentro de una celda de tabla de la plantilla.
    """
    BLOQUES = {f'{W}p', f'{W}tbl'}
    changed = True
    while changed:
        changed = False
        for i, elem in enumerate(list(contenedor)):
            if elem.tag != f'{W}p':
                continue
            nested = [c for c in list(elem) if c.tag in BLOQUES]
            if not nested:
                continue

            insert_pos = i + 1
            for bloque in nested:
                elem.remove(bloque)
                contenedor.insert(insert_pos, bloque)
                insert_pos += 1

            texto_restante = ''.join(
                (t.text or '') for t in elem.iter(f'{W}t')
            ).strip()
            if not texto_restante:
                contenedor.remove(elem)

            changed = True
            break

    # Procesar recursivamente las celdas de todas las tablas del contenedor
    for tc in contenedor.findall(f'.//{W}tc'):
        _elevar_en_contenedor(tc, W)
