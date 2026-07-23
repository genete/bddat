# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #679 (sesión 2026-07-22, continuidad de defectos entre vueltas de subsanación — `requerimientos_tarea` por `solicitud_id` + `resuelto`, ADR-033 §7). PR #691. Sesión 2026-07-23, batería de bugs de verificación manual sobre #679: #701 texto_libre ausente en GET (PR #702), #700 lápiz sin deshabilitar (PR #703), #693/#697 remount completo del inspector en cada mutación (PR #704), #694 botón guardar atenuado en cabecera (PR #705), #695 check "resuelto" condicionado a ronda de subsanación (PR #706), #699 separadores de ruta mezclados (PR #707), #696 botón de diagnóstico centrado (PR #708).

**Próximo:** Foco fijo (2026-07-16): fase `ANÁLISIS_SOLICITUD` completamente tramitable. #698 (nombre "ANY") aplazado: es poblado puro de catálogo (`tipos_tramites.nombre_en_plantilla` vacío en 31/31, `tipos_solicitudes` de AT-2004 con valor incorrecto), sin código de por medio. #572 (ADR-027) sigue ortogonal, diferido por Carlos. En cola, mismo foco: #657/#658, #444/#555, #630. Hueco de diseño sin issue: `ESPERAR_PLAZO` no admite N documentos simultáneos (`DISEÑO_ANALISIS_SOLICITUD.md` §5). Fuera de foco: ADR-021 y #644-648, aparcados.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
