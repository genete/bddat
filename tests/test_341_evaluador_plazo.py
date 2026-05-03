"""Tests issue #341 sesión 4 — _evaluar_condiciones_plazo, _seleccionar_catalogo
y la integración en obtener_estado_plazo.

Bloques:
  A) _evaluar_condiciones_plazo  — función pura, sin BD, sin mocks de módulo.
  B) _seleccionar_catalogo       — BD mockeada (query chain + joinedload).
  C) obtener_estado_plazo        — integración: ruta legacy y ruta nueva.
  D) Anti-recursión              — ctx con variables que contienen estado_plazo.
  E) Caso real art. 131.1 párr. 2 — los dos escenarios del caso canónico.
"""
from datetime import date
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers comunes
# ---------------------------------------------------------------------------

def _mock_condicion(nombre_var, operador, valor, orden=1):
    """CondicionPlazo mínima para tests de _evaluar_condiciones_plazo."""
    c = MagicMock()
    c.variable = MagicMock(nombre=nombre_var)
    c.operador = operador
    c.valor = valor
    c.orden = orden
    return c


def _mock_entrada(orden=100, entrada_id=1, condiciones=None,
                  plazo_valor=30, plazo_unidad='DIAS_NATURALES',
                  campo_fecha=None, efecto_codigo='NINGUNO'):
    """CatalogoPlazo mínimo para tests de _seleccionar_catalogo."""
    e = MagicMock()
    e.id = entrada_id
    e.orden = orden
    e.condiciones = condiciones if condiciones is not None else []
    e.plazo_valor = plazo_valor
    e.plazo_unidad = plazo_unidad
    e.campo_fecha = campo_fecha or {'fk': 'documento_resultado_id'}
    e.efecto_plazo.codigo = efecto_codigo
    return e


def _mock_fase(tipo_fase_id, fecha_administrativa, tipo_fase_codigo='CONSULTAS'):
    """Fase mínima para obtener_estado_plazo."""
    fase = MagicMock()
    fase.tipo_fase_id = tipo_fase_id
    fase.tipo_fase = MagicMock(codigo=tipo_fase_codigo)
    doc = MagicMock()
    doc.fecha_administrativa = fecha_administrativa
    fase.documento_resultado = doc
    return fase


# ---------------------------------------------------------------------------
# A) _evaluar_condiciones_plazo — función pura, sin BD
# ---------------------------------------------------------------------------

def test_sin_condiciones_siempre_pasa():
    from app.services.plazos import _evaluar_condiciones_plazo
    assert _evaluar_condiciones_plazo([], {}) is True


def test_condicion_eq_cumplida():
    from app.services.plazos import _evaluar_condiciones_plazo
    cond = _mock_condicion('tiene_solicitud_aap_favorable', 'EQ', True)
    assert _evaluar_condiciones_plazo([cond], {'tiene_solicitud_aap_favorable': True}) is True


def test_condicion_eq_no_cumplida():
    from app.services.plazos import _evaluar_condiciones_plazo
    cond = _mock_condicion('tiene_solicitud_aap_favorable', 'EQ', True)
    assert _evaluar_condiciones_plazo([cond], {'tiene_solicitud_aap_favorable': False}) is False


def test_and_implicito_primera_falla_corta_evaluacion():
    from app.services.plazos import _evaluar_condiciones_plazo
    cond1 = _mock_condicion('tiene_solicitud_aap_favorable', 'EQ', True, orden=1)
    cond2 = _mock_condicion('es_solicitud_aac_pura', 'EQ', True, orden=2)
    variables = {'tiene_solicitud_aap_favorable': False, 'es_solicitud_aac_pura': True}
    assert _evaluar_condiciones_plazo([cond1, cond2], variables) is False


def test_and_implicito_todas_cumplen():
    from app.services.plazos import _evaluar_condiciones_plazo
    cond1 = _mock_condicion('tiene_solicitud_aap_favorable', 'EQ', True, orden=1)
    cond2 = _mock_condicion('es_solicitud_aac_pura', 'EQ', True, orden=2)
    variables = {'tiene_solicitud_aap_favorable': True, 'es_solicitud_aac_pura': True}
    assert _evaluar_condiciones_plazo([cond1, cond2], variables) is True


def test_variable_ausente_falla_silenciosamente():
    from app.services.plazos import _evaluar_condiciones_plazo
    cond = _mock_condicion('tiene_solicitud_aap_favorable', 'EQ', True)
    # variable no está en el dict → False con warning (sin excepción)
    assert _evaluar_condiciones_plazo([cond], {}) is False


