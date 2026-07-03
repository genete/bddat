# Contexto actual — BDDAT

> Actualizar al cerrar cada issue. La sección de estado lleva una entrada por línea.
> El detalle y el porqué de cada decisión está en `docs/diseño/DECISIONES_UI.md` y en los ADRs.
> Los issues cerrados están en `git log` — no se duplican aquí.

---

**Último cerrado:** **#583** — **CRUD admin de `requisitos_documentales`** (+ `condiciones_requisito`): módulo `admin_requisitos` (listado ADR-022/023 con inspector overlay, alta vía modal, edición con **editor de condiciones anidado** dinámico — variable+operador+valor+orden, filas añadir/quitar); API scroll infinito `api_requisitos_documentales`; permisos ADR-013 `acceder_requisitos_documentales` / `gestionar_requisitos_documentales` (crear/editar/activar-desactivar, ADMIN+SUPERVISOR) / `eliminar_requisitos_documentales` (baja física, solo ADMIN); campo `activo` (baja lógica, decisión humana — no huérfanos en expedientes antiguos) en `RequisitoDocumental`, `evaluar_requisitos` excluye inactivos. PR #584.

**Último hito:** **PR #580 mergeado** (parte de **#579**) — **panel de estadísticas del supervisor** (ADR-028 §2): servicio agregado `estadisticas_supervisor` que **reusa el núcleo `estado_dominio`** vía `construir_arbol` por expediente (estado agregado + plazos vencidos, sin reimplementar reglas); endpoint `GET /supervisor/api/estadisticas` (`{kpis, por_estado, por_tecnico}`, `acceder_supervision`); isla React **+ Recharts** (KPIs · tarta por estado · barras de carga por técnico) con **tematizado JdA documentado** (banda azul → `--bs-blue`, porque en JdA `--bs-primary` es verde); título de las hojas del supervisor movido a la **viewbar estándar**; smoke tests. Antes se construyó la **rama Control** de #579 (blueprint `supervisor`, hub de dos bloques role-adaptive vía `mi_trabajo.index`, permiso `acceder_supervision`, tarjetas del dashboard).

**#579 sigue abierto:** el **bloque GESTIÓN del supervisor queda APARCADO** por decisión (2026-07-02) para priorizar el hilo de análisis documental y escritos. Sus piezas viven en issues propios (config motor #170/#171/#479, plazos legales, operaciones masivas #295).

**Próximos:** foco elegido (2026-07-02) en la **fase de análisis documental / requerimientos (M3)**, base de datos+motor sobre la que luego se generan los escritos de requerimiento/subsanación. Sesión de análisis (2026-07-03) revisó el clúster contra el código real (no solo los issues) y amplió el diseño — ver `docs/referencia/DISEÑO_ANALISIS_SOLICITUD.md` §4/§7. Clúster: **#408** (re-scope: poblar `requisitos_documentales` — el modelo ya está construido en #192, más general de lo previsto; solo siembra mínima, no exhaustiva), **#441** (seed `catalogo_requerimientos`), **#440** (selector de requerimientos en tarea ANALIZAR, UI/BE), **#495** (check documental completo: UI + integración en `ContextoAnalisisDocumental` + auto-generación de defectos), **#442** (formulario diagnóstico en ANALIZAR, cierre del hilo); nuevos **#581** (checklist gemelo de contenido técnico del proyecto, RD 223/2008 y RD 337/2014) y **#582** (regla de motor: tasa impagada bloquea toda fase posterior — único bloqueo de este clúster que es de motor; separata→Consultas y EIA→AAU_AAUS_INTEGRADA son imposibilidad natural de tarea, sin issue). **#583** (CRUD admin del catálogo para Supervisor, habilita que #408 no tenga que ser exhaustivo) ✅ cerrado — PR #584. *Orden: #441/#408/#581(diseño) en paralelo → #495 → UI de #581 → #440 → #442 → #582 al final.* Después, **escritos / motor adaptativo (M4)**: **#555** (clasificación ESFT de plantillas) → **#556** (variables del motor en plantillas, **depende de la cobertura de catálogo M3**) → **#561** (drop de `catalogo_variables.activa` + red de tests). La **gestión de consultas** (pista CONSULTAS) entra después; necesita issue-cabecera propio.

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
14. **#579 — Mi trabajo del supervisor (ADR-028).** **Bloque CONTROL hecho** (PR #580 mergeado): hub de dos bloques role-adaptive vía `mi_trabajo.index` + blueprint `supervisor` + permiso `acceder_supervision`; **panel de estadísticas** (servicio agregado `estadisticas_supervisor` sobre `estado_dominio` + isla React/Recharts tematizado: KPIs, tarta por estado, barras por técnico). **Bloque GESTIÓN aparcado** (2026-07-02); sus piezas en issues propios (#170/#171/#479, plazos, #295). Issue #579 permanece abierto como paraguas.

**Total estimado bloque UI: ~10-13 semanas** (1 dev + IA, ratio observado).

### Bloque análisis documental / requerimientos (M3) — foco actual

Foco elegido tras cerrar la rama Control de #579 (2026-07-02). Fase de análisis de la
solicitud (tarea ANALIZAR): datos+motor de requerimientos, base de los escritos de
requerimiento/subsanación del bloque M4. Orden afinado en sesión de análisis (2026-07-03,
ver `docs/referencia/DISEÑO_ANALISIS_SOLICITUD.md` §4/§7): #441/#408/#581(diseño) en
paralelo → #495 → UI de #581 → #440 → #442 (cierre) → #582 al final.

- **#408 — Poblar catálogo de requisitos documentales:** modelo ya construido en #192 (más general de lo previsto aquí); solo siembra mínima (incluido el requisito de tasas que consume #582) — el resto del contenido normativo crece incremental vía #583, no bloquea.
- ~~**#583 — CRUD admin de `requisitos_documentales`.**~~ ✅ Cerrado. Módulo `admin_requisitos` (listado ADR-022/023 + inspector, alta modal, editor de condiciones anidado dinámico), API scroll infinito, permisos ADR-013 (`acceder`/`gestionar`/`eliminar` — baja física solo ADMIN), campo `activo` (baja lógica) en `RequisitoDocumental`. PR #584.
- **#441 — Seed `catalogo_requerimientos`.**
- **#440 — Selector de requerimientos en tarea ANALIZAR** (UI/BE).
- **#495 — Check documental completo en tarea ANALIZAR:** UI + integración en `ContextoAnalisisDocumental` + auto-generación de defectos.
- **#442 — Formulario diagnóstico en tarea ANALIZAR** (tabla `diagnosticos`, UI) — cierre del hilo.
- **#581 — Checklist de contenido técnico del proyecto** (RD 223/2008, RD 337/2014) — nuevo, mecanismo gemelo del check documental.
- **#582 — Regla de motor: tasa impagada bloquea toda fase posterior** — nuevo; único bloqueo de este clúster que es de motor (separata→Consultas y EIA→AAU_AAUS_INTEGRADA son imposibilidad natural de tarea, sin issue).

### Bloque escritos / motor adaptativo (M4)

Hilo independiente del revamping UI; se aborda **tras** consolidar el análisis documental.

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
