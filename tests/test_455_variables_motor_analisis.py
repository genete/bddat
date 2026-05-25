"""Tests issue #455 — Variables motor ANALISIS_SOLICITUD."""


# ---------------------------------------------------------------------------
# Stubs mínimos de duck-typing
# ---------------------------------------------------------------------------

class _StubDiagnostico:
    def __init__(self, resultado): self.resultado = resultado


class _StubDoc:
    def __init__(self, diagnostico=None): self.diagnostico = diagnostico


class _StubTipoTarea:
    def __init__(self, codigo): self.codigo = codigo


class _StubTarea:
    def __init__(self, codigo_tipo, ejecutada=False, doc=None):
        self.tipo_tarea = _StubTipoTarea(codigo_tipo)
        self._ejecutada = ejecutada
        self._doc = doc

    @property
    def ejecutada(self): return self._ejecutada

    @property
    def documento_producido(self): return self._doc


class _StubTipoTramite:
    def __init__(self, codigo): self.codigo = codigo


class _StubTramite:
    def __init__(self, codigo_tipo, tareas=None):
        self.tipo_tramite = _StubTipoTramite(codigo_tipo)
        self.tareas = tareas or []


class _StubTipoFase:
    def __init__(self, codigo): self.codigo = codigo


class _StubFase:
    def __init__(self, tramites=None):
        self.tramites = tramites or []


class _StubSolicitud:
    def __init__(self, fases=None): self.fases = fases or []


class _StubCtx:
    def __init__(self, solicitud): self._solicitud = solicitud

    @property
    def solicitud(self): return self._solicitud


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_variable(nombre: str):
    import app.services.variables.calculado  # noqa: F401
    from app.services.variables import _REGISTRY
    fn = _REGISTRY.get(nombre)
    assert fn is not None, f'Variable {nombre!r} no encontrada en _REGISTRY'
    return fn


# ---------------------------------------------------------------------------
# A) tramite_analisis_con_deficiencias
# ---------------------------------------------------------------------------

def test_analisis_con_deficiencias_registrada():
    _get_variable('tramite_analisis_con_deficiencias')


def test_analisis_con_deficiencias_sin_solicitud():
    """ctx.solicitud = None → False."""
    fn = _get_variable('tramite_analisis_con_deficiencias')
    assert fn(_StubCtx(None)) is False


def test_analisis_con_deficiencias_sin_tramites():
    """Solicitud sin fases ni trámites → False."""
    fn = _get_variable('tramite_analisis_con_deficiencias')
    ctx = _StubCtx(_StubSolicitud([]))
    assert fn(ctx) is False


def test_analisis_con_deficiencias_favorable():
    """ANALISIS_DOCUMENTAL con diagnóstico favorable → False."""
    fn = _get_variable('tramite_analisis_con_deficiencias')
    doc = _StubDoc(_StubDiagnostico('favorable'))
    tarea = _StubTarea('ANALIZAR', ejecutada=True, doc=doc)
    tramite = _StubTramite('ANALISIS_DOCUMENTAL', [tarea])
    ctx = _StubCtx(_StubSolicitud([_StubFase([tramite])]))
    assert fn(ctx) is False


def test_analisis_con_deficiencias_desfavorable():
    """ANALISIS_DOCUMENTAL con diagnóstico desfavorable → True."""
    fn = _get_variable('tramite_analisis_con_deficiencias')
    doc = _StubDoc(_StubDiagnostico('desfavorable'))
    tarea = _StubTarea('ANALIZAR', ejecutada=True, doc=doc)
    tramite = _StubTramite('ANALISIS_DOCUMENTAL', [tarea])
    ctx = _StubCtx(_StubSolicitud([_StubFase([tramite])]))
    assert fn(ctx) is True


def test_analisis_con_deficiencias_sin_documento():
    """ANALIZAR sin documento producido aún → False (no hay diagnóstico)."""
    fn = _get_variable('tramite_analisis_con_deficiencias')
    tarea = _StubTarea('ANALIZAR', ejecutada=False, doc=None)
    tramite = _StubTramite('ANALISIS_DOCUMENTAL', [tarea])
    ctx = _StubCtx(_StubSolicitud([_StubFase([tramite])]))
    assert fn(ctx) is False


def test_analisis_con_deficiencias_doc_sin_diagnostico():
    """Documento producido pero sin fila en diagnosticos → False."""
    fn = _get_variable('tramite_analisis_con_deficiencias')
    doc = _StubDoc(diagnostico=None)
    tarea = _StubTarea('ANALIZAR', ejecutada=True, doc=doc)
    tramite = _StubTramite('ANALISIS_DOCUMENTAL', [tarea])
    ctx = _StubCtx(_StubSolicitud([_StubFase([tramite])]))
    assert fn(ctx) is False