def test_operador_desconocido_falla_silenciosamente():
    from app.services.plazos import _evaluar_condiciones_plazo
    cond = _mock_condicion('tiene_solicitud_aap_favorable', 'LIKE', True)
    assert _evaluar_condiciones_plazo([cond], {'tiene_solicitud_aap_favorable': True}) is False


def test_error_en_comparacion_falla_silenciosamente():
    """Si la lambda lanza excepción (ej. None > int), se captura y devuelve False."""
    from app.services.plazos import _evaluar_condiciones_plazo
    cond = _mock_condicion('tiene_solicitud_aap_favorable', 'GT', 5)
    # GT con None → el lambda de _OPERADORES devuelve False, no lanza
    assert _evaluar_condiciones_plazo([cond], {'tiene_solicitud_aap_favorable': None}) is False


# ---------------------------------------------------------------------------
# B) _seleccionar_catalogo — BD mockeada
# ---------------------------------------------------------------------------

def test_seleccionar_sin_condiciones_retorna_fallback():
    """Entrada sin condiciones siempre es válida."""
    from app.services.plazos import _seleccionar_catalogo
    entrada = _mock_entrada(orden=100, condiciones=[])
    with patch('app.models.catalogo_plazos.CatalogoPlazo') as MockCP, \
         patch('app.models.condiciones_plazo.CondicionPlazo'), \
         patch('app.services.plazos.joinedload', return_value=MagicMock()):
        MockCP.query.options.return_value.filter_by.return_value\
              .order_by.return_value.all.return_value = [entrada]
        result = _seleccionar_catalogo('FASE', 1, {})
    assert result is entrada


def test_seleccionar_condicion_dispara_gana_condicionada():
    """Entrada condicionada con variables que pasan sus condiciones → se devuelve antes que el fallback."""
    from app.services.plazos import _seleccionar_catalogo
    cond = _mock_condicion('tiene_solicitud_aap_favorable', 'EQ', True)
    entrada_condicionada = _mock_entrada(orden=10, entrada_id=1, condiciones=[cond])
    entrada_fallback = _mock_entrada(orden=100, entrada_id=2, condiciones=[])
    variables = {'tiene_solicitud_aap_favorable': True, 'es_solicitud_aac_pura': True}

    with patch('app.models.catalogo_plazos.CatalogoPlazo') as MockCP, \
         patch('app.models.condiciones_plazo.CondicionPlazo'), \
         patch('app.services.plazos.joinedload', return_value=MagicMock()):
        MockCP.query.options.return_value.filter_by.return_value\
              .order_by.return_value.all.return_value = [entrada_condicionada, entrada_fallback]
        result = _seleccionar_catalogo('FASE', 1, variables)
    assert result is entrada_condicionada


def test_seleccionar_condicion_no_dispara_gana_fallback():
    """Entrada condicionada cuyas variables no pasan → se salta y gana el fallback."""
    from app.services.plazos import _seleccionar_catalogo
    cond = _mock_condicion('tiene_solicitud_aap_favorable', 'EQ', True)
    entrada_condicionada = _mock_entrada(orden=10, entrada_id=1, condiciones=[cond])
    entrada_fallback = _mock_entrada(orden=100, entrada_id=2, condiciones=[])
    variables = {'tiene_solicitud_aap_favorable': False, 'es_solicitud_aac_pura': True}

    with patch('app.models.catalogo_plazos.CatalogoPlazo') as MockCP, \
         patch('app.models.condiciones_plazo.CondicionPlazo'), \
         patch('app.services.plazos.joinedload', return_value=MagicMock()):
        MockCP.query.options.return_value.filter_by.return_value\
              .order_by.return_value.all.return_value = [entrada_condicionada, entrada_fallback]
        result = _seleccionar_catalogo('FASE', 1, variables)
    assert result is entrada_fallback


def test_seleccionar_dos_condicionadas_primera_falla_segunda_pasa():
    """Con dos entradas condicionadas, se salta la que falla y devuelve la que pasa."""
    from app.services.plazos import _seleccionar_catalogo
    cond1 = _mock_condicion('tiene_solicitud_aap_favorable', 'EQ', True)
    cond2 = _mock_condicion('tiene_solicitud_aap_favorable', 'EQ', False)
    entrada1 = _mock_entrada(orden=5, entrada_id=1, condiciones=[cond1])   # falla
    entrada2 = _mock_entrada(orden=10, entrada_id=2, condiciones=[cond2])  # pasa
    variables = {'tiene_solicitud_aap_favorable': False}

    with patch('app.models.catalogo_plazos.CatalogoPlazo') as MockCP, \
         patch('app.models.condiciones_plazo.CondicionPlazo'), \
         patch('app.services.plazos.joinedload', return_value=MagicMock()):
        MockCP.query.options.return_value.filter_by.return_value\
              .order_by.return_value.all.return_value = [entrada1, entrada2]
        result = _seleccionar_catalogo('FASE', 1, variables)
    assert result is entrada2


