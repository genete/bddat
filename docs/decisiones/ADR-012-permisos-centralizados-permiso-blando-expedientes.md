# ADR-012 — Permisos centralizados en código y permiso blando de acceso a expedientes

**Estado:** Adoptada
**Fecha:** 2026-05-27
**Issue:** #174

---

## Contexto

El sistema de control de acceso de BDDAT tiene dos capas de protección:

1. **Acceso a secciones administrativas** (`@role_required`): protege endpoints de gestión de usuarios y plantillas. Funciona correctamente.
2. **Acceso a expedientes concretos** (`verificar_acceso_expediente`): bloqueaba a TRAMITADOR/ADMINISTRATIVO el acceso a expedientes cuyo `responsable_id` no coincidía con su `id`. Lógica de permiso duro.

La lógica de permisos estaba dispersa en ~30 endpoints distribuidos en cinco ficheros, todos comprobando strings literales `'ADMIN'`, `'SUPERVISOR'`, `'TRAMITADOR'` mediante `tiene_rol()`. La tabla `roles` existe en BD y es útil para asignar roles a personas, pero no hay ninguna tabla de permisos: qué puede hacer cada rol está exclusivamente en código Python, sin punto de referencia único.

Esta dispersión genera dos problemas:

- **Mantenibilidad**: añadir o cambiar un permiso implica buscar y editar múltiples ficheros.
- **Coherencia**: crear un rol nuevo en BD es inútil sin modificar código en docenas de puntos.

Por otra parte, la decisión de negocio (presentación a jefatura, mayo 2026) establece que la tramitación de un expediente **no debe restringirse** al usuario responsable asignado. Cualquier técnico puede tramitar cualquier expediente; el cuaderno de bitácora (#1) registra las actuaciones realizadas fuera de la asignación nominal.

El contexto organizativo es relevante: los roles de BDDAT son divisiones funcionales ad-hoc para el sistema, no equivalentes biunívocos a puestos administrativos. Un funcionario puede tener varios roles. Los cambios de permisos son decisiones de diseño del producto BDDAT, no configuraciones realizadas en producción por el administrador de turno.

---

## Decisión

### 1. No se implementa RBAC orientado a BD

No se crea tabla `permisos` ni `rol_permisos`. Los permisos son decisiones de diseño de BDDAT —equivalentes a decisiones de producto— y no requieren ser configurables en producción. Configurarlos en BD añadiría complejidad sin beneficio real para este sistema.

La tabla `roles` y `usuarios_roles` **se mantienen** porque tienen uso legítimo: permiten asignar roles a personas desde la UI de administración de usuarios.

### 2. Dict `PERMISOS` como única fuente de verdad

Se introduce en `app/utils/permisos.py` un diccionario plano:

```python
PERMISOS = {
    'acceder_expediente':   {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
    'editar_expediente':    {'ADMIN', 'SUPERVISOR', 'TRAMITADOR'},
    'cambiar_responsable':  {'ADMIN', 'SUPERVISOR'},
    'ver_todos_proyectos':  {'ADMIN', 'SUPERVISOR'},
    'gestionar_usuarios':   {'ADMIN', 'SUPERVISOR'},
    'gestionar_plantillas': {'ADMIN', 'SUPERVISOR'},
}
```

Cambiar qué rol puede hacer qué = una línea en este dict. Añadir un permiso nuevo = una entrada en el dict + el check en el endpoint.

La función `tiene_permiso(nombre)` evalúa el dict contra el rol activo de sesión.

### 3. Permiso blando de acceso a expedientes

Se elimina el bloqueo duro por `responsable_id`. Cualquier usuario con permiso `editar_expediente` puede actuar sobre cualquier expediente. Cuando un usuario actúa (acción `editar`) sobre un expediente del que no es responsable, `verificar_acceso_expediente` registra automáticamente una entrada en la bitácora (`operacion='ALTERAR'`, `detalle={'actuacion_fuera_asignacion': True}`). Las acciones de sólo lectura (`ver`) no generan traza.

### 4. Decorador `require_permiso` para endpoints admin

Se añade `require_permiso(nombre_permiso)` en `app/decorators.py`. Los endpoints de admin_plantillas y usuarios migran de `@role_required('ADMIN', 'SUPERVISOR')` a `@require_permiso('gestionar_plantillas')` / `@require_permiso('gestionar_usuarios')`. El decorador `role_required` se mantiene sin modificar para no romper código existente.

### 5. Checks manuales de TRAMITADOR en proyectos

Los checks `tiene_rol('TRAMITADOR') and not tiene_rol('ADMIN', 'SUPERVISOR')` en los módulos de proyectos se reemplazan por `not tiene_permiso('ver_todos_proyectos')`.

---

## Razonamiento

**Por qué dict en código y no tabla en BD.**
Los permisos de BDDAT los decide el equipo de desarrollo, no el administrador del sistema en producción. Moverlos a BD no añade agilidad: seguiría requiriendo despliegue para que el cambio tenga efecto real (la UI admin solo modifica datos, no lógica). Un dict en código es explícito, versionado en git, y revisable en una línea.

**Por qué permiso blando y no eliminar los controles.**
La trazabilidad de actuaciones fuera de asignación es un requisito de auditoría. El permiso blando satisface la necesidad de flexibilidad operativa sin sacrificar la trazabilidad.

**Por qué solo registrar en editar y no en ver.**
Las lecturas no producen efectos. Registrar cada consulta de un expediente no asignado generaría ruido en la bitácora sin valor auditorial.

**Por qué mantener `role_required`.**
Tiene 16 usos activos. No aporta valor romper su firma; `require_permiso` coexiste como mecanismo declarativo para código nuevo o migrado.

### 6. Indicador visual de asignación (bombilla) + toast

Para usuarios con rol activo TRAMITADOR que editan un expediente no asignado, el sistema muestra un indicador visual persistente en el layout y lanza un toast de advertencia al entrar por primera vez.

**Función:**
```python
def es_expediente_ajeno(expediente):
    """True si rol activo es TRAMITADOR y expediente.responsable_id != current_user.id."""
```

ADMINISTRATIVO, ADMIN y SUPERVISOR quedan excluidos: los primeros no son dueños de expedientes; los segundos tienen acceso pleno por diseño.

**Mecanismo (Opción A):**
- `verificar_acceso_expediente` asigna `g.expediente_actual = expediente` en todos los puntos de edición.
- Un context processor en `app/__init__.py` inyecta `indicador_asignacion` (bool o None) a todos los templates.
- El layout renderiza un icono `bi-lightbulb-fill` en posición fija: verde si es propio, rojo si es ajeno.
- Un `<script>` inline lanza el toast Bootstrap **una sola vez por expediente** usando `sessionStorage('warned_exp_<id>')`.

El toast y el indicador rojo son UI informativa, no bloqueo. La traza en bitácora se produce igualmente.

---

## Consecuencias

- Añadir o cambiar un permiso requiere editar una sola línea en `PERMISOS`.
- Las actuaciones de técnicos fuera de su asignación quedan registradas en bitácora automáticamente.
- Los módulos de proyectos dejan de usar `tiene_rol()` directo; usan `tiene_permiso()`.
- Los templates que mostraban/ocultaban controles según rol usan `tiene_permiso()` vía contexto Jinja2.
- La tabla `roles` sigue siendo útil para la UI de usuarios; no hay cambio de esquema.
- No hay migración de BD.
