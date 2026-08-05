# -*- coding: utf-8 -*-
"""
Fabrica la plantilla base de RESOLUCIÓN de BDDAT (#727, ADR-035 §5), derivada de
carta_base.odt: comparten la misma hoja de estilos, así que se parte de ella en
vez de repetir el saneado desde la papelería oficial.

    carta_base.odt → [editar] → [LibreOffice] → resolucion_base.odt

USO
    venv/Scripts/python.exe scripts/fabricar_plantilla_resolucion.py

QUÉ CAMBIA RESPECTO A LA CARTA (decisiones de Carlos, 2026-07-30)
    - Sin tabla de Fecha/Destinatario/Ref./Asunto: una resolución no se dirige
      a nadie en el encabezamiento, va al expediente.
    - Sin cuadro de sede en el pie: las resoluciones se emiten sin él, en
      ninguna página (ni la primera ni las de continuación).
    - Cuerpo propio: título (12pt Bold), referencia de expediente justificada a
      la derecha, y tres secciones —Antecedentes de Hecho, Fundamentos de
      Derecho, Resuelve— con el mismo esquema: cabecera centrada en negrita y
      cuerpo en Normal. Firma centrada en página, dos líneas (cargo + nombre).
    - Título en mayúsculas por ESTILO, no por caracteres tecleados en mayúsculas
      (#728, ADR-039 §5): `BDDAT - Título resolución` lleva
      `fo:text-transform="uppercase"` (mayúsculas de ODF/LibreOffice, no
      destructivas — Formato → Carácter → Efectos, distinto de reescribir el
      texto). El rótulo de la Delegación Territorial que compondrá ese título
      (`organo_nombre`, #728) se guarda siempre en formato normal; solo en este
      encabezamiento se ve en mayúsculas, por estilo. Afecta únicamente a la
      resolución: la carta y su membrete (`carta_base.odt`) no se tocan.

QUÉ SE CONSERVA TAL CUAL (ADR-035 §4: el logo y el membrete no son cosa de esta
plantilla, y no hay razón para tocarlos)
    - El marco `Image1`: logo decorativo anclado a la página, independiente del
      membrete y del pie.
    - El párrafo que ancla el marco del membrete y activa el cambio de master
      page de la primera página (`style:master-page-name="MPF0"`). De las «dos
      líneas H6 - Anotaciones» que Carlos señaló como raras en Writer, solo
      esta es estructural; la otra —vacía, sin marco— es residuo y se quita.
    - Fuentes, font-faces y estilos con nombre de carta_base.odt: no se tocan.

PENDIENTE, A PROPÓSITO
    Estilo enumerado «PRIMERA.-, SEGUNDA.-…»: ODF/OOXML solo numeran de forma
    automática en dígitos, letras o romanos — no existe formato nativo que
    genere ordinales en palabra española, así que insertar o borrar un párrafo
    intermedio no renumera solo las palabras siguientes. Carlos decidió
    dejarlo para más adelante; no bloquea esta plantilla base.
"""
import os
import shutil
import subprocess
import tempfile
import zipfile

from lxml import etree

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_BASE = os.path.join(RAIZ, 'app', 'data', 'plantillas_base')
CARTA = os.path.join(DIR_BASE, 'carta_base.odt')
DESTINO = os.path.join(DIR_BASE, 'resolucion_base.odt')

TALLER = tempfile.mkdtemp(prefix='bddat_plantilla_resolucion_')
SOFFICE = os.environ.get(
    'SOFFICE', r'C:\Program Files\LibreOffice\program\soffice.com')
PERFIL = 'file:///' + TALLER.replace('\\', '/') + '/perfil'

NS = {
    'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
    'style': 'urn:oasis:names:tc:opendocument:xmlns:style:1.0',
    'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
    'fo': 'urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0',
    'draw': 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0',
    'meta': 'urn:oasis:names:tc:opendocument:xmlns:meta:1.0',
}
Q = {k: '{%s}' % v for k, v in NS.items()}

FUENTE = 'Source Sans Pro'
# «Espacio» (decisión de Carlos, sin valor dado): el doble del interpárrafo de
# la carta (0,25cm), para que se lea como un corte de sección y no como un
# párrafo más. Primer valor a ojo; se ajusta con la muestra impresa.
ESPACIO = '0.5cm'

