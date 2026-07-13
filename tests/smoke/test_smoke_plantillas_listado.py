"""Smoke test — listado de plantillas (/plantillas/)."""


def test_plantillas_listado_render(usuario_supervisor):
    r = usuario_supervisor.get('/plantillas/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
