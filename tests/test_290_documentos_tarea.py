"""
Tests issue #290 — tabla documentos_tarea (INCORPORAR multi-doc v5.5).

INCORPORAR eliminado en ADR-004 (#361). Los bloques A y B están skipped.
La tabla documentos_tarea está pendiente de decisión de diseño (issue derivado de #361).

Bloques conservados para historial:
  A) Propiedades Tarea.ejecutada / planificada — skipped (#361)
  B) Invariantes _check_finalizar_tarea — skipped (#361)
  C) API endpoints — eliminados (#361, endpoints ya no existen)
"""
import pytest
from unittest.mock import MagicMock, patch


# ═══════════════════════════════════════════════════════════════════════════════
# A) Propiedades Tarea.ejecutada / planificada
#    Se invoca directamente el fget de la property sobre un objeto stub,
#    evitando SQLAlchemy por completo.
# ═══════════════════════════════════════════════════════════════════════════════

class _StubTarea:
    """Stub mínimo que implementa los atributos que leen las properties."""
    def __init__(self, codigo, documentos_tarea=None,
                 doc_producido_id=None, doc_usado_id=None):
        self.tipo_tarea = MagicMock(codigo=codigo)
        self.documentos_tarea = documentos_tarea or []
        self.documento_producido_id = doc_producido_id
        self.documento_usado_id = doc_usado_id


def _ejecutada(stub):
    from app.models.tareas import Tarea
    return Tarea.ejecutada.fget(stub)


def _planificada(stub):
    from app.models.tareas import Tarea
    return Tarea.planificada.fget(stub)


def _en_curso(stub):
    # en_curso depende de planificada y ejecutada; se resuelven explícitamente
    return not _planificada(stub) and not _ejecutada(stub)


@pytest.mark.skip(reason="#370 — INCORPORAR eliminado")
class TestTareaEjecutadaIncorporar:

    def test_incorporar_sin_docs_no_ejecutada(self):
        t = _StubTarea('INCORPORAR', documentos_tarea=[])
        assert _ejecutada(t) is False

    def test_incorporar_con_un_doc_ejecutada(self):
        t = _StubTarea('INCORPORAR', documentos_tarea=[MagicMock()])
        assert _ejecutada(t) is True

    def test_incorporar_con_varios_docs_ejecutada(self):
        t = _StubTarea('INCORPORAR', documentos_tarea=[MagicMock(), MagicMock()])
        assert _ejecutada(t) is True

    def test_incorporar_sin_docs_planificada(self):
        t = _StubTarea('INCORPORAR', documentos_tarea=[])
        assert _planificada(t) is True

    def test_incorporar_con_doc_no_planificada(self):
        t = _StubTarea('INCORPORAR', documentos_tarea=[MagicMock()])
        assert _planificada(t) is False

    def test_incorporar_en_curso_siempre_false(self):
        # INCORPORAR no tiene estado intermedio: o planificada o ejecutada
        sin_docs = _StubTarea('INCORPORAR', documentos_tarea=[])
        assert _en_curso(sin_docs) is False
        con_docs = _StubTarea('INCORPORAR', documentos_tarea=[MagicMock()])
        assert _en_curso(con_docs) is False

    def test_analisis_sin_doc_producido_no_ejecutada(self):
        t = _StubTarea('ANALIZAR', doc_producido_id=None)
        assert _ejecutada(t) is False

    def test_analisis_con_doc_producido_ejecutada(self):
        t = _StubTarea('ANALIZAR', doc_producido_id=42)
        assert _ejecutada(t) is True

    def test_analisis_con_doc_usado_en_curso(self):
        t = _StubTarea('ANALIZAR', doc_producido_id=None, doc_usado_id=7)
        assert _planificada(t) is False
        assert _ejecutada(t) is False
        assert _en_curso(t) is True


# ═══════════════════════════════════════════════════════════════════════════════
# B) Invariante _check_finalizar_tarea
#    Se parchea Tarea.query.get para devolver un stub — sin tocar la BD.
# ═══════════════════════════════════════════════════════════════════════════════

def _check_finalizar_tarea(tarea_id):
    from app.services.invariantes_esftt import _check_finalizar_tarea as fn
    return fn(tarea_id)


@pytest.mark.skip(reason="#370 — INCORPORAR eliminado")
class TestCheckFinalizarTareaIncorporar:

    def _mock_tarea(self, codigo, documentos_tarea=None,
                    doc_producido_id=None, doc_usado_id=None):
        t = MagicMock()
        t.tipo_tarea = MagicMock(codigo=codigo)
        t.documentos_tarea = documentos_tarea if documentos_tarea is not None else []
        t.documento_producido_id = doc_producido_id
        t.documento_usado_id = doc_usado_id
        return t

    def test_incorporar_sin_docs_bloquea(self, app):
        with app.app_context():
            tarea = self._mock_tarea('INCORPORAR', documentos_tarea=[])
            with patch('app.services.invariantes_esftt.Tarea') as MockTarea:
                MockTarea.query.get.return_value = tarea
                resultado = _check_finalizar_tarea(99)
            assert resultado is not None
            assert resultado.permitido is False
            assert 'INCORPORAR' in resultado.norma_compilada or 'documento' in resultado.norma_compilada.lower()

    def test_incorporar_con_docs_no_bloquea(self, app):
        with app.app_context():
            tarea = self._mock_tarea('INCORPORAR', documentos_tarea=[MagicMock()])
            with patch('app.services.invariantes_esftt.Tarea') as MockTarea:
                MockTarea.query.get.return_value = tarea
                resultado = _check_finalizar_tarea(99)
            assert resultado is None

    def test_analisis_sin_doc_producido_bloquea(self, app):
        with app.app_context():
            tarea = self._mock_tarea('ANALIZAR', doc_producido_id=None)
            with patch('app.services.invariantes_esftt.Tarea') as MockTarea:
                MockTarea.query.get.return_value = tarea
                resultado = _check_finalizar_tarea(99)
            assert resultado is not None
            assert resultado.permitido is False

    def test_analisis_con_ambos_docs_no_bloquea(self, app):
        with app.app_context():
            tarea = self._mock_tarea('ANALIZAR', doc_producido_id=5, doc_usado_id=3)
            with patch('app.services.invariantes_esftt.Tarea') as MockTarea:
                MockTarea.query.get.return_value = tarea
                resultado = _check_finalizar_tarea(99)
            assert resultado is None

    def test_tarea_inexistente_no_bloquea(self, app):
        with app.app_context():
            with patch('app.services.invariantes_esftt.Tarea') as MockTarea:
                MockTarea.query.get.return_value = None
                resultado = _check_finalizar_tarea(9999)
            assert resultado is None


# ═══════════════════════════════════════════════════════════════════════════════
# C) Endpoints API — Flask test client con BD real + limpieza
#    Se crea data mínima, se prueba, se elimina.
# ═══════════════════════════════════════════════════════════════════════════════

# TODO #370: dead code — INCORPORAR eliminado
# TestApiIncorporarVincular eliminado (endpoints /tarea/<id>/incorporar/* son dead code)
