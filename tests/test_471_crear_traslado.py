"""
Tests #471 — endpoint crear_traslado y guard en crear_tramite.

Patrón: MagicMock + patch sobre _ejecutar_crear_traslado con app.app_context().
Sin BD real. El fixture `app` viene de conftest.py.
"""
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fase_stub(fase_id=1, expediente_id=5):
    expediente = MagicMock()
    expediente.id = expediente_id
    solicitud = MagicMock()
    solicitud.expediente = expediente
    fase = MagicMock()
    fase.id = fase_id
    fase.solicitud = solicitud
    return fase


def _oe_stub(oe_id=3, expediente_id=5):
    oe = MagicMock()
    oe.id = oe_id
    oe.expediente_id = expediente_id
    return oe


def _tipo_tramite_stub(codigo, id=20):
    tt = MagicMock()
    tt.codigo = codigo
    tt.id = id
    return tt


def _form(**kwargs):
    """Simula ImmutableMultiDict de Flask con .get() tipado."""
    class _FakeForm(dict):
        def get(self, key, default=None, type=None):
            val = super().get(key, default)
            if type is not None and val is not None:
                try:
                    val = type(val)
                except (ValueError, TypeError):
                    return None
            return val
    return _FakeForm(kwargs)


_MOD = 'app.routes.api_bc'


# ---------------------------------------------------------------------------
# A) tipos_tramites.creacion_generica — guard en crear_tramite (#725, ADR-037)
# ---------------------------------------------------------------------------

class TestGuardCrearTramite:

    def _creacion_generica(self, codigo, app_ctx):
        from app.models.tipos_tramites import TipoTramite
        tipo = TipoTramite.query.filter_by(codigo=codigo).first()
        if tipo is None:
            import pytest
            pytest.skip(f'TipoTramite {codigo!r} no está en el catálogo de esta BD')
        return tipo.creacion_generica

    def test_traslado_organismo_rechazado(self, app_ctx):
        assert self._creacion_generica('CONSULTA_TRASLADO_ORGANISMO', app_ctx) is False

    def test_traslado_titular_rechazado(self, app_ctx):
        assert self._creacion_generica('CONSULTA_TRASLADO_TITULAR', app_ctx) is False

    def test_separata_no_rechazada(self, app_ctx):
        assert self._creacion_generica('CONSULTA_SEPARATA', app_ctx) is True


# ---------------------------------------------------------------------------
# B) _ejecutar_crear_traslado — validaciones de entrada
# ---------------------------------------------------------------------------

class TestEjecutarCrearTrasladoValidaciones:

    def test_tipo_invalido_devuelve_400(self, app):
        with app.app_context():
            from app.routes.api_bc import _ejecutar_crear_traslado
            fase = _fase_stub()
            resp, status = _ejecutar_crear_traslado(
                fase, _form(tipo='INVALIDO', organismo_expediente_id='3'))
            assert status == 400
            assert 'tipo' in resp.get_json()['error']

    def test_tipo_vacio_devuelve_400(self, app):
        with app.app_context():
            from app.routes.api_bc import _ejecutar_crear_traslado
            fase = _fase_stub()
            resp, status = _ejecutar_crear_traslado(
                fase, _form(organismo_expediente_id='3'))
            assert status == 400

    def test_sin_organismo_expediente_id_devuelve_400(self, app):
        with app.app_context():
            from app.routes.api_bc import _ejecutar_crear_traslado
            fase = _fase_stub()
            resp, status = _ejecutar_crear_traslado(fase, _form(tipo='ORGANISMO'))
            assert status == 400
            assert 'organismo_expediente_id' in resp.get_json()['error']

    def test_organismo_no_existe_devuelve_404(self, app):
        with app.app_context():
            from app.routes.api_bc import _ejecutar_crear_traslado
            fase = _fase_stub(expediente_id=5)
            with patch(f'{_MOD}.OrganismoExpediente') as mock_oe:
                mock_oe.query.get.return_value = None
                resp, status = _ejecutar_crear_traslado(
                    fase, _form(tipo='ORGANISMO', organismo_expediente_id='99'))
            assert status == 404

    def test_organismo_de_otro_expediente_devuelve_404(self, app):
        with app.app_context():
            from app.routes.api_bc import _ejecutar_crear_traslado
            fase = _fase_stub(expediente_id=5)
            oe = _oe_stub(oe_id=99, expediente_id=7)
            with patch(f'{_MOD}.OrganismoExpediente') as mock_oe:
                mock_oe.query.get.return_value = oe
                resp, status = _ejecutar_crear_traslado(
                    fase, _form(tipo='ORGANISMO', organismo_expediente_id='99'))
            assert status == 404


# ---------------------------------------------------------------------------
# C) _ejecutar_crear_traslado — camino feliz: crea Tramite + TramiteOrganismo
# ---------------------------------------------------------------------------

