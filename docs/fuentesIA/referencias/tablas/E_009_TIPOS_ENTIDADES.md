<!--
Tabla: TIPOS_ENTIDADES
Generado manualmente
Fecha de creación: 01/02/2026
IMPORTANTE: No editar Tablas.md directamente.
            Editar este archivo y ejecutar merge_tables.py para regenerar.
-->

### TIPOS_ENTIDADES

Catálogo de tipos de entidades del sistema con definición de roles permitidos.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del tipo de entidad | NO | PK, autoincremental |
| **CODIGO** | VARCHAR(50) | Código único identificativo del tipo | NO | UNIQUE. Valores: ADMINISTRADO, EMPRESA_SERVICIO_PUBLICO, ORGANISMO_PUBLICO, AYUNTAMIENTO, DIPUTACION |
| **NOMBRE** | VARCHAR(100) | Nombre descriptivo del tipo | NO | Para mostrar en interfaz de usuario |
| **TABLA_METADATOS** | VARCHAR(100) | Nombre de la tabla de metadatos asociada | NO | Tabla física donde residen metadatos específicos: entidades_administrados, entidades_empresas_servicio_publico, entidades_organismos_publicos, entidades_ayuntamientos, entidades_diputaciones |
| **PUEDE_SER_SOLICITANTE** | BOOLEAN | Indica si puede actuar como solicitante | NO | Default: FALSE. TRUE para tipos que pueden presentar solicitudes |
| **PUEDE_SER_CONSULTADO** | BOOLEAN | Indica si puede ser organismo consultado | NO | Default: FALSE. TRUE para tipos que pueden emitir informes en fase CONSULTAS |
| **PUEDE_PUBLICAR** | BOOLEAN | Indica si puede publicar (tablón/BOP) | NO | Default: FALSE. TRUE para tipos que pueden publicar anuncios oficiales |
| **DESCRIPCION** | TEXT | Descripción detallada del tipo de entidad | SÍ | Explicación de características y casos de uso |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `CODIGO`

#### Índices Recomendados

- `CODIGO` (búsqueda rápida por código)
- `(PUEDE_SER_SOLICITANTE, PUEDE_SER_CONSULTADO, PUEDE_PUBLICAR)` (filtros por capacidades)

#### Notas de Versión

- **v1.0** (01/02/2026): Creación inicial con 5 tipos de entidad y campos de roles

#### Filosofía

Tabla maestra que define los tipos de entidades del sistema y sus **capacidades de rol**:

- **Datos maestros estables:** Los 5 tipos no cambian, son parte de la lógica de negocio
- **Filtrado automático:** Los campos booleanos permiten filtrar entidades según contexto
- **Arquitectura tablas inversas:** Campo `TABLA_METADATOS` mapea tipo → tabla física de metadatos
- **Validación en tiempo de diseño:** La interfaz carga solo tipos válidos según operación

#### Tipos Definidos

| Código | Nombre | Tabla Metadatos | Solicitante | Consultado | Publicar |
|:---|:---|:---|:---:|:---:|:---:|
| **ADMINISTRADO** | Administrado | entidades_administrados | ✅ | ❌ | ❌ |
| **EMPRESA_SERVICIO_PUBLICO** | Empresa Servicio Público | entidades_empresas_servicio_publico | ✅ | ✅ | ❌ |
| **ORGANISMO_PUBLICO** | Organismo Público | entidades_organismos_publicos | ✅ | ✅ | ❌ |
| **AYUNTAMIENTO** | Ayuntamiento | entidades_ayuntamientos | ✅ | ✅ | ✅ |
| **DIPUTACION** | Diputación Provincial | entidades_diputaciones | ✅ | ✅ | ✅ |

#### Descripción de Tipos

**ADMINISTRADO:**
- Personas físicas o jurídicas privadas
- Roles: Titular de expediente, Solicitante, Autorizado en solicitud
- Ejemplos: Ciudadanos, empresas promotoras, comunidades de bienes
- Notificaciones: Sistema Notifica (email_notificaciones)

