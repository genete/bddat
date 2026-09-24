# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#947 (N4)** mergeado (PR #948): el certificado de cumplimiento de la fase finalizadora, con sello se lee y sin sello se calcula; el documento citado queda protegido y se corrige deshaciendo el certificado. Sin PDF: vista HTML única. De paso, el pool deja de dar un 500 al borrar el documento de un certificado o el que cierra una fase. En desarrollo, AT-25 (`RESOLUCION_DUP` #28316) queda con su `NOTIFICACION › NOTIFICAR` y un justificante vinculado, montados para la verificación, sin certificado emitido. Cadena completa en `docs/diseño/ESTADO_ADR049.md`.

**Próximo:** **N4b (`CERT_CIERRE_FASE`)**, siguiente de la cadena de ADR-049 y previo a N6; sin número todavía: crear y diseñar el issue. Punto de partida: ADR-049 §F (ocupa `documento_resultado_id`, `reabrir_fase` pasa a deshacerlo, informe «¿cómo voy?», exige el de cumplimiento) y lo que #947 dejó para él en «Fuera de este issue».

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
