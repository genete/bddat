# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #667 (sesión 2026-07-18, cierra el bloque de organización documental ADR-032 — A/B/C/D completos: #664-#667). #672 y #674 (misma sesión, tests que dejaban huérfanos silenciosos en la BD y en el filesystem de desarrollo — nueva herramienta `scripts/verificar_bd_tests.sh` para detectarlo). Detalle en los issues y en PR #671, #673, #675.

**Próximo:** Foco fijo (2026-07-16): dejar la fase `ANÁLISIS_SOLICITUD` completamente tramitable — interfaz, sistema documental, apertura, detección de documentos, notificación y elaboración — porque establece las bases que usarán el resto de fases. Se avanza alternando grupos de issues de este foco entre Próximo y Hecho hasta completarlo. Activo ahora: **#629** (diagnóstico `bddat://` sin representación visible entre ANALIZAR y ELABORAR) — milestone M2. #572 (ADR-027, pertenencia al EXPEDIENTE) sigue ortogonal a este bloque, diferido a propósito por Carlos. En cola, mismo foco: #441 (seed `catalogo_requerimientos`), #407 (`siglas_escritos`), #657/#658 (UI + `id_remesa` de notificación), #444/#555 (plantillas `.docx` definitivas de esta fase), #630 (hub tramitador/radar huérfanos). Hueco de diseño sin issue: `ESPERAR_PLAZO` no admite N documentos simultáneos en respuesta a un requerimiento (`DISEÑO_ANALISIS_SOLICITUD.md` §5). Fuera de foco: automatización externa de firma/notificación (ADR-021) y #644-648, aparcados.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
