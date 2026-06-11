"""Smoke tests — inspector de expedientes (ADR-023 / ADR-024 / #543)."""

import json
import pytest


# ── Redirects ADR-023 §9 ──────────────────────────────────────────────────────

def test_expediente_detalle_redirige_a_listado(usuario_supervisor, expediente_seed):
    """GET /expedientes/<id> redirige a /expedientes/?sel=<id> (ADR-023 §9)."""
    r = usuario_supervisor.get(f'/expedientes/{expediente_seed}')
    assert r.status_code == 302
    assert f'sel={expediente_seed}' in r.location


def test_expediente_editar_get_redirige(usuario_supervisor, expediente_seed):
    """GET /expedientes/<id>/editar redirige al listado con sel= (ADR-023 §9)."""
    r = usuario_supervisor.get(f'/expedientes/{expediente_seed}/editar')
    assert r.status_code == 302
    assert f'sel={expediente_seed}' in r.location


# ── Fragmento inspector — lectura ─────────────────────────────────────────────

def test_expediente_fragmento_supervisor(usuario_supervisor, expediente_seed):
    """GET /expedientes/<id>/fragmento → 200 para SUPERVISOR."""
    r = usuario_supervisor.get(f'/expedientes/{expediente_seed}/fragmento')
    assert r.status_code == 200
    assert b'AT-' in r.data


def test_expediente_fragmento_tramitador(usuario_tramitador, expediente_seed):
    """GET /expedientes/<id>/fragmento → 200 para TRAMITADOR."""
    r = usuario_tramitador.get(f'/expedientes/{expediente_seed}/fragmento')
    assert r.status_code == 200


def test_expediente_fragmento_admin(usuario_admin, expediente_seed):
    """GET /expedientes/<id>/fragmento → 200 para ADMIN."""
    r = usuario_admin.get(f'/expedientes/{expediente_seed}/fragmento')
    assert r.status_code == 200


def test_expediente_fragmento_contiene_secciones(usuario_supervisor, expediente_seed):
    """El fragmento incluye la sección de datos del proyecto y el botón Tramitar."""
    r = usuario_supervisor.get(f'/expedientes/{expediente_seed}/fragmento')
    assert r.status_code == 200
    assert b'Tramitar' in r.data
    assert b'Datos del proyecto' in r.data


# ── Fragmento edición ─────────────────────────────────────────────────────────

def test_expediente_editar_fragmento_render(usuario_supervisor, expediente_seed):
    """GET /expedientes/<id>/editar-fragmento → 200 con formulario."""
    r = usuario_supervisor.get(f'/expedientes/{expediente_seed}/editar-fragmento')
    assert r.status_code == 200
    assert b'titulo' in r.data


def test_expediente_editar_xhr_success(usuario_supervisor, expediente_seed, app):
    """POST editar con XHR y datos válidos → JSON {ok: true}."""
    with app.app_context():
        from app.models.expedientes import Expediente
        exp = Expediente.query.get(expediente_seed)
        form_data = {
            'titulo':      exp.proyecto.titulo if exp.proyecto else 'Test',
            'finalidad':   exp.proyecto.finalidad if exp.proyecto else 'Test',
            'emplazamiento': exp.proyecto.emplazamiento if exp.proyecto else 'Test',
        }

    r = usuario_supervisor.post(
        f'/expedientes/{expediente_seed}/editar',
        data=form_data,
        headers={'X-Requested-With': 'XMLHttpRequest'},
    )
    assert r.status_code == 200
    body = json.loads(r.data)
    assert body['ok'] is True


# ── Modal municipios ──────────────────────────────────────────────────────────

def test_expediente_gestionar_municipios_render(usuario_supervisor, expediente_seed):
    """GET /expedientes/<id>/gestionar-municipios → 200 con formulario de municipios."""
    r = usuario_supervisor.get(f'/expedientes/{expediente_seed}/gestionar-municipios')
    assert r.status_code == 200
    assert b'gm-form' in r.data


# ── Redirects proyectos/* → expedientes/* (ADR-024 §1) ───────────────────────

def test_proyectos_index_redirige(usuario_supervisor):
    """GET /proyectos/ → 302 a /expedientes/."""
    r = usuario_supervisor.get('/proyectos/')
    assert r.status_code == 302
    assert '/expedientes/' in r.location


def test_proyectos_detalle_redirige(usuario_supervisor, expediente_seed, app):
    """GET /proyectos/<proyecto_id> → 302 a /expedientes/?sel=<expediente_id>."""
    with app.app_context():
        from app.models.expedientes import Expediente
        exp = Expediente.query.get(expediente_seed)
        if exp is None or exp.proyecto_id is None:
            pytest.skip('Expediente seed sin proyecto asociado')
        proyecto_id = exp.proyecto_id

    r = usuario_supervisor.get(f'/proyectos/{proyecto_id}')
    assert r.status_code == 302
    assert f'sel={expediente_seed}' in r.location


def test_proyectos_editar_redirige(usuario_supervisor, expediente_seed, app):
    """GET /proyectos/<proyecto_id>/editar → 302 a /expedientes/?sel=<expediente_id>."""
    with app.app_context():
        from app.models.expedientes import Expediente
        exp = Expediente.query.get(expediente_seed)
        if exp is None or exp.proyecto_id is None:
            pytest.skip('Expediente seed sin proyecto asociado')
        proyecto_id = exp.proyecto_id

    r = usuario_supervisor.get(f'/proyectos/{proyecto_id}/editar')
    assert r.status_code == 302
    assert f'sel={expediente_seed}' in r.location


# ── Listado con nuevos filtros ────────────────────────────────────────────────

def test_expedientes_listado_con_filtro_ia(usuario_supervisor):
    """GET /expedientes/?ia_id=1 → 200 con estructura de listado."""
    r = usuario_supervisor.get('/expedientes/?ia_id=1', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


def test_expedientes_listado_con_filtro_tipo(usuario_supervisor):
    """GET /expedientes/?tipo_expediente_id=1 → 200."""
    r = usuario_supervisor.get('/expedientes/?tipo_expediente_id=1', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
