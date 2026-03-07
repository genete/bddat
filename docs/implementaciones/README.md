# Implementaciones Técnicas

Documentación detallada de implementaciones específicas, casos de uso y código técnico.

## 📘 Guía Principal

### GUIA_VISTAS_BOOTSTRAP.md (en raíz docs/)
**Referencia principal para Claude Code** - Implementaciones UI:
- Vista V0 (Login): Split-screen, gradiente
- Vista V1 (Dashboard): Grid cards, hover effects
- Vista V2 (Listado): Scroll infinito, C.1/C.2, API cursor
- Vista V3 (Tramitación): Acordeón Bootstrap 5, panel contexto
- **Usar esta guía para desarrollo de vistas**

---

## Documentos Activos

### VISTA_V3_TRAMITACION.md
Implementación completa Vista V3 (Tramitación):
- Plan de implementación por fases (Fase 1 completada)
- Arquitectura acordeón sin sidebar (cambio 12/02/2026)
- Modelo de datos Expediente ↔ Proyecto (crítico)
- API estructura_completa (JSON anidado)
- Mockup visual (vista3.svg)
- **Estado:** 🟡 En desarrollo (Fase 1 completada, Fase 2-6 pendientes)
- **Issue:** #101

---

## Issues y PRs de referencia

- [Issue #94 - Scroll Infinito Fase 2](https://github.com/genete/bddat/issues/94) ✅ — PR #97 merged
- [Issue #101 - Vista V3 Tramitación](https://github.com/genete/bddat/issues/101) 🟡 — en desarrollo
- [PR #98 - V1 Dashboard](https://github.com/genete/bddat/pull/98) ✅ — [PR #99 - V0 Login](https://github.com/genete/bddat/pull/99) ✅

---

## Notas

Los documentos en esta carpeta contienen **implementaciones técnicas detalladas** (código, APIs, patrones de uso).  
Para **decisiones de diseño y arquitectura**, ver [GUIA_VISTAS_BOOTSTRAP.md](../GUIA_VISTAS_BOOTSTRAP.md).  
Para **diseño de alto nivel**, ver [arquitectura/](../arquitectura/).

---

**Volver a:** [🏠 Documentación principal](../README.md)