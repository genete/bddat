"""Smoke tests — endpoints mutaciones árbol POST/PATCH/DELETE + GET editable (#500, S3b-0)."""
import pytest


def test_editable_expediente_campos_vacios(usuario_supervisor, expediente_seed):
    """GET /nodo/expediente/<id>/editable → 200, campos==[] (expediente no editable en v1)."""
    r = usuario_supervisor.get(
        f'/api/expedientes/{expediente_seed}/nodo/expediente/{expediente_seed}/editable')
    assert r.status_code == 200
    data = r.get_json()
    assert data['nodo'] == {'tipo': 'expediente', 'id': expediente_seed}
    assert data['campos'] == []


def test_crear_hijo_tipo_inexistente_404(usuario_supervisor, expediente_seed):
    """POST /nodo/expediente/<id>/hijos con tipo_id inexistente → 404."""
    r = usuario_supervisor.post(
        f'/api/expedientes/{expediente_seed}/nodo/expediente/{expediente_seed}/hijos',
        json={'tipo_id': 99999999})
    assert r.status_code == 404


def test_editar_solicitud_idempotente_200(usuario_supervisor, app):
    """PATCH /nodo/solicitud/<id> con observaciones=None → 200, ok==True."""
    with app.app_context():
        from app.models.solicitudes import Solicitud
        sol = Solicitud.query.first()
        if sol is None:
            pytest.skip('No hay solicitudes en la BD de desarrollo')
        exp_id = sol.expediente_id
        sol_id = sol.id

    r = usuario_supervisor.patch(
        f'/api/expedientes/{exp_id}/nodo/solicitud/{sol_id}',
        json={'observaciones': None})
    assert r.status_code == 200
    data = r.get_json()
    assert data.get('ok') is True


def test_borrar_solicitud_inexistente_404(usuario_supervisor, expediente_seed):
    """DELETE /nodo/solicitud/99999999 → 404 (solicitud no pertenece al expediente)."""
    r = usuario_supervisor.delete(
        f'/api/expedientes/{expediente_seed}/nodo/solicitud/99999999')
    assert r.status_code == 404


def test_bloqueo_422_surfacea_mensaje_invariante_y_motor(app):
    """El 422 de bloqueo debe surfacear el mensaje legible venga de donde venga (#500).

    La mensajería de bloqueos tiene DOS fuentes (ver EvaluacionResult):
      · motor de reglas   → `motivo`
      · invariantes ESFTT → `norma_compilada` (motivo queda '')
    `_bloqueo_422` surfacea `motivo or norma_compilada`. Sin el fallback, los
    bloqueos de invariante llegaban con motivo='' (regresión histórica).
    """
    from app.routes.api_expedientes import _bloqueo_422
    from app.services.motor_reglas import EvaluacionResult
    from app.services.mutaciones_arbol import ResultadoMutacion

    invariante = EvaluacionResult(
        permitido=False, nivel='BLOQUEAR', variables_trigger={},
        norma_compilada='Mensaje del invariante', url_norma='')          # motivo='' por defecto
    motor = EvaluacionResult(
        permitido=False, nivel='BLOQUEAR', variables_trigger={},
        norma_compilada='norma compilada X', url_norma='', motivo='Motivo del motor')

    with app.app_context():
        resp_inv, status_inv = _bloqueo_422(ResultadoMutacion(ok=False, bloqueo=invariante))
        resp_mot, status_mot = _bloqueo_422(ResultadoMutacion(ok=False, bloqueo=motor))
        body_inv = resp_inv.get_json()
        body_mot = resp_mot.get_json()

    assert status_inv == 422 and status_mot == 422
    # invariante: el mensaje (en norma_compilada) NO debe perderse
    assert body_inv['motivo'] == 'Mensaje del invariante'
    # motor: el `motivo` editorial tiene prioridad sobre norma_compilada
    assert body_mot['motivo'] == 'Motivo del motor'
