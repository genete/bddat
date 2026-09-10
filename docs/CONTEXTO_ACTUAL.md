# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **La cadena de [ADR-044](decisiones/ADR-044-reformados-proyecto-version-como-eje.md) sigue: R4 (#899, PR #900) mergeado (2026-09-10), tras R3 (#895).** `requisitos_documentales.afectado_por_reformado` (marcado a mano, con un toggle nuevo en el admin de requisitos que no estaba en el alcance original del issue — sin él el flag solo era alcanzable por SQL directo) y `reformado_id` en `documentos_requisito`/`coberturas_item_tecnico`, cada una con dos índices únicos parciales sustituyendo el `UniqueConstraint` simple. `tasa_impagada` y `evaluar_requisitos` caen a la vinculación de la versión inicial si no hay una específica de la vigente; `evaluar_items_tecnicos` no tiene ese fallback a propósito — cada versión exige su propia verificación técnica. `requerimientos_tarea.reformado_id` se quedó solo con la columna, sin rellenar: depende de #884. Lo que no consta en el ADR: al revisar el checklist del issue antes de cerrarlo, los tests de `evaluar_requisitos`/`evaluar_items_tecnicos` solo cubrían el caso sin reformado — se completaron con los casos "con reformado" en la misma sesión, antes de marcar la tarea como hecha.

**Próximo:**

1. **R5 — Arrastres del motor y de los certificados**, que depende de R3 (ya hecho). Alcance: `fase_ip_finalizada` y `existe_fase_finalizadora_cerrada` a universal (reglas 38 y 1718); `cert_fin_ip_consultas` re-emitible por ronda; `Solicitud.estado` a la última finalizadora con `order_by` (#848, absorbible aquí o suelto); aislamiento de las alegaciones por ronda; el certificado de fin de instrucción de §H —ámbito, dos redacciones, agrupación por versión y observaciones de cierre—. Descrito en el ADR §Issues, sin crear. De R3 cuelga también **R6** (el expediente-tipo del reformado), que va después de R5.

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
