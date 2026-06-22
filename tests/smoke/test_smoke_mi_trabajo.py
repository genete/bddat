"""Smoke de la vista "Mi trabajo" (#501, ADR-017 / ADR-019).

Ruta role-adaptive:
  - ADMINISTRATIVO → isla React (cola + subir) sobre base_app.
  - resto de roles → redirect al seguimiento (su "mi trabajo" actual).
"""
import pytest


def test_mi_trabajo_admin_renderiza_shell(usuario_administrativo):
    r = usuario_administrativo.get('/mi_trabajo/')
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
    assert b'data-react-island="mi-trabajo"' in r.data


def test_mi_trabajo_tramitador_redirige_a_seguimiento(usuario_tramitador):
    r = usuario_tramitador.get('/mi_trabajo/', follow_redirects=False)
    assert r.status_code == 302
    assert '/expedientes/seguimiento' in r.headers.get('Location', '')


def test_inspector_cola_fragmento(usuario_administrativo, app):
    """El fragmento del inspector de la cola entrega el detalle + 'Ir a tramitar'."""
    with app.app_context():
        from app.models.tareas import Tarea
        t = Tarea.query.first()
        if t is None:
            pytest.skip('No hay tareas en la BD de desarrollo')
        tarea_id = t.id

    r = usuario_administrativo.get(f'/mi_trabajo/tarea/{tarea_id}/fragmento')
    assert r.status_code == 200
    assert 'Ir a tramitar'.encode('utf-8') in r.data


def test_destino_post_login_por_rol():
    """Redirección post-login (#501): a "Mi trabajo" salvo ADMIN (dashboard)."""
    from app.routes.auth import _destino_post_login
    assert _destino_post_login('ADMINISTRATIVO') == 'mi_trabajo.index'
    assert _destino_post_login('TRAMITADOR') == 'mi_trabajo.index'
    assert _destino_post_login('SUPERVISOR') == 'mi_trabajo.index'
    assert _destino_post_login('ADMIN') == 'dashboard.index'
