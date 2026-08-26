"""Tests #475 — señalización de CONSULTA_TRASLADO_TITULAR vencido.

Cubre:
  A) Variable del motor `traslado_organismo_titular_vencido` (calculado.py)
  B) Helper `_traslado_titular_vencido` de la serialización de organismos (api_bc.py)

Patrón sin BD real: stubs SimpleNamespace + patch de db.session.query y
plazos.obtener_estado_plazo_tarea. Igual que #460.

#788: los dos consumidores dejaron de evaluar el plazo sobre el TRÁMITE —nivel
que no porta fecha administrativa y ya no existe en catalogo_plazos— y lo evalúan
sobre su tarea ESPERAR_PLAZO.

#778: bajar hasta esa tarea es navegación del árbol (`Tramite.tarea_espera`), no
una entrada del servicio de plazos, así que los consumidores llaman ya con la
tarea en la mano. Lo que se sustituye aquí es `obtener_estado_plazo_tarea`.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

def _ep(estado):
    return SimpleNamespace(estado=estado)


def _org(resultado, id=1):
    return SimpleNamespace(resultado=resultado, id=id)


def _ctx(organismos):
    exp = SimpleNamespace(organismos=organismos)
    return SimpleNamespace(expediente=exp)


def _get_variable(nombre):
    import app.services.variables.calculado  # noqa: F401
    from app.services.variables import _REGISTRY
    fn = _REGISTRY.get(nombre)
    assert fn is not None, f'Variable {nombre!r} no encontrada en _REGISTRY'
    return fn


# ---------------------------------------------------------------------------
# A) Variable traslado_organismo_titular_vencido
#
# #396 bloque 7: la variable delega en consultas_organismos.traslado_titular_vencido
# (parte B más abajo) en vez de reimplementar la query — el mock ya no es sobre
# db.session.query, sino sobre TramiteOrganismo.query, igual que en la parte B.
# ---------------------------------------------------------------------------

class TestVariableMotor:

    def test_registrada(self):
        _get_variable('traslado_organismo_titular_vencido')

    def test_sin_organismos_false(self):
        """Expediente sin organismos → False."""
        fn = _get_variable('traslado_organismo_titular_vencido')
        assert fn(_ctx([])) is False

    def test_organismo_cerrado_se_ignora(self):
        """Organismo con resultado (cerrado_favorable) → no se evalúa su plazo → False."""
        fn = _get_variable('traslado_organismo_titular_vencido')
        ctx = _ctx([_org('cerrado_favorable')])
        with patch('app.models.tramites_organismos.TramiteOrganismo') as mock_model:
            mock_model.query.join.side_effect = AssertionError('no debería consultarse BD')
            assert fn(ctx) is False

    def test_organismo_abierto_sin_vinculo_false(self):
        """Organismo abierto (sin resultado) pero sin CONSULTA_TRASLADO_TITULAR vinculado → False."""
        fn = _get_variable('traslado_organismo_titular_vencido')
        ctx = _ctx([_org(None)])
        with patch('app.models.tramites_organismos.TramiteOrganismo') as mock_model:
            mock_model.query.join.return_value.join.return_value \
                .filter.return_value.order_by.return_value.first.return_value = None
            assert fn(ctx) is False

    def test_organismo_abierto_plazo_en_plazo_false(self):
        """Organismo abierto con traslado EN_PLAZO → False."""
        fn = _get_variable('traslado_organismo_titular_vencido')
        ctx = _ctx([_org(None)])
        tramite_stub = SimpleNamespace(tarea_espera=SimpleNamespace())
        vinculo = SimpleNamespace(tramite=tramite_stub)
        with patch('app.models.tramites_organismos.TramiteOrganismo') as mock_model, \
             patch('app.services.plazos.obtener_estado_plazo_tarea', return_value=_ep('EN_PLAZO')):
            mock_model.query.join.return_value.join.return_value \
                .filter.return_value.order_by.return_value.first.return_value = vinculo
            assert fn(ctx) is False

    def test_organismo_abierto_plazo_vencido_true(self):
        """Organismo abierto con traslado VENCIDO → True."""
        fn = _get_variable('traslado_organismo_titular_vencido')
        ctx = _ctx([_org(None)])
        tramite_stub = SimpleNamespace(tarea_espera=SimpleNamespace())
        vinculo = SimpleNamespace(tramite=tramite_stub)
        with patch('app.models.tramites_organismos.TramiteOrganismo') as mock_model, \
             patch('app.services.plazos.obtener_estado_plazo_tarea', return_value=_ep('VENCIDO')):
            mock_model.query.join.return_value.join.return_value \
                .filter.return_value.order_by.return_value.first.return_value = vinculo
            assert fn(ctx) is True

    def test_tramite_sin_espera_false(self):
        """Trámite creado pero sin su ESPERAR_PLAZO todavía: no hay plazo que medir."""
        fn = _get_variable('traslado_organismo_titular_vencido')
        ctx = _ctx([_org(None)])
        vinculo = SimpleNamespace(tramite=SimpleNamespace(tarea_espera=None))
        with patch('app.models.tramites_organismos.TramiteOrganismo') as mock_model, \
             patch('app.services.plazos.obtener_estado_plazo_tarea') as mock_plazo:
            mock_model.query.join.return_value.join.return_value \
                .filter.return_value.order_by.return_value.first.return_value = vinculo
            assert fn(ctx) is False
        mock_plazo.assert_not_called()

    def test_or_global_un_vencido_entre_varios_true(self):
        """Un organismo vencido y otro en plazo → True (OR global)."""
        fn = _get_variable('traslado_organismo_titular_vencido')
        ctx = _ctx([_org(None, id=1), _org(None, id=2)])
        tramite_stub = SimpleNamespace(tarea_espera=SimpleNamespace())
        vinculo = SimpleNamespace(tramite=tramite_stub)

        efectos = {'1': _ep('VENCIDO'), '2': _ep('EN_PLAZO')}
        call_count = 0

        def fake_plazo(tarea, **kwargs):
            nonlocal call_count
            call_count += 1
            return efectos[str(call_count)]

        with patch('app.models.tramites_organismos.TramiteOrganismo') as mock_model, \
             patch('app.services.plazos.obtener_estado_plazo_tarea', side_effect=fake_plazo):
            mock_model.query.join.return_value.join.return_value \
                .filter.return_value.order_by.return_value.first.return_value = vinculo
            assert fn(ctx) is True


# ---------------------------------------------------------------------------
# B) Helper _traslado_titular_vencido (serialización API)
# ---------------------------------------------------------------------------

class TestHelperSerializacion:

    def _fn(self):
        from app.services.consultas_organismos import traslado_titular_vencido
        return traslado_titular_vencido

    def test_sin_vinculo_false(self):
        """Organismo sin CONSULTA_TRASLADO_TITULAR → False."""
        oe = SimpleNamespace(id=10)
        with patch('app.models.tramites_organismos.TramiteOrganismo') as mock_model:
            mock_model.query.join.return_value.join.return_value \
                .filter.return_value.order_by.return_value.first.return_value = None
            assert self._fn()(oe) is False

    def test_tramite_vencido_true(self):
        """Trámite vinculado con plazo VENCIDO → True."""
        oe = SimpleNamespace(id=10)
        tramite_stub = SimpleNamespace(tarea_espera=SimpleNamespace())
        vinculo = SimpleNamespace(tramite=tramite_stub)
        with patch('app.models.tramites_organismos.TramiteOrganismo') as mock_model, \
             patch('app.services.plazos.obtener_estado_plazo_tarea', return_value=_ep('VENCIDO')):
            mock_model.query.join.return_value.join.return_value \
                .filter.return_value.order_by.return_value.first.return_value = vinculo
            assert self._fn()(oe) is True

    def test_tramite_en_plazo_false(self):
        """Trámite vinculado con plazo EN_PLAZO → False."""
        oe = SimpleNamespace(id=10)
        tramite_stub = SimpleNamespace(tarea_espera=SimpleNamespace())
        vinculo = SimpleNamespace(tramite=tramite_stub)
        with patch('app.models.tramites_organismos.TramiteOrganismo') as mock_model, \
             patch('app.services.plazos.obtener_estado_plazo_tarea', return_value=_ep('EN_PLAZO')):
            mock_model.query.join.return_value.join.return_value \
                .filter.return_value.order_by.return_value.first.return_value = vinculo
            assert self._fn()(oe) is False
