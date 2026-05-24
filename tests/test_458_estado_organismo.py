"""
Tests #458 — hook _hook_458_analizar_separata en editar_tarea.

Patrón: objetos Python puros (MagicMock), sin BD real ni cliente Flask.
"""
from unittest.mock import MagicMock, patch


def _tarea_stub(codigo_tarea, codigo_tramite, tramite_id=5):
    tarea = MagicMock()
    tarea.tramite_id = tramite_id
    tarea.tipo_tarea = MagicMock(codigo=codigo_tarea)
    tarea.tramite = MagicMock()
    tarea.tramite.tipo_tramite = MagicMock(codigo=codigo_tramite)
    return tarea


def _vinculo_stub(org):
    """Stub de TramiteOrganismo apuntando a un OrganismoExpediente."""
    v = MagicMock()
    v.organismo_expediente = org
    return v


class TestHook458EstadoOrganismo:

    def test_analizar_separata_pone_en_tramitacion(self):
        from app.routes.api_bc import _hook_458_analizar_separata
        tarea = _tarea_stub('ANALIZAR', 'CONSULTA_SEPARATA', tramite_id=5)
        org = MagicMock()
        org.estado = 'separata_enviada'

        with patch('app.routes.api_bc.TramiteOrganismo') as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = _vinculo_stub(org)
            _hook_458_analizar_separata(tarea, id_producido=10)

        assert org.estado == 'en_tramitacion'
        mock_cls.query.filter_by.assert_called_once_with(tramite_id=5)

    def test_analizar_otro_tramite_no_cambia_estado(self):
        from app.routes.api_bc import _hook_458_analizar_separata
        tarea = _tarea_stub('ANALIZAR', 'REQUERIMIENTO_DE_MEJORA', tramite_id=5)
        org = MagicMock()
        org.estado = 'separata_enviada'

        with patch('app.routes.api_bc.TramiteOrganismo') as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = _vinculo_stub(org)
            _hook_458_analizar_separata(tarea, id_producido=10)

        assert org.estado == 'separata_enviada'
        mock_cls.query.filter_by.assert_not_called()

    def test_sin_organismo_no_falla(self):
        from app.routes.api_bc import _hook_458_analizar_separata
        tarea = _tarea_stub('ANALIZAR', 'CONSULTA_SEPARATA', tramite_id=99)

        with patch('app.routes.api_bc.TramiteOrganismo') as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = None
            # No debe lanzar excepción
            _hook_458_analizar_separata(tarea, id_producido=10)

    def test_sin_doc_producido_no_activa_hook(self):
        from app.routes.api_bc import _hook_458_analizar_separata
        tarea = _tarea_stub('ANALIZAR', 'CONSULTA_SEPARATA', tramite_id=5)
        org = MagicMock()
        org.estado = 'separata_enviada'

        with patch('app.routes.api_bc.TramiteOrganismo') as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = _vinculo_stub(org)
            _hook_458_analizar_separata(tarea, id_producido=None)

        assert org.estado == 'separata_enviada'
        mock_cls.query.filter_by.assert_not_called()
