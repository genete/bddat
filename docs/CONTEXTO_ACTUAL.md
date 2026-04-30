# Contexto actual — BDDAT

> Actualizar al cerrar cada issue. Una entrada por sección, no listas.

---

**Último cerrado:** #341 — Condiciones de aplicabilidad en `catalogo_plazos`:
módulo `operadores.py`, tabla `condiciones_plazo`, campo `orden`,
variables `tiene_solicitud_aap_favorable`/`es_solicitud_aac_pura`,
evaluador `_seleccionar_catalogo` en `obtener_estado_plazo`,
seed art. 131.1 párr. 2 RD 1955/2000 (15 días con AAP previa / 30 sin ella).

**Próximo:** #347 — Defensividad del backend ante catálogo ausente o BD no disponible (M1).

**Cadena hacia #328:**
#347 → #348 (seeds en migraciones) → #345 (tramites_tareas) + #337 (tipos_documentos)
→ #346 (mapa trámite/tarea ↔ documento) → #173 (suspensión de plazos) → #328 (seed catalogo_plazos).
