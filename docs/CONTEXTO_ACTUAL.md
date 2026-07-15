# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** Repaso de bugs no documentados detectado en interfaz (2026-07-15): #641 fuga de tests que escribían en la BD real de desarrollo (fixture `app_ctx` no aislaba transacciones — causa de fases fantasma y asignaciones de expediente que se revertían solas; PR #649), #642 filtro de municipio roto en `/expedientes/` (desplegable invisible por `overflow:hidden` + filtro no persistía visualmente; PR #650), #643 scroll interno de `/tablas_maestras/` hacía scroll de toda la página (PR #651). Quedan abiertos sin implementar: #644 (filtros de tipo en tablas_maestras), #645 (filtro Estado en seguimiento), #646 (filtro Estado en expedientes), #647 (tabs de tareas_y_subidas) y #648 (generalizar integración de componentes no-`<select>` con `FiltrosListado`, deuda técnica identificada al resolver #642).

**Próximo:** _pendiente de decidir — candidatos: #644-#647 (bugs de UI diferidos, cada uno necesita antes una decisión de diseño) o #648 (refactor de sistema de componentes)._

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
