"""Tests issue #341 sesión 3 — variables derivadas art. 131.1 párr. 2 RD 1955/2000."""
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Stubs mínimos de duck-typing
# ---------------------------------------------------------------------------

class _StubSolicitud:
    """Simula Solicitud con contiene_tipo() y fases controlables."""
    def __init__(self, siglas: str, fases=None):
        self._siglas = siglas
        self.fases = fases or []

    def contiene_tipo(self, siglas: str) -> bool:
        return siglas in self._siglas.split('+')


class _StubTipoFase:
    def __init__(self, es_finalizadora=False):
        self.es_finalizadora = es_finalizadora


class _StubResultadoFase:
    def __init__(self, codigo: str):
        self.codigo = codigo


class _StubFase:
    def __init__(self, es_finalizadora=False, finalizada=False, resultado_codigo=None):
        self.tipo_fase = _StubTipoFase(es_finalizadora=es_finalizadora)
        self._finalizada = finalizada
        self.resultado_fase = _StubResultadoFase(resultado_codigo) if resultado_codigo else None

    @property
    def finalizada(self):
        return self._finalizada


class _StubCtx:
    def __init__(self, solicitud_actual=None, solicitudes=None):
        self._solicitud_actual = solicitud_actual
        exp = MagicMock()
        exp.solicitudes = solicitudes or []
        self.expediente = exp

    @property
    def solicitud(self):
        return self._solicitud_actual


# ---------------------------------------------------------------------------
# Registro de variables (importar módulo activa los @variable)
# ---------------------------------------------------------------------------

def _get_variable(nombre: str):
    import app.services.variables.calculado  # noqa: F401
    from app.services.variables import _REGISTRY
    fn = _REGISTRY.get(nombre)
    assert fn is not None, f'Variable {nombre!r} no encontrada en _REGISTRY'
    return fn


# ---------------------------------------------------------------------------
# A) tiene_solicitud_aap_favorable
# ---------------------------------------------------------------------------

def test_tiene_solicitud_aap_favorable_registrada():
    _get_variable('tiene_solicitud_aap_favorable')


def test_tiene_solicitud_aap_favorable_verdadero():
    """Expediente con AAP previa favorable → True."""
    fase_aap = _StubFase(es_finalizadora=True, finalizada=True, resultado_codigo='FAVORABLE')
    sol_aap = _StubSolicitud('AAP', fases=[fase_aap])
    sol_aac = _StubSolicitud('AAC')
    ctx = _StubCtx(solicitud_actual=sol_aac, solicitudes=[sol_aac, sol_aap])
    assert _get_variable('tiene_solicitud_aap_favorable')(ctx) is True


def test_tiene_solicitud_aap_favorable_condicionado():
    """FAVORABLE_CONDICIONADO también cuenta como favorable."""
    fase_aap = _StubFase(es_finalizadora=True, finalizada=True,
                         resultado_codigo='FAVORABLE_CONDICIONADO')
    sol_aap = _StubSolicitud('AAP', fases=[fase_aap])
    sol_aac = _StubSolicitud('AAC')
    ctx = _StubCtx(solicitud_actual=sol_aac, solicitudes=[sol_aac, sol_aap])
    assert _get_variable('tiene_solicitud_aap_favorable')(ctx) is True


def test_tiene_solicitud_aap_favorable_falso_sin_aap():
    """Expediente sin solicitud AAP → False."""
    sol_aac = _StubSolicitud('AAC')
    ctx = _StubCtx(solicitud_actual=sol_aac, solicitudes=[sol_aac])
    assert _get_variable('tiene_solicitud_aap_favorable')(ctx) is False


def test_tiene_solicitud_aap_favorable_falso_no_finalizada():
    """AAP presente pero fase finalizadora no cerrada → False."""
    fase_aap = _StubFase(es_finalizadora=True, finalizada=False)
    sol_aap = _StubSolicitud('AAP', fases=[fase_aap])
    sol_aac = _StubSolicitud('AAC')
    ctx = _StubCtx(solicitud_actual=sol_aac, solicitudes=[sol_aac, sol_aap])
    assert _get_variable('tiene_solicitud_aap_favorable')(ctx) is False


def test_tiene_solicitud_aap_favorable_falso_desfavorable():
    """AAP finalizada con resultado DESFAVORABLE → False."""
    fase_aap = _StubFase(es_finalizadora=True, finalizada=True, resultado_codigo='DESFAVORABLE')
    sol_aap = _StubSolicitud('AAP', fases=[fase_aap])
    sol_aac = _StubSolicitud('AAC')
    ctx = _StubCtx(solicitud_actual=sol_aac, solicitudes=[sol_aac, sol_aap])
    assert _get_variable('tiene_solicitud_aap_favorable')(ctx) is False


def test_tiene_solicitud_aap_favorable_excluye_solicitud_actual():
    """La propia solicitud AAP+AAC no se cuenta como 'AAP previa'."""
    sol_combinada = _StubSolicitud('AAP+AAC')
    ctx = _StubCtx(solicitud_actual=sol_combinada, solicitudes=[sol_combinada])
    assert _get_variable('tiene_solicitud_aap_favorable')(ctx) is False


def test_tiene_solicitud_aap_favorable_sin_solicitud_en_ctx():
    """Sin solicitud en contexto → False."""
    ctx = _StubCtx(solicitud_actual=None, solicitudes=[])
    assert _get_variable('tiene_solicitud_aap_favorable')(ctx) is False


# ---------------------------------------------------------------------------
# B) es_solicitud_aac_pura
# ---------------------------------------------------------------------------

def test_es_solicitud_aac_pura_registrada():
    _get_variable('es_solicitud_aac_pura')


def test_es_solicitud_aac_pura_verdadero():
    """Solicitud solo AAC → True."""
    sol = _StubSolicitud('AAC')
    ctx = _StubCtx(solicitud_actual=sol)
    assert _get_variable('es_solicitud_aac_pura')(ctx) is True


def test_es_solicitud_aac_pura_con_dup():
    """AAC+DUP → False."""
    sol = _StubSolicitud('AAC+DUP')
    ctx = _StubCtx(solicitud_actual=sol)
    assert _get_variable('es_solicitud_aac_pura')(ctx) is False


def test_es_solicitud_aac_pura_combinada_aap_aac():
    """AAP+AAC combinada → False (contiene AAP)."""
    sol = _StubSolicitud('AAP+AAC')
    ctx = _StubCtx(solicitud_actual=sol)
    assert _get_variable('es_solicitud_aac_pura')(ctx) is False


def test_es_solicitud_aac_pura_solo_aap():
    """Solo AAP (sin AAC) → False."""
    sol = _StubSolicitud('AAP')
    ctx = _StubCtx(solicitud_actual=sol)
    assert _get_variable('es_solicitud_aac_pura')(ctx) is False


def test_es_solicitud_aac_pura_sin_solicitud_en_ctx():
    """Sin solicitud en contexto → False."""
    ctx = _StubCtx(solicitud_actual=None)
    assert _get_variable('es_solicitud_aac_pura')(ctx) is False
