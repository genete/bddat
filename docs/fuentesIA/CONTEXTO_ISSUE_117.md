# Contexto Issue #117 — Migrar vistas legacy a base_fullwidth.html

**Issue:** #117 — Migrar vistas legacy a base_fullwidth.html y eliminar base.html
**Estado:** Planificado, pendiente de implementación
**Rama a crear:** `feature/117-migrar-base-fullwidth` desde `develop`

---

## Por qué existe este issue

Tras el PR #116 (Fase 3 navegación contextual), `expedientes/detalle.html` ya fue migrado
a `base_fullwidth.html`. Sin embargo, quedan 6 templates activos usando `base.html` (layout
legacy: navbar Bootstrap verde, CDN Junta antigua, sin module-nav ni breadcrumb V2).

La decisión de qué layout base usar quedó establecida en los PR #114/#115 (Issue #93):
- **Vistas generales:** `layout/base_fullwidth.html`
- **Vista tramitación V3:** `layout/base_acordeon.html`
- **Login:** `layout/base_login.html`
- **base.html** → deprecated, debe desaparecer

---

## Estado actual del código

### Templates activos con base.html (los 6 a migrar)

| Template | Ruta Flask | Blocks usados | Variables de contexto |
|----------|-----------|---------------|----------------------|
| `app/templates/proyectos/index.html` | `/proyectos/` | title, content, extra_js | proyectos, tipos_ia, provincias, responsables, filtros_activos, sort_by, order |
| `app/templates/proyectos/detalle.html` | `/proyectos/<id>` | title, content | proyecto |
| `app/templates/usuarios/index.html` | `/usuarios/` | title, content | usuarios, roles, form_data?, error_siglas?, error_email?, show_modal? |
| `app/templates/usuarios/editar.html` | `/usuarios/<id>/editar` | title, content | usuario, roles, error_siglas?, error_email?, form_data? |
| `app/templates/perfil/index.html` | `/perfil` | title, content | usuario (= current_user) |
| `app/modules/expedientes/templates/expedientes/editar.html` | `/expedientes/<id>/editar` | title, content | expediente, tipos_expedientes, tipos_ia, usuarios |

### Templates huérfanos (no renderizados por ninguna ruta)

- `app/templates/dashboard/index.html` → dashboard usa `dashboard/index_v1.html`
- `app/templates/auth/login.html` → auth usa `auth/login_v0.html`

### Ficheros de rutas relevantes

| Ruta | Blueprint | Fichero |
|------|-----------|---------|
| `/proyectos/` | proyectos | `app/routes/proyectos.py` |
| `/usuarios/` | usuarios | `app/routes/usuarios.py` |
| `/perfil` | perfil | `app/routes/perfil.py` |
| `/expedientes/<id>/editar` | expedientes | `app/modules/expedientes/routes.py` |

---

## Patrón de migración

### Cambio base en todos los templates

```jinja2
{# ANTES #}
{% extends 'base.html' %}

{# DESPUÉS #}
{% extends 'layout/base_fullwidth.html' %}
```

### Añadir breadcrumb (nuevo bloque page_breadcrumb)

```jinja2
{% block page_breadcrumb %}
<nav aria-label="breadcrumb" class="px-4 py-2 bg-light border-bottom">
    <ol class="breadcrumb mb-0">
        <li class="breadcrumb-item">
            <a href="{{ url_for('dashboard.index') }}">Inicio</a>
        </li>
        {# niveles adicionales según la vista #}
        <li class="breadcrumb-item active">Nombre de la vista</li>
    </ol>
</nav>
{% endblock %}
```

### Adaptar el bloque content

```jinja2
{# ANTES: base.html inyecta en <main class="container flex-grow-1"> #}
{% block content %}
<div class="container">   {# ← ELIMINAR este container #}
    ...contenido...
</div>
{% endblock %}

{# DESPUÉS: base_fullwidth.html inyecta en <main class="app-main"> #}
{% block content %}
<div class="p-4">   {# ← padding directo, sin container Bootstrap #}
    ...contenido...
</div>
{% endblock %}
```

### Cambio en extra_js

