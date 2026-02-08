# Vista V1 - Dashboard

## Información General

**Epic:** #93 - Sistema de Navegación UI Modular  
**Vista:** V1 - Dashboard (Panel de Control)  
**Fecha creación:** 08/02/2026  
**Estado:** ✅ Completada  
**Rama:** `feature/epic-93-vista-v1-dashboard`  

---

## Descripción

Dashboard principal del sistema BDDAT con grid de cards para acceso rápido a los diferentes módulos. Utiliza el layout fullwidth V2 (header + main + footer) con colores corporativos de la Junta de Andalucía.

---

## Características

### Layout
- **Base:** `layout/base_fullwidth.html` (reutiliza header/footer V2)
- **Sin sidebar:** 100% ancho disponible
- **Sin subniveles C.1/C.2:** Estructura simple sin scroll interno independiente
- **Responsive:** Grid adaptativo según tamaño de pantalla

### Componentes
- **Header sticky:** Logo, breadcrumb, usuario y logout (V2)
- **Footer sticky:** Copyright y enlaces (V2)
- **Page header:** Título "Panel de Control" + bienvenida con roles
- **Dashboard grid:** Grid responsive de cards clicables
- **Cards:** Acceso directo a módulos del sistema

### Colores
- **Verde corporativo Junta de Andalucía:** `#087021`
- **Variables CSS:** Reutiliza `v2-theme.css`
- **Hover effects:** Elevación + cambio de color en iconos

---

## Estructura de Archivos

### Archivos NUEVOS

```
app/
├── static/
│   └── css/
│       └── v1-dashboard.css          # Estilos específicos dashboard
└── templates/
    └── dashboard/
        └── index_v1.html             # Template dashboard V1
```

### Archivos MODIFICADOS

```
app/
└── routes/
    └── dashboard.py                  # Apunta a index_v1.html
```

### Archivos NO TOCADOS (convivencia)

```
app/
└── templates/
    └── dashboard/
        └── index.html                # Dashboard antiguo (intacto)
```

---

## Jerarquía de Niveles

### Estructura HTML

```
A: app-container (grid principal)
├── B.1: app-header (sticky top) ← Header fijo V2
├── B.2: app-main (scrollable) ← Área de trabajo
│   ├── page-header (título + bienvenida)
│   └── dashboard-grid (grid de cards)
└── B.3: app-footer (sticky bottom) ← Footer fijo V2
```

### Diferencia con V2 (listado expedientes)

**V1 (Dashboard):**
- Todo el contenido scrollea junto
- No hay subniveles C.1/C.2/D
- Más simple y natural para dashboard

**V2 (Listado):**
- Tiene C.1 (filtros fijos sin scroll)
- Tiene C.2 (scroll interno independiente para tabla)
- Necesario para tablas largas con filtros siempre visibles

---

## Cards del Dashboard

### Cards Activas (según rol)

| Card | Descripción | Ruta | Roles Permitidos |
|------|--------------|------|------------------|
| **Expedientes** | Listado con scroll infinito (V2) | `/expedientes/listado-v2` | TRAMITADOR, ADMINISTRATIVO, SUPERVISOR, ADMIN |
| **Usuarios** | Gestión de usuarios del sistema | `/usuarios` | SUPERVISOR, ADMIN |
| **Proyectos** | Instalaciones de alta tensión | `/proyectos` | TRAMITADOR, ADMINISTRATIVO, SUPERVISOR, ADMIN |
| **Mis Expedientes** | Expedientes asignados a mí | `/expedientes?mis_expedientes=1` | TRAMITADOR, ADMINISTRATIVO, SUPERVISOR, ADMIN |
| **Nuevo Expediente** | Crear expediente de tramitación | `/expedientes/nuevo` | TRAMITADOR, ADMINISTRATIVO, SUPERVISOR, ADMIN |
| **Mi Perfil** | Configuración personal | `/perfil` | TODOS |

### Cards Deshabilitadas ("Próximamente")

| Card | Descripción | Roles Permitidos |
|------|--------------|------------------|
| **Tareas** | Gestión de tareas | TRAMITADOR, ADMINISTRATIVO, SUPERVISOR, ADMIN |
| **Documentos** | Gestión documental | TRAMITADOR, ADMINISTRATIVO, SUPERVISOR, ADMIN |
| **Estadísticas** | Panel analítico | SUPERVISOR, ADMIN |
| **Configuración** | Tablas maestras y parámetros | SUPERVISOR, ADMIN |

