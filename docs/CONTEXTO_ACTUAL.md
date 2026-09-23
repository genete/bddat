# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#928 (N1 de ADR-049)** mergeado (PR #934): las fechas de notificación salen solo de documentos; `notificaciones` sin fechas, con `RECHAZADA` y sede (`PENDIENTE_SEDE`). El `NotificarEditor` no registra puesta a disposición ni resultado hasta **#929** (asumido, D12). Cadena completa en `docs/diseño/ESTADO_ADR049.md`.

**Próximo:** **#927** (entradas múltiples de `REMISION_ACUERDO_DATOS.ELABORAR` y `ANALISIS_RBDA.ANALIZAR`, desbloqueado por N1) y luego **#930 (N2)**, siguiente de la cadena principal.

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
