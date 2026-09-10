# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#897 (PR #906, mergeado 2026-09-10) — el árbol del expediente ya no solapa la caja del nivel `version` con sus vecinas.** Faltaba la regla CSS `.arbol-nodo--version` en `arbol.css`: el nivel `version` se añadió a `layout.js` en #895 (`TAM.version: [210, 56]`) pero nunca se replicó el ancho fijo equivalente en CSS, así que el título de una versión con texto largo (p. ej. "REFORMADO DE PROYECTO DE FECHA...") desbordaba los 210px que el layout calcula e invadía visualmente al nodo vecino. El diagnóstico inicial apuntó a una limitación de `d3-flextree`/del algoritmo de layout (contornos por nivel); descartado tras verificar con datos reales (expediente AT-29/4134) que el cálculo de posiciones siempre fue correcto — el desajuste estaba solo entre lo que `layout.js` asume y lo que `arbol.css` no garantizaba. Fix de una línea; verificado en navegador.

**Próximo:** por decidir en la próxima sesión — la cadena de ADR-044 queda cerrada y no hay nada encolado todavía.

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
