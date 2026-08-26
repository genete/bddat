"""
Tests #471 — servicio crear_traslado y guard en crear_tramite.

Patrón: MagicMock + patch sobre crear_traslado con app.app_context().
Sin BD real. El fixture `app` viene de conftest.py.

La función vive en `app/services/consultas_organismos.py` desde #577 (antes era
`api_bc._ejecutar_crear_traslado`).
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


_MOD = 'app.services.consultas_organismos'


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

    def test_separata_rechazada_desde_396_bloque5(self, app_ctx):
        """CONSULTA_SEPARATA pasa a creacion_generica=false en #396 bloque 5
        (migración 396_consulta_separata_no_generica): toda separata nace desde
        enviar_consultas(), nunca de la despensa genérica del árbol."""
        assert self._creacion_generica('CONSULTA_SEPARATA', app_ctx) is False


# ---------------------------------------------------------------------------
# B) _ejecutar_crear_traslado — validaciones de entrada
# ---------------------------------------------------------------------------

class TestEjecutarCrearTrasladoValidaciones:
    """Desde #396 bloque 5, crear_traslado devuelve ResultadoMutacion (ok/error)
    en vez de (jsonify(...), status) — mismo contrato que mutaciones_arbol.py."""

    def test_tipo_invalido_falla(self, app):
        with app.app_context():
            from app.services.consultas_organismos import crear_traslado
            fase = _fase_stub()
            res = crear_traslado(
                fase, _form(tipo='INVALIDO', organismo_expediente_id='3'))
            assert not res.ok
            assert 'tipo' in res.error

    def test_tipo_vacio_falla(self, app):
        with app.app_context():
            from app.services.consultas_organismos import crear_traslado
            fase = _fase_stub()
            res = crear_traslado(
                fase, _form(organismo_expediente_id='3'))
            assert not res.ok

    def test_sin_organismo_expediente_id_falla(self, app):
        with app.app_context():
            from app.services.consultas_organismos import crear_traslado
            fase = _fase_stub()
            res = crear_traslado(fase, _form(tipo='ORGANISMO'))
            assert not res.ok
            assert 'organismo_expediente_id' in res.error

    def test_organismo_no_existe_falla(self, app):
        with app.app_context():
            from app.services.consultas_organismos import crear_traslado
            fase = _fase_stub(expediente_id=5)
            with patch(f'{_MOD}.OrganismoExpediente') as mock_oe:
                mock_oe.query.get.return_value = None
                res = crear_traslado(
                    fase, _form(tipo='ORGANISMO', organismo_expediente_id='99'))
            assert not res.ok

    def test_organismo_de_otro_expediente_falla(self, app):
        with app.app_context():
            from app.services.consultas_organismos import crear_traslado
            fase = _fase_stub(expediente_id=5)
            oe = _oe_stub(oe_id=99, expediente_id=7)
            with patch(f'{_MOD}.OrganismoExpediente') as mock_oe:
                mock_oe.query.get.return_value = oe
                res = crear_traslado(
                    fase, _form(tipo='ORGANISMO', organismo_expediente_id='99'))
            assert not res.ok


# ---------------------------------------------------------------------------
# C) _ejecutar_crear_traslado — camino feliz: crea Tramite + TramiteOrganismo
# ---------------------------------------------------------------------------

class TestEjecutarCrearTrasladoCaminoFeliz:
    """Desde #396 bloque 5 el camino feliz también pasa por check_invariante y
    check_vocabulario_tramite (comprobaciones que mutaciones_arbol.crear_tramite
    ya hacía y esta función no) — parcheadas a "sin bloqueo" para no depender
    de datos reales de BD en un fichero pensado para MagicMock puro."""

    def _run(self, app, tipo_param, codigo_esperado):
        from app.services.consultas_organismos import crear_traslado

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
             patch(f'{_MOD}.check_invariante', return_value=None), \
             patch(f'{_MOD}.check_vocabulario_tramite', return_value=None), \
             patch(f'{_MOD}._evaluar') as mock_eval, \
             patch(f'{_MOD}.db'):

            mock_oe_cls.query.get.return_value = oe
            mock_tt.query.filter_by.return_value.first.return_value = tipo_tramite
            mock_tramite_cls.return_value = tramite_nuevo
            eval_result = MagicMock()
            eval_result.permitido = True
            eval_result.nivel = None
            eval_result.motivo = None
            mock_eval.return_value = eval_result

            res = crear_traslado(
                fase, _form(tipo=tipo_param, organismo_expediente_id='3'))

        assert res.ok, res.error
        assert res.ids == [42]

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
        from app.services.consultas_organismos import crear_traslado

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
             patch(f'{_MOD}.check_invariante', return_value=None), \
             patch(f'{_MOD}.check_vocabulario_tramite', return_value=None), \
             patch(f'{_MOD}._evaluar') as mock_eval, \
             patch(f'{_MOD}.db'):

            mock_oe_cls.query.get.return_value = oe
            mock_tt.query.filter_by.return_value.first.return_value = tipo_tramite
            mock_tramite_cls.return_value = tramite_nuevo
            eval_result = MagicMock()
            eval_result.permitido = True
            eval_result.nivel = None
            mock_eval.return_value = eval_result

            crear_traslado(
                fase, _form(tipo='ORGANISMO', organismo_expediente_id='3'))

        mock_eval.assert_called_once()
        objeto = mock_eval.call_args.kwargs['objeto']
        assert objeto.get('organismo_expediente') is oe


# ---------------------------------------------------------------------------
# D) _ejecutar_crear_traslado — motor bloquea
# ---------------------------------------------------------------------------

def test_motor_bloquea_no_crea_tramite(app):
    from app.services.consultas_organismos import crear_traslado

    fase = _fase_stub(fase_id=1, expediente_id=5)
    oe = _oe_stub(oe_id=3, expediente_id=5)
    tipo_tramite = _tipo_tramite_stub('CONSULTA_TRASLADO_ORGANISMO', id=20)

    with app.app_context(), \
         patch(f'{_MOD}.OrganismoExpediente') as mock_oe_cls, \
         patch(f'{_MOD}.TipoTramite') as mock_tt, \
         patch(f'{_MOD}.Tramite') as mock_tramite_cls, \
         patch(f'{_MOD}.TramiteOrganismo') as mock_to_cls, \
         patch(f'{_MOD}.check_invariante', return_value=None), \
         patch(f'{_MOD}.check_vocabulario_tramite', return_value=None), \
         patch(f'{_MOD}._evaluar') as mock_eval:

        mock_oe_cls.query.get.return_value = oe
        mock_tt.query.filter_by.return_value.first.return_value = tipo_tramite
        eval_result = MagicMock()
        eval_result.permitido = False
        mock_eval.return_value = eval_result

        res = crear_traslado(
            fase, _form(tipo='ORGANISMO', organismo_expediente_id='3'))

    assert not res.ok
    assert res.bloqueo is eval_result
    mock_tramite_cls.assert_not_called()
    mock_to_cls.assert_not_called()
