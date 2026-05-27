"""
Variables de tipo 'plazo' — delegan en plazos.py para obtener el estado
del plazo legal asociado al elemento en contexto.

Stub Fase 2 (#190): siempre devuelven SIN_PLAZO / NINGUNO.
M3 (#172): plazos.obtener_estado_plazo() calculará el estado real.
"""
from __future__ import annotations

from app.services.variables import variable


def _resolver_elemento(ctx):
    """
    Devuelve (elemento, tipo_elemento) del objeto en contexto usando duck-typing.

    Misma lógica que ExpedienteContext en assembler.py:
      Solicitud → tiene 'fases', NO tiene 'solicitud'
      Fase      → tiene 'solicitud' y 'tramites'
      Tramite   → tiene 'fase', NO tiene 'tramites'
      Tarea     → tiene 'tramite'
    """
    obj = ctx._objeto
    if obj is None or isinstance(obj, dict):
        return None, None
    if hasattr(obj, 'fases') and not hasattr(obj, 'solicitud'):
        return obj, 'SOLICITUD'
    if hasattr(obj, 'solicitud') and hasattr(obj, 'tramites'):
        return obj, 'FASE'
    if hasattr(obj, 'fase') and not hasattr(obj, 'tramites'):
        return obj, 'TRAMITE'
    if hasattr(obj, 'tramite'):
        return obj, 'TAREA'
    return None, None


@variable('estado_plazo')
def _(ctx) -> str:
    """
    Estado del plazo legal del elemento en tramitación.
    Valores: 'SIN_PLAZO' | 'EN_PLAZO' | 'PROXIMO_VENCER' | 'VENCIDO'
    """
    elemento, tipo = _resolver_elemento(ctx)
    if elemento is None:
        return 'SIN_PLAZO'
    from app.services import plazos
    return plazos.obtener_estado_plazo(elemento, tipo, ctx=ctx).estado


@variable('efecto_plazo')
def _(ctx) -> str:
    """
    Efecto legal del vencimiento del plazo del elemento en tramitación.
    Valores: 'NINGUNO' | 'SILENCIO_ESTIMATORIO' | 'RESPONSABILIDAD_DISCIPLINARIA' | ...
    """
    elemento, tipo = _resolver_elemento(ctx)
    if elemento is None:
        return 'NINGUNO'
    from app.services import plazos
    return plazos.obtener_estado_plazo(elemento, tipo, ctx=ctx).efecto
