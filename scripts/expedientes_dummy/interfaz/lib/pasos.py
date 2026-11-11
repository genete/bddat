"""Piezas reutilizables entre expedientes-tipo: cada una es un trozo de tramitación que se ve igual en
cualquier escenario (crear un nodo, producir un diagnóstico, generar un escrito, cerrar una ELABORAR o una
NOTIFICAR, disparar un plazo y responder en él…). El expediente-tipo decide el orden y los datos; aquí está el
cómo se hace por la interfaz.

Todas reciben el `Contexto` y, cuando actúan sobre un nodo ya creado, la CLAVE con la que se anotó su id
(`c.ids`); las que lo crean la reciben para anotarlo. Cada una abre sus propios pasos con `c.s.paso(...)`.
"""
import io
import re
import zipfile
from datetime import date

from .arbol import (contador_checklist, crear_hijo, dias_habiles_antes, dia_habil_siguiente, editar, fecha_limite,
                    fecha_reloj, fijar_reloj, guardar, ids_nodos, ir_nodo, requisitos_pendientes, subir_al_pool,
                    subir_inline, vincular, vincular_requisito)
from .documentos import fichero

# El nombre con que el pool enseña el documento que produce «Producir diagnóstico».
DIAGNOSTICO = 'Diagnóstico de análisis'


# ---------------------------------------------------------------------------------------------------------
# Árbol: crear nodos
# ---------------------------------------------------------------------------------------------------------

def crear_en(c, padre, tipo, etiqueta, clave):
    """Abre `padre` (clave de un nodo ya creado) en edición, espera a su despensa y crea `tipo` (el inspector
    salta al nodo nuevo, cuyo id se anota con `clave`)."""
    with c.s.paso(f'crear {etiqueta}', 'ir al padre + Editar + despensa'):
        c.ir(padre)
        editar(c.page)
        c.insp.get_by_text(re.compile('Crear (fase|trámite|tarea)')).wait_for()
        c.anotar(clave, crear_hijo(c.page, tipo))


def crear_fase(c, tipo_fase, clave='fase'):
    """Crea una fase desde la solicitud. El id de la solicitud NO es el del expediente (AT-48 es el 4153 y su
    solicitud, la 7371): se lee del lienzo."""
    with c.s.paso('localizar la solicitud en el lienzo', 'nodo solicitud- (data-id de React Flow)'):
        c.arbol()
        c.ids['solicitud'] = next(i for i in ids_nodos(c.page) if i.startswith('solicitud-'))
    crear_en(c, 'solicitud', tipo_fase, f'la fase {tipo_fase}', clave)


# ---------------------------------------------------------------------------------------------------------
# Proyecto
# ---------------------------------------------------------------------------------------------------------

def marcar_campos_proyecto(c, marcados, tension_kv=None):
    """Campos técnicos del proyecto que el formulario de alta no pide, editados en el inspector del expediente.
    `marcados`: las etiquetas de las casillas («Sin línea aérea», «Solo suelo urbano/urbanizable»,
    «Es modificación»)."""
    page, insp = c.page, c.insp
    with c.s.paso('abrir el expediente en el listado', 'URL ?sel= + get_by_role(complementary)'):
        page.goto(f'{c.url}/expedientes/?sel={c.id}', wait_until='networkidle')
        insp.get_by_text(c.at, exact=True).first.wait_for()
    with c.s.paso('marcar los campos técnicos', 'Editar + get_by_label(checkbox) + #ef_tension'):
        insp.get_by_role('button', name='Editar').click()
        for etiqueta in marcados:
            insp.get_by_label(etiqueta).check()
        if tension_kv is not None:
            insp.locator('#ef_tension').fill(str(tension_kv))
    with c.s.paso('guardar', 'get_by_role(button, Guardar)'):
        insp.get_by_role('button', name=re.compile('Guardar')).first.click()
        page.wait_for_load_state('networkidle')
    with c.s.paso('comprobar que quedó guardado', 'recarga + Editar + is_checked'):
        page.goto(f'{c.url}/expedientes/?sel={c.id}', wait_until='networkidle')
        insp.get_by_text(c.at, exact=True).first.wait_for()
        insp.get_by_role('button', name='Editar').click()
        for etiqueta in marcados:
            if not insp.get_by_label(etiqueta).is_checked():
                raise RuntimeError(f'«{etiqueta}» no quedó marcado')
        if tension_kv is not None:
            # La columna es numérica: el campo devuelve «20.00», no «20».
            tension = insp.locator('#ef_tension').input_value()
            if float(tension.replace(',', '.') or 0) != tension_kv:
                raise RuntimeError(f'la tensión máxima no quedó en {tension_kv} (dice «{tension}»)')


