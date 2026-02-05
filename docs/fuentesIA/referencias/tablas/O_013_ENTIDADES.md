<!--
Tabla: ENTIDADES
Generado automáticamente por: scripts/split_tables.py
Fecha de generación: 01/02/2026 08:05
IMPORTANTE: No editar Tablas.md directamente.
            Editar este archivo y ejecutar merge_tables.py para regenerar.
-->

### ENTIDADES

Tabla base que centraliza todas las personas físicas, jurídicas y organismos que interactúan con el sistema (titulares, solicitantes, autorizados, organismos públicos, ayuntamientos, diputaciones). Utiliza arquitectura de tablas inversas: campos comunes en esta tabla, metadatos específicos en tablas `entidades_*` según el tipo.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único de la entidad | NO | PK, autoincremental |
| **TIPO_ENTIDAD_ID** | INTEGER | Tipo de entidad que determina tabla de metadatos | NO | FK → TIPOS_ENTIDADES(ID). Define qué tabla `entidades_*` usar |
| **CIF_NIF** | VARCHAR(20) | CIF/NIF/NIE normalizado | SÍ | UNIQUE. Mayúsculas, sin espacios/guiones. Ej: "12345678A", "B12345678". NULL para algunos organismos históricos |
| **NOMBRE_COMPLETO** | VARCHAR(200) | Razón social, nombre completo o nombre oficial | NO | Indexed. Personas físicas: nombre completo. Jurídicas/organismos: razón social/nombre oficial |
| **EMAIL** | VARCHAR(120) | Email general de contacto | SÍ | NO es el email de notificaciones (va en `entidades_administrados`) |
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
  - `TIPO_ENTIDAD_ID` → `TIPOS_ENTIDADES(ID)`
  - `MUNICIPIO_ID` → `MUNICIPIOS(ID)`
- **UNIQUE:** `CIF_NIF`

#### Índices Recomendados

- `TIPO_ENTIDAD_ID` (consultas por tipo)
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
```

#### Relaciones

- **tipo_entidad**: TIPOS_ENTIDADES.id (FK, catálogo de tipos)
- **municipio**: MUNICIPIOS.id (FK, ubicación geográfica)
- **datos_administrado**: ENTIDADES_ADMINISTRADOS.entidad_id (1:1, metadatos administrados)
- **datos_organismo**: ENTIDADES_ORGANISMOS_PUBLICOS.entidad_id (1:1, metadatos organismos)
- **datos_ayuntamiento**: ENTIDADES_AYUNTAMIENTOS.entidad_id (1:1, metadatos ayuntamientos)
- **datos_diputacion**: ENTIDADES_DIPUTACIONES.entidad_id (1:1, metadatos diputaciones)
- **expedientes_como_titular**: EXPEDIENTES.titular_id (1:N inversa)
- **solicitudes_como_solicitante**: SOLICITUDES.solicitante_id (1:N inversa)
- **solicitudes_como_autorizado**: SOLICITUDES.autorizado_id (1:N inversa)

#### Notas de Versión

- **v1.0** (01/02/2026): Creación inicial de la tabla con arquitectura de tablas inversas

#### Filosofía

La tabla `entidades` implementa el patrón de **tablas inversas** (inverse/bridge tables) para gestionar múltiples tipos de entidades con metadatos heterogéneos:

- **Campos comunes** en `entidades` (CIF, nombre, contacto, dirección)
- **Metadatos específicos** en tablas `entidades_*` según tipo
- **Relaciones polimórficas** 1:1 entre `entidades` y cada tabla de metadatos
- **Una entidad puede tener múltiples roles** (ej: ayuntamiento que también es administrado)

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
- `ENTIDADES_ADMINISTRADOS.EMAIL_NOTIFICACIONES`: específico para sistema Notifica (solo administrados)
- `ENTIDADES_ORGANISMOS_PUBLICOS.CODIGO_DIR3`: notificaciones vía SIR (solo organismos públicos)

#### Tipos de Entidad

El campo `TIPO_ENTIDAD_ID` determina:
- Qué tabla de metadatos (`ENTIDADES_*`) debe tener registro asociado
- Qué formulario mostrar en la interfaz
- Qué validaciones aplicar

Tabla `TIPOS_ENTIDADES` contiene campo `tabla_metadatos` que mapea tipo → tabla física.

#### Reglas de Negocio

1. **Normalización CIF/NIF**: Método estático `normalizar_cif_nif()` aplicar antes de guardar
2. **Validación CIF/NIF**: Método estático `validar_cif_nif()` con algoritmo oficial
3. **CIF/NIF opcional**: Algunos organismos históricos pueden tener `CIF_NIF = NULL`
4. **Múltiples roles**: Una entidad puede tener registros en múltiples tablas `entidades_*`
5. **Código postal futuro**: Preparado para tabla `codigos_postales` con sugerencias por municipio
6. **Borrado lógico**: Usar `ACTIVO = FALSE` en lugar de DELETE físico
7. **Integridad referencial**:
   - Cascade en tablas `entidades_*` (eliminar metadatos con entidad)
   - Restrict en `expedientes`/`solicitudes` (no eliminar si hay referencias activas)

#### Flujo UX de Creación

1. Usuario elige tipo de entidad (administrado, organismo, ayuntamiento, etc.)
2. Sistema carga formulario con:
   - Campos comunes (`entidades`)
   - Campos específicos (tabla `entidades_*` correspondiente)
3. Al guardar, se crean ambos registros (entidad + metadatos) en transacción

#### Filtrado por Tipo en Tareas

**Fase "Todo Vale":**
```sql
-- Usuario filtra manualmente
SELECT * FROM entidades 
WHERE tipo_entidad_id = :tipo 
AND activo = TRUE
```

**Fase "Reglas de Negocio":**
```sql
-- Sistema aplica reglas según contexto
-- Ej: notificación tablón ayuntamiento → solo tipo AYUNTAMIENTO
SELECT * FROM entidades 
WHERE tipo_entidad_id IN (:tipos_permitidos)
AND activo = TRUE
```

---
