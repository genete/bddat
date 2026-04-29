# Implementación #341 — Condiciones de aplicabilidad en `catalogo_plazos`

> Documento estratégico. Generado 2026-04-29. Actualizar al cerrar cada sesión.

---

## Contexto

La selección de la entrada aplicable en `catalogo_plazos` por `(tipo_elemento, tipo_elemento_id)` es insuficiente para plazos que dependen del contexto ESFTT completo.

**Caso canónico — art. 131.2 RD 1955/2000:** el informe de AAPP en AAC dura 30 días naturales, pero se reduce a 15 si concurren `tiene_aap_previa AND sin_modificacion_aap AND NOT solicita_dup`.

**Bloqueante para:** #328 (seed real del catálogo), #173 (suspensión de plazos).

---

## Decisiones técnicas aprobadas

| # | Decisión | Elección |
|---|----------|----------|
| A | Paso de contexto al evaluador | `variables: dict` pre-construido. Firma: `obtener_estado_plazo(elemento, tipo, ctx=None, variables=None)`. Si `ctx` → construye dict internamente. Si nada → dict vacío (entradas condicionadas se saltan, preserva tests #172). |
| B | Ubicación del modelo `CondicionPlazo` | Nuevo fichero `app/models/condiciones_plazo.py` |
| C | Reutilización de `_OPERADORES` | Extraer a `app/services/operadores.py`. `motor_reglas.py` y `plazos.py` importan de ahí. |
| D | "Plazo eliminado" Decreto 9/2011 | Fuera de #341. Es flujo (regla `motor_reglas` que prohíbe crear la fase). Issue separado. |
| E | Constraint de unicidad en `orden` | NO unique. Índice no único `idx_catalogo_plazos_tipo_orden`. Fallback por menor `id`. |
| F | Variable ausente/None | Condición falla silenciosamente con `log.warning` (igual que `_evaluar_condiciones` del motor). |
| G | Variables art. 131.2 | Implementar `tiene_aap_previa`, `solicita_dup`, `sin_modificacion_aap` en esta misma issue. Sin ellas el motor no tiene caso de uso verificable. |

**Anti-recursión:** `_compilar_variables(ctx)` necesita parámetro `excluir: set[str]` para omitir `estado_plazo`/`efecto_plazo` cuando se construye el dict de condiciones de plazo.

---

## División en sesiones

### Sesión 1 — Refactor `OPERADORES` a módulo común
**Ficheros:** `app/services/operadores.py` (NUEVO), `app/services/motor_reglas.py` (importa)
**Tests:** `tests/test_341_operadores.py` (NUEVO) — 12 tests, uno por operador
**Criterio:** `pytest tests/test_341_operadores.py tests/test_190_plazos_contrato.py` verde
**Tiempo:** ~1.5 h | **Dep.:** ninguna

### Sesión 2 — Modelo `CondicionPlazo` y migración
**Ficheros:**
- `app/models/condiciones_plazo.py` (NUEVO)
- `app/models/catalogo_plazos.py` (añadir `orden`, relationship `condiciones`)
- `app/models/__init__.py` (registrar import)
- `migrations/versions/XXX_341_condiciones_plazo.py` (NUEVO)

**Migración:**
1. `op.add_column('catalogo_plazos', Column('orden', Integer, server_default='100', ...))`
2. `op.create_index('idx_catalogo_plazos_tipo_orden', ...)`
3. `op.create_table('condiciones_plazo', ...)` con FK CASCADE a `catalogo_plazos`, FK a `catalogo_variables`, CheckConstraint operadores (mismo que `condiciones_regla`)

**Tests:** `tests/test_341_modelo_condicion_plazo.py` (NUEVO)
**Criterio:** `flask db upgrade/downgrade` limpio; tests #172 sin tocar siguen verdes
**Tiempo:** ~2 h | **Dep.:** ninguna (puede solaparse con S1)

### Sesión 3 — Variables derivadas para art. 131.2
**Ficheros:**
- `app/services/variables/calculado.py` (añadir 3 `@variable`)
- `migrations/versions/YYY_341_variables_aap_dup_mod.py` (NUEVO)
- `docs/referencia/DISEÑO_CONTEXT_ASSEMBLER.md` (actualizar estado variables)

**Variables a implementar** (art. 131.1 párrafo 2 RD 1955/2000):
- `tiene_solicitud_aap_favorable(ctx) -> bool` — existe en el expediente una Solicitud con tipo AAP (distinta de la actual) cuya fase finalizadora tiene `resultado_fase.codigo in RESULTADO_FASE_FAVORABLE_CODIGOS`. Constante definida en `invariantes_esftt.py`.
- `es_solicitud_aac_pura(ctx) -> bool` — la solicitud en curso contiene AAC y no contiene AAP ni DUP: `ctx.solicitud.contiene_tipo('AAC') and not contiene_tipo('AAP') and not contiene_tipo('DUP')`.

**⚠️ Pendiente de confirmar:** código exacto de `tipo_fase` para INFORME_AAPP en AAC (no aparece en seed de #172).

**Tests:** `tests/test_341_variables_aap_dup_mod.py` (NUEVO) — 3-4 tests por variable
**Criterio:** variables visibles en `_REGISTRY`; `catalogo_variables` con `activa=TRUE`
**Tiempo:** ~2 h | **Dep.:** ninguna (puede solaparse con S1-S2)

### Sesión 4 — Evaluador en `obtener_estado_plazo`
**Ficheros:**
- `app/services/plazos.py` (refactorizar `obtener_estado_plazo` + nueva `_seleccionar_catalogo`)
- `app/services/assembler.py` (añadir `excluir: set[str]` a `_compilar_variables`)
- `app/services/variables/plazo.py` (pasar `ctx=ctx` en las dos llamadas)

**Lógica del nuevo `_seleccionar_catalogo(tipo_elemento, tipo_id, variables_dict)`:**
1. Carga entradas activas con `joinedload(condiciones, variable)`, filtra por vigencia
2. Ordena por `orden ASC, id ASC`
3. Para cada entrada: si sin condiciones → candidata válida. Si con condiciones → llama `evaluar_condiciones(entrada.condiciones, variables_dict)`
4. Devuelve la primera que pasa; si ninguna → None

**Tests:** `tests/test_341_evaluador_plazo.py` (NUEVO)
- Sin condiciones (fallback)
- Condición dispara → gana entrada condicionada
- Condición no dispara → gana fallback
- Dos condicionadas: primera falla, segunda pasa
- Variable ausente → no dispara
- `ctx=None, variables=None` → solo fallback (compatibilidad #172)
- **Caso real art. 131.2:** ambos escenarios (con y sin AAP previa)

**Criterio:** tests #172 originales sin tocar siguen verdes; nuevos tests verdes
**Tiempo:** ~4 h | **Dep.:** sesiones 1, 2, 3

### Sesión 5 — Seed art. 131.2 y tests E2E con BD real
**Ficheros:**
- `migrations/versions/ZZZ_341_seed_art131_2.py` (NUEVO)

**Seed:** dos entradas para `INFORME_AAPP_AAC`:
- `orden=10, plazo_valor=15, DIAS_NATURALES, norma="Art. 131.2 RD 1955/2000"` + 3 condiciones
- `orden=100, plazo_valor=30, DIAS_NATURALES, norma="Art. 131.2 RD 1955/2000 — caso general"`, sin condiciones

**Tests E2E** (`tests/test_341_e2e_art131_2.py`):
- AAC con AAP previa favorable → plazo 15 días
- AAC sin AAP previa → plazo 30 días
- AAC con DUP → plazo 30 días (condición `solicita_dup=False` no se cumple)

**Criterio:** los 3 tests E2E verdes con BD real (fixture `app_ctx`)
**Tiempo:** ~3 h | **Dep.:** sesiones 1-4

### Sesión 6 — Documentación y cierre
**Ficheros:**
- `docs/referencia/DISEÑO_FECHAS_PLAZOS.md` (quitar nota DEUDA #341, añadir §3.2.1)
- `docs/CONTEXTO_ACTUAL.md` (marcar #341 cerrado)
- `app/services/plazos.py` (quitar `# TODO #341`)
- `docs/referencia/DISEÑO_CONTEXT_ASSEMBLER.md` (estados variables "implementada")
- Este fichero `IMPLEMENTACION_341.md` (marcar sesiones completadas)

**Tiempo:** ~1 h | **Dep.:** sesiones 1-5

---

## Resumen de tiempos

| Sesión | Tema | Horas |
|--------|------|-------|
| 1 | Refactor operadores | 1.5 |
| 2 | Modelo + migración | 2.0 |
| 3 | Variables derivadas | 2.0 |
| 4 | Evaluador (núcleo) | 4.0 |
| 5 | Seed + E2E | 3.0 |
| 6 | Documentación | 1.0 |
| | **Total** | **13.5 h** |

Margen real estimado: 16-18 h.

---

## Cabos sueltos → issues potenciales

1. **Código `tipo_fase` para INFORME_AAPP en AAC** — no existe en el seed de #172. Hay que crearlo en el catálogo de tipos de fase antes de la sesión 5.
2. **Semántica exacta de `es_solicitud_aac_pura`** — resuelto: `solicitud.contiene_tipo('AAC') and not contiene_tipo('AAP') and not contiene_tipo('DUP')`. Sin ambigüedad.
3. **UI Supervisor para `condiciones_plazo`** — no existe formulario. Por ahora solo vía migración/shell. Issue futuro.
4. **Caso "plazo eliminado" Decreto 9/2011 DA 1ª** — requiere regla en `motor_reglas` + variables `clasificacion_suelo`, `discurre_subterranea`. Issue separado.
5. **Cache del dict de variables** — si una request llama `evaluar_multi` y luego `obtener_estado_plazo`, `_compilar_variables` se ejecuta dos veces. Issue de optimización.
6. **`CondicionPlazo.valor` JSON vs JSONB** — `condiciones_regla` usa JSON. Armonizar a JSONB en ambas tablas: issue futuro.
7. **Caso EIA Ley 21/2013** — modelable con #341 cuando `longitud_km` esté implementada. Issue posterior.
8. **Ordenación AAP+AAC combinadas** — si una solicitud combinada pudiera tener plazos distintos por sigla, habría que iterar como hace `evaluar_multi`. Issue a abrir si emerge el caso.
9. **Refactor `tipos_resultados_fases` → enum en código** — la tabla no es configurable por el Supervisor y nunca debería serlo (rompería el motor). Patrón ya existente en el proyecto: `tipo_elemento` como String sin FK. Refactor: cambiar `Fase.resultado_fase_id` FK por `Fase.resultado_fase_codigo String(30)` + CHECK constraint + mover los valores a constante en `invariantes_esftt.py`. Issue separado, no bloquea #341. Mientras tanto, definir `RESULTADO_FASE_FAVORABLE_CODIGOS = frozenset({'FAVORABLE', 'FAVORABLE_CONDICIONADO'})` en `invariantes_esftt.py` usando la tabla existente.

---

## Riesgos

- **Recursión infinita** `estado_plazo → _compilar_variables → estado_plazo`: mitigado con `excluir` en `_compilar_variables`. Test específico obligatorio.
- **Rotura de tests #172**: mitigado con kwargs opcionales (`ctx=None, variables=None`).
- **Variable con `sin_modificacion_aap` mal interpretada**: mitigado documentando el supuesto + comentario en PR para validación.
- **Entrada sin fallback**: si todas las entradas condicionadas fallan y no hay fallback → `SIN_PLAZO` silencioso. Loggear `warning` en ese caso.

---

## Verificación end-to-end del caso canónico

```
Expediente E:
  Solicitud S1 (AAP) — resuelta favorablemente:
    fase finalizadora con resultado_fase.codigo == 'FAVORABLE'
  Solicitud S2 (AAC pura — sin AAP ni DUP):
    Fase INFORME_AAPP_AAC, doc_solicitud.fecha_administrativa = hoy-5
```

```python
ctx = ExpedienteContext(expediente=E, objeto=fase_aac)
estado = obtener_estado_plazo(fase_aac, 'FASE', ctx=ctx)
# → fecha_limite = fecha_admin + 15 días naturales (con prórroga art. 30.5)
# → estado.dias_restantes ≈ 10

# Mismo expediente sin la fase RESOLUCION_AAP:
# → fecha_limite = fecha_admin + 30 días naturales
# → estado.dias_restantes ≈ 25
```
