"""
Tests issue #780 — Regla de motor: falta de permiso de acceso y conexión
bloquea el avance de fase de una AAP renovable.

Sin BD ni app context. Valida la variable 'tiene_punto_acceso_conexion' con
mocks del mismo estilo que test_582_regla_tasa_impagada.py — misma forma,
polaridad y degradación invertidas (ver calculado_variable_snippet.py y
ANALISIS_780.md §4.2 para la justificación de cada diferencia).
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


def _run(requisitos_permiso, vinculaciones, solicitud=None):
    fn = _get_variable('tiene_punto_acceso_conexion')
    ctx = _StubCtx(solicitud if solicitud is not None else _StubSolicitud())

    mock_req_query = MagicMock()
    mock_req_query.join.return_value.filter.return_value.all.return_value = requisitos_permiso

    mock_dr_query = MagicMock()
    mock_dr_query.filter_by.return_value.all.return_value = vinculaciones

    with patch('app.models.requisitos_documentales.RequisitoDocumental') as MockReq, \
         patch('app.models.requisitos_documentales.DocumentoRequisito') as MockDR:
        MockReq.query = mock_req_query
        MockDR.query = mock_dr_query
        return fn(ctx)


def test_registrada():
    _get_variable('tiene_punto_acceso_conexion')


def test_sin_solicitud_true():
    """Sin solicitud en contexto → True (no bloquea; no hay expediente sobre el que evaluar)."""
    fn = _get_variable('tiene_punto_acceso_conexion')
    assert fn(_StubCtx(None)) is True


def test_catalogo_no_poblado_degrada_true():
    """
    Sin RequisitoDocumental activo con tipo_documento.codigo=PERMISO_ACCESO_CONEXION
    (catálogo aún no poblado) → degrada a True, no bloquea (#347). Polaridad
    inversa a tasa_impagada (#582): ahí la degradación segura es False, aquí es True.
    """
    assert _run(requisitos_permiso=[], vinculaciones=[]) is True


def test_requisito_no_cubierto_false():
    """Requisito del permiso existe pero sin DocumentoRequisito → False (bloquea)."""
    req = _requisito(20)
    assert _run(requisitos_permiso=[req], vinculaciones=[]) is False


def test_requisito_cubierto_true():
    """Requisito del permiso con DocumentoRequisito para la solicitud → True."""
    req = _requisito(20)
    dr = _doc_requisito(requisito_id=20)
    assert _run(requisitos_permiso=[req], vinculaciones=[dr]) is True


def test_dos_requisitos_uno_sin_cubrir_false():
    """Caso OR de dos filas (mismo tipo_documento, condiciones distintas): una sin cubrir → False."""
    req_a = _requisito(20)
    req_b = _requisito(21)
    dr_a = _doc_requisito(requisito_id=20)
    assert _run(requisitos_permiso=[req_a, req_b], vinculaciones=[dr_a]) is False


def test_dos_requisitos_ambos_cubiertos_true():
    req_a = _requisito(20)
    req_b = _requisito(21)
    dr_a = _doc_requisito(requisito_id=20)
    dr_b = _doc_requisito(requisito_id=21)
    assert _run(requisitos_permiso=[req_a, req_b], vinculaciones=[dr_a, dr_b]) is True
