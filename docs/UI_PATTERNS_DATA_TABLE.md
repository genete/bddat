# Patrón UI: Data Table Reutilizable

**Issue:** #94 (Fase 1 - Sistema Robusto)  
**Epic:** #93 (UI Modular)  
**Fecha:** 2026-02-07  
**Estado:** ✅ Implementado

---

## 🎯 Objetivo

Sistema de tablas **reutilizable, robusto y accesible** usando estructura DIV + CSS Grid, con sticky header funcional al 100%.

---

## 🌐 Diseño

### Ventajas sobre `<table>` HTML:

✅ **Sticky header funciona perfectamente** (sin JavaScript)  
✅ **CSS Grid flexible** para columnas responsive  
✅ **Accesibilidad** con ARIA roles  
✅ **Reutilizable** para cualquier listado  
✅ **Control total** de responsive por columna  
✅ **Fácil mantenimiento** y extensión

---

## 📚 Archivos

### CSS Base:
- `app/static/css/v2-data-table.css` - Sistema completo

### Ejemplo HTML:
- `test_v2_robust.html` - Demo con 40 expedientes

---

## 🔨 Estructura HTML

### Patrón Básico:

```html
<div class="data-table data-table--VARIANTE" role="table">
  
  <!-- HEADER (Sticky) -->
  <div class="data-table__header" role="rowgroup">
    <div class="data-table__row" role="row">
      <div class="data-table__cell" role="columnheader">Columna 1</div>
      <div class="data-table__cell" role="columnheader">Columna 2</div>
      <div class="data-table__cell" role="columnheader">Columna 3</div>
    </div>
  </div>
  
  <!-- BODY (Scrollable) -->
  <div class="data-table__body" role="rowgroup">
    <!-- Fila 1 -->
    <div class="data-table__row" role="row">
      <div class="data-table__cell" role="cell">Dato 1</div>
      <div class="data-table__cell" role="cell">Dato 2</div>
      <div class="data-table__cell" role="cell">Dato 3</div>
    </div>
    
    <!-- Más filas... -->
  </div>
  
</div>
```

---

## 📋 Variantes Disponibles

### 1. Expedientes: `.data-table--expedientes`

**Columnas:**
- N° Expediente (1fr)
- Titular (2fr)
- Solicitudes (0.8fr) - *Oculta en tablet*
- Estado (1.2fr) - *Oculta en mobile*
- Vencimiento (1fr) - *Oculta en mobile*
- Acciones (1fr)

**Ejemplo:**
```html
<div class="data-table data-table--expedientes" role="table">
  <div class="data-table__header" role="rowgroup">
    <div class="data-table__row" role="row">
      <div class="data-table__cell" role="columnheader">N° Expediente</div>
      <div class="data-table__cell" role="columnheader">Titular</div>
      <div class="data-table__cell data-table__cell--center" role="columnheader">Solicitudes</div>
      <div class="data-table__cell" role="columnheader">Estado</div>
      <div class="data-table__cell" role="columnheader">Vencimiento</div>
      <div class="data-table__cell data-table__cell--center" role="columnheader">Acciones</div>
    </div>
  </div>
  
  <div class="data-table__body" role="rowgroup">
    <div class="data-table__row" role="row">
      <div class="data-table__cell data-table__cell--strong" role="cell">EXP-2026-001</div>
      <div class="data-table__cell" role="cell">Endesa Energía S.A.</div>
      <div class="data-table__cell data-table__cell--center" role="cell">3</div>
      <div class="data-table__cell" role="cell">
        <span class="badge badge-info">En trámite</span>
      </div>
      <div class="data-table__cell" role="cell">15/02/2026</div>
      <div class="data-table__cell data-table__cell--actions" role="cell">
        <button class="btn btn-sm btn-primary">Ver</button>
      </div>
    </div>
    <!-- Más filas... -->
  </div>
</div>
```

---

### 2. Solicitudes: `.data-table--solicitudes`

**Columnas:**
- N° Solicitud (1fr)
- Tipo (2fr)
- Fecha (1fr)
- Estado (1.2fr)
- Acciones (1fr)

**CSS Grid:**
```css
.data-table--solicitudes .data-table__row {
  grid-template-columns:
    minmax(100px, 1fr)   /* N° Solicitud */
    minmax(150px, 2fr)   /* Tipo */
    minmax(100px, 1fr)   /* Fecha */
    minmax(120px, 1.2fr) /* Estado */
    minmax(100px, 1fr);  /* Acciones */
  gap: 1rem;
}
```

