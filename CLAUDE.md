# CLAUDE.md — Proyecto BDDAT

## Contexto del Proyecto
Sistema de tramitación de expedientes de autorización de instalaciones de alta tensión.
Desarrollado para la Consejería de Industria, Energía y Minas (Junta de Andalucía).

**Stack:** Python 3.x + Flask + SQLAlchemy + PostgreSQL + Bootstrap 5.3

---

## Documentos de referencia

- Antes de escribir código, templates, modelos, migraciones o commits: leer `docs/guias/REGLAS_DESARROLLO.md`
- Antes de cualquier comando Bash: leer `docs/guias/REGLAS_BASH.md`
- Para entender la estructura de docs: leer `docs/README.md`
- Para entrar en contexto de lo que está vivo: leer **siempre** `docs/CONTEXTO_ACTUAL.md`

---

## Herramientas MCP Disponibles

- **PostgreSQL MCP** — consultar esquema real de BD en desarrollo
- **Playwright MCP** — testing e interacción automática con navegador
- **Windows MCP** — redimensionado de ventanas

### Precauciones Playwright MCP
- **Consume mucho contexto**: especialmente al capturar pantalla. ¡¡Preguntar siempre!!
- Sin nombre de fichero → auto-genera `page-TIMESTAMP.png` en `.playwright-mcp/` (correcto)
- Con nombre personalizado → guarda relativo al CWD (repo root). **SIEMPRE** prefijar:
    `.playwright-mcp/nombre.png` para mantenerlos fuera del árbol git.