def test_seleccionar_variable_ausente_no_dispara():
    """Variable no presente en dict → condición falla silenciosamente → se salta."""
    from app.services.plazos import _seleccionar_catalogo
    cond = _mock_condicion('tiene_solicitud_aap_favorable', 'EQ', True)
    entrada_condicionada = _mock_entrada(orden=10, entrada_id=1, condiciones=[cond])
    entrada_fallback = _mock_entrada(orden=100, entrada_id=2, condiciones=[])
    variables = {}  # variable ausente

    with patch('app.models.catalogo_plazos.CatalogoPlazo') as MockCP, \
         patch('app.models.condiciones_plazo.CondicionPlazo'), \
         patch('app.services.plazos.joinedload', return_value=MagicMock()):
        MockCP.query.options.return_value.filter_by.return_value\
              .order_by.return_value.all.return_value = [entrada_condicionada, entrada_fallback]
        result = _seleccionar_catalogo('FASE', 1, variables)
    assert result is entrada_fallback


def test_seleccionar_sin_entradas_retorna_none():
    from app.services.plazos import _seleccionar_catalogo
    with patch('app.models.catalogo_plazos.CatalogoPlazo') as MockCP, \
         patch('app.models.condiciones_plazo.CondicionPlazo'), \
         patch('app.services.plazos.joinedload', return_value=MagicMock()):
        MockCP.query.options.return_value.filter_by.return_value\
              .order_by.return_value.all.return_value = []
        result = _seleccionar_catalogo('FASE', 1, {'x': 1})
    assert result is None


def test_seleccionar_todas_condicionadas_fallan_retorna_none():
    """Si no hay fallback y todas las condicionadas fallan → None + warning."""
    from app.services.plazos import _seleccionar_catalogo
    cond = _mock_condicion('tiene_solicitud_aap_favorable', 'EQ', True)
    entrada = _mock_entrada(orden=10, condiciones=[cond])
    variables = {'tiene_solicitud_aap_favorable': False}

    with patch('app.models.catalogo_plazos.CatalogoPlazo') as MockCP, \
         patch('app.models.condiciones_plazo.CondicionPlazo'), \
         patch('app.services.plazos.joinedload', return_value=MagicMock()):
        MockCP.query.options.return_value.filter_by.return_value\
              .order_by.return_value.all.return_value = [entrada]
        result = _seleccionar_catalogo('FASE', 1, variables)
    assert result is None


# ---------------------------------------------------------------------------
# C) obtener_estado_plazo — ruta legacy y ruta nueva
# ---------------------------------------------------------------------------

HOY = date(2025, 6, 2)


def test_ctx_none_variables_none_usa_variables_dict_vacio():
    """Sin ctx ni variables → variables_dict={} → solo entradas sin condiciones aplican."""
    from app.services.plazos import obtener_estado_plazo
    r = obtener_estado_plazo(object(), 'FASE')
    assert r.estado == 'SIN_PLAZO'


def test_variables_vacio_usa_ruta_nueva_sin_condiciones():
    """variables={} → ruta nueva; entradas sin condiciones ganan; SIN_PLAZO si no hay entrada."""
    from app.services.plazos import obtener_estado_plazo
    fase = _mock_fase(tipo_fase_id=1, fecha_administrativa=date(2025, 5, 12))

    with patch('app.models.catalogo_plazos.CatalogoPlazo') as MockCP, \
         patch('app.models.condiciones_plazo.CondicionPlazo'), \
         patch('app.services.plazos.joinedload', return_value=MagicMock()):
        MockCP.query.options.return_value.filter_by.return_value\
              .order_by.return_value.all.return_value = []
        r = obtener_estado_plazo(fase, 'FASE', variables={})
    assert r.estado == 'SIN_PLAZO'