# ---------------------------------------------------------------------------------------------------------
# Checklist documental y diagnóstico (ANALIZAR)
# ---------------------------------------------------------------------------------------------------------

def vincular_presentacion(c, clave, tipos):
    """Abre el checklist de una ANALIZAR y vincula a cada requisito el documento de su tipo (ya en el pool)."""
    page = c.page
    with c.s.paso('abrir el checklist', 'ir + Editar + «Check documental»'):
        c.ir(clave)
        editar(page)
        c.insp.get_by_text('Check documental').wait_for()
        print('     checklist:', contador_checklist(page))
    with c.s.paso(f'vincular {len(tipos)} requisito(s)', 'fila div.border-bottom por título + «Vincular documento»'):
        antes = int(contador_checklist(page).split('/')[0])
        for tipo in tipos:
            vincular_requisito(page, tipo)
        cubiertos = contador_checklist(page)
        print('     checklist:', cubiertos)
        if int(cubiertos.split('/')[0]) != antes + len(tipos):
            raise RuntimeError(f'se esperaban {antes + len(tipos)} requisitos cubiertos y el contador dice {cubiertos}')


def pendientes(c, clave):
    """Títulos de los requisitos que el checklist de una ANALIZAR enseña como «Pendiente»."""
    with c.s.paso('leer los requisitos pendientes', 'ir + Editar + `.badge` «Pendiente»'):
        c.ir(clave)
        editar(c.page)
        c.insp.get_by_text('Check documental').wait_for()
        lista = requisitos_pendientes(c.page)
        print('     pendientes:', ' | '.join(lista))
    return lista


def producir_diagnostico(c, clave, esperado):
    """Produce el documento de diagnóstico. El sentido NO se elige: lo calcula el checklist con lo que quede sin
    cubrir (ADR-033); `esperado` («Favorable» o «Desfavorable») solo comprueba que el escenario va como se prevé."""
    page, insp = c.page, c.insp
    with c.s.paso(f'leer el sentido calculado (se espera {esperado})', 'ir + Editar + «Sentido calculado»'):
        c.ir(clave)
        editar(page)
        insp.get_by_text(re.compile('Sentido calculado')).wait_for()
        sentido = ' '.join(insp.get_by_text(re.compile('Sentido calculado')).inner_text().split())
        print('    ', sentido)
        if not re.search(rf'Sentido calculado:\s*{esperado}', sentido):
            raise RuntimeError(f'se esperaba el sentido {esperado} y el checklist dice «{sentido}»')
    with c.s.paso('producir el documento de diagnóstico', 'get_by_role(button) + confirmación en línea'):
        insp.get_by_role('button', name='Producir documento de diagnóstico').click()
        insp.get_by_role('button', name='Confirmar producción').click()
        # El botón pasa a «Produciendo…» al instante: el fin es el texto «Documento producido — el resultado
        # queda bloqueado» (y la tarea, EJECUTADA).
        insp.get_by_text(re.compile('Documento producido')).wait_for(timeout=20000)


def aportar_y_vincular(c, clave, tipos):
    """Lo que aporta el titular para subsanar: sube al pool los documentos de `tipos` (con la fecha del reloj) y
    los vincula a su requisito en el checklist de la ANALIZAR `clave`."""
    with c.s.paso('subir lo que aporta el titular', 'pool: Subir fichero → Siguiente → tipo + fecha'):
        hoy = fecha_reloj(c.page)
        subir_al_pool(c.page, c.url, c.id, [(t, hoy) for t in tipos])
    vincular_presentacion(c, clave, tipos)


# ---------------------------------------------------------------------------------------------------------
# ELABORAR: escrito generado y oficio
# ---------------------------------------------------------------------------------------------------------

