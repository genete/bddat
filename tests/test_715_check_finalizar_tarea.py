"""
Tests #715 — `_check_finalizar_tarea`, sin cobertura hasta ahora.

Dos requisitos independientes por tipo de tarea (`app/services/invariantes_esftt.py`):
  - `_TIPOS_REQUIEREN_DOC_PRODUCIDO` = {ANALIZAR, ELABORAR, NOTIFICAR}: exige
    documento producido (tarea.ejecutada).
  - `_TIPOS_REQUIEREN_DOC_USADO` = {ANALIZAR, NOTIFICAR}: exige al menos un
    documento consumido. ELABORAR queda fuera — no bloquea por falta de entrada.

Árbol montado con SQL real vía `arbol_esftt` (ver `tests/conftest.py`).
"""
import pytest


def _tarea_con_entrada(arbol_esftt, tarea, expediente_id):
    """Vincula un documento CONSUMIDO cualquiera a `tarea` (documento de entrada)."""
    doc = arbol_esftt.documento(expediente_id, 'DIAGNOSTICO', f'{tarea.id}-entrada')
    arbol_esftt.vincular(tarea, doc, 'CONSUMIDO')


def _tarea_con_salida(arbol_esftt, tarea, expediente_id):
    """Vincula un documento PRODUCIDO a `tarea` (documento de salida)."""
    doc = arbol_esftt.documento(expediente_id, 'DIAGNOSTICO', f'{tarea.id}-salida')
    arbol_esftt.vincular(tarea, doc, 'PRODUCIDO')


class TestAnalizar:

    def test_sin_nada_bloquea_por_producido(self, arbol_esftt):
        from app.services.invariantes_esftt import _check_finalizar_tarea

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'ANALISIS_DOCUMENTAL')
        tarea = arbol_esftt.tarea(tramite, 'ANALIZAR')

        resultado = _check_finalizar_tarea(tarea.id)
        assert resultado is not None
        assert resultado.permitido is False

    def test_con_producido_sin_consumido_bloquea_por_entrada(self, arbol_esftt):
        from app.services.invariantes_esftt import _check_finalizar_tarea

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'ANALISIS_DOCUMENTAL')
        tarea = arbol_esftt.tarea(tramite, 'ANALIZAR')
        _tarea_con_salida(arbol_esftt, tarea, fase.solicitud.expediente_id)

        resultado = _check_finalizar_tarea(tarea.id)
        assert resultado is not None
        assert resultado.permitido is False

    def test_con_producido_y_consumido_no_bloquea(self, arbol_esftt):
        from app.services.invariantes_esftt import _check_finalizar_tarea

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'ANALISIS_DOCUMENTAL')
        tarea = arbol_esftt.tarea(tramite, 'ANALIZAR')
        _tarea_con_entrada(arbol_esftt, tarea, fase.solicitud.expediente_id)
        _tarea_con_salida(arbol_esftt, tarea, fase.solicitud.expediente_id)

        assert _check_finalizar_tarea(tarea.id) is None


class TestElaborar:

    def test_sin_producido_bloquea(self, arbol_esftt):
        from app.services.invariantes_esftt import _check_finalizar_tarea

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'ELABORACION')
        tarea = arbol_esftt.tarea(tramite, 'ELABORAR')

        resultado = _check_finalizar_tarea(tarea.id)
        assert resultado is not None
        assert resultado.permitido is False

    def test_con_producido_sin_consumido_no_bloquea(self, arbol_esftt):
        """ELABORAR no está en _TIPOS_REQUIEREN_DOC_USADO: no exige entrada."""
        from app.services.invariantes_esftt import _check_finalizar_tarea

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'ELABORACION')
        tarea = arbol_esftt.tarea(tramite, 'ELABORAR')
        _tarea_con_salida(arbol_esftt, tarea, fase.solicitud.expediente_id)

        assert _check_finalizar_tarea(tarea.id) is None


class TestNotificar:

    def test_sin_nada_bloquea_por_producido(self, arbol_esftt):
        from app.services.invariantes_esftt import _check_finalizar_tarea

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'NOTIFICACION')
        tarea = arbol_esftt.tarea(tramite, 'NOTIFICAR')

        resultado = _check_finalizar_tarea(tarea.id)
        assert resultado is not None
        assert resultado.permitido is False

    def test_con_producido_sin_consumido_bloquea_por_entrada(self, arbol_esftt):
        from app.services.invariantes_esftt import _check_finalizar_tarea

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'NOTIFICACION')
        tarea = arbol_esftt.tarea(tramite, 'NOTIFICAR')
        _tarea_con_salida(arbol_esftt, tarea, fase.solicitud.expediente_id)

        resultado = _check_finalizar_tarea(tarea.id)
        assert resultado is not None
        assert resultado.permitido is False

    def test_con_producido_y_consumido_no_bloquea(self, arbol_esftt):
        from app.services.invariantes_esftt import _check_finalizar_tarea

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'NOTIFICACION')
        tarea = arbol_esftt.tarea(tramite, 'NOTIFICAR')
        _tarea_con_entrada(arbol_esftt, tarea, fase.solicitud.expediente_id)
        _tarea_con_salida(arbol_esftt, tarea, fase.solicitud.expediente_id)

        assert _check_finalizar_tarea(tarea.id) is None


class TestEsperarPlazo:

    def test_sin_nada_no_bloquea(self, arbol_esftt):
        """ESPERAR_PLAZO no está en ninguno de los dos conjuntos: nunca bloquea aquí."""
        from app.services.invariantes_esftt import _check_finalizar_tarea

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'ANALISIS_DOCUMENTAL')
        tarea = arbol_esftt.tarea(tramite, 'ESPERAR_PLAZO')

        assert _check_finalizar_tarea(tarea.id) is None


class TestTareaInexistente:

    def test_id_inexistente_no_bloquea(self, app_ctx):
        from app.services.invariantes_esftt import _check_finalizar_tarea

        assert _check_finalizar_tarea(999_999_999) is None
