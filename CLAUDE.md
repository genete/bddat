# CLAUDE.md — Proyecto BDDAT

## Contexto del Proyecto
Sistema de tramitación de expedientes de autorización de instalaciones de alta tensión.
Desarrollado para la Consejería de Industria, Energía y Minas (Junta de Andalucía).

**Stack:** Python 3.x + Flask + SQLAlchemy + PostgreSQL + Bootstrap 5.3

---

## Documentos de referencia

- Antes de escribir código, templates, modelos, migraciones o commits: leer `docs/guias/REGLAS_DESARROLLO.md`
- Ante refactorizaciones o cambios de diseño: seguir §"Análisis de impacto previo" de `REGLAS_DESARROLLO.md` — presentar tabla de consumidores al usuario antes de escribir código
- Antes de cualquier comando Bash: leer `docs/guias/REGLAS_BASH.md`
- Para entender la estructura de docs: leer `docs/README.md`
- Para entrar en contexto de lo que está vivo: leer **siempre** `docs/CONTEXTO_ACTUAL.md`
- Al actualizar `docs/CONTEXTO_ACTUAL.md` (cierre de issue): proponer qué pasa a **Próximo** y pedir confirmación — no elegir unilateralmente.

---

## Herramientas MCP Disponibles

- **PostgreSQL MCP** — consultar esquema real de BD en desarrollo
- **Playwright MCP** — reservado para otros usos (no verificación rutinaria en navegador, ver abajo)
- **Windows MCP** — redimensionado de ventanas

## Verificación de cambios en navegador

Herramienta por defecto: el **navegador integrado de Claude Code Desktop**
(`mcp__Claude_Browser__*` — `preview_start`, `computer`, `read_page`, `javascript_tool`, etc.).
No requiere preguntar antes de usarlo. Arrancar el server con `preview_start {name: "bddat"}`
(ver `.claude/launch.json`) y autenticar con el flujo de dos pasos (`docs/...` /
memoria `project_login_dos_pasos`).

**Playwright MCP** queda reservado para otros usos — no es la herramienta por defecto para
verificar features en navegador. Si en el futuro se detecta que el navegador integrado se
cuelga o no sirve para algún caso concreto (p. ej. islas React con rAF/observers vivos como
react-flow o Recharts), documentarlo como excepción puntual antes de recurrir a Playwright,
y en ese caso sí **preguntar siempre** antes de usarlo (consume mucho contexto, especialmente
al capturar pantalla).

### Si se usa Playwright MCP (excepción)
- Sin nombre de fichero → auto-genera `page-TIMESTAMP.png` en `.playwright-mcp/` (correcto)
- Con nombre personalizado → guarda relativo al CWD (repo root). **SIEMPRE** prefijar:
    `.playwright-mcp/nombre.png` para mantenerlos fuera del árbol git.
