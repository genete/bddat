"""Smoke test — listado de proyectos (/proyectos/)."""


def test_proyectos_listado_render(usuario_supervisor):
    r = usuario_supervisor.get('/proyectos/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
