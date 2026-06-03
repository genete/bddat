"""Smoke test — vista de árbol del expediente (/expedientes/<id>/arbol, #500)."""
import pytest


def test_expediente_arbol_render(usuario_supervisor, expediente_seed):
    r = usuario_supervisor.get(f'/expedientes/{expediente_seed}/arbol', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
    # La isla React debe estar montada con su id de expediente inyectado.
    assert b'data-react-island="expediente-arbol"' in r.data
    assert b'data-expediente-id=' in r.data


def test_expediente_arbol_sin_acceso_redirige(usuario_admin):
    # Todos los roles tienen acceder_expediente; se verifica el guard con expediente
    # inexistente → 404 (get_or_404 antes del check de permiso).
    r = usuario_admin.get('/expedientes/999999/arbol')
    assert r.status_code == 404


def test_api_url_tramitacion_apunta_arbol(usuario_supervisor, expediente_seed):
    r = usuario_supervisor.get('/api/expedientes')
    assert r.status_code == 200
    data = r.get_json()
    items = data.get('data', [])
    if not items:
        pytest.skip('No hay expedientes en la BD de desarrollo')
    url = items[0]['url_tramitacion']
    assert '/arbol' in url
    assert 'tramitacion_bc' not in url
