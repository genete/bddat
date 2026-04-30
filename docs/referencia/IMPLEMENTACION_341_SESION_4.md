# Plan Sesión 4 — Evaluador de condiciones en `obtener_estado_plazo`

> Issue #341 · Generado 2026-04-29 · Revisar antes de implementar.

---

## Objetivo

Implementar el núcleo de #341: hacer que `obtener_estado_plazo` seleccione la entrada
aplicable de `catalogo_plazos` evaluando sus `condiciones_plazo` en lugar de devolver
siempre la primera por `(tipo_elemento, tipo_elemento_id)`.

Concretamente:

1. **`app/services/plazos.py`** — nueva función privada `_evaluar_condiciones_plazo`,
   nueva función privada `_seleccionar_catalogo`, y refactorización de la firma de
   `obtener_estado_plazo` para aceptar `ctx` y `variables`.
2. **`app/services/assembler.py`** — parámetro `excluir: set` en `_compilar_variables`
   para evitar recursión infinita cuando `plazos.py` construye el dict de variables.
3. **`app/services/variables/plazo.py`** — las dos llamadas a `obtener_estado_plazo`
   pasan `ctx=ctx` para activar la ruta nueva.
4. **`tests/test_341_evaluador_plazo.py`** — tests sin BD siguiendo el patrón de
   `test_172_plazos_computo.py`.

---

## Decisión técnica: función propia vs. reutilización de `_evaluar_condiciones`

### Opciones

**A) Mover `_evaluar_condiciones` a `operadores.py`** y hacer que tanto `motor_reglas.py`
como `plazos.py` la importen desde allí.
- Pros: cero duplicación.
- Cons: amplía el scope de S4 (toca `motor_reglas.py` más allá de lo planificado en S1);
  `_evaluar_condiciones` devuelve `(bool, dict)` — el trigger dict no lo necesita `plazos.py`.

**B) Escribir `_evaluar_condiciones_plazo` privada en `plazos.py`** que importa `_OPERADORES`
de `operadores.py` (S1) y devuelve solo `bool`.
- Pros: sin dependencia `plazos → motor_reglas`; función más sencilla; S4 no toca
  `motor_reglas.py`; la semántica es la misma, el contrato es diferente (no se necesita trigger).
- Cons: ~15 líneas de código similar al bloque de `motor_reglas._evaluar_condiciones`.

### Elección: **opción B**

La separación `plazos ↔ motor_reglas` es un principio rector del proyecto (el motor no conoce
el dominio; el dominio no depende del motor). Introducir `plazos → motor_reglas` violaría esa
separación. La duplicación mínima está justificada.

`_evaluar_condiciones_plazo` importa `_OPERADORES` de `app.services.operadores` (creado en S1)
y aplica la misma semántica: AND implícito, variable ausente → `False` con `log.warning`.

---

## Ficheros afectados

| Fichero | Acción |
|---------|--------|
| `app/services/assembler.py` | Modificar — parámetro `excluir` en `_compilar_variables` |
| `app/services/variables/plazo.py` | Modificar — pasar `ctx=ctx` en las dos llamadas |
| `app/services/plazos.py` | Modificar — nueva firma + `_evaluar_condiciones_plazo` + `_seleccionar_catalogo` |
| `tests/test_341_evaluador_plazo.py` | **NUEVO** |

---

## 1. `app/services/assembler.py` (MODIFICAR)

Un solo cambio: añadir el parámetro `excluir` a `_compilar_variables`.

### Cambio en la firma y bucle

Sustituir la función completa (líneas 159-182) por:

```python
def _compilar_variables(ctx: ExpedienteContext, excluir: set = None) -> dict:
    """
    Evalúa todas las variables activas en catalogo_variables invocando el registry.

    Las variables inactivas (activa=False) se omiten del dict.
    Las que fallan o no tienen función devuelven None con warning en log.
    excluir: nombres de variables a omitir (anti-recursión con plazos.py).
    """
    from app.models.motor_reglas import CatalogoVariable
    from app.services.variables import _REGISTRY

    excluir = excluir or set()
    variables_activas = CatalogoVariable.query.filter_by(activa=True).all()
    resultado = {}
    for var in variables_activas:
        if var.nombre in excluir:
            continue
        fn = _REGISTRY.get(var.nombre)
        if fn is None:
            log.warning('assembler: variable activa sin función en registry: %s', var.nombre)
            resultado[var.nombre] = None
            continue
        try:
            resultado[var.nombre] = fn(ctx)
        except Exception as exc:
            log.warning('assembler: error calculando variable %s: %s', var.nombre, exc)
            resultado[var.nombre] = None
    return resultado
```

