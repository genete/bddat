<!--
Tabla: ENTIDADES
Generado automáticamente por: scripts/split_tables.py
Fecha de generación: 11/02/2026 19:27
IMPORTANTE: No editar Tablas.md directamente.
            Editar este archivo y ejecutar merge_tables.py para regenerar.
-->

### ENTIDADES

Tabla base que centraliza todas las personas físicas, jurídicas y organismos que interactúan con el sistema (titulares, solicitantes, autorizados, organismos públicos, ayuntamientos, diputaciones).

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único de la entidad | NO | PK, autoincremental |
| **TIPO_ENTIDAD** | VARCHAR(50) | Tipo de entidad | NO | Valores: 'PERSONA_FISICA', 'PERSONA_JURIDICA', 'ORGANISMO_PUBLICO', 'AYUNTAMIENTO', 'DIPUTACION' |
| **CIF_NIF** | VARCHAR(20) | CIF/NIF/NIE normalizado | SÍ | UNIQUE. Mayúsculas, sin espacios/guiones. Ej: "12345678A", "B12345678". NULL para algunos organismos históricos |
| **NOMBRE_COMPLETO** | VARCHAR(200) | Razón social, nombre completo o nombre oficial | NO | Indexed. Personas físicas: nombre completo. Jurídicas/organismos: razón social/nombre oficial |
| **EMAIL** | VARCHAR(120) | Email general de contacto | SÍ | NO es el email de notificaciones (va en `direcciones_notificacion`) |
| **TELEFONO** | VARCHAR(20) | Teléfono de contacto general | SÍ | Formato libre |
| **DIRECCION** | TEXT | Calle, número, piso, puerta | SÍ | Usar junto con CODIGO_POSTAL y MUNICIPIO_ID (preferente para España) |
| **CODIGO_POSTAL** | VARCHAR(10) | Código postal | SÍ | Texto libre. Futuro: sugerencias desde tabla `codigos_postales` |
| **MUNICIPIO_ID** | INTEGER | Municipio de la dirección | SÍ | FK → MUNICIPIOS(ID). Preferente sobre DIRECCION_FALLBACK |
| **DIRECCION_FALLBACK** | TEXT | Dirección completa en texto libre | SÍ | Para casos excepcionales (extranjero, datos históricos). Ej: "23, Peny Lane, St, 34523, London, England" |
| **ACTIVO** | BOOLEAN | Indica si la entidad está activa | NO | Default: TRUE. Borrado lógico |
| **NOTAS** | TEXT | Observaciones generales sobre la entidad | SÍ | Campo libre para anotaciones |
| **CREATED_AT** | TIMESTAMP | Fecha y hora de creación del registro | NO | Default: NOW() |
| **UPDATED_AT** | TIMESTAMP | Fecha y hora de última actualización | NO | Default: NOW(), auto-update |

#### Claves

- **PK:** `ID`
- **FK:**
  - `MUNICIPIO_ID` → `MUNICIPIOS(ID)`
- **UNIQUE:** `CIF_NIF`

#### Índices Recomendados

- `TIPO_ENTIDAD` (consultas por tipo)
- `CIF_NIF` (búsquedas por identificación fiscal)
- `NOMBRE_COMPLETO` (búsquedas por nombre)
- `ACTIVO` (filtros por estado)
- `MUNICIPIO_ID` (consultas geográficas)

#### Constraints

```sql
-- Dirección: estructurada o fallback, al menos una opción
CONSTRAINT chk_direccion_estructurada_o_fallback 
    CHECK (
        municipio_id IS NOT NULL 
        OR direccion_fallback IS NOT NULL 
        OR direccion IS NULL
    )

-- Tipos de entidad permitidos
CONSTRAINT chk_tipo_entidad
    CHECK (tipo_entidad IN ('PERSONA_FISICA', 'PERSONA_JURIDICA', 'ORGANISMO_PUBLICO', 'AYUNTAMIENTO', 'DIPUTACION'))
```

#### Relaciones

- **municipio**: MUNICIPIOS.id (FK, ubicación geográfica)
- **direcciones_notificacion**: DIRECCIONES_NOTIFICACION.entidad_id (1:N, direcciones por rol)
- **expedientes_como_titular**: EXPEDIENTES.titular_id (1:N inversa)
- **solicitudes_como_solicitante**: SOLICITUDES.solicitante_id (1:N inversa)
- **solicitudes_como_autorizado**: SOLICITUDES.autorizado_id (1:N inversa)

#### Notas de Versión

