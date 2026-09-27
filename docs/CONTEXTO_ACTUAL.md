# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#964** (2026-09-27): los anuncios de información pública siguen al JSON: BOE y prensa sin `NOTIFICAR`, BOJA sin ELABORAR. La espera sin notificación previa la decide la secuencia del catálogo (`tramites_tareas`), con aviso al supervisor en tablas maestras. Cadena completa en `docs/diseño/ESTADO_ADR049.md`.

**Próximo:** **#966**: `PORTAL_TRANSPARENCIA` a un solo ELABORAR. Con #964, requisito de #968 (N5a-2).

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
