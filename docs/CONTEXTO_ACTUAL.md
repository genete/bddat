# Contexto actual — BDDAT

> Actualizar al cerrar cada issue. La sección de estado lleva una entrada por línea.
> El detalle y el porqué de cada decisión está en `docs/diseño/DECISIONES_UI.md` y en los ADRs.
> Los issues cerrados están en `git log` — no se duplican aquí.

---

**Último cerrado:** #545 (listado de plantillas al patrón inspector ADR-023: API `/api/admin-plantillas` con cursor + filtros estado/tipo-doc/tipo-fase; inspector lectura/edición con selects ESFTT **planos** —la whitelist se eliminó en ADR-007 y no aplica a un catálogo abstracto sin expediente—; panel de tokens y explorador de fichero en **modal grande** (capa 3); `detalle`→redirect `?sel`; PR #554). Deja follow-ups del mismo módulo, claves para la **redacción de documentos**: **#552** (limpiar vestigio de whitelist del alta) y **#553** (tokens del modal filtrados por encuadramiento ESFT, con **fase de diseño previa**) — a resolver juntos; y **#555** (decisión de datos: clasificación ESFT por fase). Precedido de: #544 (inspector usuarios; deja **#550** deuda del inspector ante edición fallida —afecta a todos los módulos—; PR #551), #543 (inspector expedientes; PR #549), #534 (ADR-023 inspector overlay), #533 (ADR-022 sistema visual base).

**Actuales:** **#552 + #553** — diseño e implementación, **juntos** (mismo PR): la **redacción de documentos** depende de ellos. #553 arranca por una **fase de diseño** (modelo de aplicabilidad ESFT de los tokens; ver §"Decisiones de diseño pendientes" del issue). Queda pendiente migrar **#546** (seguimiento — caso especial sin inspector).

**Próximos:** **#552 + #553** (claves para la redacción de documentos) → **#546** (seguimiento — caso especial sin inspector) → **#532** (Command Palette isla React, cmdk, M4) → **#501** (ADR-017 "Mi trabajo del administrativo") → **Mi trabajo del supervisor** (issue por crear).

> #502 queda como épica/referencia de ADR-018. Se cierra al mergear #532.
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
9. ~~**#534 — ADR-023 List-detail + inspector overlay + tres capas.**~~ ✅ Cerrado. Inspector **overlay** a nivel de shell (no columna del grid; sin negociación de espacio), agnóstico Jinja/React. Modelo de **tres capas** (listado · inspector · modal grande) con **navegación por capas, no por rutas**. Infraestructura validada contra el árbol + **Entidades** como listado de referencia. Cada listado restante (seguimiento, plantillas, usuarios, proyectos) migra en su propio issue.
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
