# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#568** (2026-09-30): notificación edictal (art. 44 LPACAP), diseñada desde el procedimiento legal en ADR-052 (migración `568_notificacion_edictal`). Trámite transversal `NOTIFICACION_EDICTAL` en las 13 fases que notifican; los intentos postales fallidos son documentos (`JUSTIFICANTE_POSTAL_1ER`/`_2DO`) y de ellos sale la escalada del semáforo; canal `EDICTO`; una acción aplica el anuncio publicado a las notificaciones agotadas o sin justificante de la fase. Fuera, #994 (justificante de remisión a boletín). Cadena en `docs/diseño/ESTADO_ADR049.md`.

**Próximo:** **#996 (N6)** (`CERT_CIERRE_SOLICITUD`, diseñado el 01/10/2026): el certificado de cierre de la solicitud, con botón en el inspector, resumen del plazo por acto, la instrucción y copia de los certificados de cierre de fase; además, el estado de la solicitud pasa a decidirse por acto. Cierra #921 y #801. El frontend de notificaciones (#929) espera a N6 y a ADR-050; hasta entonces la tramitación de una `NOTIFICAR` en el navegador sigue coja (#928 D12, #967 D1).
