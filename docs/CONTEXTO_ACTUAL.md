# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#966** (2026-09-27): el portal de transparencia es un solo ELABORAR que produce la URL (`JUSTIFICANTE_PORTAL`). Ningún trámite del catálogo tiene `NOTIFICAR` sin fuente. Cadena completa en `docs/diseño/ESTADO_ADR049.md`.

**Próximo:** **#968 (N5a-2)**: fuentes por fase y trámite, `tramites_destinatario` y el invariante «nadie falta ni sobra». Ya no espera a nada: #967, #964 y #966 están cerrados.

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
