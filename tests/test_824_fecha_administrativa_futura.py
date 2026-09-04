"""#824 — la fecha administrativa nunca es futura.

Tres capas, tres bloques: el servicio que decide, el invariante del modelo que
lo aplica, y el reloj que define contra qué "hoy" se compara.

No hay test de las rutas del pool a propósito: escriben por el mismo setter que
prueba el bloque B, y un test con cliente HTTP no revierte (deja documentos
sueltos en la BD de desarrollo) a cambio de no cubrir ninguna lógica nueva.
"""
from datetime import date, timedelta

import pytest

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