---

### 3. Titulares: `.data-table--titulares`

**Columnas:**
- Nombre (2fr)
- NIF/CIF (1.5fr)
- Domicilio (2fr)
- Acciones (1fr)

**CSS Grid:**
```css
.data-table--titulares .data-table__row {
  grid-template-columns:
    minmax(180px, 2fr)   /* Nombre */
    minmax(120px, 1.5fr) /* NIF/CIF */
    minmax(150px, 2fr)   /* Domicilio */
    minmax(100px, 1fr);  /* Acciones */
  gap: 1rem;
}
```

---

## ➕ Cómo Añadir Nueva Variante

### Ejemplo: Listado de Usuarios

**1. Añadir CSS en `v2-data-table.css`:**

```css
/* ===== VARIANTE: USUARIOS ===== */
.data-table--usuarios .data-table__row {
  grid-template-columns:
    minmax(150px, 1.5fr) /* Nombre */
    minmax(180px, 2fr)   /* Email */
    minmax(120px, 1fr)   /* Rol */
    minmax(100px, 1fr);  /* Acciones */
  gap: 1rem;
}

/* Responsive: ocultar Email en mobile */
@media (max-width: 767px) {
  .data-table--usuarios .data-table__row {
    grid-template-columns:
      minmax(150px, 2fr) /* Nombre */
      minmax(100px, 1fr) /* Rol */
      minmax(80px, 1fr); /* Acciones */
  }
  
  .data-table--usuarios .data-table__cell:nth-child(2) {
    display: none; /* Ocultar Email */
  }
}
```

**2. HTML:**

```html
<div class="data-table data-table--usuarios" role="table">
  <div class="data-table__header" role="rowgroup">
    <div class="data-table__row" role="row">
      <div class="data-table__cell" role="columnheader">Nombre</div>
      <div class="data-table__cell" role="columnheader">Email</div>
      <div class="data-table__cell" role="columnheader">Rol</div>
      <div class="data-table__cell data-table__cell--center" role="columnheader">Acciones</div>
    </div>
  </div>
  
  <div class="data-table__body" role="rowgroup">
    <div class="data-table__row" role="row">
      <div class="data-table__cell data-table__cell--strong" role="cell">Carlos López</div>
      <div class="data-table__cell" role="cell">carlos@example.com</div>
      <div class="data-table__cell" role="cell">
        <span class="badge badge-info">Admin</span>
      </div>
      <div class="data-table__cell data-table__cell--actions" role="cell">
        <button class="btn btn-sm btn-primary">Editar</button>
      </div>
    </div>
  </div>
</div>
```

---

## 🎨 Clases Utilidad para Celdas

### Alineación:
```html
<!-- Centrado (números, badges) -->
<div class="data-table__cell data-table__cell--center" role="cell">3</div>

<!-- Derecha (cantidades) -->
<div class="data-table__cell data-table__cell--right" role="cell">1.234,56 €</div>
```

### Peso y destaque:
```html
<!-- Texto destacado (IDs, nombres principales) -->
<div class="data-table__cell data-table__cell--strong" role="cell">EXP-2026-001</div>
```

### Acciones (botones):
```html
<!-- Contenedor de botones (alineados derecha) -->
<div class="data-table__cell data-table__cell--actions" role="cell">
  <button class="btn btn-sm btn-primary">Ver</button>
  <button class="btn btn-sm btn-outline">Editar</button>
</div>
```

---

## 📱 Responsive

### Breakpoints:
- **Desktop:** >992px - Todas las columnas
- **Tablet:** 768px-991px - Ocultar columnas secundarias
- **Mobile:** <768px - Solo columnas esenciales

### Estrategia:
1. **Desktop:** Mostrar todas las columnas definidas
2. **Tablet:** Ocultar 1-2 columnas menos importantes (`:nth-child(N)`)
3. **Mobile:** Solo 2-3 columnas esenciales + acciones

### Ejemplo Expedientes:
```css
/* Tablet: Ocultar Solicitudes */
@media (max-width: 991px) {
  .data-table--expedientes .data-table__cell:nth-child(3) {
    display: none;
  }
}

/* Mobile: Solo Expediente + Titular + Acciones */
@media (max-width: 767px) {
  .data-table--expedientes .data-table__cell:nth-child(3), /* Solicitudes */
  .data-table--expedientes .data-table__cell:nth-child(4), /* Estado */
  .data-table--expedientes .data-table__cell:nth-child(5)  /* Vencimiento */ {
    display: none;
  }
}
```

