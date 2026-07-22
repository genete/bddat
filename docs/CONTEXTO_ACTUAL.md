# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #679 (sesión 2026-07-22, continuidad de defectos entre vueltas de subsanación — `requerimientos_tarea` por `solicitud_id` + `resuelto`, ADR-033 §7). PR #691.

**Próximo:** Foco fijo (2026-07-16): dejar la fase `ANÁLISIS_SOLICITUD` completamente tramitable. Se avanza alternando grupos de issues de este foco entre Próximo y Hecho hasta completarlo. **Cabeza de cola (2026-07-22):** batería de bugs de verificación manual extremo a extremo sobre #679, mismo orden de sesión (uno tras otro si caben): #701 (crítico, bloquea diagnóstico favorable) → #700 (lápiz sin deshabilitar) → #693 (recarga completa del inspector) → #697 (doble recarga, mismo mecanismo que #693) → #694 (botón atenuado) → #695 (decisión de diseño: ¿checklist congelado tras producir?) → #698 (nombre "ANY") → #699 (ruta `/`+`\` mezclada) → #696 (confianza baja, revisar con captura). #572 (ADR-027, pertenencia al EXPEDIENTE) sigue ortogonal, diferido por Carlos. En cola, mismo foco: #657/#658 (UI + `id_remesa` de notificación), #444/#555 (plantillas `.docx` definitivas), #630 (hub tramitador/radar huérfanos). Hueco de diseño sin issue: `ESPERAR_PLAZO` no admite N documentos simultáneos (`DISEÑO_ANALISIS_SOLICITUD.md` §5). Fuera de foco: automatización externa de firma/notificación (ADR-021) y #644-648, aparcados.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
