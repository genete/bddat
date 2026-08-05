"""
Comprobación de canonicidad de plantillas .odt frente a la hoja de estilos
común (ADR-035 §5, #727).

RESPONSABILIDAD:
    Avisar cuando una plantilla se aparta de la base: fuentes fuera de la
    identidad corporativa, o estilos personalizados que la hoja canónica
    declara y la plantilla no tiene. No decide si la plantilla entra —eso es
    de `generador_escritos_odt.validar_plantilla_odt` (formato + Jinja2)—: la
    canonicidad es una regla de calidad, se admite con aviso.

POR QUÉ ESTA LISTA DE FUENTES Y NO «QUE DECLARE ALGUNA» (ADR-035 §5):
    Medido en #727: el defecto de los acentos rotos en el texto extraíble no
    lo causa la ausencia de declaración, sino Cambria en concreto (TrueType
    Collection; sus acentos se pintan sin `ToUnicode` válido al exportar a
    PDF). Calibri, Times New Roman, Liberation Sans, Carlito y Caladea salen
    limpias. La regla, aun así, no es «que no sea Cambria»: la identidad
    corporativa de la Junta exige Source Sans Pro sin margen (decisión de
    Carlos, ajena al defecto de los acentos), así que la lista es una lista
    blanca, no negra.

POR QUÉ SOLO ESTILOS PERSONALIZADOS (no «Título 1», «Subtítulo»…):
    Medido en #727: LibreOffice traduce los nombres internos de los estilos
    estándar al guardar, según el idioma de su interfaz (`Título 1` →
    `Heading 1`). Un nombre que cambia solo no sirve para comprobar nada. Los
    estilos con nombre propio (`Cabecera - Consejería`, `BDDAT - Firmante`…)
    sí sobreviven intactos.

MARCA DE VERSIÓN:
    `leer_marca` lee las claves `BDDAT:*` de `meta:user-defined` en meta.xml,
    escritas por `scripts/fabricar_plantilla_*.py`. Dice de qué base deriva la
    plantilla, no si cumple: se hereda al copiar y sobrevive aunque alguien
    cambie la fuente a mano después (no es una puerta de acceso).

    `BDDAT:plantilla-base` decide qué subconjunto de estilos personalizados se
    exige: una plantilla de resolución no tiene por qué llevar los estilos de
    formulario/destinatario de la carta, y viceversa. Si la marca falta o no
    se reconoce, se comprueban solo las fuentes: sin saber de qué base deriva,
    no hay lista de estilos que exigir sin adivinar.
"""
import zipfile

from lxml import etree

NS = {
    'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
    'style':  'urn:oasis:names:tc:opendocument:xmlns:style:1.0',
    'meta':   'urn:oasis:names:tc:opendocument:xmlns:meta:1.0',
}
Q = {k: '{%s}' % v for k, v in NS.items()}

FUENTES_PERMITIDAS = {
    'Source Sans Pro', 'Source Sans Pro Bold',
    'Source Sans Pro Light', 'Source Sans Pro SemiBold',
}

# Estilos personalizados comunes a toda la hoja (#727, subconjunto acordado
# con Carlos sobre la papelería oficial de la Junta).
ESTILOS_COMUNES = (
    'Cabecera - Consejería', 'Cabecera - Centro directivo',
    'Cabecera - Nombre Consejería Centrado', 'Cabecera - Delegación del gobierno',
    'Cabecera - Delegación Territorial',
    'Pie de página - Datos', 'Pie de página - Centrado',
    'H6 - Anotaciones',
    'Tabla - Título', 'Tabla - Título de campo', 'Tabla - Contenido desarrollo',
    'BDDAT - Firmante',
)
# Solo en plantillas derivadas de la carta (tabla de Fecha/Ref./Asunto/Destinatario)
ESTILOS_CARTA = ('Formulario - Datos', 'Formulario - Destinatario', 'Formulario - Títulos')
# Solo en plantillas derivadas de la resolución
ESTILOS_RESOLUCION = (
    'BDDAT - Título resolución', 'BDDAT - Referencia expediente',
    'BDDAT - Sección resolución', 'BDDAT - Firmante resolución',
)

ESTILOS_POR_BASE = {
    'carta': ESTILOS_COMUNES + ESTILOS_CARTA,
    'resolucion': ESTILOS_COMUNES + ESTILOS_RESOLUCION,
}


