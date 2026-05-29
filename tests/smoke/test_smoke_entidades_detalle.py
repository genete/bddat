"""Smoke test — detalle de entidad (/entidades/<id>)."""


def test_entidad_detalle_render(usuario_supervisor, entidad_seed):
    r = usuario_supervisor.get(f'/entidades/{entidad_seed}', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
