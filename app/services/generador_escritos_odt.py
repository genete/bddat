"""
Motor de render de escritos en formato ODT (ADR-035).

RESPONSABILIDAD:
    Rellenar una plantilla .odt con el contexto ya construido y devolver los
    bytes del documento resultante. Hermano de la rama .docx de
    `generador_escritos`, del que recibe el contexto: aquí no se consulta la
    base de datos ni se sabe qué es un expediente.

POR QUÉ UN MOTOR PROPIO (ADR-035):
    Un .odt es un ZIP con XML dentro y los tokens llegan enteros al XML, así
    que basta zipfile + lxml + Jinja2 — ninguna dependencia nueva. A cambio
    desaparecen los dos parches que docxtpl obliga a mantener en la rama
    .docx (_elevar_parrafos_anidados, _corregir_anidados_en_zip): aquí la
    inserción de fragmentos la escribimos nosotros y es a nivel de bloque.

ORDEN DEL RENDER (importa):
    1. Fragmentos — sustituyen al párrafo del marcador {{r Nombre }}, no se
       insertan dentro. Va ANTES de Jinja2, así un fragmento puede llevar
       tokens propios y se rellenan (docxtpl no lo permite).
    2. Recomposición de tokens partidos en varios <text:span>.
    3. Bucles de fila {%tr ... %} elevados fuera de su <table:table-row>.
    4. Jinja2 sobre content.xml y styles.xml (en styles.xml viven las
       cabeceras y pies, que son parte de las master pages).
    5. Inyección del código de seguimiento — DESPUÉS de Jinja2, para que un
       código que contuviera '{{' no se interprete como plantilla.

PARTES DEL ODT QUE SE TOCAN:
    content.xml — cuerpo del documento
    styles.xml  — estilos, master pages y con ellas cabeceras y pies
    El resto del ZIP se copia tal cual, incluido 'mimetype' (primero y sin
    comprimir, como exige ODF).
"""

import copy
import io
import logging
import os
import re
import zipfile
from xml.sax.saxutils import escape

from jinja2 import Environment
from lxml import etree

logger = logging.getLogger(__name__)

NS = {
    'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
    'style':  'urn:oasis:names:tc:opendocument:xmlns:style:1.0',
    'text':   'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
    'draw':   'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0',
    'fo':     'urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0',
    'svg':    'urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0',
    'table':  'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
}
Q = {k: '{%s}' % v for k, v in NS.items()}

# Atributos que nombran o referencian estilos. Hay que reescribirlos al traer
# los estilos de un fragmento: LibreOffice llama P1, T1, L1… a los estilos
# automáticos de todos los documentos, así que colisionan.
ATTR_NOMBRE = f'{Q["style"]}name'
ATTRS_REFERENCIA = (
    f'{Q["text"]}style-name',
    f'{Q["text"]}list-style-name',
    f'{Q["style"]}list-style-name',
)

# Elementos del cuerpo de un fragmento que no son contenido y no se copian.
NO_CONTENIDO = ('sequence-decls', 'forms', 'variable-decls', 'user-field-decls')

RE_FRAGMENTO = re.compile(r'\{\{r\s+(\w+)\s*\}\}')
RE_TOKEN = re.compile(r'\{\{.*?\}\}|\{%.*?%\}', re.S)


# ======================================================================
# API pública
# ======================================================================

