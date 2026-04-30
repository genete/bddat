# Plan Sesión 3 — Variables derivadas para art. 131.1 párr. 2 RD 1955/2000

> Issue #341 · Generado 2026-04-29 · Revisado tras feedback.

---

## Objetivo

Implementar las dos variables del Variable Registry que permiten evaluar si concurren
las condiciones del art. 131.1 párr. 2 RD 1955/2000 (plazo 15 días en lugar de 30):

| Variable | Condición que representa |
|----------|--------------------------|
| `tiene_solicitud_aap_favorable` | Existe en el expediente una solicitud AAP distinta de la actual, resuelta favorablemente |
| `es_solicitud_aac_pura` | La solicitud en curso contiene AAC y no contiene ni AAP ni DUP |

`es_solicitud_aac_pura` ya excluye implícitamente que se solicite DUP o que sea una
solicitud combinada AAP+AAC, por lo que no es necesaria una tercera variable.

Sin estas dos variables el evaluador de condiciones de la sesión 4 no tiene casos de uso
verificables. La sesión 5 (seed art. 131.1 párr. 2) depende de que ambas estén activas
en `catalogo_variables`.

> **Nombre `tiene_solicitud_aap_favorable`:** el DISEÑO_CONTEXT_ASSEMBLER.md documenta
> esta variable con el nombre provisional `tiene_aap_previa`, que es ambiguo (no expresa
> que la resolución sea favorable). En esta sesión se implementa con el nombre definitivo
> `tiene_solicitud_aap_favorable` y se actualiza el DISEÑO doc para reflejarlo.

---

## Ficheros afectados

| Fichero | Acción |
|---------|--------|
| `app/services/invariantes_esftt.py` | Modificar — añadir constante `RESULTADO_FASE_FAVORABLE_CODIGOS` |
| `app/services/variables/calculado.py` | Modificar — añadir 2 `@variable` |
| `migrations/versions/<rev>_341_variables_art131.py` | **NUEVO** |
| `tests/test_341_variables_art131.py` | **NUEVO** |
| `docs/referencia/DISEÑO_CONTEXT_ASSEMBLER.md` | Modificar — renombrar variable + añadir nueva |

---

## 1. `app/services/invariantes_esftt.py` (MODIFICAR)

Añadir la constante **al inicio del módulo**, justo después de las importaciones,
antes de la primera función:

```python
# Códigos de resultado de fase finalizadora que se consideran resolución favorable.
# Usado por tiene_solicitud_aap_favorable (art. 131.1 párr. 2 RD 1955/2000).
RESULTADO_FASE_FAVORABLE_CODIGOS = frozenset({'FAVORABLE', 'FAVORABLE_CONDICIONADO'})
```

No se cambia ninguna función existente.

---

## 2. `app/services/variables/calculado.py` (MODIFICAR)

### 2a. Import de la constante

Añadir al bloque de imports del fichero:

```python
from app.services.invariantes_esftt import RESULTADO_FASE_FAVORABLE_CODIGOS
```

### 2b. Las dos nuevas funciones

Añadir al final del fichero, después de `existe_fase_finalizadora_cerrada`:

```python
@variable('tiene_solicitud_aap_favorable')
def _(ctx) -> bool:
    """
    True si existe en el expediente una solicitud con tipo AAP (distinta de la actual)
    cuya fase finalizadora está finalizada con resultado FAVORABLE o FAVORABLE_CONDICIONADO.

    Condición del art. 131.1 párr. 2 RD 1955/2000: reduce el plazo de consultas
    en AAC de 30 a 15 días naturales cuando concurre junto con es_solicitud_aac_pura.
    """
    solicitud_actual = ctx.solicitud
    if solicitud_actual is None:
        return False
    for sol in ctx.expediente.solicitudes:
        if sol is solicitud_actual:
            continue
        if not sol.contiene_tipo('AAP'):
            continue
        for fase in sol.fases:
            if (fase.tipo_fase
                    and fase.tipo_fase.es_finalizadora
                    and fase.finalizada
                    and fase.resultado_fase
                    and fase.resultado_fase.codigo in RESULTADO_FASE_FAVORABLE_CODIGOS):
                return True
    return False


@variable('es_solicitud_aac_pura')
def _(ctx) -> bool:
    """
    True si la solicitud en contexto contiene el tipo AAC y NO contiene AAP ni DUP.

    'Pura' significa que el promotor solicita solo la AAC, sin combinarla con AAP
    (ya obtenida en solicitud previa) ni con DUP. Condición del art. 131.1 párr. 2
    RD 1955/2000. Excluye implícitamente la solicitud de DUP y las combinadas AAP+AAC.
    """
    solicitud = ctx.solicitud
    if solicitud is None:
        return False
    return (
        solicitud.contiene_tipo('AAC')
        and not solicitud.contiene_tipo('AAP')
        and not solicitud.contiene_tipo('DUP')
    )
```

