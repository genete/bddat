# Contexto actual — BDDAT

> Actualizar al cerrar cada issue. La sección de estado lleva una entrada por línea.
> El detalle y el porqué de cada decisión está en `docs/diseño/DECISIONES_UI.md` y en los ADRs.
> Los issues cerrados están en `git log` — no se duplican aquí.

---

**Último cerrado:** **#501** — Vista **"Mi trabajo" del administrativo** (ADR-017): permisos **hoja/estructura** (`gestionar_tareas` / `gestionar_estructura_expediente`, denegación 403 JSON, aplicados en el CRUD real del árbol `api_expedientes`); **cola transversal** (`GET /api/administrativo/cola` sobre el núcleo `estado_dominio`); **módulo role-adaptive** + entrada única de sidebar (admin → cola/subir; resto → seguimiento); isla React con **inspector-detalle del agregado** (Opción A, lectura) y "Ir a tramitar" al árbol; **pool abierto a todos los roles** (subir no edita el expediente, ADR-027); redirección post-login y cambio de rol al *home* del rol. PR #576. Spin-offs: limpiar `api_bc` muerto (sin consumidores tras #519); fix del test `toggle_estado`.

**Actuales:** **#579** — **Mi trabajo del supervisor** (ADR-028), gemelo de #501. **Rama Control construida** (rama `feature/issue-579-mi-trabajo-supervisor`): blueprint `supervisor` dedicado (sin entrada propia de sidebar), hub de dos bloques CONTROL/GESTIÓN (Propuesta A, hub de dos columnas) como pantalla de entrada role-adaptive vía `mi_trabajo.index`, permiso `acceder_supervision`, tarjetas del dashboard activadas, hoja de estadísticas como placeholder, smoke tests. **Aspecto del panel de estadísticas decidido** (v1: KPIs + tarta por estado + barras de carga por técnico; render isla React + Recharts) — **construcción pendiente** (sesión propia).

**Próximos:** construcción del **panel de estadísticas** de #579 (servicio agregado sobre `estado_dominio` + isla React/Recharts tematizado). Después, bloque **escritos / motor adaptativo (M4)**: **#555** (clasificación ESFT de plantillas) → **#556** (variables del motor en plantillas) → **#561** (drop de `catalogo_variables.activa` + red de tests).

