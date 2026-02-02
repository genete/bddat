# CHANGELOG - BDDAT

**Repositorio:** https://github.com/genete/bddat  
**Historial completo:** [Ver Pull Requests cerrados](https://github.com/genete/bddat/pulls?q=is%3Apr+is%3Aclosed)  
**Última actualización:** 02 de febrero de 2026

---

## Estrategia de Documentación de Cambios

Este archivo mantiene un **resumen de los últimos 5 PRs mergeados** para consulta rápida. Para detalles completos (commits, archivos modificados, diffs), consultar directamente el Pull Request correspondiente en GitHub.

**Fuente de verdad:** Los Pull Requests cerrados en GitHub contienen toda la información histórica del proyecto.

**Actualización del changelog:** Se realiza **en la misma rama de desarrollo** (feature/bugfix/etc.) antes de crear el PR, no en rama separada. Esto reduce overhead de ramas/PRs/acciones.

---

## Últimos Cambios

### 2026-02-02 - [PR #XX: Arquitectura polimórfica ENTIDADES - Fase 2: Modelos SQLAlchemy + Migración](https://github.com/genete/bddat/pull/XX)

**Objetivo:** Implementar modelos SQLAlchemy y migración Alembic de la arquitectura ENTIDADES diseñada en Fase 1, creando 7 tablas operativas en base de datos.

**Continuación de:** PR #XX (Fase 1 - Documentación de arquitectura)

**Cambios principales:**

**Añadido - Modelos SQLAlchemy (7 archivos nuevos):**
- ✅ **`app/models/tipo_entidad.py`** (TipoEntidad):
  - Catálogo maestro en `estructura.tipos_entidades`
  - Campos: codigo (UNIQUE), nombre, tabla_metadatos, puede_ser_solicitante/consultado/publicar
  - Relación 1:N con Entidad
  - Métodos estáticos: `get_by_codigo()`, `get_solicitantes()`, `get_consultados()`, `get_publicadores()`
- ✅ **`app/models/entidad.py`** (Entidad):
  - Tabla base polimórfica en `public.entidades`
  - Campos comunes: cif_nif (UNIQUE), nombre_completo, email, teléfono, dirección, municipio_id
  - FKs: `tipo_entidad_id` → `estructura.tipos_entidades`, `municipio_id` → `estructura.municipios`
  - Relaciones 1:1 con 5 tablas de metadatos (cascade='all, delete-orphan')
  - Métodos estáticos: `normalizar_cif_nif()`, `validar_cif_nif()`, `buscar_por_cif_nif()`, `buscar_por_nombre()`
- ✅ **`app/models/entidad_administrado.py`** (EntidadAdministrado):
  - Metadatos en `public.entidades_administrados`
  - Campos: email_notificaciones, representante_nif_cif, representante_nombre, representante_telefono, representante_email
  - CheckConstraint: coherencia representante (si hay CIF debe haber nombre)
  - Métodos: `obtener_cif_notifica()`, `obtener_par_notifica()`, `validar_datos_notifica()`
  - Properties: `tiene_representante`, `es_autorepresentado`
- ✅ **`app/models/entidad_empresa_servicio_publico.py`** (EntidadEmpresaServicioPublico):
  - Metadatos en `public.entidades_empresas_servicio_publico`
  - Campos: nombre_comercial, sector, codigo_cnae, observaciones
  - Sin validaciones especiales (campos opcionales)
- ✅ **`app/models/entidad_organismo_publico.py`** (EntidadOrganismoPublico):
  - Metadatos en `public.entidades_organismos_publicos`
  - Campos: codigo_dir3 (NOT NULL), ambito (ESTATAL/AUTONOMICO/LOCAL/EUROPEO), tipo_organismo, url_sede_electronica
  - Índice UNIQUE en codigo_dir3
  - Métodos estáticos: `buscar_por_dir3()`, `listar_por_ambito()`
- ✅ **`app/models/entidad_ayuntamiento.py`** (EntidadAyuntamiento):
  - Metadatos en `public.entidades_ayuntamientos`
  - Campos: codigo_dir3 (NOT NULL, UNIQUE), codigo_ine_municipio (5 dígitos), url_tablon_edictos
  - Property: `provincia` (obtiene vía entidad.municipio.provincia)
  - Métodos estáticos: `buscar_por_dir3()`, `buscar_por_ine()`, `listar_por_provincia()`
- ✅ **`app/models/entidad_diputacion.py`** (EntidadDiputacion):
  - Metadatos en `public.entidades_diputaciones`
  - Campos: codigo_dir3 (NOT NULL, UNIQUE), codigo_ine_municipio_sede, url_bop, email_publicacion_bop, observaciones
  - Property: `provincia` (obtiene vía entidad.municipio donde tiene sede)
  - Métodos estáticos: `buscar_por_dir3()`, `buscar_por_codigo_ine_sede()`

**Modificado:**
- ✅ **`app/models/__init__.py`**:
  - Importados 7 nuevos modelos en orden correcto (TipoEntidad primero, luego Entidad, luego metadatos)
  - Comentarios de orden de dependencias actualizados
  - Añadidos a `__all__` para exportación

**Migración Alembic:**
- ✅ **`migrations/versions/c21871f08bb2_añadir_arquitectura_entidades_.py`**:
  - **Migr ación manual** (no autogenerate debido a complejidad cross-schema)
  - Función `upgrade()`:
    1. `estructura.tipos_entidades` (catálogo maestro)
    2. `public.entidades` (tabla base con FKs a estructura)
    3. `public.entidades_administrados` (FK CASCADE a entidades)
    4. `public.entidades_empresas_servicio_publico` (FK CASCADE)
    5. `public.entidades_organismos_publicos` (FK CASCADE)
    6. `public.entidades_ayuntamientos` (FK CASCADE)
    7. `public.entidades_diputaciones` (FK CASCADE)
  - Todos los índices creados: cif_nif, nombre_completo, activo, tipo_entidad_id, codigo_dir3 (UNIQUE donde aplica)
  - Comentarios PostgreSQL en todas las columnas
  - Constraints: UNIQUE, CHECK, ForeignKey con ondelete='CASCADE'
  - Función `downgrade()`: DROP en orden inverso (dependientes primero)
  - **Probado**: upgrade + downgrade + upgrade exitosos

**Correcciones realizadas durante implementación:**
- ✅ **Corrección FK cross-schema en modelos:**
  - `TipoEntidad`: Añadido `__table_args__ = {'schema': 'estructura'}` (faltaba)
  - `Entidad.tipo_entidad_id`: FK corregida a `'estructura.tipos_entidades.id'` (faltaba prefijo esquema)
  - `EntidadDiputacion`: Eliminado campo `provincia_id` inexistente, añadido `@property provincia`
  - Todos los modelos verificados para consistencia de esquemas
- ✅ **Corrección modelos según documentación:**
  - `EntidadDiputacion.codigo_dir3`: Cambiado a NOT NULL (según O_019)
  - `EntidadDiputacion.email_publicacion_bop`: VARCHAR(255) en lugar de 120
  - `EntidadDiputacion.observaciones`: Añadido campo TEXT faltante
  - Todos los modelos alineados con especificación de `docs/fuentesIA/referencias/tablas/`

**Funcionalidades implementadas:**
- ✅ 7 tablas operativas en base de datos PostgreSQL
- ✅ Arquitectura polimórfica funcional (tabla base + metadatos específicos)
- ✅ FKs cross-schema correctas (`public` ↔ `estructura`)
- ✅ Validaciones y métodos de negocio en modelos
- ✅ Properties calculadas (provincia, tiene_representante, etc.)
- ✅ Métodos estáticos de búsqueda y filtrado
- ✅ Cascada DELETE en metadatos (borrar entidad borra metadatos)
- ✅ Migración reversible (upgrade/downgrade testeado)

**Archivos creados:**
- `app/models/tipo_entidad.py`
- `app/models/entidad.py`
- `app/models/entidad_administrado.py`
- `app/models/entidad_empresa_servicio_publico.py`
- `app/models/entidad_organismo_publico.py`
- `app/models/entidad_ayuntamiento.py`
- `app/models/entidad_diputacion.py`
- `migrations/versions/c21871f08bb2_añadir_arquitectura_entidades_.py`

**Archivos modificados:**
- `app/models/__init__.py` (importación de 7 nuevos modelos)
- `docs/CHANGELOG.md`

**Verificaciones realizadas:**
- ✅ `flask db current` → `c21871f08bb2 (head)`
- ✅ Tablas creadas en PostgreSQL (7 tablas verificadas)
- ✅ Foreign keys correctas (7 FKs verificadas)
- ✅ Índices creados (12 índices verificados)
- ✅ `flask run` → Sin errores
- ✅ `flask db downgrade` → Rollback exitoso
- ✅ `flask db upgrade` → Reaplicación exitosa

**Issues resueltos:** #62 (Fase 2 - Modelos + Migración)  
**Milestone:** MS-3 - Alineación Administrativa  

**Próximas fases:**
- Fase 3: Tests unitarios e integración
- Fase 4: Interfaz CRUD entidades
- Fase 5: Datos maestros (INSERT en tipos_entidades)
- Fase 6: Migración de datos legacy (si aplica)

**Notas técnicas:**
- Migración manual preferida sobre autogenerate debido a complejidad de resolución de FKs cross-schema en SQLAlchemy/Alembic
- Todos los modelos siguen patrón de arquitectura documentado en Fase 1
- Sin cambios en tablas existentes, solo adición de nuevas

---

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
- ✅ **E_010 - ENTIDADES** (tabla base polimórfica):
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
- ✅ **Tablas.md**: Refactorizado completo con arquitectura polimórfica (7 tablas nuevas)
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

**Nota:** Este changelog se mantiene con los últimos 5 PRs. Entradas más antiguas se pueden consultar en el [historial de Pull Requests](https://github.com/genete/bddat/pulls?q=is%3Apr+is%3Aclosed+sort%3Aupdated-desc) de GitHub.
