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