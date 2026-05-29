"""Smoke test — listado de entidades (/entidades/)."""


def test_entidades_listado_render(usuario_supervisor):
    r = usuario_supervisor.get('/entidades/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
