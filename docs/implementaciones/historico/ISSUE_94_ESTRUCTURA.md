# Issue #94 - Estructura de Archivos

## 🎯 Sistema de Vistas (Epic #93)

### Nomenclatura de Vistas

El sistema BDDAT utiliza un sistema modular de vistas con nomenclatura **V0, V1, V2, V3...**:

| Vista | Nombre | Descripción | Estado | Documentación |
|-------|--------|--------------|--------|----------------|
| **V0** | Login | Pantalla login split-screen 60/40 | ✅ Completada | [VISTA_V0_LOGIN.md](VISTA_V0_LOGIN.md) |
| **V1** | Dashboard | Panel control con grid de cards | ✅ Completada | [VISTA_V1_DASHBOARD.md](VISTA_V1_DASHBOARD.md) |
| **V2** | Listado Expedientes | Tabla con scroll infinito | ✅ Completada | Este documento |
| **V3** | Tramitación | Sidebar acordeón + detalle | 🔴 Pendiente | - |

### Flujo de Navegación

```
V0 (Login) → V1 (Dashboard) → V2 (Listado) → V3 (Tramitación)
    ↓              ↓              ↓              ↓
Sin auth      Cards módulos    Scroll infinito  Sidebar + detalle
```

### Características Comunes

- ✅ **CSS v2** reutilizado (theme, layout, components)
- ✅ **Colores corporativos** Junta de Andalucía
- ✅ **Header/Footer** reutilizables
- ✅ **Responsive** con breakpoints consistentes
- ✅ **Accesibilidad** (focus-visible, semántica)

---

## Archivos Creados

### CSS v2 (sin tocar existentes)
- `app/static/css/v2-theme.css` - Variables, colores Junta Andalucía, tipografía ✅
- `app/static/css/v2-layout.css` - Grid principal, header, footer ✅
- `app/static/css/v2-components.css` - Tabla, badges, botones, filtros ✅
- `app/static/css/v0-login.css` - Estilos específicos Vista V0 (Login) ✅
- `app/static/css/v1-dashboard.css` - Estilos específicos Vista V1 (Dashboard) ✅

### JavaScript v2
- `app/static/js/v2-tabla-scroll-to-top.js` - Botón scroll to top para C.2 (scroll interno tabla) ✅
- `app/static/js/v2-scroll-infinito.js` - Carga automática al scrollear ✅
- `app/static/js/v2-filtros.js` - Filtros con integración scroll infinito ✅

### Templates v2
- `app/templates/layout/base_fullwidth.html` - Layout base 100% ancho ✅
- `app/templates/layout/base_login.html` - Layout sin breadcrumb/usuario (V0) ✅
- `app/templates/layout/header.html` - Header reutilizable ✅
- `app/templates/layout/footer.html` - Footer reutilizable ✅
- `app/templates/auth/login_v0.html` - Vista V0 (Login) ✅
- `app/templates/dashboard/index_v1.html` - Vista V1 (Dashboard) ✅
- `app/templates/expedientes/listado_v2.html` - Vista V2 (Listado expedientes) ✅

### Documentación
- `docs/CSS_v2_GUIA_USO.md` - Guía completa de uso CSS v2 ✅
- `docs/SCROLL_INFINITO.md` - Estrategias implementación scroll infinito ✅
- `docs/UI_PATTERNS_DATA_TABLE.md` - Patrones UI para tablas de datos ✅
- `docs/VISTA_V0_LOGIN.md` - Documentación completa Vista V0 ✅
- `docs/VISTA_V1_DASHBOARD.md` - Documentación completa Vista V1 ✅
- `docs/ISSUE_94_ESTRUCTURA.md` - Este documento (Vista V2) ✅

## Estado Implementación

### ✅ Fase 1 - Completada (PR #95)
- [x] Estructura de archivos
- [x] CSS: Variables y tema (Tarea 2) - Colores Junta Andalucía
- [x] CSS: Layout grid (Tarea 3) - Header/main/footer responsive
- [x] CSS: Componentes (Tarea 4) - Tabla, badges, botones
- [x] Test HTML funcional (test_v2.html)
- [x] Documentación CSS v2

