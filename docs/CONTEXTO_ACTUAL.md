# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#932 (N3)** mergeado (PR #944): `certificados` con `tipo` (obligatoria) y `fase_id` (`ON DELETE RESTRICT`), índice único parcial `(fase_id, tipo)` y backref `Fase.certificados_cumplimiento` (`Fase.certificados` ya era de `CertificadoFase`). De paso, arreglada la ruta del PDF de certificado, rota desde #425 (leía un `Documento.tipo_documento` que no existe). Cadena completa en `docs/diseño/ESTADO_ADR049.md`.

**Próximo:** **N4 (`CERT_CUMPLIMIENTO_FASE`)**, siguiente de la cadena de ADR-049; sin número todavía: crear y diseñar el issue. Decisión pendiente que se toma ahí: ADR-049 §F dice que al emitir «se guardan el PDF y `datos`», mientras que #932 anotaba el patrón ligero de los certificados actuales (PDF generado al vuelo por `cert_pdf.py`, documento virtual `bddat://`). El esquema de N3 sirve para las dos.

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
