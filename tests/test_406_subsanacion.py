"""
Tests issue #406 — ContextoSubsanacion.

Bloque único: get_contexto() con stubs, sin BD ni app context.
"""
from unittest.mock import MagicMock


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _req(texto, orden):
    r = MagicMock()
    r.texto = texto
    r.orden = orden
    return r


def _tarea_con_requerimientos(reqs):
    t = MagicMock()
    t.requerimientos = reqs
    return t


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

    def test_sin_requerimientos_devuelve_lista_vacia(self):
        tarea = _tarea_con_requerimientos([])
        ctx = _cb(tarea).get_contexto()
        assert ctx['requerimientos'] == []

    def test_un_requerimiento_texto_libre(self):
        req = _req('Falta la memoria descriptiva del proyecto.', orden=1)
        tarea = _tarea_con_requerimientos([req])

        ctx = _cb(tarea).get_contexto()

        assert len(ctx['requerimientos']) == 1
        assert ctx['requerimientos'][0] == {
            'texto': 'Falta la memoria descriptiva del proyecto.',
            'orden': 1,
        }

    def test_varios_requerimientos_orden_preservado(self):
        reqs = [
            _req('Deficiencia técnica en el cálculo de cortocircuito.', orden=1),
            _req('Falta presupuesto desglosado por partidas.', orden=2),
            _req('Tasas pendientes de justificación.', orden=3),
        ]
        tarea = _tarea_con_requerimientos(reqs)

        ctx = _cb(tarea).get_contexto()

        assert len(ctx['requerimientos']) == 3
        assert ctx['requerimientos'][0]['orden'] == 1
        assert ctx['requerimientos'][1]['orden'] == 2
        assert ctx['requerimientos'][2]['orden'] == 3

    def test_texto_viene_de_property_del_modelo(self):
        """El CB usa r.texto, que en RequerimientoTarea resuelve catálogo o texto libre."""
        req_catalogo = _req('Texto resuelto desde catálogo.', orden=1)
        tarea = _tarea_con_requerimientos([req_catalogo])

        ctx = _cb(tarea).get_contexto()

        assert ctx['requerimientos'][0]['texto'] == 'Texto resuelto desde catálogo.'
