# ADR-014 — Layout único `base_app.html` con slots opcionales para vistas autenticadas

**Estado:** Adoptada
**Fecha:** 2026-05-28
**Issue:** #498

---

## Contexto

El layout actual surgió de forma reactiva durante el desarrollo. Hoy hay cuatro templates base coexistiendo:

- `base_fullwidth.html` — grid 1D (header / main / footer). Usado por dashboard, perfil, demo, errores, wizard, detalles, formularios, admin_plantillas.
- `lista_v2_base.html` — extiende fullwidth añadiendo cabecera de listado + scroll-container con tabla. Usado por listados v2 (entidades, proyectos, expedientes, seguimiento).
- `base_bc.html` — extiende fullwidth para tramitación con breadcrumbs profundos. Usado por las 5 vistas `tramitacion_bc_*`.
- `base_acordeon.html` — huérfano, sin referencias.

Más `base_login.html` para vista no autenticada.

La auditoría UI (fase 1) y el análisis crítico (fase 3) detectaron tres problemas estructurales:

1. **El layout es 1D vertical**. No admite sidebar lateral persistente ni paneles laterales/inferiores. La vista de expediente del revamping necesita un modelo **workbench** (sidebar + main + aside + panel-bottom).
2. **Tres iteraciones fallidas en la vista de tramitación** (acordeón → tabs → breadcrumbs) sintomatizan que un stack vertical no comunica la jerarquía completa del expediente.
3. **El header acumula funciones** (logo + módulos horizontales + breadcrumb + usuario + hamburguesa). Con el sidebar persistente decidido en la fase 3, varias funciones del header pasan al sidebar o a un patrón distinto.

---

## Decisión

### 1. Un único template base para vistas autenticadas

Se consolida `base_app.html` como **único template base** para todas las vistas autenticadas. Sustituye a `base_fullwidth.html`, `lista_v2_base.html`, `base_bc.html` y `base_acordeon.html`.

`base_login.html` se mantiene como template separado para la vista no autenticada (login + selección de rol).

### 2. Estructura del layout `base_app.html`

Grid CSS 2D con áreas nombradas. Cinco zonas, dos de ellas opcionales:

```
┌─────────────────────────────────────────────────────────────────────┐
│ HEADER (56px) — siempre                                             │
├──────────┬──────────────────────────────────────────┬───────────────┤
│ SIDEBAR  │ MAIN (1fr)                               │ ASIDE         │
│ (60/240) │   ├─ main_header (opcional, sticky)      │ (380px,       │
│ siempre  │   └─ content                             │  opcional)    │
│          ├──────────────────────────────────────────┴───────────────┤
│          │ PANEL-BOTTOM (240px, opcional)                           │
├──────────┴──────────────────────────────────────────────────────────┤
│ FOOTER — siempre                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

- **Header, sidebar, main y footer**: siempre presentes.
- **Aside derecho y panel inferior**: opcionales. Solo se renderizan si la vista define los bloques Jinja correspondientes; si no, el CSS Grid colapsa esas áreas a `0fr`.

### 3. Slots Jinja

`base_app.html` expone estos bloques principales:

| Bloque | Obligatorio | Propósito |
|---|---|---|
| `title` | sí | Título de la pestaña del navegador |
| `main_header` | no | Cabecera contextual sticky dentro del main (título de página, acciones, tabs) |
| `content` | sí | Contenido principal |
| `aside_right` | no | Panel lateral derecho (pool documentos, detalle nodo, etc.) |
| `panel_bottom` | no | Panel inferior (bitácora, alertas, plazos vivos) |
| `aside_state` | no | `"open"` / `"closed"` — estado inicial del aside |
| `panel_state` | no | `"open"` / `"closed"` — estado inicial del panel |
| `extra_css` / `extra_js` | no | Recursos adicionales por vista |

Vistas tipo "página" (listado, formulario, detalle simple) no definen `aside_right` ni `panel_bottom` y main ocupa el 100% del espacio. Vistas tipo "workbench" (expediente) los definen y reciben el grid 2D completo.

### 4. Sidebar persistente con chevron de colapsar/expandir

- **Mismo sidebar para todos los roles** (gracias a ADR-013, permisos blandos).
- Dos estados:
  - **Expandido** (240px): icono + texto. Estado por defecto en pantallas ≥1280px.
  - **Colapsado** (60px): solo icono, tooltip al hover con el texto. Estado por defecto en 900-1280px.
- **Chevron `«` / `»` en la esquina superior del sidebar** alterna entre estados.
- **Estado persistido en `localStorage`** (`bddat.sidebar.collapsed`).
- **Defensiva responsive (<768px)**: sidebar oculto por defecto, hamburguesa reaparece solo en ese breakpoint para abrirlo como overlay. No es objetivo de uso real (BDDAT es desktop-first) pero el CSS lo cubre por higiene.

### 5. Header simplificado

El header pasa a tener **cuatro elementos**:

```
[⚡ BDDAT]  [🔍 Buscar (Ctrl+K)____________]  [🔔]  [Carlos · TRAMITADOR ▾]
```

- **Marca** (logo + nombre): enlace a dashboard.
- **Búsqueda global** (Ctrl+K): command palette — operación primaria de localización (decisión 5.5 fase 3, varita mágica de fase 2).
- **Notificaciones** (icono campana): placeholder por ahora; futuro para alertas del motor, plazos vencidos, etc.
- **Menú usuario**: nombre + badge de rol activo + dropdown (cambiar rol, perfil, logout).

Elementos retirados del header:
- **Module-nav horizontal** → se mueve al sidebar.
- **Breadcrumb fijo** → desaparece. La navegación entre áreas la da el sidebar; el contexto intra-vista lo da `main_header` (sticky en main).
- **Hamburguesa** → se elimina del header. El sidebar tiene su propio chevron de colapsar. Solo reaparece en <768px como defensiva.
- **Indicador de bombilla** (asignación expediente, ADR-012) → se mueve al `main_header` de las vistas de expediente, donde es relevante.

### 6. Migración de vistas existentes

| Vista actual | Migra a |
|---|---|
| `base_fullwidth.html` | renombrado / sustituido por `base_app.html` |
| `lista_v2_base.html` | mantenido como mixin opcional o absorbido en `base_app.html` (decidir en implementación) |
| `base_bc.html` | eliminado — sustituido por una única vista de expediente que usa `base_app.html` con `aside_right` y `panel_bottom` definidos |
| `base_acordeon.html` | eliminado (huérfano confirmado) |
| `base_login.html` | sin cambios — sigue siendo template separado para vista no autenticada |

---

## Por qué

- **Coherencia visual total**: header y sidebar son los mismos píxeles en todas las vistas, no copias en templates separados. Cambiar el header se hace una vez.
- **Una sola superficie de mantenimiento**: un único CSS Grid, un único template raíz.
- **Workbench como patrón, no como template**: la vista de expediente es `base_app.html` con todos los slots activos. Si en el futuro la vista del administrativo necesita un patrón similar, se materializa sin nuevo template.
- **Sidebar persistente decidido de facto**: cierra la decisión 5.4 del análisis crítico fase 3.
- **Header simplificado** elimina la deuda acumulada (module-nav + breadcrumb + hamburguesa) en un solo movimiento.
- **Cierre de los tres intentos fallidos** (acordeón / tabs / BC) para la vista de tramitación: el slot `aside_right` y el `panel_bottom` dan espacio para mostrar el árbol del expediente + detalle simultáneamente, que es lo que las tres iteraciones intentaron sin conseguirlo en un layout 1D.

---

## Cómo implementar

1. **CSS Grid con `grid-template-areas`** en `app/static/css/v2-layout.css` (sustituyendo el grid actual). Áreas: `header`, `sidebar`, `main`, `aside`, `panel`, `footer`. Columnas y filas se adaptan según los `data-aside` y `data-panel` del shell.
2. **Construir `app/templates/layout/base_app.html`** con la estructura descrita. Incluir partials `layout/_header.html` (nuevo, simplificado), `layout/_sidebar.html` (nuevo), `layout/_footer.html` (existente, conservar).
3. **Sidebar con metadata**: el sidebar se genera desde `app/metadata.json` (mismo origen que el `module_nav` actual). Cada entrada lleva icono Bootstrap Icons + label + ruta + condición opcional de visibilidad (que tras ADR-013 será casi siempre `True`).
4. **JS mínimo para colapsar/expandir** sidebar y paneles. Estado en `localStorage`. ~30 líneas vanilla.
5. **Migrar templates existentes** uno por uno: cambiar `extends 'layout/base_fullwidth.html'` → `extends 'layout/base_app.html'`. Verificar visualmente con Playwright MCP.
6. **Eliminar templates huérfanos** (`base_acordeon.html`, `_header.html` huérfano).
7. **Las 5 vistas `tramitacion_bc_*` y `base_bc.html` se eliminan** como parte de la decisión de árbol del expediente (decisión 5.2, ADR posterior).
8. **Test pytest mínimo**: smoke test que verifica que `/`, `/expedientes/`, `/entidades/`, `/admin/plantillas` renderizan con HTTP 200 y contienen el shell `base_app`.

---

## Alternativa descartada

### A. Dos templates separados (`base_pagina` + `base_workbench`)

Considerada y descartada en la conversación de diseño (fase 3 / discusión de layout): los dos templates comparten el 80% de estructura (header + sidebar + footer + grid base). Tenerlos separados duplica CSS, lógica de sidebar y patrones responsive, con riesgo de divergencia visual y doble lugar para cualquier cambio.

Un único template con dos slots opcionales (aside, panel) cubre los dos patrones de uso con menos código y mejor coherencia.

### B. Mantener el layout 1D actual y resolver tramitación con tabs/secciones

Probado durante el desarrollo previo (acordeón → tabs → breadcrumbs). Los tres intentos fallaron por la misma razón: un layout 1D no comunica la jerarquía completa del expediente. Descartado por evidencia operativa.

### C. Layout unificado con N slots configurables (versión amplia de la opción adoptada)

Considerada. Descartada porque con N>2 slots opcionales el coste de scaffolding y la complejidad CSS crecen sin caso de uso real. Si en el futuro aparece la necesidad de un tercer slot (split vertical en main, por ejemplo), se evalúa entonces.