### ✅ Fase 1.5 - Estructura C.1/C.2/D (Refinamiento Layout)
- [x] Modificar `.app-main` a flexbox con `overflow: hidden`
- [x] Crear `.lista-cabecera` (C.1) - cabecera sin scroll
- [x] Crear `.lista-scroll-container` (C.2) - contenedor con scroll propio
- [x] Refactorizar test_v2.html con estructura C.1/C.2/D
- [x] **Botón scroll-to-top para C.2** - `position: sticky` en scroll interno
- [x] Añadir `min-height` a C.2 para mantener visibilidad
- [x] Documentar patrón en CSS_v2_GUIA_USO.md
- [x] Actualizar SCROLL_INFINITO.md con prerequisitos

**Objetivo Fase 1.5:** Aislar el scroll del listado para evitar que arrastre a elementos hermanos (header, footer). Preparación para Vista 3 (sidebar + detalle) y scroll infinito.

### ✅ Fase 2 - Completada (PR #97)
- [x] Templates completos (tareas 5-6)
- [x] JavaScript scroll infinito (tarea 7)
- [x] JavaScript filtros mock (tarea 8)
- [x] Ruta Flask (tarea 9)
- [x] Testing y validación (tarea 10)
- [x] Vista V2 (Listado expedientes) funcional

### ✅ Vista V1 - Dashboard (PR #98)
- [x] CSS específico `v1-dashboard.css`
- [x] Template `dashboard/index_v1.html`
- [x] Grid responsive de cards (4/3/2/1 columnas)
- [x] Filtrado por roles de usuario
- [x] Documentación completa VISTA_V1_DASHBOARD.md

### ✅ Vista V0 - Login (PR pendiente)
- [x] CSS específico `v0-login.css`
- [x] Template `layout/base_login.html` (sin breadcrumb/usuario)
- [x] Template `auth/login_v0.html` (split-screen 60/40)
- [x] Zona información (izquierda) + formulario (derecha)
- [x] Documentación completa VISTA_V0_LOGIN.md

### 🔴 Vista V3 - Tramitación (Pendiente)
- [ ] Sidebar acordeón con navegación
- [ ] Área de detalle con scroll independiente
- [ ] Integración con workflow tramitación

## Colores Corporativos Aplicados

### Junta de Andalucía (Issue #58)

| Color | HEX | Variable | Uso |
|-------|-----|----------|-----|
| Verde corporativo | `#087021` | `--primary` | Navbar, botones principales, identidad |
| Verde hover | `#0b4c1a` | `--primary-hover` | Estados hover |
| Verde apoyo | `#c4ddca` | `--primary-light` | Fondos sutiles |
| Verde claro | `#f7fbf8` | `--primary-lighter` | Fondos muy claros |

### Semánticos

| Color | HEX | Variable | Uso |
|-------|-----|----------|-----|
| Success | `#198754` | `--success` | Resuelto, validación correcta |
| Warning | `#ffc107` | `--warning` | Advertencias, incompleto |
| Danger | `#dc3545` | `--danger` | Errores, vencido |
| Info | `#0dcaf0` | `--info` | En trámite, información |

### Grises Corporativos

| Color | HEX | Variable | Uso |
|-------|-----|----------|-----|
| Gris principal | `#111111` | `--gris-principal` | Texto principal, footer |
| Gris apoyo | `#bebebe` | `--gris-apoyo` | Texto deshabilitado |
| Gris contenedor | `#eeeeee` | `--gris-contenedor` | Fondos contenedores |
| Gris específico | `#f5f5f5` | `--gris-especifico` | Fondos muy claros |

## Efectos Visuales

- **Gradiente corporativo**: `linear-gradient(180deg, rgba(255,255,255,0.15), rgba(255,255,255,0))`
  - Aplicado a navbar y headers de tabla
  - Proporciona brillo sutil moderno

- **Sombras Bootstrap**: 
  - `--shadow-sm`: Sombra pequeña
  - `--shadow`: Sombra estándar
  - `--shadow-lg`: Sombra grande

- **Focus ring**: Verde corporativo con transparencia para accesibilidad

## Arquitectura de Layout (Fase 1.5)

### Estructura Jerárquica

