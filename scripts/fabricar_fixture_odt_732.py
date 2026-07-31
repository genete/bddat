# -*- coding: utf-8 -*-
"""
Fabrica el fixture real de LibreOffice para #732: fija el contrato del motor
ODT (`generador_escritos_odt`) contra un .odt que ha pasado de verdad por
LibreOffice, no solo escrito a mano con zipfile como hacen los tests
sintéticos de #726 (`tests/test_726_renderizador_odt.py`).

    carta_base.odt (#727)     → [contenido de prueba] → [LibreOffice] → tests/fixtures/plantilla_732.odt
    fragmento_base.odt (#727) → [token propio]         → [LibreOffice] → tests/fixtures/Fundamentos732.odt

USO
    venv/Scripts/python.exe scripts/fabricar_fixture_odt_732.py

    Requiere LibreOffice instalado (ADR-035 requisito 1). La ruta de
    `soffice` se puede fijar con la variable de entorno SOFFICE.

POR QUÉ PARTIR DE CARTA_BASE Y NO DE UN .ODT EN BLANCO
    carta_base.odt (#727) ya trae, sin fabricar nada nuevo, el caso exacto que
    ADR-035 §3 señala como trampa: dos master pages con primera página
    distinta — MPF0 (primera) con cabecera Y pie propios, MP0 (siguientes)
    solo con cabecera. Es «el fixture natural» que señala el propio #732:
    reutilizarla evita fabricar dos veces el mismo fichero y de paso deja el
    fixture bajo la comprobación de canonicidad de #727.

QUÉ SE LE AÑADE
    - Token en el cuerpo (`numero_at`).
    - Token en la cabecera y el pie de LAS DOS master pages (`organo`,
      `sede.direccion`). MP0 no tenía pie: aquí se le crea uno, igual que
      tendría que hacerlo un supervisor en Writer si quisiera repetir un dato
      en todas las páginas.
    - Marcador de fragmento `{{r Fundamentos732 }}`.
    - Tabla con bucle de fila `{%tr ... %}` y párrafo con bucle `{%p ... %}`,
      con la misma sintaxis que el panel de tokens ofrece al supervisor.
    - Un fragmento real (derivado de `fragmento_base.odt`) con su propio
      token, para probar que se rellena ANTES de Jinja2 (ADR-035, #726).

POR QUÉ EL PASE FINAL POR SOFFICE
    Escribir XML con lxml y meterlo en un ZIP no es "un fichero real de
    LibreOffice": sería indistinguible de los tests sintéticos que #732
    señala como punto ciego. El `--convert-to odt` final fuerza a LibreOffice
    a reserializar el documento con su propio motor —mismo patrón que
    `fabricar_plantilla_base.py` usa para materializar la base canónica—, y
    dos condiciones dependen de que ese pase exista de verdad: MP0 recibe su
    pie tal y como LibreOffice lo escribiría, y `meta:generator` queda con la
    versión real de LibreOffice usada, no con un valor inventado.
"""
import os
import shutil
import subprocess
import tempfile
import zipfile

from lxml import etree

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASES_DIR = os.path.join(RAIZ, 'app', 'data', 'plantillas_base')
FIXTURES_DIR = os.path.join(RAIZ, 'tests', 'fixtures')

CARTA_BASE = os.path.join(BASES_DIR, 'carta_base.odt')
FRAGMENTO_BASE = os.path.join(BASES_DIR, 'fragmento_base.odt')

DESTINO_PLANTILLA = os.path.join(FIXTURES_DIR, 'plantilla_732.odt')
NOMBRE_FRAGMENTO = 'Fundamentos732'
DESTINO_FRAGMENTO = os.path.join(FIXTURES_DIR, f'{NOMBRE_FRAGMENTO}.odt')

TALLER = tempfile.mkdtemp(prefix='bddat_fixture_732_')
SOFFICE = os.environ.get(
    'SOFFICE', r'C:\Program Files\LibreOffice\program\soffice.com')
PERFIL = 'file:///' + TALLER.replace('\\', '/') + '/perfil'

