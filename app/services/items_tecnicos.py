"""
Evaluador de ítems técnicos por solicitud (#581).

Análogo a app/services/requisitos.py::evaluar_requisitos, pero contra el
catálogo de contenido técnico del proyecto (ItemTecnico/CondicionItemTecnico)
en vez de requisitos documentales. El veredicto del tramitador se registra en
CoberturaItemTecnico — máquina de 3 estados, ver su docstring
(app/models/items_tecnicos.py).
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.exc import OperationalError, ProgrammingError

from app.models.items_tecnicos import ItemTecnico, CoberturaItemTecnico

log = logging.getLogger(__name__)

# Valor devuelto en caso de error de BD o tabla inexistente
_RESULTADO_DEGRADADO: dict = {
    'items': [],
    'todos_revisados': True,
    'error': True,
}


def _evaluar_condicion(operador: str, valor_var: Any, valor_ref: Any) -> bool:
    """Evalúa una condición individual. Devuelve True si se cumple."""
    if operador == 'EQ':
        return valor_var == valor_ref
    if operador == 'NEQ':
        return valor_var != valor_ref
    if operador == 'IN':
        return valor_var in (valor_ref or [])
    if operador == 'NOT_IN':
        return valor_var not in (valor_ref or [])
    if operador == 'IS_NULL':
        return valor_var is None
    if operador == 'NOT_NULL':
        return valor_var is not None
    log.warning('items_tecnicos: operador desconocido "%s" — condición ignorada', operador)
    return True


def _item_aplica(item: Any, variables: dict) -> bool:
    """
    Devuelve True si todas las condiciones del ítem se cumplen.
    Un ítem sin condiciones es universal — siempre aplica.
    """
    for cond in item.condiciones:
        nombre_var = cond.variable.nombre if cond.variable else None
        if nombre_var is None:
            log.warning(
                'items_tecnicos: condicion_id=%s sin variable — ignorada', cond.id
            )
            continue
        valor_var = variables.get(nombre_var)
        if not _evaluar_condicion(cond.operador, valor_var, cond.valor):
            return False
    return True


def evaluar_items_tecnicos(solicitud: Any, variables: dict) -> dict:
    """
    Evalúa los ítems técnicos aplicables a una solicitud concreta.

    Args:
        solicitud:  Instancia de Solicitud con relaciones accesibles.
        variables:  Dict de variables del motor (producido por assembler.build).

    Returns:
        {
            'items': [
                {'item': ItemTecnico, 'cobertura': CoberturaItemTecnico | None},
                ...
            ],
            'todos_revisados': bool,  # True si ningún ítem aplicable está NO_REVISADO
            'error': bool,             # True solo si hubo fallo de BD
        }

    El resultado es siempre permisivo en caso de error (todos_revisados=True)
    para no bloquear la tramitación por un fallo técnico (mismo criterio que
    evaluar_requisitos, #347).
    """
    try:
        todos_items = (
            ItemTecnico.query
            .filter_by(activo=True)
            .order_by(ItemTecnico.orden)
            .all()
        )
    except (OperationalError, ProgrammingError):
        log.warning('items_tecnicos: tabla items_tecnicos no disponible')
        return _RESULTADO_DEGRADADO

    try:
        coberturas = {
            c.item_tecnico_id: c
            for c in CoberturaItemTecnico.query.filter_by(solicitud_id=solicitud.id).all()
        }
    except (OperationalError, ProgrammingError):
        log.warning('items_tecnicos: tabla coberturas_item_tecnico no disponible')
        return _RESULTADO_DEGRADADO

    items = []
    for item in todos_items:
        if not _item_aplica(item, variables):
            continue
        items.append({'item': item, 'cobertura': coberturas.get(item.id)})

    def _revisado(cobertura) -> bool:
        return cobertura is not None and bool((cobertura.texto or '').strip())

    todos_revisados = all(_revisado(it['cobertura']) for it in items)

    return {
        'items': items,
        'todos_revisados': todos_revisados,
        'error': False,
    }
