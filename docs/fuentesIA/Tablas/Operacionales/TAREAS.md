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