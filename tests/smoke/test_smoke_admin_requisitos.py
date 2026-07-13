"""Smoke test — listado del catálogo de requisitos documentales (/requisitos_documentales/)."""


def test_admin_requisitos_listado_render(usuario_supervisor):
    r = usuario_supervisor.get('/requisitos_documentales/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