### 2c. `variables/__init__.py`

`calculado.py` ya está importado ahí. **No tocar `__init__.py`**; las funciones se
registran automáticamente al ejecutarse el decorador `@variable`.

---

## 3. Migración (NUEVO)

### 3a. Verificar cabeza antes de crear

```bash
flask db heads
```

- Única cabeza es la de sesión 2: `down_revision` apunta a ella.
- Cabeza es `c9379e09ae01` (sesión 2 aún no creada): `down_revision = 'c9379e09ae01'`.
- Dos cabezas: resolver con `flask db merge heads` antes de continuar.

### 3b. Generar el esqueleto

```bash
flask db revision -m "341_variables_art131"
```

### 3c. Contenido del fichero de migración

```python
"""341_variables_art131

Revision ID: <rev>
Revises: <rev_anterior>
Create Date: <fecha>

Issue #341 sesión 3 — Registra las dos variables para art. 131.1 párr. 2 RD 1955/2000
en catalogo_variables con activa=TRUE:
  - tiene_solicitud_aap_favorable
  - es_solicitud_aac_pura
"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_variables
            (nombre, etiqueta, tipo_dato, norma_id, activa)
        VALUES
        (
            'tiene_solicitud_aap_favorable',
            'El expediente tiene resolución AAP favorable previa a la AAC en curso',
            'boolean',
            NULL,
            TRUE
        ),
        (
            'es_solicitud_aac_pura',
            'La solicitud en curso es AAC pura (sin DUP ni AAP combinada)',
            'boolean',
            NULL,
            TRUE
        )
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        DELETE FROM public.catalogo_variables
        WHERE nombre IN (
            'tiene_solicitud_aap_favorable',
            'es_solicitud_aac_pura'
        )
    """))
```

> **`norma_id = NULL`:** se deja nulo para evitar asumir el código exacto de la norma
> en BD. Si se quiere enlazar a `RD1955_2000`, sustituir `NULL` por
> `(SELECT id FROM public.normas WHERE codigo = 'RD1955_2000')` solo si se puede
> garantizar que esa fila existe (verificar con `SELECT` antes de aplicar).

### 3d. Verificar

```bash
flask db upgrade
flask db downgrade
flask db upgrade
```

---

## 4. `tests/test_341_variables_art131.py` (NUEVO)

Sin BD, sin app context. Duck-typing puro (MagicMock + stubs mínimos).
Patrón idéntico al Bloque B de `test_190_plazos_contrato.py`.

