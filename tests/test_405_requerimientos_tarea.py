"""
Tests issue #405 — CatalogoRequerimiento y RequerimientoTarea.

Sin BD ni app context. Valida lógica de modelos con stubs.
"""
from unittest.mock import MagicMock


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _catalogo(texto='Falta memoria de cálculo', categoria='tecnica', activo=True):
    from app.models.catalogo_requerimientos import CatalogoRequerimiento
    cat = MagicMock(spec=CatalogoRequerimiento)
    cat.texto = texto
    cat.categoria = categoria
    cat.activo = activo
    return cat


def _req_desde_catalogo(cat, orden=1):
    from app.models.requerimientos_tarea import RequerimientoTarea
    r = MagicMock(spec=RequerimientoTarea)
    r.catalogo_requerimientos_id = 1
    r.catalogo_requerimiento = cat
    r.texto_libre = None
    r.orden = orden
    r.texto = RequerimientoTarea.texto.fget(r)
    r.desde_catalogo = RequerimientoTarea.desde_catalogo.fget(r)
    return r


def _req_texto_libre(texto='Falta el visado colegial en el proyecto', orden=1):
    from app.models.requerimientos_tarea import RequerimientoTarea
    r = MagicMock(spec=RequerimientoTarea)
    r.catalogo_requerimientos_id = None
    r.catalogo_requerimiento = None
    r.texto_libre = texto
    r.orden = orden
    r.texto = RequerimientoTarea.texto.fget(r)
    r.desde_catalogo = RequerimientoTarea.desde_catalogo.fget(r)
    return r


# ──────────────────────────────────────────────────────────────────────────────
# CatalogoRequerimiento
# ──────────────────────────────────────────────────────────────────────────────

class TestCatalogoRequerimiento:

    def test_str_trunca_a_60(self):
        from app.models.catalogo_requerimientos import CatalogoRequerimiento
        cat = CatalogoRequerimiento()
        cat.texto = 'a' * 80
        assert str(cat) == 'a' * 60 + '…'

    def test_str_sin_truncar(self):
        from app.models.catalogo_requerimientos import CatalogoRequerimiento
        cat = CatalogoRequerimiento()
        cat.texto = 'Texto corto'
        assert str(cat) == 'Texto corto'

    def test_repr(self):
        from app.models.catalogo_requerimientos import CatalogoRequerimiento
        cat = CatalogoRequerimiento()
        cat.id = 7
        cat.categoria = 'documental'
        assert 'id=7' in repr(cat)
        assert 'documental' in repr(cat)


# ──────────────────────────────────────────────────────────────────────────────
# RequerimientoTarea — propiedad texto
# ──────────────────────────────────────────────────────────────────────────────

class TestRequerimientoTareaTexto:

    def test_texto_desde_catalogo(self):
        cat = _catalogo(texto='Falta memoria de cálculo')
        r = _req_desde_catalogo(cat)
        assert r.texto == 'Falta memoria de cálculo'

    def test_texto_libre(self):
        r = _req_texto_libre(texto='Falta el visado colegial en el proyecto')
        assert r.texto == 'Falta el visado colegial en el proyecto'

    def test_texto_catalogo_ignora_texto_libre(self):
        """El catálogo tiene precedencia (texto_libre debería ser NULL por constraint)."""
        from app.models.requerimientos_tarea import RequerimientoTarea
        r = MagicMock(spec=RequerimientoTarea)
        r.catalogo_requerimiento = _catalogo(texto='Texto del catálogo')
        r.catalogo_requerimientos_id = 1
        r.texto_libre = None
        assert RequerimientoTarea.texto.fget(r) == 'Texto del catálogo'


# ──────────────────────────────────────────────────────────────────────────────
# RequerimientoTarea — propiedad desde_catalogo
# ──────────────────────────────────────────────────────────────────────────────

class TestRequerimientoTareaOrigen:

    def test_desde_catalogo_true(self):
        cat = _catalogo()
        r = _req_desde_catalogo(cat)
        assert r.desde_catalogo is True

    def test_desde_catalogo_false_para_texto_libre(self):
        r = _req_texto_libre()
        assert r.desde_catalogo is False

    def test_repr_catalogo(self):
        from app.models.requerimientos_tarea import RequerimientoTarea
        r = RequerimientoTarea()
        r.id = 3
        r.tarea_id = 10
        r.catalogo_requerimientos_id = 5
        r.texto_libre = None
        r.orden = 2
        assert 'cat=5' in repr(r)
        assert 'orden=2' in repr(r)

    def test_repr_libre(self):
        from app.models.requerimientos_tarea import RequerimientoTarea
        r = RequerimientoTarea()
        r.id = 4
        r.tarea_id = 10
        r.catalogo_requerimientos_id = None
        r.texto_libre = 'Texto manual'
        r.orden = 1
        assert 'libre' in repr(r)