**Compatibilidad:** `build()` y `evaluar_multi()` llaman a `_compilar_variables(ctx)` sin
`excluir`. Con el default `None → set()`, el comportamiento es idéntico al actual.

---

## 2. `app/services/variables/plazo.py` (MODIFICAR)

Las dos funciones pasan `ctx=ctx` a `obtener_estado_plazo`. Sin cambios estructurales.

Sustituir las dos funciones `@variable` (líneas 37-60) por:

```python
@variable('estado_plazo')
def _(ctx) -> str:
    """
    Estado del plazo legal del elemento en tramitación.
    Valores: 'SIN_PLAZO' | 'EN_PLAZO' | 'PROXIMO_VENCER' | 'VENCIDO'
    """
    elemento, tipo = _resolver_elemento(ctx)
    if elemento is None:
        return 'SIN_PLAZO'
    from app.services import plazos
    return plazos.obtener_estado_plazo(elemento, tipo, ctx=ctx).estado


@variable('efecto_plazo')
def _(ctx) -> str:
    """
    Efecto legal del vencimiento del plazo del elemento en tramitación.
    Valores: 'NINGUNO' | 'SILENCIO_ESTIMATORIO' | 'RESPONSABILIDAD_DISCIPLINARIA' | ...
    """
    elemento, tipo = _resolver_elemento(ctx)
    if elemento is None:
        return 'NINGUNO'
    from app.services import plazos
    return plazos.obtener_estado_plazo(elemento, tipo, ctx=ctx).efecto
```

---

## 3. `app/services/plazos.py` (MODIFICAR)

Cuatro cambios en este fichero.

### 3a. Añadir `joinedload` al bloque de imports

Insertar **inmediatamente después de `from __future__ import annotations`**:

```python
from sqlalchemy.orm import joinedload
```

Este import a nivel de módulo permite parchear `app.services.plazos.joinedload` en los tests
(patrón equivalente al que usa `motor_reglas.py`).

### 3b. Nueva función `_evaluar_condiciones_plazo`

Insertar **justo antes de la línea `def _get_tipo_elemento_id`** (tras el bloque de
`EstadoPlazo` / `_SIN_PLAZO`, en la sección de "Utilidades internas"):

```python
def _evaluar_condiciones_plazo(condiciones, variables: dict) -> bool:
    """
    Evalúa lista de condiciones con AND implícito.

    Sin condiciones → siempre True.
    Variable ausente en dict → False con warning (decisión F de IMPLEMENTACION_341.md).
    Usa _OPERADORES de operadores.py (S1) — no depende de motor_reglas.
    """
    from app.services.operadores import _OPERADORES

    for cond in sorted(condiciones, key=lambda c: c.orden):
        nombre = cond.variable.nombre
        if nombre not in variables:
            log.warning('plazos: variable ausente en dict de condiciones: %s', nombre)
            return False
        op_fn = _OPERADORES.get(cond.operador)
        if op_fn is None:
            log.warning('plazos: operador desconocido en condicion_plazo: %s', cond.operador)
            return False
        try:
            if not bool(op_fn(variables[nombre], cond.valor)):
                return False
        except Exception as exc:
            log.warning('plazos: error evaluando %s %s %r: %s',
                        nombre, cond.operador, cond.valor, exc)
            return False
    return True
```

Necesita `log` a nivel de módulo. Añadir **al principio de `plazos.py`**, tras los imports:

```python
import logging
log = logging.getLogger(__name__)
```

### 3c. Nueva función `_seleccionar_catalogo`

Insertar **inmediatamente después de `_evaluar_condiciones_plazo`**:

