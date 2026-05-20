"""
Tests issue #403 — ContextoResolucion.

Bloque único: get_contexto() con stubs, sin BD ni app context.
"""
from unittest.mock import MagicMock


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _resultado_fase(codigo='FAVORABLE', nombre='Favorable'):
    r = MagicMock()
    r.codigo = codigo
    r.nombre = nombre
    return r


def _fase(resultado=None, resolucion=None):
    f = MagicMock()
    f.resultado_fase = resultado
    f.resolucion = resolucion
    return f


def _tramite(fase=None):
    t = MagicMock()
    t.fase = fase
    return t


def _tarea(tramite=None):
    t = MagicMock()
    t.tramite = tramite
    return t


def _resolucion_bd(antecedentes=None, fundamentos=None, resuelve=None, condicionado=None):
    from app.models.resolucion import Resolucion
    r = MagicMock(spec=Resolucion)
    r.antecedentes = antecedentes
    r.fundamentos = fundamentos
    r.resuelve = resuelve
    r.condicionado = condicionado
    r.as_contexto_cb = lambda: Resolucion.as_contexto_cb(r)
    return r


def _cb(tarea):
    from app.services.context_builders.contexto_resolucion import ContextoResolucion
    return ContextoResolucion(MagicMock(), MagicMock(), tarea=tarea)


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestContextoResolucion:

    def test_sin_tarea_devuelve_vacio(self):
        from app.services.context_builders.contexto_resolucion import ContextoResolucion
        cb = ContextoResolucion(MagicMock(), MagicMock(), tarea=None)
        assert cb.get_contexto() == {}

    def test_sin_resultado_fase_devuelve_vacio(self):
        fase = _fase(resultado=None)
        tarea = _tarea(_tramite(fase))
        ctx = _cb(tarea).get_contexto()
        assert ctx == {}

    def test_sin_resolucion_bd_campos_none(self):
        resultado = _resultado_fase('DESFAVORABLE', 'Desfavorable')
        fase = _fase(resultado=resultado, resolucion=None)
        tarea = _tarea(_tramite(fase))

        ctx = _cb(tarea).get_contexto()

        assert ctx['sentido_acto_codigo'] == 'DESFAVORABLE'
        assert ctx['sentido_acto_nombre'] == 'Desfavorable'
        assert ctx['resolucion_antecedentes'] is None
        assert ctx['resolucion_fundamentos'] is None
        assert ctx['resolucion_resuelve'] is None
        assert ctx['resolucion_condicionado'] is None

    def test_con_datos_completos(self):
        resultado = _resultado_fase('FAVORABLE_CONDICIONADO', 'Favorable condicionado')
        res_bd = _resolucion_bd(
            antecedentes='Con fecha 01/01/2026 se presentó solicitud…',
            fundamentos='Artículo 131 RD 1955/2000…',
            resuelve='Conceder la autorización administrativa…',
            condicionado='1. El promotor deberá…',
        )
        fase = _fase(resultado=resultado, resolucion=res_bd)
        tarea = _tarea(_tramite(fase))

        ctx = _cb(tarea).get_contexto()

        assert ctx['sentido_acto_codigo'] == 'FAVORABLE_CONDICIONADO'
        assert ctx['sentido_acto_nombre'] == 'Favorable condicionado'
        assert ctx['resolucion_antecedentes'] == 'Con fecha 01/01/2026 se presentó solicitud…'
        assert ctx['resolucion_fundamentos'] == 'Artículo 131 RD 1955/2000…'
        assert ctx['resolucion_resuelve'] == 'Conceder la autorización administrativa…'
        assert ctx['resolucion_condicionado'] == '1. El promotor deberá…'
