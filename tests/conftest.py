import pytest
from app import create_app, db as _db


@pytest.fixture(scope='session')
def app():
    application = create_app()
    application.config['TESTING'] = True
    return application


@pytest.fixture(scope='function')
def app_ctx(app):
    """Contexto de aplicación con rollback automático al terminar."""
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin_nested()
        _db.session.bind = connection
        yield app
        _db.session.rollback()
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
    Devuelve True si el rol existe en la BD para el usuario CLG, False si no.
    """
    with app.app_context():
        from app.models.usuarios import Usuario
        u = Usuario.query.filter_by(siglas='CLG').first()
        if u is None:
            return False
        rol = next((r for r in u.roles if r.nombre == rol_nombre), None)
        if rol is None:
            return False
        uid, rol_id, rol_nombre_db = str(u.id), rol.id, rol.nombre

    with client.session_transaction() as sess:
        sess['_user_id'] = uid
        sess['_fresh'] = True
        sess['rol_activo_id'] = rol_id
        sess['rol_activo_nombre'] = rol_nombre_db
    return True


@pytest.fixture
def usuario_admin(client, app):
    """Cliente autenticado como CLG con rol ADMIN."""
    if not _login_as(client, app, 'ADMIN'):
        pytest.skip('CLG con rol ADMIN no disponible en esta BD')
    return client


@pytest.fixture
def usuario_supervisor(client, app):
    """Cliente autenticado como CLG con rol SUPERVISOR."""
    if not _login_as(client, app, 'SUPERVISOR'):
        pytest.skip('CLG con rol SUPERVISOR no disponible en esta BD')
    return client


@pytest.fixture
def usuario_tramitador(client, app):
    """Cliente autenticado como CLG con rol TRAMITADOR."""
    if not _login_as(client, app, 'TRAMITADOR'):
        pytest.skip('CLG con rol TRAMITADOR no disponible en esta BD')
    return client


@pytest.fixture
def usuario_administrativo(client, app):
    """Cliente autenticado como CLG con rol ADMINISTRATIVO."""
    if not _login_as(client, app, 'ADMINISTRATIVO'):
        pytest.skip('CLG con rol ADMINISTRATIVO no disponible en esta BD')
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
    """ID del primer usuario en la BD de desarrollo. Skip si no existe ninguno."""
    with app.app_context():
        from app.models.usuarios import Usuario
        u = Usuario.query.first()
        if u is None:
            pytest.skip('No hay usuarios en la BD de desarrollo')
        return u.id


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
