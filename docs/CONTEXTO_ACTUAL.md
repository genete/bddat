# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #170 (CRUD de `reglas_motor` — condiciones y excepciones para Supervisor: selector guiado del patrón `sujeto` en cascada [nivel + hasta 4 selects reales + ANY, nunca texto libre], condiciones variable+operador+valor igual que catalogo_plazos/admin_requisitos, excepciones con sus propias condiciones en modal grande, integrado en /configuracion-motor/ junto al selector de modo global, N016; PR #636).

**Próximo:** #637 (CRUD propio del catálogo de `Norma` y `CatalogoVariable` para Supervisor — hoy solo lectura en selects; necesidad N083, separada de N016 al auditar #170).

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
