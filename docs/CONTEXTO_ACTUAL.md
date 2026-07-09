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

**Próximos:**

1. **[hueco de definición, no issue implementable — ADR-031 §7 punto 4]** Gap
   detectado por Carlos en N012/N013 (generación de escritos,
   `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`), distinto del 50%/modal sin
   enganchar ya registrado ahí. Sin analizar en código todavía: hoy solo está
   confirmado que un escrito de ELABORAR construye bien su contenido en **un**
   camino — el diagnóstico de ANALIZAR de ANÁLISIS_DOCUMENTAL →
   REQUERIMIENTO_SUBSANACIÓN (fix de `ContextoSubsanacion`, #440). No se sabe
   si el resto de trámites con tarea ELABORAR tienen su Context Builder
   correctamente enganchado (ADR-025), ni si existen otros casos con el mismo
   patrón de bug que tenía `ContextoSubsanacion` (leer una tabla de borrador
   en vez del documento de salida correcto). **Primer paso de la próxima
   sesión:** `gh issue list --label necesidad:N012 --state all` y lo mismo
   para N013 — puede que ya exista algo parcial sin label. Solo si no cubre
   el hueco, auditar los CBs por trámite/plantilla y abrir el/los issue(s)
   que falten.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
