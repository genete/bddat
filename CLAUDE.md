# CLAUDE.md — Proyecto BDDAT

## Contexto del Proyecto
Sistema de tramitación de expedientes de autorización de instalaciones de alta tensión.
Desarrollado para la Consejería de Industria, Energía y Minas (Junta de Andalucía).
Licencia: EUPL v1.2

**Stack:** Python 3.x + Flask + SQLAlchemy + PostgreSQL + Bootstrap 5.3 + Jinja2
**Fase actual:** Fase 2 — Interfaz de Usuario (evaluador motor de reglas activo desde #152)
**Rama de trabajo:** `develop`

---

## Documentos de referencia obligatorios

Antes de cualquier tarea de desarrollo, leer:

- `docs/fuentesIA/REGLAS_DESARROLLO.md` — workflow Git, commits, ramas, migraciones
- `docs/fuentesIA/GuiaGeneralNueva.md` — arquitectura general y lógica de negocio
- `docs/GUIA_VISTAS_BOOTSTRAP.md` — referencia principal para desarrollo UI
- `docs/GUIA_COMPONENTES_INTERACTIVOS.md` — catálogo de componentes JS reutilizables
- `docs/fuentesIA/Estructura_fases_tramites_tareas.json` — lógica de tramitación administrativa
- `docs/fuentesIA/ROADMAP.md` — estado actual de implementación
- `docs/fuentesIA/ARQUITECTURA_DOCUMENTOS.md` — decisiones arquitectónicas del subsistema documental

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
│   ├── __init__.py
│   ├── config.py
│   ├── decorators.py
│   ├── models/
│   │   ├── __init__.py      ← ORDEN DE IMPORTS CRÍTICO
│   │   └── ...
│   ├── modules/             ← Blueprints con template_folder propio
│   │   ├── expedientes/
│   │   ├── proyectos/
│   │   └── entidades/
│   ├── routes/              ← Blueprints simples (usan app/templates/ global)
│   │   ├── api_expedientes.py
│   │   ├── vista3.py
│   │   └── ...
│   ├── services/            ← Lógica de negocio desacoplada de rutas
│   │   └── motor_reglas.py
│   ├── templates/
│   │   └── layout/
│   │       ├── base_fullwidth.html
│   │       ├── base_acordeon.html
│   │       └── base_login.html
│   └── static/
│       └── css/
├── migrations/
├── docs/
│   └── fuentesIA/
├── run.py
└── .env                     ← NUNCA commitear
```

---

## Convención de Templates (#127)

**Regla:** Los blueprints en `app/modules/` declaran `template_folder='templates'`
(carpeta propia del módulo). Los blueprints en `app/routes/` usan la carpeta global
`app/templates/`. **No mezclar.**

- `app/modules/X/templates/X/` → templates del módulo X (prioridad más alta)
- `app/templates/` → templates globales (layout, auth, dashboard, vistas compartidas)

Si un módulo declara `template_folder` pero no tiene el template en su carpeta propia,
Flask hace fallback a `app/templates/`. **Verificar siempre** que el template correcto
está en la carpeta del módulo.

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
| vista3 | bp | /api/vista3 |
| api_entidades | api_entidades_bp | /api/entidades |

**Atención:** Los blueprints usan nombres de variable distintos (`bp`, `api_bp`, `api_entidades_bp`).
Comprobar siempre en el fichero de ruta antes de importar.

---

## Roles del Sistema

`ADMIN`, `SUPERVISOR`, `TRAMITADOR`, `ADMINISTRATIVO` — usar `@role_required('ADMIN', ...)` de `app/decorators.py`.

---

## Layout y CSS — Sistema V2

Niveles: `.app-container` → `.app-header/.app-main/.app-footer` → `.lista-cabecera` + `.lista-scroll-container`.
**Bases:** `base_fullwidth.html` (general), `base_acordeon.html` (V3), `base_login.html`.
**IMPORTANTE:** Leer `docs/GUIA_VISTAS_BOOTSTRAP.md` antes de crear cualquier vista.
**Bootstrap 5.3.3** + Font Awesome 6.5.1 — CDN Junta de Andalucía.
Toasts Flask (`flash messages`): categorías `success`, `danger`, `warning`, `info`. No usar modales para notificaciones.

---

## APIs REST

Patrón (`api_expedientes.py`): paginación por cursor, params `cursor/limit(máx 100)/search(mín 2)`,
respuesta `{ data, next_cursor, has_more, total? }`, campo `codigo` serializado como `AT-{numero_at}`.

---

## Migraciones de Base de Datos — REGLA CRÍTICA

**NUNCA usar migraciones automáticas** (`flask db migrate`).
Alembic tiene un bug conocido con `include_schemas` que regenera todas las FK.

**Procedimiento obligatorio:**
```powershell
flask db revision -m "Descripción"   # 1. Crear migración vacía
# 2. Editar manualmente migrations/versions/<rev>.py
flask db upgrade                      # 3. Aplicar
flask run                             # 4. Verificar
```

---

## Workflow Git

**Rama por defecto:** `develop`
**Categorías de commit:** `[BD]`, `[MODELO]`, `[RUTA]`, `[TEMPLATE]`, `[STYLE]`, `[MIGA]`, `[TEST]`, `[DOCS]`, `[SERVICIO]`

**Ramas temporales** (cambios complejos): `feature/issue-XX-descripcion`, `bugfix/issue-XX-descripcion`
**Cambios simples** (docs, typos, 1-2 ficheros): commit directo en `develop`.

Leer `docs/fuentesIA/REGLAS_DESARROLLO.md` para el workflow completo.

---

## Herramientas MCP Disponibles

- **PostgreSQL MCP** — consultar esquema real de BD en desarrollo
- **Playwright MCP** — testing e interacción automática con navegador
  - Sin nombre de fichero → auto-genera `page-TIMESTAMP.png` en `.playwright-mcp/` (correcto)
  - Con nombre personalizado → guarda relativo al CWD (repo root). **SIEMPRE** prefijar:
    `.playwright-mcp/nombre.png` para mantenerlos fuera del árbol git.
- **Windows MCP** — redimensionado de ventanas

---

## Seguridad y Datos Sensibles

- Credenciales siempre en `.env` (nunca en código ni commiteadas)
- Mantener cabeceras de licencia EUPL v1.2 en ficheros relevantes
- Proyecto sometido a ENS (Esquema Nacional de Seguridad)
- `db.drop_all()` y `db.create_all()` prohibidos en producción

---

## Convenciones Bash (anti-bloqueos del parser)

Los checks de seguridad de Claude Code son **hardcoded** y no los desactiva la allowlist.
Evitarlos cambiando el patrón:

| Aviso | Causa | Solución |
|-------|-------|----------|
| output redirection `>` | `cmd > fichero` | Usar tool `Write` |
| command contains newlines | heredoc en Bash | Escribir con `Write` → pasar como fichero |
| quoted newline + `#`-line | `## Header` dentro de heredoc | Ídem (fichero temporal) |
| quoted chars in flag names | comillas dentro de `--body "..."` | Ídem (fichero temporal) |
| backticks `` ` `` | sustitución de comandos | Separar en llamadas Bash secuenciales |

### Ficheros temporales — ruta obligatoria

En Windows, `/tmp/` no es fiable: la tool `Write` y `bash` (MSYS2) pueden resolver
a rutas distintas, causando que `git commit -F` o `gh pr create --body-file` lean
contenido obsoleto. **Usar siempre ruta absoluta dentro del repo:**

```
D:\BDDAT\docs_prueba\temp\   ← ignorado por .gitignore (docs_prueba/)
```

Ejemplo: `Write` a `D:\BDDAT\docs_prueba\temp\commit_msg.txt`,
luego `git -C /d/BDDAT commit -F docs_prueba/temp/commit_msg.txt`.
Borrar el fichero tras uso con `rm`.

### Patrones concretos obligatorios

- **cd + git:** usar SIEMPRE `git -C /ruta` — NUNCA `cd /ruta && git`
- **`$()` y backticks:** NUNCA — separar en llamadas Bash secuenciales o usar fichero temporal
- **cd + redirección / escritura:** separar en dos llamadas Bash distintas
- **`gh issue create` / `gh pr create`:** escribir el body con `Write` a `docs_prueba/temp/gh_body.md`,
  luego `gh pr create --body-file /d/BDDAT/docs_prueba/temp/gh_body.md ...`
- **`git commit`:** escribir el mensaje con `Write` a `docs_prueba/temp/commit_msg.txt`,
  luego `git -C /d/BDDAT commit -F docs_prueba/temp/commit_msg.txt`
