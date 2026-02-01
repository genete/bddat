<!--
Tabla: SOLICITUDES_TIPOS
Generado automáticamente por: scripts/split_tables.py
Fecha de generación: 31/01/2026 21:22
IMPORTANTE: No editar Tablas.md directamente.
            Editar este archivo y ejecutar merge_tables.py para regenerar.
-->

### SOLICITUDES_TIPOS

Tabla puente para la relación N:M entre solicitudes y tipos de solicitudes.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del registro | NO | PK, autoincremental |
| **SOLICITUD_ID** | INTEGER | Solicitud que tiene el tipo | NO | FK → SOLICITUDES(ID). Parte de UNIQUE(solicitud_id, tipo_solicitud_id) |
| **TIPO_SOLICITUD_ID** | INTEGER | Tipo de solicitud asignado | NO | FK → TIPOS_SOLICITUDES(ID). Parte de UNIQUE(solicitud_id, tipo_solicitud_id) |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `(SOLICITUD_ID, TIPO_SOLICITUD_ID)` - Una solicitud no puede tener el mismo tipo duplicado
- **FK:**
  - `SOLICITUD_ID` → `SOLICITUDES(ID)` ON DELETE CASCADE
  - `TIPO_SOLICITUD_ID` → `TIPOS_SOLICITUDES(ID)` ON DELETE CASCADE

#### Índices Recomendados

- `SOLICITUD_ID` (consulta: ¿qué tipos tiene esta solicitud?)
- `TIPO_SOLICITUD_ID` (consulta inversa: ¿qué solicitudes son de este tipo?)

#### Relaciones

- **solicitud**: SOLICITUDES.id (FK CASCADE, solicitud contenedora)
- **tipo_solicitud**: TIPOS_SOLICITUDES.id (FK CASCADE, tipo asignado)

#### Notas de Versión

- **v3.1**: Tabla nueva. Reemplaza el campo `TIPO_SOLICITUD_ID` de SOLICITUDES para permitir múltiples tipos por solicitud.

#### Filosofía

Esta tabla puente permite modelar **solicitudes complejas** con múltiples actos administrativos simultáneos:

- **Solicitud simple**: AAP (un solo registro en esta tabla)
- **Solicitud múltiple**: AAP+AAC+DUP (tres registros en esta tabla, misma `solicitud_id`)
- **Motor de reglas**: Aplica lógica sobre tipos individuales, no combinaciones
- **Sin duplicación**: El constraint UNIQUE evita asignar el mismo tipo dos veces

#### Casos de Uso

**Solicitud con un solo tipo:**
- Solicitud ID=1 (AAP)
- 1 registro: (solicitud_id=1, tipo_solicitud_id=1)

**Solicitud con múltiples tipos:**
- Solicitud ID=2 (AAP + AAC + DUP)
- 3 registros:
  - (solicitud_id=2, tipo_solicitud_id=1) -- AAP
  - (solicitud_id=2, tipo_solicitud_id=2) -- AAC
  - (solicitud_id=2, tipo_solicitud_id=3) -- DUP

**Consulta: ¿Qué tipos tiene la solicitud 2?**
```sql
SELECT ts.siglas, ts.descripcion
FROM solicitudes_tipos st
JOIN tipos_solicitudes ts ON st.tipo_solicitud_id = ts.id
WHERE st.solicitud_id = 2;
```

**Consulta inversa: ¿Qué solicitudes son AAP?**
```sql
SELECT s.id, s.fecha_solicitud, s.estado
FROM solicitudes s
JOIN solicitudes_tipos st ON s.id = st.solicitud_id
JOIN tipos_solicitudes ts ON st.tipo_solicitud_id = ts.id
WHERE ts.siglas = 'AAP';
```

#### Reglas de Negocio

1. **CASCADE en DELETE**: Si se borra una solicitud, se borran automáticamente sus tipos asociados
2. **No duplicados**: El constraint UNIQUE evita asignar el mismo tipo dos veces a una solicitud
3. **Al menos un tipo**: Toda solicitud debe tener al menos un tipo (validar en interfaz)
4. **Tipos compatibles**: El motor de reglas valida que las combinaciones sean válidas (ej: MOD requiere AAC previa)

---
