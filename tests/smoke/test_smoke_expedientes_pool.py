"""Smoke test — pool de documentos del expediente (/expedientes/<id>/documentos)."""


def test_expediente_pool_render(usuario_supervisor, expediente_seed):
    r = usuario_supervisor.get(f'/expedientes/{expediente_seed}/documentos', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
