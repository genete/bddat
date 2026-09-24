"""Smoke test — catálogo de plazos legales (/catalogo_plazos/, #632).

Cubre listado (acceso universal, 4 roles), alta en los niveles de fila con
plazo posible (ACTO/TAREA — cascada de campo_fecha), edición (incluye
condiciones anidadas con el operador BETWEEN, exclusivo de este catálogo frente
a items_tecnicos/admin_requisitos) y baja lógica (activar/desactivar),
restringidas a SUPERVISOR/ADMIN — mismo patrón que items_tecnicos (#594).

Sin tests de "eliminar": la baja física está fuera de alcance del issue.

#788 retiró las altas de nivel FASE y TRAMITE: no portan fecha administrativa
y por tanto no pueden tener plazo. ADR-048 (#892) reabrió FASE para las fases
finalizadoras y #931 la volvió a cerrar —el plazo de resolver es del acto, no
de la fase que lo resuelve—, a la vez que renombraba SOLICITUD a ACTO. Los
smoke tests de rechazo cubren la vía que sigue abierta para los niveles sin
fila — un POST directo al endpoint, sin pasar por el formulario — con el mismo
criterio que el CheckConstraint de BD: el CRUD da el error legible, la
constraint cubre lo que le llega sin pasar por él. Y el de hoja combinada
(#931, D10), el invariante del nivel ACTO que ningún CHECK puede expresar.

Estos tests corren contra la BD real de desarrollo (mismo patrón que el resto
de la suite, ver conftest._login_as) — el fixture autouse de abajo borra al
terminar toda fila que no existiera al empezar, para no dejar basura en la BD
compartida. Las marcas '#632 smoke' en norma_origen se conservan porque los
asserts las usan para localizar lo creado, pero la limpieza ya no depende de
ellas.
"""
import pytest


@pytest.fixture(autouse=True)
def _limpiar_datos_prueba(app):
    """Snapshot de ids: se borra lo que aparezca durante el test.

    Las dos estrategias anteriores dependían de que el test colaborase, y por
    eso fallaron: filtrar por texto en norma_origen se rompe cuando el propio
    test edita ese campo (test_supervisor_puede_anadir_condicion_between no lo
    envía en el POST y el endpoint lo deja a NULL, #672), y registrar el id en
    _crear_para_editar exige que cada test nuevo se acuerde de hacerlo. El
    snapshot no depende de nada que el test haga — sin él, 14 filas huérfanas
    sobrevivieron en la BD de desarrollo hasta #787.
    """
    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        previos = {
            fila.id for fila in CatalogoPlazo.query.with_entities(CatalogoPlazo.id).all()
        }
    yield
    with app.app_context():
        from app import db
        from app.models.catalogo_plazos import CatalogoPlazo
        # Las condiciones_plazo cuelgan con ON DELETE CASCADE.
        CatalogoPlazo.query.filter(
            CatalogoPlazo.id.notin_(previos)
        ).delete(synchronize_session=False)
        db.session.commit()


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


@pytest.mark.parametrize('nivel', [b'TRAMITE', b'FASE', b'SOLICITUD'])
def test_listado_no_ofrece_niveles_sin_fila(usuario_supervisor, nivel):
    """TRAMITE no porta fecha administrativa (#788), FASE se retiró en #931 y
    SOLICITUD es el nombre viejo de ACTO. Ninguno de los tres literales
    aparece como `value` en la página: los selects de tipos usan sus propios
    códigos, no el literal del nivel."""
    r = usuario_supervisor.get('/catalogo_plazos/', follow_redirects=True)
    assert r.status_code == 200
    assert b'value="' + nivel + b'"' not in r.data


def test_listado_ofrece_nivel_acto(usuario_supervisor):
    """#931: el select de nivel del modal de alta dice «Acto», y es el que
    viene elegido por defecto."""
    import re
    r = usuario_supervisor.get('/catalogo_plazos/', follow_redirects=True)
    assert r.status_code == 200
    assert re.search(rb'value="ACTO"\s+selected', r.data)


# ---------------------------------------------------------------------------
# Alta — solo SUPERVISOR/ADMIN — un caso por nivel ESFTT (cascada de campo_fecha)
# ---------------------------------------------------------------------------