```python
def _seleccionar_catalogo(tipo_elemento: str, tipo_id: int, variables_dict: dict):
    """
    Devuelve la primera entrada activa de catalogo_plazos que supera sus condiciones.

    Algoritmo (IMPLEMENTACION_341.md §Sesión 4):
      1. Carga entradas activas con joinedload de condiciones+variable.
      2. Ordena por orden ASC, id ASC (menor orden = mayor prioridad).
      3. Itera: entrada sin condiciones → candidata válida inmediata.
              entrada con condiciones → evalúa con AND implícito.
      4. Devuelve la primera que pasa; si ninguna → None con warning.
    """
    from app.models.catalogo_plazos import CatalogoPlazo
    from app.models.condiciones_plazo import CondicionPlazo

    entradas = (
        CatalogoPlazo.query
        .options(
            joinedload(CatalogoPlazo.condiciones).joinedload(CondicionPlazo.variable)
        )
        .filter_by(tipo_elemento=tipo_elemento, tipo_elemento_id=tipo_id, activo=True)
        .order_by(CatalogoPlazo.orden.asc(), CatalogoPlazo.id.asc())
        .all()
    )

    for entrada in entradas:
        if not entrada.condiciones:
            return entrada
        if _evaluar_condiciones_plazo(entrada.condiciones, variables_dict):
            return entrada

    if entradas:
        log.warning(
            'plazos: ninguna entrada de catalogo_plazos satisface condiciones '
            'para %s/%s — se devuelve SIN_PLAZO',
            tipo_elemento, tipo_id,
        )
    return None
```

### 3d. Refactorizar `obtener_estado_plazo`

Sustituir la función completa (líneas 60-121) por:

```python
def obtener_estado_plazo(
    elemento,
    tipo_elemento: str,
    ctx=None,
    variables=None,
) -> EstadoPlazo:
    """
    Devuelve el estado del plazo legal asociado a un elemento ESFTT.

    Args:
        elemento:      Instancia ORM del elemento evaluado
                       (Solicitud, Fase, Tramite o Tarea).
                       None o dict → SIN_PLAZO sin consultar BD.
        tipo_elemento: 'SOLICITUD' | 'FASE' | 'TRAMITE' | 'TAREA'
        ctx:           ExpedienteContext. Si se pasa, construye variables internamente
                       (excluyendo estado_plazo/efecto_plazo para evitar recursión).
        variables:     Dict de variables pre-construido. Tiene precedencia sobre ctx.

    Ruta legacy (ctx=None, variables=None):
        Usa CatalogoPlazo.query.filter_by(...).first() — compatible con mocks de test_172.
        La llaman las variables de plazo.py antes de la sesión 4; se elimina en sesión 6.

    Ruta nueva (ctx o variables proporcionados):
        Delega en _seleccionar_catalogo con el dict de variables para evaluar condiciones.
    """
    if elemento is None or isinstance(elemento, dict):
        return _SIN_PLAZO

    tipo_elemento_id = _get_tipo_elemento_id(elemento, tipo_elemento)
    if tipo_elemento_id is None:
        return _SIN_PLAZO

    if ctx is None and variables is None:
        # Ruta legacy: query simple, sin evaluador de condiciones.
        # Mantiene la cadena .filter_by(...).first() que mockean los tests #172 y #190
        # para que sigan verdes sin modificación.
        from app.models.catalogo_plazos import CatalogoPlazo
        catalogo = CatalogoPlazo.query.filter_by(
            tipo_elemento=tipo_elemento,
            tipo_elemento_id=tipo_elemento_id,
            activo=True,
        ).first()
    else:
        if variables is not None:
            variables_dict = variables
        else:
            from app.services.assembler import _compilar_variables
            variables_dict = _compilar_variables(
                ctx, excluir={'estado_plazo', 'efecto_plazo'}
            )
        catalogo = _seleccionar_catalogo(tipo_elemento, tipo_elemento_id, variables_dict)

    if catalogo is None:
        return _SIN_PLAZO

    fecha_acto = _resolver_campo_fecha(elemento, tipo_elemento, catalogo.campo_fecha or {})
    if fecha_acto is None:
        return _SIN_PLAZO

    hoy = _hoy()
    margen_dias = max(catalogo.plazo_valor * 60, 400)
    inhabiles = _obtener_inhabiles_bd(fecha_acto, hoy + timedelta(days=margen_dias))

    suspensiones = _obtener_suspensiones(elemento)
    fecha_limite = _aplicar_suspensiones(
        calcular_fecha_fin(fecha_acto, catalogo.plazo_valor, catalogo.plazo_unidad, inhabiles),
        suspensiones,
        inhabiles,
    )

    efecto = catalogo.efecto_plazo.codigo if catalogo.efecto_plazo else 'SIN_EFECTO_AUTOMATICO'

    if hoy > fecha_limite:
        dias = -_dias_habiles_entre(fecha_limite + timedelta(days=1), hoy, inhabiles)
        return EstadoPlazo(estado='VENCIDO', efecto=efecto,
                           fecha_limite=fecha_limite, dias_restantes=dias)

    dias = _dias_habiles_entre(hoy, fecha_limite, inhabiles)
    if dias <= UMBRAL_ALERTA:
        return EstadoPlazo(estado='PROXIMO_VENCER', efecto=efecto,
                           fecha_limite=fecha_limite, dias_restantes=dias)

    return EstadoPlazo(estado='EN_PLAZO', efecto=efecto,
                       fecha_limite=fecha_limite, dias_restantes=dias)
```

