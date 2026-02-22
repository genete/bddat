# Fase 3: Frontend Dinámico con Columnas Configurables

## Información General

**Epic:** #93 - Sistema de Navegación UI Modular  
**Fase:** 3 - Preparación Frontend Dinámico  
**Fecha creación:** 08/02/2026  
**Estado:** 📋 Documentada (Pendiente implementación)  

---

## Contexto

### Problema

En **Fase 1 y 2** las columnas de las tablas están **hardcoded** en 3 lugares:
1. **Template HTML** (`<thead>` con columnas fijas)
2. **JavaScript** (`renderRow()` con estructura fija)
3. **API Backend** (serialización con campos fijos)

**Consecuencias:**
- Añadir/quitar columna → modificar 3 archivos
- Reordenar columnas → cambiar HTML + JS
- Personalizar por rol → imposible sin lógica compleja
- Migración a Fase 4 → dolor de cabeza

---

## Estrategia de Evolución

### Comparativa de Enfoques

| Aspecto | Hardcoded (actual) | Fase 3: Python Config | Fase 4: JSON Metadata |
|---------|--------------------|-----------------------|-----------------------|
| **Añadir columna** | 3 archivos (API+HTML+JS) | 1 archivo (config.py) | 1 archivo (metadata.json) |
| **Quitar columna** | 3 archivos | 1 línea en config | 1 línea en JSON |
| **Reordenar** | HTML + JS | Cambiar orden en array | Cambiar orden en JSON |
| **Por rol** | Imposible | Filtrar config por rol | Filtrar metadata por rol |
| **Frontend** | Estático | **Dinámico** ✅ | **Dinámico** ✅ |
| **Testing** | Probar frontend cada vez | Frontend no cambia | Frontend no cambia |
| **Migración Fase 4** | Alto dolor | **Bajo dolor** ✅ | N/A |

### ¿Por qué Fase 3 antes de Fase 4?

#### ✅ **Ventajas de preparar Fase 3:**

1. **Infraestructura lista:** Frontend dinámico se hace una sola vez
2. **Validación temprana:** Descubres qué metadatos necesitas
3. **Flexibilidad inmediata:** Cambias columnas sin tocar frontend
4. **Migración sencilla:** Fase 4 = mover datos Python → JSON
5. **Sin esperas:** No dependes de definir esquema JSON completo

#### ❌ **Desventaja de saltar directo a Fase 4:**

- Defines esquema JSON sin experiencia real → retrabajos
- Frontend rígido + metadata rígido = dolor doble si falla
- No validas que frontend dinámico funciona antes de congelar JSON

---

## Arquitectura Fase 3

### Estructura de Directorios

```
app/
├── modules/                    # ← NUEVO (Fase 3)
│   ├── expedientes/
│   │   ├── __init__.py
│   │   ├── routes.py           # Blueprint expedientes
│   │   ├── columns_config.py   # ← NUEVO! Configuración columnas
│   │   ├── templates/
│   │   │   └── listado_v2.html
│   │   └── static/
│   │       ├── css/
│   │       └── js/
│   │
│   └── solicitudes/            # Ejemplo otro módulo
│       ├── __init__.py
│       ├── routes.py
│       ├── columns_config.py   # ← Config específica solicitudes
│       └── ...
│
├── routes/                     # Rutas actuales (mantener temporalmente)
│   ├── api_expedientes.py      # Se moverá a modules/expedientes/
│   └── ...
│
└── static/
    └── js/
        └── v2-scroll-infinito.js  # Se refactoriza para leer config
```

---

## Implementación Fase 3

### 1. Archivo de Configuración

**`app/modules/expedientes/columns_config.py`**

