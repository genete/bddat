# Sistema de Vistas BDDAT

## 🎯 Descripción General

Sistema modular de vistas para BDDAT con nomenclatura **V0, V1, V2, V3...** que permite migración progresiva desde el sistema antiguo al nuevo sistema V2 (Epic #93).

---

## 📊 Tabla Comparativa de Vistas

| Vista | Nombre | Objetivo | Estructura | Estado | Documentación |
|-------|--------|----------|-----------|--------|----------------|
| **V0** | Login | Pantalla autenticación | A/B.1/B.2/B.3 split-screen | ✅ Completada | [VISTA_V0_LOGIN.md](VISTA_V0_LOGIN.md) |
| **V1** | Dashboard | Panel control módulos | A/B.1/B.2/B.3 grid cards | ✅ Completada | [VISTA_V1_DASHBOARD.md](VISTA_V1_DASHBOARD.md) |
| **V2** | Listado | Tabla scroll infinito | A/B.1/B.2/C.1/C.2/D | ✅ Completada | [ISSUE_94_ESTRUCTURA.md](ISSUE_94_ESTRUCTURA.md) |
| **V3** | Tramitación | Sidebar + detalle | A/B.1/B.2/C.side/C.detail | 🔴 Pendiente | - |

---

## 🗺️ Flujo de Navegación

```
┌───────────────────────────────────────────────────────────┐
│  FLUJO USUARIO: Sin autenticación → Autenticado → Navegación → Trabajo  │
└───────────────────────────────────────────────────────────┘

    V0 (Login)           V1 (Dashboard)      V2 (Listado)        V3 (Tramitación)
    ┌───────────┐        ┌────────────┐     ┌────────────┐     ┌───────────────┐
    │  Bienvenida │        │ Cards Módulos │     │   Tabla    │     │  Sidebar +    │
    │  Instruc.   │────►│ Navegación   │──►│   Scroll   │──►│  Detalle      │
    │ [Formulario]│        │ Accesos     │     │  Infinito  │     │  Workflow     │
    └───────────┘        └────────────┘     └────────────┘     └───────────────┘
      │                       │                │                   │
   Sin auth            Post-login       Consulta datos      Tramitación
```

---

## 📖 Vista V0 - Login

### Objetivo
Pantalla de autenticación con diseño split-screen moderno.

### Características
- ✅ Split-screen 60% info / 40% formulario
- ✅ Zona izquierda: Bienvenida, ayuda, enlaces
- ✅ Zona derecha: Formulario login centrado
- ✅ Header V2 simplificado (sin breadcrumb/usuario)
- ✅ Footer V2 reutilizado
- ✅ Responsive: columnas apiladas en mobile

### Rutas
- `GET /auth/login` - Formulario login
- `POST /auth/login` - Procesar autenticación

### Archivos
- CSS: `app/static/css/v0-login.css`
- Template base: `app/templates/layout/base_login.html`
- Template: `app/templates/auth/login_v0.html`
- Ruta: `app/routes/auth.py`

### Documentación
📝 [VISTA_V0_LOGIN.md](VISTA_V0_LOGIN.md) - Documentación completa

### Estado
✅ **Completada** - PR pendiente merge

---

## 🏗️ Vista V1 - Dashboard

### Objetivo
Panel de control principal post-login con acceso rápido a módulos.

### Características
- ✅ Grid responsive de cards (4/3/2/1 columnas)
- ✅ Cards clicables con iconos circulares
- ✅ Filtrado por roles de usuario
- ✅ Hover effects (elevación + cambio color)
- ✅ Cards futuras deshabilitadas ("Próximamente")
- ✅ Header/Footer V2 completos

### Rutas
- `GET /` - Dashboard principal
- `GET /dashboard` - Dashboard (alias)

### Cards Disponibles
- Expedientes (V2 scroll infinito)
- Usuarios (listado actual)
- Proyectos (listado actual)
- Mis Expedientes
- Nuevo Expediente
- Mi Perfil
- *Próximamente:* Tareas, Documentos, Estadísticas, Configuración

### Archivos
- CSS: `app/static/css/v1-dashboard.css`
- Template: `app/templates/dashboard/index_v1.html`
- Ruta: `app/routes/dashboard.py`

### Documentación
📝 [VISTA_V1_DASHBOARD.md](VISTA_V1_DASHBOARD.md) - Documentación completa

### Estado
✅ **Completada** - PR #98 mergeado

---

## 📊 Vista V2 - Listado Expedientes

### Objetivo
Tabla de expedientes con scroll infinito y filtros.

### Características
- ✅ Estructura C.1 (filtros fijos) / C.2 (scroll independiente)
- ✅ Scroll infinito con paginación cursor-based
- ✅ Filtros en tiempo real con debounce
- ✅ Cabecera tabla sticky dentro de C.2
- ✅ Botón scroll-to-top sticky en C.2
- ✅ API REST `/api/expedientes` con paginación

### Rutas
- `GET /expedientes/listado-v2` - Vista V2
- `GET /api/expedientes` - API paginación cursor

### Componentes JavaScript
- `v2-scroll-infinito.js` - Carga automática
- `v2-filtros.js` - Filtros con integración scroll
- `v2-tabla-scroll-to-top.js` - Botón scroll en C.2

### Archivos
- Template: `app/templates/expedientes/listado_v2.html`
- API: `app/routes/api_expedientes.py`
- JavaScript: `app/static/js/v2-*.js`

### Documentación
📝 [ISSUE_94_ESTRUCTURA.md](ISSUE_94_ESTRUCTURA.md) - Documentación completa  
📝 [SCROLL_INFINITO.md](SCROLL_INFINITO.md) - Estrategias scroll infinito  
📝 [UI_PATTERNS_DATA_TABLE.md](UI_PATTERNS_DATA_TABLE.md) - Patrones UI tablas  

### Estado
✅ **Completada** - PR #97 mergeado

---

## 🛠️ Vista V3 - Tramitación (Pendiente)

### Objetivo
Interfaz de tramitación con sidebar acordeón y área de detalle.

### Características (Planeadas)
- 🔴 Sidebar izquierda con navegación acordeón
- 🔴 Área derecha con detalle del expediente
- 🔴 Ambas áreas con scroll independiente
- 🔴 Integración workflow tramitación
- 🔴 Estados, fases, trámites, tareas
- 🔴 Gestión documental

### Estado
🔴 **Pendiente** - Epic #93 Fase futura

---

## 🎨 Sistema CSS V2 (Compartido)

### Archivos CSS Modulares

Todas las vistas V0/V1/V2/V3 comparten estos CSS base:

| Archivo | Contenido | Uso |
|---------|-----------|-----|
| `v2-theme.css` | Variables, colores Junta Andalucía, tipografía | Base temática |
| `v2-layout.css` | Grid A/B/C, header, footer, responsive | Estructura layout |
| `v2-components.css` | Tabla, badges, botones, filtros | Componentes UI |

### CSS Específicos por Vista

| Vista | Archivo | Contenido |
|-------|---------|----------|
| V0 | `v0-login.css` | Split-screen, formulario login |
| V1 | `v1-dashboard.css` | Grid cards, hover effects |
| V2 | - | Usa solo CSS base (sin específicos) |
| V3 | `v3-tramitacion.css` (futuro) | Sidebar, detalle, workflow |

### Colores Corporativos

**Verde Junta de Andalucía:**
- `--primary: #087021` - Identidad corporativa
- `--primary-hover: #0b4c1a` - Estados hover
- `--primary-light: #c4ddca` - Fondos sutiles
- `--primary-lighter: #f7fbf8` - Fondos muy claros

Ver documentación completa en: [CSS_v2_GUIA_USO.md](CSS_v2_GUIA_USO.md)

---

## 📦 Arquitectura de Layout

### Jerarquía de Niveles

```
A: app-container (grid principal)
├── B.1: app-header (sticky top)
├── B.2: app-main (scrollable)
│   ├── C.1: lista-cabecera (sin scroll) [solo V2/V3]
│   ├── C.2: lista-scroll-container (scroll propio) [solo V2/V3]
│   └── O contenido directo [V0/V1]
└── B.3: app-footer (sticky bottom)
```

### Comparativa por Vista

| Vista | Estructura | Scroll | Uso |
|-------|-----------|--------|-----|
| **V0** | A/B.1/B.2/B.3 | B.2 simple | Login sin scroll interno |
| **V1** | A/B.1/B.2/B.3 | B.2 simple | Dashboard grid cards |
| **V2** | A/B.1/B.2/C.1/C.2/D/B.3 | C.2 independiente | Tabla larga scroll infinito |
| **V3** | A/B.1/B.2/C.side/C.detail/B.3 | Ambos C independientes | Sidebar + detalle |

---

## 🔗 Templates Reutilizables

### Layout Base

| Template | Uso | Vistas |
|----------|-----|--------|
| `layout/base_fullwidth.html` | Layout completo con breadcrumb/usuario | V1, V2, V3 |
| `layout/base_login.html` | Layout sin breadcrumb/usuario | V0 |

### Componentes

| Componente | Template | Uso |
|-----------|----------|-----|
| Header | `layout/header.html` | Logo, breadcrumb, usuario, logout |
| Footer | `layout/footer.html` | Copyright, enlaces institucionales |

---

## 📝 Documentación Relacionada

### Por Vista
- 📝 [VISTA_V0_LOGIN.md](VISTA_V0_LOGIN.md) - Vista V0 Login
- 📝 [VISTA_V1_DASHBOARD.md](VISTA_V1_DASHBOARD.md) - Vista V1 Dashboard
- 📝 [ISSUE_94_ESTRUCTURA.md](ISSUE_94_ESTRUCTURA.md) - Vista V2 Listado

### CSS y Patrones
- 📝 [CSS_v2_GUIA_USO.md](CSS_v2_GUIA_USO.md) - Guía completa CSS v2
- 📝 [SCROLL_INFINITO.md](SCROLL_INFINITO.md) - Estrategias scroll infinito
- 📝 [UI_PATTERNS_DATA_TABLE.md](UI_PATTERNS_DATA_TABLE.md) - Patrones tablas
- 📝 [arquitectura/PATRONES_UI.md](arquitectura/PATRONES_UI.md) - Patrones UI generales
- 🎨 [guia_colores_junta_andalucia.html](guia_colores_junta_andalucia.html) - Colores corporativos

### Issues y PRs
- 🎯 [Epic #93](https://github.com/genete/bddat/issues/93) - Sistema de Navegación UI Modular
- 🐛 [Issue #94](https://github.com/genete/bddat/issues/94) - Prototipo Vista Listado V2
- 🐛 [Issue #58](https://github.com/genete/bddat/issues/58) - Colores Junta de Andalucía
- ✅ [PR #97](https://github.com/genete/bddat/pull/97) - Vista V2 Mergeado
- ✅ [PR #98](https://github.com/genete/bddat/pull/98) - Vista V1 Mergeado

---

## ✅ Checklist Implementación

### Vista V0 (Login)
- [x] CSS específico v0-login.css
- [x] Template base_login.html
- [x] Template login_v0.html
- [x] Ruta auth.py modificada
- [x] Documentación VISTA_V0_LOGIN.md
- [x] Testing funcional
- [ ] PR mergeado

### Vista V1 (Dashboard)
- [x] CSS específico v1-dashboard.css
- [x] Template index_v1.html
- [x] Grid responsive cards
- [x] Filtrado por roles
- [x] Documentación VISTA_V1_DASHBOARD.md
- [x] Testing funcional
- [x] PR #98 mergeado

### Vista V2 (Listado)
- [x] Templates completos
- [x] JavaScript scroll infinito + filtros
- [x] API paginación cursor
- [x] Estructura C.1/C.2/D
- [x] Botón scroll-to-top
- [x] Documentación completa
- [x] Testing funcional
- [x] PR #97 mergeado

### Vista V3 (Tramitación)
- [ ] Diseño sidebar acordeón
- [ ] Área detalle workflow
- [ ] Integración backend tramitación
- [ ] CSS específico
- [ ] Templates
- [ ] Documentación
- [ ] Testing

---

## 🚀 Próximos Pasos

1. ✅ ~~Vista V2 (Listado)~~ - COMPLETADA (PR #97)
2. ✅ ~~Vista V1 (Dashboard)~~ - COMPLETADA (PR #98)
3. ✅ ~~Vista V0 (Login)~~ - COMPLETADA (PR pendiente)
4. 🔴 Vista V3 (Tramitación) - Pendiente
5. 🔴 Migración resto de módulos a V2
6. 🔴 Fase 4: Metadata-driven (cards dinámicas desde JSON)

---

## 📊 Historial de Cambios

**08/02/2026:**
- ✅ Creado índice maestro VISTAS.md
- ✅ Vista V0 (Login) completada
- ✅ Vista V1 (Dashboard) completada
- ✅ Vista V2 (Listado) completada
- ✅ Documentación cruzada actualizada
- ✅ Sistema de nomenclatura V0/V1/V2/V3 establecido

---

**📌 Nota:** Este documento es el índice maestro. Para detalles técnicos de cada vista, consultar su documentación específica.