ESTILOS_NUEVOS = f'''
<style:style style:name="BDDAT_20_-_20_Título_20_resolución"
             style:display-name="BDDAT - Título resolución"
             style:family="paragraph" style:parent-style-name="Normal">
  <style:paragraph-properties fo:margin-top="0cm" fo:margin-bottom="0cm"/>
  <style:text-properties fo:font-weight="bold" fo:font-size="12pt"
      fo:text-transform="uppercase"/>
</style:style>
<style:style style:name="BDDAT_20_-_20_Referencia_20_expediente"
             style:display-name="BDDAT - Referencia expediente"
             style:family="paragraph" style:parent-style-name="Normal">
  <style:paragraph-properties fo:text-align="end" fo:margin-top="0cm"
      fo:margin-bottom="0cm"/>
</style:style>
<style:style style:name="BDDAT_20_-_20_Sección_20_resolución"
             style:display-name="BDDAT - Sección resolución"
             style:family="paragraph" style:parent-style-name="Normal">
  <style:paragraph-properties fo:text-align="center" fo:margin-top="{ESPACIO}"
      fo:margin-bottom="{ESPACIO}"/>
  <style:text-properties fo:font-weight="bold"/>
</style:style>
<style:style style:name="BDDAT_20_-_20_Firmante_20_resolución"
             style:display-name="BDDAT - Firmante resolución"
             style:family="paragraph" style:parent-style-name="Normal">
  <style:paragraph-properties fo:text-align="center" fo:margin-top="{ESPACIO}"
      fo:margin-bottom="0cm" style:contextual-spacing="true"/>
  <style:text-properties fo:font-weight="bold"/>
</style:style>
'''

CUERPO_RESOLUCION = '''
<text:p text:style-name="BDDAT_20_-_20_Título_20_resolución">Resolución de la Delegación Territorial...</text:p>
<text:p text:style-name="BDDAT_20_-_20_Referencia_20_expediente">Ref: referencia de expediente</text:p>
<text:p text:style-name="BDDAT_20_-_20_Sección_20_resolución">ANTECEDENTES DE HECHO</text:p>
<text:p text:style-name="Normal">Texto de los antecedentes de hecho.</text:p>
<text:p text:style-name="BDDAT_20_-_20_Sección_20_resolución">FUNDAMENTOS DE DERECHO</text:p>
<text:p text:style-name="Normal">Texto de los fundamentos de derecho.</text:p>
<text:p text:style-name="BDDAT_20_-_20_Sección_20_resolución">RESUELVE</text:p>
<text:p text:style-name="Normal">Texto de la parte dispositiva.</text:p>
<text:p text:style-name="BDDAT_20_-_20_Firmante_20_resolución">Cargo del firmante</text:p>
<text:p text:style-name="BDDAT_20_-_20_Firmante_20_resolución">Nombre completo del firmante</text:p>
'''

MARCA = {
    'BDDAT:plantilla-base': 'resolucion',
    'BDDAT:version-hoja-estilos': '1.0',
    'BDDAT:origen': 'Deriva de carta_base.odt (hoja de estilos común, ADR-035 §5)',
}


def elementos(fragmento):
    decl = ' '.join(f'xmlns:{p}="{u}"' for p, u in NS.items())
    return list(etree.fromstring(f'<w {decl}>{fragmento}</w>'.encode('utf-8')))


def convertir(origen, destino_dir, etiqueta):
    os.makedirs(destino_dir, exist_ok=True)
    r = subprocess.run(
        [SOFFICE, f'-env:UserInstallation={PERFIL}', '--headless', '--norestore',
         '--convert-to', 'odt', '--outdir', destino_dir, origen],
        capture_output=True, timeout=300, text=True)
    if r.returncode != 0:
        raise RuntimeError(f'{etiqueta}: {r.stderr[:300]}')
    salida = os.path.join(
        destino_dir, os.path.splitext(os.path.basename(origen))[0] + '.odt')
    print(f'   {etiqueta}: {os.path.getsize(salida) / 1024:.0f} KB')
    return salida


