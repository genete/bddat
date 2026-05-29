"""Smoke test — detalle de plantilla (/admin/plantillas/<id>/)."""


def test_plantilla_detalle_render(usuario_supervisor, plantilla_seed):
    r = usuario_supervisor.get(f'/admin/plantillas/{plantilla_seed}/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