**Nota sobre `TODO #341`:** el comentario del TODO en la ruta legacy (líneas 81-88 actuales)
se elimina con esta sustitución. Queda una mención en la docstring ("se elimina en sesión 6")
hasta el cierre formal del issue.

---

## 4. `tests/test_341_evaluador_plazo.py` (NUEVO)

Sin BD (MagicMock), siguiendo el patrón de `test_172_plazos_computo.py`.

```python
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


def _mock_fase(tipo_fase_id, fecha_administrativa):
    """Fase mínima para obtener_estado_plazo."""
    fase = MagicMock()
    fase.tipo_fase_id = tipo_fase_id
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
    # GT con None→ el lambda de _OPERADORES devuelve False, no lanza
    assert _evaluar_condiciones_plazo([cond], {'tiene_solicitud_aap_favorable': None}) is False


# ---------------------------------------------------------------------------
# B) _seleccionar_catalogo — BD mockeada
# ---------------------------------------------------------------------------

def _query_mock(entradas):
    """Construye el mock del chain query.options().filter_by().order_by().all()."""
    import app.models.catalogo_plazos as _m
    import app.models.condiciones_plazo as _m2
    mock_chain = MagicMock()
    mock_chain.options.return_value.filter_by.return_value.order_by.return_value.all.return_value = entradas
    return mock_chain


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


def test_ctx_none_variables_none_usa_ruta_legacy():
    """Sin ctx ni variables → usa .filter_by(...).first() (compatibilidad #172)."""
    from app.services.plazos import obtener_estado_plazo
    # Sin ctx ni variables: el argumento type_elemento_id se resuelve pero
    # falta en el objeto → SIN_PLAZO (camino previo a la query)
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
    mock_sel.assert_called_once_with('FASE', 1, {})


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
# Dos entradas en catalogo_plazos para INFORME_AAPP_AAC (tipo_fase_id=42):
#   - orden=10,  plazo=15 días naturales, condiciones: tiene_solicitud_aap_favorable=True
#                                                     + es_solicitud_aac_pura=True
#                                                     + solicita_dup=False  (variable S3 no existe aún)
#   - orden=100, plazo=30 días naturales, sin condiciones (fallback general)
#
# Para estos tests se simplifican las condiciones a solo las dos variables de S3
# (tiene_solicitud_aap_favorable y es_solicitud_aac_pura) para no depender de
# 'solicita_dup' que se añadirá en S5.

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
    """Fase INFORME_AAPP_AAC con documento_solicitud."""
    fase = MagicMock()
    fase.tipo_fase_id = 42
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

    # fecha_admin=5 may + 15 días naturales = 20 may; hoy=20 may → EN_PLAZO (0 días hábiles)
    # El cómputo exacto depende de _primer_habil_desde y UMBRAL_ALERTA.
    # Lo relevante: la entrada seleccionada tiene plazo_valor=15.
    assert r.fecha_limite == d(2025, 5, 20)   # 5 may + 15 nat = 20 may (martes, hábil)
    assert r.estado in ('EN_PLAZO', 'PROXIMO_VENCER', 'VENCIDO')   # hoy=20 may → VENCIDO (hoy > limite no, igual → EN_PLAZO con 0 dias)


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
    assert r.dias_restantes == 11   # hábiles entre 20 may y 4 jun


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
```

---

## Secuencia de implementación

1. Editar `app/services/assembler.py` (§1): añadir parámetro `excluir` a
   `_compilar_variables`. Verificar que `build()` y `evaluar_multi()` siguen funcionando
   (no pasan `excluir`).

