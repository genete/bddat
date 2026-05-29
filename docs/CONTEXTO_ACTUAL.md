# Contexto actual — BDDAT

> Actualizar al cerrar cada issue. La sección de estado lleva una entrada por línea.
> El detalle y el porqué de cada decisión está en `docs/diseño/DECISIONES_UI.md` y en los ADRs.
> Los issues cerrados están en `git log` — no se duplican aquí.

---

**Último cerrado:** #503 — Smoke tests pytest Fase 1 (ADR-019). `tests/smoke/` con 15 ficheros y 20 tests; fixtures de rol vía `session_transaction` (`usuario_admin/supervisor/tramitador/administrativo`) + fixtures de datos (`expediente_seed`, `entidad_seed`, `plantilla_seed`, `primer_usuario_id`); convención "una vista nueva = un smoke test nuevo" documentada en `REGLAS_DESARROLLO.md`.

**Actuales:** —

**Próximos:** **#500 — ADR-016 Vista de árbol del expediente.** Primera isla React productiva. Sustituye las 5 vistas `tramitacion_bc_*`. ~3-4 semanas.

## Hoja de ruta — Bloque UI: Implementación del revamping

Toda la fase de diseño está cerrada (auditoría UI, estudio de usuario, inventario backend, análisis crítico, 7 ADRs y registro vivo `DECISIONES_UI.md`). Lo que queda es construcción.

Orden técnico recomendado de implementación (dependencias de las cabeceras hacia abajo):

1. ~~**#497 — ADR-013 Permisos blandos generalizados.**~~ ✅ Cerrado. Dict `PERMISOS` con pares `acceder_X`/`gestionar_X`; sidebar único para todos los roles.
2. ~~**#498 — ADR-014 Layout único `base_app.html`.**~~ ✅ Cerrado. Shell de 7 áreas operativo; `lista_v2_base` y `base_bc` (deprecated) migrados a `base_app`; `base_fullwidth`/`base_acordeon`/`header` eliminados.
3. ~~**#499 — ADR-015 Scaffolding React islas.**~~ ✅ Cerrado. `react-diagramas/`→`react-src/`, multi-bundle ES + manifest, helpers `shared/` + Jinja, POC verificado con Playwright.
4. ~~**#503 — ADR-019 Smoke tests pytest (Fase 1).**~~ ✅ Cerrado. `tests/smoke/` 20 tests; fixtures por rol vía `session_transaction`; convención documentada en REGLAS_DESARROLLO.
5. **#500 — ADR-016 Vista de árbol del expediente.** Primera isla React productiva. Pieza estrella. Sustituye las 5 vistas `tramitacion_bc_*`. ~3-4 semanas.
6. **#501 — ADR-017 Vista "Mi trabajo" del administrativo.** Reutiliza el árbol como destino de acción. ~2-3 semanas.
7. **#502 — ADR-018 Command Palette (Ctrl+K).** En M4 — Pre-producción, no M2. ~1-2 semanas cuando llegue su momento.

**Total estimado bloque UI sin Command Palette: ~10-13 semanas** (1 dev + IA, ratio observado).

## Decisiones pendientes a tomar en construcción

No requieren ADR específico — se cierran al implementar:

- **Sub-stack React por isla** (state management, data fetching avanzado, librerías concretas como cmdk/react-arborist/react-resizable-panels).
- **Contenido fino del inspector / dock / viewbar** por nivel del árbol — refinable durante implementación de #500.

## Documentos vivos del revamping

- `docs/diseño/DECISIONES_UI.md` — punto de entrada al estado del revamping.
- `docs/guias/NOMENCLATURA_LAYOUT.md` — referencia rápida de las 7 áreas del layout.
- `docs/decisiones/ADR-013` a `ADR-019` — fuente de verdad de cada decisión.

## Backlog M3/M4/M5 no afectado por el revamping

Sigue en GitHub con sus milestones. Se relee cuando se retome esa fase. Ejemplos de M3 (Motor) que conviven con el revamping pero no se mezclan: #170, #171, #322, #408, #409, #432, #495, etc.
