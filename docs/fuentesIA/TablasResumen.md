# Definiciones de Tablas Principales v3.0

**Sistema de Tramitación de Expedientes de Alta Tensión (BDDAT)**  
**Formato agnóstico a la base de datos**  
**Fecha:** 30/12/2025

---

## Índice

- [Filosofía del Diseño](#filosofía-del-diseño)
- [Tablas Operacionales](#tablas-operacionales)
  - [EXPEDIENTES](#expedientes)
  - [PROYECTOS](#proyectos)
  - [SOLICITUDES](#solicitudes)
  - [DOCUMENTOS](#documentos)
  - [DOCUMENTOS_PROYECTO](#documentos_proyecto)
  - [TAREAS](#tareas)
  - [FASES](#fases)
  - [TRAMITES](#tramites)
  - [MUNICIPIOS_PROYECTO](#municipios_proyecto)
- [Tablas Maestras](#tablas-maestras)
  - [USUARIOS](#usuarios)
  - [TIPOS_EXPEDIENTES](#tipos_expedientes)
  - [TIPOS_SOLICITUDES](#tipos_solicitudes)
  - [TIPOS_FASES](#tipos_fases)
  - [TIPOS_TRAMITES](#tipos_tramites)
  - [TIPOS_TAREAS](#tipos_tareas)
  - [TIPOS_IA](#tipos_ia)
  - [MUNICIPIOS](#municipios)
  - [TIPOS_RESULTADOS_FASES](#tipos_resultados_fases)

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