def es_vineta(nombre: str) -> bool:
    """
    Estilos de viñeta heredados de Word (Wingdings, Symbol, Courier New como
    glifo de lista) y el estilo `Graphics` de igual origen. Su fuente es el
    símbolo de la viñeta, no texto: quedan fuera de la comprobación de fuentes.
    """
    return (nombre or '').startswith('WW_') or nombre == 'Graphics'


def leer_marca(ruta_abs: str) -> dict | None:
    """
    Lee las claves `BDDAT:*` de meta:user-defined.

    Returns:
        dict  — {'plantilla-base': ..., 'version-hoja-estilos': ..., 'origen': ...}
                 (solo las claves presentes; ninguna es obligatoria).
        None  — el fichero no es un .odt legible o no tiene meta.xml.
    """
    try:
        with zipfile.ZipFile(ruta_abs) as z:
            if 'meta.xml' not in z.namelist():
                return None
            meta = etree.fromstring(z.read('meta.xml'))
    except (zipfile.BadZipFile, etree.XMLSyntaxError, OSError):
        return None

    marca = {}
    for ud in meta.iter(f'{Q["meta"]}user-defined'):
        nombre = ud.get(f'{Q["meta"]}name') or ''
        if nombre.startswith('BDDAT:'):
            marca[nombre[len('BDDAT:'):]] = ud.text or ''
    return marca or None


def comprobar_canonicidad(ruta_abs: str) -> list[str]:
    """
    Avisos de canonicidad, listos para enseñar al supervisor. Lista vacía si
    no hay nada que decir (no implica que la plantilla sea válida: eso lo
    decide `validar_plantilla_odt`).
    """
    try:
        with zipfile.ZipFile(ruta_abs) as z:
            styles_xml = z.read('styles.xml') if 'styles.xml' in z.namelist() else None
            content_xml = z.read('content.xml') if 'content.xml' in z.namelist() else None
    except (zipfile.BadZipFile, OSError):
        return []
    if content_xml is None:
        return []

    avisos = []
    avisos.extend(_avisos_fuentes(styles_xml, content_xml))

    marca = leer_marca(ruta_abs) or {}
    base = marca.get('plantilla-base')
    estilos_esperados = ESTILOS_POR_BASE.get(base)
    if estilos_esperados and styles_xml is not None:
        avisos.extend(_avisos_estilos(styles_xml, estilos_esperados))

    return avisos


def _avisos_fuentes(styles_xml: bytes | None, content_xml: bytes) -> list[str]:
    fuentes_ajenas = set()
    for datos in (styles_xml, content_xml):
        if not datos:
            continue
        root = etree.fromstring(datos)
        for estilo in root.iter(f'{Q["style"]}style'):
            if es_vineta(estilo.get(f'{Q["style"]}name')):
                continue
            for tp in estilo.iter(f'{Q["style"]}text-properties'):
                f = tp.get(f'{Q["style"]}font-name')
                if f and f not in FUENTES_PERMITIDAS:
                    fuentes_ajenas.add(f)
        for default in root.iter(f'{Q["style"]}default-style'):
            for tp in default.iter(f'{Q["style"]}text-properties'):
                f = tp.get(f'{Q["style"]}font-name')
                if f and f not in FUENTES_PERMITIDAS:
                    fuentes_ajenas.add(f)

    if not fuentes_ajenas:
        return []

    avisos = []
    if 'Cambria' in fuentes_ajenas:
        avisos.append(
            'La plantilla usa la fuente Cambria, que rompe los acentos del '
            'texto extraíble del PDF (medido en #727). Cámbiala por Source '
            'Sans Pro, la de la plantilla base.'
        )
        fuentes_ajenas.discard('Cambria')
    if fuentes_ajenas:
        avisos.append(
            'La plantilla usa fuentes fuera de la identidad corporativa: '
            f'{", ".join(sorted(fuentes_ajenas))}. La plantilla base usa '
            'Source Sans Pro.'
        )
    return avisos


def _avisos_estilos(styles_xml: bytes, esperados: tuple) -> list[str]:
    root = etree.fromstring(styles_xml)
    presentes = {
        e.get(f'{Q["style"]}display-name') or e.get(f'{Q["style"]}name')
        for e in root.iter(f'{Q["style"]}style')
        if e.get(f'{Q["style"]}family') == 'paragraph'
    }
    faltan = [nombre for nombre in esperados if nombre not in presentes]
    if not faltan:
        return []
    return [
        'Faltan estilos de la hoja canónica que los fragmentos y las demás '
        f'plantillas esperan: {", ".join(faltan)}.'
    ]
