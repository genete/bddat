"""Smoke test — vista de árbol del expediente (/expedientes/<id>/arbol, #500)."""


def test_expediente_arbol_render(usuario_supervisor, expediente_seed):
    r = usuario_supervisor.get(f'/expedientes/{expediente_seed}/arbol', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
    # La isla React debe estar montada con su id de expediente inyectado.
    assert b'data-react-island="expediente-arbol"' in r.data
    assert b'data-expediente-id=' in r.data
