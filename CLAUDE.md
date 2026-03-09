# CLAUDE.md — Proyecto BDDAT

## Contexto del Proyecto
Sistema de tramitación de expedientes de autorización de instalaciones de alta tensión.
Desarrollado para la Consejería de Industria, Energía y Minas (Junta de Andalucía).

**Stack:** Python 3.x + Flask + SQLAlchemy + PostgreSQL + Bootstrap 5.3

---

## Documentos de referencia

Índice completo de documentación: `docs/README.md`

Leer **siempre** antes de actuar:
- `docs/fuentesIA/REGLAS_DESARROLLO.md` — workflow Git, commits, ramas, migraciones (reglas que debo seguir)
- `docs/GUIA_VISTAS_BOOTSTRAP.md` — antes de crear cualquier vista
- `docs/GUIA_COMPONENTES_INTERACTIVOS.md` — antes de implementar cualquier componente JS

---

## Convención de Templates (#127)

- `app/modules/X/` → blueprint con `template_folder` propio → templates en `app/modules/X/templates/X/`
- `app/routes/` → sin `template_folder` → templates en `app/templates/` global

**No mezclar.** Si el template no está en la carpeta del módulo, Flask hace fallback silencioso a la global sin error — difícil de depurar.

---

## Arquitectura de Modelos

### Orden de imports en `app/models/__init__.py` — CRÍTICO
Respetar siempre el orden establecido: primero modelos sin FKs operacionales,
luego modelos con dependencias simples, luego dependencias múltiples.
Modificar este orden puede causar errores de circular import.

### Schema PostgreSQL
Todas las tablas usan `schema='public'` explícito.
Las FK deben referenciar con prefijo: `db.ForeignKey('public.tabla.campo')`

---

## Layout y CSS

- Notificaciones: toasts Flask (`flash`), categorías `success/danger/warning/info`. **Nunca modales.**

---

## Base de Datos

**NUNCA usar migraciones automáticas** (`flask db migrate`) — regenera todas las FK innecesariamente. Usar siempre `flask db revision` y editar manualmente. El `downgrade` requiere especial cuidado.
`db.drop_all()` y `db.create_all()` prohibidos.

---

## Herramientas MCP Disponibles

- **PostgreSQL MCP** — consultar esquema real de BD en desarrollo
- **Playwright MCP** — testing e interacción automática con navegador
  - Sin nombre de fichero → auto-genera `page-TIMESTAMP.png` en `.playwright-mcp/` (correcto)
  - Con nombre personalizado → guarda relativo al CWD (repo root). **SIEMPRE** prefijar:
    `.playwright-mcp/nombre.png` para mantenerlos fuera del árbol git.
- **Windows MCP** — redimensionado de ventanas

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