```python
"""
Configuración de columnas para listado de expedientes.
Fase 3: Columnas configurables desde Python.
Fase 4: Se migrará a metadata.json.
"""

# Definición de columnas del listado
COLUMNS = [
    {
        "key": "numeroat",
        "label": "Nº Expediente",
        "type": "number",
        "sortable": True,
        "width": "120px",
        "align": "center",
        "visible": True,
        "roles": ["TRAMITADOR", "ADMINISTRATIVO", "SUPERVISOR", "ADMIN"]
    },
    {
        "key": "titular",
        "label": "Titular",
        "type": "text",
        "sortable": True,
        "width": "250px",
        "align": "left",
        "visible": True,
        "roles": ["TRAMITADOR", "ADMINISTRATIVO", "SUPERVISOR", "ADMIN"]
    },
    {
        "key": "tipo",
        "label": "Tipo",
        "type": "text",
        "sortable": True,
        "width": "150px",
        "align": "left",
        "visible": True,
        "roles": ["TRAMITADOR", "ADMINISTRATIVO", "SUPERVISOR", "ADMIN"]
    },
    {
        "key": "estado",
        "label": "Estado",
        "type": "badge",
        "sortable": True,
        "width": "120px",
        "align": "center",
        "visible": True,
        "roles": ["TRAMITADOR", "ADMINISTRATIVO", "SUPERVISOR", "ADMIN"]
    },
    {
        "key": "responsable",
        "label": "Responsable",
        "type": "text",
        "sortable": False,
        "width": "180px",
        "align": "left",
        "visible": True,
        "roles": ["SUPERVISOR", "ADMIN"]  # Solo visible para supervisores
    },
    {
        "key": "heredado",
        "label": "Heredado",
        "type": "boolean",
        "sortable": True,
        "width": "100px",
        "align": "center",
        "visible": False,  # Oculta por defecto (usuario puede activar)
        "roles": ["TRAMITADOR", "ADMINISTRATIVO", "SUPERVISOR", "ADMIN"]
    },
    {
        "key": "acciones",
        "label": "Acciones",
        "type": "actions",
        "sortable": False,
        "width": "120px",
        "align": "center",
        "visible": True,
        "roles": ["TRAMITADOR", "ADMINISTRATIVO", "SUPERVISOR", "ADMIN"]
    }
]


def get_columns_for_role(user_roles):
    """
    Filtra columnas según roles del usuario.
    
    Args:
        user_roles (list): Lista de nombres de roles del usuario
        
    Returns:
        list: Columnas visibles para ese rol
    """
    return [
        col for col in COLUMNS
        if any(role in user_roles for role in col['roles'])
    ]


def get_visible_columns(user_roles):
    """
    Devuelve solo columnas visibles por defecto para un rol.
    
    Args:
        user_roles (list): Lista de nombres de roles del usuario
        
    Returns:
        list: Columnas visibles filtradas por rol
    """
    return [
        col for col in get_columns_for_role(user_roles)
        if col['visible']
    ]
```

---

### 2. Endpoint API para Columnas

**`app/modules/expedientes/routes.py`**

```python
"""
Blueprint del módulo Expedientes.
"""

from flask import Blueprint, jsonify, render_template
from flask_login import login_required, current_user
from .columns_config import get_columns_for_role, get_visible_columns

bp = Blueprint('expedientes', __name__, url_prefix='/expedientes')


@bp.route('/columns', methods=['GET'])
@login_required
def get_columns():
    """
    Endpoint que devuelve configuración de columnas según rol del usuario.
    
    Fase 3: Lee desde columns_config.py
    Fase 4: Leerá desde metadata.json
    
    Returns:
        JSON con array de columnas filtradas por rol
    """
    user_roles = [r.nombre for r in current_user.roles]
    
    # Devuelve TODAS las columnas permitidas (incluidas ocultas)
    # El frontend decide cuáles mostrar según preferencias usuario
    columns = get_columns_for_role(user_roles)
    
    return jsonify({
        'columns': columns,
        'total': len(columns)
    })


@bp.route('/columns/visible', methods=['GET'])
@login_required
def get_visible_columns_endpoint():
    """
    Endpoint que devuelve solo columnas visibles por defecto.
    
    Returns:
        JSON con array de columnas visibles
    """
    user_roles = [r.nombre for r in current_user.roles]
    columns = get_visible_columns(user_roles)
    
    return jsonify({
        'columns': columns,
        'total': len(columns)
    })


@bp.route('/listado-v2')
@login_required
def listado_v2():
    """
    Vista principal del listado con scroll infinito.
    """
    return render_template('expedientes/listado_v2.html')
```

---

### 3. Refactorizar JavaScript para Leer Config

**`app/static/js/v2-scroll-infinito.js`** (modificado)

