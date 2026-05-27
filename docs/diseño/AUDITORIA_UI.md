# Auditoría UI — Fase 1: Inventario

> Inventario crudo y lectura del grafo de navegación. Sin propuestas de cambio.
> Fecha del corte: 2026-05-27 (tag `v0.8.0-pre-frontend`).

---

## 1. Mapa de rutas

### 1.1 Blueprints de UI (5)

| Blueprint | Rutas | Notas |
|---|---|---|
| `auth` | login, logout, cambiar_rol, seleccionar_rol | login_v0 |
| `dashboard` | `/`, `/dashboard`, `/mis_expedientes` (redirect) | index_v1 |
| `perfil` | `/perfil/` | |
| `demo` | `/demo/diagrama` | React POC |
| `entidades` | index + nueva + detalle(modo ver/editar) + 6 acciones POST sobre direcciones/autorizados | |
| `usuarios` | index + detalle(modo ver/editar) + toggle_estado | `require_permiso('gestionar_usuarios')` |
| `proyectos` | index + detalle (redirige a `expedientes.detalle`) + editar_proyecto (redirige a `expedientes.editar#proyecto`) | módulo casi vacío — vive bajo expedientes |
| `expedientes` | listado_v2, seguimiento, detalle(ver/editar), pool_documentos (+ 8 endpoints JSON de pool), tramitación BC (5 niveles), generar_cert, cert_pdf | núcleo |
| `admin_plantillas` | listado, nueva, detalle, editar (form modo nueva/editar), descargar, activar + 5 endpoints JSON | `require_permiso('gestionar_plantillas')` |
| `wizard_expediente` | paso1, paso2, paso3 | flujo lineal |

### 1.2 Blueprints API (7 — solo JSON)

Localizados en `app/routes/` (fuera de `app/modules/`):

| Blueprint | Propósito (según nombre) |
|---|---|
| `api_expedientes` | endpoints del listado v2 y operaciones |
| `api_entidades` | listado v2 + candidatos autorización |
| `api_proyectos` | listado v2 |
| `api_seguimiento` | tabla de seguimiento |
| `api_bc` | navegación breadcrumbs (cruds de fase/trámite/tarea) |
| `api_municipios` | selector municipios |
| `api_escritos` | generación de escritos (probable backend de `generar_escrito.js`) |

### 1.3 Tramitación BC — 5 niveles jerárquicos

```
/expedientes/<id>/tramitacion
  └─ /solicitud/<sol_id>
       └─ /fase/<fase_id>
            └─ /tramite/<tram_id>
                 └─ /tarea/<tarea_id>
```

Cada nivel = un template propio (`tramitacion_bc.html`, `_solicitud.html`, `_fase.html`, `_tramite.html`, `_tarea.html`).

---

## 2. Templates — herencia

### 2.1 Layouts base

| Layout | Padre | Uso | Estado |
|---|---|---|---|
| `layout/base_login.html` | raíz | login, seleccionar_rol | vivo |
| `layout/base_fullwidth.html` | raíz | dashboard, perfil, demo, errores, wizard, detalles, formularios, admin_plantillas | vivo (base estándar) |
| `layout/lista_v2_base.html` | `base_fullwidth` | listados v2 (entidades, proyectos, expedientes, seguimiento) | vivo |
| `layout/base_bc.html` | `base_fullwidth` | tramitación BC (5 templates) | vivo |
| `layout/base_acordeon.html` | raíz | — | **huérfano** |

### 2.2 Templates por módulo

Resumen — la tabla detallada se omite por extensión. 40 templates total: 21 globales (layouts, auth, dashboard, demo, perfil, errors, wizard, vistas) + 19 en módulos (entidades 3, usuarios 2, proyectos 1, expedientes 6, admin_plantillas 4).

**Patrón "template dual" — un template sirve dos rutas (ver/editar o nueva/editar):**
- `entidades/detalle.html` → `/<id>` y `/<id>/editar` (modo)
- `usuarios/detalle.html` → idem
- `expedientes/detalle.html` → idem
- `admin_plantillas/form.html` → `/nueva` y `/<id>/editar` (modo)

