# CSS v2 - Guía de Uso

**Proyecto:** BDDAT - Sistema de tramitación administrativa  
**Epic:** #93 (Diseño UI modular v2)  
**Issue relacionado:** #94 (Fase 1)  
**Fecha:** 8 de febrero de 2026  
**Versión:** 1.0

---

## Índice

1. [Introducción](#introducción)
2. [Arquitectura CSS v2](#arquitectura-css-v2)
3. [Estructura HTML Base](#estructura-html-base)
4. [Patrón de Listados con Scroll Independiente](#patrón-de-listados-con-scroll-independiente)
5. [Componentes Disponibles](#componentes-disponibles)
6. [Responsive](#responsive)
7. [Ejemplos de Uso](#ejemplos-de-uso)

---

## Introducción

El **CSS v2** es un sistema de diseño modular creado específicamente para BDDAT siguiendo la identidad corporativa de la Junta de Andalucía.

**Objetivos:**
- Grid principal con header/main/footer fijos
- Componentes reutilizables (tablas, botones, filtros)
- Scroll independiente para listados largos
- Responsive mobile-first
- Mantenibilidad y escalabilidad

**Archivos CSS:**
```
app/static/css/
├── v2-theme.css       # Variables, colores, tipografía
├── v2-layout.css      # Grid principal (A/B/C)
└── v2-components.css  # Tablas, botones, filtros, badges
```

---

## Arquitectura CSS v2

### Separación de Responsabilidades

| Archivo | Responsabilidad |
|---------|----------------|
| `v2-theme.css` | Variables CSS, colores corporativos, tipografía base |
| `v2-layout.css` | Estructura principal (header fijo, main scrollable, footer fijo) |
| `v2-components.css` | Componentes reutilizables (tablas, botones, badges, filtros) |

### Jerarquía de Layout

```
A: app-container (grid 100vh)
├── B: app-header (sticky top)
├── C: app-main (flexbox, overflow:hidden)
│   ├── C.1: lista-cabecera (flex-shrink:0, sin scroll)
│   └── C.2: lista-scroll-container (flex:1, overflow-y:auto)
│       └── D: expedientes-table (full-width)
└── E: app-footer (sticky bottom)
```

**Clave:** `.app-main` usa `display: flex; flex-direction: column; overflow: hidden` para permitir scroll independiente en C.2.

---

## Estructura HTML Base

### Layout Completo

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
    <!-- A: Grid Principal -->
    <div class="app-container">
        
        <!-- B: Header Fijo -->
        <header class="app-header">
            <a href="#" class="logo">
                <i class="fas fa-bolt"></i>
                BDDAT
            </a>
            <nav class="breadcrumb">
                <a href="#">Inicio</a>
                <span>/</span>
                <span>Expedientes</span>
            </nav>
            <div class="spacer"></div>
            <div class="user-menu">
                <span>👤 Usuario</span>
                <a href="#"><i class="fas fa-sign-out-alt"></i> Salir</a>
            </div>
        </header>
        
        <!-- C: Main Content -->
        <main class="app-main">
            <!-- Contenido aquí (ver secciones siguientes) -->
        </main>
        
        <!-- E: Footer Fijo -->
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

## Patrón de Listados con Scroll Independiente

### Estructura C.1/C.2/D

**Problema resuelto:** Scroll independiente para tablas largas sin afectar cabecera/filtros.

**Arquitectura:**

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
                Mostrando <span>1-40</span> de <span>156</span>
            </div>
        </div>
    </div>
    
    <!-- C.2: Contenedor con scroll -->
    <div class="lista-scroll-container">
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
            <tbody>
                <!-- ... filas ... -->
            </tbody>
        </table>
    </div>
    
</main>
```

### Clases CSS Clave

#### `.lista-cabecera` (C.1)

```css
.lista-cabecera {
  flex-shrink: 0;              /* No se comprime */
  background: var(--gris-especifico);
  padding-bottom: 0;
}
```

**Uso:** Contiene page-header y filtros. NO hace scroll.

#### `.lista-scroll-container` (C.2)

```css
.lista-scroll-container {
  flex: 1;                      /* Ocupa espacio disponible */
  overflow-y: auto;             /* Scroll vertical */
  overflow-x: hidden;
  position: relative;           /* Contexto para sticky */
  background: white;
}
```

**Uso:** Contiene la tabla. Hace scroll independiente.

#### Sticky Header en C.2

```css
.lista-scroll-container .expedientes-table thead th {
  position: sticky;
  top: 0;                       /* Pegado al top de C.2, no al viewport */
  z-index: 10;
}
```

**Resultado:** El header de la tabla queda fijo al hacer scroll dentro de C.2.

---

## Componentes Disponibles

### 1. Page Header

```html
<div class="page-header content-constrained">
    <h1>
        <i class="fas fa-folder-open"></i>
        Título de Página
    </h1>
    <button class="btn btn-primary">
        <i class="fas fa-plus"></i>
        Nueva Acción
    </button>
</div>
```

**Clases:**
- `.page-header`: Flexbox space-between
- `.content-constrained`: Añade padding lateral

---

### 2. Filtros + Paginación

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

**Clases:**
- `.filters-row`: Flexbox space-between
- `.filters`: Flexbox con gap
- `.pagination-info`: Texto alineado a la derecha

---

### 3. Tabla Responsive

```html
<table class="expedientes-table">
    <thead>
        <tr>
            <th>Columna 1</th>
            <th>Columna 2</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Dato 1</td>
            <td>Dato 2</td>
        </tr>
    </tbody>
</table>
```

**Características:**
- Full-width (sin margen lateral)
- Sticky header (si está dentro de `.lista-scroll-container`)
- Hover en filas
- Responsive (oculta columnas en mobile)

---

### 4. Botones

```html
<!-- Primario -->
<button class="btn btn-primary">
    <i class="fas fa-save"></i> Guardar
</button>

<!-- Secundario -->
<button class="btn btn-secondary">
    <i class="fas fa-times"></i> Cancelar
</button>

<!-- Outline -->
<button class="btn btn-outline">
    <i class="fas fa-filter"></i> Filtrar
</button>

<!-- Warning -->
<button class="btn btn-warning">
    <i class="fas fa-exclamation-triangle"></i> Subsanar
</button>

<!-- Danger -->
<button class="btn btn-danger">
    <i class="fas fa-trash"></i> Eliminar
</button>

<!-- Pequeño -->
<button class="btn btn-sm btn-primary">Ver</button>
```

**Variantes:**
- `.btn-primary`: Verde corporativo Junta (con gradiente)
- `.btn-secondary`: Gris oscuro
- `.btn-outline`: Borde gris, fondo transparente
- `.btn-warning`: Amarillo (subsanaciones)
- `.btn-danger`: Rojo (acciones críticas)
- `.btn-sm`: Tamaño reducido

---

### 5. Badges (Estados)

```html
<span class="badge badge-info">En trámite</span>
<span class="badge badge-success">Resuelto</span>
<span class="badge badge-warning">Incompleto</span>
<span class="badge badge-danger">Vencido</span>
```

**Variantes:**
- `.badge-info`: Azul (en trámite)
- `.badge-success`: Verde (resuelto)
- `.badge-warning`: Amarillo (incompleto)
- `.badge-danger`: Rojo (vencido)

---

### 6. Scroll to Top (Opcional)

```html
<button id="scroll-to-top" class="scroll-to-top" aria-label="Volver arriba">
    <i class="fas fa-chevron-up"></i>
</button>

<script src="/static/js/v2-scroll-to-top.js"></script>
```

**Nota:** Se muestra automáticamente al hacer scroll.

---

## Responsive

### Breakpoints

| Dispositivo | Ancho | Cambios |
|------------|-------|--------|
| Desktop | >1200px | Layout completo |
| Tablet | 768-1199px | Padding reducido, breadcrumb visible |
| Mobile | <768px | Padding mínimo, breadcrumb oculto, columnas de tabla ocultas |

### Comportamiento Mobile

**Header:**
- Breadcrumb oculto
- Logo reducido (1.25rem)
- User menu compacto

**Tabla:**
- Columnas no críticas ocultas (ver media queries en `v2-components.css`)
- Padding reducido en celdas
- Sticky header ajustado (top: 56px)

**Filtros:**
- Apilados verticalmente
- Inputs full-width

---

## Ejemplos de Uso

### Ejemplo 1: Listado de Expedientes (con scroll)

```html
<main class="app-main">
    <!-- C.1: Cabecera fija -->
    <div class="lista-cabecera">
        <div class="page-header content-constrained">
            <h1><i class="fas fa-folder-open"></i> Expedientes</h1>
            <button class="btn btn-primary">
                <i class="fas fa-plus"></i> Nuevo Expediente
            </button>
        </div>
        
        <div class="filters-row content-constrained">
            <div class="filters">
                <input type="search" placeholder="Buscar expedientes...">
                <select>
                    <option>Estado: Todos</option>
                    <option>En trámite</option>
                    <option>Resuelto</option>
                </select>
                <button class="btn btn-outline">
                    <i class="fas fa-filter"></i> Filtrar
                </button>
            </div>
            <div class="pagination-info">
                Mostrando <span>1-40</span> de <span>156</span>
            </div>
        </div>
    </div>
    
    <!-- C.2: Tabla scrollable -->
    <div class="lista-scroll-container">
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
                    <td>
                        <button class="btn btn-sm btn-primary">Ver</button>
                    </td>
                </tr>
                <!-- ... más filas ... -->
            </tbody>
        </table>
    </div>
</main>
```

---

### Ejemplo 2: Página de Detalle (sin scroll especial)

```html
<main class="app-main">
    <div class="page-header content-constrained">
        <h1><i class="fas fa-file-alt"></i> Detalle Expediente</h1>
        <div>
            <button class="btn btn-outline">
                <i class="fas fa-arrow-left"></i> Volver
            </button>
            <button class="btn btn-primary">
                <i class="fas fa-save"></i> Guardar
            </button>
        </div>
    </div>
    
    <div class="content-constrained" style="margin-top: 2rem;">
        <!-- Contenido del detalle -->
        <div class="card">
            <h2>Información Básica</h2>
            <p><strong>N° Expediente:</strong> EXP-2026-001</p>
            <p><strong>Titular:</strong> Endesa Energía S.A.</p>
            <!-- ... -->
        </div>
    </div>
</main>
```

**Nota:** Sin `.lista-cabecera` ni `.lista-scroll-container`, el scroll es normal en `.app-main`.

---

## Resumen de Clases Principales

| Clase | Propósito |
|-------|----------|
| `.app-container` | Grid principal (header/main/footer) |
| `.app-header` | Header fijo top (sticky) |
| `.app-main` | Main content (flexbox, overflow:hidden) |
| `.app-footer` | Footer fijo bottom (sticky) |
| `.lista-cabecera` | Super-cabecera de listado (sin scroll) |
| `.lista-scroll-container` | Contenedor scrollable para tablas |
| `.expedientes-table` | Tabla responsive full-width |
| `.page-header` | Cabecera de página (título + acción) |
| `.filters-row` | Fila de filtros + paginación |
| `.content-constrained` | Añade padding lateral |
| `.btn` | Botón base |
| `.badge` | Badge/píldora de estado |
| `.scroll-to-top` | Botón flotante volver arriba |

---

## Notas Finales

1. **Prerequisitos para Scroll Infinito:** Si implementas scroll infinito en el futuro, asegúrate de:
   - Usar la estructura C.1/C.2
   - Adjuntar listener de scroll a `.lista-scroll-container` (no a `window`)
   - Calcular threshold basado en `.scrollHeight` de C.2

2. **Mantenimiento:** Cualquier cambio en colores o variables debe hacerse en `v2-theme.css`.

3. **Extensión:** Para nuevos componentes, añádelos a `v2-components.css` con comentarios descriptivos.

4. **Testing:** Probar siempre en:
   - Desktop (>1200px)
   - Tablet (768-1199px)
   - Mobile (<768px)

---

**Fin de la guía.**