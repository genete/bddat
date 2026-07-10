# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #440, #495, #581 — confluencia completa de la tarea ANALIZAR
(ADR-023 §6): check documental, check de ítems técnicos, selector de
requerimientos shuttle. Los tres alimentan `consolidar_defectos()` →
`Diagnostico.defectos`, único documento de salida. Incluye fix de
`ContextoSubsanacion` (dejaba de leer `requerimientos_tarea` directamente) y
reclasificación de ADR-025 §4. PRs #604, #605, #606.

Hueco de definición de CB/ADR-031 §7 punto 4: cerrado, sin issue propio.
Derivado: #607.

**Próximos:**

1. **N012/N013** (Generación de escritos, `MATRIZ_COBERTURA_BDDAT.md`, 50%
   ambas). Backend de generación completo — confirmado por la auditoría de
   CB de esta sesión. Falta enganchar el modal/wizard existente (fichero ya
   creado) a una vista real: hoy un Tramitador no puede llegar a generar un
   escrito desde la UI. `gh issue list --label necesidad:N012 --state all`
   devuelve #435/#407/#246/#243 — ninguno cubre este enganche. N013 no tiene
   ningún issue con label. Próxima sesión: repetir esa búsqueda por si algo
   quedó sin etiquetar (ADR-031 §7 ciclo de reposición) antes de abrir
   issue(s) nuevos.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