def transformar(ruta_entrada, ruta_salida):
    with zipfile.ZipFile(ruta_entrada) as z:
        partes = {n: z.read(n) for n in z.namelist()}

    content = etree.fromstring(partes['content.xml'])
    styles = etree.fromstring(partes['styles.xml'])
    cuerpo = content.find(f'{Q["office"]}body/{Q["office"]}text')

    # 1. Quitar el párrafo H6-Anotaciones vacío (residuo) y la tabla de datos.
    #    Se conserva el <draw:frame Image1> y el párrafo que ancla el membrete
    #    (master-page-name=MPF0): son estructurales, no del cuerpo de la carta.
    quitados = {'residuo': 0, 'tabla': 0}
    for hijo in list(cuerpo):
        etiqueta = etree.QName(hijo).localname
        estilo = hijo.get(f'{Q["text"]}style-name')
        sin_frame = not list(hijo.iter(f'{Q["draw"]}frame'))
        vacio = not (hijo.text or '').strip()
        if etiqueta == 'p' and estilo == 'H6_20_-_20_Anotaciones' and sin_frame and vacio:
            cuerpo.remove(hijo)
            quitados['residuo'] += 1
        elif etiqueta == 'table':
            cuerpo.remove(hijo)
            quitados['tabla'] += 1
    print(f'   quitados: {quitados["residuo"]} párrafo(s) residuo, '
          f'{quitados["tabla"]} tabla(s)')

    # 2. El cuerpo de la carta (Normal + BDDAT - Firmante) se sustituye por el
    #    de la resolución. Se busca el <text:p style-name="Normal"> heredado
    #    de la carta (el único que queda tras el paso 1) y todo lo que le siga.
    marcador = None
    for hijo in cuerpo:
        if (hijo.get(f'{Q["text"]}style-name') or '').endswith('Normal') \
                and etree.QName(hijo).localname == 'p':
            marcador = hijo
            break
    if marcador is None:
        raise RuntimeError('No se encuentra el párrafo "Normal" de la carta base')

    padre = marcador.getparent()
    posicion = list(padre).index(marcador)
    for hijo in list(padre)[posicion:]:
        padre.remove(hijo)
    for e in elementos(CUERPO_RESOLUCION):
        padre.append(e)
    print('   cuerpo sustituido por el esquema de resolución')

    # 3. Estilos nuevos.
    office_styles = styles.find(f'{Q["office"]}styles')
    for e in elementos(ESTILOS_NUEVOS):
        office_styles.append(e)
    print('   estilos añadidos: Título resolución, Referencia expediente, '
          'Sección resolución, Firmante resolución')

    # 4. Sin cuadro de sede: se quita el <style:footer> de MPF0 (única master
    #    page que lo llevaba; MP0 ya no tenía).
    quitado_pie = 0
    for master in styles.iter(f'{Q["style"]}master-page'):
        if master.get(f'{Q["style"]}name') != 'MPF0':
            continue
        pie = master.find(f'{Q["style"]}footer')
        if pie is not None:
            master.remove(pie)
            quitado_pie += 1
    print(f'   pie de sede quitado de {quitado_pie} master page(s)')

    # 5. Marca de versión: distinta de la carta, mismo esquema.
    meta = etree.fromstring(partes['meta.xml'])
    om = meta.find(f'{Q["office"]}meta')
    for e in om.findall(f'{Q["meta"]}user-defined'):
        om.remove(e)
    for clave, valor in MARCA.items():
        ud = etree.SubElement(om, f'{Q["meta"]}user-defined')
        ud.set(f'{Q["meta"]}name', clave)
        ud.text = valor
    partes['meta.xml'] = etree.tostring(meta, xml_declaration=True, encoding='UTF-8')

    partes['content.xml'] = etree.tostring(content, xml_declaration=True, encoding='UTF-8')
    partes['styles.xml'] = etree.tostring(styles, xml_declaration=True, encoding='UTF-8')

    with zipfile.ZipFile(ruta_salida, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', partes.pop('mimetype'), compress_type=zipfile.ZIP_STORED)
        for nombre, datos in partes.items():
            z.writestr(nombre, datos)


os.makedirs(TALLER, exist_ok=True)
os.makedirs(DIR_BASE, exist_ok=True)

print('\n1. Transformar sobre carta_base.odt')
editado = os.path.join(TALLER, 'resolucion_base.odt')
transformar(CARTA, editado)

print('\n2. Pasada por LibreOffice (punto fijo, fixture real para #732)')
final = convertir(editado, os.path.join(TALLER, 'final'), 'final')
shutil.copy(final, DESTINO)

print(f'\nResultado: {DESTINO}  ({os.path.getsize(DESTINO) / 1024:.0f} KB)')
shutil.rmtree(TALLER, ignore_errors=True)