```javascript
/**
 * Clase ScrollInfinito - Versión dinámica (Fase 3)
 * Lee configuración de columnas desde API y genera tabla dinámicamente.
 */
class ScrollInfinito {
    constructor(options) {
        this.apiUrl = options.apiUrl;
        this.columnsUrl = options.columnsUrl || '/expedientes/columns/visible';
        this.limit = options.limit || 50;
        this.threshold = options.threshold || 0.8;
        
        this.columns = [];  // Se cargará desde API
        this.data = [];
        this.loading = false;
        this.hasMore = true;
        this.cursor = null;
    }

    /**
     * Carga configuración de columnas desde API.
     */
    async loadColumns() {
        try {
            const response = await fetch(this.columnsUrl);
            const data = await response.json();
            this.columns = data.columns;
            
            // Generar <thead> dinámicamente
            this.generateTableHeader();
            
        } catch (error) {
            console.error('Error cargando columnas:', error);
        }
    }

    /**
     * Genera <thead> dinámicamente según configuración de columnas.
     */
    generateTableHeader() {
        const thead = document.querySelector('.expedientes-table thead tr');
        thead.innerHTML = '';  // Limpiar thead hardcoded
        
        this.columns.forEach(col => {
            const th = document.createElement('th');
            th.textContent = col.label;
            th.style.width = col.width || 'auto';
            th.style.textAlign = col.align || 'left';
            
            if (col.sortable) {
                th.classList.add('sortable');
                th.dataset.key = col.key;
            }
            
            thead.appendChild(th);
        });
    }

    /**
     * Renderiza una fila de la tabla dinámicamente.
     * Lee configuración de columnas para saber qué campos mostrar.
     */
    renderRow(expediente) {
        const tr = document.createElement('tr');
        tr.dataset.id = expediente.id;
        
        this.columns.forEach(col => {
            const td = document.createElement('td');
            td.style.textAlign = col.align || 'left';
            
            // Renderizado según tipo de columna
            switch (col.type) {
                case 'number':
                    td.textContent = expediente[col.key] || '-';
                    break;
                    
                case 'text':
                    td.textContent = expediente[col.key] || '-';
                    break;
                    
                case 'badge':
                    const badge = document.createElement('span');
                    badge.className = `badge badge-${expediente[col.key + '_class'] || 'secondary'}`;
                    badge.textContent = expediente[col.key] || 'Sin estado';
                    td.appendChild(badge);
                    break;
                    
                case 'boolean':
                    const icon = document.createElement('i');
                    icon.className = expediente[col.key] 
                        ? 'fas fa-check text-success' 
                        : 'fas fa-times text-muted';
                    td.appendChild(icon);
                    break;
                    
                case 'actions':
                    const link = document.createElement('a');
                    link.href = `/expedientes/${expediente.id}`;
                    link.className = 'btn btn-sm btn-outline-primary';
                    link.innerHTML = '<i class="fas fa-eye"></i> Ver';
                    td.appendChild(link);
                    break;
                    
                default:
                    td.textContent = expediente[col.key] || '-';
            }
            
            tr.appendChild(td);
        });
        
        return tr;
    }

    /**
     * Inicializa el scroll infinito.
     * Ahora carga columnas primero, luego datos.
     */
    async init() {
        // 1. Cargar configuración de columnas
        await this.loadColumns();
        
        // 2. Cargar datos iniciales
        await this.loadMore();
        
        // 3. Configurar scroll listener
        this.setupScrollListener();
    }

    // ... resto de métodos (loadMore, setupScrollListener, etc.) igual que antes
}
```

---

### 4. Template HTML Simplificado

**`app/templates/expedientes/listado_v2.html`**

