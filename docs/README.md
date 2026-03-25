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

Todos los documentos viven en `docs/` raíz. Subdirectorios solo para no-MDs.

### 🎨 [estilos/](estilos/)
- [guia_colores_junta_andalucia.html](estilos/guia_colores_junta_andalucia.html) - Paleta interactiva

### Reglas y workflow
- [REGLAS_DESARROLLO.md](REGLAS_DESARROLLO.md) — workflow Git, commits, ramas, migraciones
- [REGLAS_ARQUITECTURA.md](REGLAS_ARQUITECTURA.md) — flujo de decisiones arquitectónicas, sincronización documental
- [REGLAS_BASH.md](REGLAS_BASH.md) — patrones prohibidos en Bash y workarounds

### Arquitectura y diseño
- [GUIA_GENERAL.md](GUIA_GENERAL.md) — arquitectura general y lógica de negocio
- [DISEÑO_MOTOR_REGLAS.md](DISEÑO_MOTOR_REGLAS.md) — diseño del motor de reglas ESFTT
- [DISEÑO_SUBSISTEMA_DOCUMENTAL.md](DISEÑO_SUBSISTEMA_DOCUMENTAL.md) — pool documental: tipos, vías de entrada, decisiones
- [DISEÑO_ANALISIS_SOLICITUD.md](DISEÑO_ANALISIS_SOLICITUD.md) — fase ANÁLISIS_SOLICITUD, checklist documental (#248)
- [DISEÑO_CONSULTAS_ORGANISMOS.md](DISEÑO_CONSULTAS_ORGANISMOS.md) — fase consultas a organismos (#247)
- [DISEÑO_DIAGRAMAS_ESFTT.md](DISEÑO_DIAGRAMAS_ESFTT.md) — diagramas de flujo ESFTT por capas (#249)

### Planificación
- [PLAN_ROADMAP.md](PLAN_ROADMAP.md) — estado actual de implementación por milestones
- [PLAN_ESTRATEGIA.md](PLAN_ESTRATEGIA.md) — visión estratégica, 14 bloques funcionales

### Guías técnicas
- [GUIA_CONTEXT_BUILDERS.md](GUIA_CONTEXT_BUILDERS.md) — context builders para generación de escritos
- [GUIA_ROLES.md](GUIA_ROLES.md) — roles y permisos del sistema

### Análisis
- [ANALISIS_TAREAS_INVERSO.md](ANALISIS_TAREAS_INVERSO.md) — tabla inversa de tareas atómicas ESFTT
- [ANALISIS_HOMOGENEIZACION_UI.md](ANALISIS_HOMOGENEIZACION_UI.md) — estudio de homogeneización de la interfaz

### Procedimientos
- [PROCEDIMIENTO_SETUP_PC.md](PROCEDIMIENTO_SETUP_PC.md) — configuración del entorno de desarrollo
- [PROCEDIMIENTO_MMD_DESDE_DOCUMENTACION.md](PROCEDIMIENTO_MMD_DESDE_DOCUMENTACION.md) — generación de diagramas Mermaid
- [PROCEDIMIENTO_MMD_DESDE_IMAGEN.md](PROCEDIMIENTO_MMD_DESDE_IMAGEN.md) — generación de diagramas desde imagen

---

## Enlaces Rápidos

- [📘 Guía Vistas Bootstrap](GUIA_VISTAS_BOOTSTRAP.md) — **Referencia principal UI**
- [Reglas de Desarrollo](REGLAS_DESARROLLO.md) — flujo de trabajo Git
- [PLAN_ROADMAP](PLAN_ROADMAP.md) — qué está hecho, qué está pendiente
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