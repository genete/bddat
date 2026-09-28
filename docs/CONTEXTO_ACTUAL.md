# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#968 (N5a-2)** (2026-09-27, PR #981): BDDAT sabe a quién notificar en cada trámite (catálogo `notificacion_fuentes`, `tramites_destinatario`, servicio de destinatarios) y no da un trámite por terminado mientras falte alguien por notificar o sobre una notificación. En el PC: aplicar la migración y recrear los expedientes-tipo. Cadena completa en `docs/diseño/ESTADO_ADR049.md`.

**Próximo:** **#971**: expediente-tipo que llega a la resolución notificada a solicitante (con representante) y organismos, con sus certificados; ya no espera a nada. Después, **#969 (N5a-3)**, que lo usa.

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
