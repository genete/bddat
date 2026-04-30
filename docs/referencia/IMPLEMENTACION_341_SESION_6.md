# Plan Sesión 6 — Documentación y cierre de #341

> Issue #341 · Generado 2026-04-30 · Ejecutar con S1–S5 completadas.

---

## Objetivo

Sesión de cierre: sin código nuevo. Las tareas son:

1. Eliminar la ruta legacy de `obtener_estado_plazo` (quedaba de puente desde S4).
2. Actualizar los mocks de `test_172` que dependían de esa ruta.
3. Quitar la nota DEUDA #341 de `DISEÑO_FECHAS_PLAZOS.md` y añadir §3.2.1.
4. Marcar variables implementadas en `DISEÑO_CONTEXT_ASSEMBLER.md`.
5. Cerrar el issue en `CONTEXTO_ACTUAL.md`.
6. Marcar sesiones como completadas en `IMPLEMENTACION_341.md`.

---

## Ficheros afectados

| Fichero | Acción |
|---------|--------|
| `app/services/plazos.py` | Modificar — eliminar ruta legacy y `# TODO #341` |
| `tests/test_172_plazos_computo.py` | Modificar — actualizar mocks a nueva cadena de query |
| `tests/test_341_evaluador_plazo.py` | Modificar — renombrar test de ruta legacy (nombre, no comportamiento) |
| `docs/referencia/DISEÑO_FECHAS_PLAZOS.md` | Modificar — quitar nota DEUDA #341, añadir §3.2.1 |
| `docs/referencia/DISEÑO_CONTEXT_ASSEMBLER.md` | Modificar — marcar variables de S3 como `implementada` |
| `docs/CONTEXTO_ACTUAL.md` | Modificar — marcar #341 cerrado (proponer Próximo al usuario) |
| `docs/referencia/IMPLEMENTACION_341.md` | Modificar — marcar sesiones S1–S6 completadas |

---

## 1. `app/services/plazos.py` (MODIFICAR)

### Contexto de partida (tras S4)

S4 dejó en `obtener_estado_plazo` dos ramas:

```python
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
```

### Cambio en S6

Sustituir ese bloque `if/else` por una versión unificada. La firma no cambia.

