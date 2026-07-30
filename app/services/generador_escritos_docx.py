"""
Motor de render de escritos en formato OOXML (.docx) — python-docx-template.

RESPONSABILIDAD:
    Rellenar una plantilla .docx con el contexto ya construido y devolver los
    bytes del documento resultante. Hermano de `generador_escritos_odt`, del
    que se diferencia en todo menos en la firma: aquí manda el modelo de
    docxtpl (Subdoc, InlineImage) y allí el de ODF.

    Como el ODT, recibe el contexto hecho (ADR-035 §6): no consulta la base de
    datos ni sabe qué es un expediente.

MOTOR HEREDADO, EN RETIRADA (ADR-035 §2):
    El formato de referencia es .odt. Este motor se conserva a propósito para
    poder migrar plantilla a plantilla y tener vía de vuelta, y se retira
    cuando no haya prisa — momento en el que este fichero desaparece entero.

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
import os
import re
import zipfile

from docxtpl import DocxTemplate

logger = logging.getLogger(__name__)


# ======================================================================
# API pública
# ======================================================================

def generar_escrito_docx(plantilla_path: str, contexto: dict) -> bytes:
    """
    Renderiza una plantilla .docx con el contexto dado.

    Añade al contexto lo que solo existe en este formato: la función img()
    (InlineImage) y los fragmentos como Subdoc.

    Args:
        plantilla_path: Ruta absoluta de la plantilla .docx.
        contexto:       Dict ya construido (escritos.construir_contexto).

    Returns:
        bytes — Contenido del .docx generado.
    """
    tpl = DocxTemplate(plantilla_path)

    # Función img() para incrustar imágenes desde PLANTILLAS_BASE/recursos/
    # Uso en plantilla: {{ img('logo.png', '3.5', '1.98') }}
    from flask import current_app
    _recursos = os.path.join(current_app.config.get('PLANTILLAS_BASE', ''), 'recursos')
    contexto['img'] = _fn_imagen(tpl, _recursos)

    # Fragmentos insertables: {{r NombreFragmento}} → tpl.new_subdoc(ruta)
    contexto.update(_cargar_fragmentos(tpl, plantilla_path))

    tpl.render(contexto)

    # Párrafos anidados en el cuerpo: se corrigen en memoria antes de save()
    _elevar_parrafos_anidados(tpl.docx)

    # Devolver bytes sin escribir a disco (la escritura es responsabilidad del caller)
    buffer = io.BytesIO()
    tpl.save(buffer)

    # Y en cabeceras/pies, sobre el ZIP ya escrito
    return _corregir_anidados_en_zip(buffer.getvalue())


def validar_plantilla_docx(ruta_abs: str) -> str | None:
    """
    Comprueba que el fichero sea un .docx utilizable como plantilla: formato
    OOXML bien formado y sintaxis Jinja2 del XML ya parcheado por docxtpl.

    Returns:
        str  — Mensaje de error, listo para enseñar al supervisor.
        None — La plantilla es válida.
    """
    from docx import Document as DocxDocument
    from jinja2 import Environment

    try:
        DocxDocument(ruta_abs)
    except Exception as e:
        return f'No es un .docx válido: {e}'

    try:
        tpl = DocxTemplate(ruta_abs)
        tpl.init_docx()
        Environment().parse(tpl.patch_xml(tpl.get_xml()))
    except Exception as e:
        return str(e)

    return None


# ======================================================================
# Imágenes y fragmentos
# ======================================================================

def _fn_imagen(tpl, recursos_dir: str):
    """
    Devuelve la función img() que las plantillas Jinja2 usan para incrustar imágenes.

    Uso en plantilla .docx:
        {{ img('logo_portada.png', '3.5', '1.98') }}   — ancho y alto en cm
        {{ img('firma.png', '4.0') }}                  — solo ancho; alto proporcional
        {{ img('sello.png') }}                         — tamaño original del fichero

    El fichero se busca en PLANTILLAS_BASE/recursos/<nombre_fichero>.
    El anclaje lo controla la plantilla (inline, dentro de cuadro de texto, etc.),
    no esta función — ver ADR-009.
    """
    from docx.shared import Cm
    from docxtpl import InlineImage

    def img(nombre_fichero: str, ancho=None, alto=None) -> InlineImage:
        ruta = os.path.join(recursos_dir, nombre_fichero)
        kwargs = {}
        if ancho is not None:
            kwargs['width'] = Cm(float(ancho))
        if alto is not None:
            kwargs['height'] = Cm(float(alto))
        return InlineImage(tpl, ruta, **kwargs)

    return img


def _cargar_fragmentos(tpl, plantilla_path) -> dict:
    """
    Detecta etiquetas {{r NombreFragmento}} en el XML de la plantilla y carga
    los subdocumentos correspondientes desde PLANTILLAS_BASE/fragmentos/.

    python-docx-template requiere que el contexto contenga un objeto Subdoc
    creado con tpl.new_subdoc(ruta) para cada {{r variable}}.
    """
    # Escanear todos los XML relevantes: body, cabeceras y pies de página
    _PARTES_ESCANEAR = re.compile(r'^word/(document|header\d*|footer\d*)\.xml$')
    nombres = set()
    with zipfile.ZipFile(plantilla_path) as z:
        for nombre_parte in z.namelist():
            if _PARTES_ESCANEAR.match(nombre_parte):
                xml = z.read(nombre_parte).decode('utf-8', errors='replace')
                nombres.update(re.findall(r'\{\{r\s+(\w+)\s*\}\}', xml))

    if not nombres:
        return {}

    from flask import current_app
    base = current_app.config['PLANTILLAS_BASE']
    fragmentos_dir = os.path.join(base, 'fragmentos')

    resultado = {}
    for nombre in set(nombres):
        ruta_frag = os.path.join(fragmentos_dir, nombre + '.docx')
        if os.path.isfile(ruta_frag):
            resultado[nombre] = tpl.new_subdoc(ruta_frag)
        else:
            logger.warning(
                'Fragmento "%s.docx" referenciado en plantilla pero no encontrado en %s',
                nombre, fragmentos_dir
            )

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
