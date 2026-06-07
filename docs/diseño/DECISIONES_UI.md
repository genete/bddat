# Decisiones del revamping UI

> Registro vivo. El análisis crítico (fase 3) planteó las preguntas; este documento lleva la cuenta de las respuestas.
> Los ADRs son la fuente de verdad de cada decisión y viven en `docs/decisiones/`; aquí solo se enlazan.
> Cada decisión cerrada apunta a su ADR (con justificación completa) y su issue de implementación.

---

## Origen documental

Este registro cierra el ciclo abierto por estos cuatro documentos de la fase 1 a 3:

| Documento | Fase | Propósito |
|---|---|---|
| `AUDITORIA_UI.md` | 1 | Inventario de templates, rutas, componentes y grafo de navegación actual |
| `ESTUDIO_USUARIO.md` | 2 | Perfiles, flujo operativo real, dolor, aspiraciones |
| `INVENTARIO_BACKEND.md` | 2.5 | Modelos, motor, servicios, ADRs existentes, issues, presentación POC |
| `ANALISIS_CRITICO.md` | 3 | Hallazgos cruzados, referencias, principios de diseño, decisiones pendientes |

El **análisis crítico es snapshot inmutable** del estado de reflexión al 28-may-2026. Este documento es el **lugar vivo** donde se anotan respuestas.

---

## Decisiones cerradas

| ADR | Decisión | Issue | Cerrada |
|---|---|---|---|
| **ADR-013** | Permisos blandos generalizados — la visibilidad de pantallas administrativas pasa a ser universal por defecto; los permisos restringen actos no miradas | #497 | 2026-05-28 |
| **ADR-014** | Layout único `base_app.html` con slots opcionales (`inspector`, `dock`) para vistas autenticadas | #498 | 2026-05-28 |
| **ADR-014 §Nomenclatura** | Las 7 áreas del layout llevan nombres fijos: `topbar`, `sidebar`, `viewbar`, `main`, `inspector`, `dock`, `footer`. Referencia rápida: `docs/guias/NOMENCLATURA_LAYOUT.md` | #498 | 2026-05-28 |
| **ADR-015** | Stack JS: React montado como islas sobre templates Jinja. CSS único Bootstrap+JdA. Sin SPA, sin React Router, sin tokens. Vite para build | #499 | 2026-05-28 |
| **ADR-016** | Vista de árbol del expediente — primera isla React productiva. Sustituye las 5 vistas `tramitacion_bc_*` y resuelve los 3 intentos previos fallidos (acordeón/tabs/breadcrumbs) | #500 | 2026-05-28 |
| **ADR-017** | Vista "Mi trabajo" del administrativo — cola común de tareas pendientes + subida de docs al pool. Reutiliza el árbol como destino de acción. Amplía permisos con `gestionar_tareas` y `gestionar_estructura_expediente` | #501 | 2026-05-28 |
| **ADR-018** | Command Palette (Ctrl+K) — búsqueda global de expedientes/entidades + navegación + recientes. Versión básica en M4, iteraciones extendidas en M5. Sustituye #75 | #502 (M4) | 2026-05-28 |
| **ADR-019** | Estrategia de tests UI por 3 fases. Fase 1 (durante revamping): solo smoke tests pytest + verificación manual Playwright MCP. NO E2E ni RTL hasta que la UI estabilice | #503 | 2026-05-28 |
| **ADR-020** | Dock global: deja de ser slot Jinja por vista y pasa a chrome global (partial del shell). Toggle vía campana del topbar. Dos tabs verticales: Bitácora (por usuario, BD) + Avisos (toasts de sesión, sessionStorage). Badge de no leídos, modal por tab, botón limpiar | #506 | 2026-05-29 |
| **ADR-022** | Sistema visual base — escala tipográfica única (rem global 14-15px + shell a rem), tokens de color sin fugas, componente de tabla unificado con overrides heredables, retirada del recorte ~95% en `main`. Prerrequisito de ADR-023 | #533 | 2026-06-07 |
| **ADR-023** | List-detail + inspector universal — selección de fila en lugar de botón "Ver", inspector resizable a nivel de shell con negociación de espacio (maestro reducido por listado, viewbar en `main_min`, automático parco/manual libre, overlay con histéresis). Enmienda ADR-016 §14 | #534 | 2026-06-07 |

---

## Decisiones implicadas (cerradas de facto por otras)

| Decisión original | Cerrada por |
|---|---|
| **5.4 Sidebar persistente vs. navbar** | ADR-014: el layout incluye sidebar persistente con chevron de colapsar/expandir |
| **5.3 Pool de documentos como panel lateral** (estructura) | ADR-014: el slot `inspector` está pensado para el pool entre otros usos. Falta definir contenido concreto — sigue como pendiente abajo |
| **5.2 Árbol del expediente** | ADR-016 cierra topología, bloques, modos lectura/edición, inspector adaptativo, despensa, menú contextual, interacciones, filtros, URL sync y minimapa |

