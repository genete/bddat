# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** Cerrada la fase de diseño de **ADR-049** (fechas de notificación, cumplimiento del plazo, certificados de cierre) — sustituye a #921 y #801. Toda la cadena de issues, en qué orden y qué depende de qué, en `docs/diseño/ESTADO_ADR049.md` (documento vivo). Sin cambios en código: `app/` sigue en el estado de #892 (PR #923, último merge).

**Próximo:** Implementar la cadena desde el principio: **#926** (bug prerrequisito de N1), luego **#928 (N1)** y el resto en el orden de `docs/diseño/ESTADO_ADR049.md`.

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
