# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **La cadena de [ADR-044](decisiones/ADR-044-reformados-proyecto-version-como-eje.md) se cierra: R6 (#903, PR #905) mergeado (2026-09-10) — R1-R6 implementados.** Primer expediente-tipo (`scripts/expedientes_dummy/reformado_analisis_y_consultas.py`) que ejercita `reformados_proyecto` por el circuito real: dos versiones de proyecto, con `ANALISIS_SOLICITUD` y `CONSULTAS` cortadas por el mismo reformado — un organismo enquistado en la `CONSULTAS` de la v1 (hueco vivo, §I, ninguna fase se salda por una posterior) y una v2 limpia que repite ese organismo y añade uno nuevo (§F, regla de motor genérica; `UNIQUE(fase_id, organismo_id)` sin conflicto entre rondas). El hueco vivo se resolvió con un organismo sin contestar y no con un defecto de checklist documental —`evaluar_requisitos` resuelve por `ultimo_reformado` en el momento de la llamada, así que un requisito sin cubrir en la v1 seguiría sin cubrir en la v2—; el porqué completo queda en la nota "Hecho — #903" del propio ADR. De paso destapó y corrigió #896 (#904, mergeado antes): ningún expediente-tipo anclaba el proyecto principal, y `consultas_varios_estados.py` llevaba desde R2 (#887) bloqueado al crear `CONSULTAS` sin que nadie lo hubiera vuelto a ejecutar. Verificado con `preparar_bd_test.py --recrear` + suite completa (1761 tests) con los tres expedientes-tipo enganchados a la semilla.

**Próximo:** por decidir en la próxima sesión — la cadena de ADR-044 queda cerrada y no hay nada encolado todavía.

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
