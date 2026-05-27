# Plan Sesión 1 — Refactor `_OPERADORES` a módulo común

> Issue #341 · Generado 2026-04-29 · Revisar antes de implementar.

---

## Objetivo

Extraer el dict `_OPERADORES` de `app/services/motor_reglas.py` a un módulo reutilizable
`app/services/operadores.py`, de modo que la sesión 4 pueda importarlo desde `plazos.py`
sin duplicar lógica ni crear dependencias circulares.

---

## Contexto

En `motor_reglas.py` (líneas 96-109) existe un dict de 12 lambdas que implementan los
operadores de comparación (`EQ`, `NEQ`, `IN`, `NOT_IN`, `IS_NULL`, `NOT_NULL`, `GT`,
`GTE`, `LT`, `LTE`, `BETWEEN`, `NOT_BETWEEN`). En la sesión 4, `plazos.py` necesitará
evaluar las `condiciones_plazo` con esos mismos operadores. Si no se extrae ahora, habrá
que duplicarlos o crear una dependencia `plazos → motor_reglas` que rompe la separación
de responsabilidades.

**Impacto:** ningún cambio de comportamiento. Refactor puro. Todos los tests existentes
deben seguir verdes sin modificación.

---

## Ficheros afectados

| Fichero | Acción |
|---------|--------|
| `app/services/operadores.py` | **NUEVO** |
| `app/services/motor_reglas.py` | Modificar — importar de `operadores.py`, eliminar definición local |
| `tests/test_341_operadores.py` | **NUEVO** — 12 tests unitarios puros |

---

## 1. `app/services/operadores.py` (NUEVO)

Fichero mínimo. Sin imports externos. Sin dependencias de Flask, SQLAlchemy ni modelos.

```python
"""
Operadores de comparación reutilizables para evaluadores de condiciones.

Usados por motor_reglas._evaluar_condiciones y (sesión 4) por plazos._seleccionar_catalogo.
"""

_OPERADORES = {
    'EQ':          lambda v, ref: v == ref,
    'NEQ':         lambda v, ref: v != ref,
    'IN':          lambda v, ref: v in (ref if isinstance(ref, list) else [ref]),
    'NOT_IN':      lambda v, ref: v not in (ref if isinstance(ref, list) else [ref]),
    'IS_NULL':     lambda v, _: v is None,
    'NOT_NULL':    lambda v, _: v is not None,
    'GT':          lambda v, ref: v is not None and v > ref,
    'GTE':         lambda v, ref: v is not None and v >= ref,
    'LT':          lambda v, ref: v is not None and v < ref,
    'LTE':         lambda v, ref: v is not None and v <= ref,
    'BETWEEN':     lambda v, ref: v is not None and ref[0] <= v <= ref[1],
    'NOT_BETWEEN': lambda v, ref: v is not None and not (ref[0] <= v <= ref[1]),
}
```

**No exportar nada más.** `_evaluar_condiciones` permanece en `motor_reglas.py`
hasta la sesión 4, cuando se decidirá si moverla o duplicarla para condiciones de plazo.

---

## 2. `app/services/motor_reglas.py` (MODIFICAR)

Dos cambios quirúrgicos, sin tocar nada más:

### 2a. Añadir import al bloque de imports existente

Insertar **inmediatamente antes** de la línea `log = logging.getLogger(__name__)`:

```python
from app.services.operadores import _OPERADORES
```

### 2b. Eliminar la definición local de `_OPERADORES`

Borrar las líneas 96-109 (bloque completo):

```python
_OPERADORES = {
    'EQ':          lambda v, ref: v == ref,
    ...
    'NOT_BETWEEN': lambda v, ref: v is not None and not (ref[0] <= v <= ref[1]),
}
```

**El resto del fichero no se toca.** `_evaluar_condiciones` permanece igual en
`motor_reglas.py`.

### Verificación visual tras el cambio

`motor_reglas.py` debe quedar sin ninguna definición de `_OPERADORES`; solo el import.
Grep de comprobación:

```
grep -n "_OPERADORES" app/services/motor_reglas.py
# Debe aparecer solo en la línea del import, no en ninguna asignación.
```

---

## 3. `tests/test_341_operadores.py` (NUEVO)

12 funciones de test, una por operador. Sin BD, sin app context, sin mocking.
Importa `_OPERADORES` directamente de `app.services.operadores`.

Estructura del fichero:

