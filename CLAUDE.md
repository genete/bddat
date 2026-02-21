# CLAUDE.md — Proyecto BDDAT

## Contexto del Proyecto
Sistema de tramitación de expedientes de autorización de instalaciones de alta tensión.
Desarrollado para la Consejería de Industria, Energía y Minas (Junta de Andalucía).
Licencia: EUPL v1.2

**Stack:** Python 3.x + Flask + SQLAlchemy + PostgreSQL + Bootstrap 5.3 + Jinja2
**Fase actual:** Fase 2 — Interfaz de Usuario (sin restricciones de lógica de negocio activas)
**Rama de trabajo:** `develop`

---

## Documentos de referencia obligatorios

Antes de cualquier tarea de desarrollo, leer:

- `docs/fuentesIA/REGLAS_DESARROLLO.md` — workflow Git, commits, ramas, migraciones
- `docs/fuentesIA/GuiaGeneralNueva.md` — arquitectura general y lógica de negocio
- `docs/GUIA_VISTAS_BOOTSTRAP.md` — referencia principal para desarrollo UI
- `docs/fuentesIA/Estructura_fases_tramites_tareas.json` — lógica de tramitación administrativa

---

## Convenciones de Nomenclatura

- **Clases SQLAlchemy:** `CamelCase` (ej: `ExpedienteAT`, `TipoInstalacion`)
- **Tablas y campos BD:** `snake_case` con `schema='public'` explícito
- **Variables, funciones, métodos Python:** `snake_case` en español
- **Variables JavaScript:** `snake_case` en español
- **Rutas Flask:** kebab-case en español (ej: `/expedientes/nuevo`)
- **Nombres de fichero:** `snake_case` en español

---

## Estructura del Proyecto

```
bddat/
├── app/
│   ├── __init__.py          ← Factory pattern, registro de blueprints
│   ├── config.py            ← DevelopmentConfig / ProductionConfig
│   ├── decorators.py        ← @role_required('ADMIN', 'SUPERVISOR', ...)
│   ├── models/
│   │   ├── __init__.py      ← ORDEN DE IMPORTS CRÍTICO (ver abajo)
│   │   ├── expedientes.py   ← Modelo raíz + signal after_insert
│   │   ├── usuarios.py      ← UserMixin, Rol, tabla usuarios_roles
│   │   └── ...
│   ├── routes/
│   │   ├── api_expedientes.py    ← Blueprint 'api', prefijo /api
│   │   ├── wizard_expediente.py  ← Blueprint multi-paso con sesión Flask
│   │   └── ...
│   ├── templates/
│   │   └── layout/
│   │       ├── base_fullwidth.html    ← Base principal (header+main+footer)
│   │       ├── base_acordeon.html     ← Vista V3 tramitación
│   │       ├── base_login.html        ← Vista V0 login
│   │       └── base_tramitacion.html  ← Vista V3 con sidebar (legacy)
│   └── static/
│       ├── css/v2-theme.css           ← Variables CSS corporativas Junta
│       ├── css/v2-layout.css          ← Grid A/B/C (app-container)
│       ├── css/v2-components.css      ← Componentes reutilizables
│       └── css/custom.css             ← Toasts, hover effects
├── migrations/              ← Alembic — NO editar manualmente
├── docs/
│   └── fuentesIA/           ← Documentos de referencia para IA
├── run.py
└── .env                     ← NUNCA commitear
```

---

## Arquitectura de Modelos

### Orden de imports en `app/models/__init__.py` — CRÍTICO
Respetar siempre el orden establecido: primero modelos sin FKs operacionales,
luego modelos con dependencias simples, luego dependencias múltiples.
Modificar este orden puede causar errores de circular import.

### Relaciones clave
```
Expediente (1:1) → Proyecto
Expediente (1:N) → Solicitud → Fase → Tramite → Tarea
Expediente → titular_id (snapshot de Entidad, desnormalizado)
Expediente → HistoricoTitularExpediente (signal after_insert automático)
Usuario (N:M) → Rol (tabla usuarios_roles)
```

### Schema PostgreSQL
Todas las tablas usan `schema='public'` explícito.
Las FK deben referenciar con prefijo: `db.ForeignKey('public.tabla.campo')`

---

## Blueprints Registrados

| Blueprint | Variable | Prefijo URL |
|-----------|----------|-------------|
| auth | bp | /auth |
| dashboard | bp | /dashboard |
| expedientes | bp | /expedientes |
| proyectos | bp | /proyectos |
| usuarios | bp | /usuarios |
| perfil | bp | /perfil |
| entidades | bp | /entidades |
| wizard_expediente | bp | /expedientes/wizard |
| api_expedientes | api_bp | /api |
| api_municipios | bp | /api/municipios |
| vista3 | bp | /vista3 |
| api_entidades | api_entidades_bp | /api/entidades |

**Atención:** Los blueprints usan nombres de variable distintos (`bp`, `api_bp`, `api_entidades_bp`).
Comprobar siempre en el fichero de ruta antes de importar.

---

## Roles del Sistema

`ADMIN`, `SUPERVISOR`, `TRAMITADOR`, `ADMINISTRATIVO`

