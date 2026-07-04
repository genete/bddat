# Contexto actual — BDDAT

> Actualizar al cerrar cada issue. Los issues cerrados están en `git log` — no se duplican aquí.
> Detalle y porqué de cada decisión: `docs/diseño/DECISIONES_UI.md` y los ADRs.

---

**Último cerrado:** #583 — CRUD admin de `requisitos_documentales` (listado + inspector, editor de condiciones anidado, permisos ADR-013, baja lógica). PR #584.

**Último hito:** PR #580 (parte de #579) — panel de estadísticas del supervisor: servicio `estadisticas_supervisor` sobre el núcleo `estado_dominio`, isla React + Recharts tematizada.

**#579 sigue abierto:** bloque GESTIÓN aparcado (2026-07-02) para priorizar M3. Piezas en issues propios: config motor #170/#171/#479, plazos legales, operaciones masivas #295.

**Próximos:** foco en M3 — análisis documental/requerimientos (ver hoja de ruta abajo). Spin-offs vivos de #558/#559 pendientes: #566/#567 (árbol), #568 (`NOTIFICACION_INFRUCTUOSA`), #570/#571 (filtros y tokens del seguimiento). Tras M3: bloque escritos/motor adaptativo (M4).

## Hoja de ruta — Implementación

### Bloque UI — revamping

Diseño cerrado (7 ADRs + `DECISIONES_UI.md`). Implementados y cerrados: #497 (ADR-013 permisos), #498 (ADR-014 layout `base_app`), #499 (ADR-015 scaffolding React), #503 (ADR-019 smoke tests), #500 (ADR-016 árbol), #506 (ADR-020 dock global), #531/#532 (ADR-018 command palette + búsqueda unificada), #533 (ADR-022 sistema visual), #534 (ADR-023 list-detail/inspector), #558 (núcleo `estado_dominio`), #501 (ADR-017 Mi trabajo), #559 (inspector de seguimiento). Detalle de cada uno en git log / PRs asociados.

Activo:

- **#579 — Mi trabajo del supervisor (ADR-028).** Bloque CONTROL hecho (PR #580). Bloque GESTIÓN aparcado. Permanece abierto como paraguas.

**Total estimado bloque UI: ~10-13 semanas** (1 dev + IA, ratio observado).

### Bloque análisis documental / requerimientos (M3) — foco actual

Orden (sesión 2026-07-03, detalle en `docs/referencia/DISEÑO_ANALISIS_SOLICITUD.md` §4/§7):
#441/#408/#581 (diseño) en paralelo → #495 → UI #581 → #440 → #442 (cierre) → #582.

- **#408** — Poblar catálogo de requisitos documentales (siembra mínima; modelo ya construido en #192).
- ~~**#583**~~ ✅ CRUD admin del catálogo. PR #584.
- **#441** — Seed `catalogo_requerimientos`.
- **#440** — Selector de requerimientos en tarea ANALIZAR.
- **#495** — Check documental completo + auto-generación de defectos.
- **#442** — Formulario diagnóstico en ANALIZAR (cierre del hilo).
- **#581** — Checklist de contenido técnico del proyecto (RD 223/2008, RD 337/2014).
- **#582** — Regla de motor: tasa impagada bloquea toda fase posterior.

### Bloque escritos / motor adaptativo (M4)

Se aborda tras consolidar M3.

- **#555** — Clasificación ESFT de plantillas.
- **#556** — Variables del motor en plantillas (documento adaptativo). Depende de la cobertura de catálogo (M3).
- **#561** — Drop `catalogo_variables.activa` + red de tests (ADR-026).

**ADR-021** (operaciones externas BandeJA/Notifica-PNT): diseño acordado, issue pendiente de crear.

## Decisiones pendientes a tomar en construcción

- Sub-stack React por isla (state management, data fetching, librerías concretas).
- Contenido fino del inspector/dock/viewbar por nivel del árbol — se refina durante implementación.

## Documentos vivos del revamping

- `docs/diseño/DECISIONES_UI.md` — punto de entrada al estado del revamping.
- `docs/guias/NOMENCLATURA_LAYOUT.md` — referencia de las 7 áreas del layout.
- `docs/decisiones/ADR-013` a `ADR-021`.

## Backlog M3/M4/M5 no afectado por el revamping

Sigue en GitHub con sus milestones. Ejemplos: #170, #171, #322, #408, #409, #432, #495, etc.
