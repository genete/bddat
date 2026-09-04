"""#824 — la fecha administrativa nunca es futura.

Tres capas, tres bloques: el servicio que decide, el invariante del modelo que
lo aplica, y el reloj que define contra qué "hoy" se compara.

El bloque D cubre la ruta de edición del pool, que tuvo el fallo real: el
invariante lanzaba, su `except ValueError` de parseo se lo tragaba, y el
resultado era peor que no validar —la fecha del documento quedaba borrada y la
respuesta decía ok—. Se llama a la vista como función y no por HTTP para que el
SAVEPOINT de `app_ctx` revierta: el fixture `client` corre en la sesión real de
la app (#641) y dejaría documentos sueltos en la BD de desarrollo.
"""
from datetime import date, timedelta

import pytest
from flask_login import login_user

from app.services.fechas import fecha_administrativa_valida


# ---------------------------------------------------------------------------
# A) El servicio — sin contexto de aplicación, `hoy` explícito
# ---------------------------------------------------------------------------

class TestServicioFechaAdministrativaValida:

    HOY = date(2026, 9, 4)

    def test_none_es_valida(self):
        """NULL es un caso legítimo documentado: pool pendiente de revisión, o
        documento sin valor jurídico propio."""
        assert fecha_administrativa_valida(None, hoy=self.HOY) is True

    def test_pasada_es_valida(self):
        assert fecha_administrativa_valida(date(2025, 1, 15), hoy=self.HOY) is True

    def test_hoy_es_valida(self):
        """El día en curso es el caso normal: se registra lo que acaba de pasar."""
        assert fecha_administrativa_valida(self.HOY, hoy=self.HOY) is True

    def test_manana_no_es_valida(self):
        assert fecha_administrativa_valida(self.HOY + timedelta(days=1), hoy=self.HOY) is False

    def test_futura_lejana_no_es_valida(self):
        assert fecha_administrativa_valida(date(2027, 1, 1), hoy=self.HOY) is False


# ---------------------------------------------------------------------------
# B) El invariante del modelo — sin BD ni contexto (como test_574)
# ---------------------------------------------------------------------------

class TestInvarianteDocumento:
    """Sin app context, `hoy()` es la fecha de pared: estos tests no dependen
    del reloj de desarrollo ni de lo que haya en instance/."""

    def test_asignar_fecha_futura_lanza(self):
        from app.models.documentos import Documento

        with pytest.raises(ValueError, match='no puede ser futura'):
            Documento(fecha_administrativa=date.today() + timedelta(days=1))

    def test_asignar_fecha_pasada_no_lanza(self):
        from app.models.documentos import Documento

        doc = Documento(fecha_administrativa=date.today() - timedelta(days=1))
        assert doc.fecha_administrativa == date.today() - timedelta(days=1)

    def test_asignar_none_no_lanza(self):
        from app.models.documentos import Documento

        doc = Documento(fecha_administrativa=None)
        assert doc.fecha_administrativa is None

    def test_no_hay_flag_que_lo_desactive(self):
        """Invariante, no regla de motor: la asignación posterior también pasa
        por el validador, no solo el constructor."""
        from app.models.documentos import Documento

        doc = Documento(fecha_administrativa=None)
        with pytest.raises(ValueError):
            doc.fecha_administrativa = date.today() + timedelta(days=365)


# ---------------------------------------------------------------------------
# C) Contra qué "hoy" se compara — reloj de desarrollo (#820)
# ---------------------------------------------------------------------------

class TestRelojDeDesarrollo:
    """El reloj se simula con monkeypatch, nunca escribiendo el fichero real:
    `instance/reloj_simulado.txt` es estado del entorno de quien desarrolla y un
    test no tiene por qué moverlo (ni dejarlo movido si falla a media ejecución).
    """

    def test_reloj_adelantado_hace_valida_una_fecha_futura_de_pared(self, app_ctx, monkeypatch):
        from app.services import reloj_simulado
        from app.models.documentos import Documento

        futura = date.today() + timedelta(days=30)
        monkeypatch.setattr(reloj_simulado, 'obtener', lambda: futura)
        app_ctx.config['DEBUG'] = True

        doc = Documento(fecha_administrativa=futura)
        assert doc.fecha_administrativa == futura

    def test_sin_debug_el_reloj_se_ignora(self, app_ctx, monkeypatch):
        """Doble candado: en producción DEBUG es False y el fichero, si
        existiera, no cambia nada."""
        from app.services import reloj_simulado
        from app.models.documentos import Documento

        futura = date.today() + timedelta(days=30)
        monkeypatch.setattr(reloj_simulado, 'obtener', lambda: futura)
        debug_original = app_ctx.config.get('DEBUG')
        app_ctx.config['DEBUG'] = False
        try:
            with pytest.raises(ValueError, match='no puede ser futura'):
                Documento(fecha_administrativa=futura)
        finally:
            app_ctx.config['DEBUG'] = debug_original

    def test_hoy_del_sistema_sin_reloj_es_la_fecha_real(self, app_ctx, monkeypatch):
        from app.services import reloj_simulado

        monkeypatch.setattr(reloj_simulado, 'obtener', lambda: None)
        assert reloj_simulado.hoy() == date.today()

    def test_motor_de_plazos_y_validacion_comparten_reloj(self, app_ctx, monkeypatch):
        """`plazos._hoy()` delega desde #824: si divergieran, un plazo podría
        vencer contra una fecha y el documento validarse contra otra."""
        from app.services import reloj_simulado
        from app.services.plazos import _hoy

        simulada = date.today() + timedelta(days=7)
        monkeypatch.setattr(reloj_simulado, 'obtener', lambda: simulada)
        app_ctx.config['DEBUG'] = True

        assert _hoy() == reloj_simulado.hoy() == simulada


