# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#893 (PR #917, mergeado 2026-09-17) — `tipos_solicitudes.nombre_en_plantilla` corregido en los ids 19/20/21, desplazados desde un catálogo de combinaciones anterior por la migración `c3d4e5f6a7b8`.** Migración manual (`893_tipos_solicitudes_nombre_en_plantilla`) por clave natural (`siglas`), no por `id`. De paso, corrige también AAE→AE en los ids 4/5 (`AE_PROVISIONAL`/`AE_DEFINITIVA`) — nomenclatura confirmada en `NORMATIVA_PLAZOS.md` §2.1/§2.2 (RD 1955/2000 art. 132, LSE 24/2013). Verificado que ningún test ni plantilla dependía de los valores previos. Detalle completo en el propio #893 (cerrado).

**Próximo:** con #914 y #893 cerrados se desbloquea el siguiente tramo de la cadena ya prevista (`#891, #892 → #801, #912 → #894`; `#431` en paralelo): el foco pasa a **#891** (regla de orden ADR-045 §C — la DUP no se resuelve sin proyecto de ejecución aprobado, ancla en `RESOLUCION_DUP.ELABORACION.ELABORAR`, ya señalada por ADR-046 §E) y **#892** (plazo de resolución de la DUP — cita normativa a corregir y plazo propio para la parte DUP de las combinadas, converge con el hueco de plazo dual que #914 dejó documentado en `DISEÑO_RESOLUCION_DUP.md` §1). #801, #912 y #894 quedan detrás en la cadena.

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
