# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **La decisión de los reformados de proyecto, cerrada en [ADR-044](decisiones/ADR-044-reformados-proyecto-version-como-eje.md) (2026-09-08).** **#819** se descarta a sí mismo: quien se relaciona con la versión no siempre es la fase —en consultas es el organismo, en el análisis el requisito técnico—, así que el eje pasa a `reformados_proyecto`, cuyas filas son **cortes** en la línea temporal de los `DOC_PROYECTO`, con alta por una sola puerta (la ingesta en el pool) y `documentos_proyecto` retirada por deducible. El camino, con el barrido de las nueve fases, en [`ANALISIS_REFORMADOS_PROYECTO.md`](referencia/ANALISIS_REFORMADOS_PROYECTO.md); los seis issues de implementación quedan **descritos en el ADR, sin crear**. Desbloquea **#864** y enmienda ADR-016 §1 y ADR-043 §E. Con vida propia salieron **#881**, **#882**, **#883** y **#884** (precedente de la implementación).

**Próximo:**

1. **R1 — `reformados_proyecto` y la retirada de `documentos_proyecto`**, el primero de los seis issues que [ADR-044](decisiones/ADR-044-reformados-proyecto-version-como-eje.md) §Issues describe sin crear. Tras él siguen **R2** (ancla del proyecto principal y su regla de motor), **R3** (`fases.reformado_id`, nodo del árbol y la regla genérica — desbloquea **#864**), **R4** (coberturas por versión, que necesita antes **#884**), **R5** (arrastres del motor y los certificados) y **R6** (el expediente-tipo del reformado, el que faltaba para trabajar la segunda ronda). El orden y las dependencias, en el propio ADR.

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