def generar_escrito_odt(plantilla_path: str, contexto: dict,
                        codigo_seguimiento: str | None = None,
                        fragmentos_dir: str | None = None) -> bytes:
    """
    Renderiza una plantilla .odt con el contexto dado.

    Args:
        plantilla_path:     Ruta absoluta de la plantilla .odt.
        contexto:           Dict ya construido (escritos.construir_contexto).
        codigo_seguimiento: Código de trazabilidad a embeber (#182). None = no
                            se inyecta nada.
        fragmentos_dir:     Directorio de fragmentos .odt. Si es None se toma
                            de PLANTILLAS_BASE/fragmentos (requiere app context).

    Returns:
        bytes — Contenido del .odt generado.
    """
    if fragmentos_dir is None:
        fragmentos_dir = _fragmentos_dir()

    with zipfile.ZipFile(plantilla_path) as zin:
        partes = {n: zin.read(n) for n in zin.namelist()}
        infos = {i.filename: i for i in zin.infolist()}

    env = Environment(autoescape=True)

    for nombre in ('content.xml', 'styles.xml'):
        if nombre not in partes:
            continue

        root = etree.fromstring(partes[nombre])

        if nombre == 'content.xml':
            insertados = _insertar_fragmentos(root, fragmentos_dir)
            if insertados:
                logger.debug('Fragmentos insertados: %s', ', '.join(insertados))

        _recomponer_tokens(root)

        xml = etree.tostring(root, encoding='unicode')
        xml = _elevar_bucles_de_fila(xml)
        xml = env.from_string(xml).render(**contexto)

        if nombre == 'styles.xml' and codigo_seguimiento:
            # Después de Jinja2 y sobre el árbol ya renderizado: el código es
            # dato, no plantilla.
            root = etree.fromstring(xml.encode('utf-8'))
            _inyectar_codigo(root, codigo_seguimiento)
            xml = etree.tostring(root, encoding='unicode')

        partes[nombre] = _con_declaracion_xml(xml)

    return _escribir_odt(partes, infos)


# ======================================================================
# Fragmentos
# ======================================================================

def validar_plantilla_odt(ruta_abs: str) -> str | None:
    """
    Comprueba que el fichero sea un .odt utilizable como plantilla.

    Mira las dos cosas que pueden fallar sin que se note hasta el momento de
    generar: que el ZIP traiga sus partes y estén bien formadas, y que la
    sintaxis Jinja2 compile. No se rellena nada — sin contexto no se puede—,
    así que un token con un nombre inventado pasa la validación; lo que no
    pasa es un `{% for %}` sin cerrar.

    Returns:
        str  — Mensaje de error, listo para enseñar al supervisor.
        None — La plantilla es válida.
    """
    env = Environment(autoescape=True)
    try:
        with zipfile.ZipFile(ruta_abs) as z:
            nombres = z.namelist()
            if 'content.xml' not in nombres:
                return 'El fichero no es un .odt: le falta content.xml.'
            for nombre in ('content.xml', 'styles.xml'):
                if nombre not in nombres:
                    continue
                root = etree.fromstring(z.read(nombre))
                xml = _elevar_bucles_de_fila(etree.tostring(root, encoding='unicode'))
                # Los marcadores de fragmento no son sintaxis Jinja2: los
                # resuelve el motor antes, así que aquí solo estorban.
                env.parse(RE_FRAGMENTO.sub('', xml))
    except zipfile.BadZipFile:
        return 'El fichero no es un .odt: no es un archivo comprimido válido.'
    except etree.XMLSyntaxError as e:
        return f'XML mal formado dentro del .odt: {e}'
    except Exception as e:
        return str(e)

    return None


def _insertar_fragmentos(root, directorio: str) -> list[str]:
    """
    Sustituye cada párrafo que contenga {{r Nombre }} por los bloques del
    fragmento correspondiente.

    Sustituir en vez de insertar dentro es la diferencia esencial con docxtpl:
    no queda párrafo contenedor cuyo formato herede el fragmento, ni bloques
    anidados que reparar después.

    Devuelve la lista de nombres insertados.
    """
    estilos_auto = root.find(f'{Q["office"]}automatic-styles')
    insertados = []

    for parrafo in list(root.iter(f'{Q["text"]}p')):
        nombres = RE_FRAGMENTO.findall(''.join(parrafo.itertext()))
        if not nombres:
            continue

        padre = parrafo.getparent()
        posicion = list(padre).index(parrafo)

        for nombre in nombres:
            ruta = os.path.join(directorio or '', f'{nombre}.odt')
            if not os.path.isfile(ruta):
                logger.warning(
                    'Fragmento "%s.odt" referenciado en plantilla pero no '
                    'encontrado en %s', nombre, directorio
                )
                continue

            bloques, estilos = _cargar_fragmento(ruta, f'frg{nombre}')
            if estilos_auto is not None:
                for e in estilos:
                    estilos_auto.append(e)
            for desplazamiento, bloque in enumerate(bloques):
                padre.insert(posicion + desplazamiento, bloque)
            posicion += len(bloques)
            insertados.append(nombre)

        # El párrafo del marcador desaparece: los bloques del fragmento ocupan
        # su sitio con su propio formato.
        padre.remove(parrafo)

    return insertados


