# Estudio de Homogeneización UI — BDDAT

**Fecha:** 2026-03-08
**Estado:** Completo — pendiente de crear issues
**Referencia:** Este documento es la fuente de verdad para las tareas de homogeneización.
Cada issue creado debe enlazar aquí.

---

## 0. Vocabulario y Convenciones del Estudio

Para evitar ambigüedades, este estudio usa los siguientes términos:

| Término | Significado |
|---------|-------------|
| **V0, V1, V2, V4** | Tipos de vista definidos en `docs/GUIA_VISTAS_BOOTSTRAP.md` |
| **V3-BC** | Vista de tramitación por breadcrumbs (evolución de V3; no usa acordeón ni tabs) |
| **C.1** | Zona fija superior sin scroll (`lista-cabecera`) |
| **C.2** | Zona scrollable independiente (`lista-scroll-container`) |
| **Listado embebido** | Tabla dentro de una card V4 (ej: documentos en detalle de expediente, direcciones en detalle de entidad). Thead gris claro, hover Bootstrap, card-header verde secundario |
| **Tabla V2** | Tabla con clase `expedientes-table`, thead verde corporativo sticky, scroll infinito JS |
| **Tabla BC** | Tabla generada por `_tabla_hijos.html`, Bootstrap puro `table-hover table-sm`, thead `table-light` |
| **Tabla Pool** | Tabla `#pool-tabla`, `table-layout: fixed`, thead sticky gris con `box-shadow inset` |

### Archivos clave del sistema de estilos

| Archivo | Contenido |
|---------|-----------|
| `app/static/css/v2-theme.css` | Variables CSS `:root` — colores, tipografía, layout |
| `app/static/css/v2-layout.css` | Grid A/B.1/B.2/B.3, header, footer, responsive |
| `app/static/css/v2-components.css` | C.1/C.2, tabla V2, badges, botones, filtros, V4 cards |
| `app/static/css/v3-breadcrumbs.css` | Estilos V3-BC: card nodo, bc-meta, breadcrumb legibilidad |
| `app/static/css/custom.css` | Toasts, override acordeones CDN |
| `app/templates/layout/lista_v2_base.html` | Template base para listados V2 (C.1+C.2+ScrollInfinito) |
| `app/static/js/v2-scroll-infinito.js` | Clase `ScrollInfinito` — acepta `columns` en constructor |
| `app/static/js/v2-filtros.js` | Clase `FiltrosExpedientes` — filtrado con debounce |
| `app/templates/vistas/vista3_bc/_tabla_hijos.html` | Partial de tabla BC con columnas dinámicas Jinja |

---

## 1. Clasificación de Vistas por Tipo

### Vistas que SÍ usan un tipo predefinido

| Template | Tipo | Base | Notas |
|----------|------|------|-------|
| `auth/login_v0.html` | **V0** | `base_login.html` | OK |
| `dashboard/index_v1.html` | **V1** | `base_fullwidth.html` | OK |
| `expedientes/listado_v2.html` | **V2** | `lista_v2_base.html` | C.1+C.2, scroll independiente, ScrollInfinito |
| `entidades/index.html` | **V2** | `lista_v2_base.html` | C.1+C.2, scroll independiente, ScrollInfinito |
| `proyectos/index.html` | **V2** | `lista_v2_base.html` | C.1+C.2, scroll independiente, ScrollInfinito |
| `expedientes/detalle.html` | **V4** | `base_fullwidth.html` | `v4-content` (max-width 1200px), cards V4, contiene **listado embebido** de documentos |
| `entidades/detalle.html` | **V4** | `base_fullwidth.html` | Idem, contiene **dos listados embebidos** (direcciones y autorizaciones) |
| `perfil/index.html` | **V4** | `base_fullwidth.html` | Usa clases V4, max-width col-lg-8 (≈ 1200px efectivo) |
| `expedientes/tramitacion_bc.html` | **V3-BC** | `base_fullwidth.html` | C.1 card expediente + C.2 tabla BC solicitudes. **Tiene `overflow-y:hidden`** |
| `expedientes/tramitacion_bc_solicitud.html` | **V3-BC** | idem | C.1 card solicitud + C.2 tabla BC fases. **NO tiene `overflow-y:hidden`** |
| `expedientes/tramitacion_bc_fase.html` | **V3-BC** | idem | C.1 card fase + C.2 tabla BC trámites. **NO tiene `overflow-y:hidden`** |
| `expedientes/tramitacion_bc_tramite.html` | **V3-BC** | idem | C.1 card trámite + C.2 tabla BC tareas. **NO tiene `overflow-y:hidden`** |
| `expedientes/tramitacion_bc_tarea.html` | **V3-BC** | idem | C.1 card tarea + C.2 card documentos (placeholder). **NO tiene `overflow-y:hidden`** |
| `expedientes/pool_documentos.html` | **Pool** (variante V3-BC) | `base_fullwidth.html` | C.1 card expediente + fichas entrada + C.2 tabla pool. **Tiene `overflow-y:hidden`** |

