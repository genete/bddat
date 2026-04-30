"""
Tests issue #172 — algoritmo de cómputo de plazos y obtener_estado_plazo.

Bloques:
  A) calcular_fecha_fin    — función pura, sin BD ni app context.
  B) obtener_estado_plazo  — cuatro estados; BD y fecha.today() mockeados.
"""
from datetime import date
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Fixture: festivos nacionales + andaluces 2025-2026 (sólo días laborables)
# ---------------------------------------------------------------------------

INHABILES = frozenset({
    date(2025, 1, 1),   date(2025, 1, 6),
    date(2025, 2, 28),  date(2025, 4, 17), date(2025, 4, 18), date(2025, 4, 21),
    date(2025, 5, 1),   date(2025, 8, 15),
    date(2025, 12, 8),  date(2025, 12, 25),
    date(2026, 1, 1),   date(2026, 1, 6),
    date(2026, 4, 2),   date(2026, 4, 3),  date(2026, 4, 6),
    date(2026, 5, 1),   date(2026, 10, 12),
    date(2026, 12, 8),  date(2026, 12, 25),
})


# ---------------------------------------------------------------------------
# A) Tests unitarios de calcular_fecha_fin — sin BD
# ---------------------------------------------------------------------------

class TestCalcularFechaFinDiasHabiles:

    def test_basico_sin_inhabiles(self):
        from app.services.plazos import calcular_fecha_fin
        fecha_limite = calcular_fecha_fin(
            date(2025, 6, 2),   # lunes
            5, 'DIAS_HABILES', frozenset(),
        )
        assert fecha_limite == date(2025, 6, 9)  # lunes siguiente (5 hábiles: mar-vie + lunes)

    def test_salta_fin_de_semana(self):
        from app.services.plazos import calcular_fecha_fin
        fecha_limite = calcular_fecha_fin(
            date(2025, 6, 6),   # viernes
            3, 'DIAS_HABILES', frozenset(),
        )
        assert fecha_limite == date(2025, 6, 11)  # mié (7=sáb, 8=dom, 9=lun, 10=mar, 11=mié)

    def test_salta_festivo_en_mitad(self):
        from app.services.plazos import calcular_fecha_fin
        fecha_limite = calcular_fecha_fin(
            date(2025, 4, 16),   # miércoles (día anterior a Jueves Santo 2025)
            5, 'DIAS_HABILES', INHABILES,
        )
        # Inhabiles: jue 17 + vie 18 + sáb 19 + dom 20 + lun 21 (Lunes Pascua AND)
        # Cómputo arranca jue 17 (inhábil) → vie 18 (inhábil) → lun 21 (inhábil AND)
        # Día 1=mar 22, 2=mié 23, 3=jue 24, 4=vie 25, 5=lun 28
        assert fecha_limite == date(2025, 4, 28)

    def test_resultado_siempre_habil(self):
        from app.services.plazos import calcular_fecha_fin, _es_habil
        fecha_limite = calcular_fecha_fin(
            date(2025, 6, 2), 10, 'DIAS_HABILES', INHABILES,
        )
        assert _es_habil(fecha_limite, INHABILES)


class TestCalcularFechaFinDiasNaturales:

    def test_basico_sin_inhabiles(self):
        from app.services.plazos import calcular_fecha_fin
        fecha_limite = calcular_fecha_fin(
            date(2025, 6, 1),   # domingo
            30, 'DIAS_NATURALES', frozenset(),
        )
        assert fecha_limite == date(2025, 7, 1)  # 1 jul = martes → hábil ✓

    def test_prorroga_art30_5_si_cae_sabado(self):
        from app.services.plazos import calcular_fecha_fin
        fecha_limite = calcular_fecha_fin(
            date(2025, 6, 3),   # martes: +4 días = sábado 7
            4, 'DIAS_NATURALES', frozenset(),
        )
        assert fecha_limite == date(2025, 6, 9)  # sáb 7 inhábil → dom 8 inhábil → lun 9

    def test_prorroga_sobre_festivo(self):
        from app.services.plazos import calcular_fecha_fin
        fecha_limite = calcular_fecha_fin(
            date(2025, 4, 30),   # miércoles: +1 día = 1 mayo (festivo)
            1, 'DIAS_NATURALES', INHABILES,
        )
        assert fecha_limite == date(2025, 5, 2)  # 1 mayo inhábil → 2 mayo (viernes)


