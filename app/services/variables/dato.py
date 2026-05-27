"""
Variables de tipo 'dato' — leen directamente un campo del modelo Proyecto.

Fuente de verdad: campo rellenado manualmente por el tramitador.
No requieren cómputo; devuelven el valor crudo (o None si no está informado).
"""
from __future__ import annotations

from app.services.variables import variable


@variable('sin_linea_aerea')
def _(ctx) -> bool | None:
    """True si la instalación no contiene ninguna línea aérea."""
    proyecto = ctx.expediente.proyecto
    return proyecto.sin_linea_aerea if proyecto else None


@variable('max_tension_nominal_kv')
def _(ctx) -> float | None:
    """Tensión nominal máxima de la instalación en kV. Numeric → float para comparaciones."""
    proyecto = ctx.expediente.proyecto
    if proyecto is None or proyecto.max_tension_nominal_kv is None:
        return None
    return float(proyecto.max_tension_nominal_kv)


@variable('solo_suelo_urbano_urbanizable')
def _(ctx) -> bool | None:
    """True si el recorrido íntegro de las instalaciones es en suelo urbano o urbanizable."""
    proyecto = ctx.expediente.proyecto
    return proyecto.solo_suelo_urbano_urbanizable if proyecto else None