---

## Decisiones pendientes

| # | Decisión | Origen | Próximo paso | Bloqueada por |
|---|---|---|---|---|
| **5.3-bis** | Contenidos concretos del inspector por nivel (refinamiento adaptativo Solicitud/Fase/Trámite/Tarea) | ADR-016 §15 | **Modo lectura resuelto en S3a (#500)** — tabla por nivel en ADR-016 §5, contrato del endpoint lazy en §16. Modo edición (despensa) → S3b | — |
| **5.3-ter** | Viewbar del expediente: contenido exacto, mini-indicadores de alertas del motor y plazos vivos (migrados del dock por ADR-020) | ADR-020 + ANALISIS_CRITICO §2.7 | Diseño pendiente — discutir antes de implementar #500 | — |
| **5.5** | Sub-stack React concreto: librerías específicas (cmdk, react-arborist, etc.), state management si crece, data fetching avanzado si se necesita | ANALISIS_CRITICO §5.5 + ADR-015 §6 | Decisión por isla en su implementación | — (incremental) |
| ~~**5.6**~~ | ~~Mini-estudio del administrativo antes de diseñar su vista~~ → **Resuelta: NO se hace mini-estudio** (supervisor conoce el flujo). Diseño cerrado en ADR-017 #501 | — | cerrada | — |
| ~~**5.7**~~ | ~~Tests UI mínimos~~ → **Cerrada en ADR-019 #503**. Estrategia por 3 fases. Fase 1 inmediata = solo smoke tests pytest | — | cerrada | — |
| ~~**— nuevo —**~~ | ~~Command palette (Ctrl+K)~~ → **Cerrada en ADR-018 #502 (M4)**. Iteraciones extendidas pendientes para M5 (creación inline, tokens avanzados, prefijos, pinned items) | — | cerrada (básica) | — |
| ~~**— nuevo —**~~ | ~~Vista del administrativo~~ → **Cerrada en ADR-017 #501** | — | cerrada | — |
| **— deuda ADR-016 —** | Líneas de dependencia hermano-hermano en el árbol | ADR-016 §15 | Retomable cuando motor completamente seeded o emerja otra solución | motor seeded |
| **— deuda ADR-016 —** | Modo "solo camino activo" (tecla F) en árbol | ADR-016 §15 | Iteración posterior a v1 del árbol | — |
| **— deuda ADR-016 —** | Vista alternativa timeline (toggle desde viewbar) | ADR-016 §15 | Iteración posterior, viewbar puede reservar el espacio | — |
| **— deuda ADR-016 —** | Drag-drop de documentos pool ↔ tareas (detalle: qué rol asigna por defecto, qué tipos admite cada tarea) | ADR-016 §10 | Refinable en implementación de #500 | — |

---

## Principios de diseño vigentes (de ANALISIS_CRITICO §4)

Criterios de decisión cuando hay alternativas en la fase 4:

1. Densidad sí, simplismo no.
2. El sistema empuja con semáforos, no espera disciplina.
3. Una vista única con filtros potentes y guardables (no múltiples vistas predefinidas).
4. Búsqueda global por número de expediente como operación primaria (`Ctrl+K`).
5. Estructura discreta e indexable, no campos libres genéricos.
6. Convivencia con otras apps, no kiosko.
7. Identidad JdA mantenida, lenguaje aplicado modernizado.
8. Mismo flujo DyT/Renovables, distinta velocidad — no bifurcar UI.
9. El motor explica lo que prohíbe (norma compilada + enlace).
10. El revamping no rehace lo que el backend ya sabe — compone.

---

## Fuera de alcance del revamping (recordatorio)

De ANALISIS_CRITICO §6:

- Migración legacy (#175, #105) — wizard de importación es trabajo aparte.
- ENS, HTTPS, infraestructura producción (#176, #177, #178).
- Integración con BandeJA / Notifica / PortaFirmas — requiere ADA, BDDAT solo enlaza.
- PostGIS / cartografía (#27).
- Sistema de ayuda / manual de usuario (#228) — evaluable si el revamping reduce su necesidad.

---

## Histórico de cierre

- **2026-05-28** — ADR-013 cerrado (#497). Permisos blandos generalizados.
- **2026-05-28** — ADR-014 cerrado (#498). Layout único + nomenclatura 7 áreas.
- **2026-05-28** — ADR-015 cerrado (#499). Stack JS: React islas.
- **2026-05-28** — ADR-016 cerrado (#500). Vista de árbol del expediente — primera isla React productiva.
- **2026-05-28** — ADR-017 cerrado (#501). Vista "Mi trabajo" del administrativo + ampliación de permisos.
- **2026-05-28** — ADR-018 cerrado (#502 M4, sustituye #75). Command Palette (Ctrl+K) versión básica.
- **2026-05-28** — ADR-019 cerrado (#503). Estrategia de tests UI por 3 fases. Fase 1 inmediata: smoke tests pytest.
- **2026-05-29** — ADR-020 cerrado (#506). Dock global: chrome partial + toggle campana topbar + tabs Bitácora/Avisos.
- **2026-06-07** — ADR-022 cerrado (#533). Sistema visual base: escala tipográfica única + tokens de color + tabla unificada.
- **2026-06-07** — ADR-023 cerrado (#534). List-detail + inspector universal con negociación de espacio. Enmienda ADR-016 §14. Deriva del PRE-ADR `PRE-ADR-workbench-listados.md`.

---

## Anotaciones para futuros casos de layout

Patrones identificados durante la validación del layout `base_app.html` contra siete casos previstos: descripción del proyecto técnico, mapa cartográfico, mantenimiento de plantillas con despensa de tokens, listado de legacy, migración individual de legacy, dashboard del supervisor, y vista timeline alternativa del expediente.

**Conclusión de la validación**: el layout aguanta los siete casos sin rediseño. Las siguientes tres extensiones del shell se documentarán formalmente en `NOMENCLATURA_LAYOUT.md` cuando llegue el primer caso productivo que las necesite — no antes (no inventar abstracciones sin caso real).

### Patrón A — Split horizontal dentro de `main`

Vistas que necesitan dos sub-zonas dentro de main: típicamente árbol/lista a la izquierda + detalle del elemento seleccionado a la derecha.

Ejemplos previstos:
- Editor del proyecto técnico (árbol de elementos del proyecto + formulario del elemento seleccionado).
- Vistas maestra-detalle dentro del workbench.

Implementación previsible: CSS Grid o flex dentro de `<main class="app-main">` con convención de clase modificadora (por ejemplo `app-main--split-h`). **No es slot nuevo del layout** — main sigue siendo main; cambia su geometría interna.

### Patrón B — Shell inmersivo (sin sidebar ni footer)

Vistas que necesitan maximizar el área de contenido minimizando UI auxiliar.

Ejemplos previstos:
- Visualización cartográfica (PostGIS + Leaflet/OpenLayers, issue #27).
- Eventualmente, modo presentación o pantalla completa de un expediente.

Implementación previsible: clase opcional `app-shell--immersive` en `<body>` o equivalente que colapsa sidebar y footer dejando topbar + main (+ inspector/dock opcionales). El topbar permanece para no perder navegación y búsqueda global. **Es extensión del shell, no template nuevo.**

### Patrón C — Tabs internas del inspector

Vistas donde el inspector necesita mostrar varias secciones al mismo tiempo.

Ejemplos previstos:
- Despensa de tokens en mantenimiento de plantillas (Capa 1 base / Capa 2 CB / Consultas nombradas / Preview).
- Inspector de instalación cartográfica (Ficha técnica / Documentos / Histórico).

Implementación previsible: `nav-tabs` Bootstrap dentro de `<aside class="app-inspector">`. **Es contenido del inspector, no extensión del layout.** Sin cambios en `base_app.html`; sí merece convención escrita para que el patrón sea consistente entre islas.

### Tabla resumen de casos validados

| Caso | Modo | Extensiones aplicadas |
|---|---|---|
| 1. Descripción del proyecto técnico por elementos | workbench | patrón A (split en main) |
| 2. Visualización cartográfica | workbench inmersivo | patrón B |
| 3. Mantenimiento de plantillas con despensa de tokens | workbench | patrón C (tabs en inspector) |
| 4. Listado de expedientes legacy importados | página simple | ninguna |
| 5. Migración individual de expediente legacy | workbench | ninguna |
| 6. Dashboard del supervisor con gráficos | workbench ligero | ninguna |
| 7. Vista alternativa del expediente como línea temporal | workbench | ninguna (toggle desde viewbar; inspector y dock idénticos al modo árbol) |

---

## Cómo se mantiene este documento

- Cada ADR nuevo del revamping se anota arriba en "Decisiones cerradas" y abajo en "Histórico".
- Cada decisión pendiente que se cierra se traslada de la tabla pendiente a la tabla cerrada (con su ADR + issue).
- Cada decisión nueva que emerge durante la implementación se añade a "Decisiones pendientes".
- Los principios y el fuera-de-alcance NO se editan salvo que un ADR los modifique explícitamente.
