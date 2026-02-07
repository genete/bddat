# Guía de Uso - CSS v2 (Modular)

**Issue:** #94 (Fase 1)  
**Epic:** #93  
**Fecha:** 2026-02-07

---

## 📚 Índice

1. [Introducción](#introducción)
2. [Estructura de Archivos](#estructura-de-archivos)
3. [Cómo Usar](#cómo-usar)
4. [Clases Principales](#clases-principales)
5. [Patrones Comunes](#patrones-comunes)
6. [Responsive](#responsive)
7. [Notas Importantes](#notas-importantes)

---

## 🎯 Introducción

El **CSS v2** es un sistema modular de estilos para BDDAT que reemplaza el CSS monolítico anterior. Está diseñado para:

- ✅ **Mantenibilidad:** Archivos pequeños y especializados
- ✅ **Reutilización:** Componentes independientes
- ✅ **Escalabilidad:** Fácil de extender
- ✅ **Colores corporativos:** Junta de Andalucía (#58)

---

## 📂 Estructura de Archivos

```
app/static/css/
├── v2-theme.css         # Variables CSS (colores, spacing, etc.)
├── v2-layout.css        # Grid principal (header/main/footer)
└── v2-components.css    # Componentes (tabla, badges, botones, filtros)
```

### **Orden de Carga (IMPORTANTE)**

```html
<!-- 1. Variables primero -->
<link rel="stylesheet" href="app/static/css/v2-theme.css">
<!-- 2. Layout segundo -->
<link rel="stylesheet" href="app/static/css/v2-layout.css">
<!-- 3. Componentes tercero -->
<link rel="stylesheet" href="app/static/css/v2-components.css">
```

---

## 🛠️ Cómo Usar

### **Estructura HTML Básica**

```html
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
        <!-- Contenido aquí -->
    </main>
    
    <!-- Footer fijo bottom -->
    <footer class="app-footer">
        <div>© 2026 Junta de Andalucía</div>
    </footer>
</div>
```

---

## 🏛️ Clases Principales

### **Layout (v2-layout.css)**

| Clase | Uso |
|-------|-----|
| `.app-container` | Contenedor principal (grid header/main/footer) |
| `.app-header` | Cabecera fija top (sticky) |
| `.app-main` | Contenido principal (scrollable) |
| `.app-footer` | Pie fijo bottom (sticky) |
| `.content-constrained` | **NUEVO:** Añade márgenes laterales (2rem) |
| `.page-header` | Título de página + botón acción |
| `.breadcrumb` | Navegación miga de pan |
| `.spacer` | Flex spacer (empuja elementos a la derecha) |

### **Componentes (v2-components.css)**

| Clase | Uso |
|-------|-----|
| `.expedientes-table` | Tabla de expedientes (full-width) |
| `.badge`, `.badge-info/success/warning/danger` | Badges de estado |
| `.btn`, `.btn-primary/secondary/outline/warning/danger` | Botones |
| `.btn-sm` | Botón pequeño |
| `.filters-row` | Contenedor filtros + paginación |
| `.filters` | Grupo de filtros (input + select + btn) |
| `.pagination-info` | Texto paginación |

---

## 📋 Patrones Comunes

### **1. Página de Listado (Tabla Full-Width)**

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

### **3. Badges de Estado**

```html
<span class="badge badge-info">En trámite</span>
<span class="badge badge-success">Resuelto</span>
<span class="badge badge-warning">Incompleto</span>
<span class="badge badge-danger">Vencido</span>
```

---

### **4. Botones**

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

---

## 📝 Notas sobre Mobile

**🚨 Importante:** Esta aplicación está diseñada principalmente para **uso en escritorio** (tramitación administrativa).

**Mobile:**
- ✅ Aceptable para **consulta** de expedientes
- ❌ **NO optimizado** para tramitación completa
- Los iconos de cabecera pueden reducirse en mobile (aceptable)
- Si en el futuro se necesita mejor soporte mobile, se puede refinar

---

## 🔗 Referencias

- **Issue:** [#94](https://github.com/genete/bddat/issues/94)
- **Epic:** [#93](https://github.com/genete/bddat/issues/93)
- **Colores corporativos:** [#58](https://github.com/genete/bddat/issues/58)
- **Test HTML:** `test_v2.html` (raíz del proyecto)

---

## ✅ Checklist de Implementación

Cuando migres una página al CSS v2:

- [ ] Cambiar imports de CSS (v2-theme, v2-layout, v2-components)
- [ ] Envolver contenido en `.app-container`
- [ ] Añadir `.app-header`, `.app-main`, `.app-footer`
- [ ] Usar `.content-constrained` para elementos con margen
- [ ] Dejar tablas/listados fuera de `.content-constrained` (full-width)
- [ ] Añadir `.spacer` en header si es necesario
- [ ] Probar sticky header (scroll)
- [ ] Verificar responsive (desktop, tablet, mobile)

---

**Última actualización:** 2026-02-07  
**Autor:** Carlos López  
**Estado:** ✅ Fase 1 completada