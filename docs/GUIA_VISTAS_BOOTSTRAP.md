# Guía de Vistas Bootstrap - BDDAT

**Versión:** 2.2
**Fecha:** 25 de marzo de 2026
**Para:** Claude Code - Referencia de diseño UI

---

## 📖 Vocabulario

| Término | Significado |
|---------|-------------|
| **V0, V1, V2, V4** | Tipos de vista definidos en esta guía |
| **V3-BC** | Vista de tramitación por breadcrumbs (evolución de V3; no usa acordeón ni tabs) |
| **C.1** | Zona fija superior sin scroll (`lista-cabecera`) |
| **C.2** | Zona scrollable independiente (`lista-scroll-container`) |
| **Listado embebido** | Tabla dentro de una card V4 (ej: documentos en detalle de expediente, direcciones en detalle de entidad) |
| **Tabla V2** | Tabla `expedientes-table` dentro de `card.tabla-bloque`, thead verde claro sticky, scroll infinito JS |
| **Tabla BC** | Tabla `_tabla_hijos.html` dentro de `card.tabla-bloque`, thead verde claro (unificado con V2), sin sticky |
| **Tabla Pool** | Tabla `#pool-tabla`, `table-layout: fixed`, thead sticky gris con `box-shadow inset` |
| **`.tabla-bloque`** | Card contenedor de tabla (V2 y BC): bordes redondeados, sombra. Con `card-header` → `overflow:hidden` (esquinas limpias); con `expedientes-table` directa → bg verde claro (esquinas seamless + sticky intacto) |

---

## 🎨 Sistema de Colores Corporativos

### Junta de Andalucía
- **Primary:** `#087021` - Verde corporativo (navbar, botones, identidad)
- **Primary Hover:** `#0b4c1a`
- **Primary Light:** `#c4ddca` - Fondos sutiles
- **Primary Lighter:** `#f7fbf8` - Fondos muy claros

### Variables CSS (v2-theme.css)
```css
--primary: #087021;
--primary-hover: #0b4c1a;
--primary-light: #c4ddca;
--primary-lighter: #f7fbf8;
```

