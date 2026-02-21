# Guía de Vistas Bootstrap - BDDAT

**Versión:** 1.0  
**Fecha:** 16 de febrero de 2026  
**Para:** Claude Code - Referencia de diseño UI

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
| **V3** (Tramitación) | A/B.1/B.2/acordeón/B.3 | Simple | NO |
| **V4** (Detalle/Edición) | A/B.1/B.2/B.3 | Simple | NO |

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
    <table class="expedientes-table"> <!-- D: thead sticky top: 0 -->
      <thead>...</thead>
      <tbody>...</tbody>
    </table>
    <button id="tabla-scroll-to-top">↑</button> <!-- sticky bottom: 1rem -->
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

## 🛠️ Vista V3 - Tramitación (Acordeón)

### ⚠️ Cambio Arquitectónico (12/02/2026)
**De:** Sidebar lateral (250px) + panel detalle  
**A:** Acordeón completo Bootstrap 5 en 100% ancho

### Decisiones de Diseño

#### Panel Contexto Fijo (Sticky)
- **Contenido:** Expediente + Proyecto juntos (NO en acordeón)
- **Razón:** No son parte de jerarquía de tramitación, mantienen contexto
- **CSS:** `position: sticky; top: 60px; z-index: 100;`

#### Jerarquía Acordeón
```
Panel Contexto (sticky)
└── Acordeón Solicitudes (Bootstrap 5)
    └── Detalle Solicitud
        └── Acordeón Fases (anidado)
            └── Detalle Fase
                └── Acordeón Trámites (anidado)
                    └── Detalle Trámite
                        └── Acordeón Tareas (anidado)
```

#### Cabeceras con Columnas Customizadas
```html
<button class="accordion-button collapsed">
  <span class="col-tipo">Solicitud 1: AAP+AAC</span>
  <span class="col-fases">Fases (1/2)</span>
  <span class="col-tramites">Trámites (1/5)</span>
  <span class="badge bg-success">Activa</span>
</button>
```

```css
.accordion-button {
  display: flex;
  justify-content: space-between;
}

.col-tipo { width: 200px; }
.col-fases { width: 100px; }
.col-tramites { width: 100px; }
```

#### Anidación Visual (Indentación)
```css
/* Cada nivel anidado: margen + borde color */
.accordion .accordion {
  margin-left: 2rem;
  border-left: 3px solid #0d6efd;
  padding-left: 1rem;
}

.accordion .accordion .accordion {
  border-left-color: #198754; /* Trámites */
}

.accordion .accordion .accordion .accordion {
  border-left-color: #ffc107; /* Tareas */
}
```

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

### API Estructura Completa

```python
@app.route('/api/expedientes/<int:id>/estructura_completa')
def estructura_completa(id):
    """Una sola petición HTTP con jerarquía completa."""
    expediente = Expediente.query.get_or_404(id)
    
    return jsonify({
        'expediente': expediente.to_dict(),
        'proyecto': expediente.proyecto.to_dict(),
        'solicitudes': [{
            **sol.to_dict(),
            'fases': [{
                **fase.to_dict(),
                'tramites': [{
                    **tram.to_dict(),
                    'tareas': [t.to_dict() for t in tram.tareas]
                } for tram in fase.tramites]
            } for fase in sol.fases]
        } for sol in expediente.solicitudes]
    })
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

### Estructura de Fichas

```html
<!-- Ficha tipo V4: cabecera verde secundario + cuerpo gris -->
<div class="card shadow-sm mb-3">
    <div class="card-header card-header-accent">
        <h5 class="mb-0 fw-semibold">
            <i class="fas fa-icon me-2"></i>Título Ficha
        </h5>
    </div>
    <div class="card-body card-body-tinted">
        <!-- Campos del formulario -->
    </div>
</div>
```

### Clases CSS Globales (en `v2-components.css`)

| Clase | Uso |
|-------|-----|
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

```html
{% if modo == 'editar' %}
<form id="form_expediente" class="form-detail"
      action="{{ url_for('blueprint.editar', id=objeto.id) }}" method="POST">
{% endif %}

<!-- ... contenido de la vista ... -->

{% if modo == 'editar' %}
</form>
{% endif %}
```

La clase `form-detail` activa el focus ring verde corporativo via `v2-components.css`.

### Botones de Acción

```html
{% if modo == 'ver' %}
    <a href="{{ url_for('blueprint.listado') }}" class="btn btn-secondary me-2">
        <i class="fas fa-arrow-left me-1"></i> Volver
    </a>
    <!-- Acciones específicas de la vista (ej: Tramitar) -->
    <a href="{{ url_for('blueprint.editar', id=objeto.id) }}" class="btn btn-primary">
        <i class="fas fa-edit me-1"></i> Editar
    </a>
{% else %}
    <a href="{{ url_for('blueprint.detalle', id=objeto.id) }}" class="btn btn-secondary me-2">
        <i class="fas fa-times me-1"></i> Cancelar
    </a>
    <button type="submit" class="btn btn-primary">
        <i class="fas fa-save me-1"></i> Guardar Cambios
    </button>
{% endif %}
```

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
Bloquea `position: sticky`. En C.1/C.2, el `overflow: hidden` va en `.app-main`, NO en `.lista-scroll-container`.

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
- [ ] ¿Qué tipo de vista? (Login, Dashboard, Listado, Tramitación, **Detalle/Edición**)
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
- **V2:** Sin CSS específico (usa solo base), `listado_v2.html`, `v2-scroll-infinito.js`
- **V3:** `v3-tramitacion.css` (pendiente), `tramitacion_v3.html`, `v3-accordion-main.js` (pendiente)
- **V4:** Sin CSS específico (clases en `v2-components.css`), `detalle.html` unificado

### Bootstrap 5
- [Accordion](https://getbootstrap.com/docs/5.3/components/accordion/)
- [Badges](https://getbootstrap.com/docs/5.3/components/badge/)
- [Buttons](https://getbootstrap.com/docs/5.3/components/buttons/)

---

**Versión:** 1.0 - Compactada para Claude Code  
**Fecha:** 16 de febrero de 2026  
**Histórico completo:** Ver `docs/arquitectura/FASE_3_FRONTEND_DINAMICO.md` y documentos relacionados