def test_variables_dict_selecciona_entrada_y_calcula_estado():
    """Con variables dict, selecciona catálogo y devuelve estado calculado."""
    from app.services.plazos import obtener_estado_plazo
    fase = _mock_fase(tipo_fase_id=1, fecha_administrativa=date(2025, 5, 12))
    entrada = _mock_entrada(orden=100, condiciones=[], plazo_valor=20,
                            plazo_unidad='DIAS_HABILES', efecto_codigo='SILENCIO_DESESTIMATORIO')

    with (patch('app.services.plazos._hoy', return_value=HOY),
          patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()),
          patch('app.models.catalogo_plazos.CatalogoPlazo') as MockCP,
          patch('app.models.condiciones_plazo.CondicionPlazo'),
          patch('app.services.plazos.joinedload', return_value=MagicMock())):
        MockCP.query.options.return_value.filter_by.return_value\
              .order_by.return_value.all.return_value = [entrada]
        r = obtener_estado_plazo(fase, 'FASE', variables={})
    assert r.estado == 'EN_PLAZO'
    assert r.fecha_limite == date(2025, 6, 9)


# ---------------------------------------------------------------------------
# D) Anti-recursión — ctx pasa excluir a _compilar_variables
# ---------------------------------------------------------------------------

def test_ctx_llama_compilar_variables_con_excluir():
    """Cuando se pasa ctx, _compilar_variables recibe excluir={'estado_plazo','efecto_plazo'}."""
    from app.services.plazos import obtener_estado_plazo
    from app.services.assembler import ExpedienteContext

    fase = _mock_fase(tipo_fase_id=1, fecha_administrativa=date(2025, 5, 1))
    ctx = MagicMock(spec=ExpedienteContext)

    with patch('app.services.plazos._seleccionar_catalogo', return_value=None) as mock_sel, \
         patch('app.services.assembler._compilar_variables', return_value={}) as mock_cv:
        obtener_estado_plazo(fase, 'FASE', ctx=ctx)

    mock_cv.assert_called_once_with(ctx, excluir={'estado_plazo', 'efecto_plazo'})
    mock_sel.assert_called_once_with('FASE', 'CONSULTAS', {})


def test_variables_directo_no_llama_compilar_variables():
    """Cuando se pasa variables dict directamente, no se llama a _compilar_variables."""
    from app.services.plazos import obtener_estado_plazo

    fase = _mock_fase(tipo_fase_id=1, fecha_administrativa=date(2025, 5, 1))

    with patch('app.services.plazos._seleccionar_catalogo', return_value=None), \
         patch('app.services.assembler._compilar_variables') as mock_cv:
        obtener_estado_plazo(fase, 'FASE', variables={'x': 1})

    mock_cv.assert_not_called()


# ---------------------------------------------------------------------------
# E) Caso real art. 131.1 párr. 2 RD 1955/2000
# ---------------------------------------------------------------------------
#
# Dos entradas en catalogo_plazos para la fase CONSULTAS (válida para AAP y AAC):
#   - orden=10,  plazo=15 días naturales, condiciones: tiene_solicitud_aap_favorable=True
#                                                     + es_solicitud_aac_pura=True
#   - orden=100, plazo=30 días naturales, sin condiciones (fallback general)

HOY_131 = date(2025, 5, 20)    # martes


def _entradas_art131():
    """Las dos entradas de catálogo para art. 131.1 párr. 2."""
    cond_aap = _mock_condicion('tiene_solicitud_aap_favorable', 'EQ', True, orden=1)
    cond_aac = _mock_condicion('es_solicitud_aac_pura', 'EQ', True, orden=2)
    entrada_15d = _mock_entrada(
        orden=10, entrada_id=1,
        condiciones=[cond_aap, cond_aac],
        plazo_valor=15, plazo_unidad='DIAS_NATURALES',
        campo_fecha={'fk': 'documento_solicitud_id'},
        efecto_codigo='NINGUNO',
    )
    entrada_30d = _mock_entrada(
        orden=100, entrada_id=2,
        condiciones=[],
        plazo_valor=30, plazo_unidad='DIAS_NATURALES',
        campo_fecha={'fk': 'documento_solicitud_id'},
        efecto_codigo='NINGUNO',
    )
    return entrada_15d, entrada_30d


def _mock_fase_aac(fecha_admin):
    """Fase CONSULTAS (cubre AAP y AAC) con documento_solicitud."""
    fase = MagicMock()
    fase.tipo_fase_id = 42
    fase.tipo_fase = MagicMock(codigo='CONSULTAS')
    fase.tareas = []
    doc_sol = MagicMock()
    doc_sol.fecha_administrativa = fecha_admin
    sol = MagicMock()
    sol.documento_solicitud = doc_sol
    fase.solicitud = sol
    # No tiene documento_resultado (campo_fecha apunta a documento_solicitud_id)
    fase.documento_solicitud = None  # la resolución va vía fase.solicitud
    return fase


