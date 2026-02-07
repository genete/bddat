#!/bin/bash

###############################################################################
# Script de inicialización Issue #94 - Prototipo Vista Listado v2
# Epic #93 - UI Modular
# 
# Uso:
#   chmod +x scripts/init-issue-94.sh
#   ./scripts/init-issue-94.sh
#
# Crea estructura de archivos con TODOs y esqueletos básicos
###############################################################################

set -e  # Salir si hay error

echo "🚀 Inicializando estructura Issue #94..."

# Crear directorios
echo "📁 Creando directorios..."
mkdir -p templates/layout
mkdir -p templates/expedientes
mkdir -p static/css
mkdir -p static/js

# ============================================================================
# 1. CSS: TEMA (VARIABLES)
# ============================================================================
echo "🎨 Creando v2-theme.css..."
cat > static/css/v2-theme.css << 'EOF'
/**
 * v2-theme.css
 * Variables CSS, colores, tipografía para UI v2
 * 
 * Issue: #94 (Fase 1 - Prototipo Vista Listado v2)
 * Epic: #93 (Sistema de Navegación UI Modular)
 * Referencia: #90 (Especificación Patrones UI)
 */

:root {
  /* Layout */
  --max-width: 100%;           /* Sin limitador max-width */
  --content-padding: 2rem;
  --header-height: 60px;
  --footer-height: 50px;
  
  /* Colores principales */
  --primary: #0ea5e9;          /* Sky 500 - Acciones primarias */
  --secondary: #64748b;        /* Slate 500 - Secundario */
  --success: #10b981;          /* Emerald 500 - Resuelto */
  --warning: #f59e0b;          /* Amber 500 - Próximo vencimiento */
  --danger: #ef4444;           /* Red 500 - Vencido */
  --info: #3b82f6;             /* Blue 500 - En trámite */
  
  /* Backgrounds */
  --bg-page: #f8fafc;          /* Slate 50 - Fondo página */
  --bg-card: #ffffff;          /* Blanco - Tablas/cards */
  --bg-header: #1e293b;        /* Slate 800 - Header oscuro */
  --bg-footer: #334155;        /* Slate 700 - Footer */
  
  /* Texto */
  --text-primary: #0f172a;     /* Slate 900 */
  --text-secondary: #475569;   /* Slate 600 */
  --text-inverse: #ffffff;     /* Texto sobre fondos oscuros */
  
  /* Bordes */
  --border-color: #e2e8f0;     /* Slate 200 */
  --border-radius: 0.5rem;
  
  /* Sombras */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
}

/* Tipografía base */
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  font-size: 16px;
  line-height: 1.5;
  color: var(--text-primary);
  background-color: var(--bg-page);
}

h1, h2, h3, h4, h5, h6 {
  font-weight: 600;
  line-height: 1.2;
  margin: 0;
}

/* Resets */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* TODO #94: Añadir más estilos base si es necesario */
EOF

# ============================================================================
# 2. CSS: LAYOUT (GRID)
# ============================================================================
echo "🏗️  Creando v2-layout.css..."
cat > static/css/v2-layout.css << 'EOF'
/**
 * v2-layout.css
 * Grid principal (header/main/footer), responsive
 * 
 * Issue: #94 (Fase 1)
 * Epic: #93
 */

/* TODO #94: Implementar grid principal (Tarea 3) */

/* Grid principal */
.app-container {
  display: grid;
  grid-template-rows: var(--header-height) 1fr var(--footer-height);
  min-height: 100vh;
  width: 100%;
}

/* TODO: Header fijo top */
.app-header {
  /* Implementar según especificación */
}

/* TODO: Main content scrollable */
.app-main {
  /* Implementar según especificación */
}

/* TODO: Footer fijo bottom */
.app-footer {
  /* Implementar según especificación */
}

/* TODO: Responsive breakpoints */
@media (max-width: 768px) {
  /* Mobile */
}

@media (min-width: 769px) and (max-width: 1199px) {
  /* Tablet */
}

@media (min-width: 1200px) {
  /* Desktop */
}
EOF

