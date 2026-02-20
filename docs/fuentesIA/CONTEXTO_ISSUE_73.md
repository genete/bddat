# Contexto Issues #70-73 — Fase 3 Navegación Contextual

**Epic:** Issue #61 — Interfaz Navegación Contextual
**Estado:** Planificado, pendiente de implementación
**Rama a crear:** `feature/61-fase3-navegacion-contextual` desde `develop`

---

## Decisiones arquitectónicas tomadas

### Sidebar descartado (#71)
El issue #71 describe un panel lateral de 250px. Hay un comentario en ese issue que lo descarta.
**Decisión:** Continuar con Vista 3 de acordeones (ya funcional). El breadcrumb dinámico clicable
ya actúa como navegación contextual. El sidebar de los mockups del issue está obsoleto.

### Campo `fecha_limite` en Tramite
El issue #70 incluye "Próximo Vencimiento" pero `Tramite` no tiene `fecha_limite` en BD.
**Decisión:** Omitir por ahora. Cuando el listado sea metadata-driven, se añadirá la migración
y la columna de forma independiente (#74 semáforos/alertas).

### Listado modular (metadata-driven)
El listado V2 ya tiene config de columnas en JS. La idea a largo plazo es que esas columnas
sean configurables via JSON. Por ahora extendemos la config JS existente.

---

## Estado actual del código

### Lo que ya funciona
- **Listado V2** (`/expedientes/listado-v2`): scroll infinito, columnas básicas, paginación cursor
- **Vista 3** (`/expedientes/<id>/tramitacion_v3`): acordeones jerárquicos Expediente→Solicitudes→Fases→Trámites→Tareas
- **Breadcrumb dinámico** en Vista 3: clicable, navega al nivel correcto (`vista3_navigation.js`)
- **Botón cancelar en editar.html**: vuelve al detalle (commit `713818a`)

### Modelos SFTT relevantes

```
Expediente — id, numero_at, titular_id (NULL en datos prueba), responsable_id
  └── Solicitud — estado: EN_TRAMITE | RESUELTA | DESISTIDA | ARCHIVADA, fecha_fin
        └── Fase — fecha_inicio, fecha_fin (NULL=en curso), resultado_fase_id
              └── Tramite — fecha_inicio, fecha_fin (NO tiene fecha_limite)
                    └── Tarea — fecha_inicio, fecha_fin, doc_usado_id, doc_producido_id
```

### Ficheros clave
| Ruta | Propósito |
|------|-----------|
| `app/routes/api_expedientes.py` | API REST listado + jerarquía |
| `app/modules/expedientes/routes.py` | Rutas del módulo |
| `app/modules/expedientes/templates/expedientes/listado_v2.html` | Listado V2 |
| `app/modules/expedientes/templates/expedientes/tramitacion_v3.html` | Vista 3 contenedor |
| `app/modules/expedientes/templates/expedientes/detalle.html` | Detalle (usa base.html LEGACY) |
| `app/templates/vistas/vista3/_expediente_body.html` | Parcial acordeón nivel expediente |
| `app/templates/vistas/vista3/_solicitudes_accordion.html` | Parcial lista solicitudes |
| `app/templates/vistas/vista3/_solicitud_accordion.html` | Parcial detalle solicitud |
| `app/templates/vistas/vista3/_fase_accordion.html` | Parcial detalle fase |
| `app/templates/vistas/vista3/_tramite_accordion.html` | Parcial detalle trámite |
| `app/templates/vistas/vista3/_tarea_accordion.html` | Parcial detalle tarea |
| `app/routes/vista3.py` | Backend renderización dinámica Vista 3 |
| `app/static/js/vista3_navigation.js` | Lógica navegación stack JS |
| `app/static/css/v3-tramitacion.css` | Estilos acordeones anidados |

---

## Plan de implementación

### Bloque 1 — Issue #70: Enriquecer listado V2

**`app/routes/api_expedientes.py`** — función `listar_expedientes()`:
- Añadir subconsulta LEFT JOIN con `solicitudes` para:
  - `num_solicitudes` (COUNT total)
  - `num_activas` (COUNT donde estado = 'EN_TRAMITE')
- Añadir campo `estado_tramitacion` calculado:
  - `SIN_SOLICITUDES` — sin ninguna solicitud
  - `EN_TRAMITE` — al menos una solicitud activa
  - `RESUELTO` — todas resueltas/archivadas/desistidas
- Añadir campo `url_tramitacion` = URL a tramitacion_v3

**`app/modules/expedientes/templates/expedientes/listado_v2.html`** — config JS de columnas:
- Añadir columna `solicitudes` (count + badge activas)
- Añadir columna `estado_tramitacion` (badge con color semántico)
- Botón "Tramitar" en acciones apunta a `url_tramitacion`

**Commit:** `[RUTA][TEMPLATE] #70 Enriquecer listado V2 con datos SFTT`

---

### Bloque 2 — Issues #71 + #72: Tabs dentro de acordeones Vista 3

Añadir Bootstrap tabs dentro de cada parcial de la Vista 3:

| Template | Tabs |
|----------|------|
| `_solicitud_accordion.html` | [Datos] [Fases] [Documentos] |
| `_fase_accordion.html` | [Datos] [Trámites] [Documentos] |
| `_tramite_accordion.html` | [Datos] [Tareas] [Documentos] |
| `_tarea_accordion.html` | [Datos] [Documentos] |

- Tab "Datos": datos actuales del nivel (mover al tab)
- Tab "Hijos": lista actual de hijos (Fases/Trámites/Tareas — mover al tab)
- Tab "Documentos": placeholder "Sin documentos registrados" (modelo existe, sin datos prueba)
- IDs de tabs: usar `tab-{tipo}-{id}` para evitar conflictos entre acordeones

**Ajustar `app/static/css/v3-tramitacion.css`** si hay problemas visuales con tabs dentro de acordeones.

**Commit:** `[TEMPLATE][STYLE] #71 #72 Tabs en acordeones Vista 3`

---

### Bloque 3 — Issue #73: detalle.html + breadcrumb coherente

**`app/modules/expedientes/templates/expedientes/detalle.html`**:
- Cambiar `{% extends 'base.html' %}` → `{% extends 'layout/base_fullwidth.html' %}`
- Añadir `{% block breadcrumb %}`:
  ```html
  <a href="{{ url_for('dashboard.index') }}">Inicio</a>
  <span>›</span>
  <a href="{{ url_for('expedientes.listado_v2') }}">Expedientes</a>
  <span>›</span>
  <span>AT-{{ expediente.numero_at }}</span>
  ```
- Añadir botón "Tramitar" → `url_for('expedientes.tramitacion_v3', id=expediente.id)`

**`app/modules/expedientes/routes.py`** — auditar redirects POST:
- Verificar que todos los POST redirigen a `detalle`, no al listado

**Commit:** `[TEMPLATE] #73 Migrar detalle.html a base_fullwidth + breadcrumb`

---

## Verificación con Playwright

Al finalizar los 3 bloques, ejecutar test para verificar:
1. `/expedientes/listado-v2` — columnas nuevas visibles, botón "Tramitar" funciona
2. `/expedientes/104/tramitacion_v3` — tabs dentro de acordeones, clicables
3. `/expedientes/104` — tiene breadcrumb y module-nav (sin base.html legacy)
4. Flujo completo: Listado → Tramitar → Vista 3 → breadcrumb clicable navega atrás

Se pueden reusar/adaptar `test_fase4.js` y `test_breadcrumb.js`.

---

## Notas adicionales

- `titular_id` es NULL en los 3 expedientes de prueba — mostrar "Sin titular" de forma graciosa
- `base.html` legacy sigue existiendo para otras vistas (auth, dashboard, proyectos) — no eliminar
- Seguir convenciones de commit del proyecto: `[RUTA]`, `[TEMPLATE]`, `[STYLE]`
- PRs siempre contra `develop`, no contra `main`
