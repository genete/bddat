# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **La cadena de [ADR-044](decisiones/ADR-044-reformados-proyecto-version-como-eje.md) sigue: R5 (#901, PR #902) mergeado (2026-09-10), tras R4 (#899).** Absorbe #848: `Solicitud.estado` pasa de "primera/última finalizadora" a universal —exige que estén cerradas todas las que tenga la solicitud, no solo alguna— y gana `RESUELTA_DISCREPANTE` para cuando ADR-045 admite dos actos resolutorios independientes (`AAP+AAC+DUP`) sin relación de orden entre ellos. `fase_ip_finalizada`/`existe_fase_finalizadora_cerrada` reciben el mismo arreglo existencial→universal (reglas 38 y 1718). `Certificado` gana `solicitud_id`+`reformado_id` para que `cert_fin_ip_consultas` se re-emita por ronda sin confundir solicitudes del mismo expediente. Alegaciones acotadas a su fase; certificado de fin de instrucción con ámbito, observaciones de cierre y agrupación por versión (§H). El detalle de diseño y las tres correcciones de implementación (universal en vez de "la última", scoping de `Certificado`, `crear_fase` por relación en vez de FK a pelo) quedan en la nota "Hecho — #901" del propio ADR. ADR-045 actualizado: su "lo que no decide" sobre `Solicitud.estado` ya no describe el código viejo.

**Próximo:**

1. **R6 — Expediente-tipo del reformado** (ADR-044 §Issues), que depende de R3 y da por cerrada la cadena de ADR-044. Sin crear todavía — pendiente de confirmación de Carlos antes de abrirlo.

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
