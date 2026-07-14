"""Smoke test — catálogo de efectos de plazo (/efectos_plazo/, #633).

Cubre listado (acceso universal, 4 roles), alta/edición (restringidas a
SUPERVISOR/ADMIN, código inmutable) y baja física (solo ADMIN, bloqueada si
el efecto está en uso por catalogo_plazos) — mismo patrón que items_tecnicos
(#594) para la protección de baja, y tipos_documentos (#621) para el resto.

Estos tests corren contra la BD real de desarrollo (mismo patrón que el resto
de la suite, ver conftest._login_as) — las filas de alta/edición se marcan con
código 'ZZ_SMOKE_633' y se borran en el fixture autouse de abajo para no dejar
basura en la BD compartida.
"""
import pytest


@pytest.fixture(autouse=True)
def _limpiar_datos_prueba(app):
    yield
    with app.app_context():
        from app import db
        from app.models.catalogo_plazos import CatalogoPlazo
        from app.models.efectos_plazo import EfectoPlazo
        CatalogoPlazo.query.filter(
            CatalogoPlazo.tipo_elemento_codigo.like('ZZ_SMOKE_633%')
        ).delete(synchronize_session=False)
        EfectoPlazo.query.filter(
            EfectoPlazo.codigo.like('ZZ_SMOKE_633%')
        ).delete(synchronize_session=False)
        db.session.commit()


# ---------------------------------------------------------------------------
# Listado — acceso universal (4 roles)
# ---------------------------------------------------------------------------

def test_listado_render_supervisor(usuario_supervisor):
    r = usuario_supervisor.get('/efectos_plazo/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


def test_listado_accesible_admin(usuario_admin):
    r = usuario_admin.get('/efectos_plazo/', follow_redirects=True)
    assert r.status_code == 200


def test_listado_accesible_tramitador(usuario_tramitador):
    r = usuario_tramitador.get('/efectos_plazo/', follow_redirects=True)
    assert r.status_code == 200


def test_listado_accesible_administrativo(usuario_administrativo):
    r = usuario_administrativo.get('/efectos_plazo/', follow_redirects=True)
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Alta — solo SUPERVISOR/ADMIN
# ---------------------------------------------------------------------------

def test_supervisor_puede_crear(usuario_supervisor, app):
    r = usuario_supervisor.post('/efectos_plazo/crear', data={
        'codigo': 'ZZ_SMOKE_633',
        'nombre': 'Efecto de prueba (#633 smoke)',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/efectos_plazo/' in r.headers.get('Location', '')

    with app.app_context():
        from app.models.efectos_plazo import EfectoPlazo
        creado = EfectoPlazo.query.filter_by(codigo='ZZ_SMOKE_633').first()
        assert creado is not None
        assert creado.nombre == 'Efecto de prueba (#633 smoke)'


def test_tramitador_no_puede_crear(usuario_tramitador):
    r = usuario_tramitador.post('/efectos_plazo/crear', data={
        'codigo': 'ZZ_SMOKE_633_NO',
        'nombre': 'Intento no autorizado (#633 smoke)',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


# ---------------------------------------------------------------------------
# Edición — solo SUPERVISOR/ADMIN, código inmutable
# ---------------------------------------------------------------------------

def _crear_para_editar(app, codigo='ZZ_SMOKE_633_EDIT'):
    from app import db
    from app.models.efectos_plazo import EfectoPlazo
    with app.app_context():
        efecto = EfectoPlazo(codigo=codigo, nombre='Efecto base para edición (#633 smoke)')
        db.session.add(efecto)
        db.session.commit()
        return efecto.id


def test_supervisor_puede_editar(usuario_supervisor, app):
    efecto_id = _crear_para_editar(app)
    r = usuario_supervisor.post(f'/efectos_plazo/{efecto_id}/editar', data={
        'nombre': 'Efecto editado (#633 smoke)',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.efectos_plazo import EfectoPlazo
        editado = EfectoPlazo.query.get(efecto_id)
        assert editado.codigo == 'ZZ_SMOKE_633_EDIT'  # inmutable
        assert editado.nombre == 'Efecto editado (#633 smoke)'


def test_editar_ignora_codigo_enviado(usuario_supervisor, app):
    efecto_id = _crear_para_editar(app, codigo='ZZ_SMOKE_633_EDIT2')
    usuario_supervisor.post(f'/efectos_plazo/{efecto_id}/editar', data={
        'codigo': 'INTENTO_CAMBIO_CODIGO',
        'nombre': 'Efecto editado 2 (#633 smoke)',
    }, follow_redirects=False)

    with app.app_context():
        from app.models.efectos_plazo import EfectoPlazo
        editado = EfectoPlazo.query.get(efecto_id)
        assert editado.codigo == 'ZZ_SMOKE_633_EDIT2'


def test_tramitador_no_puede_editar(usuario_tramitador, app):
    efecto_id = _crear_para_editar(app, codigo='ZZ_SMOKE_633_EDIT3')
    r = usuario_tramitador.post(f'/efectos_plazo/{efecto_id}/editar', data={
        'nombre': 'Intento no autorizado (#633 smoke)',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


# ---------------------------------------------------------------------------
# Baja física — solo ADMIN, bloqueada si está en uso
# ---------------------------------------------------------------------------

def test_supervisor_no_puede_eliminar(usuario_supervisor, app):
    efecto_id = _crear_para_editar(app, codigo='ZZ_SMOKE_633_DEL1')
    r = usuario_supervisor.post(f'/efectos_plazo/{efecto_id}/eliminar', follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


def test_admin_puede_eliminar_sin_uso(usuario_admin, app):
    efecto_id = _crear_para_editar(app, codigo='ZZ_SMOKE_633_DEL2')
    r = usuario_admin.post(f'/efectos_plazo/{efecto_id}/eliminar', follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.efectos_plazo import EfectoPlazo
        assert EfectoPlazo.query.get(efecto_id) is None


def test_admin_no_puede_eliminar_en_uso(usuario_admin, app):
    from app import db
    from app.models.catalogo_plazos import CatalogoPlazo
    efecto_id = _crear_para_editar(app, codigo='ZZ_SMOKE_633_DEL3')
    with app.app_context():
        plazo = CatalogoPlazo(
            tipo_elemento='TAREA',
            tipo_elemento_id=0,
            tipo_elemento_codigo='ZZ_SMOKE_633_TAREA',
            plazo_valor=10,
            plazo_unidad='DIAS_HABILES',
            efecto_vencimiento_id=efecto_id,
        )
        db.session.add(plazo)
        db.session.commit()

    r = usuario_admin.post(f'/efectos_plazo/{efecto_id}/eliminar', follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.efectos_plazo import EfectoPlazo
        assert EfectoPlazo.query.get(efecto_id) is not None
