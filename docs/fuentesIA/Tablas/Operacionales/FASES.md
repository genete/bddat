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