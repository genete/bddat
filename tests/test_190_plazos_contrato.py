"""
Tests issue #190 — contrato interfaz plazos.py + variables motor estado_plazo/efecto_plazo.

Bloques:
  A) Stub plazos.py          — sin BD ni app context.
  B) Variables registry      — sin BD ni app context.
  C) Motor: condición EQ     — sin BD ni app context.
"""
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Stubs de contexto y objetos ORM mínimos
# ---------------------------------------------------------------------------

class _StubCtx:
    """Contexto mínimo para las funciones de variable de plazo."""
    def __init__(self, objeto=None):
        self._objeto = objeto
        self.expediente = MagicMock()


class _StubFase:
    """Duck-type de Fase: tiene solicitud y tramites, NO fases ni fase ni tramite."""
    def __init__(self):
        self.solicitud = MagicMock()
        self.tramites = []


class _StubTramite:
    """Duck-type de Tramite: tiene fase, NO tramites."""
    def __init__(self):
        self.fase = MagicMock()


class _StubTarea:
    """Duck-type de Tarea: tiene tramite."""
    def __init__(self):
        self.tramite = MagicMock()


class _StubSolicitud:
    """Duck-type de Solicitud: tiene fases, NO solicitud."""
    def __init__(self):
        self.fases = []


# ---------------------------------------------------------------------------
# A) Contrato de plazos.py — dos entradas, una por nivel con plazo (#778)
# ---------------------------------------------------------------------------

def test_elemento_sin_tipo_devuelve_sin_plazo():
    """Un objeto que no lleva su tipo ESFTT no llega a tocar BD."""
    from app.services.plazos import (
        EstadoPlazo, EstadoPlazoSolicitud,
        obtener_estado_plazo_solicitud, obtener_estado_plazo_tarea,
    )
    r = obtener_estado_plazo_solicitud(object())
    assert isinstance(r, EstadoPlazoSolicitud)
    assert (r.estado, r.efecto, r.fecha_limite, r.dias_restantes) == \
           ('SIN_PLAZO', 'NINGUNO', None, None)
    assert r.suspendido is False

    r = obtener_estado_plazo_tarea(object())
    assert isinstance(r, EstadoPlazo)
    assert (r.estado, r.efecto, r.fecha_limite, r.dias_restantes) == \
           ('SIN_PLAZO', 'NINGUNO', None, None)


def test_acepta_none_y_dict_como_elemento():
    """Los consumidores llaman con lo que tienen en contexto, y para CREAR eso es
    un dict, no una instancia ORM."""
    from app.services.plazos import (
        obtener_estado_plazo_solicitud, obtener_estado_plazo_tarea,
    )
    for fn in (obtener_estado_plazo_solicitud, obtener_estado_plazo_tarea):
        for elemento in (None, {'tipo_fase': MagicMock()}):
            r = fn(elemento)
            assert r.estado == 'SIN_PLAZO'
            assert r.efecto == 'NINGUNO'


def test_las_cuatro_fechas_acompanan_al_estado():
    """Son el dato; el estado es la lectura cómoda de ese dato (ADR-041 §C)."""
    from app.services.plazos import EstadoPlazo
    campos = EstadoPlazo.__dataclass_fields__
    for campo in ('fecha_disparo', 'fecha_limite', 'fecha_cumplimiento', 'fecha_parada'):
        assert campo in campos


# ---------------------------------------------------------------------------
# B) Variables registry
# ---------------------------------------------------------------------------

def test_variables_registradas_en_registry():
    import app.services.variables.plazo  # noqa: F401 — registra los @variable
    from app.services.variables import _REGISTRY
    assert 'estado_plazo' in _REGISTRY
    assert 'efecto_plazo' in _REGISTRY


def test_estado_plazo_objeto_none():
    import app.services.variables.plazo  # noqa: F401
    from app.services.variables import _REGISTRY
    fn = _REGISTRY['estado_plazo']
    assert fn(_StubCtx(objeto=None)) == 'SIN_PLAZO'


def test_efecto_plazo_objeto_none():
    import app.services.variables.plazo  # noqa: F401
    from app.services.variables import _REGISTRY
    fn = _REGISTRY['efecto_plazo']
    assert fn(_StubCtx(objeto=None)) == 'NINGUNO'


