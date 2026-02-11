# O_014_DIRECCIONES_NOTIFICACION

## Propósito

Tabla que almacena direcciones de notificación específicas por rol para cada entidad. Permite que una misma entidad tenga diferentes direcciones según actúe como titular, consultado o publicador.

## Descripción

Gestiona direcciones de notificación diferenciadas por rol operativo. Una entidad puede tener múltiples direcciones activas simultáneamente, cada una asociada a roles específicos mediante bit flags.

**Casos de uso**:
- Empresa con direcciones diferentes para consultas y titularidad
- Organismo con múltiples sedes según tipo de trámite
- Histórico de direcciones con vigencia temporal

## Campos

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INTEGER | PK, AUTO_INCREMENT | Identificador único |
| `entidad_id` | INTEGER | NOT NULL, FK → entidades(id) ON DELETE CASCADE | Entidad propietaria |
| `descripcion` | TEXT | NULL | Descripción de la dirección (ej: "Sede Social", "Oficina Técnica") |
| `tipo_rol` | SMALLINT | NOT NULL | Bit flags: 1=TITULAR, 2=CONSULTADO, 4=PUBLICADOR |
| `email` | VARCHAR(120) | NULL | Email de notificación |
| `codigo_sir` | VARCHAR(50) | NULL | Código SIR (Sistema de Interconexión de Registros) |
| `codigo_dir3` | VARCHAR(20) | NULL | Código DIR3 (Directorio Común de Unidades Orgánicas) |
| `direccion` | TEXT | NULL | Calle, número, piso, puerta |
| `codigo_postal` | VARCHAR(10) | NULL | Código postal |
| `municipio_id` | INTEGER | NULL, FK → municipios(id) | Municipio (preferente sobre fallback) |
| `direccion_fallback` | TEXT | NULL | Dirección completa en texto libre (extranjero, datos históricos) |
| `activo` | BOOLEAN | NOT NULL, DEFAULT TRUE | Indica si la dirección está activa |
| `fecha_inicio` | DATE | NULL | Fecha de inicio de vigencia |
| `fecha_fin` | DATE | NULL | Fecha de fin de vigencia |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Fecha de creación |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Fecha de última actualización |

## Relaciones

- **entidad** → `ENTIDADES.id` (N:1, CASCADE)
- **municipio** → `MUNICIPIOS.id` (N:1)

## Índices

```sql
CREATE INDEX ix_direcciones_notificacion_entidad_id ON direcciones_notificacion(entidad_id);
CREATE INDEX ix_direcciones_notificacion_activo ON direcciones_notificacion(activo);
CREATE INDEX ix_direcciones_notificacion_tipo_rol ON direcciones_notificacion(tipo_rol);
```

## Constraints

```sql
ALTER TABLE direcciones_notificacion 
ADD CONSTRAINT fk_direcciones_notificacion_entidad 
FOREIGN KEY (entidad_id) REFERENCES entidades(id) ON DELETE CASCADE;

ALTER TABLE direcciones_notificacion 
ADD CONSTRAINT fk_direcciones_notificacion_municipio 
FOREIGN KEY (municipio_id) REFERENCES municipios(id);
```

## Bit Flags (tipo_rol)

| Valor | Constante | Descripción |
|-------|-----------|-------------|
| 1 | TITULAR | Dirección para rol de titular de expedientes |
| 2 | CONSULTADO | Dirección para consultas en trámites |
| 4 | PUBLICADOR | Dirección para publicaciones/notificaciones |
| 3 | TITULAR + CONSULTADO | Combinación (1 OR 2) |
| 5 | TITULAR + PUBLICADOR | Combinación (1 OR 4) |
| 6 | CONSULTADO + PUBLICADOR | Combinación (2 OR 4) |
| 7 | TODOS | Combinación (1 OR 2 OR 4) |

## Métodos Helper (Modelo Python)

```python
# Cálculo de bit flags
tipo_rol = DireccionNotificacion.calcular_tipo_rol(
    es_titular=True,
    es_consultado=False,
    es_publicador=True
)  # → 5 (1 + 4)

# Verificación de roles
direccion.es_titular  # Property booleana
direccion.es_consultado
direccion.es_publicador

# Listado de roles
direccion.roles_lista  # → ['TITULAR', 'PUBLICADOR']

# Dirección formateada
direccion.direccion_formateada()
# → {'linea1': 'C/ Falsa, 123', 'linea2': '28001 Madrid', 'provincia': 'Madrid'}
```

