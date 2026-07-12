"""Smoke test — catálogo de tipos de documento (/tipos_documentos/, #621).

Cubre listado (acceso universal, 4 roles) y alta/edición (restringidas a
SUPERVISOR/ADMIN) — mismo patrón que catalogo_requerimientos (#593), sin
baja (ni lógica ni física, decisión de Carlos: el modelo no tiene `activo`).

Estos tests corren contra la BD real de desarrollo (mismo patrón que el resto
de la suite, ver conftest._login_as) — las filas de alta/edición se marcan con
código 'ZZ_SMOKE_621' y se borran en el fixture autouse de abajo para no dejar
basura en la BD compartida.
"""
import pytest


@pytest.fixture(autouse=True)
def _limpiar_datos_prueba(app):
    yield
    with app.app_context():
        from app import db
        from app.models.tipos_documentos import TipoDocumento
        TipoDocumento.query.filter(
            TipoDocumento.codigo.like('ZZ_SMOKE_621%')
        ).delete(synchronize_session=False)
        db.session.commit()


# ---------------------------------------------------------------------------
# Listado — acceso universal (4 roles)
# ---------------------------------------------------------------------------

def test_listado_render_supervisor(usuario_supervisor):
    r = usuario_supervisor.get('/tipos_documentos/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


def test_listado_accesible_admin(usuario_admin):
    r = usuario_admin.get('/tipos_documentos/', follow_redirects=True)
    assert r.status_code == 200


def test_listado_accesible_tramitador(usuario_tramitador):
    r = usuario_tramitador.get('/tipos_documentos/', follow_redirects=True)
    assert r.status_code == 200


def test_listado_accesible_administrativo(usuario_administrativo):
    r = usuario_administrativo.get('/tipos_documentos/', follow_redirects=True)
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Alta — solo SUPERVISOR/ADMIN
# ---------------------------------------------------------------------------

def test_supervisor_puede_crear(usuario_supervisor, app):
    r = usuario_supervisor.post('/tipos_documentos/crear', data={
        'codigo': 'ZZ_SMOKE_621',
        'nombre': 'Tipo de prueba (#621 smoke)',
        'origen': 'AMBOS',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/tipos_documentos/' in r.headers.get('Location', '')

    with app.app_context():
        from app.models.tipos_documentos import TipoDocumento
        creado = TipoDocumento.query.filter_by(codigo='ZZ_SMOKE_621').first()
        assert creado is not None
        assert creado.nombre == 'Tipo de prueba (#621 smoke)'
        assert creado.origen == 'AMBOS'


def test_tramitador_no_puede_crear(usuario_tramitador):
    r = usuario_tramitador.post('/tipos_documentos/crear', data={
        'codigo': 'ZZ_SMOKE_621_NO',
        'nombre': 'Intento no autorizado (#621 smoke)',
        'origen': 'AMBOS',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


# ---------------------------------------------------------------------------
# Edición — solo SUPERVISOR/ADMIN, código inmutable
# ---------------------------------------------------------------------------

def _crear_para_editar(app):
    from app import db
    from app.models.tipos_documentos import TipoDocumento
    with app.app_context():
        tipo = TipoDocumento(
            codigo='ZZ_SMOKE_621_EDIT',
            nombre='Tipo base para edición (#621 smoke)',
            origen='AMBOS',
        )
        db.session.add(tipo)
        db.session.commit()
        return tipo.id


def test_supervisor_puede_editar(usuario_supervisor, app):
    tipo_id = _crear_para_editar(app)
    r = usuario_supervisor.post(f'/tipos_documentos/{tipo_id}/editar', data={
        'nombre': 'Tipo editado (#621 smoke)',
        'descripcion': 'Descripción tras editar',
        'origen': 'INTERNO',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.tipos_documentos import TipoDocumento
        editado = TipoDocumento.query.get(tipo_id)
        assert editado.codigo == 'ZZ_SMOKE_621_EDIT'  # inmutable
        assert editado.nombre == 'Tipo editado (#621 smoke)'
        assert editado.origen == 'INTERNO'


def test_editar_ignora_codigo_enviado(usuario_supervisor, app):
    tipo_id = _crear_para_editar(app)
    usuario_supervisor.post(f'/tipos_documentos/{tipo_id}/editar', data={
        'codigo': 'INTENTO_CAMBIO_CODIGO',
        'nombre': 'Tipo editado 2 (#621 smoke)',
        'origen': 'EXTERNO',
    }, follow_redirects=False)

    with app.app_context():
        from app.models.tipos_documentos import TipoDocumento
        editado = TipoDocumento.query.get(tipo_id)
        assert editado.codigo == 'ZZ_SMOKE_621_EDIT'


def test_tramitador_no_puede_editar(usuario_tramitador, app):
    tipo_id = _crear_para_editar(app)
    r = usuario_tramitador.post(f'/tipos_documentos/{tipo_id}/editar', data={
        'nombre': 'Intento no autorizado (#621 smoke)',
        'origen': 'AMBOS',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')
