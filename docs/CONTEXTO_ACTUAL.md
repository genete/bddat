# Contexto actual — BDDAT

> Actualizar al cerrar cada issue. Los issues cerrados están en `git log` — no se duplican aquí.
> Detalle y porqué de cada decisión: `docs/diseño/DECISIONES_UI.md` y los ADRs.

---

**Último cerrado:** trabajo en paralelo con tres worktrees (sesión 2026-07-06) — #593 CRUD de `catalogo_requerimientos` (PR #597), #591 corte mínimo `activo_red`/`envolvente`/tabla puente (PR #598), #582 regla de motor tasa impagada (PR #596). Migraciones de #591/#582 coordinadas manualmente (misma cabeza `b88f9bb4755b`, rebasada para cadena lineal en vez de heads divergentes). Además, cerrada del todo la deuda de tests preexistente que las tres sesiones venían reverificando sin corregir: #487 (app_context en `test_247`, esquema de URL en `test_341`), #578 (test de `toggle_estado` obsoleto) y #227 (ya resuelto sin querer por #544) — PR #599. Suite completa: 0 fallos (antes 8).

**Último hito:** PR #580 (parte de #579) — panel de estadísticas del supervisor: servicio `estadisticas_supervisor` sobre el núcleo `estado_dominio`, isla React + Recharts tematizada.

**#579 sigue abierto:** bloque GESTIÓN aparcado (2026-07-02) para priorizar M3. Piezas en issues propios: config motor #170/#171/#479, plazos legales, operaciones masivas #295 — **antes de construir cualquiera de estas, resolver #588/#589/#590 (ADR-029, navegación administrativa)**, que fijan dónde encajan (hub universal "Control y Gestión"); construirlas antes repetiría el problema que #583 destapó.

**Próximos:** foco en M3 — análisis documental/requerimientos (ver hoja de ruta abajo). Spin-offs vivos de #558/#559 pendientes: #566/#567 (árbol), #568 (`NOTIFICACION_INFRUCTUOSA`), #570/#571 (filtros y tokens del seguimiento). Tras M3: bloque escritos/motor adaptativo (M4).

## Hoja de ruta — Implementación

### Bloque UI — revamping

Diseño cerrado (7 ADRs + `DECISIONES_UI.md`). Implementados y cerrados: #497 (ADR-013 permisos), #498 (ADR-014 layout `base_app`), #499 (ADR-015 scaffolding React), #503 (ADR-019 smoke tests), #500 (ADR-016 árbol), #506 (ADR-020 dock global), #531/#532 (ADR-018 command palette + búsqueda unificada), #533 (ADR-022 sistema visual), #534 (ADR-023 list-detail/inspector), #558 (núcleo `estado_dominio`), #501 (ADR-017 Mi trabajo), #559 (inspector de seguimiento). Detalle de cada uno en git log / PRs asociados.

Activo:

- **#579 — Mi trabajo del supervisor (ADR-028).** Bloque CONTROL hecho (PR #580). Bloque GESTIÓN aparcado. Permanece abierto como paraguas.
- **#588/#589/#590 — Navegación administrativa (ADR-029).** Van **antes** que cualquier issue que pueble el bloque GESTIÓN de #579 (#170/#171/#479/plazos/#295): fijan la estructura (hub universal "Control y Gestión", dashboard 1:1 con el sidebar, retirada del prefijo `/admin`) donde esas piezas tienen que encajar.

**Total estimado bloque UI: ~10-13 semanas** (1 dev + IA, ratio observado).

### Bloque análisis documental / requerimientos (M3) — foco actual

Orden (sesión 2026-07-03, re-troceado en sesión 2026-07-05 — detalle en
`docs/referencia/DISEÑO_ANALISIS_SOLICITUD.md` §4/§7): tres ramas de diseño/poblado en
paralelo, cada una CRUD→poblado antes que su UI, convergen en #495 → UI #581 → #440 →
#442 (cierre) → #582.

**Rama documental (sin cambios):**
- ~~**#583**~~ ✅ CRUD admin de `requisitos_documentales`. PR #584.
- **#408** — Poblar catálogo de requisitos documentales (modelo ya construido en #192).

**Rama requerimientos (#441 re-troceado 2026-07-05):**
- ~~**#593**~~ ✅ [ADMIN] CRUD de `catalogo_requerimientos` (gemelo simplificado de #583,
  sin condiciones anidadas). PR #597.
- **#441** — poblado puro de `catalogo_requerimientos`, ya no bloqueado (CRUD de #593
  existe). Antes pedía script+migración; descartado, mismo criterio que #408.

**Rama ítems técnicos (#581 re-troceado 2026-07-05):**
- ~~**#591**~~ ✅ Corte mínimo de integración con
  [bddat-instalaciones](https://github.com/genete/bddat-instalaciones)
  (`activo_red`/`envolvente`/tabla puente) — deriva el RD aplicable sin campo proxy. PR #598.
- **#594** — [MODELO][ADMIN] `items_tecnicos` + `condiciones_item_tecnico` + CRUD
  Supervisor. Ya no bloqueado (#591 resuelto).
- **#595** — poblado normativo de `items_tecnicos` (RD 223/2008, RD 337/2014). Depende
  de #594.
- **#581** — redefinido a solo la UI de verificación del tramitador en tarea ANALIZAR
  (antes bundlaba diseño+poblado+UI). Depende de #594/#595.

**Convergencia:**
- **#495** — Check documental completo + auto-generación de defectos.
- **#440** — Selector de requerimientos en tarea ANALIZAR.
- **#442** — Formulario diagnóstico en ANALIZAR (cierre del hilo).
- ~~**#582**~~ ✅ Regla de motor: tasa impagada bloquea toda fase posterior. PR #596.

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
- `docs/decisiones/` — ADR-013 en adelante (revamping); `DECISIONES_UI.md` mantiene el listado curado y actualizado, no un rango fijo aquí.

## Backlog M3/M4/M5 no afectado por el revamping

Sigue en GitHub con sus milestones. Ejemplos: #170, #171, #322, #408, #409, #432, #495, etc.

**#592** (M5) — Integración completa del modelo de activos técnicos de
[bddat-instalaciones](https://github.com/genete/bddat-instalaciones) (líneas, aparamenta,
geometría/PostGIS, generación). Corte mínimo ya resuelto en #591 (M3).
