# CLAUDE.md — Proyecto BDDAT

## Contexto del Proyecto
Sistema de tramitación de expedientes de autorización de instalaciones de alta tensión.
Desarrollado para la Consejería de Industria, Energía y Minas (Junta de Andalucía).

**Stack:** Python 3.x + Flask + SQLAlchemy + PostgreSQL + Bootstrap 5.3

---

## Documentos de referencia

- Antes de escribir código, templates, modelos, migraciones o commits: leer `docs/guias/REGLAS_DESARROLLO.md`
- Ante refactorizaciones o cambios de diseño: seguir §"Análisis de impacto previo" de `REGLAS_DESARROLLO.md` — presentar tabla de consumidores al usuario antes de escribir código
- Comandos Bash: las reglas de `docs/guias/REGLAS_BASH.md` **las aplica un hook**, no la
  buena memoria. `.claude/hooks/reglas_bash_guard.py` (PreToolUse sobre Bash) deniega los
  anti-patrones conocidos antes de que lleguen al usuario. Si un comando sale denegado con
  «REGLAS_BASH.md — anti-patrón detectado», **reescribirlo con el arreglo que indica el
  mensaje; nunca reintentarlo igual**. El hook cubre lo mecánico; leer la guía completa
  sigue mereciendo la pena antes de una tanda larga de comandos, y es obligatorio si hay
  que tocar el propio guard.
- Para entender la estructura de docs: leer `docs/README.md`
- Para entrar en contexto de lo que está vivo: leer **siempre** `docs/CONTEXTO_ACTUAL.md`
- Al actualizar `docs/CONTEXTO_ACTUAL.md` (cierre de issue): proponer qué pasa a **Próximo** y pedir confirmación — no elegir unilateralmente.

---

## Herramientas MCP Disponibles

- **PostgreSQL MCP** — consultar esquema real de BD en desarrollo
- **Playwright MCP** — verificación rutinaria en navegador, ver abajo
- **Windows MCP** — redimensionado de ventanas

## Verificación de cambios en navegador

Herramienta por defecto: **Playwright MCP**, sin preguntar al usuario.

Uso: navegación e interacción para comprobar el funcionamiento y las respuestas de la
interfaz. Para artefactos de render, capturas de pantalla preferentemente contenidas en
HD o Full HD. Para casos especiales, fijar la dimensión con `browser_resize` al arrancar
el navegador (cambia el viewport real, verificado). Login de dos pasos: memoria
`project_login_dos_pasos`. Al terminar la verificación, cerrar el navegador con
`browser_close`.

Ficheros: sin nombre → auto-genera `page-TIMESTAMP.png` en `.playwright-mcp/` (correcto).
Con nombre propio → **SIEMPRE** prefijar `.playwright-mcp/nombre.png`, si no guarda suelto
en la raíz del repo.
