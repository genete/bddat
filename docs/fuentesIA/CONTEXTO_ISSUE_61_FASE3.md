# Contexto Issue #61 — Fase 3: Interfaz Navegación Contextual

**Fecha documento:** 2026-02-19
**Rama a crear:** `feature/61-fase3-navegacion-contextual`
**Issues del bloque:** #70, #71, #72, #73
**Epic padre:** #61 (Alineación Administrativa)

---

## ⚠️ Aviso importante: issues desactualizados

Los issues #70-73 se escribieron antes de que se implementara la Vista V3
(`tramitacion_v3`). Sus wireframes y referencias a "menú lateral contextual"
o "sidebar acordeón" describen una arquitectura que **ya no es la correcta**.

**La vista correcta es `base_acordeon.html`**, accesible en
`/expedientes/<id>/tramitacion_v3`. Probada con Playwright en expediente id=104.

Leer los issues por sus **requisitos funcionales de fondo**, no por sus
wireframes literales. El sidebar lateral como componente independiente
está **deprecado**.

---

## Estado del codebase al iniciar Fase 3

### Lo que ya existe y funciona
- Vista V3 tramitación en `/expedientes/<id>/tramitacion_v3`
  (`app/modules/expedientes/templates/expedientes/tramitacion_v3.html`)
  — Usa `base_acordeon.html` (CSS v2, header con module-nav)
  — Carga `js/vista3_navigation.js` + API `/api/...`
- Módulos `expedientes` y `entidades` en `app/modules/` (issue #93 cerrado)
- Module-nav metadata-driven en el header
- API REST expedientes con paginación cursor (`/api/expedientes`)
- Modelos SFTT completos: `Solicitud`, `Fase`, `Tramite`, `Tarea`
  en `app/models/solicitudes.py`, `fases.py`, `tramites.py`, `tareas.py`

### Lo que falta (bloque Fase 3)

| Issue | Título | Nota |
|-------|--------|------|
| #70 | Listado Gestión Expedientes con datos SFTT | Enriquecer listado V2 con titular, conteo solicitudes, estado tramitación |
| #71 | Menú lateral contextual | **Depreciado como sidebar**. El requisito real es: navegación jerárquica funcional dentro de tramitacion_v3 |
| #72 | Vista detalle con hijos directos | Panel de detalle por nodo (Expediente/Solicitud/Fase/Trámite) con tabs y lista de hijos |
| #73 | Breadcrumb horizontal + transiciones | Coherencia de navegación: breadcrumb clicable, botones "volver" consistentes |

---

## Alcance funcional real (sin los wireframes obsoletos)

### #70 — Enriquecer listado V2

El listado actual (`/expedientes/listado-v2`) carga datos vía API `/api/expedientes`.
Hay que añadir a la API y al template:
- Titular del expediente (campo `titular_id` + join a `Entidad`)
- Conteo de solicitudes (total / activas)
- Estado de tramitación calculado (Incompleto / Vencido / En trámite / Resuelto)
- Próximo vencimiento (min `fecha_limite` de trámites pendientes)

**Ficheros a tocar:**
- `app/routes/api_expedientes.py` — añadir campos a la respuesta JSON
- `app/modules/expedientes/templates/expedientes/listado_v2.html` — añadir columnas
- Posiblemente un helper en `app/utils/` para `calcular_estado_tramitacion()`

### #71 — Navegación jerárquica en tramitacion_v3

El requisito real (más allá del wireframe del sidebar): que la vista
`tramitacion_v3` permita navegar de forma funcional por la jerarquía
Expediente → Solicitudes → Fases → Trámites → Tareas con datos reales de la BD.

Actualmente `tramitacion_v3.html` es un **mockup estático** con acordeón HTML.
`vista3_navigation.js` llama a `initVista3(EXPEDIENTE_ID)` pero depende de
APIs que pueden no estar completas.

**Verificar antes de empezar:**
- ¿Qué endpoints consume `vista3_navigation.js`?
- ¿Están implementados en `app/routes/vista3.py`?
- ¿Devuelven datos reales o son stubs?

### #72 — Panel de detalle por nodo

Cuando el usuario selecciona un nodo en la vista V3, el panel derecho (o
el área principal en la vista acordeón) debe mostrar:
- Datos del nodo seleccionado (tabs: Datos / Documentos / Historial)
- Lista de hijos directos con acciones (crear, ver, editar)

Esto es la segunda mitad de lo que hace `tramitacion_v3`: actualmente muestra
la jerarquía pero el panel de detalle está pendiente de implementación real.

### #73 — Breadcrumb horizontal + transiciones coherentes

Problema actual:
- Botón "Cancelar" en editar vuelve al listado en vez de al detalle
- Botón "Volver" en detalle vuelve al listado
- No hay breadcrumb clicable consistente en las vistas V3

El bug #113 ya resolvió el caso del wizard (cancelar vuelve al origen).
Este issue extiende ese patrón al resto de vistas.

**Ficheros a revisar:**
- `app/modules/expedientes/templates/expedientes/detalle.html`
- `app/modules/expedientes/templates/expedientes/editar.html`
- `app/modules/expedientes/templates/expedientes/tramitacion_v3.html`

---

## Modelos relevantes

```python
# Jerarquía SFTT
Expediente (1:N) → Solicitud → Fase → Tramite → Tarea

# Campos fecha clave
Solicitud.fecha_fin   # NULL = activa
Fase.fecha_fin        # NULL = activa
Tramite.fecha_fin     # NULL = pendiente
Tramite.fecha_limite  # para calcular vencimientos

# Titular
Expediente.titular_id → Entidad.id
# (desnormalizado en expediente; historial en HistoricoTitularExpediente)
```

---

## Orden de implementación sugerido

1. **#73** primero — sin BD, solo templates. Coherencia botones/volver.
2. **#70** — enriquecer API + listado. Requiere queries con joins.
3. **#71 + #72** juntos — son las dos mitades de tramitacion_v3 funcional.
   Dependen de que las APIs de vista3 estén listas o se creen.

---

## Preguntas a resolver antes de empezar

1. ¿Qué hace actualmente `vista3_navigation.js`? ¿Qué endpoints llama?
2. ¿Está `app/routes/vista3.py` con datos reales o stubs?
3. ¿El `titular_id` en `Expediente` apunta a `Entidad` o a otra tabla?
   (El issue #61 menciona que falta tabla de titulares — ¿se creó?)

---

## Referencias

- Issue #61: https://github.com/genete/bddat/issues/61 (ABIERTO)
- Issue #70: https://github.com/genete/bddat/issues/70
- Issue #71: https://github.com/genete/bddat/issues/71
- Issue #72: https://github.com/genete/bddat/issues/72
- Issue #73: https://github.com/genete/bddat/issues/73
- Contexto #93 completado: `docs/fuentesIA/CONTEXTO_ISSUE_93.md`