def _cargar_fragmento(ruta_odt: str, prefijo: str):
    """
    Devuelve (bloques, estilos) de un fragmento .odt, con sus estilos
    automáticos renombrados con `prefijo` para que no choquen con los del
    documento destino.

    Si plantilla y fragmento derivan de la misma plantilla base (#727) el
    renombrado apenas tiene trabajo, porque los estilos con nombre propio
    viven en la base y no se duplican.
    """
    with zipfile.ZipFile(ruta_odt) as z:
        root = etree.fromstring(z.read('content.xml'))

    cuerpo = root.find(f'{Q["office"]}body/{Q["office"]}text')
    if cuerpo is None:
        return [], []

    estilos_auto = root.find(f'{Q["office"]}automatic-styles')
    estilos = [copy.deepcopy(e) for e in (estilos_auto if estilos_auto is not None else [])]
    bloques = [copy.deepcopy(b) for b in cuerpo
               if etree.QName(b).localname not in NO_CONTENIDO]

    mapa = {}
    for e in estilos:
        nombre = e.get(ATTR_NOMBRE)
        if nombre:
            mapa[nombre] = f'{prefijo}_{nombre}'

    for e in estilos:
        if e.get(ATTR_NOMBRE) in mapa:
            e.set(ATTR_NOMBRE, mapa[e.get(ATTR_NOMBRE)])
        _renombrar_referencias(e, mapa)
    for b in bloques:
        _renombrar_referencias(b, mapa)

    return bloques, estilos


def _renombrar_referencias(elemento, mapa: dict) -> None:
    """Reescribe en el árbol las referencias a los estilos renombrados."""
    for nodo in elemento.iter():
        for attr in ATTRS_REFERENCIA:
            valor = nodo.get(attr)
            if valor in mapa:
                nodo.set(attr, mapa[valor])


# ======================================================================
# Tokens partidos
# ======================================================================

def _recomponer_tokens(root) -> None:
    """
    Reúne en un solo nodo de texto los tokens que hayan quedado repartidos
    entre varios <text:span>.

    En ODT los tokens llegan enteros al XML mientras nadie los edite, pero en
    cuanto se cambia el formato a media palabra en Writer —o queda una marca
    de revisión ortográfica— `{{ titular }}` se parte y deja de ser un token.
    docxtpl invierte esfuerzo en lo mismo porque en OOXML pasa siempre.

    El texto del token se concentra en el primer nodo donde empieza, así que
    el resultado hereda el formato de ese primer trozo. Es lo mismo que hace
    docxtpl y lo único que se puede hacer sin adivinar la intención.
    """
    for parrafo in root.iter(f'{Q["text"]}p', f'{Q["text"]}h'):
        slots = _slots_de_texto(parrafo)
        if len(slots) < 2:
            continue

        completo = ''.join(texto for _, _, texto in slots)
        if '{' not in completo:
            continue

        # Frontera de cada slot dentro del texto concatenado
        limites, acumulado = [], 0
        for _, _, texto in slots:
            limites.append((acumulado, acumulado + len(texto)))
            acumulado += len(texto)

        # Se reescribe de atrás adelante para no invalidar los límites
        nuevos = [texto for _, _, texto in slots]
        cambiado = False
        for m in reversed(list(RE_TOKEN.finditer(completo))):
            afectados = [i for i, (ini, fin) in enumerate(limites)
                         if ini < m.end() and fin > m.start()]
            if len(afectados) < 2:
                continue

            # El token entero va al primer slot, donde empezaba. Lo que había
            # detrás del corte en ese slot era el principio del token, así que
            # no se pierde nada al sustituirlo.
            primero = afectados[0]
            corte = m.start() - limites[primero][0]
            nuevos[primero] = nuevos[primero][:corte] + m.group(0)

            # De los slots siguientes se recorta el trozo de token que traían;
            # lo que venga después del token se conserva.
            for i in afectados[1:]:
                nuevos[i] = nuevos[i][m.end() - limites[i][0]:]
            cambiado = True

        if not cambiado:
            continue

        for (elemento, atributo, _), texto in zip(slots, nuevos):
            if atributo == 'text':
                elemento.text = texto
            else:
                elemento.tail = texto


