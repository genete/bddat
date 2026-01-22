### SOLICITUDES_TIPOS

Tabla puente que gestiona relaciones muchos a muchos entre solicitudes y tipos de solicitudes individuales.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del registro | NO | PK, autoincremental |
| **SOLICITUD_ID** | INTEGER | Solicitud a la que se aplica el tipo | NO | FK → SOLICITUDES(ID). Una solicitud puede contener múltiples tipos |
| **TIPO_SOLICITUD_ID** | INTEGER | Tipo individual de solicitud aplicado | NO | FK → TIPOS_SOLICITUDES(ID). Los tipos individuales se definen en TIPOS_SOLICITUDES |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `(SOLICITUD_ID, TIPO_SOLICITUD_ID)` - Una solicitud no puede tener el mismo tipo duplicado
- **FK:**
  - `SOLICITUD_ID` → `SOLICITUDES(ID)` ON DELETE CASCADE
  - `TIPO_SOLICITUD_ID` → `TIPOS_SOLICITUDES(ID)`

#### Índices Recomendados

- `SOLICITUD_ID` (tipos de una solicitud)
- `TIPO_SOLICITUD_ID` (solicitudes que incluyen un tipo específico)

#### Notas de Versión

- **v3.0:** **NUEVA TABLA**. Implementa arquitectura de tipos individuales con combinaciones flexibles mediante tabla puente N:M.

#### Filosofía

Esta tabla implementa la **arquitectura v3.0 de tipos individuales**:

**Antes (v2.0):**
- Tipos combinados hardcodeados: AAP+AAC, AAP+DUP, AAP+AAC+DUP
- 20+ tipos en `TIPOS_SOLICITUDES` con combinaciones explícitas
- Difícil añadir nuevas combinaciones
- Redundancia y difícil mantenimiento

**Ahora (v3.0):**
- 17 tipos individuales en `TIPOS_SOLICITUDES`: AAP, AAC, DUP, AAE_PROVISIONAL, AAE_DEFINITIVA, etc.
- Combinaciones mediante tabla puente `SOLICITUDES_TIPOS`
- Flexibilidad total: cualquier combinación posible
- Escalable y mantenible

#### Ejemplos de Uso

**Solicitud simple (AAP):**
```sql
-- Solicitud ID=1: Solo AAP
INSERT INTO solicitudes_tipos (solicitud_id, tipo_solicitud_id) VALUES (1, 1); -- AAP
```

**Solicitud combinada (AAP + AAC):**
```sql
-- Solicitud ID=2: AAP + AAC
INSERT INTO solicitudes_tipos (solicitud_id, tipo_solicitud_id) VALUES 
  (2, 1), -- AAP
  (2, 2); -- AAC
```

**Solicitud triple (AAP + AAC + DUP):**
```sql
-- Solicitud ID=3: AAP + AAC + DUP
INSERT INTO solicitudes_tipos (solicitud_id, tipo_solicitud_id) VALUES 
  (3, 1), -- AAP
  (3, 2), -- AAC
  (3, 3); -- DUP
```

**Solicitud con explotación (AAE_PROVISIONAL):**
```sql
-- Solicitud ID=4: Solo AAE Provisional (RDL 7/2025)
INSERT INTO solicitudes_tipos (solicitud_id, tipo_solicitud_id) VALUES (4, 4); -- AAE_PROVISIONAL
```

**Solicitud con explotación definitiva (tras pruebas):**
```sql
-- Solicitud ID=5: Solo AAE Definitiva
INSERT INTO solicitudes_tipos (solicitud_id, tipo_solicitud_id) VALUES (5, 5); -- AAE_DEFINITIVA
```

**Renovables con RAIPEE:**
```sql
-- Solicitud ID=6: AAP + RAIPEE_PREVIA
INSERT INTO solicitudes_tipos (solicitud_id, tipo_solicitud_id) VALUES 
  (6, 1), -- AAP
  (6, 7); -- RAIPEE_PREVIA

-- Solicitud ID=7: AAE_DEFINITIVA + RAIPEE_DEFINITIVA
INSERT INTO solicitudes_tipos (solicitud_id, tipo_solicitud_id) VALUES 
  (7, 5),  -- AAE_DEFINITIVA
  (7, 8);  -- RAIPEE_DEFINITIVA
```

**Autoconsumo Andalucía:**
```sql
-- Solicitud ID=8: AAP + AAC + RADNE (obligatorio en Andalucía para AT)
INSERT INTO solicitudes_tipos (solicitud_id, tipo_solicitud_id) VALUES 
  (8, 1), -- AAP
  (8, 2), -- AAC
  (8, 9); -- RADNE
```

#### Consultas Típicas

**Obtener todos los tipos de una solicitud:**
```sql
SELECT ts.siglas, ts.descripcion
FROM solicitudes_tipos st
JOIN tipos_solicitudes ts ON st.tipo_solicitud_id = ts.id
WHERE st.solicitud_id = ?
ORDER BY ts.siglas;
```

