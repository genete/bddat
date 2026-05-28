# ADR-013 — Permisos blandos generalizados: restringir actos, no miradas

**Estado:** Adoptada
**Fecha:** 2026-05-28
**Issue:** #497

---

## Contexto

ADR-012 estableció el "permiso blando" sobre expedientes: cualquier técnico con permiso `editar_expediente` puede actuar sobre cualquier expediente, no solo el asignado. La traza queda en bitácora. Esa decisión fue específica para el dominio de expedientes.

El resto del sistema mantenía la filosofía clásica: el rol no autorizado **no puede entrar** a la pantalla. `/admin/plantillas` redirige al perfil si no eres ADMIN/SUPERVISOR. Lo mismo para usuarios, y lo mismo se aplicaría a las futuras UIs de gestión del motor de reglas (#170), de tablas maestras (#171) y del catálogo de plazos.

Reflexión actual del usuario: BDDAT se usa en una organización donde la **visibilidad de los asuntos no es problema**. Lo que hay que evitar son los "manazas", no los "ojos". El conocimiento compartido facilita aprendizaje, continuidad ante jubilaciones y autonomía. Que un técnico pueda asomarse a las reglas del motor, al catálogo de plazos o al listado de plantillas sin riesgo de modificarlas es **valioso, no peligroso**.

Esta decisión también se ve reforzada por la auditoría UI y el análisis crítico de la fase 3 del revamping: ocultar pantallas administrativas obliga a redirects feos, complica el sidebar (que tendría que variar por rol) y rompe la coherencia visual entre lo que cada usuario percibe del sistema.

Excepciones razonables identificadas:

- Datos personales sensibles concretos: DNI de compañeros (otras apps corporativas como PTWANDA ya lo exponen sin tapujos; aquí preferimos restringirlo salvo a roles administrativos o al propio usuario).
- Estadísticas explícitas del trabajo individual de otros tramitadores (en caso de materializarse en alguna vista futura).

---

## Decisión

### 1. Generalización de la filosofía blanda

Por defecto, **cualquier rol autenticado puede ver cualquier pantalla administrativa**. Los permisos del sistema restringen **acciones** (crear, editar, borrar, activar, generar), no acceso visual.

### 2. Desdoblamiento del dict `PERMISOS`

Cada área administrativa pasa de un permiso único `gestionar_X` a (al menos) dos verbos: `acceder_X` y `gestionar_X`.

```python
PERMISOS = {
    # Expedientes — ya regulado por ADR-012, se mantiene
    'acceder_expediente':        {ADMIN, SUPERVISOR, TRAMITADOR, ADMINISTRATIVO},
    'editar_expediente':         {ADMIN, SUPERVISOR, TRAMITADOR},
    'cambiar_responsable':       {ADMIN, SUPERVISOR},
    'ver_todos_proyectos':       {ADMIN, SUPERVISOR, ADMINISTRATIVO},

    # Áreas administrativas — nuevo patrón acceder/gestionar
    'acceder_plantillas':        {ADMIN, SUPERVISOR, TRAMITADOR, ADMINISTRATIVO},
    'gestionar_plantillas':      {ADMIN, SUPERVISOR},

    'acceder_usuarios':          {ADMIN, SUPERVISOR, TRAMITADOR, ADMINISTRATIVO},
    'gestionar_usuarios':        {ADMIN, SUPERVISOR},

    'acceder_reglas_motor':      {ADMIN, SUPERVISOR, TRAMITADOR, ADMINISTRATIVO},
    'gestionar_reglas_motor':    {ADMIN, SUPERVISOR},

    'acceder_catalogo_plazos':   {ADMIN, SUPERVISOR, TRAMITADOR, ADMINISTRATIVO},
    'gestionar_catalogo_plazos': {ADMIN, SUPERVISOR},

    'acceder_tablas_maestras':   {ADMIN, SUPERVISOR, TRAMITADOR, ADMINISTRATIVO},
    'gestionar_tablas_maestras': {ADMIN, SUPERVISOR},

    # Excepciones para datos sensibles
    'ver_dni_usuarios':          {ADMIN, SUPERVISOR},
    # (Futuro, si se implementa una vista explícita de estadísticas por técnico:)
    # 'ver_estadisticas_otros': {ADMIN, SUPERVISOR},
}
```

### 3. Patrón de UI

- Endpoints de **lectura** (`listado`, `detalle`, `descargar`) llevan `@require_permiso('acceder_X')`.
- Endpoints de **mutación** (`nueva`, `editar`, `borrar`, `activar`, `toggle_*`) llevan `@require_permiso('gestionar_X')`.
- En templates Jinja, los botones y enlaces de mutación se envuelven en `{% if tiene_permiso('gestionar_X') %}`.
- En componentes React isla, los botones se condicionan con `tienePermiso('gestionar_X')`.
- La función `tiene_permiso` se expone al contexto Jinja vía context processor para evitar imports en cada vista.

### 4. Excepciones declaradas

- **DNI**: campo oculto con `***` salvo para roles con `ver_dni_usuarios` o cuando el usuario consulta su propio registro. Helper `puedo_ver_dni(entidad)`.
- **Estadísticas individuales agregadas**: si en el futuro se materializa una vista de rendimiento por técnico (varita mágica nº 1 del estudio de usuario fase 2), lleva permiso propio `ver_estadisticas_otros`. La lista de expedientes asignados a otros tramitadores **no** se considera estadística — sigue siendo visible.

### 5. Defensa en profundidad inalterada

Los endpoints siguen verificando permisos en backend. Que un botón no se muestre no exime al backend de validar el permiso al recibir la petición (defensa contra peticiones forjadas manualmente). El motor de reglas y los invariantes ESFTT siguen actuando con independencia del rol.

### 6. Sidebar y navegación

El sidebar es **el mismo para todos los roles**. Esto simplifica el componente de navegación y refuerza la sensación de transparencia del sistema. Lo único que se oculta condicionalmente son botones de acción dentro de cada pantalla.

---

## Por qué

- **Cultural**: refleja la transparencia real de la organización. Coherente con la frase del usuario: *"evitar manazas pero no ojos"*.
- **Operativo**: el conocimiento del sistema circula. Mitiga el riesgo identificado en S01 de la presentación POC: *"el conocimiento acumulado se va con las personas"*. Un técnico que ve cómo están configuradas las reglas del motor puede aprenderlas y, llegado el caso, suceder a quien las mantenga.
- **Técnico**: simplifica el código (menos paths de redirect "no permitido"), elimina flashes y mensajes feos al toparse con bloqueos. La UI condicionando botones es el patrón estándar.
- **Coherente con ADR-012**: extiende la filosofía de "actuar sí, pero con traza" al resto del sistema en lugar de ser una excepción puntual.
- **Habilitante del revamping (fase 4)**: el sidebar puede ser único, las pantallas administrativas pueden formar parte de la navegación normal sin lógica condicional de visibilidad, y el rediseño no hereda redirects de la lógica restrictiva antigua.

---

## Cómo implementar

1. Refactor del dict `PERMISOS` en `app/utils/permisos.py` añadiendo los pares `acceder_X` + `gestionar_X`. Mantener los `gestionar_X` ya existentes para no romper, eliminar los wrappers de compatibilidad cuando ya no haya call sites.
2. Refactor de decoradores en endpoints administrativos:
   - `admin_plantillas`: `listado`/`detalle`/`descargar` → `acceder_plantillas`; `nueva`/`editar`/`activar` → `gestionar_plantillas`.
   - `usuarios`: `index`/`detalle` → `acceder_usuarios`; `editar`/`toggle_estado` → `gestionar_usuarios`.
   - (Cuando existan UIs CRUD, #170/#171: reglas_motor, catalogo_plazos, tablas maestras análogo.)
3. Envolver botones de acción en templates con `{% if tiene_permiso('gestionar_X') %}`.
4. Introducir helper `puedo_ver_dni(entidad)` y aplicar en plantillas que muestren DNI de Usuario/Entidad.
5. Exponer `tiene_permiso` al contexto Jinja vía `@app.context_processor`.
6. Test pytest mínimo: verificar que TRAMITADOR puede entrar a `/admin/plantillas` (GET 200) pero no puede editar (POST 403).
7. Verificación manual con Playwright MCP: cada rol ve las pantallas administrativas y los botones correctos.

---

## Alternativa descartada

**Mantener el modelo restrictivo actual y solo añadir excepciones puntuales por área.**

Descartada: cada nueva pantalla obligaba a decidir si era visible o no, generaba decisiones inconsistentes a lo largo del tiempo, y el patrón general acababa siendo "restrictivo por defecto" con un parche por aquí y otro por allá. Más simple y honesto **invertir la presunción**: visible por defecto, restringido por excepción documentada en este ADR.

Además, el modelo restrictivo es incompatible con el sidebar único decidido para el revamping (fase 4) — habría que generar sidebars distintos por rol, complicando el componente sin beneficio real.
