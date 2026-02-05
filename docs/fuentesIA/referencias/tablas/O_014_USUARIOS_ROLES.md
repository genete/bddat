<!--
Tabla: USUARIOS_ROLES
Generado automáticamente por: scripts/split_tables.py
Fecha de generación: 31/01/2026 21:24
IMPORTANTE: No editar Tablas.md directamente.
            Editar este archivo y ejecutar merge_tables.py para regenerar.
-->

### USUARIOS_ROLES

Tabla puente para la relación N:M entre usuarios y roles (RBAC).

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del registro | NO | PK, autoincremental |
| **USUARIO_ID** | INTEGER | Usuario al que se asigna el rol | NO | FK → USUARIOS(ID). Parte de UNIQUE(usuario_id, rol_id) |
| **ROL_ID** | INTEGER | Rol asignado al usuario | NO | FK → ROLES(ID). Parte de UNIQUE(usuario_id, rol_id) |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `(USUARIO_ID, ROL_ID)` - Un usuario no puede tener el mismo rol duplicado
- **FK:**
  - `USUARIO_ID` → `USUARIOS(ID)` ON DELETE CASCADE
  - `ROL_ID` → `ROLES(ID)` ON DELETE CASCADE

#### Índices Recomendados

- `USUARIO_ID` (consulta: ¿qué roles tiene este usuario?)
- `ROL_ID` (consulta inversa: ¿qué usuarios tienen este rol?)

#### Relaciones

- **usuario**: USUARIOS.id (FK CASCADE, usuario contenedor)
- **rol**: ROLES.id (FK CASCADE, rol asignado)

#### Notas de Versión

- **v3.1**: Tabla nueva. Reemplaza el campo `rol` en USUARIOS (que antes era 1:1) para permitir roles múltiples.

#### Filosofía

Esta tabla puente permite **roles múltiples por usuario**:

- **Un rol**: Usuario ID=1 con rol TRAMITADOR (1 registro)
- **Roles múltiples**: Usuario ID=2 con TRAMITADOR + SUPERVISOR (2 registros)
- **Flexibilidad**: Permite promoción sin perder permisos anteriores
- **Sin duplicados**: El constraint UNIQUE evita asignar el mismo rol dos veces

#### Casos de Uso

**Usuario con un solo rol (Tramitador):**
- Usuario ID=1
- 1 registro: (usuario_id=1, rol_id=3) -- TRAMITADOR

**Usuario con roles múltiples (Tramitador + Supervisor):**
- Usuario ID=2
- 2 registros:
  - (usuario_id=2, rol_id=3) -- TRAMITADOR
  - (usuario_id=2, rol_id=2) -- SUPERVISOR

**Administrador puro:**
- Usuario ID=3
- 1 registro: (usuario_id=3, rol_id=1) -- ADMIN

**Consulta: ¿Qué roles tiene el usuario 2?**
```sql
SELECT r.codigo, r.nombre
FROM usuarios_roles ur
JOIN roles r ON ur.rol_id = r.id
WHERE ur.usuario_id = 2;
```

**Consulta inversa: ¿Qué usuarios son SUPERVISOR?**
```sql
SELECT u.username, u.nombre, u.apellidos
FROM usuarios u
JOIN usuarios_roles ur ON u.id = ur.usuario_id
JOIN roles r ON ur.rol_id = r.id
WHERE r.codigo = 'SUPERVISOR';
```

**Verificar si usuario tiene permiso ADMIN:**
```sql
SELECT COUNT(*) > 0 AS es_admin
FROM usuarios_roles ur
JOIN roles r ON ur.rol_id = r.id
WHERE ur.usuario_id = ? AND r.codigo = 'ADMIN';
```

#### Reglas de Negocio

1. **CASCADE en DELETE**: Si se borra un usuario, se borran automáticamente sus roles
2. **No duplicados**: El constraint UNIQUE evita asignar el mismo rol dos veces
3. **Al menos un rol**: Todo usuario activo debe tener al menos un rol (validar en interfaz)
4. **Sin auto-asignación ADMIN**: Solo un ADMIN puede asignar rol ADMIN a otro usuario
5. **Roles acumulativos**: Los permisos se suman (TRAMITADOR + SUPERVISOR = permisos de ambos)

#### Combinaciones Típicas

| Combinación | Uso típico |
|:---|:---|
| **TRAMITADOR** | Técnico que solo tramita sus expedientes asignados |
| **TRAMITADOR + SUPERVISOR** | Jefe de sección: tramita + coordina equipo |
| **SUPERVISOR** | Coordinador que solo supervisa, no tramita |
| **ADMIN** | Administrador del sistema (no necesita otros roles) |
| **ADMINISTRATIVO** | Personal auxiliar de consulta |

---
