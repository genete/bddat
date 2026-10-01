# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#996 (N6)** (2026-10-01, PR #999), que cierra la cadena de ADR-049: el certificado de cierre de la solicitud (`CERT_CIERRE_SOLICITUD`), con botón en el inspector, resumen del plazo por acto, la instrucción y copia literal de los certificados de cierre de fase, retirable con justificación. La solicitud solo está resuelta con cada acto en su fase de resolución cerrada (D6), y en una resuelta y notificada ya no se crean fases. #921 y #801 cerrados. Pendiente en el PC: la migración `996_cert_cierre_solicitud`. Derivados abiertos: #997 (qué solicitudes consumen el certificado) y #998 (variables del motor que miran cualquier finalizadora). Cadena en `docs/diseño/ESTADO_ADR049.md`.

**Próximo:** **ADR-050, fase 0** (confirmado por Carlos el 01/10/2026): revalidar la tabla de consumidores (§M) y crear los issues de implementación (§I). Antes, un hilo sobre cómo reducir los riesgos que el ADR deja para fases posteriores: la edición por WebDAV sin probar en un puesto real, la respuesta de Informática a #151, el manifiesto y la exportación en la fase 7, y una salida de vuelta probada. El frontend de notificaciones (#929) solo espera ya a las fases 0-3 de ADR-050; hasta entonces la tramitación de una `NOTIFICAR` en el navegador sigue coja (#928 D12, #967 D1).