NS = {
    'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
    'style':  'urn:oasis:names:tc:opendocument:xmlns:style:1.0',
    'text':   'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
    'table':  'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
    'draw':   'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0',
    'fo':     'urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0',
    'svg':    'urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0',
}
Q = {k: '{%s}' % v for k, v in NS.items()}


def elementos(fragmento):
    """Parsea un fragmento XML suelto (varios hermanos) y devuelve sus elementos."""
    decl = ' '.join(f'xmlns:{p}="{u}"' for p, u in NS.items())
    return list(etree.fromstring(f'<w {decl}>{fragmento}</w>'.encode('utf-8')))


def elemento(fragmento):
    return elementos(fragmento)[0]


def texto_de(nodo):
    return ''.join(nodo.itertext())


# ----------------------------------------------------------------------
# Contenido de prueba a insertar
# ----------------------------------------------------------------------

TABLA_BUCLE = '''
<table:table table:name="TablaMunicipios" table:style-name="TablaMunicipios">
  <table:table-column table:style-name="TablaMunicipios.A"/>
  <table:table-row table:style-name="TablaMunicipios.1">
    <table:table-cell table:style-name="TablaMunicipios.A1" office:value-type="string">
      <text:p text:style-name="Normal">{%tr for m in municipios %}{{ m }}</text:p>
    </table:table-cell>
  </table:table-row>
  <table:table-row table:style-name="TablaMunicipios.1">
    <table:table-cell table:style-name="TablaMunicipios.A1" office:value-type="string">
      <text:p text:style-name="Normal">{%tr endfor %}</text:p>
    </table:table-cell>
  </table:table-row>
</table:table>
'''

ESTILOS_TABLA_BUCLE = '''
<style:style style:name="TablaMunicipios" style:family="table">
  <style:table-properties style:width="16.688cm" fo:margin-top="0.25cm" fo:margin-bottom="0.25cm" table:align="left"/>
</style:style>
<style:style style:name="TablaMunicipios.A" style:family="table-column">
  <style:table-column-properties style:column-width="16.688cm"/>
</style:style>
<style:style style:name="TablaMunicipios.A1" style:family="table-cell">
  <style:table-cell-properties fo:padding="0.1cm" fo:border="0.5pt solid #000000"/>
</style:style>
'''

BUCLE_PARRAFO = '''
<text:p text:style-name="Normal">{%p for m in municipios %}</text:p>
<text:p text:style-name="Normal">{{ m }}</text:p>
<text:p text:style-name="Normal">{%p endfor %}</text:p>
'''


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


