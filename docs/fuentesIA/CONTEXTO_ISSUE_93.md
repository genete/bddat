# Contexto Issue #93 — Sprint Fase 3: Refactoring Modular

**Fecha sesión:** 2026-02-19
**Rama activa:** `feature/93-fase3-refactoring-modular`
**Tag de partida:** `v0.4.0` (creado al inicio del sprint)

---

## Lo que llevamos hecho en esta sesión

### Previo al sprint (mini-sprint bugs)
- **Bug #109** (commit `b051278`): Creados templates `errors/404.html` y `errors/500.html` + favicon vacío en bases. Probado con Playwright — OK.
- **Bug #113** (commit `4bde7e8`): Wizard guarda `request.referrer` como `origen` en sesión; `cancelar()` vuelve al origen. Probado con Playwright desde listado y desde dashboard — OK.
- Push de ambos commits a `origin/develop`.

### Sprint #93 Fase 3
- **Paso 0** (commit implícito en rama): Tag `v0.4.0` creado y subido. Rama `feature/93-fase3-refactoring-modular` creada desde `develop`.
- **Paso 1** (commit `1593a27`): Limpieza legacy completada.

---

## Ficheros modificados y por qué

### Paso 1 — Limpieza legacy

| Fichero | Acción | Motivo |
|---------|--------|--------|
| `app/routes/expedientes.py` | Modificado | Eliminadas funciones `index()` y `nuevo()` (sustituidas por `listado_v2` y wizard). Eliminado import `current_user` (ya no se usa directamente). Actualizado docstring. |
| `app/routes/dashboard.py` | Modificado | `mis_expedientes()` redirigía a `expedientes.index` → actualizado a `expedientes.listado_v2` |
| `app/utils/permisos.py` | Modificado | `verificar_acceso_expediente()` redirigía a `expedientes.index` → actualizado a `expedientes.listado_v2` |
| `app/templates/expedientes/detalle.html` | Modificado | Botón "Volver" apuntaba a `expedientes.index` → actualizado a `expedientes.listado_v2` |
| `app/templates/expedientes/editar.html` | Modificado | Botón "Cancelar" apuntaba a `expedientes.index` → actualizado a `expedientes.listado_v2` |
| `app/templates/expedientes/index.html` | **Eliminado** | Template pre-wizard, heredaba de `base.html` (obsoleto) |
| `app/templates/expedientes/nuevo.html` | **Eliminado** | Template pre-wizard, reemplazado por el wizard de 3 pasos |
| `app/templates/layout/base_full_width.html` | **Eliminado** | Duplicado de `base_fullwidth.html` con guión bajo, nadie lo heredaba |
| `app/templates/layout/base_tramitacion.html` | **Eliminado** | Marcado legacy en CLAUDE.md, nadie lo heredaba |

---

## Decisiones tomadas

1. **Opción A para `detalle.html` y `editar.html`**: Se migran tal cual (incompletas) al módulo. Se abre issue separado para actualizarlas con los campos completos del wizard.

2. **`metadata.json` — esquema mínimo para Fase 3**:
```json
{
  "module": "expedientes",
  "name": "Expedientes",
  "icon": "fa-folder-open",
  "order": 10,
  "permissions": {
    "list": ["ADMIN", "SUPERVISOR", "TRAMITADOR", "ADMINISTRATIVO"],
    "create": ["ADMIN", "SUPERVISOR", "TRAMITADOR"],
    "edit": ["ADMIN", "SUPERVISOR", "TRAMITADOR"],
    "delete": ["ADMIN"]
  },
  "navigation": {
    "label": "Expedientes",
    "route": "expedientes.listado_v2"
  }
}
```

3. **`ModuleRegistry`**: Registro manual en Fase 3. Auto-discovery queda para Fase 4.

4. **Alcance de módulos**: Solo `expedientes` y `entidades` en esta fase. El resto de blueprints (`auth`, `dashboard`, `usuarios`, `perfil`, `proyectos`, `vista3`, APIs) se quedan en `app/routes/`.

5. **Modelos**: No se mueven. Permanecen en `app/models/`.

6. **Vista V3** (`tramitacion_v3`): Ya existe y funciona en `/expedientes/<id>/tramitacion_v3`. Confirmado con Playwright en expediente id=104.

---

## Problemas pendientes / abiertos

- **Issue a crear**: Actualizar `detalle.html` y `editar.html` con campos completos del wizard (tipo expediente, titular, tramitador, heredado, municipios, proyecto). Actualmente muestran campos pre-wizard incompletos.

- **`mis_expedientes`**: La ruta `/mis_expedientes` ahora redirige a `listado_v2` pero sin filtro por usuario (el filtro era de `index()`). Queda pendiente implementar filtrado en `listado_v2` / API. Anotarlo como deuda técnica.

- **`base.html`**: Existe en `app/templates/base.html` y sigue referenciando `expedientes.index`. No se ha tocado porque solo la usan los templates legacy ya eliminados. Verificar si puede eliminarse también en el Paso 2.

---

## Próximo paso exacto para continuar

**Paso 2 — Crear estructura `app/modules/` con `ModuleRegistry` manual**

1. Crear `app/modules/__init__.py` con clase `ModuleRegistry`:
   - Registro manual de módulos (lista explícita)
   - Método `register_all(app)` que registra los blueprints de cada módulo

2. Crear esqueleto de directorios:
```
app/modules/
├── __init__.py          ← ModuleRegistry
├── expedientes/
│   ├── __init__.py
│   ├── metadata.json
│   ├── routes.py        (vacío por ahora, se rellena en Paso 3)
│   └── templates/
│       └── expedientes/
└── entidades/
    ├── __init__.py
    ├── metadata.json
    ├── routes.py        (vacío por ahora, se rellena en Paso 4)
    └── templates/
        └── entidades/
```

3. Actualizar `app/__init__.py` para usar `ModuleRegistry` en paralelo a los blueprints existentes (sin romper nada todavía).

---

## Referencias

- Issue #93: https://github.com/genete/bddat/issues/93
- Rama: `feature/93-fase3-refactoring-modular`
- Tag checkpoint: `v0.4.0`
- Plan de trabajo completo: `memory/plan_trabajo.md`
