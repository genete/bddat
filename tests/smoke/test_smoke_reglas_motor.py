"""Smoke test — CRUD de reglas del motor (/configuracion-motor/, #170, N016).

Cubre listado embebido (acceso universal, 4 roles), alta con la cascada de
`sujeto` (nivel + selects reales, nunca texto libre), edición (condiciones
anidadas), baja lógica (activar/desactivar) y el CRUD anidado de excepciones
(con sus propias condiciones) — restringidos a SUPERVISOR/ADMIN, mismo
permiso `gestionar_reglas_motor` que ya usaba el selector de modo global.

Estos tests corren contra la BD real de desarrollo (mismo patrón que el resto
de la suite, ver conftest._login_as) — las filas de alta/edición se marcan con
'#170 smoke' en descripcion y se borran en el fixture autouse de abajo.
"""
import pytest

# Ids de ReglaMotor creadas por _crear_para_editar() en el test en curso — no
# basta con filtrar por texto en descripcion: algún test edita ese mismo campo
# (p.ej. test_supervisor_puede_anadir_condicion no lo envía en el POST, y el
# endpoint real lo deja a NULL), lo que borraría el marcador que la limpieza
# necesita para encontrar la fila (#672).
_ids_creados_para_editar = []


@pytest.fixture(autouse=True)
def _limpiar_datos_prueba(app):
    yield
    with app.app_context():
        from app import db
        from app.models.motor_reglas import ReglaMotor
        ReglaMotor.query.filter(
            db.or_(
                ReglaMotor.descripcion.like('%#170 smoke%'),
                ReglaMotor.id.in_(_ids_creados_para_editar),
            )
        ).delete(synchronize_session=False)
        db.session.commit()
    _ids_creados_para_editar.clear()


# ---------------------------------------------------------------------------
# Listado — acceso universal (4 roles)
# ---------------------------------------------------------------------------

