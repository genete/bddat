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