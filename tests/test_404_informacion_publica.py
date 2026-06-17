"""
Tests issue #404 — ContextoInformacionPublica.

Bloque único: get_contexto() con stubs, sin BD ni app context.
"""
from unittest.mock import MagicMock


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _fase(informacion_publica=None):
    f = MagicMock()
    f.informacion_publica = informacion_publica
    return f


def _tramite(fase=None):
    t = MagicMock()
    t.fase = fase
    return t


def _tarea(tramite=None):
    t = MagicMock()
    t.tramite = tramite
    return t


def _ip_bd(antecedentes=None, fundamentos=None, exposicion_publica=None):
    from app.models.informacion_publica import InformacionPublica
    ip = MagicMock(spec=InformacionPublica)
    ip.antecedentes = antecedentes
    ip.fundamentos = fundamentos
    ip.exposicion_publica = exposicion_publica
    ip.as_contexto_cb = lambda: InformacionPublica.as_contexto_cb(ip)
    return ip


def _cb(tarea):
    from app.services.context_builders.contexto_informacion_publica import ContextoInformacionPublica
    return ContextoInformacionPublica(MagicMock(), MagicMock(), tarea=tarea)


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestContextoInformacionPublica:

    def test_sin_tarea_devuelve_vacio(self):
        from app.services.context_builders.contexto_informacion_publica import ContextoInformacionPublica
        cb = ContextoInformacionPublica(MagicMock(), MagicMock(), tarea=None)
        assert cb.get_contexto() == {}

    def test_sin_fase_devuelve_vacio(self):
        tramite = MagicMock()
        tramite.fase = None
        tarea = _tarea(tramite)
        assert _cb(tarea).get_contexto() == {}

    def test_sin_registro_bd_campos_none(self):
        fase = _fase(informacion_publica=None)
        tarea = _tarea(_tramite(fase))

        ctx = _cb(tarea).get_contexto()

        assert ctx['ip_antecedentes'] is None
        assert ctx['ip_fundamentos'] is None
        assert ctx['ip_exposicion_publica'] is None

    def test_con_datos_completos(self):
        ip_bd = _ip_bd(
            antecedentes='Con fecha 15/01/2026 se presentó solicitud de autorización…',
            fundamentos='Artículo 131 del RD 1955/2000, de 1 de diciembre…',
            exposicion_publica='Se somete a información pública por plazo de treinta (30) días hábiles…',
        )
        fase = _fase(informacion_publica=ip_bd)
        tarea = _tarea(_tramite(fase))

        ctx = _cb(tarea).get_contexto()

        assert ctx['ip_antecedentes'] == 'Con fecha 15/01/2026 se presentó solicitud de autorización…'
        assert ctx['ip_fundamentos'] == 'Artículo 131 del RD 1955/2000, de 1 de diciembre…'
        assert ctx['ip_exposicion_publica'] == 'Se somete a información pública por plazo de treinta (30) días hábiles…'

    def test_con_datos_parciales(self):
        ip_bd = _ip_bd(antecedentes='Antecedentes redactados.')
        fase = _fase(informacion_publica=ip_bd)
        tarea = _tarea(_tramite(fase))

        ctx = _cb(tarea).get_contexto()

        assert ctx['ip_antecedentes'] == 'Antecedentes redactados.'
        assert ctx['ip_fundamentos'] is None
        assert ctx['ip_exposicion_publica'] is None
