# Definiciones de Tablas Principales v3.1

**Sistema de Tramitación de Expedientes de Alta Tensión (BDDAT)**  
**Formato agnóstico a la base de datos**  
**Fecha:** 04/02/2026  
**Generado automáticamente:** 04/02/2026 17:14 por merge_tables.py

---

## Índice

- [Filosofía del Diseño](#filosofía-del-diseño)
- [Tablas de Estructura](#tablas-de-estructura)
  - [MUNICIPIOS](#municipios)
  - [TIPOS_ENTIDAD](#tiposentidad)
  - [TIPOS_ENTIDADES](#tiposentidades)
  - [TIPOS_EXPEDIENTES](#tiposexpedientes)
  - [TIPOS_FASES](#tiposfases)
  - [TIPOS_IA](#tiposia)
  - [TIPOS_RESULTADOS_FASES](#tiposresultadosfases)
  - [TIPOS_SOLICITUDES](#tipossolicitudes)
  - [TIPOS_TAREAS](#tipostareas)
  - [TIPOS_TRAMITES](#tipostramites)
- [Tablas Operacionales](#tablas-operacionales)
  - [AUTORIZADOS_TITULAR](#autorizadostitular)
  - [DOCUMENTOS](#documentos)
  - [DOCUMENTOS_PROYECTO](#documentosproyecto)
  - [ENTIDADES](#entidades)
  - [ENTIDADES_ADMINISTRADOS](#entidadesadministrados)
  - [ENTIDADES_AYUNTAMIENTOS](#entidadesayuntamientos)
  - [ENTIDADES_DIPUTACIONES](#entidadesdiputaciones)
  - [ENTIDADES_EMPRESAS_SERVICIO_PUBLICO](#entidadesempresasserviciopublico)
  - [ENTIDADES_ORGANISMOS_PUBLICOS](#entidadesorganismospublicos)
  - [EXPEDIENTES](#expedientes)
  - [FASES](#fases)
  - [MUNICIPIOS_PROYECTO](#municipiosproyecto)
  - [PROYECTOS](#proyectos)
  - [ROLES](#roles)
  - [SOLICITUDES](#solicitudes)
  - [SOLICITUDES_TIPOS](#solicitudestipos)
  - [TAREAS](#tareas)
  - [TRAMITES](#tramites)
  - [USUARIOS](#usuarios)
  - [USUARIOS_ROLES](#usuariosroles)

---

## Filosofía del Diseño

### Arquitectura General v3.0

**Expediente:** Solo uno en el conjunto de expedientes de la organización.

**Proyecto:** Solo uno, vinculado desde expediente. Es decir `EXPEDIENTE.PROYECTO_ID` es lo que existe. Existe un proyecto por expediente en toda la organización.

**Solicitudes:** n, varias por expediente, pero con una particularidad: su relación con el proyecto se deduce del expediente, ya que solo hay uno.

**Documentos:** n por expediente. Una clave inversa hacia el expediente que vive en el documento: `DOCUMENTOS.EXPEDIENTE_ID` (1:n). El documento es agnóstico a quien pertenece excepto al expediente. No más claves en el documento.

### Relación Proyecto-Documentos

**¿Cómo saben su proyecto las tareas y documentos?**

- **Tareas:** Claves hacia el documento que la origina (`DOCUMENTO_USADO_ID`) y el documento que produce (`DOCUMENTO_PRODUCIDO_ID`).
- **Proyecto:** Nueva tabla `DOCUMENTOS_PROYECTO`. Ahí, además de meter la relación entre nuestro `proyecto_id` (el único del expediente) y los m documentos, podemos poner otros metadatos relativos al proyecto: principal, refundido, anexo, etc.

### Solicitudes y Proyecto

¿Cómo puedo saber qué proyecto es el que está solicitándose?

- La solicitud solicita el proyecto principal, con los documentos que existan en ese momento de solicitud (los documentos tienen fechas administrativas) asociados al único proyecto.
- ¿Qué pasa si la solicitud se archiva por cambio radical y se empieza de nuevo con otro modificado radical de proyecto que impide seguir con la solicitud? La solicitud muerta se queda con los documentos existentes a fecha de cierre.

### Documento como Entidad Pura

**DOCUMENTO ahora es:**

- Pool puro de archivos del expediente
- No sabe quién lo creó
- No sabe quién lo consume
- No sabe si es proyecto o no

**Las relaciones viven FUERA del documento.**

### Ventajas de la Arquitectura v3.0

#### 1. Documento como entidad pura

```
DOCUMENTO = archivo físico en el expediente
├─ No sabe de dónde viene
├─ No sabe a dónde va
└─ Solo sabe a qué expediente pertenece
```

#### 2. Relaciones unidireccionales claras

```
TAREA → apunta a → DOCUMENTO (usado/producido)
DOCUMENTO ← no apunta a → TAREA
```

No hay referencias circulares ni ambigüedad.

#### 3. Un documento puede ser usado por múltiples tareas

```
DOCUMENTO ID=100 (Solicitud AAP)
├─ Usado por TAREA ID=2  (ANALISIS inicial)
├─ Usado por TAREA ID=10 (ANALISIS complementario)
└─ Usado por TAREA ID=15 (ANALISIS final)
```

**Antes (con TAREA_DESTINO_ID en documento):**
- Un documento solo podía tener UN destino
- Si se reutilizaba, había que duplicar o gestionar estados

**Ahora:**
- Múltiples tareas pueden usar el mismo documento
- Consulta natural: `SELECT * FROM TAREAS WHERE DOCUMENTO_USADO_ID = ?`

#### 4. Un documento puede ser producido por una sola tarea

```sql
-- Validación de integridad:
-- Un documento solo puede tener UNA tarea que lo produjo
CREATE UNIQUE INDEX IX_TAREA_DOC_PRODUCIDO 
ON TAREAS(DOCUMENTO_PRODUCIDO_ID) 
WHERE DOCUMENTO_PRODUCIDO_ID IS NOT NULL;
```

**Semántica correcta:** Un documento tiene un único origen (la tarea que lo incorporó/generó).

#### 5. Coherencia con DOCUMENTOS_PROYECTO

```
DOCUMENTO ID=250 (Proyecto modificado)
├─ EXPEDIENTE_ID = 10 (único FK en documento)
├─ Usado/producido por TAREA → se define en TAREAS
└─ Es proyecto → se define en DOCUMENTOS_PROYECTO
```

**Tres planos independientes:**

1. **Pertenencia:** `DOCUMENTOS.EXPEDIENTE_ID`
2. **Flujo de tareas:** `TAREAS.DOCUMENTO_USADO_ID / DOCUMENTO_PRODUCIDO_ID`
3. **Rol en proyecto:** `DOCUMENTOS_PROYECTO.DOCUMENTO_ID`

Un mismo documento puede tener roles simultáneos:
- Ser producido por tarea INCORPORAR
- Ser usado por tarea ANALISIS
- Ser documento MODIFICADO del proyecto
- Pertenecer al expediente AT-2025-001

### Ejemplo de Flujo de Tareas

#### Tarea INCORPORAR

```
TAREA ID=1 (TIPO='INCORPORAR', TRAMITE_ID=5)
├─ DOCUMENTO_USADO_ID = NULL          (no consume documento previo)
└─ DOCUMENTO_PRODUCIDO_ID = 100       (incorpora documento externo al sistema)

DOCUMENTO ID=100 (EXPEDIENTE_ID=10)
└─ Archivo físico "Solicitud_AAP.pdf"
```

**Consulta inversa:** "¿Qué tarea incorporó este documento?"

```sql
SELECT * 
FROM TAREAS T
WHERE DOCUMENTO_PRODUCIDO_ID = 100
```

#### Tarea ANALISIS

```
TAREA ID=2 (TIPO='ANALISIS', TRAMITE_ID=5)
├─ DOCUMENTO_USADO_ID = 100           (analiza la solicitud)
└─ DOCUMENTO_PRODUCIDO_ID = 101       (genera informe de análisis)

DOCUMENTO ID=101 (EXPEDIENTE_ID=10)
└─ Archivo "Informe_Analisis_Tecnico.odt"
```

#### Tarea REDACTAR

```
TAREA ID=3 (TIPO='REDACTAR', TRAMITE_ID=6)
├─ DOCUMENTO_USADO_ID = 101           (opcional: se basa en informe previo)
└─ DOCUMENTO_PRODUCIDO_ID = 102       (genera borrador)

DOCUMENTO ID=102 (EXPEDIENTE_ID=10)
└─ Archivo "Borrador_Requerimiento.odt"
```

#### Tarea FIRMAR

```
TAREA ID=4 (TIPO='FIRMAR', TRAMITE_ID=6)
├─ DOCUMENTO_USADO_ID = 102           (transforma borrador)
└─ DOCUMENTO_PRODUCIDO_ID = 103       (genera documento firmado)

DOCUMENTO ID=103 (EXPEDIENTE_ID=10)
└─ Archivo "Requerimiento_Firmado.pdf"
```

#### Tarea NOTIFICAR

```
TAREA ID=5 (TIPO='NOTIFICAR', TRAMITE_ID=6)
├─ DOCUMENTO_USADO_ID = 103           (notifica el documento firmado)
└─ DOCUMENTO_PRODUCIDO_ID = 104       (genera justificante)

DOCUMENTO ID=104 (EXPEDIENTE_ID=10)
└─ Archivo "Acuse_Notificacion.pdf"
```

#### Tarea ESPERARPLAZO

```
TAREA ID=6 (TIPO='ESPERARPLAZO', TRAMITE_ID=6)
├─ DOCUMENTO_USADO_ID = NULL          (no maneja documentos)
└─ DOCUMENTO_PRODUCIDO_ID = NULL
```

---

---

## Tablas de Estructura

### MUNICIPIOS

Catálogo de municipios.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del municipio | NO | PK, autoincremental |
| **CODIGO** | VARCHAR(10) | Código INE del municipio | NO | Código oficial de 5 dígitos |
| **NOMBRE** | VARCHAR(200) | Nombre del municipio | NO | Denominación oficial |
| **PROVINCIA** | VARCHAR(100) | Provincia a la que pertenece | NO | Nombre de provincia |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `CODIGO`

#### Índices Recomendados

- `CODIGO` (búsqueda por código INE)
- `NOMBRE` (búsqueda alfabética)
- `PROVINCIA` (filtros por provincia)

#### Notas de Versión

- **v3.0:** Sin cambios estructurales.

#### Filosofía

Tabla maestra con el catálogo oficial de municipios:

- Basado en códigos INE oficiales
- Necesario para gestionar afecciones territoriales de proyectos
- Determina competencias administrativas y publicaciones en tablones

#### Relación con Otras Tablas

Usado en:
- `MUNICIPIOS_PROYECTO.MUNICIPIO_ID` (municipios afectados por proyectos)

---

---

### TIPOS_ENTIDAD

Catálogo de tipos de entidades del sistema con definición de roles permitidos.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del tipo de entidad | NO | PK, autoincremental |
| **CODIGO** | VARCHAR(50) | Código único identificativo del tipo | NO | UNIQUE. Valores: ADMINISTRADO, EMPRESA_SERVICIO_PUBLICO, ORGANISMO_PUBLICO, AYUNTAMIENTO, DIPUTACION |
| **NOMBRE** | VARCHAR(100) | Nombre descriptivo del tipo | NO | Para mostrar en interfaz de usuario |
| **TABLA_METADATOS** | VARCHAR(100) | Nombre de la tabla de metadatos asociada | NO | Tabla física donde residen metadatos específicos: entidades_administrados, entidades_empresas_servicio_publico, entidades_organismos_publicos, entidades_ayuntamientos, entidades_diputaciones |
| **PUEDE_SER_SOLICITANTE** | BOOLEAN | Indica si puede actuar como solicitante | NO | Default: FALSE. TRUE para tipos que pueden presentar solicitudes |
| **PUEDE_SER_CONSULTADO** | BOOLEAN | Indica si puede ser organismo consultado | NO | Default: FALSE. TRUE para tipos que pueden emitir informes en fase CONSULTAS |
| **PUEDE_PUBLICAR** | BOOLEAN | Indica si puede publicar (tablón/BOP) | NO | Default: FALSE. TRUE para tipos que pueden publicar anuncios oficiales |
| **DESCRIPCION** | TEXT | Descripción detallada del tipo de entidad | SÍ | Explicación de características y casos de uso |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `CODIGO`

#### Índices Recomendados

- `CODIGO` (búsqueda rápida por código)
- `(PUEDE_SER_SOLICITANTE, PUEDE_SER_CONSULTADO, PUEDE_PUBLICAR)` (filtros por capacidades)

#### Notas de Versión

- **v1.0** (01/02/2026): Creación inicial con 5 tipos de entidad y campos de roles

#### Filosofía

Tabla maestra que define los tipos de entidades del sistema y sus **capacidades de rol**:

- **Datos maestros estables:** Los 5 tipos no cambian, son parte de la lógica de negocio
- **Filtrado automático:** Los campos booleanos permiten filtrar entidades según contexto
- **Arquitectura tablas inversas:** Campo `TABLA_METADATOS` mapea tipo → tabla física de metadatos
- **Validación en tiempo de diseño:** La interfaz carga solo tipos válidos según operación

#### Tipos Definidos

| Código | Nombre | Tabla Metadatos | Solicitante | Consultado | Publicar |
|:---|:---|:---|:---:|:---:|:---:|
| **ADMINISTRADO** | Administrado | entidades_administrados | ✅ | ❌ | ❌ |
| **EMPRESA_SERVICIO_PUBLICO** | Empresa Servicio Público | entidades_empresas_servicio_publico | ✅ | ✅ | ❌ |
| **ORGANISMO_PUBLICO** | Organismo Público | entidades_organismos_publicos | ❌ | ✅ | ❌ |
| **AYUNTAMIENTO** | Ayuntamiento | entidades_ayuntamientos | ✅ | ✅ | ✅ |
| **DIPUTACION** | Diputación Provincial | entidades_diputaciones | ❌ | ✅ | ✅ |

#### Descripción de Tipos

**ADMINISTRADO:**
- Personas físicas o jurídicas privadas
- Roles: Titular de expediente, Solicitante, Autorizado en solicitud
- Ejemplos: Ciudadanos, empresas promotoras, comunidades de bienes
- Notificaciones: Sistema Notifica (email_notificaciones)

**EMPRESA_SERVICIO_PUBLICO:**
- Operadores de infraestructuras críticas y servicios públicos
- Roles: Solicitante (instalaciones propias) + Organismo consultado (afecciones)
- Ejemplos: Enagas, E-Distribución, REE, Consorcios de Aguas, operadores ferroviarios
- Características: Pueden tener instalaciones propias Y deben informar sobre afecciones a sus infraestructuras

**ORGANISMO_PUBLICO:**
- Administraciones públicas y organismos oficiales
- Roles: Solo organismo consultado (informes técnicos/administrativos)
- Ejemplos: Consejerías Junta Andalucía, Ministerios, Confederaciones Hidrográficas, ADIF, Defensa, AESA, Patrimonio
- Notificaciones: Sistema SIR (codigo_dir3) o BandeJA

**AYUNTAMIENTO:**
- Corporaciones locales municipales
- Roles: Solicitante (ocasional) + Organismo consultado + Publicador (tablón edictos)
- Múltiples capacidades según contexto
- Notificaciones: SIR (codigo_dir3) cuando actúa como organismo, Notifica cuando actúa como solicitante

**DIPUTACION:**
- Corporaciones provinciales
- Roles: Organismo consultado + Publicador (Boletín Oficial Provincial)
- No suelen ser solicitantes
- Notificaciones: SIR (codigo_dir3)

#### Uso en Filtrado de Interfaz

**Contexto: Crear solicitud**
```sql
-- Cargar solo entidades que pueden ser solicitantes
SELECT e.* 
FROM entidades e
JOIN tipos_entidad te ON e.tipo_entidad_id = te.id
WHERE te.puede_ser_solicitante = TRUE
AND e.activo = TRUE
ORDER BY e.nombre_completo;
```

**Contexto: Fase CONSULTAS - Solicitar informe**
```sql
-- Cargar solo entidades que pueden emitir informes
SELECT e.* 
FROM entidades e
JOIN tipos_entidad te ON e.tipo_entidad_id = te.id
WHERE te.puede_ser_consultado = TRUE
AND e.activo = TRUE
ORDER BY te.codigo, e.nombre_completo;
```

**Contexto: Publicar en tablón municipal**
```sql
-- Cargar solo ayuntamientos
SELECT e.* 
FROM entidades e
JOIN tipos_entidad te ON e.tipo_entidad_id = te.id
WHERE te.codigo = 'AYUNTAMIENTO'
AND e.activo = TRUE
ORDER BY e.nombre_completo;
```

**Contexto: Publicar en BOP**
```sql
-- Cargar solo diputaciones
SELECT e.* 
FROM entidades e
JOIN tipos_entidad te ON e.tipo_entidad_id = te.id
WHERE te.codigo = 'DIPUTACION'
AND e.activo = TRUE
ORDER BY e.nombre_completo;
```

#### Validaciones en Lógica de Negocio

**Al crear solicitud:**
```python
# Validar que tipo_entidad puede ser solicitante
if not solicitante.tipo_entidad.puede_ser_solicitante:
    raise ValidationError("Este tipo de entidad no puede ser solicitante")
```

**Al solicitar informe en fase CONSULTAS:**
```python
# Validar que tipo_entidad puede ser consultado
if not organismo.tipo_entidad.puede_ser_consultado:
    raise ValidationError("Este tipo de entidad no puede emitir informes")
```

**Al publicar en tablón:**
```python
# Validar que tipo_entidad puede publicar
if not entidad_publicadora.tipo_entidad.puede_publicar:
    raise ValidationError("Este tipo de entidad no puede publicar anuncios")
```

#### Datos Maestros

```sql
INSERT INTO tipos_entidad (codigo, nombre, tabla_metadatos, puede_ser_solicitante, puede_ser_consultado, puede_publicar, descripcion) VALUES
(
    'ADMINISTRADO', 
    'Administrado', 
    'entidades_administrados', 
    TRUE, 
    FALSE, 
    FALSE,
    'Personas físicas o jurídicas privadas. Roles: Titular, Solicitante, Autorizado. Notificaciones vía Notifica.'
),
(
    'EMPRESA_SERVICIO_PUBLICO', 
    'Empresa Servicio Público', 
    'entidades_empresas_servicio_publico', 
    TRUE, 
    TRUE, 
    FALSE,
    'Operadores de infraestructuras críticas (Enagas, E-Distribución, REE, Consorcios Aguas). Pueden ser solicitantes Y emitir informes sobre afecciones.'
),
(
    'ORGANISMO_PUBLICO', 
    'Organismo Público', 
    'entidades_organismos_publicos', 
    FALSE, 
    TRUE, 
    FALSE,
    'Administraciones públicas (Junta, Ministerios, Confederaciones, ADIF, Defensa, AESA). Solo emiten informes. Notificaciones vía SIR/BandeJA (DIR3).'
),
(
    'AYUNTAMIENTO', 
    'Ayuntamiento', 
    'entidades_ayuntamientos', 
    TRUE, 
    TRUE, 
    TRUE,
    'Corporaciones locales. Múltiples roles: solicitante ocasional, organismo consultado, publicador (tablón edictos). Notificaciones vía SIR (DIR3) o Notifica según rol.'
),
(
    'DIPUTACION', 
    'Diputación Provincial', 
    'entidades_diputaciones', 
    FALSE, 
    TRUE, 
    TRUE,
    'Corporaciones provinciales. Roles: organismo consultado, publicador BOP. Notificaciones vía SIR (DIR3).'
);
```

#### Relación con Otras Tablas

Usado en:
- `ENTIDADES.TIPO_ENTIDAD_ID` (clasificación de entidad)

Relacionado con:
- `ENTIDADES_ADMINISTRADOS.ENTIDAD_ID` (metadatos si tipo = ADMINISTRADO)
- `ENTIDADES_EMPRESAS_SERVICIO_PUBLICO.ENTIDAD_ID` (metadatos si tipo = EMPRESA_SERVICIO_PUBLICO)
- `ENTIDADES_ORGANISMOS_PUBLICOS.ENTIDAD_ID` (metadatos si tipo = ORGANISMO_PUBLICO)
- `ENTIDADES_AYUNTAMIENTOS.ENTIDAD_ID` (metadatos si tipo = AYUNTAMIENTO)
- `ENTIDADES_DIPUTACIONES.ENTIDAD_ID` (metadatos si tipo = DIPUTACION)

#### Reglas de Negocio

1. **Tabla inmutable:** Los 5 tipos son parte de la lógica de negocio. No añadir/eliminar tipos en runtime
2. **Código estable:** `CODIGO` no debe cambiar (ruptura de lógica en código Python)
3. **Una entidad, múltiples roles:** Una misma entidad puede tener registro en múltiples tablas `entidades_*` si su tipo lo permite (ej: Ayuntamiento puede estar en `entidades_ayuntamientos` Y en `entidades_administrados` si alguna vez actúa como solicitante)
4. **Validación obligatoria:** Siempre validar capacidades antes de asignar roles
5. **Filtrado por defecto:** Interfaces deben filtrar automáticamente según contexto usando campos `PUEDE_SER_*`

---

---

### TIPOS_ENTIDADES

Catálogo de tipos de entidades del sistema con definición de roles permitidos.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del tipo de entidad | NO | PK, autoincremental |
| **CODIGO** | VARCHAR(50) | Código único identificativo del tipo | NO | UNIQUE. Valores: ADMINISTRADO, EMPRESA_SERVICIO_PUBLICO, ORGANISMO_PUBLICO, AYUNTAMIENTO, DIPUTACION |
| **NOMBRE** | VARCHAR(100) | Nombre descriptivo del tipo | NO | Para mostrar en interfaz de usuario |
| **TABLA_METADATOS** | VARCHAR(100) | Nombre de la tabla de metadatos asociada | NO | Tabla física donde residen metadatos específicos: entidades_administrados, entidades_empresas_servicio_publico, entidades_organismos_publicos, entidades_ayuntamientos, entidades_diputaciones |
| **PUEDE_SER_SOLICITANTE** | BOOLEAN | Indica si puede actuar como solicitante | NO | Default: FALSE. TRUE para tipos que pueden presentar solicitudes |
| **PUEDE_SER_CONSULTADO** | BOOLEAN | Indica si puede ser organismo consultado | NO | Default: FALSE. TRUE para tipos que pueden emitir informes en fase CONSULTAS |
| **PUEDE_PUBLICAR** | BOOLEAN | Indica si puede publicar (tablón/BOP) | NO | Default: FALSE. TRUE para tipos que pueden publicar anuncios oficiales |
| **DESCRIPCION** | TEXT | Descripción detallada del tipo de entidad | SÍ | Explicación de características y casos de uso |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `CODIGO`

#### Índices Recomendados

- `CODIGO` (búsqueda rápida por código)
- `(PUEDE_SER_SOLICITANTE, PUEDE_SER_CONSULTADO, PUEDE_PUBLICAR)` (filtros por capacidades)

#### Notas de Versión

- **v1.0** (01/02/2026): Creación inicial con 5 tipos de entidad y campos de roles

#### Filosofía

Tabla maestra que define los tipos de entidades del sistema y sus **capacidades de rol**:

- **Datos maestros estables:** Los 5 tipos no cambian, son parte de la lógica de negocio
- **Filtrado automático:** Los campos booleanos permiten filtrar entidades según contexto
- **Arquitectura tablas inversas:** Campo `TABLA_METADATOS` mapea tipo → tabla física de metadatos
- **Validación en tiempo de diseño:** La interfaz carga solo tipos válidos según operación

#### Tipos Definidos

| Código | Nombre | Tabla Metadatos | Solicitante | Consultado | Publicar |
|:---|:---|:---|:---:|:---:|:---:|
| **ADMINISTRADO** | Administrado | entidades_administrados | ✅ | ❌ | ❌ |
| **EMPRESA_SERVICIO_PUBLICO** | Empresa Servicio Público | entidades_empresas_servicio_publico | ✅ | ✅ | ❌ |
| **ORGANISMO_PUBLICO** | Organismo Público | entidades_organismos_publicos | ✅ | ✅ | ❌ |
| **AYUNTAMIENTO** | Ayuntamiento | entidades_ayuntamientos | ✅ | ✅ | ✅ |
| **DIPUTACION** | Diputación Provincial | entidades_diputaciones | ✅ | ✅ | ✅ |

#### Descripción de Tipos

**ADMINISTRADO:**
- Personas físicas o jurídicas privadas
- Roles: Titular de expediente, Solicitante, Autorizado en solicitud
- Ejemplos: Ciudadanos, empresas promotoras, comunidades de bienes
- Notificaciones: Sistema Notifica (email_notificaciones)

**EMPRESA_SERVICIO_PUBLICO:**
- Operadores de infraestructuras críticas y servicios públicos
- Roles: Solicitante (instalaciones propias) + Organismo consultado (afecciones)
- Ejemplos: Enagas, E-Distribución, REE, Consorcios de Aguas, operadores ferroviarios
- Características: Pueden tener instalaciones propias Y deben informar sobre afecciones a sus infraestructuras

**ORGANISMO_PUBLICO:**
- Administraciones públicas y organismos oficiales
- Roles: Organismo consultado + Solicitante ocasional (casos excepcionales)
- Ejemplos: Consejerías Junta Andalucía, Ministerios, Confederaciones Hidrográficas, ADIF, Defensa, AESA, Patrimonio
- Casos solicitante: Consejería Medio Ambiente autoriza instalación eléctrica en depuradora propia
- Notificaciones: Sistema SIR (codigo_dir3) o BandeJA cuando actúan como organismo; Notifica cuando actúan como solicitante

**AYUNTAMIENTO:**
- Corporaciones locales municipales
- Roles: Solicitante (ocasional) + Organismo consultado + Publicador (tablón edictos)
- Múltiples capacidades según contexto
- Notificaciones: SIR (codigo_dir3) cuando actúa como organismo, Notifica cuando actúa como solicitante

**DIPUTACION:**
- Corporaciones provinciales
- Roles: Solicitante ocasional + Organismo consultado + Publicador (Boletín Oficial Provincial)
- Casos solicitante: Construye infraestructuras para ayuntamientos (da servicio a municipios)
- Notificaciones: SIR (codigo_dir3) cuando actúa como organismo, Notifica cuando actúa como solicitante

#### Uso en Filtrado de Interfaz

**Contexto: Crear solicitud**
```sql
-- Cargar solo entidades que pueden ser solicitantes
SELECT e.* 
FROM entidades e
JOIN tipos_entidades te ON e.tipo_entidad_id = te.id
WHERE te.puede_ser_solicitante = TRUE
AND e.activo = TRUE
ORDER BY e.nombre_completo;
```

**Contexto: Fase CONSULTAS - Solicitar informe**
```sql
-- Cargar solo entidades que pueden emitir informes
SELECT e.* 
FROM entidades e
JOIN tipos_entidades te ON e.tipo_entidad_id = te.id
WHERE te.puede_ser_consultado = TRUE
AND e.activo = TRUE
ORDER BY te.codigo, e.nombre_completo;
```

**Contexto: Publicar en tablón municipal**
```sql
-- Cargar solo ayuntamientos
SELECT e.* 
FROM entidades e
JOIN tipos_entidades te ON e.tipo_entidad_id = te.id
WHERE te.codigo = 'AYUNTAMIENTO'
AND e.activo = TRUE
ORDER BY e.nombre_completo;
```

**Contexto: Publicar en BOP**
```sql
-- Cargar solo diputaciones
SELECT e.* 
FROM entidades e
JOIN tipos_entidades te ON e.tipo_entidad_id = te.id
WHERE te.codigo = 'DIPUTACION'
AND e.activo = TRUE
ORDER BY e.nombre_completo;
```

#### Validaciones en Lógica de Negocio

**Al crear solicitud:**
```python
# Validar que tipo_entidad puede ser solicitante
if not solicitante.tipo_entidad.puede_ser_solicitante:
    raise ValidationError("Este tipo de entidad no puede ser solicitante")
```

**Al solicitar informe en fase CONSULTAS:**
```python
# Validar que tipo_entidad puede ser consultado
if not organismo.tipo_entidad.puede_ser_consultado:
    raise ValidationError("Este tipo de entidad no puede emitir informes")
```

**Al publicar en tablón:**
```python
# Validar que tipo_entidad puede publicar
if not entidad_publicadora.tipo_entidad.puede_publicar:
    raise ValidationError("Este tipo de entidad no puede publicar anuncios")
```

#### Datos Maestros

```sql
INSERT INTO tipos_entidades (codigo, nombre, tabla_metadatos, puede_ser_solicitante, puede_ser_consultado, puede_publicar, descripcion) VALUES
(
    'ADMINISTRADO', 
    'Administrado', 
    'entidades_administrados', 
    TRUE, 
    FALSE, 
    FALSE,
    'Personas físicas o jurídicas privadas. Roles: Titular, Solicitante, Autorizado. Notificaciones vía Notifica.'
),
(
    'EMPRESA_SERVICIO_PUBLICO', 
    'Empresa Servicio Público', 
    'entidades_empresas_servicio_publico', 
    TRUE, 
    TRUE, 
    FALSE,
    'Operadores de infraestructuras críticas (Enagas, E-Distribución, REE, Consorcios Aguas). Pueden ser solicitantes Y emitir informes sobre afecciones.'
),
(
    'ORGANISMO_PUBLICO', 
    'Organismo Público', 
    'entidades_organismos_publicos', 
    TRUE, 
    TRUE, 
    FALSE,
    'Administraciones públicas (Junta, Ministerios, Confederaciones, ADIF, Defensa, AESA). Emiten informes. Excepcionalmente solicitantes (ej: depuradoras). Notificaciones vía SIR/BandeJA (DIR3) como organismo, Notifica como solicitante.'
),
(
    'AYUNTAMIENTO', 
    'Ayuntamiento', 
    'entidades_ayuntamientos', 
    TRUE, 
    TRUE, 
    TRUE,
    'Corporaciones locales. Múltiples roles: solicitante ocasional, organismo consultado, publicador (tablón edictos). Notificaciones vía SIR (DIR3) como organismo, Notifica como solicitante.'
),
(
    'DIPUTACION', 
    'Diputación Provincial', 
    'entidades_diputaciones', 
    TRUE, 
    TRUE, 
    TRUE,
    'Corporaciones provinciales. Roles: solicitante ocasional (construyen para ayuntamientos), organismo consultado, publicador BOP. Notificaciones vía SIR (DIR3) como organismo, Notifica como solicitante.'
);
```

#### Relación con Otras Tablas

Usado en:
- `ENTIDADES.TIPO_ENTIDAD_ID` (clasificación de entidad)

Relacionado con:
- `ENTIDADES_ADMINISTRADOS.ENTIDAD_ID` (metadatos si tipo = ADMINISTRADO o cualquier tipo que actúe como solicitante)
- `ENTIDADES_EMPRESAS_SERVICIO_PUBLICO.ENTIDAD_ID` (metadatos si tipo = EMPRESA_SERVICIO_PUBLICO)
- `ENTIDADES_ORGANISMOS_PUBLICOS.ENTIDAD_ID` (metadatos si tipo = ORGANISMO_PUBLICO)
- `ENTIDADES_AYUNTAMIENTOS.ENTIDAD_ID` (metadatos si tipo = AYUNTAMIENTO)
- `ENTIDADES_DIPUTACIONES.ENTIDAD_ID` (metadatos si tipo = DIPUTACION)

#### Reglas de Negocio

1. **Tabla inmutable:** Los 5 tipos son parte de la lógica de negocio. No añadir/eliminar tipos en runtime
2. **Código estable:** `CODIGO` no debe cambiar (ruptura de lógica en código Python)
3. **Una entidad, múltiples roles:** Una misma entidad puede tener registro en múltiples tablas `entidades_*` si su tipo lo permite (ej: Consejería Medio Ambiente puede estar en `entidades_organismos_publicos` Y en `entidades_administrados` cuando solicita instalación en depuradora)
4. **Validación obligatoria:** Siempre validar capacidades antes de asignar roles
5. **Filtrado por defecto:** Interfaces deben filtrar automáticamente según contexto usando campos `PUEDE_SER_*`

---

---

### TIPOS_EXPEDIENTES

Clasificación normativa de expedientes.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del tipo de expediente | NO | PK, autoincremental |
| **TIPO** | VARCHAR(100) | Denominación del tipo de expediente | SÍ | Nombre descriptivo del tipo según clasificación normativa |
| **DESCRIPCION** | VARCHAR(200) | Descripción detallada del tipo | SÍ | Explicación de las características y particularidades procedimentales |

#### Claves

- **PK:** `ID`

#### Índices Recomendados

- `TIPO` (búsqueda y ordenación alfabética)

#### Notas de Versión

- **v3.0:** Sin cambios estructurales. Tabla maestra estable.

#### Filosofía

Tabla maestra que define la clasificación de expedientes según normativa:

- Combina tipo de titular (particular, empresa distribuidora, productor) y tipo de instalación
- Determina procedimientos aplicables y restricciones según legislación sectorial
- La semntica procedimental vive en esta tabla, no en campos de `EXPEDIENTES`

#### Uso en Reglas de Negocio

El `TIPO_EXPEDIENTE_ID` es clave para determinar:

- Qué solicitudes son aplicables (AAP, AAC, DUP, etc.)
- Qué fases son obligatorias (consulta Ministerio solo para transporte)
- Qué organismos deben ser consultados
- Requisitos de información pública
- Instrumentos ambientales aplicables

#### Relación con Otras Tablas

Usado en:
- `EXPEDIENTES.TIPO_EXPEDIENTE_ID` (clasificación del expediente)

Relacionado con motor de reglas:
- Tablas de configuración de lógica de negocio que determinan flujos según tipo

---

---

### TIPOS_FASES

Catálogo de fases procedimentales.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del tipo de fase | NO | PK, autoincremental |
| **CODIGO** | VARCHAR(50) | Código único identificativo de la fase | NO | Código normalizado sin espacios: ADMISIBILIDAD, CONSULTAS, INFORMACION_PUBLICA, etc. |
| **NOMBRE** | VARCHAR(200) | Denominación completa de la fase | NO | Nombre descriptivo legible para interfaz de usuario |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `CODIGO`

#### Índices Recomendados

- `CODIGO` (búsqueda rápida y validaciones)

#### Notas de Versión

- **v3.0:** Sin cambios estructurales. Tabla maestra estable.

#### Filosofía

Tabla maestra que define las fases procedimentales de tramitación administrativa:

- Basadas en estructura normativa del procedimiento administrativo eléctrico
- Cada fase agrupa trámites relacionados con un objetivo procedimental concreto
- El `CODIGO` es la referencia estable para reglas de negocio (no cambiar una vez en producción)

#### Uso en Reglas de Negocio

El `TIPO_FASE_ID` determina:

- Secuencia obligatoria de fases según `TIPO_SOLICITUD_ID`
- Trámites posibles dentro de la fase
- Requisitos de finalización
- Dependencias con fases anteriores

#### Relación con Otras Tablas

Usado en:
- `FASES.TIPO_FASE_ID` (clasificación de la fase)

Relacionado con motor de reglas:
- Tablas de configuración que definen secuencias y dependencias de fases

---

---

### TIPOS_IA

Tipos de instrumentos ambientales aplicables.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del tipo de IA | NO | PK, autoincremental |
| **SIGLAS** | VARCHAR(50) | Siglas del instrumento ambiental | NO | AAU, AAUS, CA, NO_SUJETO, etc. |
| **NOMBRE** | VARCHAR(200) | Denominación completa del instrumento | NO | Autorización Ambiental Unificada, Comunicación Ambiental, etc. |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `SIGLAS`

#### Índices Recomendados

- `SIGLAS` (búsqueda rápida)

#### Notas de Versión

- **v3.0:** Sin cambios estructurales.

#### Filosofía

Tabla maestra que define los instrumentos ambientales según normativa vigente:

- Determina qué trámites ambientales son necesarios
- Define organismos competentes
- Establece plazos y requisitos documentales específicos

#### Relación con Otras Tablas

Usado en:
- `PROYECTOS.IA_ID` (instrumento ambiental del proyecto)

---

---

### TIPOS_RESULTADOS_FASES

Catálogo de resultados posibles de fases.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del tipo de resultado | NO | PK, autoincremental |
| **CODIGO** | VARCHAR(50) | Código del resultado | NO | FAVORABLE, DESFAVORABLE, CONDICIONADO, SIN_PRONUNCIAMIENTO, etc. |
| **NOMBRE** | VARCHAR(200) | Denominación del resultado | NO | Descripción legible |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `CODIGO`

#### Índices Recomendados

- `CODIGO` (búsqueda rápida)

#### Notas de Versión

- **v3.0:** Sin cambios estructurales.

#### Filosofía

Tabla maestra que define los posibles resultados de las fases:

- Determina si la fase tuvo éxito procedimental
- Condiciona las fases siguientes según reglas de negocio
- El técnico debe evaluar manualmente el resultado tras analizar documentos

#### Relación con Otras Tablas

Usado en:
- `FASES.RESULTADO_FASE_ID` (resultado de la fase)

---

## Resumen Final

**Tablas Operacionales:** 9  
**Tablas Maestras:** 9  
**Total:** 18 tablas

### Principios v3.0

1. **Minimalismo estructural:** Tablas con campos mínimos, semántica en tipos
2. **Documento agnóstico:** Solo `EXPEDIENTE_ID` como FK
3. **Relaciones unidireccionales:** TAREA → DOCUMENTO (no al revés)
4. **Estados deducibles:** No almacenar lo que se puede calcular
5. **Fechas administrativas:** Fechas con efectos legales, no técnicas
6. **Fuente de verdad única:** No duplicar información
7. **Configurabilidad:** Lógica de negocio en motor de reglas, no hardcoded

---

**Versión:** 3.0  
**Fecha:** 30 de diciembre de 2025  
**Proyecto:** BDDAT - Sistema de Tramitación de Expedientes de Alta Tensión

---

### TIPOS_SOLICITUDES

Tipos de actos administrativos solicitables.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del tipo de solicitud | NO | PK, autoincremental |
| **SIGLAS** | VARCHAR(100) | Siglas o código del tipo de solicitud | SÍ | Abreviatura normalizada: AAP, AAC, MOD, DUP, etc. |
| **DESCRIPCION** | VARCHAR(200) | Descripción completa del tipo de solicitud | SÍ | Denominación legal del acto administrativo solicitado |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `SIGLAS` (recomendado para evitar duplicados)

#### Índices Recomendados

- `SIGLAS` (búsqueda rápida por código)

#### Notas de Versión

- **v3.0:** Sin cambios estructurales. Tabla maestra estable.

#### Filosofía

Tabla maestra que define los tipos de actos administrativos que pueden solicitarse:

- Basados en nomenclatura legal establecida en normativa sectorial eléctrica
- Cada tipo tiene procedimiento, requisitos y efectos jurídicos específicos
- Determinan qué fases son obligatorias para tramitar la solicitud

#### Tipos Especiales

**DESISTIMIENTO y RENUNCIA:**

- Solicitudes que afectan a otra solicitud previa
- Requieren campo `SOLICITUD_AFECTADA_ID` NOT NULL en `SOLICITUDES`
- Finalizan la solicitud referenciada sin resolución de fondo

#### Uso en Reglas de Negocio

El `TIPO_SOLICITUD_ID` determina:

- Fases obligatorias del procedimiento (AAP: ADMISIBILIDAD, ANALISIS_TECNICO, CONSULTAS, INFORMACION_PUBLICA, RESOLUCION)
- Requisitos documentales (proyectos, estudios ambientales, etc.)
- Plazos máximos de resolución
- Posibilidad de silencio administrativo (positivo/negativo)
- Compatibilidad con otras solicitudes del mismo expediente

#### Relación con Otras Tablas

Usado en:
- `SOLICITUDES.TIPO_SOLICITUD_ID` (clasificación de la solicitud)

Relacionado con motor de reglas:
- Tablas de configuración que definen fases obligatorias por tipo de solicitud
- Validaciones de secuencia (MOD requiere AAC previa concedida)

---

---

### TIPOS_TAREAS

Catálogo de tipos atómicos de tareas.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del tipo de tarea | NO | PK, autoincremental |
| **CODIGO** | VARCHAR(50) | Código único identificativo de la tarea | NO | Valores: INCORPORAR, ANALISIS, REDACTAR, FIRMAR, NOTIFICAR, PUBLICAR, ESPERARPLAZO |
| **NOMBRE** | VARCHAR(200) | Denominación completa de la tarea | NO | Nombre descriptivo |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `CODIGO`

#### Índices Recomendados

- `CODIGO` (búsqueda rápida)

#### Notas de Versión

- **v3.0:** Sin cambios estructurales. **Solo 7 tipos atómicos**.

#### Filosofía

Tabla maestra que define los **7 tipos atómicos** de tareas:

1. **INCORPORAR:** Incorpora documento externo al sistema
2. **ANALISIS:** Analiza documento y genera informe
3. **REDACTAR:** Redacta borrador de documento
4. **FIRMAR:** Firma documento (transforma borrador en oficial)
5. **NOTIFICAR:** Notifica documento y genera justificante
6. **PUBLICAR:** Publica documento y genera justificante
7. **ESPERARPLAZO:** Espera transcurso de plazo administrativo

Estos 7 tipos cubren todas las operaciones administrativas posibles en la tramitación.

#### Relación con Otras Tablas

Usado en:
- `TAREAS.TIPO_TAREA_ID` (clasificación de la tarea)

---

---

### TIPOS_TRAMITES

Catálogo de trámites administrativos.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del tipo de trámite | NO | PK, autoincremental |
| **CODIGO** | VARCHAR(50) | Código único identificativo del trámite | NO | Código normalizado: SOLICITUD_INFORME, ANUNCIO_BOP, RECEPCION_ALEGACION, etc. |
| **NOMBRE** | VARCHAR(200) | Denominación completa del trámite | NO | Nombre descriptivo legible |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `CODIGO`

#### Índices Recomendados

- `CODIGO` (búsqueda rápida)

#### Notas de Versión

- **v3.0:** Sin cambios estructurales. Tabla maestra estable.

#### Filosofía

Tabla maestra que define los trámites administrativos:

- Cada trámite representa una actuación administrativa concreta
- Define patrones de tareas esperados (no hardcoded, mediante reglas)
- El `CODIGO` es la referencia para identificar el tipo en reglas de negocio

#### Patrones de Tareas

Cada `TIPO_TRAMITE` sugiere un patrón de tareas (definido en motor de reglas):

- **SOLICITUD_INFORME:** REDACTAR → FIRMAR → NOTIFICAR → ESPERARPLAZO
- **RECEPCION_INFORME:** INCORPORAR → ANALISIS
- **ANUNCIO_BOP:** REDACTAR → FIRMAR → NOTIFICAR → ESPERARPLAZO → INCORPORAR → ESPERARPLAZO

#### Relación con Otras Tablas

Usado en:
- `TRAMITES.TIPO_TRAMITE_ID` (clasificación del trámite)

---

---

## Tablas Operacionales

### AUTORIZADOS_TITULAR

Tabla de relación N:N que registra las autorizaciones entre administrados. Permite que un titular (administrado) autorice a otro administrado para actuar en su nombre en la tramitación de expedientes. Sustituye el concepto legacy de la tabla `administrados` en las relaciones de autorización.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del registro de autorización | NO | PK, autoincremental |
| **TITULAR_ENTIDAD_ID** | INTEGER | Administrado titular que concede la autorización | NO | FK → ENTIDADES(ID). Debe tener entrada en ENTIDADES_ADMINISTRADOS |
| **AUTORIZADO_ENTIDAD_ID** | INTEGER | Administrado autorizado para representar al titular | NO | FK → ENTIDADES(ID). Debe tener entrada en ENTIDADES_ADMINISTRADOS |
| **ACTIVO** | BOOLEAN | Indica si la autorización está vigente | NO | Default: TRUE. Permite revocación sin borrar historial |
| **OBSERVACIONES** | TEXT | Notas libres del tramitador sobre la autorización | SÍ | Usos: ámbito (expediente específico/general), periodo de vigencia, motivo de desactivación |
| **CREATED_AT** | TIMESTAMP | Fecha y hora de creación del registro | NO | Default: NOW() |
| **UPDATED_AT** | TIMESTAMP | Fecha y hora de última actualización | NO | Default: NOW(), auto-update |

#### Claves

- **PK:** `ID`
- **FK:**
  - `TITULAR_ENTIDAD_ID` → `ENTIDADES(ID)` ON DELETE CASCADE
  - `AUTORIZADO_ENTIDAD_ID` → `ENTIDADES(ID)` ON DELETE CASCADE
- **UNIQUE:** `(TITULAR_ENTIDAD_ID, AUTORIZADO_ENTIDAD_ID)`

#### Índices Recomendados

- `TITULAR_ENTIDAD_ID` (consulta "¿quién puede actuar por este titular?")
- `AUTORIZADO_ENTIDAD_ID` (consulta "¿por quién puede actuar este autorizado?")
- `ACTIVO` (filtros por estado)
- `(TITULAR_ENTIDAD_ID, ACTIVO)` (consultas combinadas más frecuentes)

#### Constraints

```sql
-- No puede autorizarse a sí mismo
CONSTRAINT chk_no_autoautorizacion 
    CHECK (titular_entidad_id != autorizado_entidad_id)

-- Evitar duplicados
CONSTRAINT uq_titular_autorizado 
    UNIQUE (titular_entidad_id, autorizado_entidad_id)
```

#### Relaciones

- **titular**: ENTIDADES.id (FK, administrado que concede autorización)
- **autorizado**: ENTIDADES.id (FK, administrado que recibe autorización)

#### Notas de Versión

- **v1.0** (03/02/2026): Creación inicial. Sustituye relaciones legacy de tabla `administrados`

#### Filosofía

Esta tabla implementa el concepto de **representación legal/comercial** en el sistema:

- **Relación N:N**: Un titular puede autorizar a múltiples administrados, y un administrado puede estar autorizado por múltiples titulares
- **Borrado lógico**: `ACTIVO = FALSE` permite revocar sin perder historial
- **Validación en lógica de negocio**: Ambas entidades deben tener entrada en `ENTIDADES_ADMINISTRADOS`
- **Autoautorización implícita**: El titular SIEMPRE puede actuar por sí mismo (no requiere entrada en esta tabla)

#### Casos de Uso

**1. Consultora autorizada permanentemente**
```sql
INSERT INTO autorizados_titular (titular_entidad_id, autorizado_entidad_id, activo, observaciones)
VALUES (
    123,  -- E-Distribución
    456,  -- Consultora ACME SL
    TRUE,
    'Autorización general permanente para todos los expedientes'
);
```

**2. Autorización específica para un expediente**
```sql
INSERT INTO autorizados_titular (titular_entidad_id, autorizado_entidad_id, activo, observaciones)
VALUES (
    789,  -- Empresa Solar XYZ
    456,  -- Consultora ACME SL
    TRUE,
    'Autorización específica para expediente AT-2024-1234 (Planta fotovoltaica)'
);
```

**3. Revocación de autorización**
```sql
UPDATE autorizados_titular
SET activo = FALSE,
    observaciones = observaciones || ' | REVOCADA el 2026-02-03 por cambio de contrato',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 42;
```

#### Consultas Frecuentes

**¿Quién puede actuar en nombre del titular X?**
```sql
SELECT 
    e.id,
    e.nombre_completo,
    e.cif_nif,
    at.created_at AS autorizado_desde,
    at.observaciones
FROM autorizados_titular at
JOIN entidades e ON e.id = at.autorizado_entidad_id
WHERE at.titular_entidad_id = 123
  AND at.activo = TRUE;
```

**¿En nombre de qué titulares puede actuar el autorizado Y?**
```sql
SELECT 
    e.id,
    e.nombre_completo,
    e.cif_nif,
    at.created_at AS autorizado_desde,
    at.observaciones
FROM autorizados_titular at
JOIN entidades e ON e.id = at.titular_entidad_id
WHERE at.autorizado_entidad_id = 456
  AND at.activo = TRUE;
```

#### Reglas de Negocio

1. **Validación de administrados**: Antes de insertar, validar que ambas entidades tengan entrada en `ENTIDADES_ADMINISTRADOS`
2. **Autoautorización implícita**: El titular puede actuar por sí mismo sin entrada en esta tabla
   ```python
   def puede_actuar_como(entidad_id, titular_id):
       if entidad_id == titular_id:
           return True  # Autoautorización implícita
       return AutorizadoTitular.query.filter_by(
           titular_entidad_id=titular_id,
           autorizado_entidad_id=entidad_id,
           activo=True
       ).first() is not None
   ```
3. **Borrado lógico**: Nunca DELETE físico, siempre `ACTIVO = FALSE`
4. **Auditoría**: Mantener historial de autorizaciones revocadas
5. **Campo OBSERVACIONES flexible**: Permite registrar metadatos sin modificar schema:
   - Ámbito: "Expediente AT-2024-1234" vs "General"
   - Vigencia temporal: "Válida hasta 31/12/2026"
   - Motivo de desactivación: "Fin de contrato"
   - Tipo de poder: "Apoderado con poder notarial nº 123/2024"

#### Flujo UX de Gestión

**Alta de autorización:**
1. Usuario selecciona titular (selector de administrados)
2. Usuario selecciona autorizado (selector de administrados, excluyendo titular)
3. Usuario especifica observaciones (opcional)
4. Sistema crea registro con `ACTIVO = TRUE`

**Revocación:**
1. Usuario marca autorización como inactiva
2. Sistema solicita motivo (obligatorio)
3. Sistema actualiza `ACTIVO = FALSE` y concatena motivo en `OBSERVACIONES`

**Consulta:**
- Listar autorizaciones activas de un titular
- Listar titulares de un autorizado
- Filtrar por texto libre en observaciones

---

---

### DOCUMENTOS

Pool puro de archivos físicos asociados a expedientes.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del documento | NO | PK, autoincremental |
| **EXPEDIENTE_ID** | INTEGER | Expediente al que pertenece el documento | NO | FK → EXPEDIENTES(ID). **Único FK del documento**. El documento es agnóstico a cualquier otra relación |
| **URL** | VARCHAR(500) | Ruta o URL del archivo físico | NO | Ruta al archivo en el sistema de archivos o repositorio documental |
| **TIPO_CONTENIDO** | VARCHAR(50) | Tipo MIME o extensión del archivo | SÍ | Ejemplo: 'application/pdf', 'application/vnd.oasis.opendocumentext', 'application/zip' |
| **FECHA_ADMINISTRATIVA** | DATE | Fecha con valor administrativo oficial | NO | Fecha objetiva con efectos legales: firma, registro de entrada/salida, generación oficial, publicación. **Es la fecha que cuenta** para plazos, notificaciones y secuencia administrativa. NO es la fecha de creación del archivo físico |
| **ASUNTO** | VARCHAR(500) | Descripción o asunto del documento | SÍ | Breve descripción del contenido o propósito del documento |
| **ORIGEN** | VARCHAR(100) | Procedencia del documento | SÍ | Ej: 'EXTERNO', 'INTERNO', 'ORGANISMO_X', 'SOLICITANTE' |
| **PRIORIDAD** | INTEGER | Nivel de prioridad o relevancia | SÍ | Valor numérico para ordenar por importancia. Default: 0 |
| **NOMBRE_DISPLAY** | VARCHAR(200) | Nombre para mostrar en interfaz | SÍ | Nombre legible para el usuario, puede diferir del nombre de archivo físico |
| **HASH_MD5** | VARCHAR(32) | Hash MD5 del archivo para integridad | SÍ | Verificación de integridad y detección de duplicados |
| **OBSERVACIONES** | VARCHAR(2000) | Notas o comentarios adicionales | SÍ | Campo libre para anotaciones del técnico |

#### Claves

- **PK:** `ID`
- **FK:**
  - `EXPEDIENTE_ID` → `EXPEDIENTES(ID)` (único FK)

#### Índices Recomendados

- `EXPEDIENTE_ID` (consultas frecuentes por expediente)
- `FECHA_ADMINISTRATIVA` (ordenación cronológica y filtros temporales)
- `HASH_MD5` (detección de duplicados)

#### Notas de Versión

- **v3.0:** **RENOMBRADO** `FECHA_DOCUMENTO` → `FECHA_ADMINISTRATIVA`. Clarifica que es la fecha con valor legal/administrativo, no la fecha de creación del archivo físico.
- **v3.0:** **ELIMINADO** campo `TAREA_ORIGEN_ID`. Ya no existe en el documento.
- **v3.0:** **ELIMINADO** campo `TAREA_DESTINO_ID`. Ya no existe en el documento.
- **v3.0:** **ELIMINADO** campo `PROYECTO_ID`. Ya no existe en el documento.

#### Filosofía

El documento es una **entidad pura del expediente**. Solo sabe a qué expediente pertenece. Es completamente agnóstico respecto a:

- Qué tarea lo produjo (se define en `TAREAS.DOCUMENTO_PRODUCIDO_ID`)
- Qué tareas lo usan (se define en `TAREAS.DOCUMENTO_USADO_ID`)
- Si es parte de un proyecto (se define en `DOCUMENTOS_PROYECTO`)
- Su rol en el flujo de tramitación

**Pool único de documentos por expediente**, las relaciones viven fuera.

#### Aclaración Crítica sobre FECHA_ADMINISTRATIVA

**NO es la fecha del archivo físico** (metadatos del sistema de archivos), sino la **fecha con efectos administrativos y legales**:

- **Solicitud:** fecha de registro de entrada
- **Resolución:** fecha de firma
- **Notificación:** fecha de notificación efectiva
- **Publicación:** fecha de publicación oficial
- **Informe externo:** fecha del informe
- **Proyecto:** fecha de visado o firma del proyecto

**Es la fecha que determina plazos, efectos jurídicos y secuencia administrativa**.

---

---

### DOCUMENTOS_PROYECTO

Vinculación entre documentos y proyectos con metadatos de tipo y evolución.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del registro | NO | PK, autoincremental |
| **PROYECTO_ID** | INTEGER | Proyecto al que pertenece el documento | NO | FK → PROYECTOS(ID). El documento pertenece a UN proyecto único |
| **DOCUMENTO_ID** | INTEGER | Documento que forma parte del proyecto | NO | FK → DOCUMENTOS(ID). Archivo físico (PDF del proyecto, planos, anexos, etc.). **UNIQUE** - Un documento solo puede vincularse a un proyecto |
| **TIPO** | VARCHAR(20) | Tipo de documento en la evolución del proyecto | NO | Valores: 'PRINCIPAL', 'MODIFICADO', 'REFUNDIDO', 'ANEXO'. Define la naturaleza del documento en la secuencia temporal del proyecto |
| **OBSERVACIONES** | VARCHAR(500) | Notas sobre la vinculación | SÍ | Comentarios del técnico sobre la incorporación del documento (ej: "Modificación exigida por Medio Ambiente") |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `DOCUMENTO_ID` - **Un documento solo puede estar en un proyecto** (relación N:1, no N:M)
- **FK:**
  - `PROYECTO_ID` → `PROYECTOS(ID)` ON DELETE CASCADE
  - `DOCUMENTO_ID` → `DOCUMENTOS(ID)` ON DELETE CASCADE

#### Índices Recomendados

- `PROYECTO_ID` (documentos de un proyecto)
- `DOCUMENTO_ID` (único, consulta inversa: en qué proyecto está este documento)
- `(PROYECTO_ID, TIPO)` (filtros por tipo dentro del proyecto)

#### Notas de Versión

- **v3.0:** **NUEVA TABLA**. Externaliza la relación `DOCUMENTO.PROYECTO_ID` con metadatos (TIPO).
- **v3.0:** **Relación N:1**, no N:M. Un documento pertenece a un solo proyecto.
- **v3.0:** **ELIMINADO** campo `FECHA_VINCULACION`. Sin valor administrativo, trazabilidad ya existe en bitácora.
- **v3.0:** **ELIMINADO** campo `VIGENTE`. Vigencia se deduce de TIPO + orden cronológico (usando `DOCUMENTOS.FECHA_ADMINISTRATIVA`).

#### Filosofía

Esta tabla **NO es una relación muchos a muchos**, sino una **FK externalizada con metadatos**.

**Ventajas de externalizar:**

- Permite añadir metadatos (TIPO, OBSERVACIONES) sin modificar `DOCUMENTOS`
- Mantiene `DOCUMENTOS` puro (solo `EXPEDIENTE_ID`)
- La relación es opcional (un documento puede NO ser de proyecto)

#### Deducción de Vigencia (sin campo VIGENTE)

**Regla automática por consulta:**

1. **REFUNDIDO más reciente anula todos los anteriores**
2. **Sin REFUNDIDO: PRINCIPAL + todos los MODIFICADOS + ANEXOS son vigentes**
3. **ANEXOS siempre son vigentes (complementarios, no sustituyen)**

#### Valores de Campo TIPO

| Valor | Significado | Efecto en vigencia |
|:---|:---|:---|
| **PRINCIPAL** | Proyecto inicial presentado | Vigente hasta que aparece REFUNDIDO |
| **MODIFICADO** | Proyecto con cambios (mantiene esencia) | Se acumula al PRINCIPAL. Vigente hasta REFUNDIDO |
| **REFUNDIDO** | Consolida PRINCIPAL + MODIFICADOS | Anula todos los PRINCIPAL y MODIFICADOS anteriores. Es el único vigente |
| **ANEXO** | Documentación complementaria (cálculos, planos) | Siempre vigente, no sustituye otros |

#### Validaciones y Reglas

**Validación 1: Un documento solo en un proyecto**
```sql
-- UNIQUE constraint en DOCUMENTO_ID lo garantiza automáticamente
```

**Validación 2: Un proyecto siempre tiene al menos un PRINCIPAL**
```sql
-- Al crear proyecto, debe vincularse inmediatamente con documento PRINCIPAL
-- Validación en lógica de negocio al intentar eliminar el último PRINCIPAL
```

**Validación 3: REFUNDIDO debe ser posterior a PRINCIPAL**
```sql
-- Validación en interfaz: 
-- Si TIPO='REFUNDIDO', verificar que existe PRINCIPAL con FECHA_ADMINISTRATIVA anterior
```

#### Nota sobre Fechas

La ordenación de los documentos del proyecto se basa en la **fecha administrativa del documento** al que apunta cada `DOCUMENTO_ID`. Es por esto que la tabla `DOCUMENTOS_PROYECTO` no tiene campo de fecha, porque reside en el documento en sí, manteniendo los principios de **localización de la fuente de la verdad** y **no duplicidad innecesaria**.

---

---

### ENTIDADES

Tabla base que centraliza todas las personas físicas, jurídicas y organismos que interactúan con el sistema (titulares, solicitantes, autorizados, organismos públicos, ayuntamientos, diputaciones). Utiliza arquitectura de tablas inversas: campos comunes en esta tabla, metadatos específicos en tablas `entidades_*` según el tipo.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único de la entidad | NO | PK, autoincremental |
| **TIPO_ENTIDAD_ID** | INTEGER | Tipo de entidad que determina tabla de metadatos | NO | FK → TIPOS_ENTIDADES(ID). Define qué tabla `entidades_*` usar |
| **CIF_NIF** | VARCHAR(20) | CIF/NIF/NIE normalizado | SÍ | UNIQUE. Mayúsculas, sin espacios/guiones. Ej: "12345678A", "B12345678". NULL para algunos organismos históricos |
| **NOMBRE_COMPLETO** | VARCHAR(200) | Razón social, nombre completo o nombre oficial | NO | Indexed. Personas físicas: nombre completo. Jurídicas/organismos: razón social/nombre oficial |
| **EMAIL** | VARCHAR(120) | Email general de contacto | SÍ | NO es el email de notificaciones (va en `entidades_administrados`) |
| **TELEFONO** | VARCHAR(20) | Teléfono de contacto general | SÍ | Formato libre |
| **DIRECCION** | TEXT | Calle, número, piso, puerta | SÍ | Usar junto con CODIGO_POSTAL y MUNICIPIO_ID (preferente para España) |
| **CODIGO_POSTAL** | VARCHAR(10) | Código postal | SÍ | Texto libre. Futuro: sugerencias desde tabla `codigos_postales` |
| **MUNICIPIO_ID** | INTEGER | Municipio de la dirección | SÍ | FK → MUNICIPIOS(ID). Preferente sobre DIRECCION_FALLBACK |
| **DIRECCION_FALLBACK** | TEXT | Dirección completa en texto libre | SÍ | Para casos excepcionales (extranjero, datos históricos). Ej: "23, Peny Lane, St, 34523, London, England" |
| **ACTIVO** | BOOLEAN | Indica si la entidad está activa | NO | Default: TRUE. Borrado lógico |
| **NOTAS** | TEXT | Observaciones generales sobre la entidad | SÍ | Campo libre para anotaciones |
| **CREATED_AT** | TIMESTAMP | Fecha y hora de creación del registro | NO | Default: NOW() |
| **UPDATED_AT** | TIMESTAMP | Fecha y hora de última actualización | NO | Default: NOW(), auto-update |

#### Claves

- **PK:** `ID`
- **FK:**
  - `TIPO_ENTIDAD_ID` → `TIPOS_ENTIDADES(ID)`
  - `MUNICIPIO_ID` → `MUNICIPIOS(ID)`
- **UNIQUE:** `CIF_NIF`

#### Índices Recomendados

- `TIPO_ENTIDAD_ID` (consultas por tipo)
- `CIF_NIF` (búsquedas por identificación fiscal)
- `NOMBRE_COMPLETO` (búsquedas por nombre)
- `ACTIVO` (filtros por estado)
- `MUNICIPIO_ID` (consultas geográficas)

#### Constraints

```sql
-- Dirección: estructurada o fallback, al menos una opción
CONSTRAINT chk_direccion_estructurada_o_fallback 
    CHECK (
        municipio_id IS NOT NULL 
        OR direccion_fallback IS NOT NULL 
        OR direccion IS NULL
    )
```

#### Relaciones

- **tipo_entidad**: TIPOS_ENTIDADES.id (FK, catálogo de tipos)
- **municipio**: MUNICIPIOS.id (FK, ubicación geográfica)
- **datos_administrado**: ENTIDADES_ADMINISTRADOS.entidad_id (1:1, metadatos administrados)
- **datos_organismo**: ENTIDADES_ORGANISMOS_PUBLICOS.entidad_id (1:1, metadatos organismos)
- **datos_ayuntamiento**: ENTIDADES_AYUNTAMIENTOS.entidad_id (1:1, metadatos ayuntamientos)
- **datos_diputacion**: ENTIDADES_DIPUTACIONES.entidad_id (1:1, metadatos diputaciones)
- **expedientes_como_titular**: EXPEDIENTES.titular_id (1:N inversa)
- **solicitudes_como_solicitante**: SOLICITUDES.solicitante_id (1:N inversa)
- **solicitudes_como_autorizado**: SOLICITUDES.autorizado_id (1:N inversa)

#### Notas de Versión

- **v1.0** (01/02/2026): Creación inicial de la tabla con arquitectura de tablas inversas

#### Filosofía

La tabla `entidades` implementa el patrón de **tablas inversas** (inverse/bridge tables) para gestionar múltiples tipos de entidades con metadatos heterogéneos:

- **Campos comunes** en `entidades` (CIF, nombre, contacto, dirección)
- **Metadatos específicos** en tablas `entidades_*` según tipo
- **Relaciones polimórficas** 1:1 entre `entidades` y cada tabla de metadatos
- **Una entidad puede tener múltiples roles** (ej: ayuntamiento que también es administrado)

#### Normalización CIF/NIF

- Siempre en **MAYÚSCULAS**
- Sin espacios, guiones ni caracteres especiales
- Ejemplos válidos: "12345678A", "B12345678", "X1234567L"
- Algoritmo de validación implementado en modelo SQLAlchemy

#### Dirección: Estructurada vs Fallback

**Preferente (España):**
- `DIRECCION` + `CODIGO_POSTAL` + `MUNICIPIO_ID`
- Permite consultas geográficas, validaciones y sugerencias

**Fallback (casos excepcionales):**
- `DIRECCION_FALLBACK` en texto libre
- Para direcciones extranjeras, datos históricos sin municipio en BD
- El país se incluye en el texto

**Regla:** Al menos una opción debe estar presente si hay dirección

#### Email General vs Email de Notificaciones

- `ENTIDADES.EMAIL`: contacto general, puede no usarse para notificaciones oficiales
- `ENTIDADES_ADMINISTRADOS.EMAIL_NOTIFICACIONES`: específico para sistema Notifica (solo administrados)
- `ENTIDADES_ORGANISMOS_PUBLICOS.CODIGO_DIR3`: notificaciones vía SIR (solo organismos públicos)

#### Tipos de Entidad

El campo `TIPO_ENTIDAD_ID` determina:
- Qué tabla de metadatos (`ENTIDADES_*`) debe tener registro asociado
- Qué formulario mostrar en la interfaz
- Qué validaciones aplicar

Tabla `TIPOS_ENTIDADES` contiene campo `tabla_metadatos` que mapea tipo → tabla física.

#### Reglas de Negocio

1. **Normalización CIF/NIF**: Método estático `normalizar_cif_nif()` aplicar antes de guardar
2. **Validación CIF/NIF**: Método estático `validar_cif_nif()` con algoritmo oficial
3. **CIF/NIF opcional**: Algunos organismos históricos pueden tener `CIF_NIF = NULL`
4. **Múltiples roles**: Una entidad puede tener registros en múltiples tablas `entidades_*`
5. **Código postal futuro**: Preparado para tabla `codigos_postales` con sugerencias por municipio
6. **Borrado lógico**: Usar `ACTIVO = FALSE` en lugar de DELETE físico
7. **Integridad referencial**:
   - Cascade en tablas `entidades_*` (eliminar metadatos con entidad)
   - Restrict en `expedientes`/`solicitudes` (no eliminar si hay referencias activas)

#### Flujo UX de Creación

1. Usuario elige tipo de entidad (administrado, organismo, ayuntamiento, etc.)
2. Sistema carga formulario con:
   - Campos comunes (`entidades`)
   - Campos específicos (tabla `entidades_*` correspondiente)
3. Al guardar, se crean ambos registros (entidad + metadatos) en transacción

#### Filtrado por Tipo en Tareas

**Fase "Todo Vale":**
```sql
-- Usuario filtra manualmente
SELECT * FROM entidades 
WHERE tipo_entidad_id = :tipo 
AND activo = TRUE
```

**Fase "Reglas de Negocio":**
```sql
-- Sistema aplica reglas según contexto
-- Ej: notificación tablón ayuntamiento → solo tipo AYUNTAMIENTO
SELECT * FROM entidades 
WHERE tipo_entidad_id IN (:tipos_permitidos)
AND activo = TRUE
```

---

---

### ENTIDADES_ADMINISTRADOS

Metadatos específicos de personas físicas o jurídicas que actúan como administrados (titulares, solicitantes, autorizados) en el sistema.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ENTIDAD_ID** | INTEGER | Referencia a entidad base | NO | PK y FK → ENTIDADES(ID), UNIQUE, CASCADE |
| **EMAIL_NOTIFICACIONES** | VARCHAR(120) | Email oficial para sistema Notifica | NO | Email donde se reciben notificaciones electrónicas oficiales. Puede ser personal o corporativo |
| **REPRESENTANTE_NIF_CIF** | VARCHAR(20) | NIF/CIF de quien representa/gestiona | SÍ | NULL si autorepresentado (persona física) o gestión corporativa directa. Normalizado como CIF/NIF |
| **REPRESENTANTE_NOMBRE** | VARCHAR(200) | Nombre completo del representante | SÍ | NULL si autorepresentado. Puede ser persona física (administrador único) o jurídica (consultora contratada) |
| **REPRESENTANTE_TELEFONO** | VARCHAR(20) | Teléfono del representante | SÍ | Contacto directo con quien gestiona |
| **REPRESENTANTE_EMAIL** | VARCHAR(120) | Email del representante | SÍ | Email de contacto (NO oficial para notificaciones, solo coordinación) |
| **NOTAS_REPRESENTACION** | TEXT | Observaciones sobre la representación | SÍ | Tipo de cargo o relación: "Administrador único", "Consultora ACME SL contratada", "Apoderado con poder notarial", etc. |

#### Claves

- **PK:** `ENTIDAD_ID`
- **FK:**
  - `ENTIDAD_ID` → `ENTIDADES(ID)` ON DELETE CASCADE

#### Índices Recomendados

- `REPRESENTANTE_NIF_CIF` (búsquedas por representante)
- `EMAIL_NOTIFICACIONES` (búsquedas por email oficial)

#### Constraints

```sql
-- Si hay representante_nif_cif, debe haber representante_nombre
CONSTRAINT chk_representante_coherente
    CHECK (
        (representante_nif_cif IS NULL AND representante_nombre IS NULL)
        OR
        (representante_nif_cif IS NOT NULL AND representante_nombre IS NOT NULL)
    )
```

#### Relaciones

- **entidad**: ENTIDADES.id (FK, relación 1:1 con entidad base)

#### Notas de Versión

- **v1.0** (01/02/2026): Creación inicial con estructura simplificada de representación genérica

#### Filosofía

Tabla de metadatos para **administrados** (personas físicas o jurídicas privadas):

- **Relación 1:1** con `ENTIDADES` mediante `ENTIDAD_ID` como PK y FK
- **Representación simplificada:** Un solo campo `REPRESENTANTE_*` que cubre todos los casos (persona física, jurídica, consultora)
- **Autorepresentación:** Si `REPRESENTANTE_NIF_CIF` es NULL, el administrado se representa a sí mismo
- **Par obligatorio Notifica:** `(CIF/NIF, EMAIL_NOTIFICACIONES)` debe estar completo para poder notificar

#### Casos de Uso

**Caso A: Persona física autorepresentada**
```sql
-- ENTIDADES
INSERT INTO entidades (tipo_entidad_id, cif_nif, nombre_completo, ...) 
VALUES (1, '12345678A', 'Juan Pérez García', ...);

-- ENTIDADES_ADMINISTRADOS
INSERT INTO entidades_administrados (entidad_id, email_notificaciones, representante_nif_cif, representante_nombre)
VALUES (1, 'juan.perez@gmail.com', NULL, NULL);

-- Par Notifica: ('12345678A', 'juan.perez@gmail.com')
```

**Caso B: Persona jurídica con administrador único**
```sql
-- ENTIDADES
INSERT INTO entidades (tipo_entidad_id, cif_nif, nombre_completo, ...) 
VALUES (1, 'B12345678', 'Constructora García SL', ...);

-- ENTIDADES_ADMINISTRADOS
INSERT INTO entidades_administrados (
    entidad_id, 
    email_notificaciones, 
    representante_nif_cif, 
    representante_nombre,
    notas_representacion
)
VALUES (
    2, 
    'notificaciones@constructoragarcia.com', 
    '12345678A', 
    'Juan García López',
    'Administrador único'
);

-- Par Notifica: ('12345678A', 'notificaciones@constructoragarcia.com')
```

**Caso C: Persona jurídica con gestión corporativa directa**
```sql
-- ENTIDADES
INSERT INTO entidades (tipo_entidad_id, cif_nif, nombre_completo, ...) 
VALUES (1, 'B87654321', 'Gran Empresa Eléctrica SA', ...);

-- ENTIDADES_ADMINISTRADOS
INSERT INTO entidades_administrados (
    entidad_id, 
    email_notificaciones, 
    representante_nif_cif, 
    representante_nombre,
    notas_representacion
)
VALUES (
    3, 
    'tramites.juridico@granempresa.com', 
    NULL, 
    NULL,
    'Gestión corporativa directa'
);

-- Par Notifica: ('B87654321', 'tramites.juridico@granempresa.com')
```

**Caso D: Persona jurídica representada por consultora**
```sql
-- ENTIDADES
INSERT INTO entidades (tipo_entidad_id, cif_nif, nombre_completo, ...) 
VALUES (1, 'B11111111', 'Promotora Solar XXX SL', ...);

-- ENTIDADES_ADMINISTRADOS
INSERT INTO entidades_administrados (
    entidad_id, 
    email_notificaciones, 
    representante_nif_cif, 
    representante_nombre,
    representante_telefono,
    representante_email,
    notas_representacion
)
VALUES (
    4, 
    'notifica@consultoraacme.com', 
    'B22222222', 
    'Consultora ACME SL',
    '956123456',
    'contacto@consultoraacme.com',
    'Consultora contratada para tramitación completa'
);

-- Par Notifica: ('B22222222', 'notifica@consultoraacme.com')
```

#### Regla de Negocio: CIF/NIF para Notifica

**Par obligatorio para notificar:** `(CIF/NIF, EMAIL_NOTIFICACIONES)`

**Lógica de obtención del CIF/NIF:**

```python
def obtener_cif_notifica(administrado):
    """
    Devuelve el CIF/NIF que debe usarse para notificar.
    
    Regla:
    - Si hay representante_nif_cif → usar ese (quien gestiona)
    - Si representante_nif_cif es NULL → usar entidades.cif_nif (titular)
    """
    if administrado.representante_nif_cif:
        return administrado.representante_nif_cif
    else:
        return administrado.entidad.cif_nif

def obtener_par_notifica(administrado):
    """
    Devuelve el par (CIF/NIF, EMAIL) para sistema Notifica.
    """
    return (
        obtener_cif_notifica(administrado),
        administrado.email_notificaciones
    )
```

**Consulta SQL:**
```sql
-- Obtener par para notificar
SELECT 
    COALESCE(ea.representante_nif_cif, e.cif_nif) AS cif_notifica,
    ea.email_notificaciones
FROM entidades_administrados ea
JOIN entidades e ON ea.entidad_id = e.id
WHERE ea.entidad_id = :id;
```

#### Visualización en Interfaz

**Al crear/editar administrado:**

```
┌─────────────────────────────────────────────────┐
│ DATOS DEL TITULAR                               │
├─────────────────────────────────────────────────┤
│ CIF/NIF: B12345678                              │
│ Nombre: Constructora García SL                  │
│ ...                                             │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ NOTIFICACIONES ELECTRÓNICAS (Notifica)          │
├─────────────────────────────────────────────────┤
│ Email notificaciones: [_____________________]   │
│   ⓘ Email oficial donde se recibirán las       │
│     notificaciones electrónicas                 │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ REPRESENTACIÓN (Opcional)                       │
├─────────────────────────────────────────────────┤
│ ☐ El titular se representa a sí mismo           │
│                                                 │
│ ☑ Hay representante/apoderado                   │
│   NIF/CIF: [12345678A]                          │
│   Nombre:  [Juan García López]                  │
│   Teléfono: [____________]                      │
│   Email:    [____________]                      │
│   Notas:    [Administrador único]               │
│                                                 │
│ ⚠️ NOTIFICACIONES SE ENVIARÁN A:                │
│    CIF/NIF: 12345678A  (representante)          │
│    Email:   notificaciones@constructora...      │
└─────────────────────────────────────────────────┘
```

#### Validaciones

**Al guardar:**

1. `EMAIL_NOTIFICACIONES` obligatorio (NOT NULL)
2. Si `REPRESENTANTE_NIF_CIF` tiene valor → `REPRESENTANTE_NOMBRE` obligatorio
3. Si `REPRESENTANTE_NIF_CIF` es NULL → `REPRESENTANTE_NOMBRE` debe ser NULL
4. `REPRESENTANTE_NIF_CIF` debe pasar validación algoritmo NIF/CIF (si no es NULL)
5. Par `(CIF_NOTIFICA, EMAIL_NOTIFICACIONES)` debe estar completo

**Validación Python:**
```python
from models import Entidad, EntidadAdministrado

def validar_administrado(administrado):
    # Email notificaciones obligatorio
    if not administrado.email_notificaciones:
        raise ValidationError("Email de notificaciones es obligatorio")
    
    # Coherencia representante
    tiene_cif = administrado.representante_nif_cif is not None
    tiene_nombre = administrado.representante_nombre is not None
    
    if tiene_cif != tiene_nombre:
        raise ValidationError(
            "Si hay CIF de representante, debe haber nombre (y viceversa)"
        )
    
    # Validar CIF representante
    if tiene_cif:
        if not Entidad.validar_cif_nif(administrado.representante_nif_cif):
            raise ValidationError("CIF/NIF del representante no es válido")
    
    # Par Notifica completo
    cif_notifica = administrado.representante_nif_cif or administrado.entidad.cif_nif
    if not cif_notifica or not administrado.email_notificaciones:
        raise ValidationError(
            "No se puede determinar el par (CIF/NIF, email) para notificar"
        )
```

#### Consultas Frecuentes

**1. Listar administrados con sus datos de notificación:**
```sql
SELECT 
    e.id,
    e.cif_nif AS cif_titular,
    e.nombre_completo AS nombre_titular,
    COALESCE(ea.representante_nif_cif, e.cif_nif) AS cif_notifica,
    COALESCE(ea.representante_nombre, e.nombre_completo) AS nombre_notifica,
    ea.email_notificaciones
FROM entidades e
JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE e.activo = TRUE
ORDER BY e.nombre_completo;
```

**2. Buscar por email de notificaciones:**
```sql
SELECT e.*, ea.*
FROM entidades e
JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE ea.email_notificaciones ILIKE '%@consultoraacme.com';
```

**3. Administrados representados por una consultora específica:**
```sql
SELECT e.*, ea.*
FROM entidades e
JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE ea.representante_nif_cif = 'B22222222'  -- CIF consultora
AND e.activo = TRUE;
```

**4. Administrados autorepresentados (personas físicas):**
```sql
SELECT e.*, ea.*
FROM entidades e
JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE ea.representante_nif_cif IS NULL
AND e.cif_nif LIKE '_________'  -- NIF (8 dígitos + letra)
AND e.activo = TRUE;
```

---

---

### ENTIDADES_AYUNTAMIENTOS

Metadatos específicos de corporaciones locales (ayuntamientos) que pueden actuar con múltiples roles: organismo consultado, solicitante ocasional y publicador de anuncios oficiales.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ENTIDAD_ID** | INTEGER | Referencia a entidad base | NO | PK y FK → ENTIDADES(ID), UNIQUE, CASCADE |
| **CODIGO_DIR3** | VARCHAR(20) | Código DIR3 oficial del ayuntamiento | SÍ | UNIQUE (cuando no es NULL). Para notificaciones SIR cuando actúa como organismo consultado |

#### Claves

- **PK:** `ENTIDAD_ID`
- **FK:**
  - `ENTIDAD_ID` → `ENTIDADES(ID)` ON DELETE CASCADE

#### Índices

- `ix_public_entidades_ayuntamientos_codigo_dir3` (único, sobre `CODIGO_DIR3`)

#### Relaciones

- **entidad**: ENTIDADES.id (FK, relación 1:1 con entidad base)

#### Notas de Versión

- **v1.0** (01/02/2026): Creación inicial con estructura minimalista
- **v1.1** (04/02/2026): Sincronización con schema.sql - codigo_dir3 es VARCHAR(20) y NULLABLE, eliminar campo observaciones

#### Filosofía

Tabla de metadatos para **ayuntamientos** (corporaciones locales municipales):

- **Relación 1:1** con `ENTIDADES` mediante `ENTIDAD_ID` como PK y FK
- **Estructura minimalista:** Solo código DIR3 (opcional)
- **CODIGO_DIR3 opcional:** Puede ser NULL (ayuntamientos pequeños sin código DIR3, o datos históricos)
- **Sin representante:** La entidad es la corporación en sí (persona jurídica pública)
- **Múltiples roles posibles:** Solicitante + Consultado + Publicador (triple entrada posible)
- **Notificaciones:** SIR (DIR3) cuando actúa como organismo, Notifica cuando actúa como solicitante

#### Campos que YA están en ENTIDADES (no duplicar)

**Todos estos datos viven en `ENTIDADES`:**

- `CIF_NIF`: CIF formato `P` + código INE (7 dígitos) + dígito control (ej: `P2807901D` - Ayto. Madrid)
- `NOMBRE_COMPLETO`: Denominación oficial (ej: "Ayuntamiento de Madrid", "Concello de Vigo")
- `EMAIL`: Email general corporativo
- `TELEFONO`: Teléfono general
- `DIRECCION`, `CODIGO_POSTAL`: Sede del ayuntamiento (Casa Consistorial)
- `MUNICIPIO_ID`: FK a MUNICIPIOS → **El ayuntamiento ES el municipio que gestiona**
- `NOTAS`: Observaciones generales (horarios, contactos específicos, etc.)

**Para contactos específicos (email urbanismo, teléfono medio ambiente), usar campo `NOTAS` en `ENTIDADES`.**

#### CIF de Ayuntamientos

**Formato obligatorio:**
- Letra **P** (personas jurídicas públicas)
- 7 dígitos del código INE del municipio
- 1 dígito de control

**Ejemplos reales:**
- Madrid: `P2807901D` (INE: 28079)
- Barcelona: `P0801900J` (INE: 08019)
- Valencia: `P4690000H` (INE: 46900)
- Sevilla: `P4109100I` (INE: 41091)
- Alcobendas: `P2800700F` (INE: 28007)

**Características:**
- CIF único por ayuntamiento (no compartido como en AGE o CCAA)
- Cada ayuntamiento es entidad jurídica independiente
- CIF obligatorio (NOT NULL en `ENTIDADES.CIF_NIF`)

#### Sistema DIR3: Ayuntamientos

**¿Qué es DIR3 para ayuntamientos?**
- Código oficial de la unidad orgánica del ayuntamiento en DIR3
- Obligatorio para facturación electrónica y comunicaciones interadministrativas
- Formato: 1-2 letras + 7-8 números (ej: `L01410084`)

**Uso en BDDAT:**
- Identificación única para notificaciones vía **SIR** cuando el ayuntamiento actúa como **organismo consultado** (emite informe)
- NO se usa para notificar cuando actúa como **solicitante** (ahí usa Notifica con email)

**Campo NULLABLE:**
- Ayuntamientos pequeños pueden no tener código DIR3 registrado
- Datos históricos de ayuntamientos sin código DIR3
- Ayuntamientos en proceso de registro

**Consulta de códigos DIR3:**
- Portal oficial: https://administracionelectronica.gob.es/ctt/dir3
- Descargas: https://administracionelectronica.gob.es/ctt/dir3/descargas

#### Múltiples Roles: Ayuntamiento con Triple Capacidad

**Escenario:** Ayuntamiento de Alcorcón actúa en 3 roles diferentes

**Registros necesarios:**

1. **ENTIDADES** (tabla base):
   - `cif_nif`: "P2800600A" (CIF único)
   - `nombre_completo`: "Ayuntamiento de Alcorcón"
   - `tipo_entidad_id`: AYUNTAMIENTO
   - `municipio_id`: FK al municipio de Alcorcón
   - `notas`: "Horario: L-V 9-14h. Email urbanismo: urbanismo@aytoalcorcon.es"

2. **ENTIDADES_AYUNTAMIENTOS** (rol: consultado + publicador):
   - `codigo_dir3`: "L01280061" (código oficial)

3. **ENTIDADES_ADMINISTRADOS** (rol: solicitante ocasional):
   - `email_notificaciones`: "notifica@aytoalcorcon.es"
   - `representante_nif_cif`: NULL (gestión corporativa)
   - `representante_nombre`: NULL

**Filtrado automático en interfaz:**

```sql
-- Contexto: Solicitar informe urbanismo (fase CONSULTAS)
-- Aparecen ayuntamientos con tipo AYUNTAMIENTO
SELECT e.* FROM entidades e
JOIN tipos_entidades te ON e.tipo_entidad_id = te.id
WHERE te.puede_ser_consultado = TRUE
AND e.activo = TRUE;

-- Contexto: Crear solicitud (ayto. solicita instalación propia)
-- Solo aparecen entidades con registro en ENTIDADES_ADMINISTRADOS
SELECT e.* FROM entidades e
JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE e.activo = TRUE;

-- Contexto: Publicar en tablón municipal
-- Solo aparecen ayuntamientos
SELECT e.* FROM entidades e
JOIN tipos_entidades te ON e.tipo_entidad_id = te.id
WHERE te.codigo = 'AYUNTAMIENTO'
AND e.activo = TRUE;
```

#### Flujo UX: Copia de Datos entre Roles

**Aplica la misma lógica que otras tablas de metadatos:**

1. Usuario introduce CIF o nombre que ya existe
2. Sistema detecta roles activos del ayuntamiento
3. Sistema ofrece copiar datos de rol existente (si aplica)
4. Usuario selecciona o introduce datos nuevos

**Nota:** El campo más relevante para copiar es `email_notificaciones` (si actúa como solicitante).

#### Reglas de Negocio

1. **CODIGO_DIR3 opcional** (puede ser NULL)
2. **CIF_NIF obligatorio** en `ENTIDADES` (formato P+INE+control)
3. **Sin representante** (no aplican campos `REPRESENTANTE_*`)
4. **Múltiples roles:** Un ayuntamiento puede estar en esta tabla Y en `ENTIDADES_ADMINISTRADOS`
5. **Notificaciones duales:**
   - Como **organismo consultado**: SIR (usa CODIGO_DIR3 si existe)
   - Como **solicitante**: Notifica (usa email de `ENTIDADES_ADMINISTRADOS`)
6. **Publicación anuncios:** Tablón edictos propio según Ley 39/2015 Art. 45.4 (obligación vs administrados, no dato BDDAT)
7. **Validación DIR3:** Formato alfanumérico, 8-10 caracteres (si no es NULL)
8. **MUNICIPIO_ID en ENTIDADES:** El ayuntamiento gestiona el municipio al que pertenece (relación 1:1)

#### Tablón de Edictos Electrónico: Aclaración Legal

**Ley 39/2015, Artículo 45.4:**

> "Las Administraciones Locales deberán tener un tablón de edictos electrónico único, donde se publicarán todos los anuncios que deban publicarse en el tablón de edictos de la entidad."

**Interpretación correcta:**
- **Obligación:** Para que **ciudadanos** puedan leer notificaciones públicas
- **Destinatarios:** Administrados (personas físicas/jurídicas privadas)
- **Sistema BDDAT:** No publica directamente en tablón municipal

**Flujo real desde BDDAT:**

```
BDDAT → Sistema SIR (Servicio Integrado de Registro) → Ayuntamiento recibe notificación
                                                      ↓
                                            Ayuntamiento publica en su tablón electrónico
                                                      ↓
                                            Ciudadanos leen en sede electrónica municipal
```

**Conclusión:**
- **NO almacenamos URL del tablón** (no es dato estructurado que necesitemos)
- **Usamos SIR** para enviar anuncios al ayuntamiento (si tiene DIR3)
- **El ayuntamiento** es responsable de publicar en su tablón (sede electrónica)
- **Si no tiene DIR3:** Métodos tradicionales (correo postal, email general)

#### Validaciones

**Validación Python:**

```python
import re

def validar_cif_ayuntamiento(cif):
    """
    Valida CIF de ayuntamiento.
    Formato: P + 7 dígitos INE + 1 dígito control
    Ejemplo válido: P2807901D
    """
    if not cif:
        return False
    
    # Patrón: P + 7 dígitos + 1 letra/dígito
    patron = r'^P\d{7}[A-Z0-9]$'
    return re.match(patron, cif.upper()) is not None

def validar_codigo_dir3(codigo):
    """
    Valida formato de código DIR3.
    Formato: 1-2 letras + 7-8 números
    Ejemplos válidos: L01410084, A12002696
    """
    if not codigo:
        return True  # Nullable
    
    # Patrón: 1-2 letras mayúsculas + 7-8 dígitos
    patron = r'^[A-Z]{1,2}\d{7,8}$'
    return re.match(patron, codigo.upper()) is not None

class EntidadAyuntamiento(db.Model):
    # ...
    
    @validates('codigo_dir3')
    def validate_codigo_dir3(self, key, value):
        if not value:
            return None  # Nullable
        
        value_upper = value.upper().strip()
        
        if not validar_codigo_dir3(value_upper):
            raise ValueError(
                f"Código DIR3 inválido: {value}. "
                "Formato esperado: 1-2 letras + 7-8 dígitos (ej: L01410084)"
            )
        
        return value_upper
```

**Validación en interfaz:**

```javascript
// Validación cliente (JavaScript)
function validarCIFAyuntamiento(cif) {
    const patron = /^P\d{7}[A-Z0-9]$/;
    return patron.test(cif.toUpperCase());
}

function validarDIR3(codigo) {
    if (!codigo || codigo.trim() === '') return true; // Nullable
    const patron = /^[A-Z]{1,2}\d{7,8}$/;
    return patron.test(codigo.toUpperCase());
}
```

#### Consultas Frecuentes

**1. Listar ayuntamientos con su DIR3 y CIF:**

```sql
SELECT 
    e.id,
    e.nombre_completo,
    e.cif_nif,
    ea.codigo_dir3,
    e.email,
    e.telefono,
    m.nombre AS municipio
FROM entidades e
JOIN entidades_ayuntamientos ea ON e.id = ea.entidad_id
JOIN estructura.municipios m ON e.municipio_id = m.id
WHERE e.activo = TRUE
ORDER BY e.nombre_completo;
```

**2. Buscar ayuntamiento por código DIR3:**

```sql
SELECT e.*, ea.*
FROM entidades e
JOIN entidades_ayuntamientos ea ON e.id = ea.entidad_id
WHERE ea.codigo_dir3 = :codigo_dir3;
```

**3. Buscar ayuntamiento por CIF:**

```sql
SELECT e.*, ea.*
FROM entidades e
JOIN entidades_ayuntamientos ea ON e.id = ea.entidad_id
WHERE e.cif_nif = :cif;
```

**4. Ayuntamientos que son consultados Y solicitantes:**

```sql
SELECT 
    e.nombre_completo,
    e.cif_nif,
    ea.codigo_dir3,
    ead.email_notificaciones
FROM entidades e
JOIN entidades_ayuntamientos ea ON e.id = ea.entidad_id
JOIN entidades_administrados ead ON e.id = ead.entidad_id
WHERE e.activo = TRUE
ORDER BY e.nombre_completo;
```

**5. Ayuntamientos sin código DIR3 (métodos tradicionales):**

```sql
SELECT 
    e.nombre_completo,
    e.cif_nif,
    e.email,
    e.telefono,
    m.nombre AS municipio
FROM entidades e
JOIN entidades_ayuntamientos ea ON e.id = ea.entidad_id
JOIN estructura.municipios m ON e.municipio_id = m.id
WHERE ea.codigo_dir3 IS NULL
AND e.activo = TRUE
ORDER BY e.nombre_completo;
```

**6. Ayuntamientos de una provincia específica:**

```sql
SELECT 
    e.nombre_completo,
    m.nombre AS municipio,
    m.provincia,
    ea.codigo_dir3
FROM entidades e
JOIN entidades_ayuntamientos ea ON e.id = ea.entidad_id
JOIN estructura.municipios m ON e.municipio_id = m.id
WHERE m.provincia = 'Ourense'
AND e.activo = TRUE
ORDER BY m.nombre;
```

**7. Verificar si un ayuntamiento puede actuar como solicitante:**

```sql
SELECT 
    e.nombre_completo,
    e.cif_nif,
    CASE 
        WHEN ead.entidad_id IS NOT NULL THEN 'SÍ'
        ELSE 'NO'
    END AS puede_solicitar,
    ead.email_notificaciones
FROM entidades e
JOIN entidades_ayuntamientos ea ON e.id = ea.entidad_id
LEFT JOIN entidades_administrados ead ON e.id = ead.entidad_id
WHERE e.cif_nif = :cif;
```

---

---

### ENTIDADES_DIPUTACIONES

Metadatos específicos de diputaciones provinciales que pueden actuar con múltiples roles: organismo consultado, solicitante ocasional y publicador en Boletín Oficial Provincial (BOP).

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ENTIDAD_ID** | INTEGER | Referencia a entidad base | NO | PK y FK → ENTIDADES(ID), UNIQUE, CASCADE |
| **CODIGO_DIR3** | VARCHAR(10) | Código DIR3 oficial de la diputación | NO | UNIQUE. Para notificaciones SIR cuando actúa como organismo consultado |
| **EMAIL_PUBLICACION_BOP** | VARCHAR(255) | Email para solicitar publicaciones en BOP | SÍ | Ej: boletin@bopcadiz.org. Método tradicional: correo con datos pagador + texto a publicar |
| **OBSERVACIONES** | TEXT | Notas adicionales | SÍ | Procedimientos publicación, tarifas, plataformas alternativas, contactos específicos |

#### Claves

- **PK:** `ENTIDAD_ID`
- **UNIQUE:** `CODIGO_DIR3`
- **FK:**
  - `ENTIDAD_ID` → `ENTIDADES(ID)` ON DELETE CASCADE

#### Índices Recomendados

- `CODIGO_DIR3` (único, búsqueda rápida por código oficial)

#### Relaciones

- **entidad**: ENTIDADES.id (FK, relación 1:1 con entidad base)

#### Notas de Versión

- **v1.0** (01/02/2026): Creación inicial con estructura minimalista (DIR3 + email publicación BOP + observaciones)

#### Filosofía

Tabla de metadatos para **diputaciones provinciales**:

- **Relación 1:1** con `ENTIDADES` mediante `ENTIDAD_ID` como PK y FK
- **Estructura minimalista:** Solo campos que NO están en `ENTIDADES`
- **CODIGO_DIR3 como clave de negocio:** Identificación oficial para comunicaciones interadministrativas
- **EMAIL_PUBLICACION_BOP:** Método real de trabajo (al menos Cádiz y otras provincias)
- **Sin representante:** La entidad es la corporación en sí (persona jurídica pública)
- **Múltiples roles posibles:** Solicitante + Consultado + Publicador BOP
- **Notificaciones:** SIR (DIR3) cuando actúa como organismo, Notifica cuando actúa como solicitante

#### Campos que YA están en ENTIDADES (no duplicar)

**Todos estos datos viven en `ENTIDADES`:**

- `CIF_NIF`: CIF formato `P` + código provincia + dígito control (ej: `P2800000J` - Diputación Madrid)
- `NOMBRE_COMPLETO`: Denominación oficial (ej: "Diputación Provincial de Cádiz", "Diputació de València")
- `EMAIL`: Email general corporativo
- `TELEFONO`: Teléfono general
- `DIRECCION`, `CODIGO_POSTAL`: Sede de la diputación (Palacio Provincial)
- `MUNICIPIO_ID`: FK a municipio donde tiene sede (capital provincia), pero NO gestiona ese municipio

**Si se necesitan contactos específicos (email área técnica, teléfono informática), usar campo `OBSERVACIONES`.**

#### CIF de Diputaciones

**Formato obligatorio:**
- Letra **P** (personas jurídicas públicas)
- Código de provincia (2 dígitos) + 5 ceros
- 1 dígito de control

**Ejemplos reales:**
- Madrid: `P2800000J` (provincia 28)
- Cádiz: `P1100000B` (provincia 11)
- Valencia: `P4600000A` (provincia 46)
- Sevilla: `P4100000G` (provincia 41)
- Barcelona: `P0800000H` (provincia 08)

**Características:**
- CIF único por diputación (no compartido)
- Cada diputación es entidad jurídica independiente
- CIF obligatorio (NOT NULL en `ENTIDADES.CIF_NIF`)

#### Sistema DIR3: Diputaciones

**¿Qué es DIR3 para diputaciones?**
- Código oficial de la unidad orgánica de la diputación en DIR3
- Obligatorio para facturación electrónica y comunicaciones interadministrativas
- Formato: 1-2 letras + 7-8 números (ej: `L01110002`)

**Uso en BDDAT:**
- Identificación única para notificaciones vía **SIR** cuando la diputación actúa como **organismo consultado** (emite informe)
- NO se usa para notificar cuando actúa como **solicitante** (ahí usa Notifica con email)

**Consulta de códigos DIR3:**
- Portal oficial: https://administracionelectronica.gob.es/ctt/dir3
- Descargas: https://administracionelectronica.gob.es/ctt/dir3/descargas

#### EMAIL_PUBLICACION_BOP: Método Real de Trabajo

**Sistema tradicional de publicación en BOP:**

1. **BDDAT prepara texto** del anuncio a publicar
2. **Se envía email** a dirección de publicaciones BOP:
   - Datos del pagador (organismo que solicita)
   - Texto completo del anuncio
   - Justificante de pago (si aplica)
3. **BOP procesa** y publica en próxima edición
4. **Confirmación** mediante publicación en boletín oficial

**Ejemplos reales de emails:**
- Cádiz: `boletin@bopcadiz.org`
- Valencia: `bop@dival.es`
- Sevilla: `bop@dipusevilla.es`
- Málaga: `bop@malaga.es`

**Campo nullable:**
- Algunas diputaciones pueden usar exclusivamente plataforma electrónica (SIR u otra)
- Si existe método alternativo, se documenta en `OBSERVACIONES`

#### BOP Cádiz: Caso Real Verificado

**Gestión del Boletín Oficial Provincial de Cádiz:**

- **Responsable:** Diputación Provincial de Cádiz
- **Concesionaria:** Asociación de la Prensa de Cádiz (CIF: G11013232)
- **Domicilio:** Calle Ancha, nº 6 - 11001 Cádiz
- **Email:** `boletin@bopcadiz.org`
- **Teléfonos:** 956 213 861 / 956 212 370
- **Web:** https://www.bopcadiz.es

**Fuente:** [Boletín Oficial Provincia Cádiz - Contacto](https://www.bopcadiz.es/contacto/)

**Procedimiento:**
- La Diputación de Cádiz contrata a la Asociación de la Prensa como concesionaria
- La Asociación gestiona la edición, publicación y administración del BOP
- Los organismos envían anuncios al email indicado

#### Múltiples Roles: Diputación con Triple Capacidad

**Escenario:** Diputación de Cádiz actúa en 3 roles diferentes

**Registros necesarios:**

1. **ENTIDADES** (tabla base):
   - `cif_nif`: "P1100000B" (CIF único)
   - `nombre_completo`: "Diputación Provincial de Cádiz"
   - `tipo_entidad_id`: DIPUTACION
   - `municipio_id`: FK a Cádiz capital (sede, NO gestión)

2. **ENTIDADES_DIPUTACIONES** (rol: consultado + publicador BOP):
   - `codigo_dir3`: "L01110002" (código oficial)
   - `email_publicacion_bop`: "boletin@bopcadiz.org"
   - `observaciones`: "Concesionaria: Asociación Prensa Cádiz. Tarifas: consultar Ordenanza. Publicación L-V días hábiles."

3. **ENTIDADES_ADMINISTRADOS** (rol: solicitante ocasional):
   - `email_notificaciones`: "notifica@dipucadiz.es"
   - `representante_nif_cif`: NULL (gestión corporativa)
   - `representante_nombre`: NULL

**Filtrado automático en interfaz:**

```sql
-- Contexto: Solicitar informe (fase CONSULTAS)
-- Aparecen diputaciones con tipo DIPUTACION
SELECT e.* FROM entidades e
JOIN tipos_entidades te ON e.tipo_entidad_id = te.id
WHERE te.puede_ser_consultado = TRUE;

-- Contexto: Crear solicitud (diputación solicita instalación propia)
-- Solo aparecen entidades con registro en ENTIDADES_ADMINISTRADOS
SELECT e.* FROM entidades e
JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE e.activo = TRUE;

-- Contexto: Publicar en BOP
-- Solo aparecen diputaciones
SELECT e.* FROM entidades e
JOIN tipos_entidades te ON e.tipo_entidad_id = te.id
WHERE te.codigo = 'DIPUTACION'
AND e.activo = TRUE;
```

#### Diferencia con Ayuntamientos: Publicación

**AYUNTAMIENTOS:**
- Publican en su **tablón edictos municipal** (Ley 39/2015 Art. 45.4)
- BDDAT notifica vía **SIR** al ayuntamiento
- Ayuntamiento publica en su sede electrónica
- Sin campo `email_publicacion` (proceso interno del ayuntamiento)

**DIPUTACIONES:**
- Publican en **BOP** (Boletín Oficial Provincial)
- BDDAT solicita publicación vía **email** tradicional (método real)
- Campo `EMAIL_PUBLICACION_BOP` necesario (ej: `boletin@bopcadiz.org`)
- BOP puede estar gestionado por concesionaria (caso Cádiz: Asociación Prensa)

#### Flujo UX: Copia de Datos entre Roles

**Aplica la misma lógica que otras tablas de metadatos:**

1. Usuario introduce CIF o nombre que ya existe
2. Sistema detecta roles activos de la diputación
3. Sistema ofrece copiar datos de rol existente (si aplica)
4. Usuario selecciona o introduce datos nuevos

**Campos relevantes para copiar:**
- `email_notificaciones` (si actúa como solicitante)
- `email_publicacion_bop` (si ya existe registro previo)

#### Reglas de Negocio

1. **CODIGO_DIR3 obligatorio** (NOT NULL, UNIQUE)
2. **CIF_NIF obligatorio** en `ENTIDADES` (formato P+provincia+00000+control)
3. **EMAIL_PUBLICACION_BOP opcional** (nullable, algunas usan solo plataforma electrónica)
4. **Sin representante** (no aplican campos `REPRESENTANTE_*`)
5. **Múltiples roles:** Una diputación puede estar en esta tabla Y en `ENTIDADES_ADMINISTRADOS`
6. **Notificaciones duales:**
   - Como **organismo consultado**: SIR (usa CODIGO_DIR3)
   - Como **solicitante**: Notifica (usa email de `ENTIDADES_ADMINISTRADOS`)
7. **Publicación BOP:** Método tradicional email (datos pagador + texto anuncio)
8. **Validación DIR3:** Formato alfanumérico, 8-10 caracteres
9. **MUNICIPIO_ID en ENTIDADES:** Sede de la diputación (capital), NO implica gestión de ese municipio

#### Validaciones

**Validación Python:**

```python
import re

def validar_cif_diputacion(cif):
    """
    Valida CIF de diputación.
    Formato: P + código provincia (2 dígitos) + 00000 + dígito control
    Ejemplo válido: P2800000J (Diputación Madrid)
    """
    if not cif:
        return False
    
    # Patrón: P + 2 dígitos + 5 ceros + 1 letra/dígito
    patron = r'^P\d{2}00000[A-Z0-9]$'
    return re.match(patron, cif.upper()) is not None

def validar_codigo_dir3(codigo):
    """
    Valida formato de código DIR3.
    Formato: 1-2 letras + 7-8 números
    Ejemplos válidos: L01110002, A12002696
    """
    if not codigo:
        return False
    
    # Patrón: 1-2 letras mayúsculas + 7-8 dígitos
    patron = r'^[A-Z]{1,2}\d{7,8}$'
    return re.match(patron, codigo.upper()) is not None

def validar_email(email):
    """
    Valida formato básico de email.
    """
    if not email:
        return True  # Nullable
    
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None

class EntidadDiputacion(db.Model):
    # ...
    
    @validates('codigo_dir3')
    def validate_codigo_dir3(self, key, value):
        if not value:
            raise ValueError("Código DIR3 es obligatorio")
        
        value_upper = value.upper().strip()
        
        if not validar_codigo_dir3(value_upper):
            raise ValueError(
                f"Código DIR3 inválido: {value}. "
                "Formato esperado: 1-2 letras + 7-8 dígitos (ej: L01110002)"
            )
        
        return value_upper
    
    @validates('email_publicacion_bop')
    def validate_email_publicacion(self, key, value):
        if value and not validar_email(value):
            raise ValueError(
                f"Email inválido: {value}. "
                "Formato esperado: usuario@dominio.ext"
            )
        
        return value.lower().strip() if value else None
```

**Validación en interfaz:**

```javascript
// Validación cliente (JavaScript)
function validarCIFDiputacion(cif) {
    const patron = /^P\d{2}00000[A-Z0-9]$/;
    return patron.test(cif.toUpperCase());
}

function validarDIR3(codigo) {
    const patron = /^[A-Z]{1,2}\d{7,8}$/;
    return patron.test(codigo.toUpperCase());
}

function validarEmail(email) {
    if (!email) return true; // Nullable
    const patron = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return patron.test(email);
}
```

#### Consultas Frecuentes

**1. Listar diputaciones con su DIR3, CIF y email publicación:**

```sql
SELECT 
    e.id,
    e.nombre_completo,
    e.cif_nif,
    ed.codigo_dir3,
    ed.email_publicacion_bop,
    e.email,
    e.telefono,
    p.nombre AS provincia
FROM entidades e
JOIN entidades_diputaciones ed ON e.id = ed.entidad_id
JOIN municipios m ON e.municipio_id = m.id
JOIN provincias p ON m.provincia_id = p.id
WHERE e.activo = TRUE
ORDER BY p.nombre;
```

**2. Buscar diputación por código DIR3:**

```sql
SELECT e.*, ed.*
FROM entidades e
JOIN entidades_diputaciones ed ON e.id = ed.entidad_id
WHERE ed.codigo_dir3 = :codigo_dir3;
```

**3. Buscar diputación por CIF:**

```sql
SELECT e.*, ed.*
FROM entidades e
JOIN entidades_diputaciones ed ON e.id = ed.entidad_id
WHERE e.cif_nif = :cif;
```

**4. Diputaciones que son consultadas Y solicitantes:**

```sql
SELECT 
    e.nombre_completo,
    e.cif_nif,
    ed.codigo_dir3,
    ed.email_publicacion_bop,
    ead.email_notificaciones
FROM entidades e
JOIN entidades_diputaciones ed ON e.id = ed.entidad_id
JOIN entidades_administrados ead ON e.id = ead.entidad_id
WHERE e.activo = TRUE
ORDER BY e.nombre_completo;
```

**5. Obtener email publicación BOP para una provincia:**

```sql
SELECT 
    p.nombre AS provincia,
    e.nombre_completo,
    ed.email_publicacion_bop,
    e.telefono
FROM entidades e
JOIN entidades_diputaciones ed ON e.id = ed.entidad_id
JOIN municipios m ON e.municipio_id = m.id
JOIN provincias p ON m.provincia_id = p.id
WHERE p.codigo = '11'  -- Cádiz
AND e.activo = TRUE;
```

**6. Verificar si una diputación puede actuar como solicitante:**

```sql
SELECT 
    e.nombre_completo,
    CASE 
        WHEN ead.entidad_id IS NOT NULL THEN 'SÍ'
        ELSE 'NO'
    END AS puede_solicitar
FROM entidades e
JOIN entidades_diputaciones ed ON e.id = ed.entidad_id
LEFT JOIN entidades_administrados ead ON e.id = ead.entidad_id
WHERE e.cif_nif = :cif;
```

**7. Diputaciones sin email publicación BOP (usan plataforma electrónica):**

```sql
SELECT 
    e.nombre_completo,
    ed.codigo_dir3,
    ed.observaciones
FROM entidades e
JOIN entidades_diputaciones ed ON e.id = ed.entidad_id
WHERE ed.email_publicacion_bop IS NULL
AND e.activo = TRUE;
```

---

---

### ENTIDADES_EMPRESAS_SERVICIO_PUBLICO

Metadatos específicos de empresas operadoras de infraestructuras críticas y servicios públicos que actúan como organismos consultados (informes sobre afecciones a sus infraestructuras). A diferencia de otras entidades, estas empresas pueden actuar simultáneamente como solicitantes (necesitan entrada en ENTIDADES_ADMINISTRADOS) y consultados.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ENTIDAD_ID** | INTEGER | Referencia a entidad base | NO | PK y FK → ENTIDADES(ID), UNIQUE, CASCADE |
| **CODIGO_DIR3** | VARCHAR(20) | Código DIR3 para notificaciones SIR | SÍ | Opcional, no todas las empresas tienen. Para comunicaciones interadministrativas |

#### Claves

- **PK:** `ENTIDAD_ID`
- **FK:**
  - `ENTIDAD_ID` → `ENTIDADES(ID)` ON DELETE CASCADE

#### Índices

- `ix_public_entidades_empresas_servicio_publico_codigo_dir3` (único, sobre `CODIGO_DIR3`)

#### Relaciones

- **entidad**: ENTIDADES.id (FK, relación 1:1 con entidad base)

#### Notas de Versión

- **v1.0** (01/02/2026): Creación inicial con estructura minimalista (solo DIR3 opcional)
- **v1.1** (04/02/2026): Sincronización con schema.sql - Eliminar campos de representante que NO existen en la tabla real

#### Filosofía

Tabla de metadatos para **empresas de servicio público** (operadores de infraestructuras críticas):

- **Relación 1:1** con `ENTIDADES` mediante `ENTIDAD_ID` como PK y FK
- **Estructura minimalista:** Solo código DIR3 opcional
- **Doble rol simultáneo:**
  - Como **organismo consultado**: Emiten informes sobre afecciones a sus infraestructuras existentes (uso DIR3 si lo tienen)
  - Como **solicitante**: Si necesitan presentar solicitudes propias, deben tener entrada adicional en `ENTIDADES_ADMINISTRADOS`
- **DIR3 opcional:** No todas las empresas privadas tienen código DIR3 (solo si son operadores de infraestructuras con convenios interadministrativos)

#### Campos que YA están en ENTIDADES (no duplicar)

**Todos estos datos viven en `ENTIDADES`:**

- `CIF_NIF`: CIF de la empresa operadora
- `NOMBRE_COMPLETO`: Razón social (ej: "E-Distribución Redes Digitales S.L.U.", "Gas Natural Distribución SDG S.A.")
- `EMAIL`: Email general corporativo
- `TELEFONO`: Teléfono general
- `DIRECCION`, `CODIGO_POSTAL`, `MUNICIPIO_ID`: Domicilio social
- `ACTIVO`: Borrado lógico

**Para contactos específicos o representantes, usar campo `NOTAS` en `ENTIDADES`.**

#### Representación y Notificaciones

**A DIFERENCIA de las tablas MD anteriores:**

Esta tabla **NO tiene campos de representante** (`representante_nif_cif`, `representante_nombre`, etc.). 

**¿Por qué?**

1. **Cuando actúan como consultadas:** No necesitan notificaciones vía Notifica (emiten informes, no los reciben)
2. **Cuando actúan como solicitantes:** Deben tener entrada en `ENTIDADES_ADMINISTRADOS` donde SÍ están los campos de representante

**Patrón real:**
```
Empresa X (ENTIDADES)
│
├─ ENTIDADES_EMPRESAS_SERVICIO_PUBLICO (rol: consultada)
│   └─ codigo_dir3 (opcional)
│
└─ ENTIDADES_ADMINISTRADOS (rol: solicitante)
    ├─ email_notificaciones
    ├─ representante_nif_cif
    └─ representante_nombre
```

#### Ejemplos de Entidades (tipos)

**Sector energético:**
- E-Distribución Redes Digitales S.L.U. (distribuidora eléctrica)
- Red Eléctrica de España S.A.U. (transporte eléctrica)
- Gas Natural Distribución SDG S.A. (distribuidora gas)

**Sector agua:**
- Consorcio de Aguas de la provincia
- Empresa Metropolitana de Abastecimiento

**Sector transporte:**
- ADIF (Administrador de Infraestructuras Ferroviarias)
- Operadores de transporte por cable

**Sector telecomunicaciones:**
- Telefónica de España S.A.U.
- Operadores de fibra óptica

#### Sistema DIR3: Empresas de Servicio Público

**¿Qué es DIR3 para empresas privadas?**
- Código opcional que algunas empresas de servicio público tienen cuando operan infraestructuras con convenios interadministrativos
- Formato: 1-2 letras + 7-8 números (ej: `E12345678`)
- **NO todas las empresas lo tienen** (mayormente empresas públicas o con participación pública)

**Uso en BDDAT:**
- Identificación para notificaciones vía **SIR** cuando actúan como **organismos consultados**
- Si no tienen DIR3, se usan métodos tradicionales (email, correo postal)

**Campo nullable:**
- TRUE (no obligatorio)
- Mayoría de empresas privadas no tienen DIR3

#### Regla de Negocio: Doble Entrada Posible

**Una empresa puede estar en DOS tablas de metadatos:**

1. **Esta tabla** (`ENTIDADES_EMPRESAS_SERVICIO_PUBLICO`):
   - Para actuar como consultada (emitir informes)
   - Solo necesita `codigo_dir3` (opcional)

2. **`ENTIDADES_ADMINISTRADOS`**:
   - Para actuar como solicitante (presentar solicitudes)
   - Necesita `email_notificaciones`, `representante_*`, etc.

**Ejemplo real:**
```sql
-- E-Distribución solicita autorización para nueva subestación
-- Y también es consultada sobre afecciones en proyectos de terceros

-- 1. ENTIDADES (base)
INSERT INTO entidades (tipo_entidad_id, cif_nif, nombre_completo)
VALUES (tipo_empresa_servicio_publico_id, 'B12345678', 'E-Distribución Redes Digitales S.L.U.');

-- 2. ENTIDADES_EMPRESAS_SERVICIO_PUBLICO (rol: consultada)
INSERT INTO entidades_empresas_servicio_publico (entidad_id, codigo_dir3)
VALUES (entidad_id, NULL);  -- Sin DIR3

-- 3. ENTIDADES_ADMINISTRADOS (rol: solicitante)
INSERT INTO entidades_administrados (
    entidad_id, 
    email_notificaciones,
    representante_nif_cif,
    representante_nombre
) VALUES (
    entidad_id,
    'notificaciones@edistribucion.com',
    'B98765432',
    'Consultora ACME Proyectos S.L.'
);
```

#### Filtrado Automático en Interfaz

**Contexto 1: Solicitar informe sobre afecciones (fase CONSULTAS)**
```sql
-- Solo aparecen empresas servicio público + organismos + ayuntamientos
SELECT e.* FROM entidades e
JOIN tipos_entidades te ON e.tipo_entidad_id = te.id
WHERE te.puede_ser_consultado = TRUE
AND e.activo = TRUE;
```

**Contexto 2: Crear solicitud (empresa solicita autorización propia)**
```sql
-- Solo aparecen entidades con registro en ENTIDADES_ADMINISTRADOS
SELECT e.* FROM entidades e
JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE e.activo = TRUE;
```

#### Validaciones

**Validación Python:**

```python
import re

def validar_codigo_dir3(codigo):
    """
    Valida formato de código DIR3.
    Formato: 1-2 letras + 7-8 números
    Ejemplos válidos: E12345678, EA0044689
    """
    if not codigo:
        return True  # Nullable, válido si es None/vacío
    
    # Patrón: 1-2 letras mayúsculas + 7-8 dígitos
    patron = r'^[A-Z]{1,2}\d{7,8}$'
    return re.match(patron, codigo.upper()) is not None

class EntidadEmpresaServicioPublico(db.Model):
    # ...
    
    @validates('codigo_dir3')
    def validate_codigo_dir3(self, key, value):
        if not value:
            return None  # Nullable
        
        value_upper = value.upper().strip()
        
        if not validar_codigo_dir3(value_upper):
            raise ValueError(
                f"Código DIR3 inválido: {value}. "
                "Formato esperado: 1-2 letras + 7-8 dígitos (ej: E12345678)"
            )
        
        return value_upper
```

**Validación en interfaz:**

```javascript
// Validación cliente (JavaScript)
function validarDIR3(codigo) {
    if (!codigo || codigo.trim() === '') return true; // Nullable
    const patron = /^[A-Z]{1,2}\d{7,8}$/;
    return patron.test(codigo.toUpperCase());
}
```

#### Consultas Frecuentes

**1. Listar empresas de servicio público con DIR3:**

```sql
SELECT 
    e.id,
    e.nombre_completo,
    e.cif_nif,
    ees.codigo_dir3,
    e.email,
    e.telefono
FROM entidades e
JOIN entidades_empresas_servicio_publico ees ON e.id = ees.entidad_id
WHERE e.activo = TRUE
ORDER BY e.nombre_completo;
```

**2. Empresas que son consultadas Y solicitantes:**

```sql
SELECT 
    e.nombre_completo,
    e.cif_nif,
    ees.codigo_dir3,
    ea.email_notificaciones,
    ea.representante_nombre
FROM entidades e
JOIN entidades_empresas_servicio_publico ees ON e.id = ees.entidad_id
JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE e.activo = TRUE
ORDER BY e.nombre_completo;
```

**3. Empresas sin DIR3 (solo métodos tradicionales):**

```sql
SELECT 
    e.nombre_completo,
    e.cif_nif,
    e.email,
    e.telefono
FROM entidades e
JOIN entidades_empresas_servicio_publico ees ON e.id = ees.entidad_id
WHERE ees.codigo_dir3 IS NULL
AND e.activo = TRUE
ORDER BY e.nombre_completo;
```

**4. Verificar si empresa puede actuar como solicitante:**

```sql
SELECT 
    e.nombre_completo,
    CASE 
        WHEN ea.entidad_id IS NOT NULL THEN 'SÍ'
        ELSE 'NO'
    END AS puede_solicitar,
    ea.email_notificaciones
FROM entidades e
JOIN entidades_empresas_servicio_publico ees ON e.id = ees.entidad_id
LEFT JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE e.cif_nif = :cif;
```

**5. Empresas por sector (usando notas o clasificación):**

```sql
-- Asumiendo que el sector está en campo NOTAS o en un futuro campo sector
SELECT 
    e.nombre_completo,
    e.cif_nif,
    ees.codigo_dir3
FROM entidades e
JOIN entidades_empresas_servicio_publico ees ON e.id = ees.entidad_id
WHERE e.notas ILIKE '%energía%'  -- Filtro ejemplo
AND e.activo = TRUE
ORDER BY e.nombre_completo;
```

---

---

### ENTIDADES_ORGANISMOS_PUBLICOS

Metadatos específicos de administraciones públicas y organismos oficiales que actúan como organismos consultados (informes técnicos/administrativos) en procedimientos de autorización. Incluye información sobre ámbito territorial, tipo de organismo y vigencia temporal.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ENTIDAD_ID** | INTEGER | Referencia a entidad base | NO | PK y FK → ENTIDADES(ID), UNIQUE, CASCADE |
| **CODIGO_DIR3** | VARCHAR(20) | Código DIR3 oficial del organismo | SÍ | Identificación para notificaciones vía SIR/BandeJA. Formato: EA0044689, A12002696 |
| **AMBITO** | VARCHAR(50) | Ámbito del organismo | SÍ | ESTATAL, AUTONOMICO, LOCAL |
| **TIPO_ORGANISMO** | VARCHAR(50) | Tipo específico de organismo | SÍ | Consejería, Ministerio, Confederación, Entidad Pública, etc. |
| **LEGISLATURA** | VARCHAR(50) | Legislatura asociada | SÍ | Ej: "2019-2023", "2023-2027" |
| **FECHA_DESDE** | DATE | Fecha inicio vigencia del organismo | SÍ | Desde cuando está operativo |
| **FECHA_HASTA** | DATE | Fecha fin vigencia del organismo | SÍ | NULL si sigue activo |

#### Claves

- **PK:** `ENTIDAD_ID`
- **FK:**
  - `ENTIDAD_ID` → `ENTIDADES(ID)` ON DELETE CASCADE

#### Índices

- `ix_public_entidades_organismos_publicos_codigo_dir3` (sobre `CODIGO_DIR3`)
- `ix_public_entidades_organismos_publicos_ambito` (sobre `AMBITO`)
- `ix_public_entidades_organismos_publicos_legislatura` (sobre `LEGISLATURA`)

#### Relaciones

- **entidad**: ENTIDADES.id (FK, relación 1:1 con entidad base)

#### Notas de Versión

- **v1.0** (01/02/2026): Creación inicial con estructura minimalista
- **v1.1** (04/02/2026): Sincronización con schema.sql - Agregar campos ambito, tipo_organismo, legislatura, fechas. codigo_dir3 nullable y VARCHAR(20)

#### Filosofía

Tabla de metadatos para **organismos públicos** (administraciones y entidades oficiales):

- **Relación 1:1** con `ENTIDADES` mediante `ENTIDAD_ID` como PK y FK
- **Estructura enriquecida:** Campos de clasificación y vigencia temporal
- **CODIGO_DIR3 opcional:** Puede ser NULL (organismos históricos o sin código)
- **Sin representante:** La entidad es el organismo en sí (persona jurídica pública)
- **Roles múltiples posibles:** Un organismo puede ser consultado Y solicitante (doble entrada: esta tabla + `ENTIDADES_ADMINISTRADOS`)
- **Vigencia temporal:** Organismos que cambian con legislaturas o reorganizaciones administrativas
- **Notificaciones interadministrativas:** Sistema SIR (Servicio Integrado de Registro) usando CODIGO_DIR3

#### Campos que YA están en ENTIDADES (no duplicar)

**Todos estos datos viven en `ENTIDADES`:**

- `CIF_NIF`: Puede ser NULL o CIF compartido (AGE: S2833011F, Junta Andalucía: CIF único)
- `NOMBRE_COMPLETO`: Denominación oficial del organismo (ej: "Dirección General de Industria, Energía y Minas")
- `EMAIL`: Email general del organismo
- `TELEFONO`: Teléfono general
- `DIRECCION`, `CODIGO_POSTAL`, `MUNICIPIO_ID`: Sede del organismo
- `ACTIVO`: Borrado lógico
- `NOTAS`: Observaciones generales

#### Campo: AMBITO

**Valores típicos:**

- `ESTATAL`: Organismos de la Administración General del Estado (AGE)
  - Ministerios, Direcciones Generales, Organismos Autónomos
  - Ejemplos: Ministerio para la Transición Ecológica, MITECO, Confederación Hidrográfica
  
- `AUTONOMICO`: Organismos de Comunidades Autónomas
  - Consejerías, Direcciones Generales, Agencias autonómicas
  - Ejemplos: Junta de Andalucía, Xunta de Galicia
  
- `LOCAL`: Organismos de Administración Local (no ayuntamientos individuales)
  - Diputaciones, Consorcios, Mancomunidades
  - **Nota:** Ayuntamientos usan tabla `ENTIDADES_AYUNTAMIENTOS`

**Uso:**
- Clasificación para estadísticas
- Filtrado en interfaces de consulta
- Asignación automática de competencias según ámbito

#### Campo: TIPO_ORGANISMO

**Ejemplos de valores:**

- `Ministerio`: Ministerio para la Transición Ecológica y el Reto Demográfico
- `Dirección General`: Dirección General de Política Energética y Minas
- `Organismo Autónomo`: ADIF, Puertos del Estado
- `Consejería`: Consejería de Agricultura, Agua y Desarrollo Rural
- `Viceconsejería`: Viceconsejería de Medio Ambiente
- `Confederación`: Confederación Hidrográfica del Miño-Sil
- `Agencia`: Agencia Andaluza de la Energía
- `Entidad Pública`: Entidad Pública Empresarial de X

**Uso:**
- Clasificación fina para organización administrativa
- Ayuda en autocompletado de formularios
- Filtrado por nivel jerárquico

#### Campo: LEGISLATURA

**Formato:** "YYYY-YYYY" (año inicio - año fin)

**Ejemplos:**
- `2019-2023`: XIV Legislatura
- `2023-2027`: XV Legislatura (actual)
- `2015-2019`: Legislatura anterior

**Uso:**
- Tracking de reorganizaciones administrativas tras cambios de gobierno
- Consulta de organismos vigentes en momento histórico
- Auditoría de cambios de competencias

**Nota:** Puede ser NULL si el organismo no está vinculado a legislaturas (ej: organismos técnicos permanentes)

#### Campos: FECHA_DESDE / FECHA_HASTA

**FECHA_DESDE:**
- Fecha en que el organismo comenzó a operar
- Puede coincidir con inicio de legislatura o ser independiente
- NULL si no se conoce fecha exacta (organismos históricos)

**FECHA_HASTA:**
- NULL = organismo activo actualmente
- Fecha = organismo cesado/reorganizado/fusionado
- Permite mantener histórico de organismos que ya no existen

**Ejemplos:**

```sql
-- Organismo actual (Ministerio actual)
fecha_desde = '2020-01-13'  -- Formación gobierno
fecha_hasta = NULL           -- Activo

-- Organismo histórico (Ministerio anterior, reorganizado)
fecha_desde = '2016-11-04'
fecha_hasta = '2020-01-13'   -- Reorganización

-- Consejería tras cambio autonómico
fecha_desde = '2022-07-20'  -- Nueva legislatura
fecha_hasta = NULL           -- Activa
```

**Uso:**
- Mantener histórico de informes emitidos por organismos desaparecidos
- Validar competencias según fecha de solicitud
- Migración automática a nuevo organismo competente

#### CIF de Organismos Públicos: Casos Especiales

**Administración General del Estado (AGE):**
- **CIF único compartido:** `S2833011F`
- Todos los Ministerios, organismos autónomos, etc. comparten el mismo CIF
- Identificación real mediante **CODIGO_DIR3**

**Comunidades Autónomas (ej: Junta de Andalucía):**
- **CIF único compartido** por todas las Consejerías y Direcciones Generales
- Cada organismo se identifica mediante **CODIGO_DIR3**

**Ayuntamientos:**
- **CIF propio único** por ayuntamiento (letra P + código)
- Son entidades jurídicas independientes
- **No usan esta tabla** → Usan `ENTIDADES_AYUNTAMIENTOS`

**Entidades locales menores, consorcios, etc.:**
- Pueden tener CIF propio o compartido según su naturaleza jurídica

#### Sistema DIR3: Directorio Común de Unidades Orgánicas

**¿Qué es DIR3?**
- Directorio oficial de unidades orgánicas y oficinas de las AAPP españolas
- Obligatorio para facturación electrónica y comunicaciones interadministrativas
- Formato: 1-2 letras + 7-8 números (ej: `EA0044689`, `A12002696`)

**Uso en BDDAT:**
- Identificación única del organismo (más fiable que CIF)
- Clave para enviar notificaciones vía **SIR** (Servicio Integrado de Registro)
- En Junta de Andalucía: Sistema **BandeJA** (Bandeja de la Junta de Andalucía) para comunicaciones interiores electrónicas

**Campo NULLABLE:**
- Organismos históricos pueden no tener DIR3
- Organismos extranjeros o especiales sin código DIR3
- Organismos en proceso de registro

**Consulta de códigos DIR3:**
- Portal oficial: https://administracionelectronica.gob.es/ctt/dir3
- Descargas: https://administracionelectronica.gob.es/ctt/dir3/descargas

#### Roles Múltiples: Organismo Consultado Y Solicitante

**Escenario:** Consejería de Medio Ambiente solicita autorización para instalación eléctrica en depuradora propia

**Registros necesarios:**

1. **ENTIDADES** (tabla base):
   - `cif_nif`: CIF único Junta Andalucía (o NULL)
   - `nombre_completo`: "Consejería de Agricultura, Agua y Desarrollo Rural"
   - `tipo_entidad_id`: ORGANISMO_PUBLICO

2. **ENTIDADES_ORGANISMOS_PUBLICOS** (rol: consultado):
   - `codigo_dir3`: "A12002696" (código oficial)
   - `ambito`: "AUTONOMICO"
   - `tipo_organismo`: "Consejería"
   - `legislatura`: "2023-2027"
   - `fecha_desde`: "2022-07-20"
   - `fecha_hasta`: NULL

3. **ENTIDADES_ADMINISTRADOS** (rol: solicitante):
   - `email_notificaciones`: "notifica.medioambiente@juntadeandalucia.es"
   - `representante_nif_cif`: NULL (gestión corporativa)
   - `representante_nombre`: NULL

**Filtrado automático en interfaz:**

```sql
-- Contexto: Solicitar informe (fase CONSULTAS)
-- Solo aparecen organismos con tipo ORGANISMO_PUBLICO + otros consultables
SELECT e.* FROM entidades e
JOIN tipos_entidades te ON e.tipo_entidad_id = te.id
WHERE te.puede_ser_consultado = TRUE
AND e.activo = TRUE;

-- Contexto: Crear solicitud
-- Solo aparecen entidades con registro en ENTIDADES_ADMINISTRADOS
SELECT e.* FROM entidades e
JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE e.activo = TRUE;
```

#### Reglas de Negocio

1. **CODIGO_DIR3 opcional** (puede ser NULL)
2. **CIF_NIF opcional** en `ENTIDADES` (puede ser NULL o compartido)
3. **Sin representante** (no aplican campos `REPRESENTANTE_*`)
4. **Múltiples roles:** Un organismo puede estar en esta tabla Y en `ENTIDADES_ADMINISTRADOS`
5. **Notificaciones interadministrativas:** Usar CODIGO_DIR3 para SIR, no email Notifica
6. **Vigencia temporal:** `fecha_hasta` NULL = organismo activo
7. **Reorganizaciones:** Crear nuevo registro con nuevo `entidad_id` y cerrar anterior con `fecha_hasta`

#### Validaciones

**Validación Python:**

```python
import re
from datetime import date

def validar_codigo_dir3(codigo):
    """
    Valida formato de código DIR3.
    Formato: 1-2 letras + 7-8 números
    Ejemplos válidos: EA0044689, A12002696
    """
    if not codigo:
        return True  # Nullable
    
    # Patrón: 1-2 letras mayúsculas + 7-8 dígitos
    patron = r'^[A-Z]{1,2}\d{7,8}$'
    return re.match(patron, codigo.upper()) is not None

def validar_legislatura(legislatura):
    """
    Valida formato de legislatura: YYYY-YYYY
    """
    if not legislatura:
        return True  # Nullable
    
    patron = r'^\d{4}-\d{4}$'
    if not re.match(patron, legislatura):
        return False
    
    inicio, fin = legislatura.split('-')
    return int(inicio) < int(fin)

class EntidadOrganismoPublico(db.Model):
    # ...
    
    @validates('codigo_dir3')
    def validate_codigo_dir3(self, key, value):
        if not value:
            return None  # Nullable
        
        value_upper = value.upper().strip()
        
        if not validar_codigo_dir3(value_upper):
            raise ValueError(
                f"Código DIR3 inválido: {value}. "
                "Formato esperado: 1-2 letras + 7-8 dígitos (ej: EA0044689)"
            )
        
        return value_upper
    
    @validates('ambito')
    def validate_ambito(self, key, value):
        if not value:
            return None
        
        ambitos_validos = ['ESTATAL', 'AUTONOMICO', 'LOCAL']
        value_upper = value.upper().strip()
        
        if value_upper not in ambitos_validos:
            raise ValueError(
                f"Ámbito inválido: {value}. "
                f"Valores permitidos: {', '.join(ambitos_validos)}"
            )
        
        return value_upper
    
    @validates('legislatura')
    def validate_legislatura(self, key, value):
        if not value:
            return None
        
        if not validar_legislatura(value):
            raise ValueError(
                f"Legislatura inválida: {value}. "
                "Formato esperado: YYYY-YYYY (ej: 2023-2027)"
            )
        
        return value
    
    @validates('fecha_hasta')
    def validate_fecha_hasta(self, key, value):
        if not value:
            return None  # NULL = activo
        
        if self.fecha_desde and value < self.fecha_desde:
            raise ValueError(
                "fecha_hasta no puede ser anterior a fecha_desde"
            )
        
        return value
```

#### Consultas Frecuentes

**1. Listar organismos activos con su clasificación:**

```sql
SELECT 
    e.id,
    e.nombre_completo,
    eop.codigo_dir3,
    eop.ambito,
    eop.tipo_organismo,
    eop.legislatura,
    e.email,
    e.telefono
FROM entidades e
JOIN entidades_organismos_publicos eop ON e.id = eop.entidad_id
WHERE e.activo = TRUE
AND (eop.fecha_hasta IS NULL OR eop.fecha_hasta > CURRENT_DATE)
ORDER BY eop.ambito, e.nombre_completo;
```

**2. Buscar organismo por código DIR3:**

```sql
SELECT e.*, eop.*
FROM entidades e
JOIN entidades_organismos_publicos eop ON e.id = eop.entidad_id
WHERE eop.codigo_dir3 = :codigo_dir3;
```

**3. Organismos de ámbito ESTATAL activos:**

```sql
SELECT 
    e.nombre_completo,
    eop.codigo_dir3,
    eop.tipo_organismo
FROM entidades e
JOIN entidades_organismos_publicos eop ON e.id = eop.entidad_id
WHERE eop.ambito = 'ESTATAL'
AND e.activo = TRUE
AND (eop.fecha_hasta IS NULL OR eop.fecha_hasta > CURRENT_DATE)
ORDER BY e.nombre_completo;
```

**4. Organismos de legislatura actual:**

```sql
SELECT 
    e.nombre_completo,
    eop.codigo_dir3,
    eop.ambito,
    eop.legislatura,
    eop.fecha_desde
FROM entidades e
JOIN entidades_organismos_publicos eop ON e.id = eop.entidad_id
WHERE eop.legislatura = '2023-2027'
AND e.activo = TRUE
ORDER BY eop.ambito, e.nombre_completo;
```

**5. Organismos que cesaron (histórico):**

```sql
SELECT 
    e.nombre_completo,
    eop.codigo_dir3,
    eop.ambito,
    eop.fecha_desde,
    eop.fecha_hasta,
    eop.legislatura
FROM entidades e
JOIN entidades_organismos_publicos eop ON e.id = eop.entidad_id
WHERE eop.fecha_hasta IS NOT NULL
ORDER BY eop.fecha_hasta DESC;
```

**6. Organismos que son consultados Y solicitantes:**

```sql
SELECT 
    e.nombre_completo,
    eop.codigo_dir3,
    eop.ambito,
    ea.email_notificaciones
FROM entidades e
JOIN entidades_organismos_publicos eop ON e.id = eop.entidad_id
JOIN entidades_administrados ea ON e.id = ea.entidad_id
WHERE e.activo = TRUE
AND (eop.fecha_hasta IS NULL OR eop.fecha_hasta > CURRENT_DATE);
```

**7. Organismos por tipo (ej: Consejerías):**

```sql
SELECT 
    e.nombre_completo,
    eop.codigo_dir3,
    eop.legislatura
FROM entidades e
JOIN entidades_organismos_publicos eop ON e.id = eop.entidad_id
WHERE eop.tipo_organismo = 'Consejería'
AND e.activo = TRUE
AND (eop.fecha_hasta IS NULL OR eop.fecha_hasta > CURRENT_DATE)
ORDER BY e.nombre_completo;
```

---

---

### EXPEDIENTES

Tabla principal que representa cada expediente de tramitación administrativa.

#### Estructura

| Campo | Tipo | Nullable | Descripción | Notas |
|:---|:---|:---|:---|:------|
| **ID** | INTEGER | NO | Identificador único del expediente | PK, autoincremental |
| **NUMERO_AT** | INTEGER | NO | Número de expediente administrativo (formato legacy) | Único en la organización. No es el ID sino un número correlativo tomado del sistema anterior |
| **RESPONSABLE_ID** | INTEGER | SÍ | Usuario responsable del expediente | FK → USUARIOS(ID). Usuario asignado con permisos de gestión completa. NULL = expediente huérfano sin asignar |
| **TIPO_EXPEDIENTE_ID** | INTEGER | SÍ | Tipo de expediente según clasificación normativa | FK → TIPOS_EXPEDIENTES(ID). Define lógica procedimental aplicable |
| **HEREDADO** | BOOLEAN | SÍ | Indica si el expediente proviene del sistema anterior | TRUE = datos incompletos, solo metadatos heredados. FALSE/NULL = expediente gestionado completamente en este sistema |
| **PROYECTO_ID** | INTEGER | NO | Proyecto técnico único asociado al expediente | FK → PROYECTOS(ID). **UNIQUE** (relación 1:1). **Nuevo campo v3.0** |
| **TITULAR_ID** | INTEGER | SÍ | Titular actual del expediente | FK → ENTIDADES(ID). Nullable para expedientes en creación. **Nuevo campo v3.1** - Issue #64 |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `NUMERO_AT`, `PROYECTO_ID`
- **FK:**
  - `RESPONSABLE_ID` → `USUARIOS(ID)` (sin CASCADE, usuarios nunca se borran, solo se desactivan)
  - `TIPO_EXPEDIENTE_ID` → `TIPOS_EXPEDIENTES(ID)`
  - `PROYECTO_ID` → `PROYECTOS(ID)`
  - `TITULAR_ID` → `ENTIDADES(ID)` (sin CASCADE, entidades nunca se borran, solo se desactivan)

#### Índices

- `idx_expedientes_titular` sobre `TITULAR_ID`
- `idx_expedientes_numero_at` sobre `NUMERO_AT`
- `idx_expedientes_proyecto` sobre `PROYECTO_ID`
- `idx_expedientes_responsable` sobre `RESPONSABLE_ID`
- `idx_expedientes_tipo` sobre `TIPO_EXPEDIENTE_ID`

#### Decisiones de Diseño

##### Campo RESPONSABLE_ID

**Nullable = TRUE**
- **Motivo:** Permite expedientes huérfanos sin usuario asignado temporalmente
- **Regla de negocio:** Los usuarios nunca se borran físicamente, solo se desactivan mediante campo `activo`
- **Sin CASCADE:** No hay riesgo de borrado accidental de expedientes por gestión de usuarios

##### Campo TITULAR_ID (v3.1 - Issue #64)

**Contexto:**  
Los expedientes administrativos tienen un titular legal que evoluciona durante su vida útil. Cambios de titularidad pueden ocurrir por transmisión de instalación, herencia, fusión empresarial, etc.

**Problema resuelto:**  
- **Consulta eficiente del titular actual** sin joins constantes a tabla de histórico
- **Punto de referencia** para modelo temporal de titularidad
- **Validación:** expediente sin titular = expediente incompleto (estado transitorio válido durante creación)

**Decisiones:**

1. **Nullable = TRUE**
   - **Motivo:** Permite flujo de creación por etapas (expediente → proyecto → solicitud inicial)
   - **Regla:** `titular_id` debe asignarse antes de tramitar primera solicitud de autorización
   - **Validación:** En capa de negocio, no constraint CHECK (permite estados transitorios)

2. **FK a ENTIDADES (no ENTIDADES_ADMINISTRADOS)**
   - **Motivo:** Entidad es tabla base polimórfica. Validación de rol "administrado" se realiza en capa de aplicación
   - **Ventaja:** Preparado para casos excepcionales (ej: organismos públicos titulares temporales de instalaciones)
   - **Referencia:** Tabla `ESTRUCTURA.TIPOS_ENTIDADES` define qué tipos pueden ser titulares via flag `puede_ser_solicitante`

3. **Gestión de desactivación de entidades (sin CASCADE)**
   - **Regla de negocio:** Las entidades nunca se borran físicamente, solo se desactivan mediante campo `activo`
   - **Comportamiento al desactivar titular:**
     - **Expediente en tramitación:** Reglas de negocio impiden desactivar entidad si tiene expedientes activos con titular_id apuntando a ella
     - **Expediente en construcción:** Se permite pasar titular_id a NULL si el expediente aún no ha iniciado tramitación formal
   - **Sin ON DELETE:** No hay constraint CASCADE/SET NULL porque no hay borrados físicos
   - **Validación:** En capa de aplicación según estado del expediente

4. **Campo redundante con histórico**
   - **Motivo:** Optimización de rendimiento. El 99% de consultas acceden al titular actual, no al histórico
   - **Coste:** Sincronización titular_id ↔ HISTORICO_TITULARES_EXPEDIENTE gestionada mediante triggers o lógica aplicación
   - **Alternativa descartada:** Consultar siempre `MAX(fecha_desde) WHERE fecha_hasta IS NULL` en histórico (costoso en queries recurrentes)

**Relación con tabla HISTORICO_TITULARES_EXPEDIENTE:**

El campo `titular_id` representa una **caché desnormalizada** del titular actual. La tabla `HISTORICO_TITULARES_EXPEDIENTE` (Issue #64) almacena:
- Todos los titulares históricos con vigencia temporal
- Motivo del cambio (INICIAL, VENTA, HERENCIA, FUSION, etc.)
- Solicitud que originó el cambio de titularidad

**Regla de consistencia:**  
`expedientes.titular_id` DEBE coincidir con el registro de `historico_titulares_expediente` donde `expediente_id = expedientes.id AND fecha_hasta IS NULL`

#### Notas de Versión

- **v3.0:** Añadido campo `PROYECTO_ID` (relación 1:1 con proyecto). Un expediente tiene exactamente un proyecto técnico, que evoluciona mediante documentos versionados.
- **v3.1 (Issue #64):** Añadido campo `TITULAR_ID` para gestión de titularidad. Campo nullable que almacena el titular actual del expediente. Relacionado con nueva tabla `HISTORICO_TITULARES_EXPEDIENTE` para trazabilidad completa de cambios.

---

---

### FASES

Contenedor temporal de trámites con objetivo procedimental concreto.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único de la fase | NO | PK, autoincremental |
| **SOLICITUD_ID** | INTEGER | Solicitud a la que pertenece la fase | NO | FK → SOLICITUDES(ID). Cada fase se ejecuta dentro de una solicitud específica |
| **TIPO_FASE_ID** | INTEGER | Tipo de fase según catálogo normativo | NO | FK → TIPOS_FASES(ID). Define la fase procedimental: ADMISIBILIDAD, CONSULTAS, INFORMACION_PUBLICA, RESOLUCION, etc. |
| **FECHA_INICIO** | DATE | Fecha de inicio administrativo de la fase | SÍ | NULL = fase planificada pero no iniciada. NOT NULL = fase en curso o finalizada |
| **FECHA_FIN** | DATE | Fecha de finalización de la fase | SÍ | NULL = fase pendiente o en curso. NOT NULL = fase completada. Se deduce como la última fecha de finalización de todos los trámites asociados, pero debe rellenarse manualmente |
| **OBSERVACIONES** | VARCHAR(2000) | Notas o comentarios sobre la fase | SÍ | Campo libre para anotaciones del técnico sobre la ejecución de la fase |
| **RESULTADO_FASE_ID** | INTEGER | Resultado o desenlace de la fase | SÍ | FK → TIPOS_RESULTADOS_FASES(ID). Indica el resultado: FAVORABLE, DESFAVORABLE, CONDICIONADO, etc. Debe rellenarse manualmente al cerrar la fase |
| **DOCUMENTO_RESULTADO_ID** | INTEGER | Documento oficial que formaliza el resultado | SÍ | FK → DOCUMENTOS(ID). Documento clave que define el resultado (ej: informe favorable, resolución de inadmisión). Puede ser NULL si el resultado no genera documento específico |

#### Claves

- **PK:** `ID`
- **FK:**
  - `SOLICITUD_ID` → `SOLICITUDES(ID)` ON DELETE CASCADE
  - `TIPO_FASE_ID` → `TIPOS_FASES(ID)`
  - `RESULTADO_FASE_ID` → `TIPOS_RESULTADOS_FASES(ID)`
  - `DOCUMENTO_RESULTADO_ID` → `DOCUMENTOS(ID)`

#### Índices Recomendados

- `SOLICITUD_ID` (fases de una solicitud)
- `TIPO_FASE_ID` (filtros por tipo de fase)
- `RESULTADO_FASE_ID` (consultas por resultado)
- `(FECHA_INICIO, FECHA_FIN)` (estado temporal y secuencia)

#### Notas de Versión

- **v3.0:** Sin cambios estructurales respecto a v2.0. Mantiene diseño minimalista.

#### Filosofía

La fase es un **contenedor temporal de trámites** con un objetivo procedimental concreto:

- **Campos mínimos:** Solo metadatos administrativos (fechas, tipo, resultado)
- **Semántica en TIPO:** La lógica procedimental vive en `TIPOS_FASES`, no en campos específicos
- **Resultado manual:** El técnico debe evaluar y registrar el resultado tras analizar documentos
- **Fecha fin sugestionable:** Puede calcularse automáticamente como MAX(TRAMITES.FECHA_FIN), pero siempre se registra manualmente para control administrativo

#### Estados Deducibles (no almacenados)

- **PENDIENTE:** `FECHA_INICIO IS NULL`
- **EN_CURSO:** `FECHA_INICIO IS NOT NULL AND FECHA_FIN IS NULL`
- **COMPLETADA:** `FECHA_FIN IS NOT NULL`
- **EXITOSA:** `FECHA_FIN IS NOT NULL AND RESULTADO_FASE_ID indica éxito`

#### Reglas de Negocio

1. **No puede finalizarse** (`FECHA_FIN` NOT NULL) si existen trámites asociados sin finalizar (`TRAMITES.FECHA_FIN IS NULL`)
2. `RESULTADO_FASE_ID obligatorio` al establecer `FECHA_FIN` (validación de interfaz)
3. **Secuencias de fases:** Determinadas por motor de reglas según `TIPO_FASE_ID` y `TIPO_SOLICITUD_ID`

---

---

### MUNICIPIOS_PROYECTO

Relación muchos a muchos entre proyectos y municipios afectados.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del registro | NO | PK, autoincremental |
| **MUNICIPIO_ID** | INTEGER | Municipio afectado por el proyecto | NO | FK → MUNICIPIOS(ID). Municipio por donde discurre la instalación o donde se ubica |
| **PROYECTO_ID** | INTEGER | Proyecto que afecta al municipio | NO | FK → PROYECTOS(ID). Proyecto técnico del expediente |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `(MUNICIPIO_ID, PROYECTO_ID)` - Un municipio no puede vincularse dos veces al mismo proyecto
- **FK:**
  - `MUNICIPIO_ID` → `MUNICIPIOS(ID)`
  - `PROYECTO_ID` → `PROYECTOS(ID)` ON DELETE CASCADE

#### Índices Recomendados

- `PROYECTO_ID` (municipios de un proyecto)
- `MUNICIPIO_ID` (proyectos que afectan a un municipio)

#### Notas de Versión

- **v3.0:** Sin cambios estructurales. Continúa siendo relación N:M entre proyectos y municipios.

#### Filosofía

Tabla intermedia que gestiona la relación **muchos a muchos** entre proyectos y municipios:

- Un proyecto puede afectar múltiples municipios (línea que atraviesa varios términos)
- Un municipio puede tener múltiples proyectos que lo afectan
- Necesaria para determinar publicaciones en tablones, consultas a ayuntamientos y análisis territorial

#### Uso Administrativo

**Derivaciones:**

- Determinar qué ayuntamientos deben ser consultados
- Publicaciones en tablones municipales (fase INFORMACION_PUBLICA)
- Generación de separatas por término municipal
- Evaluación ambiental diferente según afecte a más de un municipio

**Consultas típicas:**

**Municipios de un expediente:**
```
EXPEDIENTES → PROYECTO_ID → MUNICIPIOS_PROYECTO → MUNICIPIOS
```

**Expedientes que afectan a un municipio:**
```
MUNICIPIOS → MUNICIPIOS_PROYECTO → PROYECTOS → EXPEDIENTES
```

---

## Tablas Maestras

---

### PROYECTOS

Proyecto técnico único asociado a cada expediente.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del proyecto | NO | PK, autoincremental |
| **TITULO** | VARCHAR(500) | Título del proyecto técnico | NO | Descripción breve. Default: "⚠️ Falta el título del proyecto" |
| **DESCRIPCION** | VARCHAR(10000) | Descripción técnica del proyecto | NO | Texto libre extenso. Default: "⚠️ Falta la descripción del proyecto" |
| **FECHA** | DATE | Fecha de firma o visado del proyecto | NO | Fecha técnica del documento de proyecto (NO es fecha de presentación administrativa). Ayuda a identificar y ordenar versiones cronológicamente |
| **FINALIDAD** | VARCHAR(500) | Finalidad de la instalación | NO | Uso previsto. Default: "⚠️ Falta la finalidad del proyecto" |
| **EMPLAZAMIENTO** | VARCHAR(200) | Ubicación geográfica de la instalación | NO | Descripción textual. Default: "⚠️ Falta el emplazamiento" |
| **IA_ID** | INTEGER | Instrumento ambiental aplicable | SÍ | FK → TIPOS_IA(ID). Define figura ambiental (AAU, AAUS, CA, No sujeto) |

#### Claves

- **PK:** `ID`
- **FK:**
  - `IA_ID` → `TIPOS_IA(ID)`

#### Notas de Versión

- **v3.0:** **ELIMINADO** `EXPEDIENTE_ID`. Relación inversa (expediente apunta a proyecto).
- **v3.0:** **ELIMINADO** `TIPO_PROYECTO_ID`. Tipos de versión viven en `DOCUMENTOS_PROYECTO.TIPO`.
- **v3.0:** **ACLARADO** `FECHA`: Es fecha técnica del proyecto (firma/visado), NO fecha administrativa de presentación.

#### Filosofía

El proyecto es una **entidad técnica pura y única**. No tiene múltiples versiones en esta tabla. Las versiones documentales (proyecto inicial, modificados, refundidos) se gestionan mediante documentos vinculados en `DOCUMENTOS_PROYECTO`.

---

---

### ROLES

Tabla maestra que define los roles del sistema (RBAC - Role-Based Access Control).

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del rol | NO | PK, autoincremental |
| **CODIGO** | VARCHAR(50) | Código único identificativo del rol | NO | UNIQUE. Inmutable. Usado en lógica de negocio |
| **NOMBRE** | VARCHAR(100) | Nombre descriptivo del rol | NO | Para mostrar en interfaz |
| **DESCRIPCION** | VARCHAR(500) | Descripción detallada de permisos | SÍ | Explicación de qué puede hacer este rol |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `CODIGO`

#### Índices Recomendados

- `CODIGO` (consultas frecuentes para validación de permisos)

#### Relaciones

- **usuarios_roles**: USUARIOS_ROLES.rol_id → asignaciones de usuarios (N:M)

#### Notas de Versión

- **v3.1**: Tabla nueva. Define roles para sistema RBAC (antes gestionado solo en Flask).

#### Filosofía

Los roles definen **niveles de acceso** en el sistema:

- **CODIGO**: Referencia estable para código Python (no cambiar en producción)
- **NOMBRE**: Etiqueta legible para interfaz de usuario
- **N:M con usuarios**: Un usuario puede tener múltiples roles
- **Permisos derivados**: El rol determina qué schemas/tablas/operaciones están permitidas

#### Roles Definidos

| Código | Nombre | Permisos principales |
|:---|:---|:---|
| **ADMIN** | Administrador | Acceso total: schemas (public, estructura, legacy), gestión de usuarios, configuración |
| **SUPERVISOR** | Supervisor | Gestión de usuarios, asignación de expedientes, visión global, schemas (public, estructura) |
| **TRAMITADOR** | Tramitador | Tramitación completa de expedientes asignados, schema public (lectura/escritura) |
| **ADMINISTRATIVO** | Administrativo | Solo lectura y consulta, schema public (solo SELECT) |

#### Permisos por Rol

**ADMIN:**
- GRANT ALL en schemas: `public`, `estructura`, `legacy`
- Gestión de usuarios y roles
- Configuración del sistema
- Acceso a auditoría completa

**SUPERVISOR:**
- GRANT SELECT, INSERT, UPDATE en schemas: `public`, `estructura`
- Asignación de expedientes a tramitadores
- Creación/modificación de usuarios (excepto ADMIN)
- Visión global de todos los expedientes

**TRAMITADOR:**
- GRANT SELECT, INSERT, UPDATE, DELETE en schema: `public`
- Solo expedientes asignados (filtro por `responsable_id`)
- Gestión completa de solicitudes, fases, trámites, documentos
- No puede modificar tipos/maestras

**ADMINISTRATIVO:**
- GRANT SELECT en schema: `public`
- Solo lectura: expedientes, proyectos, solicitudes, documentos
- No puede crear ni modificar datos

#### Reglas de Negocio

1. **CODIGO inmutable**: No cambiar en producción (ruptura de lógica)
2. **Al menos TRAMITADOR**: Todo usuario activo debe tener al menos un rol
3. **Roles múltiples**: Un usuario puede ser TRAMITADOR + SUPERVISOR
4. **Sin auto-asignación ADMIN**: Solo otro ADMIN puede asignar rol ADMIN
5. **Roles preestablecidos**: Tabla inmutable (INSERT inicial, no modificar)

#### Datos Maestros

```sql
INSERT INTO roles (codigo, nombre, descripcion) VALUES
('ADMIN', 'Administrador', 'Acceso total al sistema: gestión de usuarios, configuración, schemas completos'),
('SUPERVISOR', 'Supervisor', 'Gestión de usuarios, asignación de expedientes, visión global'),
('TRAMITADOR', 'Tramitador', 'Tramitación completa de expedientes asignados'),
('ADMINISTRATIVO', 'Administrativo', 'Solo lectura y consulta de expedientes');
```

---

---

### SOLICITUDES

Actos administrativos solicitados dentro de un expediente.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único de la solicitud | NO | PK, autoincremental |
| **EXPEDIENTE_ID** | INTEGER | Expediente al que pertenece la solicitud | NO | FK → EXPEDIENTES(ID). Relación directa solicitud-expediente |
| **SOLICITUD_AFECTADA_ID** | INTEGER | Solicitud sobre la que actúa (desistimiento/renuncia) | SÍ | FK → SOLICITUDES(ID). Solo para tipos DESISTIMIENTO o RENUNCIA. Apunta a la solicitud que se desiste/renuncia |
| **FECHA_SOLICITUD** | DATE | Fecha de presentación de la solicitud | NO | Fecha administrativa oficial (registro de entrada) |
| **ESTADO** | VARCHAR(20) | Estado actual de la solicitud | NO | Valores: `EN_TRAMITE`, `RESUELTA`, `DESISTIDA`, `ARCHIVADA`. Default: `EN_TRAMITE` |
| **OBSERVACIONES** | VARCHAR(2000) | Notas o comentarios adicionales | SÍ | Campo libre para anotaciones del técnico |

#### Claves

- **PK:** `ID`
- **FK:**
  - `EXPEDIENTE_ID` → `EXPEDIENTES(ID)`
  - `SOLICITUD_AFECTADA_ID` → `SOLICITUDES(ID)` (autorreferencia)

#### Índices Recomendados

- `EXPEDIENTE_ID` (consultas frecuentes por expediente)
- `FECHA_SOLICITUD` (ordenación cronológica)
- `ESTADO` (filtros por estado)

#### Relaciones

- **expediente**: EXPEDIENTES.id (FK, expediente contenedor)
- **solicitud_afectada**: SOLICITUDES.id (FK self-referencia, para DESISTIMIENTO/RENUNCIA)
- **solicitudes_tipos**: SOLICITUDES_TIPOS.solicitud_id → tipos de la solicitud (N:M)
- **fases**: FASES.solicitud_id → fases de tramitación (1:N)

#### Notas de Versión

- **v3.0**: 
  - AÑADIDO campo `EXPEDIENTE_ID`. Relación directa con expediente, elimina dependencia transitiva vía proyecto.
  - ELIMINADO campo `PROYECTO_ID`. La solicitud ya no apunta a un proyecto específico. El proyecto se deduce del expediente (EXPEDIENTE.PROYECTO_ID). La solicitud actúa sobre el estado del proyecto en el momento de su presentación (determinado por documentos vigentes en DOCUMENTOS_PROYECTO con FECHA_ADMINISTRATIVA ≤ SOLICITUD.FECHA).
  - AÑADIDO campo `SOLICITUD_AFECTADA_ID` para soportar desistimientos y renuncias.

- **v3.1**:
  - **ELIMINADO campo `TIPO_SOLICITUD_ID`**. Movido a tabla puente SOLICITUDES_TIPOS para permitir múltiples tipos por solicitud.
  - **AÑADIDO campo `ESTADO`**. Estados: EN_TRAMITE, RESUELTA, DESISTIDA, ARCHIVADA.
  - **RENOMBRADO `FECHA` → `FECHA_SOLICITUD`**. Mayor claridad semántica.
  - **ELIMINADO campo `FECHA_FIN`**. Redundante con estado y fases.

#### Filosofía

La solicitud es un **acto administrativo concreto** dentro de un expediente. No necesita apuntar directamente al proyecto porque:
- Solo hay **UN proyecto por expediente**
- La solicitud actúa sobre el **estado temporal del proyecto** en su momento de presentación
- El estado se reconstruye consultando documentos del proyecto vigentes en esa fecha

#### Relación N:M con Tipos de Solicitud

Una solicitud puede tener **múltiples tipos simultáneamente** (ej: AAP+AAC+DUP en una misma presentación):
- Gestionado mediante tabla puente **SOLICITUDES_TIPOS**
- Motor de reglas aplica lógica sobre tipos individuales, no combinaciones
- Cada tipo determina fases procedimentales específicas
- Permite modelar solicitudes complejas sin duplicación

#### Estados de Solicitud

| Estado | Significado | Transiciones permitidas |
|:---|:---|:---|
| **EN_TRAMITE** | Solicitud activa en procedimiento | → RESUELTA, DESISTIDA, ARCHIVADA |
| **RESUELTA** | Resolución firme emitida | (Estado final) |
| **DESISTIDA** | Peticionario desiste | (Estado final) |
| **ARCHIVADA** | Procedimiento finalizado sin resolución (caducidad, etc.) | (Estado final) |

#### Reglas de Negocio

1. **Tipos múltiples**: Gestionados en tabla puente SOLICITUDES_TIPOS (N:M)
2. **DESISTIMIENTO/RENUNCIA**: Requiere `SOLICITUD_AFECTADA_ID NOT NULL`
3. **MOD**: Debe existir AAC previa concedida en el expediente (validar en interfaz)
4. **Estado RESUELTA**: Debe existir al menos una fase completada con resultado favorable
5. **Estado DESISTIDA**: Debe tener `SOLICITUD_AFECTADA_ID NOT NULL` si es desistimiento de otra solicitud
6. **Validación de fecha**: `FECHA_SOLICITUD` debe ser ≥ fecha de creación del expediente

---

---

### SOLICITUDES_TIPOS

Tabla puente para la relación N:M entre solicitudes y tipos de solicitudes.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del registro | NO | PK, autoincremental |
| **SOLICITUD_ID** | INTEGER | Solicitud que tiene el tipo | NO | FK → SOLICITUDES(ID). Parte de UNIQUE(solicitud_id, tipo_solicitud_id) |
| **TIPO_SOLICITUD_ID** | INTEGER | Tipo de solicitud asignado | NO | FK → TIPOS_SOLICITUDES(ID). Parte de UNIQUE(solicitud_id, tipo_solicitud_id) |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `(SOLICITUD_ID, TIPO_SOLICITUD_ID)` - Una solicitud no puede tener el mismo tipo duplicado
- **FK:**
  - `SOLICITUD_ID` → `SOLICITUDES(ID)` ON DELETE CASCADE
  - `TIPO_SOLICITUD_ID` → `TIPOS_SOLICITUDES(ID)` ON DELETE CASCADE

#### Índices Recomendados

- `SOLICITUD_ID` (consulta: ¿qué tipos tiene esta solicitud?)
- `TIPO_SOLICITUD_ID` (consulta inversa: ¿qué solicitudes son de este tipo?)

#### Relaciones

- **solicitud**: SOLICITUDES.id (FK CASCADE, solicitud contenedora)
- **tipo_solicitud**: TIPOS_SOLICITUDES.id (FK CASCADE, tipo asignado)

#### Notas de Versión

- **v3.1**: Tabla nueva. Reemplaza el campo `TIPO_SOLICITUD_ID` de SOLICITUDES para permitir múltiples tipos por solicitud.

#### Filosofía

Esta tabla puente permite modelar **solicitudes complejas** con múltiples actos administrativos simultáneos:

- **Solicitud simple**: AAP (un solo registro en esta tabla)
- **Solicitud múltiple**: AAP+AAC+DUP (tres registros en esta tabla, misma `solicitud_id`)
- **Motor de reglas**: Aplica lógica sobre tipos individuales, no combinaciones
- **Sin duplicación**: El constraint UNIQUE evita asignar el mismo tipo dos veces

#### Casos de Uso

**Solicitud con un solo tipo:**
- Solicitud ID=1 (AAP)
- 1 registro: (solicitud_id=1, tipo_solicitud_id=1)

**Solicitud con múltiples tipos:**
- Solicitud ID=2 (AAP + AAC + DUP)
- 3 registros:
  - (solicitud_id=2, tipo_solicitud_id=1) -- AAP
  - (solicitud_id=2, tipo_solicitud_id=2) -- AAC
  - (solicitud_id=2, tipo_solicitud_id=3) -- DUP

**Consulta: ¿Qué tipos tiene la solicitud 2?**
```sql
SELECT ts.siglas, ts.descripcion
FROM solicitudes_tipos st
JOIN tipos_solicitudes ts ON st.tipo_solicitud_id = ts.id
WHERE st.solicitud_id = 2;
```

**Consulta inversa: ¿Qué solicitudes son AAP?**
```sql
SELECT s.id, s.fecha_solicitud, s.estado
FROM solicitudes s
JOIN solicitudes_tipos st ON s.id = st.solicitud_id
JOIN tipos_solicitudes ts ON st.tipo_solicitud_id = ts.id
WHERE ts.siglas = 'AAP';
```

#### Reglas de Negocio

1. **CASCADE en DELETE**: Si se borra una solicitud, se borran automáticamente sus tipos asociados
2. **No duplicados**: El constraint UNIQUE evita asignar el mismo tipo dos veces a una solicitud
3. **Al menos un tipo**: Toda solicitud debe tener al menos un tipo (validar en interfaz)
4. **Tipos compatibles**: El motor de reglas valida que las combinaciones sean válidas (ej: MOD requiere AAC previa)

---

---

### TAREAS

Unidad de trabajo registrable con entrada/salida documental.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único de la tarea | NO | PK, autoincremental |
| **TRAMITE_ID** | INTEGER | Trámite al que pertenece la tarea | NO | FK → TRAMITES(ID). Cada tarea se ejecuta dentro de un trámite específico |
| **TIPO_TAREA_ID** | INTEGER | Tipo de tarea según catálogo | NO | FK → TIPOS_TAREAS(ID). Define el tipo atómico: INCORPORAR, ANALISIS, REDACTAR, FIRMAR, NOTIFICAR, PUBLICAR, ESPERARPLAZO |
| **FECHA_INICIO** | DATE | Fecha de inicio administrativo de la tarea | SÍ | NULL = tarea planificada pero no iniciada. NOT NULL = tarea en curso o finalizada |
| **FECHA_FIN** | DATE | Fecha de finalización de la tarea | SÍ | NULL = tarea pendiente o en curso. NOT NULL = tarea completada. Determina el cierre administrativo |
| **NOTAS** | VARCHAR(2000) | Observaciones o información adicional | SÍ | Campo libre. Puede contener datos específicos según tipo: plazos (ESPERARPLAZO), referencia publicación (PUBLICAR), remitente (INCORPORAR), etc. |
| **DOCUMENTO_USADO_ID** | INTEGER | Documento de entrada que consume la tarea | SÍ | FK → DOCUMENTOS(ID). Documento que la tarea analiza/transforma/notifica. NULL para tareas sin entrada (INCORPORAR, ESPERARPLAZO) |
| **DOCUMENTO_PRODUCIDO_ID** | INTEGER | Documento de salida que genera la tarea | SÍ | FK → DOCUMENTOS(ID). Documento que la tarea crea/incorpora al sistema. NULL para tareas sin salida (ESPERARPLAZO) o tareas no finalizadas |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `DOCUMENTO_PRODUCIDO_ID` (cuando NOT NULL) - Un documento solo puede ser producido por una tarea
- **FK:**
  - `TRAMITE_ID` → `TRAMITES(ID)` ON DELETE CASCADE
  - `TIPO_TAREA_ID` → `TIPOS_TAREAS(ID)`
  - `DOCUMENTO_USADO_ID` → `DOCUMENTOS(ID)`
  - `DOCUMENTO_PRODUCIDO_ID` → `DOCUMENTOS(ID)`

#### Índices Recomendados

- `TRAMITE_ID` (tareas de un trámite)
- `TIPO_TAREA_ID` (filtros por tipo)
- `DOCUMENTO_USADO_ID` (consulta inversa: qué tareas usaron este documento)
- `DOCUMENTO_PRODUCIDO_ID` (único, consulta inversa: qué tarea produjo este documento)
- `(FECHA_INICIO, FECHA_FIN)` (estado temporal de tareas)

#### Notas de Versión

- **v3.0:** **AÑADIDO** campo `DOCUMENTO_USADO_ID`. Entrada de la tarea, antes vivía en `DOCUMENTOS.TAREA_DESTINO_ID`.
- **v3.0:** **AÑADIDO** campo `DOCUMENTO_PRODUCIDO_ID`. Salida de la tarea, antes vivía en `DOCUMENTOS.TAREA_ORIGEN_ID`.

#### Filosofía

La tarea es una **unidad de trabajo registrable** con entrada/salida documental clara:

- **Relación unidireccional:** TAREA → DOCUMENTO (no al revés)
- **Documento agnóstico:** El documento no sabe de tareas, las tareas apuntan a documentos
- **Un documento, un productor:** Un documento solo puede ser producido por una tarea (índice único)
- **Un documento, múltiples consumidores:** Varias tareas pueden usar el mismo documento de entrada

#### Semántica según Tipo de Tarea

| Tipo | DOCUMENTO_USADO_ID | DOCUMENTO_PRODUCIDO_ID |
|:---|:---|:---|
| **INCORPORAR** | NULL (documento externo aún no en sistema) | Obligatorio (documento incorporado) |
| **ANALISIS** | Obligatorio (documento a analizar) | Obligatorio (informe de análisis) |
| **REDACTAR** | Opcional (informe previo si existe) | Obligatorio (borrador) |
| **FIRMAR** | Obligatorio (borrador) | Obligatorio (documento firmado) |
| **NOTIFICAR** | Obligatorio (documento firmado) | Obligatorio (justificante notificación) |
| **PUBLICAR** | Obligatorio (documento firmado) | Obligatorio (justificante publicación) |
| **ESPERARPLAZO** | NULL (no maneja documentos) | NULL (no maneja documentos) |

#### Validaciones de Negocio

1. **Antes de** `FECHA_FIN NOT NULL`: Verificar que tareas con salida obligatoria tienen `DOCUMENTO_PRODUCIDO_ID` NOT NULL
2. `DOCUMENTO_USADO_ID`: Debe pertenecer al mismo expediente que la tarea (vía TRAMITE→FASE→SOLICITUD→EXPEDIENTE)
3. `DOCUMENTO_PRODUCIDO_ID`: Único constraint garantiza que no se duplica el productor

---

---

### TRAMITES

Contenedor organizativo de tareas dentro de una fase.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del trámite | NO | PK, autoincremental |
| **FASE_ID** | INTEGER | Fase a la que pertenece el trámite | NO | FK → FASES(ID). Cada trámite se ejecuta dentro de una fase específica |
| **TIPO_TRAMITE_ID** | INTEGER | Tipo de trámite según catálogo | NO | FK → TIPOS_TRAMITES(ID). Define el trámite procedimental: SOLICITUD_INFORME, ANUNCIO_BOP, RECEPCION_ALEGACION, etc. |
| **FECHA_INICIO** | DATE | Fecha de inicio administrativo del trámite | SÍ | NULL = trámite planificado pero no iniciado. NOT NULL = trámite en curso o finalizado |
| **FECHA_FIN** | DATE | Fecha de finalización del trámite | SÍ | NULL = trámite pendiente o en curso. NOT NULL = trámite completado. Se deduce como la última fecha de finalización de todas las tareas asociadas, pero debe rellenarse manualmente |
| **OBSERVACIONES** | VARCHAR(2000) | Notas o comentarios sobre el trámite | SÍ | Campo libre para anotaciones del técnico sobre la ejecución del trámite |

#### Claves

- **PK:** `ID`
- **FK:**
  - `FASE_ID` → `FASES(ID)` ON DELETE CASCADE
  - `TIPO_TRAMITE_ID` → `TIPOS_TRAMITES(ID)`

#### Índices Recomendados

- `FASE_ID` (trámites de una fase)
- `TIPO_TRAMITE_ID` (filtros por tipo de trámite)
- `(FECHA_INICIO, FECHA_FIN)` (estado temporal y secuencia)

#### Notas de Versión

- **v3.0:** Sin cambios estructurales respecto a v2.0. Mantiene diseño minimalista.

#### Filosofía

El trámite es un **contenedor organizativo de tareas** dentro de una fase:

- **Estructura mínima:** Solo fechas, tipo y observaciones
- **Semántica en TIPO:** Los patrones de tareas (secuencias) viven en `TIPOS_TRAMITES` y se combinan según reglas de negocio
- **Sin campos específicos:** No hay remitentes, destinatarios ni documentos en esta tabla. Esos datos viven en las tareas y documentos
- **Fecha fin sugestionable:** Puede calcularse automáticamente como MAX(TAREAS.FECHA_FIN), pero se registra manualmente

#### Estados Deducibles (no almacenados)

- **PENDIENTE:** `FECHA_INICIO IS NULL`
- **EN_CURSO:** `FECHA_INICIO IS NOT NULL AND FECHA_FIN IS NULL`
- **COMPLETADO:** `FECHA_FIN IS NOT NULL`

#### Patrones de Tareas según Tipo

Cada `TIPO_TRAMITE_ID` determina qué secuencia de tareas se esperan (definido en lógica de negocio):

**Ejemplos:**

- **SOLICITUD_INFORME:** REDACTAR → FIRMAR → NOTIFICAR → ESPERARPLAZO
- **RECEPCION_INFORME:** INCORPORAR → ANALISIS
- **ANUNCIO_BOP:** REDACTAR → FIRMAR → NOTIFICAR → ESPERARPLAZO → INCORPORAR → ESPERARPLAZO (doble espera)
- **COMPROBACION_ADMISIBILIDAD:** ANALISIS

Los patrones se combinan y adaptan según reglas de negocio, no están hardcoded.

#### Reglas de Negocio

1. **No puede finalizarse** (`FECHA_FIN` NOT NULL) si existen tareas asociadas sin finalizar (`TAREAS.FECHA_FIN IS NULL`)
2. **Secuencias de trámites:** Determinadas por motor de reglas según `TIPO_TRAMITE_ID` y `TIPO_FASE_ID`
3. **Los trámites pueden ejecutarse en paralelo** dentro de una misma fase (ej: múltiples consultas a organismos simultáneas)

---

---

### USUARIOS

Usuarios del sistema con datos personales básicos.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del usuario | NO | PK, autoincremental |
| **SIGLAS** | VARCHAR(50) | Siglas o código identificativo del usuario | NO | Identificador corto para uso interno. Default: "NULO" |
| **NOMBRE** | VARCHAR(100) | Nombre del usuario | NO | Nombre de pila. Default: "Usuario" |
| **APELLIDO1** | VARCHAR(50) | Primer apellido | NO | Default: "no asignado" |
| **APELLIDO2** | VARCHAR(50) | Segundo apellido | SÍ | Puede ser NULL si no aplica |
| **ACTIVO** | BOOLEAN | Indica si el usuario está activo en el sistema | SÍ | TRUE = usuario habilitado. FALSE = usuario desactivado (no eliminado). Default: TRUE |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `SIGLAS` (recomendado, aunque no está explícito en schema actual)

#### Índices Recomendados

- `SIGLAS` (búsqueda rápida por código)
- `ACTIVO` (filtrar usuarios activos)

#### Notas de Versión

- **v3.0:** Sin cambios estructurales respecto a versiones anteriores.

#### Filosofía

Tabla maestra de usuarios del sistema:

- Usuarios técnicos (tramitadores, supervisores)
- Identificación personal para responsabilidad y auditoría
- **No contiene credenciales** (gestionadas por motor de BD PostgreSQL)
- `ACTIVO=FALSE` permite deshabilitar usuarios sin perder historial (expedientes asignados, tareas realizadas)

#### Roles de Sistema

Los roles se gestionan a nivel de base de datos PostgreSQL. Consultar documento `Roles.md` para más información.

#### Uso Administrativo

- `RESPONSABLE_ID` en `EXPEDIENTES`: Usuario asignado como responsable del expediente completo
- Auditoría: Posibilidad futura de campos `CREADO_POR`, `MODIFICADO_POR` en tablas operacionales
- Interfaz: Filtros por tramitador, asignaciones de trabajo, estadísticas por usuario

#### Valores por Defecto

Los defaults permiten crear registros temporales de usuarios mientras se completa información, pero en producción todos los campos deberían tener valores reales.

---

---

### USUARIOS_ROLES

Tabla puente para la relación N:M entre usuarios y roles (RBAC).

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del registro | NO | PK, autoincremental |
| **USUARIO_ID** | INTEGER | Usuario al que se asigna el rol | NO | FK → USUARIOS(ID). Parte de UNIQUE(usuario_id, rol_id) |
| **ROL_ID** | INTEGER | Rol asignado al usuario | NO | FK → ROLES(ID). Parte de UNIQUE(usuario_id, rol_id) |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `(USUARIO_ID, ROL_ID)` - Un usuario no puede tener el mismo rol duplicado
- **FK:**
  - `USUARIO_ID` → `USUARIOS(ID)` ON DELETE CASCADE
  - `ROL_ID` → `ROLES(ID)` ON DELETE CASCADE

#### Índices Recomendados

- `USUARIO_ID` (consulta: ¿qué roles tiene este usuario?)
- `ROL_ID` (consulta inversa: ¿qué usuarios tienen este rol?)

#### Relaciones

- **usuario**: USUARIOS.id (FK CASCADE, usuario contenedor)
- **rol**: ROLES.id (FK CASCADE, rol asignado)

#### Notas de Versión

- **v3.1**: Tabla nueva. Reemplaza el campo `rol` en USUARIOS (que antes era 1:1) para permitir roles múltiples.

#### Filosofía

Esta tabla puente permite **roles múltiples por usuario**:

- **Un rol**: Usuario ID=1 con rol TRAMITADOR (1 registro)
- **Roles múltiples**: Usuario ID=2 con TRAMITADOR + SUPERVISOR (2 registros)
- **Flexibilidad**: Permite promoción sin perder permisos anteriores
- **Sin duplicados**: El constraint UNIQUE evita asignar el mismo rol dos veces

#### Casos de Uso

**Usuario con un solo rol (Tramitador):**
- Usuario ID=1
- 1 registro: (usuario_id=1, rol_id=3) -- TRAMITADOR

**Usuario con roles múltiples (Tramitador + Supervisor):**
- Usuario ID=2
- 2 registros:
  - (usuario_id=2, rol_id=3) -- TRAMITADOR
  - (usuario_id=2, rol_id=2) -- SUPERVISOR

**Administrador puro:**
- Usuario ID=3
- 1 registro: (usuario_id=3, rol_id=1) -- ADMIN

**Consulta: ¿Qué roles tiene el usuario 2?**
```sql
SELECT r.codigo, r.nombre
FROM usuarios_roles ur
JOIN roles r ON ur.rol_id = r.id
WHERE ur.usuario_id = 2;
```

**Consulta inversa: ¿Qué usuarios son SUPERVISOR?**
```sql
SELECT u.username, u.nombre, u.apellidos
FROM usuarios u
JOIN usuarios_roles ur ON u.id = ur.usuario_id
JOIN roles r ON ur.rol_id = r.id
WHERE r.codigo = 'SUPERVISOR';
```

**Verificar si usuario tiene permiso ADMIN:**
```sql
SELECT COUNT(*) > 0 AS es_admin
FROM usuarios_roles ur
JOIN roles r ON ur.rol_id = r.id
WHERE ur.usuario_id = ? AND r.codigo = 'ADMIN';
```

#### Reglas de Negocio

1. **CASCADE en DELETE**: Si se borra un usuario, se borran automáticamente sus roles
2. **No duplicados**: El constraint UNIQUE evita asignar el mismo rol dos veces
3. **Al menos un rol**: Todo usuario activo debe tener al menos un rol (validar en interfaz)
4. **Sin auto-asignación ADMIN**: Solo un ADMIN puede asignar rol ADMIN a otro usuario
5. **Roles acumulativos**: Los permisos se suman (TRAMITADOR + SUPERVISOR = permisos de ambos)

#### Combinaciones Típicas

| Combinación | Uso típico |
|:---|:---|
| **TRAMITADOR** | Técnico que solo tramita sus expedientes asignados |
| **TRAMITADOR + SUPERVISOR** | Jefe de sección: tramita + coordina equipo |
| **SUPERVISOR** | Coordinador que solo supervisa, no tramita |
| **ADMIN** | Administrador del sistema (no necesita otros roles) |
| **ADMINISTRATIVO** | Personal auxiliar de consulta |

---

---