> **Notas a Próximos:**
> - **#559 cerrado:** inspector-detalle del seguimiento (implementación del patrón ADR-023 para agregados que navegan al árbol, sobre el caso más simple). Spin-offs: **#570** (filtros v2 en URL), **#571** (tokens semáforo del árbol heredan del shell). Siguen vivos de #558: **#566**/**#567** (árbol), **#568** (`NOTIFICACION_INFRUCTUOSA`, M3).
> - seguimiento y "Mi trabajo" (**#501**) son agregados que navegan al árbol con **inspector-detalle del agregado** (lectura) y edición delegada al árbol — hecho en **#559** (seguimiento) y **#501** (Mi trabajo, inspector Opción A). ADR-017 quedó confirmado en implementación; su gemelo del supervisor reusará la cola/inspector.
> - **Bloque escritos / motor adaptativo (M4):** **#555** clasificación ESFT de plantillas (fase concreta vs comodín); **#556** variables del motor en plantillas (documento adaptativo, **depende de la cobertura de catálogo, M3**); **#561** drop de `catalogo_variables.activa` + red de seguridad por tests (**ADR-026**, spin-off de #556). El hilo se aborda **tras** el hilo UI en curso.
> - **#502** (épica/referencia de ADR-018) **cerrada** al mergear #532 (PR #564).

## Hoja de ruta — Implementación

### Bloque UI — revamping

Toda la fase de diseño está cerrada (auditoría UI, estudio de usuario, inventario backend, análisis crítico, 7 ADRs y registro vivo `DECISIONES_UI.md`). Lo que queda es construcción.

Orden técnico recomendado de implementación (dependencias de las cabeceras hacia abajo):

1. ~~**#497 — ADR-013 Permisos blandos generalizados.**~~ ✅ Cerrado. Dict `PERMISOS` con pares `acceder_X`/`gestionar_X`; sidebar único para todos los roles.
2. ~~**#498 — ADR-014 Layout único `base_app.html`.**~~ ✅ Cerrado. Shell de 7 áreas operativo; `lista_v2_base` y `base_bc` (deprecated) migrados a `base_app`; `base_fullwidth`/`base_acordeon`/`header` eliminados.
3. ~~**#499 — ADR-015 Scaffolding React islas.**~~ ✅ Cerrado. `react-diagramas/`→`react-src/`, multi-bundle ES + manifest, helpers `shared/` + Jinja, POC verificado con Playwright.
4. ~~**#503 — ADR-019 Smoke tests pytest (Fase 1).**~~ ✅ Cerrado. `tests/smoke/` 20 tests; fixtures por rol vía `session_transaction`; convención documentada en REGLAS_DESARROLLO.
5. ~~**#500 — ADR-016 Vista de árbol del expediente.**~~ ✅ Cerrado. Primera isla React productiva; sustituye las 5 vistas `tramitacion_bc_*`; vistas BC eliminadas (PR #519); smoke tests K completo.
6. ~~**#506 — ADR-020 Dock global: bitácora + avisos de sesión.**~~ ✅ Cerrado. Chrome global del shell (`base_app.html`); fix de bitácora vacía en #528.
7. ~~**#531 — ADR-018 Command Palette, endpoints de búsqueda.**~~ ✅ Cerrado. Blueprint `api_search_bp`, fichero `app/routes/api_search.py`. Las rutas por-entidad iniciales (`/api/search/expedientes`, `/entidades`) las **unificó #532** en `GET /api/search?tipos=…` (registro `BUSCADORES`); las rutas por-entidad se retiraron.
8. ~~**#533 — ADR-022 Sistema visual base.**~~ ✅ Cerrado. Rem global 15px como mando maestro, tabla unificada `.lista-table` (elimina la dualidad `data-table`/`expedientes-table`; ocultación responsive declarativa `.lt-hide-*` + truncado `.lt-truncate`), tokens de color sin fugas en el shell, retirada del recorte ~95% en `main`. Absorbió la migración #281. PR #538. Deja abierto #537 (cabecera del listado → viewbar).
9. ~~**#534 — ADR-023 List-detail + inspector overlay + tres capas.**~~ ✅ Cerrado. Inspector **overlay** a nivel de shell (no columna del grid; sin negociación de espacio), agnóstico Jinja/React. Modelo de **tres capas** (listado · inspector · modal grande) con **navegación por capas, no por rutas**. Infraestructura validada contra el árbol + **Entidades** como listado de referencia. Cada listado restante (seguimiento, plantillas, usuarios, proyectos) migra en su propio issue.
10. ~~**#532 — ADR-018 Command Palette (isla React, cmdk).**~~ ✅ Cerrado. Primera isla global del shell (`base_app.html`); input del topbar como disparador `readonly`. **Búsqueda unificada** `GET /api/search` con registro `BUSCADORES` (expedientes/entidades/usuarios/plantillas, sin filtro `activo`); atajos "IR A" vía `palette_nav` (fuente del sidebar). PR #564; cierra #502. Spin-off: #563 (lazy-load del bundle).
11. ~~**#558 — Unificar el núcleo de reglas de estado.**~~ ✅ Cerrado. Núcleo `estado_dominio` consumido por árbol y `seguimiento.py` como proyecciones; tabla prioridad/color canónica + regla `es_finalizadora`. PR #565. Spin-offs: #566/#567 (árbol), #568 (`NOTIFICACION_INFRUCTUOSA`, M3).
12. ~~**#501 — ADR-017 Vista "Mi trabajo" del administrativo.**~~ ✅ Cerrado. Permisos hoja/estructura en el CRUD del árbol (`api_expedientes`), cola transversal (`/api/administrativo/cola` sobre `estado_dominio`), módulo role-adaptive + sidebar, isla React con inspector-detalle (Opción A) y "Ir a tramitar"; pool abierto a todos los roles (ADR-027). PR #576. Spin-offs: limpiar `api_bc` muerto; fix test `toggle_estado`.
13. ~~**#559 — Inspector-detalle del listado de seguimiento.**~~ ✅ Cerrado. Lectura del agregado en el lenguaje del árbol (`construir_arbol_solicitud` + `_cuello_botella`); edición delegada vía "Ir a tramitar". Tokens `--sem-*` al shell (paso 1 de unificación de color). PR #569. Spin-offs: #570 (filtros v2 en URL), #571 (tokens del árbol heredan del shell).
14. **#579 — Mi trabajo del supervisor (ADR-028).** **En curso.** Gemelo de #501. Rama Control construida: blueprint `supervisor`, hub de dos bloques (Propuesta A) role-adaptive vía `mi_trabajo.index`, permiso `acceder_supervision`, tarjetas dashboard, smoke tests. Pendiente: construir el panel de estadísticas (v1 decidido: KPIs + tarta por estado + barras por técnico; isla React + Recharts) y los bloques de Gestión.

**Total estimado bloque UI: ~10-13 semanas** (1 dev + IA, ratio observado).

### Bloque escritos / motor adaptativo (M4)

Hilo independiente del revamping UI; se aborda **tras** el hilo UI en curso.

15. **#555 — Clasificación ESFT de plantillas:** fase concreta vs comodín.
16. **#556 — Variables del motor en plantillas (documento adaptativo).** Inyectar `build(expediente_id)` namespaced en el contexto del escrito. **Depende de la cobertura del catálogo (M3).**
17. **#561 — Drop de `catalogo_variables.activa` + red de seguridad por tests** (existencia de cómputo de variables/consultas + resolubilidad de tokens de plantillas). **ADR-026**; spin-off de #556.

**ADR-021 — Operaciones externas** (firma en BandeJA, notificación en Notifica-PNT): diseño acordado, issue pendiente de crear. No bloquea el bloque UI; sus formularios viven en el inspector del árbol y en la cola del admin.

## Decisiones pendientes a tomar en construcción

No requieren ADR específico — se cierran al implementar:

- **Sub-stack React por isla** (state management, data fetching avanzado, librerías concretas como cmdk/react-arborist/react-resizable-panels).
- **Contenido fino del inspector / dock / viewbar** por nivel del árbol — refinable durante implementación de #500.

## Documentos vivos del revamping

- `docs/diseño/DECISIONES_UI.md` — punto de entrada al estado del revamping.
- `docs/guias/NOMENCLATURA_LAYOUT.md` — referencia rápida de las 7 áreas del layout.
- `docs/decisiones/ADR-013` a `ADR-021` — fuente de verdad de cada decisión.

## Backlog M3/M4/M5 no afectado por el revamping

Sigue en GitHub con sus milestones. Se relee cuando se retome esa fase. Ejemplos de M3 (Motor) que conviven con el revamping pero no se mezclan: #170, #171, #322, #408, #409, #432, #495, etc.
