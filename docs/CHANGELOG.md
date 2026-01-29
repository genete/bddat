# CHANGELOG - BDDAT

**Repositorio:** https://github.com/genete/bddat  
**Historial completo:** [Ver Pull Requests cerrados](https://github.com/genete/bddat/pulls?q=is%3Apr+is%3Aclosed)  
**Última actualización:** 29 de enero de 2026

---

## Estrategia de Documentación de Cambios

Este archivo mantiene un **resumen de los últimos 5 PRs mergeados** para consulta rápida. Para detalles completos (commits, archivos modificados, diffs), consultar directamente el Pull Request correspondiente en GitHub.

**Fuente de verdad:** Los Pull Requests cerrados en GitHub contienen toda la información histórica del proyecto.

**Actualización del changelog:** Se realiza **en la misma rama de desarrollo** (feature/bugfix/etc.) antes de crear el PR, no en rama separada. Esto reduce overhead de ramas/PRs/acciones.

---

## Últimos Cambios

### 2026-01-29 - [PR #XX: Edición de proyecto desde vista detalle (redirect inteligente)](https://github.com/genete/bddat/pull/XX)

**Objetivo:** Habilitar edición de proyecto desde su vista detallada mediante redirección inteligente al formulario de expediente con scroll automático a la sección proyecto.

**Estrategia:** Opción A - Redirección inteligente (issue #41)  
En lugar de duplicar lógica de formulario, se reutiliza el formulario de expediente existente con anchor `#proyecto` para scroll automático.

**Cambios principales:**
- ✅ **Ruta editar** (`app/routes/proyectos.py`):
  - `GET /proyectos/<id>/editar` redirige a `/expedientes/<expediente_id>/editar#proyecto`
  - Verificación de permisos (mismos que vista detalle)
  - Manejo 404/403 antes de redirigir
- ✅ **Anchor HTML** (`app/templates/expedientes/editar.html`):
  - Añadido `id="proyecto"` en card "Datos del Proyecto"
  - Permite scroll directo a sección específica
- ✅ **JavaScript scroll automático** (`app/templates/expedientes/editar.html`):
  - Detecta `window.location.hash === '#proyecto'`
  - Scroll suave (`scrollIntoView`) con timeout de 100ms
  - Comportamiento: Al llegar desde botón "Editar Proyecto", scroll automático a sección
- ✅ **Botones actualizados** (`app/templates/proyectos/detalle.html`):
  - Botón header "Editar Proyecto" ahora usa `url_for('proyectos.editar_proyecto', id=proyecto.id)`
  - Botón sidebar "Editar Proyecto" actualizado igualmente
  - Experiencia consistente en toda la vista

**Ventajas del enfoque elegido:**
- ✅ Reutiliza lógica existente (DRY)
- ✅ No duplica validaciones
- ✅ Mantiene coherencia con relación 1:1 expediente-proyecto
- ✅ Implementación simple y mantenible (15 minutos)
- ✅ Experiencia de usuario fluida (scroll automático)

**Funcionalidades:**
- Botón "Editar Proyecto" en vista detalle totalmente funcional
- Redirección automática a formulario de expediente
- Scroll automático a sección proyecto al cargar
- Permisos aplicados correctamente (TRAMITADOR vs ADMIN/SUPERVISOR)
- Tras guardar, usuario puede volver a vista proyecto o expediente

**Issues resueltos:** #41  
**Milestone:** MS-2 - Fase 2.2 Gestión de Expedientes  
**Archivos:** app/routes/proyectos.py, app/templates/expedientes/editar.html, app/templates/proyectos/detalle.html, docs/CHANGELOG.md

**Nota:** Se descartó Opción B (formulario independiente) por pragmatismo y coherencia con modelo 1:1.

---

### 2026-01-29 - [PR #55: Vista detallada de proyecto con maquetas](https://github.com/genete/bddat/pull/55)

**Objetivo:** Implementar vista detallada individual de proyecto con todas las secciones solicitadas, incluyendo maquetas visuales para Documentos y Solicitudes futuras.

**Cambios principales:**
- ✅ **Ruta detalle** (`app/routes/proyectos.py`):
  - `GET /proyectos/<id>` con verificación de permisos
  - TRAMITADOR: Solo ve proyectos de sus expedientes
  - ADMIN/SUPERVISOR: Ve cualquier proyecto
  - Manejo de errores 404 (no existe) y 403 (sin permisos)
  - Query con joins: Expediente, Usuario, TipoIA
- ✅ **Template detalle** (`app/templates/proyectos/detalle.html`):
  - Layout responsive col-lg-8 (contenido) + col-lg-4 (sidebar)
  - Breadcrumb: Inicio → Proyectos → Título proyecto
  - Badge "Interprovincial" en header cuando aplica
  - Botones header: Editar Proyecto, Volver
- ✅ **Sección: Datos Básicos** (card verde):
  - Título, Descripción, Finalidad, Emplazamiento
  - Tipo de instalación AT (badge + descripción completa)
  - Fecha de creación
  - Manejo de campos opcionales vacíos ("No especificado/a")
- ✅ **Sección: Localización** (card verde):
  - Lista completa de municipios con provincia y código INE
  - Badge "Proyecto Interprovincial" cuando `es_interprovincial == True`
  - Alerta amarilla informativa con lista de provincias afectadas
  - Resumen de provincias afectadas
- ✅ **Sección: Documentos - MAQUETA** (card azul):
  - Alerta info: "Funcionalidad en desarrollo"
  - Vista preliminar al 50% opacidad (no funcional)
  - Ejemplos visuales: Memoria_Tecnica.pdf, Plano_Situacion.dwg
  - Preparado para futura gestión de archivos adjuntos
- ✅ **Sección: Solicitudes - MAQUETA** (card amarilla):
  - Alerta warning: "Funcionalidad pendiente (Milestone 4)"
  - Vista preliminar al 50% opacidad (no funcional)
  - Tabla ejemplo: Consulta Previa (Aprobada), Autorización Administrativa (En tramitación)
  - Preparado para MS4 (CRUD solicitudes)
- ✅ **Sidebar: Expediente Asociado** (card azul):
  - Número AT con enlace a detalle expediente
  - Tipo de expediente (badge info)
  - Responsable: nombre, email, icono
  - Badge "Tú" para usuario actual
  - Badge "Sin asignar" para expedientes huérfanos
  - Indicador de expediente heredado (check verde)
  - Botón "Ver Expediente Completo"
- ✅ **Sidebar: Acciones Rápidas** (card gris):
  - Editar Proyecto (redirige a `/expedientes/<id>/editar#proyecto`)
  - Editar Expediente
  - Volver al Listado
- ✅ **Botón "Ver detalle" habilitado** en listado de proyectos

**Funcionalidades:**
- Vista detallada accesible desde `/proyectos/<id>`
- Botón "Ver detalle" funcional en listado (antes deshabilitado)
- Navegación breadcrumb completa
- Detección automática de proyectos interprovinciales
- Visualización completa de municipios con datos INE
- Maquetas visuales de secciones futuras (Documentos, Solicitudes)
- Enlaces cruzados a expediente y formulario de edición
- Tooltips en badges para información adicional

**Estilo:**
- Cards con `shadow-sm` y headers coloreados (colores JDA)
- Maquetas con `opacity-50` para indicar no funcionalidad
- Alertas con iconos `fa-2x` para mayor visibilidad
- Textos "Sin datos" con `text-muted fst-italic`
- Responsive con sidebar colapsable en móvil

**Issues resueltos:** #40  
**Milestone:** MS-2 - Fase 2.2 Gestión de Expedientes  
**Archivos:** app/routes/proyectos.py, app/templates/proyectos/detalle.html (NUEVO), app/templates/proyectos/index.html, docs/CHANGELOG.md

**Notas:** Se planea iteración posterior para mejoras de diseño según feedback.

---

### 2026-01-29 - [PR #54: Listado de proyectos con filtros y ordenamiento](https://github.com/genete/bddat/pull/54)

**Objetivo:** Implementar listado completo de proyectos de instalaciones AT con filtros, ordenamiento y visualización detallada.

**Cambios principales:**
- ✅ **Blueprint proyectos** (`app/routes/proyectos.py`):
  - Ruta `GET /proyectos/` con filtros por Instrumento Ambiental, Provincia, Responsable
  - Ordenamiento server-side por: Expediente AT, Título, Inst. Ambiental, Responsable, Fecha
  - Permisos: TRAMITADOR ve solo sus proyectos, ADMIN/SUPERVISOR ven todos
  - **outerjoin con Usuario** para incluir proyectos sin responsable asignado (huérfanos)
  - Filtrado por provincia usando subconsulta con `municipios_proyecto`
- ✅ **Modelo Proyecto** (`app/models/proyectos.py`):
  - **Property `municipios`**: Acceso directo a lista de Municipios vía backref `municipios_afectados`
  - Properties `es_interprovincial` y `provincias_afectadas` funcionando correctamente
  - Documentación actualizada sobre relación N:M con Municipios
- ✅ **Template HTML** (`app/templates/proyectos/index.html`):
  - Tabla responsive con columnas: Expediente AT, Título, Inst. Ambiental, Municipios, Provincias, Responsable, Acciones
  - **Columna Expediente AT primera** (a la izquierda)
  - **Columna Provincias** muestra nombres de provincias afectadas
  - Formulario de filtros con selectores (Inst. Ambiental, Provincia, Responsable)
  - Badge "Interprovincial" cuando afecta a múltiples provincias
  - Badge "Sin asignar" para expedientes huérfanos (responsable NULL)
  - Badge "Tú" para proyectos del usuario actual
  - **Iconos Font Awesome** (fas) coherentes con listado de Expedientes
  - **Estilo coherente** con Expedientes: card shadow-sm, thead table-success, badges con colores JDA
  - Contador de proyectos en formato texto (igual que Expedientes)
  - Tooltips en badges y botones
  - Botones: Ver detalle (deshabilitado, issue #40), Editar proyecto

**Funcionalidades:**
- Vista independiente de proyectos accesible desde `/proyectos/`
- Filtrado por Instrumento Ambiental (AAI, AAU, AAUS, CA, EXENTO)
- Filtrado por provincia de Andalucía (8 provincias)
- Filtrado por responsable (solo ADMIN/SUPERVISOR)
- Ordenamiento por columnas: Expediente AT, Título, Inst. Ambiental, Responsable, Fecha
- Visualización de hasta 3 municipios en tabla (con contador "... y X más")
- **Proyectos sin responsable visibles** con badge amarillo "Sin asignar"
- Badge "Interprovincial" automático cuando proyecto afecta a 2+ provincias
- Enlace directo a detalle de expediente desde número AT
- Botón "Editar" redirige a `/expedientes/<id>/editar#proyecto`

**Issues resueltos:** #39  
**Issues relacionados:** #52 (Búsqueda por texto), #53 (Filtrado inline en columnas)  
**Milestone:** MS-2 - Fase 2.2 Gestión de Expedientes  
**Archivos:** app/routes/proyectos.py (NUEVO), app/templates/proyectos/index.html (NUEVO), app/models/proyectos.py, app/__init__.py, docs/CHANGELOG.md

---

### 2026-01-29 - [PR #48: Gestión de municipios afectados en expedientes](https://github.com/genete/bddat/pull/48)

**Objetivo:** Permitir asociar múltiples municipios a cada proyecto/expediente mediante interfaz intuitiva con búsqueda substring.

**Cambios principales:**
- ✅ **API REST** (`app/routes/api_municipios.py`):
  - `GET /api/provincias?q=` - Búsqueda provincias con filtro substring case-insensitive
  - `GET /api/municipios?provincia=&q=` - Búsqueda municipios filtrados por provincia
- ✅ **Rutas expedientes.py**:
  - Validación obligatoriedad municipios (server-side)
  - Inserción transaccional en `municipios_proyecto`
  - Actualización municipios en edición (DELETE + INSERT)
- ✅ **JavaScript** (`app/static/js/municipios_selector.js`):
  - Dropdowns dinámicos con búsqueda substring
  - Lista acumulativa con checkboxes para borrado múltiple
  - Validación client-side antes de submit
  - Hidden inputs para POST del formulario
- ✅ **Templates**:
  - `nuevo.html` / `editar.html` - Card selector municipios con interfaz completa
  - `detalle.html` - Visualización municipios + alerta proyecto interprovincial
- ✅ **Sin cambios en BD**: Usa tabla `municipios_proyecto` existente

**Funcionalidades:**
- Selector de provincia con búsqueda instantánea
- Dropdown municipio filtrado por provincia seleccionada
- Lista acumulativa de municipios con borrado selectivo
- Campo obligatorio (*) con validación dual (JS + Python)
- Detección automática de proyectos interprovinciales en vista detalle

**Issues resueltos:** #48  
**Milestone:** 1.3 - Expedientes básicos (MVP)  
**Archivos:** app/routes/api_municipios.py (NUEVO), app/static/js/municipios_selector.js (NUEVO), app/__init__.py, app/routes/expedientes.py, app/templates/expedientes/*.html

---

### 2026-01-28 - [PR #46: Permitir expedientes sin responsable asignado (huérfanos)](https://github.com/genete/bddat/pull/46)

**Objetivo:** Modificar el modelo Expediente para permitir `responsable_id = NULL`, habilitando la creación de expedientes huérfanos que posteriormente pueden ser asignados por un supervisor según carga de trabajo o especialización.

**Cambios principales:**
- ✅ **Modelo expedientes.py**: `responsable_id` ahora acepta NULL
- ✅ **Migración Alembic**: `ALTER TABLE expedientes ALTER COLUMN responsable_id DROP NOT NULL`
- ✅ **Rutas expedientes.py**: Permitir crear y editar expedientes con `responsable_id = None`
- ✅ **Templates nuevo.html/editar.html**: Opción "-- Sin asignar (huérfano) --" en select de responsable
- ✅ **Templates detalle.html/index.html**: Badge visual "Sin asignar" cuando expediente sin responsable
- ✅ **Documentación**: Actualizada docstring del modelo con reglas de negocio de expedientes huérfanos

**Casos de uso:**
- Supervisor crea expediente para posterior asignación según disponibilidad
- Redistribución de carga: dejar expediente sin asignar temporalmente
- Gestión flexible de recursos humanos

**Issues resueltos:** #46  
**Milestone:** 1.3 - Expedientes básicos (MVP)  
**Archivos:** app/models/expedientes.py, migrations/versions/51fcf34d6955_*.py, app/routes/expedientes.py, app/templates/expedientes/*.html

---

**Nota:** Este changelog se mantiene con los últimos 5 PRs. Entradas más antiguas se pueden consultar en el [historial de Pull Requests](https://github.com/genete/bddat/pulls?q=is%3Apr+is%3Aclosed+sort%3Aupdated-desc) de GitHub.