Usar siempre el decorador de `app/decorators.py`:
```python
@role_required('ADMIN', 'SUPERVISOR')
```

---

## Layout y CSS — Sistema V2

La arquitectura de layout tiene 3 niveles:
- **A:** `.app-container` (grid 3 filas: header / main / footer)
- **B:** `.app-header`, `.app-main`, `.app-footer`
- **C:** `.lista-cabecera` (fijo), `.lista-scroll-container` (scroll interno), contenido adicional

**Bases disponibles:**
- `base_fullwidth.html` — uso general
- `base_acordeon.html` — Vista V3 tramitación (sin sidebar)
- `base_login.html` — autenticación

**IMPORTANTE:** Antes de crear cualquier nueva vista, leer `docs/GUIA_VISTAS_BOOTSTRAP.md`.

**Bootstrap:** Cargado siempre desde CDN oficial. Versión 5.3.2.
Font Awesome 6.5.1 para iconos (no Bootstrap Icons excepto en base_fullwidth.html).

---

## Notificaciones al Usuario

Sistema de toasts Flask (`flash messages`) definido en `base_fullwidth.html`.
Categorías: `success`, `danger`, `warning`, `info`.
Estilos en `app/static/css/custom.css`.
**No usar modales para notificaciones** salvo riesgo de pérdida de datos.

---

## APIs REST

Patrón establecido en `api_expedientes.py`:
- Paginación por cursor (no por OFFSET)
- Parámetros: `cursor`, `limit` (máx 100), `search` (mín 2 chars), filtros opcionales
- Respuesta: `{ data, next_cursor, has_more, total? }`
- Serializar siempre campo `codigo` como `AT-{numero_at}` para expedientes

---

## Wizard Multi-Paso

Patrón establecido en `wizard_expediente.py`:
- Datos de pasos intermedios guardados en sesión Flask con clave `SESSION_KEY`
- Helpers: `_get_wizard()`, `_save_wizard(data)`, `_reset_wizard()`
- Commit transaccional completo solo en el último paso
- Usar `db.session.flush()` para obtener IDs antes del commit final

---

## Migraciones de Base de Datos — REGLA CRÍTICA

**NUNCA usar migraciones automáticas** (`flask db migrate`).
Alembic tiene un bug conocido con `include_schemas` que regenera todas las FK.

**Procedimiento obligatorio:**
```powershell
# 1. Crear migración vacía
flask db revision -m "Descripción del cambio"

# 2. Editar manualmente el archivo en migrations/versions/
#    Solo añadir los cambios necesarios (add_column, create_table...)
#    NO tocar FK existentes

# 3. Aplicar
flask db upgrade

# 4. Verificar
flask run
```

---

## Workflow Git

**Rama por defecto:** `develop`

**Commits:**
```
[MODELO] Añadir campo observaciones a Fase
[RUTA]   Implementar endpoint GET /expedientes/<id>
[MIGA]   Añadir campo fecha_fin a tramites
[DOCS]   Actualizar GuiaGeneralNueva con lógica de fases
```
Categorías: `[BD]`, `[MODELO]`, `[RUTA]`, `[TEMPLATE]`, `[STYLE]`, `[MIGA]`, `[TEST]`, `[DOCS]`

**Ramas temporales** (para cambios complejos con testing):
`feature/issue-XX-descripcion`, `bugfix/issue-XX-descripcion`

**Cambios simples** (docs, typos, 1-2 ficheros): commit directo en `develop`.

Leer `docs/fuentesIA/REGLAS_DESARROLLO.md` para el workflow completo.

---

## Herramientas MCP Disponibles

- **PostgreSQL MCP** — consultar esquema real de BD en desarrollo
- **Playwright MCP** — testing e interacción automática con navegador
- **Windows MCP** — redimensionado de ventanas
- **GitHub MCP** — gestión de issues, PRs y ramas

---

## Seguridad y Datos Sensibles

- Credenciales siempre en `.env` (nunca en código ni commiteadas)
- Mantener cabeceras de licencia EUPL v1.2 en ficheros relevantes
- Proyecto sometido a ENS (Esquema Nacional de Seguridad)
- `db.drop_all()` y `db.create_all()` prohibidos en producción

---

## Estado actual del desarrollo

**Último PR mergeado:** #101 — Vista V3 Fase 1 (acordeón Bootstrap)
**En curso:** Vista V3 Fase 2 — Issue #101
**Rama activa:** develop
**Próximo hito:** Completar Vista V3 Tramitación

---

## Qué está y no está implementado

**Completado:**
- Vista V0 (Login), V1 (Dashboard), V2 (Listado con scroll infinito)
- Autenticación Flask-Login + RBAC
- CRUD Expedientes, Usuarios, Entidades
- Wizard de creación de expedientes (3 pasos)
- API REST expedientes (paginación cursor)
- Sistema de toasts/flash messages

**En desarrollo:**
- Vista V3 Tramitación (Fase 1 completada, acordeón Bootstrap 5)

**Pendiente (Fase 3):**
- Motor de reglas de negocio (lógica de tramitación administrativa)
- Restricciones basadas en tipos de expediente/solicitud/fase
