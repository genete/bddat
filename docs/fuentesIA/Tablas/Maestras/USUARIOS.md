### USUARIOS

Usuarios del sistema con datos personales básicos.

#### Estructura

| Campo | Tipo | Descripción | Nullable | Notas |
|:---|:---|:---|:---|:---|
| **ID** | INTEGER | Identificador único del usuario | NO | PK, autoincremental |
| **SIGLAS** | VARCHAR(50) | Siglas o código identificativo del usuario | NO | Identificador corto para uso interno. Default: "NULO" |
| **NOMBRE** | VARCHAR(100) | Nombre del usuario | NO | Nombre de pila. Default: "Usuario" |
| **APELLIDO1** | VARCHAR(50) | Primer apellido | NO | Default: "no asignado" |
| **APELLIDO2** | VARCHAR(50) | Segundo apellido | SÍ | Puede ser NULL si no aplica |
| **ACTIVO** | BOOLEAN | Indica si el usuario está activo en el sistema | SÍ | TRUE = usuario habilitado. FALSE = usuario desactivado (no eliminado). Default: TRUE |

#### Claves

- **PK:** `ID`
- **UNIQUE:** `SIGLAS` (recomendado, aunque no está explícito en schema actual)

#### Índices Recomendados

- `SIGLAS` (búsqueda rápida por código)
- `ACTIVO` (filtrar usuarios activos)

#### Notas de Versión

- **v3.0:** Sin cambios estructurales respecto a versiones anteriores.

#### Filosofía

Tabla maestra de usuarios del sistema:

- Usuarios técnicos (tramitadores, supervisores)
- Identificación personal para responsabilidad y auditoría
- **No contiene credenciales** (gestionadas por motor de BD PostgreSQL)
- `ACTIVO=FALSE` permite deshabilitar usuarios sin perder historial (expedientes asignados, tareas realizadas)

#### Roles de Sistema

Los roles se gestionan a nivel de base de datos PostgreSQL. Consultar documento `Roles.md` para más información.

#### Uso Administrativo

- `RESPONSABLE_ID` en `EXPEDIENTES`: Usuario asignado como responsable del expediente completo
- Auditoría: Posibilidad futura de campos `CREADO_POR`, `MODIFICADO_POR` en tablas operacionales
- Interfaz: Filtros por tramitador, asignaciones de trabajo, estadísticas por usuario

#### Valores por Defecto

Los defaults permiten crear registros temporales de usuarios mientras se completa información, pero en producción todos los campos deberían tener valores reales.

---