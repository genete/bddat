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