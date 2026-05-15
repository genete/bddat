"""
Tests issue #392 — Diagnostico.as_contexto_cb() y ContextoAnalisisDocumental.

Bloques:
  A) Diagnostico.as_contexto_cb()  — stubs, sin BD ni app context.
  B) ContextoAnalisisDocumental.get_contexto() — stubs.
"""
from unittest.mock import MagicMock


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _diagnostico(resultado='favorable', defectos=None):
    """Stub de Diagnostico con as_contexto_cb() delegando al método real."""
    from app.models.diagnosticos import Diagnostico
    d = MagicMock()
    d.resultado = resultado
    d.defectos = defectos if defectos is not None else []
    d.as_contexto_cb = lambda: Diagnostico.as_contexto_cb(d)
    return d


def _tarea_stub(codigo, doc_producido=None, tramite_id=1):
    t = MagicMock()
    t.tramite_id = tramite_id
    t.tipo_tarea = MagicMock(codigo=codigo)
    t.documento_producido = doc_producido
    return t


def _tramite_con_tareas(tareas):
    tr = MagicMock()
    tr.tareas = tareas
    return tr


def _doc(diagnostico=None):
    d = MagicMock()
    d.diagnostico = diagnostico
    return d


# ──────────────────────────────────────────────────────────────────────────────
# A) Diagnostico.as_contexto_cb()
# ──────────────────────────────────────────────────────────────────────────────

class TestAsContextoCb:

    def test_campos_completos(self):
        diag = _diagnostico(resultado='condicionado', defectos=[{'texto': 'Falta plano'}])
        ctx = diag.as_contexto_cb()
        assert ctx['diagnostico_resultado'] == 'condicionado'
        assert ctx['diagnostico_defectos'] == [{'texto': 'Falta plano'}]
        assert ctx['diagnostico_tiene_defectos'] is True

    def test_sin_defectos(self):
        diag = _diagnostico(resultado='favorable', defectos=[])
        ctx = diag.as_contexto_cb()
        assert ctx['diagnostico_tiene_defectos'] is False
        assert ctx['diagnostico_defectos'] == []

    def test_defectos_none_tratado_como_lista_vacia(self):
        diag = _diagnostico(resultado='favorable', defectos=None)
        ctx = diag.as_contexto_cb()
        assert ctx['diagnostico_tiene_defectos'] is False
        assert ctx['diagnostico_defectos'] == []

    def test_resultado_pasa_sin_transformacion(self):
        diag = _diagnostico(resultado='desfavorable')
        ctx = diag.as_contexto_cb()
        assert ctx['diagnostico_resultado'] == 'desfavorable'


# ──────────────────────────────────────────────────────────────────────────────
# B) ContextoAnalisisDocumental.get_contexto()
# ──────────────────────────────────────────────────────────────────────────────

class TestContextoAnalisisDocumental:

    def test_sin_tarea_devuelve_vacio(self):
        from app.services.context_builders.analisis_documental import ContextoAnalisisDocumental
        cb = ContextoAnalisisDocumental(MagicMock(), MagicMock(), tarea=None)
        assert cb.get_contexto() == {}

    def test_sin_tarea_analizar_devuelve_vacio(self):
        from app.services.context_builders.analisis_documental import ContextoAnalisisDocumental
        tarea_elab = _tarea_stub('ELABORAR', tramite_id=1)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab])
        cb = ContextoAnalisisDocumental(MagicMock(), MagicMock(), tarea=tarea_elab)
        assert cb.get_contexto() == {}

    def test_analizar_sin_documento_producido_devuelve_vacio(self):
        from app.services.context_builders.analisis_documental import ContextoAnalisisDocumental
        tarea_anal = _tarea_stub('ANALIZAR', doc_producido=None, tramite_id=1)
        tarea_elab = _tarea_stub('ELABORAR', tramite_id=1)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab, tarea_anal])
        cb = ContextoAnalisisDocumental(MagicMock(), MagicMock(), tarea=tarea_elab)
        assert cb.get_contexto() == {}

    def test_con_diagnostico_completo_campos_correctos(self):
        from app.services.context_builders.analisis_documental import ContextoAnalisisDocumental
        diag = _diagnostico(resultado='condicionado', defectos=[{'texto': 'Falta memoria'}])
        doc = _doc(diagnostico=diag)
        tarea_anal = _tarea_stub('ANALIZAR', doc_producido=doc, tramite_id=1)
        tarea_elab = _tarea_stub('ELABORAR', tramite_id=1)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab, tarea_anal])
        cb = ContextoAnalisisDocumental(MagicMock(), MagicMock(), tarea=tarea_elab)
        ctx = cb.get_contexto()
        assert ctx['diagnostico_resultado'] == 'condicionado'
        assert ctx['diagnostico_defectos'] == [{'texto': 'Falta memoria'}]
        assert ctx['diagnostico_tiene_defectos'] is True
