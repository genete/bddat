<!--
Tabla: TIPOS_TRAMITES
Generado automáticamente por: scripts/split_tables.py
Fecha de generación: 31/01/2026 21:04
IMPORTANTE: No editar Tablas.md directamente.
            Editar este archivo y ejecutar merge_tables.py para regenerar.
-->

### TIPOS_TRAMITES

Catálogo de trámites administrativos.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del tipo de trámite | NO | PK, autoincremental |
| **CODIGO** | VARCHAR(50) | Código único identificativo del trámite | NO | Código normalizado: SOLICITUD_INFORME, ANUNCIO_BOP, RECEPCION_ALEGACION, etc. |
| **NOMBRE** | VARCHAR(200) | Denominación completa del trámite | NO | Nombre descriptivo legible |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `CODIGO`

#### Índices Recomendados

- `CODIGO` (búsqueda rápida)

#### Notas de Versión

- **v3.0:** Sin cambios estructurales. Tabla maestra estable.

#### Filosofía

Tabla maestra que define los trámites administrativos:

- Cada trámite representa una actuación administrativa concreta
- Define patrones de tareas esperados (no hardcoded, mediante reglas)
- El `CODIGO` es la referencia para identificar el tipo en reglas de negocio

#### Patrones de Tareas

Cada `TIPO_TRAMITE` sugiere un patrón de tareas (definido en motor de reglas):

- **SOLICITUD_INFORME:** REDACTAR → FIRMAR → NOTIFICAR → ESPERARPLAZO
- **RECEPCION_INFORME:** INCORPORAR → ANALISIS
- **ANUNCIO_BOP:** REDACTAR → FIRMAR → NOTIFICAR → ESPERARPLAZO → INCORPORAR → ESPERARPLAZO

#### Relación con Otras Tablas

Usado en:
- `TRAMITES.TIPO_TRAMITE_ID` (clasificación del trámite)

---
