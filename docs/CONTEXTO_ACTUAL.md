# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#914 (PR #916, mergeado 2026-09-15) — `RESOLUCION_DUP` y `DATOS_CATASTRALES` ya existen en el catálogo real de BD, ADR-046 implementado.** Fuente de verdad cerrada primero (`ESTRUCTURA_ESF.md` v2.4, `ESTRUCTURA_FTT.md` v6.5), luego 8 migraciones (`tipos_solicitudes` con `AAP+DUP` ex-#911, `tipos_fases`, `tipos_documentos` con 10 filas nuevas, `tipos_tramites`/`tramites_tareas` con 11 trámites, `fases_tramites`, `tramites_tareas_documentos`, `reglas_motor` con el duplicado quirúrgico de las 5 reglas de `RESOLUCION`, `catalogo_plazos`) y tres piezas de código (`informe_instruccion.py` de mapa a lista de fases finalizadoras, `nombres_documentos.py`, `api_expedientes.py`). Trámite nuevo no previsto en el diseño original, detectado en sesión: `REQUERIMIENTO_RBDA_DEFINITIVA` (previo a `RESOLUCION_DUP.ELABORACION`, procedimiento interno del servicio — RBDA definitiva o confirmación de la ya publicada, 10 días). El plazo de fase de `RESOLUCION_DUP` (6 meses) no se creó — transferido a #892, que ya lo tenía listado como tarea pendiente. Detalle completo de hallazgos y decisiones en el propio #914 (cerrado) y en `DISEÑO_RESOLUCION_DUP.md`.

**Próximo:** con #914 cerrado se desbloquea el siguiente tramo de la cadena ya prevista (`#914+#893 → #891, #892 → #801, #912 → #894`; `#431` en paralelo): el foco pasa a **#891** (regla de orden ADR-045 §C — la DUP no se resuelve sin proyecto de ejecución aprobado, ancla en `RESOLUCION_DUP.ELABORACION.ELABORAR`, ya señalada por ADR-046 §E) y **#892** (plazo de resolución de la DUP — cita normativa a corregir y plazo propio para la parte DUP de las combinadas, converge con el hueco de plazo dual que #914 dejó documentado en `DISEÑO_RESOLUCION_DUP.md` §1). **#893** (bug de `nombre_en_plantilla` en `tipos_solicitudes` 19/20/21) sigue abierto y en paralelo, sin depender de #914. #801, #912 y #894 quedan detrás en la cadena.

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
