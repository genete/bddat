"""Tests issue #777 — variables nuevas para condicionar requisitos documentales:
solicitud_incluye_dup, solicitante_es_persona_juridica, solicitud_por_representante.
"""


# ---------------------------------------------------------------------------
# Stubs mínimos de duck-typing
# ---------------------------------------------------------------------------

class _StubSolicitud:
    """Simula Solicitud con contiene_tipo() y entidad_id (solicitante)."""
    def __init__(self, siglas: str = '', entidad_id=None):
        self._siglas = siglas
        self.entidad_id = entidad_id

    def contiene_tipo(self, siglas: str) -> bool:
        return siglas in self._siglas.split('+')


class _StubEntidad:
    def __init__(self, nif=None):
        self.nif = nif


class _StubExpediente:
    def __init__(self, titular_id=None, titular_nif=None, sin_titular=False):
        self.titular_id = titular_id
        self.titular = None if sin_titular else _StubEntidad(nif=titular_nif)


class _StubCtx:
    def __init__(self, solicitud_actual=None, expediente=None):
        self._solicitud_actual = solicitud_actual
        self.expediente = expediente

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
# A) solicitud_incluye_dup
# ---------------------------------------------------------------------------

def test_solicitud_incluye_dup_registrada():
    _get_variable('solicitud_incluye_dup')


def test_solicitud_incluye_dup_verdadero():
    sol = _StubSolicitud('AAP+AAC+DUP')
    ctx = _StubCtx(solicitud_actual=sol)
    assert _get_variable('solicitud_incluye_dup')(ctx) is True


def test_solicitud_incluye_dup_falso():
    sol = _StubSolicitud('AAC')
    ctx = _StubCtx(solicitud_actual=sol)
    assert _get_variable('solicitud_incluye_dup')(ctx) is False


def test_solicitud_incluye_dup_sin_solicitud_en_ctx():
    ctx = _StubCtx(solicitud_actual=None)
    assert _get_variable('solicitud_incluye_dup')(ctx) is False


# ---------------------------------------------------------------------------
# B) solicitante_es_persona_juridica (sobre el TITULAR)
# ---------------------------------------------------------------------------

def test_solicitante_es_persona_juridica_registrada():
    _get_variable('solicitante_es_persona_juridica')


def test_solicitante_es_persona_juridica_letra_espanola():
    """NIF que empieza por letra de forma jurídica española (B = SL) -> True."""
    exp = _StubExpediente(titular_id=1, titular_nif='B12345678')
    ctx = _StubCtx(expediente=exp)
    assert _get_variable('solicitante_es_persona_juridica')(ctx) is True


def test_solicitante_es_persona_juridica_letra_n_extranjera():
    """NIF que empieza por N (entidad extranjera, art. 4 Orden EHA/451/2008) -> True."""
    exp = _StubExpediente(titular_id=1, titular_nif='N1234567A')
    ctx = _StubCtx(expediente=exp)
    assert _get_variable('solicitante_es_persona_juridica')(ctx) is True


def test_solicitante_es_persona_juridica_dni_numerico():
    """DNI español, empieza por dígito -> False (persona física)."""
    exp = _StubExpediente(titular_id=1, titular_nif='12345678Z')
    ctx = _StubCtx(expediente=exp)
    assert _get_variable('solicitante_es_persona_juridica')(ctx) is False


def test_solicitante_es_persona_juridica_nie_extranjero():
    """NIE (persona física extranjera), empieza por X/Y/Z -> False."""
    exp = _StubExpediente(titular_id=1, titular_nif='X1234567L')
    ctx = _StubCtx(expediente=exp)
    assert _get_variable('solicitante_es_persona_juridica')(ctx) is False


def test_solicitante_es_persona_juridica_sin_titular():
    exp = _StubExpediente(titular_id=None, sin_titular=True)
    ctx = _StubCtx(expediente=exp)
    assert _get_variable('solicitante_es_persona_juridica')(ctx) is None


def test_solicitante_es_persona_juridica_nif_vacio():
    exp = _StubExpediente(titular_id=1, titular_nif=None)
    ctx = _StubCtx(expediente=exp)
    assert _get_variable('solicitante_es_persona_juridica')(ctx) is None


def test_solicitante_es_persona_juridica_sin_expediente():
    ctx = _StubCtx(expediente=None)
    assert _get_variable('solicitante_es_persona_juridica')(ctx) is None


# ---------------------------------------------------------------------------
# C) solicitud_por_representante (titular actual, sin histórico)
# ---------------------------------------------------------------------------

def test_solicitud_por_representante_registrada():
    _get_variable('solicitud_por_representante')


def test_solicitud_por_representante_titular_juridico_actua_si_mismo():
    """Solicitante == titular actual y titular persona jurídica -> True."""
    sol = _StubSolicitud(entidad_id=10)
    exp = _StubExpediente(titular_id=10, titular_nif='B12345678')
    ctx = _StubCtx(solicitud_actual=sol, expediente=exp)
    assert _get_variable('solicitud_por_representante')(ctx) is True


def test_solicitud_por_representante_titular_fisico_actua_si_mismo():
    """Solicitante == titular actual pero titular persona física -> False
    (no necesita poder para representarse a sí misma)."""
    sol = _StubSolicitud(entidad_id=10)
    exp = _StubExpediente(titular_id=10, titular_nif='12345678Z')
    ctx = _StubCtx(solicitud_actual=sol, expediente=exp)
    assert _get_variable('solicitud_por_representante')(ctx) is False


def test_solicitud_por_representante_tercero_actua():
    """Solicitante distinto del titular (tercero autorizado) -> False.
    Es el caso de AUTORIZACION_TRAMITAR (#408), no de PODER_REPRESENTACION."""
    sol = _StubSolicitud(entidad_id=99)
    exp = _StubExpediente(titular_id=10, titular_nif='B12345678')
    ctx = _StubCtx(solicitud_actual=sol, expediente=exp)
    assert _get_variable('solicitud_por_representante')(ctx) is False


def test_solicitud_por_representante_sin_solicitud_en_ctx():
    exp = _StubExpediente(titular_id=10, titular_nif='B12345678')
    ctx = _StubCtx(solicitud_actual=None, expediente=exp)
    assert _get_variable('solicitud_por_representante')(ctx) is False


def test_solicitud_por_representante_sin_titular():
    sol = _StubSolicitud(entidad_id=10)
    exp = _StubExpediente(titular_id=None, sin_titular=True)
    ctx = _StubCtx(solicitud_actual=sol, expediente=exp)
    assert _get_variable('solicitud_por_representante')(ctx) is False
