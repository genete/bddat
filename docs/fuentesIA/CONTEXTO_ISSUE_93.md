# Contexto Issue #93 — Epic Sistema de Navegación UI Modular (CERRADO)

**Estado:** CERRADO ✅
**Fecha cierre:** 2026-02-19
**PRs mergeados a develop:** #108, #110, #114, #115

---

## Resumen de fases completadas

### Fase 1+2 — Prototipo HTML + Integración backend (PRs #108 + #110)
- Vista V0 (Login), V1 (Dashboard), V2 (Listado scroll infinito)
- API REST expedientes con paginación cursor
- CSS sistema V2: `v2-theme.css`, `v2-layout.css`, `v2-components.css`
- Base templates: `base_fullwidth.html`, `base_acordeon.html`, `base_login.html`

### Fase 3 — Refactoring modular (PR #114)
- Limpieza templates y rutas legacy pre-wizard
- Creación `app/modules/` con `ModuleRegistry`
- Migración blueprint `expedientes` a `app/modules/expedientes/`
- Migración blueprint `entidades` a `app/modules/entidades/`
- Templates movidos junto al módulo (`template_folder='templates'`)
- Fix `base.html`: referencias rotas a `expedientes.index` → `listado_v2`

### Fase 4 — Sistema metadata-driven (PR #115)
- `ModuleRegistry`: auto-discovery por escaneo de `app/modules/`
- `get_metadata()` con caché, `get_navigation(user_roles)` con filtro de permisos
- Context processor `inject_module_nav()` → inyecta `module_nav` y `active_module`
- `header.html` + `base_acordeon.html`: nav de módulos + breadcrumb automático
- CSS `.module-nav` / `.module-nav-link` en `v2-layout.css`

---

## Estructura final resultante

```
app/modules/
├── __init__.py              ← ModuleRegistry (auto-discovery + metadata)
├── expedientes/
│   ├── routes.py            ← Blueprint activo (template_folder='templates')
│   ├── metadata.json        ← order:10, permisos, navigation.route
│   └── templates/expedientes/
│       ├── listado_v2.html
│       ├── tramitacion_v3.html
│       ├── detalle.html     ← pendiente actualizar con campos wizard (#TBD)
│       └── editar.html      ← pendiente actualizar con campos wizard (#TBD)
└── entidades/
    ├── routes.py
    ├── metadata.json        ← order:20, permisos, navigation.route
    └── templates/entidades/
        ├── index.html
        ├── nueva.html
        └── detalle.html
```

## Patrón para añadir un módulo nuevo
1. Crear `app/modules/<nombre>/`
2. Crear `routes.py` con `bp = Blueprint(...)` y `template_folder='templates'`
3. Crear `metadata.json` con `order`, `permissions`, `navigation.route`
4. Crear `templates/<nombre>/`
5. **Sin tocar código central** — `ModuleRegistry` lo descubre automáticamente

---

## Deuda técnica pendiente (issues a crear)

- `detalle.html` y `editar.html` de expedientes muestran campos pre-wizard incompletos.
  Falta: tipo expediente, titular, tramitador, heredado, municipios, proyecto.
- Filtro `mis_expedientes` (tramitador ve solo los suyos): `listado_v2` no lo implementa.
  El filtro era de `index()` (eliminada). Pendiente en API.
- `base.html` (legacy): solo la usan `detalle.html` y `editar.html`. Candidato a
  eliminar cuando esas páginas se actualicen al sistema V2.

---

## Referencias
- Issue #93: https://github.com/genete/bddat/issues/93 (CERRADO)
- Siguiente bloque: issue #61 Fase 3 → ver `CONTEXTO_ISSUE_61_FASE3.md`
