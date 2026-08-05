# -*- coding: utf-8 -*-
"""
Fabrica la plantilla base canónica de escritos de BDDAT (#727, ADR-035 §5).

    papelería oficial → [LibreOffice] → saneado → [LibreOffice] → carta_base.odt

USO
    venv/Scripts/python.exe scripts/fabricar_plantilla_base.py

    Requiere LibreOffice instalado (ya lo es de BDDAT, ADR-035 requisito 1). La
    ruta de `soffice` se puede fijar con la variable de entorno SOFFICE.

PARA QUÉ SIRVE
    La Junta publica su papelería en https://juntadeandalucia.es/identidad. Ese
    documento NO es directamente utilizable como plantilla de BDDAT, y este
    script deja constancia ejecutable de qué hay que corregirle. Cuando la Junta
    publique una versión nueva, se sustituye el fichero de `origen_jda/` y se
    vuelve a ejecutar, en vez de repetir la investigación a mano.

POR QUÉ CONVERTIR ANTES DE SANEAR
    LibreOffice materializa al guardar sus estilos base (`Standard`, `Heading`,
    `Text body`) con SU fuente por defecto —medido: Liberation Sans— y traduce
    los nombres internos de los estilos estándar (`Título 1` → `Heading 1`).
    Saneando después se trabaja sobre el fichero que LibreOffice deja de verdad,
    y no sobre uno que él va a rehacer.

    La segunda conversión no es adorno: comprueba que el resultado es un punto
    fijo, o sea que abrir y guardar en Writer —lo que hará el supervisor— no
    reintroduce fuentes ajenas.

QUÉ SE LE CORRIGE AL DOCUMENTO OFICIAL, Y POR QUÉ
    1. `default-style` declara Calibri. La identidad corporativa manda Source
       Sans Pro, así que cualquier párrafo que se teclee sin aplicar estilo salía
       con una fuente que no es la de la Junta.
    2. `Standard` no declara fuente: si se deja el hueco, Writer lo rellena con
       Liberation Sans en cuanto alguien abre y guarda.
    3. Conviven dos font-faces que solo difieren en mayúsculas («Source Sans Pro
       SemiBold» y «...semibold»), y LibreOffice desdobla la misma fuente en «X»
       y «X1» según los usos lleven o no `style:font-pitch`.
    4. La familia «Formulario - *» está montada al revés: `Datos` hereda de
       `Títulos` (verde, Bold, 12 pt) y declara un rojo que TODOS sus usos anulan
       con formato directo; y `Formulario - Destinatario` —el estilo pensado para
       la celda del destinatario— está huérfano. Medido en la página 68 del
       Manual de Identidad (marzo 2025): el destinatario va en #007933, que es el
       verde del estilo huérfano, no el #367d3c que llegaba por formato directo.
    5. El firmante vive en un cuadro de texto flotante con coordenadas absolutas.
       Medido en un requerimiento de dos páginas: el cuerpo acababa en y=112,2 mm
       y el firmante aparecía en y=207,3, con casi diez centímetros de vacío.
    6. Espaciado del cuerpo: ver INTERPARRAFO y ARRANQUE_CUERPO más abajo.
    7. `meta.xml` trae el nombre de la persona que hizo el documento en la Junta.
    8. La segunda línea del membrete (el hueco para «Nombre completo de la
       Delegación Territorial») llevaba el estilo genérico `Cabecera - Centro
       directivo`, sin nombre propio ni mayúsculas — #728, ADR-039 §5: en las
       resoluciones ese rótulo va en mayúsculas de estilo (no destructivas).

    Y se añade lo que la hoja oficial no tiene: la marca de versión de ADR-035 §5,
    el estilo `BDDAT - Firmante` y el estilo `Cabecera - Delegación Territorial`
    (#728, ADR-039 §5).

NOTA SOBRE CAMBRIA
    Medido en esta misma investigación: de siete fuentes probadas, Cambria es la
    única que rompe el texto extraíble del PDF —los acentos salen descompuestos,
    'Cá \\x03diz' en vez de 'Cádiz'—, porque está instalada como TrueType
    Collection. Es la fuente por defecto de los documentos heredados de Word, de
    donde viene el defecto que ADR-035 §5 atribuía a «no declarar fuente».
"""
import os
import shutil
import subprocess
import tempfile
import zipfile

