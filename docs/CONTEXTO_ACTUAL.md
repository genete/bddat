# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#918 (PR #919, mergeado 2026-09-17) — `RESOLUCION_AAP`/`RESOLUCION_AAC` como acto partido de AAP+AAC (ADR-047).** Dos fases finalizadoras nuevas, alternativa al acto conjunto `RESOLUCION` (elección del técnico, no regla de motor); exclusión mutua en el árbol; duplicado quirúrgico de las 5 reglas de motor de `RESOLUCION`; regla de orden AAP→AAC (ADR-047 §F) con ancla real distinta de la prevista — el motor no compila sujeto a nivel de tarea, así que bloquea en `crear_tramite` (`ELABORACION` de `RESOLUCION_AAC`), no en la tarea `ELABORAR`. `catalogo_plazos` del plazo partido queda fuera de alcance, converge con #892 (comentado ahí). #891 queda desbloqueado (comentado ahí). Detalle completo en el propio #918 (cerrado).

**Próximo:** con #918 cerrado, el foco pasa a **#891** (regla de orden ADR-045 §C — la DUP no se resuelve sin proyecto de ejecución aprobado; `tiene_aac_previa` ya puede escribirse correctamente considerando también `RESOLUCION_AAC` partida, ADR-047 §E) y **#892** (cita normativa de la DUP a corregir, plazo propio para la parte DUP de las combinadas, y ahora también el plazo partido de AAP+AAC que #918 dejó documentado en `NORMATIVA_PLAZOS.md`). #801, #912 y #894 quedan detrás en la cadena; #431 en paralelo.

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