def test_art131_con_aap_previa_usa_plazo_15_dias():
    """AAC con AAP previa favorable → entry condicionada (15 días)."""
    from app.services.plazos import obtener_estado_plazo
    from datetime import date as d

    fecha_admin = d(2025, 5, 5)   # lunes
    fase = _mock_fase_aac(fecha_admin)

    variables = {
        'tiene_solicitud_aap_favorable': True,
        'es_solicitud_aac_pura': True,
    }
    entrada_15d, entrada_30d = _entradas_art131()

    with (patch('app.services.plazos._hoy', return_value=HOY_131),
          patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()),
          patch('app.models.catalogo_plazos.CatalogoPlazo') as MockCP,
          patch('app.models.condiciones_plazo.CondicionPlazo'),
          patch('app.services.plazos.joinedload', return_value=MagicMock())):
        MockCP.query.options.return_value.filter_by.return_value\
              .order_by.return_value.all.return_value = [entrada_15d, entrada_30d]
        r = obtener_estado_plazo(fase, 'FASE', variables=variables)

    # fecha_admin=5 may + 15 días naturales = 20 may; hoy=20 may → fecha_limite correcta
    assert r.fecha_limite == d(2025, 5, 20)
    assert r.estado in ('EN_PLAZO', 'PROXIMO_VENCER', 'VENCIDO')


def test_art131_sin_aap_previa_usa_plazo_30_dias():
    """AAC sin AAP previa → fallback (30 días)."""
    from app.services.plazos import obtener_estado_plazo
    from datetime import date as d

    fecha_admin = d(2025, 5, 5)
    fase = _mock_fase_aac(fecha_admin)

    variables = {
        'tiene_solicitud_aap_favorable': False,
        'es_solicitud_aac_pura': True,
    }
    entrada_15d, entrada_30d = _entradas_art131()

    with (patch('app.services.plazos._hoy', return_value=HOY_131),
          patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()),
          patch('app.models.catalogo_plazos.CatalogoPlazo') as MockCP,
          patch('app.models.condiciones_plazo.CondicionPlazo'),
          patch('app.services.plazos.joinedload', return_value=MagicMock())):
        MockCP.query.options.return_value.filter_by.return_value\
              .order_by.return_value.all.return_value = [entrada_15d, entrada_30d]
        r = obtener_estado_plazo(fase, 'FASE', variables=variables)

    # fecha_admin=5 may + 30 días naturales = 4 jun (miércoles, hábil)
    assert r.fecha_limite == d(2025, 6, 4)
    assert r.estado == 'EN_PLAZO'
    assert r.dias_restantes == 12   # hábiles entre 20 may y 4 jun (4+5+3)


def test_art131_seleccion_correcta_verificada_via_plazo_valor():
    """Confirma que la entrada correcta (15 vs 30) queda registrada en fecha_limite."""
    from app.services.plazos import obtener_estado_plazo
    from datetime import date as d

    fecha_admin = d(2025, 5, 1)
    fase = _mock_fase_aac(fecha_admin)
    entrada_15d, entrada_30d = _entradas_art131()

    # Con condiciones satisfechas → 15 días
    variables_con = {'tiene_solicitud_aap_favorable': True, 'es_solicitud_aac_pura': True}
    # Sin condición satisfecha → 30 días
    variables_sin = {'tiene_solicitud_aap_favorable': False, 'es_solicitud_aac_pura': True}

    with (patch('app.services.plazos._hoy', return_value=d(2025, 5, 1)),
          patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()),
          patch('app.models.catalogo_plazos.CatalogoPlazo') as MockCP,
          patch('app.models.condiciones_plazo.CondicionPlazo'),
          patch('app.services.plazos.joinedload', return_value=MagicMock())):
        MockCP.query.options.return_value.filter_by.return_value\
              .order_by.return_value.all.return_value = [entrada_15d, entrada_30d]

        r_con = obtener_estado_plazo(fase, 'FASE', variables=variables_con)
        r_sin = obtener_estado_plazo(fase, 'FASE', variables=variables_sin)

    # 1 may + 15 nat = 16 may (viernes)
    assert r_con.fecha_limite == d(2025, 5, 16)
    # 1 may + 30 nat = 31 may (sábado) → prorroga art. 30.5 → 2 jun (lunes)
    assert r_sin.fecha_limite == d(2025, 6, 2)