class TestEjecutarCrearTrasladoCaminoFeliz:

    def _run(self, app, tipo_param, codigo_esperado):
        from app.routes.api_bc import _ejecutar_crear_traslado

        fase = _fase_stub(fase_id=1, expediente_id=5)
        oe = _oe_stub(oe_id=3, expediente_id=5)
        tipo_tramite = _tipo_tramite_stub(codigo_esperado, id=20)
        tramite_nuevo = MagicMock()
        tramite_nuevo.id = 42

        with app.app_context(), \
             patch(f'{_MOD}.OrganismoExpediente') as mock_oe_cls, \
             patch(f'{_MOD}.TipoTramite') as mock_tt, \
             patch(f'{_MOD}.Tramite') as mock_tramite_cls, \
             patch(f'{_MOD}.TramiteOrganismo') as mock_to_cls, \
             patch(f'{_MOD}._leer_bypass', return_value=(None, None)), \
             patch(f'{_MOD}._evaluar') as mock_eval, \
             patch(f'{_MOD}.db'):

            mock_oe_cls.query.get.return_value = oe
            mock_tt.query.filter_by.return_value.first.return_value = tipo_tramite
            mock_tramite_cls.return_value = tramite_nuevo
            eval_result = MagicMock()
            eval_result.permitido = True
            eval_result.motivo = None
            mock_eval.return_value = eval_result

            resp, status = _ejecutar_crear_traslado(
                fase, _form(tipo=tipo_param, organismo_expediente_id='3'))

        assert status == 200
        assert resp.get_json()['ok'] is True
        assert resp.get_json()['id'] == 42

        mock_to_cls.assert_called_once_with(tramite_id=42, organismo_expediente_id=3)
        mock_tt.query.filter_by.assert_called_with(codigo=codigo_esperado)
        return mock_to_cls, mock_eval

    def test_tipo_organismo_crea_vinculo(self, app):
        self._run(app, 'ORGANISMO', 'CONSULTA_TRASLADO_ORGANISMO')

    def test_tipo_titular_crea_vinculo(self, app):
        self._run(app, 'TITULAR', 'CONSULTA_TRASLADO_TITULAR')

    def test_tipo_case_insensitive(self, app):
        """'organismo' en minúsculas también funciona por el .upper()."""
        self._run(app, 'organismo', 'CONSULTA_TRASLADO_ORGANISMO')

    def test_motor_pasa_organismo_expediente_en_objeto(self, app):
        """El evaluador recibe organismo_expediente en el objeto de contexto."""
        from app.routes.api_bc import _ejecutar_crear_traslado

        fase = _fase_stub(fase_id=1, expediente_id=5)
        oe = _oe_stub(oe_id=3, expediente_id=5)
        tipo_tramite = _tipo_tramite_stub('CONSULTA_TRASLADO_ORGANISMO', id=20)
        tramite_nuevo = MagicMock()
        tramite_nuevo.id = 42

        with app.app_context(), \
             patch(f'{_MOD}.OrganismoExpediente') as mock_oe_cls, \
             patch(f'{_MOD}.TipoTramite') as mock_tt, \
             patch(f'{_MOD}.Tramite') as mock_tramite_cls, \
             patch(f'{_MOD}.TramiteOrganismo'), \
             patch(f'{_MOD}._leer_bypass', return_value=(None, None)), \
             patch(f'{_MOD}._evaluar') as mock_eval, \
             patch(f'{_MOD}.db'):

            mock_oe_cls.query.get.return_value = oe
            mock_tt.query.filter_by.return_value.first.return_value = tipo_tramite
            mock_tramite_cls.return_value = tramite_nuevo
            eval_result = MagicMock()
            eval_result.permitido = True
            mock_eval.return_value = eval_result

            _ejecutar_crear_traslado(
                fase, _form(tipo='ORGANISMO', organismo_expediente_id='3'))

        mock_eval.assert_called_once()
        objeto = mock_eval.call_args.kwargs['objeto']
        assert objeto.get('organismo_expediente') is oe


# ---------------------------------------------------------------------------
# D) _ejecutar_crear_traslado — motor bloquea
# ---------------------------------------------------------------------------

def test_motor_bloquea_no_crea_tramite(app):
    from app.routes.api_bc import _ejecutar_crear_traslado

    fase = _fase_stub(fase_id=1, expediente_id=5)
    oe = _oe_stub(oe_id=3, expediente_id=5)
    tipo_tramite = _tipo_tramite_stub('CONSULTA_TRASLADO_ORGANISMO', id=20)

    with app.app_context(), \
         patch(f'{_MOD}.OrganismoExpediente') as mock_oe_cls, \
         patch(f'{_MOD}.TipoTramite') as mock_tt, \
         patch(f'{_MOD}.Tramite') as mock_tramite_cls, \
         patch(f'{_MOD}.TramiteOrganismo') as mock_to_cls, \
         patch(f'{_MOD}._leer_bypass', return_value=(None, None)), \
         patch(f'{_MOD}._evaluar') as mock_eval, \
         patch(f'{_MOD}._bloqueo', return_value=({'ok': False}, 403)):

        mock_oe_cls.query.get.return_value = oe
        mock_tt.query.filter_by.return_value.first.return_value = tipo_tramite
        eval_result = MagicMock()
        eval_result.permitido = False
        mock_eval.return_value = eval_result

        _ejecutar_crear_traslado(
            fase, _form(tipo='ORGANISMO', organismo_expediente_id='3'))

    mock_tramite_cls.assert_not_called()
    mock_to_cls.assert_not_called()
