# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #678 (sesión 2026-07-22, reversión controlada del diagnóstico producido — endpoint `DELETE .../analizar`, candado servidor en las cuatro mutaciones de bloque, confirmación destructiva inline en frontend; ADR-033 §5, enmienda ADR-005). PR #690.

**Próximo:** Foco fijo (2026-07-16): dejar la fase `ANÁLISIS_SOLICITUD` completamente tramitable — interfaz, sistema documental, apertura, detección de documentos, notificación y elaboración — porque establece las bases que usarán el resto de fases. Se avanza alternando grupos de issues de este foco entre Próximo y Hecho hasta completarlo. **Cabeza de cola (2026-07-22):** #679 (continuidad de defectos entre vueltas de subsanación, ADR-033 §7) — siguiente en el orden ya fijado por ADR-033 (cada issue del bloque fija el contrato del siguiente); se elevó junto con #678 para no dejarlo abierto mientras se sigue tocando código en esa misma zona (inspector/ANALIZAR), lo que arriesgaría revisiones que diverjan del diseño ya fijado en ADR-033. #572 (ADR-027, pertenencia al EXPEDIENTE) sigue ortogonal a este bloque, diferido a propósito por Carlos. En cola, mismo foco: #657/#658 (UI + `id_remesa` de notificación), #444/#555 (plantillas `.docx` definitivas de esta fase), #630 (hub tramitador/radar huérfanos). Hueco de diseño sin issue: `ESPERAR_PLAZO` no admite N documentos simultáneos en respuesta a un requerimiento (`DISEÑO_ANALISIS_SOLICITUD.md` §5). Fuera de foco: automatización externa de firma/notificación (ADR-021) y #644-648, aparcados.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
