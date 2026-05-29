"""Smoke test — listado de usuarios (/usuarios/)."""


def test_usuarios_listado_render(usuario_supervisor):
    r = usuario_supervisor.get('/usuarios/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
