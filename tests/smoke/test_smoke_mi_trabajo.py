"""Smoke de la vista "Mi trabajo" (#501 ADR-017, dispatcher puro desde #588 ADR-029).

Ruta role-adaptive, ahora dispatcher puro (ya no renderiza contenido propio):
  - ADMINISTRATIVO   → redirect a tareas_y_subidas.index.
  - SUPERVISOR/ADMIN → redirect a supervisor.index (Control y Gestión).
  - TRAMITADOR       → redirect al seguimiento (su "mi trabajo" actual).
"""


def test_mi_trabajo_administrativo_redirige_a_tareas_y_subidas(usuario_administrativo):
    r = usuario_administrativo.get('/mi_trabajo/', follow_redirects=False)
    assert r.status_code == 302
    assert '/tareas_y_subidas/' in r.headers.get('Location', '')


def test_mi_trabajo_tramitador_redirige_a_seguimiento(usuario_tramitador):
    r = usuario_tramitador.get('/mi_trabajo/', follow_redirects=False)
    assert r.status_code == 302
    assert '/expedientes/seguimiento' in r.headers.get('Location', '')


def test_destino_post_login_por_rol():
    """Redirección post-login (#501): a "Mi trabajo" salvo ADMIN (dashboard)."""
    from app.routes.auth import _destino_post_login
    assert _destino_post_login('ADMINISTRATIVO') == 'mi_trabajo.index'
    assert _destino_post_login('TRAMITADOR') == 'mi_trabajo.index'
    assert _destino_post_login('SUPERVISOR') == 'mi_trabajo.index'
    assert _destino_post_login('ADMIN') == 'dashboard.index'
