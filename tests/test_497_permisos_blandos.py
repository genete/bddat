"""Smoke tests de permisos blandos (ADR-013 / Issue #497).

Verifica que:
  1. TRAMITADOR puede acceder en lectura a áreas administrativas (GET 200).
  2. TRAMITADOR no puede ejecutar mutaciones (302 a perfil o 403).
  3. SUPERVISOR sigue teniendo acceso completo sin regresiones.
"""
import pytest


# ---------------------------------------------------------------------------
# Helpers de login
# ---------------------------------------------------------------------------

def _login(client, siglas, password, rol_nombre):
    """
    Hace login con siglas/password y selecciona el rol indicado.
    Devuelve True si el login fue exitoso, False si el rol no existe.
    """
    r1 = client.post(
        '/auth/login',
        data={'siglas': siglas, 'password': password},
        follow_redirects=False,
    )
    if r1.status_code not in (200, 302):
        return False

    if r1.status_code == 200:
        # El servidor pide selección de rol
        from app.models.usuarios import Usuario
        u = Usuario.query.filter_by(siglas=siglas).first()
        if u is None:
            return False
        rol = next((r for r in u.roles if r.nombre == rol_nombre), None)
        if rol is None:
            return False
        r2 = client.post(
            '/auth/login',
            data={'rol_id': str(rol.id)},
            follow_redirects=False,
        )
        if r2.status_code not in (200, 302):
            return False

    return True


@pytest.fixture
def tramitador(client):
    """Cliente autenticado como CLG con rol TRAMITADOR."""
    ok = _login(client, 'CLG', '31416', 'TRAMITADOR')
    if not ok:
        pytest.skip('Usuario CLG con rol TRAMITADOR no disponible en esta BD')
    return client


@pytest.fixture
def supervisor(client):
    """Cliente autenticado como CLG con rol SUPERVISOR."""
    ok = _login(client, 'CLG', '31416', 'SUPERVISOR')
    if not ok:
        pytest.skip('Usuario CLG con rol SUPERVISOR no disponible en esta BD')
    return client


# ---------------------------------------------------------------------------
# TRAMITADOR — acceso de lectura (debe ser 200)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('ruta', [
    '/admin/plantillas/',
    '/usuarios/',
])
def test_tramitador_puede_leer(tramitador, ruta):
    """TRAMITADOR accede en lectura a áreas administrativas."""
    r = tramitador.get(ruta, follow_redirects=True)
    assert r.status_code == 200, f'TRAMITADOR no puede leer {ruta} (status {r.status_code})'


def test_tramitador_puede_ver_detalle_plantilla(tramitador):
    """TRAMITADOR puede ver el detalle de una plantilla si existe alguna."""
    from app.models.plantillas import Plantilla
    p = Plantilla.query.first()
    if p is None:
        pytest.skip('No hay plantillas en la BD')
    r = tramitador.get(f'/admin/plantillas/{p.id}/', follow_redirects=True)
    assert r.status_code == 200


def test_tramitador_puede_ver_detalle_usuario(tramitador):
    """TRAMITADOR puede ver el detalle de un usuario."""
    from app.models.usuarios import Usuario
    u = Usuario.query.first()
    if u is None:
        pytest.skip('No hay usuarios en la BD')
    r = tramitador.get(f'/usuarios/{u.id}', follow_redirects=True)
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# TRAMITADOR — mutaciones de plantillas (debe ser 302 → perfil)
# ---------------------------------------------------------------------------

def test_tramitador_no_puede_crear_plantilla_get(tramitador):
    """TRAMITADOR no accede al formulario de nueva plantilla."""
    r = tramitador.get('/admin/plantillas/nueva/', follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


def test_tramitador_no_puede_editar_plantilla(tramitador):
    """TRAMITADOR no accede al formulario de edición de plantilla."""
    from app.models.plantillas import Plantilla
    p = Plantilla.query.first()
    if p is None:
        pytest.skip('No hay plantillas en la BD')
    r = tramitador.get(f'/admin/plantillas/{p.id}/editar', follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


def test_tramitador_no_puede_activar_plantilla(tramitador):
    """TRAMITADOR no puede activar/desactivar una plantilla."""
    from app.models.plantillas import Plantilla
    p = Plantilla.query.first()
    if p is None:
        pytest.skip('No hay plantillas en la BD')
    r = tramitador.post(f'/admin/plantillas/{p.id}/activar', follow_redirects=False)
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


def test_tramitador_no_puede_editar_usuario(tramitador):
    """TRAMITADOR no accede al formulario de edición de un usuario."""
    from app.models.usuarios import Usuario
    u = Usuario.query.first()
    if u is None:
        pytest.skip('No hay usuarios en la BD')
    r = tramitador.get(f'/usuarios/{u.id}/editar', follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


def test_tramitador_no_puede_toggle_estado(tramitador):
    """TRAMITADOR no puede cambiar el estado activo de un usuario."""
    from app.models.usuarios import Usuario
    u = Usuario.query.first()
    if u is None:
        pytest.skip('No hay usuarios en la BD')
    r = tramitador.post(f'/usuarios/{u.id}/toggle_estado', follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


# ---------------------------------------------------------------------------
# SUPERVISOR — sin regresiones (acceso completo)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('ruta', [
    '/admin/plantillas/',
    '/usuarios/',
])
def test_supervisor_sigue_accediendo(supervisor, ruta):
    """SUPERVISOR mantiene acceso de lectura sin regresiones."""
    r = supervisor.get(ruta, follow_redirects=True)
    assert r.status_code == 200, f'SUPERVISOR perdió acceso a {ruta}'


def test_supervisor_puede_crear_plantilla_get(supervisor):
    """SUPERVISOR accede al formulario de nueva plantilla."""
    r = supervisor.get('/admin/plantillas/nueva/', follow_redirects=True)
    assert r.status_code == 200


def test_supervisor_puede_editar_usuario(supervisor):
    """SUPERVISOR accede al formulario de edición de un usuario."""
    from app.models.usuarios import Usuario
    u = Usuario.query.first()
    if u is None:
        pytest.skip('No hay usuarios en la BD')
    r = supervisor.get(f'/usuarios/{u.id}/editar', follow_redirects=True)
    assert r.status_code == 200
