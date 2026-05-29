"""Smoke test — listado de expedientes (/expedientes/)."""


def test_expedientes_listado_render(usuario_supervisor):
    r = usuario_supervisor.get('/expedientes/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