# ============================================================================
# 3. CSS: COMPONENTES
# ============================================================================
echo "🧩 Creando v2-components.css..."
cat > static/css/v2-components.css << 'EOF'
/**
 * v2-components.css
 * Tabla, badges, botones, filtros
 * 
 * Issue: #94 (Fase 1)
 * Epic: #93
 */

/* TODO #94: Implementar componentes (Tarea 4) */

/* ===== TABLA RESPONSIVE ===== */
.expedientes-table {
  /* TODO: Estilos tabla base */
}

/* ===== BADGES ESTADOS ===== */
.badge {
  /* TODO: Badge base */
}

.badge-info { /* En trámite */ }
.badge-success { /* Resuelto */ }
.badge-warning { /* Incompleto */ }
.badge-danger { /* Vencido */ }

/* ===== BOTONES ===== */
.btn {
  /* TODO: Botón base */
}

.btn-primary { /* Tramitar */ }
.btn-secondary { /* Ver */ }
.btn-outline { /* Exportar */ }
.btn-warning { /* Subsanar */ }
.btn-danger { /* Urgente */ }

/* ===== FILTROS ===== */
/* NOTA: Diseño final con filtros en columnas (comentado en issue) */
/* Implementar versión inicial, refinar después */

.filters {
  /* TODO: Contenedor filtros */
}

/* TODO: Input search global */
/* TODO: Filtros en cabeceras (hover) */
/* TODO: Iconos filtro activo */
EOF

# ============================================================================
# 4. JAVASCRIPT: SCROLL INFINITO
# ============================================================================
echo "📜 Creando v2-scroll-infinito.js..."
cat > static/js/v2-scroll-infinito.js << 'EOF'
/**
 * v2-scroll-infinito.js
 * Simulación de carga automática de registros al scrollear
 * 
 * Issue: #94 (Fase 1 - Tarea 7)
 * Epic: #93
 */

// TODO #94: Implementar detección scroll
// TODO #94: Función loadNextPage()
// TODO #94: Actualizar indicador "Mostrando X-Y de Z"

let currentPage = 1;
const itemsPerPage = 25;
const totalItems = 50;

console.log('[Scroll Infinito] Script cargado - Issue #94');

// TODO: Implementar lógica completa según especificación del issue
EOF

# ============================================================================
# 5. JAVASCRIPT: FILTROS
# ============================================================================
echo "🔍 Creando v2-filtros.js..."
cat > static/js/v2-filtros.js << 'EOF'
/**
 * v2-filtros.js
 * Filtros mock (solo UI, sin backend)
 * 
 * Issue: #94 (Fase 1 - Tarea 8)
 * Epic: #93
 * 
 * NOTA: Diseño final con filtros en cabeceras de columnas (hover)
 * Esta versión inicial puede ser más simple, refinar después.
 */

// TODO #94: Implementar filtro búsqueda global
// TODO #94: Implementar filtros por columna (hover en cabecera)
// TODO #94: Iconos de filtro activo
// TODO #94: Actualizar contador visible

console.log('[Filtros] Script cargado - Issue #94');

document.addEventListener('DOMContentLoaded', () => {
  console.log('[Filtros] DOM listo, inicializando...');
  
  // TODO: Implementar lógica completa
});
EOF

# ============================================================================
# 6. TEMPLATE: LAYOUT BASE
# ============================================================================
echo "🗂️  Creando base_full_width.html..."
cat > templates/layout/base_full_width.html << 'EOF'
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}BDDAT v2{% endblock %}</title>
    
    <!-- CSS v2 (NO tocar styles.css existente) -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/v2-theme.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/v2-layout.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/v2-components.css') }}">
    
    {% block extra_css %}{% endblock %}
</head>
<body>
    <div class="app-container">
        <!-- Header -->
        {% include 'layout/_header.html' %}
        
        <!-- Main Content -->
        <main class="app-main">
            {% block content %}
            <!-- TODO #94: Contenido de vistas heredadas -->
            {% endblock %}
        </main>
        
        <!-- Footer -->
        {% include 'layout/_footer.html' %}
    </div>
    
    <!-- JavaScript v2 -->
    <script src="{{ url_for('static', filename='js/v2-scroll-infinito.js') }}"></script>
    <script src="{{ url_for('static', filename='js/v2-filtros.js') }}"></script>
    
    {% block extra_js %}{% endblock %}
