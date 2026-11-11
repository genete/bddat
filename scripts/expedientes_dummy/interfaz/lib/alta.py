"""El formulario de alta de expediente (`/expedientes/nuevo/`), parametrizable.

Es el primer paso que se rompería si se rediseña el alta (#1048) o los selectores y fechas compartidos (#1105),
y por eso está aislado aquí. Casi todo son `<label for>` e ids; lo difícil son los selectores con buscador
(`SelectorBusqueda`: la lista se reinserta en `<body>` y sus `<li>` no llevan roles) y las fechas
(`EntradaFecha`: el mismo placeholder en todas las instancias).

CREA UN EXPEDIENTE REAL en la BD a la que apunte la aplicación y deja fijado el reloj de desarrollo
(«Usar fecha real» en la barra superior lo quita).
"""
import re
from dataclasses import dataclass
from datetime import date, datetime

from .arbol import abrir_arbol, fijar_reloj
from .documentos import TipoDummy, adjunto


@dataclass
class DatosAlta:
    """Lo que se rellena en el formulario. Los textos son los de los desplegables y listas de la aplicación."""
    titulo: str
    descripcion: str
    finalidad: str
    emplazamiento: str
    proyecto: TipoDummy            # el proyecto técnico que entra con el alta (queda como principal)
    fecha_proyecto: date
    escrito_solicitud: TipoDummy   # el escrito de solicitud, que ancla la solicitud
    fecha_registro: date
    observaciones: str
    tipo_expediente: str = 'Distribución'
    instrumento_ambiental: str = 'EXENTO'
    provincia: str = 'Sevilla'
    municipio: str = 'Mairena del Aljarafe'
    tipo_solicitud: str = 'AAP+AAC'
    responsable: str | None = None   # None → el primero real del desplegable (el 0 es «Sin asignar»)
    titular: str | None = None       # None → el primero de la lista


def _dmy(d):
    return d.strftime('%d/%m/%Y')


def _elegir_en_selector(page, contenedor, texto=None):
    """SelectorBusqueda: la lista se reinserta en <body> (ul.sb-lista.show) y sus <li> no llevan roles."""
    entrada = page.locator(f'{contenedor} .sb-input')
    entrada.click()
    if texto:
        entrada.fill(texto)
    items = page.locator('ul.sb-lista.show li.dropdown-item:not(.sb-placeholder)')
    item = items.filter(has_text=texto).first if texto else items.first
    item.wait_for(state='visible', timeout=5000)
    etiqueta = item.text_content().strip()
    item.click()
    return etiqueta


def _fecha(page, contenedor, d):
    """EntradaFecha: texto dd/mm/aaaa que se normaliza al salir."""
    entrada = page.locator(f'{contenedor} .ef-input')
    entrada.fill(_dmy(d))
    entrada.press('Enter')


def _id_de_expediente(page, base, n):
    """Id interno del expediente AT-n, pedido a la API del listado (`page.request` comparte la sesión).

    NO se usa el filtro de texto del listado con «AT-n»: su `search` solo entiende un número de 2+ cifras
    (`numero_at == n`) o texto del titular (#1104). El buscador global Ctrl+K sí entiende «AT-45», pero es
    otra API (`/api/search`)."""
    codigo = f'AT-{n}'

    def pedir(**params):
        r = page.request.get(f'{base}/api/expedientes', params={'limit': 100, **params})
        if not r.ok:
            raise RuntimeError(f'/api/expedientes {params} → {r.status}')
        return r.json()

    # Atajo: con 2+ cifras, `search=<n>` ya trae el expediente en una sola petición.
    if n >= 10:
        for e in pedir(search=str(n))['data']:
            if e['codigo'] == codigo:
                return e['id']
    # General: paginación por cursor (orden por id ascendente) hasta dar con el código.
    cursor = 0
    while True:
        j = pedir(cursor=cursor)
        for e in j['data']:
            if e['codigo'] == codigo:
                return e['id']
        if not j['has_more']:
            raise RuntimeError(f'{codigo} no aparece en /api/expedientes')
        cursor = j['next_cursor']


