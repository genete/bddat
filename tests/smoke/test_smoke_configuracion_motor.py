"""Smoke de "Configuración del motor" (#479, ADR-028 bloque Gestión).

Selector de modo global (BLOQUEAR/SOLO_ADVERTIR/INACTIVO). El resto de la
página (reglas del motor, #170) es solo un aviso de "próximamente".
"""
from app import db
from app.models.configuracion_sistema import ConfiguracionSistema
from app.services.motor_modo_global import CLAVE_MODO


def test_configuracion_motor_renderiza_shell(usuario_supervisor):
    r = usuario_supervisor.get('/configuracion-motor/')
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
    assert b'Modo global del motor' in r.data


def test_configuracion_motor_accesible_a_tramitador_solo_lectura(usuario_tramitador):
    """acceder_reglas_motor incluye TRAMITADOR — ve el modo, no el formulario habilitado."""
    r = usuario_tramitador.get('/configuracion-motor/')
    assert r.status_code == 200
    assert b'disabled' in r.data


def test_guardar_modo_denegado_a_tramitador(usuario_tramitador, app):
    with app.app_context():
        modo_previo = ConfiguracionSistema.get(CLAVE_MODO, 'BLOQUEAR')
    r = usuario_tramitador.post('/configuracion-motor/modo-global',
                                data={'modo': 'INACTIVO'}, follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')
    with app.app_context():
        assert ConfiguracionSistema.get(CLAVE_MODO, 'BLOQUEAR') == modo_previo


def test_guardar_modo_supervisor_y_restaura(usuario_supervisor, app):
    """SUPERVISOR puede cambiar el modo — se restaura el valor previo al terminar."""
    with app.app_context():
        modo_previo = ConfiguracionSistema.get(CLAVE_MODO, 'BLOQUEAR')
    nuevo = 'SOLO_ADVERTIR' if modo_previo != 'SOLO_ADVERTIR' else 'INACTIVO'
    try:
        r = usuario_supervisor.post('/configuracion-motor/modo-global',
                                    data={'modo': nuevo}, follow_redirects=True)
        assert r.status_code == 200
        with app.app_context():
            assert ConfiguracionSistema.get(CLAVE_MODO) == nuevo
    finally:
        with app.app_context():
            ConfiguracionSistema.set(CLAVE_MODO, modo_previo)
            db.session.commit()