def _datos_maestros_acto(app):
    """Siglas de un tipo atómico SIN entrada activa de nivel ACTO, más un efecto.

    `.first()` a secas picaría con cualquier tipo, incluido uno de los 7 que
    llevan el plazo para resolver y notificar — y el alta chocaría contra la
    validación de duplicado ciego de #786. Se elige uno libre, igual que ya
    hacía el caso de nivel trámite. Atómico porque la hoja de una fila ACTO no
    puede ser una combinación (#931, D10).
    """
    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        from app.models.tipos_solicitudes import TipoSolicitud
        from app.models.efectos_plazo import EfectoPlazo
        caminos_ocupados = {
            camino for (camino,) in CatalogoPlazo.query
            .filter_by(tipo_elemento='ACTO', activo=True)
            .with_entities(CatalogoPlazo.camino).all()
        }
        tipo = next(
            (t for t in TipoSolicitud.query.order_by(TipoSolicitud.id).all()
             if '+' not in t.siglas and f'ANY/{t.siglas}' not in caminos_ocupados),
            None,
        )
        efecto = EfectoPlazo.query.first()
        if tipo is None or efecto is None:
            pytest.skip('Faltan datos maestros (tipos_solicitudes / efectos_plazo) en esta BD')
        return tipo.siglas, efecto.id


def _datos_maestros_tarea(app):
    """Código de tipo de tarea SIN entrada activa a nivel TAREA, más un efecto.

    Mismo motivo que `_datos_maestros_acto`: `.first()` a secas picaba con
    NOTIFICAR en cuanto #776 (2026-08-22) sembró su plazo genérico del art. 40
    LPACAP (`ANY/ANY/ANY/ANY/NOTIFICAR`) — el alta chocaba contra la validación
    de duplicado ciego de #786. Se elige un código libre, igual que ya hacía el
    caso de nivel solicitud.
    """
    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        from app.models.tipos_tareas import TipoTarea
        from app.models.efectos_plazo import EfectoPlazo
        caminos_ocupados = {
            camino for (camino,) in CatalogoPlazo.query
            .filter_by(tipo_elemento='TAREA', activo=True)
            .with_entities(CatalogoPlazo.camino).all()
        }
        tipo_tarea = next(
            (t for t in TipoTarea.query.order_by(TipoTarea.id).all()
             if f'ANY/ANY/ANY/ANY/{t.codigo}' not in caminos_ocupados),
            None,
        )
        efecto = EfectoPlazo.query.first()
        if tipo_tarea is None or efecto is None:
            pytest.skip('Faltan datos maestros (tipos_tareas / efectos_plazo) en esta BD')
        return tipo_tarea.codigo, efecto.id


