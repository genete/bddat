"""
Tests #715 — `_check_finalizar_fase` y `_check_finalizar_tramite` contra SQL real.

Sustituyen al bloque D (mockeado) de `tests/test_296_senal_resultado.py`: allí
`db.session.query()` devolvía un `MagicMock` cuyo `.first()` respondía lo que se
le dijera — el `if` posterior se comprobaba, nunca el SQL (los JOIN, el filtro
por `TipoTarea.codigo`, el criterio de dominio). Aquí el árbol se monta de
verdad en BD (`arbol_esftt`, ver `tests/conftest.py`) y revierte por el
SAVEPOINT de `app_ctx`.

Cada función cubre dos motivos de bloqueo independientes:
  - Tarea incompleta: ANALIZAR/ELABORAR/NOTIFICAR sin documento PRODUCIDO.
  - NOTIFICAR con resultado INCORRECTA (#418), aunque tenga PRODUCIDO.
"""
import pytest


class TestCheckFinalizarFase:

    def test_tarea_sin_producido_bloquea(self, arbol_esftt):
        from app.services.invariantes_esftt import _check_finalizar_fase

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'ANALISIS_DOCUMENTAL')
        arbol_esftt.tarea(tramite, 'ANALIZAR')  # sin documento producido

        resultado = _check_finalizar_fase(fase.id)
        assert resultado is not None
        assert resultado.permitido is False

    def test_notificar_incorrecta_bloquea_aunque_tenga_producido(self, arbol_esftt):
        from app.services.invariantes_esftt import _check_finalizar_fase

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'NOTIFICACION')
        tarea = arbol_esftt.tarea(tramite, 'NOTIFICAR')
        doc = arbol_esftt.documento(fase.solicitud.expediente_id,
                                     'JUSTIFICANTE_NOTIFICA', f'{tarea.id}-notif')
        arbol_esftt.vincular(tarea, doc, 'PRODUCIDO')
        arbol_esftt.notificacion(tarea, resultado='INCORRECTA')

        resultado = _check_finalizar_fase(fase.id)
        assert resultado is not None
        assert resultado.permitido is False
        assert 'notificaci' in resultado.norma_compilada.lower()

    def test_todo_correcto_no_bloquea(self, arbol_esftt):
        from app.services.invariantes_esftt import _check_finalizar_fase

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'NOTIFICACION')
        tarea = arbol_esftt.tarea(tramite, 'NOTIFICAR')
        doc = arbol_esftt.documento(fase.solicitud.expediente_id,
                                     'JUSTIFICANTE_NOTIFICA', f'{tarea.id}-ok')
        arbol_esftt.vincular(tarea, doc, 'PRODUCIDO')
        arbol_esftt.notificacion(tarea, resultado='CORRECTA')

        assert _check_finalizar_fase(fase.id) is None

    def test_fase_sin_tramites_no_bloquea(self, arbol_esftt):
        """Fase recién creada, sin trámites: ninguna de las dos consultas encuentra fila."""
        from app.services.invariantes_esftt import _check_finalizar_fase

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        assert _check_finalizar_fase(fase.id) is None


class TestCheckFinalizarTramite:

    def test_tarea_sin_producido_bloquea(self, arbol_esftt):
        from app.services.invariantes_esftt import _check_finalizar_tramite

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'ELABORACION')
        arbol_esftt.tarea(tramite, 'ELABORAR')  # sin documento producido

        resultado = _check_finalizar_tramite(tramite.id)
        assert resultado is not None
        assert resultado.permitido is False

    def test_notificar_incorrecta_bloquea_aunque_tenga_producido(self, arbol_esftt):
        from app.services.invariantes_esftt import _check_finalizar_tramite

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'NOTIFICACION')
        tarea = arbol_esftt.tarea(tramite, 'NOTIFICAR')
        doc = arbol_esftt.documento(fase.solicitud.expediente_id,
                                     'JUSTIFICANTE_NOTIFICA', f'{tarea.id}-notif')
        arbol_esftt.vincular(tarea, doc, 'PRODUCIDO')
        arbol_esftt.notificacion(tarea, resultado='INCORRECTA')

        resultado = _check_finalizar_tramite(tramite.id)
        assert resultado is not None
        assert resultado.permitido is False
        assert 'notificaci' in resultado.norma_compilada.lower()

    def test_todo_correcto_no_bloquea(self, arbol_esftt):
        from app.services.invariantes_esftt import _check_finalizar_tramite

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'NOTIFICACION')
        tarea = arbol_esftt.tarea(tramite, 'NOTIFICAR')
        doc = arbol_esftt.documento(fase.solicitud.expediente_id,
                                     'JUSTIFICANTE_NOTIFICA', f'{tarea.id}-ok')
        arbol_esftt.vincular(tarea, doc, 'PRODUCIDO')
        arbol_esftt.notificacion(tarea, resultado='CORRECTA')

        assert _check_finalizar_tramite(tramite.id) is None

    def test_tramite_sin_tareas_no_bloquea(self, arbol_esftt):
        from app.services.invariantes_esftt import _check_finalizar_tramite

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'ELABORACION')
        assert _check_finalizar_tramite(tramite.id) is None