def test_estado_plazo_objeto_dict_crear():
    """Para CREAR (objeto=dict) el stub devuelve SIN_PLAZO."""
    import app.services.variables.plazo  # noqa: F401
    from app.services.variables import _REGISTRY
    fn = _REGISTRY['estado_plazo']
    assert fn(_StubCtx(objeto={'tipo_fase': MagicMock()})) == 'SIN_PLAZO'


def test_estado_plazo_con_fase():
    import app.services.variables.plazo  # noqa: F401
    from app.services.variables import _REGISTRY
    fn = _REGISTRY['estado_plazo']
    assert fn(_StubCtx(objeto=_StubFase())) == 'SIN_PLAZO'


def test_efecto_plazo_con_fase():
    import app.services.variables.plazo  # noqa: F401
    from app.services.variables import _REGISTRY
    fn = _REGISTRY['efecto_plazo']
    assert fn(_StubCtx(objeto=_StubFase())) == 'NINGUNO'


def test_estado_plazo_con_tramite():
    import app.services.variables.plazo  # noqa: F401
    from app.services.variables import _REGISTRY
    fn = _REGISTRY['estado_plazo']
    assert fn(_StubCtx(objeto=_StubTramite())) == 'SIN_PLAZO'


def test_estado_plazo_con_solicitud():
    import app.services.variables.plazo  # noqa: F401
    from app.services.variables import _REGISTRY
    fn = _REGISTRY['estado_plazo']
    assert fn(_StubCtx(objeto=_StubSolicitud())) == 'SIN_PLAZO'


def test_estado_plazo_con_tarea():
    import app.services.variables.plazo  # noqa: F401
    from app.services.variables import _REGISTRY
    fn = _REGISTRY['estado_plazo']
    assert fn(_StubCtx(objeto=_StubTarea())) == 'SIN_PLAZO'


# ---------------------------------------------------------------------------
# C) Motor agnóstico — condición EQ con variables de plazo
# ---------------------------------------------------------------------------

def test_motor_no_dispara_sin_plazo_contra_vencido():
    """
    Regla hipotética: estado_plazo == 'VENCIDO' → BLOQUEAR.
    Con estado='SIN_PLAZO' la condición no se cumple → no dispara.
    """
    from app.services.motor_reglas import _evaluar_condiciones
    cond = MagicMock()
    cond.variable = MagicMock(nombre='estado_plazo')
    cond.operador = 'EQ'
    cond.valor = 'VENCIDO'
    cond.orden = 1
    disparada, _ = _evaluar_condiciones([cond], {'estado_plazo': 'SIN_PLAZO'})
    assert not disparada


def test_motor_dispara_vencido_cuando_vencido():
    """La condición SÍ dispara si el estado es VENCIDO (validación del operador EQ)."""
    from app.services.motor_reglas import _evaluar_condiciones
    cond = MagicMock()
    cond.variable = MagicMock(nombre='estado_plazo')
    cond.operador = 'EQ'
    cond.valor = 'VENCIDO'
    cond.orden = 1
    disparada, _ = _evaluar_condiciones([cond], {'estado_plazo': 'VENCIDO'})
    assert disparada


def test_motor_dispara_in_proximo_o_vencido():
    """Operador IN: alerta si estado en ['PROXIMO_VENCER', 'VENCIDO']."""
    from app.services.motor_reglas import _evaluar_condiciones
    cond = MagicMock()
    cond.variable = MagicMock(nombre='estado_plazo')
    cond.operador = 'IN'
    cond.valor = ['PROXIMO_VENCER', 'VENCIDO']
    cond.orden = 1
    for estado in ('PROXIMO_VENCER', 'VENCIDO'):
        disparada, _ = _evaluar_condiciones([cond], {'estado_plazo': estado})
        assert disparada, f'Esperaba disparo para {estado}'
    for estado in ('SIN_PLAZO', 'EN_PLAZO'):
        disparada, _ = _evaluar_condiciones([cond], {'estado_plazo': estado})
        assert not disparada, f'No esperaba disparo para {estado}'