**Inconsistencia detectada:** `entidades/nueva.html` es un fichero **independiente** del detalle. En el resto de módulos, "nueva" o no existe o se canaliza por wizard. Para entidades hay tres caminos distintos a "alta": template propio, modo en detalle, etc. → revisar coherencia.

---

## 3. Componentes reutilizables

### 3.1 Macros Jinja (2)

| Macro | Fichero | Usos |
|---|---|---|
| `page_header(title, icon, accent)` | `macros/page_header.html` | base_bc, 3 detalles, pool_documentos |
| `bc_card_compacto(icon, label, url)` | `macros/bc_cards.html` | base_bc, 3 templates BC (fase, trámite, tarea) |

Inventario muy pobre — la mayoría del HTML está inline en templates.

### 3.2 Partials / includes

| Partial | Usado en |
|---|---|
| `vistas/vista3_bc/_tabla_hijos.html` | 4 templates BC (tramitacion_bc, _solicitud, _fase, _tramite) |
| `admin_plantillas/_panel_tokens.html` | `admin_plantillas/detalle.html` |
| `layout/_header.html` | **huérfano** (existe `layout/header.html` que sí se usa) |

### 3.3 Módulos JS (16)

**Por familia:**

| Familia | Ficheros | Templates que los cargan |
|---|---|---|
| v2 (listados) | `v2-scroll-infinito.js`, `v2-filtros.js`, `v2-scroll-to-top.js`, `v2-tabla-scroll-to-top.js` | `lista_v2_base.html` (+ `base_fullwidth`) |
| v3 (BC) | `v3-breadcrumbs-crear.js`, `v3-breadcrumbs-edicion.js`, `v3-breadcrumbs-acciones.js` | 4 templates BC (no en tramitacion_bc raíz) |
| Widgets reutilizables | `selector_busqueda.js`, `selector_filtro.js`, `input_filtro.js`, `entrada_fecha.js`, `municipios_selector.js` | dispersos (detalles, wizard, pool) |
| Específicos | `tarea_documentos.js` (solo tramitacion_bc_tarea), `proyectos_listado.js` (solo proyectos/index) | uso único |
| React | `react/diagrama-esftt.iife.js` | solo `demo/diagrama.html` |
| Huérfano | `generar_escrito.js` | sin referencia en templates (¿pendiente o muerto?) |

### 3.4 CSS (13 ficheros — estratificación clara)

| Familia | Ficheros |
|---|---|
| Globales / widgets | `custom.css`, `selector_busqueda.css`, `selector_filtro.css`, `input_filtro.css`, `entrada_fecha.css` |
| v0 | `v0-login.css` |
| v1 | `v1-dashboard.css` |
| v2 | `v2-theme.css`, `v2-layout.css`, `v2-components.css`, `v2-data-table.css` |
| v3 | `v3-tramitacion.css`, `v3-breadcrumbs.css` |

---

## 4. Grafo de navegación

### 4.1 Patrón general

- **Dashboard** = hub central. Enlaza a las 5 áreas (entidades, expedientes, proyectos, usuarios, admin_plantillas).
- **Listados v2** → detalle (un único destino).
- **Detalle expediente** → 3 puertas: editar, pool_documentos, tramitación.
- **Tramitación BC** → estrictamente descendente. Cada nivel solo enlaza al inmediato inferior (+ pool + detalle expediente).

### 4.2 Hallazgos del grafo

#### Puertas duplicadas (mismo destino, N enlaces desde sitios distintos)
- `expedientes.detalle(exp_id)` enlazado desde **los 5 templates BC** (atajo persistente "volver a la cabecera").
- `expedientes.pool_documentos(exp_id)` enlazado desde **los 5 templates BC** (atajo persistente al pool).
- `dashboard.index` enlazado desde detalles de entidades, usuarios y admin_plantillas como "home".

**Lectura:** las dos primeras son diseño intencional para evitar perderse en la jerarquía BC profunda. Habrá que decidir si en el revamping se sustituyen por un componente persistente (sidebar/breadcrumbs sticky) en lugar de repetirlos en cada template.

