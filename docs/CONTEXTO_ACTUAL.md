# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#969 (N5a-3)** (2026-09-29, PR #988): un solo `NOTIFICACION` en `RESOLUCION_DUP` (migración `969_una_notificacion_dup`) y plazo del acto cumplido solo por la `NOTIFICAR` de fuente `SOLICITANTE`. Aplicado y verificado en el PC. Cierra N5a. Después, revisión de #929 (29/09/2026, sin código): reescrito como acumulador que se ejecuta tras #568, N6 y ADR-050 fases 0-3; sus huecos de dominio salen a #989. Cadena en `docs/diseño/ESTADO_ADR049.md`.

**Próximo:** **#989** (solicitante, representante y sede de notificación en la solicitud; el alta deja de guardar al autorizado como solicitante; refresco de las `NOTIFICAR` al cambiarlos), después **#568** (edicto tras notificación infructuosa, art. 44) y después **N6** (`CERT_CIERRE_SOLICITUD`, sin crear). El frontend de notificaciones (#929) espera a ADR-050; hasta entonces la tramitación de una `NOTIFICAR` en el navegador sigue coja (#928 D12, #967 D1).
