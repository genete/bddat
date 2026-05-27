"""
Evaluador de requisitos documentales por solicitud (#192).

Dado una solicitud y el dict de variables del expediente, determina qué
requisitos del catálogo son aplicables y cuáles tienen ya un documento del
pool asignado.

Uso típico (dentro de ContextoAnalisisDocumental — ver #495):

    from app.services.requisitos import evaluar_requisitos
    from app.services.assembler import build

    _, variables = build(expediente, objeto=fase)
    resultado = evaluar_requisitos(solicitud, variables)
    todos_cubiertos = resultado['todos_cubiertos']
    checklist = resultado['items']

Semántica de condiciones:
    Cada RequisitoDocumental puede tener cero o más CondicionRequisito.
    Todas se evalúan en AND. Un requisito sin condiciones es universal
    (aplica siempre). Los operadores soportados son los mismos que
    CondicionRegla: EQ, NEQ, IN, NOT_IN, IS_NULL, NOT_NULL.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.exc import OperationalError, ProgrammingError

from app.models.requisitos_documentales import RequisitoDocumental, DocumentoRequisito

log = logging.getLogger(__name__)

# Valor devuelto en caso de error de BD o tabla inexistente
_RESULTADO_DEGRADADO: dict = {
    'items': [],
    'todos_cubiertos': True,
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
    log.warning('requisitos: operador desconocido "%s" — condición ignorada', operador)
    return True


def _requisito_aplica(requisito: Any, variables: dict) -> bool:
    """
    Devuelve True si todas las condiciones del requisito se cumplen.
    Un requisito sin condiciones es universal — siempre aplica.
    """
    for cond in requisito.condiciones:
        nombre_var = cond.variable.nombre if cond.variable else None
        if nombre_var is None:
            log.warning(
                'requisitos: condicion_id=%s sin variable — ignorada', cond.id
            )
            continue
        valor_var = variables.get(nombre_var)
        if not _evaluar_condicion(cond.operador, valor_var, cond.valor):
            return False
    return True


def evaluar_requisitos(solicitud: Any, variables: dict) -> dict:
    """
    Evalúa los requisitos documentales aplicables a una solicitud concreta.

    Args:
        solicitud:  Instancia de Solicitud con relaciones accesibles.
        variables:  Dict de variables del motor (producido por assembler.build).

    Returns:
        {
            'items': [
                {
                    'requisito':  RequisitoDocumental,
                    'cubierto':   bool,
                    'documento':  Documento | None,
                },
                ...
            ],
            'todos_cubiertos': bool,
            'error': bool,   # True solo si hubo fallo de BD
        }

    El resultado es siempre permisivo en caso de error (todos_cubiertos=True)
    para no bloquear la tramitación por un fallo técnico (#347).
    """
    try:
        todos_requisitos = (
            RequisitoDocumental.query
            .order_by(RequisitoDocumental.orden)
            .all()
        )
    except (OperationalError, ProgrammingError):
        log.warning('requisitos: tabla requisitos_documentales no disponible')
        return _RESULTADO_DEGRADADO

    # Índice de vinculaciones ya hechas para esta solicitud: requisito_id → DocumentoRequisito
    try:
        vinculaciones = {
            dr.requisito_id: dr
            for dr in DocumentoRequisito.query.filter_by(solicitud_id=solicitud.id).all()
        }
    except (OperationalError, ProgrammingError):
        log.warning('requisitos: tabla documentos_requisito no disponible')
        return _RESULTADO_DEGRADADO

    items = []
    for req in todos_requisitos:
        if not _requisito_aplica(req, variables):
            continue
        vinculo = vinculaciones.get(req.id)
        items.append({
            'requisito': req,
            'cubierto':  vinculo is not None,
            'documento': vinculo.documento if vinculo else None,
        })

    todos_cubiertos = all(item['cubierto'] for item in items)

    return {
        'items':          items,
        'todos_cubiertos': todos_cubiertos,
        'error':          False,
    }
