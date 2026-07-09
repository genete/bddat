# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #442 — contenedor del inspector de la tarea ANALIZAR (ADR-023 §6),
componente React `AnalizarEditor` con contrato de consolidación de defectos
(degradado permisivo mientras #495/#581/#440 no existan). PR #603.

**Próximos:**

1. #440 — selector de requerimientos (modal shuttle); CRUD del catálogo ya
   existe (#593), falta el modal + rutas. Se enchufa al contrato de
   consolidación de #442.
2. #495 — check documental, sección inline en el contenedor de #442
   (evaluador `evaluar_requisitos` ya existe, falta integrarlo + fragmento).
3. #581 — check de ítems técnicos, sección inline en el contenedor de #442
   (necesita evaluador nuevo `evaluar_items_tecnicos`).

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
