# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#568** (2026-09-30): notificación edictal (art. 44 LPACAP), diseñada desde el procedimiento legal en ADR-052 (migración `568_notificacion_edictal`). Trámite transversal `NOTIFICACION_EDICTAL` en las 13 fases que notifican; los intentos postales fallidos son documentos (`JUSTIFICANTE_POSTAL_1ER`/`_2DO`) y de ellos sale la escalada del semáforo; canal `EDICTO`; una acción aplica el anuncio publicado a las notificaciones agotadas o sin justificante de la fase. Pendiente en el PC: aplicar la migración, `comparar_catalogo.py` y el BOE como entidad publicadora. Fuera, #994 (justificante de remisión a boletín). Cadena en `docs/diseño/ESTADO_ADR049.md`.

**Próximo:** **N6** (`CERT_CIERRE_SOLICITUD`, sin crear): el certificado de cierre de la solicitud, que enumera por acto y cierra #921 y #801. El frontend de notificaciones (#929) espera a N6 y a ADR-050; hasta entonces la tramitación de una `NOTIFICAR` en el navegador sigue coja (#928 D12, #967 D1).