from lxml import etree

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO_DIR = os.path.join(RAIZ, 'app', 'data', 'plantillas_base')
ORIGEN = os.path.join(DESTINO_DIR, 'origen_jda',
                      'Carta_DelegacionesTerritoriales_JuntaAndalucia.odt')
DESTINO = os.path.join(DESTINO_DIR, 'carta_base.odt')

TALLER = tempfile.mkdtemp(prefix='bddat_plantilla_base_')
SOFFICE = os.environ.get(
    'SOFFICE', r'C:\Program Files\LibreOffice\program\soffice.com')
PERFIL = 'file:///' + TALLER.replace('\\', '/') + '/perfil'

NS = {
    'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
    'style': 'urn:oasis:names:tc:opendocument:xmlns:style:1.0',
    'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
    'fo': 'urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0',
    'svg': 'urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0',
    'draw': 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0',
    'meta': 'urn:oasis:names:tc:opendocument:xmlns:meta:1.0',
    'dc': 'http://purl.org/dc/elements/1.1/',
}
Q = {k: '{%s}' % v for k, v in NS.items()}

FUENTE = 'Source Sans Pro'
CORPORATIVAS = {'Source Sans Pro', 'Source Sans Pro Bold',
                'Source Sans Pro Light', 'Source Sans Pro SemiBold'}
# Estilos de viñeta heredados de Word: su fuente es el glifo del bullet
# (Wingdings, Symbol, Courier New). Tocarlas rompería las listas.
def es_vineta(nombre):
    return nombre.startswith('WW_') or nombre == 'Graphics'


BORRAR = [
    'FAX_20_-_20_Datos', 'FAX_20_-_20_Mensaje',
    'Invitación_20_-_20_Título', 'Invitación_20_-_20_Texto',
    'Invitación_20_-_20_Cierre', 'Invitación_20_-_20_Nombre_20_y_20_apellidos',
    'Invitación_20_-_20_Cargo_20_completo',
    'Tabla_20_-_20_Check_20_List', 'Formulario_20_-_20_Comu._20_Datos',
]

MARCA = {
    'BDDAT:plantilla-base': 'carta',
    'BDDAT:version-hoja-estilos': '1.0',
    'BDDAT:origen': 'JdA identidad corporativa — 2.3.4 Carta Delegaciones Territoriales',
}

# El firmante va EN EL FLUJO del texto, no en un cuadro flotante. El original lo
# tenía anclado al párrafo con svg:x/svg:y absolutos, así que su posición no
# dependía de dónde acabase el cuerpo: medido en un requerimiento de dos páginas,
# el texto terminaba en y=112,2 mm y el firmante aparecía en y=207,3 — casi diez
# centímetros de vacío. Como párrafo, fluye siempre detrás del cuerpo.
# La sangría izquierda de 10,22 cm lo sitúa en x=122,2 mm (margen de 20 + 102,2),
# que es la columna donde la ficha 2.3.4 coloca la zona de firma.
# Peso Regular, heredado de «Normal»: el manual no destaca el firmante, y el
# nombre se compondrá en mayúsculas desde el dato, como en los escritos actuales.
# El estilo aporta solo posición.
FIRMANTE = f'''
<style:style style:name="BDDAT_20_-_20_Firmante" style:display-name="BDDAT - Firmante"
             style:family="paragraph" style:parent-style-name="Normal">
  <style:paragraph-properties fo:margin-left="10.22cm" fo:margin-top="1.5cm"
      fo:text-align="start" fo:text-indent="0cm"/>
</style:style>
'''

# #728, ADR-039 §5 — la papelería oficial trae la segunda línea del membrete
# (el hueco de "Nombre completo de la Delegación Territorial") con el estilo
# genérico "Cabecera - Centro directivo": no existe un estilo con nombre
# propio para la Delegación Territorial, y en las resoluciones ese rótulo va
# en mayúsculas. Hereda de "Cabecera - Centro directivo" (mismo tipo/tamaño/
# espaciado) y solo añade fo:text-transform="uppercase" — mayúsculas de
# ODF/LibreOffice (Formato → Carácter → Efectos), no destructivo: el dato
# subyacente se guarda siempre en formato normal.
DELEGACION_TERRITORIAL = '''
<style:style style:name="Cabecera_20_-_20_Delegación_20_Territorial"
             style:display-name="Cabecera - Delegación Territorial"
             style:family="paragraph"
             style:parent-style-name="Cabecera_20_-_20_Centro_20_directivo"
             style:auto-update="true">
  <style:text-properties fo:text-transform="uppercase"/>
</style:style>
'''