class TestCalcularFechaFinMeses:

    def test_basico(self):
        from app.services.plazos import calcular_fecha_fin
        fecha_limite = calcular_fecha_fin(
            date(2025, 1, 10),   # viernes; 3 meses = 10 abr 2025 (jueves, hábil)
            3, 'MESES', frozenset(),
        )
        assert fecha_limite == date(2025, 4, 10)

    def test_ultimo_dia_mes_cuando_no_existe(self):
        from app.services.plazos import calcular_fecha_fin
        fecha_limite = calcular_fecha_fin(
            date(2025, 1, 31),
            1, 'MESES', frozenset(),
        )
        assert fecha_limite == date(2025, 2, 28)  # feb no tiene día 31

    def test_cruza_anyo(self):
        from app.services.plazos import calcular_fecha_fin
        fecha_limite = calcular_fecha_fin(
            date(2025, 11, 6),
            3, 'MESES', frozenset(),
        )
        assert fecha_limite == date(2026, 2, 6)

    def test_prorroga_art30_5(self):
        from app.services.plazos import calcular_fecha_fin
        fecha_limite = calcular_fecha_fin(
            date(2025, 5, 4),   # domingo; 3 meses = 4 ago (lunes) ← sin inhabiles → hábil
            3, 'MESES', frozenset(),
        )
        assert fecha_limite == date(2025, 8, 4)

    def test_prorroga_sobre_festivo_agosto(self):
        from app.services.plazos import calcular_fecha_fin
        fecha_limite = calcular_fecha_fin(
            date(2025, 5, 15),   # 3 meses = 15 ago 2025 (festivo nacional)
            3, 'MESES', INHABILES,
        )
        assert fecha_limite == date(2025, 8, 18)  # 15=festivo, 16=sáb, 17=dom, 18=lun


class TestCalcularFechaFinAnos:

    def test_basico(self):
        from app.services.plazos import calcular_fecha_fin
        fecha_limite = calcular_fecha_fin(
            date(2025, 3, 17),   # lunes; +1 año = 17 mar 2026 (martes, hábil)
            1, 'ANOS', frozenset(),
        )
        assert fecha_limite == date(2026, 3, 17)

    def test_bisiesto_29_feb(self):
        from app.services.plazos import calcular_fecha_fin
        fecha_limite = calcular_fecha_fin(
            date(2024, 2, 29),   # año bisiesto; +1 año → 2025 no tiene 29 feb
            1, 'ANOS', frozenset(),
        )
        assert fecha_limite == date(2025, 2, 28)

    def test_prorroga_art30_5(self):
        from app.services.plazos import calcular_fecha_fin
        fecha_limite = calcular_fecha_fin(
            date(2025, 1, 25),   # +1 año = 25 ene 2026 (domingo)
            1, 'ANOS', frozenset(),
        )
        assert fecha_limite == date(2026, 1, 26)   # lunes siguiente


# ---------------------------------------------------------------------------
# Helpers para tests de obtener_estado_plazo
# ---------------------------------------------------------------------------

HOY = date(2025, 6, 2)   # lunes fijo para todos los tests de estado


def _mock_catalogo(plazo_valor, plazo_unidad, campo_fecha, efecto_codigo):
    m = MagicMock()
    m.plazo_valor = plazo_valor
    m.plazo_unidad = plazo_unidad
    m.campo_fecha = campo_fecha
    m.efecto_plazo.codigo = efecto_codigo
    m.condiciones = []
    return m


def _mock_fase(tipo_fase_id, fecha_administrativa):
    """Fase mínima con tipo_fase_id y documento_resultado.fecha_administrativa."""
    fase = MagicMock()
    fase.tipo_fase_id = tipo_fase_id
    doc = MagicMock()
    doc.fecha_administrativa = fecha_administrativa
    fase.documento_resultado = doc
    return fase


# ---------------------------------------------------------------------------
# B) Tests de obtener_estado_plazo — BD y today() mockeados
# ---------------------------------------------------------------------------

class TestObtenerEstadoPlazoSinPlazo:

    def test_elemento_none(self):
        from app.services.plazos import obtener_estado_plazo
        r = obtener_estado_plazo(None, 'FASE')
        assert r.estado == 'SIN_PLAZO'
        assert r.efecto == 'NINGUNO'
        assert r.fecha_limite is None
        assert r.dias_restantes is None

    def test_elemento_dict(self):
        from app.services.plazos import obtener_estado_plazo
        r = obtener_estado_plazo({'tipo_fase': MagicMock()}, 'FASE')
        assert r.estado == 'SIN_PLAZO'

    def test_sin_tipo_elemento_id(self):
        from app.services.plazos import obtener_estado_plazo
        r = obtener_estado_plazo(object(), 'FASE')
        assert r.estado == 'SIN_PLAZO'

    def test_sin_entrada_catalogo(self):
        from app.services.plazos import obtener_estado_plazo
        fase = _mock_fase(tipo_fase_id=999, fecha_administrativa=date(2025, 1, 1))
        with patch('app.models.catalogo_plazos.CatalogoPlazo') as mock_cp, \
             patch('app.models.condiciones_plazo.CondicionPlazo'), \
             patch('app.services.plazos.joinedload', return_value=MagicMock()):
            mock_cp.query.options.return_value.filter_by.return_value\
                  .order_by.return_value.all.return_value = []
            r = obtener_estado_plazo(fase, 'FASE')
        assert r.estado == 'SIN_PLAZO'

    def test_sin_fecha_acto(self):
        from app.services.plazos import obtener_estado_plazo
        fase = MagicMock()
        fase.tipo_fase_id = 1
        fase.documento_resultado = None
        fase.solicitud = None
        catalogo = _mock_catalogo(20, 'DIAS_HABILES', {'fk': 'documento_resultado_id'}, 'SILENCIO_DESESTIMATORIO')
        with patch('app.models.catalogo_plazos.CatalogoPlazo') as mock_cp, \
             patch('app.models.condiciones_plazo.CondicionPlazo'), \
             patch('app.services.plazos.joinedload', return_value=MagicMock()):
            mock_cp.query.options.return_value.filter_by.return_value\
                  .order_by.return_value.all.return_value = [catalogo]
            r = obtener_estado_plazo(fase, 'FASE')
        assert r.estado == 'SIN_PLAZO'