**EMPRESA_SERVICIO_PUBLICO:**
- Operadores de infraestructuras críticas y servicios públicos
- Roles: Solicitante (instalaciones propias) + Organismo consultado (afecciones)
- Ejemplos: Enagas, E-Distribución, REE, Consorcios de Aguas, operadores ferroviarios
- Características: Pueden tener instalaciones propias Y deben informar sobre afecciones a sus infraestructuras

**ORGANISMO_PUBLICO:**
- Administraciones públicas y organismos oficiales
- Roles: Organismo consultado + Solicitante ocasional (casos excepcionales)
- Ejemplos: Consejerías Junta Andalucía, Ministerios, Confederaciones Hidrográficas, ADIF, Defensa, AESA, Patrimonio
- Casos solicitante: Consejería Medio Ambiente autoriza instalación eléctrica en depuradora propia
- Notificaciones: Sistema SIR (codigo_dir3) o BandeJA cuando actúan como organismo; Notifica cuando actúan como solicitante

**AYUNTAMIENTO:**
- Corporaciones locales municipales
- Roles: Solicitante (ocasional) + Organismo consultado + Publicador (tablón edictos)
- Múltiples capacidades según contexto
- Notificaciones: SIR (codigo_dir3) cuando actúa como organismo, Notifica cuando actúa como solicitante

**DIPUTACION:**
- Corporaciones provinciales
- Roles: Solicitante ocasional + Organismo consultado + Publicador (Boletín Oficial Provincial)
- Casos solicitante: Construye infraestructuras para ayuntamientos (da servicio a municipios)
- Notificaciones: SIR (codigo_dir3) cuando actúa como organismo, Notifica cuando actúa como solicitante

#### Uso en Filtrado de Interfaz

**Contexto: Crear solicitud**
```sql
-- Cargar solo entidades que pueden ser solicitantes
SELECT e.* 
FROM entidades e
JOIN tipos_entidades te ON e.tipo_entidad_id = te.id
WHERE te.puede_ser_solicitante = TRUE
AND e.activo = TRUE
ORDER BY e.nombre_completo;
```

**Contexto: Fase CONSULTAS - Solicitar informe**
```sql
-- Cargar solo entidades que pueden emitir informes
SELECT e.* 
FROM entidades e
JOIN tipos_entidades te ON e.tipo_entidad_id = te.id
WHERE te.puede_ser_consultado = TRUE
AND e.activo = TRUE
ORDER BY te.codigo, e.nombre_completo;
```

**Contexto: Publicar en tablón municipal**
```sql
-- Cargar solo ayuntamientos
SELECT e.* 
FROM entidades e
JOIN tipos_entidades te ON e.tipo_entidad_id = te.id
WHERE te.codigo = 'AYUNTAMIENTO'
AND e.activo = TRUE
ORDER BY e.nombre_completo;
```

**Contexto: Publicar en BOP**
```sql
-- Cargar solo diputaciones
SELECT e.* 
FROM entidades e
JOIN tipos_entidades te ON e.tipo_entidad_id = te.id
WHERE te.codigo = 'DIPUTACION'
AND e.activo = TRUE
ORDER BY e.nombre_completo;
```

#### Validaciones en Lógica de Negocio

**Al crear solicitud:**
```python
# Validar que tipo_entidad puede ser solicitante
if not solicitante.tipo_entidad.puede_ser_solicitante:
    raise ValidationError("Este tipo de entidad no puede ser solicitante")
```

**Al solicitar informe en fase CONSULTAS:**
```python
# Validar que tipo_entidad puede ser consultado
if not organismo.tipo_entidad.puede_ser_consultado:
    raise ValidationError("Este tipo de entidad no puede emitir informes")
```

**Al publicar en tablón:**
```python
# Validar que tipo_entidad puede publicar
if not entidad_publicadora.tipo_entidad.puede_publicar:
    raise ValidationError("Este tipo de entidad no puede publicar anuncios")
```

