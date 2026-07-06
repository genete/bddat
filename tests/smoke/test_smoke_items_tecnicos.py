"""Smoke test — catálogo de ítems técnicos (/items_tecnicos/, #594).

Cubre listado (acceso universal, 4 roles), alta y edición (restringidas a
SUPERVISOR/ADMIN), y baja física (solo ADMIN) — mismo patrón que
admin_requisitos (#583).

Estos tests corren contra la BD real de desarrollo (mismo patrón que el resto
de la suite, ver conftest._login_as) — las filas de alta/edición se marcan con
'#594 smoke' y se borran en el fixture autouse de abajo para no dejar basura
en la BD compartida.
"""
import pytest


@pytest.fixture(autouse=True)
def _limpiar_datos_prueba(app):
    yield
    with app.app_context():
        from app import db
        from app.models.items_tecnicos import ItemTecnico
        ItemTecnico.query.filter(
            ItemTecnico.descripcion.like('%#594 smoke%')
        ).delete(synchronize_session=False)
        db.session.commit()


# ---------------------------------------------------------------------------
# Listado — acceso universal (4 roles)
# ---------------------------------------------------------------------------

def test_listado_render_supervisor(usuario_supervisor):
    r = usuario_supervisor.get('/items_tecnicos/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


def test_listado_accesible_admin(usuario_admin):
    r = usuario_admin.get('/items_tecnicos/', follow_redirects=True)
    assert r.status_code == 200


def test_listado_accesible_tramitador(usuario_tramitador):
    r = usuario_tramitador.get('/items_tecnicos/', follow_redirects=True)
    assert r.status_code == 200


def test_listado_accesible_administrativo(usuario_administrativo):
    r = usuario_administrativo.get('/items_tecnicos/', follow_redirects=True)
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Alta — solo SUPERVISOR/ADMIN
# ---------------------------------------------------------------------------

def test_supervisor_puede_crear(usuario_supervisor, app):
    r = usuario_supervisor.post('/items_tecnicos/crear', data={
        'descripcion': 'Anejo de cálculo de redes de tierra (#594 smoke)',
        'orden': '1',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/items_tecnicos/' in r.headers.get('Location', '')

    with app.app_context():
        from app.models.items_tecnicos import ItemTecnico
        creado = ItemTecnico.query.filter_by(
            descripcion='Anejo de cálculo de redes de tierra (#594 smoke)'
        ).first()
        assert creado is not None
        assert creado.activo is True
        assert creado.condiciones == []


def test_tramitador_no_puede_crear(usuario_tramitador):
    r = usuario_tramitador.post('/items_tecnicos/crear', data={
        'descripcion': 'Intento no autorizado (#594 smoke)',
        'orden': '1',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


# ---------------------------------------------------------------------------
# Edición (incluye condiciones anidadas) — solo SUPERVISOR/ADMIN
# ---------------------------------------------------------------------------

def _crear_para_editar(app):
    from app import db
    from app.models.items_tecnicos import ItemTecnico
    with app.app_context():
        item = ItemTecnico(
            descripcion='Ítem base para edición (#594 smoke)',
            orden=1,
        )
        db.session.add(item)
        db.session.commit()
        return item.id


def test_supervisor_puede_editar_sin_condiciones(usuario_supervisor, app):
    item_id = _crear_para_editar(app)
    r = usuario_supervisor.post(f'/items_tecnicos/{item_id}/editar', data={
        'descripcion': 'Ítem editado (#594 smoke)',
        'orden': '2',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.items_tecnicos import ItemTecnico
        editado = ItemTecnico.query.get(item_id)
        assert editado.descripcion == 'Ítem editado (#594 smoke)'
        assert editado.orden == 2


def test_supervisor_puede_anadir_condicion(usuario_supervisor, app):
    item_id = _crear_para_editar(app)

    with app.app_context():
        from app.models.motor_reglas import CatalogoVariable
        variable = CatalogoVariable.query.filter_by(nombre='aplica_rd223_2008').first()
        if variable is None:
            pytest.skip('catalogo_variables sin aplica_rd223_2008 sembrada en esta BD')
        variable_id = variable.id

    r = usuario_supervisor.post(f'/items_tecnicos/{item_id}/editar', data={
        'descripcion': 'Ítem con condición (#594 smoke)',
        'orden': '1',
        'cond_variable_id': str(variable_id),
        'cond_operador': 'EQ',
        'cond_valor': 'true',
        'cond_orden': '1',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.items_tecnicos import ItemTecnico
        editado = ItemTecnico.query.get(item_id)
        assert len(editado.condiciones) == 1
        assert editado.condiciones[0].operador == 'EQ'


def test_tramitador_no_puede_editar(usuario_tramitador, app):
    item_id = _crear_para_editar(app)
    r = usuario_tramitador.post(f'/items_tecnicos/{item_id}/editar', data={
        'descripcion': 'Intento no autorizado (#594 smoke)',
        'orden': '1',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


# ---------------------------------------------------------------------------
# Baja lógica (activar/desactivar) — SUPERVISOR y ADMIN
# ---------------------------------------------------------------------------

def test_supervisor_puede_desactivar(usuario_supervisor, app):
    item_id = _crear_para_editar(app)
    r = usuario_supervisor.post(f'/items_tecnicos/{item_id}/activar', follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.items_tecnicos import ItemTecnico
        editado = ItemTecnico.query.get(item_id)
        assert editado.activo is False


# ---------------------------------------------------------------------------
# Baja física — solo ADMIN
# ---------------------------------------------------------------------------

def test_supervisor_no_puede_eliminar(usuario_supervisor, app):
    item_id = _crear_para_editar(app)
    r = usuario_supervisor.post(f'/items_tecnicos/{item_id}/eliminar', follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


def test_admin_puede_eliminar_sin_usos(usuario_admin, app):
    item_id = _crear_para_editar(app)
    r = usuario_admin.post(f'/items_tecnicos/{item_id}/eliminar', follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.items_tecnicos import ItemTecnico
        assert ItemTecnico.query.get(item_id) is None