```jinja
{% extends "layout/base_fullwidth.html" %}

{% block title %}Expedientes{% endblock %}

{% block extracss %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/v2-components.css') }}">
{% endblock %}

{% block content %}
<!-- Super-cabecera sin scroll -->
<div class="lista-cabecera">
    <div class="page-header content-constrained">
        <h1><i class="fas fa-folder-open"></i> Expedientes</h1>
        <button class="btn btn-primary" onclick="location.href='{{ url_for('expedientes.nuevo') }}'">
            <i class="fas fa-plus"></i> Nuevo Expediente
        </button>
    </div>

    <div class="filters-row content-constrained">
        <div class="filters">
            <input type="search" id="search-input" placeholder="Buscar expediente o titular...">
            <select id="estado-filter">
                <option value="">Estado: Todos</option>
                <option value="borrador">Borrador</option>
                <option value="tramitacion">Tramitación</option>
                <option value="finalizado">Finalizado</option>
            </select>
            <button class="btn btn-secondary" id="btn-filtrar">Filtrar</button>
            <button class="btn btn-outline-secondary" id="btn-limpiar">Limpiar</button>
        </div>
        <div class="pagination-info">
            Mostrando <span id="items-mostrados">0</span> de <span id="items-total">0</span> expedientes
        </div>
    </div>
</div>

<!-- Tabla scrollable -->
<div class="lista-scroll-container">
    <table class="expedientes-table">
        <thead>
            <tr>
                <!-- Se genera dinámicamente desde JavaScript -->
            </tr>
        </thead>
        <tbody id="expedientes-tbody">
            <!-- Cargado por JS -->
        </tbody>
    </table>
    <button id="tabla-scroll-to-top" style="display: none;">
        <i class="fas fa-chevron-up"></i>
    </button>
</div>
{% endblock %}

{% block extrajs %}
<script src="{{ url_for('static', filename='js/v2-scroll-infinito.js') }}"></script>
<script src="{{ url_for('static', filename='js/v2-tabla-scroll-to-top.js') }}"></script>
<script>
    // Configuración dinámica (lee columnas desde API)
    const scrollInfinito = new ScrollInfinito({
        apiUrl: '{{ url_for('api.listar_expedientes') }}',
        columnsUrl: '{{ url_for('expedientes.get_visible_columns_endpoint') }}',
        limit: 50,
        threshold: 0.8
    });
    
    scrollInfinito.init();
</script>
{% endblock %}
```

**Diferencia clave:** El `<thead>` está vacío. Se genera dinámicamente desde JS tras leer la configuración de columnas.

---

## Migración a Fase 4 (Metadata-Driven)

### Paso 1: Definir Esquema JSON

**`app/modules/expedientes/metadata.json`**

```json
{
  "module": "expedientes",
  "name": "Expedientes",
  "description": "Gestión de expedientes de tramitación",
  "icon": "fa-folder-open",
  
  "navigation": {
    "menu": {
      "label": "Expedientes",
      "order": 1,
      "roles": ["TRAMITADOR", "ADMINISTRATIVO", "SUPERVISOR", "ADMIN"]
    }
  },
  
  "views": {
    "list": {
      "template": "listado_v2.html",
      "title": "Expedientes",
      
      "columns": [
        {
          "key": "numeroat",
          "label": "Nº Expediente",
          "type": "number",
          "sortable": true,
          "width": "120px",
          "align": "center",
          "visible": true,
          "roles": ["TRAMITADOR", "ADMINISTRATIVO", "SUPERVISOR", "ADMIN"]
        },
        {
          "key": "titular",
          "label": "Titular",
          "type": "text",
          "sortable": true,
          "width": "250px",
          "align": "left",
          "visible": true,
          "roles": ["TRAMITADOR", "ADMINISTRATIVO", "SUPERVISOR", "ADMIN"]
        }
      ],
      
      "filters": [
        {"key": "search", "type": "text", "placeholder": "Buscar..."},
        {"key": "estado", "type": "select", "options": ["borrador", "tramitacion", "finalizado"]}
      ],
      
      "actions": [
        {"key": "view", "label": "Ver", "icon": "fa-eye", "url": "/expedientes/{id}"},
        {"key": "edit", "label": "Editar", "icon": "fa-edit", "url": "/expedientes/{id}/editar"}
      ]
    }
  },
  
  "permissions": {
    "view": ["TRAMITADOR", "ADMINISTRATIVO", "SUPERVISOR", "ADMIN"],
    "create": ["TRAMITADOR", "ADMINISTRATIVO", "SUPERVISOR", "ADMIN"],
    "edit": ["TRAMITADOR", "SUPERVISOR", "ADMIN"],
    "delete": ["ADMIN"]
  }
}
```

