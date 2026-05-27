"""Tests issue #388 — variable tipo_sujeto_solicitado y propiedad tipo_sujeto."""
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

class _StubTipo:
    def __init__(self, codigo: str):
        self.codigo = codigo


class _StubCtx:
    """Contexto mínimo que expone tipo_sujeto (propiedad real de ExpedienteContext)."""

    def __init__(self, objeto=None):
        self._objeto = objeto
        self._tramite = None
        self._fase = None

    @property
    def tramite(self):
        return self._tramite

    @property
    def fase(self):
        return self._fase

    @property
    def tipo_sujeto(self):
        from app.services.assembler import ExpedienteContext
        return ExpedienteContext.tipo_sujeto.fget(self)


def _get_variable(nombre: str):
    import app.services.variables.calculado  # noqa: F401
    from app.services.variables import _REGISTRY
    fn = _REGISTRY.get(nombre)
    assert fn is not None, f'Variable {nombre!r} no encontrada en _REGISTRY'
    return fn


def _stub_condicion(nombre_var, operador, valor):
    c = MagicMock()
    c.orden = 1
    c.operador = operador
    c.valor = valor
    c.variable = MagicMock()
    c.variable.nombre = nombre_var
    return c


def _stub_regla(regla_id, sujeto, efecto, condiciones=None):
    r = MagicMock()
    r.id = regla_id
    r.sujeto = sujeto
    r.efecto = efecto
    r.prioridad = regla_id
    r.descripcion = ''
    r.condiciones = condiciones or []
    r.excepciones = []
    r.norma = None
    r.activa = True
    return r


# ---------------------------------------------------------------------------
# A) Propiedad tipo_sujeto en ExpedienteContext
# ---------------------------------------------------------------------------

class TestTipoSujetoPropiedad:

    def test_crear_tramite_dict(self):
        """Dict CREAR con tipo_tramite → devuelve el tipo_tramite."""
        tt = _StubTipo('ACUERDO_INICIO')
        ctx = _StubCtx({'fase': MagicMock(), 'tipo_tramite': tt})
        assert ctx.tipo_sujeto is tt

    def test_crear_fase_dict(self):
        """Dict CREAR con tipo_fase (sin tipo_tramite) → devuelve el tipo_fase."""
        tf = _StubTipo('INSTRUCCION')
        ctx = _StubCtx({'solicitud': MagicMock(), 'tipo_fase': tf})
        assert ctx.tipo_sujeto is tf

    def test_tramite_existente(self):
        """Tramite existente → devuelve su tipo_tramite."""
        tt = _StubTipo('NOTIFICACION')
        tramite = MagicMock()
        tramite.tipo_tramite = tt
        ctx = _StubCtx()
        ctx._tramite = tramite
        assert ctx.tipo_sujeto is tt

    def test_fase_existente(self):
        """Fase existente sin trámite → devuelve su tipo_fase."""
        tf = _StubTipo('RESOLUCION')
        fase = MagicMock()
        fase.tipo_fase = tf
        ctx = _StubCtx()
        ctx._fase = fase
        assert ctx.tipo_sujeto is tf

    def test_dict_sin_tipo(self):
        """Dict sin tipo_tramite ni tipo_fase → None."""
        ctx = _StubCtx({'solicitud': MagicMock()})
        assert ctx.tipo_sujeto is None

    def test_objeto_none(self):
        """Objeto None → None."""
        ctx = _StubCtx(None)
        assert ctx.tipo_sujeto is None

    def test_tipo_tramite_tiene_prioridad_sobre_tipo_fase(self):
        """Si dict incluye ambos (improbable pero posible), tipo_tramite gana."""
        tt = _StubTipo('PUBLICACION')
        tf = _StubTipo('RESOLUCION')
        ctx = _StubCtx({'tipo_tramite': tt, 'tipo_fase': tf})
        assert ctx.tipo_sujeto is tt


# ---------------------------------------------------------------------------
# B) Variable tipo_sujeto_solicitado
# ---------------------------------------------------------------------------

