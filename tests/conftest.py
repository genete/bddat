import pytest
from sqlalchemy.orm import scoped_session, sessionmaker
from app import create_app, db as _db


# Tope de tests que pueden autodesactivarse en una pasada completa (#849).
#
# Un skip no se distingue de un test que pasa cuando solo se mira el resultado
# global: por eso 174 `pytest.skip` repartidos por 52 ficheros podían saltar sin
# que nadie lo supiera. Este tope hace visible la deuda — si sube, la suite
# falla y hay que mirar por qué.
#
# El número SOLO BAJA. Subirlo es aceptar que algo dejó de probarse, y eso se
# decide a propósito, no de pasada. Bajarlo al cerrar cada tanda es lo que
# convierte esto en un trinquete.
#
#   2026-09-05  50  línea base medida antes de tocar nada
#   2026-09-05  19  tras desclavar _login_as de CLG (-21) y revivir test_348 (-10)
UMBRAL_SKIPS = 19


def pytest_sessionfinish(session, exitstatus):
    """Falla la sesión si los skips superan el tope acordado (#849)."""
    reporter = session.config.pluginmanager.get_plugin('terminalreporter')
    if reporter is None:
        return
    n_skips = len(reporter.stats.get('skipped', []))
    if n_skips <= UMBRAL_SKIPS:
        return
    reporter.write_line('')
    reporter.write_line(
        f'#849 — {n_skips} tests saltados, por encima del tope de {UMBRAL_SKIPS}.',
        red=True, bold=True)
    reporter.write_line(
        '        Un skip por falta de datos es un hueco de cobertura, no un aprobado: '
        'mira el detalle con `pytest -rs`.')
    session.exitstatus = 1


@pytest.fixture(scope='session')
def app():
    """OJO: la suite todavía corre contra la BD de DESARROLLO (#849, fase A).

    El mundo aislado ya existe y funciona —`TestingConfig`, base construida
    desde las migraciones, semilla de catálogo y usuarios, raíz de ficheros
    propia—, pero le falta la semilla de datos de negocio, que llega con
    `alta_expediente()` en #428 (fase B).

    Medido el 2026-09-05 cambiando esta línea a `create_app('testing')`:

        contra desarrollo:  3 failed, 1586 passed,   50 skipped
        contra la de tests: 16 failed, 1180 passed, 441 skipped, 2 errors

    Los 16 fallos y los 441 skips tienen todos la misma causa —no hay
    expedientes, solicitudes ni entidades—, ninguno es achacable al
    aislamiento. Activar el interruptor hoy cambiaría 50 skips por 441, así
    que espera a que la semilla de negocio exista. Entonces esta línea pasa a
    `create_app('testing')` y no se vuelve atrás.
    """
    application = create_app()
    application.config['TESTING'] = True
    return application


@pytest.fixture(scope='function')
def app_ctx(app):
    """Contexto de aplicación con rollback automático al terminar.

    Aísla los tests en un SAVEPOINT: aunque el código de aplicación llame a
    db.session.commit() (p. ej. mutaciones_arbol.crear_fase), join_transaction_mode
    'create_savepoint' reabre el SAVEPOINT tras cada commit/rollback de la sesión,
    de forma que nada sale de la transacción externa.

    OJO: no basta con _db.session.configure(bind=connection, ...) — la Session
    custom de Flask-SQLAlchemy (flask_sqlalchemy.session.Session.get_bind) resuelve
    el bind de CUALQUIER modelo mapeado por su bind_key en _db.engines, ANTES de
    mirar self.bind, así que ignora silenciosamente el bind que le configuremos y
    los commits del código de aplicación llegaban a la BD real de desarrollo (#641).
    Por eso aquí se sustituye _db.session por una scoped_session de SQLAlchemy
    "vainilla" (sin ese override), la única forma de que el bind=connection se respete.
    """
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()
        session_original = _db.session
        _db.session = scoped_session(
            sessionmaker(bind=connection, join_transaction_mode='create_savepoint')
        )
        yield app
        _db.session.remove()
        _db.session = session_original
        transaction.rollback()
        connection.close()