---

## Grid Responsive

### Breakpoints

| Tamaño Pantalla | Columnas | Media Query |
|------------------|----------|-------------|
| Desktop XL (≥1400px) | 4 | `@media (min-width: 1400px)` |
| Desktop (992-1399px) | 3 | `@media (min-width: 992px) and (max-width: 1399px)` |
| Tablet (768-991px) | 2 | `@media (min-width: 768px) and (max-width: 991px)` |
| Mobile (<768px) | 1 | `@media (max-width: 767px)` |

### CSS del Grid

```css
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
  padding-top: 2rem;
  padding-bottom: 3rem;
}
```

---

## Estilos CSS (v1-dashboard.css)

### Variables Reutilizadas (v2-theme.css)

```css
--primary: #087021;           /* Verde corporativo Junta */
--primary-lighter: #f7fbf8;   /* Fondo iconos */
--bg-card: #ffffff;           /* Fondo cards */
--border-color: #dee2e6;      /* Bordes */
--border-radius-lg: 0.5rem;   /* Esquinas redondeadas */
--shadow-lg: 0 1rem 3rem rgba(0, 0, 0, 0.175); /* Sombra hover */
```

### Clases Principales

#### `.dashboard-card`
- Card individual clicable
- Padding: `2rem 1.5rem`
- Border radius: `var(--border-radius-lg)`
- Transition: `all 0.3s ease`

#### `.dashboard-card:hover`
- Transform: `translateY(-4px)` (elevación)
- Box-shadow: `var(--shadow-lg)`
- Border-color: `var(--primary)`

#### `.card-icon`
- Tamaño: `80px x 80px`
- Border-radius: `50%` (circular)
- Background: `var(--primary-lighter)`
- Font-size: `2.5rem`

#### `.card-icon:hover`
- Background: `var(--primary)` (verde corporativo)
- Color: `var(--text-inverse)` (blanco)
- Transform: `scale(1.05)`

#### `.dashboard-card.disabled`
- Opacity: `0.5`
- Cursor: `not-allowed`
- Pointer-events: `none`

---

## Lógica de Permisos

### Implementación Actual (Template)

```jinja
{% set user_roles = current_user.roles | map(attribute='nombre') | list %}
{% if 'TRAMITADOR' in user_roles or 'ADMIN' in user_roles %}
<a href="{{ url_for('expedientes.listado_v2') }}" class="dashboard-card">
    <!-- Card visible solo para roles permitidos -->
</a>
{% endif %}
```

### Backend Simplificado

```python
# app/routes/dashboard.py
@bp.route('/')
@login_required
def index():
    # Permisos gestionados en template (Fase 1)
    return render_template('dashboard/index_v1.html')
```

### Fase 4 (Futuro - Metadata-Driven)

**Configuración JSON:**
```json
{
  "cards": [
    {
      "id": "expedientes",
      "nombre": "Expedientes",
      "descripcion": "Listado con scroll infinito",
      "icono": "fa-folder-open",
      "url": "expedientes.listado_v2",
      "orden": 1,
      "roles": ["TRAMITADOR", "ADMIN"],
      "activo": true
    }
  ]
}
```

**Backend cargará JSON y filtrará por roles:**
```python
import json

@bp.route('/')
def index():
    with open('app/config/dashboard_cards.json') as f:
        config = json.load(f)
    
    user_roles = [r.nombre for r in current_user.roles]
    cards_visibles = [
        c for c in config['cards'] 
        if c['activo'] and any(rol in user_roles for rol in c['roles'])
    ]
    
    return render_template('dashboard/index_v1.html', cards=cards_visibles)
```

---

## Testing

### Casos de Prueba

#### 1. Testing Visual
- ✅ Dashboard carga correctamente
- ✅ Header y footer V2 visibles
- ✅ Grid responsive funciona
- ✅ Hover effects en cards
- ✅ Iconos circulares correctos
- ✅ Padding horizontal correcto (no pegado a bordes)

#### 2. Testing Funcional
- ✅ Click en "Expedientes" → `/expedientes/listado-v2`
- ✅ Click en "Usuarios" → `/usuarios`
- ✅ Click en "Proyectos" → `/proyectos`
- ✅ Click en "Mis Expedientes" → `/expedientes?mis_expedientes=1`
- ✅ Click en "Nuevo Expediente" → `/expedientes/nuevo`
- ✅ Click en "Mi Perfil" → `/perfil`
- ✅ Cards deshabilitadas no son clicables