#### Datos Maestros

```sql
INSERT INTO tipos_entidades (codigo, nombre, tabla_metadatos, puede_ser_solicitante, puede_ser_consultado, puede_publicar, descripcion) VALUES
(
    'ADMINISTRADO', 
    'Administrado', 
    'entidades_administrados', 
    TRUE, 
    FALSE, 
    FALSE,
    'Personas físicas o jurídicas privadas. Roles: Titular, Solicitante, Autorizado. Notificaciones vía Notifica.'
),
(
    'EMPRESA_SERVICIO_PUBLICO', 
    'Empresa Servicio Público', 
    'entidades_empresas_servicio_publico', 
    TRUE, 
    TRUE, 
    FALSE,
    'Operadores de infraestructuras críticas (Enagas, E-Distribución, REE, Consorcios Aguas). Pueden ser solicitantes Y emitir informes sobre afecciones.'
),
(
    'ORGANISMO_PUBLICO', 
    'Organismo Público', 
    'entidades_organismos_publicos', 
    TRUE, 
    TRUE, 
    FALSE,
    'Administraciones públicas (Junta, Ministerios, Confederaciones, ADIF, Defensa, AESA). Emiten informes. Excepcionalmente solicitantes (ej: depuradoras). Notificaciones vía SIR/BandeJA (DIR3) como organismo, Notifica como solicitante.'
),
(
    'AYUNTAMIENTO', 
    'Ayuntamiento', 
    'entidades_ayuntamientos', 
    TRUE, 
    TRUE, 
    TRUE,
    'Corporaciones locales. Múltiples roles: solicitante ocasional, organismo consultado, publicador (tablón edictos). Notificaciones vía SIR (DIR3) como organismo, Notifica como solicitante.'
),
(
    'DIPUTACION', 
    'Diputación Provincial', 
    'entidades_diputaciones', 
    TRUE, 
    TRUE, 
    TRUE,
    'Corporaciones provinciales. Roles: solicitante ocasional (construyen para ayuntamientos), organismo consultado, publicador BOP. Notificaciones vía SIR (DIR3) como organismo, Notifica como solicitante.'
);
```

#### Relación con Otras Tablas

Usado en:
- `ENTIDADES.TIPO_ENTIDAD_ID` (clasificación de entidad)

Relacionado con:
- `ENTIDADES_ADMINISTRADOS.ENTIDAD_ID` (metadatos si tipo = ADMINISTRADO o cualquier tipo que actúe como solicitante)
- `ENTIDADES_EMPRESAS_SERVICIO_PUBLICO.ENTIDAD_ID` (metadatos si tipo = EMPRESA_SERVICIO_PUBLICO)
- `ENTIDADES_ORGANISMOS_PUBLICOS.ENTIDAD_ID` (metadatos si tipo = ORGANISMO_PUBLICO)
- `ENTIDADES_AYUNTAMIENTOS.ENTIDAD_ID` (metadatos si tipo = AYUNTAMIENTO)
- `ENTIDADES_DIPUTACIONES.ENTIDAD_ID` (metadatos si tipo = DIPUTACION)

#### Reglas de Negocio

1. **Tabla inmutable:** Los 5 tipos son parte de la lógica de negocio. No añadir/eliminar tipos en runtime
2. **Código estable:** `CODIGO` no debe cambiar (ruptura de lógica en código Python)
3. **Una entidad, múltiples roles:** Una misma entidad puede tener registro en múltiples tablas `entidades_*` si su tipo lo permite (ej: Consejería Medio Ambiente puede estar en `entidades_organismos_publicos` Y en `entidades_administrados` cuando solicita instalación en depuradora)
4. **Validación obligatoria:** Siempre validar capacidades antes de asignar roles
5. **Filtrado por defecto:** Interfaces deben filtrar automáticamente según contexto usando campos `PUEDE_SER_*`

---
