# Contexto actual — BDDAT

> Actualizar al cerrar cada issue. La sección de estado lleva una entrada por línea.
> El detalle y el porqué de cada decisión está en `docs/diseño/DECISIONES_UI.md` y en los ADRs.
> Los issues cerrados están en `git log` — no se duplican aquí.

---

**Último cerrado:** Fase de diseño del revamping UI — 7 ADRs aprobados (#497 a #503), `DECISIONES_UI.md` como registro vivo. Issue #75 sustituido y cerrado.

**Actuales:** —

**Próximos:** **Implementación del revamping UI** — empezar por #497 (permisos blandos).

## Hoja de ruta — Bloque UI: Implementación del revamping

Toda la fase de diseño está cerrada (auditoría UI, estudio de usuario, inventario backend, análisis crítico, 7 ADRs y registro vivo `DECISIONES_UI.md`). Lo que queda es construcción.

Orden técnico recomendado de implementación (dependencias de las cabeceras hacia abajo):

1. **#497 — ADR-013 Permisos blandos generalizados.** Refactor backend mecánico. No bloquea otros pero limpia base. ~2-3 días.
2. **#498 — ADR-014 Layout único `base_app.html`.** Esqueleto sobre el que monta todo el resto. Sustituye `base_fullwidth`/`lista_v2_base`/`base_bc`/`base_acordeon`. ~1 semana.
3. **#499 — ADR-015 Scaffolding React islas.** Reestructura `react-diagramas/` → `react-src/`, prepara multi-bundle, helpers de auth/permisos/API. ~1 semana.
4. **#503 — ADR-019 Smoke tests pytest (Fase 1).** Transversal. Conviene arrancar a la par que #497/#498 — convención "una vista nueva = un smoke test nuevo". ~3-5 días.
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
