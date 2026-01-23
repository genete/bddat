### SOLICITUDES

Actos administrativos solicitados dentro de un expediente.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único de la solicitud | NO | PK, autoincremental |
| **EXPEDIENTE_ID** | INTEGER | Expediente al que pertenece la solicitud | NO | FK → EXPEDIENTES(ID). **Nuevo campo v3.0**. Relación directa solicitud-expediente |
| **TIPO_SOLICITUD_ID** | INTEGER | Tipo de solicitud según normativa | NO | FK → TIPOS_SOLICITUDES(ID). Define el acto administrativo solicitado (AAP, AAC, MOD, DUP, etc.) |
| **FECHA** | DATE | Fecha de presentación de la solicitud | SÍ | Fecha administrativa oficial (registro de entrada). Puede ser NULL si está en preparación |
| **SOLICITUD_AFECTADA_ID** | INTEGER | Solicitud sobre la que actúa (desistimiento/renuncia) | SÍ | FK → SOLICITUDES(ID). Solo para tipos DESISTIMIENTO o RENUNCIA. Apunta a la solicitud que se desiste/renuncia |
| **FECHA_FIN** | DATE | Fecha de finalización/archivo de la solicitud | SÍ | Fecha de resolución, caducidad, archivo o cierre administrativo. NULL = solicitud en curso |

#### Claves

- **PK:** `ID`
- **FK:**
  - `EXPEDIENTE_ID` → `EXPEDIENTES(ID)`
  - `TIPO_SOLICITUD_ID` → `TIPOS_SOLICITUDES(ID)`
  - `SOLICITUD_AFECTADA_ID` → `SOLICITUDES(ID)` (autorreferencia)

#### Notas de Versión

- **v3.0:** **AÑADIDO** campo `EXPEDIENTE_ID`. Relación directa con expediente, elimina dependencia transitiva vía proyecto.
- **v3.0:** **ELIMINADO** campo `PROYECTO_ID`. La solicitud ya no apunta a un proyecto específico. El proyecto se deduce del expediente (`EXPEDIENTE.PROYECTO_ID`). La solicitud actúa sobre el estado del proyecto en el momento de su presentación (determinado por documentos vigentes en `DOCUMENTOS_PROYECTO` con `FECHA_ADMINISTRATIVA <= SOLICITUD.FECHA`).

#### Filosofía

La solicitud es un **acto administrativo concreto** dentro de un expediente. No necesita apuntar directamente al proyecto porque:

- Solo hay UN proyecto por expediente
- La solicitud actúa sobre el **estado temporal del proyecto** en su momento de presentación
- El estado se reconstruye consultando documentos del proyecto vigentes en esa fecha

---