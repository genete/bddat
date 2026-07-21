"""
Tests #677 — resultado derivado del borrador + gate de secciones extendidas
(ADR-033 §3). Helpers puros de post_analizar/get_analizar en api_expedientes.py.
"""


class TestResultadoDerivado:

    def test_sin_items_es_favorable(self):
        from app.routes.api_expedientes import _resultado_derivado
        assert _resultado_derivado({'items': [], 'completo': True}) == 'favorable'

    def test_con_items_es_desfavorable(self):
        from app.routes.api_expedientes import _resultado_derivado
        consolidado = {'items': [{'texto': 'Falta memoria técnica', 'origen': 'documental'}], 'completo': True}
        assert _resultado_derivado(consolidado) == 'desfavorable'


class TestTieneSeccionesExtendidas:

    def test_analisis_documental_tiene_secciones(self):
        from unittest.mock import MagicMock
        from app.routes.api_expedientes import _tiene_secciones_extendidas
        tarea = MagicMock()
        tarea.tramite.tipo_tramite.codigo = 'ANALISIS_DOCUMENTAL'
        assert _tiene_secciones_extendidas(tarea) is True

    def test_consulta_separata_no_tiene_secciones(self):
        from unittest.mock import MagicMock
        from app.routes.api_expedientes import _tiene_secciones_extendidas
        tarea = MagicMock()
        tarea.tramite.tipo_tramite.codigo = 'CONSULTA_SEPARATA'
        assert _tiene_secciones_extendidas(tarea) is False

    def test_sin_tramite_no_tiene_secciones(self):
        from app.routes.api_expedientes import _tiene_secciones_extendidas
        tarea = type('T', (), {'tramite': None})()
        assert _tiene_secciones_extendidas(tarea) is False
