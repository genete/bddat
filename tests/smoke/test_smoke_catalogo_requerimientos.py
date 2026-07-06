"""Smoke test — catálogo de requerimientos (/catalogo_requerimientos/, #593).

Cubre listado (acceso universal, 4 roles), alta y edición (restringidas a
SUPERVISOR/ADMIN — ADMINISTRATIVO/TRAMITADOR reciben 302 a /perfil, mismo
patrón que admin_requisitos/#503).

Estos tests corren contra la BD real de desarrollo (mismo patrón que el resto
de la suite, ver conftest._login_as) — las filas de alta/edición se marcan con
'#593 smoke' y se borran en el fixture autouse de abajo para no dejar basura
en la BD compartida.
"""
import pytest


@pytest.fixture(autouse=True)
def _limpiar_datos_prueba(app):
    yield
    with app.app_context():
        from app import db
        from app.models.catalogo_requerimientos import CatalogoRequerimiento
        CatalogoRequerimiento.query.filter(
            CatalogoRequerimiento.texto.like('%#593 smoke%')
        ).delete(synchronize_session=False)
        db.session.commit()


# ---------------------------------------------------------------------------
# Listado — acceso universal (4 roles)
# ---------------------------------------------------------------------------

def test_listado_render_supervisor(usuario_supervisor):
    r = usuario_supervisor.get('/catalogo_requerimientos/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


def test_listado_accesible_admin(usuario_admin):
    r = usuario_admin.get('/catalogo_requerimientos/', follow_redirects=True)
    assert r.status_code == 200


def test_listado_accesible_tramitador(usuario_tramitador):
    r = usuario_tramitador.get('/catalogo_requerimientos/', follow_redirects=True)
    assert r.status_code == 200


def test_listado_accesible_administrativo(usuario_administrativo):
    r = usuario_administrativo.get('/catalogo_requerimientos/', follow_redirects=True)
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Alta — solo SUPERVISOR/ADMIN
# ---------------------------------------------------------------------------

def test_supervisor_puede_crear(usuario_supervisor, app):
    r = usuario_supervisor.post('/catalogo_requerimientos/crear', data={
        'texto': 'Falta aportar el certificado de dirección de obra (#593 smoke)',
        'categoria': 'documental',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/catalogo_requerimientos/' in r.headers.get('Location', '')

    with app.app_context():
        from app.models.catalogo_requerimientos import CatalogoRequerimiento
        creado = CatalogoRequerimiento.query.filter_by(
            texto='Falta aportar el certificado de dirección de obra (#593 smoke)'
        ).first()
        assert creado is not None
        assert creado.categoria == 'documental'
        assert creado.activo is True


def test_tramitador_no_puede_crear(usuario_tramitador):
    r = usuario_tramitador.post('/catalogo_requerimientos/crear', data={
        'texto': 'Intento no autorizado (#593 smoke)',
        'categoria': 'documental',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


def test_administrativo_no_puede_crear(usuario_administrativo):
    r = usuario_administrativo.post('/catalogo_requerimientos/crear', data={
        'texto': 'Intento no autorizado (#593 smoke)',
        'categoria': 'documental',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


# ---------------------------------------------------------------------------
# Edición — solo SUPERVISOR/ADMIN
# ---------------------------------------------------------------------------

def _crear_para_editar(app):
    from app import db
    from app.models.catalogo_requerimientos import CatalogoRequerimiento
    with app.app_context():
        req = CatalogoRequerimiento(
            texto='Requerimiento base para edición (#593 smoke)',
            categoria='tecnica',
        )
        db.session.add(req)
        db.session.commit()
        return req.id


def test_supervisor_puede_editar(usuario_supervisor, app):
    req_id = _crear_para_editar(app)
    r = usuario_supervisor.post(f'/catalogo_requerimientos/{req_id}/editar', data={
        'texto': 'Requerimiento editado (#593 smoke)',
        'categoria': 'administrativa',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.catalogo_requerimientos import CatalogoRequerimiento
        editado = CatalogoRequerimiento.query.get(req_id)
        assert editado.texto == 'Requerimiento editado (#593 smoke)'
        assert editado.categoria == 'administrativa'


def test_tramitador_no_puede_editar(usuario_tramitador, app):
    req_id = _crear_para_editar(app)
    r = usuario_tramitador.post(f'/catalogo_requerimientos/{req_id}/editar', data={
        'texto': 'Intento no autorizado (#593 smoke)',
        'categoria': 'tasas',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


# ---------------------------------------------------------------------------
# Baja lógica (activar/desactivar) — solo ADMIN
# ---------------------------------------------------------------------------

def test_supervisor_no_puede_archivar(usuario_supervisor, app):
    req_id = _crear_para_editar(app)
    r = usuario_supervisor.post(f'/catalogo_requerimientos/{req_id}/activar', follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


def test_admin_puede_archivar(usuario_admin, app):
    req_id = _crear_para_editar(app)
    r = usuario_admin.post(f'/catalogo_requerimientos/{req_id}/activar', follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.catalogo_requerimientos import CatalogoRequerimiento
        editado = CatalogoRequerimiento.query.get(req_id)
        assert editado.activo is False
