"""Checker de consistencia catalogo_variables <-> Variable Registry (#587).

Dirección inversa de #347 (`catalogo_requerido.py`): allí la fila de catálogo
asume que existe un código en BD; aquí `CatalogoVariable.nombre` asume que
existe una función registrada en el Variable Registry
(`app/services/variables`, `_REGISTRY`). Sin esa función el assembler evalúa
la condición contra `None` (`app/services/assembler.py:188`, fallback ya
defensivo) sin lanzar excepción — riesgo de negocio silencioso, no de arranque.

validar_registro_variables() es la única fuente de verdad de este desajuste.
Llamar desde create_app() junto a validar_catalogo() (#347), tras db.init_app().
"""
from __future__ import annotations

import logging
from typing import List

log = logging.getLogger(__name__)


def validar_registro_variables() -> List[str]:
    """
    Compara `CatalogoVariable.nombre` (activa=True) con las claves del
    Variable Registry en ambas direcciones:

    - Variable activa en catálogo sin función registrada → el assembler la
      evaluaría contra `None` (condición de negocio incorrecta en silencio).
    - Función registrada sin fila `activa=True` correspondiente → registro
      huérfano, invisible para el Supervisor en el formulario de alta de
      reglas. Mismo valor informativo, no bloqueante.

    Returns:
        Lista de strings describiendo cada desajuste. Lista vacía → catálogo
        y registro coinciden. Nunca lanza excepción; si la BD no está
        disponible loguea y devuelve lista vacía (mismo criterio que
        validar_catalogo(), #347).
    """
    from sqlalchemy.exc import OperationalError, ProgrammingError

    from app.services.variables import get_registry

    try:
        from app.models.motor_reglas import CatalogoVariable
        activas = {cv.nombre for cv in CatalogoVariable.query.filter_by(activa=True).all()}
    except (OperationalError, ProgrammingError) as exc:
        log.warning('registro_variables: tabla catalogo_variables no disponible — %s', exc)
        # Rollback necesario: en PostgreSQL un error aborta la transacción
        # y las queries siguientes fallarían con InFailedSqlTransaction.
        try:
            from app import db as _db
            _db.session.rollback()
        except Exception:
            pass
        return []

    registradas = set(get_registry().keys())

    avisos: List[str] = []
    for nombre in sorted(activas - registradas):
        avisos.append(
            f"catalogo_variables.nombre='{nombre}' (activa=True) sin función en el "
            f'Variable Registry → el assembler la evaluaría contra None'
        )
    for nombre in sorted(registradas - activas):
        avisos.append(
            f"Variable Registry tiene '{nombre}' sin fila activa=True correspondiente "
            f'en catalogo_variables → registro huérfano, invisible para el Supervisor'
        )

    if avisos:
        log.error(
            'registro_variables: desajustes catalogo_variables <-> Variable Registry:\n%s',
            '\n'.join(f'  - {a}' for a in avisos),
        )

    return avisos
