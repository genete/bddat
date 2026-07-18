"""Smoke test — catálogo de plazos legales (/catalogo_plazos/, #632).

Cubre listado (acceso universal, 4 roles), alta en los 4 niveles ESFTT
(SOLICITUD/FASE/TRAMITE/TAREA — cascada de campo_fecha), edición (incluye
condiciones anidadas con el operador BETWEEN, exclusivo de este catálogo
frente a items_tecnicos/admin_requisitos) y baja lógica (activar/desactivar),
restringidas a SUPERVISOR/ADMIN — mismo patrón que items_tecnicos (#594).

Sin tests de "eliminar": la baja física está fuera de alcance del issue.

Estos tests corren contra la BD real de desarrollo (mismo patrón que el resto
de la suite, ver conftest._login_as) — las filas de alta/edición se marcan con
'#632 smoke' en norma_origen y se borran en el fixture autouse de abajo para
no dejar basura en la BD compartida.
"""
import pytest

# Ids de CatalogoPlazo creadas por _crear_para_editar() en el test en curso —
# no basta con filtrar por texto en norma_origen: algún test edita ese mismo
# campo (p.ej. test_supervisor_puede_anadir_condicion_between no lo envía en
# el POST, y el endpoint real lo deja a NULL), lo que borraría el marcador
# que la limpieza necesita para encontrar la fila (#672).
_ids_creados_para_editar = []


@pytest.fixture(autouse=True)
def _limpiar_datos_prueba(app):
    yield
    with app.app_context():
        from app import db
        from app.models.catalogo_plazos import CatalogoPlazo
        CatalogoPlazo.query.filter(
            db.or_(
                CatalogoPlazo.norma_origen.like('%#632 smoke%'),
                CatalogoPlazo.id.in_(_ids_creados_para_editar),
            )
        ).delete(synchronize_session=False)
        db.session.commit()
    _ids_creados_para_editar.clear()


# ---------------------------------------------------------------------------
# Listado — acceso universal (4 roles)
# ---------------------------------------------------------------------------

