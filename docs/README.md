# Documentación BDDAT

Sistema de tramitación administrativa de expedientes de autorización de instalaciones de alta tensión en Andalucía.

---

## 📘 Guías de referencia activas

### [GUIA_VISTAS_BOOTSTRAP.md](GUIA_VISTAS_BOOTSTRAP.md)
**Referencia principal de diseño UI** — layout, vistas V0/V1/V2/V3/V4, CSS corporativo, errores comunes.

### [GUIA_COMPONENTES_INTERACTIVOS.md](GUIA_COMPONENTES_INTERACTIVOS.md)
Catálogo de componentes JS reutilizables: SelectorBusqueda, ScrollInfinito, AcordeonLazy.
Leer antes de implementar cualquier componente interactivo.

---

## Estructura de Documentación

### 📁 [setup/](setup/)
Guías de instalación y configuración inicial del proyecto.
- [PROCEDIMIENTO_SETUP_PC.md](setup/PROCEDIMIENTO_SETUP_PC.md)

### 🏗️ [arquitectura/](arquitectura/)
Documentos de diseño de alto nivel: arquitectura frontend, sistema de módulos.
- [FASE_3_FRONTEND_DINAMICO.md](arquitectura/FASE_3_FRONTEND_DINAMICO.md) - Sistema metadata-driven (futuro)

### 🎨 [estilos/](estilos/)
Guías de estilos CSS y recursos visuales.
- [guia_colores_junta_andalucia.html](estilos/guia_colores_junta_andalucia.html) - Paleta interactiva

### 💻 [implementaciones/](implementaciones/)
Documentación técnica de implementaciones específicas.
- [VISTA_V3_TRAMITACION.md](implementaciones/VISTA_V3_TRAMITACION.md) - Vista tramitación V3-BC (breadcrumbs)

### 🤖 [fuentesIA/](fuentesIA/)
Referencias y reglas para desarrollo asistido por IA (Claude Code).
- [REGLAS_DESARROLLO.md](fuentesIA/REGLAS_DESARROLLO.md) — workflow Git, commits, ramas, migraciones
- [GUIA_GENERAL.md](fuentesIA/GUIA_GENERAL.md) — arquitectura general y lógica de negocio
- [PLAN_ROADMAP.md](fuentesIA/PLAN_ROADMAP.md) — estado actual de implementación por milestones
- [PLAN_ESTRATEGIA.md](fuentesIA/PLAN_ESTRATEGIA.md) — visión estratégica, 14 bloques funcionales
- [DISEÑO_SUBSISTEMA_DOCUMENTAL.md](fuentesIA/DISEÑO_SUBSISTEMA_DOCUMENTAL.md) — decisiones subsistema documental
- [DISEÑO_MOTOR_REGLAS.md](fuentesIA/DISEÑO_MOTOR_REGLAS.md) — diseño del motor de reglas
- [GUIA_CONTEXT_BUILDERS.md](fuentesIA/GUIA_CONTEXT_BUILDERS.md) — generación de escritos administrativos
- [ANALISIS_TAREAS_INVERSO.md](fuentesIA/ANALISIS_TAREAS_INVERSO.md) — tabla inversa de tareas atómicas ESFTT
- [GUIA_ROLES.md](fuentesIA/GUIA_ROLES.md) — roles y permisos del sistema
- **[referencias/](fuentesIA/referencias/)** — conocimiento de dominio AT (normativa y clasificaciones):
  - [Clasificacion AT Andalucia.md](fuentesIA/referencias/Clasificacion%20AT%20Andalucia.md) — tipos de instalaciones y competencias Junta/Estado
  - [Clasificacion AT Capa2.md](fuentesIA/referencias/Clasificacion%20AT%20Capa2.md) — subtipos físicos, generación, modificaciones e Instrucción 1/2023
  - [Mapa Normativo AT Andalucia.md](fuentesIA/referencias/Mapa%20Normativo%20AT%20Andalucia.md) — inventario completo de normativa estatal y autonómica con relaciones entre normas

---

## Enlaces Rápidos

- [📘 Guía Vistas Bootstrap](GUIA_VISTAS_BOOTSTRAP.md) — **Referencia principal UI**
- [Reglas de Desarrollo](fuentesIA/REGLAS_DESARROLLO.md) — flujo de trabajo Git
- [PLAN_ROADMAP](fuentesIA/PLAN_ROADMAP.md) — qué está hecho, qué está pendiente
- [Repositorio en GitHub](https://github.com/genete/bddat)

---

## Historial de cambios de documentación

### Marzo 2026 — Limpieza era Perplexity
Eliminados ficheros que solo tenían valor en el flujo anterior (Perplexity Pro + conector GitHub).
El contenido sigue accesible via `git log` en el commit `[DOCS] Limpieza documentación era Perplexity`.

**Eliminados (artefactos de flujo Perplexity):**
- `fuentesIA/ACCESO_RAPIDO_PROYECTO.md` — punto de entrada para Perplexity; reemplazado por `CLAUDE.md`
- `fuentesIA/referencias/Tablas.md` y `TablasResumen.md` — generados por `merge_tables.py`; reemplazados por PostgreSQL MCP
- `fuentesIA/referencias/tablas/` — 20 ficheros individuales de tablas (O_001…O_022, E_001…E_008); ídem
- `fuentesIA/MOTOR_REGLAS_plan_perplexity.md` y `MOTOR_REGLAS_prompts_perplexity.md` — prompts de sesión Perplexity
- `fuentesIA/CONTEXTO_ISSUE_*.md` (issues #61, #73, #93, #117) — contexto pre-masticado para Perplexity; issues cerrados
- `utils/generar_estructura.bat`, `sincronizar_drive.bat/.sh` — utilidades de sincronización con espacio Perplexity

**Eliminados (históricos redundantes ya compactados en GUIA_VISTAS_BOOTSTRAP.md):**
- `arquitectura/historico/` — PATRONES_UI, VISTAS, VISTA_V0_LOGIN, VISTA_V1_DASHBOARD
- `estilos/historico/` — CSS_v2_GUIA_USO
- `implementaciones/historico/` — ISSUE_94_ESTRUCTURA, SCROLL_INFINITO, UI_PATTERNS_DATA_TABLE

### Febrero 2026 — Transición a Claude Code
- Nueva guía compactada: [GUIA_VISTAS_BOOTSTRAP.md](GUIA_VISTAS_BOOTSTRAP.md)
- Documentos detallados movidos a carpetas `historico/` (ahora eliminadas, ver arriba)
- Vista V3: cambio arquitectónico de sidebar → acordeón → V3-BC breadcrumbs (12/02/2026)
- Vistas completadas: V0 (Login), V1 (Dashboard), V2 (Listado scroll infinito)

---

**Stack:** PostgreSQL + Flask (SQLAlchemy) + Bootstrap 5
**Rama de desarrollo:** `develop`
**Última actualización:** 7 de marzo de 2026