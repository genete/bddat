"""Tests issue #587 — Checker de consistencia catalogo_variables <-> Variable Registry.

Mismo patrón que tests/test_347_defensividad_backend.py (bloque A): mocks, sin BD real.
Dirección inversa de #347 — aquí la fila de catálogo asume que existe código
(función registrada), no al revés.
"""
import logging
from unittest.mock import MagicMock, patch

from sqlalchemy.exc import OperationalError


def _mock_catalogo_variable(nombres_activas):
    mock_modelo = MagicMock()
    filas = [MagicMock(nombre=n) for n in nombres_activas]
    mock_modelo.query.filter_by.return_value.all.return_value = filas
    return mock_modelo


def test_variable_activa_sin_funcion_registrada_se_reporta(caplog):
    """catalogo_variables tiene una fila activa=True que el Registry no conoce."""
    from app.checks.registro_variables import validar_registro_variables

    mock_cv = _mock_catalogo_variable(['tension_nominal_kv', 'variable_fantasma'])

    with patch('app.models.motor_reglas.CatalogoVariable', mock_cv), \
         patch('app.services.variables.get_registry',
               return_value={'tension_nominal_kv': lambda ctx: None}):
        with caplog.at_level(logging.ERROR, logger='app.checks.registro_variables'):
            avisos = validar_registro_variables()

    assert any("nombre='variable_fantasma'" in a for a in avisos)
    assert not any("nombre='tension_nominal_kv'" in a for a in avisos)


def test_funcion_registrada_sin_fila_activa_se_reporta_como_huerfana():
    """Una función del Registry sin fila activa=True correspondiente es huérfana."""
    from app.checks.registro_variables import validar_registro_variables

    mock_cv = _mock_catalogo_variable(['tension_nominal_kv'])

    with patch('app.models.motor_reglas.CatalogoVariable', mock_cv), \
         patch('app.services.variables.get_registry',
               return_value={'tension_nominal_kv': lambda ctx: None,
                              'huerfana_sin_fila': lambda ctx: None}):
        avisos = validar_registro_variables()

    assert any("Variable Registry tiene 'huerfana_sin_fila'" in a for a in avisos)


def test_catalogo_y_registry_coinciden_lista_vacia():
    """Con activas == registradas, no hay nada que reportar."""
    from app.checks.registro_variables import validar_registro_variables

    mock_cv = _mock_catalogo_variable(['tension_nominal_kv', 'sin_linea_aerea'])

    with patch('app.models.motor_reglas.CatalogoVariable', mock_cv), \
         patch('app.services.variables.get_registry',
               return_value={'tension_nominal_kv': lambda ctx: None,
                              'sin_linea_aerea': lambda ctx: None}):
        avisos = validar_registro_variables()

    assert avisos == []


def test_bd_no_disponible_no_lanza():
    """Si la BD lanza OperationalError, el checker loguea y continúa sin excepción."""
    from app.checks.registro_variables import validar_registro_variables

    mock_cv = MagicMock()
    mock_cv.query.filter_by.return_value.all.side_effect = OperationalError(
        'connection refused', None, None
    )

    with patch('app.models.motor_reglas.CatalogoVariable', mock_cv):
        avisos = validar_registro_variables()  # no debe lanzar

    assert avisos == []