```python
"""Tests unitarios de _OPERADORES — issue #341 sesión 1."""
import pytest
from app.services.operadores import _OPERADORES


# EQ
def test_eq_igual():
    assert _OPERADORES['EQ']('VENCIDO', 'VENCIDO') is True

def test_eq_distinto():
    assert _OPERADORES['EQ']('EN_PLAZO', 'VENCIDO') is False


# NEQ
def test_neq_distinto():
    assert _OPERADORES['NEQ']('EN_PLAZO', 'VENCIDO') is True

def test_neq_igual():
    assert _OPERADORES['NEQ']('VENCIDO', 'VENCIDO') is False


# IN
def test_in_en_lista():
    assert _OPERADORES['IN']('VENCIDO', ['PROXIMO_VENCER', 'VENCIDO']) is True

def test_in_fuera_de_lista():
    assert _OPERADORES['IN']('EN_PLAZO', ['PROXIMO_VENCER', 'VENCIDO']) is False

def test_in_valor_unico_como_ref():
    """ref es string, no lista — debe funcionar igual que ref=['VENCIDO']."""
    assert _OPERADORES['IN']('VENCIDO', 'VENCIDO') is True


# NOT_IN
def test_not_in_fuera():
    assert _OPERADORES['NOT_IN']('EN_PLAZO', ['PROXIMO_VENCER', 'VENCIDO']) is True

def test_not_in_dentro():
    assert _OPERADORES['NOT_IN']('VENCIDO', ['PROXIMO_VENCER', 'VENCIDO']) is False


# IS_NULL
def test_is_null_con_none():
    assert _OPERADORES['IS_NULL'](None, None) is True

def test_is_null_con_valor():
    assert _OPERADORES['IS_NULL']('algo', None) is False


# NOT_NULL
def test_not_null_con_valor():
    assert _OPERADORES['NOT_NULL']('algo', None) is True

def test_not_null_con_none():
    assert _OPERADORES['NOT_NULL'](None, None) is False


# GT
def test_gt_mayor():
    assert _OPERADORES['GT'](10, 5) is True

def test_gt_igual():
    assert _OPERADORES['GT'](5, 5) is False

def test_gt_none_falla_silenciosamente():
    assert _OPERADORES['GT'](None, 5) is False


# GTE
def test_gte_mayor():
    assert _OPERADORES['GTE'](10, 5) is True

def test_gte_igual():
    assert _OPERADORES['GTE'](5, 5) is True

def test_gte_menor():
    assert _OPERADORES['GTE'](3, 5) is False


# LT
def test_lt_menor():
    assert _OPERADORES['LT'](3, 5) is True

def test_lt_igual():
    assert _OPERADORES['LT'](5, 5) is False

def test_lt_none_falla_silenciosamente():
    assert _OPERADORES['LT'](None, 5) is False


# LTE
def test_lte_menor():
    assert _OPERADORES['LTE'](3, 5) is True

def test_lte_igual():
    assert _OPERADORES['LTE'](5, 5) is True

def test_lte_mayor():
    assert _OPERADORES['LTE'](7, 5) is False


# BETWEEN
def test_between_dentro():
    assert _OPERADORES['BETWEEN'](5, [1, 10]) is True

def test_between_en_extremo():
    assert _OPERADORES['BETWEEN'](1, [1, 10]) is True
    assert _OPERADORES['BETWEEN'](10, [1, 10]) is True

def test_between_fuera():
    assert _OPERADORES['BETWEEN'](0, [1, 10]) is False

def test_between_none_falla_silenciosamente():
    assert _OPERADORES['BETWEEN'](None, [1, 10]) is False


# NOT_BETWEEN
def test_not_between_fuera():
    assert _OPERADORES['NOT_BETWEEN'](0, [1, 10]) is True

def test_not_between_dentro():
    assert _OPERADORES['NOT_BETWEEN'](5, [1, 10]) is False

def test_not_between_none_falla_silenciosamente():
    assert _OPERADORES['NOT_BETWEEN'](None, [1, 10]) is False
```

**Nota:** el conteo supera 12 funciones porque algunos operadores tienen más de un caso
relevante (EQ positivo + EQ negativo, etc.). El plan original "12 tests, uno por operador"
era orientativo. Añadir casos adicionales no viola el criterio; solo enriquece la cobertura.
Si se prefiere exactamente 12, colapsar EQ+NEQ en parametrize, pero la legibilidad es peor.

---

## Secuencia de implementación

1. Crear `app/services/operadores.py` con el contenido exacto de la sección §1.
2. Editar `app/services/motor_reglas.py`:
   - Añadir el import (§2a).
   - Eliminar el bloque `_OPERADORES` local (§2b).
3. Verificar visualmente que `motor_reglas.py` no contiene la definición local.
4. Crear `tests/test_341_operadores.py` con los tests de la sección §3.
5. Ejecutar el criterio de aceptación.

---

## Criterio de aceptación

```bash
pytest tests/test_341_operadores.py tests/test_190_plazos_contrato.py -v
```

- Todos los tests de `test_341_operadores.py` verdes.
- Todos los tests de `test_190_plazos_contrato.py` verdes sin modificar ese fichero.
- En particular, `test_motor_no_dispara_sin_plazo_contra_vencido` y
  `test_motor_dispara_vencido_cuando_vencido` deben seguir pasando (validan que
  `_evaluar_condiciones` en `motor_reglas.py` sigue usando `_OPERADORES` correctamente
  tras el import).

---

## Riesgos y notas

- **Import circular:** `operadores.py` no importa nada del proyecto → riesgo nulo.
- **Nombre privado `_OPERADORES`:** se mantiene el guión bajo. No es parte de la API
  pública del módulo, solo se comparte entre servicios internos.
- **`motor_reglas.py` no cambia de comportamiento:** `_evaluar_condiciones` usa
  `_OPERADORES` exactamente igual; solo el origen del objeto cambia.
- **Sesión 4:** al implementar `_seleccionar_catalogo` en `plazos.py`, bastará con
  `from app.services.operadores import _OPERADORES` y llamar las lambdas directamente,
  o mover/duplicar `_evaluar_condiciones` a `operadores.py`. Esa decisión se documenta
  en el plan de sesión 4.
