"""
Consolidación de defectos para el contenedor de la tarea ANALIZAR (#442).

Agrega las contribuciones de los tres proveedores que se enchufan al
contenedor: check documental (#495), check de ítems técnicos (#581) y
selector de requerimientos (#440).

FORMA DEL ITEM:
    {'texto': str, 'origen': 'documental'|'tecnico'|'requerimiento', 'tarea_id': int, ...}

    Cada origen añade su propio id estable (#724 — detectar si un ítem ya se exigió
    en una vuelta anterior notificada, ver diagnosticos.diagnostico_donde_se_exigio_*):
    documental → 'requisito_id', tecnico → 'item_tecnico_id', requerimiento →
    'catalogo_requerimientos_id' (None si es texto libre — sin id de catálogo, el
    emparejamiento cae al texto exacto, único identificador disponible para ese caso).
    Los diagnósticos ya congelados antes de #724 no llevan estos ids: el
    emparejamiento simplemente no encuentra coincidencia (degradación aceptada, no
    bloquea de más).

CAMPO 'completo':
    AND de "¿queda algo sin revisar?" de los proveedores con estado de
    revisión (documental #495, técnico #581 cuando aterrice). El proveedor
    de requerimientos (#440) no contribuye a completo — la selección del
    técnico es siempre "revisada" por definición, al ser voluntaria.
"""
from __future__ import annotations

from app.services.assembler import build
from app.services.requisitos import evaluar_requisitos
from app.services.items_tecnicos import evaluar_items_tecnicos


def _cita_normativa(norma, articulo) -> str:
    """' (art. X, Título de la norma)' si hay norma; cadena vacía si no.

    Regla acordada 2026-07-06: la cita solo se compone si `norma_id` está
    relleno — que esté vacío no implica arbitrio administrativo, puede que
    la norma exista y esté pendiente de catalogar (#408/#595).
    """
    if norma is None:
        return ''
    return f' (art. {articulo or "—"}, {norma.titulo})'


def _items_documental(tarea) -> tuple[list, bool]:
    """Defectos documentales no cubiertos (#495) + si el checklist está completo."""
    solicitud = tarea.tramite.fase.solicitud
    _, variables = build(solicitud.expediente, objeto=tarea)
    resultado = evaluar_requisitos(solicitud, variables)
    if resultado['error']:
        return [], True

    items = []
    for it in resultado['items']:
        if it['cubierto']:
            continue
        req = it['requisito']
        texto = (req.descripcion_legal or '') + _cita_normativa(req.norma, req.articulo)
        items.append({'texto': texto, 'origen': 'documental', 'tarea_id': tarea.id, 'requisito_id': req.id})
    return items, resultado['todos_cubiertos']


def _items_tecnico(tarea) -> tuple[list, bool]:
    """Defectos técnicos desfavorables (#581) + si el checklist está completo.

    Solo los ítems revisados (texto no vacío) cuentan como defecto cuando
    cubierto=False. Los no revisados (sin fila o texto vacío) no generan
    defecto — solo restan a 'completo', igual que documental.
    """
    solicitud = tarea.tramite.fase.solicitud
    _, variables = build(solicitud.expediente, objeto=tarea)
    resultado = evaluar_items_tecnicos(solicitud, variables)
    if resultado['error']:
        return [], True

    items = []
    for it in resultado['items']:
        cobertura = it['cobertura']
        if cobertura is None or not (cobertura.texto or '').strip():
            continue  # no revisado — no es defecto, solo resta a completo
        if cobertura.cubierto:
            continue  # favorable — no es defecto
        item_tecnico = it['item']
        texto = (item_tecnico.descripcion or '') + _cita_normativa(item_tecnico.norma, item_tecnico.articulo)
        items.append({
            'texto': texto, 'origen': 'tecnico', 'tarea_id': tarea.id,
            'item_tecnico_id': item_tecnico.id,
        })
    return items, resultado['todos_revisados']


