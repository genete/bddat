### DOCUMENTOS_PROYECTO

Vinculación entre documentos y proyectos con metadatos de tipo y evolución.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del registro | NO | PK, autoincremental |
| **PROYECTO_ID** | INTEGER | Proyecto al que pertenece el documento | NO | FK → PROYECTOS(ID). El documento pertenece a UN proyecto único |
| **DOCUMENTO_ID** | INTEGER | Documento que forma parte del proyecto | NO | FK → DOCUMENTOS(ID). Archivo físico (PDF del proyecto, planos, anexos, etc.). **UNIQUE** - Un documento solo puede vincularse a un proyecto |
| **TIPO** | VARCHAR(20) | Tipo de documento en la evolución del proyecto | NO | Valores: 'PRINCIPAL', 'MODIFICADO', 'REFUNDIDO', 'ANEXO'. Define la naturaleza del documento en la secuencia temporal del proyecto |
| **OBSERVACIONES** | VARCHAR(500) | Notas sobre la vinculación | SÍ | Comentarios del técnico sobre la incorporación del documento (ej: "Modificación exigida por Medio Ambiente") |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `DOCUMENTO_ID` - **Un documento solo puede estar en un proyecto** (relación N:1, no N:M)
- **FK:**
  - `PROYECTO_ID` → `PROYECTOS(ID)` ON DELETE CASCADE
  - `DOCUMENTO_ID` → `DOCUMENTOS(ID)` ON DELETE CASCADE

#### Índices Recomendados

- `PROYECTO_ID` (documentos de un proyecto)
- `DOCUMENTO_ID` (único, consulta inversa: en qué proyecto está este documento)
- `(PROYECTO_ID, TIPO)` (filtros por tipo dentro del proyecto)

#### Notas de Versión

- **v3.0:** **NUEVA TABLA**. Externaliza la relación `DOCUMENTO.PROYECTO_ID` con metadatos (TIPO).
- **v3.0:** **Relación N:1**, no N:M. Un documento pertenece a un solo proyecto.
- **v3.0:** **ELIMINADO** campo `FECHA_VINCULACION`. Sin valor administrativo, trazabilidad ya existe en bitácora.
- **v3.0:** **ELIMINADO** campo `VIGENTE`. Vigencia se deduce de TIPO + orden cronológico (usando `DOCUMENTOS.FECHA_ADMINISTRATIVA`).

#### Filosofía

Esta tabla **NO es una relación muchos a muchos**, sino una **FK externalizada con metadatos**.

**Ventajas de externalizar:**

- Permite añadir metadatos (TIPO, OBSERVACIONES) sin modificar `DOCUMENTOS`
- Mantiene `DOCUMENTOS` puro (solo `EXPEDIENTE_ID`)
- La relación es opcional (un documento puede NO ser de proyecto)

#### Deducción de Vigencia (sin campo VIGENTE)

**Regla automática por consulta:**

1. **REFUNDIDO más reciente anula todos los anteriores**
2. **Sin REFUNDIDO: PRINCIPAL + todos los MODIFICADOS + ANEXOS son vigentes**
3. **ANEXOS siempre son vigentes (complementarios, no sustituyen)**

#### Valores de Campo TIPO

| Valor | Significado | Efecto en vigencia |
|:---|:---|:---|
| **PRINCIPAL** | Proyecto inicial presentado | Vigente hasta que aparece REFUNDIDO |
| **MODIFICADO** | Proyecto con cambios (mantiene esencia) | Se acumula al PRINCIPAL. Vigente hasta REFUNDIDO |
| **REFUNDIDO** | Consolida PRINCIPAL + MODIFICADOS | Anula todos los PRINCIPAL y MODIFICADOS anteriores. Es el único vigente |
| **ANEXO** | Documentación complementaria (cálculos, planos) | Siempre vigente, no sustituye otros |

#### Validaciones y Reglas

**Validación 1: Un documento solo en un proyecto**
```sql
-- UNIQUE constraint en DOCUMENTO_ID lo garantiza automáticamente
```

**Validación 2: Un proyecto siempre tiene al menos un PRINCIPAL**
```sql
-- Al crear proyecto, debe vincularse inmediatamente con documento PRINCIPAL
-- Validación en lógica de negocio al intentar eliminar el último PRINCIPAL
```

**Validación 3: REFUNDIDO debe ser posterior a PRINCIPAL**
```sql
-- Validación en interfaz: 
-- Si TIPO='REFUNDIDO', verificar que existe PRINCIPAL con FECHA_ADMINISTRATIVA anterior
```

#### Nota sobre Fechas

La ordenación de los documentos del proyecto se basa en la **fecha administrativa del documento** al que apunta cada `DOCUMENTO_ID`. Es por esto que la tabla `DOCUMENTOS_PROYECTO` no tiene campo de fecha, porque reside en el documento en sí, manteniendo los principios de **localización de la fuente de la verdad** y **no duplicidad innecesaria**.

---