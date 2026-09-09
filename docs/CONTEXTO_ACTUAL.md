# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **La cadena de [ADR-044](decisiones/ADR-044-reformados-proyecto-version-como-eje.md) arranca: R1 (#885) y R2 (#887) mergeados (2026-09-09).** `reformados_proyecto` existe y `documentos_proyecto` se retiró; la ingesta pregunta una cosa u otra según el estado del ancla, y `proyectos.documento_principal_id` la sostiene con dos reglas de motor (RD 1955/2000 arts. 123.1 y 130.1). Lo que no consta en el ADR ni en los issues: con esas reglas, **tener proyecto identificado pasa a formar parte del estado mínimo para avanzar** —como ya lo era cubrir la tasa—, y eso rompió 15 tests de #827 y #838 que fabricaban expedientes sin él; el builder de tests gana `anclar_proyecto()` y los `_cumplir_requisitos` lo llaman. Cada regla nueva del motor moverá ese mínimo otra vez.

**Próximo:**

1. **R3 — `fases.reformado_id`, el nodo del árbol y la regla genérica de §F**, que desbloquea **#864** y del que cuelgan los tres últimos: **R4** (coberturas por versión, que necesita antes **#884**), **R5** (arrastres del motor y los certificados) y **R6** (el expediente-tipo del reformado). Descritos en el ADR §Issues, sin crear. Bajo R1 y R2 quedó anotado allí lo que la implementación corrigió del diseño.

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
