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
