# Contexto actual — BDDAT

> Actualizar al cerrar cada issue. La sección de estado lleva una entrada por línea.
> El detalle y el porqué de cada decisión está en `docs/diseño/DECISIONES_UI.md` y en los ADRs.
> Los issues cerrados están en `git log` — no se duplican aquí.

---

**Último cerrado:** **#558** — **Núcleo unificado de estado** (`estado_dominio.py`): una sola fuente de reglas (vocabulario, hoja `estado_tarea`, contenedores, `COLOR`/`PRIORIDAD`, `mayor_prioridad`) consumida por la vista de árbol y por `seguimiento.py` como proyecciones. Tabla de prioridad/color **canónica coherente con el color**; cierre de fase `es_finalizadora`-aware. PR #565. Spin-offs: **#566** (abrev ANALIZAR), **#567** (colapso manual por nodo), **#568** (trámite `NOTIFICACION_INFRUCTUOSA`, art. 44, M3).

**Actuales:** **#559** — Inspector-detalle del listado de seguimiento (lectura del agregado, edición delegada al árbol). Desbloqueado por #558.

**Próximos:** hilo UI — **#559** (inspector-detalle del seguimiento, en curso) → **#501** (Mi trabajo del administrativo) → **Mi trabajo del supervisor** (por crear). Después, bloque **escritos / motor adaptativo (M4)**: **#555** (clasificación ESFT de plantillas) → **#556** (variables del motor en plantillas) → **#561** (drop de `catalogo_variables.activa` + red de tests).

> **Notas a Próximos:**
> - **#558 cerrado:** núcleo `estado_dominio` (deuda `MODELO_ESTADOS_SEMAFORO` §10 saldada). Spin-offs vivos: **#566**/**#567** (árbol) y **#568** (`NOTIFICACION_INFRUCTUOSA`, M3).
> - seguimiento y "Mi trabajo" (**#501**) son agregados que navegan al árbol; se decidió dotarlos de **inspector-detalle del agregado** (lectura) con la edición delegada al árbol — **#559** (seguimiento) y **#501** (Mi trabajo). **ADR-017 candidato a revisión** al implementar #501. Primero consolidar infra + migrar lo existente; las vistas nuevas aisladas se construyen con la lección aprendida.
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
12. **#501 — ADR-017 Vista "Mi trabajo" del administrativo.** Agregado que navega al árbol (gemelo de seguimiento), con **inspector-detalle del agregado** (lectura) y edición delegada al árbol. **Desbloqueado (#558 cerrado); va tras #559.** ADR-017 candidato a revisión. Requiere tabla unificada (#533) + scroll infinito. ~2-3 semanas.
13. **#559 — Inspector-detalle del listado de seguimiento.** **En curso (Actual).** Lectura del agregado, edición delegada al árbol. Desbloqueado por #558.
14. **Mi trabajo del supervisor.** Gemelo de #501 para el rol supervisor. Issue por crear.

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
