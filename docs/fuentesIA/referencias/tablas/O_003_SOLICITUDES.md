<!--
Tabla: SOLICITUDES
Generado automáticamente por: scripts/split_tables.py
Fecha de generación: 31/01/2026 21:04
IMPORTANTE: No editar Tablas.md directamente.
            Editar este archivo y ejecutar merge_tables.py para regenerar.
-->

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
