"""Smoke test — dashboard (/) y demo React (/demo/diagrama).

/demo/diagrama no requiere login y sirve como referencia de assert del shell
React (class="app-shell", <div id="app-root"), según nota de implementación #503.
"""


def test_dashboard_render(usuario_supervisor):
    r = usuario_supervisor.get('/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


def test_demo_diagrama_render(client):
    """Demo React — pública, sin login. Verifica shell React básico."""
    r = client.get('/demo/diagrama', follow_redirects=True)
    assert r.status_code == 200
    assert b'app-shell' in r.data or b'app-root' in r.data
