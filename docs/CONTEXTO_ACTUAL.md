# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #171 — CRUD de tipos ESFTT (Expediente/Solicitud/Fase/Trámite/Tarea;
`MATRIZ_COBERTURA_BDDAT.md` N016 15%→bloque de tablas estructurales resuelto, N019
0%→cubierto). Módulo único con pestañas (`app/modules/tablas_maestras/`),
patrón config-driven en vez de 5 módulos duplicados. Campo identificador
inmutable tras el alta en las 5 tablas — protege capa 2 (datos de
`reglas_motor`/condiciones) además de capa 3 (Python), no solo lo que cubre
`catalogo_requerido.py`. Editor anidado de `tramites_tareas`/
`tramites_tareas_documentos` para la secuencia de tareas del Trámite, con una
FK compuesta nueva entre ambas tablas (antes solo "coincidían" por convención
documentada, sin garantía de BD). Fixes de paso: gap `DUP` en
`catalogo_requerido.py['TipoSolicitud']` (hardcodeado en `contiene_tipo`, sin
figurar en el manifiesto); docstring desactualizado de `TipoSolicitud`
(mencionaba una tabla puente `solicitudes_tipos` que nunca se construyó).
Verificado en navegador con los 4 roles. Suite completa: 820 passed, 24
skipped. PR #613.

**Próximos:** #479 (selector UI de modo global del motor — backend ya en #323)
y #612 (N034 — asignación masiva de expedientes a técnico, abierto en la
sesión de reposición de #171).

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
