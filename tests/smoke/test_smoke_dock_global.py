"""Smoke test — dock global (ADR-020 / Issue #506).

Verifica que el partial .app-dock aparece en todas las vistas autenticadas
y que el endpoint /api/bitacora/reciente responde correctamente.
"""
import json


def _tiene_dock(response):
    return b'class="app-dock"' in response.data or b'id="js-dock"' in response.data


def test_dock_en_dashboard(usuario_supervisor):
    r = usuario_supervisor.get('/', follow_redirects=True)
    assert r.status_code == 200
    assert _tiene_dock(r), 'El dock no aparece en el dashboard'


def test_dock_en_listado_expedientes(usuario_supervisor):
    r = usuario_supervisor.get('/expedientes/', follow_redirects=True)
    assert r.status_code == 200
    assert _tiene_dock(r), 'El dock no aparece en el listado de expedientes'


def test_dock_en_workbench(usuario_supervisor, expediente_seed):
    r = usuario_supervisor.get(f'/expedientes/{expediente_seed}/arbol', follow_redirects=True)
    assert r.status_code == 200
    assert _tiene_dock(r), 'El dock no aparece en el workbench (árbol)'


def test_api_bitacora_reciente_ok(usuario_supervisor):
    r = usuario_supervisor.get('/api/bitacora/reciente')
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)


def test_api_bitacora_reciente_formato(usuario_supervisor):
    r = usuario_supervisor.get('/api/bitacora/reciente')
    data = r.get_json()
    if not data:
        return  # sin entradas en BD de test — no hay nada que verificar
    for item in data:
        assert 'hora'        in item
        assert 'icono'       in item
        assert 'descripcion' in item


def test_api_bitacora_sin_login(client):
    r = client.get('/api/bitacora/reciente', follow_redirects=False)
    assert r.status_code in (302, 401), 'El endpoint debe requerir login'