#### Caminos cruzados (rutas distintas, mismo destino final)
- **Proyecto = expediente.** `proyectos.detalle(id)` redirige a `expedientes.detalle(id)`. `proyectos.editar_proyecto(id)` redirige a `expedientes.editar(id)#proyecto`. El blueprint `proyectos` apenas existe — es un alias de UI sobre expedientes.
- **Mis expedientes.** `dashboard.mis_expedientes` redirige a `expedientes.listado_v2`. Punto de entrada alternativo sin diferenciación real en destino.

**Lectura:** hay nomenclatura de doble vida ("proyecto" vs "expediente"; "mis expedientes" vs "listado") que no se traduce en pantallas distintas. Decisión a tomar: ¿se unifica el vocabulario, o el aliasing tiene valor para el usuario?

#### Callejones sin salida
- `errors/404.html`, `errors/500.html` — solo header (no enlazan a nada útil).
- `auth/login_v0.html`, `auth/seleccionar_rol.html` — flujo cerrado, esperado.
- `entidades/nueva.html` — solo botón "Cancelar" → vuelve a index. Coherente con su rol, pero subraya el patrón inconsistente con detalle modal/dual.

#### Navegación lateral ausente
- En tramitación BC, una vez en `tarea/<id>`, no hay enlaces a tareas hermanas, ni a otros trámites del mismo nivel. El usuario debe subir por breadcrumbs y volver a bajar.
- En listados v2, no hay paginación clásica — solo scroll infinito. Para navegar a un expediente concreto, scroll + búsqueda.

---

## 5. Capas geológicas

5 sistemas de UI coexisten en producción:

| Capa | Templates | JS | CSS | Alcance actual |
|---|---|---|---|---|
| v0 | `login_v0.html` | — | `v0-login.css` | login |
| v1 | `index_v1.html` | — | `v1-dashboard.css` | dashboard |
| v2 | `lista_v2_base.html`, `listado_v2.html` + 3 listados sin sufijo (entidades, proyectos, seguimiento) | 4 | 4 | listados infinitos |
| v3/BC | `base_bc.html` + 5 templates `tramitacion_bc_*` + `_tabla_hijos.html` | 3 | 2 | tramitación |
| React POC | `demo/diagrama.html` | 1 bundle | — | un solo diagrama |

**Sin versión (capa "base"):** detalles, formularios, wizard, errores, perfil, admin_plantillas. Usan `base_fullwidth.html` directamente.

**Coste de mantenimiento implícito:** cada capa tiene sus propios estilos, su propio JS y a veces su propio modelo de interacción. Una decisión sobre tipografía o spacing debería aplicarse a 13 CSS y 16 JS para ser coherente.

---

## 6. Anomalías

| Tipo | Hallazgo | Acción sugerida |
|---|---|---|
| Template huérfano | `layout/base_acordeon.html` | candidato a borrar tras confirmar |
| Template huérfano | `layout/_header.html` (existe `header.html` activo) | candidato a borrar |
| JS huérfano | `generar_escrito.js` (no cargado en templates actuales) | verificar si va con `api_escritos` pendiente o es muerto |
| JS duplicado | `v2-scroll-to-top.js` y `v2-tabla-scroll-to-top.js` (lógica similar) | unificar |
| Aliasing UI | `proyectos.*` redirige a `expedientes.*` | decidir si `proyectos` desaparece o gana entidad propia |

---

## 7. Hallazgos clave para la fase 2 (estudio de usuario)

1. **5 capas de UI conviviendo** — el revamping necesita decidir cuál se conserva como base y cuál se reescribe encima de la nueva.
2. **Tramitación BC tiene 5 niveles de profundidad** sin navegación lateral — preguntar al usuario cómo se mueve realmente entre tareas hermanas y si la jerarquía profunda es necesaria.
3. **Aliasing `proyecto`/`expediente`** y `mis_expedientes`/`listado` — pendiente decisión semántica.
4. **Inventario de macros ridículamente pobre** (2 macros, 5 partials) frente a 40 templates — hay HTML duplicado inline que el revamping debe extraer a componentes.
5. **Pool de documentos = puerta omnipresente** en BC. Si en lugar de un destino fuera un panel lateral persistente, se eliminaría una de las dos puertas duplicadas en cada nivel.
6. **Wizard de alta de expediente** vive aparte y no usa ningún componente compartido con detalles/edición. Riesgo de divergencia.
