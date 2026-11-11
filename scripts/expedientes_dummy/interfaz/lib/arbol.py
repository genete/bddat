"""Operaciones sobre el árbol del expediente (lienzo React Flow + inspector + despensa).

Sin `data-testid`: se localiza por rol, por texto exacto y por los `data-id` que React Flow pone a cada nodo
(`fase-11`, `tramite-29`, `tareas-29`, `solicitud-6`…). Los sitios donde cuesta, y por qué, están en #1105.

Para actuar sobre un nodo NO se pincha en el lienzo (con el inspector abierto, este tapa el centro y a veces la
esquina de los nodos): se navega a `…/arbol?nodo=<id>`, que abre el inspector sobre él. El id de lo que se acaba
de crear se lee de esa misma URL (`nodo_actual`), porque al crear, el inspector salta al nodo nuevo.
"""
import re
from datetime import date, datetime, timedelta

from .documentos import adjunto, fichero

TEXTO_DATOS = re.compile(r'Datos (de la|del) (tarea|trámite|fase|solicitud|expediente)')


def inspector(page):
    return page.get_by_role('complementary', name='Inspector')


# --------------------------------------------------------------------------------------------------------
# Reloj de desarrollo y fechas
# --------------------------------------------------------------------------------------------------------

def fecha_reloj(page):
    """La fecha del reloj de desarrollo, leída de la barra superior (dd/mm/aaaa). Es la «hoy» de la
    aplicación: ninguna fecha administrativa puede ser posterior (#824)."""
    texto = page.locator('.app-topbar__reloj-dev button').first.text_content()
    return datetime.strptime(re.search(r'\d\d/\d\d/\d{4}', texto).group(0), '%d/%m/%Y').date()


def fijar_reloj(page, fecha):
    """Fija el reloj de desarrollo en `fecha` desde la barra superior (recarga la página)."""
    page.get_by_title(re.compile('Reloj de desarrollo')).click()
    page.locator('.app-topbar__reloj-dev input[type="date"]').fill(fecha.isoformat())
    page.get_by_role('button', name='Fijar').click()
    page.wait_for_load_state('load')
    if fecha_reloj(page) != fecha:
        raise RuntimeError(f'el reloj dice {fecha_reloj(page)}, se esperaba {fecha}')


def dias_habiles_antes(fecha, n):
    """`n` días hábiles (lunes a viernes) antes de `fecha`. No conoce los festivos: para situar una respuesta
    «unos días antes de vencer» basta, porque un festivo solo la adelanta un día respecto al cálculo real."""
    d, hechos = fecha, 0
    while hechos < n:
        d -= timedelta(days=1)
        if d.weekday() < 5:
            hechos += 1
    return d


def dia_habil_siguiente(fecha):
    d = fecha + timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


# --------------------------------------------------------------------------------------------------------
# Navegación por nodos
# --------------------------------------------------------------------------------------------------------

def abrir_arbol(page, url, exp_id):
    page.goto(f'{url}/expedientes/{exp_id}/arbol', wait_until='networkidle')
    page.locator('.react-flow__node').first.wait_for(timeout=15000)


def ids_nodos(page):
    return page.locator('.react-flow__node').evaluate_all('ns => ns.map(n => n.dataset.id)')


def nodo_actual(page):
    """`tarea-33199`, `tramite-29911`… según la URL del inspector (None si no hay ninguno abierto)."""
    m = re.search(r'[?&]nodo=([\w-]+)', page.url)
    return m.group(1) if m else None


def ir_nodo(page, url, exp_id, nodo):
    """Abre el árbol con el inspector sobre `nodo` (en lectura) y espera a que cargue."""
    page.goto(f'{url}/expedientes/{exp_id}/arbol?nodo={nodo}', wait_until='networkidle')
    inspector(page).get_by_text(TEXTO_DATOS).first.wait_for(timeout=15000)


def editar(page):
    """Pasa el inspector a edición (si ya está en edición, no hay botón)."""
    boton = inspector(page).get_by_role('button', name='Editar')
    if boton.count():
        boton.click()


# --------------------------------------------------------------------------------------------------------
# Avisos, guardar y creación desde la despensa
# --------------------------------------------------------------------------------------------------------