### Vistas que NO usan ningún tipo predefinido

| Template | Problema | Acción |
|----------|----------|--------|
| **`usuarios/index.html`** | Tabla `table-striped` + thead `table-success`. Sin V2, sin scroll, sin responsive | → Issue en M2 (#168 ya existe) |
| **`usuarios/editar.html`** | Card con `bg-success text-white`. No sigue V4 | → Issue en M2 (#168) |
| **`entidades/nueva.html`** | `max-width: 720px` inline. No es V4 formal | → Menor, incluir en issue de consistencia |
| **`expedientes/wizard_paso1/2/3.html`** | Wizard multi-paso, estilo propio | Valorar si definir tipo V5-Wizard |
| **`expedientes/tramitacion_v3.html`** | Legacy (acordeón/tabs), no se usa | Solo referencia, no tocar |

---

## 2. Inconsistencias en Listados

### 2.A — Listados V2 (expedientes, entidades, proyectos)

**Homogéneo entre ellos:** estructura C.1+C.2, `ScrollInfinito`, buscador, filtros, contador, tabla `expedientes-table`, scroll-to-top.

**Diferencias menores:**

| Aspecto | Expedientes | Entidades | Proyectos |
|---------|-------------|-----------|-----------|
| Botón "Nuevo" | Sí | Sí | **No** |
| Filtrado JS | `FiltrosExpedientes` (clase) | Listeners inline | Listeners inline |
| Debounce | Via clase | `setTimeout` manual | `setTimeout` manual |

**Decisión pendiente:** El debounce automático (entidades/proyectos) da mejor UX que el botón "Filtrar" obligatorio (expedientes). Decidir si `FiltrosListado` genérica soporta ambos modos.

### 2.B — Listados V3-BC (tabla hijos SFTT)

`_tabla_hijos.html` genera tablas **completamente distintas** a V2:

| Aspecto | V2 | V3-BC (tabla hijos) |
|---------|----|--------------------|
| Clase tabla | `expedientes-table` | `table table-hover table-sm` |
| Thead | Verde corporativo, sticky, uppercase | `table-light`, **NO sticky** |
| Columnas | JS `columns` en `ScrollInfinito` | Jinja `columnas` desde Python |
| Indicador estado | No | Icono BI (check/clock/circle) |
| Acciones | `btn-outline-primary` "Ver" | `btn-outline-secondary` "→" |
| Scroll-to-top | Sí | **No** |
| Responsive | Media queries | **No** |

**Nota:** Las columnas de V3-BC son necesarias y correctas. El problema no es qué columnas hay sino **la forma distinta de definirlas** respecto a V2.

### 2.C — Tabla Pool

Variante propia: `table-layout: fixed`, thead sticky gris con `box-shadow inset`, responsive con 5 breakpoints, checkbox de selección.

### 2.D — Tabla Usuarios

La más desalineada: `table-striped`, thead `table-success` (#198754), sin paginación, sin responsive. → Ya cubierta por #168.

### 2.E — Listados embebidos (dentro de V4)

Tablas dentro de cards V4 en detalle de expediente (documentos) y detalle de entidad (direcciones, autorizaciones). Comparten: `table table-sm table-hover`, thead `table-light`, card con `card-header-accent`. **Estéticamente correctos, mantener.**

---

## 3. Inconsistencias de Scroll

| Vista | `.app-main` overflow | C.2 independiente | Resultado |
|-------|---------------------|-------------------|-----------|
| **Listados V2** | `auto` (base) | Sí (C.2 absorbe) | **Correcto** |
| **tramitacion_bc.html** | `hidden` (inline) | Sí | **Correcto** |
| **tramitacion_bc_solicitud** | Sin override → `auto` | C.2 presente pero body hace scroll | **Bug** |
| **tramitacion_bc_fase** | Sin override → `auto` | Idem | **Bug** |
| **tramitacion_bc_tramite** | Sin override → `auto` | Idem | **Bug** |
| **tramitacion_bc_tarea** | Sin override → `auto` | Idem | **Bug** |
| **pool_documentos** | `hidden` (inline) | Sí | **Correcto** |
| **Detalle V4** | `auto` | No C.2 (body scroll) | **Correcto** para V4 |

**Causa:** `tramitacion_bc.html` y `pool_documentos.html` añaden en `<style>`:
```css
.app-main { overflow-y: hidden; }
.bc-view { display: flex; flex-direction: column; flex: 1; min-height: 0; }
```
Las otras cuatro vistas BC (`_solicitud`, `_fase`, `_tramite`, `_tarea`) **no tienen ese override**.

---

## 4. Inconsistencias de Encabezados

| Vista | Encabezado | Estilo |
|-------|-----------|--------|
| **V2** | `.page-header` con `<h1>` + icono + botón. Debajo: `.filters-row` | Completo, homogéneo |
| **V3-BC** | `<h6>` + botón `btn-sm` en flex, dentro de C.2 | Mínimo |
| **Pool** | Card meta expediente en C.1, sin título de listado | El listado arranca directo en C.2 |
| **Usuarios** | `<h2>` + botón en `row col-md-8/col-md-4` | Legacy |

---

## 5. Inconsistencias de Colores y Estilos

### 5.A — Colores hardcoded

| Ubicación | Código | Corrección |
|-----------|--------|------------|
| `usuarios/index.html:29` | `table-success` thead | → clase corporativa o `table-light` |
| `usuarios/index.html:52` | `style="bg: #e6e6e5; color: #54585a"` badges rol | → variable o clase |
| `usuarios/index.html:69` | `style="bg: #00695c"` badge Activo | → `bg-primary` o `bg-success` |
| `usuarios/index.html:101` | `modal-header bg-success text-white` | → `card-header-accent` |
| `usuarios/editar.html:18` | `card-header bg-success text-white` | → `card-header-accent` |
| `v3-breadcrumbs.css:54-62` | `color: #444` hardcoded | → `var(--text-primary)` |
| `pool_documentos.html:59` | `background-color: #f8f9fa` thead | → variable o clase |

### 5.B — `btn-success` fuera de semántica

Botones de "Nuevo" y "Guardar" que usan `btn-success` (`#198754`) en vez de `btn-primary` (`#087021`):
- `usuarios/index.html:19`, `usuarios/editar.html:152`
- `tramitacion_bc_solicitud.html:79` (Guardar edición)
- `tramitacion_bc_fase.html:84`, `_tramite.html:84`, `_tarea.html:89`

### 5.C — Fuentes y tamaños inconsistentes

| Aspecto | Estándar | Excepciones |
|---------|----------|-------------|
| Cabecera página | `.page-header h1` = 1.5rem | Usuarios usa `<h2>` sin `.page-header` |
| Thead V2 | 0.875rem uppercase letter-spacing | Pool: sin uppercase. BC: tamaño BS default |
| Labels formulario | `form-label fw-semibold` (V4) | Usuarios: `form-label` sin `fw-semibold` |

### 5.D — `text-muted` (#bebebe) en textos que deberían ser legibles

Usar `text-secondary` (#6c757d) en su lugar para:
- "Sin roles" (usuarios), "No hay elementos" (_tabla_hijos), "Sin tipo" (detalle exp.), "No hay municipios" (detalle exp.)

---

## 6. Estado de Columnas Dinámicas (Fase 3)

### Situación actual

| Pieza | Estado |
|-------|--------|
| `columns_config.py` | **No existe** |
| `metadata.json` en módulos | Existe pero **solo navegación** (no columnas) |
| Endpoint `/columns` | **No existe** |
| `ScrollInfinito` acepta `columns` | **Sí** (desde v1.2) — el frontend ya es semi-dinámico |
| Definición de columnas | **Hardcoded en 2 sitios**: `{% block thead_cols %}` + JS inline `columns: [...]` |

### Camino propuesto

1. Añadir `views.list.columns` al `metadata.json` de cada módulo
2. La ruta de listado pasa `columns` al template vía contexto Jinja
3. `lista_v2_base.html` genera el `<thead>` desde `columns` (elimina `{% block thead_cols %}`)
4. El JS recibe `columns` inyectado como `JSON` en el template (no endpoint separado)
5. **Resultado:** cambiar columna = editar 1 línea en `metadata.json`

Esto es poco complicado porque el `ScrollInfinito` ya acepta `columns`. El cambio es mover la definición de cada template a `metadata.json` y que el template base lo lea.

### Tablas no-V2

Para `_tabla_hijos.html` (V3-BC) y listados embebidos (V4), el mismo principio puede aplicarse: definir columnas en Python/JSON y que el partial las lea, en vez de hardcodear.

---

## 7. Decisión visual: color del thead V2

**Estado actual:** thead verde corporativo oscuro (#087021) con gradiente blanco — mismo color que el header de la aplicación.

**Feedback del usuario:** demasiado verde, compite con el header. Le gusta:
- La cabecera de página (título negro sobre gradiente): **impactante, mantener**
- Las cards V4 (verde secundario #c4ddca): **elegante, mantener**
- El thead de la tabla BC / pool (gris claro): **más discreto**

**Decisión pendiente:** Probar el thead V2 con un tono más discreto. Opciones:
- A) Gris oscuro (#343a40) con texto blanco (como footer)
- B) Verde secundario (#c4ddca) con texto oscuro (como cards V4)
- C) Gris claro (#f8f9fa) con texto oscuro (como pool/BC)

Esto requiere una **sesión visual** con Playwright para comparar. Crear issue separado.

---

## 8. Decisión visual: cabecera de tramitación BC

**Estado actual:** La card del expediente en `tramitacion_bc.html` usa `card-header-accent` (verde secundario). Visualmente se diluye respecto a la cabecera del listado de expedientes de la que vienes.

**Feedback del usuario:** La cabecera del expediente en tramitación debería **mantener la presencia** del listado V2, con texto coherente con el breadcrumb (ej: "Expediente AT-1 — Tramitación").

**Decisión pendiente:** Crear una variante de cabecera más prominente para el nodo raíz de tramitación. Evaluar en la misma sesión visual del punto 7.

---

## 9. Plan de Issues — Mapeo a Milestones

### Issues a CREAR (nuevos)

| # | Título propuesto | Milestone | Justificación |
|---|-----------------|-----------|---------------|
| A | `[UI] Scroll independiente en vistas V3-BC (solicitud/fase/trámite/tarea)` | **M1** | Bug funcional — la cabecera C.1 se desplaza con el body |
| B | `[UI] Homogeneizar tabla de hijos BC — thead sticky, responsive, encabezado coherente` | **M1** | Tramitación ESFTT incompleta visualmente |
| C | `[STYLE] Eliminar colores hardcoded y btn-success fuera de semántica` | **M1** | Corrección rápida, afecta a usuarios y V3-BC |
| D | `[STYLE] Auditar text-muted en textos legibles → text-secondary` | **M1** | Accesibilidad — textos casi invisibles |
| E | `[UI] Revisar color thead V2 y cabecera tramitación BC (sesión visual)` | **M2** | Decisión de diseño, no bloquea funcionalidad |
| F | `[UI] Columnas dinámicas en metadata.json — Fase 3 frontend` | **M2** | Deuda técnica, prerequisito para escalabilidad |
| G | `[UI] Clase CSS estandarizada para listados embebidos y theads internos` | **M2** | Homogeneización visual |
| H | `[UI] Refactor FiltrosExpedientes → FiltrosListado genérica` | **M2** | Deuda técnica, código duplicado |
| I | `[DOCS] Actualizar GUIA_VISTAS_BOOTSTRAP.md — eliminar V3 acordeón/tabs, documentar V3-BC y listados embebidos` | **M1** | La guía actual está desactualizada y es referencia obligatoria |

### Issues EXISTENTES que cubren parte del alcance

| Issue | Título | Milestone | Relación |
|-------|--------|-----------|----------|
| #168 | [UI] Gestión de usuarios — adaptar a vistas estandarizadas V4 | M2 | Cubre migración usuarios a V2/V4. Los puntos C y D de este estudio se aplican antes como prerequisito |
| #166 | [DOCS] Sistema documental en nivel Tarea (Vista 3 Breadcrumbs) | M1 | La tarea BC necesita scroll correcto (issue A) |

### Orden sugerido de ejecución

```
Fase inmediata (M1 — correcciones):
  I → Actualizar guía (base conceptual para todo lo demás)
  A → Fix scroll V3-BC (bug funcional)
  C → Eliminar btn-success y colores hardcoded (rápido)
  D → text-muted → text-secondary (rápido)
  B → Homogeneizar tabla hijos BC (requiere decisión menor de estilo)

Fase siguiente (M2 — evolución):
  E → Sesión visual thead + cabecera BC (decisión de diseño)
  G → Clase CSS listados embebidos
  F → Columnas dinámicas metadata.json
  H → FiltrosListado genérica
  #168 → Migración completa de Usuarios
```

---

## 10. Archivos que se modificarán (referencia rápida)

### Issue A (scroll V3-BC)
- `app/modules/expedientes/templates/expedientes/tramitacion_bc_solicitud.html`
- `app/modules/expedientes/templates/expedientes/tramitacion_bc_fase.html`
- `app/modules/expedientes/templates/expedientes/tramitacion_bc_tramite.html`
- `app/modules/expedientes/templates/expedientes/tramitacion_bc_tarea.html`

### Issue B (tabla hijos BC)
- `app/templates/vistas/vista3_bc/_tabla_hijos.html`
- `app/static/css/v3-breadcrumbs.css` (o nuevo CSS)

### Issue C (colores hardcoded)
- `app/templates/usuarios/index.html`
- `app/templates/usuarios/editar.html`
- `app/modules/expedientes/templates/expedientes/tramitacion_bc_solicitud.html`
- `app/modules/expedientes/templates/expedientes/tramitacion_bc_fase.html`
- `app/modules/expedientes/templates/expedientes/tramitacion_bc_tramite.html`
- `app/modules/expedientes/templates/expedientes/tramitacion_bc_tarea.html`
- `app/static/css/v3-breadcrumbs.css`

### Issue D (text-muted)
- `app/templates/usuarios/index.html`
- `app/templates/vistas/vista3_bc/_tabla_hijos.html`
- `app/modules/expedientes/templates/expedientes/detalle.html`

### Issue F (columnas dinámicas)
- `app/modules/expedientes/metadata.json`
- `app/modules/entidades/metadata.json`
- `app/modules/proyectos/metadata.json`
- `app/templates/layout/lista_v2_base.html`
- `app/modules/expedientes/templates/expedientes/listado_v2.html`
- `app/modules/entidades/templates/entidades/index.html`
- `app/modules/proyectos/templates/proyectos/index.html`

### Issue I (actualizar guía)
- `docs/GUIA_VISTAS_BOOTSTRAP.md`
