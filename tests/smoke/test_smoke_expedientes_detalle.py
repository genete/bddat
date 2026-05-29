"""Smoke test — detalle de expediente (/expedientes/<id>)."""


def test_expediente_detalle_render(usuario_supervisor, expediente_seed):
    r = usuario_supervisor.get(f'/expedientes/{expediente_seed}', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