def generar_escrito(c, clave, esperados=(), plantilla='demostraci'):
    """Genera el escrito de una ELABORAR desde la plantilla cuyo nombre contenga `plantilla` (por defecto, las
    `DEMO_` que registra `scripts/plantillas_demo.py`) y comprueba su contenido: el código del expediente y
    cada texto de `esperados`, sin `{{ }}` sin sustituir. El .odt se lee como zip (`unzip` no existe en Windows)."""
    page, insp = c.page, c.insp
    with c.s.paso('elegir la plantilla y generar', 'get_by_role(combobox) de «Generar escrito» + «Generar»'):
        c.ir(clave)
        editar(page)
        insp.get_by_text('Generar escrito').wait_for()
        combo = insp.get_by_role('combobox').last
        # Las plantillas se cargan tras abrir el editor: hay que esperarlas, no leer el desplegable al vuelo.
        try:
            combo.locator('option', has_text=re.compile(plantilla, re.I)).wait_for(state='attached', timeout=10000)
        except Exception:  # noqa: BLE001
            raise RuntimeError('no hay plantilla DEMO: ejecuta antes venv/Scripts/python.exe '
                               'scripts/plantillas_demo.py --claves <TRAMITE> …') from None
        elegida = next(t.strip() for t in combo.locator('option').all_text_contents() if re.search(plantilla, t, re.I))
        print('     plantilla:', elegida)
        combo.select_option(label=elegida)
        insp.get_by_role('button', name=re.compile(r'^Generar$')).click()
        # No se espera el aviso «Escrito generado» (a veces se repinta el inspector antes de que se vea): el
        # fin es que el borrador .odt aparezca en la lista de documentos de la tarea.
        insp.get_by_role('link', name=re.compile(r'\.odt$')).first.wait_for(timeout=20000)
    with c.s.paso('descargar el borrador y leer su texto', 'enlace del inspector + page.request + zipfile'):
        c.ir(clave)
        enlaces = insp.locator('a[href*="/documentos/"]')
        enlaces.first.wait_for(timeout=10000)
        hrefs = [enlaces.nth(i).get_attribute('href') for i in range(enlaces.count())
                 if enlaces.nth(i).inner_text().strip().endswith('.odt')]
        if not hrefs:
            raise RuntimeError('el inspector no muestra ningún .odt')
        cuerpo = page.request.get(f'{c.url}{hrefs[-1]}').body()
        with zipfile.ZipFile(io.BytesIO(cuerpo)) as z:
            xml = z.read('content.xml').decode('utf-8')
        texto = ' '.join(re.sub(r'<[^>]+>', ' ', xml).split())
        print('     texto del borrador:', texto[:300])
        for esperado in (c.at, *esperados):
            if esperado not in texto:
                raise RuntimeError(f'el borrador no contiene «{esperado}»')
        if '{{' in texto:
            raise RuntimeError('quedan marcadores {{ }} sin sustituir')


def elaborar_oficio(c, clave, tipo_oficio, asunto):
    """Cierra una ELABORAR: sube el oficio (el escrito ya firmado) como PRODUCIDO y consume el diagnóstico más
    reciente (el que motiva el escrito). El borrador generado ya figura como consumido."""
    page, insp = c.page, c.insp
    with c.s.paso('subir el oficio y vincular producido y consumido', 'subida en línea + «+ Producido» + «+ Consumido»'):
        c.ir(clave)
        editar(page)
        subir_inline(page, tipo_oficio, fecha_reloj(page), asunto)
        vincular(page, 'Producido')
        vincular(page, 'Consumido', nombre=DIAGNOSTICO)
        guardar(page)
        # Tras guardar el árbol se repinta y el inspector puede cerrarse: se comprueba reabriendo la tarea.
        c.ir(clave)
        insp.get_by_text('EJECUTADA').first.wait_for(timeout=10000)


# ---------------------------------------------------------------------------------------------------------
# NOTIFICAR
# ---------------------------------------------------------------------------------------------------------

def notificar(c, clave, tipo_oficio, tipo_justificante):
    """Cierra una NOTIFICAR: el oficio entra como CONSUMIDO («a notificar»), el justificante como PRODUCIDO (su
    tipo fija el canal) y el resultado de la notificación se marca «Correcta» (sin eso el ESPERAR_PLAZO
    siguiente no podría crearse: #823)."""
    page, insp = c.page, c.insp
    with c.s.paso('vincular el oficio y el justificante', 'subida en línea + «+ Consumido» + «+ Producido»'):
        c.ir(clave)
        editar(page)
        vincular(page, 'Consumido', nombre=fichero(tipo_oficio))
        subir_inline(page, tipo_justificante, fecha_reloj(page))
        vincular(page, 'Producido')
        guardar(page)
    with c.s.paso('resultado de la notificación: Correcta', 'combobox «Resultado» + «Guardar» del registro'):
        # Tras guardar los vínculos, el árbol se repinta y el inspector puede cerrarse: se reabre la tarea.
        c.ir(clave)
        editar(page)
        resultado = insp.get_by_role('combobox', name='Resultado')
        resultado.wait_for()
        resultado.select_option(label='Correcta')
        guardar(page, 'Notificación registrada', ultimo=True)