def escribir_odt(partes, ruta_salida):
    with zipfile.ZipFile(ruta_salida, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', partes.pop('mimetype'), compress_type=zipfile.ZIP_STORED)
        for nombre, datos in partes.items():
            z.writestr(nombre, datos)


def construir_plantilla(ruta_entrada, ruta_salida):
    with zipfile.ZipFile(ruta_entrada) as z:
        partes = {n: z.read(n) for n in z.namelist()}

    content = etree.fromstring(partes['content.xml'])
    styles = etree.fromstring(partes['styles.xml'])

    # --- content.xml: token en el cuerpo, marcador de fragmento, bucles ---
    cuerpo = None
    for p in content.iter(f'{Q["text"]}p'):
        if texto_de(p) == 'Cuerpo de texto del documento':
            cuerpo = p
            break
    if cuerpo is None:
        raise RuntimeError('carta_base.odt: no se encuentra el párrafo de cuerpo esperado')
    cuerpo.text = 'Expediente {{ numero_at }}.'

    padre = cuerpo.getparent()
    posicion = list(padre).index(cuerpo)
    nuevos = (
        [elemento(f'<text:p text:style-name="Normal">{{{{r {NOMBRE_FRAGMENTO} }}}}</text:p>')]
        + elementos(TABLA_BUCLE)
        + elementos(BUCLE_PARRAFO)
    )
    for i, nodo in enumerate(nuevos):
        padre.insert(posicion + 1 + i, nodo)

    estilos_auto = content.find(f'{Q["office"]}automatic-styles')
    for e in elementos(ESTILOS_TABLA_BUCLE):
        estilos_auto.append(e)

    # --- styles.xml: token en cabecera y pie de las DOS master pages ---
    master_mp0 = master_mpf0 = None
    for m in styles.iter(f'{Q["style"]}master-page'):
        nombre = m.get(f'{Q["style"]}name')
        if nombre == 'MP0':
            master_mp0 = m
        elif nombre == 'MPF0':
            master_mpf0 = m
    if master_mp0 is None or master_mpf0 is None:
        raise RuntimeError('carta_base.odt: no se encuentran las master pages MP0/MPF0')

    # MP0 (páginas siguientes): cabecera ya trae el logo; se añade un párrafo
    # con el token. Pie: no existía, se crea igual que tendría que hacerlo un
    # supervisor en Writer.
    header_mp0 = master_mp0.find(f'{Q["style"]}header')
    header_mp0.append(elemento('<text:p text:style-name="Header">{{ organo }}</text:p>'))
    footer_mp0 = etree.SubElement(master_mp0, f'{Q["style"]}footer')
    footer_mp0.append(elemento('<text:p text:style-name="Footer">{{ sede.direccion }}</text:p>'))

    # MPF0 (primera página): cabecera trae logo + tab; el token va tras el
    # tab, en el mismo párrafo. Pie: el cuadro de texto ya existente lleva
    # "Dirección Delegación" de muestra — se sustituye por el token, tal y
    # como describe ADR-035 §4 ("el cuadro ya dibujado en la plantilla... se
    # rellena como cualquier token").
    header_mpf0 = master_mpf0.find(f'{Q["style"]}header')
    p_header = header_mpf0.find(f'{Q["text"]}p')
    tab = p_header.find(f'{Q["text"]}tab')
    tab.tail = (tab.tail or '') + '{{ organo }}'

    footer_mpf0 = master_mpf0.find(f'{Q["style"]}footer')
    textbox = footer_mpf0.find(f'.//{Q["draw"]}text-box')
    primer_span = textbox.find(f'{Q["text"]}p/{Q["text"]}span')
    primer_span.text = '{{ sede.direccion }}'

    partes['content.xml'] = etree.tostring(content, xml_declaration=True, encoding='UTF-8')
    partes['styles.xml'] = etree.tostring(styles, xml_declaration=True, encoding='UTF-8')
    escribir_odt(partes, ruta_salida)


def construir_fragmento(ruta_entrada, ruta_salida):
    with zipfile.ZipFile(ruta_entrada) as z:
        partes = {n: z.read(n) for n in z.namelist()}

    content = etree.fromstring(partes['content.xml'])
    cuerpo = content.find(f'{Q["office"]}body/{Q["office"]}text')
    placeholder = cuerpo.find(f'{Q["text"]}p')
    placeholder.text = 'Fundamentos de Derecho de la resolución.'
    placeholder.addnext(
        elemento('<text:p text:style-name="Normal">Alegado por {{ titular }}.</text:p>'))

    partes['content.xml'] = etree.tostring(content, xml_declaration=True, encoding='UTF-8')
    escribir_odt(partes, ruta_salida)


os.makedirs(TALLER, exist_ok=True)
os.makedirs(FIXTURES_DIR, exist_ok=True)

print('\n1. Construir plantilla con contenido de prueba (antes del pase por LibreOffice)')
plantilla_intermedia = os.path.join(TALLER, 'plantilla_732_intermedia.odt')
construir_plantilla(CARTA_BASE, plantilla_intermedia)

print('\n2. Construir fragmento con contenido de prueba')
fragmento_intermedio = os.path.join(TALLER, f'{NOMBRE_FRAGMENTO}_intermedio.odt')
construir_fragmento(FRAGMENTO_BASE, fragmento_intermedio)

print('\n3. Pase final por LibreOffice real (fija el contrato del fixture)')
plantilla_final = convertir(plantilla_intermedia, os.path.join(TALLER, 'final_plantilla'), 'plantilla')
fragmento_final = convertir(fragmento_intermedio, os.path.join(TALLER, 'final_fragmento'), 'fragmento')

shutil.copy(plantilla_final, DESTINO_PLANTILLA)
shutil.copy(fragmento_final, DESTINO_FRAGMENTO)

print(f'\nResultado:\n   {DESTINO_PLANTILLA}\n   {DESTINO_FRAGMENTO}')
shutil.rmtree(TALLER, ignore_errors=True)
