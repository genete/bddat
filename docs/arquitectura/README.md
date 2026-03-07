# Arquitectura y Diseño

Documentación de alto nivel sobre decisiones arquitectónicas, patrones de diseño y estructura del sistema.

## 📘 Guía Principal

### GUIA_VISTAS_BOOTSTRAP.md (en raíz docs/)
**Referencia principal para Claude Code** - Decisiones de diseño UI no deducibles:
- Sistema de colores corporativos Junta de Andalucía
- Arquitectura de layout (A/B/C niveles)
- Vistas V0/V1/V2/V3: decisiones clave y patrones CSS
- Scroll infinito, acordeones, responsive
- Errores comunes y checklist

---

## Documentos Activos

### FASE_3_FRONTEND_DINAMICO.md
Arquitectura del frontend dinámico (futuro):
- Sistema modular metadata-driven
- Estructura de módulos auto-descubribles
- Navegación contextual
- Migración de columnas hardcoded → Python config → JSON metadata
- **Estado:** 📋 Documentada (Pendiente implementación)
- **Relacionado:** Epic #93

---

## Decisiones Arquitectónicas Importantes

### Sistema de Navegación Modular
- **Propuesta:** [Issue #61 - Comentario sobre navegación modular](https://github.com/genete/bddat/issues/61#issuecomment-3863698363)
- **Epic relacionado:** [#93 - Sistema de Navegación UI Modular](https://github.com/genete/bddat/issues/93)
- **Fundamento:** [Issue #90 - Especificación Patrones UI](https://github.com/genete/bddat/issues/90)

---

**Volver a:** [🏠 Documentación principal](../README.md)