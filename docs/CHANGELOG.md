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

### 2026-01-27 - [PR #3: Mejorar Diseño de Mensajes Informativos](https://github.com/genete/bddat/pull/3)

**Objetivo:** Mejorar el diseño visual y comportamiento de los mensajes informativos (toasts) implementando los cambios solicitados en el issue #3.

**Cambios principales:**
- ✅ **Ancho 90%**: Los toasts ocupan el 90% del ancho visible con márgenes del 5% a cada lado
- ✅ **Borde uniforme**: Cambio de borde izquierdo de 4px a borde completo de 1px del color oscuro de cada tipo
- ✅ **Botón cerrar coloreado**: La "X" de cerrar ahora tiene el mismo color que el texto/borde de cada tipo (verde, rojo, amarillo, azul)
- ✅ **Transparencia inicial**: Los mensajes aparecen con opacity 0.9
- ✅ **Efecto hover**: Al pasar el ratón, el mensaje se oscurece (opacity 1), la sombra se intensifica y se eleva ligeramente
- ✅ **Tiempo ampliado**: El tiempo de auto-cierre aumenta de 5 a 8 segundos
- ✅ **Animaciones fade**: Transiciones suaves de 300ms al aparecer y desaparecer con desplazamiento vertical

**Issues resueltos:** #3  
**Archivos:** app/static/css/custom.css, app/templates/base.html

---

### 2026-01-25 - [PR #24: Detección de Proyectos Interprovinciales](https://github.com/genete/bddat/pull/24)

**Objetivo:** Añadir lógica al modelo Proyecto para detectar automáticamente si afecta a más de una provincia.

**Cambios principales:**
- ✅ **Propiedad `es_interprovincial`**: Booleana, detecta proyectos con municipios de 2+ provincias
- ✅ **Propiedad `provincias_afectadas`**: Lista ordenada de nombres de provincias únicas
- ✅ **Lógica**: Usa primeros 2 dígitos del código INE (PPMMM) del municipio
- ✅ **Sin migración**: Propiedades calculadas en runtime con `@property`

**Uso:**
```python
if proyecto.es_interprovincial:
    flash('⚠️ Proyecto interprovincial', 'warning')

provincias = proyecto.provincias_afectadas  # ['Almería', 'Granada']
```

**Archivos:** app/models/proyectos.py

---

**Nota:** Este changelog se mantiene con los últimos 5 PRs. Entradas más antiguas se pueden consultar en el [historial de Pull Requests](https://github.com/genete/bddat/pulls?q=is%3Apr+is%3Aclosed+sort%3Aupdated-desc) de GitHub.
