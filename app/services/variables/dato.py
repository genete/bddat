"""
Variables de tipo 'dato' — leen directamente un campo del modelo (Proyecto, Expediente).

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


@variable('proyecto_sin_principal')
def _(ctx) -> bool:
    """True si el proyecto no tiene documento principal anclado (#887, ADR-044 §D).

    Es dato y no cálculo: lee `proyectos.documento_principal_id`, sin consultas ni
    agregación —a diferencia de `tasa_impagada` o `tiene_punto_acceso_conexion`, que
    cuentan coberturas del checklist—. Por lo mismo no necesita degradación por
    catálogo ausente: no depende de ninguna fila de catálogo.

    Polaridad negativa, como `tasa_impagada`: True = falta, que es la condición que
    hace saltar la regla `BLOQUEAR`. Sin proyecto (imposible por constraint:
    `expedientes.proyecto_id` es NOT NULL) devuelve False, que es no bloquear.
    """
    proyecto = ctx.expediente.proyecto
    if proyecto is None:
        return False
    return proyecto.documento_principal_id is None


@variable('expediente_heredado')
def _(ctx) -> bool:
    """True si el expediente viene migrado del sistema anterior (#887).

    `expedientes.heredado` es *nullable* y NULL es lo normal en los nacidos aquí, así
    que se lee con `bool(...)`: NULL significa «no heredado», no «desconocido». La
    excepción de los heredados va como condición de la regla y no como bypass manual
    porque un expediente migrado nunca va a tener el dato, y sin ella el técnico
    tendría que justificar el escape fase tras fase en cada uno de ellos.
    """
    return bool(ctx.expediente.heredado)
