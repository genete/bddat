# CLAUDE.md — Proyecto BDDAT

## Contexto del Proyecto
Sistema de tramitación de expedientes de autorización de instalaciones de alta tensión.
Desarrollado para la Consejería de Industria, Energía y Minas (Junta de Andalucía).

**Stack:** Python 3.x + Flask + SQLAlchemy + PostgreSQL + Bootstrap 5.3

---

## Documentos de referencia

Índice completo y estado actual: `docs/README.md`

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
- **Windows MCP** — redimensionado de ventanas

### Precauciones Playright MCP
- **Consume mucho contexto**: especialmente al capturar pantalla. ¡¡Preguntar siempre!!
- Sin nombre de fichero → auto-genera `page-TIMESTAMP.png` en `.playwright-mcp/` (correcto)
- Con nombre personalizado → guarda relativo al CWD (repo root). **SIEMPRE** prefijar:
    `.playwright-mcp/nombre.png` para mantenerlos fuera del árbol git.

---

## Convenciones Bash (anti-bloqueos del parser)

Ver referencia completa: `docs/guias/REGLAS_BASH.md`

- **Activar venv:** NUNCA `source venv/Scripts/activate` — usar `venv/Scripts/python.exe script.py`
