# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#989** (2026-09-30, PR #991 y corrección PR #993): solicitante, representante y sede de notificación en la solicitud (migración `989_sede_solicitud`). El alta guarda siempre al titular como solicitante; el oficio va siempre al titular, a la sede o a su ficha; la notificación, al representante con su ficha y, sin él, al titular. El representante es siempre un autorizado activo del solicitante. Aplicado y verificado en el PC. Cadena en `docs/diseño/ESTADO_ADR049.md`.

**Próximo:** **#568** (edicto tras notificación infructuosa, art. 44) y después **N6** (`CERT_CIERRE_SOLICITUD`, sin crear). El frontend de notificaciones (#929) espera a ADR-050; hasta entonces la tramitación de una `NOTIFICAR` en el navegador sigue coja (#928 D12, #967 D1).
