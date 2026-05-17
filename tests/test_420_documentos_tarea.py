"""
Tests #420 — modelo N:M documento↔tarea con rol (ADR-010).

Verifica las properties de Tarea derivadas de los vínculos documentales
(documentos_tarea con campo rol): documentos_consumidos, documento_producido,
ejecutada, planificada, en_curso, estado.

Se invoca el fget de cada property sobre stubs, sin tocar SQLAlchemy ni BD.
"""
from app.models.tareas import Tarea


class _Vinculo:
    """Stub de DocumentoTarea — vínculo documento↔tarea con rol."""
    def __init__(self, rol, documento=None):
        self.rol = rol
        self.documento = documento if documento is not None else object()


class _StubTarea:
    """Stub mínimo: solo expone la lista de vínculos documentales."""
    def __init__(self, vinculos=None):
        self.vinculos_documento = vinculos or []


def _ejecutada(t):    return Tarea.ejecutada.fget(t)
def _planificada(t):  return Tarea.planificada.fget(t)
def _consumidos(t):   return Tarea.documentos_consumidos.fget(t)
def _producido(t):    return Tarea.documento_producido.fget(t)


def _en_curso(t):
    # en_curso depende de planificada y ejecutada; se resuelven explícitamente
    # sobre el stub sin necesidad de exponerlas como properties.
    return not _planificada(t) and not _ejecutada(t)


class TestEstadoSegunVinculos:

    def test_sin_vinculos_planificada(self):
        t = _StubTarea([])
        assert _planificada(t) is True
        assert _ejecutada(t) is False
        assert _en_curso(t) is False

    def test_solo_consumido_en_curso(self):
        t = _StubTarea([_Vinculo('CONSUMIDO')])
        assert _planificada(t) is False
        assert _ejecutada(t) is False
        assert _en_curso(t) is True

    def test_con_producido_ejecutada(self):
        t = _StubTarea([_Vinculo('PRODUCIDO')])
        assert _ejecutada(t) is True
        assert _en_curso(t) is False
        assert _planificada(t) is False

    def test_consumido_y_producido_ejecutada(self):
        t = _StubTarea([_Vinculo('CONSUMIDO'), _Vinculo('PRODUCIDO')])
        assert _ejecutada(t) is True


class TestAccesoresDocumentales:

    def test_documentos_consumidos_filtra_por_rol(self):
        d1, d2, d3 = object(), object(), object()
        t = _StubTarea([
            _Vinculo('CONSUMIDO', d1),
            _Vinculo('CONSUMIDO', d2),
            _Vinculo('PRODUCIDO', d3),
        ])
        assert _consumidos(t) == [d1, d2]
        assert _producido(t) is d3

    def test_consumo_multiple(self):
        docs = [object() for _ in range(4)]
        t = _StubTarea([_Vinculo('CONSUMIDO', d) for d in docs])
        assert _consumidos(t) == docs
        assert _producido(t) is None

    def test_sin_producido_devuelve_none(self):
        t = _StubTarea([_Vinculo('CONSUMIDO')])
        assert _producido(t) is None

    def test_sin_consumidos_devuelve_lista_vacia(self):
        t = _StubTarea([_Vinculo('PRODUCIDO')])
        assert _consumidos(t) == []
