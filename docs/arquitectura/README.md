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

## Histórico (Referencia Detallada)

Los siguientes documentos han sido **compactados en la guía principal** pero se mantienen como referencia histórica detallada:

### historico/PATRONES_UI.md
Especificación completa de los 3 patrones de vistas:
- Vista Dashboard (panel control sin sidebar)
- Vista Listado (tabla scroll infinito sin sidebar)
- Vista Tramitación (sidebar acordeón + detalle)
- Mockups ASCII detallados
- **Estado:** ✅ Completado (7-feb-2026)
- **Issue:** #90

### historico/VISTAS.md
Sistema completo de vistas V0/V1/V2/V3:
- Nomenclatura y flujos de navegación
- Tabla comparativa estructuras
- CSS y archivos por vista
- Historial de implementación
- **Estado:** 📚 Documentación histórica

### historico/VISTA_V0_LOGIN.md
Documentación detallada Vista V0:
- Split-screen 60/40 con gradiente
- Template base_login.html sin breadcrumb
- Flujo autenticación completo
- **Estado:** ✅ Completada (PR pendiente)

### historico/VISTA_V1_DASHBOARD.md
Documentación detallada Vista V1:
- Grid responsive 4/3/2/1 columnas
- Cards clicables con hover effects
- Filtrado por roles
- **Estado:** ✅ Completada (PR #98)

---

## Decisiones Arquitectónicas Importantes

### Sistema de Navegación Modular
- **Propuesta:** [Issue #61 - Comentario sobre navegación modular](https://github.com/genete/bddat/issues/61#issuecomment-3863698363)
- **Epic relacionado:** [#93 - Sistema de Navegación UI Modular](https://github.com/genete/bddat/issues/93)
- **Fundamento:** [Issue #90 - Especificación Patrones UI](https://github.com/genete/bddat/issues/90)

---

**Volver a:** [🏠 Documentación principal](../README.md)