---

### Paso 2: Parser de Metadata

**`app/core/metadata_parser.py`**

```python
"""
Parser de metadata.json para Fase 4.
Carga y cachea metadata de todos los módulos.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

# Caché global de metadatos
_METADATA_CACHE = {}


def load_module_metadata(module_name: str) -> Dict:
    """
    Carga metadata.json de un módulo.
    
    Args:
        module_name: Nombre del módulo (ej: 'expedientes')
        
    Returns:
        Dict con metadata del módulo
        
    Raises:
        FileNotFoundError: Si no existe metadata.json
    """
    if module_name in _METADATA_CACHE:
        return _METADATA_CACHE[module_name]
    
    metadata_path = Path(f"app/modules/{module_name}/metadata.json")
    
    if not metadata_path.exists():
        raise FileNotFoundError(f"No existe metadata.json para módulo '{module_name}'")
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    _METADATA_CACHE[module_name] = metadata
    return metadata


def get_columns_config(module_name: str, view_name: str = 'list') -> List[Dict]:
    """
    Obtiene configuración de columnas desde metadata.json.
    
    Args:
        module_name: Nombre del módulo
        view_name: Nombre de la vista (default: 'list')
        
    Returns:
        Lista de columnas
    """
    metadata = load_module_metadata(module_name)
    return metadata.get('views', {}).get(view_name, {}).get('columns', [])


def filter_columns_by_role(columns: List[Dict], user_roles: List[str]) -> List[Dict]:
    """
    Filtra columnas según roles del usuario.
    
    Args:
        columns: Lista de columnas
        user_roles: Lista de roles del usuario
        
    Returns:
        Columnas filtradas por rol
    """
    return [
        col for col in columns
        if any(role in user_roles for role in col.get('roles', []))
    ]


def clear_cache():
    """Limpia caché de metadatos (útil en desarrollo)."""
    global _METADATA_CACHE
    _METADATA_CACHE = {}
```

---

### Paso 3: Actualizar Endpoint (Fase 4)

**`app/modules/expedientes/routes.py`** (Fase 4)

```python
"""
Blueprint del módulo Expedientes - Versión Fase 4.
"""

from flask import Blueprint, jsonify, render_template
from flask_login import login_required, current_user
from app.core.metadata_parser import get_columns_config, filter_columns_by_role

bp = Blueprint('expedientes', __name__, url_prefix='/expedientes')


@bp.route('/columns', methods=['GET'])
@login_required
def get_columns():
    """
    Endpoint que devuelve configuración de columnas según rol del usuario.
    
    Fase 4: Lee desde metadata.json (parser)
    
    Returns:
        JSON con array de columnas filtradas por rol
    """
    # Cargar columnas desde metadata.json
    all_columns = get_columns_config('expedientes', 'list')
    
    # Filtrar por roles del usuario
    user_roles = [r.nombre for r in current_user.roles]
    columns = filter_columns_by_role(all_columns, user_roles)
    
    return jsonify({
        'columns': columns,
        'total': len(columns)
    })


@bp.route('/columns/visible', methods=['GET'])
@login_required
def get_visible_columns_endpoint():
    """
    Endpoint que devuelve solo columnas visibles por defecto.
    """
    all_columns = get_columns_config('expedientes', 'list')
    user_roles = [r.nombre for r in current_user.roles]
    
    columns = filter_columns_by_role(all_columns, user_roles)
    visible_columns = [col for col in columns if col.get('visible', True)]
    
    return jsonify({
        'columns': visible_columns,
        'total': len(visible_columns)
    })
```

**Cambio clave:** Ahora lee desde `metadata.json` en lugar de `columns_config.py`.

---

### Paso 4: Frontend NO Cambia

El frontend **YA está preparado** desde Fase 3. No requiere modificaciones:

- ✅ `v2-scroll-infinito.js` → sigue leyendo de `/expedientes/columns`
- ✅ `listado_v2.html` → sigue igual
- ✅ JavaScript genera tabla dinámicamente → funciona igual

**Resultado:** Migración transparente para el frontend.

---

## Ventajas de Este Enfoque

### Para Desarrollo

