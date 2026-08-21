"""Tests issue #341 sesión 4 — _evaluar_condiciones_plazo, _seleccionar_catalogo
y la integración en obtener_estado_plazo.

Reanclados a nivel TAREA en #788: el plazo del art. 131 no es de la fase
CONSULTAS sino de cada organismo consultado, y corre desde la notificación de SU
separata — un acto, y todo acto es una tarea. Las dos entradas del caso canónico
viven hoy en `ANY/ANY/ANY/CONSULTA_SEPARATA/ESPERAR_PLAZO`, con las mismas dos
condiciones y con los plazos que fija la norma (15 y 30 días HÁBILES; las filas
de nivel fase que se retiraron los contaban como naturales desde la solicitud).

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
                  plazo_valor=30, plazo_unidad='DIAS_HABILES',
                  campo_fecha=None, efecto_codigo='NINGUNO',
                  camino='ANY/ANY/ANY/CONSULTA_SEPARATA/ESPERAR_PLAZO'):
    """CatalogoPlazo mínimo para tests de _seleccionar_catalogo.

    `camino` (#785) por defecto casa con la espera de cualquier CONSULTA_SEPARATA,
    que es el nivel que usan estos tests desde #788.
    """
    e = MagicMock()
    e.id = entrada_id
    e.orden = orden
    e.condiciones = condiciones if condiciones is not None else []
    e.plazo_valor = plazo_valor
    e.plazo_unidad = plazo_unidad
    e.campo_fecha = campo_fecha or {'rol': 'CONSUMIDO'}
    # Explícitos para que no salgan MagicMock (truthy): estos tests miden la
    # selección de entrada, no el cumplimiento ni la suspensión (#778).
    e.campo_fecha_cumplimiento = None
    e.suspende_plazo_solicitud = False
    e.efecto_plazo.codigo = efecto_codigo
    e.camino = camino
    return e


def _ascendencia_tarea(tarea, tipo_tarea_codigo='ESPERAR_PLAZO',
                       tipo_tramite_codigo='CONSULTA_SEPARATA',
                       tipo_fase_codigo='CONSULTAS', siglas='AAC',
                       tipo_expediente='Distribucion'):
    """Cuelga de la tarea la ascendencia que compilar_camino necesita (#785).

    Con MagicMock puro los segmentos salen MagicMock y el join del camino falla:
    hay que fijar strings reales en cada eslabón.
    """
    tarea.tipo_tarea = MagicMock(codigo=tipo_tarea_codigo)
    tarea.tramite.tipo_tramite = MagicMock(codigo=tipo_tramite_codigo)
    tarea.tramite.fase.tipo_fase = MagicMock(codigo=tipo_fase_codigo)
    tarea.tramite.fase.solicitud.tipo_solicitud = MagicMock(siglas=siglas)
    tarea.tramite.fase.solicitud.expediente.tipo_expediente = MagicMock(tipo=tipo_expediente)
    return tarea


def _mock_tarea_camino(**kwargs):
    """Tarea mínima solo para _seleccionar_catalogo (sin documento)."""
    tarea = _ascendencia_tarea(MagicMock(), **kwargs)
    tarea.documentos_consumidos = []
    tarea.documento_producido = None
    return tarea


def _mock_tarea(fecha_administrativa, **kwargs):
    """Tarea ESPERAR_PLAZO con el justificante que porta la fecha de inicio."""
    tarea = _mock_tarea_camino(**kwargs)
    doc = MagicMock()
    doc.fecha_administrativa = fecha_administrativa
    tarea.documentos_consumidos = [doc]
    return tarea


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
        result = _seleccionar_catalogo(_mock_tarea_camino(), 'TAREA',{})
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
        result = _seleccionar_catalogo(_mock_tarea_camino(), 'TAREA',variables)
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
        result = _seleccionar_catalogo(_mock_tarea_camino(), 'TAREA',variables)
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
        result = _seleccionar_catalogo(_mock_tarea_camino(), 'TAREA',variables)
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
        result = _seleccionar_catalogo(_mock_tarea_camino(), 'TAREA',variables)
    assert result is entrada_fallback


def test_seleccionar_sin_entradas_retorna_none():
    from app.services.plazos import _seleccionar_catalogo
    with patch('app.models.catalogo_plazos.CatalogoPlazo') as MockCP, \
         patch('app.models.condiciones_plazo.CondicionPlazo'), \
         patch('app.services.plazos.joinedload', return_value=MagicMock()):
        MockCP.query.options.return_value.filter_by.return_value\
              .order_by.return_value.all.return_value = []
        result = _seleccionar_catalogo(_mock_tarea_camino(), 'TAREA',{'x': 1})
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
        result = _seleccionar_catalogo(_mock_tarea_camino(), 'TAREA',variables)
    assert result is None


# ---------------------------------------------------------------------------
# C) obtener_estado_plazo — ruta legacy y ruta nueva
# ---------------------------------------------------------------------------

HOY = date(2025, 6, 2)


def test_ctx_none_variables_none_usa_variables_dict_vacio():
    """Sin ctx ni variables → variables_dict={} → solo entradas sin condiciones aplican."""
    from app.services.plazos import obtener_estado_plazo_tarea
    r = obtener_estado_plazo_tarea(object())
    assert r.estado == 'SIN_PLAZO'


def test_variables_vacio_usa_ruta_nueva_sin_condiciones():
    """variables={} → ruta nueva; entradas sin condiciones ganan; SIN_PLAZO si no hay entrada."""
    from app.services.plazos import obtener_estado_plazo_tarea
    tarea = _mock_tarea(fecha_administrativa=date(2025, 5, 12))

    with patch('app.models.catalogo_plazos.CatalogoPlazo') as MockCP, \
         patch('app.models.condiciones_plazo.CondicionPlazo'), \
         patch('app.services.plazos.joinedload', return_value=MagicMock()):
        MockCP.query.options.return_value.filter_by.return_value\
              .order_by.return_value.all.return_value = []
        r = obtener_estado_plazo_tarea(tarea, variables={})
    assert r.estado == 'SIN_PLAZO'


def test_variables_dict_selecciona_entrada_y_calcula_estado():
    """Con variables dict, selecciona catálogo y devuelve estado calculado."""
    from app.services.plazos import obtener_estado_plazo_tarea
    tarea = _mock_tarea(fecha_administrativa=date(2025, 5, 12))
    entrada = _mock_entrada(orden=100, condiciones=[], plazo_valor=20,
                            plazo_unidad='DIAS_HABILES', efecto_codigo='SILENCIO_DESESTIMATORIO')

    with (patch('app.services.plazos._hoy', return_value=HOY),
          patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()),
          patch('app.models.catalogo_plazos.CatalogoPlazo') as MockCP,
          patch('app.models.condiciones_plazo.CondicionPlazo'),
          patch('app.services.plazos.joinedload', return_value=MagicMock())):
        MockCP.query.options.return_value.filter_by.return_value\
              .order_by.return_value.all.return_value = [entrada]
        r = obtener_estado_plazo_tarea(tarea, variables={})
    assert r.estado == 'EN_PLAZO'
    assert r.fecha_limite == date(2025, 6, 9)


# ---------------------------------------------------------------------------
# D) Anti-recursión — ctx pasa excluir a _compilar_variables
# ---------------------------------------------------------------------------

def test_ctx_llama_compilar_variables_con_excluir():
    """Cuando se pasa ctx, _compilar_variables recibe excluir={'estado_plazo','efecto_plazo'}."""
    from app.services.plazos import obtener_estado_plazo_tarea
    from app.services.assembler import ExpedienteContext

    tarea = _mock_tarea(fecha_administrativa=date(2025, 5, 1))
    ctx = MagicMock(spec=ExpedienteContext)

    with patch('app.services.plazos._seleccionar_catalogo', return_value=None) as mock_sel, \
         patch('app.services.assembler._compilar_variables', return_value={}) as mock_cv:
        obtener_estado_plazo_tarea(tarea, ctx=ctx)

    mock_cv.assert_called_once_with(ctx, excluir={'estado_plazo', 'efecto_plazo'})
    # #785: recibe el elemento, no su código de tipo — el camino lo deriva dentro.
    mock_sel.assert_called_once_with(tarea, 'TAREA', {})


def test_variables_directo_no_llama_compilar_variables():
    """Cuando se pasa variables dict directamente, no se llama a _compilar_variables."""
    from app.services.plazos import obtener_estado_plazo_tarea

    tarea = _mock_tarea(fecha_administrativa=date(2025, 5, 1))

    with patch('app.services.plazos._seleccionar_catalogo', return_value=None), \
         patch('app.services.assembler._compilar_variables') as mock_cv:
        obtener_estado_plazo_tarea(tarea, variables={'x': 1})

    mock_cv.assert_not_called()


# ---------------------------------------------------------------------------
# E) Caso real art. 131.1 párr. 2 RD 1955/2000
# ---------------------------------------------------------------------------
#
# Dos entradas en catalogo_plazos para la espera de CONSULTA_SEPARATA:
#   - orden=10,  plazo=15 días hábiles, condiciones: tiene_solicitud_aap_favorable=True
#                                                    + es_solicitud_aac_pura=True
#   - orden=100, plazo=30 días hábiles, sin condiciones (fallback general)
#
# El plazo corre desde la notificación de la separata a SU organismo —el
# justificante que consume la espera—, no desde la fecha de solicitud (#788).

HOY_131 = date(2025, 5, 20)    # martes


def _entradas_art131():
    """Las dos entradas de catálogo para art. 131.1 párr. 2."""
    cond_aap = _mock_condicion('tiene_solicitud_aap_favorable', 'EQ', True, orden=1)
    cond_aac = _mock_condicion('es_solicitud_aac_pura', 'EQ', True, orden=2)
    entrada_15d = _mock_entrada(
        orden=10, entrada_id=1,
        condiciones=[cond_aap, cond_aac],
        plazo_valor=15, plazo_unidad='DIAS_HABILES',
        efecto_codigo='CONFORMIDAD_PRESUNTA',
    )
    entrada_30d = _mock_entrada(
        orden=100, entrada_id=2,
        condiciones=[],
        plazo_valor=30, plazo_unidad='DIAS_HABILES',
        efecto_codigo='CONFORMIDAD_PRESUNTA',
    )
    return entrada_15d, entrada_30d


def test_art131_con_aap_previa_usa_plazo_15_dias():
    """AAC con AAP previa favorable → entrada condicionada (15 días hábiles)."""
    from app.services.plazos import obtener_estado_plazo_tarea
    from datetime import date as d

    tarea = _mock_tarea(fecha_administrativa=d(2025, 5, 5))   # lunes

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
        r = obtener_estado_plazo_tarea(tarea, variables=variables)

    # 5 may + 15 hábiles = lun 26 may
    assert r.fecha_limite == d(2025, 5, 26)
    assert r.efecto == 'CONFORMIDAD_PRESUNTA'


def test_art131_sin_aap_previa_usa_plazo_30_dias():
    """AAC sin AAP previa → fallback (30 días hábiles)."""
    from app.services.plazos import obtener_estado_plazo_tarea
    from datetime import date as d

    tarea = _mock_tarea(fecha_administrativa=d(2025, 5, 5))

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
        r = obtener_estado_plazo_tarea(tarea, variables=variables)

    # 5 may + 30 hábiles = lun 16 jun
    assert r.fecha_limite == d(2025, 6, 16)
    assert r.estado == 'EN_PLAZO'
    assert r.dias_restantes == 20   # hábiles entre 20 may y 16 jun, ambos inclusive


def test_art131_seleccion_correcta_verificada_via_plazo_valor():
    """Confirma que la entrada correcta (15 vs 30) queda registrada en fecha_limite."""
    from app.services.plazos import obtener_estado_plazo_tarea
    from datetime import date as d

    tarea = _mock_tarea(fecha_administrativa=d(2025, 5, 1))   # jueves
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

        r_con = obtener_estado_plazo_tarea(tarea, variables=variables_con)
        r_sin = obtener_estado_plazo_tarea(tarea, variables=variables_sin)

    # 1 may (jue) + 15 hábiles = jue 22 may
    assert r_con.fecha_limite == d(2025, 5, 22)
    # 1 may (jue) + 30 hábiles = jue 12 jun
    assert r_sin.fecha_limite == d(2025, 6, 12)
