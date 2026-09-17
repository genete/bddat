"""
Variables de tipo 'plazo' — delegan en plazos.py para obtener el estado
del plazo legal asociado al elemento en contexto.

Tres niveles pueden tener plazo: la Solicitud y la Tarea, que portan fecha
administrativa propia (#788), y la Fase finalizadora, excepción acotada de
ADR-048 — RESOLUCION_DUP/AAP/AAC son el acto, no taxonomía. Desde #778 el
servicio lo dice en su propia interfaz —una función por cada uno— y aquí se
elige cuál llamar, en vez de pasar un literal de nivel y dejar que el servicio
responda «sin plazo» a los que no aplican. El Trámite se resuelve aquí mismo,
sin tocar el servicio ni la BD.
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

    Trámite se identifica igual —el contexto puede traerlo— pero devuelve nivel
    None: no hay plazo que buscarle. Fase devuelve 'FASE' siempre: el filtro a
    solo finalizadoras lo hace el catálogo (sin fila para una fase taxonómica,
    `obtener_estado_plazo_fase` devuelve SIN_PLAZO), no esta función — mismo
    criterio que el resto del servicio de plazos.
    """
    obj = ctx._objeto
    if obj is None or isinstance(obj, dict):
        return None, None
    if hasattr(obj, 'fases') and not hasattr(obj, 'solicitud'):
        return obj, 'SOLICITUD'
    if hasattr(obj, 'solicitud') and hasattr(obj, 'tramites'):
        return obj, 'FASE'
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
    if nivel == 'SOLICITUD':
        return plazos.obtener_estado_plazo_solicitud(elemento, ctx=ctx)
    if nivel == 'FASE':
        return plazos.obtener_estado_plazo_fase(elemento, ctx=ctx)
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