```
A: app-container (grid header/main/footer)
├── B.1: app-header (sticky top)
├── B.2: app-main (flexbox vertical, overflow:hidden)
│   ├── C.1: lista-cabecera (flex-shrink:0, sin scroll)
│   │   ├── page-header (título + botón)
│   │   └── filters-row (filtros + paginación)
│   └── C.2: lista-scroll-container (flex:1, overflow-y:auto, min-height:220px)
│       ├── D: expedientes-table (crece verticalmente)
│       │   ├── thead (sticky top:0 respecto a C.2)
│       │   └── tbody
│       └── #tabla-scroll-to-top (position:sticky, bottom:1rem)
└── B.3: app-footer (sticky bottom)
```

### Comparativa de Estructuras por Vista

| Vista | Estructura | Scroll | Uso |
|-------|-----------|--------|-----|
| **V0** | A/B.1/B.2/B.3 | B.2 scroll simple | Login sin scroll interno |
| **V1** | A/B.1/B.2/B.3 | B.2 scroll simple | Dashboard grid cards |
| **V2** | A/B.1/B.2/C.1/C.2/D/B.3 | C.2 scroll independiente | Listado tabla larga |
| **V3** | A/B.1/B.2/C.sidebar/C.detail/B.3 | Ambos C scroll independiente | Tramitación |

### Ventajas de C.1/C.2/D

- ✅ Scroll aislado solo en C.2 (no afecta a B.1, B.3, ni C.1)
- ✅ Cabecera de tabla sticky funcional dentro de C.2
- ✅ `min-height: 220px` en C.2 evita colapso completo al reducir ventana
- ✅ Botón scroll-to-top con `position: sticky` dentro de C.2
- ✅ Reutilizable en Vista 3 (sidebar + detalle)
- ✅ Preparado para scroll infinito (observar solo C.2)
- ✅ UX mejorada: filtros/título siempre visibles

### Botón Scroll-to-Top (Fase 1.5)

**Implementación:**
- **Ubicación:** Dentro de `.lista-scroll-container` (C.2), hermano de `<table>`
- **CSS:** `position: sticky; bottom: 1rem` → se mantiene fijo visualmente en C.2
- **JavaScript:** `v2-tabla-scroll-to-top.js` escucha `scroll` en C.2 (no en `window`)
- **Comportamiento:** Aparece al scrollear >200px en C.2, vuelve al inicio de C.2
- **Ventaja:** Solo aparece en scroll largo (tabla), no en scroll de página (demasiado corto)

**HTML:**
```html
<div class="lista-scroll-container">
    <table class="expedientes-table">...</table>
    <button id="tabla-scroll-to-top" aria-label="Volver arriba de la tabla">
        <i class="fas fa-chevron-up"></i>
    </button>
</div>
```

**CSS clave:**
```css
#tabla-scroll-to-top {
  position: sticky;           /* Fijo visualmente en C.2 */
  bottom: 1rem;               /* Siempre a 1rem del borde inferior visible */
  left: calc(100% - 3.75rem); /* Alineado derecha */
  margin-top: -3.75rem;       /* No ocupa espacio en flujo */
  pointer-events: none;       /* Desactiva mientras invisible */
}

#tabla-scroll-to-top.visible {
  opacity: 1;
  visibility: visible;
  pointer-events: auto;       /* Activa cuando visible */
}
```

## Próximos Pasos

