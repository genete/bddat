"""Smoke de "Tareas y Subidas" (#501 ADR-017, extraído en #588 ADR-029).

Cola de tareas administrativas + subida de documentos al pool. Antes exclusivo
de ADMINISTRATIVO bajo mi_trabajo — ahora ruta propia y universal
(`acceder_tareas_y_subidas`, 4 roles; la escritura, `gestionar_tareas`, ya era
universal desde ADR-017 §6).
"""
import pytest


def test_tareas_y_subidas_renderiza_shell(usuario_administrativo):
    r = usuario_administrativo.get('/tareas_y_subidas/')
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
    assert b'data-react-island="mi-trabajo"' in r.data


def test_tareas_y_subidas_universal_4_roles(usuario_admin, usuario_supervisor,
                                             usuario_tramitador, usuario_administrativo):
    """ADR-029 §1: consulta diaria de cualquier rol → entrada propia universal."""
    for cliente in (usuario_admin, usuario_supervisor, usuario_tramitador, usuario_administrativo):
        r = cliente.get('/tareas_y_subidas/')
        assert r.status_code == 200


def test_inspector_cola_fragmento(usuario_administrativo, app):
    """El fragmento del inspector de la cola entrega el detalle + 'Ir a tramitar'."""
    with app.app_context():
        from app.models.tareas import Tarea
        t = Tarea.query.first()
        if t is None:
            pytest.skip('No hay tareas en la BD de desarrollo')
        tarea_id = t.id

    r = usuario_administrativo.get(f'/tareas_y_subidas/tarea/{tarea_id}/fragmento')
    assert r.status_code == 200
    assert 'Ir a tramitar'.encode('utf-8') in r.data
