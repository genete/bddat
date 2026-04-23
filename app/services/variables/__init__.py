"""
Variable Registry — registro central de funciones de cómputo de variables del motor.

Cada módulo (dato, calculado, derivado_fase, derivado_documento) registra sus funciones
usando el decorador @variable. Al importar los módulos, las funciones se registran
automáticamente en _REGISTRY. El assembler invoca cada función con un ExpedienteContext.

Ciclo de vida completo: docs/DISEÑO_CONTEXT_ASSEMBLER.md §Ciclo de vida de una variable
"""
from __future__ import annotations

from typing import Callable, Any

_REGISTRY: dict[str, Callable] = {}


def variable(nombre: str):
    """
    Decorador que registra una función de cómputo de variable en _REGISTRY.

    Uso:
        @variable('sin_linea_aerea')
        def _(ctx: ExpedienteContext) -> bool | None:
            return ctx.expediente.proyecto.sin_linea_aerea
    """
    def decorator(fn: Callable) -> Callable:
        _REGISTRY[nombre] = fn
        return fn
    return decorator


def get_registry() -> dict[str, Callable]:
    """Devuelve el registry completo (solo para tests e inspección)."""
    return _REGISTRY


# Importar submódulos para que sus @variable se registren al arrancar Flask
from app.services.variables import dato        # noqa: E402, F401
from app.services.variables import calculado   # noqa: E402, F401
