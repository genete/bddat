"""Tests issue #396 bloque 6 — Aviso de motor en segunda ronda de CONSULTAS."""


# ---------------------------------------------------------------------------
# Stubs mínimos de duck-typing
# ---------------------------------------------------------------------------

class _StubTipoFase:
    def __init__(self, codigo): self.codigo = codigo


class _StubFase:
    def __init__(self, codigo):
        self.tipo_fase = _StubTipoFase(codigo)


class _StubSolicitud:
    def __init__(self, fases): self.fases = fases


class _StubCtxConSolicitud:
    def __init__(self, fases):
        self.solicitud = _StubSolicitud(fases)


def _get_variable(nombre):
    import app.services.variables.calculado  # noqa: F401
    from app.services.variables import _REGISTRY
    fn = _REGISTRY.get(nombre)
    assert fn is not None, f'Variable {nombre!r} no encontrada en _REGISTRY'
    return fn


# ---------------------------------------------------------------------------
# A) Variable existe_fase_consultas_previa
# ---------------------------------------------------------------------------

def test_existe_fase_consultas_previa_registrada():
    _get_variable('existe_fase_consultas_previa')


def test_existe_fase_consultas_previa_sin_solicitud_en_ctx():
    """Sin solicitud en contexto → False."""
    class _CtxSinSolicitud:
        solicitud = None

    assert _get_variable('existe_fase_consultas_previa')(_CtxSinSolicitud()) is False


def test_existe_fase_consultas_previa_solicitud_sin_fases():
    """Solicitud sin fases → False (primera fase CONSULTAS a crear, sin aviso)."""
    ctx = _StubCtxConSolicitud([])
    assert _get_variable('existe_fase_consultas_previa')(ctx) is False


def test_existe_fase_consultas_previa_otras_fases_sin_consultas():
    """Solicitud con fases de otro tipo, ninguna CONSULTAS → False."""
    ctx = _StubCtxConSolicitud([_StubFase('ANALISIS_SOLICITUD'), _StubFase('RESOLUCION')])
    assert _get_variable('existe_fase_consultas_previa')(ctx) is False


def test_existe_fase_consultas_previa_con_fase_consultas():
    """Ya existe una fase CONSULTAS → True (segunda ronda, dispara el aviso)."""
    ctx = _StubCtxConSolicitud([_StubFase('ANALISIS_SOLICITUD'), _StubFase('CONSULTAS')])
    assert _get_variable('existe_fase_consultas_previa')(ctx) is True


# ---------------------------------------------------------------------------
# B) Motor: regla ADVERTIR presente en BD
# ---------------------------------------------------------------------------

def test_regla_segunda_ronda_en_bd(app_ctx):
    """La regla ADVERTIR para ANY/ANY/CONSULTAS está activa en BD."""
    from app.models.motor_reglas import ReglaMotor
    regla = ReglaMotor.query.filter_by(
        accion='CREAR', sujeto='ANY/ANY/CONSULTAS', efecto='ADVERTIR', activa=True,
    ).first()
    assert regla is not None
    assert regla.descripcion == (
        'Nueva ronda de consultas. Compruebe que los documentos del '
        'proyecto y las separatas lo reflejan.'
    )


def test_regla_segunda_ronda_tiene_condicion(app_ctx):
    from app.models.motor_reglas import ReglaMotor
    regla = ReglaMotor.query.filter_by(
        accion='CREAR', sujeto='ANY/ANY/CONSULTAS', efecto='ADVERTIR',
    ).first()
    assert regla is not None
    nombres = [c.variable.nombre for c in regla.condiciones]
    assert nombres == ['existe_fase_consultas_previa']