def test_analisis_con_deficiencias_otro_tipo_tramite():
    """Trámite de otro tipo no influye en la variable."""
    fn = _get_variable('tramite_analisis_con_deficiencias')
    doc = _StubDoc(_StubDiagnostico('desfavorable'))
    tarea = _StubTarea('ANALIZAR', ejecutada=True, doc=doc)
    tramite = _StubTramite('OTRO_TRAMITE', [tarea])
    ctx = _StubCtx(_StubSolicitud([_StubFase([tramite])]))
    assert fn(ctx) is False


# ---------------------------------------------------------------------------
# B) tramite_requerimiento_sin_respuesta
# ---------------------------------------------------------------------------

def test_requerimiento_sin_respuesta_registrada():
    _get_variable('tramite_requerimiento_sin_respuesta')


def test_requerimiento_sin_respuesta_sin_solicitud():
    """ctx.solicitud = None → False."""
    fn = _get_variable('tramite_requerimiento_sin_respuesta')
    assert fn(_StubCtx(None)) is False


def test_requerimiento_sin_respuesta_sin_tramites():
    """Solicitud sin fases → False."""
    fn = _get_variable('tramite_requerimiento_sin_respuesta')
    ctx = _StubCtx(_StubSolicitud([]))
    assert fn(ctx) is False


def test_requerimiento_sin_respuesta_esperar_plazo_sin_doc():
    """ESPERAR_PLAZO sin documento producido → True (requerimiento pendiente)."""
    fn = _get_variable('tramite_requerimiento_sin_respuesta')
    tarea = _StubTarea('ESPERAR_PLAZO', ejecutada=False)
    tramite = _StubTramite('REQUERIMIENTO_SUBSANACION', [tarea])
    ctx = _StubCtx(_StubSolicitud([_StubFase([tramite])]))
    assert fn(ctx) is True


def test_requerimiento_sin_respuesta_esperar_plazo_con_doc():
    """ESPERAR_PLAZO con documento producido → False (titular respondió)."""
    fn = _get_variable('tramite_requerimiento_sin_respuesta')
    tarea = _StubTarea('ESPERAR_PLAZO', ejecutada=True)
    tramite = _StubTramite('REQUERIMIENTO_SUBSANACION', [tarea])
    ctx = _StubCtx(_StubSolicitud([_StubFase([tramite])]))
    assert fn(ctx) is False


def test_requerimiento_sin_respuesta_otro_tipo_tramite():
    """Trámite de otro tipo con ESPERAR_PLAZO sin doc no activa la variable."""
    fn = _get_variable('tramite_requerimiento_sin_respuesta')
    tarea = _StubTarea('ESPERAR_PLAZO', ejecutada=False)
    tramite = _StubTramite('OTRO_TRAMITE', [tarea])
    ctx = _StubCtx(_StubSolicitud([_StubFase([tramite])]))
    assert fn(ctx) is False


def test_requerimiento_sin_respuesta_multiples_tramites_uno_pendiente():
    """Dos REQUERIMIENTO_SUBSANACION: uno respondido, otro no → True."""
    fn = _get_variable('tramite_requerimiento_sin_respuesta')
    tarea_ok = _StubTarea('ESPERAR_PLAZO', ejecutada=True)
    tarea_pen = _StubTarea('ESPERAR_PLAZO', ejecutada=False)
    tramite_ok = _StubTramite('REQUERIMIENTO_SUBSANACION', [tarea_ok])
    tramite_pen = _StubTramite('REQUERIMIENTO_SUBSANACION', [tarea_pen])
    ctx = _StubCtx(_StubSolicitud([_StubFase([tramite_ok, tramite_pen])]))
    assert fn(ctx) is True


def test_requerimiento_sin_respuesta_todos_respondidos():
    """Dos REQUERIMIENTO_SUBSANACION ambos respondidos → False."""
    fn = _get_variable('tramite_requerimiento_sin_respuesta')
    tarea1 = _StubTarea('ESPERAR_PLAZO', ejecutada=True)
    tarea2 = _StubTarea('ESPERAR_PLAZO', ejecutada=True)
    tramite1 = _StubTramite('REQUERIMIENTO_SUBSANACION', [tarea1])
    tramite2 = _StubTramite('REQUERIMIENTO_SUBSANACION', [tarea2])
    ctx = _StubCtx(_StubSolicitud([_StubFase([tramite1, tramite2])]))
    assert fn(ctx) is False
