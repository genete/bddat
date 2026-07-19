"""
Tests para #407 — campo `siglas_escritos` en Usuario y token
`responsable_siglas_escritos` en ContextoBaseExpediente.
"""
from unittest.mock import MagicMock

from app.services.escritos import ContextoBaseExpediente


def _make_exp(responsable=None):
    exp = MagicMock()
    exp.titular = None
    exp.proyecto = None
    exp.responsable = responsable
    exp.numero_at = None
    return exp


def _mock_responsable(siglas_escritos=None):
    r = MagicMock()
    r.nombre = 'Carlos'
    r.apellido1 = 'López'
    r.apellido2 = None
    r.siglas_escritos = siglas_escritos
    return r


class TestResponsableSiglasEscritos:
    def test_expone_siglas_escritos_del_responsable(self):
        responsable = _mock_responsable(siglas_escritos='CLG')
        exp = _make_exp(responsable=responsable)

        ctx = ContextoBaseExpediente(exp).get_contexto()

        assert ctx['responsable_siglas_escritos'] == 'CLG'

    def test_responsable_sin_siglas_escritos_devuelve_none(self):
        responsable = _mock_responsable(siglas_escritos=None)
        exp = _make_exp(responsable=responsable)

        ctx = ContextoBaseExpediente(exp).get_contexto()

        assert ctx['responsable_siglas_escritos'] is None

    def test_sin_responsable_devuelve_none(self):
        exp = _make_exp(responsable=None)

        ctx = ContextoBaseExpediente(exp).get_contexto()

        assert ctx['responsable_siglas_escritos'] is None
