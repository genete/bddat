"""Tests issue #777 — no-regresión de app.services.requisitos._requisito_aplica.

Antes de #777, condiciones_requisito estaba vacía y TODOS los requisitos eran
universales (sin condiciones -> aplica siempre). Esta migración empieza a
poblar condiciones reales; este test fija que el camino "sin condiciones"
sigue comportándose igual, sin verse afectado por el nuevo camino "con
condiciones".
"""
from app.services.requisitos import _requisito_aplica


class _StubVariable:
    def __init__(self, nombre):
        self.nombre = nombre


class _StubCondicion:
    def __init__(self, id_, nombre_var, operador, valor):
        self.id = id_
        self.variable = _StubVariable(nombre_var) if nombre_var else None
        self.operador = operador
        self.valor = valor


class _StubRequisito:
    def __init__(self, condiciones=None):
        self.condiciones = condiciones or []


# ---------------------------------------------------------------------------
# Requisito sin condiciones: universal, siempre aplica (comportamiento previo
# a #777 para los 9 requisitos de #408, no debe cambiar)
# ---------------------------------------------------------------------------

def test_requisito_sin_condiciones_aplica_con_variables_vacias():
    requisito = _StubRequisito(condiciones=[])
    assert _requisito_aplica(requisito, {}) is True


def test_requisito_sin_condiciones_aplica_independientemente_de_las_variables():
    """Ninguna variable coincide ni desmiente nada — sigue aplicando: no hay
    condición que evaluar."""
    requisito = _StubRequisito(condiciones=[])
    variables = {
        'solicitante_es_persona_juridica': False,
        'solicitud_por_representante': False,
        'solicitud_incluye_dup': False,
    }
    assert _requisito_aplica(requisito, variables) is True


# ---------------------------------------------------------------------------
# Requisito con condiciones: el camino nuevo que #777 empieza a poblar
# ---------------------------------------------------------------------------

def test_requisito_con_condicion_cumplida_aplica():
    cond = _StubCondicion(1, 'solicitante_es_persona_juridica', 'EQ', True)
    requisito = _StubRequisito(condiciones=[cond])
    variables = {'solicitante_es_persona_juridica': True}
    assert _requisito_aplica(requisito, variables) is True


def test_requisito_con_condicion_no_cumplida_no_aplica():
    cond = _StubCondicion(1, 'solicitante_es_persona_juridica', 'EQ', True)
    requisito = _StubRequisito(condiciones=[cond])
    variables = {'solicitante_es_persona_juridica': False}
    assert _requisito_aplica(requisito, variables) is False


def test_requisito_con_variable_ausente_del_dict_no_aplica():
    """Variable no presente en el dict de variables (None) != True -> no aplica."""
    cond = _StubCondicion(1, 'solicitud_incluye_dup', 'EQ', True)
    requisito = _StubRequisito(condiciones=[cond])
    assert _requisito_aplica(requisito, {}) is False


def test_requisito_con_condicion_sin_variable_se_ignora():
    """Condición huérfana (variable_id sin FK resuelta) se ignora — no bloquea
    el requisito por sí sola."""
    cond = _StubCondicion(1, None, 'EQ', True)
    requisito = _StubRequisito(condiciones=[cond])
    assert _requisito_aplica(requisito, {}) is True