def _items_requerimiento(tarea) -> tuple[list, list]:
    """Requerimientos libres de la solicitud (#440, elevado a `solicitud_id`
    en #679, ADR-033 §7) — pendientes y resueltos por separado.

    A diferencia de documental/técnico, los pendientes no contribuyen a
    'completo' — la selección del técnico es siempre "revisada" por
    definición, al ser voluntaria. Tampoco componen cita normativa (el modelo
    no tiene norma_id).

    Los resueltos (`resuelto=True`, marca manual del técnico) no son defecto
    activo — se devuelven aparte, solo para que el borrador muestre progreso
    (ADR-033 §7), sin contar en el borrador que determina el resultado.
    """
    solicitud = tarea.tramite.fase.solicitud
    pendientes, resueltos = [], []
    for r in solicitud.requerimientos:
        item = {
            'texto': r.texto, 'origen': 'requerimiento', 'tarea_id': tarea.id,
            # No 'requerimiento_tarea_id': la fila se borra y recrea entera en cada
            # guardado del shuttle (post_requerimientos), así que su id no es estable
            # entre vueltas. El id de catálogo sí lo es; el texto libre no tiene
            # ninguno — el emparejamiento cae al texto exacto (#724).
            'catalogo_requerimientos_id': r.catalogo_requerimientos_id,
        }
        (resueltos if r.resuelto else pendientes).append(item)
    return pendientes, resueltos


def consolidar_defectos(tarea) -> dict:
    """
    Consolida los defectos aplicables a la tarea ANALIZAR dada.

    Returns:
        {'items': list, 'items_resueltos': list, 'completo': bool, 'error': bool}

    'items' son los defectos activos: determinan 'completo', el resultado
    derivado (ADR-033 §3) y lo que se congela en el próximo Diagnostico.
    'items_resueltos' (ADR-033 §7) son requerimientos libres ya marcados
    resueltos por el técnico — no cuentan como defecto, solo se exponen para
    que el borrador muestre progreso sin abrir el escrito notificado.

    'completo' es solo técnico (ADR-033 §4): el documental es directo (ausencia
    = defecto, no "pendiente de revisar" — no existe estado "sin revisar" real
    como en técnico), así que no debe bloquear la producción. El libre nunca
    contó tampoco.
    """
    items_documental, _completo_documental = _items_documental(tarea)
    items_tecnico, completo_tecnico = _items_tecnico(tarea)
    items_requerimiento, items_requerimiento_resueltos = _items_requerimiento(tarea)

    return {
        'items': items_documental + items_tecnico + items_requerimiento,
        'items_resueltos': items_requerimiento_resueltos,
        'completo': completo_tecnico,
        'error': False,
    }


ETIQUETA_ORIGEN = {
    'documental': 'Documental',
    'tecnico': 'Técnico',
    'requerimiento': 'Requerimientos',
}

ORDEN_ORIGEN = ('documental', 'tecnico', 'requerimiento')


def agrupar_defectos_por_origen(defectos: list) -> list:
    """
    Agrupa defectos ya persistidos en `Diagnostico.defectos` por su campo
    `origen`, para representaciones de solo lectura (#629).

    Omite grupos sin ítems (un origen que no aportó ningún defecto no debe
    aparecer, ni con un "sin defectos" — simplemente no se pinta). Los
    defectos sin `origen` (snapshots anteriores a #442, o una tarea ANALIZAR
    sin las tres capas) van en un grupo sin etiqueta, al final.

    Returns:
        [{'etiqueta': str|None, 'textos': [str, ...]}, ...]

    Clave `textos`, no `items`: en Jinja2 `grupo.items` resuelve al método
    `dict.items()` antes que a la clave del diccionario (TypeError al iterar).
    """
    if not defectos:
        return []

    grupos = []
    for origen in ORDEN_ORIGEN:
        textos = [d.get('texto', '') for d in defectos if d.get('origen') == origen]
        if textos:
            grupos.append({'etiqueta': ETIQUETA_ORIGEN[origen], 'textos': textos})

    sin_origen = [d.get('texto', '') for d in defectos if not d.get('origen')]
    if sin_origen:
        grupos.append({'etiqueta': None, 'textos': sin_origen})

    return grupos
