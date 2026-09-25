# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#956 (N4b)** mergeado (PR #957): las fases finalizadoras se cierran emitiendo su `CERT_CIERRE_FASE`, que ocupa `documento_resultado_id`, exige el certificado de cumplimiento y no admite escape a nivel de fase; guarda una foto fija del informe y se deshace reabriendo la fase. El editor ya no deja elegir documento de resultado en ellas. En desarrollo, AT-25 (`RESOLUCION_DUP` #28316) quedó cerrada con los dos certificados y la solicitud resuelta: ya no se puede reabrir, así que no sirve para volver a probar el cierre. Derivados abiertos: #954 y #955. Cadena completa en `docs/diseño/ESTADO_ADR049.md`.

**Próximo:** **N5 (notificación multi-destinatario, `Tarea.notificacion` → lista)**, siguiente de la cadena de ADR-049 y previo a N6; sin número todavía: crear y diseñar el issue. Punto de partida: ADR-049 §C/§D y «Lo que este ADR no decide» (cómo se liga cada justificante final a su destinatario).

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
