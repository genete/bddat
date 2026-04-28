# Contexto actual — BDDAT

> Actualizar al cerrar cada issue. Una entrada por sección, no listas.

---

**Último cerrado:** #172 — Plazos legales: `calcular_fecha_fin` art. 30 LPACAP (4 unidades), tablas `efectos_plazo`/`ambitos_inhabilidad`/`dias_inhabiles`/`catalogo_plazos`, seed festivos 2025-2026. Deuda de diseño identificada: la selección de plazo por `(tipo_elemento_id)` es insuficiente para condicionantes normativos complejos (art. 131.2 RD 1955/2000) → #341.

**Próximo:** #341 — Condiciones de aplicabilidad en `catalogo_plazos`: tabla `condiciones_plazo` paralela a `condiciones_regla`, campo `orden`, evaluador en `obtener_estado_plazo`. Bloqueante para seed real del catálogo y cierre de #328.

**En espera:** #173 — Suspensión de plazos (depende de #341).
