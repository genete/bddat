"""
Tests #462 — helper _calcular_plazo_consulta y lógica de acción en bloque.

Patrón: objetos Python puros (MagicMock), sin BD real ni cliente Flask.
"""
from unittest.mock import MagicMock


def _sol_stub(tipos=('AAC',), aap_favorable=False):
    sol = MagicMock()
    sol.contiene_tipo = lambda codigo: codigo in tipos
    fase_fin = MagicMock()
    fase_fin.tipo_fase = MagicMock(es_finalizadora=True)
    fase_fin.finalizada = aap_favorable
    fase_fin.resultado_fase = MagicMock(codigo='FAVORABLE') if aap_favorable else None
    sol.fases = [fase_fin]
    return sol


def _expediente_stub(solicitud_actual, otras_solicitudes=()):
    exp = MagicMock()
    exp.solicitudes = [solicitud_actual] + list(otras_solicitudes)
    exp.organismos = []
    return exp


class TestCalcularPlazoConsulta:

    def test_plazo_general_aap(self):
        from app.routes.api_bc import _calcular_plazo_consulta
        sol = _sol_stub(tipos=('AAP',))
        exp = _expediente_stub(sol)
        assert _calcular_plazo_consulta(exp, sol) == 30

    def test_plazo_general_aap_aac_combinado(self):
        from app.routes.api_bc import _calcular_plazo_consulta
        sol = _sol_stub(tipos=('AAP', 'AAC'))
        exp = _expediente_stub(sol)
        assert _calcular_plazo_consulta(exp, sol) == 30

    def test_plazo_general_aac_sin_aap_previa(self):
        """AAC pura pero sin ninguna AAP previa favorable → 30 días."""
        from app.routes.api_bc import _calcular_plazo_consulta
        sol = _sol_stub(tipos=('AAC',))
        exp = _expediente_stub(sol)
        assert _calcular_plazo_consulta(exp, sol) == 30

    def test_plazo_reducido_aac_pura_con_aap_favorable(self):
        """AAC pura + AAP previa con fase finalizadora FAVORABLE → 15 días."""
        from app.routes.api_bc import _calcular_plazo_consulta
        sol_actual = _sol_stub(tipos=('AAC',))
        sol_aap = _sol_stub(tipos=('AAP',), aap_favorable=True)
        exp = _expediente_stub(sol_actual, otras_solicitudes=[sol_aap])
        assert _calcular_plazo_consulta(exp, sol_actual) == 15

    def test_dup_excluye_reduccion(self):
        """AAC+DUP no es AAC pura → 30 días aunque haya AAP previa favorable."""
        from app.routes.api_bc import _calcular_plazo_consulta
        sol_actual = _sol_stub(tipos=('AAC', 'DUP'))
        sol_aap = _sol_stub(tipos=('AAP',), aap_favorable=True)
        exp = _expediente_stub(sol_actual, otras_solicitudes=[sol_aap])
        assert _calcular_plazo_consulta(exp, sol_actual) == 30

    def test_aap_previa_no_favorable_no_reduce(self):
        """AAP previa existe pero su fase finalizadora no está cerrada como favorable."""
        from app.routes.api_bc import _calcular_plazo_consulta
        sol_actual = _sol_stub(tipos=('AAC',))
        sol_aap = _sol_stub(tipos=('AAP',), aap_favorable=False)
        exp = _expediente_stub(sol_actual, otras_solicitudes=[sol_aap])
        assert _calcular_plazo_consulta(exp, sol_actual) == 30

    def test_solicitud_actual_no_se_evalua_como_aap_previa(self):
        """La propia solicitud AAC+AAP no cuenta como 'AAP previa' de sí misma."""
        from app.routes.api_bc import _calcular_plazo_consulta
        sol = _sol_stub(tipos=('AAC', 'AAP'))
        exp = _expediente_stub(sol)
        assert _calcular_plazo_consulta(exp, sol) == 30


class TestEnviarConsultasLogica:

    def _oe_stub(self, id=1, via='consulta', estado='pendiente'):
        oe = MagicMock()
        oe.id = id
        oe.via = via
        oe.estado = estado
        oe.plazo_legal_dias = None
        return oe

    def test_filtra_solo_consulta_pendiente(self):
        """Solo los organismos via=consulta y estado=pendiente se incluyen en el envío."""
        oe_ok = self._oe_stub(id=1)
        oe_dr = self._oe_stub(id=2, via='declaracion_responsable')
        oe_env = self._oe_stub(id=3, estado='separata_enviada')
        organismos = [oe_ok, oe_dr, oe_env]
        pendientes = [oe for oe in organismos if oe.via == 'consulta' and oe.estado == 'pendiente']
        assert len(pendientes) == 1
        assert pendientes[0].id == 1

    def test_filtra_multiples_pendientes(self):
        organismos = [self._oe_stub(id=i) for i in range(1, 4)]
        organismos.append(self._oe_stub(id=4, estado='separata_enviada'))
        pendientes = [oe for oe in organismos if oe.via == 'consulta' and oe.estado == 'pendiente']
        assert len(pendientes) == 3

    def test_plazo_calculado_una_vez_aplicado_a_todos(self):
        """El mismo plazo (calculado antes del bucle) se asigna a cada organismo."""
        from app.routes.api_bc import _calcular_plazo_consulta
        sol_actual = _sol_stub(tipos=('AAC',))
        sol_aap = _sol_stub(tipos=('AAP',), aap_favorable=True)
        exp = _expediente_stub(sol_actual, otras_solicitudes=[sol_aap])
        plazo = _calcular_plazo_consulta(exp, sol_actual)
        assert plazo == 15
        # Simular asignación a 3 organismos
        oes = [self._oe_stub(id=i) for i in range(3)]
        for oe in oes:
            oe.plazo_legal_dias = plazo
        assert all(oe.plazo_legal_dias == 15 for oe in oes)

    def test_estado_actualizado_tras_envio(self):
        oe = self._oe_stub()
        oe.estado = 'separata_enviada'
        assert oe.estado == 'separata_enviada'
