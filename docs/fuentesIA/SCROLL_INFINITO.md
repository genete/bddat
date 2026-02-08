# Scroll Infinito - Especificación e Implementación

**Proyecto:** BDDAT  
**Epic:** #93 (Diseño UI modular v2)  
**Issue relacionado:** #94 (Fase 1.5 y Fase 2)  
**Fecha:** 8 de febrero de 2026  
**Versión:** 1.0

---

## Índice

1. [Introducción](#introducción)
2. [Prerequisitos de Layout](#prerequisitos-de-layout)
3. [Arquitectura General](#arquitectura-general)
4. [Implementación Frontend](#implementación-frontend)
5. [Implementación Backend](#implementación-backend)
6. [Estados y Feedback](#estados-y-feedback)
7. [Testing](#testing)
8. [Referencias](#referencias)

---

## Introducción

**Scroll infinito** es una técnica de paginación automática que carga más resultados cuando el usuario se acerca al final de la lista visible, sin necesidad de pulsar "Siguiente".

### Objetivos

- Mejorar UX en listados con muchos registros (>100)
- Reducir carga inicial (cargar 40 items, luego 20 en cada batch)
- Mantener performance (evitar cargar todo en memoria)
- Integrar con estructura de layout modular existente (C.1/C.2/D)

### Casos de Uso en BDDAT

1. Listado de expedientes
2. Listado de solicitudes
3. Listado de actuaciones
4. Listado de documentos
5. Listado de entidades (si es muy grande)

---

## Prerequisitos de Layout

### ⚠️ IMPORTANTE: Estructura C.1/C.2 Obligatoria

**El scroll infinito requiere la estructura de layout modular** definida en `CSS_v2_GUIA_USO.md` (Fase 1.5, Issue #94).

### Arquitectura HTML Requerida

```html
<main class="app-main">
    <!-- C.1: Super-cabecera (sin scroll) -->
    <div class="lista-cabecera">
        <div class="page-header content-constrained">
            <h1>Expedientes</h1>
            <button class="btn btn-primary">Nuevo</button>
        </div>
        
        <div class="filters-row content-constrained">
            <div class="filters">
                <input type="search" id="search" placeholder="Buscar...">
                <select id="estado-filter">
                    <option>Estado: Todos</option>
                </select>
                <button class="btn btn-outline">Filtrar</button>
            </div>
            <div class="pagination-info" id="pagination-info">
                Mostrando <span id="current-count">40</span> de <span id="total-count">156</span>
            </div>
        </div>
    </div>
    
    <!-- C.2: Contenedor scrollable -->
    <div class="lista-scroll-container" id="scroll-container">
        <table class="expedientes-table">
            <thead>
                <tr>
                    <th>N° Expediente</th>
                    <th>Titular</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody id="table-body">
                <!-- Filas cargadas aquí -->
            </tbody>
        </table>
        
        <!-- Loader (dentro de C.2, al final de tabla) -->
        <div class="loading-indicator" id="loading-indicator" style="display:none;">
            <i class="fas fa-spinner fa-spin"></i> Cargando más resultados...
        </div>
    </div>
</main>
```

### CSS Requerido (ya implementado en Fase 1.5)

```css
/* v2-layout.css */
.app-main {
  display: flex;
  flex-direction: column;
  overflow: hidden;  /* CRÍTICO */
}

/* v2-components.css */
.lista-cabecera {
  flex-shrink: 0;    /* No se comprime */
  background: var(--gris-especifico);
}

.lista-scroll-container {
  flex: 1;                  /* Ocupa espacio disponible */
  overflow-y: auto;         /* Scroll vertical */
  overflow-x: hidden;
  position: relative;       /* Contexto para sticky header */
}

/* Sticky header dentro de C.2 */
.lista-scroll-container .expedientes-table thead th {
  position: sticky;
  top: 0;
  z-index: 10;
}
```

### ¿Por qué es obligatorio C.1/C.2?

| Aspecto | Sin C.1/C.2 (scroll en window) | Con C.1/C.2 (scroll en contenedor) |
|---------|-------------------------------|------------------------------------|
| **Listener de scroll** | `window.addEventListener('scroll', ...)` | `container.addEventListener('scroll', ...)` |
| **Cálculo umbral** | `window.innerHeight + window.scrollY` | `container.scrollTop + container.clientHeight` |
| **Sticky header** | Relativo a viewport (puede desaparecer) | Relativo a contenedor (siempre visible) |
| **Filtros al scroll** | Desaparecen | Siempre visibles (en C.1) |
| **Control preciso** | Más difícil | Más sencillo |

---

## Arquitectura General

### Flujo de Datos

```
1. Usuario abre listado
   ↓
2. Backend: cargar 40 items (primera carga)
   ↓
3. Frontend: renderizar en tabla
   ↓
4. Usuario hace scroll hacia abajo
   ↓
5. JavaScript detecta proximidad al final (threshold: 80%)
   ↓
6. AJAX GET /api/expedientes?offset=40&limit=20
   ↓
7. Backend: devolver siguientes 20 items
   ↓
8. Frontend: append filas a tabla
   ↓
9. Actualizar contador "Mostrando X de Y"
   ↓
10. Repetir 4-9 hasta llegar al final
```

### Parámetros de Configuración

```javascript
const CONFIG = {
  INITIAL_LIMIT: 40,      // Primera carga
  BATCH_SIZE: 20,          // Siguientes cargas
  SCROLL_THRESHOLD: 0.8,   // Cargar cuando se ha scrolleado 80%
  DEBOUNCE_MS: 200         // Evitar múltiples peticiones
};
```

---

## Implementación Frontend

### JavaScript (ES6)

```javascript
// app/static/js/infinite-scroll.js

class InfiniteScrollList {
  constructor(options) {
    this.container = document.getElementById(options.containerId);
    this.tableBody = document.getElementById(options.tableBodyId);
    this.loadingIndicator = document.getElementById(options.loadingId);
    this.currentCountEl = document.getElementById('current-count');
    this.totalCountEl = document.getElementById('total-count');
    
    this.apiEndpoint = options.apiEndpoint;
    this.initialLimit = options.initialLimit || 40;
    this.batchSize = options.batchSize || 20;
    this.threshold = options.threshold || 0.8;
    
    this.offset = this.initialLimit;  // Ya cargados 40 inicialmente
    this.total = parseInt(this.totalCountEl.textContent) || 0;
    this.loading = false;
    this.hasMore = this.offset < this.total;
    
    this.init();
  }
  
  init() {
    // Adjuntar listener al contenedor scrollable (C.2)
    this.container.addEventListener('scroll', this.debounce(() => {
      this.checkScrollPosition();
    }, 200));
  }
  
  checkScrollPosition() {
    if (this.loading || !this.hasMore) return;
    
    const scrollTop = this.container.scrollTop;
    const scrollHeight = this.container.scrollHeight;
    const clientHeight = this.container.clientHeight;
    
    // Calcular porcentaje scrolleado
    const scrollPercentage = (scrollTop + clientHeight) / scrollHeight;
    
    if (scrollPercentage >= this.threshold) {
      this.loadMore();
    }
  }
  
  async loadMore() {
    this.loading = true;
    this.showLoading();
    
    try {
      const url = `${this.apiEndpoint}?offset=${this.offset}&limit=${this.batchSize}`;
      const response = await fetch(url);
      const data = await response.json();
      
      // Renderizar nuevas filas
      this.renderRows(data.items);
      
      // Actualizar estado
      this.offset += data.items.length;
      this.hasMore = this.offset < data.total;
      
      // Actualizar contador
      this.updateCounter();
      
    } catch (error) {
      console.error('Error cargando más resultados:', error);
      this.showError();
    } finally {
      this.loading = false;
      this.hideLoading();
    }
  }
  
  renderRows(items) {
    items.forEach(item => {
      const row = this.createRow(item);
      this.tableBody.appendChild(row);
    });
  }
  
  createRow(item) {
    // Implementación específica por listado
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${item.numero_expediente}</strong></td>
      <td>${item.titular}</td>
      <td><span class="badge badge-${item.estado_class}">${item.estado}</span></td>
      <td>
        <a href="/expedientes/${item.id_expediente}" class="btn btn-sm btn-primary">Ver</a>
      </td>
    `;
    return tr;
  }
  
  updateCounter() {
    this.currentCountEl.textContent = this.offset;
  }
  
  showLoading() {
    this.loadingIndicator.style.display = 'flex';
  }
  
  hideLoading() {
    this.loadingIndicator.style.display = 'none';
  }
  
  showError() {
    // Opcional: mostrar toast/mensaje de error
    alert('Error al cargar más resultados. Inténtalo de nuevo.');
  }
  
  // Utility: debounce
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }
}

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
  const scrollList = new InfiniteScrollList({
    containerId: 'scroll-container',
    tableBodyId: 'table-body',
    loadingId: 'loading-indicator',
    apiEndpoint: '/api/expedientes',
    initialLimit: 40,
    batchSize: 20,
    threshold: 0.8
  });
});
```

### CSS para Loading Indicator

```css
/* v2-components.css */
.loading-indicator {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
  gap: 0.5rem;
}

.loading-indicator i {
  font-size: 1.25rem;
  color: var(--primary);
}
```

---

## Implementación Backend

### Endpoint Flask

```python
# app/routes/api_routes.py

from flask import Blueprint, request, jsonify
from app.models import Expediente
from app import db

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/expedientes', methods=['GET'])
def get_expedientes_paginated():
    """
    Endpoint para scroll infinito de expedientes.
    
    Query params:
      - offset: Número de registros a saltar (default: 0)
      - limit: Número de registros a devolver (default: 20, max: 100)
      - search: Término de búsqueda (opcional)
      - estado: Filtro por estado (opcional)
    
    Returns:
      JSON con items, total, offset, limit
    """
    try:
        # Parámetros
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 20, type=int)
        search = request.args.get('search', '', type=str)
        estado_filter = request.args.get('estado', '', type=str)
        
        # Validación
        if limit > 100:
            limit = 100
        
        # Query base
        query = db.session.query(Expediente)
        
        # Filtros
        if search:
            query = query.filter(
                db.or_(
                    Expediente.numero_expediente.ilike(f'%{search}%'),
                    Expediente.titular.ilike(f'%{search}%')
                )
            )
        
        if estado_filter:
            query = query.filter(Expediente.estado == estado_filter)
        
        # Total (antes de paginar)
        total = query.count()
        
        # Paginar
        items = query.order_by(Expediente.fecha_presentacion.desc()) \
                     .offset(offset) \
                     .limit(limit) \
                     .all()
        
        # Serializar
        items_json = [
            {
                'id_expediente': exp.id_expediente,
                'numero_expediente': exp.numero_expediente,
                'titular': exp.titular,
                'estado': exp.estado,
                'estado_class': get_badge_class(exp.estado),
                'vencimiento': exp.vencimiento.strftime('%d/%m/%Y') if exp.vencimiento else '-'
            }
            for exp in items
        ]
        
        return jsonify({
            'items': items_json,
            'total': total,
            'offset': offset,
            'limit': limit,
            'has_more': (offset + limit) < total
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_badge_class(estado):
    """Helper para clases CSS de badges."""
    mapping = {
        'En trámite': 'info',
        'Resuelto': 'success',
        'Incompleto': 'warning',
        'Vencido': 'danger'
    }
    return mapping.get(estado, 'secondary')
```

### Ruta Principal (primera carga)

```python
# app/routes/expedientes_routes.py

@expedientes_bp.route('/expedientes')
def listar_expedientes():
    """Vista principal de listado de expedientes."""
    # Primera carga: 40 items
    expedientes = db.session.query(Expediente) \
                             .order_by(Expediente.fecha_presentacion.desc()) \
                             .limit(40) \
                             .all()
    
    total = db.session.query(Expediente).count()
    
    return render_template(
        'expedientes/listado.html',
        expedientes=expedientes,
        total=total,
        current_count=len(expedientes)
    )
```

---

## Estados y Feedback

### Estados del Sistema

1. **Carga inicial**: Mostrar primeros 40 items
2. **Scrolling**: Usuario hace scroll, sistema detecta threshold
3. **Loading**: Mostrar indicador "Cargando..."
4. **Success**: Append nuevas filas, actualizar contador
5. **End**: Ya no hay más items (ocultar indicador)
6. **Error**: Mostrar mensaje de error, permitir reintentar

### Indicadores Visuales

```html
<!-- Loading indicator -->
<div class="loading-indicator" id="loading-indicator">
    <i class="fas fa-spinner fa-spin"></i>
    Cargando más resultados...
</div>

<!-- End of list -->
<div class="end-of-list" id="end-indicator" style="display:none;">
    <i class="fas fa-check-circle"></i>
    Has visto todos los expedientes
</div>

<!-- Error -->
<div class="error-indicator" id="error-indicator" style="display:none;">
    <i class="fas fa-exclamation-triangle"></i>
    Error al cargar. <button class="btn btn-sm btn-outline" onclick="retryLoad()">Reintentar</button>
</div>
```

---

## Testing

### Casos de Prueba

1. **Scroll hasta el final**: Verificar que se cargan todos los items
2. **Scroll rápido**: No debe lanzar múltiples peticiones (debounce)
3. **Error de red**: Debe mostrar error y permitir reintentar
4. **Sin más resultados**: Debe dejar de intentar cargar
5. **Filtros aplicados**: Scroll infinito debe respetar filtros
6. **Responsive mobile**: Scroll debe funcionar igual en mobile

### Testing Manual

```bash
# 1. Crear muchos expedientes de prueba (>100)
flask shell
>>> from app.utils.seed_data import create_test_expedientes
>>> create_test_expedientes(200)

# 2. Abrir navegador y probar scroll
# 3. Monitorizar Network tab (deben aparecer peticiones AJAX)
# 4. Verificar que contador se actualiza
```

---

## Referencias

- **CSS_v2_GUIA_USO.md**: Estructura de layout C.1/C.2/D (prerequisito)
- **ISSUE_94_ESTRUCTURA.md**: Roadmap de implementación UI v2
- **MDN Intersection Observer API**: Alternativa más moderna (considerar para Fase 3)
- **Flask-SQLAlchemy Pagination**: [Docs oficiales](https://flask-sqlalchemy.palletsprojects.com/en/2.x/api/#flask_sqlalchemy.Pagination)

---

**Fin del documento.**