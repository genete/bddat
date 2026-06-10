# Contexto actual — BDDAT

> Actualizar al cerrar cada issue. La sección de estado lleva una entrada por línea.
> El detalle y el porqué de cada decisión está en `docs/diseño/DECISIONES_UI.md` y en los ADRs.
> Los issues cerrados están en `git log` — no se duplican aquí.

---

**Último cerrado:** #533 (ADR-022 sistema visual base: rem global 15px como mando maestro, tokens de color sin fugas en el shell, tabla unificada `.lista-table` con ocultación responsive declarativa `.lt-hide-*` y truncado `.lt-truncate`, retirada del recorte ~95%; absorbe la migración #281; PR #538). Precedido de: #531 (backend palette `/api/search`), #528/#506 (dock bitácora).

**Actuales:** **#534** (ADR-023 — estudio cerrado; inspector overlay + tres capas; implementación en 5 fases, ver issue).

**Próximos:** **Migrar los listados existentes** al patrón inspector (seguimiento\*, plantillas, usuarios, proyectos — issues a crear) → **#501** (ADR-017 "Mi trabajo", ya con patrón maduro; clona seguimiento) → **#532** (frontend palette: isla React cmdk, M4 — aislada, no preceptiva).

> #502 queda como épica/referencia de ADR-018. Se cierra al mergear #532.
> #537 (cabecera del listado → viewbar con prioridades de colapso, M2): abierto desde #533; coordinar con #534 al tocar la estructura del listado en `main`.
> \* seguimiento y "Mi trabajo" (#501) son agregados que navegan al árbol, sin inspector-detalle. **ADR-017 candidato a revisión** al implementar #501. Primero consolidar infra + migrar lo existente; las vistas nuevas aisladas se construyen con la lección aprendida.

## Hoja de ruta — Bloque UI: Implementación del revamping

Toda la fase de diseño está cerrada (auditoría UI, estudio de usuario, inventario backend, análisis crítico, 7 ADRs y registro vivo `DECISIONES_UI.md`). Lo que queda es construcción.

Orden técnico recomendado de implementación (dependencias de las cabeceras hacia abajo):

1. ~~**#497 — ADR-013 Permisos blandos generalizados.**~~ ✅ Cerrado. Dict `PERMISOS` con pares `acceder_X`/`gestionar_X`; sidebar único para todos los roles.
2. ~~**#498 — ADR-014 Layout único `base_app.html`.**~~ ✅ Cerrado. Shell de 7 áreas operativo; `lista_v2_base` y `base_bc` (deprecated) migrados a `base_app`; `base_fullwidth`/`base_acordeon`/`header` eliminados.
3. ~~**#499 — ADR-015 Scaffolding React islas.**~~ ✅ Cerrado. `react-diagramas/`→`react-src/`, multi-bundle ES + manifest, helpers `shared/` + Jinja, POC verificado con Playwright.
4. ~~**#503 — ADR-019 Smoke tests pytest (Fase 1).**~~ ✅ Cerrado. `tests/smoke/` 20 tests; fixtures por rol vía `session_transaction`; convención documentada en REGLAS_DESARROLLO.
5. ~~**#500 — ADR-016 Vista de árbol del expediente.**~~ ✅ Cerrado. Primera isla React productiva; sustituye las 5 vistas `tramitacion_bc_*`; vistas BC eliminadas (PR #519); smoke tests K completo.
6. ~~**#506 — ADR-020 Dock global: bitácora + avisos de sesión.**~~ ✅ Cerrado. Chrome global del shell (`base_app.html`); fix de bitácora vacía en #528.
7. ~~**#531 — ADR-018 Command Palette, endpoints de búsqueda.**~~ ✅ Cerrado. `GET /api/search/expedientes` y `GET /api/search/entidades`. Blueprint `api_search_bp`, fichero `app/routes/api_search.py`. 6 smoke tests.
8. ~~**#533 — ADR-022 Sistema visual base.**~~ ✅ Cerrado. Rem global 15px como mando maestro, tabla unificada `.lista-table` (elimina la dualidad `data-table`/`expedientes-table`; ocultación responsive declarativa `.lt-hide-*` + truncado `.lt-truncate`), tokens de color sin fugas en el shell, retirada del recorte ~95% en `main`. Absorbió la migración #281. PR #538. Deja abierto #537 (cabecera del listado → viewbar).
9. **#534 — ADR-023 List-detail + inspector overlay + tres capas.** Inspector **overlay** a nivel de shell (no columna del grid; sin negociación de espacio), agnóstico Jinja/React. Modelo de **tres capas** (listado · inspector · modal grande) con **navegación por capas, no por rutas**. #534 pone la infraestructura (validada contra el árbol) + **Entidades** como listado de referencia, en 5 fases. Cada listado existente restante (seguimiento, plantillas, usuarios, proyectos) migra en su propio issue. Requiere #533. Detalle en ADR-023.
10. **#501 — ADR-017 Vista "Mi trabajo" del administrativo.** Agregado que navega al árbol (gemelo de seguimiento), **sin inspector-detalle**. Reutiliza el árbol como destino de acción. ~2-3 semanas. Se construye **tras migrar los listados existentes** (patrón maduro). ADR-017 candidato a revisión. Requiere tabla unificada (#533) + scroll infinito.
11. **#532 — ADR-018 Command Palette (isla React, cmdk).** M4 — Pre-producción. Primera isla global del shell (`base_app.html`). Instalar `cmdk`, entrada en `vite.config.js`. ~1-2 semanas cuando llegue su momento.

**Total estimado bloque UI sin Command Palette frontend: ~10-13 semanas** (1 dev + IA, ratio observado).

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
