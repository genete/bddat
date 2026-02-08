# VISTA V3 - TRAMITACIÓN CON SIDEBAR ACORDEÓN

**Estado:** 🟡 En desarrollo (Fase 1 completada)  
**Patrón UI:** Vista Tramitación con Sidebar  
**Epic:** #93 - Sistema de Navegación UI Modular  
**Última actualización:** 8 de febrero de 2026

---

## 📋 Índice

1. [Descripción General](#descripción-general)
2. [Características Implementadas](#características-implementadas)
3. [Arquitectura de Layout](#arquitectura-de-layout)
4. [Componentes Principales](#componentes-principales)
5. [Navegación Jerárquica](#navegación-jerárquica)
6. [Archivos del Proyecto](#archivos-del-proyecto)
7. [Plan de Implementación](#plan-de-implementación)
8. [Testing y Validación](#testing-y-validación)
9. [Referencias](#referencias)

---

## Descripción General

La Vista V3 (Tramitación) es un **patrón de interfaz con sidebar acordeón** diseñado para la navegación jerárquica dentro de un expediente específico. Permite al usuario moverse entre solicitudes, fases, trámites y tareas de forma fluida y contextual.

### Objetivo

Proporcionar una interfaz eficiente para la tramitación completa de expedientes de alta tensión, con navegación clara y acceso rápido a todos los elementos de la jerarquía: Expediente → Solicitudes → Fases → Trámites → Tareas.

### Características Clave

- **Sidebar acordeón** (250px redimensionable) con lista plana tipo acordeón
- **Panel de detalle** con tabs [Datos] [Documentos] [Historial]
- **Regla de visualización**: Solo muestra paneles de hijos DIRECTOS del elemento seleccionado
- **Navegación**: Breadcrumb dinámico sin botón "Volver"
- **Divisor arrastrable** entre sidebar y contenido principal
- **Scroll independiente** en sidebar y panel detalle

---

## Características Implementadas

### ✅ Fase 1 - Estructura Base Layout (COMPLETADA)

#### Layout y CSS Base
- ✅ Layout `base_tramitacion.html` con grid 2 columnas + divisor
- ✅ CSS `v3-tramitacion.css` con:
  - Grid sidebar + contenido principal
  - Estilos sidebar acordeón (lista plana)
  - Estilos panel detalle con tabs
  - Divisor redimensionable
  - Responsive: sidebar colapsable en móvil

#### Template Mockup
- ✅ Template `tramitacion_v3.html` con datos mockup
- ✅ Sidebar con estructura acordeón semántica
- ✅ Panel detalle con tabs funcionales
- ✅ Breadcrumb dinámico

#### Ruta Flask
- ✅ Ruta `/tramitacion/<id>` para acceder a Vista V3
- ✅ Integración con sistema de autenticación

#### Stubs JavaScript
- ✅ Archivos JavaScript stub creados para Fase 2:
  - `v3-sidebar-accordion.js` - Lógica acordeón
  - `v3-tabs.js` - Sistema de tabs
  - `v3-breadcrumb.js` - Breadcrumb dinámico
  - `v3-tramitacion-controller.js` - Orquestador

### 🔴 Fase 2 - Sidebar Acordeón Dinámico (PENDIENTE)

- [ ] Componente JavaScript Sidebar completo
- [ ] Lógica acordeón (expandir/contraer)
- [ ] Gestión estado seleccionado (●)
- [ ] Visibilidad hijos directos con indentación
- [ ] Divisor redimensionable drag-and-drop
- [ ] API Backend para estructura sidebar

### 🔴 Fase 3 - Panel Detalle con Tabs (PENDIENTE)

- [ ] Sistema de tabs completo
- [ ] Paneles de hijos directos dinámicos
- [ ] Lazy loading de contenido
- [ ] APIs Backend para datos detalle

### 🔴 Fase 4 - Breadcrumb Dinámico (PENDIENTE)

- [ ] Componente Breadcrumb completo
- [ ] Construcción dinámica según elemento
- [ ] Navegación hacia ancestros
- [ ] API Backend para ancestros

### 🔴 Fase 5 - Integración y Testing (PENDIENTE)

- [ ] Orquestador principal JavaScript
- [ ] Conexión con Vista V2
- [ ] History API para URLs navegables
- [ ] Testing completo

---

## Arquitectura de Layout

### Estructura Jerárquica

```
A: app-container (grid header/main/footer)
├── B.1: app-header (sticky top)
├── B.2: app-main (grid 2 columnas: sidebar + contenido)
│   ├── C.sidebar: tramitacion-sidebar (ancho fijo, scroll independiente)
│   │   ├── sidebar-header (expediente seleccionado)
│   │   └── sidebar-nav (lista acordeón)
│   │       ├── nav-item (elemento)
│   │       ├── nav-item.active ● (seleccionado)
│   │       └── nav-item-children (hijos visibles)
│   ├── C.divider: sidebar-divider (arrastrable para redimensionar)
│   └── C.detail: tramitacion-detail (flex:1, scroll independiente)
│       ├── detail-breadcrumb (navegación ancestros)
│       ├── detail-tabs (Datos/Documentos/Historial)
│       └── detail-content (contenido según tab)
│           ├── detail-info (datos principales)
│           ├── detail-panels (paneles hijos directos)
│           │   ├── panel-hijos (lista + botón crear)
│           │   └── panel-documentos (lista + botón subir)
│           └── detail-historial (registro cambios)
└── B.3: app-footer (sticky bottom)
```

### Grid Principal App-Main

```css
.app-main {
    display: grid;
    grid-template-columns: 250px 4px 1fr;
    grid-template-areas: "sidebar divider detail";
    overflow: hidden;
}
```

### Responsive Breakpoints

| Breakpoint | Sidebar | Comportamiento |
|------------|---------|----------------|
| Desktop (>1200px) | 250px fijo | Visible siempre, redimensionable |
| Tablet (768-1199px) | 200px fijo | Visible siempre, menos ancho |
| Mobile (<768px) | Overlay | Colapsado, abre con botón hamburguesa |

---

## Componentes Principales

### 1. Sidebar Acordeón

#### Características

- **Lista plana** (NO árbol indentado)
- Elemento seleccionado marcado con **●**
- Hijos directos del seleccionado visibles (con indentación visual)
- Ancestros visibles pero compactos
- Hermanos del seleccionado visibles
- Ancho redimensionable con divisor arrastrable (250px por defecto)
- Scrollbar horizontal automático si contenido excede ancho

#### Reglas de Visualización

1. **Solo el elemento seleccionado está expandido** (marcado con ●)
2. **Hijos directos** del seleccionado se listan debajo (con indentación visual leve)
3. **Ancestros** permanecen visibles en formato compacto
4. **Hermanos** del seleccionado permanecen visibles
5. **NO es árbol indentado**, es lista plana tipo acordeón

#### Ejemplo de Estado

**Estado inicial - Solicitud AAP seleccionada:**
```
Expediente AT-123
Solicitud AAP ●          ← Seleccionado
├ Fase 1                 ← Hijos visibles
├ Fase 2
└ Fase 3
Solicitud DUP            ← Hermano
Proyecto
```

**Usuario hace clic en "Fase 1 - Información Pública":**
```
Expediente AT-123
Solicitud AAP
Fase Info. Pública ●     ← Nuevo seleccionado
├ Trámite 1              ← Nuevos hijos visibles
└ Trámite 2
Fase Resolución          ← Hermano
Fase Archivo             ← Hermano
```

### 2. Panel Detalle

#### Estructura de Tabs

- **[Datos]** - Información principal del elemento
- **[Documentos]** - Documentos asociados
- **[Historial]** - Registro de cambios y acciones

#### Regla: Solo Hijos DIRECTOS

El panel detalle **solo muestra paneles de hijos DIRECTOS** del elemento seleccionado:

| Elemento | Paneles Visibles | NO Visibles |
|----------|------------------|-------------|
| Expediente | Solicitudes, Documentos | Fases, Trámites, Tareas |
| Solicitud | Fases, Documentos | Trámites, Tareas |
| Fase | Trámites, Documentos | Tareas |
| Trámite | Tareas, Documentos | - |

#### Paneles Siempre Visibles

Los paneles de hijos se muestran **siempre**, incluso si están vacíos:
- **Con datos**: Listado + botón `[+ Crear]`
- **Sin datos**: Mensaje informativo + botón `[+ Crear]`

### 3. Breadcrumb Dinámico

#### Características

- Construcción dinámica según elemento seleccionado
- Muestra la ruta completa desde raíz: `Expedientes > AT-123 > Solicitud AAP > Fase 1`
- Cada nivel es clickable para navegación rápida hacia ancestros
- **NO hay botón [⟲ Volver]** (navegación por breadcrumb o sidebar)

#### Ejemplo de Evolución

```
Expediente seleccionado:
Expedientes > AT-123

Solicitud seleccionada:
Expedientes > AT-123 > Solicitud AAP

Fase seleccionada:
Expedientes > AT-123 > Solicitud AAP > Fase Info. Pública
```

### 4. Divisor Redimensionable

#### Características

- Divisor vertical arrastrable (⋮) entre sidebar y panel
- Usuario puede arrastrar para expandir/contraer sidebar
- Ancho persistente en localStorage
- Si contenido excede ancho → scrollbar horizontal automático en sidebar
- Al expandir suficiente → scrollbar desaparece

#### Implementación

```javascript
// Lógica simplificada
let isDragging = false;
divider.addEventListener('mousedown', () => isDragging = true);
document.addEventListener('mousemove', (e) => {
    if (isDragging) {
        const newWidth = e.clientX;
        sidebar.style.width = `${newWidth}px`;
        localStorage.setItem('sidebarWidth', newWidth);
    }
});
document.addEventListener('mouseup', () => isDragging = false);
```

---

## Navegación Jerárquica

### Flujo de Navegación Completo

```
Vista V2 (Listado expedientes)
    ↓ [Clic en botón "Tramitar"]
Vista V3 (Expediente AT-123)
    ↓ [Clic en "Solicitud AAP" en sidebar]
Vista V3 (Solicitud AAP)
    ↓ [Clic en "Fase Info. Pública"]
Vista V3 (Fase Info. Pública)
    ↓ [Clic en "Trámite 1"]
Vista V3 (Trámite 1)
    ↓ [Clic en breadcrumb "Solicitud AAP"]
Vista V3 (Solicitud AAP) - Vuelta rápida
    ↓ [Clic en breadcrumb "Inicio > Tramitación"]
Vista V2 (Listado expedientes) - Vuelta a listado
```

### Sincronización Componentes

Los 3 componentes principales deben estar **siempre sincronizados**:

1. **Sidebar** - Muestra elemento seleccionado con ●
2. **Breadcrumb** - Muestra ruta completa hasta elemento
3. **Panel Detalle** - Muestra datos + paneles hijos directos

**Evento de cambio:**
```javascript
function seleccionarElemento(tipo, id) {
    // 1. Actualizar sidebar (marcar ●, mostrar hijos)
    actualizarSidebar(tipo, id);
    
    // 2. Actualizar breadcrumb (construir ruta)
    actualizarBreadcrumb(tipo, id);
    
    // 3. Actualizar panel detalle (cargar datos + paneles)
    actualizarPanelDetalle(tipo, id);
    
    // 4. Actualizar URL (history API)
    history.pushState({tipo, id}, '', `/tramitacion/${id}`);
}
```

---

## Archivos del Proyecto

### CSS Creados

| Archivo | Descripción | Estado |
|---------|-------------|--------|
| `app/static/css/v3-tramitacion.css` | Estilos completos Vista V3 | ✅ Fase 1 |

### JavaScript Creados

| Archivo | Descripción | Estado |
|---------|-------------|--------|
| `app/static/js/v3-sidebar-accordion.js` | Lógica acordeón sidebar | 🟡 Stub |
| `app/static/js/v3-tabs.js` | Sistema de tabs | 🟡 Stub |
| `app/static/js/v3-breadcrumb.js` | Breadcrumb dinámico | 🟡 Stub |
| `app/static/js/v3-tramitacion-controller.js` | Orquestador principal | 🟡 Stub |

### Templates Creados

| Archivo | Descripción | Estado |
|---------|-------------|--------|
| `app/templates/layout/base_tramitacion.html` | Layout base V3 | ✅ Fase 1 |
| `app/templates/expedientes/tramitacion_v3.html` | Vista tramitación mockup | ✅ Fase 1 |

### Rutas Flask

| Ruta | Descripción | Estado |
|------|-------------|--------|
| `/tramitacion/<int:id>` | Acceso a Vista V3 | ✅ Fase 1 |

---

## Plan de Implementación

### Fase 1: Estructura Base Layout ✅ COMPLETADA

**Duración estimada:** 2-3 días  
**Estado:** ✅ Completada

- [x] Crear `base_tramitacion.html` (layout V3)
- [x] Crear `v3-tramitacion.css` con grid 2 columnas + divisor
- [x] Estilos sidebar acordeón (lista plana)
- [x] Estilos panel detalle con tabs
- [x] Responsive: sidebar colapsable en móvil
- [x] Template `tramitacion_v3.html` con mockup
- [x] Ruta Flask `/tramitacion/<id>`
- [x] Crear stubs JavaScript (Fase 2+)

### Fase 2: Sidebar Acordeón Dinámico 🔴 PENDIENTE

**Duración estimada:** 3-4 días

#### 2.1 Componente JavaScript Sidebar
- [ ] Crear `v3-sidebar-accordion.js` completo:
  - Lógica acordeón (expandir/contraer elementos)
  - Gestión estado seleccionado (●)
  - Visibilidad hijos directos con indentación
  - Eventos clic en elementos

#### 2.2 Divisor Redimensionable
- [ ] Implementar drag-and-drop del divisor ⋮
- [ ] Persistencia ancho sidebar (localStorage)
- [ ] Scrollbar horizontal automático si excede ancho

#### 2.3 API Backend para Sidebar
- [ ] Endpoint `GET /api/expedientes/<id>/sidebar-data`:
  - Estructura jerárquica completa del expediente
  - IDs, tipos, etiquetas de todos los elementos
  - Estado de cada elemento (completo, pendiente, etc.)

### Fase 3: Panel Detalle con Tabs 🔴 PENDIENTE

**Duración estimada:** 3-4 días

#### 3.1 Sistema de Tabs
- [ ] Crear `v3-tabs.js` completo:
  - Navegación entre [Datos] [Documentos] [Historial]
  - Lazy loading de contenido
  - Estado activo persistente

#### 3.2 Paneles de Hijos Directos
- [ ] Implementar lógica "solo hijos DIRECTOS":
  - Expediente → muestra Solicitudes
  - Solicitud → muestra Fases (NO Trámites)
  - Fase → muestra Trámites (NO Tareas)
  - Trámite → muestra Tareas
- [ ] Paneles con botón [+ Crear] siempre visibles
- [ ] Mensaje informativo cuando panel vacío

#### 3.3 APIs Backend Panel Detalle
- [ ] `GET /api/expedientes/<id>/detalles` - Datos expediente
- [ ] `GET /api/solicitudes/<id>/detalles` - Datos solicitud
- [ ] `GET /api/fases/<id>/detalles` - Datos fase
- [ ] `GET /api/tramites/<id>/detalles` - Datos trámite
- [ ] `GET /api/tareas/<id>/detalles` - Datos tarea
- [ ] `GET /api/<tipo>/<id>/hijos` - Lista hijos directos

### Fase 4: Breadcrumb Dinámico 🔴 PENDIENTE

**Duración estimada:** 1-2 días

#### 4.1 Componente Breadcrumb
- [ ] Crear `v3-breadcrumb.js` completo:
  - Construcción dinámica según elemento seleccionado
  - Navegación hacia ancestros (clic en cualquier nivel)
  - Sincronización con sidebar y panel

#### 4.2 API Backend Breadcrumb
- [ ] Endpoint `GET /api/elementos/<id>/ancestros`:
  - Cadena completa de ancestros desde raíz
  - Tipo, ID y etiqueta de cada ancestro

### Fase 5: Integración y Navegación 🔴 PENDIENTE

**Duración estimada:** 2 días

#### 5.1 Orquestador Principal
- [ ] Crear `v3-tramitacion-controller.js` completo:
  - Coordina sidebar + panel + breadcrumb
  - Estado global de navegación
  - Gestión history API (URLs navegables)

#### 5.2 Conexión con Vista V2
- [ ] Botón [Tramitar] en V2 → carga V3 con expediente seleccionado
- [ ] Breadcrumb "Tramitación" → vuelve a V2 (listado)
- [ ] Paso de parámetros: `id_expediente` en URL

### Fase 6: Documentación y Testing 🔴 PENDIENTE

**Duración estimada:** 2 días

#### 6.1 Documentación
- [ ] Actualizar este documento con implementación completa
- [ ] Ejemplos de uso APIs
- [ ] Actualizar `docs/implementaciones/README.md`
- [ ] Actualizar `docs/arquitectura/PATRONES_UI.md`

#### 6.2 Testing
- [ ] Testing visual: layout, acordeón, tabs, responsive
- [ ] Testing funcional: navegación jerárquica, breadcrumb
- [ ] Testing integración: flujo V2 → V3 → V2
- [ ] Testing accesibilidad (semántica HTML, focus-visible)

---

## Testing y Validación

### Testing Visual (Fase 1) ✅ COMPLETADO

- [x] Vista V3 carga correctamente con mockup
- [x] Grid 2 columnas funcional (sidebar + divisor + detalle)
- [x] Sidebar con estructura acordeón visible
- [x] Panel detalle con tabs visible
- [x] Header y footer V2 reutilizados correctamente
- [x] Responsive: sidebar colapsable en móvil

### Testing Funcional (Fases 2-5) 🔴 PENDIENTE

- [ ] Sidebar acordeón: expandir/contraer funciona
- [ ] Elemento seleccionado marcado con ●
- [ ] Hijos directos visibles al seleccionar elemento
- [ ] Divisor redimensionable drag-and-drop funciona
- [ ] Tabs navegan correctamente
- [ ] Paneles de hijos directos se actualizan según elemento
- [ ] Breadcrumb construye ruta correctamente
- [ ] Navegación hacia ancestros funciona
- [ ] Integración V2 → V3 funciona

### Testing Integración (Fase 5) 🔴 PENDIENTE

- [ ] Flujo completo V2 → V3 → navegación → V2
- [ ] URLs navegables con history API
- [ ] Persistencia ancho sidebar (localStorage)
- [ ] Sincronización sidebar-breadcrumb-panel

### Testing Accesibilidad 🔴 PENDIENTE

- [ ] Semántica HTML correcta
- [ ] ARIA labels en elementos interactivos
- [ ] Focus visible en sidebar y tabs
- [ ] Navegación por teclado funcional
- [ ] Contraste adecuado (colores corporativos)

---

## Referencias

### Epic y Issues

- [Epic #93](https://github.com/genete/bddat/issues/93) - Sistema de Navegación UI Modular
- [Issue #94](https://github.com/genete/bddat/issues/94) - Prototipo Vista Listado V2
- [Issue #90](https://github.com/genete/bddat/issues/90) - Especificación Patrones UI

### Documentación Relacionada

- [PATRONES_UI.md](../arquitectura/PATRONES_UI.md) - Patrones UI completos (3 vistas)
- [ISSUE_94_ESTRUCTURA.md](ISSUE_94_ESTRUCTURA.md) - Sistema de vistas V0/V1/V2/V3
- [VISTA_V0_LOGIN.md](VISTA_V0_LOGIN.md) - Vista V0 (Login)
- [VISTA_V1_DASHBOARD.md](VISTA_V1_DASHBOARD.md) - Vista V1 (Dashboard)
- [CSS_v2_GUIA_USO.md](../estilos/CSS_v2_GUIA_USO.md) - Guía CSS v2

### Pull Requests

- PR #97 - Vista V2 (Listado expedientes) ✅ Mergeado
- PR #98 - Vista V1 (Dashboard) ✅ Mergeado
- PR #99 - Vista V0 (Login) ✅ Mergeado
- PR pendiente - Vista V3 (Tramitación) 🟡 En desarrollo

---

## Notas de Diseño

### Diferencia con Vistas V0/V1/V2

| Vista | Estructura Main | Scroll | Sidebar |
|-------|----------------|--------|---------|
| V0 (Login) | Simple (pantalla completa) | B.2 scroll simple | NO |
| V1 (Dashboard) | Simple (grid cards) | B.2 scroll simple | NO |
| V2 (Listado) | C.1/C.2/D (tabla scroll) | C.2 scroll interno | NO |
| **V3 (Tramitación)** | **Grid 2 columnas** | **Sidebar + Detail scroll independiente** | **SÍ** |

### Decisiones de Diseño

**Lista plana vs Árbol indentado:**
- ✅ **Elegido**: Lista plana tipo acordeón
- ❌ **Descartado**: Árbol indentado con muchos niveles
- **Razón**: Lista plana es más limpia y clara. Indentación solo para hijos directos del seleccionado.

**Paneles de hijos directos:**
- ✅ **Elegido**: Solo mostrar paneles de hijos DIRECTOS
- ❌ **Descartado**: Mostrar todos los niveles anidados
- **Razón**: Evita sobrecarga visual. Usuario navega jerárquicamente paso a paso.

**Breadcrumb sin botón Volver:**
- ✅ **Elegido**: Breadcrumb clickable para navegación
- ❌ **Descartado**: Botón [⟲ Volver] adicional
- **Razón**: Breadcrumb ya permite navegación hacia ancestros. Botón redundante.

**Divisor redimensionable:**
- ✅ **Elegido**: Drag-and-drop para ajustar ancho sidebar
- **Razón**: Flexibilidad para usuarios con pantallas grandes/pequeñas. Persistencia mejora UX.

### Reutilización de CSS v2

Vista V3 reutiliza variables y componentes de CSS v2:
- `v2-theme.css` - Colores corporativos, tipografía
- `v2-layout.css` - Grid principal, header, footer
- `v2-components.css` - Badges, botones, formularios

Solo añade estilos específicos en `v3-tramitacion.css`:
- Grid 2 columnas sidebar + detalle
- Estilos sidebar acordeón
- Estilos divisor redimensionable
- Estilos tabs panel detalle

---

## Historial de Cambios

**08/02/2026 - Fase 1 completada:**
- Creado layout `base_tramitacion.html` con grid 2 columnas
- Creado CSS `v3-tramitacion.css` completo
- Creado template mockup `tramitacion_v3.html`
- Creada ruta Flask `/tramitacion/<id>`
- Creados stubs JavaScript para Fase 2+
- Creado documento `VISTA_V3_TRAMITACION.md`

---

**✏️ Changelog completo en commits individuales**
