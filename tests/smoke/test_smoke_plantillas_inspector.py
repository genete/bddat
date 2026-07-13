"""Smoke test — inspector de plantillas y API de listado (ADR-023 / #545)."""

import json

import pytest


@pytest.fixture
def primera_plantilla_id(app):
    """ID de la primera plantilla en la BD de desarrollo. Skip si no hay ninguna."""
    with app.app_context():
        from app.models.plantillas import Plantilla
        p = Plantilla.query.first()
        if p is None:
            pytest.skip('No hay plantillas en la BD de desarrollo')
        return p.id


def test_plantillas_listado(usuario_supervisor):
    """GET /plantillas/ → 200 con el shell del layout (ADR-019)."""
    r = usuario_supervisor.get('/plantillas/')
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


def test_api_plantillas_listar(usuario_supervisor):
    """GET /api/admin-plantillas → JSON paginado con data y has_more."""
    r = usuario_supervisor.get('/api/admin-plantillas?limit=5')
    assert r.status_code == 200
    assert r.content_type == 'application/json'
    body = json.loads(r.data)
    assert isinstance(body.get('data'), list)
    assert 'has_more' in body


def test_api_plantillas_filtro_estado(usuario_supervisor):
    """GET /api/admin-plantillas?estado=true → 200 con total (hay filtro activo)."""
    r = usuario_supervisor.get('/api/admin-plantillas?estado=true')
    assert r.status_code == 200
    body = json.loads(r.data)
    assert isinstance(body.get('data'), list)
    assert 'total' in body


def test_plantilla_detalle_redirige_a_listado(usuario_supervisor, primera_plantilla_id):
    """GET /plantillas/<id>/ redirige a /plantillas/?sel=<id> (ADR-023 §9)."""
    r = usuario_supervisor.get(f'/plantillas/{primera_plantilla_id}/')
    assert r.status_code == 302
    assert f'sel={primera_plantilla_id}' in r.location


def test_plantilla_fragmento_render(usuario_supervisor, primera_plantilla_id):
    """GET /plantillas/<id>/fragmento → 200 con el parcial de lectura."""
    r = usuario_supervisor.get(f'/plantillas/{primera_plantilla_id}/fragmento')
    assert r.status_code == 200
    assert b'Identificaci' in r.data


def test_plantilla_editar_fragmento_render(usuario_supervisor, primera_plantilla_id):
    """GET /plantillas/<id>/editar-fragmento → 200 con formulario de edición."""
    r = usuario_supervisor.get(f'/plantillas/{primera_plantilla_id}/editar-fragmento')
    assert r.status_code == 200
    assert b'name="codigo"' in r.data
    assert b'name="tipo_documento_id"' in r.data


def test_plantilla_tokens_fragmento_render(usuario_supervisor):
    """GET /plantillas/tokens/fragmento → 200 con el panel de tokens (global)."""
    r = usuario_supervisor.get('/plantillas/tokens/fragmento')
    assert r.status_code == 200
    assert b'Tokens disponibles' in r.data


def test_plantilla_tokens_fragmento_contextual(usuario_supervisor):
    """GET .../tokens/fragmento?contexto_clase=X → añade los tokens del CB (ADR-025 / #553).

    Con contexto_clase aparece la sección Capa 2 y sus tokens; sin él, no.
    """
    r = usuario_supervisor.get(
        '/plantillas/tokens/fragmento?contexto_clase=ContextoResolucion'
    )
    assert r.status_code == 200
    assert b'Contexto avanzado' in r.data
    assert b'sentido_acto_nombre' in r.data
    # Universal: sin contexto_clase no se ofrece ningún token de Capa 2
    r_global = usuario_supervisor.get('/plantillas/tokens/fragmento')
    assert b'sentido_acto_nombre' not in r_global.data


def test_alta_error_conserva_campos(usuario_supervisor):
    """POST alta sin fichero → re-render con error pero conservando lo tecleado (#552).

    Antes el alta repintaba con plantilla=None y borraba todos los campos.
    """
    r = usuario_supervisor.post('/plantillas/nueva/', data={
        'nombre': 'Plantilla de prueba XYZ',
        'codigo': 'PRUEBA_XYZ',
        'contexto_clase': 'ContextoResolucion',
        # sin ruta_plantilla → error de validación; no se persiste
    }, follow_redirects=True)
    assert r.status_code == 200
    assert b'Plantilla de prueba XYZ' in r.data   # nombre conservado
    assert b'PRUEBA_XYZ' in r.data                 # código conservado
    assert b'Contexto avanzado' in r.data          # la clase tecleada repuebla el panel


def test_plantilla_editar_get_redirige(usuario_supervisor, primera_plantilla_id):
    """GET /plantillas/<id>/editar redirige al listado con sel= (ADR-023 §9)."""
    r = usuario_supervisor.get(f'/plantillas/{primera_plantilla_id}/editar')
    assert r.status_code == 302
    assert f'sel={primera_plantilla_id}' in r.location


def test_plantilla_editar_xhr_error(usuario_supervisor, primera_plantilla_id):
    """POST editar con XHR y form vacío → JSON {ok: false, errors}."""
    r = usuario_supervisor.post(
        f'/plantillas/{primera_plantilla_id}/editar',
        data={},
        headers={'X-Requested-With': 'XMLHttpRequest'},
    )
    assert r.status_code == 200
    assert r.content_type == 'application/json'
    body = json.loads(r.data)
    assert body['ok'] is False
    assert isinstance(body['errors'], list)
    assert len(body['errors']) > 0


def test_plantilla_editar_xhr_success(usuario_supervisor, primera_plantilla_id, app):
    """POST editar con XHR reenviando los datos actuales → JSON {ok: true}.

    Reenvía los valores existentes (sin tocar el .docx) para no provocar cambios netos.
    """
    with app.app_context():
        from app.models.plantillas import Plantilla
        p = Plantilla.query.get(primera_plantilla_id)
        form_data = {
            'nombre':            p.nombre,
            'codigo':            p.codigo,
            'variante':          p.variante or '',
            'descripcion':       p.descripcion or '',
            'tipo_documento_id': str(p.tipo_documento_id),
            'tipo_expediente_id': str(p.tipo_expediente_id) if p.tipo_expediente_id else '',
            'tipo_solicitud_id':  str(p.tipo_solicitud_id)  if p.tipo_solicitud_id  else '',
            'tipo_fase_id':       str(p.tipo_fase_id)       if p.tipo_fase_id       else '',
            'tipo_tramite_id':    str(p.tipo_tramite_id)    if p.tipo_tramite_id    else '',
            'contexto_clase':    p.contexto_clase or '',
        }
        if p.activo:
            form_data['activo'] = 'on'

    r = usuario_supervisor.post(
        f'/plantillas/{primera_plantilla_id}/editar',
        data=form_data,
        headers={'X-Requested-With': 'XMLHttpRequest'},
    )
    assert r.status_code == 200
    body = json.loads(r.data)
    assert body['ok'] is True
