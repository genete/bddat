"""Smoke tests del layout único base_app.html (ADR-014 / Issue #498).

Verifica que las vistas autenticadas:
  1. Devuelven HTTP 200.
  2. Renderizan el shell nuevo (.app-topbar y .app-sidebar).
  3. Ya no incluyen el shell viejo (.app-header de v2-layout).

Si esta convención se mantiene en futuras vistas (ADR-019), añadir aquí
la nueva ruta y su comprobación de 200.
"""
import pytest


RUTAS_SMOKE = [
    '/',                       # dashboard.index
    '/expedientes/',           # listado V2
    '/entidades/',             # listado V2
    '/plantillas/',            # listado admin
    '/usuarios/',              # listado admin
    '/perfil/',                # detalle propio
]


@pytest.fixture
def logged_in(client):
    """Hace login como CLG con rol SUPERVISOR.

    Asume que el usuario CLG existe en la BD de desarrollo (seed
    estándar del proyecto). Si no, todos los smoke tests se saltan.
    """
    # Primera pasada: validar credenciales
    r1 = client.post('/auth/login',
                     data={'siglas': 'CLG', 'password': '31416'},
                     follow_redirects=False)
    if r1.status_code not in (200, 302):
        pytest.skip(f'Login de smoke no disponible (status {r1.status_code})')

    if r1.status_code == 200:
        # Segunda pasada: el usuario tiene varios roles → elegir SUPERVISOR
        from app.models.usuarios import Usuario, Rol
        u = Usuario.query.filter_by(siglas='CLG').first()
        if u is None:
            pytest.skip('Usuario CLG no presente en la BD')
        rol_super = next((r for r in u.roles if r.nombre == 'SUPERVISOR'), None)
        if rol_super is None:
            pytest.skip('CLG no tiene rol SUPERVISOR en la BD')
        r2 = client.post('/auth/login',
                         data={'rol_id': str(rol_super.id)},
                         follow_redirects=False)
        assert r2.status_code in (200, 302), f'Segunda pasada de login devolvió {r2.status_code}'

    return client


@pytest.mark.parametrize('ruta', RUTAS_SMOKE)
def test_ruta_devuelve_200(logged_in, ruta):
    """Cada ruta smoke responde 200 (o 302 redirigible) tras login."""
    r = logged_in.get(ruta, follow_redirects=True)
    assert r.status_code == 200, f'{ruta} devolvió {r.status_code}'


@pytest.mark.parametrize('ruta', RUTAS_SMOKE)
def test_ruta_renderiza_shell_nuevo(logged_in, ruta):
    """Cada ruta smoke contiene la marca de las áreas obligatorias del shell
    (ADR-014): topbar, sidebar, main, footer."""
    html = logged_in.get(ruta, follow_redirects=True).get_data(as_text=True)
    assert 'class="app-topbar"' in html, f'{ruta} no contiene .app-topbar'
    assert 'class="app-sidebar"'  in html, f'{ruta} no contiene .app-sidebar'
    assert 'class="app-main"'     in html, f'{ruta} no contiene .app-main'
    assert 'class="app-footer"'   in html, f'{ruta} no contiene .app-footer'


@pytest.mark.parametrize('ruta', RUTAS_SMOKE)
def test_ruta_no_incluye_shell_viejo(logged_in, ruta):
    """Garantiza que las vistas ya no usan el chrome v2 (app-header con
    breadcrumb-row y module-nav). Marcador de que la migración a base_app
    es completa para esa ruta."""
    html = logged_in.get(ruta, follow_redirects=True).get_data(as_text=True)
    assert 'header-nav-row'        not in html, f'{ruta} todavía pinta header-nav-row del shell viejo'
    assert 'header-breadcrumb-row' not in html, f'{ruta} todavía pinta breadcrumb-row del shell viejo'
