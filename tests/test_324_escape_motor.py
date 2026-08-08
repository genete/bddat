"""
Tests #324 — Mecanismo de escape del motor.

Bloques:
  A) EvaluacionResult.puede_escapar — campo propagado correctamente por el motor.
  B) bloqueo() — JSON de respuesta incluye puede_escapar.
  C) leer_bypass() — validación y lectura de parámetros de escape.
  D) Invariantes — bloqueos de invariantes_esftt no son escapables.
"""
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# A) EvaluacionResult.puede_escapar
# ---------------------------------------------------------------------------

def test_puede_escapar_es_true_en_resultado_bloquear():
    """El motor setea puede_escapar=True cuando devuelve BLOQUEAR."""
    from app.services.motor_reglas import EvaluacionResult
    res = EvaluacionResult(
        permitido=False, nivel='BLOQUEAR',
        variables_trigger={}, norma_compilada='Art. 1 RD test',
        url_norma='', motivo='test', puede_escapar=True,
    )
    assert res.puede_escapar is True


def test_puede_escapar_es_false_en_permitido():
    """PERMITIDO tiene puede_escapar=False (default del dataclass)."""
    from app.services.motor_reglas import PERMITIDO
    assert PERMITIDO.puede_escapar is False


def test_puede_escapar_es_false_en_advertir():
    """ADVERTIR tiene puede_escapar=False."""
    from app.services.motor_reglas import EvaluacionResult
    res = EvaluacionResult(
        permitido=True, nivel='ADVERTIR',
        variables_trigger={}, norma_compilada='',
        url_norma='', motivo='',
    )
    assert res.puede_escapar is False


# ---------------------------------------------------------------------------
# B) bloqueo() — JSON incluye puede_escapar
# ---------------------------------------------------------------------------

def test_bloqueo_json_incluye_puede_escapar_true(app_ctx):
    """bloqueo() con resultado del motor devuelve puede_escapar: true en JSON."""
    from app.utils.api_respuestas import bloqueo
    from app.services.motor_reglas import EvaluacionResult
    res = EvaluacionResult(
        permitido=False, nivel='BLOQUEAR',
        variables_trigger={}, norma_compilada='Art. 1 RD test',
        url_norma='https://boe.es/test', motivo='motivo de test',
        puede_escapar=True,
    )
    response, status = bloqueo(res)
    data = response.get_json()
    assert status == 422
    assert data['puede_escapar'] is True
    assert data['ok'] is False


def test_bloqueo_json_incluye_puede_escapar_false_para_invariante(app_ctx):
    """bloqueo() con resultado de invariante devuelve puede_escapar: false."""
    from app.utils.api_respuestas import bloqueo
    from app.services.motor_reglas import EvaluacionResult
    res = EvaluacionResult(
        permitido=False, nivel='BLOQUEAR',
        variables_trigger={}, norma_compilada='Hijos sin cerrar',
        url_norma='', motivo='',
        # puede_escapar=False por defecto — comportamiento de invariantes_esftt
    )
    response, status = bloqueo(res)
    data = response.get_json()
    assert status == 422
    assert data['puede_escapar'] is False


# ---------------------------------------------------------------------------
# C) leer_bypass() — validación de parámetros
# ---------------------------------------------------------------------------

def test_leer_bypass_sin_bypass_devuelve_nones():
    """Sin bypass en el form, no hay acción de escape."""
    from app.utils.api_respuestas import leer_bypass
    justificacion, err = leer_bypass({})
    assert justificacion is None
    assert err is None


def test_leer_bypass_bypass_false_devuelve_nones():
    from app.utils.api_respuestas import leer_bypass
    justificacion, err = leer_bypass({'bypass': 'false'})
    assert justificacion is None
    assert err is None


def test_leer_bypass_bypass_true_sin_justificacion_devuelve_error_400(app_ctx):
    """bypass=true sin justificacion → error 400."""
    from app.utils.api_respuestas import leer_bypass
    justificacion, err = leer_bypass({'bypass': 'true'})
    assert justificacion is None
    assert err is not None
    response, status = err
    assert status == 400
    assert response.get_json()['ok'] is False


def test_leer_bypass_justificacion_solo_espacios_devuelve_error_400(app_ctx):
    """Justificación vacía (solo espacios) → error 400."""
    from app.utils.api_respuestas import leer_bypass
    justificacion, err = leer_bypass({'bypass': 'true', 'justificacion': '   '})
    assert justificacion is None
    assert err is not None


def test_leer_bypass_con_justificacion_valida_devuelve_texto():
    """bypass=true + justificacion con texto → devuelve el texto."""
    from app.utils.api_respuestas import leer_bypass
    justificacion, err = leer_bypass({'bypass': 'true', 'justificacion': 'Tramitación urgente'})
    assert justificacion == 'Tramitación urgente'
    assert err is None


def test_leer_bypass_acepta_bypass_uno():
    """bypass='1' también activa el escape."""
    from app.utils.api_respuestas import leer_bypass
    justificacion, err = leer_bypass({'bypass': '1', 'justificacion': 'justificado'})
    assert justificacion == 'justificado'
    assert err is None


def test_leer_bypass_acepta_bool_true_de_json():
    """bypass=True (bool nativo, body JSON de api_expedientes.py #616) también activa el escape."""
    from app.utils.api_respuestas import leer_bypass
    justificacion, err = leer_bypass({'bypass': True, 'justificacion': 'justificado'})
    assert justificacion == 'justificado'
    assert err is None


# ---------------------------------------------------------------------------
# D) Invariantes — bloqueos de invariantes_esftt no son escapables
# ---------------------------------------------------------------------------

def test_invariante_bloquear_no_es_escapable():
    """_bloquear() de invariantes_esftt produce puede_escapar=False por defecto."""
    from app.services.invariantes_esftt import _bloquear
    res = _bloquear('Hijos sin cerrar')
    assert res.puede_escapar is False
    assert res.permitido is False
    assert res.nivel == 'BLOQUEAR'
