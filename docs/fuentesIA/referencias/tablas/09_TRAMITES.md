<!--
Tabla: TRAMITES
Generado automáticamente por: scripts/split_tables.py
Fecha de generación: 31/01/2026 21:04
IMPORTANTE: No editar Tablas.md directamente.
            Editar este archivo y ejecutar merge_tables.py para regenerar.
-->

### TRAMITES

Contenedor organizativo de tareas dentro de una fase.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del trámite | NO | PK, autoincremental |
| **FASE_ID** | INTEGER | Fase a la que pertenece el trámite | NO | FK → FASES(ID). Cada trámite se ejecuta dentro de una fase específica |
| **TIPO_TRAMITE_ID** | INTEGER | Tipo de trámite según catálogo | NO | FK → TIPOS_TRAMITES(ID). Define el trámite procedimental: SOLICITUD_INFORME, ANUNCIO_BOP, RECEPCION_ALEGACION, etc. |
| **FECHA_INICIO** | DATE | Fecha de inicio administrativo del trámite | SÍ | NULL = trámite planificado pero no iniciado. NOT NULL = trámite en curso o finalizado |
| **FECHA_FIN** | DATE | Fecha de finalización del trámite | SÍ | NULL = trámite pendiente o en curso. NOT NULL = trámite completado. Se deduce como la última fecha de finalización de todas las tareas asociadas, pero debe rellenarse manualmente |
| **OBSERVACIONES** | VARCHAR(2000) | Notas o comentarios sobre el trámite | SÍ | Campo libre para anotaciones del técnico sobre la ejecución del trámite |

#### Claves

- **PK:** `ID`
- **FK:**
  - `FASE_ID` → `FASES(ID)` ON DELETE CASCADE
  - `TIPO_TRAMITE_ID` → `TIPOS_TRAMITES(ID)`

#### Índices Recomendados

- `FASE_ID` (trámites de una fase)
- `TIPO_TRAMITE_ID` (filtros por tipo de trámite)
- `(FECHA_INICIO, FECHA_FIN)` (estado temporal y secuencia)

#### Notas de Versión

- **v3.0:** Sin cambios estructurales respecto a v2.0. Mantiene diseño minimalista.

#### Filosofía

El trámite es un **contenedor organizativo de tareas** dentro de una fase:

- **Estructura mínima:** Solo fechas, tipo y observaciones
- **Semántica en TIPO:** Los patrones de tareas (secuencias) viven en `TIPOS_TRAMITES` y se combinan según reglas de negocio
- **Sin campos específicos:** No hay remitentes, destinatarios ni documentos en esta tabla. Esos datos viven en las tareas y documentos
- **Fecha fin sugestionable:** Puede calcularse automáticamente como MAX(TAREAS.FECHA_FIN), pero se registra manualmente

#### Estados Deducibles (no almacenados)

- **PENDIENTE:** `FECHA_INICIO IS NULL`
- **EN_CURSO:** `FECHA_INICIO IS NOT NULL AND FECHA_FIN IS NULL`
- **COMPLETADO:** `FECHA_FIN IS NOT NULL`

#### Patrones de Tareas según Tipo

Cada `TIPO_TRAMITE_ID` determina qué secuencia de tareas se esperan (definido en lógica de negocio):

**Ejemplos:**

- **SOLICITUD_INFORME:** REDACTAR → FIRMAR → NOTIFICAR → ESPERARPLAZO
- **RECEPCION_INFORME:** INCORPORAR → ANALISIS
- **ANUNCIO_BOP:** REDACTAR → FIRMAR → NOTIFICAR → ESPERARPLAZO → INCORPORAR → ESPERARPLAZO (doble espera)
- **COMPROBACION_ADMISIBILIDAD:** ANALISIS

Los patrones se combinan y adaptan según reglas de negocio, no están hardcoded.

#### Reglas de Negocio

1. **No puede finalizarse** (`FECHA_FIN` NOT NULL) si existen tareas asociadas sin finalizar (`TAREAS.FECHA_FIN IS NULL`)
2. **Secuencias de trámites:** Determinadas por motor de reglas según `TIPO_TRAMITE_ID` y `TIPO_FASE_ID`
3. **Los trámites pueden ejecutarse en paralelo** dentro de una misma fase (ej: múltiples consultas a organismos simultáneas)

---