| Aspecto | Ventaja |
|---------|---------|
| **Iteración rápida** | Cambias 1 línea en config → recarga página |
| **Testing frontend** | Frontend no cambia, solo validas datos |
| **Descubrimiento** | Aprendes qué metadatos necesitas realmente |
| **Sin bloqueos** | No esperas a que se defina esquema JSON completo |

### Para Fase 4

| Aspecto | Ventaja |
|---------|---------|
| **Migración sencilla** | Copiar array Python → JSON |
| **Sin romper nada** | Frontend ya validado, solo cambias backend |
| **Rollback fácil** | Revertir endpoint a leer de Python |
| **Confianza alta** | Ya sabes que funciona antes de JSON |

### Para Producto

| Aspecto | Ventaja |
|---------|---------|
| **Flexibilidad** | Añadir columna = 5 líneas en 1 archivo |
| **Por rol** | Filtrado automático según permisos |
| **Personalización** | Usuario puede ocultar/mostrar columnas (futuro) |
| **Escalabilidad** | Añadir módulo = copiar estructura |

---

## Checklist de Validación

### Fase 3 - Antes de Considerar Completa

- [ ] Estructura `app/modules/{modulo}/` creada
- [ ] Archivo `columns_config.py` con array COLUMNS
- [ ] Endpoint `/api/{modulo}/columns` funcional
- [ ] JavaScript lee config y genera `<thead>` dinámicamente
- [ ] JavaScript renderiza filas según config
- [ ] Filtrado por rol funciona correctamente
- [ ] Añadir columna no requiere tocar frontend
- [ ] Quitar columna no requiere tocar frontend
- [ ] Reordenar columnas funciona solo cambiando config
- [ ] Validado con 2-3 módulos diferentes (expedientes, solicitudes, etc.)

### Fase 4 - Antes de Migrar a JSON

- [ ] Esquema `metadata.json` definido y validado
- [ ] Parser `metadata_parser.py` implementado
- [ ] Caché de metadatos funcional
- [ ] Endpoints actualizados para leer desde JSON
- [ ] Frontend sigue funcionando sin cambios
- [ ] Rollback a Fase 3 funciona (endpoint lee de Python)
- [ ] Documentación actualizada
- [ ] Tests de integración pasan

---

## Referencias Cruzadas

### Documentación Relacionada

- **[ISSUE_94_ESTRUCTURA.md](../ISSUE_94_ESTRUCTURA.md):** Estructura layout V2 y sistema de vistas
- **[VISTA_V1_DASHBOARD.md](../VISTA_V1_DASHBOARD.md):** Referencia a Fase 4 metadata-driven
- **[VISTA_V2_LISTADO.md](../VISTA_V2_LISTADO.md):** Implementación actual con columnas hardcoded
- **[PATRONES_UI.md](./PATRONES_UI.md):** Patrones de diseño UI del sistema

### Issues y PRs

- **Epic #93:** Sistema de Navegación UI Modular
- **Issue #94:** Prototipo Vista Listado V2
- **PR #97:** Vista V2 (Listado) - Columnas hardcoded (Fase 1-2)
- **PR #98:** Vista V1 (Dashboard) - Cards hardcoded (Fase 1)

---

## Historial de Cambios

**08/02/2026 - Documentación Creada:**
- Estrategia Fase 3 documentada
- Arquitectura `app/modules/` diseñada
- Código de ejemplo Python + JavaScript + JSON
- Comparativa hardcoded vs Python config vs JSON metadata
- Checklist de validación Fase 3 y Fase 4
- Referencias cruzadas con documentos existentes
- Listo para implementación cuando proceda

---

## Próximos Pasos

### Inmediato (Fase 1 pendiente)
1. ✅ Vista V0 (Login) → PR #99
2. ⏳ Vista V3 (Tramitación con sidebar acordeón) → Pendiente

### Medio Plazo (Fase 3)
1. Refactorizar a `app/modules/expedientes/`
2. Implementar `columns_config.py`
3. Actualizar JavaScript para leer config
4. Validar con 2-3 módulos más

### Largo Plazo (Fase 4)
1. Definir esquema `metadata.json` completo
2. Implementar parser y caché
3. Migrar columnas Python → JSON
4. Integrar navegación dinámica + breadcrumbs