1. ~~Implementar CSS completo (tareas 2-4)~~ ✅ COMPLETADO (Fase 1)
2. ~~Refinar estructura layout (C.1/C.2/D)~~ ✅ COMPLETADO (Fase 1.5)
3. ~~Botón scroll-to-top para C.2~~ ✅ COMPLETADO (Fase 1.5)
4. ~~Templates completos + JavaScript~~ ✅ COMPLETADO (Fase 2 - Vista V2)
5. ~~Vista V1 (Dashboard)~~ ✅ COMPLETADO (PR #98)
6. ~~Vista V0 (Login)~~ ✅ COMPLETADO (PR pendiente)
7. Vista V3 (Tramitación con sidebar) 🔴 Pendiente

## Referencias

### Issues y Epics
- [Epic #93](https://github.com/genete/bddat/issues/93) - Sistema de Navegación UI Modular
- [Issue #94](https://github.com/genete/bddat/issues/94) - Prototipo Vista Listado v2
- [Issue #58](https://github.com/genete/bddat/issues/58) - Colores Junta Andalucía
- [Issue #90](https://github.com/genete/bddat/issues/90) - Especificación Patrones UI

### Documentación
- [VISTA_V0_LOGIN.md](VISTA_V0_LOGIN.md) - Vista V0 (Login)
- [VISTA_V1_DASHBOARD.md](VISTA_V1_DASHBOARD.md) - Vista V1 (Dashboard)
- [CSS_v2_GUIA_USO.md](CSS_v2_GUIA_USO.md) - Guía completa CSS v2
- [SCROLL_INFINITO.md](SCROLL_INFINITO.md) - Estrategias scroll infinito
- [UI_PATTERNS_DATA_TABLE.md](UI_PATTERNS_DATA_TABLE.md) - Patrones UI tablas
- [PATRONES_UI.md](arquitectura/PATRONES_UI.md) - Patrones UI generales
- [guia_colores_junta_andalucia.html](guia_colores_junta_andalucia.html) - Guía colores

### Pull Requests
- PR #97 - Vista V2 (Listado expedientes scroll infinito) ✅ Mergeado
- PR #98 - Vista V1 (Dashboard grid cards) ✅ Mergeado
- PR pendiente - Vista V0 (Login split-screen) 🔴 Pendiente review

## Notas de Diseño

**Filtros en Columnas** (cambio respecto a diseño inicial):
- Filtro global (búsqueda texto) fuera de tabla
- Filtros por columna aparecen con hover en cabecera
- Icono mini 🔽 si filtro activo
- Cabecera limpia sin hover (salvo icono filtrado)

Comentar cambios en el issue cuando se llegue a esa implementación.

**Scroll Independiente (Fase 1.5)**:
- Problema resuelto: listado largo arrastraba scroll a todo B (header, footer)
- Solución: C.2 con `overflow-y: auto` contiene el scroll del listado
- Mejora: `min-height: 220px` mantiene C.2 visible (cabecera + 2-3 filas) al reducir ventana
- Beneficio: reutilizable en cualquier contexto (Vista 3, modales, paneles)

**Botón Scroll-to-Top (Fase 1.5)**:
- Decisión: Solo en C.2 (scroll interno tabla), no en scroll de página (muy corto)
- Razón: Scroll de página (B.2) es pequeño, no merece botón
- Scroll de C.2 (tabla larga) sí merece botón para volver arriba rápidamente

## Convivencia No Destructiva

✅ Todos los archivos v2-* conviven con los existentes sin conflictos.  
✅ CSS existente (`custom.css`) no se toca.  
✅ Templates existentes no se modifican.  
✅ Estrategia de migración progresiva.  
✅ Nomenclatura clara V0/V1/V2/V3 para trazabilidad.  

## Historial de Cambios

**08/02/2026 - Vista V0 y documentación cruzada:**
- Implementada Vista V0 (Login split-screen 60/40)
- Actualizado sistema de nomenclatura vistas (V0/V1/V2/V3)
- Añadidas referencias cruzadas entre documentos
- Tabla comparativa de estructuras por vista

**08/02/2026 - Vista V1 (Dashboard):**
- Implementada Vista V1 con grid responsive de cards
- CSS específico v1-dashboard.css
- Filtrado por roles de usuario
- Documentación completa VISTA_V1_DASHBOARD.md

**08/02/2026 - Fase 2 (Vista V2 completa):**
- Templates completos con scroll infinito
- JavaScript v2-scroll-infinito.js y v2-filtros.js
- Ruta Flask /expedientes/listado-v2
- Integración API paginación cursor-based

**08/02/2026 - Fase 1.5 (refinamiento final):**
- Implementado botón scroll-to-top para C.2 con `position: sticky`
- Añadido `min-height: 220px` a C.2 (mantiene visibilidad al reducir ventana)
- Creado `v2-tabla-scroll-to-top.js` (escucha scroll en C.2, no en window)
- Actualizada documentación (CSS_v2_GUIA_USO.md, ISSUE_94_ESTRUCTURA.md)

**08/02/2026 - Fase 1.5:**
- Implementada estructura C.1/C.2/D para scroll independiente
- Refactorizado test_v2.html con nuevo layout
- Actualizada documentación CSS_v2_GUIA_USO.md
- Actualizado SCROLL_INFINITO.md con prerequisitos

**07/02/2026 - Fase 1 (PR #95):**
- Implementado CSS v2 modular completo
- Creados v2-theme.css, v2-layout.css, v2-components.css
- Test HTML completo
- Documentación inicial
