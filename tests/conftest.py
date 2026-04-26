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
