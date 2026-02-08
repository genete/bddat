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
6. [Mockup con Datos Hardcodeados](#mockup-con-datos-hardcodeados)
7. [Archivos del Proyecto](#archivos-del-proyecto)
8. [Plan de Implementación](#plan-de-implementación)
9. [Testing y Validación](#testing-y-validación)
10. [Referencias](#referencias)

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

### ✅ Fase 1 - Estructura Base Layout + Mockup (COMPLETADA)

#### Layout y CSS Base
- ✅ Layout `base_tramitacion.html` con grid 2 columnas + divisor
- ✅ CSS `v3-tramitacion.css` con:
  - Grid sidebar + contenido principal
  - Estilos sidebar acordeón (lista plana)
  - Estilos panel detalle con tabs
  - Divisor redimensionable (visual, sin funcionalidad)
  - Responsive: sidebar colapsable en móvil

#### Template Mockup con Datos Hardcodeados
- ✅ Template `tramitacion_v3.html` con **mockup completo**:
  - **Sidebar**: Expediente AT-123 con Solicitud AAP seleccionada, 3 fases, Sol. DUP, Proyecto
  - **Panel contexto**: Datos expediente siempre visibles (Nº AT, Titular, Estado, Proyecto)
  - **Breadcrumb**: Expedientes > AT-123 > Solicitud AAP
  - **Tabs funcionales**: [Datos] [Documentos] [Historial] con JavaScript básico
  - **Tab Datos**: Información de Solicitud AAP (tipo, solicitante, fecha, estado)
  - **Tab Documentos**: Listado 3 documentos PDF mockup
  - **Tab Historial**: Placeholder "próximamente"
  - **Panel Fases**: Tabla con 3 fases (Info. Pública, Resolución, Archivo) + botón [+ Nueva Fase]
  - **Panel Documentos**: Lista 5 documentos PDF + botón [+ Subir documento]

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
│       ├── detail-context (expediente/proyecto siempre visible)
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

#### Ejemplo de Estado (Mockup Fase 1)

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

### 2. Panel Contexto (Nuevo componente)

**Bloque fijo siempre visible** encima del panel detalle que muestra información del expediente/proyecto:

- **Título**: "📁 Contexto: Expediente AT-123"
- **Datos**: Nº Expediente, Titular, Estado, Proyecto
- **Objetivo**: Mantener contexto del expediente completo mientras se navega por solicitudes/fases/trámites

### 3. Panel Detalle

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

### 4. Breadcrumb Dinámico

#### Características

- Construcción dinámica según elemento seleccionado
- Muestra la ruta completa desde raíz: `Expedientes > AT-123 > Solicitud AAP`
- Cada nivel es clickable para navegación rápida hacia ancestros
- **NO hay botón [⟲ Volver]** (navegación por breadcrumb o sidebar)

#### Ejemplo de Evolución

```
Expediente seleccionado:
Expedientes > AT-123

Solicitud seleccionada (mockup Fase 1):
Expedientes > AT-123 > Solicitud AAP

Fase seleccionada:
Expedientes > AT-123 > Solicitud AAP > Fase Info. Pública
```

### 5. Divisor Redimensionable

#### Características

- Divisor vertical arrastrable (⋮) entre sidebar y panel
- Usuario puede arrastrar para expandir/contraer sidebar
- Ancho persistente en localStorage
- Si contenido excede ancho → scrollbar horizontal automático en sidebar
- Al expandir suficiente → scrollbar desaparece

**⚠️ Fase 1:** Visual implementado, funcionalidad drag-and-drop pendiente Fase 2.

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

**Evento de cambio (Fase 2+):**
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

## Mockup con Datos Hardcodeados

### Escenario del Mockup (Fase 1)

El mockup simula el estado de **Solicitud AAP seleccionada** dentro del Expediente AT-123:

#### Sidebar (jerarquía visible)

```
📁 Expediente AT-123
📝 Solicitud AAP ● (SELECCIONADA)
  ├ ⚙️ Fase 1 - Información Pública [En curso]
  ├ ⚙️ Fase 2 - Resolución [Pendiente]
  └ ⚙️ Fase 3 - Archivo [No iniciado]
📝 Solicitud DUP [Pendiente]
🏛️ Proyecto Técnico [Completo]
```

#### Panel Contexto (siempre visible)

```
📁 Contexto: Expediente AT-123

Nº Expediente: AT-123
Titular: (depende de datos reales)
Estado: En tramitación
Proyecto: (depende de datos reales)
```

#### Breadcrumb

```
Expedientes > AT-123 > Solicitud AAP
```

#### Panel Detalle - Tab [Datos]

**Información de la Solicitud AAP:**
- Tipo: AAP - Autorización Administrativa Previa
- Solicitante: Endesa SA (CIF: A12345678)
- Fecha de presentación: 15/01/2026
- Estado: Completa ✅
- Observaciones: Solicitud presentada de forma telemática. Documentación completa.

#### Panel Detalle - Tab [Documentos]

**Listado de 3 documentos mockup:**
1. 📄 proyecto_tecnico.pdf (2.3 MB) - 15/01/2026
2. 📄 licencia_municipal.pdf (1.1 MB) - 15/01/2026
3. 📄 escritura_propiedad.pdf (0.8 MB) - 15/01/2026

**Botón:** [+ Subir documento]

#### Panel Detalle - Tab [Historial]

**Placeholder:** "El historial de cambios estará disponible próximamente." 🗓️

#### Panel Hijos Directos: Fases

**Título:** Fases (3) | **Botón:** [+ Nueva Fase]

**Tabla de fases:**

| Fase | Estado | Inicio | Fin Previsto | Acciones |
|------|--------|--------|--------------|----------|
| ⚙️ Fase 1 - Información Pública | En curso ⚠️ | 20/01/2026 | 05/02/2026 (quedan 15 días) | [Ver detalle ▶] |
| ⚙️ Fase 2 - Resolución | Pendiente | - | - | [Ver detalle ▶] |
| ⚙️ Fase 3 - Archivo | No iniciado | - | - | [Ver detalle ▶] |

#### Panel Hijos Directos: Documentos

**Título:** Documentos (5) | **Botón:** [+ Subir documento]

**Listado de 5 documentos:**
1. 📄 proyecto_tecnico.pdf (2.3 MB) - 15/01/2026 [Descargar]
2. 📄 licencia_municipal.pdf (1.1 MB) - 15/01/2026 [Descargar]
3. 📄 escritura_propiedad.pdf (0.8 MB) - 15/01/2026 [Descargar]
4. 📄 anejos_tecnicos.pdf (4.2 MB) - 15/01/2026 [Descargar]
5. 📄 planos.pdf (6.5 MB) - 15/01/2026 [Descargar]

### JavaScript Básico Tabs (Mockup Fase 1)

```javascript
// Funcionalidad básica de tabs
document.addEventListener('DOMContentLoaded', function() {
    const tabs = document.querySelectorAll('.panel-tab');
    const tabContents = document.querySelectorAll('.panel-tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Remover active de todos
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(tc => tc.classList.remove('active'));
            
            // Añadir active al clickeado
            this.classList.add('active');
            const tabId = this.getAttribute('data-tab');
            document.getElementById('tab' + tabId.charAt(0).toUpperCase() + tabId.slice(1)).classList.add('active');
        });
    });
});
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
| `app/templates/expedientes/tramitacion_v3.html` | Vista tramitación con mockup completo | ✅ Fase 1 |

### Rutas Flask

| Ruta | Descripción | Estado |
|------|-------------|--------|
| `/tramitacion/<int:id>` | Acceso a Vista V3 | ✅ Fase 1 |

---

## Plan de Implementación

### Fase 1: Estructura Base Layout + Mockup ✅ COMPLETADA

**Duración:** 2-3 días  
**Estado:** ✅ Completada el 08/02/2026

- [x] Crear `base_tramitacion.html` (layout V3)
- [x] Crear `v3-tramitacion.css` con grid 2 columnas + divisor
- [x] Estilos sidebar acordeón (lista plana)
- [x] Estilos panel detalle con tabs
- [x] Responsive: sidebar colapsable en móvil
- [x] Template `tramitacion_v3.html` con **mockup completo hardcodeado**:
  - Sidebar con jerarquía Expediente AT-123
  - Panel contexto expediente (siempre visible)
  - Breadcrumb: Expedientes > AT-123 > Solicitud AAP
  - Tabs [Datos] [Documentos] [Historial] con JavaScript básico
  - Datos mockup Solicitud AAP
  - Panel Fases (3 fases en tabla)
  - Panel Documentos (5 documentos)
- [x] Ruta Flask `/tramitacion/<id>`
- [x] Crear stubs JavaScript (Fase 2+)
- [x] **Testing visual mockup completo**

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

- [x] Vista V3 carga correctamente con mockup en `/tramitacion/1`
- [x] Grid 2 columnas funcional (sidebar + divisor + detalle)
- [x] Sidebar con estructura acordeón visible:
  - Expediente AT-123 en raíz
  - Solicitud AAP marcada como seleccionada
  - 3 Fases visibles como hijos
  - Sol. DUP y Proyecto visibles como hermanos
- [x] Panel contexto expediente visible arriba del detalle
- [x] Breadcrumb visible: "Expedientes > AT-123 > Solicitud AAP"
- [x] Tabs [Datos] [Documentos] [Historial] visibles y funcionan con clic
- [x] Tab [Datos]: Información Solicitud AAP visible
- [x] Tab [Documentos]: Listado 3 documentos visible
- [x] Tab [Historial]: Placeholder visible
- [x] Panel Fases: Tabla con 3 fases + botón [+ Nueva Fase]
- [x] Panel Documentos: Lista 5 documentos + botón [+ Subir documento]
- [x] Header y footer V2 reutilizados correctamente
- [x] Responsive: sidebar visible en desktop (pendiente colapso móvil)

### Testing Funcional Básico (Fase 1) ✅ COMPLETADO

- [x] Ruta `/tramitacion/1` accesible con autenticación
- [x] Tabs [Datos] [Documentos] [Historial] cambian contenido al hacer clic
- [x] JavaScript básico tabs funciona correctamente
- [x] Botones mockup [Ver detalle ▶] visibles (sin funcionalidad)
- [x] Botones mockup [+ Nueva Fase] [+ Subir documento] visibles (sin funcionalidad)

### Testing Funcional Avanzado (Fases 2-5) 🔴 PENDIENTE

- [ ] Sidebar acordeón: expandir/contraer funciona
- [ ] Elemento seleccionado marcado con ●
- [ ] Hijos directos visibles al seleccionar elemento
- [ ] Divisor redimensionable drag-and-drop funciona
- [ ] Tabs navegan correctamente con lazy loading
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
- PR pendiente - Vista V3 (Tramitación Fase 1) 🟡 En desarrollo

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

**Panel contexto expediente:**
- ✅ **Elegido**: Bloque fijo siempre visible con datos expediente/proyecto
- **Razón**: Mantiene contexto del expediente completo mientras se navega por elementos hijos.

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
- Estilos panel contexto

---

## Historial de Cambios

**08/02/2026 - Fase 1 completada:**
- Creado layout `base_tramitacion.html` con grid 2 columnas
- Creado CSS `v3-tramitacion.css` completo
- Creado template mockup `tramitacion_v3.html` con **datos hardcodeados completos**:
  - Sidebar con jerarquía Expediente AT-123
  - Panel contexto expediente (nuevo componente)
  - Solicitud AAP seleccionada
  - Tabs funcionales [Datos] [Documentos] [Historial]
  - Panel Fases (3 fases en tabla)
  - Panel Documentos (5 documentos)
- Creada ruta Flask `/tramitacion/<id>`
- Creados stubs JavaScript para Fase 2+
- **Testing visual mockup completado**
- Creado documento `VISTA_V3_TRAMITACION.md`

---

**✏️ Changelog completo en commits individuales**
