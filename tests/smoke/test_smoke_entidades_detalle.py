"""Smoke test — detalle y fragmento de entidad (ADR-023 / #534)."""

import json
import pytest


def test_entidad_detalle_redirige_a_index(usuario_supervisor, entidad_seed):
    """GET /entidades/<id> redirige a /entidades/?sel=<id> (ADR-023 §9)."""
    r = usuario_supervisor.get(f'/entidades/{entidad_seed}')
    assert r.status_code == 302
    assert f'sel={entidad_seed}' in r.location


def test_entidad_detalle_sigue_redireccion(usuario_supervisor, entidad_seed):
    """Seguir la redirección llega al listado (200 con shell)."""
    r = usuario_supervisor.get(f'/entidades/{entidad_seed}', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


def test_entidad_fragmento_render(usuario_supervisor, entidad_seed):
    """GET /entidades/<id>/fragmento → 200 con contenido del parcial."""
    r = usuario_supervisor.get(f'/entidades/{entidad_seed}/fragmento')
    assert r.status_code == 200
    assert b'Identificaci' in r.data


def test_entidad_editar_fragmento_render(usuario_supervisor, entidad_seed):
    """GET /entidades/<id>/editar-fragmento → 200 con formulario de edición."""
    r = usuario_supervisor.get(f'/entidades/{entidad_seed}/editar-fragmento')
    assert r.status_code == 200
    assert b'nombre_completo' in r.data


def test_entidad_editar_get_redirige(usuario_supervisor, entidad_seed):
    """GET /entidades/<id>/editar redirige al listado con sel= (ADR-023 §9)."""
    r = usuario_supervisor.get(f'/entidades/{entidad_seed}/editar')
    assert r.status_code == 302
    assert f'sel={entidad_seed}' in r.location


# ── Fase 4: modal grande (fragmentos de gestión + rutas XHR) ─────────────────

def test_entidad_gestionar_direcciones_render(usuario_supervisor, entidad_seed):
    """GET /entidades/<id>/gestionar-direcciones → 200 con fragmento de gestión."""
    r = usuario_supervisor.get(f'/entidades/{entidad_seed}/gestionar-direcciones')
    assert r.status_code == 200
    assert b'gdir-form' in r.data


def test_entidad_gestionar_autorizaciones_no_titular(usuario_supervisor, entidad_seed, app):
    """GET /entidades/<id>/gestionar-autorizaciones → 403 si la entidad no es titular."""
    with app.app_context():
        from app.models.entidad import Entidad
        e = Entidad.query.filter_by(id=entidad_seed).first()
        if e and e.rol_titular:
            pytest.skip('La entidad seed es titular; usar test de titular')
    r = usuario_supervisor.get(f'/entidades/{entidad_seed}/gestionar-autorizaciones')
    assert r.status_code == 403


def test_entidad_gestionar_autorizaciones_titular(usuario_supervisor, app):
    """GET /entidades/<id>/gestionar-autorizaciones → 200 para una entidad titular."""
    with app.app_context():
        from app.models.entidad import Entidad
        e = Entidad.query.filter_by(rol_titular=True).first()
        if e is None:
            pytest.skip('No hay entidades titulares en la BD de desarrollo')
        eid = e.id
    r = usuario_supervisor.get(f'/entidades/{eid}/gestionar-autorizaciones')
    assert r.status_code == 200
    assert b'gaut-form' in r.data


def test_entidad_nueva_direccion_xhr_error(usuario_supervisor, entidad_seed):
    """POST nueva_direccion con XHR y form vacío → JSON {ok: false, errors}."""
    r = usuario_supervisor.post(
        f'/entidades/{entidad_seed}/direcciones/nueva',
        data={},
        headers={'X-Requested-With': 'XMLHttpRequest'},
    )
    assert r.status_code == 200
    assert r.content_type == 'application/json'
    body = json.loads(r.data)
    assert body['ok'] is False
    assert isinstance(body['errors'], list)
    assert len(body['errors']) > 0


def test_entidad_editar_xhr_success(usuario_supervisor, entidad_seed, app):
    """POST editar con XHR y datos válidos → JSON {ok: true}."""
    with app.app_context():
        from app.models.entidad import Entidad
        e = Entidad.query.get(entidad_seed)
        form_data = {
            'nombre_completo': e.nombre_completo,
            'nif':             e.nif or '',
            'email':           e.email or '',
            'telefono':        e.telefono or '',
            'notas':           e.notas or '',
            'activo':          'on',
        }
        if e.rol_titular:    form_data['rol_titular']    = 'on'
        if e.rol_consultado: form_data['rol_consultado'] = 'on'
        if e.rol_publicador: form_data['rol_publicador'] = 'on'

    r = usuario_supervisor.post(
        f'/entidades/{entidad_seed}/editar',
        data=form_data,
        headers={'X-Requested-With': 'XMLHttpRequest'},
    )
    assert r.status_code == 200
    body = json.loads(r.data)
    assert body['ok'] is True
