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