# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#931 (N2b)** mergeado (PR #941): el plazo de resolver solo existe por acto. Fuera las filas de combinación y de fase del catálogo, el plazo de la solicitud y el de la fase; el nivel del catálogo pasa a `ACTO`. La suspensión (`_causas_suspension`) queda conservada pero sin conectar hasta #796. Cadena completa en `docs/diseño/ESTADO_ADR049.md`.

**Próximo:** **#796**, siguiente de la cadena principal de ADR-049: conectar la suspensión al plazo de cada acto (causa a), requerimiento de subsanación) y apagar en el catálogo la marca de la causa d) (petición de informes).

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