# ---------------------------------------------------------------------------
# D) La ruta de edición del pool — regresión del borrado silencioso
# ---------------------------------------------------------------------------

def _usuario():
    from app.models.usuarios import Usuario
    usuario = Usuario.query.first()
    if usuario is None:
        pytest.skip('No hay usuarios en la BD de desarrollo')
    return usuario


def _hoy_del_sistema():
    """La fecha de trabajo, no la de pared.

    Estos tests corren con `app_ctx` (DEBUG=True), así que el reloj de desarrollo
    está activo y puede estar en cualquier fecha — el script de expedientes-tipo
    lo deja fijado donde termina el escenario. Medir desde `date.today()` haría
    que estos tests fallasen según dónde quedara el reloj, por una razón que no
    tiene nada que ver con lo que prueban. El bloque B sí usa la fecha de pared,
    y puede: corre sin contexto de aplicación, donde no hay reloj que leer.
    """
    from app.services.reloj_simulado import hoy
    return hoy()


def _documento_con_fecha(arbol, fecha):
    """Documento del primer expediente, con una fecha administrativa válida."""
    from app import db
    from app.models.expedientes import Expediente
    expediente = Expediente.query.first()
    if expediente is None:
        pytest.skip('No hay expedientes en la BD de desarrollo')
    doc = arbol.documento(expediente.id, 'MODELO_SOLICITUD', f'824-{fecha}')
    doc.fecha_administrativa = fecha
    db.session.flush()
    return expediente, doc


def _editar(app_ctx, expediente_id, doc_id, payload):
    """Llama a la vista como función, dentro del SAVEPOINT de app_ctx.

    Por HTTP el commit de la vista escaparía a la BD de desarrollo (#641). Aquí
    `db.session` es la sesión con SAVEPOINT y todo revierte al terminar.
    """
    from flask import session
    from app.modules.expedientes.routes import pool_editar_documento

    with app_ctx.test_request_context(json=payload):
        login_user(_usuario())
        session['rol_activo_nombre'] = 'SUPERVISOR'   # editar_expediente
        resultado = pool_editar_documento(expediente_id, doc_id)

    respuesta, codigo = resultado if isinstance(resultado, tuple) else (resultado, 200)
    return respuesta.get_json(), codigo


class TestRutaEdicionPool:

    def test_fecha_futura_ni_se_guarda_ni_se_da_por_buena(self, arbol_esftt, app_ctx):
        """Las dos aserciones importan, y la segunda es la que cazó el fallo: el
        `except ValueError` de parseo se tragaba el invariante, así que la ruta
        respondía ok y dejaba la fecha en NULL — un borrado silencioso."""
        hoy = _hoy_del_sistema()
        valida = hoy - timedelta(days=10)
        expediente, doc = _documento_con_fecha(arbol_esftt, valida)

        cuerpo, codigo = _editar(app_ctx, expediente.id, doc.id, {
            'fecha_administrativa': (hoy + timedelta(days=365)).isoformat(),
        })

        assert cuerpo['ok'] is False
        assert 'no puede ser futura' in cuerpo['error']
        assert doc.fecha_administrativa == valida

    def test_fecha_pasada_se_guarda(self, arbol_esftt, app_ctx):
        """El contraste: la ruta sigue haciendo su trabajo."""
        hoy = _hoy_del_sistema()
        expediente, doc = _documento_con_fecha(arbol_esftt, hoy - timedelta(days=10))
        nueva = hoy - timedelta(days=3)

        cuerpo, codigo = _editar(app_ctx, expediente.id, doc.id, {
            'fecha_administrativa': nueva.isoformat(),
        })

        assert cuerpo['ok'] is True
        assert doc.fecha_administrativa == nueva

    def test_formato_invalido_sigue_vaciando_la_fecha(self, arbol_esftt, app_ctx):
        """Comportamiento previo al issue, conservado a propósito: una fecha
        ilegible se ignora y el campo queda vacío, sin error. Lo que cambia es
        que la fecha *futura* ya no entra por esa puerta."""
        expediente, doc = _documento_con_fecha(
            arbol_esftt, _hoy_del_sistema() - timedelta(days=10))

        cuerpo, codigo = _editar(app_ctx, expediente.id, doc.id,
                                 {'fecha_administrativa': '32/13/2026'})

        assert cuerpo['ok'] is True
        assert doc.fecha_administrativa is None
