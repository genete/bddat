"""
Consolidación de defectos para el contenedor de la tarea ANALIZAR (#442).

Agrega las contribuciones de los tres proveedores que se enchufan al
contenedor: check documental (#495), check de ítems técnicos (#581) y
selector de requerimientos (#440).

FORMA DEL ITEM:
    {'texto': str, 'origen': 'documental'|'tecnico'|'requerimiento', 'tarea_id': int}

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
        items.append({'texto': texto, 'origen': 'documental', 'tarea_id': tarea.id})
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
        items.append({'texto': texto, 'origen': 'tecnico', 'tarea_id': tarea.id})
    return items, resultado['todos_revisados']


def consolidar_defectos(tarea) -> dict:
    """
    Consolida los defectos aplicables a la tarea ANALIZAR dada.

    Returns:
        {'items': list, 'completo': bool, 'error': bool}
    """
    items_documental, completo_documental = _items_documental(tarea)
    items_tecnico, completo_tecnico = _items_tecnico(tarea)

    return {
        'items': items_documental + items_tecnico,
        'completo': completo_documental and completo_tecnico,
        'error': False,
    }
