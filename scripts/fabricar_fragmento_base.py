# -*- coding: utf-8 -*-
"""
Fabrica el fragmento base de BDDAT (#727, ADR-035 §5), derivado de
resolucion_base.odt: comparten la hoja de estilos, así que se parte de ahí en
vez de repetir el saneado.

    resolucion_base.odt → [editar] → [LibreOffice] → fragmento_base.odt

USO
    venv/Scripts/python.exe scripts/fabricar_fragmento_base.py

POR QUÉ DE RESOLUCIÓN Y NO DE LA CARTA
    El motor (`generador_escritos_odt._cargar_fragmento`) solo lee del fichero
    de fragmento `office:body/office:text` y `office:automatic-styles`: nunca
    fusiona `styles.xml`. Lo que hace que un fragmento encaje sin fusión es que
    el NOMBRE del estilo que use el supervisor exista también en la plantilla
    donde se inserte (ADR-035 §5). `resolucion_base.odt` tiene el superconjunto
    de estilos con nombre —los de la carta más los cuatro propios de la
    resolución (Título, Referencia, Sección, Firmante resolución)—, así que un
    fragmento nacido de ahí sirve para las dos familias.

QUÉ SE QUITA (nada de esto lo toca el motor al insertar un fragmento)
    - El cuerpo específico de la resolución (título, referencia, secciones,
      firma).
    - El marco `Image1` (logo) y el párrafo que ancla el membrete y cambia de
      master page: son de la plantilla, no del fragmento.
    - Las master pages `MP0`/`MPF0` y sus page-layouts (`Mpm2`/`Mpm3`): solo
      queda `Standard`/`Mpm1`, en blanco. Dejarlas sería peso muerto y, peor,
      confundiría al supervisor si abre el fragmento y ve un membrete que
      nunca va a aparecer donde lo inserte.

QUÉ SE CONSERVA
    Todos los estilos con nombre (párrafo, carácter, tabla) y las font-faces:
    es el catálogo que el supervisor usa para que su fragmento case con
    cualquier plantilla derivada de la misma base.
"""
import os
import shutil
import subprocess
import tempfile
import zipfile

from lxml import etree

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_BASE = os.path.join(RAIZ, 'app', 'data', 'plantillas_base')
ORIGEN = os.path.join(DIR_BASE, 'resolucion_base.odt')
DESTINO = os.path.join(DIR_BASE, 'fragmento_base.odt')

TALLER = tempfile.mkdtemp(prefix='bddat_fragmento_base_')
SOFFICE = os.environ.get(
    'SOFFICE', r'C:\Program Files\LibreOffice\program\soffice.com')
PERFIL = 'file:///' + TALLER.replace('\\', '/') + '/perfil'

NS = {
    'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
    'style': 'urn:oasis:names:tc:opendocument:xmlns:style:1.0',
    'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
    'meta': 'urn:oasis:names:tc:opendocument:xmlns:meta:1.0',
}
Q = {k: '{%s}' % v for k, v in NS.items()}

# Master pages y page-layouts propios de la plantilla, que el fragmento no usa.
MASTER_PAGES_FUERA = ('MP0', 'MPF0')
LAYOUTS_FUERA = ('Mpm2', 'Mpm3')

MARCA = {
    'BDDAT:plantilla-base': 'fragmento',
    'BDDAT:version-hoja-estilos': '1.0',
    'BDDAT:origen': 'Deriva de resolucion_base.odt (hoja de estilos común, ADR-035 §5)',
}


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

    # 1. El cuerpo entero se sustituye por un único párrafo marcador.
    cuerpo = content.find(f'{Q["office"]}body/{Q["office"]}text')
    for hijo in list(cuerpo):
        cuerpo.remove(hijo)
    marcador = etree.SubElement(cuerpo, f'{Q["text"]}p')
    marcador.set(f'{Q["text"]}style-name', 'Normal')
    marcador.text = '[Contenido del fragmento]'
    print('   cuerpo sustituido por un párrafo marcador (Normal)')

    # 2. Fuera las master pages y page-layouts propios de la plantilla.
    quitadas_mp, quitados_pl = 0, 0
    for master in list(styles.iter(f'{Q["style"]}master-page')):
        if master.get(f'{Q["style"]}name') in MASTER_PAGES_FUERA:
            master.getparent().remove(master)
            quitadas_mp += 1
    for layout in list(styles.iter(f'{Q["style"]}page-layout')):
        if layout.get(f'{Q["style"]}name') in LAYOUTS_FUERA:
            layout.getparent().remove(layout)
            quitados_pl += 1
    print(f'   quitadas {quitadas_mp} master page(s) y {quitados_pl} page-layout(s)')

    # 3. Marca de versión: distinta de la carta y la resolución.
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

print('\n1. Transformar sobre resolucion_base.odt')
editado = os.path.join(TALLER, 'fragmento_base.odt')
transformar(ORIGEN, editado)

print('\n2. Pasada por LibreOffice (punto fijo)')
final = convertir(editado, os.path.join(TALLER, 'final'), 'final')
shutil.copy(final, DESTINO)

print(f'\nResultado: {DESTINO}  ({os.path.getsize(DESTINO) / 1024:.0f} KB)')
shutil.rmtree(TALLER, ignore_errors=True)
