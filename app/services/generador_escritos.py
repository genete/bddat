"""
Servicio de generación de escritos administrativos.

RESPONSABILIDAD:
    Orquesta las capas de contexto y despacha al motor de render que
    corresponda para producir un escrito relleno a partir de una Plantilla
    registrada.

DOS MOTORES HERMANOS (ADR-035 §2):
    .docx → python-docx-template, en este módulo (_generar_docx)
    .odt  → renderizador propio, en generador_escritos_odt

    La elección se hace por la extensión de plantilla.ruta_plantilla: sin
    columna nueva ni migración. No hay abstracción común entre ambos — los
    modelos de docxtpl y de ODF no se parecen (ADR-035, alternativa B).

FLUJO:
    1. Resuelve la ruta de la plantilla en PLANTILLAS_BASE
    2. Construye el contexto (escritos.construir_contexto) — agnóstico del formato
    3. Renderiza con el motor que toque
    4. Devuelve los bytes del documento resultante

FUNCIONES PÚBLICAS ADICIONALES (Fase 5 #167):
    componer_nombre_documento  — Nombre sistematizado para el documento generado
    ruta_destino_documento     — Ruta en FILESYSTEM_BASE/AT-XXXX/
    guardar_documento          — Escribe bytes a disco (sobrescribe si existe)
    tipo_contenido_documento   — MIME del documento según su extensión

USO:
    from app.services.generador_escritos import (
        generar_escrito, componer_nombre_documento,
        ruta_destino_documento, guardar_documento,
    )

    doc_bytes = generar_escrito(plantilla, expediente, db_session)
    nombre = componer_nombre_documento(tarea, plantilla)
    ruta = ruta_destino_documento(expediente, nombre)
    guardar_documento(doc_bytes, ruta)

DEPENDENCIA:
    pip install python-docx-template   (solo la rama .docx; la .odt no añade nada)
"""

import logging
import os
import re

from docxtpl import DocxTemplate

from app.services.escritos import construir_contexto

logger = logging.getLogger(__name__)

# MIME por extensión de plantilla. Lo consume la API al registrar el documento
# generado en el pool.
TIPOS_CONTENIDO = {
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.odt':  'application/vnd.oasis.opendocument.text',
}


def generar_escrito(plantilla, expediente, db_session, tarea=None,
                    codigo_seguimiento=None) -> bytes:
    """
    Genera el escrito relleno para la plantilla y expediente dados.

    Despacha al motor .docx o al .odt según la extensión de la plantilla.

    Args:
        plantilla:   Instancia de Plantilla (plantilla + contexto registrado).
        expediente:  Instancia de Expediente con relaciones cargadas.
        db_session:  Sesión SQLAlchemy activa (para ejecutar consultas nombradas).
        tarea:       Instancia de Tarea opcional. Si se proporciona y tiene
                     documentos consumidos, el primero se añade al contexto
                     como 'doc_entrada'.
        codigo_seguimiento: Código de trazabilidad a embeber en el documento
                     (#182). Solo lo soporta el motor .odt; en .docx se ignora
                     con un warning, porque ningún canal de metadatos OOXML
                     sobrevive al pipeline (ADR-035, contexto).

    Returns:
        bytes — Contenido del documento generado, listo para guardar en disco.

    Raises:
        FileNotFoundError — Si la plantilla no existe en PLANTILLAS_BASE.
        RuntimeError      — Si el Context Builder especificado no se puede cargar.
        ValueError        — Si la extensión de la plantilla no tiene motor.
    """
    plantilla_path = _ruta_plantilla(plantilla.ruta_plantilla)
    extension = os.path.splitext(plantilla_path)[1].lower()

    ctx = construir_contexto(plantilla, expediente, db_session, tarea=tarea)

    if extension == '.odt':
        from app.services.generador_escritos_odt import generar_escrito_odt
        return generar_escrito_odt(plantilla_path, ctx,
                                   codigo_seguimiento=codigo_seguimiento)

    if extension == '.docx':
        if codigo_seguimiento:
            logger.warning(
                'Código de seguimiento ignorado: la plantilla %s es .docx y el '
                'motor OOXML no lo soporta (ADR-035)', plantilla.ruta_plantilla
            )
        return _generar_docx(plantilla_path, ctx)

    raise ValueError(
        f'No hay motor de generación para la extensión "{extension}" '
        f'(plantilla: {plantilla.ruta_plantilla}). Formatos soportados: '
        f'{", ".join(sorted(TIPOS_CONTENIDO))}.'
    )


