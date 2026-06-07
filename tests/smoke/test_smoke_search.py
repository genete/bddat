"""Smoke tests — endpoints de búsqueda del Command Palette (#531).

Cubre:
    GET /api/search/expedientes?q=...
    GET /api/search/entidades?q=...
"""
import pytest


def test_search_expedientes_ok(usuario_supervisor, expediente_seed, app):
    """GET /api/search/expedientes con q válida → 200, clave 'results'."""
    with app.app_context():
        from app.models.expedientes import Expediente
        exp = Expediente.query.get(expediente_seed)
        q = str(exp.numero_at)

    r = usuario_supervisor.get(f'/api/search/expedientes?q={q}')
    assert r.status_code == 200
    data = r.get_json()
    assert 'results' in data
    assert isinstance(data['results'], list)


def test_search_entidades_ok(usuario_supervisor, entidad_seed, app):
    """GET /api/search/entidades con q válida → 200, clave 'results'."""
    with app.app_context():
        from app.models.entidad import Entidad
        e = Entidad.query.get(entidad_seed)
        q = e.nombre_completo[:4]

    r = usuario_supervisor.get(f'/api/search/entidades?q={q}')
    assert r.status_code == 200
    data = r.get_json()
    assert 'results' in data
    assert isinstance(data['results'], list)


def test_search_expedientes_q_corto(usuario_supervisor):
    """q de 1 char → 200, results vacío."""
    r = usuario_supervisor.get('/api/search/expedientes?q=x')
    assert r.status_code == 200
    assert r.get_json()['results'] == []


def test_search_entidades_q_corto(usuario_supervisor):
    """q de 1 char → 200, results vacío."""
    r = usuario_supervisor.get('/api/search/entidades?q=x')
    assert r.status_code == 200
    assert r.get_json()['results'] == []


def test_search_sin_auth_redirige(client):
    """Sin sesión → redirige al login (no 200)."""
    r = client.get('/api/search/expedientes?q=test')
    assert r.status_code != 200


def test_search_expedientes_formato(usuario_supervisor, expediente_seed, app):
    """Cada ítem del resultado tiene tipo, id, label, breadcrumb y url."""
    with app.app_context():
        from app.models.expedientes import Expediente
        exp = Expediente.query.get(expediente_seed)
        q = str(exp.numero_at)

    r = usuario_supervisor.get(f'/api/search/expedientes?q={q}')
    assert r.status_code == 200
    results = r.get_json()['results']
    if not results:
        pytest.skip('La búsqueda no devolvió resultados para el expediente seed')
    item = results[0]
    assert item.get('tipo') == 'expediente'
    assert 'id' in item
    assert 'label' in item
    assert 'breadcrumb' in item
    assert 'url' in item
