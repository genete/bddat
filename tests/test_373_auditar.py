"""Tests unitarios issue #373 — auditar() y auditar_multi().

Sin BD real — usa stubs/mocks de los modelos y el registry de variables.
"""
import pytest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Stubs mínimos para ReglaMotor y estructuras relacionadas
# ---------------------------------------------------------------------------

def _stub_condicion(nombre_var, operador, valor):
    c = MagicMock()
    c.orden = 1
    c.operador = operador
    c.valor = valor
    c.variable = MagicMock()
    c.variable.nombre = nombre_var
    return c


def _stub_regla(regla_id, sujeto, efecto, condiciones=None, excepciones=None, descripcion='', norma=None):
    r = MagicMock()
    r.id = regla_id
    r.sujeto = sujeto
    r.efecto = efecto
    r.prioridad = regla_id
    r.descripcion = descripcion
    r.condiciones = condiciones or []
    r.excepciones = excepciones or []
    r.norma = norma
    r.activa = True
    return r


def _stub_excepcion(condiciones=None, activa=True):
    e = MagicMock()
    e.activa = activa
    e.condiciones = condiciones or []
    e.norma = None
    return e


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAuditar:
    """Tests unitarios de motor_reglas.auditar()."""

    def _run(self, reglas_mock, accion, sujeto, variables):
        """Ejecuta auditar() con la lista de reglas mockeada."""
        from app.services.motor_reglas import auditar

        query_mock = MagicMock()
        query_mock.options.return_value.filter_by.return_value.all.return_value = reglas_mock

        # joinedload usa atributos de RelationshipProperty; parchearlo evita
        # que SQLAlchemy intente resolver los atributos del mock.
        jl_mock = MagicMock()
        jl_mock.return_value.joinedload.return_value = jl_mock.return_value

        with patch('app.services.motor_reglas.joinedload', jl_mock), \
             patch('app.services.motor_reglas.ReglaMotor') as MockRegla:
            MockRegla.query = query_mock
            return auditar(accion, sujeto, variables)

    def test_sin_reglas_permite_y_lista_vacia(self):
        """Sin reglas configuradas → permitido=True, reglas_evaluadas vacía."""
        resultado = self._run([], 'CREAR', 'Distribucion/AAP/RESOLUCION', {})
        assert resultado.permitido is True
        assert resultado.reglas_evaluadas == []

    def test_regla_que_dispara_advertir_incluida(self):
        """Una regla ADVERTIR que dispara aparece en reglas_evaluadas y no bloquea."""
        cond = _stub_condicion('fase_activa', 'EQ', True)
        regla = _stub_regla(1, 'Distribucion/AAP/RESOLUCION', 'ADVERTIR',
                            condiciones=[cond], descripcion='Advertencia test')

        from app.services.operadores import _OPERADORES
        with patch.dict(_OPERADORES, {'EQ': lambda a, b: a == b}):
            resultado = self._run([regla], 'CREAR', 'Distribucion/AAP/RESOLUCION',
                                  {'fase_activa': True})

        assert resultado.permitido is True
        assert len(resultado.reglas_evaluadas) == 1
        rr = resultado.reglas_evaluadas[0]
        assert rr.disparada is True
        assert rr.neutralizada is False
        assert rr.efecto == 'ADVERTIR'

    def test_regla_bloqueante_no_neutralizada_permitido_false(self):
        """Una regla BLOQUEAR sin excepciones → permitido=False."""
        cond = _stub_condicion('fase_activa', 'EQ', True)
        regla = _stub_regla(1, 'Distribucion/AAP/RESOLUCION', 'BLOQUEAR',
                            condiciones=[cond])

        from app.services.operadores import _OPERADORES
        with patch.dict(_OPERADORES, {'EQ': lambda a, b: a == b}):
            resultado = self._run([regla], 'CREAR', 'Distribucion/AAP/RESOLUCION',
                                  {'fase_activa': True})

        assert resultado.permitido is False
        rr = resultado.reglas_evaluadas[0]
        assert rr.disparada is True
        assert rr.neutralizada is False

    def test_regla_bloqueante_neutralizada_por_excepcion(self):
        """Una regla BLOQUEAR con excepción que casa → neutralizada=True, permitido=True."""
        cond = _stub_condicion('fase_activa', 'EQ', True)
        exc_cond = _stub_condicion('tiene_permiso', 'EQ', True)
        excepcion = _stub_excepcion(condiciones=[exc_cond])
        regla = _stub_regla(1, 'Distribucion/AAP/RESOLUCION', 'BLOQUEAR',
                            condiciones=[cond], excepciones=[excepcion])

        from app.services.operadores import _OPERADORES
        with patch.dict(_OPERADORES, {'EQ': lambda a, b: a == b}):
            resultado = self._run([regla], 'CREAR', 'Distribucion/AAP/RESOLUCION',
                                  {'fase_activa': True, 'tiene_permiso': True})

        assert resultado.permitido is True
        rr = resultado.reglas_evaluadas[0]
        assert rr.disparada is True
        assert rr.neutralizada is True

    def test_regla_que_no_dispara_incluida_como_no_disparada(self):
        """Una regla cuyas condiciones no se cumplen → disparada=False, incluida igualmente."""
        cond = _stub_condicion('fase_activa', 'EQ', True)
        regla = _stub_regla(1, 'Distribucion/AAP/RESOLUCION', 'BLOQUEAR',
                            condiciones=[cond])

        from app.services.operadores import _OPERADORES
        with patch.dict(_OPERADORES, {'EQ': lambda a, b: a == b}):
            resultado = self._run([regla], 'CREAR', 'Distribucion/AAP/RESOLUCION',
                                  {'fase_activa': False})

        assert resultado.permitido is True
        rr = resultado.reglas_evaluadas[0]
        assert rr.disparada is False
        assert rr.neutralizada is False

    def test_no_short_circuit_acumula_todas(self):
        """Con dos reglas bloqueantes, ambas se evalúan (sin short-circuit)."""
        cond1 = _stub_condicion('var1', 'EQ', True)
        cond2 = _stub_condicion('var2', 'EQ', True)
        regla1 = _stub_regla(1, 'Distribucion/AAP/RESOLUCION', 'BLOQUEAR', condiciones=[cond1])
        regla2 = _stub_regla(2, 'Distribucion/AAP/RESOLUCION', 'BLOQUEAR', condiciones=[cond2])

        from app.services.operadores import _OPERADORES
        with patch.dict(_OPERADORES, {'EQ': lambda a, b: a == b}):
            resultado = self._run(
                [regla1, regla2], 'CREAR', 'Distribucion/AAP/RESOLUCION',
                {'var1': True, 'var2': True}
            )

        assert resultado.permitido is False
        assert len(resultado.reglas_evaluadas) == 2

    def test_sujeto_no_casa_excluye_regla(self):
        """Regla con sujeto diferente no aparece en reglas_evaluadas."""
        regla = _stub_regla(1, 'Distribucion/AAC/RESOLUCION', 'BLOQUEAR')

        resultado = self._run([regla], 'CREAR', 'Distribucion/AAP/RESOLUCION', {})
        assert resultado.reglas_evaluadas == []
        assert resultado.permitido is True

    def test_sujeto_any_casa(self):
        """Sujeto con ANY en patrón casa con cualquier valor en esa posición."""
        regla = _stub_regla(1, 'ANY/AAP/RESOLUCION', 'BLOQUEAR', condiciones=[])
        resultado = self._run([regla], 'CREAR', 'Distribucion/AAP/RESOLUCION', {})
        # Sin condiciones la regla dispara siempre → una fila en reglas_evaluadas
        assert len(resultado.reglas_evaluadas) == 1
