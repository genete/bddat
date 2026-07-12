"""
Tests #616 — Vía de escape (bypass/justificación) alcanzable desde el árbol real.

Antes de este fix, POST /api/expedientes/<id>/nodo/<tipo>/<id>/hijos ignoraba
bypass/justificacion del body y nunca los propagaba a mutaciones_arbol.py.

Bloques:
  A) crear_hijo_nodo lee bypass+justificacion del JSON y los propaga a svc.crear_*.
  B) _bloqueo_422 incluye puede_escapar (antes ausente, #616).
  C) tipos_creables._item propaga puede_escapar solo en bloqueos del motor.
"""
from unittest.mock import patch

from app.services.mutaciones_arbol import ResultadoMutacion


# ---------------------------------------------------------------------------
# A) crear_hijo_nodo — bypass/justificacion del body JSON
# ---------------------------------------------------------------------------

def test_crear_hijo_nodo_propaga_justificacion_a_svc(usuario_supervisor, expediente_seed):
    """bypass:true + justificacion en el body → se pasa a svc.crear_solicitud."""
    with patch('app.routes.api_expedientes.svc.crear_solicitud') as mock_crear:
        mock_crear.return_value = ResultadoMutacion(ok=True, ids=[1])
        r = usuario_supervisor.post(
            f'/api/expedientes/{expediente_seed}/nodo/expediente/{expediente_seed}/hijos',
            json={'tipo_id': 1, 'bypass': True, 'justificacion': 'Tramitación urgente'})

    assert r.status_code == 201
    assert mock_crear.call_args.kwargs['justificacion'] == 'Tramitación urgente'


def test_crear_hijo_nodo_sin_bypass_justificacion_none(usuario_supervisor, expediente_seed):
    """Sin bypass en el body, justificacion=None (comportamiento normal, evalúa motor)."""
    with patch('app.routes.api_expedientes.svc.crear_solicitud') as mock_crear:
        mock_crear.return_value = ResultadoMutacion(ok=True, ids=[1])
        r = usuario_supervisor.post(
            f'/api/expedientes/{expediente_seed}/nodo/expediente/{expediente_seed}/hijos',
            json={'tipo_id': 1})

    assert r.status_code == 201
    assert mock_crear.call_args.kwargs['justificacion'] is None


def test_crear_hijo_nodo_bypass_sin_justificacion_400(usuario_supervisor, expediente_seed):
    """bypass:true sin justificacion → 400, sin llegar a invocar el servicio de mutación."""
    with patch('app.routes.api_expedientes.svc.crear_solicitud') as mock_crear:
        r = usuario_supervisor.post(
            f'/api/expedientes/{expediente_seed}/nodo/expediente/{expediente_seed}/hijos',
            json={'tipo_id': 1, 'bypass': True})

    assert r.status_code == 400
    assert mock_crear.called is False


# ---------------------------------------------------------------------------
# B) _bloqueo_422 — incluye puede_escapar (#616)
# ---------------------------------------------------------------------------

def test_bloqueo_422_incluye_puede_escapar(app):
    from app.routes.api_expedientes import _bloqueo_422
    from app.services.motor_reglas import EvaluacionResult

    motor = EvaluacionResult(
        permitido=False, nivel='BLOQUEAR', variables_trigger={},
        norma_compilada='norma X', url_norma='', motivo='motivo del motor',
        puede_escapar=True,
    )
    with app.app_context():
        resp, status = _bloqueo_422(ResultadoMutacion(ok=False, bloqueo=motor))
        data = resp.get_json()

    assert status == 422
    assert data['puede_escapar'] is True


# ---------------------------------------------------------------------------
# C) tipos_creables._item — puede_escapar solo en bloqueos del motor
# ---------------------------------------------------------------------------

def test_tipos_creables_item_propaga_puede_escapar_true():
    from app.services.tipos_creables import _item
    from app.services.motor_reglas import EvaluacionResult

    res = EvaluacionResult(
        permitido=False, nivel='BLOQUEAR', variables_trigger={},
        norma_compilada='norma X', url_norma='', motivo='bloqueado por regla',
        puede_escapar=True,
    )
    item = _item(1, 'COD', 'Nombre', res)
    assert item['puede_escapar'] is True


def test_tipos_creables_item_no_incluye_puede_escapar_si_permitido():
    from app.services.tipos_creables import _item
    from app.services.motor_reglas import PERMITIDO

    item = _item(1, 'COD', 'Nombre', PERMITIDO)
    assert 'puede_escapar' not in item
