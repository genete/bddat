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


class _StubCtx:
    def __init__(self, solicitud):
        self._solicitud = solicitud

    @property
    def solicitud(self):
        return self._solicitud


def _requisito(req_id):
    r = MagicMock()
    r.id = req_id
    return r


def _doc_requisito(requisito_id, solicitud_id=1):
    dr = MagicMock()
    dr.requisito_id = requisito_id
    dr.solicitud_id = solicitud_id
    return dr


def _run(requisitos_tasa, vinculaciones, solicitud=None):
    fn = _get_variable('tasa_impagada')
    ctx = _StubCtx(solicitud if solicitud is not None else _StubSolicitud())

    mock_req_query = MagicMock()
    mock_req_query.join.return_value.filter.return_value.all.return_value = requisitos_tasa

    mock_dr_query = MagicMock()
    mock_dr_query.filter_by.return_value.all.return_value = vinculaciones

    with patch('app.models.requisitos_documentales.RequisitoDocumental') as MockReq, \
         patch('app.models.requisitos_documentales.DocumentoRequisito') as MockDR:
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
