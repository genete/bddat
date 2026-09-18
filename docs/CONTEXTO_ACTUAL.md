# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#892 (PR #923, mergeado 2026-09-17) — plazo propio de fases finalizadoras (ADR-048): `RESOLUCION_DUP`/`RESOLUCION_AAP`/`RESOLUCION_AAC` ya tienen plazo en `catalogo_plazos`.** Reabre a propósito la exclusión de nivel FASE que #788 fijó, acotada a fases finalizadoras (son el acto, no taxonomía ESFTT) — `catalogo_plazos.tipo_elemento` admite ahora `FASE` junto a `SOLICITUD`/`TAREA`. Corrige de paso la cita inexistente de `ANY/DUP` (art. 145.4 RD 1955/2000, que no existe → art. 148.1, 3→6 meses). El cumplimiento de las tres filas nuevas queda `NULL` a propósito — la Fase no tiene hoy cierre propio (equivalente a `Solicitud.documento_cierre_id`); converge con **#921** (nueva, cierre propio por fase). Superficie de UI del plazo de fase en el árbol/inspector: **#922** (nueva). Detalle completo en `docs/decisiones/ADR-048-plazo-fase-finalizadora.md` y en el propio #892 (cerrado).

**Próximo:** con #892 cerrado, el foco pasa a **#801 + #921 juntos** — mismo problema de cardinalidad de notificaciones (certificado agregado de cierre), a nivel solicitud (`CERT_CIERRE_SOLICITUD`, #801) y a nivel fase finalizadora (#921, nueva); diseñarlos en la misma sesión evita que #921 quede atado a una lectura de #801 que luego cambie. #912, #894 y #922 quedan detrás en la cadena; #431 en paralelo.

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