def _slots_de_texto(parrafo) -> list:
    """
    Devuelve los huecos de texto del párrafo en orden de lectura, como tuplas
    (elemento, 'text'|'tail', contenido).

    No entra en los párrafos anidados —los que viven dentro de un marco de
    texto colocado en este párrafo—: tienen su propio flujo y el iterador
    principal ya pasa por ellos. Sí se toma su cola, que sí es texto de este
    párrafo.
    """
    slots = []
    if parrafo.text:
        slots.append((parrafo, 'text', parrafo.text))

    def recorrer(elemento):
        for hijo in elemento:
            anidado = hijo.tag in (f'{Q["text"]}p', f'{Q["text"]}h')
            if not anidado:
                if hijo.text:
                    slots.append((hijo, 'text', hijo.text))
                recorrer(hijo)
            if hijo.tail:
                slots.append((hijo, 'tail', hijo.tail))

    recorrer(parrafo)
    return slots


# ======================================================================
# Bucles de fila
# ======================================================================

def _elevar_bucles_de_fila(xml: str) -> str:
    """
    Saca las etiquetas {%tr ... %} de su <table:table-row> y las deja delante.

    La etiqueta se teclea dentro de una celda porque es donde el supervisor
    puede escribirla, pero Jinja2 necesita verla fuera para repetir la fila.

    El comportamiento replica al de docxtpl a propósito: la etiqueta va
    *delante* de su fila, de modo que `{%tr for … %}` repite la fila que la
    contiene y `{%tr endfor %}` cierra antes de la suya. Es la convención que
    el panel de tokens le enseña al supervisor, y tiene que valer igual con
    plantillas .docx y .odt.
    """
    def procesar(match):
        fila = match.group(0)
        etiquetas = re.findall(r'\{%tr\s+(.+?)\s*%\}', fila)
        if not etiquetas:
            return fila
        limpia = re.sub(r'\{%tr\s+.+?\s*%\}', '', fila)
        return ''.join(f'{{% {e} %}}' for e in etiquetas) + limpia

    return re.sub(r'<table:table-row\b.*?</table:table-row>', procesar,
                  xml, flags=re.S)


# ======================================================================
# Código de seguimiento — gancho de #182
# ======================================================================

# Estilos del marco del código. Nombres con prefijo bddat para no chocar con
# los estilos automáticos de la plantilla (P1, T1, gr1…).
ESTILOS_CODIGO = '''
<style:style style:name="bddatGr" style:family="graphic">
  <style:graphic-properties style:protect="content position size"
      style:vertical-pos="from-top" style:vertical-rel="paragraph"
      style:horizontal-pos="from-left" style:horizontal-rel="paragraph"
      style:wrap="none" draw:fill="none" draw:stroke="none"
      fo:padding="0cm" fo:border="none"/>
</style:style>
<style:style style:name="bddatP" style:family="paragraph">
  <style:text-properties fo:font-size="7pt" style:font-name="Liberation Mono"
      fo:font-family="&apos;Liberation Mono&apos;"/>
</style:style>
'''

# Marco del código. `style:protect` es lo único que sobrevive a que Writer
# abra y guarde el fichero (ADR-035): conserva posición y tamaño.
FRAME_CODIGO = '''
<draw:frame draw:style-name="bddatGr" draw:name="CodigoSeguimientoBDDAT"
            text:anchor-type="paragraph" draw:z-index="1"
            svg:width="14cm" svg:height="0.6cm"
            svg:x="0cm" svg:y="0cm">
  <draw:text-box><text:p text:style-name="bddatP">{codigo}</text:p></draw:text-box>
</draw:frame>
'''