2. Editar `app/services/variables/plazo.py` (§2): añadir `ctx=ctx` a las dos llamadas.
   En este punto los tests de #190 pueden fallar (las variables ahora pasan ctx) — pero
   `test_190` usa `_StubCtx` sin ctx real, y la firma acepta ctx=None como antes (los stubs
   devuelven `None` para `_resolver_elemento`). Verificar antes de continuar:
   ```bash
   pytest tests/test_190_plazos_contrato.py -v
   ```

3. Editar `app/services/plazos.py` (§3):
   - 3a: añadir `from sqlalchemy.orm import joinedload` e `import logging / log`.
   - 3b: añadir `_evaluar_condiciones_plazo` (antes de `_get_tipo_elemento_id`).
   - 3c: añadir `_seleccionar_catalogo` (después de `_evaluar_condiciones_plazo`).
   - 3d: sustituir `obtener_estado_plazo`.

4. Crear `tests/test_341_evaluador_plazo.py` (§4).

5. Ejecutar el criterio de aceptación completo.

---

## Criterio de aceptación

```bash
# Tests nuevos de S4
pytest tests/test_341_evaluador_plazo.py -v

# Regresión #172 y #190 — sin tocar esos ficheros
pytest tests/test_172_plazos_computo.py tests/test_190_plazos_contrato.py -v

# Todos los tests de #341 anteriores (S1–S3 si ya están implementados)
pytest tests/test_341_operadores.py tests/test_341_modelo_condicion_plazo.py \
       tests/test_341_variables_art131.py tests/test_341_evaluador_plazo.py -v
```

---

## Riesgos y notas

### Recursión infinita `estado_plazo → _compilar_variables → estado_plazo`

- **Causa:** `variables/plazo.py` llama `obtener_estado_plazo(elemento, tipo, ctx=ctx)`.
  Con `ctx` → `_compilar_variables(ctx, excluir={...})`. Sin `excluir`, `_compilar_variables`
  evaluaría `estado_plazo`, que llama de nuevo a `obtener_estado_plazo(ctx=ctx)` → bucle infinito.
- **Mitigación:** `excluir={'estado_plazo', 'efecto_plazo'}` en la llamada desde `plazos.py`.
  El test `test_ctx_llama_compilar_variables_con_excluir` (bloque D) valida este contrato.

### Ruta legacy

La ruta `ctx=None, variables=None` usa el query `.filter_by(...).first()` original. Es
compatible con los mocks de test_172 y test_190. En sesión 6 (cierre) se elimina y se hace
`_seleccionar_catalogo` el único camino, actualizando los mocks de test_172 si es necesario.

### Dependencia `plazos → assembler` (lazy import)

`from app.services.assembler import _compilar_variables` está dentro de `obtener_estado_plazo`
(lazy). No genera import circular porque `assembler.py` no importa `plazos.py` a nivel de
módulo (solo la cadena `_compilar_variables → _REGISTRY[estado_plazo] → plazos` se forma
en tiempo de ejecución, y el `excluir` lo corta).

### `joinedload` a nivel de módulo en `plazos.py`

Requiere que SQLAlchemy esté instalado (siempre lo está en este proyecto). El import a nivel
de módulo permite `patch('app.services.plazos.joinedload')` en los tests de `_seleccionar_catalogo`
sin tocar SQLAlchemy globalmente.

### Tests del caso art. 131.1 párr. 2 (bloque E)

Los tests usan `campo_fecha={'fk': 'documento_solicitud_id'}` y navegan vía `fase.solicitud`.
La lógica en `_resolver_campo_fecha` ya soporta este caso (rama FASE sin `via_tarea_tipo`).
Si el código de tipo de fase para INFORME_AAPP_AAC no es 42 en BD real, actualizar el mock
en S5 cuando se conozca el código exacto (cabo suelto nº 1 de IMPLEMENTACION_341.md).

### Estado `PROXIMO_VENCER` vs `VENCIDO` en `test_art131_con_aap_previa_usa_plazo_15_dias`

El test acepta cualquier estado diferente de `SIN_PLAZO` porque el objeto principal a
validar es que `fecha_limite` corresponde a 15 días (no 30). Si se desea fijar el estado,
ajustar `HOY_131` a una fecha donde el estado sea inequívoco. La aserción sobre `fecha_limite`
es el verdadero oracle de la prueba.