def test_supervisor_puede_crear_nivel_acto(usuario_supervisor, app):
    siglas, efecto_id = _datos_maestros_acto(app)
    r = usuario_supervisor.post('/catalogo_plazos/crear', data={
        'tipo_elemento': 'ACTO',
        'camino_solicitud': siglas,
        'plazo_valor': '3',
        'plazo_unidad': 'MESES',
        'efecto_vencimiento_id': str(efecto_id),
        'norma_origen': 'Nivel acto (#632 smoke)',
        'orden': '999',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/catalogo_plazos/' in r.headers.get('Location', '')

    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        creado = CatalogoPlazo.query.filter_by(norma_origen='Nivel acto (#632 smoke)').first()
        assert creado is not None
        assert creado.activo is True
        assert creado.tipo_elemento == 'ACTO'
        assert creado.camino == f'ANY/{siglas}'
        assert creado.campo_fecha == {'fk': 'documento_solicitud_id'}
        assert creado.condiciones == []


def test_crear_acto_con_combinacion_es_rechazado(usuario_supervisor, app):
    """#931 (D10): la hoja de una fila ACTO debe ser un tipo atómico. Con una
    combinación la fila se guardaría sin error y no casaría nunca: el camino
    del acto lleva siempre su tipo simple."""
    with app.app_context():
        from app.models.efectos_plazo import EfectoPlazo
        efecto = EfectoPlazo.query.first()
        assert efecto is not None, 'la semilla debe traer efectos_plazo'
        efecto_id = efecto.id

    r = usuario_supervisor.post('/catalogo_plazos/crear', data={
        'tipo_elemento': 'ACTO',
        'camino_solicitud': 'AAP+AAC',
        'plazo_valor': '3',
        'plazo_unidad': 'MESES',
        'efecto_vencimiento_id': str(efecto_id),
        'norma_origen': 'Acto combinado (#931 smoke)',
    }, follow_redirects=False)
    assert r.status_code == 200, 'Debe re-renderizar el formulario con el error, no redirigir'
    assert 'combinación de actos' in r.get_data(as_text=True)

    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        assert CatalogoPlazo.query.filter_by(norma_origen='Acto combinado (#931 smoke)').first() is None


def test_la_combinacion_sigue_valiendo_como_ancestro_de_una_tarea(usuario_supervisor, app):
    """Control de D10: en el camino de una tarea el segundo segmento son las
    siglas reales de la solicitud, y ahí una combinación sí es válida."""
    codigo_tarea, efecto_id = _datos_maestros_tarea(app)
    r = usuario_supervisor.post('/catalogo_plazos/crear', data={
        'tipo_elemento': 'TAREA',
        'camino_solicitud': 'AAP+AAC',
        'camino_tarea': codigo_tarea,
        'campo_fecha_rol': 'CONSUMIDO',
        'plazo_valor': '10',
        'plazo_unidad': 'DIAS_HABILES',
        'efecto_vencimiento_id': str(efecto_id),
        'norma_origen': 'Tarea bajo combinación (#931 smoke)',
        'orden': '999',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        creado = CatalogoPlazo.query.filter_by(
            norma_origen='Tarea bajo combinación (#931 smoke)').first()
        assert creado is not None
        assert creado.camino == f'ANY/AAP+AAC/ANY/ANY/{codigo_tarea}'


def test_supervisor_puede_crear_nivel_tarea(usuario_supervisor, app):
    codigo_tarea, efecto_id = _datos_maestros_tarea(app)

    r = usuario_supervisor.post('/catalogo_plazos/crear', data={
        'tipo_elemento': 'TAREA',
        'camino_tarea': codigo_tarea,   # ancestros omitidos → ANY (#785)
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


def test_supervisor_puede_crear_tarea_suspensora_con_cumplimiento(usuario_supervisor, app):
    """#778: los dos datos nuevos del catálogo viajan en el mismo formulario —
    con qué documento se cierra el plazo y si suspende el de la solicitud."""
    codigo_tarea, efecto_id = _datos_maestros_tarea(app)

    r = usuario_supervisor.post('/catalogo_plazos/crear', data={
        'tipo_elemento': 'TAREA',
        'camino_tarea': codigo_tarea,
        'campo_fecha_rol': 'CONSUMIDO',
        'campo_cumplimiento_rol': 'PRODUCIDO',
        'suspende_plazo_solicitud': '1',
        'plazo_valor': '10',
        'plazo_unidad': 'DIAS_HABILES',
        'efecto_vencimiento_id': str(efecto_id),
        'norma_origen': 'Tarea suspensora (#778 smoke)',
        'orden': '999',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        creado = CatalogoPlazo.query.filter_by(norma_origen='Tarea suspensora (#778 smoke)').first()
        assert creado is not None
        assert creado.campo_fecha_cumplimiento == {'rol': 'PRODUCIDO'}
        assert creado.suspende_plazo_solicitud is True


def test_crear_tarea_sin_cumplimiento_lo_deja_vacio(usuario_supervisor, app):
    """El caso del tablón (#416): sin señalador el plazo no alcanza CUMPLIDO, y
    eso es una decisión, no un formulario a medio rellenar."""
    codigo_tarea, efecto_id = _datos_maestros_tarea(app)

    r = usuario_supervisor.post('/catalogo_plazos/crear', data={
        'tipo_elemento': 'TAREA',
        'camino_tarea': codigo_tarea,
        'campo_fecha_rol': 'PRODUCIDO',
        'campo_cumplimiento_rol': '',
        'plazo_valor': '30',
        'plazo_unidad': 'DIAS_NATURALES',
        'efecto_vencimiento_id': str(efecto_id),
        'norma_origen': 'Tarea sin cierre (#778 smoke)',
        'orden': '998',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        creado = CatalogoPlazo.query.filter_by(norma_origen='Tarea sin cierre (#778 smoke)').first()
        assert creado is not None
        assert creado.campo_fecha_cumplimiento is None
        assert creado.suspende_plazo_solicitud is False


def test_crear_acto_se_cumple_con_la_notificacion_al_titular(usuario_supervisor, app):
    """En el nivel ACTO los dos extremos son fijos: el documento de
    solicitud abre el plazo y lo cierra la notificación al titular en la fase
    que resuelve el acto, calculada (#930, D9). Y la casilla de suspensión se
    ignora aunque llegue: el art. 22 suspende el plazo de resolver, así que
    marcarlo a él sería suspenderse a sí mismo."""
    siglas, efecto_id = _datos_maestros_acto(app)
    r = usuario_supervisor.post('/catalogo_plazos/crear', data={
        'tipo_elemento': 'ACTO',
        'camino_solicitud': siglas,
        'suspende_plazo_solicitud': '1',   # POST directo: la UI no la ofrece aquí
        'plazo_valor': '3',
        'plazo_unidad': 'MESES',
        'efecto_vencimiento_id': str(efecto_id),
        'norma_origen': 'Solicitud con cierre (#778 smoke)',
        'orden': '997',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        creado = CatalogoPlazo.query.filter_by(norma_origen='Solicitud con cierre (#778 smoke)').first()
        assert creado is not None
        assert creado.campo_fecha == {'fk': 'documento_solicitud_id'}
        assert creado.campo_fecha_cumplimiento == {'calculado': 'documento_cumplimiento'}
        assert creado.suspende_plazo_solicitud is False


def test_crear_con_ancestros_concretos_compone_el_camino(usuario_supervisor, app):
    """#785: los ancestros concretados viajan al camino; los omitidos van a ANY."""
    with app.app_context():
        from app.models.tipos_solicitudes import TipoSolicitud
        from app.models.tipos_fases import TipoFase
        from app.models.tipos_tramites import TipoTramite
        from app.models.tipos_tareas import TipoTarea
        from app.models.efectos_plazo import EfectoPlazo
        tipo_sol = TipoSolicitud.query.first()
        tipo_fase = TipoFase.query.first()
        tipo_tramite = TipoTramite.query.first()
        tipo_tarea = TipoTarea.query.first()
        efecto = EfectoPlazo.query.first()
        if not all([tipo_sol, tipo_fase, tipo_tramite, tipo_tarea, efecto]):
            pytest.skip('Faltan datos maestros en esta BD')
        siglas, cod_fase = tipo_sol.siglas, tipo_fase.codigo
        cod_tramite, cod_tarea, efecto_id = tipo_tramite.codigo, tipo_tarea.codigo, efecto.id

    r = usuario_supervisor.post('/catalogo_plazos/crear', data={
        'tipo_elemento': 'TAREA',
        'camino_solicitud': siglas,
        'camino_fase': cod_fase,
        'camino_tramite': cod_tramite,
        'camino_tarea': cod_tarea,
        'campo_fecha_rol': 'CONSUMIDO',
        'plazo_valor': '15',
        'plazo_unidad': 'DIAS_HABILES',
        'efecto_vencimiento_id': str(efecto_id),
        'norma_origen': 'Camino concreto (#632 smoke)',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        creado = CatalogoPlazo.query.filter_by(norma_origen='Camino concreto (#632 smoke)').first()
        assert creado is not None
        assert creado.camino == f'ANY/{siglas}/{cod_fase}/{cod_tramite}/{cod_tarea}'
        assert creado.hoja == cod_tarea


def test_crear_sin_hoja_es_rechazado(usuario_supervisor, app):
    """#785: la hoja identifica el elemento evaluado — no puede quedar en ANY."""
    with app.app_context():
        from app.models.efectos_plazo import EfectoPlazo
        efecto = EfectoPlazo.query.first()
        if efecto is None:
            pytest.skip('Faltan datos maestros (efectos_plazo) en esta BD')
        efecto_id = efecto.id

    r = usuario_supervisor.post('/catalogo_plazos/crear', data={
        'tipo_elemento': 'TAREA',
        'camino_tarea': 'ANY',          # hoja sin concretar
        'campo_fecha_rol': 'CONSUMIDO',
        'plazo_valor': '1',
        'plazo_unidad': 'MESES',
        'efecto_vencimiento_id': str(efecto_id),
        'norma_origen': 'Hoja ANY (#632 smoke)',
    }, follow_redirects=False)
    assert r.status_code == 200, 'Debe re-renderizar el formulario con el error, no redirigir'

    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        assert CatalogoPlazo.query.filter_by(norma_origen='Hoja ANY (#632 smoke)').first() is None


def test_crear_con_tipo_inexistente_es_rechazado(usuario_supervisor, app):
    """#785: los segmentos concretos se validan contra su catálogo de tipos."""
    with app.app_context():
        from app.models.efectos_plazo import EfectoPlazo
        efecto = EfectoPlazo.query.first()
        if efecto is None:
            pytest.skip('Faltan datos maestros (efectos_plazo) en esta BD')
        efecto_id = efecto.id

    r = usuario_supervisor.post('/catalogo_plazos/crear', data={
        'tipo_elemento': 'TAREA',
        'camino_tarea': 'TAREA_QUE_NO_EXISTE',
        'campo_fecha_rol': 'CONSUMIDO',
        'plazo_valor': '1',
        'plazo_unidad': 'MESES',
        'efecto_vencimiento_id': str(efecto_id),
        'norma_origen': 'Tipo inexistente (#632 smoke)',
    }, follow_redirects=False)
    assert r.status_code == 200

    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        assert CatalogoPlazo.query.filter_by(norma_origen='Tipo inexistente (#632 smoke)').first() is None


@pytest.mark.parametrize('nivel,camino', [
    ('TRAMITE', {}),
    ('FASE', {'camino_fase': 'RESOLUCION_DUP'}),
    ('SOLICITUD', {'camino_solicitud': 'AAP'}),
])
def test_crear_nivel_sin_fila_es_rechazado(usuario_supervisor, app, nivel, camino):
    """#788 (TRAMITE), #931 (FASE, y SOLICITUD como nombre viejo de ACTO):
    aunque el formulario no los ofrece, el endpoint debe rechazarlos con un
    error legible si llegan igual (POST directo, no por la UI) — no un 500 del
    CheckConstraint. Mismo criterio que la BD: el CRUD da el error legible, la
    constraint cubre lo que le llega sin pasar por él."""
    with app.app_context():
        from app.models.efectos_plazo import EfectoPlazo
        efecto = EfectoPlazo.query.first()
        if efecto is None:
            pytest.skip('Faltan datos maestros (efectos_plazo) en esta BD')
        efecto_id = efecto.id

    norma = f'Nivel {nivel} rechazado (#931 smoke)'
    r = usuario_supervisor.post('/catalogo_plazos/crear', data={
        'tipo_elemento': nivel,
        **camino,
        'plazo_valor': '1',
        'plazo_unidad': 'MESES',
        'efecto_vencimiento_id': str(efecto_id),
        'norma_origen': norma,
    }, follow_redirects=False)
    assert r.status_code == 200, 'Debe re-renderizar el formulario con el error, no un 500'

    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        assert CatalogoPlazo.query.filter_by(norma_origen=norma).first() is None


def test_tramitador_no_puede_crear(usuario_tramitador, app):
    siglas, efecto_id = _datos_maestros_acto(app)
    r = usuario_tramitador.post('/catalogo_plazos/crear', data={
        'tipo_elemento': 'ACTO',
        'camino_solicitud': siglas,
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

def _crear_para_editar(app, cumplimiento=None):
    """Fila ACTO de partida, en un camino libre.

    Las siglas salen de `_datos_maestros_acto` y no de un `.first()` ciego:
    la ruta de edición revalida la colisión de camino (#786), así que reeditar
    una fila plantada sobre un camino ya ocupado se bloquearía sin que el test
    llegue a probar lo suyo.
    """
    from app import db
    from app.models.catalogo_plazos import CatalogoPlazo
    siglas, efecto_id = _datos_maestros_acto(app)
    with app.app_context():
        item = CatalogoPlazo(
            tipo_elemento='ACTO',
            camino=f'ANY/{siglas}',
            campo_fecha={'fk': 'documento_solicitud_id'},
            campo_fecha_cumplimiento=cumplimiento,
            plazo_valor=3,
            plazo_unidad='MESES',
            efecto_vencimiento_id=efecto_id,
            norma_origen='Base para edición (#632 smoke)',
            orden=999,
        )
        db.session.add(item)
        db.session.commit()
        return item.id, siglas, efecto_id


def test_supervisor_puede_editar_sin_condiciones(usuario_supervisor, app):
    item_id, siglas, efecto_id = _crear_para_editar(app)
    r = usuario_supervisor.post(f'/catalogo_plazos/{item_id}/editar', data={
        'tipo_elemento': 'ACTO',
        'camino_solicitud': siglas,
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
        'tipo_elemento': 'ACTO',
        'camino_solicitud': siglas,
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
        'tipo_elemento': 'ACTO',
        'camino_solicitud': siglas,
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


def test_editar_una_fila_de_acto_no_revierte_el_cumplimiento(usuario_supervisor, app):
    """H3 de #930: la edición reescribe el cumplimiento por nivel, así que
    abrir y guardar una fila deshacía la migración en silencio. Ahora escribe
    lo mismo que la migración."""
    calculado = {'calculado': 'documento_cumplimiento'}
    item_id, siglas, efecto_id = _crear_para_editar(app, cumplimiento=calculado)
    r = usuario_supervisor.post(f'/catalogo_plazos/{item_id}/editar', data={
        'tipo_elemento': 'ACTO',
        'camino_solicitud': siglas,
        'plazo_valor': '3',
        'plazo_unidad': 'MESES',
        'efecto_vencimiento_id': str(efecto_id),
        'norma_origen': 'Acto reeditado (#930 smoke)',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        editado = CatalogoPlazo.query.get(item_id)
        assert editado.norma_origen == 'Acto reeditado (#930 smoke)'
        assert editado.campo_fecha_cumplimiento == calculado


def test_detalle_rotula_el_cumplimiento_calculado(usuario_supervisor, app):
    item_id, _siglas, _efecto_id = _crear_para_editar(
        app, cumplimiento={'calculado': 'documento_cumplimiento'})
    r = usuario_supervisor.get(f'/catalogo_plazos/{item_id}/fragmento')
    assert r.status_code == 200
    texto = r.get_data(as_text=True)
    assert 'notificación al titular en la fase que resuelve este acto' in texto


def test_detalle_nombra_el_acto_por_su_tipo(usuario_supervisor, app):
    """#931 (D7): el nivel de la fila es ACTO, pero la hoja se nombra con el
    catálogo del nodo que ocupa —tipos_solicitudes—, «AAP — descripción» y no
    las siglas peladas; y el segmento se rotula «Acto», no «Solicitud»."""
    item_id, siglas, _efecto_id = _crear_para_editar(app)
    with app.app_context():
        from app.models.tipos_solicitudes import TipoSolicitud
        descripcion = TipoSolicitud.query.filter_by(siglas=siglas).one().descripcion

    r = usuario_supervisor.get(f'/catalogo_plazos/{item_id}/fragmento')
    assert r.status_code == 200
    texto = r.get_data(as_text=True)
    from markupsafe import escape
    assert str(escape(f'{siglas} — {descripcion}')) in texto
    assert 'Acto:' in texto
    assert 'value="Acto"' in texto


def test_detalle_avisa_de_un_calculado_desconocido(usuario_supervisor, app):
    """D5: un nombre fuera de `plazos.CALCULADOS` solo puede llegar por
    migración o SQL; la lectura lo resuelve a None y esto es lo único que lo
    dice en la interfaz."""
    item_id, _siglas, _efecto_id = _crear_para_editar(
        app, cumplimiento={'calculado': 'no_existe_930'})
    r = usuario_supervisor.get(f'/catalogo_plazos/{item_id}/fragmento')
    assert r.status_code == 200
    texto = r.get_data(as_text=True)
    assert '⚠ Propiedad calculada desconocida «no_existe_930»' in texto
    assert 'el plazo no puede cumplirse' in texto


def test_cada_propiedad_calculada_tiene_su_etiqueta():
    """Quien añada una propiedad calculada tiene que decir qué significa."""
    from app.modules.catalogo_plazos.routes import _CALCULADO_LABEL
    from app.services.plazos import CALCULADOS
    assert set(_CALCULADO_LABEL) == set(CALCULADOS)


def test_tramitador_no_puede_editar(usuario_tramitador, app):
    item_id, siglas, efecto_id = _crear_para_editar(app)
    r = usuario_tramitador.post(f'/catalogo_plazos/{item_id}/editar', data={
        'tipo_elemento': 'ACTO',
        'camino_solicitud': siglas,
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