```python
"""Tests issue #341 sesión 3 — variables derivadas art. 131.1 párr. 2 RD 1955/2000."""
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Stubs mínimos de duck-typing
# ---------------------------------------------------------------------------

class _StubSolicitud:
    """Simula Solicitud con contiene_tipo() y fases controlables."""
    def __init__(self, siglas: str, fases=None):
        self._siglas = siglas
        self.fases = fases or []

    def contiene_tipo(self, siglas: str) -> bool:
        return siglas in self._siglas.split('+')


class _StubTipoFase:
    def __init__(self, es_finalizadora=False):
        self.es_finalizadora = es_finalizadora


class _StubResultadoFase:
    def __init__(self, codigo: str):
        self.codigo = codigo


class _StubFase:
    def __init__(self, es_finalizadora=False, finalizada=False, resultado_codigo=None):
        self.tipo_fase = _StubTipoFase(es_finalizadora=es_finalizadora)
        self._finalizada = finalizada
        self.resultado_fase = _StubResultadoFase(resultado_codigo) if resultado_codigo else None

    @property
    def finalizada(self):
        return self._finalizada


class _StubCtx:
    def __init__(self, solicitud_actual=None, solicitudes=None):
        self._solicitud_actual = solicitud_actual
        exp = MagicMock()
        exp.solicitudes = solicitudes or []
        self.expediente = exp

    @property
    def solicitud(self):
        return self._solicitud_actual


# ---------------------------------------------------------------------------
# Registro de variables (importar módulo activa los @variable)
# ---------------------------------------------------------------------------

def _get_variable(nombre: str):
    import app.services.variables.calculado  # noqa: F401
    from app.services.variables import _REGISTRY
    fn = _REGISTRY.get(nombre)
    assert fn is not None, f'Variable {nombre!r} no encontrada en _REGISTRY'
    return fn


# ---------------------------------------------------------------------------
# A) tiene_solicitud_aap_favorable
# ---------------------------------------------------------------------------

def test_tiene_solicitud_aap_favorable_registrada():
    _get_variable('tiene_solicitud_aap_favorable')


def test_tiene_solicitud_aap_favorable_verdadero():
    """Expediente con AAP previa favorable → True."""
    fase_aap = _StubFase(es_finalizadora=True, finalizada=True, resultado_codigo='FAVORABLE')
    sol_aap = _StubSolicitud('AAP', fases=[fase_aap])
    sol_aac = _StubSolicitud('AAC')
    ctx = _StubCtx(solicitud_actual=sol_aac, solicitudes=[sol_aac, sol_aap])
    assert _get_variable('tiene_solicitud_aap_favorable')(ctx) is True


def test_tiene_solicitud_aap_favorable_condicionado():
    """FAVORABLE_CONDICIONADO también cuenta como favorable."""
    fase_aap = _StubFase(es_finalizadora=True, finalizada=True,
                         resultado_codigo='FAVORABLE_CONDICIONADO')
    sol_aap = _StubSolicitud('AAP', fases=[fase_aap])
    sol_aac = _StubSolicitud('AAC')
    ctx = _StubCtx(solicitud_actual=sol_aac, solicitudes=[sol_aac, sol_aap])
    assert _get_variable('tiene_solicitud_aap_favorable')(ctx) is True


def test_tiene_solicitud_aap_favorable_falso_sin_aap():
    """Expediente sin solicitud AAP → False."""
    sol_aac = _StubSolicitud('AAC')
    ctx = _StubCtx(solicitud_actual=sol_aac, solicitudes=[sol_aac])
    assert _get_variable('tiene_solicitud_aap_favorable')(ctx) is False


def test_tiene_solicitud_aap_favorable_falso_no_finalizada():
    """AAP presente pero fase finalizadora no cerrada → False."""
    fase_aap = _StubFase(es_finalizadora=True, finalizada=False)
    sol_aap = _StubSolicitud('AAP', fases=[fase_aap])
    sol_aac = _StubSolicitud('AAC')
    ctx = _StubCtx(solicitud_actual=sol_aac, solicitudes=[sol_aac, sol_aap])
    assert _get_variable('tiene_solicitud_aap_favorable')(ctx) is False


def test_tiene_solicitud_aap_favorable_falso_desfavorable():
    """AAP finalizada con resultado DESFAVORABLE → False."""
    fase_aap = _StubFase(es_finalizadora=True, finalizada=True, resultado_codigo='DESFAVORABLE')
    sol_aap = _StubSolicitud('AAP', fases=[fase_aap])
    sol_aac = _StubSolicitud('AAC')
    ctx = _StubCtx(solicitud_actual=sol_aac, solicitudes=[sol_aac, sol_aap])
    assert _get_variable('tiene_solicitud_aap_favorable')(ctx) is False


def test_tiene_solicitud_aap_favorable_excluye_solicitud_actual():
    """La propia solicitud AAP+AAC no se cuenta como 'AAP previa'."""
    sol_combinada = _StubSolicitud('AAP+AAC')
    ctx = _StubCtx(solicitud_actual=sol_combinada, solicitudes=[sol_combinada])
    assert _get_variable('tiene_solicitud_aap_favorable')(ctx) is False


def test_tiene_solicitud_aap_favorable_sin_solicitud_en_ctx():
    """Sin solicitud en contexto → False."""
    ctx = _StubCtx(solicitud_actual=None, solicitudes=[])
    assert _get_variable('tiene_solicitud_aap_favorable')(ctx) is False


# ---------------------------------------------------------------------------
# B) es_solicitud_aac_pura
# ---------------------------------------------------------------------------

def test_es_solicitud_aac_pura_registrada():
    _get_variable('es_solicitud_aac_pura')


def test_es_solicitud_aac_pura_verdadero():
    """Solicitud solo AAC → True."""
    sol = _StubSolicitud('AAC')
    ctx = _StubCtx(solicitud_actual=sol)
    assert _get_variable('es_solicitud_aac_pura')(ctx) is True


def test_es_solicitud_aac_pura_con_dup():
    """AAC+DUP → False."""
    sol = _StubSolicitud('AAC+DUP')
    ctx = _StubCtx(solicitud_actual=sol)
    assert _get_variable('es_solicitud_aac_pura')(ctx) is False


def test_es_solicitud_aac_pura_combinada_aap_aac():
    """AAP+AAC combinada → False (contiene AAP)."""
    sol = _StubSolicitud('AAP+AAC')
    ctx = _StubCtx(solicitud_actual=sol)
    assert _get_variable('es_solicitud_aac_pura')(ctx) is False


def test_es_solicitud_aac_pura_solo_aap():
    """Solo AAP (sin AAC) → False."""
    sol = _StubSolicitud('AAP')
    ctx = _StubCtx(solicitud_actual=sol)
    assert _get_variable('es_solicitud_aac_pura')(ctx) is False


def test_es_solicitud_aac_pura_sin_solicitud_en_ctx():
    """Sin solicitud en contexto → False."""
    ctx = _StubCtx(solicitud_actual=None)
    assert _get_variable('es_solicitud_aac_pura')(ctx) is False
```

