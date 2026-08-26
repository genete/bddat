"""Tests issue #460 — Variables motor cierre CONSULTAS."""
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Stubs mínimos de duck-typing
# ---------------------------------------------------------------------------

class _StubOrganismo:
    def __init__(self, resultado, id=1): self.resultado = resultado; self.id = id


class _StubExpediente:
    def __init__(self, organismos): self.organismos = organismos


class _StubCtx:
    def __init__(self, organismos):
        self.expediente = _StubExpediente(organismos)


# ---------------------------------------------------------------------------
# Registro de variables
# ---------------------------------------------------------------------------

def _get_variable(nombre: str):
    import app.services.variables.calculado  # noqa: F401
    from app.services.variables import _REGISTRY
    fn = _REGISTRY.get(nombre)
    assert fn is not None, f'Variable {nombre!r} no encontrada en _REGISTRY'
    return fn


# ---------------------------------------------------------------------------
# A) organismos_todos_terminados
# ---------------------------------------------------------------------------

def test_organismos_todos_terminados_registrada():
    _get_variable('organismos_todos_terminados')


def test_organismos_todos_terminados_sin_organismos():
    """Expediente sin organismos → True (vacío es condición cumplida)."""
    ctx = _StubCtx([])
    assert _get_variable('organismos_todos_terminados')(ctx) is True


def test_organismos_todos_terminados_todos_cerrado_favorable():
    """Dos organismos en cerrado_favorable → True."""
    ctx = _StubCtx([_StubOrganismo('cerrado_favorable'), _StubOrganismo('cerrado_favorable')])
    assert _get_variable('organismos_todos_terminados')(ctx) is True


def test_organismos_todos_terminados_estados_mixtos_terminales():
    """Tres organismos en estados terminales distintos → True."""
    ctx = _StubCtx([
        _StubOrganismo('cerrado_favorable'),
        _StubOrganismo('exonerado'),
        _StubOrganismo('audiencia_previa'),
    ])
    assert _get_variable('organismos_todos_terminados')(ctx) is True


def test_organismos_todos_terminados_alguno_en_curso():
    """Un organismo sin resultado (en curso) → False."""
    ctx = _StubCtx([_StubOrganismo('cerrado_favorable'), _StubOrganismo(None)])
    assert _get_variable('organismos_todos_terminados')(ctx) is False


def test_organismos_todos_terminados_todos_en_curso():
    """Ningún organismo con resultado → False."""
    ctx = _StubCtx([_StubOrganismo(None)])
    assert _get_variable('organismos_todos_terminados')(ctx) is False


# ---------------------------------------------------------------------------
# B) organismo_supera_iteraciones
# ---------------------------------------------------------------------------

def test_organismo_supera_iteraciones_registrada():
    _get_variable('organismo_supera_iteraciones')


def test_organismo_supera_iteraciones_sin_traslados():
    """COUNT = 0 para todos los organismos → False."""
    with patch('app.db') as mock_db:
        mock_db.session.query.return_value \
            .join.return_value \
            .join.return_value \
            .filter.return_value \
            .count.return_value = 0
        fn = _get_variable('organismo_supera_iteraciones')
        ctx = _StubCtx([_StubOrganismo(None)])
        assert fn(ctx) is False


def test_organismo_supera_iteraciones_con_traslado():
    """COUNT ≥ 1 en al menos un organismo → True."""
    with patch('app.db') as mock_db:
        mock_db.session.query.return_value \
            .join.return_value \
            .join.return_value \
            .filter.return_value \
            .count.return_value = 1
        fn = _get_variable('organismo_supera_iteraciones')
        ctx = _StubCtx([_StubOrganismo(None)])
        assert fn(ctx) is True


def test_organismo_supera_iteraciones_sin_organismos():
    """Sin organismos en el expediente → False (el bucle no itera)."""
    fn = _get_variable('organismo_supera_iteraciones')
    ctx = _StubCtx([])
    assert fn(ctx) is False