class TestObtenerEstadoPlazoEnPlazo:

    def test_en_plazo(self):
        """fecha_acto=12 may → 20 hábiles → 9 jun; hoy=2 jun; dias=6 > 5 → EN_PLAZO"""
        from app.services.plazos import obtener_estado_plazo
        fase = _mock_fase(tipo_fase_id=1, fecha_administrativa=date(2025, 5, 12))
        catalogo = _mock_catalogo(20, 'DIAS_HABILES', {'fk': 'documento_resultado_id'}, 'SILENCIO_DESESTIMATORIO')
        with (patch('app.services.plazos._hoy', return_value=HOY),
              patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()),
              patch('app.models.catalogo_plazos.CatalogoPlazo') as mock_cp,
              patch('app.models.condiciones_plazo.CondicionPlazo'),
              patch('app.services.plazos.joinedload', return_value=MagicMock())):
            mock_cp.query.options.return_value.filter_by.return_value\
                  .order_by.return_value.all.return_value = [catalogo]
            r = obtener_estado_plazo(fase, 'FASE')
        assert r.estado == 'EN_PLAZO'
        assert r.efecto == 'SILENCIO_DESESTIMATORIO'
        assert r.fecha_limite == date(2025, 6, 9)
        assert r.dias_restantes == 6


class TestObtenerEstadoPlazoProximoVencer:

    def test_proximo_vencer(self):
        """fecha_acto=9 may → 20 hábiles → 6 jun; hoy=2 jun; dias=5 ≤ 5 → PROXIMO_VENCER"""
        from app.services.plazos import obtener_estado_plazo
        fase = _mock_fase(tipo_fase_id=2, fecha_administrativa=date(2025, 5, 9))
        catalogo = _mock_catalogo(20, 'DIAS_HABILES', {'fk': 'documento_resultado_id'}, 'RESPONSABILIDAD_DISCIPLINARIA')
        with (patch('app.services.plazos._hoy', return_value=HOY),
              patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()),
              patch('app.models.catalogo_plazos.CatalogoPlazo') as mock_cp,
              patch('app.models.condiciones_plazo.CondicionPlazo'),
              patch('app.services.plazos.joinedload', return_value=MagicMock())):
            mock_cp.query.options.return_value.filter_by.return_value\
                  .order_by.return_value.all.return_value = [catalogo]
            r = obtener_estado_plazo(fase, 'FASE')
        assert r.estado == 'PROXIMO_VENCER'
        assert r.efecto == 'RESPONSABILIDAD_DISCIPLINARIA'
        assert r.fecha_limite == date(2025, 6, 6)
        assert r.dias_restantes == 5


class TestObtenerEstadoPlazoVencido:

    def test_vencido(self):
        """fecha_acto=16 may → 10 hábiles → 30 may; hoy=2 jun > 30 may → VENCIDO"""
        from app.services.plazos import obtener_estado_plazo
        fase = _mock_fase(tipo_fase_id=3, fecha_administrativa=date(2025, 5, 16))
        catalogo = _mock_catalogo(10, 'DIAS_HABILES', {'fk': 'documento_resultado_id'}, 'SILENCIO_ESTIMATORIO')
        with (patch('app.services.plazos._hoy', return_value=HOY),
              patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()),
              patch('app.models.catalogo_plazos.CatalogoPlazo') as mock_cp,
              patch('app.models.condiciones_plazo.CondicionPlazo'),
              patch('app.services.plazos.joinedload', return_value=MagicMock())):
            mock_cp.query.options.return_value.filter_by.return_value\
                  .order_by.return_value.all.return_value = [catalogo]
            r = obtener_estado_plazo(fase, 'FASE')
        assert r.estado == 'VENCIDO'
        assert r.efecto == 'SILENCIO_ESTIMATORIO'
        assert r.fecha_limite == date(2025, 5, 30)
        assert r.dias_restantes == -1   # 1 día hábil de retraso (lun 2 jun)