# Espaciado medido sobre el ejemplo de la página 68 del Manual de Identidad
# (marzo 2025), deshaciendo la escala de la maqueta (45,55%, deducida de los
# 102 mm de retícula que ocupan 131,7 pt impresos):
#   interlineado      5,7 pt impresos → 12,5 pt reales = el natural de la fuente
#                     para 10,5 pt de cuerpo. El manual NO amplía el interlineado.
#   salto de párrafo  9,0 pt impresos → 19,8 pt reales, o sea 1,58× el interlineado
#   luego el margen entre párrafos es 19,8 − 12,5 = 7,2 pt = 0,25 cm
INTERPARRAFO = '0.25cm'
# El cuerpo arranca en y=89,5 mm: lo dice la ficha 2.3.4 («Contenido de la carta»)
# y lo confirma el ejemplo del manual (saludo en 89,5 mm). Ese hueco se lo damos
# a la TABLA de datos, no al primer párrafo: así todo el cuerpo usa «Normal» y no
# hay un primer párrafo con reglas propias que el tramitador deba recordar —ni que
# separe distinto del resto, que es lo que pasaba con P7 y su margin-bottom a cero.
ARRANQUE_CUERPO = '0.33cm'


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


def elementos(fragmento):
    decl = ' '.join(f'xmlns:{p}="{u}"' for p, u in NS.items())
    return list(etree.fromstring(f'<w {decl}>{fragmento}</w>'.encode('utf-8')))


def declarar_fuente(estilo, fuente=FUENTE):
    tp = estilo.find(f'{Q["style"]}text-properties')
    if tp is None:
        tp = etree.SubElement(estilo, f'{Q["style"]}text-properties')
    tp.set(f'{Q["style"]}font-name', fuente)
    tp.set(f'{Q["fo"]}font-family', f"'{fuente}'")


