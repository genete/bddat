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