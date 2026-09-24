# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#927** mergeado (PR #937): 8 entradas múltiples de `DATOS_CATASTRALES` en `tramites_tareas_documentos`. Deja abiertos #935 (la sugerencia de tipo mezcla `ENTRADA` y `SALIDA` y se pierde en esos pasos), #936 (la tabla no distingue por fase) y #938 (repaso general de la tabla contra `ESTRUCTURA_FTT`). Cadena completa en `docs/diseño/ESTADO_ADR049.md`.

**Próximo:** **#930 (N2)**, siguiente de la cadena principal de ADR-049 (el plazo es del acto; cumplimiento calculado).

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
