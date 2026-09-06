"""Smoke test — vista de login (/auth/login).

La vista es pública. El POST no: exige credenciales, y cuando el usuario tiene
más de un rol el login es de dos pasos —primero siglas y contraseña, después el
rol con el que se entra—.

Ese segundo paso no tenía test propio (#849). Se ejercitaba de rebote en las
fixtures de test_497 y test_498, que entraban como el usuario de la base de
desarrollo con su contraseña; en cualquier otra base se saltaban, así que en la
práctica no lo cubría nadie. Aquí se prueba a propósito, con los usuarios que
siembra `scripts/semilla_test.py` — que es también de dónde salen las
credenciales, para no tener dos copias de la misma contraseña.
"""
import pytest

from scripts.semilla_test import CONTRASENA, USUARIOS

# Un usuario con un solo rol y otro con tres, que son los dos caminos del login.
SIGLAS_UN_ROL = next(s for s, _, _, roles, activo in USUARIOS if len(roles) == 1 and activo)
SIGLAS_MULTIRROL = next(s for s, _, _, roles, activo in USUARIOS if len(roles) > 1 and activo)


def _usuario(siglas):
    from app.models.usuarios import Usuario
    u = Usuario.query.filter_by(siglas=siglas).first()
    assert u is not None, (
        f'la semilla debe traer el usuario {siglas!r} — '
        'ver scripts/semilla_test.py (#849, criterio 6)'
    )
    return u


def test_login_render(client):
    r = client.get('/auth/login')
    assert r.status_code == 200
    assert b'login' in r.data.lower()


def test_credenciales_malas_no_autentican(client, app_ctx):
    r = client.post('/auth/login',
                    data={'siglas': SIGLAS_UN_ROL, 'password': 'no-es-la-buena'},
                    follow_redirects=False)
    assert r.status_code == 200, 'un login fallido repinta el formulario, no redirige'
    with client.session_transaction() as sess:
        assert '_user_id' not in sess


def test_un_solo_rol_entra_de_una_vez(client, app_ctx):
    """Sin ambigüedad que resolver, el primer POST ya autentica."""
    u = _usuario(SIGLAS_UN_ROL)
    r = client.post('/auth/login',
                    data={'siglas': u.siglas, 'password': CONTRASENA},
                    follow_redirects=False)
    assert r.status_code == 302
    with client.session_transaction() as sess:
        assert sess.get('_user_id') == str(u.id)


def test_multirrol_pide_el_rol_en_un_segundo_paso(client, app_ctx):
    """Con varios roles, el primer POST devuelve la selección y no autentica aún."""
    u = _usuario(SIGLAS_MULTIRROL)
    roles = {r.nombre: r.id for r in u.roles}
    assert len(roles) > 1

    r1 = client.post('/auth/login',
                     data={'siglas': u.siglas, 'password': CONTRASENA},
                     follow_redirects=False)
    assert r1.status_code == 200, 'el multirrol debe recibir la pantalla de selección'

    nombre_rol, rol_id = sorted(roles.items())[0]
    r2 = client.post('/auth/login', data={'rol_id': str(rol_id)}, follow_redirects=False)
    assert r2.status_code == 302
    with client.session_transaction() as sess:
        assert sess.get('_user_id') == str(u.id)
        assert sess.get('rol_activo_nombre') == nombre_rol


def test_usuario_desactivado_no_entra(client, app_ctx):
    """Credenciales correctas, cuenta desactivada: vuelve al login sin sesión.

    Redirige (302) en vez de repintar como hace un fallo de credenciales — no
    es lo mismo equivocarse de contraseña que tener la cuenta cerrada.
    """
    siglas_inactivo = next((s for s, _, _, _, activo in USUARIOS if not activo), None)
    assert siglas_inactivo is not None, 'la semilla debe traer un usuario desactivado'

    r = client.post('/auth/login',
                    data={'siglas': siglas_inactivo, 'password': CONTRASENA},
                    follow_redirects=False)
    assert r.status_code == 302
    assert '/auth/login' in r.headers.get('Location', '')
    with client.session_transaction() as sess:
        assert '_user_id' not in sess
