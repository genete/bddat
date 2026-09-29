# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#969 (N5a-3)** (2026-09-29, rama `claude/tender-archimedes-2a9dxn`, pendiente de PR): un solo `NOTIFICACION` en `RESOLUCION_DUP` (migración `969_una_notificacion_dup`, que aborta si hay trámites de los dos tipos retirados) y plazo del acto cumplido solo por la `NOTIFICAR` de fuente `SOLICITANTE`. En el PC falta aplicar la migración y pasar `comparar_catalogo.py`. Cadena en `docs/diseño/ESTADO_ADR049.md`.

**Antes, #971** (2026-09-28, PR #983): expediente-tipo `RESOLUCION_CON_ORGANISMOS` — único que llega a cerrar `RESOLUCION`, con las tres consultas cerradas (favorable, condicionado con traslado aceptado, silencio reconocido), solicitante representado, botón «añadir los que faltan» y los dos certificados de fase. De paso, un test añadido a `test_968_fuentes_destinatarios.py` (organismo sin notificar bloquea de verdad `CERT_CIERRE_FASE`) y el hueco de catálogo #982 (silencio de `CONSULTA_SEPARATA` sin vía limpia de cierre), abierto pero sin bloquear. Cadena completa en `docs/diseño/ESTADO_ADR049.md`.

**Próximo:** **#929** (interfaz de notificaciones: selector de destinatario en ELABORAR y NOTIFICAR, botón «añadir los que faltan», `NOTIFICAR` pintadas por fuente, representante de la solicitud), y después **#568** (edicto tras notificación infructuosa, art. 44). Sin #929 la tramitación de una `NOTIFICAR` en el navegador sigue coja (ADR-051, #967 D1).

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