# ---------------------------------------------------------------------------------------------------------
# ESPERAR_PLAZO
# ---------------------------------------------------------------------------------------------------------

def disparar_plazo(c, clave, tipo_oficio):
    """Dispara el plazo de una ESPERAR_PLAZO: el oficio ya notificado entra como CONSUMIDO. Devuelve la fecha límite
    que enseña el inspector."""
    with c.s.paso('consumir el oficio notificado (dispara el plazo)', '«+ Consumido» + Guardar'):
        c.ir(clave)
        editar(c.page)
        vincular(c.page, 'Consumido', nombre=fichero(tipo_oficio))
        guardar(c.page)
        c.ir(clave)    # el inspector puede haberse cerrado al repintarse el árbol
        limite = fecha_limite(c.page)
        print('     fecha límite:', limite)
    return limite


def responder_en_plazo(c, clave, tipo_respuesta, asunto, margen_habiles):
    """El titular responde dentro de plazo: la fecha sale del vencimiento que enseña el inspector (nunca de un
    número de días escrito a mano), el reloj se lleva a ella y la respuesta entra como PRODUCIDO, que cierra el
    plazo («Cumplido»)."""
    page, insp = c.page, c.insp
    with c.s.paso('situar la respuesta antes del vencimiento y llevar el reloj', 'fecha límite del inspector + reloj'):
        c.ir(clave)
        limite = fecha_limite(page)
        disparo = fecha_reloj(page)     # la notificación se fechó con el reloj
        respuesta = dias_habiles_antes(limite, margen_habiles)
        if respuesta <= disparo:        # plazo más corto que el margen: el día hábil siguiente al disparo
            respuesta = dia_habil_siguiente(disparo)
        if respuesta > date.today():
            raise RuntimeError(f'la respuesta caería el {respuesta}, posterior a hoy: el escenario no cabe '
                               'en la ventana (usa --dias con un número mayor)')
        print(f'     plazo hasta {limite}; responde el {respuesta}')
        fijar_reloj(page, respuesta)
    with c.s.paso('subir la respuesta y cerrar el plazo', 'subida en línea + «+ Producido»'):
        c.ir(clave)
        editar(page)
        subir_inline(page, tipo_respuesta, fecha_reloj(page), asunto)
        vincular(page, 'Producido')
        guardar(page)
        c.ir(clave)
        insp.get_by_text('Cumplido').first.wait_for(timeout=10000)


# ---------------------------------------------------------------------------------------------------------
# Reciclado
# ---------------------------------------------------------------------------------------------------------

def reciclar(c, estado_previo, marca):
    """Marca `[RECICLAR]` el expediente de la ejecución anterior de este mismo expediente-tipo, desde la interfaz
    (observaciones de su solicitud), para que lo recoja `limpiar_reciclables.py`. No borra nada.

    Solo toca un expediente cuyas observaciones empiecen por `marca` (`[DUMMY:<CODIGO>]`): nunca algo que no sea de
    este escenario, aunque el estado local apunte a otro. Si el expediente ya no existe o ya está marcado, lo dice
    y sigue."""
    page, insp = c.page, c.insp
    exp_id, at = estado_previo.get('id'), estado_previo.get('at')
    if not exp_id:
        print('     la ejecución anterior no llegó a crear un expediente: nada que reciclar')
        return
    with c.s.paso(f'reciclar {at} (ejecución anterior)', 'inspector de la solicitud + «Observaciones» + Guardar'):
        respuesta = page.goto(f'{c.url}/expedientes/{exp_id}/arbol', wait_until='networkidle')
        if respuesta is None or respuesta.status >= 400:
            print(f'     {at} ya no existe en esta base: nada que reciclar')
            return
        page.locator('.react-flow__node').first.wait_for(timeout=15000)
        solicitud = next(i for i in ids_nodos(page) if i.startswith('solicitud-'))
        ir_nodo(page, c.url, exp_id, solicitud)
        editar(page)
        observaciones = insp.locator('textarea').first
        texto = observaciones.input_value()
        if texto.startswith('[RECICLAR]'):
            print(f'     {at} ya estaba marcado [RECICLAR]')
            return
        if not texto.startswith(marca):
            raise RuntimeError(f'{at} no es de este escenario (sus observaciones no empiezan por {marca}): no se toca')
        observaciones.fill(f'[RECICLAR] {texto}')
        guardar(page)
        print(f'     {at} marcado [RECICLAR] (sin borrar)')
