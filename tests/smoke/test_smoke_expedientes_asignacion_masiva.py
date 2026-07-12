"""Smoke test — asignación masiva de expedientes a técnico (#612 / N034)."""

import pytest


def test_asignacion_masiva_ok(usuario_supervisor, app, tramitador_usuario_id):
    """POST con un expediente sin asignar → 200, responsable_id actualizado."""
    from app import db
    from app.models.expedientes import Expediente

    with app.app_context():
        huerfano = Expediente.query.filter_by(responsable_id=None).first()
        if huerfano is None:
            pytest.skip('No hay expedientes sin asignar en la BD de desarrollo')
        exp_id = huerfano.id

    try:
        r = usuario_supervisor.post(
            '/expedientes/asignacion-masiva',
            json={'expediente_ids': [exp_id], 'responsable_id': tramitador_usuario_id},
        )
        assert r.status_code == 200
        body = r.get_json()
        assert body['ok'] is True
        assert body['actualizados'] == 1

        with app.app_context():
            exp = Expediente.query.get(exp_id)
            assert exp.responsable_id == tramitador_usuario_id
    finally:
        with app.app_context():
            exp = Expediente.query.get(exp_id)
            exp.responsable_id = None
            db.session.commit()


def test_asignacion_masiva_omite_ya_asignado(usuario_supervisor, expediente_seed, app, tramitador_usuario_id):
    """Un expediente que ya tiene responsable no se toca (defensa en profundidad)."""
    with app.app_context():
        from app.models.expedientes import Expediente
        exp = Expediente.query.get(expediente_seed)
        if exp.responsable_id is None:
            pytest.skip('El expediente seed no tiene responsable asignado')
        responsable_previo = exp.responsable_id

    r = usuario_supervisor.post(
        '/expedientes/asignacion-masiva',
        json={'expediente_ids': [expediente_seed], 'responsable_id': tramitador_usuario_id},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body['ok'] is True
    assert body['actualizados'] == 0
    assert expediente_seed in body['omitidos']

    with app.app_context():
        from app.models.expedientes import Expediente
        exp = Expediente.query.get(expediente_seed)
        assert exp.responsable_id == responsable_previo


def test_asignacion_masiva_sin_permiso(usuario_tramitador, expediente_seed, tramitador_usuario_id):
    """TRAMITADOR no puede asignar en lote (mismo permiso que la edición individual)."""
    r = usuario_tramitador.post(
        '/expedientes/asignacion-masiva',
        json={'expediente_ids': [expediente_seed], 'responsable_id': tramitador_usuario_id},
    )
    assert r.status_code == 403
