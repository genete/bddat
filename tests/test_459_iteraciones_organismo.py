"""
Tests #459 — hook _hook_459_traslado_organismo en crear_tramite.

Patrón: objetos Python puros (MagicMock), sin BD real ni cliente Flask.
"""
from unittest.mock import MagicMock, patch, call


def _tipo_tramite_stub(codigo):
    tt = MagicMock()
    tt.codigo = codigo
    tt.id = 99
    return tt


def _fase_stub(fase_id=1):
    fase = MagicMock()
    fase.id = fase_id
    return fase


def _org_stub(tramite_id, num_iteraciones=0):
    org = MagicMock()
    org.tramite_id = tramite_id
    org.num_iteraciones_organismo = num_iteraciones
    return org


class TestHook459IteracionesOrganismo:

    def test_crear_traslado_organismo_incrementa(self):
        from app.routes.api_bc import _hook_459_traslado_organismo
        tipo = _tipo_tramite_stub('CONSULTA_TRASLADO_ORGANISMO')
        fase = _fase_stub(1)
        org = _org_stub(tramite_id=10, num_iteraciones=0)

        cod_sep = MagicMock()
        cod_sep.id = 7

        tram_sep = MagicMock()
        tram_sep.id = 10

        with patch('app.routes.api_bc.TipoTramite') as mock_tt, \
             patch('app.routes.api_bc.Tramite') as mock_tram, \
             patch('app.routes.api_bc.OrganismoExpediente') as mock_org:

            mock_tt.query.filter_by.return_value.first.return_value = cod_sep
            mock_tram.query.filter_by.return_value.all.return_value = [tram_sep]
            mock_org.query.filter.return_value.all.return_value = [org]

            _hook_459_traslado_organismo(tipo, fase)

        assert org.num_iteraciones_organismo == 1

    def test_crear_otro_tramite_no_incrementa(self):
        from app.routes.api_bc import _hook_459_traslado_organismo
        tipo = _tipo_tramite_stub('CONSULTA_SEPARATA')
        fase = _fase_stub(1)
        org = _org_stub(tramite_id=10, num_iteraciones=0)

        with patch('app.routes.api_bc.TipoTramite') as mock_tt, \
             patch('app.routes.api_bc.OrganismoExpediente') as mock_org:

            _hook_459_traslado_organismo(tipo, fase)

            mock_tt.query.filter_by.assert_not_called()

        assert org.num_iteraciones_organismo == 0

    def test_sin_organismo_no_falla(self):
        from app.routes.api_bc import _hook_459_traslado_organismo
        tipo = _tipo_tramite_stub('CONSULTA_TRASLADO_ORGANISMO')
        fase = _fase_stub(1)

        cod_sep = MagicMock()
        cod_sep.id = 7

        with patch('app.routes.api_bc.TipoTramite') as mock_tt, \
             patch('app.routes.api_bc.Tramite') as mock_tram, \
             patch('app.routes.api_bc.OrganismoExpediente') as mock_org:

            mock_tt.query.filter_by.return_value.first.return_value = cod_sep
            mock_tram.query.filter_by.return_value.all.return_value = []
            mock_org.query.filter.return_value.all.return_value = []

            # No debe lanzar excepción
            _hook_459_traslado_organismo(tipo, fase)

    def test_multiples_organismos_no_incrementa(self):
        from app.routes.api_bc import _hook_459_traslado_organismo
        tipo = _tipo_tramite_stub('CONSULTA_TRASLADO_ORGANISMO')
        fase = _fase_stub(1)
        org1 = _org_stub(tramite_id=10, num_iteraciones=0)
        org2 = _org_stub(tramite_id=11, num_iteraciones=0)

        cod_sep = MagicMock()
        cod_sep.id = 7
        tram1 = MagicMock()
        tram1.id = 10
        tram2 = MagicMock()
        tram2.id = 11

        with patch('app.routes.api_bc.TipoTramite') as mock_tt, \
             patch('app.routes.api_bc.Tramite') as mock_tram, \
             patch('app.routes.api_bc.OrganismoExpediente') as mock_org:

            mock_tt.query.filter_by.return_value.first.return_value = cod_sep
            mock_tram.query.filter_by.return_value.all.return_value = [tram1, tram2]
            mock_org.query.filter.return_value.all.return_value = [org1, org2]

            _hook_459_traslado_organismo(tipo, fase)

        assert org1.num_iteraciones_organismo == 0
        assert org2.num_iteraciones_organismo == 0