## Reglas de Negocio

1. **Una entidad puede tener múltiples direcciones activas**
   - Filtrar por `activo=TRUE` para obtener direcciones vigentes
   - Filtrar por `fecha_inicio` y `fecha_fin` para vigencia temporal

2. **Bit flags permiten múltiples roles por dirección**
   - Una dirección puede servir para varios roles simultáneamente
   - Query eficiente: `WHERE tipo_rol & 1 > 0` (tiene rol TITULAR)

3. **Prioridad de dirección**
   - Si `municipio_id` tiene valor → usar campos separados
   - Si `municipio_id` es NULL → usar `direccion_fallback`

4. **Soft delete implícito**
   - No borrar registros, marcar `activo=FALSE`
   - Mantener histórico de direcciones

5. **CASCADE on DELETE**
   - Si se borra entidad, se borran sus direcciones
   - Mantener integridad referencial

## Consultas Típicas

```sql
-- Direcciones activas de una entidad
SELECT * FROM direcciones_notificacion
WHERE entidad_id = 123 AND activo = TRUE
ORDER BY fecha_inicio DESC;

-- Direcciones con rol TITULAR
SELECT * FROM direcciones_notificacion
WHERE tipo_rol & 1 > 0 AND activo = TRUE;

-- Direcciones con múltiples roles
SELECT * FROM direcciones_notificacion
WHERE tipo_rol & 3 = 3  -- TITULAR Y CONSULTADO
AND activo = TRUE;

-- Direcciones vigentes en fecha específica
SELECT * FROM direcciones_notificacion
WHERE entidad_id = 123
AND activo = TRUE
AND (fecha_inicio IS NULL OR fecha_inicio <= '2026-02-11')
AND (fecha_fin IS NULL OR fecha_fin >= '2026-02-11');
```

## Ejemplos de Datos

```sql
-- Entidad con direcciones diferenciadas
INSERT INTO direcciones_notificacion 
(entidad_id, descripcion, tipo_rol, email, direccion, codigo_postal, municipio_id, activo)
VALUES
-- Sede para titularidad
(1, 'Sede Social', 1, 'titularidad@empresa.com', 'C/ Principal, 10', '18001', 100, TRUE),
-- Oficina técnica para consultas
(1, 'Oficina Técnica', 2, 'tecnico@empresa.com', 'Polígono Industrial, 5', '18002', 101, TRUE),
-- Dirección general para todos los roles
(2, 'Sede Única', 7, 'info@organismo.es', 'Plaza Mayor, 1', '28001', 200, TRUE);
```

## Migración desde Modelo Anterior

**Antes**: Direcciones en tablas especializadas (entidades_administrados, etc.)

**Ahora**: Todas en `direcciones_notificacion` con roles

**Script de migración** (ejemplo conceptual):
```sql
-- Migrar administrados (rol TITULAR)
INSERT INTO direcciones_notificacion 
(entidad_id, tipo_rol, email, direccion, codigo_postal, activo)
SELECT 
    entidad_id,
    1 AS tipo_rol,  -- TITULAR
    email_notificacion,
    domicilio_notificacion,
    codigo_postal,
    TRUE
FROM entidades_administrados;

-- Migrar organismos (rol CONSULTADO + PUBLICADOR)
INSERT INTO direcciones_notificacion 
(entidad_id, tipo_rol, email, codigo_sir, direccion, municipio_id, activo)
SELECT 
    entidad_id,
    6 AS tipo_rol,  -- CONSULTADO + PUBLICADOR (2 + 4)
    email_sede_electronica,
    codigo_sir,
    direccion,
    municipio_id,
    TRUE
FROM entidades_organismos_publicos;
```

## Notas de Versión

- **v1.0** (Issue #103): Creación inicial con bit flags y soft delete
- Sistema de roles flexible para evolución futura
- Preparado para integración con sede electrónica (SIR, DIR3)

## Referencias

- Issue #103: Refactorización modelo Entidades
- PR #104: Implementación direcciones_notificacion
- Normativa: Esquema Nacional de Interoperabilidad (ENI)
