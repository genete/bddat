# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#967 (N5a-1)** (2026-09-27): toda `NOTIFICAR` nace con su ficha y su fuente, y sin destinatario no admite documentos, salvo escape justificado e irreversible; la solicitud guarda su representante (ADR-051 §B, §K). Solo servidor: hasta #929 no hay pantalla para fijar el destinatario ni el representante, así que en el navegador una `NOTIFICAR` solo avanza forzando el escape. `seed_listado.py` y `verificar_seed.py`, ya obsoletos antes, retirados en **#974**. Cadena completa en `docs/diseño/ESTADO_ADR049.md`.

**Próximo:** **#964** y **#966**: retirar las `NOTIFICAR` que el procedimiento no tiene (`ANUNCIO_BOE`, `ANUNCIO_PRENSA`; `PORTAL_TRANSPARENCIA` a un solo ELABORAR). Son requisito de #968 (N5a-2).

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
