# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#796** mergeado (PR #942): la suspensión del art. 22 corre sobre el plazo de cada acto y solo suspende la causa a) (requerimiento de subsanación), que empuja el plazo de todos los actos de la solicitud. La marca de la causa d) (informes, separatas) queda apagada en el catálogo (migración `796_suspension_solo_causa_a`); sigue siendo dato editable. #925 cerrado como superado. Cadena completa en `docs/diseño/ESTADO_ADR049.md`.

**Próximo:** **#932 (N3)**, siguiente de la cadena de ADR-049: columnas `tipo` y `fase_id` en `certificados`, infraestructura para N4 (`CERT_CUMPLIMIENTO_FASE`).

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