class TestVariableTipoSujetoSolicitado:

    def test_registrada(self):
        _get_variable('tipo_sujeto_solicitado')

    def test_crear_tramite_devuelve_codigo(self):
        tt = _StubTipo('ACUERDO_INICIO')
        ctx = _StubCtx({'fase': MagicMock(), 'tipo_tramite': tt})
        assert _get_variable('tipo_sujeto_solicitado')(ctx) == 'ACUERDO_INICIO'

    def test_crear_fase_devuelve_codigo(self):
        tf = _StubTipo('INSTRUCCION')
        ctx = _StubCtx({'solicitud': MagicMock(), 'tipo_fase': tf})
        assert _get_variable('tipo_sujeto_solicitado')(ctx) == 'INSTRUCCION'

    def test_tramite_existente_devuelve_codigo(self):
        tt = _StubTipo('NOTIFICACION')
        tramite = MagicMock()
        tramite.tipo_tramite = tt
        ctx = _StubCtx()
        ctx._tramite = tramite
        assert _get_variable('tipo_sujeto_solicitado')(ctx) == 'NOTIFICACION'

    def test_fase_existente_devuelve_codigo(self):
        tf = _StubTipo('RESOLUCION')
        fase = MagicMock()
        fase.tipo_fase = tf
        ctx = _StubCtx()
        ctx._fase = fase
        assert _get_variable('tipo_sujeto_solicitado')(ctx) == 'RESOLUCION'

    def test_sin_tipo_devuelve_none(self):
        ctx = _StubCtx({'solicitud': MagicMock()})
        assert _get_variable('tipo_sujeto_solicitado')(ctx) is None

    def test_objeto_none_devuelve_none(self):
        ctx = _StubCtx(None)
        assert _get_variable('tipo_sujeto_solicitado')(ctx) is None


# ---------------------------------------------------------------------------
# C) Pipeline NOT_IN — evaluar() sin BD
# ---------------------------------------------------------------------------

class TestNotInPipeline:
    """Verifica que NOT_IN sobre tipo_sujeto_solicitado bloquea en el motor."""

    def _run_evaluar(self, reglas_mock, sujeto, variables):
        from app.services.motor_reglas import evaluar
        query_mock = MagicMock()
        query_mock.options.return_value.filter_by.return_value.all.return_value = reglas_mock
        jl_mock = MagicMock()
        jl_mock.return_value.joinedload.return_value = jl_mock.return_value
        with patch('app.services.motor_reglas.joinedload', jl_mock), \
             patch('app.services.motor_reglas.ReglaMotor') as MockRegla:
            MockRegla.query = query_mock
            return evaluar('CREAR', sujeto, variables)

    def test_not_in_bloquea_tipo_fuera_de_lista_permitida(self):
        """BLOQUEAR NOT_IN ['ACUERDO_INICIO'] = 'solo se puede crear ACUERDO_INICIO'.
        Si el tipo es NOTIFICACION (no está en la lista) → la regla dispara → bloqueado."""
        cond = _stub_condicion('tipo_sujeto_solicitado', 'NOT_IN', ['ACUERDO_INICIO'])
        regla = _stub_regla(1, 'ANY/AAP/INSTRUCCION', 'BLOQUEAR', condiciones=[cond])
        variables = {'tipo_sujeto_solicitado': 'NOTIFICACION'}
        resultado = self._run_evaluar([regla], 'Distribucion/AAP/INSTRUCCION', variables)
        assert resultado.permitido is False

    def test_not_in_permite_tipo_dentro_de_lista_permitida(self):
        """BLOQUEAR NOT_IN ['ACUERDO_INICIO'] → si el tipo sí está en la lista, no dispara."""
        cond = _stub_condicion('tipo_sujeto_solicitado', 'NOT_IN', ['ACUERDO_INICIO'])
        regla = _stub_regla(1, 'ANY/AAP/INSTRUCCION', 'BLOQUEAR', condiciones=[cond])
        variables = {'tipo_sujeto_solicitado': 'ACUERDO_INICIO'}
        resultado = self._run_evaluar([regla], 'Distribucion/AAP/INSTRUCCION', variables)
        assert resultado.permitido is True

    def test_not_in_lista_multiple_permite_tipo_incluido(self):
        """NOT_IN ['X', 'Y'] → tipo 'Y' está en la lista permitida → no bloquea."""
        cond = _stub_condicion('tipo_sujeto_solicitado', 'NOT_IN',
                               ['ACUERDO_INICIO', 'CONVENIO'])
        regla = _stub_regla(1, 'ANY/AAP/INSTRUCCION', 'BLOQUEAR', condiciones=[cond])
        variables = {'tipo_sujeto_solicitado': 'CONVENIO'}
        resultado = self._run_evaluar([regla], 'Distribucion/AAP/INSTRUCCION', variables)
        assert resultado.permitido is True

    def test_sujeto_nivel_f_no_aplica_regla_nivel_ft(self):
        """Regla de 4 segmentos no casa con sujeto de 3 segmentos."""
        cond = _stub_condicion('tipo_sujeto_solicitado', 'NOT_IN', ['ACUERDO_INICIO'])
        regla = _stub_regla(1, 'ANY/AAP/INSTRUCCION/ACUERDO_INICIO', 'BLOQUEAR',
                            condiciones=[cond])
        variables = {'tipo_sujeto_solicitado': 'ACUERDO_INICIO'}
        resultado = self._run_evaluar([regla], 'Distribucion/AAP/INSTRUCCION', variables)
        assert resultado.permitido is True
