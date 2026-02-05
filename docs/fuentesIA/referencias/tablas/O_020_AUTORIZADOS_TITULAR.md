<!--
Tabla: AUTORIZADOS_TITULAR
Generado: 03/02/2026
IMPORTANTE: No editar Tablas.md directamente.
            Editar este archivo y ejecutar merge_tables.py para regenerar.
-->

### AUTORIZADOS_TITULAR

Tabla de relación N:N que registra las autorizaciones entre administrados. Permite que un titular (administrado) autorice a otro administrado para actuar en su nombre en la tramitación de expedientes. Sustituye el concepto legacy de la tabla `administrados` en las relaciones de autorización.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del registro de autorización | NO | PK, autoincremental |
| **TITULAR_ENTIDAD_ID** | INTEGER | Administrado titular que concede la autorización | NO | FK → ENTIDADES(ID). Debe tener entrada en ENTIDADES_ADMINISTRADOS |
| **AUTORIZADO_ENTIDAD_ID** | INTEGER | Administrado autorizado para representar al titular | NO | FK → ENTIDADES(ID). Debe tener entrada en ENTIDADES_ADMINISTRADOS |
| **ACTIVO** | BOOLEAN | Indica si la autorización está vigente | NO | Default: TRUE. Permite revocación sin borrar historial |
| **OBSERVACIONES** | TEXT | Notas libres del tramitador sobre la autorización | SÍ | Usos: ámbito (expediente específico/general), periodo de vigencia, motivo de desactivación |
| **CREATED_AT** | TIMESTAMP | Fecha y hora de creación del registro | NO | Default: NOW() |
| **UPDATED_AT** | TIMESTAMP | Fecha y hora de última actualización | NO | Default: NOW(), auto-update |

#### Claves

- **PK:** `ID`
- **FK:**
  - `TITULAR_ENTIDAD_ID` → `ENTIDADES(ID)` ON DELETE CASCADE
  - `AUTORIZADO_ENTIDAD_ID` → `ENTIDADES(ID)` ON DELETE CASCADE
- **UNIQUE:** `(TITULAR_ENTIDAD_ID, AUTORIZADO_ENTIDAD_ID)`

#### Índices Recomendados

- `TITULAR_ENTIDAD_ID` (consulta "¿quién puede actuar por este titular?")
- `AUTORIZADO_ENTIDAD_ID` (consulta "¿por quién puede actuar este autorizado?")
- `ACTIVO` (filtros por estado)
- `(TITULAR_ENTIDAD_ID, ACTIVO)` (consultas combinadas más frecuentes)

#### Constraints

```sql
-- No puede autorizarse a sí mismo
CONSTRAINT chk_no_autoautorizacion 
    CHECK (titular_entidad_id != autorizado_entidad_id)

-- Evitar duplicados
CONSTRAINT uq_titular_autorizado 
    UNIQUE (titular_entidad_id, autorizado_entidad_id)
```

#### Relaciones

- **titular**: ENTIDADES.id (FK, administrado que concede autorización)
- **autorizado**: ENTIDADES.id (FK, administrado que recibe autorización)

#### Notas de Versión

- **v1.0** (03/02/2026): Creación inicial. Sustituye relaciones legacy de tabla `administrados`

#### Filosofía

Esta tabla implementa el concepto de **representación legal/comercial** en el sistema:

- **Relación N:N**: Un titular puede autorizar a múltiples administrados, y un administrado puede estar autorizado por múltiples titulares
- **Borrado lógico**: `ACTIVO = FALSE` permite revocar sin perder historial
- **Validación en lógica de negocio**: Ambas entidades deben tener entrada en `ENTIDADES_ADMINISTRADOS`
- **Autoautorización implícita**: El titular SIEMPRE puede actuar por sí mismo (no requiere entrada en esta tabla)

#### Casos de Uso

**1. Consultora autorizada permanentemente**
```sql
INSERT INTO autorizados_titular (titular_entidad_id, autorizado_entidad_id, activo, observaciones)
VALUES (
    123,  -- E-Distribución
    456,  -- Consultora ACME SL
    TRUE,
    'Autorización general permanente para todos los expedientes'
);
```

**2. Autorización específica para un expediente**
```sql
INSERT INTO autorizados_titular (titular_entidad_id, autorizado_entidad_id, activo, observaciones)
VALUES (
    789,  -- Empresa Solar XYZ
    456,  -- Consultora ACME SL
    TRUE,
    'Autorización específica para expediente AT-2024-1234 (Planta fotovoltaica)'
);
```

**3. Revocación de autorización**
```sql
UPDATE autorizados_titular
SET activo = FALSE,
    observaciones = observaciones || ' | REVOCADA el 2026-02-03 por cambio de contrato',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 42;
```

#### Consultas Frecuentes

**¿Quién puede actuar en nombre del titular X?**
```sql
SELECT 
    e.id,
    e.nombre_completo,
    e.cif_nif,
    at.created_at AS autorizado_desde,
    at.observaciones
FROM autorizados_titular at
JOIN entidades e ON e.id = at.autorizado_entidad_id
WHERE at.titular_entidad_id = 123
  AND at.activo = TRUE;
```

**¿En nombre de qué titulares puede actuar el autorizado Y?**
```sql
SELECT 
    e.id,
    e.nombre_completo,
    e.cif_nif,
    at.created_at AS autorizado_desde,
    at.observaciones
FROM autorizados_titular at
JOIN entidades e ON e.id = at.titular_entidad_id
WHERE at.autorizado_entidad_id = 456
  AND at.activo = TRUE;
```

#### Reglas de Negocio

1. **Validación de administrados**: Antes de insertar, validar que ambas entidades tengan entrada en `ENTIDADES_ADMINISTRADOS`
2. **Autoautorización implícita**: El titular puede actuar por sí mismo sin entrada en esta tabla
   ```python
   def puede_actuar_como(entidad_id, titular_id):
       if entidad_id == titular_id:
           return True  # Autoautorización implícita
       return AutorizadoTitular.query.filter_by(
           titular_entidad_id=titular_id,
           autorizado_entidad_id=entidad_id,
           activo=True
       ).first() is not None
   ```
3. **Borrado lógico**: Nunca DELETE físico, siempre `ACTIVO = FALSE`
4. **Auditoría**: Mantener historial de autorizaciones revocadas
5. **Campo OBSERVACIONES flexible**: Permite registrar metadatos sin modificar schema:
   - Ámbito: "Expediente AT-2024-1234" vs "General"
   - Vigencia temporal: "Válida hasta 31/12/2026"
   - Motivo de desactivación: "Fin de contrato"
   - Tipo de poder: "Apoderado con poder notarial nº 123/2024"

#### Flujo UX de Gestión

**Alta de autorización:**
1. Usuario selecciona titular (selector de administrados)
2. Usuario selecciona autorizado (selector de administrados, excluyendo titular)
3. Usuario especifica observaciones (opcional)
4. Sistema crea registro con `ACTIVO = TRUE`

**Revocación:**
1. Usuario marca autorización como inactiva
2. Sistema solicita motivo (obligatorio)
3. Sistema actualiza `ACTIVO = FALSE` y concatena motivo en `OBSERVACIONES`

**Consulta:**
- Listar autorizaciones activas de un titular
- Listar titulares de un autorizado
- Filtrar por texto libre en observaciones

---
