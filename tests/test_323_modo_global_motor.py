"""Tests issue #323 — Modo global del motor de reglas.

Bloques:
  A) ConfiguracionSistema.get() — defensividad ante BD no disponible y clave ausente.
  B) _aplicar_modo_global() — transformación según modo BLOQUEAR / SOLO_ADVERTIR / INACTIVO.
"""
from unittest.mock import patch

import pytest
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.services.motor_reglas import EvaluacionResult, PERMITIDO


def _res(nivel):
    """EvaluacionResult mínimo con el nivel indicado."""
    return EvaluacionResult(
        permitido=(nivel != 'BLOQUEAR'),
        nivel=nivel,
        variables_trigger={},
        norma_compilada='art. 1 RD test',
        url_norma='https://boe.es/test',
        motivo='motivo de test',
    )


def _mock_modo(valor):
    return patch('app.routes.api_bc.ConfiguracionSistema.get', return_value=valor)


# ---------------------------------------------------------------------------
# A) ConfiguracionSistema.get()
# ---------------------------------------------------------------------------

def test_configuracion_get_bd_disponible(app_ctx):
    """La clave sembrada en la migración se lee correctamente."""
    from app.models.configuracion_sistema import ConfiguracionSistema
    assert ConfiguracionSistema.get('motor.modo_operacion') == 'BLOQUEAR'


def test_configuracion_get_clave_ausente_devuelve_default(app_ctx):
    """Una clave inexistente devuelve el default sin lanzar excepción."""
    from app.models.configuracion_sistema import ConfiguracionSistema
    assert ConfiguracionSistema.get('clave.inexistente', 'X') == 'X'


def test_configuracion_get_operational_error_devuelve_default(app_ctx):
    """OperationalError → devuelve default sin propagar la excepción."""
    from app.models.configuracion_sistema import ConfiguracionSistema
    with patch.object(
        ConfiguracionSistema.query, 'filter_by',
        side_effect=OperationalError('conn refused', None, None),
    ):
        result = ConfiguracionSistema.get('motor.modo_operacion', 'BLOQUEAR')
    assert result == 'BLOQUEAR'


def test_configuracion_get_programming_error_devuelve_default(app_ctx):
    """ProgrammingError (tabla inexistente) → devuelve default sin propagar."""
    from app.models.configuracion_sistema import ConfiguracionSistema
    with patch.object(
        ConfiguracionSistema.query, 'filter_by',
        side_effect=ProgrammingError('relation does not exist', None, None),
    ):
        result = ConfiguracionSistema.get('motor.modo_operacion', 'BLOQUEAR')
    assert result == 'BLOQUEAR'


# ---------------------------------------------------------------------------
# B) _aplicar_modo_global()
# ---------------------------------------------------------------------------

def test_modo_bloquear_no_modifica_bloquear():
    from app.routes.api_bc import _aplicar_modo_global
    res = _res('BLOQUEAR')
    with _mock_modo('BLOQUEAR'):
        out = _aplicar_modo_global(res)
    assert out is res


def test_modo_bloquear_no_modifica_advertir():
    from app.routes.api_bc import _aplicar_modo_global
    res = _res('ADVERTIR')
    with _mock_modo('BLOQUEAR'):
        out = _aplicar_modo_global(res)
    assert out is res


def test_modo_inactivo_devuelve_permitido_siempre():
    from app.routes.api_bc import _aplicar_modo_global
    for nivel in ('BLOQUEAR', 'ADVERTIR', ''):
        res = _res(nivel)
        with _mock_modo('INACTIVO'):
            out = _aplicar_modo_global(res)
        assert out is PERMITIDO, f"INACTIVO debería devolver PERMITIDO para nivel={nivel!r}"


def test_modo_solo_advertir_convierte_bloquear():
    """SOLO_ADVERTIR: BLOQUEAR → ADVERTIR y permitido=True, preservando motivo y norma."""
    from app.routes.api_bc import _aplicar_modo_global
    res = _res('BLOQUEAR')
    with _mock_modo('SOLO_ADVERTIR'):
        out = _aplicar_modo_global(res)
    assert out.permitido is True
    assert out.nivel == 'ADVERTIR'
    assert out.motivo == res.motivo
    assert out.norma_compilada == res.norma_compilada
    assert out.url_norma == res.url_norma


def test_modo_solo_advertir_no_modifica_advertir():
    """SOLO_ADVERTIR: un ADVERTIR original no se toca."""
    from app.routes.api_bc import _aplicar_modo_global
    res = _res('ADVERTIR')
    with _mock_modo('SOLO_ADVERTIR'):
        out = _aplicar_modo_global(res)
    assert out is res


def test_modo_solo_advertir_no_modifica_permitido():
    """SOLO_ADVERTIR: PERMITIDO (nivel='') no se toca."""
    from app.routes.api_bc import _aplicar_modo_global
    with _mock_modo('SOLO_ADVERTIR'):
        out = _aplicar_modo_global(PERMITIDO)
    assert out is PERMITIDO


def test_bd_no_disponible_defaultea_a_bloquear():
    """Si BD falla al leer el modo, el default BLOQUEAR mantiene el comportamiento estricto."""
    from app.routes.api_bc import _aplicar_modo_global
    res = _res('BLOQUEAR')
    with patch('app.routes.api_bc.ConfiguracionSistema.get', return_value='BLOQUEAR'):
        out = _aplicar_modo_global(res)
    assert out is res
    assert out.permitido is False