</body>
</html>

<!-- 
TODO #94 (Tarea 5): Implementar layout completo
- Grid principal
- Includes header/footer
- Carga CSS/JS v2
-->
EOF

# ============================================================================
# 7. TEMPLATE: HEADER
# ============================================================================
echo "📌 Creando _header.html..."
cat > templates/layout/_header.html << 'EOF'
<!-- 
_header.html
Header reutilizable para layout v2

Issue: #94 (Fase 1 - Tarea 5)
Epic: #93
-->

<header class="app-header">
    <!-- TODO #94: Implementar header completo -->
    <div>
        <a href="{{ url_for('dashboard.index') if 'dashboard' in url_for.__globals__ else '#' }}" class="logo">
            BDDAT v2
        </a>
        <nav class="breadcrumb">
            <a href="#">Inicio</a>
            <span>›</span>
            {% block breadcrumb %}
            <span>Tramitación</span>
            {% endblock %}
        </nav>
    </div>
    
    <div class="user-menu">
        <span>{{ usuario|default('Usuario') }}</span>
        <a href="#">🔔 <sup>{{ notificaciones|default(0) }}</sup></a>
        <a href="#">Salir</a>
    </div>
</header>

<!-- TODO: Añadir estilos completos en v2-layout.css -->
EOF

# ============================================================================
# 8. TEMPLATE: FOOTER
# ============================================================================
echo "📌 Creando _footer.html..."
cat > templates/layout/_footer.html << 'EOF'
<!-- 
_footer.html
Footer reutilizable para layout v2

Issue: #94 (Fase 1 - Tarea 5)
Epic: #93
-->

<footer class="app-footer">
    <!-- TODO #94: Implementar footer completo -->
    <div>
        📊 {{ total_expedientes|default(0) }} expedientes | 
        Estadísticas mock
    </div>
    <div>
        © 2026 BDDAT v0.3.3
    </div>
</footer>

<!-- TODO: Añadir estilos completos en v2-layout.css -->
EOF

# ============================================================================
# 9. TEMPLATE: VISTA LISTADO V2
# ============================================================================
echo "📋 Creando listado_v2.html..."
cat > templates/expedientes/listado_v2.html << 'EOF'
{% extends "layout/base_full_width.html" %}

{% block title %}Gestión de Expedientes - BDDAT v2{% endblock %}

{% block breadcrumb %}
<span>Tramitación</span>
{% endblock %}

{% block content %}

<!-- TODO #94 (Tarea 6): Implementar vista listado completa -->

<!-- Banner prototipo (temporal) -->
<div style="background: linear-gradient(135deg, #fef3c7 0%, #fed7aa 100%); 
            border-left: 4px solid #f59e0b; 
            padding: 1rem 2rem; 
            margin-bottom: 2rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
  <div style="display: flex; align-items: center; justify-content: space-between;">
    <div>
      <h4 style="margin: 0; color: #92400e; font-weight: 600;">
        🚧 PROTOTIPO UI v2 - Issue #94 (Fase 1)
      </h4>
      <p style="margin: 0.5rem 0 0 0; color: #78350f; font-size: 0.9rem;">
        Datos ficticios. Vista experimental de listado con scroll infinito.
        <a href="https://github.com/genete/bddat/issues/94" 
           style="color: #92400e; text-decoration: underline;">
          Ver Issue #94
        </a>
      </p>
    </div>
    <div style="display: flex; gap: 1rem;">
      <a href="{{ url_for('expedientes.index') }}" class="btn btn-outline">
        Ver Versión Actual
      </a>
      <a href="{{ url_for('dashboard.index') if 'dashboard' in url_for.__globals__ else '#' }}" class="btn btn-secondary">
        ← Dashboard
      </a>
    </div>
  </div>