def cerrar_avisos(page):
    """Los avisos duran 8 s (toast.js) y se acumulan: se cierran con su botón para que un aviso viejo no se
    tome por el de la acción siguiente."""
    for boton in page.locator('.toast .btn-close').all():
        try:
            boton.click(timeout=1000)
        except Exception:  # noqa: BLE001
            pass


def guardar(page, texto_aviso='Cambios guardados', ultimo=False):
    """Pulsa «Guardar» del inspector y espera el aviso. Una NOTIFICAR en edición tiene dos «Guardar»: el de la
    cabecera (los vínculos de documentos, el primero) y el del registro de la notificación (el resultado, el
    último, con el aviso «Notificación registrada»)."""
    cerrar_avisos(page)
    botones = inspector(page).get_by_role('button', name='Guardar', exact=True)
    (botones.last if ultimo else botones.first).click()
    page.get_by_text(texto_aviso).filter(visible=True).first.wait_for(timeout=10000)
    cerrar_avisos(page)


def crear_hijo(page, tipo):
    """Despensa: elegir un tipo (un <div>, no un botón) y pulsar «Crear». El nodo se crea al instante y el
    inspector salta a él: devuelve su id (`tarea-33199`), leído de la URL."""
    insp = inspector(page)
    cerrar_avisos(page)
    antes = nodo_actual(page)
    insp.get_by_text(tipo, exact=True).click()
    insp.get_by_role('button', name='Crear', exact=True).click()
    page.get_by_text('Elemento creado').filter(visible=True).first.wait_for(timeout=10000)
    cerrar_avisos(page)
    page.wait_for_function(
        'a => { const m = location.search.match(/nodo=([\\w-]+)/); return !!m && m[1] !== a; }', arg=antes, timeout=10000)
    return nodo_actual(page)


# --------------------------------------------------------------------------------------------------------
# Documentos: pool, subida en línea y vínculos CONSUMIDO / PRODUCIDO de una tarea
# --------------------------------------------------------------------------------------------------------

def subir_al_pool(page, url, exp_id, documentos):
    """Sube documentos al pool del expediente con el asistente de 2 pasos: [(tipo, fecha), …] (`tipo` es un
    `TipoDummy`; su nombre es el del desplegable, porque los `value` son ids de catálogo).

    No se comprueba en el listado del pool (es otra pantalla, que puede fallar sin que la subida lo haga): los
    documentos nuevos aparecen en el desplegable de «Vincular documento» del checklist."""
    page.goto(f'{url}/expedientes/{exp_id}/documentos', wait_until='networkidle')
    page.get_by_role('button', name=re.compile('Subir', re.I)).first.click()
    dlg = page.get_by_role('dialog')
    dlg.wait_for()
    dlg.locator('input[type="file"]').set_input_files([adjunto(tipo) for tipo, _ in documentos])
    dlg.get_by_role('button', name=re.compile('Siguiente')).click()
    filas = dlg.locator('tbody tr')
    filas.nth(len(documentos) - 1).wait_for()
    for i, (tipo, fecha) in enumerate(documentos):
        fila = filas.nth(i)
        fila.get_by_role('combobox').select_option(label=tipo.nombre)
        campo = fila.locator('.ef-input')
        campo.fill(fecha.strftime('%d/%m/%Y'))
        campo.press('Enter')
    dlg.get_by_role('button', name=re.compile(r'Subir \d+ fichero', re.I)).click()
    dlg.wait_for(state='hidden', timeout=20000)


def _item_pool(page, nombre):
    """Un documento del pool de la tarea, por texto de su botón («Documento <fichero> <fecha> <tipo>»). El pool
    va del más nuevo al más antiguo, así que `.first` es el último que entró con ese nombre."""
    return inspector(page).get_by_role('button', name=re.compile(r'^Documento .*' + re.escape(nombre))).first


