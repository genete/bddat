# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#891 (PR #920, mergeado 2026-09-17) — regla de orden DUP→AAC (ADR-045 §C): `RESOLUCION_DUP` no se elabora sin AAC previa.** Variable `tiene_aac_previa` (fase hermana de la misma solicitud —`RESOLUCION`/`RESOLUCION_AAC`, ADR-047 §E— o de solicitud anterior del expediente, favorable) + regla `BLOQUEAR` con escape en `ANY/RESOLUCION_DUP/ELABORACION`, RD 1955/2000 art. 149.1. Mismo ancla que #918 fijó para `RESOLUCION_AAC` — el motor no compila sujeto a nivel de tarea. `catalogo_plazos` de la DUP queda fuera de alcance, converge con #892. Detalle completo en el propio #891 (cerrado).

**Próximo:** con #891 cerrado, el foco pasa a **#892** (cita normativa de la DUP a corregir, plazo propio para la parte DUP de las combinadas, y el plazo partido de AAP+AAC que #918 dejó documentado en `NORMATIVA_PLAZOS.md`). #801, #912 y #894 quedan detrás en la cadena; #431 en paralelo.

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
