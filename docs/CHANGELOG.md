# CHANGELOG - BDDAT

**Repositorio:** https://github.com/genete/bddat  
**Historial completo:** [Ver Pull Requests cerrados](https://github.com/genete/bddat/pulls?q=is%3Apr+is%3Aclosed)  
**Última actualización:** 01 de febrero de 2026

---

## Estrategia de Documentación de Cambios

Este archivo mantiene un **resumen de los últimos 5 PRs mergeados** para consulta rápida. Para detalles completos (commits, archivos modificados, diffs), consultar directamente el Pull Request correspondiente en GitHub.

**Fuente de verdad:** Los Pull Requests cerrados en GitHub contienen toda la información histórica del proyecto.

**Actualización del changelog:** Se realiza **en la misma rama de desarrollo** (feature/bugfix/etc.) antes de crear el PR, no en rama separada. Esto reduce overhead de ramas/PRs/acciones.

---

## Últimos Cambios

### 2026-02-01 - [PR #XX: Arquitectura polímorfica ENTIDADES - Fase 1: Documentación](https://github.com/genete/bddat/pull/XX)

**Objetivo:** Diseñar y documentar arquitectura unificada de entidades (administrados, organismos públicos, ayuntamientos, diputaciones, empresas de servicio público) mediante patrón de tablas inversas/puente.

**Problema identificado:** Sistema original proponía tabla única `administrados`, pero el sistema real requiere gestionar múltiples tipos de entidades con metadatos muy diferentes (titulares, organismos consultados, ayuntamientos para tablón, diputaciones para BOP, empresas eléctricas).

**Decisión arquitectónica:**
Se adoptó **patrón de tablas inversas/puente** tras análisis documentado en Issue #62:
- **Opción descartada:** Vistas actualizables sobre tabla única (muchos NULL, tabla muy ancha, validaciones complejas)
- **Opción adoptada:** Tabla base `ENTIDADES` + tablas de metadatos específicos por tipo
- **Ventajas:** Normalización, escalabilidad, validaciones modulares, compatibilidad SQLAlchemy, migraciones Alembic automáticas

**Cambios principales:**

**Añadido:**
- ✅ **E_009 - TIPOS_ENTIDADES** (catálogo):
  - Tabla de referencia con 5 tipos: ADMINISTRADO, EMPRESA_SERVICIO_PUBLICO, ORGANISMO_PUBLICO, AYUNTAMIENTO, DIPUTACION
  - Campos rol: `puede_ser_solicitante`, `puede_ser_consultado`, `puede_publicar`
  - Filtrado automático en UI según contexto (solicitud vs consulta vs publicación)
  - Incluye código, nombre, descripción, activo
- ✅ **E_010 - ENTIDADES** (tabla base polímórfica):
  - Campos comunes: CIF/NIF, nombre completo, email, teléfono, dirección, municipio
  - FK a `TIPOS_ENTIDADES` para clasificación
  - Relaciones 1:1 con tablas de metadatos específicos
  - Sin campos específicos de ningún tipo (0% NULL irrelevantes)
- ✅ **O_015 - ENTIDADES_ADMINISTRADOS**:
  - Metadatos: tipo persona (FÍsica/Jurídica), representante (NIF+nombre), email notificaciones
  - Sistema Notifica: email registrado + teléfono SMS opcional
  - Puede actuar como titular, solicitante o autorizado
  - Validaciones CIF/NIF (algoritmo oficial), email formato
- ✅ **O_016 - ENTIDADES_EMPRESAS_SERVICIO_PUBLICO**:
  - Empresas eléctricas (distribuidoras, transportistas) y telecos
  - Campo DIR3 para comunicaciones SIR cuando actúan como organismos consultados
  - Sin representante (gestión corporativa directa)
  - Validación DIR3 formato alfanumérico 8-10 caracteres
- ✅ **O_017 - ENTIDADES_ORGANISMOS_PUBLICOS**:
  - Organismos AGE (Ministerios, Secretarías Estado) y CCAA (Consejerías, Delegaciones)
  - DIR3 para notificaciones SIR, legislatura para versionado histórico
  - Campos fecha_desde/fecha_hasta para cambios de estructura administrativa
  - Sistema versionado: mismo organismo, múltiples registros por legislatura
  - Ejemplo documentado: Bandeja SIR en ARIES-SIR para envío/recepción
- ✅ **O_018 - ENTIDADES_AYUNTAMIENTOS**:
  - CIF formato P+INE (7 dígitos) + control (ej: P2807901D - Madrid)
  - DIR3 para notificaciones SIR cuando actúan como organismo consultado
  - Múltiples roles: solicitante ocasional, consultado, publicador tablón
  - Aclaración Ley 39/2015 Art. 45.4: tablón edictos es obligación vs administrados (no dato BDDAT)
  - Flujo: BDDAT → SIR → Ayuntamiento publica en su tablón
- ✅ **O_019 - ENTIDADES_DIPUTACIONES**:
  - CIF formato P+provincia (2 dígitos)+00000+control (ej: P1100000B - Cádiz)
  - DIR3 para notificaciones SIR como organismo consultado
  - **EMAIL_PUBLICACION_BOP**: Método tradicional email (datos pagador + texto anuncio)
  - Caso real verificado: BOP Cádiz gestionado por Asociación Prensa (concesionaria)
  - Ejemplo email: `boletin@bopcadiz.org`
  - Diferencia con ayuntamientos: BOP usa email, tablón usa SIR interno

**Modificado:**
- ✅ **Tablas.md**: Refactorizado completo con arquitectura polímórfica (7 tablas nuevas)
  - Tabla base + catálogo + 5 tablas metadatos documentadas
  - Estructura, claves, índices, relaciones, validaciones por tabla
  - Consultas SQL frecuentes (7 por cada tabla de metadatos)
  - Filosofía minimalista: solo campos que NO están en ENTIDADES

**Documentación:**
- ✅ **Issue #62**: Decisión arquitectónica completa con análisis Tablas Inversas vs Vistas Actualizables
  - Tabla comparativa con 10 criterios técnicos
  - Justificación: normalización, escalabilidad, compatibilidad SQLAlchemy, validaciones modulares
  - Ejemplos de uso en código Python (crear entidades, consultas JOIN)
- ✅ **Sistemas de notificación**:
  - **Notifica**: Email registrado + CIF/NIF (administrados como solicitantes)
  - **SIR**: DIR3 para comunicaciones interadministrativas (organismos consultados)
  - Diferenciación clara: email general vs email notificaciones vs DIR3
- ✅ **Validaciones documentadas**:
  - CIF/NIF: Algoritmo oficial (NIF 8+letra, NIE X/Y/Z+7+letra, CIF letra+7+letra/dígito)
  - DIR3: Formato alfanumérico 1-2 letras + 7-8 dígitos
  - CIF ayuntamientos: P+INE(7)+control
  - CIF diputaciones: P+provincia(2)+00000+control
  - Email: Formato estándar usuario@dominio.ext
- ✅ **Flujo UX**: Copia de datos entre roles (múltiples roles por entidad)
  - Ejemplo: Diputación como consultada + solicitante + publicador BOP
  - Sistema detecta roles activos y ofrece copiar datos
- ✅ **Consultas SQL**: 35+ consultas documentadas (5-7 por tabla)
  - Listar por tipo, buscar por CIF/DIR3, verificar roles múltiples, filtrar por provincia/legislatura

**Funcionalidades preparadas:**
- ✅ Fuente única de verdad para todas las entidades (sin duplicaciones)
- ✅ Múltiples roles por entidad (ayuntamiento puede ser solicitante Y consultado)
- ✅ Versionado histórico de organismos públicos (legislatura + vigencia)
- ✅ Validaciones específicas por tipo de entidad
- ✅ Sistema de notificaciones dual (Notifica vs SIR)
- ✅ Escalabilidad: añadir nuevos tipos sin modificar existentes

**Archivos creados:**
- `docs/fuentesIA/referencias/tablas/E_009_TIPOS_ENTIDADES.md`
- `docs/fuentesIA/referencias/tablas/E_010_ENTIDADES.md`
- `docs/fuentesIA/referencias/tablas/O_015_ENTIDADES_ADMINISTRADOS.md`
- `docs/fuentesIA/referencias/tablas/O_016_ENTIDADES_EMPRESAS_SERVICIO_PUBLICO.md`
- `docs/fuentesIA/referencias/tablas/O_017_ENTIDADES_ORGANISMOS_PUBLICOS.md`
- `docs/fuentesIA/referencias/tablas/O_018_ENTIDADES_AYUNTAMIENTOS.md`
- `docs/fuentesIA/referencias/tablas/O_019_ENTIDADES_DIPUTACIONES.md`

**Archivos modificados:**
- `docs/fuentesIA/referencias/Tablas.md` (refactorizado completo)
- `docs/CHANGELOG.md`

**Issues resueltos:** #62 (Fase 1 - Documentación)  
**Issues relacionados:** #78 (Ampliar municipios toda España - bloqueado por este)  
**Milestone:** MS-3 - Alineación Administrativa  

**Próximas fases:**
- Fase 2: Migraciones Alembic (crear tablas en BD)
- Fase 3: Modelos SQLAlchemy (mapeo ORM)
- Fase 4: Tests unitarios e integración
- Fase 5: Interfaz CRUD entidades

**Notas:** Esta fase solo documenta el diseño. No incluye código Python ni SQL ejecutable. El patrón arquitectónico adoptado (tablas inversas) permite escalabilidad y mantenibilidad superior a alternativas consideradas.

---

### 2026-01-30 - [PR #XX: Añadir Proyectos al menú de navegación principal](https://github.com/genete/bddat/pull/XX)

**Objetivo:** Habilitar acceso directo a listado de proyectos desde cualquier página de la aplicación mediante ítem permanente en la barra de navegación superior.

**Problema identificado:** Aunque las rutas y templates de proyectos estaban implementados y funcionales (`/proyectos/`, `/proyectos/<id>`), no existía ningún enlace de navegación hacia ellos desde la interfaz de usuario, convirtiéndolos en páginas "huérfanas" accesibles solo vía URL directa.

**Cambios principales:**
- ✅ **Navbar** (`app/templates/base.html`):
  - Añadido ítem "Proyectos" en menú principal
  - Ubicación: después de "Expedientes", antes de "Usuarios"
  - Visible para todos los roles autenticados (TRAMITADOR, ADMIN, SUPERVISOR)
  - Icono: `fa-bolt` (coherente con identidad visual del módulo proyectos)
  - Accesible desde cualquier página del sistema
- ✅ **Dashboard** (`app/routes/dashboard.py`):
  - Mantenido ítem "Listado proyectos" en bloque Tramitación (acceso directo adicional)
  - Ubicación: después de "Listado expedientes", antes de "Nuevo expediente"
  - Mismos permisos que expedientes: `['TRAMITADOR', 'ADMINISTRATIVO', 'SUPERVISOR', 'ADMIN']`
- ✅ **Limpieza de templates**:
  - Eliminados botones cruzados "Ver Proyectos" / "Ver Expedientes" de headers
  - Restaurado layout original limpio en `expedientes/index.html`
  - Restaurado layout original limpio en `proyectos/index.html`
  - Único botón principal: "Nuevo Expediente" (verde, sin distracciones visuales)

**Funcionalidades:**
- ✅ Navegación desde cualquier página → Proyectos (navbar siempre visible)
- ✅ Acceso rápido desde Dashboard → Proyectos (bloque Tramitación)
- ✅ Layout limpio sin botones redundantes en headers
- ✅ Coherencia con estructura de navegación existente (Inicio, Expedientes, Proyectos, Usuarios)
- ✅ Sin cambios en permisos ni lógica de negocio (solo presentación)

**Estilo:**
- Navbar: texto blanco sobre fondo verde (bg-success JDA)
- Icono Font Awesome: `fa-bolt` (proyectos específicamente)
- Coherencia con patrón de navegación existente en otros módulos
- Eliminación de botones outline-primary que rompian el diseño de headers

**Decisión de diseño:**
Se optó por navbar sobre botones cruzados porque:
1. Acceso universal desde cualquier página (no solo listados)
2. Coherencia con patrón de navegación existente
3. No rompe el layout limpio de las páginas individuales
4. Facilita descubribilidad de la funcionalidad

**Issues resueltos:** #59  
**Milestone:** MS-2 - Fase 2.2 Gestión de Expedientes  
**Archivos:** app/templates/base.html, app/templates/expedientes/index.html, app/templates/proyectos/index.html, app/routes/dashboard.py, docs/CHANGELOG.md

**Notas:** Las rutas y funcionalidad de proyectos ya existían desde issue #39. Este cambio solo mejora la accesibilidad desde la UI.

---

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

**Nota:** Este changelog se mantiene con los últimos 5 PRs. Entradas más antiguas se pueden consultar en el [historial de Pull Requests](https://github.com/genete/bddat/pulls?q=is%3Apr+is%3Aclosed+sort%3Aupdated-desc) de GitHub.