def test_listado_render_supervisor(usuario_supervisor):
    r = usuario_supervisor.get('/configuracion-motor/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


def test_listado_accesible_admin(usuario_admin):
    r = usuario_admin.get('/configuracion-motor/', follow_redirects=True)
    assert r.status_code == 200


def test_listado_accesible_tramitador(usuario_tramitador):
    r = usuario_tramitador.get('/configuracion-motor/', follow_redirects=True)
    assert r.status_code == 200


def test_listado_accesible_administrativo(usuario_administrativo):
    r = usuario_administrativo.get('/configuracion-motor/', follow_redirects=True)
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Alta — solo SUPERVISOR/ADMIN — sujeto por cascada (nivel SOLICITUD)
# ---------------------------------------------------------------------------

def _tipo_solicitud_siglas(app):
    with app.app_context():
        from app.models.tipos_solicitudes import TipoSolicitud
        tipo = TipoSolicitud.query.first()
        if tipo is None:
            pytest.skip('Faltan datos maestros (tipos_solicitudes) en esta BD')
        return tipo.siglas


def test_supervisor_puede_crear_regla(usuario_supervisor, app):
    siglas = _tipo_solicitud_siglas(app)
    r = usuario_supervisor.post('/configuracion-motor/reglas/crear', data={
        'accion': 'CREAR',
        'efecto': 'BLOQUEAR',
        'sujeto_nivel': 'SOLICITUD',
        'sujeto_seg0': 'ANY',
        'sujeto_seg1': siglas,
        'prioridad': '0',
        'descripcion': 'Regla de prueba (#170 smoke)',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/configuracion-motor/' in r.headers.get('Location', '')

    with app.app_context():
        from app.models.motor_reglas import ReglaMotor
        creada = ReglaMotor.query.filter_by(descripcion='Regla de prueba (#170 smoke)').first()
        assert creada is not None
        assert creada.activa is True
        assert creada.sujeto == f'ANY/{siglas}'
        assert creada.condiciones == []


def test_crear_con_segmento_inexistente_no_guarda(usuario_supervisor, app):
    r = usuario_supervisor.post('/configuracion-motor/reglas/crear', data={
        'accion': 'CREAR',
        'efecto': 'BLOQUEAR',
        'sujeto_nivel': 'SOLICITUD',
        'sujeto_seg0': 'ANY',
        'sujeto_seg1': 'SIGLAS_QUE_NO_EXISTEN_XYZ',
        'descripcion': 'No debe crearse (#170 smoke)',
    }, follow_redirects=True)
    assert r.status_code == 200

    with app.app_context():
        from app.models.motor_reglas import ReglaMotor
        assert ReglaMotor.query.filter_by(descripcion='No debe crearse (#170 smoke)').first() is None


def test_tramitador_no_puede_crear(usuario_tramitador, app):
    siglas = _tipo_solicitud_siglas(app)
    r = usuario_tramitador.post('/configuracion-motor/reglas/crear', data={
        'accion': 'CREAR',
        'efecto': 'BLOQUEAR',
        'sujeto_nivel': 'SOLICITUD',
        'sujeto_seg0': 'ANY',
        'sujeto_seg1': siglas,
        'descripcion': 'Intento no autorizado (#170 smoke)',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


# ---------------------------------------------------------------------------
# Edición (incluye condiciones anidadas) — solo SUPERVISOR/ADMIN
# ---------------------------------------------------------------------------

def _crear_para_editar(app):
    from app import db
    from app.models.motor_reglas import ReglaMotor
    from app.models.tipos_solicitudes import TipoSolicitud
    with app.app_context():
        tipo = TipoSolicitud.query.first()
        if tipo is None:
            pytest.skip('Faltan datos maestros (tipos_solicitudes) en esta BD')
        item = ReglaMotor(
            accion='CREAR',
            sujeto=f'ANY/{tipo.siglas}',
            efecto='BLOQUEAR',
            prioridad=0,
            activa=True,
            descripcion='Base para edición (#170 smoke)',
        )
        db.session.add(item)
        db.session.commit()
        _ids_creados_para_editar.append(item.id)
        return item.id, tipo.siglas


def test_supervisor_puede_editar_sin_condiciones(usuario_supervisor, app):
    item_id, siglas = _crear_para_editar(app)
    r = usuario_supervisor.post(f'/configuracion-motor/reglas/{item_id}/editar', data={
        'accion': 'BORRAR',
        'efecto': 'ADVERTIR',
        'sujeto_nivel': 'SOLICITUD',
        'sujeto_seg0': 'ANY',
        'sujeto_seg1': siglas,
        'prioridad': '5',
        'descripcion': 'Editada (#170 smoke)',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.motor_reglas import ReglaMotor
        editado = ReglaMotor.query.get(item_id)
        assert editado.accion == 'BORRAR'
        assert editado.efecto == 'ADVERTIR'
        assert editado.prioridad == 5


def test_supervisor_puede_anadir_condicion(usuario_supervisor, app):
    item_id, siglas = _crear_para_editar(app)

    with app.app_context():
        from app.models.motor_reglas import CatalogoVariable
        variable = CatalogoVariable.query.filter_by(tipo_dato='numerico', activa=True).first()
        if variable is None:
            pytest.skip('catalogo_variables sin variable numérica activa en esta BD')
        variable_id = variable.id

    r = usuario_supervisor.post(f'/configuracion-motor/reglas/{item_id}/editar', data={
        'accion': 'CREAR',
        'efecto': 'BLOQUEAR',
        'sujeto_nivel': 'SOLICITUD',
        'sujeto_seg0': 'ANY',
        'sujeto_seg1': siglas,
        'cond_variable_id': str(variable_id),
        'cond_operador': 'GTE',
        'cond_valor': '10',
        'cond_orden': '1',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.motor_reglas import ReglaMotor
        editado = ReglaMotor.query.get(item_id)
        assert len(editado.condiciones) == 1
        assert editado.condiciones[0].operador == 'GTE'
        assert editado.condiciones[0].valor == 10


def test_tramitador_no_puede_editar(usuario_tramitador, app):
    item_id, siglas = _crear_para_editar(app)
    r = usuario_tramitador.post(f'/configuracion-motor/reglas/{item_id}/editar', data={
        'accion': 'CREAR',
        'efecto': 'BLOQUEAR',
        'sujeto_nivel': 'SOLICITUD',
        'sujeto_seg0': 'ANY',
        'sujeto_seg1': siglas,
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


# ---------------------------------------------------------------------------
# Baja lógica (activar/desactivar) — SUPERVISOR y ADMIN
# ---------------------------------------------------------------------------

def test_supervisor_puede_desactivar(usuario_supervisor, app):
    item_id, _siglas = _crear_para_editar(app)
    r = usuario_supervisor.post(f'/configuracion-motor/reglas/{item_id}/activar', follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.motor_reglas import ReglaMotor
        editado = ReglaMotor.query.get(item_id)
        assert editado.activa is False


def test_tramitador_no_puede_desactivar(usuario_tramitador, app):
    item_id, _siglas = _crear_para_editar(app)
    r = usuario_tramitador.post(f'/configuracion-motor/reglas/{item_id}/activar', follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


# ---------------------------------------------------------------------------
# Excepciones anidadas (modal grande) — solo SUPERVISOR/ADMIN
# ---------------------------------------------------------------------------

def test_supervisor_puede_crear_excepcion_con_condicion(usuario_supervisor, app):
    item_id, _siglas = _crear_para_editar(app)

    with app.app_context():
        from app.models.motor_reglas import CatalogoVariable
        variable = CatalogoVariable.query.filter_by(tipo_dato='boolean', activa=True).first()
        if variable is None:
            pytest.skip('catalogo_variables sin variable booleana activa en esta BD')
        variable_id = variable.id

    r = usuario_supervisor.post(
        f'/configuracion-motor/reglas/{item_id}/excepciones/crear',
        data={
            'articulo': 'DA1',
            'cond_variable_id': str(variable_id),
            'cond_operador': 'EQ',
            'cond_valor': 'true',
            'cond_orden': '1',
        },
        headers={'X-Requested-With': 'XMLHttpRequest'},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body['ok'] is True

    with app.app_context():
        from app.models.motor_reglas import ReglaMotor
        regla = ReglaMotor.query.get(item_id)
        assert len(regla.excepciones) == 1
        excepcion = regla.excepciones[0]
        assert excepcion.articulo == 'DA1'
        assert len(excepcion.condiciones) == 1
        assert excepcion.condiciones[0].valor is True


def test_supervisor_puede_desactivar_excepcion(usuario_supervisor, app):
    item_id, _siglas = _crear_para_editar(app)

    from app import db
    from app.models.motor_reglas import ExcepcionMotor
    with app.app_context():
        exc = ExcepcionMotor(regla_id=item_id, activa=True, articulo='DA1 (#170 smoke)')
        db.session.add(exc)
        db.session.commit()
        exc_id = exc.id

    r = usuario_supervisor.post(
        f'/configuracion-motor/reglas/{item_id}/excepciones/{exc_id}/activar',
        headers={'X-Requested-With': 'XMLHttpRequest'},
    )
    assert r.status_code == 200
    assert r.get_json()['activa'] is False

    with app.app_context():
        assert ExcepcionMotor.query.get(exc_id).activa is False


def test_tramitador_no_puede_crear_excepcion(usuario_tramitador, app):
    item_id, _siglas = _crear_para_editar(app)
    r = usuario_tramitador.post(
        f'/configuracion-motor/reglas/{item_id}/excepciones/crear',
        data={'articulo': 'DA1'},
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')
