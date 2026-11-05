"""Smoke test — pestaña Fragmentos de /plantillas/ (#1009): listado, inspector y descarga."""


def test_fragmentos_listado_inspector_y_descarga(usuario_supervisor, fragmento_commiteado):
    r = usuario_supervisor.get('/plantillas/?tab=fragmentos', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data

    r = usuario_supervisor.get('/api/admin-fragmentos')
    assert r.status_code == 200
    assert 'Test_1009_Fragmento' in [f['nombre'] for f in r.get_json()['data']]

    r = usuario_supervisor.get(f'/plantillas/fragmentos/{fragmento_commiteado}/fragmento')
    assert r.status_code == 200
    assert b'data-inspector-frame="ver"' in r.data

    r = usuario_supervisor.get(f'/plantillas/fragmentos/{fragmento_commiteado}/editar-fragmento')
    assert r.status_code == 200
    assert b'data-inspector-frame="editar"' in r.data

    r = usuario_supervisor.get(f'/plantillas/fragmentos/{fragmento_commiteado}/descargar')
    assert r.status_code == 200
    assert 'Test_1009_Fragmento.odt' in r.headers['Content-Disposition']
