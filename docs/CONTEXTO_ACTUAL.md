# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **La decisión de los reformados de proyecto, cerrada en [ADR-044](decisiones/ADR-044-reformados-proyecto-version-como-eje.md) (2026-09-08).** **#819** se descarta a sí mismo: quien se relaciona con la versión no siempre es la fase —en consultas es el organismo, en el análisis el requisito técnico—, así que el eje pasa a `reformados_proyecto`, cuyas filas son **cortes** en la línea temporal de los `DOC_PROYECTO`, con alta por una sola puerta (la ingesta en el pool) y `documentos_proyecto` retirada por deducible. El camino, con el barrido de las nueve fases, en [`ANALISIS_REFORMADOS_PROYECTO.md`](referencia/ANALISIS_REFORMADOS_PROYECTO.md); los seis issues de implementación quedan **descritos en el ADR, sin crear**. Desbloquea **#864** y enmienda ADR-016 §1 y ADR-043 §E. Con vida propia salieron **#881**, **#882**, **#883** y **#884** (precedente de la implementación).

**Próximo:**

1. **El expediente-tipo del modificado de proyecto**, que es el que falta para trabajar la segunda ronda —de consultas y de información pública— y el que obliga a decidir cómo se modela: una sola fase `ANALISIS_SOLICITUD` con varios `ANALISIS_DOCUMENTAL`, o varias fases. Esa decisión es **#819** (asociar consultas e IP al conjunto documental del proyecto y sus modificados) y es **requisito previo**, no una consecuencia: sin ella no se puede escribir el escenario ni la variable que necesita **#864** — la advertencia al abrir una fase con `ANALISIS_SOLICITUD` sin cerrar, diferida por lo mismo (una variable ingenua cogería la fase cerrada del proyecto original y callaría justo en la ronda del modificado).

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