def _generar_docx(plantilla_path: str, ctx: dict) -> bytes:
    """
    Motor .docx — python-docx-template sobre el contexto ya construido.

    Añade al contexto lo que solo existe en este formato: la función img()
    (InlineImage) y los fragmentos como Subdoc.
    """
    # Renderizado
    tpl = DocxTemplate(plantilla_path)

    # Función img() para incrustar imágenes desde PLANTILLAS_BASE/recursos/
    # Uso en plantilla: {{ img('logo.png', '3.5', '1.98') }}
    from flask import current_app
    _recursos = os.path.join(current_app.config.get('PLANTILLAS_BASE', ''), 'recursos')
    ctx['img'] = _fn_imagen(tpl, _recursos)

    # Fragmentos insertables: {{r NombreFragmento}} → tpl.new_subdoc(ruta)
    ctx.update(_cargar_fragmentos(tpl, plantilla_path))

    tpl.render(ctx)

    # docxtpl/docxcompose genera <w:p> anidados (inválido en OOXML) al insertar subdocs.
    # Word descarta silenciosamente el contenido anidado. Corrección necesaria.
    # — Para el body: se puede corregir en memoria antes de save()
    _elevar_parrafos_anidados(tpl.docx)

    # Devolver bytes sin escribir a disco (la escritura es responsabilidad del caller)
    import io
    buffer = io.BytesIO()
    tpl.save(buffer)

    # — Para cabeceras/pies: docxtpl los renderiza en Parts separados no accesibles
    #   vía tpl.docx en memoria; hay que parchear el ZIP resultante.
    return _corregir_anidados_en_zip(buffer.getvalue())


# ------------------------------------------------------------------
# Funciones públicas — nombre, ruta y guardado (Fase 5 #167)
# ------------------------------------------------------------------

# Caracteres no válidos en nombres de fichero Windows
_CARACTERES_INVALIDOS = re.compile(r'[\\/:*?"<>|]')


def componer_nombre_documento(tarea, plantilla) -> str:
    """
    Genera un nombre sistematizado para el documento a partir de la cadena ESFTT.

    Recorre tarea → tipo_tarea → tramite → tipo_tramite → fase → tipo_fase
    → solicitud → tipo_solicitud → expediente, tomando nombre_en_plantilla
    de cada nivel. NULL al final se omite; NULL en medio se reemplaza por "ANY".

    Si plantilla.variante existe, se añade " V {variante}" al final.
    La extensión es la de la plantilla (.docx o .odt), no una fija: el escrito
    generado conserva el formato de su plantilla (ADR-035 §2).
    Caracteres inválidos para fichero → '_'.
    """
    tramite = tarea.tramite
    fase = tramite.fase if tramite else None
    solicitud = fase.solicitud if fase else None
    expediente = solicitud.expediente if solicitud else None

    # Recoger nombre_en_plantilla de cada nivel (de más genérico a más específico)
    partes_raw = [
        getattr(tarea.tipo_tarea, 'nombre_en_plantilla', None) if tarea.tipo_tarea else None,
        getattr(tramite.tipo_tramite, 'nombre_en_plantilla', None) if tramite and tramite.tipo_tramite else None,
        getattr(fase.tipo_fase, 'nombre_en_plantilla', None) if fase and fase.tipo_fase else None,
        getattr(solicitud.tipo_solicitud, 'nombre_en_plantilla', None) if solicitud and solicitud.tipo_solicitud else None,
        f'AT-{expediente.numero_at}' if expediente and expediente.numero_at else None,
    ]

    # Recortar NULLs del final; reemplazar NULLs internos por "ANY"
    while partes_raw and partes_raw[-1] is None:
        partes_raw.pop()

    partes = [p if p is not None else 'ANY' for p in partes_raw]

    nombre = ' '.join(partes)

    if plantilla.variante:
        nombre += f' V {plantilla.variante}'

    nombre += os.path.splitext(plantilla.ruta_plantilla or '')[1].lower() or '.docx'

    # Sanitizar caracteres inválidos para nombre de fichero
    nombre = _CARACTERES_INVALIDOS.sub('_', nombre)

    return nombre


def ruta_destino_documento(expediente, nombre_fichero) -> str:
    """
    Calcula la ruta absoluta donde guardar el documento generado.

    Estructura: FILESYSTEM_BASE / AT-{numero_at} / {nombre_fichero}
    Crea el subdirectorio si no existe.

    NOTA: Ruta hardcoded provisional. Se reemplazará por rutas configurables
    en tablas maestras cuando se implemente esa decisión de arquitectura
    (Bloque 2/8 del roadmap).
    """
    from flask import current_app
    base = current_app.config.get('FILESYSTEM_BASE', '')
    if not base:
        raise RuntimeError('FILESYSTEM_BASE no está configurado')

    carpeta_exp = f'AT-{expediente.numero_at}'
    directorio = os.path.join(base, carpeta_exp)
    os.makedirs(directorio, exist_ok=True)

    return os.path.join(directorio, nombre_fichero)


