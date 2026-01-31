<!--
Tabla: ROLES
Generado automáticamente por: scripts/split_tables.py
Fecha de generación: 31/01/2026 21:23
IMPORTANTE: No editar Tablas.md directamente.
            Editar este archivo y ejecutar merge_tables.py para regenerar.
-->

### ROLES

Tabla maestra que define los roles del sistema (RBAC - Role-Based Access Control).

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del rol | NO | PK, autoincremental |
| **CODIGO** | VARCHAR(50) | Código único identificativo del rol | NO | UNIQUE. Inmutable. Usado en lógica de negocio |
| **NOMBRE** | VARCHAR(100) | Nombre descriptivo del rol | NO | Para mostrar en interfaz |
| **DESCRIPCION** | VARCHAR(500) | Descripción detallada de permisos | SÍ | Explicación de qué puede hacer este rol |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `CODIGO`

#### Índices Recomendados

- `CODIGO` (consultas frecuentes para validación de permisos)

#### Relaciones

- **usuarios_roles**: USUARIOS_ROLES.rol_id → asignaciones de usuarios (N:M)

#### Notas de Versión

- **v3.1**: Tabla nueva. Define roles para sistema RBAC (antes gestionado solo en Flask).

#### Filosofía

Los roles definen **niveles de acceso** en el sistema:

- **CODIGO**: Referencia estable para código Python (no cambiar en producción)
- **NOMBRE**: Etiqueta legible para interfaz de usuario
- **N:M con usuarios**: Un usuario puede tener múltiples roles
- **Permisos derivados**: El rol determina qué schemas/tablas/operaciones están permitidas

#### Roles Definidos

| Código | Nombre | Permisos principales |
|:---|:---|:---|
| **ADMIN** | Administrador | Acceso total: schemas (public, estructura, legacy), gestión de usuarios, configuración |
| **SUPERVISOR** | Supervisor | Gestión de usuarios, asignación de expedientes, visión global, schemas (public, estructura) |
| **TRAMITADOR** | Tramitador | Tramitación completa de expedientes asignados, schema public (lectura/escritura) |
| **ADMINISTRATIVO** | Administrativo | Solo lectura y consulta, schema public (solo SELECT) |

#### Permisos por Rol

**ADMIN:**
- GRANT ALL en schemas: `public`, `estructura`, `legacy`
- Gestión de usuarios y roles
- Configuración del sistema
- Acceso a auditoría completa

**SUPERVISOR:**
- GRANT SELECT, INSERT, UPDATE en schemas: `public`, `estructura`
- Asignación de expedientes a tramitadores
- Creación/modificación de usuarios (excepto ADMIN)
- Visión global de todos los expedientes

**TRAMITADOR:**
- GRANT SELECT, INSERT, UPDATE, DELETE en schema: `public`
- Solo expedientes asignados (filtro por `responsable_id`)
- Gestión completa de solicitudes, fases, trámites, documentos
- No puede modificar tipos/maestras

**ADMINISTRATIVO:**
- GRANT SELECT en schema: `public`
- Solo lectura: expedientes, proyectos, solicitudes, documentos
- No puede crear ni modificar datos

#### Reglas de Negocio

1. **CODIGO inmutable**: No cambiar en producción (ruptura de lógica)
2. **Al menos TRAMITADOR**: Todo usuario activo debe tener al menos un rol
3. **Roles múltiples**: Un usuario puede ser TRAMITADOR + SUPERVISOR
4. **Sin auto-asignación ADMIN**: Solo otro ADMIN puede asignar rol ADMIN
5. **Roles preestablecidos**: Tabla inmutable (INSERT inicial, no modificar)

#### Datos Maestros

```sql
INSERT INTO roles (codigo, nombre, descripcion) VALUES
('ADMIN', 'Administrador', 'Acceso total al sistema: gestión de usuarios, configuración, schemas completos'),
('SUPERVISOR', 'Supervisor', 'Gestión de usuarios, asignación de expedientes, visión global'),
('TRAMITADOR', 'Tramitador', 'Tramitación completa de expedientes asignados'),
('ADMINISTRATIVO', 'Administrativo', 'Solo lectura y consulta de expedientes');
```

---
