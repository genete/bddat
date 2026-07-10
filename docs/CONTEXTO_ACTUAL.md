# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #608 — N012/N013 (Generación de escritos, `MATRIZ_COBERTURA_BDDAT.md`,
50%→95% ambas). Enganchado `ElaborarEditor.jsx` (patrón `AnalizarEditor.jsx`) a
la tarea ELABORAR: generar desde plantilla, preview, vinculación automática del
`.docx` como consumido (inocuo para el semáforo). Reutiliza el backend #167 sin
tocarlo. Ciclo verificado end-to-end hasta PENDIENTE_FIRMA. Elimina el JS legacy
huérfano desde la eliminación del sistema BC en #500. PR #611.

Spinoffs detectados en la misma sesión, sin tocar: token de trazabilidad
embebido en el `.docx` documentado pero no implementado ni probado (#181/#182);
enlace de documentos `bddat://` en el inspector siempre da 404, sin rama para
ese esquema (#610, nuevo). #609 (abrir documento sin salir de la tarea) se
descartó — ya existe el mecanismo en modo lectura.

**Próximos:** (vacío — ciclo de reposición pendiente, ADR-031 §7, decisión de
Carlos cuando retome).

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
