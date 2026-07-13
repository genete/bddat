"""Smoke tests de acceso por rol a áreas admin (ADR-013 / #503).

Cubre ADMINISTRATIVO específicamente, complementando los tests de TRAMITADOR
ya existentes en tests/test_497_permisos_blandos.py.

ADMINISTRATIVO tiene 'acceder_plantillas' y 'acceder_usuarios'
pero NO 'gestionar_plantillas' ni 'gestionar_usuarios'.
"""


# ---------------------------------------------------------------------------
# ADMINISTRATIVO — acceso en lectura (debe ser 200)
# ---------------------------------------------------------------------------

def test_administrativo_puede_ver_plantillas(usuario_administrativo):
    r = usuario_administrativo.get('/plantillas/', follow_redirects=True)
    assert r.status_code == 200, f'ADMINISTRATIVO no puede leer /plantillas/ (status {r.status_code})'


def test_administrativo_puede_ver_usuarios(usuario_administrativo):
    r = usuario_administrativo.get('/usuarios/', follow_redirects=True)
    assert r.status_code == 200, f'ADMINISTRATIVO no puede leer /usuarios/ (status {r.status_code})'


# ---------------------------------------------------------------------------
# ADMINISTRATIVO — mutaciones bloqueadas (deben devolver 302 → /perfil)
# ---------------------------------------------------------------------------

def test_administrativo_no_puede_crear_plantilla(usuario_administrativo):
    r = usuario_administrativo.get('/plantillas/nueva/', follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


def test_administrativo_no_puede_editar_plantilla(usuario_administrativo, plantilla_seed):
    r = usuario_administrativo.get(f'/plantillas/{plantilla_seed}/editar', follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


def test_administrativo_no_puede_editar_usuario(usuario_administrativo, primer_usuario_id):
    r = usuario_administrativo.get(f'/usuarios/{primer_usuario_id}/editar', follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')
