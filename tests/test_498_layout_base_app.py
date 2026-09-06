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
def logged_in(usuario_supervisor):
    """Cliente autenticado con rol SUPERVISOR.

    Por rol y no como CLG con la contraseña de desarrollo (#849): así los
    dieciocho smoke de este fichero se ejecutan en cualquier base sembrada, en
    vez de saltarse. El formulario de login tiene su propio test en
    tests/smoke/test_smoke_login.py.
    """
    return usuario_supervisor


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