def test_listado_render_supervisor(usuario_supervisor):
    r = usuario_supervisor.get('/catalogo_plazos/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


def test_listado_accesible_admin(usuario_admin):
    r = usuario_admin.get('/catalogo_plazos/', follow_redirects=True)
    assert r.status_code == 200


def test_listado_accesible_tramitador(usuario_tramitador):
    r = usuario_tramitador.get('/catalogo_plazos/', follow_redirects=True)
    assert r.status_code == 200


def test_listado_accesible_administrativo(usuario_administrativo):
    r = usuario_administrativo.get('/catalogo_plazos/', follow_redirects=True)
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Alta — solo SUPERVISOR/ADMIN — un caso por nivel ESFTT (cascada de campo_fecha)
# ---------------------------------------------------------------------------

def _datos_maestros_solicitud(app):
    with app.app_context():
        from app.models.tipos_solicitudes import TipoSolicitud
        from app.models.efectos_plazo import EfectoPlazo
        tipo = TipoSolicitud.query.first()
        efecto = EfectoPlazo.query.first()
        if tipo is None or efecto is None:
            pytest.skip('Faltan datos maestros (tipos_solicitudes / efectos_plazo) en esta BD')
        return tipo.siglas, efecto.id


def test_supervisor_puede_crear_nivel_solicitud(usuario_supervisor, app):
    siglas, efecto_id = _datos_maestros_solicitud(app)
    r = usuario_supervisor.post('/catalogo_plazos/crear', data={
        'tipo_elemento': 'SOLICITUD',
        'tipo_elemento_codigo': siglas,
        'plazo_valor': '3',
        'plazo_unidad': 'MESES',
        'efecto_vencimiento_id': str(efecto_id),
        'norma_origen': 'Nivel solicitud (#632 smoke)',
        'orden': '999',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/catalogo_plazos/' in r.headers.get('Location', '')

    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        creado = CatalogoPlazo.query.filter_by(norma_origen='Nivel solicitud (#632 smoke)').first()
        assert creado is not None
        assert creado.activo is True
        assert creado.campo_fecha == {'fk': 'documento_solicitud_id'}
        assert creado.condiciones == []


def test_supervisor_puede_crear_nivel_fase(usuario_supervisor, app):
    with app.app_context():
        from app.models.tipos_fases import TipoFase
        from app.models.efectos_plazo import EfectoPlazo
        tipo_fase = TipoFase.query.first()
        efecto = EfectoPlazo.query.first()
        if tipo_fase is None or efecto is None:
            pytest.skip('Faltan datos maestros (tipos_fases / efectos_plazo) en esta BD')
        codigo_fase, efecto_id = tipo_fase.codigo, efecto.id

    r = usuario_supervisor.post('/catalogo_plazos/crear', data={
        'tipo_elemento': 'FASE',
        'tipo_elemento_codigo': codigo_fase,
        'campo_fecha_fk': 'documento_resultado_id',
        'plazo_valor': '1',
        'plazo_unidad': 'MESES',
        'efecto_vencimiento_id': str(efecto_id),
        'norma_origen': 'Nivel fase (#632 smoke)',
        'orden': '999',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        creado = CatalogoPlazo.query.filter_by(norma_origen='Nivel fase (#632 smoke)').first()
        assert creado is not None
        assert creado.tipo_elemento == 'FASE'
        assert creado.campo_fecha == {'fk': 'documento_resultado_id'}


def test_supervisor_puede_crear_nivel_tramite(usuario_supervisor, app):
    with app.app_context():
        from app.models.tipos_tramites import TipoTramite
        from app.models.tipos_tareas import TipoTarea
        from app.models.efectos_plazo import EfectoPlazo
        tipo_tramite = TipoTramite.query.first()
        tipo_tarea = TipoTarea.query.first()
        efecto = EfectoPlazo.query.first()
        if tipo_tramite is None or tipo_tarea is None or efecto is None:
            pytest.skip('Faltan datos maestros (tipos_tramites/tipos_tareas/efectos_plazo) en esta BD')
        codigo_tramite, codigo_tarea, efecto_id = tipo_tramite.codigo, tipo_tarea.codigo, efecto.id

    r = usuario_supervisor.post('/catalogo_plazos/crear', data={
        'tipo_elemento': 'TRAMITE',
        'tipo_elemento_codigo': codigo_tramite,
        'campo_fecha_via_tarea_tipo': codigo_tarea,
        'campo_fecha_rol': 'PRODUCIDO',
        'plazo_valor': '15',
        'plazo_unidad': 'DIAS_NATURALES',
        'efecto_vencimiento_id': str(efecto_id),
        'norma_origen': 'Nivel tramite (#632 smoke)',
        'orden': '999',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        creado = CatalogoPlazo.query.filter_by(norma_origen='Nivel tramite (#632 smoke)').first()
        assert creado is not None
        assert creado.tipo_elemento == 'TRAMITE'
        assert creado.campo_fecha == {'via_tarea_tipo': codigo_tarea, 'rol': 'PRODUCIDO'}


def test_supervisor_puede_crear_nivel_tarea(usuario_supervisor, app):
    with app.app_context():
        from app.models.tipos_tareas import TipoTarea
        from app.models.efectos_plazo import EfectoPlazo
        tipo_tarea = TipoTarea.query.first()
        efecto = EfectoPlazo.query.first()
        if tipo_tarea is None or efecto is None:
            pytest.skip('Faltan datos maestros (tipos_tareas / efectos_plazo) en esta BD')
        codigo_tarea, efecto_id = tipo_tarea.codigo, efecto.id

    r = usuario_supervisor.post('/catalogo_plazos/crear', data={
        'tipo_elemento': 'TAREA',
        'tipo_elemento_codigo': codigo_tarea,
        'campo_fecha_rol': 'CONSUMIDO',
        'plazo_valor': '10',
        'plazo_unidad': 'DIAS_HABILES',
        'efecto_vencimiento_id': str(efecto_id),
        'norma_origen': 'Nivel tarea (#632 smoke)',
        'orden': '999',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        creado = CatalogoPlazo.query.filter_by(norma_origen='Nivel tarea (#632 smoke)').first()
        assert creado is not None
        assert creado.tipo_elemento == 'TAREA'
        assert creado.campo_fecha == {'rol': 'CONSUMIDO'}


def test_tramitador_no_puede_crear(usuario_tramitador, app):
    siglas, efecto_id = _datos_maestros_solicitud(app)
    r = usuario_tramitador.post('/catalogo_plazos/crear', data={
        'tipo_elemento': 'SOLICITUD',
        'tipo_elemento_codigo': siglas,
        'plazo_valor': '1',
        'plazo_unidad': 'MESES',
        'efecto_vencimiento_id': str(efecto_id),
        'norma_origen': 'Intento no autorizado (#632 smoke)',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


# ---------------------------------------------------------------------------
# Edición (incluye condiciones anidadas y operador BETWEEN) — solo SUPERVISOR/ADMIN
# ---------------------------------------------------------------------------

def _crear_para_editar(app):
    from app import db
    from app.models.catalogo_plazos import CatalogoPlazo
    from app.models.tipos_solicitudes import TipoSolicitud
    from app.models.efectos_plazo import EfectoPlazo
    with app.app_context():
        tipo = TipoSolicitud.query.first()
        efecto = EfectoPlazo.query.first()
        if tipo is None or efecto is None:
            pytest.skip('Faltan datos maestros (tipos_solicitudes / efectos_plazo) en esta BD')
        item = CatalogoPlazo(
            tipo_elemento='SOLICITUD',
            tipo_elemento_id=tipo.id,
            tipo_elemento_codigo=tipo.siglas,
            campo_fecha={'fk': 'documento_solicitud_id'},
            plazo_valor=3,
            plazo_unidad='MESES',
            efecto_vencimiento_id=efecto.id,
            norma_origen='Base para edición (#632 smoke)',
            orden=999,
        )
        db.session.add(item)
        db.session.commit()
        _ids_creados_para_editar.append(item.id)
        return item.id, tipo.siglas, efecto.id


def test_supervisor_puede_editar_sin_condiciones(usuario_supervisor, app):
    item_id, siglas, efecto_id = _crear_para_editar(app)
    r = usuario_supervisor.post(f'/catalogo_plazos/{item_id}/editar', data={
        'tipo_elemento': 'SOLICITUD',
        'tipo_elemento_codigo': siglas,
        'plazo_valor': '2',
        'plazo_unidad': 'DIAS_HABILES',
        'efecto_vencimiento_id': str(efecto_id),
        'norma_origen': 'Editado (#632 smoke)',
        'orden': '5',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        editado = CatalogoPlazo.query.get(item_id)
        assert editado.plazo_valor == 2
        assert editado.plazo_unidad == 'DIAS_HABILES'
        assert editado.orden == 5


def test_supervisor_puede_anadir_condicion_between(usuario_supervisor, app):
    item_id, siglas, efecto_id = _crear_para_editar(app)

    with app.app_context():
        from app.models.motor_reglas import CatalogoVariable
        variable = CatalogoVariable.query.filter_by(tipo_dato='numerico', activa=True).first()
        if variable is None:
            pytest.skip('catalogo_variables sin variable numérica activa en esta BD')
        variable_id = variable.id

    r = usuario_supervisor.post(f'/catalogo_plazos/{item_id}/editar', data={
        'tipo_elemento': 'SOLICITUD',
        'tipo_elemento_codigo': siglas,
        'plazo_valor': '3',
        'plazo_unidad': 'MESES',
        'efecto_vencimiento_id': str(efecto_id),
        'cond_variable_id': str(variable_id),
        'cond_operador': 'BETWEEN',
        'cond_valor': '10, 20',
        'cond_orden': '1',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        editado = CatalogoPlazo.query.get(item_id)
        assert len(editado.condiciones) == 1
        assert editado.condiciones[0].operador == 'BETWEEN'
        assert editado.condiciones[0].valor == [10, 20]


def test_editar_rango_con_un_solo_valor_falla(usuario_supervisor, app):
    item_id, siglas, efecto_id = _crear_para_editar(app)

    with app.app_context():
        from app.models.motor_reglas import CatalogoVariable
        variable = CatalogoVariable.query.filter_by(tipo_dato='numerico', activa=True).first()
        if variable is None:
            pytest.skip('catalogo_variables sin variable numérica activa en esta BD')
        variable_id = variable.id

    r = usuario_supervisor.post(f'/catalogo_plazos/{item_id}/editar', data={
        'tipo_elemento': 'SOLICITUD',
        'tipo_elemento_codigo': siglas,
        'plazo_valor': '3',
        'plazo_unidad': 'MESES',
        'efecto_vencimiento_id': str(efecto_id),
        'cond_variable_id': str(variable_id),
        'cond_operador': 'BETWEEN',
        'cond_valor': '10',
        'cond_orden': '1',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        sin_cambios = CatalogoPlazo.query.get(item_id)
        assert sin_cambios.condiciones == []


def test_tramitador_no_puede_editar(usuario_tramitador, app):
    item_id, siglas, efecto_id = _crear_para_editar(app)
    r = usuario_tramitador.post(f'/catalogo_plazos/{item_id}/editar', data={
        'tipo_elemento': 'SOLICITUD',
        'tipo_elemento_codigo': siglas,
        'plazo_valor': '1',
        'plazo_unidad': 'MESES',
        'efecto_vencimiento_id': str(efecto_id),
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


# ---------------------------------------------------------------------------
# Baja lógica (activar/desactivar) — SUPERVISOR y ADMIN
# ---------------------------------------------------------------------------

def test_supervisor_puede_desactivar(usuario_supervisor, app):
    item_id, _siglas, _efecto_id = _crear_para_editar(app)
    r = usuario_supervisor.post(f'/catalogo_plazos/{item_id}/activar', follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        editado = CatalogoPlazo.query.get(item_id)
        assert editado.activo is False


def test_tramitador_no_puede_desactivar(usuario_tramitador, app):
    item_id, _siglas, _efecto_id = _crear_para_editar(app)
    r = usuario_tramitador.post(f'/catalogo_plazos/{item_id}/activar', follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')
