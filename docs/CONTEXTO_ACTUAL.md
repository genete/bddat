# Contexto actual — BDDAT

> Actualizar al cerrar cada issue. La sección de estado lleva una entrada por línea.
> El detalle y el porqué de cada decisión está en `docs/diseño/DECISIONES_UI.md` y en los ADRs.
> Los issues cerrados están en `git log` — no se duplican aquí.

---

**Último cerrado:** #531 (ADR-018 backend palette: `GET /api/search/expedientes` + `GET /api/search/entidades`, blueprint `api_search_bp`, 6 smoke tests). Precedido de: #528/#506 (dock bitácora), #525/#523/#521/#512 (viewbar/toast/banner).

**Actuales:** —

**Próximos:** **#533** (ADR-022 sistema visual base) → **#534** (ADR-023 list-detail + inspector universal) → **#501** (ADR-017 Vista "Mi trabajo") → **#532** (frontend palette: isla React cmdk, M4).

> #502 queda como épica/referencia de ADR-018. Se cierra al mergear #532.

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
8. **#533 — ADR-022 Sistema visual base.** Rem global único (14-15px), tabla unificada (elimina dualidad `data-table`/`expedientes-table`), tokens de color sin fugas en el shell, retirada del recorte ~95% en `main`. Absorbe migración #281 (Plantillas y Usuarios al nuevo componente de tabla). Prerequisito de #534.
9. **#534 — ADR-023 List-detail + inspector universal.** Inspector redimensionable a nivel de shell (CSS Grid + JS ligero, agnóstico Jinja/React). Patrón selección-en-fila → inspector para todos los listados. Cada listado existente (seguimiento, entidades, plantillas, usuarios) migra en su propio issue; #534 pone la infraestructura de shell y el primer listado de referencia. Requiere #533.
10. **#501 — ADR-017 Vista "Mi trabajo" del administrativo.** Reutiliza el árbol como destino de acción. ~2-3 semanas. Requiere #534 (tabla unificada + patrón inspector ya operativos).
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
