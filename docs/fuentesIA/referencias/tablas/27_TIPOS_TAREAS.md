<!--
Tabla: TIPOS_TAREAS
Generado automáticamente por: scripts/split_tables.py
Fecha de generación: 31/01/2026 21:04
IMPORTANTE: No editar Tablas.md directamente.
            Editar este archivo y ejecutar merge_tables.py para regenerar.
-->

### TIPOS_TAREAS

Catálogo de tipos atómicos de tareas.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del tipo de tarea | NO | PK, autoincremental |
| **CODIGO** | VARCHAR(50) | Código único identificativo de la tarea | NO | Valores: INCORPORAR, ANALISIS, REDACTAR, FIRMAR, NOTIFICAR, PUBLICAR, ESPERARPLAZO |
| **NOMBRE** | VARCHAR(200) | Denominación completa de la tarea | NO | Nombre descriptivo |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `CODIGO`

#### Índices Recomendados

- `CODIGO` (búsqueda rápida)

#### Notas de Versión

- **v3.0:** Sin cambios estructurales. **Solo 7 tipos atómicos**.

#### Filosofía

Tabla maestra que define los **7 tipos atómicos** de tareas:

1. **INCORPORAR:** Incorpora documento externo al sistema
2. **ANALISIS:** Analiza documento y genera informe
3. **REDACTAR:** Redacta borrador de documento
4. **FIRMAR:** Firma documento (transforma borrador en oficial)
5. **NOTIFICAR:** Notifica documento y genera justificante
6. **PUBLICAR:** Publica documento y genera justificante
7. **ESPERARPLAZO:** Espera transcurso de plazo administrativo

Estos 7 tipos cubren todas las operaciones administrativas posibles en la tramitación.

#### Relación con Otras Tablas

Usado en:
- `TAREAS.TIPO_TAREA_ID` (clasificación de la tarea)

---