def _inyectar_codigo(styles_root, codigo: str) -> int:
    """
    Inserta el marco con el código de seguimiento en el pie de TODAS las master
    pages, y devuelve en cuántas lo hizo.

    Recorrer todas es el punto delicado (ADR-035 §3): una plantilla con primera
    página distinta tiene al menos dos master pages, y el código insertado en
    una sola no aparece en la otra. En la prueba de concepto se perdió
    justamente en la página 1. Es el equivalente a recorrer todas las secciones
    en OOXML.

    Los tokens no tienen ese problema: Jinja2 procesa styles.xml completo.

    GANCHO DE #182: este módulo pone el marco donde se ve y sobrevive al
    pipeline; la composición del código (id de instancia, dígito de control) y
    la decisión de si va en el pie o girado en el margen son de #182 y solo
    tocan `codigo` y `FRAME_CODIGO`.
    """
    estilos_auto = styles_root.find(f'{Q["office"]}automatic-styles')
    if estilos_auto is not None:
        for estilo in _xml_a_elementos(ESTILOS_CODIGO):
            estilos_auto.append(estilo)

    master_styles = styles_root.find(f'{Q["office"]}master-styles')
    if master_styles is None:
        logger.warning('styles.xml sin <office:master-styles>: código no inyectado')
        return 0

    frame_xml = FRAME_CODIGO.format(codigo=escape(codigo))
    inyectados = 0

    for master in master_styles.findall(f'{Q["style"]}master-page'):
        pie = master.find(f'{Q["style"]}footer')
        if pie is None:
            pie = etree.SubElement(master, f'{Q["style"]}footer')
            etree.SubElement(pie, f'{Q["text"]}p')

        parrafo = pie.find(f'{Q["text"]}p')
        if parrafo is None:
            parrafo = etree.SubElement(pie, f'{Q["text"]}p')

        # El marco va al principio del párrafo: los marcos deben preceder al
        # texto dentro de un <text:p>.
        parrafo.insert(0, _xml_a_elementos(frame_xml)[0])
        inyectados += 1

    if not inyectados:
        logger.warning('Ninguna master page en styles.xml: código no inyectado')

    return inyectados


# ======================================================================
# Utilidades de XML y de ZIP
# ======================================================================

def _xml_a_elementos(fragmento: str) -> list:
    """
    Parsea un fragmento XML suelto y devuelve sus elementos.

    Va envuelto en una raíz que declara todos los prefijos ODF, porque un
    fragmento aislado no los tiene declarados y lxml lo rechazaría.
    """
    declaraciones = ' '.join(f'xmlns:{p}="{u}"' for p, u in NS.items())
    raiz = etree.fromstring(f'<w {declaraciones}>{fragmento}</w>'.encode('utf-8'))
    return list(raiz)


def _con_declaracion_xml(xml: str) -> bytes:
    """Devuelve el XML como bytes UTF-8 con su declaración."""
    if not xml.lstrip().startswith('<?xml'):
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml
    return xml.encode('utf-8')


def _escribir_odt(partes: dict, infos: dict) -> bytes:
    """
    Reconstruye el ZIP del .odt.

    'mimetype' va primero y sin comprimir: lo exige ODF y es como los
    programas reconocen el formato sin descomprimir el fichero.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zout:
        if 'mimetype' in partes:
            zout.writestr('mimetype', partes.pop('mimetype'),
                          compress_type=zipfile.ZIP_STORED)
        for nombre, datos in partes.items():
            zout.writestr(infos.get(nombre, nombre), datos)
    return buffer.getvalue()


def _fragmentos_dir() -> str:
    """Directorio de fragmentos .odt dentro de PLANTILLAS_BASE."""
    from flask import current_app
    base = current_app.config.get('PLANTILLAS_BASE', '')
    return os.path.join(base, 'fragmentos') if base else ''
