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

## Histórico (Referencia Detallada)

Los siguientes documentos han sido **compactados en la guía principal** pero se mantienen como referencia histórica técnica:

### historico/ISSUE_94_ESTRUCTURA.md
Estructura detallada implementación Issue #94:
- Fase 2: Listado V2 con scroll infinito
- Archivos modificados y creados
- Decisión arquitectura C.1/C.2/D
- Testing y validación completa
- **Estado:** ✅ Completado (PR #97 merged)

### historico/SCROLL_INFINITO.md
Documentación técnica scroll infinito:
- Comparativa de estrategias (Append, Windowing, Cursor, Híbrido)
- Arquitectura paginación cursor-based
- JavaScript modular reutilizable
- API Backend Flask/SQLAlchemy
- Performance benchmarks
- **Estado:** 📚 Referencia técnica histórica
- **Versión:** 2.0

### historico/UI_PATTERNS_DATA_TABLE.md
Implementación patrones tablas de datos:
- Sistema DIV + CSS Grid (alternativa a `<table>`)
- Sticky header 100% funcional
- Variantes (expedientes, solicitudes, titulares)
- Reutilización en Flask (Jinja2)
- **Estado:** 📚 Referencia histórica (reemplazado por C.1/C.2)
- **Fase:** 1 completada

---

## Enlaces a Issues y PRs

### Issues Relacionados
- [Issue #90 - Especificación Patrones UI](https://github.com/genete/bddat/issues/90) ✅
- [Issue #94 - Scroll Infinito Fase 2](https://github.com/genete/bddat/issues/94) ✅
- [Issue #101 - Vista V3 Tramitación](https://github.com/genete/bddat/issues/101) 🟡
- [Epic #93 - Sistema de Navegación UI Modular](https://github.com/genete/bddat/issues/93) ⏳

### Pull Requests Relacionados
- [PR #97 - Vista V2 (Listado scroll infinito)](https://github.com/genete/bddat/pull/97) ✅ merged
- [PR #98 - Vista V1 (Dashboard grid cards)](https://github.com/genete/bddat/pull/98) ✅ merged
- [PR #99 - Vista V0 (Login split-screen)](https://github.com/genete/bddat/pull/99) ✅ merged
- PR pendiente - Vista V3 (Tramitación Fase 1+2) 🔴 Pendiente

---

## Notas

Los documentos en esta carpeta contienen **implementaciones técnicas detalladas** (código, APIs, patrones de uso).  
Para **decisiones de diseño y arquitectura**, ver [GUIA_VISTAS_BOOTSTRAP.md](../GUIA_VISTAS_BOOTSTRAP.md).  
Para **diseño de alto nivel**, ver [arquitectura/](../arquitectura/).

---

**Volver a:** [🏠 Documentación principal](../README.md)