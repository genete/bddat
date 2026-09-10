# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **La cadena de [ADR-044](decisiones/ADR-044-reformados-proyecto-version-como-eje.md) sigue: R3 (#895) mergeado (2026-09-10), tras R1 (#885) y R2 (#887).** `fases.reformado_id` engancha cada fase a la versión vigente del proyecto (la rellena `crear_fase`, no el técnico) y la regla de §F bloquea repetir un tipo de fase dentro de la misma versión sin reformado que lo justifique, con su nodo `version` en el árbol y el inspector. Lo que no consta en el ADR ni en el issue: a diferencia de R1/R2, esta regla **no rompió ningún test existente** — solo bloquea repetir un tipo de fase dentro de la misma versión, y ningún fixture lo hacía. Dos hallazgos quedaron como issues aparte, sin relación funcional con R3: #896 (un script de expediente-tipo no anclaba el proyecto, choca con la regla de R2) y #897 (el árbol no reserva bien el ancho entre ramas hermanas muy asimétricas, límite de `d3-flextree` anterior a R3, no introducido por él).

**Próximo:**

1. **R4 — Las coberturas del análisis por versión**, que depende de R3 (ya hecho) y de **#884** para la parte de `requerimientos_tarea` (ese campo no sobrevive a un guardado destructivo). Alcance: flag de afección por reformado en `requisitos_documentales`; `reformado_id` en `documentos_requisito` y `coberturas_item_tecnico`; reescritura de `tasa_impagada` para mirar la versión vigente. Descrito en el ADR §Issues, sin crear. De R3 cuelgan también **R5** (arrastres del motor y los certificados) y **R6** (el expediente-tipo del reformado), que van después de R4.

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
