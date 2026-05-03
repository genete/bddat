"""Tests issue #347 — Defensividad del backend ante catálogo ausente o BD no disponible.

Bloques:
  A) validar_catalogo() — registro ausente y catálogo completo.
  B) plazos.py — _seleccionar_catalogo devuelve SIN_PLAZO ante OperationalError.
  C) Manejador global — OperationalError en ruta API → HTTP 503 JSON.
  D) seguimiento.py — estado_solicitud degrada ante BD no disponible.
"""
import logging
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError, ProgrammingError


# ---------------------------------------------------------------------------
# A) validar_catalogo()
# ---------------------------------------------------------------------------

def _mock_modelo_con_codigos(nombre_modelo, codigos):
    """Mock de modelo SQLAlchemy con query.with_entities().all() devolviendo el atributo correcto."""
    from app.checks.catalogo_requerido import _CODIGO_ATTR
    attr = _CODIGO_ATTR.get(nombre_modelo, 'codigo')
    rows = [MagicMock(**{attr: c}) for c in codigos]
    mock_modelo = MagicMock()
    mock_modelo.query.with_entities.return_value.all.return_value = rows
    setattr(mock_modelo, attr, MagicMock())
    return mock_modelo


def test_validar_catalogo_registro_ausente(caplog):
    """Si falta un código requerido, validar_catalogo lo informa sin lanzar excepción."""
    from app.checks.catalogo_requerido import REGISTROS_REQUERIDOS, validar_catalogo

    mocks = {}
    for nombre_modelo, codigos in REGISTROS_REQUERIDOS.items():
        presentes = [c for c in codigos if not (nombre_modelo == 'TipoTarea' and c == 'FIRMAR')]
        mocks[nombre_modelo] = _mock_modelo_con_codigos(nombre_modelo, presentes)

    def fake_importar(modulo, clase):
        return mocks.get(clase)

    with patch('app.checks.catalogo_requerido._importar', side_effect=fake_importar):
        with caplog.at_level(logging.ERROR, logger='app.checks.catalogo_requerido'):
            faltantes = validar_catalogo()

    assert any("TipoTarea.codigo='FIRMAR'" in f for f in faltantes)
    assert "TipoTarea.codigo='FIRMAR' → no encontrado" in faltantes


def test_validar_catalogo_bd_completa():
    """Con todos los registros presentes, validar_catalogo retorna lista vacía."""
    from app.checks.catalogo_requerido import REGISTROS_REQUERIDOS, validar_catalogo

    mocks = {}
    for nombre_modelo, codigos in REGISTROS_REQUERIDOS.items():
        mocks[nombre_modelo] = _mock_modelo_con_codigos(nombre_modelo, list(codigos))

    def fake_importar(modulo, clase):
        return mocks.get(clase)

    with patch('app.checks.catalogo_requerido._importar', side_effect=fake_importar):
        faltantes = validar_catalogo()

    assert faltantes == []


def test_validar_catalogo_bd_no_disponible_no_lanza():
    """Si la BD lanza OperationalError, validar_catalogo loguea y continúa sin excepción."""
    from app.checks.catalogo_requerido import validar_catalogo

    mock_modelo = MagicMock()
    mock_modelo.query.with_entities.return_value.all.side_effect = OperationalError(
        'connection refused', None, None
    )

    with patch('app.checks.catalogo_requerido._importar', return_value=mock_modelo):
        faltantes = validar_catalogo()  # no debe lanzar

    assert isinstance(faltantes, list)


# ---------------------------------------------------------------------------
# B) plazos.py — defensividad en _seleccionar_catalogo
# ---------------------------------------------------------------------------

def test_seleccionar_catalogo_operational_error_retorna_none(caplog):
    """OperationalError en query → devuelve None sin propagar excepción."""
    from app.services.plazos import _seleccionar_catalogo

    with patch('app.models.catalogo_plazos.CatalogoPlazo') as MockCP, \
         patch('app.models.condiciones_plazo.CondicionPlazo'), \
         patch('app.services.plazos.joinedload', return_value=MagicMock()):
        MockCP.query.options.return_value.filter_by.return_value \
              .order_by.return_value.all.side_effect = OperationalError(
                  'connection refused', None, None
              )
        with caplog.at_level(logging.WARNING, logger='app.services.plazos'):
            result = _seleccionar_catalogo('FASE', 'CONSULTAS', {})

    assert result is None
    assert any('catalogo_plazos no disponible' in m for m in caplog.messages)


def test_seleccionar_catalogo_programming_error_retorna_none():
    """ProgrammingError (tabla inexistente) → devuelve None sin propagar excepción."""
    from app.services.plazos import _seleccionar_catalogo

    with patch('app.models.catalogo_plazos.CatalogoPlazo') as MockCP, \
         patch('app.models.condiciones_plazo.CondicionPlazo'), \
         patch('app.services.plazos.joinedload', return_value=MagicMock()):
        MockCP.query.options.return_value.filter_by.return_value \
              .order_by.return_value.all.side_effect = ProgrammingError(
                  'relation does not exist', None, None
              )
        result = _seleccionar_catalogo('FASE', 'CONSULTAS', {})

    assert result is None


# ---------------------------------------------------------------------------
# C) Manejador global — OperationalError en ruta API → HTTP 503 JSON
# ---------------------------------------------------------------------------

def test_manejador_operational_error_devuelve_503_json(app):
    """OperationalError lanzada en contexto /api/ → HTTP 503 con JSON {"code": "DB_ERROR"}."""
    # Buscamos el manejador registrado para OperationalError
    handlers = app.error_handler_spec.get(None, {}).get(None, {})
    handler_fn = next(
        (fn for cls, fn in handlers.items() if cls is OperationalError),
        None,
    )
    assert handler_fn is not None, 'No hay manejador registrado para OperationalError'

    exc = OperationalError('connection refused', None, None)

    # Invocamos el manejador dentro de un request context /api/ para que
    # request.path.startswith('/api/') devuelva True
    with app.test_request_context('/api/expedientes/test'):
        with patch('app.db.session'):
            result = handler_fn(exc)

    # Flask acepta tanto Response como (Response, code)
    if isinstance(result, tuple):
        resp, code = result
        assert code == 503
    else:
        resp = result
        assert resp.status_code == 503

    data = resp.get_json()
    assert data is not None
    assert data.get('code') == 'DB_ERROR'


# ---------------------------------------------------------------------------
# D) seguimiento.py — degradación ante BD no disponible
# ---------------------------------------------------------------------------

def test_estado_solicitud_bd_no_disponible_degrada():
    """Si la query de Solicitud lanza OperationalError → PENDIENTE_TRAMITAR para pistas obligatorias."""
    from app.services.seguimiento import PISTAS_OBLIGATORIAS, estado_solicitud

    exc = OperationalError('connection refused', None, None)
    mock_solicitud = MagicMock()
    mock_solicitud.query.get.side_effect = exc

    # Parcheamos el símbolo Solicitud dentro del módulo seguimiento
    with patch('app.services.seguimiento.Solicitud', mock_solicitud):
        estados = estado_solicitud(1)

    for pista in PISTAS_OBLIGATORIAS:
        assert estados[pista].codigo == 'PENDIENTE_TRAMITAR'