---

## ♻️ Reutilización en Flask (Jinja2)

### Template base: `templates/components/data_table.html`

```jinja2
{# Componente reutilizable de tabla #}
<div class="data-table data-table--{{ variant }}" role="table">
  
  <div class="data-table__header" role="rowgroup">
    <div class="data-table__row" role="row">
      {% for column in columns %}
        <div class="data-table__cell {{ column.class }}" role="columnheader">
          {{ column.label }}
        </div>
      {% endfor %}
    </div>
  </div>
  
  <div class="data-table__body" role="rowgroup">
    {% if rows %}
      {% for row in rows %}
        <div class="data-table__row" role="row">
          {% for cell in row.cells %}
            <div class="data-table__cell {{ cell.class }}" role="cell">
              {{ cell.content | safe }}
            </div>
          {% endfor %}
        </div>
      {% endfor %}
    {% else %}
      <div class="data-table__empty">
        <i class="fas fa-inbox"></i>
        <p>{{ empty_message | default('No hay datos para mostrar') }}</p>
      </div>
    {% endif %}
  </div>
  
</div>
```

### Uso en ruta Flask:

```python
from flask import render_template

@app.route('/expedientes')
def listar_expedientes():
    expedientes = Expediente.query.all()
    
    # Configuración tabla
    columns = [
        {'label': 'N° Expediente', 'class': ''},
        {'label': 'Titular', 'class': ''},
        {'label': 'Solicitudes', 'class': 'data-table__cell--center'},
        {'label': 'Estado', 'class': ''},
        {'label': 'Vencimiento', 'class': ''},
        {'label': 'Acciones', 'class': 'data-table__cell--center'},
    ]
    
    # Datos filas
    rows = []
    for exp in expedientes:
        rows.append({
            'cells': [
                {'content': f'<strong>{exp.numero}</strong>', 'class': 'data-table__cell--strong'},
                {'content': exp.titular.nombre, 'class': ''},
                {'content': exp.solicitudes.count(), 'class': 'data-table__cell--center'},
                {'content': f'<span class="badge badge-{exp.estado_badge}">{exp.estado}</span>', 'class': ''},
                {'content': exp.fecha_vencimiento or '-', 'class': ''},
                {'content': f'<a href="{url_for('ver_expediente', id=exp.id)}" class="btn btn-sm btn-primary">Ver</a>', 'class': 'data-table__cell--actions'},
            ]
        })
    
    return render_template('expedientes/listar.html',
                         columns=columns,
                         rows=rows,
                         variant='expedientes')
```

---

## ✅ Testing

### Test Manual:
1. Abrir `test_v2_robust.html` en navegador
2. Verificar sticky header al scrollear
3. Redimensionar ventana (desktop → tablet → mobile)
4. Validar columnas ocultas en cada breakpoint
5. Hover en filas (fondo verde claro)

### Checklist:
- [ ] Header verde con gradiente Junta
- [ ] Sticky header se queda fijo al scrollear
- [ ] Hover filas cambia a verde claro
- [ ] Responsive oculta columnas correctamente
- [ ] Badges estados con colores correctos
- [ ] Botones alineados derecha en acciones

---

## 📄 Referencias

- **Issue:** [#94 - Listado Expedientes (UI)](https://github.com/genete/bddat/issues/94)
- **Epic:** [#93 - Epic UI Modular](https://github.com/genete/bddat/issues/93)
- **Colores:** [#58 - Paleta Junta Andalucía](https://github.com/genete/bddat/issues/58)

---

## 📝 Notas

### Por qué DIVs en vez de `<table>`:

❌ **Problema con `<table>` HTML:**
- `position: sticky` en `<thead>` no funciona bien cross-browser
- `overflow: hidden` bloquea sticky
- `border-collapse` rompe sticky en algunos navegadores
- Responsive limitado (solo `display: none` por columna)

✅ **Solución con DIVs + CSS Grid:**
- Sticky funciona al 100% sin JavaScript
- Control total de responsive con Grid
- ARIA roles mantienen accesibilidad
- Fácil de personalizar y extender

---

**Última actualización:** 2026-02-07  
**Autor:** Carlos López (@genete)