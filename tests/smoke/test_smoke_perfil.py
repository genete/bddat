"""Smoke test — perfil del usuario (/perfil/)."""


def test_perfil_render(usuario_supervisor):
    r = usuario_supervisor.get('/perfil/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