#### 3. Testing Permisos por Rol

**Usuario ADMIN:**
- ✅ Ve TODAS las cards activas
- ✅ Ve todas las cards deshabilitadas

**Usuario TRAMITADOR:**
- ✅ Ve: Expedientes, Proyectos, Mis Expedientes, Nuevo Expediente, Mi Perfil
- ✅ Ve: Tareas, Documentos (deshabilitadas)
- ❌ NO ve: Usuarios, Estadísticas, Configuración

**Usuario SUPERVISOR:**
- ✅ Ve TODAS las cards (igual que ADMIN)

#### 4. Testing Responsive
- ✅ Desktop XL (1400px+): 4 columnas
- ✅ Desktop (992-1399px): 3 columnas
- ✅ Tablet (768-991px): 2 columnas
- ✅ Mobile (<768px): 1 columna

---

## Accesibilidad

### Focus Visible
```css
.dashboard-card:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
  box-shadow: 0 0 0 0.25rem var(--focus-ring);
}
```

### Semántica HTML
- `<a>` para cards clicables (navegación)
- `<div>` para cards deshabilitadas (no navegación)
- `<h1>` para título principal
- `<h2>` para títulos de cards

### Atributos ARIA
- Cards deshabilitadas: `pointer-events: none` (no interactivas)
- Iconos decorativos (no necesitan `aria-label`)

---

## Convivencia con Sistema Antiguo

### Estrategia No Destructiva

**Archivos nuevos:**
- `v1-dashboard.css` (no toca `custom.css`)
- `index_v1.html` (no toca `index.html`)

**Dashboard antiguo intacto:**
- `app/templates/dashboard/index.html` permanece sin cambios
- Si se revierte `dashboard.py`, vuelve a funcionar el antiguo

**Migración progresiva:**
- V1 activa por defecto en `dashboard.py`
- V2 activa en ruta específica `/expedientes/listado-v2`
- Resto de módulos mantienen templates antiguos hasta migración

---

## Commits Realizados

### Rama: `feature/epic-93-vista-v1-dashboard`

1. **[STYLE]** Crear CSS para Vista V1 Dashboard con grid de cards
2. **[TEMPLATE]** Crear dashboard V1 con layout fullwidth y grid de cards
3. **[RUTA]** Actualizar dashboard para usar template index_v1.html (Vista V1)
4. **[FIX]** Corregir sintaxis Jinja2 en validación de roles del dashboard
5. **[FIX]** Corregir padding horizontal en page-header y dashboard-grid
6. **[DOCS]** Documentar Vista V1 (Dashboard) - estructura, estilos y funcionalidad

---

## Próximos Pasos

### Fase Actual (Completada)
- ✅ Vista V1 (Dashboard) implementada y funcional
- ✅ Testing completo con diferentes roles
- ✅ Documentación creada
- ✅ Listo para PR a `develop`

### Siguientes Vistas (Epic #93)
- **Vista V2:** Listado expedientes con scroll infinito ✅ COMPLETADA (PR #97)
- **Vista V3:** Tramitación con sidebar acordeón (pendiente)
- **Vista V4+:** Otras vistas modulares según necesidad

### Fase 4 (Futuro)
- Cards configurables desde JSON
- Iconos dinámicos desde metadata
- Orden configurable
- Activar/desactivar cards sin tocar código
- Roles dinámicos desde configuración

---

## Referencias

- **Epic #93:** Sistema de Navegación UI Modular
- **Issue #94:** Prototipo Vista Listado V2 (base de diseño)
- **Issue #58:** Colores Junta de Andalucía
- **PATRONES_UI.md:** Especificación patrones UI
- **CSS_v2_GUIA_USO.md:** Guía CSS V2
- **ISSUE_94_ESTRUCTURA.md:** Estructura V2 (referencia)

---

## Historial de Cambios

**08/02/2026 - Vista V1 Completada:**
- Implementado dashboard con layout fullwidth V2
- Grid responsive de cards (4/3/2/1 columnas)
- CSS específico v1-dashboard.css
- Filtrado por roles funcional
- Testing completo con diferentes roles
- Documentación completa creada
- Listo para PR a develop
