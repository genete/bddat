# Contexto actual — BDDAT

> Actualizar al cerrar cada issue. La sección de estado lleva una entrada por línea.
> El detalle y el porqué de cada decisión está en `docs/historial/REVISION_VALIDEZ_ISSUES_MAYO_2026.md`.
> Los issues cerrados están en `git log` — no se duplican aquí.

---

**Último cerrado:** #174 (PR #493) — permisos centralizados (`PERMISOS` dict), permiso blando en expedientes con traza en bitácora, indicador de asignación en header, `require_permiso` decorator, ADR-012.

**Actuales:** —

**Próximos:** **#410** y **#192** — últimos requisitos estructurales antes del revamping de UI.


## Hoja de ruta — orden propuesto para próximas sesiones

> Una sesión limpia por ítem. Las dependencias se indican con «(tras #X)».

### Pre-frontend — Requisitos estructurales

Estos issues deben cerrarse antes de arrancar la UI porque condicionan
el diseño del frontend o tienen código activo con huecos conocidos.

1. ~~**#488**~~ — ✓ cerrado (PR #490)
2. ~~**#470**~~ — ✓ cerrado (PR #491)
3. ~~**#466**~~ — ✓ cerrado (PR #492)
4. ~~**#174**~~ — ✓ cerrado (PR #493)
5. **#410** — compatibilidad de tipos de solicitud como reglas del motor
6. **#192** — requisitos documentales por procedimiento (rediseñar: anclar a CREAR fase siguiente, sin tabla `procedimientos`)

### Bloque UI — Revamping de interfaz de usuario

Una vez cerrados #410 y #192, arrancar con un **estudio a fondo de la UI** antes
de añadir pantallas nuevas: auditar lo existente, decidir qué se poda, qué se
refactoriza y qué se construye desde cero. El resultado es un plan de UI como
etapa propia, no un apéndice incremental.

### Bloque 5 — Análisis heurístico de PDF

7. **#304** — script de detección del tipo de solicitud
8. **#305** — script de detección del tipo de expediente
9. **#306** — helper de cálculo de tasa y extracción de presupuesto (tras #304)

### Backlog M3 sin posición en la ruta

Troceo de #248 fuera del recorrido priorizado: **#407** (campo `siglas_escritos`),
**#408** (checklist documental — posible post-producción), **#409** (regla de tasas;
tras #408).

Correcciones de tests preexistentes: **#487** (app context en `TestSerializarOrgExp` + URL de stub en e2e art. 131),
**#489** (texto de `norma_origen` en seed de `catalogo_plazos`: RD 88/2026).

### Backlog M4 — Pre-producción

- **#464** — ampliar `seed_demo` con registros reales en `organismos_expediente` (tras #247).