**Verificar si una solicitud incluye un tipo específico:**
```sql
SELECT EXISTS (
  SELECT 1 
  FROM solicitudes_tipos 
  WHERE solicitud_id = ? AND tipo_solicitud_id = ?
) AS tiene_tipo;
```

**Buscar solicitudes con combinación específica (AAP + AAC):**
```sql
SELECT s.id, s.fecha
FROM solicitudes s
WHERE EXISTS (
  SELECT 1 FROM solicitudes_tipos WHERE solicitud_id = s.id AND tipo_solicitud_id = 1 -- AAP
) AND EXISTS (
  SELECT 1 FROM solicitudes_tipos WHERE solicitud_id = s.id AND tipo_solicitud_id = 2 -- AAC
);
```

**Contar solicitudes por tipo individual:**
```sql
SELECT ts.siglas, COUNT(st.solicitud_id) AS total
FROM tipos_solicitudes ts
LEFT JOIN solicitudes_tipos st ON ts.id = st.tipo_solicitud_id
GROUP BY ts.id, ts.siglas
ORDER BY total DESC;
```

#### Reglas de Negocio

**Validación 1: Tipos incompatibles**
```sql
-- AAE_PROVISIONAL y AAE_DEFINITIVA son mutuamente excluyentes
-- Validación en interfaz: no permitir ambas en la misma solicitud
```

**Validación 2: Secuencia temporal**
```sql
-- RAIPEE_DEFINITIVA requiere RAIPEE_PREVIA previa (en solicitud anterior del mismo expediente)
-- AAE_DEFINITIVA requiere AAE_PROVISIONAL previa (en solicitud anterior)
```

**Validación 3: Requisitos legales**
```sql
-- DUP solo aplicable si existe AAP o AAC previa o simultánea
-- RADNE obligatorio en Andalucía para autoconsumo AT
```

**Validación 4: Coherencia con tipo de expediente**
```sql
-- RAIPEE solo para tipo_expediente_id = 'Renovable'
-- RADNE solo para tipo_expediente_id = 'Autoconsumo'
-- DUP solo para tipos que requieren ocupación de dominio público
```

#### Ventajas de la Arquitectura v3.0

1. **Flexibilidad total:** Cualquier combinación posible sin modificar maestras
2. **Escalabilidad:** Nuevos tipos individuales se añaden una sola vez
3. **Mantenimiento simple:** 17 tipos individuales vs 20+ combinaciones hardcodeadas
4. **Trazabilidad:** Histórico claro de qué se solicitó en cada acto
5. **Adaptabilidad normativa:** RDL 7/2025 (AAE dividida) implementado sin reestructuración
6. **Estadísticas precisas:** Conteo individual de AAP, AAC, DUP, etc.
7. **Validaciones específicas:** Reglas por tipo individual, no por combinación

#### Migración desde v2.0

**Conversión de tipos combinados a individuales:**

```sql
-- AAP+AAC (v2.0) → AAP + AAC (v3.0)
INSERT INTO solicitudes_tipos (solicitud_id, tipo_solicitud_id)
SELECT s.id, 1 FROM solicitudes s WHERE tipo_solicitud_id = tipo_antiguo_aapaac -- AAP
UNION ALL
SELECT s.id, 2 FROM solicitudes s WHERE tipo_solicitud_id = tipo_antiguo_aapaac; -- AAC

-- AAP+DUP (v2.0) → AAP + DUP (v3.0)
INSERT INTO solicitudes_tipos (solicitud_id, tipo_solicitud_id)
SELECT s.id, 1 FROM solicitudes s WHERE tipo_solicitud_id = tipo_antiguo_aapdup -- AAP
UNION ALL
SELECT s.id, 3 FROM solicitudes s WHERE tipo_solicitud_id = tipo_antiguo_aapdup; -- DUP

-- AAP+AAC+DUP (v2.0) → AAP + AAC + DUP (v3.0)
INSERT INTO solicitudes_tipos (solicitud_id, tipo_solicitud_id)
SELECT s.id, 1 FROM solicitudes s WHERE tipo_solicitud_id = tipo_antiguo_aapaacdup -- AAP
UNION ALL
SELECT s.id, 2 FROM solicitudes s WHERE tipo_solicitud_id = tipo_antiguo_aapaacdup -- AAC
UNION ALL
SELECT s.id, 3 FROM solicitudes s WHERE tipo_solicitud_id = tipo_antiguo_aapaacdup; -- DUP
```

#### Notas de Implementación

- El campo `SOLICITUDES.TIPO_SOLICITUD_ID` pasa a ser **opcional** o se elimina en futuras versiones
- La tabla `SOLICITUDES_TIPOS` es ahora la **fuente de verdad** para los tipos de una solicitud
- Interfaz debe permitir selección múltiple de tipos individuales
- Motor de reglas debe validar combinaciones según normativa vigente
- Informes y estadísticas deben basarse en `SOLICITUDES_TIPOS`, no en `SOLICITUDES.TIPO_SOLICITUD_ID`

---

**Versión:** 3.0  
**Fecha:** 22 de enero de 2026  
**Proyecto:** BDDAT - Sistema de Tramitación de Expedientes de Alta Tensión