@pytest.fixture(scope='function')
def client(app):
    """Flask test client — sin contexto de BD gestionado."""
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Fixtures de autenticación por rol (#503 — smoke tests ADR-019)
# ---------------------------------------------------------------------------

def _login_as(client, app, rol_nombre):
    """
    Autentica el cliente de test usando session_transaction: fija _user_id
    y rol_activo_nombre directamente en la sesión sin simular el formulario.
    Devuelve True si algún usuario de la BD tiene ese rol, False si no.

    Busca el primer usuario ACTIVO con el rol pedido, en vez de exigir unas
    siglas concretas (#849). Clavarlo a 'CLG' hacía que TODO test con
    `usuario_admin` se autodesactivara en silencio —CLG tiene SUPERVISOR,
    TRAMITADOR y ADMINISTRATIVO, pero no ADMIN—, dejando sin cobertura efectiva
    las pantallas de administración. El orden por id es lo que mantiene a CLG
    como usuario de los otros tres roles: es quien los tiene con id más bajo.
    """
    with app.app_context():
        from app.models.usuarios import Rol, Usuario
        u = (Usuario.query
             .join(Usuario.roles)
             .filter(Rol.nombre == rol_nombre, Usuario.activo.is_(True))
             .order_by(Usuario.id)
             .first())
        if u is None:
            return False
        rol = next(r for r in u.roles if r.nombre == rol_nombre)
        uid, rol_id, rol_nombre_db = str(u.id), rol.id, rol.nombre

    with client.session_transaction() as sess:
        sess['_user_id'] = uid
        sess['_fresh'] = True
        sess['rol_activo_id'] = rol_id
        sess['rol_activo_nombre'] = rol_nombre_db
    return True


@pytest.fixture
def usuario_admin(client, app):
    """Cliente autenticado con rol ADMIN."""
    if not _login_as(client, app, 'ADMIN'):
        pytest.skip('Ningún usuario activo con rol ADMIN en esta BD')
    return client


@pytest.fixture
def usuario_supervisor(client, app):
    """Cliente autenticado con rol SUPERVISOR."""
    if not _login_as(client, app, 'SUPERVISOR'):
        pytest.skip('Ningún usuario activo con rol SUPERVISOR en esta BD')
    return client


@pytest.fixture
def usuario_tramitador(client, app):
    """Cliente autenticado con rol TRAMITADOR."""
    if not _login_as(client, app, 'TRAMITADOR'):
        pytest.skip('Ningún usuario activo con rol TRAMITADOR en esta BD')
    return client


@pytest.fixture
def usuario_administrativo(client, app):
    """Cliente autenticado con rol ADMINISTRATIVO."""
    if not _login_as(client, app, 'ADMINISTRATIVO'):
        pytest.skip('Ningún usuario activo con rol ADMINISTRATIVO en esta BD')
    return client


@pytest.fixture
def expediente_seed(app):
    """ID del primer expediente en la BD de desarrollo. Skip si no existe ninguno."""
    with app.app_context():
        from app.models.expedientes import Expediente
        exp = Expediente.query.first()
        if exp is None:
            pytest.skip('No hay expedientes en la BD de desarrollo')
        return exp.id


@pytest.fixture
def entidad_seed(app):
    """ID de la primera entidad en la BD de desarrollo. Skip si no existe ninguna."""
    with app.app_context():
        from app.models.entidad import Entidad
        e = Entidad.query.first()
        if e is None:
            pytest.skip('No hay entidades en la BD de desarrollo')
        return e.id


@pytest.fixture
def plantilla_seed(app):
    """ID de la primera plantilla en la BD de desarrollo. Skip si no existe ninguna."""
    with app.app_context():
        from app.models.plantillas import Plantilla
        p = Plantilla.query.first()
        if p is None:
            pytest.skip('No hay plantillas en la BD de desarrollo')
        return p.id


@pytest.fixture
def primer_usuario_id(app):
    """ID del primer usuario en la BD de desarrollo. Skip si no existe ninguno.

    Con ORDER BY explícito (#849): un `first()` a secas devuelve la primera
    tupla FÍSICA, que se mueve con cada UPDATE de la tabla —el mecanismo que
    hizo indiagnosticable #832 y que #836 documenta—. Sin orden, esta fixture
    apunta a un usuario distinto según la pasada.
    """
    with app.app_context():
        from app.models.usuarios import Usuario
        u = Usuario.query.order_by(Usuario.id).first()
        if u is None:
            pytest.skip('No hay usuarios en la BD de desarrollo')
        return u.id


@pytest.fixture
def diagnostico_seed(app):
    """(expediente_id, documento_id) del primer Diagnostico en la BD de desarrollo.

    Skip si no existe ninguno (#629 — fragmento modal de diagnóstico).
    """
    with app.app_context():
        from app.models.diagnosticos import Diagnostico
        diag = Diagnostico.query.first()
        if diag is None:
            pytest.skip('No hay diagnósticos en la BD de desarrollo')
        return diag.documento.expediente_id, diag.documento_id


@pytest.fixture
def fs_tmp(app, tmp_path):
    """Redirige FILESYSTEM_BASE a un directorio temporal (#674).

    app_ctx revierte la BD por SAVEPOINT, pero el filesystem no es
    transaccional — cualquier test que genere un documento/certificado real
    dentro de una transacción que luego revierte deja el fichero físico
    huérfano en el servidor de ficheros de desarrollo real
    (FILESYSTEM_BASE=D:/BDDAT/docs_prueba en .env). Usar en cualquier test
    que cree un Expediente/Documento con esquema local y pueda disparar
    escritura a disco (certificados, escritos, pool).
    """
    base_original = app.config.get('FILESYSTEM_BASE')
    app.config['FILESYSTEM_BASE'] = str(tmp_path)
    yield tmp_path
    app.config['FILESYSTEM_BASE'] = base_original


@pytest.fixture
def tramitador_usuario_id(app):
    """ID del primer usuario activo con rol TRAMITADOR. Skip si no existe ninguno."""
    with app.app_context():
        from app.models.usuarios import Usuario, Rol
        u = Usuario.query.filter_by(activo=True).join(Usuario.roles).filter(
            Rol.nombre == 'TRAMITADOR'
        ).first()
        if u is None:
            pytest.skip('No hay usuarios con rol TRAMITADOR en la BD de desarrollo')
        return u.id


# ---------------------------------------------------------------------------
# Árbol ESFTT mínimo reutilizable (#715)
# ---------------------------------------------------------------------------

class ArbolESFTT:
    """Builder de árbol ESFTT mínimo para tests de invariantes contra SQL real.

    Monta solo los niveles que cada test necesita (fase/trámite/tarea/
    documento/vínculo/notificación), siempre bajo `app_ctx`: la sesión con
    SAVEPOINT revierte todo al terminar el test, igual que ya hacía
    `_montar_fase` en test_711_cierre_fase_cadena.py (de donde se extrae este
    builder para no duplicarlo en cada fichero de test — #715 checklist punto 1).

    Sin mocks: cada método hace un INSERT real y `flush()` para que las
    consultas de los checks (`app/services/invariantes_esftt.py`) vean las
    filas dentro de la misma transacción.
    """

    def __init__(self, db):
        self.db = db

    def _tipo(self, modelo, codigo):
        fila = modelo.query.filter_by(codigo=codigo).first()
        if fila is None:
            pytest.skip(f'{modelo.__name__} {codigo!r} no está en el catálogo de esta BD')
        return fila

    def solicitud_existente(self):
        """Primera solicitud de la BD de desarrollo. Puede tener hijos previos —
        usar `solicitud_nueva()` cuando el test necesite un árbol garantizado vacío."""
        from app.models.solicitudes import Solicitud
        s = Solicitud.query.first()
        if s is None:
            pytest.skip('No hay solicitudes en la BD de desarrollo')
        return s

    def solicitud_nueva(self):
        """Solicitud aislada, sin fases: para el caso 'sin hijos' de _check_borrar,
        donde reutilizar `solicitud_existente()` arriesga hijos previos ajenos al test."""
        from app.models.solicitudes import Solicitud
        from app.models.expedientes import Expediente
        from app.models.entidad import Entidad
        from app.models.tipos_solicitudes import TipoSolicitud
        exp = Expediente.query.first()
        ent = Entidad.query.first()
        tipo = TipoSolicitud.query.first()
        if exp is None or ent is None or tipo is None:
            pytest.skip('Faltan expediente/entidad/tipo_solicitud base en la BD de desarrollo')
        s = Solicitud(expediente_id=exp.id, entidad_id=ent.id, tipo_solicitud_id=tipo.id)
        self.db.session.add(s)
        self.db.session.flush()
        return s

    def fase(self, codigo_fase, solicitud=None):
        from app.models.fases import Fase
        from app.models.tipos_fases import TipoFase
        solicitud = solicitud or self.solicitud_existente()
        f = Fase(solicitud_id=solicitud.id, tipo_fase_id=self._tipo(TipoFase, codigo_fase).id)
        self.db.session.add(f)
        self.db.session.flush()
        return f

    def tramite(self, fase, codigo_tramite):
        from app.models.tramites import Tramite
        from app.models.tipos_tramites import TipoTramite
        t = Tramite(fase_id=fase.id, tipo_tramite_id=self._tipo(TipoTramite, codigo_tramite).id)
        self.db.session.add(t)
        self.db.session.flush()
        return t

    def tarea(self, tramite, codigo_tarea):
        from app.models.tareas import Tarea
        from app.models.tipos_tareas import TipoTarea
        ta = Tarea(tramite_id=tramite.id, tipo_tarea_id=self._tipo(TipoTarea, codigo_tarea).id)
        self.db.session.add(ta)
        self.db.session.flush()
        return ta

    def documento(self, expediente_id, codigo_tipo_doc, sufijo):
        from app.models.documentos import Documento
        from app.models.tipos_documentos import TipoDocumento
        doc = Documento(
            expediente_id=expediente_id,
            tipo_doc_id=self._tipo(TipoDocumento, codigo_tipo_doc).id,
            url=f'bddat://test-715/{sufijo}',
        )
        self.db.session.add(doc)
        self.db.session.flush()
        return doc

    def vincular(self, tarea, documento, rol):
        from app.models.documentos_tarea import DocumentoTarea
        v = DocumentoTarea(tarea_id=tarea.id, documento_id=documento.id, rol=rol)
        self.db.session.add(v)
        self.db.session.flush()
        return v

    def notificacion(self, tarea, resultado, canal='NOTIFICA'):
        from app.models.notificaciones import Notificacion
        import datetime
        n = Notificacion(
            tarea_id=tarea.id,
            resultado=resultado,
            canal=canal,
            fecha_puesta_disposicion=datetime.date.today(),
        )
        self.db.session.add(n)
        self.db.session.flush()
        return n


@pytest.fixture
def arbol_esftt(app_ctx):
    """Builder `ArbolESFTT` listo para usar, sobre la transacción de `app_ctx`."""
    from app import db
    return ArbolESFTT(db)
