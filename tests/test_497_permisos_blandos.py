"""Smoke tests de permisos blandos (ADR-013 / Issue #497).

Verifica que:
  1. TRAMITADOR puede acceder en lectura a áreas administrativas (GET 200).
  2. TRAMITADOR no puede ejecutar mutaciones (302 a perfil o 403).
  3. SUPERVISOR sigue teniendo acceso completo sin regresiones.
"""
import pytest


# ---------------------------------------------------------------------------
# Autenticación
#
# Por rol y no por siglas (#849): estas fixtures hacían login como CLG con la
# contraseña de la base de desarrollo, así que los trece tests del fichero se
# saltaban enteros en cualquier otra base. Lo que aquí se prueba son los
# permisos, no el formulario de login — que tiene su propio test en
# tests/smoke/test_smoke_login.py.
# ---------------------------------------------------------------------------

@pytest.fixture
def tramitador(usuario_tramitador):
    """Cliente autenticado con rol TRAMITADOR."""
    return usuario_tramitador


@pytest.fixture
def supervisor(usuario_supervisor):
    """Cliente autenticado con rol SUPERVISOR."""
    return usuario_supervisor


# Con `app.app_context()` y con `assert`, no con `pytest.skip` (#849): estas
# consultas se hacían fuera de contexto —nunca llegaron a ejecutarse, porque el
# fichero entero se saltaba— y en una base sembrada por nosotros la ausencia de
# una plantilla o de un usuario es un defecto de la semilla, no un motivo para
# no probar. ORDER BY explícito: un `first()` a secas devuelve la primera tupla
# física, que se mueve con cada UPDATE (#836).

def _id_plantilla(app):
    from app.models.plantillas import Plantilla
    with app.app_context():
        p = Plantilla.query.order_by(Plantilla.id).first()
        assert p is not None, 'la semilla debe traer alguna plantilla'
        return p.id


def _id_usuario(app):
    from app.models.usuarios import Usuario
    with app.app_context():
        u = Usuario.query.order_by(Usuario.id).first()
        assert u is not None, 'la semilla debe traer algún usuario'
        return u.id


# ---------------------------------------------------------------------------
# TRAMITADOR — acceso de lectura (debe ser 200)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('ruta', [
    '/plantillas/',
    '/usuarios/',
])
def test_tramitador_puede_leer(tramitador, ruta):
    """TRAMITADOR accede en lectura a áreas administrativas."""
    r = tramitador.get(ruta, follow_redirects=True)
    assert r.status_code == 200, f'TRAMITADOR no puede leer {ruta} (status {r.status_code})'


def test_tramitador_puede_ver_detalle_plantilla(tramitador, app):
    """TRAMITADOR puede ver el detalle de una plantilla."""
    r = tramitador.get(f'/plantillas/{_id_plantilla(app)}/', follow_redirects=True)
    assert r.status_code == 200


def test_tramitador_puede_ver_detalle_usuario(tramitador, app):
    """TRAMITADOR puede ver el detalle de un usuario."""
    r = tramitador.get(f'/usuarios/{_id_usuario(app)}', follow_redirects=True)
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# TRAMITADOR — mutaciones de plantillas (debe ser 302 → perfil)
# ---------------------------------------------------------------------------

def test_tramitador_no_puede_crear_plantilla_get(tramitador):
    """TRAMITADOR no accede al formulario de nueva plantilla."""
    r = tramitador.get('/plantillas/nueva/', follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


def test_tramitador_no_puede_editar_plantilla(tramitador, app):
    """TRAMITADOR no accede al formulario de edición de plantilla."""
    r = tramitador.get(f'/plantillas/{_id_plantilla(app)}/editar', follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


def test_tramitador_no_puede_activar_plantilla(tramitador, app):
    """TRAMITADOR no puede activar/desactivar una plantilla."""
    r = tramitador.post(f'/plantillas/{_id_plantilla(app)}/activar', follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


# ---------------------------------------------------------------------------
# TRAMITADOR — mutaciones de usuarios
# ---------------------------------------------------------------------------

def test_tramitador_no_puede_crear_usuario(tramitador):
    """TRAMITADOR recibe 403 al intentar crear un usuario vía POST."""
    r = tramitador.post(
        '/usuarios/',
        data={'siglas': 'TST', 'nombre': 'Test', 'apellido1': 'Test',
              'password': 'x', 'confirm_password': 'x'},
        follow_redirects=False,
    )
    assert r.status_code == 403


def test_tramitador_no_puede_editar_usuario(tramitador, app):
    """TRAMITADOR no accede al formulario de edición de un usuario."""
    r = tramitador.get(f'/usuarios/{_id_usuario(app)}/editar', follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')



# ---------------------------------------------------------------------------
# SUPERVISOR — sin regresiones (acceso completo)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('ruta', [
    '/plantillas/',
    '/usuarios/',
])
def test_supervisor_sigue_accediendo(supervisor, ruta):
    """SUPERVISOR mantiene acceso de lectura sin regresiones."""
    r = supervisor.get(ruta, follow_redirects=True)
    assert r.status_code == 200, f'SUPERVISOR perdió acceso a {ruta}'


def test_supervisor_puede_crear_plantilla_get(supervisor):
    """SUPERVISOR accede al formulario de nueva plantilla."""
    r = supervisor.get('/plantillas/nueva/', follow_redirects=True)
    assert r.status_code == 200


def test_supervisor_puede_editar_usuario(supervisor, app):
    """SUPERVISOR accede al formulario de edición de un usuario."""
    r = supervisor.get(f'/usuarios/{_id_usuario(app)}/editar', follow_redirects=True)
    assert r.status_code == 200