**Código resultante de la función completa:**

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
        elemento:      Instancia ORM del elemento evaluado.
                       None o dict → SIN_PLAZO sin consultar BD.
        tipo_elemento: 'SOLICITUD' | 'FASE' | 'TRAMITE' | 'TAREA'
        ctx:           ExpedienteContext. Construye variables internamente
                       (excluyendo estado_plazo/efecto_plazo para evitar recursión).
        variables:     Dict de variables pre-construido. Tiene precedencia sobre ctx.
                       Sin ctx ni variables → dict vacío (solo entradas sin condiciones).
    """
    if elemento is None or isinstance(elemento, dict):
        return _SIN_PLAZO

    tipo_elemento_id = _get_tipo_elemento_id(elemento, tipo_elemento)
    if tipo_elemento_id is None:
        return _SIN_PLAZO

    if variables is not None:
        variables_dict = variables
    elif ctx is not None:
        from app.services.assembler import _compilar_variables
        variables_dict = _compilar_variables(
            ctx, excluir={'estado_plazo', 'efecto_plazo'}
        )
    else:
        variables_dict = {}

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

**Efecto del cambio:** `obtener_estado_plazo(fase, 'FASE')` (sin ctx ni variables) usa
`variables_dict={}` → `_seleccionar_catalogo` devuelve solo entradas sin condiciones
(fallback general). Reproduce el comportamiento pre-#341 para código que no pasa contexto.

---

## 2. `tests/test_172_plazos_computo.py` (MODIFICAR)

Los tests del bloque B (`TestObtenerEstadoPlazo*`) mockeaban la cadena `.filter_by(...).first()`
de la ruta legacy. Con su eliminación, la query pasa por `_seleccionar_catalogo`:

```python
CatalogoPlazo.query
    .options(joinedload(CatalogoPlazo.condiciones).joinedload(CondicionPlazo.variable))
    .filter_by(tipo_elemento=..., tipo_elemento_id=..., activo=True)
    .order_by(CatalogoPlazo.orden.asc(), CatalogoPlazo.id.asc())
    .all()
```

Los tests del bloque A (`TestCalcularFechaFin*`) no necesitan cambios (función pura).

### 2a. Actualizar `_mock_catalogo`

Añadir `m.condiciones = []` para que `_seleccionar_catalogo` lo trate como entrada sin
condiciones (candidata válida inmediata):

```python
def _mock_catalogo(plazo_valor, plazo_unidad, campo_fecha, efecto_codigo):
    m = MagicMock()
    m.plazo_valor = plazo_valor
    m.plazo_unidad = plazo_unidad
    m.campo_fecha = campo_fecha
    m.efecto_plazo.codigo = efecto_codigo
    m.condiciones = []
    return m
```

### 2b. Actualizar `test_sin_entrada_catalogo`

```python
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
```

### 2c. Actualizar `test_sin_fecha_acto`

```python
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
```

### 2d. Actualizar `test_en_plazo`

```python
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
```

### 2e. Actualizar `test_proximo_vencer`

```python
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
```

### 2f. Actualizar `test_vencido`

```python
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
    assert r.dias_restantes == -1
```

---

## 3. `tests/test_341_evaluador_plazo.py` (MODIFICAR — menor)

El test `test_ctx_none_variables_none_usa_ruta_legacy` (bloque C) ya pasa sin cambios
funcionales (el objeto sin `tipo_fase_id` sigue devolviendo `SIN_PLAZO`). Solo se actualiza
el nombre del test y su docstring para reflejar que ya no hay ruta legacy:

```python
def test_ctx_none_variables_none_usa_variables_dict_vacio():
    """Sin ctx ni variables → variables_dict={} → solo entradas sin condiciones aplican."""
    from app.services.plazos import obtener_estado_plazo
    r = obtener_estado_plazo(object(), 'FASE')
    assert r.estado == 'SIN_PLAZO'
```

---

## 4. `docs/referencia/DISEÑO_FECHAS_PLAZOS.md` (MODIFICAR)

### 4a. Actualizar encabezado de §3.2

Cambiar:
```
### 3.2 Catálogo de plazos — CERRADO (campo_fecha rediseñado 2026-04-19) — DEUDA #341
```

Por:
```
### 3.2 Catálogo de plazos — CERRADO (campo_fecha 2026-04-19, condiciones_plazo #341 2026-04-30)
```

### 4b. Eliminar nota DEUDA #341

Eliminar el bloque que empieza en `> **Deuda de diseño (#341,` y termina en `> Ver #341.`
(incluidos los saltos de línea circundantes). Queda intacta la línea:
```
> **Decisión:** Tabla separada `catalogo_plazos`, administrable por el Supervisor.
```

### 4c. Añadir §3.2.1 al final de la sección §3.2

Insertar inmediatamente antes del separador `---` que da paso a `### 3.3 Suspensiones`:

```markdown
#### §3.2.1 Condiciones de aplicabilidad — `_seleccionar_catalogo` (#341)

Cuando `obtener_estado_plazo` recibe `ctx` o `variables`, delega la selección de
la entrada aplicable en `_seleccionar_catalogo(tipo_elemento, tipo_id, variables_dict)`.

**Algoritmo:**

1. **Carga** todas las entradas activas de `catalogo_plazos` para
   `(tipo_elemento, tipo_elemento_id)` con `joinedload` de `condiciones` y la
   `variable` de cada condición (una sola query).
2. **Ordena** por `orden ASC, id ASC` (menor `orden` = mayor prioridad;
   `id` como desempate estable ante empate de `orden`).
3. **Itera** en orden:
   - Entrada **sin condiciones** → candidata válida; se devuelve inmediatamente.
   - Entrada **con condiciones** → evalúa AND implícito:
     si todas las condiciones se cumplen → se devuelve;
     si alguna falla → se salta, se evalúa la siguiente.
4. Si ninguna entrada supera la evaluación → `None` + `log.warning`.
   El llamante devuelve `SIN_PLAZO` sin lanzar excepción.

**Semántica AND implícito:**

- Cada condición evalúa `variables_dict[nombre] OPERADOR valor`.
- Variable ausente en el dict → condición falla silenciosamente con `log.warning`
  (decisión F de IMPLEMENTACION_341.md: el catálogo nunca lanza excepción por
  variable no calculada).
- Operadores: los de `app/services/operadores.py`
  (`EQ`, `NEQ`, `GT`, `GTE`, `LT`, `LTE`, `IN`, `NOT_IN`).

**Compatibilidad hacia atrás:**

Sin `ctx` ni `variables`, `variables_dict = {}`. Solo las entradas sin condiciones
son candidatas válidas — reproduce el comportamiento pre-#341 para cualquier
llamada que no pase contexto.

**Caso de uso canónico — art. 131.2 RD 1955/2000:**

```
catalogo_plazos para INFORME_AAPP_AAC:
  orden=10,  plazo=15 días naturales,
             condiciones: tiene_solicitud_aap_favorable=True
                        + es_solicitud_aac_pura=True
                        + requiere_dup=False
  orden=100, plazo=30 días naturales, sin condiciones (fallback)
```

Si las tres condiciones se cumplen → 15 días; en caso contrario → 30 días.
```

---

## 5. `docs/referencia/DISEÑO_CONTEXT_ASSEMBLER.md` (MODIFICAR)

Tras S3, las variables `tiene_solicitud_aap_favorable` y `es_solicitud_aac_pura` están
implementadas en `app/services/variables/calculado.py` y registradas en `catalogo_variables`
con `activa=TRUE`.

Localizar sus filas en el diccionario de variables y actualizar la columna **Estado**:

| Variable | Cambio |
|---|---|
| `tiene_solicitud_aap_favorable` (ex `tiene_aap_previa`) | `definida` → `implementada` |
| `es_solicitud_aac_pura` | `pendiente de implementar` → `implementada` |

Si S3 renombró la fila `tiene_aap_previa` a `tiene_solicitud_aap_favorable`, actualizar
también la columna **Variable**. Si S3 añadió `es_solicitud_aac_pura` como fila nueva,
localizar por nombre y cambiar solo el estado.

---

## 6. `docs/CONTEXTO_ACTUAL.md` (MODIFICAR)

⚠️ **Regla del proyecto:** proponer al usuario qué pasa a "Próximo" y esperar confirmación
antes de escribir esa línea.

Candidatos (los dos desbloqueados por #341):
- **#328** — seed real de `catalogo_plazos`
- **#173** — suspensión de plazos

Plantilla a completar una vez confirmado el "Próximo":

```markdown
**Último cerrado:** #341 — Condiciones de aplicabilidad en `catalogo_plazos`:
módulo `operadores.py`, tabla `condiciones_plazo`, campo `orden`,
variables `tiene_solicitud_aap_favorable`/`es_solicitud_aac_pura`,
evaluador `_seleccionar_catalogo` en `obtener_estado_plazo`,
seed art. 131.2 RD 1955/2000 (15 días con AAP previa / 30 sin ella).
Desbloquea #328 y #173.

**Próximo:** [CONFIRMAR CON USUARIO: #328 o #173]

**En espera:** #173 — Suspensión de plazos (ya desbloqueado por #341).
```

---

## 7. `docs/referencia/IMPLEMENTACION_341.md` (MODIFICAR)

Añadir marca de completado en cada encabezado de sesión. Ejemplo:

```
### Sesión 1 ✓ — Refactor `OPERADORES` a módulo común
```

Repetir para Sesiones 2, 3, 4, 5 y 6. Añadir al final del documento (antes de la sección
`## Riesgos`):

```markdown
---

## Estado final

**Cerrado 2026-04-30.** Todas las sesiones completadas. Issue #341 resuelto.
Desbloqueados: #328 (seed catálogo real), #173 (suspensiones de plazos).
```

---

## Secuencia de implementación

1. **Actualizar `tests/test_172_plazos_computo.py`** (§2):
   - `_mock_catalogo`: añadir `m.condiciones = []`
   - Cinco tests: `test_sin_entrada_catalogo`, `test_sin_fecha_acto`,
     `test_en_plazo`, `test_proximo_vencer`, `test_vencido`

2. **Actualizar `app/services/plazos.py`** (§1): sustituir la función completa.

3. **Verificar regresión** (#172 y #190):
   ```bash
   pytest tests/test_172_plazos_computo.py tests/test_190_plazos_contrato.py -v
   ```
   Deben ser verdes. Si fallan, depurar antes de continuar.

4. **Renombrar test en `test_341_evaluador_plazo.py`** (§3): solo nombre y docstring.

5. **Ejecutar suite completa de #341**:
   ```bash
   pytest tests/test_341_operadores.py \
          tests/test_341_modelo_condicion_plazo.py \
          tests/test_341_variables_art131.py \
          tests/test_341_evaluador_plazo.py \
          tests/test_341_e2e_art131_2.py -v
   ```

6. **Editar `DISEÑO_FECHAS_PLAZOS.md`** (§4): encabezado + eliminar DEUDA + añadir §3.2.1.

7. **Editar `DISEÑO_CONTEXT_ASSEMBLER.md`** (§5): actualizar estado de variables.

8. **Proponer "Próximo"** al usuario y esperar confirmación.

9. **Editar `CONTEXTO_ACTUAL.md`** (§6) con el "Próximo" confirmado.

10. **Editar `IMPLEMENTACION_341.md`** (§7): marcar sesiones completadas.

---

## Criterio de aceptación final del issue #341

```bash
pytest tests/test_341_operadores.py \
       tests/test_341_modelo_condicion_plazo.py \
       tests/test_341_variables_art131.py \
       tests/test_341_evaluador_plazo.py \
       tests/test_341_e2e_art131_2.py \
       tests/test_172_plazos_computo.py \
       tests/test_190_plazos_contrato.py -v
```

Todos los tests deben ser verdes sin `-k` ni `--ignore`.
