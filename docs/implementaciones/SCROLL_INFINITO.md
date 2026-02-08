# Scroll Infinito - Estrategia de Implementación

**Issue:** #94 (Fase 2)  
**Epic:** #93  
**Fecha:** 2026-02-08  
**Versión:** 2.0 (fusionada)

---

## 📚 Índice

1. [Problema](#problema)
2. [Prerequisitos de Layout](#prerequisitos-de-layout)
3. [Estrategias Disponibles](#estrategias-disponibles)
4. [Recomendación para BDDAT](#recomendación-para-bddat)
5. [Implementación Paso a Paso](#implementación-paso-a-paso)
6. [Performance](#performance)
7. [Testing](#testing)
8. [Referencias](#referencias)

---

## 📝 Problema

**Escenario:**
- Base de datos con 10,000+ expedientes
- Imposible cargar todos al inicio (lento, consume memoria)
- Necesidad de scroll infinito (carga progresiva)

**Objetivo:**
- Cargar 40-50 items inicialmente
- Cargar 20-50 más automáticamente al scrollear cerca del final
- Mantener DOM limpio y navegador rápido

---

## ⚠️ Prerequisitos de Layout

### ✅ IMPORTANTE: Estructura C.1/C.2 Obligatoria

**El scroll infinito REQUIERE la estructura de layout modular** definida en `CSS_v2_GUIA_USO.md` (Fase 1.5, completada).

### Arquitectura HTML Requerida

```html
<main class="app-main">
    <!-- C.1: Super-cabecera (sin scroll) -->
    <div class="lista-cabecera">
        <div class="page-header content-constrained">
            <h1><i class="fas fa-folder-open"></i> Expedientes</h1>
            <button class="btn btn-primary">Nuevo</button>
        </div>
        
        <div class="filters-row content-constrained">
            <div class="filters">
                <input type="search" placeholder="Buscar...">
                <select><option>Estado: Todos</option></select>
                <button class="btn btn-outline">Filtrar</button>
            </div>
            <div class="pagination-info">
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
        
        <!-- Loader dentro de C.2 -->
        <div class="loading-indicator" id="loading-indicator" style="display:none;">
            <i class="fas fa-spinner fa-spin"></i> Cargando más...
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
  overflow: hidden;  /* CRÍTICO: aislamos scroll */
}

/* v2-components.css */
.lista-cabecera {
  flex-shrink: 0;    /* No se comprime */
}

.lista-scroll-container {
  flex: 1;                  /* Ocupa espacio disponible */
  overflow-y: auto;         /* Scroll vertical */
  position: relative;       /* Contexto para sticky */
}

.lista-scroll-container .expedientes-table thead th {
  position: sticky;
  top: 0;                   /* Pegado al top de C.2 */
  z-index: 10;
}
```

### 💡 ¿Por qué es obligatorio C.1/C.2?

| Aspecto | Sin C.1/C.2 (scroll en `window`) | Con C.1/C.2 (scroll en contenedor) |
|---------|-----------------------------------|-------------------------------------|
| **Listener** | `window.addEventListener('scroll', ...)` | `container.addEventListener('scroll', ...)` |
| **Cálculo umbral** | `window.innerHeight + window.scrollY` | `container.scrollTop + container.clientHeight` |
| **Sticky header** | Relativo a viewport (desaparece) | Relativo a contenedor (siempre visible) |
| **Filtros al scroll** | Desaparecen con scroll | **Siempre visibles (C.1)** ✅ |
| **Control preciso** | Más difícil | **Más sencillo** ✅ |

**Conclusión:** C.2 con `overflow-y: auto` permite scroll independiente, manteniendo filtros (C.1) y header/footer (B.1/B.3) fijos.

---

## 🛠️ Estrategias Disponibles

### **A) Append Simple (Acumula TODO)** ⚠️

**Cómo funciona:**
```javascript
// Carga inicial: 50 registros
// Scroll down → carga 50 más (total 100 en DOM)
// Scroll down → carga 50 más (total 150 en DOM)
// ... sigue acumulando
```

**Pros:**
- ✅ Simple de implementar
- ✅ No necesita librerías

**Contras:**
- ❌ Con 10,000 registros → DOM gigante → navegador lento
- ❌ Memoria crece sin control
- ❌ **NO recomendado** para muchos registros

---

### **B) Windowing Virtual (TanStack Virtual)** ✅

**Cómo funciona:**
```javascript
// Tienes 10,000 registros en memoria (JavaScript)
// Solo renderizas los 20 visibles en pantalla
// Al hacer scroll:
//   - Destruye filas que salen del viewport
//   - Crea filas que entran al viewport
// DOM siempre tiene ~20 filas (rápido)
```

**Pros:**
- ✅ DOM pequeño (solo lo visible)
- ✅ Scroll súper fluido
- ✅ Soporta millones de registros

**Contras:**
- ⚠️ Requiere librería ([TanStack Virtual](https://tanstack.com/virtual/latest))
- ⚠️ Todos los datos deben estar en memoria JavaScript

**Cuándo usar:**
- Más de 20,000 registros en memoria
- Necesitas scroll súper fluido
- Aceptas añadir librería externa

---

### **C) Paginación Cursor Backend** 🚀 **RECOMENDADO**

**Cómo funciona:**
```python
# Backend Flask/SQLAlchemy
@app.route('/api/expedientes')
def get_expedientes():
    cursor = request.args.get('cursor', 0)  # Último ID visto
    limit = 50
    
    expedientes = db.session.query(Expediente)\
        .filter(Expediente.id > cursor)\
        .order_by(Expediente.id)\
        .limit(limit)\
        .all()
    
    return jsonify({
        'data': [e.to_dict() for e in expedientes],
        'next_cursor': expedientes[-1].id if expedientes else None,
        'has_more': len(expedientes) == limit
    })
```

```javascript
// Frontend: escucha scroll en C.2 (lista-scroll-container)
const container = document.getElementById('scroll-container');
let cursor = 0;

container.addEventListener('scroll', async () => {
    const scrollTop = container.scrollTop;
    const scrollHeight = container.scrollHeight;
    const clientHeight = container.clientHeight;
    
    // Threshold: 80% scrolleado
    if ((scrollTop + clientHeight) / scrollHeight >= 0.8) {
        const response = await fetch(`/api/expedientes?cursor=${cursor}`);
        const { data, next_cursor, has_more } = await response.json();
        
        appendRowsToTable(data);
        cursor = next_cursor;
    }
});
```

**Pros:**
- ✅ Fácil de implementar (Flask + SQLAlchemy)
- ✅ No necesita librería frontend compleja
- ✅ Backend solo envía lo necesario
- ✅ 10,000 registros es manejable (200 cargas de 50)
- ✅ **Integrado con estructura C.2** (scroll en contenedor)

**Contras:**
- ⚠️ DOM crece con el tiempo (1000 filas = pesado)
- ⚠️ Si usuario scrollea mucho, puede ralentizarse

**Cuándo usar:**
- Hasta 10,000-20,000 registros
- Si no quieres añadir librerías JavaScript
- **Caso de BDDAT** 🎯

---

### **D) Windowing + Cursor Backend** 🏆 **ÓPTIMO**

**Cómo funciona:**
```javascript
// Combina C + B:
// 1. Backend pagina con cursor (50 en 50)
// 2. Frontend usa windowing virtual
// 3. Solo renderizas 20 filas visibles
// 4. Al hacer scroll cerca del final del buffer, pide más al backend
```

**Pros:**
- ✅ DOM siempre tiene ~20 filas (rápido)
- ✅ Backend solo envía lo necesario
- ✅ Soporta millones de registros
- ✅ Mejor experiencia de usuario

**Contras:**
- ⚠️ Más complejo de implementar
- ⚠️ Requiere TanStack Virtual o similar

**Cuándo usar:**
- Más de 20,000 registros
- Si necesitas scroll súper fluido
- **Futura expansión de BDDAT**

---

## 🎯 Recomendación para BDDAT

### **Fase 2: Opción C (Cursor Backend)** 🚀

**Razones:**
1. ✅ 10,000 expedientes es manejable
2. ✅ Implementación simple (Flask + SQLAlchemy)
3. ✅ No requiere librerías complejas
4. ✅ Performance aceptable
5. ✅ **Ya tenemos estructura C.1/C.2 lista (Fase 1.5)** 🎉

**Si en el futuro hay 100,000+ expedientes:**
- Migrar a Opción D (Windowing + Cursor)

---

## 📝 Implementación Paso a Paso

### **1. Backend (Flask)**

```python
# app/routes/expedientes.py

@expedientes_bp.route('/api/expedientes')
def api_expedientes():
    """API para scroll infinito con cursor."""
    cursor = request.args.get('cursor', 0, type=int)
    limit = request.args.get('limit', 50, type=int)
    
    # Filtros opcionales
    estado = request.args.get('estado')
    search = request.args.get('search')
    
    query = db.session.query(Expediente)
    
    # Aplicar filtros
    if estado and estado != 'todos':
        query = query.filter(Expediente.estado == estado)
    
    if search:
        query = query.filter(
            db.or_(
                Expediente.numero.ilike(f'%{search}%'),
                Expediente.titular.ilike(f'%{search}%')
            )
        )
    
    # Paginación con cursor
    query = query.filter(Expediente.id > cursor)\
                 .order_by(Expediente.id)\
                 .limit(limit)
    
    expedientes = query.all()
    
    return jsonify({
        'data': [{
            'id': e.id,
            'numero': e.numero,
            'titular': e.titular,
            'estado': e.estado,
            'estado_class': e.get_estado_class(),
            'vencimiento': e.vencimiento.isoformat() if e.vencimiento else None
        } for e in expedientes],
        'next_cursor': expedientes[-1].id if expedientes else None,
        'has_more': len(expedientes) == limit
    })
```

### **2. Frontend (JavaScript)**

Crear `app/static/js/v2-scroll-infinito.js`:

```javascript
/**
 * v2-scroll-infinito.js
 * Carga progresiva de expedientes con scroll infinito
 * REQUIERE: Estructura C.1/C.2 (lista-scroll-container)
 */

class ScrollInfinito {
    constructor(options) {
        // Contenedor scrollable (C.2)
        this.container = document.getElementById(options.containerId || 'scroll-container');
        this.tbody = document.querySelector(options.tbody);
        this.loadingIndicator = document.getElementById('loading-indicator');
        this.currentCountEl = document.getElementById('current-count');
        this.totalCountEl = document.getElementById('total-count');
        
        this.apiUrl = options.apiUrl || '/api/expedientes';
        this.cursor = 0;
        this.loading = false;
        this.hasMore = true;
        this.limit = options.limit || 50;
        this.threshold = options.threshold || 0.8; // 80%
        
        this.init();
    }
    
    init() {
        // Escuchar scroll en C.2 (NO en window)
        this.container.addEventListener('scroll', () => this.handleScroll());
        this.loadMore(); // Carga inicial
    }
    
    handleScroll() {
        const scrollTop = this.container.scrollTop;
        const scrollHeight = this.container.scrollHeight;
        const clientHeight = this.container.clientHeight;
        
        // Calcular porcentaje scrolleado
        const scrollPercentage = (scrollTop + clientHeight) / scrollHeight;
        
        if (scrollPercentage >= this.threshold && !this.loading && this.hasMore) {
            this.loadMore();
        }
    }
    
    async loadMore() {
        this.loading = true;
        this.showLoader();
        
        try {
            const url = `${this.apiUrl}?cursor=${this.cursor}&limit=${this.limit}`;
            const response = await fetch(url);
            const { data, next_cursor, has_more } = await response.json();
            
            this.appendRows(data);
            this.cursor = next_cursor;
            this.hasMore = has_more;
            
            // Actualizar contador
            if (this.currentCountEl) {
                const currentCount = parseInt(this.currentCountEl.textContent) + data.length;
                this.currentCountEl.textContent = currentCount;
            }
            
            if (!has_more) {
                this.showEndMessage();
            }
        } catch (error) {
            console.error('Error cargando expedientes:', error);
            this.showError();
        } finally {
            this.loading = false;
            this.hideLoader();
        }
    }
    
    appendRows(expedientes) {
        expedientes.forEach(exp => {
            const row = this.createRow(exp);
            this.tbody.insertAdjacentHTML('beforeend', row);
        });
    }
    
    createRow(exp) {
        return `
            <tr>
                <td><strong>${exp.numero}</strong></td>
                <td>${exp.titular}</td>
                <td><span class="badge badge-${exp.estado_class}">${exp.estado}</span></td>
                <td>
                    <button class="btn btn-sm btn-primary" 
                            onclick="window.location.href='/expedientes/${exp.id}'">
                        Ver
                    </button>
                </td>
            </tr>
        `;
    }
    
    showLoader() {
        if (this.loadingIndicator) {
            this.loadingIndicator.style.display = 'flex';
        }
    }
    
    hideLoader() {
        if (this.loadingIndicator) {
            this.loadingIndicator.style.display = 'none';
        }
    }
    
    showEndMessage() {
        // Opcional: mostrar mensaje "No hay más expedientes"
        console.log('No hay más expedientes');
    }
    
    showError() {
        alert('Error cargando más expedientes. Inténtalo de nuevo.');
    }
}

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    // Solo inicializar si existe el contenedor
    if (document.getElementById('scroll-container')) {
        new ScrollInfinito({
            containerId: 'scroll-container',
            tbody: '.expedientes-table tbody',
            apiUrl: '/api/expedientes',
            limit: 50,
            threshold: 0.8
        });
    }
});
```

### **3. Template HTML**

```html
<!-- En el template (listado.html) -->
<script src="{{ url_for('static', filename='js/v2-scroll-infinito.js') }}"></script>
```

### **4. CSS para Loading Indicator**

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
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
```

---

## 📊 Performance

### **Benchmarks Esperados**

| Registros | Estrategia | DOM Nodes | Tiempo Carga | Memoria |
|-----------|------------|-----------|--------------|----------|
| 1,000 | Opción C | 200-400 | 1-2s | ~10MB |
| 10,000 | Opción C | 1,000-2,000 | 5-10s | ~50MB |
| 100,000 | Opción D | 20-30 | 1-2s | ~20MB |

### **Optimizaciones**

1. **Debounce en scroll** (opcional):
```javascript
handleScroll() {
    clearTimeout(this.scrollTimeout);
    this.scrollTimeout = setTimeout(() => {
        // Lógica de scroll...
    }, 200);
}
```

2. **Cursor por ID** (más rápido que OFFSET):
```python
# OFFSET/LIMIT es lento con muchos registros
# Cursor por ID es más rápido
query.filter(Expediente.id > cursor).limit(50)
```

3. **Índices en BD**:
```sql
CREATE INDEX idx_expedientes_id ON expedientes(id);
CREATE INDEX idx_expedientes_estado ON expedientes(estado);
```

---

## ✅ Testing

### **Casos de Prueba**

1. **Scroll hasta el final**: Verificar que se cargan todos los items
2. **Scroll rápido**: No debe lanzar múltiples peticiones simultáneas
3. **Error de red**: Debe mostrar error y permitir reintentar
4. **Sin más resultados**: Debe dejar de intentar cargar
5. **Filtros aplicados**: Scroll infinito debe respetar filtros
6. **Responsive mobile**: Scroll debe funcionar igual en mobile
7. **Sticky header**: Header de tabla debe permanecer visible

### **Testing Manual**

```bash
# 1. Crear muchos expedientes de prueba (>100)
flask shell
>>> from app.utils.seed_data import create_test_expedientes
>>> create_test_expedientes(200)

# 2. Abrir navegador y probar scroll
# 3. Monitorizar Network tab (deben aparecer peticiones AJAX)
# 4. Verificar que contador se actualiza
# 5. Verificar que filtros permanecen visibles (C.1)
```

---

## ✅ Checklist Implementación

### Prerequisitos (Fase 1.5) ✅
- [x] Estructura C.1/C.2 implementada
- [x] CSS `.lista-cabecera` y `.lista-scroll-container`
- [x] `.app-main` con `overflow: hidden`
- [x] Sticky header en tabla

### Fase 2 (pendiente)
- [ ] Crear API `/api/expedientes` con cursor
- [ ] Implementar `v2-scroll-infinito.js`
- [ ] Añadir loader/spinner al final de tabla
- [ ] Mensaje "No hay más expedientes"
- [ ] Manejo de errores
- [ ] Testing con 10,000+ registros
- [ ] Documentar en CSS_v2_GUIA_USO.md

---

## 🔗 Referencias

- **CSS_v2_GUIA_USO.md**: Estructura de layout C.1/C.2/D (prerequisito)
- **ISSUE_94_ESTRUCTURA.md**: Roadmap UI v2
- [TanStack Virtual](https://tanstack.com/virtual/latest) (Opción B/D)
- [Intersection Observer API](https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API) (alternativa futura)
- [Issue #94](https://github.com/genete/bddat/issues/94)

---

**Última actualización:** 2026-02-08  
**Estado:** 📝 Documentado (Fase 1.5 prerequisitos completados, Fase 2 pendiente)  
**Versión:** 2.0 (fusión de docs/ y docs/fuentesIA/)