```jinja2
{# ANTES #}
{% block extra_js %}
<script>...</script>
{% endblock %}

{# DESPUÉS — llamar super() para incluir Bootstrap bundle y toasts #}
{% block extra_js %}
{{ super() }}
<script>...</script>
{% endblock %}
```

---

## Breadcrumbs por template

| Template | Breadcrumb |
|----------|-----------|
| `proyectos/index.html` | Inicio › Proyectos |
| `proyectos/detalle.html` | Inicio › Proyectos › {{ proyecto.titulo }} |
| `usuarios/index.html` | Inicio › Usuarios |
| `usuarios/editar.html` | Inicio › Usuarios › Editar |
| `perfil/index.html` | Inicio › Mi Perfil |
| `expedientes/editar.html` | Inicio › Expedientes › AT-{{ expediente.numero_at }} › Editar |

---

## Particularidades importantes

### proyectos/index.html
- Tiene tabla con ordenación (`sort_by`, `order`) y filtros activos
- Si usa `{% block extra_js %}`, añadir `{{ super() }}` al principio

### usuarios/index.html
- Contiene modal Bootstrap para crear usuario — funciona con base_fullwidth sin cambios
- Variable `show_modal` puede auto-abrir el modal — mantener lógica JS

### usuarios/editar.html
- Formulario con validación server-side (`form_data`, `error_siglas`, `error_email`)
- Los mensajes de error deben seguir funcionando tras la migración

### expedientes/editar.html
- Está en `app/modules/expedientes/templates/` (template_folder del blueprint)
- El botón Cancelar ya está corregido (vuelve a detalle, PR anterior)
- Tiene acceso a `expediente.numero_at` para el breadcrumb

---

## Plan de implementación

### Commit 1: Proyectos
```
[TEMPLATE] #117 proyectos: migrar index + detalle a base_fullwidth
```
Ficheros: `app/templates/proyectos/index.html`, `app/templates/proyectos/detalle.html`

### Commit 2: Usuarios
```
[TEMPLATE] #117 usuarios: migrar index + editar a base_fullwidth
```
Ficheros: `app/templates/usuarios/index.html`, `app/templates/usuarios/editar.html`

### Commit 3: Perfil + Expedientes editar
```
[TEMPLATE] #117 perfil y expedientes/editar: migrar a base_fullwidth
```
Ficheros: `app/templates/perfil/index.html`, `app/modules/expedientes/templates/expedientes/editar.html`

### Commit 4: Eliminar legacy
```
[TEMPLATE] #117 Eliminar base.html y templates huérfanos legacy
```
Ficheros a borrar: `app/templates/base.html`, `app/templates/dashboard/index.html`, `app/templates/auth/login.html`

---

## Verificación

1. Arrancar servidor y navegar a cada URL:
   - `/proyectos/` — module-nav activo en "Proyectos", breadcrumb visible
   - `/proyectos/<id>` — breadcrumb con título del proyecto
   - `/usuarios/` — modal crear usuario funciona, module-nav activo
   - `/usuarios/<id>/editar` — formulario con errores server-side funciona
   - `/perfil` — breadcrumb "Inicio › Mi Perfil"
   - `/expedientes/<id>/editar` — breadcrumb correcto, cancelar vuelve a detalle
2. Verificar que base.html ya no es usado:
   `grep -r "extends 'base.html'" app/` → resultado vacío
3. Confirmar que las vistas no migradas siguen funcionando:
   - `/auth/login` → usa `login_v0.html` (base_login)
   - `/dashboard` → usa `index_v1.html` (base_fullwidth ya)

---

## Notas adicionales

- `base_fullwidth.html` incluye `header.html` que ya tiene breadcrumb automático de módulo
  (`Inicio › {módulo activo}`). El `page_breadcrumb` añade niveles adicionales cuando se necesita
- El system `inject_module_nav()` (context processor) funciona en todas las rutas autenticadas
- No eliminar `base_login.html` ni `base_acordeon.html` (siguen en uso)
- PRs siempre contra `develop`, no contra `main`
- Issues a cerrar con `Closes #117` en inglés en el PR
