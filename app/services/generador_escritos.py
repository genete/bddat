"""
Servicio de generación de escritos administrativos (.docx).

RESPONSABILIDAD:
    Orquesta las capas de contexto + python-docx-template para producir
    un fichero .docx relleno a partir de una Plantilla registrada.

FLUJO:
    1. Carga la plantilla .docx desde PLANTILLAS_BASE
    2. Construye el contexto: Capa 1 (ContextoBaseExpediente) + Capa 2 opcional
    3. Ejecuta las consultas nombradas referenciadas en la plantilla
    4. Renderiza con DocxTemplate (python-docx-template / Jinja2)
    5. Devuelve bytes del .docx resultante

FUNCIONES PÚBLICAS ADICIONALES (Fase 5 #167):
    componer_nombre_documento  — Nombre sistematizado para el .docx generado
    ruta_destino_documento     — Ruta en FILESYSTEM_BASE/AT-XXXX/
    guardar_docx               — Escribe bytes a disco (sobrescribe si existe)

USO:
    from app.services.generador_escritos import generar_escrito
    from app.services.generador_escritos import componer_nombre_documento, ruta_destino_documento, guardar_docx

    docx_bytes = generar_escrito(plantilla, expediente, db_session)
    nombre = componer_nombre_documento(tarea, plantilla)
    ruta = ruta_destino_documento(expediente, nombre)
    guardar_docx(docx_bytes, ruta)

DEPENDENCIA:
    pip install python-docx-template
"""

import importlib
import logging
import os
import re

from docxtpl import DocxTemplate

from app.services.escritos import ContextoBaseExpediente

logger = logging.getLogger(__name__)


def generar_escrito(plantilla, expediente, db_session) -> bytes:
    """
    Genera el .docx relleno para la plantilla y expediente dados.

    Args:
        plantilla:   Instancia de Plantilla (plantilla + contexto registrado).
        expediente:  Instancia de Expediente con relaciones cargadas.
        db_session:  Sesión SQLAlchemy activa (para ejecutar consultas nombradas).

    Returns:
        bytes — Contenido del .docx generado, listo para guardar en disco.

    Raises:
        FileNotFoundError — Si la plantilla .docx no existe en PLANTILLAS_BASE.
        RuntimeError      — Si el Context Builder especificado no se puede cargar.
    """
    plantilla_path = _ruta_plantilla(plantilla.ruta_plantilla)

    # Capa 1: contexto base del expediente
    ctx = ContextoBaseExpediente(expediente).get_contexto()

    # Capa 2: Context Builder opcional
    if plantilla.contexto_clase:
        builder = _cargar_context_builder(plantilla.contexto_clase)
        ctx.update(builder(expediente, db_session).get_contexto())

    # Consultas nombradas: se añaden al contexto con su nombre como clave
    ctx.update(_ejecutar_consultas(plantilla, expediente, db_session))

    # Renderizado
    tpl = DocxTemplate(plantilla_path)

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
    Genera un nombre sistematizado para el .docx a partir de la cadena ESFTT.

    Recorre tarea → tipo_tarea → tramite → tipo_tramite → fase → tipo_fase
    → solicitud → tipo_solicitud → expediente, tomando nombre_en_plantilla
    de cada nivel. NULL al final se omite; NULL en medio se reemplaza por "ANY".

    Si plantilla.variante existe, se añade " V {variante}" al final.
    Sufijo siempre .docx. Caracteres inválidos para fichero → '_'.
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

    nombre += '.docx'

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


def guardar_docx(docx_bytes, ruta_destino) -> str:
    """
    Escribe bytes del .docx a disco. Sobrescribe si existe (regeneración B6).

    Returns:
        str — Ruta absoluta del fichero escrito.
    """
    with open(ruta_destino, 'wb') as f:
        f.write(docx_bytes)
    return ruta_destino


# ------------------------------------------------------------------
# Helpers privados
# ------------------------------------------------------------------

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


def _cargar_context_builder(nombre_clase: str):
    """
    Importa y devuelve la clase Context Builder por nombre.

    Convenio de módulo: app.services.context_builders.<nombre_clase_en_snake>
    Ejemplo: 'RequerimientoSubsanacion' → app.services.context_builders.requerimiento_subsanacion
    """
    import re
    snake = re.sub(r'(?<!^)(?=[A-Z])', '_', nombre_clase).lower()
    modulo_path = f'app.services.context_builders.{snake}'
    try:
        modulo = importlib.import_module(modulo_path)
        return getattr(modulo, nombre_clase)
    except (ModuleNotFoundError, AttributeError) as e:
        raise RuntimeError(
            f'No se pudo cargar el Context Builder "{nombre_clase}" '
            f'desde {modulo_path}: {e}'
        )


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
            for nested_p in nested:
                elem.remove(nested_p)
                contenedor.insert(insert_pos, nested_p)
                insert_pos += 1

            texto_restante = ''.join(
                (t.text or '') for t in elem.iter(f'{W}t')
            ).strip()
            if not texto_restante:
                contenedor.remove(elem)

            changed = True
            break


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


def _ejecutar_consultas(plantilla, expediente, db_session) -> dict:
    """
    Ejecuta TODAS las ConsultaNombrada activas con :expediente_id y las pasa
    al contexto. Las no referenciadas en la plantilla se ignoran por Jinja2.

    Estrategia simple: ejecutar todas es más barato que parsear el .docx
    buscando etiquetas {%tr for row in X %}. Si una consulta falla, se
    registra un warning y se pasa como lista vacía (no rompe la generación).
    """
    from app.models.consultas_nombradas import ConsultaNombrada
    from sqlalchemy import text

    resultado = {}

    for cn in ConsultaNombrada.query.filter_by(activo=True).all():
        try:
            rows = db_session.execute(
                text(cn.sql),
                {'expediente_id': expediente.id}
            ).mappings().all()
            resultado[cn.nombre] = [dict(r) for r in rows]
        except Exception as e:
            logger.warning(
                'Consulta nombrada "%s" (id=%s) falló para expediente %s: %s',
                cn.nombre, cn.id, expediente.id, e
            )
            resultado[cn.nombre] = []

    return resultado
