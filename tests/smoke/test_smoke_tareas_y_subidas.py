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


# ---------------------------------------------------------------------------
# Ayuda de recepción (#766) — regla de #764 sobre qué documento es el producido
# ---------------------------------------------------------------------------

def _primera_tarea_de_tipo(app, codigo):
    with app.app_context():
        from app.models.tareas import Tarea
        from app.models.tipos_tareas import TipoTarea
        t = (Tarea.query
             .join(TipoTarea, TipoTarea.id == Tarea.tipo_tarea_id)
             .filter(TipoTarea.codigo == codigo)
             .first())
        if t is None:
            pytest.skip(f'No hay tareas {codigo} en la BD de desarrollo')
        return t.id


def test_inspector_cola_ayuda_solo_en_esperar_plazo(usuario_administrativo, app):
    """La ayuda se muestra en ESPERAR_PLAZO —la única tarea cuyo producido es un
    documento recibido de fuera— y no en el resto."""
    from app.modules.tareas_y_subidas.routes import AYUDA_PRODUCIDO_ESPERAR_PLAZO
    marca = AYUDA_PRODUCIDO_ESPERAR_PLAZO[:60].encode('utf-8')

    plazo_id = _primera_tarea_de_tipo(app, 'ESPERAR_PLAZO')
    r = usuario_administrativo.get(f'/tareas_y_subidas/tarea/{plazo_id}/fragmento')
    assert r.status_code == 200
    assert marca in r.data

    elaborar_id = _primera_tarea_de_tipo(app, 'ELABORAR')
    r = usuario_administrativo.get(f'/tareas_y_subidas/tarea/{elaborar_id}/fragmento')
    assert r.status_code == 200
    assert marca not in r.data