def sanear(ruta_entrada, ruta_salida):
    with zipfile.ZipFile(ruta_entrada) as z:
        partes = {n: z.read(n) for n in z.namelist()}

    # Unificar la font-face que solo difiere en mayúsculas
    for n in ('styles.xml', 'content.xml'):
        partes[n] = partes[n].decode('utf-8').replace(
            'Source Sans Pro semibold', 'Source Sans Pro SemiBold').encode('utf-8')

    styles = etree.fromstring(partes['styles.xml'])
    content = etree.fromstring(partes['content.xml'])

    # 1. default-style
    default = styles.find(f'{Q["office"]}styles/{Q["style"]}default-style'
                          f'[@{Q["style"]}family="paragraph"]')
    tp = default.find(f'{Q["style"]}text-properties')
    previa = tp.get(f'{Q["style"]}font-name')
    tp.set(f'{Q["style"]}font-name', FUENTE)
    tp.set(f'{Q["fo"]}font-family', f"'{FUENTE}'")
    tp.set(f'{Q["style"]}font-name-asian', FUENTE)
    print(f'   default-style: {previa} → {FUENTE}')

    # 2. Todo estilo latino que no sea de viñeta usa fuente corporativa
    office_styles = styles.find(f'{Q["office"]}styles')
    corregidos = []
    for e in office_styles.iter(f'{Q["style"]}style'):
        nombre = e.get(f'{Q["style"]}name') or ''
        if es_vineta(nombre):
            continue
        tpe = e.find(f'{Q["style"]}text-properties')
        actual = tpe.get(f'{Q["style"]}font-name') if tpe is not None else None
        if actual is not None and actual not in CORPORATIVAS:
            declarar_fuente(e)
            corregidos.append(f'{nombre.replace("_20_", " ")} ({actual})')
    # Los estilos raíz de LibreOffice deben declararla aunque no la tuvieran:
    # si se deja el hueco, Writer lo rellena con Liberation Sans al guardar.
    for raiz in ('Standard', 'Heading', 'Text_20_body'):
        e = office_styles.find(f'{Q["style"]}style[@{Q["style"]}name="{raiz}"]')
        if e is not None:
            tpe = e.find(f'{Q["style"]}text-properties')
            if tpe is None or tpe.get(f'{Q["style"]}font-name') not in CORPORATIVAS:
                declarar_fuente(e)
                corregidos.append(f'{raiz.replace("_20_", " ")} (raíz)')
    print(f'   estilos con fuente corregida: {len(corregidos)}')
    for c in corregidos:
        print(f'      {c}')

    # 2 ter. La familia «Formulario - *» viene mal montada de origen:
    #   Formulario - Títulos  (verde #367d3c, Bold, 12 pt)   → 0 usos
    #   Formulario - Datos    (hijo del anterior, ROJO #c9211e) → 0 usos
    #   Formulario - Destinatario (verde #007942)            → 0 usos: huérfano
    # y lo que se aplica son automáticos hijos de «Datos» que tapan el rojo con
    # formato directo: negro para Fecha/Ref./Asunto y verde #367d3c para el
    # destinatario. Medido en la página 68 del manual, el destinatario va en
    # #007933 —el verde del estilo huérfano, no el #367d3c— y las etiquetas en
    # el mismo gris del cuerpo. Se aplican, pues, los estilos con nombre.
    COLOR_CUERPO = '#21211e'
    destinatario = office_styles.find(
        f'{Q["style"]}style[@{Q["style"]}name="Formulario_20_-_20_Destinatario"]')
    if destinatario is not None:
        destinatario.set(f'{Q["style"]}parent-style-name', 'Formulario_20_-_20_Datos')
        print('   «Formulario - Destinatario» pasa a ser hijo de «Formulario - Datos»')

    datos = office_styles.find(
        f'{Q["style"]}style[@{Q["style"]}name="Formulario_20_-_20_Datos"]')
    if datos is not None:
        tpd = datos.find(f'{Q["style"]}text-properties')
        if tpd is not None:
            rojo = tpd.get(f'{Q["fo"]}color')
            tpd.set(f'{Q["fo"]}color', COLOR_CUERPO)
            print(f'   «Formulario - Datos»: color {rojo} → {COLOR_CUERPO}')

    # Los automáticos se reparten por el color con que tapaban al padre
    reparto = {'verde': 0, 'etiqueta': 0}
    autos = {e.get(f'{Q["style"]}name'): e for e in content.iter(f'{Q["style"]}style')
             if e.get(f'{Q["style"]}parent-style-name') == 'Formulario_20_-_20_Datos'}
    destino = {}
    for nombre_auto, e in autos.items():
        tpa = e.find(f'{Q["style"]}text-properties')
        color = tpa.get(f'{Q["fo"]}color') if tpa is not None else None
        if color and color.lower() == '#367d3c':
            destino[nombre_auto] = 'Formulario_20_-_20_Destinatario'
            reparto['verde'] += 1
        else:
            destino[nombre_auto] = 'Formulario_20_-_20_Datos'
            reparto['etiqueta'] += 1
    for p in content.iter(f'{Q["text"]}p'):
        actual = p.get(f'{Q["text"]}style-name')
        if actual in destino:
            p.set(f'{Q["text"]}style-name', destino[actual])
    print(f'   automáticos sustituidos: {reparto["verde"]} → Destinatario, '
          f'{reparto["etiqueta"]} → Datos')

    # 3. Estilos fuera del subconjunto
    borrados = 0
    for e in list(office_styles):
        if e.tag == f'{Q["style"]}style' and e.get(f'{Q["style"]}name') in BORRAR:
            office_styles.remove(e)
            borrados += 1
    print(f'   estilos borrados: {borrados}')

    # 4. Estilos propios de BDDAT
    for e in elementos(FIRMANTE):
        office_styles.append(e)
    for e in elementos(DELEGACION_TERRITORIAL):
        office_styles.append(e)

    # 4 ter. La segunda línea del membrete ("Nombre completo de la Delegación
    # Territorial") pasa del estilo genérico "Cabecera - Centro directivo" al
    # nuevo "Cabecera - Delegación Territorial" (#728, ADR-039 §5). El
    # automático que la porta NO tiene nombre estable entre pasadas de
    # LibreOffice (medido: "P3" cae en un estilo distinto según la ejecución),
    # así que se localiza por el TEXTO del párrafo, no por el nombre del
    # automático, y solo se retoca si su padre es el esperado (salvaguarda).
    parrafo_membrete = None
    for p in content.iter(f'{Q["text"]}p'):
        if ''.join(p.itertext()).strip() == 'Nombre completo de la Delegación Territorial':
            parrafo_membrete = p
            break
    if parrafo_membrete is None:
        print('   AVISO: no se encuentra el párrafo del membrete de la Delegación Territorial — revisar a mano')
    else:
        nombre_auto = parrafo_membrete.get(f'{Q["text"]}style-name')
        automatico = content.find(
            f'{Q["office"]}automatic-styles/'
            f'{Q["style"]}style[@{Q["style"]}name="{nombre_auto}"]')
        if automatico is not None and automatico.get(f'{Q["style"]}parent-style-name') == 'Cabecera_20_-_20_Centro_20_directivo':
            automatico.set(f'{Q["style"]}parent-style-name', 'Cabecera_20_-_20_Delegación_20_Territorial')
            print(f'   membrete: {nombre_auto} (segunda línea) → "Cabecera - Delegación Territorial"')
        else:
            padre_actual = automatico.get(f'{Q["style"]}parent-style-name') if automatico is not None else '(automático no encontrado)'
            print(f'   AVISO: el automático "{nombre_auto}" del membrete no tiene el padre esperado '
                  f'(tiene: {padre_actual}) — revisar a mano')
    # El cuadro flotante del firmante desaparece; su texto pasa a ser un párrafo
    # normal, colocado detrás del párrafo al que el marco estaba anclado.
    quitados, texto_firma = 0, 'Nombre del firmante,'
    for frame in list(content.iter(f'{Q["draw"]}frame')):
        contenido = ' '.join(t.strip() for t in frame.itertext() if t.strip())
        if 'firmante' not in contenido.lower():
            continue
        texto_firma = contenido
        ancla = frame.getparent()          # el <text:p> que lo contiene
        abuelo = ancla.getparent()
        # El texto que sigue al marco dentro del párrafo es su `tail`, y lxml lo
        # descarta al hacer remove(). Aquí ese tail es «Cuerpo de texto del
        # documento», el texto de muestra que marca dónde va el cuerpo.
        cola = frame.tail
        ancla.remove(frame)
        if cola and cola.strip():
            ancla.text = (ancla.text or '') + cola
        nuevo = etree.SubElement(abuelo, f'{Q["text"]}p')
        nuevo.set(f'{Q["text"]}style-name', 'BDDAT_20_-_20_Firmante')
        nuevo.text = texto_firma
        abuelo.insert(list(abuelo).index(ancla) + 1, nuevo)
        quitados += 1
    print(f'   firmante: {quitados} cuadro(s) flotante(s) → párrafo en el flujo '
          f'(«{texto_firma}»)')

    # 3 bis. El logo decorativo «Image1» (Hércules/columnas/leones, anclado a la
    # página cerca del borde inferior) no llevaba margen de ajuste de texto: el
    # cuerpo podía llegar a tocarlo. En la carta no se nota —el pie de sede alto
    # reservaba ese hueco de rebote—, pero al quitar el pie en la resolución
    # (#727) el cuerpo queda libre para acercarse. El margen va en el propio
    # marco, no en la página: así protege en cualquier plantilla derivada,
    # tenga pie o no.
    for frame in content.iter(f'{Q["draw"]}frame'):
        if frame.get(f'{Q["draw"]}name') != 'Image1':
            continue
        nombre_estilo = frame.get(f'{Q["draw"]}style-name')
        estilo_grafico = content.find(
            f'{Q["office"]}automatic-styles/'
            f'{Q["style"]}style[@{Q["style"]}name="{nombre_estilo}"]')
        if estilo_grafico is None:
            print(f'   AVISO: no se encuentra el estilo gráfico "{nombre_estilo}" de Image1')
            break
        gp = estilo_grafico.find(f'{Q["style"]}graphic-properties')
        gp.set(f'{Q["style"]}wrap', 'parallel')
        for lado in ('left', 'right', 'top', 'bottom'):
            gp.set(f'{Q["fo"]}margin-{lado}', '0.4cm')
        print(f'   margen de 0,4cm alrededor de Image1 (estilo "{nombre_estilo}")')
        break

    # 4 bis. Espaciado del cuerpo, con los valores medidos del manual.
    # «Normal» manda en todo el cuerpo: margen inferior para separar párrafos e
    # interlineado natural (se retira cualquier fo:line-height heredado).
    normal = office_styles.find(f'{Q["style"]}style[@{Q["style"]}name="Normal"]')
    pp = normal.find(f'{Q["style"]}paragraph-properties')
    if pp is None:
        pp = etree.SubElement(normal, f'{Q["style"]}paragraph-properties')
    pp.set(f'{Q["fo"]}margin-top', '0cm')
    pp.set(f'{Q["fo"]}margin-bottom', INTERPARRAFO)
    if pp.get(f'{Q["fo"]}line-height'):
        del pp.attrib[f'{Q["fo"]}line-height']
    print(f'   «Normal»: interpárrafo {INTERPARRAFO}, interlineado natural')

    # El primer párrafo del cuerpo pasa a «Normal» como todos los demás. El
    # automático P7 imponía fo:margin-top de 1,411 cm y fo:margin-bottom de 0: de
    # ahí que el cuerpo arrancase 10,8 mm por debajo de la ficha y que entre el
    # primer párrafo y el segundo no hubiera separación ninguna.
    cambiados = 0
    for p in content.iter(f'{Q["text"]}p'):
        if p.get(f'{Q["text"]}style-name') == 'P7':
            p.set(f'{Q["text"]}style-name', 'Normal')
            cambiados += 1
    print(f'   primer párrafo del cuerpo: P7 → Normal ({cambiados})')

    # El hueco hasta el cuerpo lo da la tabla de datos (Fecha / Ref. / Asunto),
    # que es parte de la plantilla y no del texto que se teclea.
    tablas = 0
    for est in content.iter(f'{Q["style"]}style'):
        if est.get(f'{Q["style"]}family') != 'table':
            continue
        tp = est.find(f'{Q["style"]}table-properties')
        if tp is None:
            tp = etree.SubElement(est, f'{Q["style"]}table-properties')
        tp.set(f'{Q["fo"]}margin-bottom', ARRANQUE_CUERPO)
        tablas += 1
    print(f'   hueco hasta el cuerpo ({ARRANQUE_CUERPO}) puesto en {tablas} tabla(s)')

    # 5. Font-faces: deduplicar por FUENTE REAL (svg:font-family), no por nombre.
    #    LibreOffice desdobla la misma fuente en «X» y «X1» cuando unos usos
    #    llevan style:font-pitch y otros no.
    for raiz in (styles, content):
        decls = raiz.find(f'{Q["office"]}font-face-decls')
        if decls is None:
            continue
        canonico, renombrar = {}, {}
        for ff in list(decls):
            familia = ff.get(f'{Q["svg"]}font-family')
            nombre = ff.get(f'{Q["style"]}name')
            if familia in canonico:
                renombrar[nombre] = canonico[familia]
                decls.remove(ff)
            else:
                canonico[familia] = nombre
        if renombrar:
            for nodo in raiz.iter():
                for attr, valor in list(nodo.attrib.items()):
                    if attr.endswith('font-name') and valor in renombrar:
                        nodo.set(attr, renombrar[valor])
            print(f'   font-faces fusionadas: {renombrar}')

    partes['styles.xml'] = etree.tostring(styles, xml_declaration=True, encoding='UTF-8')
    partes['content.xml'] = etree.tostring(content, xml_declaration=True, encoding='UTF-8')

    # 6. Font-faces sin uso
    todo = partes['styles.xml'].decode('utf-8') + partes['content.xml'].decode('utf-8')
    styles = etree.fromstring(partes['styles.xml'])
    decls = styles.find(f'{Q["office"]}font-face-decls')
    sin_uso = []
    for ff in list(decls if decls is not None else []):
        nombre = ff.get(f'{Q["style"]}name')
        if f'font-name="{nombre}"' not in todo and f'font-name-asian="{nombre}"' not in todo \
                and f'font-name-complex="{nombre}"' not in todo:
            decls.remove(ff)
            sin_uso.append(nombre)
    print(f'   font-faces sin uso eliminadas: {sin_uso or "(ninguna)"}')
    partes['styles.xml'] = etree.tostring(styles, xml_declaration=True, encoding='UTF-8')

    # 7. meta.xml: autoría fuera, marca dentro
    meta = etree.fromstring(partes['meta.xml'])
    om = meta.find(f'{Q["office"]}meta')
    for etiqueta in (f'{Q["meta"]}initial-creator', f'{Q["dc"]}creator',
                     f'{Q["meta"]}editing-cycles', f'{Q["meta"]}editing-duration',
                     f'{Q["dc"]}date', f'{Q["meta"]}creation-date'):
        for e in om.findall(etiqueta):
            om.remove(e)
    for e in om.findall(f'{Q["meta"]}user-defined'):
        om.remove(e)
    for clave, valor in MARCA.items():
        ud = etree.SubElement(om, f'{Q["meta"]}user-defined')
        ud.set(f'{Q["meta"]}name', clave)
        ud.text = valor
    partes['meta.xml'] = etree.tostring(meta, xml_declaration=True, encoding='UTF-8')
    print('   autoría limpiada y marca de versión escrita')

    with zipfile.ZipFile(ruta_salida, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', partes.pop('mimetype'), compress_type=zipfile.ZIP_STORED)
        for nombre, datos in partes.items():
            z.writestr(nombre, datos)


def fuentes_latinas(ruta):
    """{fuente real: [estilos que la usan]}, ignorando las de viñeta."""
    with zipfile.ZipFile(ruta) as z:
        piezas = [z.read('styles.xml'), z.read('content.xml')]
    uso = {}
    for datos in piezas:
        raiz = etree.fromstring(datos)
        familias = {ff.get(f'{Q["style"]}name'): ff.get(f'{Q["svg"]}font-family')
                    for ff in raiz.iter(f'{Q["style"]}font-face')}
        for est in raiz.iter(f'{Q["style"]}style'):
            nombre = est.get(f'{Q["style"]}name') or '?'
            if es_vineta(nombre):
                continue
            for tp in est.iter(f'{Q["style"]}text-properties'):
                f = tp.get(f'{Q["style"]}font-name')
                if f:
                    uso.setdefault(familias.get(f, f), set()).add(
                        nombre.replace('_20_', ' '))
        for d in raiz.iter(f'{Q["style"]}default-style'):
            for tp in d.iter(f'{Q["style"]}text-properties'):
                f = tp.get(f'{Q["style"]}font-name')
                if f:
                    uso.setdefault(familias.get(f, f), set()).add('(default-style)')
    return uso


os.makedirs(TALLER, exist_ok=True)
os.makedirs(DESTINO_DIR, exist_ok=True)

print('\n1. Normalizar el original con LibreOffice')
normalizado = convertir(ORIGEN, os.path.join(TALLER, 'paso1'), 'normalizado')

print('\n2. Sanear')
saneado = os.path.join(TALLER, 'carta_base.odt')
sanear(normalizado, saneado)

print('\n3. Segunda pasada por LibreOffice (¿es un punto fijo?)')
final = convertir(saneado, os.path.join(TALLER, 'paso3'), 'final')
shutil.copy(final, DESTINO)

print('\n4. Fuentes latinas del resultado (por fuente real, sin viñetas)')
malas = []
for familia, estilos_ in sorted(fuentes_latinas(DESTINO).items()):
    limpia = (familia or '').strip("'") in CORPORATIVAS
    print(f'   {(familia or "-"):32s} {len(estilos_):2d} estilos  '
          f'{"" if limpia else "← AJENA: " + str(sorted(estilos_)[:4])}')
    if not limpia:
        malas.append(familia)

print(f'\n   {"✓ todas corporativas" if not malas else "✗ quedan fuentes ajenas"}')
print(f'\nResultado: {DESTINO}  ({os.path.getsize(DESTINO) / 1024:.0f} KB)')
shutil.rmtree(TALLER, ignore_errors=True)
raise SystemExit(0 if not malas else 1)
