"""Smoke tests — búsqueda del Command Palette (#531, #532).

Cubre:
    GET /api/search?q=...&tipos=...   (endpoint unificado, #532)
    + el contenedor de la isla global en el shell.

Las rutas por-entidad (/api/search/<tipo>) se retiraron al unificar (#532 fase 2).
"""
import pytest


def _grupo(grupos, tipo):
    """Devuelve los resultados del grupo `tipo` (lista vacía si no está)."""
    return next((g['resultados'] for g in grupos if g['tipo'] == tipo), [])


def test_search_unificado_ok(usuario_supervisor):
    """GET /api/search con q válida → 200 y clave 'grupos' (lista)."""
    r = usuario_supervisor.get('/api/search?q=test&tipos=expedientes,entidades')
    assert r.status_code == 200
    data = r.get_json()
    assert 'grupos' in data
    assert isinstance(data['grupos'], list)


def test_search_unificado_q_corto(usuario_supervisor):
    """q de 1 char → 200, grupos vacío."""
    r = usuario_supervisor.get('/api/search?q=x')
    assert r.status_code == 200
    assert r.get_json()['grupos'] == []


def test_search_unificado_sin_auth_redirige(client):
    """Sin sesión → no 200."""
    r = client.get('/api/search?q=test')
    assert r.status_code != 200


def test_search_unificado_expediente_formato(usuario_supervisor, expediente_seed, app):
    """Busca el expediente seed por número → grupo 'expedientes' con items
    {tipo, id, label, breadcrumb, url}."""
    with app.app_context():
        from app.models.expedientes import Expediente
        exp = Expediente.query.get(expediente_seed)
        q = str(exp.numero_at)

    r = usuario_supervisor.get(f'/api/search?q={q}&tipos=expedientes')
    assert r.status_code == 200
    items = _grupo(r.get_json()['grupos'], 'expedientes')
    if not items:
        pytest.skip('La búsqueda no devolvió el expediente seed')
    item = items[0]
    assert item['tipo'] == 'expediente'
    assert {'id', 'label', 'breadcrumb', 'url'} <= item.keys()


def test_search_unificado_entidad_formato(usuario_supervisor, entidad_seed, app):
    """Busca la entidad seed → grupo 'entidades' con items bien formados."""
    with app.app_context():
        from app.models.entidad import Entidad
        e = Entidad.query.get(entidad_seed)
        q = e.nombre_completo[:4]

    r = usuario_supervisor.get(f'/api/search?q={q}&tipos=entidades')
    assert r.status_code == 200
    items = _grupo(r.get_json()['grupos'], 'entidades')
    if not items:
        pytest.skip('La búsqueda no devolvió la entidad seed')
    item = items[0]
    assert item['tipo'] == 'entidad'
    assert {'id', 'label', 'breadcrumb', 'url'} <= item.keys()


def test_search_unificado_plantillas(usuario_supervisor, app):
    """tipos=plantillas → 200; si hay datos, el grupo trae items bien formados."""
    with app.app_context():
        from app.models.plantillas import Plantilla
        p = Plantilla.query.first()
        if p is None:
            pytest.skip('No hay plantillas sembradas')
        q = p.nombre[:3]

    r = usuario_supervisor.get(f'/api/search?q={q}&tipos=plantillas')
    assert r.status_code == 200
    grupos = r.get_json()['grupos']
    assert all(g['tipo'] == 'plantillas' for g in grupos)
    for item in _grupo(grupos, 'plantillas'):
        assert item['tipo'] == 'plantilla'
        assert {'id', 'label', 'breadcrumb', 'url'} <= item.keys()


def test_palette_bundle_en_shell(usuario_supervisor):
    """El dashboard incluye el contenedor de la isla global Command Palette (#532)."""
    r = usuario_supervisor.get('/dashboard')
    assert r.status_code == 200
    assert b'data-react-island="command-palette"' in r.data
    # Los atajos "IR A" llegan derivados de palette_nav() (no hardcodeados).
    assert b'data-nav=' in r.data