### ⚠️ Regla Crítica
**NO usar `.bg-success` (#198754) para identidad corporativa.** Solo para mensajes de éxito semánticos.

---

## 🏗️ Arquitectura de Layout

### Jerarquía de Niveles

```
A: app-container (grid header/main/footer)
├── B.1: app-header (sticky top)
├── B.2: app-main (scrollable o flexbox según vista)
│   ├── C.1: lista-cabecera (opcional, sin scroll)
│   ├── C.2: lista-scroll-container (opcional, scroll propio)
│   └── O contenido directo
└── B.3: app-footer (sticky bottom)
```

### Comparativa por Vista

| Vista | Estructura | B.2 Scroll | Uso C.1/C.2 |
|-------|-----------|------------|-------------|
| **V0** (Login) | A/B.1/B.2/B.3 | Simple | NO |
| **V1** (Dashboard) | A/B.1/B.2/B.3 | Simple | NO |
| **V2** (Listado) | A/B.1/B.2/C.1/C.2/D/B.3 | C.2 independiente | SÍ |
| **V3-BC** (Tramitación) | A/B.1/B.2/C.1/C.2/B.3 | C.2 independiente | SÍ |
| **V4** (Detalle/Edición) | A/B.1/B.2/C.1/B.3 | Simple (B.2 entera) | C.1 solo header |
| **Pool** (variante V3-BC) | A/B.1/B.2/C.1/C.2/B.3 | C.2 independiente | SÍ |

---

## 📋 Vista V0 - Login

### Decisiones de Diseño
- **Split-screen:** 60% info / 40% formulario
- **Header simplificado:** Solo logo (sin breadcrumb, sin usuario)
- **Gradiente fondo:** `linear-gradient(135deg, var(--primary-lighter), #ffffff)`

### Estructura Clave
```html
<main class="app-main">
  <div class="login-container"> <!-- grid 60/40 -->
    <div class="login-info">Bienvenida + ayuda</div>
    <div class="login-form-zone">Formulario centrado</div>
  </div>
</main>
```

### Responsive
- **Desktop:** Split-screen 60/40
- **Mobile (<991px):** Columnas apiladas (info arriba, form abajo)

---

## 🏠 Vista V1 - Dashboard

### Decisiones de Diseño
- **Grid responsive de cards:** 4/3/2/1 columnas según breakpoint
- **Cards clicables:** Hover con `translateY(-4px)` + sombra
- **Iconos circulares:** 80px, background `var(--primary-lighter)`, hover → `var(--primary)`
- **Filtrado por roles:** Lógica en template Jinja2

### Breakpoints Grid
| Tamaño | Columnas | Media Query |
|--------|----------|-------------|
| Desktop XL (≥1400px) | 4 | `@media (min-width: 1400px)` |
| Desktop (992-1399px) | 3 | `@media (min-width: 992px)` |
| Tablet (768-991px) | 2 | `@media (min-width: 768px)` |
| Mobile (<768px) | 1 | Default |

### CSS Cards
```css
.dashboard-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--primary);
}

.card-icon:hover {
  background: var(--primary);
  color: var(--text-inverse);
  transform: scale(1.05);
}
```

---

## 📊 Vista V2 - Listado (Scroll Infinito)

### Decisiones de Diseño Clave

#### ¿Cuándo usar C.1/C.2?
- ✅ **Usar cuando:** Lista larga (>100 items), scroll infinito, filtros siempre visibles
- ❌ **NO usar cuando:** Lista corta (<50 items), formularios simples

#### Estructura C.1/C.2/D
```html
<main class="app-main"> <!-- flexbox, overflow: hidden -->
  <div class="lista-cabecera"> <!-- C.1: flex-shrink: 0 -->
    <div class="page-header content-constrained">Título + botón</div>
    <div class="filters-row content-constrained">Filtros + paginación</div>
  </div>

  <div class="lista-scroll-container"> <!-- C.2: flex: 1, overflow-y: auto -->
    <div class="content-constrained py-3">
      <div class="card tabla-bloque"> <!-- bordes redondeados + sombra; bg verde → esquinas seamless -->
        <table class="expedientes-table"> <!-- thead sticky top: 0 -->
          <thead>...</thead>
          <tbody><!-- filas JS ScrollInfinito --></tbody>
        </table>
      </div>
    </div>
    <button id="tabla-scroll-to-top">↑</button> <!-- sticky bottom: 1rem, FUERA del card -->
  </div>
</main>
```

#### CSS Crítico
```css
.app-main {
  display: flex;
  flex-direction: column;
  overflow: hidden; /* CRÍTICO: aislamos scroll */
}

.lista-cabecera {
  flex-shrink: 0; /* No se comprime */
}

.lista-scroll-container {
  flex: 1;
  overflow-y: auto;
  position: relative;
  min-height: 220px; /* Mantiene visibilidad */
}

.lista-scroll-container .expedientes-table thead th {
  position: sticky;
  top: 0; /* Pegado a C.2, no al viewport */
  z-index: 10;
}
```

### Botón Scroll-to-Top

**Decisión:** Solo en C.2 (scroll interno tabla), no en scroll de página.

```css
#tabla-scroll-to-top {
  position: sticky;
  bottom: 1rem;
  left: calc(100% - 3.75rem);
  margin-top: -3.75rem; /* No ocupa espacio */
  pointer-events: none; /* Desactiva mientras invisible */
  opacity: 0;
}

#tabla-scroll-to-top.visible {
  opacity: 1;
  pointer-events: auto;
}
```

**JavaScript:**
```javascript
// Escucha scroll en C.2, NO en window
const container = document.querySelector('.lista-scroll-container');
container.addEventListener('scroll', toggleButton);
```

### Scroll Infinito - API

**Opción C (Cursor Backend)** - Recomendada hasta 10-20K registros

```python
@app.route('/api/expedientes')
def get_expedientes():
    cursor = request.args.get('cursor', 0, type=int)
    limit = request.args.get('limit', 50, type=int)
    
    query = Expediente.query\
        .filter(Expediente.id > cursor)\
        .order_by(Expediente.id)\
        .limit(limit)
    
    return jsonify({
        'data': [e.to_dict() for e in query.all()],
        'next_cursor': expedientes[-1].id if expedientes else None,
        'has_more': len(expedientes) == limit
    })
```

---

## 🛠️ Vista V3-BC - Tramitación (Breadcrumbs)

### Evolución histórica
| Fecha | Cambio |
|-------|--------|
| 12/02/2026 | Sidebar → Acordeón Bootstrap 5 |
| 28/02/2026 | Acordeón → Tabs 4 niveles (#150) |
| 04/03/2026 | Tabs → **Breadcrumbs** (#157) — arquitectura actual |

> **Legacy:** La versión anterior (acordeón/tabs) sigue en el repositorio pero **no se usa**.
> Archivos legacy: `app/templates/vistas/vista3/` (partials acordeón/tabs),
> `app/modules/expedientes/templates/expedientes/tramitacion_v3.html`,
> `app/routes/vista3.py`, `app/static/js/v3-tabs-main.js`,
> `app/static/js/acordeon_lazy.js`, `app/templates/layout/base_acordeon.html`.
> No crear vistas nuevas con ese patrón.

### Concepto

Navegación drill-down por la jerarquía ESFTT (Expediente → Solicitud → Fase → Trámite → Tarea).
Cada nivel es una **página independiente** con:
- **C.1** — Card del nodo actual (datos de la entidad, metadatos, botones de acción)
- **C.2** — Tabla de hijos del nodo (`_tabla_hijos.html`) o contenido específico (tarea → documentos)

El breadcrumb del header permite volver a cualquier nivel superior.

### Estructura tipo (cada nivel)

```html
<main class="app-main" style="overflow-y: hidden;">
  <!-- C.1: card del nodo actual -->
  <div class="lista-cabecera">
    <div class="bc-view">
      <div class="card bc-card-nodo">
        <div class="card-header card-header-accent">Título nodo</div>
        <div class="card-body card-body-tinted">
          <div class="bc-meta">Metadatos: estado, fechas...</div>
          <div class="bc-acciones-bar">Botones acción</div>
        </div>
      </div>
    </div>
  </div>

  <!-- C.2: tabla de hijos -->
  <div class="lista-scroll-container">
    <div class="content-constrained py-3">
      <div class="card tabla-bloque"> <!-- overflow:hidden vía :has(>.card-header) → esquinas limpias -->
        <div class="card-header card-header-accent d-flex justify-content-between align-items-center py-2">
          <span class="fw-semibold">
            <i class="fas fa-..."></i> [Título hijos]
            <span class="badge bg-primary ms-2">{{ hijos|length }}</span>
          </span>
          <button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#modal-nuevo-...">
            <i class="fas fa-plus me-1"></i> Nuevo [hijo]
          </button>
        </div>
        {% include 'vistas/vista3_bc/_tabla_hijos.html' %}
      </div>
    </div>
  </div>
</main>
```

**Regla crítica de scroll:** `overflow-y: hidden` en `.app-main` es obligatorio para que C.2
absorba el scroll de forma independiente (misma mecánica que V2).

### Partial `_tabla_hijos.html`

Genera la tabla de hijos con columnas dinámicas desde Python:

```html
<!-- Variables de contexto: hijos (lista de dicts), columnas (lista de {key, label}) -->
<!-- Clase tabla-hijos: permite responsive mobile (oculta columnas medias en ≤767px) -->
<table class="table table-hover table-sm align-middle mb-0 tabla-hijos">
  <thead>
    <!-- Sin table-light: el CSS de v3-breadcrumbs.css sobreescribe el bg a verde claro -->
    <tr>
      <th style="width:2rem"></th>         <!-- indicador estado — siempre visible -->
      {% for col in columnas %}
      <th>{{ col.label }}</th>             <!-- ocultas en mobile vía .tabla-hijos media query -->
      {% endfor %}
      <th style="width:3rem"></th>         <!-- botón → — siempre visible -->
    </tr>
  </thead>
  <tbody>
    {% for hijo in hijos %}
    <tr>
      <td>{{ indicador_estado(hijo.estado) }}</td>
      {% for col in columnas %}
      <td>{{ hijo[col.key] }}</td>
      {% endfor %}
      <td><a href="{{ hijo.url_detalle }}" class="btn btn-sm btn-outline-secondary">→</a></td>
    </tr>
    {% endfor %}
  </tbody>
</table>
```

Indicadores de estado: `bi-check-circle-fill` (finalizada), `bi-clock-fill` (en curso), `bi-circle` (planificada).

### Clases CSS específicas (`v3-breadcrumbs.css` y `v2-components.css`)

| Clase | Archivo | Uso |
|-------|---------|-----|
| `.bc-card-nodo` | v3-breadcrumbs | Card del nodo actual — sombra discreta |
| `.bc-meta` | v3-breadcrumbs | Texto de metadatos (0.85rem, color secundario) |
| `.bc-view` | v3-breadcrumbs | Contenedor centrado `max-width: 1200px` |
| `.bc-acciones-bar` | v3-breadcrumbs | Flex row de botones de acción |
| `.tabla-bloque` | v2-components | Card contenedor de tabla (V2 y BC): `border-radius`, `box-shadow`. Ver vocabulario para comportamiento por variante. |
| `.tabla-hijos` | v3-breadcrumbs | Clase en `<table>` de `_tabla_hijos.html`; activa responsive mobile (oculta columnas medias en ≤767px) |

### Archivos clave

| Archivo | Propósito |
|---------|-----------|
| `app/static/css/v3-breadcrumbs.css` | Estilos V3-BC |
| `app/templates/vistas/vista3_bc/_tabla_hijos.html` | Partial tabla de hijos (columnas dinámicas) |
| `app/modules/expedientes/templates/expedientes/tramitacion_bc.html` | Nivel expediente |
| `app/modules/expedientes/templates/expedientes/tramitacion_bc_solicitud.html` | Nivel solicitud |
| `app/modules/expedientes/templates/expedientes/tramitacion_bc_fase.html` | Nivel fase |
| `app/modules/expedientes/templates/expedientes/tramitacion_bc_tramite.html` | Nivel trámite |
| `app/modules/expedientes/templates/expedientes/tramitacion_bc_tarea.html` | Nivel tarea |

### Endpoints backend

| Operación | URL |
|-----------|-----|
| Crear solicitud | POST `/api/vista3/expediente/<id>/solicitudes/nueva` |
| Crear fase | POST `/api/vista3/solicitud/<id>/fases/nueva` |
| Crear trámite | POST `/api/vista3/fase/<id>/tramites/nuevo` |
| Crear tarea | POST `/api/vista3/tramite/<id>/tareas/nueva` |
| Editar solicitud | POST `/api/vista3/solicitud/<id>/editar` |
| Editar fase | POST `/api/vista3/fase/<id>/editar` |
| Editar trámite | POST `/api/vista3/tramite/<id>/editar` |
| Editar tarea | POST `/api/vista3/tarea/<id>/editar` |
| Borrar solicitud | POST `/api/vista3/solicitud/<id>/borrar` |
| Borrar fase | POST `/api/vista3/fase/<id>/borrar` |
| Borrar trámite | POST `/api/vista3/tramite/<id>/borrar` |
| Borrar tarea | POST `/api/vista3/tarea/<id>/borrar` |

### Filtros Jinja2 registrados (app/__init__.py)
`icono_solicitud`, `color_solicitud`, `icono_fase`, `color_fase`,
`icono_tramite`, `color_tramite`, `icono_tarea`, `color_tarea`

### Modelo de Datos Crítico

**Relación Expediente ↔ Proyecto:**
```
EXPEDIENTES ←──────────────→ PROYECTOS (1:1)
  ├─ proyecto_id (FK)         ├─ expediente_id (FK)

SOLICITUDES
  ├─ expediente_id (FK → EXPEDIENTES)
  └─ NO tiene proyecto_id ❌
```

**Acceso correcto:**
```python
# ✅ CORRECTO
proyecto = solicitud.expediente.proyecto

# ❌ INCORRECTO
proyecto = solicitud.proyecto  # NO existe esta relación
```

---

## 📄 Vista V4 - Detalle/Edición Unificada

**Referencia:** `detalle.html` de expedientes (issue #49)
**Tipo de vista:** Registro único con alternancia lectura ↔ edición

### Concepto: Template único con parámetro `modo`

Un solo template sirve para ver y editar. El parámetro `modo` controla qué se renderiza:
- `modo='ver'` → campos bloqueados, botones Volver/Tramitar/Editar
- `modo='editar'` → campos editables, botones Cancelar/Guardar

**Regla fundamental: CERO salto de layout entre modos.**
Los mismos elementos HTML en las mismas posiciones. Solo cambia el atributo `readonly`/`disabled` y aparecen controles auxiliares en edición (ej: selector de municipios).

### Estructura real de un template V4

```html
{% from 'macros/page_header.html' import page_header %}

{% block content %}
{% if modo == 'editar' %}
<form id="form_objeto" class="form-detail" action="{{ url_for(...) }}" method="POST">
{% endif %}

<!-- C.1: Encabezado homogéneo (lista-cabecera sin scroll) -->
<div class="lista-cabecera">
  {% call page_header('Título', 'fas fa-icon', title_accent=objeto.codigo) %}
    {% if modo == 'ver' %}
      <a href="{{ url_for('...listado') }}" class="btn btn-outline-primary">Volver</a>
      <a href="{{ url_for('...editar', id=objeto.id) }}" class="btn btn-primary">Editar</a>
    {% else %}
      <a href="{{ url_for('...detalle', id=objeto.id) }}" class="btn btn-outline-primary">Cancelar</a>
      <button type="submit" class="btn btn-primary">Guardar cambios</button>
    {% endif %}
  {% endcall %}
</div>

<!-- Contenido: fichas de campos, scroll del body entero -->
<div class="v4-content content-constrained py-3">
  <!-- Fichas aquí -->
</div>

{% if modo == 'editar' %}</form>{% endif %}
{% endblock %}
```

**`lista-cabecera` en V4:** se usa solo para el header de página (macro `page_header`), no hay C.2 — el scroll es del `<body>` entero. La mecánica C.1/C.2 con scroll independiente es exclusiva de V2, V3-BC y Pool.

**Macro `page_header`** — genera el bloque título + botones de forma homogénea entre todas las vistas:
```jinja2
{% call page_header('Expediente', 'fas fa-folder-open', title_accent='AT-' ~ expediente.numero_at) %}
  ... botones ...
{% endcall %}
```
El parámetro `title_accent` añade la parte variable del título en color primario (ej: número AT).

### Estructura de Fichas

```html
<!-- Ficha tipo V4: cabecera verde secundario + cuerpo gris -->
<div class="card shadow-sm mb-3">
    <div class="card-header card-header-accent">
        <h6 class="mb-0 fw-semibold">
            <i class="fas fa-icon me-2"></i>Título Ficha
        </h6>
    </div>
    <div class="card-body card-body-tinted py-3">
        <!-- Campos del formulario -->
    </div>
</div>
```

### Clases CSS Globales (en `v2-components.css`)

| Clase | Uso |
|-------|-----|
| `.v4-content` | Wrapper del cuerpo de fichas (usar siempre con `content-constrained`) |
| `.card-header-accent` | Cabecera de ficha en `#c4ddca` (verde apoyo corporativo) |
| `.card-body-tinted` | Fondo `#f5f5f5` en cuerpo de ficha para destacar campos blancos |
| `.form-control[readonly]` | Override global: campos readonly con fondo blanco (igual que editable) |
| `.form-detail .form-control:focus` | Focus ring verde corporativo en formularios de edición |

### Patrón de Campos

#### Campos de texto (mismo elemento en ambos modos)
```html
<input type="text" class="form-control" id="titulo" name="titulo"
       value="{{ objeto.campo or '' }}"
       {% if modo == 'ver' %}readonly{% endif %}>
```

#### Selects (select en editar, input readonly en ver — mismo alto visual)
```html
{% if modo == 'ver' %}
<input type="text" class="form-control" readonly
       value="{{ objeto.relacion.nombre if objeto.relacion else '' }}"
       placeholder="Sin valor">
{% else %}
<select class="form-select" id="campo_id" name="campo_id">
    <option value="">-- Sin valor --</option>
    {% for item in items %}
        <option value="{{ item.id }}" {% if objeto.campo_id == item.id %}selected{% endif %}>
            {{ item.nombre }}
        </option>
    {% endfor %}
</select>
{% endif %}
```

#### Campos bloqueados → tooltip, NO texto subtítulo
```html
<!-- ✅ BIEN: tooltip en hover -->
<input type="text" class="form-control" value="AT-{{ num }}" disabled
       data-bs-toggle="tooltip" title="No modificable">

<!-- ❌ MAL: texto subtítulo visible siempre -->
<input type="text" class="form-control" value="AT-{{ num }}" disabled>
<small class="text-muted">No modificable</small>
```

### Formulario de Edición

El `<form>` envuelve **todo** el contenido del bloque, incluyendo `lista-cabecera`, para que el botón "Guardar cambios" (dentro del header) sea un `<button type="submit">` del mismo form. La clase `form-detail` activa el focus ring verde corporativo.

```html
{% if modo == 'editar' %}
<form id="form_objeto" class="form-detail" action="..." method="POST">
{% endif %}

<div class="lista-cabecera">...</div>  {# header con botones Guardar/Cancelar #}
<div class="v4-content content-constrained py-3">...</div>

{% if modo == 'editar' %}</form>{% endif %}
```

Los **botones de acción** van dentro de la macro `page_header` (ver "Estructura real" arriba). Usar `btn-outline-primary` para acciones secundarias (Volver, Cancelar) y `btn-primary` para la acción principal (Editar, Guardar).

### Tooltips — Inicialización

```html
{% block extra_js %}
{{ super() }}
<script>
    document.addEventListener('DOMContentLoaded', () => {
        // Siempre inicializar tooltips (presentes en ambos modos)
        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
            new bootstrap.Tooltip(el);
        });
    });
</script>
{% if modo == 'editar' %}
<!-- Scripts específicos de edición aquí -->
{% endif %}
{% endblock %}
```

### Ruta Flask

```python
@bp.route('/<int:id>')
@login_required
def detalle(id):
    objeto = Modelo.query.get_or_404(id)
    return render_template('modulo/detalle.html', objeto=objeto, modo='ver')

@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    objeto = Modelo.query.get_or_404(id)
    if request.method == 'POST':
        # ... guardar cambios ...
        return redirect(url_for('blueprint.detalle', id=id))
    # GET: mismo template con datos de formulario
    return render_template('modulo/detalle.html',
                           objeto=objeto,
                           modo='editar',
                           lista_opciones=...,)
```

---

## 📋 Listados Embebidos (tablas dentro de V4)

Tablas cortas dentro de cards V4, para datos secundarios del registro principal.
Ejemplos: documentos en detalle de expediente, direcciones y autorizaciones en detalle de entidad.

### Convenciones

- Card con `card-header-accent` (verde secundario) + `card-body` sin `card-body-tinted`
- Tabla: `table table-sm table-hover table-embedded`, thead `table-light`
- Sin scroll infinito, sin C.1/C.2, sin botón scroll-to-top
- Paginación: no necesaria (listados cortos, <50 registros típicamente)
- Acciones por fila: botones `btn-sm btn-outline-*`

### Ejemplo

```html
<div class="card shadow-sm mb-3">
  <div class="card-header card-header-accent">
    <h5 class="mb-0 fw-semibold">
      <i class="fas fa-list me-2"></i>Direcciones
    </h5>
  </div>
  <div class="card-body p-0">
    <table class="table table-sm table-hover table-embedded">
      <thead class="table-light">
        <tr><th>Tipo</th><th>Dirección</th><th>Acciones</th></tr>
      </thead>
      <tbody>...</tbody>
    </table>
  </div>
</div>
```

### Diferencias con tabla V2

| Aspecto | V2 | Listado embebido |
|---------|----|--------------------|
| Contenedor | C.2 (`lista-scroll-container`) | Card body V4 |
| Thead | Verde corporativo, sticky, uppercase | `table-light`, no sticky |
| Scroll | Infinito (JS) | Página completa |
| Clase tabla | `expedientes-table` | `table table-sm table-hover table-embedded` |

---

## 📦 Vista Pool (variante V3-BC)

El pool de documentos del expediente sigue la estructura V3-BC (C.1 + C.2) pero con
particularidades propias.

### Estructura

- **C.1** — Card del expediente (metadatos) + fichas de entrada (subida/enlace)
- **C.2** — Tabla pool (`#pool-tabla`)

### Particularidades de la tabla Pool

| Aspecto | Pool | V2 / BC |
|---------|------|---------|
| Layout | `table-layout: fixed` | Auto |
| Thead | Sticky, gris claro, `box-shadow inset` inferior | Corporativo (V2) o `table-light` (BC) |
| Responsive | 5 breakpoints con columnas ocultas | Media queries simples (V2) o ninguno (BC) |
| Selección | Checkbox por fila | No |
| Scroll | C.2 independiente | Igual |

### Archivo clave
- `app/modules/expedientes/templates/expedientes/pool_documentos.html`

---

## 🎨 Patrones CSS Reutilizables

### `.content-constrained` - Márgenes Laterales
**Usar cuando:** Contenido normal (page-header, filtros, formularios)  
**NO usar cuando:** Tablas full-width

```css
.content-constrained {
  padding-left: 2rem;
  padding-right: 2rem;
}
```

### Badges de Estado
```html
<span class="badge badge-info">En trámite</span>
<span class="badge badge-success">Resuelto</span>
<span class="badge badge-warning">Incompleto</span>
<span class="badge badge-danger">Vencido</span>
```

### Botones con Iconos
```html
<button class="btn btn-primary">
  <i class="fas fa-plus"></i> Nuevo
</button>

<button class="btn btn-sm btn-outline-primary">
  <i class="fas fa-eye"></i> Ver
</button>
```

### Gradiente Corporativo
```css
.bg-primary.bg-gradient {
  background-image: linear-gradient(180deg, 
    rgba(255, 255, 255, 0.15), 
    rgba(255, 255, 255, 0)
  );
}
```

---

## 📱 Responsive - Breakpoints

| Tamaño | Ancho | Comportamiento |
|--------|-------|----------------|
| Desktop XL | ≥1400px | Layout completo |
| Desktop | 992-1399px | Grid 3 columnas, ocultar columnas secundarias |
| Tablet | 768-991px | Grid 2 columnas, ocultar más columnas |
| Mobile | <768px | Grid 1 columna, solo columnas esenciales |

### Ejemplo Ocultar Columnas en Tabla
```css
/* Tablet: Ocultar "Solicitudes" */
@media (max-width: 991px) {
  .expedientes-table th:nth-child(3),
  .expedientes-table td:nth-child(3) {
    display: none;
  }
}

/* Mobile: Solo Expediente + Titular + Acciones */
@media (max-width: 767px) {
  .expedientes-table th:nth-child(4),
  .expedientes-table td:nth-child(4),
  .expedientes-table th:nth-child(5),
  .expedientes-table td:nth-child(5) {
    display: none;
  }
}
```

---

## ⚠️ Errores Comunes a Evitar

### 1. NO añadir padding a `.app-main`
```css
/* MAL */
.app-main { padding: 2rem; }

/* BIEN: usar .content-constrained donde se necesite */
```

### 2. NO usar `overflow: hidden` en contenedores con sticky
Bloquea `position: sticky`. `overflow: hidden` crea un nuevo scroll container y el `thead` sticky pasa a resolverse relativo al card (que no scrollea) en lugar de a `.lista-scroll-container`.

**Solución para esquinas redondeadas en V2:** usar `overflow: clip` (CSS Overflow Level 4).
Recorta visualmente igual que `hidden` pero **no crea scroll container ni nuevo BFC**, por lo que el sticky sigue funcionando:

```css
.tabla-bloque:has(> table) {
  overflow: clip;  /* recorta esquinas sin romper sticky */
}
```

Soporte: Chrome 90+, Firefox 81+, Safari 16+, Edge 90+.

**Excepción controlada (BC):** `.tabla-bloque:has(> .card-header)` usa `overflow: hidden` porque en las vistas V4 la tabla no tiene `thead` sticky propio — el sticky se resuelve relativo al viewport a través de `.app-main`. No hay conflicto.

### 3. Botón scroll-to-top FUERA de `<table>`
```html
<!-- MAL: Se mueve con scroll -->
<table>
  <tbody>...</tbody>
  <button id="tabla-scroll-to-top">↑</button>
</table>

<!-- BIEN: Hermano de table -->
<div class="lista-scroll-container">
  <table>...</table>
  <button id="tabla-scroll-to-top">↑</button>
</div>
```

### 4. NO escuchar `window.scroll` en C.2
```javascript
// MAL: Escucha scroll de página
window.addEventListener('scroll', toggleButton);

// BIEN: Escucha scroll de C.2
const container = document.querySelector('.lista-scroll-container');
container.addEventListener('scroll', toggleButton);
```

### 5. NO usar C.1/C.2 en formularios simples
- C.1/C.2 es para listas largas con scroll
- Formularios usan `.content-constrained` directamente en `.app-main`

---

## 📝 Checklist Implementación Vista

### Antes de Empezar
- [ ] ¿Qué tipo de vista? (V0 Login, V1 Dashboard, V2 Listado, V3-BC Tramitación, V4 Detalle/Edición, Pool)
- [ ] ¿Necesita C.1/C.2? (solo si lista larga >100 items)
- [ ] ¿Colores corporativos? (verde #087021 para identidad)
- [ ] ¿Responsive? (definir breakpoints y columnas a ocultar)

### Durante Implementación
- [ ] CSS: Cargar v2-theme.css, v2-layout.css, v2-components.css (en ese orden)
- [ ] Layout: Usar estructura A/B.1/B.2/B.3
- [ ] Colores: Usar variables CSS `var(--primary)`, NO hardcodear
- [ ] Padding: Usar `.content-constrained` selectivamente
- [ ] Sticky: Verificar que funciona (sin `overflow: hidden` en padre)

### Testing Final
- [ ] Desktop (>1200px): Layout completo
- [ ] Tablet (768-1199px): Columnas ocultas correctamente
- [ ] Mobile (<768px): Columnas esenciales visibles
- [ ] Sticky header: Funciona al scrollear
- [ ] Hover effects: Cards/botones responden
- [ ] Colores: Verde corporativo (#087021) en elementos de identidad

---

## 🔗 Referencias

### Archivos CSS v2
- `v2-theme.css` - Variables colores, spacing, tipografía
- `v2-layout.css` - Grid A/B/C, header, footer
- `v2-components.css` - Tabla, badges, botones, filtros

### Archivos por Vista
- **V0:** `v0-login.css`, `base_login.html`, `login_v0.html`
- **V1:** `v1-dashboard.css`, `index_v1.html`
- **V2:** Sin CSS específico (usa solo base), `lista_v2_base.html`, `listado_v2.html`, `v2-scroll-infinito.js`
- **V3-BC:** `v3-breadcrumbs.css`, `tramitacion_bc*.html`, `_tabla_hijos.html`
- **V4:** Sin CSS específico (clases en `v2-components.css`), `detalle.html` unificado, macro `macros/page_header.html`
- **Pool:** Inline en `pool_documentos.html` (variante V3-BC)

### Bootstrap 5
- [Accordion](https://getbootstrap.com/docs/5.3/components/accordion/)
- [Badges](https://getbootstrap.com/docs/5.3/components/badge/)
- [Buttons](https://getbootstrap.com/docs/5.3/components/buttons/)

---

**Versión:** 2.2
**Fecha:** 25 de marzo de 2026
**Cambios v2.0:** Eliminada V3 acordeón/tabs (legacy), documentada V3-BC, listados embebidos y Pool.
**Cambios v2.1 (#202):** Unificado thead V2/BC (verde claro `#c4ddca`). Añadido `.tabla-bloque` como contenedor card de tabla. Thead BC sin sticky (listas cortas). Responsive mobile en `_tabla_hijos.html` (clase `.tabla-hijos`). Estructura C.2 actualizada en V2 y V3-BC.
**Cambios v2.2 (#251):** Estructura real de V4 documentada: `lista-cabecera` para header vía macro `page_header`, wrapper `v4-content`, form envuelve todo el contenido. Lista completa de archivos legacy V3. Comparativa corregida (V4 usa C.1 solo para header).
**Referencia estudio:** `docs/ANALISIS_HOMOGENEIZACION_UI.md`