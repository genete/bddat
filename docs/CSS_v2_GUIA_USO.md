# Guía de Uso - CSS v2 (Modular)

**Issue:** #94 (Fase 1 y Fase 1.5)  
**Epic:** #93  
**Fecha:** 2026-02-08  
**Versión:** 2.0 (fusionada)

---

## 📚 Índice

1. [Introducción](#introducción)
2. [Estructura de Archivos](#estructura-de-archivos)
3. [Arquitectura de Layout](#arquitectura-de-layout)
4. [Cómo Usar](#cómo-usar)
5. [Clases Principales](#clases-principales)
6. [Patrones Comunes](#patrones-comunes)
7. [Patrón C.1/C.2/D (Scroll Independiente)](#patrón-c1c2d-scroll-independiente)
8. [Componentes](#componentes)
9. [Responsive](#responsive)
10. [Notas Importantes](#notas-importantes)
11. [Referencias](#referencias)

---

## 🎯 Introducción

El **CSS v2** es un sistema modular de estilos para BDDAT que reemplaza el CSS monolítico anterior. Está diseñado para:

- ✅ **Mantenibilidad:** Archivos pequeños y especializados
- ✅ **Reutilización:** Componentes independientes
- ✅ **Escalabilidad:** Fácil de extender
- ✅ **Colores corporativos:** Junta de Andalucía (#58)
- ✅ **Scroll independiente:** Preparado para listas largas y scroll infinito

---

## 📂 Estructura de Archivos

```
app/static/css/
├── v2-theme.css         # Variables CSS (colores, spacing, tipografía)
├── v2-layout.css        # Grid principal (header/main/footer)
└── v2-components.css    # Componentes (tabla, badges, botones, filtros)
```

### **Orden de Carga (IMPORTANTE)**

```html
<!-- 1. Variables primero -->
<link rel="stylesheet" href="/static/css/v2-theme.css">
<!-- 2. Layout segundo -->
<link rel="stylesheet" href="/static/css/v2-layout.css">
<!-- 3. Componentes tercero -->
<link rel="stylesheet" href="/static/css/v2-components.css">
```

---

## 🏛️ Arquitectura de Layout

### Jerarquía de Layout (A → B → C)

```
A: app-container (grid 100vh)
├── B.1: app-header (sticky top)
├── B.2: app-main (flexbox vertical, overflow:hidden)
│   ├── C.1: lista-cabecera (flex-shrink:0, sin scroll)
│   │   ├── page-header (título + botón)
│   │   └── filters-row (filtros + paginación)
│   └── C.2: lista-scroll-container (flex:1, overflow-y:auto)
│       └── D: expedientes-table (crece verticalmente)
│           ├── thead (sticky respecto a C.2)
│           └── tbody
└── B.3: app-footer (sticky bottom)
```

**Clave:** `.app-main` usa `display: flex; flex-direction: column; overflow: hidden` para permitir scroll independiente en C.2.

### Ventajas de C.1/C.2/D (Fase 1.5)

- ✅ **Scroll aislado** solo en C.2 (no afecta a B.1, B.3, ni C.1)
- ✅ **Cabecera de tabla sticky** funcional dentro de C.2
- ✅ **Reutilizable** en Vista 3 (árbol lateral + detalle)
- ✅ **Preparado para scroll infinito** (observar solo C.2)
- ✅ **UX mejorada:** filtros/título siempre visibles

---

## 🛠️ Cómo Usar

### **Estructura HTML Básica**

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BDDAT</title>
    
    <!-- CSS v2 -->
    <link rel="stylesheet" href="/static/css/v2-theme.css">
    <link rel="stylesheet" href="/static/css/v2-layout.css">
    <link rel="stylesheet" href="/static/css/v2-components.css">
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
</head>
<body>
    <div class="app-container">
        <!-- Header fijo top -->
        <header class="app-header">
            <a href="#" class="logo">
                <i class="fas fa-bolt"></i> BDDAT
            </a>
            <nav class="breadcrumb">
                <a href="#">Inicio</a>
                <span>/</span>
                <span>Expedientes</span>
            </nav>
            <div class="spacer"></div> <!-- Empuja user-menu a la derecha -->
            <div class="user-menu">
                <span>👤 Admin</span>
                <a href="#"><i class="fas fa-sign-out-alt"></i> Salir</a>
            </div>
        </header>
        
        <!-- Main content scrollable -->
        <main class="app-main">
            <!-- Contenido aquí (ver patrones) -->
        </main>
        
        <!-- Footer fijo bottom -->
        <footer class="app-footer">
            <div>© 2026 Junta de Andalucía - BDDAT</div>
            <div>
                <a href="#">Ayuda</a> · <a href="#">Contacto</a>
            </div>
        </footer>
    </div>
</body>
</html>
```

---

## 🏛️ Clases Principales

### **Layout (v2-layout.css)**

| Clase | Uso |
|-------|-----|
| `.app-container` | Contenedor principal (grid header/main/footer) |
| `.app-header` | Cabecera fija top (sticky) |
| `.app-main` | Contenido principal (flexbox, overflow:hidden) |
| `.app-footer` | Pie fijo bottom (sticky) |
| `.content-constrained` | **NUEVO:** Añade márgenes laterales (2rem) |
| `.page-header` | Título de página + botón acción |
| `.breadcrumb` | Navegación miga de pan |
| `.spacer` | Flex spacer (empuja elementos a la derecha) |

### **Componentes (v2-components.css)**

| Clase | Uso |
|-------|-----|
| `.lista-cabecera` | **Fase 1.5:** Super-cabecera sin scroll (C.1) |
| `.lista-scroll-container` | **Fase 1.5:** Contenedor con scroll propio (C.2) |
| `.expedientes-table` | Tabla de expedientes (full-width) |
| `.badge`, `.badge-info/success/warning/danger` | Badges de estado |
| `.btn`, `.btn-primary/secondary/outline/warning/danger` | Botones |
| `.btn-sm` | Botón pequeño |
| `.filters-row` | Contenedor filtros + paginación |
| `.filters` | Grupo de filtros (input + select + btn) |
| `.pagination-info` | Texto paginación |

---

## 📋 Patrones Comunes

### **1. Página de Listado Simple (Tabla Full-Width, sin C.1/C.2)**

**Usar cuando:**
- Lista corta (<50 items)
- NO necesitas scroll infinito
- Contenido completo cabe en pantalla

```html
<main class="app-main">
    <!-- Page header CON margen -->
    <div class="page-header content-constrained">
        <h1><i class="fas fa-folder-open"></i> Expedientes</h1>
        <button class="btn btn-primary">
            <i class="fas fa-plus"></i> Nuevo Expediente
        </button>
    </div>
    
    <!-- Filtros + Paginación CON margen -->
    <div class="filters-row content-constrained">
        <div class="filters">
            <input type="search" placeholder="Buscar...">
            <select>
                <option>Estado: Todos</option>
            </select>
            <button class="btn btn-outline">
                <i class="fas fa-filter"></i> Filtrar
            </button>
        </div>
        <div class="pagination-info">
            Mostrando <span>1-40</span> de <span>156</span> expedientes
        </div>
    </div>
    
    <!-- Tabla SIN margen (full-width) -->
    <table class="expedientes-table">
        <thead>
            <tr>
                <th>N° Expediente</th>
                <th>Titular</th>
                <th>Estado</th>
                <th>Acciones</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>EXP-2026-001</strong></td>
                <td>Endesa Energía S.A.</td>
                <td><span class="badge badge-info">En trámite</span></td>
                <td><button class="btn btn-sm btn-primary">Ver</button></td>
            </tr>
        </tbody>
    </table>
</main>
```

**💡 Clave:** 
- `.content-constrained` en `page-header` y `filters-row` → con márgenes
- Tabla **SIN** `.content-constrained` → full-width
- TH/TD tienen padding lateral que coincide con `.content-constrained`

---

### **2. Página de Formulario (Con Márgenes)**

```html
<main class="app-main">
    <div class="content-constrained">
        <div class="page-header">
            <h1><i class="fas fa-edit"></i> Editar Expediente</h1>
        </div>
        
        <form>
            <!-- Campos del formulario -->
        </form>
    </div>
</main>
```

**💡 Clave:** Todo dentro de `.content-constrained`

---

## 📜 Patrón C.1/C.2/D (Scroll Independiente)

### 🎯 ¿Cuándo usar C.1/C.2/D?

**Usar cuando:**
- ✅ Lista larga (>100 items)
- ✅ Necesitas **scroll infinito**
- ✅ Quieres que **filtros/título NO desaparezcan** al scrollear
- ✅ Necesitas **sticky header en tabla** funcional
- ✅ Vista compleja (ej: Vista 3 con árbol lateral + detalle)

**NO usar cuando:**
- ❌ Lista corta (<50 items)
- ❌ Formularios simples
- ❌ Página de detalle sin scroll especial

---

### Estructura HTML C.1/C.2/D

```html
<main class="app-main">
    
    <!-- C.1: Super-cabecera (fija, sin scroll) -->
    <div class="lista-cabecera">
        <!-- Page Header -->
        <div class="page-header content-constrained">
            <h1><i class="fas fa-folder-open"></i> Expedientes</h1>
            <button class="btn btn-primary">
                <i class="fas fa-plus"></i> Nuevo
            </button>
        </div>
        
        <!-- Filtros + Paginación -->
        <div class="filters-row content-constrained">
            <div class="filters">
                <input type="search" placeholder="Buscar...">
                <select>
                    <option>Estado: Todos</option>
                </select>
                <button class="btn btn-outline">
                    <i class="fas fa-filter"></i> Filtrar
                </button>
            </div>
            <div class="pagination-info">
                Mostrando <span id="current-count">40</span> de <span id="total-count">156</span>
            </div>
        </div>
    </div>
    
    <!-- C.2: Contenedor con scroll -->
    <div class="lista-scroll-container" id="scroll-container">
        <!-- D: Tabla full-width -->
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
                <!-- ... filas ... -->
            </tbody>
        </table>
        
        <!-- Loader (opcional, para scroll infinito) -->
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
  flex-shrink: 0;              /* No se comprime */
  background: var(--gris-especifico);
  padding-bottom: 0;
}

.lista-scroll-container {
  flex: 1;                      /* Ocupa espacio disponible */
  overflow-y: auto;             /* Scroll vertical */
  overflow-x: hidden;
  position: relative;           /* Contexto para sticky */
  background: white;
}

/* Sticky header dentro de C.2 */
.lista-scroll-container .expedientes-table thead th {
  position: sticky;
  top: 0;                       /* Pegado al top de C.2, no al viewport */
  z-index: 10;
}
```

### 💡 Ventajas de C.1/C.2/D

| Aspecto | Sin C.1/C.2 | Con C.1/C.2 |
|---------|-------------|-------------|
| **Scroll** | Todo `.app-main` scrollea | Solo C.2 scrollea |
| **Filtros** | Desaparecen al scrollear | ✅ Siempre visibles |
| **Sticky header** | Relativo a viewport | ✅ Relativo a C.2 (mejor) |
| **Scroll infinito** | Más difícil (`window`) | ✅ Más fácil (`container`) |
| **Vista 3** | No reutilizable | ✅ Reutilizable |

---

## 🧩 Componentes

### 1. Badges de Estado

```html
<span class="badge badge-info">En trámite</span>
<span class="badge badge-success">Resuelto</span>
<span class="badge badge-warning">Incompleto</span>
<span class="badge badge-danger">Vencido</span>
```

---

### 2. Botones

```html
<!-- Primario (acción principal) -->
<button class="btn btn-primary">
    <i class="fas fa-plus"></i> Nuevo
</button>

<!-- Secundario -->
<button class="btn btn-secondary">Cancelar</button>

<!-- Outline -->
<button class="btn btn-outline">
    <i class="fas fa-filter"></i> Filtrar
</button>

<!-- Warning (subsanar) -->
<button class="btn btn-warning">Subsanar</button>

<!-- Danger (urgente) -->
<button class="btn btn-danger">Urgente</button>

<!-- Pequeño -->
<button class="btn btn-sm btn-primary">Ver</button>
```

---

### 3. Filtros + Paginación

```html
<div class="filters-row content-constrained">
    <div class="filters">
        <input type="search" placeholder="Buscar...">
        <select>
            <option>Filtro 1</option>
        </select>
        <button class="btn btn-outline">
            <i class="fas fa-filter"></i> Filtrar
        </button>
    </div>
    <div class="pagination-info">
        Mostrando <span>1-40</span> de <span>156</span>
    </div>
</div>
```

---

## 📱 Responsive

### **Breakpoints**

| Tamaño | Ancho | Comportamiento |
|---------|-------|----------------|
| Desktop | >1200px | Layout completo |
| Tablet | 768-1199px | Oculta columna "Solicitudes" |
| Mobile | <768px | Oculta breadcrumb, columnas "Estado" y "Vencimiento" |

### **Sticky Header**

```css
/* Desktop */
.expedientes-table th {
  position: sticky;
  top: 60px; /* Altura del header */
}

/* Con C.2 (Fase 1.5) */
.lista-scroll-container .expedientes-table th {
  position: sticky;
  top: 0;    /* Relativo a C.2, no al viewport */
}

/* Mobile */
@media (max-width: 767px) {
  .expedientes-table th {
    top: 56px; /* Header mobile más bajo */
  }
}
```

---

## ⚠️ Notas Importantes

### **✅ Hacer**

1. **Usar `.content-constrained` para contenido normal:**
   ```html
   <div class="content-constrained">
     <!-- Contenido con márgenes -->
   </div>
   ```

2. **NO usar `.content-constrained` en tablas full-width:**
   ```html
   <table class="expedientes-table">
     <!-- Tabla de lado a lado -->
   </table>
   ```

3. **Añadir `.spacer` en header para separar zonas:**
   ```html
   <header class="app-header">
     <a class="logo">Logo</a>
     <nav class="breadcrumb">...</nav>
     <div class="spacer"></div> <!-- Empuja a la derecha -->
     <div class="user-menu">...</div>
   </header>
   ```

4. **Mantener orden de carga CSS:**
   - `v2-theme.css` primero (variables)
   - `v2-layout.css` segundo (estructura)
   - `v2-components.css` tercero (componentes)

5. **Usar C.1/C.2 para listas largas:**
   - Mejora UX (filtros siempre visibles)
   - Preparado para scroll infinito
   - Sticky header funcional

### **❌ NO Hacer**

1. **NO añadir padding a `.app-main`:**
   ```css
   /* MAL */
   .app-main { padding: 2rem; }
   
   /* BIEN: usar .content-constrained donde se necesite */
   ```

2. **NO usar `overflow: hidden` en contenedores con sticky:**
   - Bloquea `position: sticky`
   - Ya está comentado en el CSS

3. **NO mezclar estilos inline con clases CSS:**
   ```html
   <!-- MAL -->
   <div class="page-header" style="margin-bottom: 3rem;">
   
   <!-- BIEN -->
   <div class="page-header custom-spacing">
   ```

4. **NO usar C.1/C.2 en formularios simples:**
   - C.1/C.2 es para listas largas con scroll
   - Formularios usan `.content-constrained` directamente

---

## 📝 Notas sobre Mobile

**🚨 Importante:** Esta aplicación está diseñada principalmente para **uso en escritorio** (tramitación administrativa).

**Mobile:**
- ✅ Aceptable para **consulta** de expedientes
- ❌ **NO optimizado** para tramitación completa
- Los iconos de cabecera pueden reducirse en mobile (aceptable)
- Si en el futuro se necesita mejor soporte mobile, se puede refinar

---

## ✅ Checklist de Implementación

Cuando migres una página al CSS v2:

- [ ] Cambiar imports de CSS (v2-theme, v2-layout, v2-components)
- [ ] Envolver contenido en `.app-container`
- [ ] Añadir `.app-header`, `.app-main`, `.app-footer`
- [ ] Decidir: ¿Lista larga? → Usar C.1/C.2. ¿Formulario/corto? → `.content-constrained`
- [ ] Usar `.content-constrained` para elementos con margen
- [ ] Dejar tablas/listados fuera de `.content-constrained` (full-width)
- [ ] Añadir `.spacer` en header si es necesario
- [ ] Probar sticky header (scroll)
- [ ] Verificar responsive (desktop, tablet, mobile)

---

## 🔗 Referencias

- **Issue:** [#94](https://github.com/genete/bddat/issues/94)
- **Epic:** [#93](https://github.com/genete/bddat/issues/93)
- **Colores corporativos:** [#58](https://github.com/genete/bddat/issues/58)
- **Test HTML:** `test_v2.html` (raíz del proyecto)
- **SCROLL_INFINITO.md:** Implementación de scroll infinito (Fase 2)
- **ISSUE_94_ESTRUCTURA.md:** Roadmap completo UI v2

---

**Última actualización:** 2026-02-08  
**Autor:** Carlos López  
**Estado:** ✅ Fase 1 y Fase 1.5 completadas  
**Versión:** 2.0 (fusión de docs/ y docs/fuentesIA/)