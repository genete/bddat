"""
Tests #459 — hook _hook_459_traslado_organismo en crear_tramite.

Tras #456: el hook ya no incrementa num_iteraciones_organismo (campo eliminado).
Navega al organismo vía TramiteOrganismo.query.filter(tramite_id.in_()).
El conteo de iteraciones es un COUNT derivado que implementa #460.

Patrón: objetos Python puros (MagicMock), sin BD real ni cliente Flask.
"""
from unittest.mock import MagicMock, patch


def _tipo_tramite_stub(codigo):
    tt = MagicMock()
    tt.codigo = codigo
    tt.id = 99
    return tt


def _fase_stub(fase_id=1):
    fase = MagicMock()
    fase.id = fase_id
    return fase


class TestHook459TrasladoOrganismo:

    def test_otro_tramite_no_consulta_bd(self):
        from app.routes.api_bc import _hook_459_traslado_organismo
        tipo = _tipo_tramite_stub('CONSULTA_SEPARATA')
        fase = _fase_stub(1)

        with patch('app.routes.api_bc.TipoTramite') as mock_tt:
            _hook_459_traslado_organismo(tipo, fase)
            mock_tt.query.filter_by.assert_not_called()

    def test_traslado_organismo_navega_via_tramite_organismo(self):
        from app.routes.api_bc import _hook_459_traslado_organismo
        tipo = _tipo_tramite_stub('CONSULTA_TRASLADO_ORGANISMO')
        fase = _fase_stub(1)

        cod_sep = MagicMock()
        cod_sep.id = 7
        tram_sep = MagicMock()
        tram_sep.id = 10

        with patch('app.routes.api_bc.TipoTramite') as mock_tt, \
             patch('app.routes.api_bc.Tramite') as mock_tram, \
             patch('app.routes.api_bc.TramiteOrganismo') as mock_org:

            mock_tt.query.filter_by.return_value.first.return_value = cod_sep
            mock_tram.query.filter_by.return_value.all.return_value = [tram_sep]
            mock_org.query.filter.return_value.all.return_value = []

            # No debe lanzar excepción aunque no haya vínculos
            _hook_459_traslado_organismo(tipo, fase)

        mock_org.query.filter.assert_called_once()

    def test_sin_separatas_no_consulta_tramite_organismo(self):
        from app.routes.api_bc import _hook_459_traslado_organismo
        tipo = _tipo_tramite_stub('CONSULTA_TRASLADO_ORGANISMO')
        fase = _fase_stub(1)

        cod_sep = MagicMock()
        cod_sep.id = 7

        with patch('app.routes.api_bc.TipoTramite') as mock_tt, \
             patch('app.routes.api_bc.Tramite') as mock_tram, \
             patch('app.routes.api_bc.TramiteOrganismo') as mock_org:

            mock_tt.query.filter_by.return_value.first.return_value = cod_sep
            mock_tram.query.filter_by.return_value.all.return_value = []

            _hook_459_traslado_organismo(tipo, fase)

        mock_org.query.filter.assert_not_called()