def alta(c, datos, fecha_base):
    """Fija el reloj de desarrollo en `fecha_base`, rellena y envía el formulario y apunta en el estado el
    expediente creado (`at`, `id`)."""
    page, s = c.page, c.s

    with s.paso('reloj de desarrollo: fijar la fecha base', 'get_by_title + input[type=date] + get_by_role(button)'):
        fijar_reloj(page, fecha_base)

    with s.paso('abrir el formulario de alta', 'URL directa'):
        page.goto(f'{c.url}/expedientes/nuevo/')
        page.get_by_role('heading', name=re.compile('Nuevo Expediente')).wait_for()

    with s.paso('tipo de expediente', 'get_by_label + select_option(label)'):
        page.get_by_label(re.compile('Tipo de expediente')).select_option(label=datos.tipo_expediente)

    with s.paso('tramitador responsable', 'get_by_label + select_option'):
        combo = page.get_by_label(re.compile('Tramitador responsable'))
        opciones = [t.strip() for t in combo.locator('option').all_text_contents()]
        print('     opciones de responsable:', ' | '.join(opciones))
        if datos.responsable:
            combo.select_option(label=next(o for o in opciones if datos.responsable in o))
        else:
            combo.select_option(index=1)

    with s.paso('título, descripción, finalidad, emplazamiento', 'get_by_label (cadenas, no regex ancladas)'):
        page.get_by_label('Título del proyecto').fill(datos.titulo)
        page.get_by_label('Descripción').fill(datos.descripcion)
        page.get_by_label('Finalidad').fill(datos.finalidad)
        page.get_by_label('Emplazamiento').fill(datos.emplazamiento)

    with s.paso('fichero del proyecto técnico', 'id #documento_proyecto (get_by_label «Fichero» da 2)'):
        page.locator('#documento_proyecto').set_input_files(adjunto(datos.proyecto, unico=False))

    with s.paso('fecha del proyecto', 'contenedor #ef-fecha (el placeholder sale dos veces)'):
        _fecha(page, '#ef-fecha', datos.fecha_proyecto)

    with s.paso('instrumento ambiental', 'get_by_label + select_option(label)'):
        sel = page.get_by_label(re.compile('Instrumento ambiental'))
        textos = [t.strip() for t in sel.locator('option').all_text_contents()]
        sel.select_option(label=next(t for t in textos if t.startswith(datos.instrumento_ambiental)))

    with s.paso('provincia y municipio', 'SelectorBusqueda por id de contenedor + ul.sb-lista.show'):
        _elegir_en_selector(page, '#wp2-provincia', datos.provincia)
        m = _elegir_en_selector(page, '#wp2-municipio', datos.municipio)
        page.locator('#municipios-seleccionados').get_by_text(m).wait_for()

    with s.paso('titular', 'SelectorBusqueda (#sb-titular)'):
        print('     titular elegido:', _elegir_en_selector(page, '#sb-titular', datos.titular))

    with s.paso(f'tipo de solicitud {datos.tipo_solicitud}', 'get_by_label + select_option(label)'):
        sel = page.get_by_label(re.compile('Tipo de solicitud'))
        textos = [t.strip() for t in sel.locator('option').all_text_contents()]
        sel.select_option(label=next(t for t in textos if re.match(rf'{re.escape(datos.tipo_solicitud)}\s+—', t)))

    with s.paso('escrito de solicitud y fecha de registro', 'id #documento_solicitud + contenedor #ef-registro'):
        page.locator('#documento_solicitud').set_input_files(adjunto(datos.escrito_solicitud, unico=False))
        _fecha(page, '#ef-registro', datos.fecha_registro)

    with s.paso('observaciones (con la marca [DUMMY:…])', 'get_by_label'):
        page.get_by_label('Observaciones').fill(datos.observaciones)

    s.captura('alta-rellena')

    with s.paso('crear el expediente', 'get_by_role(button) + expect_navigation'):
        with page.expect_navigation(url=lambda u: '/expedientes/nuevo' not in u, timeout=20000):
            page.get_by_role('button', name=re.compile('Crear expediente')).click()
        page.wait_for_load_state('networkidle')

    with s.paso('localizar el expediente creado', 'aviso «Expediente AT-N creado» + /api/expedientes (cursor)'):
        aviso = page.get_by_text(re.compile(r'Expediente AT-\d+ creado')).first.text_content()
        n = int(re.search(r'AT-(\d+)', aviso).group(1))
        c.estado['at'] = f'AT-{n}'
        c.estado['id'] = str(_id_de_expediente(page, c.url, n))
        c.estado['creado'] = datetime.now().isoformat()
        c.guardar()
        print(f'     expediente creado: {c.at} (id {c.id})')

    with s.paso('comprobar el id abriendo el árbol', 'URL directa + data-id del nodo de React Flow'):
        abrir_arbol(page, c.url, c.id)
        page.locator(f'[data-id="expediente-{c.id}"]').wait_for(timeout=15000)