---

## 5. `docs/referencia/DISEÑO_CONTEXT_ASSEMBLER.md` (MODIFICAR)

### 5a. Renombrar `tiene_aap_previa` → `tiene_solicitud_aap_favorable`

Localizar la fila (línea ~134 del doc):

```
| `tiene_aap_previa` | boolean | `derivado_fase` · Expediente | RD 1955/2000 art. 131 — ... | definida |
```

Sustituirla por:

```markdown
| `tiene_solicitud_aap_favorable` | boolean | `calculado` · Expediente | RD 1955/2000 art. 131.1 párr. 2 — existe solicitud AAP en el expediente (distinta de la actual) cuya fase finalizadora está cerrada con resultado FAVORABLE o FAVORABLE_CONDICIONADO; reduce el plazo de consultas AAC de 30 a 15 días naturales | implementada en `calculado.py` (#341-S3) |
```

Cambios respecto a la fila original:
- Nombre: `tiene_aap_previa` → `tiene_solicitud_aap_favorable`
- Naturaleza: `derivado_fase` → `calculado` (vive en `calculado.py`, no en un hipotético `derivado_fase.py`)
- Artículo: `art. 131` → `art. 131.1 párr. 2`
- Estado: `definida` → `implementada en calculado.py (#341-S3)`

### 5b. Añadir `es_solicitud_aac_pura`

Insertar **inmediatamente después** de la fila anterior:

```markdown
| `es_solicitud_aac_pura` | boolean | `calculado` · Solicitud | RD 1955/2000 art. 131.1 párr. 2 — la solicitud en curso contiene AAC y no contiene AAP ni DUP; condición de reducción del plazo de consultas a 15 días naturales; excluye implícitamente las solicitudes combinadas y las que incluyen DUP | implementada en `calculado.py` (#341-S3) |
```

---

## Secuencia de implementación

1. Añadir `RESULTADO_FASE_FAVORABLE_CODIGOS` a `invariantes_esftt.py` (§1).
2. Editar `calculado.py`: añadir import (§2a) + dos funciones al final (§2b).
3. Crear `tests/test_341_variables_art131.py` (§4) y ejecutar:
   ```bash
   pytest tests/test_341_variables_art131.py -v
   ```
4. Generar y rellenar la migración (§3b–§3c).
5. Verificar migración (§3d).
6. Actualizar `DISEÑO_CONTEXT_ASSEMBLER.md` (§5).

---

## Criterio de aceptación

```bash
# Tests nuevas variables (sin BD)
pytest tests/test_341_variables_art131.py -v

# Regresión (sin BD)
pytest tests/test_172_plazos_computo.py tests/test_190_plazos_contrato.py -v

# Migración (con BD)
flask db upgrade && flask db downgrade && flask db upgrade
```

---

## Riesgos y notas

- **Import de `RESULTADO_FASE_FAVORABLE_CODIGOS` en `calculado.py`:** cuando `calculado.py`
  se carga, arrastra los imports de `invariantes_esftt.py` (que importa modelos ORM a nivel
  de módulo). En Flask esto es seguro. Si algún test importa `calculado` en un entorno sin
  app context y falla por ese motivo, la alternativa es definir la constante directamente en
  `calculado.py` como `_CODIGOS_FAVORABLE = frozenset({'FAVORABLE', 'FAVORABLE_CONDICIONADO'})`.

- **`fase.tipo_fase.es_finalizadora`:** campo existente en `TipoFase`, ya usado en
  `existe_fase_finalizadora_cerrada` (línea 53 de `calculado.py`). No requiere cambios en
  el modelo.

- **Seed sesión 5:** las condiciones del plazo de 15 días usarán los nombres
  `tiene_solicitud_aap_favorable` y `es_solicitud_aac_pura` para referenciar las filas de
  `catalogo_variables`. Verificar que esos nombres coinciden exactamente con el INSERT de
  la migración de esta sesión.
