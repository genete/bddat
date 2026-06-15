"""Smoke test — inspector de usuarios y API de listado (ADR-023 / #544)."""

import json


def test_api_usuarios_listar(usuario_supervisor):
    """GET /api/usuarios → JSON paginado con data y has_more."""
    r = usuario_supervisor.get('/api/usuarios?limit=5')
    assert r.status_code == 200
    assert r.content_type == 'application/json'
    body = json.loads(r.data)
    assert isinstance(body.get('data'), list)
    assert 'has_more' in body


def test_api_usuarios_filtro_rol(usuario_supervisor):
    """GET /api/usuarios?rol=ADMIN → 200 con total (hay filtro activo)."""
    r = usuario_supervisor.get('/api/usuarios?rol=ADMIN')
    assert r.status_code == 200
    body = json.loads(r.data)
    assert isinstance(body.get('data'), list)
    assert 'total' in body  # con filtro se devuelve el total


def test_usuario_detalle_redirige_a_index(usuario_supervisor, primer_usuario_id):
    """GET /usuarios/<id> redirige a /usuarios/?sel=<id> (ADR-023 §9)."""
    r = usuario_supervisor.get(f'/usuarios/{primer_usuario_id}')
    assert r.status_code == 302
    assert f'sel={primer_usuario_id}' in r.location


def test_usuario_fragmento_render(usuario_supervisor, primer_usuario_id):
    """GET /usuarios/<id>/fragmento → 200 con contenido del parcial de lectura."""
    r = usuario_supervisor.get(f'/usuarios/{primer_usuario_id}/fragmento')
    assert r.status_code == 200
    assert b'Identificaci' in r.data


def test_usuario_editar_fragmento_render(usuario_admin, primer_usuario_id):
    """GET /usuarios/<id>/editar-fragmento → 200 con formulario de edición."""
    r = usuario_admin.get(f'/usuarios/{primer_usuario_id}/editar-fragmento')
    assert r.status_code == 200
    assert b'name="siglas"' in r.data


def test_usuario_editar_get_redirige(usuario_admin, primer_usuario_id):
    """GET /usuarios/<id>/editar redirige al listado con sel= (ADR-023 §9)."""
    r = usuario_admin.get(f'/usuarios/{primer_usuario_id}/editar')
    assert r.status_code == 302
    assert f'sel={primer_usuario_id}' in r.location


def test_usuario_editar_xhr_error(usuario_admin, primer_usuario_id):
    """POST editar con XHR y form vacío → JSON {ok: false, errors}."""
    r = usuario_admin.post(
        f'/usuarios/{primer_usuario_id}/editar',
        data={},
        headers={'X-Requested-With': 'XMLHttpRequest'},
    )
    assert r.status_code == 200
    assert r.content_type == 'application/json'
    body = json.loads(r.data)
    assert body['ok'] is False
    assert isinstance(body['errors'], list)
    assert len(body['errors']) > 0


def test_usuario_editar_xhr_success(usuario_admin, primer_usuario_id, app):
    """POST editar con XHR reenviando los datos actuales → JSON {ok: true}.

    Reenvía los valores existentes del usuario (incluido activo=on y sus roles)
    para no provocar cambios netos ni violar reglas (último ADMIN, etc.).
    """
    with app.app_context():
        from app.models.usuarios import Usuario
        u = Usuario.query.get(primer_usuario_id)
        form_data = {
            'siglas':    u.siglas,
            'nombre':    u.nombre,
            'apellido1': u.apellido1,
            'apellido2': u.apellido2 or '',
            'email':     u.email or '',
            'activo':    'on',
            'roles':     [str(r.id) for r in u.roles],
        }

    r = usuario_admin.post(
        f'/usuarios/{primer_usuario_id}/editar',
        data=form_data,
        headers={'X-Requested-With': 'XMLHttpRequest'},
    )
    assert r.status_code == 200
    body = json.loads(r.data)
    assert body['ok'] is True
