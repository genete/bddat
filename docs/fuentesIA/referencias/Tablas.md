# Definiciones de Tablas Principales v3.1

**Sistema de Tramitación de Expedientes de Alta Tensión (BDDAT)**  
**Formato agnóstico a la base de datos**  
**Fecha:** 11/02/2026  
**Generado automáticamente:** 11/02/2026 19:31 por merge_tables.py

---

## Índice

- [Filosofía del Diseño](#filosofía-del-diseño)
- [Tablas de Estructura](#tablas-de-estructura)
  - [MUNICIPIOS](#municipios)
  - [TIPOS_EXPEDIENTES](#tiposexpedientes)
  - [TIPOS_FASES](#tiposfases)
  - [TIPOS_IA](#tiposia)
  - [TIPOS_RESULTADOS_FASES](#tiposresultadosfases)
  - [TIPOS_SOLICITUDES](#tipossolicitudes)
  - [TIPOS_TAREAS](#tipostareas)
  - [TIPOS_TRAMITES](#tipostramites)
- [Tablas Operacionales](#tablas-operacionales)
  - [AUTORIZADOS_TITULAR](#autorizadostitular)
  - [DIRECCIONES_NOTIFICACION](#direccionesnotificacion)
  - [DOCUMENTOS](#documentos)
  - [DOCUMENTOS_PROYECTO](#documentosproyecto)
  - [ENTIDADES](#entidades)
  - [EXPEDIENTES](#expedientes)
  - [FASES](#fases)
  - [HISTORICO_TITULARES_EXPEDIENTE](#historicotitularesexpediente)
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

# O_014_DIRECCIONES_NOTIFICACION

## Propósito

Tabla que almacena direcciones de notificación específicas por rol para cada entidad. Permite que una misma entidad tenga diferentes direcciones según actúe como titular, consultado o publicador.

## Descripción

Gestiona direcciones de notificación diferenciadas por rol operativo. Una entidad puede tener múltiples direcciones activas simultáneamente, cada una asociada a roles específicos mediante bit flags.

**Casos de uso**:
- Empresa con direcciones diferentes para consultas y titularidad
- Organismo con múltiples sedes según tipo de trámite
- Histórico de direcciones con vigencia temporal

## Campos

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INTEGER | PK, AUTO_INCREMENT | Identificador único |
| `entidad_id` | INTEGER | NOT NULL, FK → entidades(id) ON DELETE CASCADE | Entidad propietaria |
| `descripcion` | TEXT | NULL | Descripción de la dirección (ej: "Sede Social", "Oficina Técnica") |
| `tipo_rol` | SMALLINT | NOT NULL | Bit flags: 1=TITULAR, 2=CONSULTADO, 4=PUBLICADOR |
| `email` | VARCHAR(120) | NULL | Email de notificación |
| `codigo_sir` | VARCHAR(50) | NULL | Código SIR (Sistema de Interconexión de Registros) |
| `codigo_dir3` | VARCHAR(20) | NULL | Código DIR3 (Directorio Común de Unidades Orgánicas) |
| `direccion` | TEXT | NULL | Calle, número, piso, puerta |
| `codigo_postal` | VARCHAR(10) | NULL | Código postal |
| `municipio_id` | INTEGER | NULL, FK → municipios(id) | Municipio (preferente sobre fallback) |
| `direccion_fallback` | TEXT | NULL | Dirección completa en texto libre (extranjero, datos históricos) |
| `activo` | BOOLEAN | NOT NULL, DEFAULT TRUE | Indica si la dirección está activa |
| `fecha_inicio` | DATE | NULL | Fecha de inicio de vigencia |
| `fecha_fin` | DATE | NULL | Fecha de fin de vigencia |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Fecha de creación |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Fecha de última actualización |

## Relaciones

- **entidad** → `ENTIDADES.id` (N:1, CASCADE)
- **municipio** → `MUNICIPIOS.id` (N:1)

## Índices

```sql
CREATE INDEX ix_direcciones_notificacion_entidad_id ON direcciones_notificacion(entidad_id);
CREATE INDEX ix_direcciones_notificacion_activo ON direcciones_notificacion(activo);
CREATE INDEX ix_direcciones_notificacion_tipo_rol ON direcciones_notificacion(tipo_rol);
```

## Constraints

```sql
ALTER TABLE direcciones_notificacion 
ADD CONSTRAINT fk_direcciones_notificacion_entidad 
FOREIGN KEY (entidad_id) REFERENCES entidades(id) ON DELETE CASCADE;

ALTER TABLE direcciones_notificacion 
ADD CONSTRAINT fk_direcciones_notificacion_municipio 
FOREIGN KEY (municipio_id) REFERENCES municipios(id);
```

## Bit Flags (tipo_rol)

| Valor | Constante | Descripción |
|-------|-----------|-------------|
| 1 | TITULAR | Dirección para rol de titular de expedientes |
| 2 | CONSULTADO | Dirección para consultas en trámites |
| 4 | PUBLICADOR | Dirección para publicaciones/notificaciones |
| 3 | TITULAR + CONSULTADO | Combinación (1 OR 2) |
| 5 | TITULAR + PUBLICADOR | Combinación (1 OR 4) |
| 6 | CONSULTADO + PUBLICADOR | Combinación (2 OR 4) |
| 7 | TODOS | Combinación (1 OR 2 OR 4) |

## Métodos Helper (Modelo Python)

```python
# Cálculo de bit flags
tipo_rol = DireccionNotificacion.calcular_tipo_rol(
    es_titular=True,
    es_consultado=False,
    es_publicador=True
)  # → 5 (1 + 4)

# Verificación de roles
direccion.es_titular  # Property booleana
direccion.es_consultado
direccion.es_publicador

# Listado de roles
direccion.roles_lista  # → ['TITULAR', 'PUBLICADOR']

# Dirección formateada
direccion.direccion_formateada()
# → {'linea1': 'C/ Falsa, 123', 'linea2': '28001 Madrid', 'provincia': 'Madrid'}
```

## Reglas de Negocio

1. **Una entidad puede tener múltiples direcciones activas**
   - Filtrar por `activo=TRUE` para obtener direcciones vigentes
   - Filtrar por `fecha_inicio` y `fecha_fin` para vigencia temporal

2. **Bit flags permiten múltiples roles por dirección**
   - Una dirección puede servir para varios roles simultáneamente
   - Query eficiente: `WHERE tipo_rol & 1 > 0` (tiene rol TITULAR)

3. **Prioridad de dirección**
   - Si `municipio_id` tiene valor → usar campos separados
   - Si `municipio_id` es NULL → usar `direccion_fallback`

4. **Soft delete implícito**
   - No borrar registros, marcar `activo=FALSE`
   - Mantener histórico de direcciones

5. **CASCADE on DELETE**
   - Si se borra entidad, se borran sus direcciones
   - Mantener integridad referencial

## Consultas Típicas

```sql
-- Direcciones activas de una entidad
SELECT * FROM direcciones_notificacion
WHERE entidad_id = 123 AND activo = TRUE
ORDER BY fecha_inicio DESC;

-- Direcciones con rol TITULAR
SELECT * FROM direcciones_notificacion
WHERE tipo_rol & 1 > 0 AND activo = TRUE;

-- Direcciones con múltiples roles
SELECT * FROM direcciones_notificacion
WHERE tipo_rol & 3 = 3  -- TITULAR Y CONSULTADO
AND activo = TRUE;

-- Direcciones vigentes en fecha específica
SELECT * FROM direcciones_notificacion
WHERE entidad_id = 123
AND activo = TRUE
AND (fecha_inicio IS NULL OR fecha_inicio <= '2026-02-11')
AND (fecha_fin IS NULL OR fecha_fin >= '2026-02-11');
```

## Ejemplos de Datos

```sql
-- Entidad con direcciones diferenciadas
INSERT INTO direcciones_notificacion 
(entidad_id, descripcion, tipo_rol, email, direccion, codigo_postal, municipio_id, activo)
VALUES
-- Sede para titularidad
(1, 'Sede Social', 1, 'titularidad@empresa.com', 'C/ Principal, 10', '18001', 100, TRUE),
-- Oficina técnica para consultas
(1, 'Oficina Técnica', 2, 'tecnico@empresa.com', 'Polígono Industrial, 5', '18002', 101, TRUE),
-- Dirección general para todos los roles
(2, 'Sede Única', 7, 'info@organismo.es', 'Plaza Mayor, 1', '28001', 200, TRUE);
```

## Migración desde Modelo Anterior

**Antes**: Direcciones en tablas especializadas (entidades_administrados, etc.)

**Ahora**: Todas en `direcciones_notificacion` con roles

**Script de migración** (ejemplo conceptual):
```sql
-- Migrar administrados (rol TITULAR)
INSERT INTO direcciones_notificacion 
(entidad_id, tipo_rol, email, direccion, codigo_postal, activo)
SELECT 
    entidad_id,
    1 AS tipo_rol,  -- TITULAR
    email_notificacion,
    domicilio_notificacion,
    codigo_postal,
    TRUE
FROM entidades_administrados;

-- Migrar organismos (rol CONSULTADO + PUBLICADOR)
INSERT INTO direcciones_notificacion 
(entidad_id, tipo_rol, email, codigo_sir, direccion, municipio_id, activo)
SELECT 
    entidad_id,
    6 AS tipo_rol,  -- CONSULTADO + PUBLICADOR (2 + 4)
    email_sede_electronica,
    codigo_sir,
    direccion,
    municipio_id,
    TRUE
FROM entidades_organismos_publicos;
```

## Notas de Versión

- **v1.0** (Issue #103): Creación inicial con bit flags y soft delete
- Sistema de roles flexible para evolución futura
- Preparado para integración con sede electrónica (SIR, DIR3)

## Referencias

- Issue #103: Refactorización modelo Entidades
- PR #104: Implementación direcciones_notificacion
- Normativa: Esquema Nacional de Interoperabilidad (ENI)

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

Tabla base que centraliza todas las personas físicas, jurídicas y organismos que interactúan con el sistema (titulares, solicitantes, autorizados, organismos públicos, ayuntamientos, diputaciones).

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único de la entidad | NO | PK, autoincremental |
| **TIPO_ENTIDAD** | VARCHAR(50) | Tipo de entidad | NO | Valores: 'PERSONA_FISICA', 'PERSONA_JURIDICA', 'ORGANISMO_PUBLICO', 'AYUNTAMIENTO', 'DIPUTACION' |
| **CIF_NIF** | VARCHAR(20) | CIF/NIF/NIE normalizado | SÍ | UNIQUE. Mayúsculas, sin espacios/guiones. Ej: "12345678A", "B12345678". NULL para algunos organismos históricos |
| **NOMBRE_COMPLETO** | VARCHAR(200) | Razón social, nombre completo o nombre oficial | NO | Indexed. Personas físicas: nombre completo. Jurídicas/organismos: razón social/nombre oficial |
| **EMAIL** | VARCHAR(120) | Email general de contacto | SÍ | NO es el email de notificaciones (va en `direcciones_notificacion`) |
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
  - `MUNICIPIO_ID` → `MUNICIPIOS(ID)`
- **UNIQUE:** `CIF_NIF`

#### Índices Recomendados

- `TIPO_ENTIDAD` (consultas por tipo)
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

-- Tipos de entidad permitidos
CONSTRAINT chk_tipo_entidad
    CHECK (tipo_entidad IN ('PERSONA_FISICA', 'PERSONA_JURIDICA', 'ORGANISMO_PUBLICO', 'AYUNTAMIENTO', 'DIPUTACION'))
```

#### Relaciones

- **municipio**: MUNICIPIOS.id (FK, ubicación geográfica)
- **direcciones_notificacion**: DIRECCIONES_NOTIFICACION.entidad_id (1:N, direcciones por rol)
- **expedientes_como_titular**: EXPEDIENTES.titular_id (1:N inversa)
- **solicitudes_como_solicitante**: SOLICITUDES.solicitante_id (1:N inversa)
- **solicitudes_como_autorizado**: SOLICITUDES.autorizado_id (1:N inversa)

#### Notas de Versión

- **v1.0** (01/02/2026): Creación inicial de la tabla
- **v2.0** (11/02/2026 - Issue #103): Refactorización completa
  - Eliminada arquitectura de tablas inversas
  - Campo `tipo_entidad_id` (FK) reemplazado por `tipo_entidad` (VARCHAR)
  - Eliminadas tablas `tipos_entidades`, `entidades_administrados`, `entidades_organismos_publicos`, `entidades_ayuntamientos`, `entidades_diputaciones`, `entidades_consultados`
  - Creada tabla `direcciones_notificacion` para gestionar direcciones por rol
  - Simplificación: una tabla con todos los campos comunes

#### Filosofía

La tabla `entidades` implementa un **modelo simplificado** que centraliza toda la información común:

- **Campos comunes** en `entidades` (CIF, nombre, contacto, dirección general)
- **Direcciones de notificación por rol** en tabla `direcciones_notificacion` (1:N)
- **Sin metadatos especializados**: los campos específicos de cada tipo (si fueran necesarios) se añadirían como columnas opcionales en esta tabla
- **Una entidad puede tener múltiples direcciones** según el rol que desempeñe (titular, consultado, publicador)

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
- `DIRECCIONES_NOTIFICACION.EMAIL`: específico para notificaciones según rol (titular, consultado, publicador)
- `DIRECCIONES_NOTIFICACION.CODIGO_DIR3`: notificaciones vía SIR para organismos públicos

#### Tipos de Entidad

El campo `TIPO_ENTIDAD` determina:
- La naturaleza jurídica de la entidad
- Qué formulario mostrar en la interfaz
- Qué validaciones aplicar

Valores permitidos:
- `PERSONA_FISICA`: Ciudadanos individuales
- `PERSONA_JURIDICA`: Empresas, sociedades
- `ORGANISMO_PUBLICO`: Organismos de la administración
- `AYUNTAMIENTO`: Administraciones municipales
- `DIPUTACION`: Administraciones provinciales

#### Reglas de Negocio

1. **Normalización CIF/NIF**: Método estático `normalizar_cif_nif()` aplicar antes de guardar
2. **Validación CIF/NIF**: Método estático `validar_cif_nif()` con algoritmo oficial
3. **CIF/NIF opcional**: Algunos organismos históricos pueden tener `CIF_NIF = NULL`
4. **Múltiples direcciones**: Una entidad puede tener varias direcciones en `direcciones_notificacion` según roles
5. **Código postal futuro**: Preparado para tabla `codigos_postales` con sugerencias por municipio
6. **Borrado lógico**: Usar `ACTIVO = FALSE` en lugar de DELETE físico
7. **Integridad referencial**:
   - Cascade en `direcciones_notificacion` (eliminar direcciones con entidad)
   - Restrict en `expedientes`/`solicitudes` (no eliminar si hay referencias activas)

#### Flujo UX de Creación
1. Usuario elige tipo de entidad (persona física, jurídica, organismo, etc.)
2. Sistema carga formulario con:
   - Campos comunes (`entidades`)
   - Opción de añadir direcciones de notificación por rol
3. Al guardar, se crea la entidad y sus direcciones asociadas en transacción

#### Filtrado por Tipo en Tareas

**Fase "Todo Vale":**
```sql
-- Usuario filtra manualmente
SELECT * FROM entidades 
WHERE tipo_entidad = :tipo 
AND activo = TRUE
```

**Fase "Reglas de Negocio":**
```sql
-- Sistema aplica reglas según contexto
-- Ej: notificación tablón ayuntamiento → solo tipo AYUNTAMIENTO
SELECT * FROM entidades 
WHERE tipo_entidad IN (:tipos_permitidos)
AND activo = TRUE
```

#### Direcciones de Notificación

Ver tabla `DIRECCIONES_NOTIFICACION` para:
- Direcciones específicas por rol (titular, consultado, publicador)
- Múltiples direcciones activas por entidad
- Histórico de direcciones con vigencia temporal
- Integración con sistemas externos (SIR, DIR3)

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

### HISTORICO_TITULARES_EXPEDIENTE

Tabla de auditoría inmutable que registra todos los cambios de titularidad de expedientes a lo largo del tiempo. Mantiene trazabilidad completa de la cadena de titularidad desde el origen, permitiendo consultar quién fue titular en cualquier momento histórico.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del registro histórico | NO | PK, autoincremental |
| **EXPEDIENTE_ID** | INTEGER | Expediente cuya titularidad cambia | NO | FK → EXPEDIENTES(ID), ondelete=CASCADE. Indexed |
| **TITULAR_ID** | INTEGER | Titular durante este periodo de vigencia | NO | FK → ENTIDADES(ID). Indexed |
| **FECHA_DESDE** | TIMESTAMP | Timestamp inicio vigencia de este titular | NO | UNIQUE(expediente_id, fecha_desde). Indexed |
| **FECHA_HASTA** | TIMESTAMP | Timestamp fin vigencia | SÍ | NULL = titular actual vigente. Indexed |
| **SOLICITUD_CAMBIO_ID** | INTEGER | Solicitud que motivó el cambio de titularidad | SÍ | FK → SOLICITUDES(ID). NULL para registro INICIAL |
| **MOTIVO** | VARCHAR(50) | Motivo del cambio de titularidad | SÍ | Valores: INICIAL, VENTA, HERENCIA, FUSION, ESCISION, CAMBIO_TITULAR, OTRO |
| **OBSERVACIONES** | TEXT | Observaciones adicionales sobre el cambio | SÍ | Campo libre para detalles |
| **CREATED_AT** | TIMESTAMP | Timestamp de creación del registro (auditoría) | NO | Default: NOW() |

#### Claves

- **PK:** `ID`
- **FK:**
  - `EXPEDIENTE_ID` → `EXPEDIENTES(ID)` (CASCADE)
  - `TITULAR_ID` → `ENTIDADES(ID)`
  - `SOLICITUD_CAMBIO_ID` → `SOLICITUDES(ID)`
- **UNIQUE:** `(EXPEDIENTE_ID, FECHA_DESDE)`

#### Índices Recomendados

- `EXPEDIENTE_ID` (consultas por expediente)
- `TITULAR_ID` (consultas por titular)
- `FECHA_HASTA` (filtrar registros vigentes: WHERE fecha_hasta IS NULL)
- `(EXPEDIENTE_ID, FECHA_DESDE)` (UNIQUE constraint, evita duplicados)

#### Constraints

```sql
-- Vigencia: fecha_hasta debe ser posterior a fecha_desde
CONSTRAINT chk_vigencia_titular 
    CHECK (fecha_hasta IS NULL OR fecha_hasta >= fecha_desde)

-- Unicidad: solo un registro por expediente+timestamp
CONSTRAINT uq_expediente_titular_desde 
    UNIQUE (expediente_id, fecha_desde)
```

#### Relaciones

- **expediente**: EXPEDIENTES.id (FK, expediente afectado)
- **titular**: ENTIDADES.id (FK, titular en este periodo)
- **solicitud_cambio**: SOLICITUDES.id (FK, acto administrativo que motivó el cambio)
- **expediente.historico_titulares**: Relación inversa 1:N desde Expediente
- **titular.historico_como_titular**: Relación inversa 1:N desde Entidad

#### Notas de Versión

- **v3.2** (07/02/2026): Creación inicial de la tabla (Issue #64)
- **v3.3** (07/02/2026): Cambio DATE → DateTime para permitir múltiples cambios/día

#### Filosofía

Esta tabla implementa un **histórico inmutable** con las siguientes características:

- **Auditoría completa**: Cada cambio queda registrado permanentemente
- **Solo INSERT**: No se permite UPDATE ni DELETE (integridad histórica)
- **Titular actual**: Solo un registro puede tener `FECHA_HASTA = NULL` por expediente
- **Snapshot en expedientes**: `EXPEDIENTES.TITULAR_ID` almacena snapshot desnormalizado del titular actual (optimización de rendimiento)
- **Fuente de verdad**: Esta tabla es la fuente autoritativa del histórico completo
- **TIMESTAMP**: Permite múltiples cambios el mismo día (corrección de errores, regularizaciones)

#### Relación con EXPEDIENTES.TITULAR_ID

**Desnormalización intencional para rendimiento:**

```
EXPEDIENTES.TITULAR_ID = snapshot del titular actual
↑
MANTENIDO SINCRONIZADO AUTOMÁTICAMENTE
↓
HISTORICO_TITULARES_EXPEDIENTE (WHERE fecha_hasta IS NULL)
```

**¿Por qué duplicar el dato?**

- Evita JOIN en consultas frecuentes (listar expedientes con titular)
- Optimización: 95% de consultas solo necesitan titular actual
- El histórico completo se consulta raramente (auditoría, informes)

**Sincronización automática:**

1. Al crear expediente con titular → signal crea registro histórico INICIAL
2. Al cambiar titular → método `registrar_cambio()` actualiza ambos lugares
3. Garantía: `expedientes.titular_id` siempre apunta al titular vigente en histórico

#### Motivos de Cambio

| Motivo | Descripción | Solicitud Requerida |
|:---|:---|:---|
| **INICIAL** | Primer titular del expediente | NO (automático) |
| **VENTA** | Compraventa de la instalación | SÍ |
| **HERENCIA** | Transmisión mortis causa | SÍ |
| **FUSION** | Absorción o fusión empresarial | SÍ |
| **ESCISION** | División empresarial | SÍ |
| **CAMBIO_TITULAR** | Cambio genérico (especificar en observaciones) | SÍ |
| **OTRO** | Otros motivos (detallar en observaciones) | SÍ |

#### Uso de TIMESTAMP (no DATE)

**Decisión de diseño: TIMESTAMP en lugar de DATE**

**Casos de uso que justifican TIMESTAMP:**

1. **Corrección inmediata de errores**
   ```
   09:00 - Se asigna titular erróneo por error
   09:15 - Se detecta error y se corrige
   → Dos cambios el mismo día, diferente hora
   ```

2. **Procesos de regularización**
   ```
   Expediente con múltiples titulares históricos sin registrar
   Se regularizan todos el mismo día con horas secuenciales
   ```

3. **Auditoría precisa**
   ```
   Saber exactamente cuándo se realizó cada cambio (hora exacta)
   ```

**Con DATE esto fallaría:**
```sql
-- CONSTRAINT UNIQUE(expediente_id, fecha_desde) fallaría si:
INSERT ... fecha_desde='2026-02-07'  -- OK
INSERT ... fecha_desde='2026-02-07'  -- ERROR: duplicate key
```

**Con TIMESTAMP funciona:**
```sql
INSERT ... fecha_desde='2026-02-07 09:00:00'  -- OK
INSERT ... fecha_desde='2026-02-07 09:15:00'  -- OK (diferente timestamp)
```

#### Reglas de Negocio

1. **Inmutabilidad**: Los registros NO se actualizan ni eliminan (solo INSERT)
2. **Registro inicial automático**: Al crear expediente con titular_id, signal crea registro con motivo INICIAL
3. **Un único titular vigente**: Solo un registro puede tener `fecha_hasta = NULL` por expediente
4. **Validación de fechas**: `fecha_hasta` debe ser posterior o igual a `fecha_desde`
5. **Trazabilidad**: Cambios posteriores al inicial deben tener `solicitud_cambio_id` (recomendado)
6. **Sincronización snapshot**: Al cambiar titular, actualizar `expedientes.titular_id` simultáneamente
7. **Cierre de vigencia**: Al crear nuevo titular vigente, cerrar el anterior con `fecha_hasta`

#### Flujo de Creación de Expediente

**Caso 1: Expediente con titular desde el inicio**

```python
expediente = Expediente(
    numero_at=123,
    proyecto_id=45,
    titular_id=10,  # ← Titular asignado
    tipo_expediente_id=1
)
db.session.add(expediente)
db.session.commit()

# → Signal 'after_insert' ejecuta automáticamente:
# INSERT INTO historico_titulares_expediente (
#     expediente_id=123,
#     titular_id=10,
#     fecha_desde=NOW(),
#     fecha_hasta=NULL,
#     motivo='INICIAL'
# )
```

**Caso 2: Expediente sin titular inicial**

```python
expediente = Expediente(
    numero_at=124,
    proyecto_id=46,
    titular_id=None,  # ← Sin titular
    tipo_expediente_id=1
)
db.session.add(expediente)
db.session.commit()

# → Signal no crea registro histórico (titular_id es NULL)
# El titular se asignará posteriormente mediante solicitud
```

#### Flujo de Cambio de Titular

**Cuando se aprueba solicitud de cambio de titularidad:**

```python
from datetime import datetime
from app.models import HistoricoTitularExpediente

# Usuario aprueba solicitud de cambio de titularidad
solicitud = Solicitud.query.get(120)
solicitud.estado = 'RESUELTA'

# Registrar cambio de titular
HistoricoTitularExpediente.registrar_cambio(
    expediente_id=expediente.id,
    nuevo_titular_id=15,  # Nueva entidad
    fecha_cambio=datetime.now(),
    motivo='VENTA',
    solicitud_cambio_id=solicitud.id,
    observaciones='Venta según escritura pública nº 1234'
)

db.session.commit()

# → Método registrar_cambio() ejecuta:
# 1. UPDATE historico_titulares_expediente 
#    SET fecha_hasta=NOW() 
#    WHERE expediente_id=X AND fecha_hasta IS NULL
#
# 2. INSERT INTO historico_titulares_expediente (
#      expediente_id=X,
#      titular_id=15,
#      fecha_desde=NOW(),
#      fecha_hasta=NULL,
#      solicitud_cambio_id=120,
#      motivo='VENTA'
#    )
#
# 3. UPDATE expedientes 
#    SET titular_id=15 
#    WHERE id=X
```

#### Consultas Habituales

**Obtener titular actual de un expediente:**

```python
# Opción 1: Snapshot (rápido, sin JOIN)
expediente = Expediente.query.get(123)
titular_actual = expediente.titular  # Relación eager loaded

# Opción 2: Desde histórico (con metadatos)
registro = HistoricoTitularExpediente.titular_actual(expediente_id=123)
if registro:
    titular = registro.titular
    desde = registro.fecha_desde
    motivo = registro.motivo
```

**Obtener histórico completo de un expediente:**

```python
historico = HistoricoTitularExpediente.query\
    .filter_by(expediente_id=123)\
    .order_by('fecha_desde')\
    .all()

for registro in historico:
    print(f"{registro.titular.nombre_completo}: "
          f"{registro.fecha_desde} - {registro.fecha_hasta or 'ACTUAL'} "
          f"({registro.motivo})")
```

**Consultar quién era titular en una fecha concreta:**

```sql
SELECT e.nombre_completo, h.fecha_desde, h.fecha_hasta
FROM historico_titulares_expediente h
JOIN entidades e ON e.id = h.titular_id
WHERE h.expediente_id = 123
  AND h.fecha_desde <= '2025-06-15 10:30:00'
  AND (h.fecha_hasta IS NULL OR h.fecha_hasta >= '2025-06-15 10:30:00')
```

**Obtener todos los expedientes de un titular (actual):**

```sql
-- Opción 1: Desde snapshot (rápido)
SELECT * FROM expedientes WHERE titular_id = 10;

-- Opción 2: Desde histórico (verifica vigencia)
SELECT e.* 
FROM expedientes e
JOIN historico_titulares_expediente h ON h.expediente_id = e.id
WHERE h.titular_id = 10 AND h.fecha_hasta IS NULL;
```

**Obtener expedientes donde una entidad FUE titular (histórico):**

```sql
SELECT DISTINCT e.numero_at, e.id
FROM expedientes e
JOIN historico_titulares_expediente h ON h.expediente_id = e.id
WHERE h.titular_id = 10
ORDER BY e.numero_at;
```

#### Property vs Método Estático

**Property en Expediente:**

```python
expediente = Expediente.query.get(123)
registro = expediente.titular_actual  # Property
```

**Método estático en HistoricoTitularExpediente:**

```python
registro = HistoricoTitularExpediente.titular_actual(expediente_id=123)
```

Ambos retornan el mismo objeto `HistoricoTitularExpediente` vigente.

#### Métodos del Modelo

**Método estático: titular_actual(expediente_id)**

Obtiene el registro histórico del titular actual vigente.

```python
registro = HistoricoTitularExpediente.titular_actual(expediente_id=42)
if registro:
    print(f"Titular: {registro.titular.nombre_completo}")
    print(f"Desde: {registro.fecha_desde}")
    print(f"Motivo: {registro.motivo}")
```

**Método estático: registrar_cambio(...)**

Registra un cambio de titularidad completo:
1. Cierra registro actual (`fecha_hasta = fecha_cambio`)
2. Crea nuevo registro vigente (`fecha_hasta = NULL`)
3. Actualiza snapshot en `expedientes.titular_id`

```python
nuevo_registro = HistoricoTitularExpediente.registrar_cambio(
    expediente_id=42,
    nuevo_titular_id=15,
    fecha_cambio=datetime.now(),
    motivo='VENTA',
    solicitud_cambio_id=120,
    observaciones='Cambio aprobado por resolución favorable'
)
db.session.commit()
```

**Método estático: crear_inicial(...)**

Crea el registro INICIAL del primer titular (usado por signal).

```python
registro = HistoricoTitularExpediente.crear_inicial(
    expediente_id=42,
    titular_id=10,
    fecha_desde=datetime.now(),
    observaciones='Titular original del expediente'
)
db.session.add(registro)
db.session.commit()
```

#### Signals SQLAlchemy

**Signal: after_insert en Expediente**

Cuando se crea un expediente con `titular_id` asignado, automáticamente se crea el registro histórico inicial.

```python
@event.listens_for(Expediente, 'after_insert')
def crear_registro_historico_inicial(mapper, connection, target):
    if target.titular_id is None:
        return  # Sin titular, no crear histórico
    
    # INSERT en historico_titulares_expediente
    connection.execute(
        insert(historico_table).values(
            expediente_id=target.id,
            titular_id=target.titular_id,
            fecha_desde=datetime.now(),
            fecha_hasta=None,
            motivo='INICIAL',
            observaciones='Titular inicial del expediente'
        )
    )
```

#### Validaciones

**Prevenir múltiples titulares vigentes:**

```python
# Antes de insertar nuevo registro vigente, cerrar el anterior
registro_actual = HistoricoTitularExpediente.titular_actual(expediente_id)
if registro_actual:
    registro_actual.fecha_hasta = datetime.now()
```

**Validar fecha_cambio no anterior a fecha_desde:**

```python
if fecha_cambio < registro_actual.fecha_desde:
    raise ValueError(
        f"Fecha cambio ({fecha_cambio}) anterior a vigencia actual "
        f"({registro_actual.fecha_desde})"
    )
```

#### Integración con Interfaz Web

**Vista de histórico en detalle de expediente:**

```html
<h3>Histórico de Titularidad</h3>
<table>
    <tr>
        <th>Titular</th>
        <th>Desde</th>
        <th>Hasta</th>
        <th>Motivo</th>
        <th>Solicitud</th>
    </tr>
    {% for registro in expediente.historico_titulares|sort(attribute='fecha_desde') %}
    <tr>
        <td>{{ registro.titular.nombre_completo }}</td>
        <td>{{ registro.fecha_desde|datetime }}</td>
        <td>{{ registro.fecha_hasta|datetime if registro.fecha_hasta else 'VIGENTE' }}</td>
        <td>{{ registro.motivo }}</td>
        <td>
            {% if registro.solicitud_cambio %}
                <a href="{{ url_for('solicitudes.detalle', id=registro.solicitud_cambio_id) }}">
                    Solicitud {{ registro.solicitud_cambio_id }}
                </a>
            {% else %}
                -
            {% endif %}
        </td>
    </tr>
    {% endfor %}
</table>
```

**Formulario de cambio de titular:**

```python
@bp.route('/expediente/<int:id>/cambiar-titular', methods=['POST'])
@login_required
def cambiar_titular(id):
    expediente = Expediente.query.get_or_404(id)
    nuevo_titular_id = request.form.get('nuevo_titular_id')
    motivo = request.form.get('motivo')
    observaciones = request.form.get('observaciones')
    
    try:
        HistoricoTitularExpediente.registrar_cambio(
            expediente_id=expediente.id,
            nuevo_titular_id=nuevo_titular_id,
            fecha_cambio=datetime.now(),
            motivo=motivo,
            solicitud_cambio_id=None,  # O ID de solicitud aprobada
            observaciones=observaciones
        )
        db.session.commit()
        flash('Titular actualizado correctamente', 'success')
    except ValueError as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('expedientes.detalle', id=id))
```

#### Migraciones

**Creación inicial:** `bf66f512eaf4_add_historico_titulares_expediente_table.py`

**Cambio DATE → DateTime:** `0d6742443660_cambiar_fecha_desde_y_fecha_hasta_de.py`

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
