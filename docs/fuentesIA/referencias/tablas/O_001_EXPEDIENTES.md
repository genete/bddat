<!--
Tabla: EXPEDIENTES
Generado automáticamente por: scripts/split_tables.py
Fecha de generación: 04/02/2026 07:00
IMPORTANTE: No editar Tablas.md directamente.
            Editar este archivo y ejecutar merge_tables.py para regenerar.
-->

### EXPEDIENTES

Tabla principal que representa cada expediente de tramitación administrativa.

#### Estructura

| Campo | Tipo | Nullable | Descripción | Notas |
|:---|:---|:---|:---|:------|
| **ID** | INTEGER | NO | Identificador único del expediente | PK, autoincremental |
| **NUMERO_AT** | INTEGER | NO | Número de expediente administrativo (formato legacy) | Único en la organización. No es el ID sino un número correlativo tomado del sistema anterior |
| **RESPONSABLE_ID** | INTEGER | NO | Usuario responsable del expediente | FK → USUARIOS(ID). Usuario asignado con permisos de gestión completa |
| **TIPO_EXPEDIENTE_ID** | INTEGER | SÍ | Tipo de expediente según clasificación normativa | FK → TIPOS_EXPEDIENTES(ID). Define lógica procedimental aplicable |
| **HEREDADO** | BOOLEAN | SÍ | Indica si el expediente proviene del sistema anterior | TRUE = datos incompletos, solo metadatos heredados. FALSE/NULL = expediente gestionado completamente en este sistema |
| **PROYECTO_ID** | INTEGER | NO | Proyecto técnico único asociado al expediente | FK → PROYECTOS(ID). **UNIQUE** (relación 1:1). **Nuevo campo v3.0** |
| **TITULAR_ID** | INTEGER | SÍ | Titular actual del expediente | FK → ENTIDADES(ID). Nullable para expedientes en creación. **Nuevo campo v3.1** - Issue #64 |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `NUMERO_AT`, `PROYECTO_ID`
- **FK:**
  - `RESPONSABLE_ID` → `USUARIOS(ID)`
  - `TIPO_EXPEDIENTE_ID` → `TIPOS_EXPEDIENTES(ID)`
  - `PROYECTO_ID` → `PROYECTOS(ID)`
  - `TITULAR_ID` → `ENTIDADES(ID)` ON DELETE SET NULL

#### Índices

- `idx_expedientes_titular` sobre `TITULAR_ID`
- `idx_expedientes_numero_at` sobre `NUMERO_AT`
- `idx_expedientes_proyecto` sobre `PROYECTO_ID`
- `idx_expedientes_responsable` sobre `RESPONSABLE_ID`
- `idx_expedientes_tipo` sobre `TIPO_EXPEDIENTE_ID`

#### Decisiones de Diseño

##### Campo TITULAR_ID (v3.1 - Issue #64)

**Contexto:**  
Los expedientes administrativos tienen un titular legal que evoluciona durante su vida útil. Cambios de titularidad pueden ocurrir por transmisión de instalación, herencia, fusión empresarial, etc.

**Problema resuelto:**  
- **Consulta eficiente del titular actual** sin joins constantes a tabla de histórico
- **Punto de referencia** para modelo temporal de titularidad
- **Validación:** expediente sin titular = expediente incompleto (estado transitorio válido durante creación)

**Decisiones:**

1. **Nullable = TRUE**
   - **Motivo:** Permite flujo de creación por etapas (expediente → proyecto → solicitud inicial)
   - **Regla:** `titular_id` debe asignarse antes de tramitar primera solicitud de autorización
   - **Validación:** En capa de negocio, no constraint CHECK (permite estados transitorios)

2. **FK a ENTIDADES (no ENTIDADES_ADMINISTRADOS)**
   - **Motivo:** Entidad es tabla base polimórfica. Validación de rol "administrado" se realiza en capa de aplicación
   - **Ventaja:** Preparado para casos excepcionales (ej: organismos públicos titulares temporales de instalaciones)
   - **Referencia:** Tabla `ESTRUCTURA.TIPOS_ENTIDADES` define qué tipos pueden ser titulares via flag `puede_ser_solicitante`

3. **ON DELETE SET NULL (no CASCADE)**
   - **Motivo:** Preservar integridad histórica del expediente aunque se elimine la entidad
   - **Impacto:** Expediente con titular NULL por borrado = estado excepcional que requiere corrección administrativa

4. **Campo redundante con histórico**
   - **Motivo:** Optimización de rendimiento. El 99% de consultas acceden al titular actual, no al histórico
   - **Coste:** Sincronización titular_id ↔ HISTORICO_TITULARES_EXPEDIENTE gestionada mediante triggers o lógica aplicación
   - **Alternativa descartada:** Consultar siempre `MAX(fecha_desde) WHERE fecha_hasta IS NULL` en histórico (costoso en queries recurrentes)

**Relación con tabla HISTORICO_TITULARES_EXPEDIENTE:**

El campo `titular_id` representa una **caché desnormalizada** del titular actual. La tabla `HISTORICO_TITULARES_EXPEDIENTE` (Issue #64) almacena:
- Todos los titulares históricos con vigencia temporal
- Motivo del cambio (INICIAL, VENTA, HERENCIA, FUSION, etc.)
- Solicitud que originó el cambio de titularidad

**Regla de consistencia:**  
`expedientes.titular_id` DEBE coincidir con el registro de `historico_titulares_expediente` donde `expediente_id = expedientes.id AND fecha_hasta IS NULL`

#### Notas de Versión

- **v3.0:** Añadido campo `PROYECTO_ID` (relación 1:1 con proyecto). Un expediente tiene exactamente un proyecto técnico, que evoluciona mediante documentos versionados.
- **v3.1 (Issue #64):** Añadido campo `TITULAR_ID` para gestión de titularidad. Campo nullable que almacena el titular actual del expediente. Relacionado con nueva tabla `HISTORICO_TITULARES_EXPEDIENTE` para trazabilidad completa de cambios.

---