def guardar_documento(doc_bytes, ruta_destino) -> str:
    """
    Escribe los bytes del documento a disco. Sobrescribe si existe (regeneración B6).

    Returns:
        str — Ruta absoluta del fichero escrito.
    """
    with open(ruta_destino, 'wb') as f:
        f.write(doc_bytes)
    return ruta_destino


def validar_plantilla(ruta_abs: str) -> str | None:
    """
    Comprueba que el fichero sea una plantilla utilizable por su motor.

    Dos cosas distintas, y ambas importan en el alta: que el fichero esté bien
    formado para su formato, y que su sintaxis Jinja2 compile — un `{% for %}`
    sin cerrar no se ve hasta que alguien genera el escrito.

    Returns:
        str  — Mensaje de error, listo para enseñar al supervisor.
        None — La plantilla es válida.
    """
    extension = os.path.splitext(ruta_abs or '')[1].lower()

    if extension == '.odt':
        from app.services.generador_escritos_odt import validar_plantilla_odt
        return validar_plantilla_odt(ruta_abs)

    if extension == '.docx':
        return _validar_plantilla_docx(ruta_abs)

    return (f'Formato de plantilla no soportado: "{extension}". '
            f'Se admiten {", ".join(sorted(TIPOS_CONTENIDO))}.')


def _validar_plantilla_docx(ruta_abs: str) -> str | None:
    """Formato OOXML bien formado + sintaxis Jinja2 del XML ya parcheado."""
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


def tipo_contenido_documento(nombre_o_ruta: str) -> str:
    """
    MIME del documento generado, deducido de su extensión.

    Desconocida → 'application/octet-stream', que es lo honesto: mejor que el
    navegador no sepa abrirlo a que lo abra con el programa equivocado.
    """
    extension = os.path.splitext(nombre_o_ruta or '')[1].lower()
    return TIPOS_CONTENIDO.get(extension, 'application/octet-stream')


# ------------------------------------------------------------------
# Helpers privados
# ------------------------------------------------------------------

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
    from docxtpl import InlineImage
    from docx.shared import Cm

    def img(nombre_fichero: str, ancho=None, alto=None) -> InlineImage:
        ruta = os.path.join(recursos_dir, nombre_fichero)
        kwargs = {}
        if ancho is not None:
            kwargs['width'] = Cm(float(ancho))
        if alto is not None:
            kwargs['height'] = Cm(float(alto))
        return InlineImage(tpl, ruta, **kwargs)

    return img


def _ruta_plantilla(ruta_relativa: str) -> str:
    """Resuelve la ruta absoluta de la plantilla dentro de PLANTILLAS_BASE."""
    from flask import current_app
    base = current_app.config['PLANTILLAS_BASE']
    ruta = os.path.join(base, 'plantillas', ruta_relativa)
    if not os.path.isfile(ruta):
        raise FileNotFoundError(
            f'Plantilla no encontrada: {ruta}. '
            f'Comprueba PLANTILLAS_BASE y la ruta registrada en la plantilla.'
        )
    return ruta


def _corregir_anidados_en_zip(docx_bytes: bytes) -> bytes:
    """
    Parchea el ZIP del .docx resultante para corregir <w:p> anidados en las
    partes que docxtpl renderiza fuera del objeto Document en memoria:
    cabeceras (word/header*.xml) y pies de página (word/footer*.xml).

    Devuelve los bytes corregidos.
    """
    import zipfile
    import io as _io
    from lxml import etree

    W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    _PARTES = re.compile(r'^word/(header|footer)\d*\.xml$')

    buf_in = _io.BytesIO(docx_bytes)
    buf_out = _io.BytesIO()

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
    W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

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


def _cargar_fragmentos(tpl, plantilla_path) -> dict:
    """
    Detecta etiquetas {{r NombreFragmento}} en el XML de la plantilla y carga
    los subdocumentos correspondientes desde PLANTILLAS_BASE/fragmentos/.

    python-docx-template requiere que el contexto contenga un objeto Subdoc
    creado con tpl.new_subdoc(ruta) para cada {{r variable}}.
    """
    import zipfile

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