</div>

<!-- Header página -->
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
  <h1>📂 Gestión de Expedientes</h1>
  <button class="btn btn-primary">+ Nuevo</button>
</div>

<!-- TODO: Implementar filtros según diseño final (filtros en columnas) -->
<!-- TODO: Implementar indicador "Mostrando X-Y de Z" -->
<!-- TODO: Implementar tabla con 50 filas hardcodeadas -->
<!-- TODO: Implementar badges estados -->
<!-- TODO: Implementar botones acciones -->

<p style="color: var(--text-secondary); padding: 2rem; text-align: center; border: 2px dashed var(--border-color); border-radius: 0.5rem;">
  🚧 Contenido en construcción - Issue #94
  <br><br>
  <strong>Tareas pendientes:</strong>
  <br>• Tabla con datos mock (50 expedientes)
  <br>• Filtros (búsqueda global + columnas)
  <br>• Scroll infinito funcional
  <br>• Badges estados (4 tipos)
  <br>• Botones acciones
</p>

{% endblock %}
EOF

# ============================================================================
# 10. README ESTRUCTURA
# ============================================================================
echo "📄 Creando README en docs..."
cat > docs/ISSUE_94_ESTRUCTURA.md << 'EOF'
# Issue #94 - Estructura de Archivos

## Archivos Creados

### CSS v2 (sin tocar existentes)
- `static/css/v2-theme.css` - Variables, colores, tipografía
- `static/css/v2-layout.css` - Grid principal, header, footer
- `static/css/v2-components.css` - Tabla, badges, botones, filtros

### JavaScript v2
- `static/js/v2-scroll-infinito.js` - Carga automática al scrollear
- `static/js/v2-filtros.js` - Filtros mock (UI sin backend)

### Templates v2
- `templates/layout/base_full_width.html` - Layout base 100% ancho
- `templates/layout/_header.html` - Header reutilizable
- `templates/layout/_footer.html` - Footer reutilizable
- `templates/expedientes/listado_v2.html` - Vista listado prototipo

## Próximos Pasos

1. Implementar CSS completo (tareas 2-4 del issue)
2. Implementar templates completos (tarea 5-6)
3. Implementar JavaScript (tareas 7-8)
4. Añadir ruta Flask (tarea 9)
5. Testing y validación (tarea 10)

## Referencias

- [Issue #94](https://github.com/genete/bddat/issues/94)
- [Epic #93](https://github.com/genete/bddat/issues/93)
- [Especificación #90](https://github.com/genete/bddat/issues/90)
- [PATRONES_UI.md](../arquitectura/PATRONES_UI.md)

## Notas de Diseño

**Filtros en Columnas** (cambio respecto a diseño inicial):
- Filtro global (búsqueda texto) fuera de tabla
- Filtros por columna aparecen con hover en cabecera
- Icono mini 🔽 si filtro activo
- Cabecera limpia sin hover (salvo icono filtrado)

Comentar cambios en el issue cuando se llegue a esa implementación.
EOF

echo ""
echo "✅ Estructura creada exitosamente!"
echo ""
echo "📂 Archivos creados:"
echo "   • static/css/v2-theme.css"
echo "   • static/css/v2-layout.css"
echo "   • static/css/v2-components.css"
echo "   • static/js/v2-scroll-infinito.js"
echo "   • static/js/v2-filtros.js"
echo "   • templates/layout/base_full_width.html"
echo "   • templates/layout/_header.html"
echo "   • templates/layout/_footer.html"
echo "   • templates/expedientes/listado_v2.html"
echo "   • docs/ISSUE_94_ESTRUCTURA.md"
echo ""
echo "🚀 Próximo paso:"
echo "   git add ."
echo "   git commit -m \"feat(ui): estructura base Issue #94 - Prototipo Vista Listado v2"
echo ""
echo "   Archivos con TODOs y esqueletos básicos."
echo "   Refs: #94, #93, #90\""
echo ""
echo "📖 Ver detalles en: docs/ISSUE_94_ESTRUCTURA.md"
