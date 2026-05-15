# Contexto actual — BDDAT

> Actualizar al cerrar cada issue. Una entrada por sección, no listas.

---

**Último cerrado:** #360 y #335 — whitelists `expedientes_solicitudes` (E→S) y `solicitudes_fases` (S→F), cerrados en favor de #387. Decisión arquitectónica adoptada (ADR-007): las tres tablas whitelist E-S-F-T son blacklists implícitas que contradicen el principio del motor; se eliminan y sus reglas pasan al motor como reglas CREAR con base legal. Los verbos INICIAR y FINALIZAR se eliminan del motor (estados derivados, no acciones de usuario desde ADR-002). `tramites_tareas` y `tramites_tareas_documentos` se mantienen como capa de sugerencias. #192 marcado como semi-obsoleto (usa FINALIZAR y propone tabla que solapa con tipos existentes).

**Actuales:** —

**Próximo:** #388 (exponer tipo_sujeto_solicitado, prerrequisito) → #387 (refactoring motor+whitelists, M3) → #289 → #386 (semáforos de plazo en vista BC, M3).
