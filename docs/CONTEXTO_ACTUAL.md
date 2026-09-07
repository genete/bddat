# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **Lote de pulido heterogéneo — diez issues cerrados en una sola sesión (2026-09-07).** Elegidos en la revisión del mismo día por llevar poco código y agotarse en sí mismos: **#859** el listado de expedientes pedía dos endpoints inexistentes y el filtro «IA» no llegaba a construirse ([PR #869](https://github.com/genete/bddat/pull/869)) · **#571** `arbol.css` ya no redefine los tokens de semáforo, los hereda del shell ([PR #870](https://github.com/genete/bddat/pull/870)) · **#752** `ArbolESFTT.diagnostico()` nuevo, y los tres ficheros de test que duplicaban el helper migrados a él ([PR #871](https://github.com/genete/bddat/pull/871)) · **#550** el inspector ya no se queda bloqueado si el fragmento de edición falla (403/404/500) ([PR #872](https://github.com/genete/bddat/pull/872)) · **#587** checker de consistencia `catalogo_variables` ↔ Variable Registry — ya encontró un huérfano real, **#879** ([PR #873](https://github.com/genete/bddat/pull/873)) · **#802** `bitacora.detalle` y `catalogo_plazos.campo_fecha_cumplimiento` a `jsonb` ([PR #874](https://github.com/genete/bddat/pull/874)) · **#847** un `bddat://` no contemplado degrada la fila del pool en vez de tumbar el listado entero ([PR #875](https://github.com/genete/bddat/pull/875)) · **#240** tooltips centralizados con `MutationObserver`, sin reinits manuales dispersos ([PR #876](https://github.com/genete/bddat/pull/876)) · **#563** el bundle del Command Palette se carga diferido al primer Ctrl+K — de paso corrigió un `base` de Vite ausente que habría roto cualquier `import()` dinámico futuro de cualquier isla ([PR #877](https://github.com/genete/bddat/pull/877)) · **#834** el criterio ausente/vacío de #832 aplicado a las once rutas de edición que quedaban ([PR #878](https://github.com/genete/bddat/pull/878)). Dos hallazgos laterales quedaron como borrador, sin diagnosticar: **#879** (variable huérfana en `catalogo_variables`) y **#880** (`test_827` intermitente, posible residuo de #836 tras el aislamiento de BD de test).

**Próximo:**

1. **El expediente-tipo del modificado de proyecto**, que es el que falta para trabajar la segunda ronda —de consultas y de información pública— y el que obliga a decidir cómo se modela: una sola fase `ANALISIS_SOLICITUD` con varios `ANALISIS_DOCUMENTAL`, o varias fases. Esa decisión es **#819** (asociar consultas e IP al conjunto documental del proyecto y sus modificados) y es **requisito previo**, no una consecuencia: sin ella no se puede escribir el escenario ni la variable que necesita **#864** — la advertencia al abrir una fase con `ANALISIS_SOLICITUD` sin cerrar, diferida por lo mismo (una variable ingenua cogería la fase cerrada del proyecto original y callaría justo en la ronda del modificado).

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
