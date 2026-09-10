"""
Tests issue #582 — Regla de motor: tasa impagada bloquea toda fase posterior
a ANÁLISIS_SOLICITUD.

Sin BD ni app context. Valida la variable 'tasa_impagada' con mocks del
mismo estilo que test_192_requisitos_documentales.py.
"""
from unittest.mock import MagicMock, patch


def _get_variable(nombre):
    import app.services.variables.calculado  # noqa: F401
    from app.services.variables import _REGISTRY
    fn = _REGISTRY.get(nombre)
    assert fn is not None, f'Variable {nombre!r} no registrada'
    return fn


class _StubSolicitud:
    def __init__(self, sol_id=1):
        self.id = sol_id


class _StubExpediente:
    def __init__(self, exp_id=1):
        self.id = exp_id


class _StubCtx:
    def __init__(self, solicitud, expediente=None):
        self._solicitud = solicitud
        self.expediente = expediente if expediente is not None else _StubExpediente()

    @property
    def solicitud(self):
        return self._solicitud


def _requisito(req_id):
    r = MagicMock()
    r.id = req_id
    return r


def _doc_requisito(requisito_id, solicitud_id=1, reformado_id=None):
    dr = MagicMock()
    dr.requisito_id = requisito_id
    dr.solicitud_id = solicitud_id
    dr.reformado_id = reformado_id
    return dr


def _run(requisitos_tasa, vinculaciones, solicitud=None, version_vigente_id=None):
    """
    `version_vigente_id`: simula ultimo_reformado() devolviendo un reformado con
    ese id (o None — sin reformado, comportamiento previo a R4/#899).
    """
    fn = _get_variable('tasa_impagada')
    ctx = _StubCtx(solicitud if solicitud is not None else _StubSolicitud())

    mock_req_query = MagicMock()
    mock_req_query.join.return_value.filter.return_value.all.return_value = requisitos_tasa

    mock_dr_query = MagicMock()
    mock_dr_query.filter_by.return_value.all.return_value = vinculaciones

    version_vigente = None
    if version_vigente_id is not None:
        version_vigente = MagicMock()
        version_vigente.id = version_vigente_id

    with patch('app.models.requisitos_documentales.RequisitoDocumental') as MockReq, \
         patch('app.models.requisitos_documentales.DocumentoRequisito') as MockDR, \
         patch('app.services.reformados.ultimo_reformado', return_value=version_vigente):
        MockReq.query = mock_req_query
        MockDR.query = mock_dr_query
        return fn(ctx)


def test_registrada():
    _get_variable('tasa_impagada')


def test_sin_solicitud_false():
    fn = _get_variable('tasa_impagada')
    assert fn(_StubCtx(None)) is False


def test_catalogo_no_poblado_degrada_false():
    """
    Sin RequisitoDocumental activo con tipo_documento.codigo=JUSTIFICANTE_PAGO_TASA
    (catálogo aún no poblado por #408) → degrada a False, no bloquea (#347).
    """
    assert _run(requisitos_tasa=[], vinculaciones=[]) is False


def test_requisito_no_cubierto_true():
    """Requisito de tasa existe pero sin DocumentoRequisito → True (bloquea)."""
    req = _requisito(10)
    assert _run(requisitos_tasa=[req], vinculaciones=[]) is True


def test_requisito_cubierto_false():
    """Requisito de tasa con DocumentoRequisito para la solicitud → False."""
    req = _requisito(10)
    dr = _doc_requisito(requisito_id=10)
    assert _run(requisitos_tasa=[req], vinculaciones=[dr]) is False


def test_dos_requisitos_uno_sin_cubrir_true():
    """OR de dos filas (mismo tipo_documento, condiciones distintas): una sin cubrir → True."""
    req_a = _requisito(10)
    req_b = _requisito(11)
    dr_a = _doc_requisito(requisito_id=10)
    assert _run(requisitos_tasa=[req_a, req_b], vinculaciones=[dr_a]) is True


def test_dos_requisitos_ambos_cubiertos_false():
    req_a = _requisito(10)
    req_b = _requisito(11)
    dr_a = _doc_requisito(requisito_id=10)
    dr_b = _doc_requisito(requisito_id=11)
    assert _run(requisitos_tasa=[req_a, req_b], vinculaciones=[dr_a, dr_b]) is False


# --- ADR-044 §E bis (R4 #899): cobertura por versión ---

def test_reformado_vinculacion_inicial_sigue_cubriendo_false():
    """Hay reformado, pero la tasa antigua (reformado_id NULL) sigue valiendo:
    no se exige complementaria si el técnico no la pidió."""
    req = _requisito(10)
    dr = _doc_requisito(requisito_id=10, reformado_id=None)
    assert _run(requisitos_tasa=[req], vinculaciones=[dr], version_vigente_id=5) is False


def test_reformado_complementaria_en_version_vigente_false():
    """Complementaria vinculada específicamente a la versión vigente → cubierto."""
    req = _requisito(10)
    dr = _doc_requisito(requisito_id=10, reformado_id=5)
    assert _run(requisitos_tasa=[req], vinculaciones=[dr], version_vigente_id=5) is False


def test_reformado_vinculacion_de_version_anterior_no_cubre_true():
    """La única vinculación es de un reformado que ya no es el vigente
    (ni NULL ni el id actual) → no cubre, sigue impagada."""
    req = _requisito(10)
    dr = _doc_requisito(requisito_id=10, reformado_id=3)
    assert _run(requisitos_tasa=[req], vinculaciones=[dr], version_vigente_id=5) is True
