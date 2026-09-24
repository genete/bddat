"""
Variables de tipo 'plazo' — delegan en plazos.py para obtener el estado
del plazo legal asociado al elemento en contexto.

Hoy solo la Tarea tiene implementación: es el único nodo del árbol con un
plazo propio que el servicio sabe medir (`obtener_estado_plazo_tarea`).

La Solicitud y la Fase la tuvieron (#788; la Fase finalizadora desde
ADR-048) y la perdieron en #931: el plazo de resolver es del ACTO (#930,
ADR-049 §E), no de su contenedor ni de la fase que lo resuelve, y las dos
funciones a las que llamaban se retiraron. Degradan como ya degradaba el
Trámite —taxonomía ESFTT sin plazo propio—, sin tocar el servicio ni la BD.

Las variables NO se retiran (#931, D1): son genéricas —«el estado del plazo
del sujeto en contexto»— y la ley puede condicionar un trámite a ese estado.
El día que una regla necesite el plazo de un acto se añade aquí la rama del
sujeto `ActoSolicitud`; hoy ese objeto no llega al contexto del motor.
"""
from __future__ import annotations

from app.services.variables import variable


def _resolver_elemento(ctx):
    """
    Devuelve (elemento, nivel) del objeto en contexto usando duck-typing.

    Misma lógica que ExpedienteContext en assembler.py:
      Solicitud → tiene 'fases', NO tiene 'solicitud'
      Fase      → tiene 'solicitud' y 'tramites'
      Tramite   → tiene 'fase', NO tiene 'tramites'
      Tarea     → tiene 'tramite'

    Solicitud, Fase y Trámite se identifican igual —el contexto puede
    traerlos— pero devuelven nivel None: no hay plazo que buscarles (#931).
    """
    obj = ctx._objeto
    if obj is None or isinstance(obj, dict):
        return None, None
    if hasattr(obj, 'fases') and not hasattr(obj, 'solicitud'):
        return obj, None            # Solicitud — el plazo es de cada acto (#930)
    if hasattr(obj, 'solicitud') and hasattr(obj, 'tramites'):
        return obj, None            # Fase — ídem, aunque sea la que resuelve el acto
    if hasattr(obj, 'fase') and not hasattr(obj, 'tramites'):
        return obj, None            # Trámite — taxonomía ESFTT, no figura jurídica
    if hasattr(obj, 'tramite'):
        return obj, 'TAREA'
    return None, None


def _estado_plazo(ctx):
    """EstadoPlazo del elemento en contexto, o None si el nivel no tiene plazo."""
    elemento, nivel = _resolver_elemento(ctx)
    if nivel is None:
        return None
    from app.services import plazos
    return plazos.obtener_estado_plazo_tarea(elemento, ctx=ctx)


@variable('estado_plazo')
def _(ctx) -> str:
    """
    Estado del plazo legal del elemento en tramitación.
    Valores: 'SIN_PLAZO' | 'EN_PLAZO' | 'PROXIMO_VENCER' | 'VENCIDO' | 'CUMPLIDO'
    """
    ep = _estado_plazo(ctx)
    return ep.estado if ep else 'SIN_PLAZO'


@variable('efecto_plazo')
def _(ctx) -> str:
    """
    Efecto legal del vencimiento del plazo del elemento en tramitación.
    Valores: 'NINGUNO' | 'SILENCIO_ESTIMATORIO' | 'RESPONSABILIDAD_DISCIPLINARIA' | ...
    """
    ep = _estado_plazo(ctx)
    return ep.efecto if ep else 'NINGUNO'