def subir_inline(page, tipo, fecha, asunto=None):
    """«Subir documento nuevo» de la despensa de una tarea en edición. El documento entra al pool y queda
    SELECCIONADO, nada más (a pesar del rótulo «Subir y vincular», #1105): falta pulsar «+ Producido» o
    «+ Consumido» (`vincular`) y guardar."""
    insp = inspector(page)
    insp.get_by_role('button', name=re.compile('Subir documento nuevo')).click()
    insp.locator('input[type="file"]').set_input_files(adjunto(tipo))
    bloque = insp.locator('div.rounded.border').filter(has=page.locator('input[type="file"]'))
    bloque.get_by_role('combobox').select_option(label=tipo.nombre)
    if asunto:
        bloque.get_by_placeholder('Asunto').fill(asunto)
    bloque.locator('input[type="date"]').fill(fecha.isoformat())
    bloque.get_by_role('button', name='Subir y vincular').click()
    # El documento recién subido queda seleccionado (`aria-pressed`, en un elemento con rol de botón que no
    # es necesariamente un <button>).
    insp.locator('[aria-pressed="true"]').first.wait_for(timeout=15000)


def vincular(page, rol, nombre=None):
    """Vincula a la tarea en edición un documento del pool como «Consumido» o «Producido». Con `nombre`
    selecciona antes el documento (el más nuevo cuyo texto lo contenga); sin él, vale el recién subido, que ya
    está seleccionado (volver a pulsarlo lo desmarcaría)."""
    insp = inspector(page)
    if nombre:
        item = _item_pool(page, nombre)
        item.wait_for(timeout=10000)
        if item.get_attribute('aria-pressed') != 'true':
            item.click()
    insp.get_by_role('button', name=re.compile(rf'\+ {rol}', re.I)).click()


# --------------------------------------------------------------------------------------------------------
# Plazos
# --------------------------------------------------------------------------------------------------------

def fecha_limite(page):
    """La «Fecha límite: aaaa-mm-dd» que enseña una ESPERAR_PLAZO con el plazo disparado."""
    insp = inspector(page)
    insp.get_by_text(re.compile(r'Fecha límite')).first.wait_for(timeout=10000)
    texto = ' '.join(insp.inner_text().split())
    return date.fromisoformat(re.search(r'Fecha límite:\s*(\d{4}-\d{2}-\d{2})', texto).group(1))


# --------------------------------------------------------------------------------------------------------
# Checklist documental de ANALIZAR
# --------------------------------------------------------------------------------------------------------

def fila_requisito(page, titulo):
    """Fila de un requisito del checklist de ANALIZAR, por el título exacto del requisito. No hay
    `data-testid` ni agrupación accesible (#1105): cada fila es un `div.border-bottom` con el título en
    `.fw-semibold` y el estado (Pendiente/Cubierto) en `.badge`."""
    return inspector(page).locator('div.border-bottom').filter(has=page.get_by_text(titulo, exact=True))


def requisitos_pendientes(page):
    """Títulos de los requisitos que el checklist enseña como «Pendiente»."""
    filas = inspector(page).locator('div.border-bottom').filter(has=page.locator('.badge', has_text='Pendiente'))
    return [t.strip() for t in filas.locator('.fw-semibold').all_text_contents()]


def vincular_requisito(page, tipo):
    """Vincula al requisito de este tipo de documento (su título es el nombre del tipo) el documento del pool
    cuyo fichero es el del tipo, y espera a que la fila pase a CUBIERTO."""
    fila = fila_requisito(page, tipo.nombre)
    fila.get_by_role('button', name='Vincular documento').click()
    combo = fila.get_by_role('combobox')
    opciones = combo.locator('option').all_text_contents()
    elegida = next((o for o in opciones if fichero(tipo) in o), None)
    if elegida is None:
        raise RuntimeError(f'ningún documento del pool es «{fichero(tipo)}»: {opciones}')
    combo.select_option(label=elegida)
    fila.get_by_role('button', name='Vincular', exact=True).click()
    fila.get_by_text(re.compile('cubierto', re.I)).first.wait_for(timeout=8000)


def contador_checklist(page):
    """«n/9» del botón «Check documental n/9 cubiertos»."""
    texto = inspector(page).get_by_role('button', name=re.compile('Check documental')).inner_text()
    return re.search(r'(\d+)/(\d+)', texto).group(0)