- **v1.0** (01/02/2026): Creación inicial de la tabla
- **v2.0** (11/02/2026 - Issue #103): Refactorización completa
  - Eliminada arquitectura de tablas inversas
  - Campo `tipo_entidad_id` (FK) reemplazado por `tipo_entidad` (VARCHAR)
  - Eliminadas tablas `tipos_entidades`, `entidades_administrados`, `entidades_organismos_publicos`, `entidades_ayuntamientos`, `entidades_diputaciones`, `entidades_consultados`
  - Creada tabla `direcciones_notificacion` para gestionar direcciones por rol
  - Simplificación: una tabla con todos los campos comunes

#### Filosofía

La tabla `entidades` implementa un **modelo simplificado** que centraliza toda la información común:

- **Campos comunes** en `entidades` (CIF, nombre, contacto, dirección general)
- **Direcciones de notificación por rol** en tabla `direcciones_notificacion` (1:N)
- **Sin metadatos especializados**: los campos específicos de cada tipo (si fueran necesarios) se añadirían como columnas opcionales en esta tabla
- **Una entidad puede tener múltiples direcciones** según el rol que desempeñe (titular, consultado, publicador)

#### Normalización CIF/NIF

- Siempre en **MAYÚSCULAS**
- Sin espacios, guiones ni caracteres especiales
- Ejemplos válidos: "12345678A", "B12345678", "X1234567L"
- Algoritmo de validación implementado en modelo SQLAlchemy

#### Dirección: Estructurada vs Fallback

**Preferente (España):**
- `DIRECCION` + `CODIGO_POSTAL` + `MUNICIPIO_ID`
- Permite consultas geográficas, validaciones y sugerencias

**Fallback (casos excepcionales):**
- `DIRECCION_FALLBACK` en texto libre
- Para direcciones extranjeras, datos históricos sin municipio en BD
- El país se incluye en el texto

**Regla:** Al menos una opción debe estar presente si hay dirección

#### Email General vs Email de Notificaciones

- `ENTIDADES.EMAIL`: contacto general, puede no usarse para notificaciones oficiales
- `DIRECCIONES_NOTIFICACION.EMAIL`: específico para notificaciones según rol (titular, consultado, publicador)
- `DIRECCIONES_NOTIFICACION.CODIGO_DIR3`: notificaciones vía SIR para organismos públicos

#### Tipos de Entidad

El campo `TIPO_ENTIDAD` determina:
- La naturaleza jurídica de la entidad
- Qué formulario mostrar en la interfaz
- Qué validaciones aplicar

Valores permitidos:
- `PERSONA_FISICA`: Ciudadanos individuales
- `PERSONA_JURIDICA`: Empresas, sociedades
- `ORGANISMO_PUBLICO`: Organismos de la administración
- `AYUNTAMIENTO`: Administraciones municipales
- `DIPUTACION`: Administraciones provinciales

#### Reglas de Negocio

1. **Normalización CIF/NIF**: Método estático `normalizar_cif_nif()` aplicar antes de guardar
2. **Validación CIF/NIF**: Método estático `validar_cif_nif()` con algoritmo oficial
3. **CIF/NIF opcional**: Algunos organismos históricos pueden tener `CIF_NIF = NULL`
4. **Múltiples direcciones**: Una entidad puede tener varias direcciones en `direcciones_notificacion` según roles
5. **Código postal futuro**: Preparado para tabla `codigos_postales` con sugerencias por municipio
6. **Borrado lógico**: Usar `ACTIVO = FALSE` en lugar de DELETE físico
7. **Integridad referencial**:
   - Cascade en `direcciones_notificacion` (eliminar direcciones con entidad)
   - Restrict en `expedientes`/`solicitudes` (no eliminar si hay referencias activas)

#### Flujo UX de Creación
1. Usuario elige tipo de entidad (persona física, jurídica, organismo, etc.)
2. Sistema carga formulario con:
   - Campos comunes (`entidades`)
   - Opción de añadir direcciones de notificación por rol
3. Al guardar, se crea la entidad y sus direcciones asociadas en transacción

#### Filtrado por Tipo en Tareas

**Fase "Todo Vale":**
```sql
-- Usuario filtra manualmente
SELECT * FROM entidades 
WHERE tipo_entidad = :tipo 
AND activo = TRUE
```

**Fase "Reglas de Negocio":**
```sql
-- Sistema aplica reglas según contexto
-- Ej: notificación tablón ayuntamiento → solo tipo AYUNTAMIENTO
SELECT * FROM entidades 
WHERE tipo_entidad IN (:tipos_permitidos)
AND activo = TRUE
```

#### Direcciones de Notificación

Ver tabla `DIRECCIONES_NOTIFICACION` para:
- Direcciones específicas por rol (titular, consultado, publicador)
- Múltiples direcciones activas por entidad
- Histórico de direcciones con vigencia temporal
- Integración con sistemas externos (SIR, DIR3)

---
