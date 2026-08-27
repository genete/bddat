"""Tests del reloj de desarrollo (#820): doble candado DEBUG + fichero.

`app` es session-scoped (conftest.py) — cada test restaura `app.config['DEBUG']`
y usa monkeypatch sobre `app.instance_path` para no tocar el
`instance/reloj_simulado.txt` real de la máquina de desarrollo.

El CLI (`app.cli.reloj`) no se prueba contra `app.config['DEBUG']`: Flask
reescribe `current_app.debug` en cada `test_cli_runner().invoke()` según la
variable de entorno `FLASK_DEBUG` (`ScriptInfo.load_app()`), independiente
de `DevelopmentConfig`/`ProductionConfig` — el candado real solo se aplica
en `_hoy()` y en el blueprint web, que sí corren en el proceso del servidor.
"""
from datetime import date

from app.services import plazos, reloj_simulado


def test_hoy_usa_fecha_simulada_con_debug_true(app, tmp_path, monkeypatch):
    monkeypatch.setattr(app, 'instance_path', str(tmp_path))
    original_debug = app.config['DEBUG']
    app.config['DEBUG'] = True
    try:
        with app.app_context():
            fecha_simulada = date(2099, 1, 1)
            reloj_simulado.fijar(fecha_simulada)
            assert plazos._hoy() == fecha_simulada

            reloj_simulado.borrar()
            assert plazos._hoy() == date.today()
    finally:
        app.config['DEBUG'] = original_debug


def test_hoy_ignora_fichero_con_debug_false(app, tmp_path, monkeypatch):
    """Candado de producción: DEBUG=False ignora el reloj aunque el fichero exista."""
    monkeypatch.setattr(app, 'instance_path', str(tmp_path))
    original_debug = app.config['DEBUG']
    try:
        with app.app_context():
            reloj_simulado.fijar(date(2099, 1, 1))
            app.config['DEBUG'] = False
            assert plazos._hoy() == date.today()
    finally:
        app.config['DEBUG'] = original_debug


def test_cli_set_show_clear(app, tmp_path, monkeypatch):
    """Invocar `test_cli_runner()` reescribe app.debug (ver docstring del módulo) — restaurar."""
    monkeypatch.setattr(app, 'instance_path', str(tmp_path))
    original_debug = app.config['DEBUG']
    try:
        runner = app.test_cli_runner()

        resultado = runner.invoke(args=['reloj', 'set', '2026-09-15'])
        assert resultado.exit_code == 0
        assert '2026-09-15' in resultado.output

        resultado = runner.invoke(args=['reloj', 'show'])
        assert '2026-09-15' in resultado.output

        resultado = runner.invoke(args=['reloj', 'clear'])
        assert resultado.exit_code == 0

        resultado = runner.invoke(args=['reloj', 'show'])
        assert 'Sin reloj simulado' in resultado.output
    finally:
        app.config['DEBUG'] = original_debug


def test_cli_set_fecha_invalida(app, tmp_path, monkeypatch):
    monkeypatch.setattr(app, 'instance_path', str(tmp_path))
    original_debug = app.config['DEBUG']
    try:
        resultado = app.test_cli_runner().invoke(args=['reloj', 'set', 'no-es-una-fecha'])
        assert resultado.exit_code != 0
    finally:
        app.config['DEBUG'] = original_debug


def test_endpoint_web_404_si_debug_false(usuario_supervisor, app, tmp_path, monkeypatch):
    monkeypatch.setattr(app, 'instance_path', str(tmp_path))
    original_debug = app.config['DEBUG']
    app.config['DEBUG'] = False
    try:
        resp = usuario_supervisor.post('/dev/reloj/fijar', data={'fecha': '2026-09-15'})
        assert resp.status_code == 404
    finally:
        app.config['DEBUG'] = original_debug


def test_endpoint_web_fija_y_borra_con_debug_true(usuario_supervisor, app, tmp_path, monkeypatch):
    monkeypatch.setattr(app, 'instance_path', str(tmp_path))
    original_debug = app.config['DEBUG']
    app.config['DEBUG'] = True
    try:
        resp = usuario_supervisor.post('/dev/reloj/fijar', data={'fecha': '2026-09-15'})
        assert resp.status_code == 302
        with app.app_context():
            assert reloj_simulado.obtener() == date(2026, 9, 15)

        resp = usuario_supervisor.post('/dev/reloj/borrar')
        assert resp.status_code == 302
        with app.app_context():
            assert reloj_simulado.obtener() is None
    finally:
        app.config['DEBUG'] = original_debug


def test_endpoint_web_requiere_login(client, app, tmp_path, monkeypatch):
    monkeypatch.setattr(app, 'instance_path', str(tmp_path))
    original_debug = app.config['DEBUG']
    app.config['DEBUG'] = True
    try:
        resp = client.post('/dev/reloj/fijar', data={'fecha': '2026-09-15'})
        assert resp.status_code == 302
        assert '/auth/login' in resp.headers['Location']
    finally:
        app.config['DEBUG'] = original_debug
