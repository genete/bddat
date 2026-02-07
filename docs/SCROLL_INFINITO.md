# Scroll Infinito - Estrategia de Implementación

**Issue:** #94 (Fase 2)  
**Epic:** #93  
**Fecha:** 2026-02-07

---

## 📚 Problema

**Escenario:**
- Base de datos con 10,000+ expedientes
- Imposible cargar todos al inicio (lento, consume memoria)
- Necesidad de scroll infinito (carga progresiva)

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

**Librerías:**
- [TanStack Virtual](https://tanstack.com/virtual/latest) (recomendada)
- [react-window](https://github.com/bvaughn/react-window) (React)

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
// Frontend: app/static/js/v2-scroll-infinito.js
let cursor = 0;
let loading = false;
let hasMore = true;

window.addEventListener('scroll', async () => {
    // Detectar si está cerca del final
    const scrollPosition = window.innerHeight + window.scrollY;
    const threshold = document.body.offsetHeight - 500; // 500px antes del final
    
    if (scrollPosition >= threshold && !loading && hasMore) {
        loading = true;
        
        try {
            const response = await fetch(`/api/expedientes?cursor=${cursor}`);
            const { data, next_cursor, has_more } = await response.json();
            
            // Añadir filas a la tabla
            appendRowsToTable(data);
            
            cursor = next_cursor;
            hasMore = has_more;
            
            if (!has_more) {
                showEndMessage('No hay más expedientes');
            }
        } catch (error) {
            console.error('Error cargando expedientes:', error);
        } finally {
            loading = false;
        }
    }
});

function appendRowsToTable(expedientes) {
    const tbody = document.querySelector('.expedientes-table tbody');
    
    expedientes.forEach(exp => {
        const row = `
            <tr>
                <td><strong>${exp.numero}</strong></td>
                <td>${exp.titular}</td>
                <td><span class="badge badge-${exp.estado_class}">${exp.estado}</span></td>
                <td><button class="btn btn-sm btn-primary">Ver</button></td>
            </tr>
        `;
        tbody.insertAdjacentHTML('beforeend', row);
    });
}
```

**Pros:**
- ✅ Fácil de implementar (Flask + SQLAlchemy)
- ✅ No necesita librería frontend compleja
- ✅ Backend solo envía lo necesario
- ✅ 10,000 registros es manejable (200 cargas de 50)

**Contras:**
- ⚠️ DOM crece con el tiempo (1000 filas = pesado)
- ⚠️ Si usuario scrollea mucho, puede ralentizarse

**Cuándo usar:**
- Hasta 10,000-20,000 registros
- Si no quieres añadir librerías JavaScript

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

---

## 🎯 Recomendación para BDDAT

### **Fase 2: Opción C (Cursor Backend)** 🚀

**Razones:**
1. ✅ 10,000 expedientes es manejable
2. ✅ Implementación simple (Flask + SQLAlchemy)
3. ✅ No requiere librerías complejas
4. ✅ Performance aceptable

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
 */

class ScrollInfinito {
    constructor(options) {
        this.apiUrl = options.apiUrl || '/api/expedientes';
        this.tbody = document.querySelector(options.tbody);
        this.cursor = 0;
        this.loading = false;
        this.hasMore = true;
        this.limit = options.limit || 50;
        this.threshold = options.threshold || 500; // px antes del final
        
        this.init();
    }
    
    init() {
        window.addEventListener('scroll', () => this.handleScroll());
        this.loadMore(); // Carga inicial
    }
    
    handleScroll() {
        const scrollPosition = window.innerHeight + window.scrollY;
        const threshold = document.body.offsetHeight - this.threshold;
        
        if (scrollPosition >= threshold && !this.loading && this.hasMore) {
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
        // Mostrar spinner al final de la tabla
    }
    
    hideLoader() {
        // Ocultar spinner
    }
    
    showEndMessage() {
        // Mostrar "No hay más expedientes"
    }
    
    showError() {
        // Mostrar mensaje de error
    }
}

// Inicializar
document.addEventListener('DOMContentLoaded', () => {
    new ScrollInfinito({
        tbody: '.expedientes-table tbody',
        apiUrl: '/api/expedientes',
        limit: 50,
        threshold: 500
    });
});
```

### **3. Template HTML**

```html
<!-- En el template -->
<script src="{{ url_for('static', filename='js/v2-scroll-infinito.js') }}"></script>
```

---

## 📊 Performance

### **Benchmarks Esperados**

| Registros | Estrategia | DOM Nodes | Tiempo Carga | Memoria |
|-----------|------------|-----------|--------------|----------|
| 10,000 | Opción C | 1,000-2,000 | 5-10s | ~50MB |
| 100,000 | Opción D | 20-30 | 1-2s | ~20MB |

---

## ✅ Checklist Implementación

- [ ] Crear API `/api/expedientes` con cursor
- [ ] Implementar `v2-scroll-infinito.js`
- [ ] Añadir loader/spinner al final de tabla
- [ ] Mensaje "No hay más expedientes"
- [ ] Manejo de errores
- [ ] Testing con 10,000+ registros
- [ ] Documentar en CSS_v2_GUIA_USO.md

---

## 🔗 Referencias

- [TanStack Virtual](https://tanstack.com/virtual/latest)
- [Intersection Observer API](https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API)
- [Issue #94](https://github.com/genete/bddat/issues/94)

---

**Última actualización:** 2026-02-07  
**Estado:** 📄 Documentado (pendiente implementación Fase 2)