"""
Tests issue #406 — ContextoSubsanacion.

Reescrito en #440: el CB deja de leer `tarea.requerimientos` (borrador del
shuttle) y pasa a leer el Diagnostico del trámite ANTERIOR en la misma fase
(ANÁLISIS_DOCUMENTAL en primera vuelta; un REQUERIMIENTO_SUBSANACIÓN previo
en vueltas posteriores). Ver ADR-025 §4 y [[project_diseno_tarea_analizar_442]].

Bloque único: get_contexto() con stubs, sin BD ni app context.
"""
from unittest.mock import MagicMock


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _tarea_analizar_con_diagnostico(defectos):
    """Tarea ANALIZAR de un trámite previo, con documento_producido -> diagnostico."""
    tarea = MagicMock()
    tarea.tipo_tarea.codigo = 'ANALIZAR'
    diag = MagicMock()
    diag.as_contexto_cb.return_value = {'diagnostico_defectos': defectos}
    doc = MagicMock()
    doc.diagnostico = diag
    tarea.documento_producido = doc
    return tarea


def _tramite(id_, tareas=None):
    t = MagicMock()
    t.id = id_
    t.tareas = tareas or []
    return t


def _tarea_elaborar(tramite_actual_id, tramites_de_la_fase):
    """Tarea de ELABORAR (self._tarea) cuyo tramite.fase.tramites es la lista dada."""
    tramite_actual = MagicMock()
    tramite_actual.id = tramite_actual_id
    fase = MagicMock()
    fase.tramites = tramites_de_la_fase
    tramite_actual.fase = fase
    tarea = MagicMock()
    tarea.tramite = tramite_actual
    return tarea


def _cb(tarea):
    from app.services.context_builders.contexto_subsanacion import ContextoSubsanacion
    return ContextoSubsanacion(MagicMock(), MagicMock(), tarea=tarea)


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestContextoSubsanacion:

    def test_sin_tarea_devuelve_vacio(self):
        from app.services.context_builders.contexto_subsanacion import ContextoSubsanacion
        cb = ContextoSubsanacion(MagicMock(), MagicMock(), tarea=None)
        assert cb.get_contexto() == {}

    def test_sin_tramite_previo_devuelve_vacio(self):
        """Primer trámite de la fase (id más bajo) — no hay nada anterior que leer."""
        tramite_actual = _tramite(10)
        tarea = _tarea_elaborar(10, [tramite_actual])
        assert _cb(tarea).get_contexto() == {}

    def test_tramite_previo_sin_tarea_analizar_devuelve_vacio(self):
        tramite_previo = _tramite(10, tareas=[])
        tramite_actual = _tramite(20)
        tarea = _tarea_elaborar(20, [tramite_previo, tramite_actual])
        assert _cb(tarea).get_contexto() == {}

    def test_tramite_previo_sin_documento_producido_devuelve_vacio(self):
        tarea_analizar = MagicMock()
        tarea_analizar.tipo_tarea.codigo = 'ANALIZAR'
        tarea_analizar.documento_producido = None
        tramite_previo = _tramite(10, tareas=[tarea_analizar])
        tramite_actual = _tramite(20)
        tarea = _tarea_elaborar(20, [tramite_previo, tramite_actual])
        assert _cb(tarea).get_contexto() == {}

    def test_un_defecto(self):
        tarea_analizar = _tarea_analizar_con_diagnostico(
            [{'texto': 'Falta la memoria descriptiva del proyecto.', 'origen': 'documental', 'tarea_id': 1}]
        )
        tramite_previo = _tramite(10, tareas=[tarea_analizar])
        tramite_actual = _tramite(20)
        tarea = _tarea_elaborar(20, [tramite_previo, tramite_actual])

        ctx = _cb(tarea).get_contexto()

        assert ctx['requerimientos'] == [
            {'texto': 'Falta la memoria descriptiva del proyecto.', 'orden': 1},
        ]

    def test_varios_defectos_orden_asignado_por_posicion(self):
        defectos = [
            {'texto': 'Deficiencia técnica en el cálculo de cortocircuito.', 'origen': 'tecnico', 'tarea_id': 1},
            {'texto': 'Falta presupuesto desglosado por partidas.', 'origen': 'documental', 'tarea_id': 1},
            {'texto': 'Tasas pendientes de justificación.', 'origen': 'requerimiento', 'tarea_id': 1},
        ]
        tarea_analizar = _tarea_analizar_con_diagnostico(defectos)
        tramite_previo = _tramite(10, tareas=[tarea_analizar])
        tramite_actual = _tramite(20)
        tarea = _tarea_elaborar(20, [tramite_previo, tramite_actual])

        ctx = _cb(tarea).get_contexto()

        assert len(ctx['requerimientos']) == 3
        assert ctx['requerimientos'][0]['orden'] == 1
        assert ctx['requerimientos'][1]['orden'] == 2
        assert ctx['requerimientos'][2]['orden'] == 3

    def test_toma_el_tramite_previo_mas_reciente(self):
        """Segunda vuelta de subsanación: debe leer el REQUERIMIENTO_SUBSANACION
        anterior (id más alto por debajo del actual), no el ANÁLISIS_DOCUMENTAL
        original (id más bajo)."""
        tarea_analizar_antigua = _tarea_analizar_con_diagnostico(
            [{'texto': 'Defecto de la primera vuelta.', 'origen': 'documental', 'tarea_id': 1}]
        )
        tarea_analizar_reciente = _tarea_analizar_con_diagnostico(
            [{'texto': 'Defecto de la segunda vuelta.', 'origen': 'documental', 'tarea_id': 2}]
        )
        tramite_analisis_documental = _tramite(10, tareas=[tarea_analizar_antigua])
        tramite_subsanacion_1 = _tramite(20, tareas=[tarea_analizar_reciente])
        tramite_subsanacion_2 = _tramite(30)  # trámite actual (ELABORAR)

        tarea = _tarea_elaborar(
            30, [tramite_analisis_documental, tramite_subsanacion_1, tramite_subsanacion_2]
        )

        ctx = _cb(tarea).get_contexto()

        assert ctx['requerimientos'] == [{'texto': 'Defecto de la segunda vuelta.', 'orden': 1}]
