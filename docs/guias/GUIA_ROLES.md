# Roles y Permisos del Sistema BDDAT

## Descripción General

El sistema BDDAT implementa cuatro roles con permisos diferenciados sobre las tablas de la base de datos PostgreSQL. Esta estructura permite una gestión segura y eficiente de las operaciones administrativas y de tramitación.

---

## Definición de Roles

### ADMIN

Administrador total del sistema BDDAT, con control completo sobre toda la estructura.

**Permisos:**
- Control total sobre todos los schemas y tablas
- Único rol con permisos sobre tabla `alembic_version` (gestión de migraciones)
- Único rol que puede modificar el schema `legacy` (datos heredados del sistema anterior)
- Puede gestionar tablas reservadas exclusivamente para ADMIN

**Uso previsto:**
- Mantenimiento del sistema
- Gestión de migraciones de base de datos
- Administración de datos heredados

---

### SUPERVISOR

Rol de gestión y configuración del sistema, orientado a la supervisión operativa y configuración de reglas de negocio.

**Permisos:**
- Lectura y escritura completa sobre tabla `USUARIOS` (incluyendo asignación de roles)
- Lectura y escritura sobre tablas maestras del schema `public` (TIPOS_*, motor de reglas)
- Lectura sobre schema `legacy` (sin permisos de modificación)
- Lectura y escritura sobre todas las tablas operacionales del schema `public`

**No puede acceder a:**
- Tabla `alembic_version`
- Tablas reservadas específicamente para ADMIN
- Modificación del schema `legacy`

**Funciones principales:**
1. Gestión completa de usuarios y roles del sistema
2. Configuración del sistema (tablas maestras del schema `public`):
   - Gestión de tablas maestras (TIPOSEXPEDIENTES, TIPOSSOLICITUDES, TIPOSFASES, etc.)
   - Administración del motor de reglas de negocio
3. Supervisión de expedientes y procesos de tramitación

**Nota:** No es un tramitador. No tiene acceso a las vistas e interfaces específicas de tramitación.

---

### TRAMITADOR

Usuario operativo encargado de la tramitación de expedientes.

**Permisos:**
- Lectura y escritura sobre tablas operacionales: EXPEDIENTES, SOLICITUDES, FASES, TRAMITES, TAREAS, DOCUMENTOS
- Lectura sobre tabla `USUARIOS` (consultar datos de compañeros, modificar propios datos personales)
- Lectura sobre tablas maestras del schema `public` (necesario para tramitar según tipos, fases y reglas de negocio)
- Lectura sobre schema `legacy`

**No puede acceder a:**
- Gestión de usuarios (crear/eliminar/asignar roles)
- Tabla `alembic_version`
- Modificación de tablas maestras (TIPOS_*)
- Modificación del schema `legacy`

**Características:**
- Tiene vistas e interfaces propias del perfil de tramitación
- Puede modificar sus propios datos personales en tabla `USUARIOS`
- No puede modificar roles ni gestionar otros usuarios

---

### ADMINISTRATIVO

Usuario de apoyo administrativo con permisos similares a TRAMITADOR pero con interfaces diferenciadas.

**Permisos:**
- Lectura y escritura sobre tablas operacionales relevantes para tareas administrativas
- Lectura sobre tabla `USUARIOS` (consultar datos de compañeros, modificar propios datos personales)
- Lectura sobre tablas maestras del schema `public`
- Lectura sobre schema `legacy`

**No puede acceder a:**
- Gestión de usuarios (crear/eliminar/asignar roles)
- Tabla `alembic_version`
- Modificación de tablas maestras (TIPOS_*)
- Modificación del schema `legacy`
- Vistas e interfaces del perfil TRAMITADOR

**Diferencia principal con TRAMITADOR:**
- Tiene vistas e interfaces propias diferenciadas, orientadas a tareas administrativas
- No tiene acceso a las vistas específicas de tramitación técnica

---

## Tabla Resumen de Permisos

| Rol | USUARIOS | Tablas maestras | legacy | alembic_version | Tablas operacionales |
|:---|:---|:---|:---|:---|:---|
| **ADMIN** | RW | RW | RW | RW | RW |
| **SUPERVISOR** | RW | RW | R | - | RW |
| **TRAMITADOR** | R¹ | R | R | - | RW² |
| **ADMINISTRATIVO** | R¹ | R | R | - | RW² |

**Leyenda:**
- **RW**: Lectura y Escritura completa
- **R**: Solo Lectura
- **-**: Sin acceso
- **R¹**: Lectura completa + modificación de propios datos personales
- **RW²**: Lectura y Escritura sobre tablas operacionales del schema `public`

---

## Schemas del Sistema

### Schema `public`
Contiene todas las tablas del sistema: tablas operacionales (EXPEDIENTES, SOLICITUDES, FASES, TRAMITES, TAREAS, DOCUMENTOS, USUARIOS) y tablas maestras de configuración (TIPOSEXPEDIENTES, TIPOSSOLICITUDES, TIPOSFASES, TIPOSTRAMITES, TIPOSTAREAS, motor de reglas, etc.).

### Schema `legacy`
Contiene los datos heredados del sistema anterior. Solo lectura para todos los roles excepto ADMIN.

---

## Principios de Diseño

1. **Separación de responsabilidades**: Cada rol tiene un propósito claramente definido
2. **Principio de mínimo privilegio**: Los usuarios solo tienen los permisos necesarios para su función
3. **Protección de datos críticos**: Schema legacy protegido contra modificaciones no autorizadas
4. **Trazabilidad**: Cada usuario trabaja bajo su propio rol, facilitando auditorías

---

**Versión:** 1.1
**Fecha:** Abril 2026
**Proyecto:** BDDAT - Sistema de Tramitación de Expedientes de Alta Tensión
