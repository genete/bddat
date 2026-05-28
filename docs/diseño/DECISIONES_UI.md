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

---

## Decisiones implicadas (cerradas de facto por otras)

| Decisión original | Cerrada por |
|---|---|
| **5.4 Sidebar persistente vs. navbar** | ADR-014: el layout incluye sidebar persistente con chevron de colapsar/expandir |
| **5.3 Pool de documentos como panel lateral** (estructura) | ADR-014: el slot `inspector` está pensado para el pool entre otros usos. Falta definir contenido concreto — sigue como pendiente abajo |

---

## Decisiones pendientes

| # | Decisión | Origen | Próximo paso | Bloqueada por |
|---|---|---|---|---|
| **5.2** | Árbol del expediente: librería (xyflow vs. react-arborist vs. custom), datos de entrada, comportamiento al seleccionar nodo, interacciones (drag, expand-collapse, etc.) | ANALISIS_CRITICO §2.2 | ADR-016 + issue | — (se puede arrancar) |
| **5.3-bis** | Contenidos concretos del inspector: ¿siempre muestra el pool del expediente? ¿cambia según nodo seleccionado en el árbol? ¿permite drag de documentos? | ANALISIS_CRITICO §2.7 | ADR-017 + issue | 5.2 (depende de qué emite el árbol) |
| **5.5** | Sub-stack React concreto: librerías específicas (cmdk, react-arborist, etc.), state management si crece, data fetching avanzado si se necesita | ANALISIS_CRITICO §5.5 + ADR-015 §6 | Decisión por isla en su implementación | — (incremental) |
| **5.6** | Mini-estudio del administrativo antes de diseñar su vista | ANALISIS_CRITICO §2.4 + §5.6 | Decisión binaria sí/no del usuario | — (independiente) |
| **5.7** | Tests UI mínimos: ¿se introducen Playwright E2E? ¿solo smoke tests Jinja? ¿RTL para componentes React? | ANALISIS_CRITICO §5.7 | Decisión política | — (independiente) |
| **— nuevo —** | Command palette (Ctrl+K): primera isla React además del árbol. Librería (cmdk vs. custom), alcance (búsqueda + acciones + navegación) | ANALISIS_CRITICO §2.5 (búsqueda) + ADR-014 (input ya reservado en topbar) | ADR + issue | ADR-015 (scaffolding) |
| **— nuevo —** | Vista del administrativo: estructura (`base_app` con o sin slots), contenido, integración con backend | ANALISIS_CRITICO §2.4 | Tras 5.6 (mini-estudio) | 5.6 |

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

---

## Cómo se mantiene este documento

- Cada ADR nuevo del revamping se anota arriba en "Decisiones cerradas" y abajo en "Histórico".
- Cada decisión pendiente que se cierra se traslada de la tabla pendiente a la tabla cerrada (con su ADR + issue).
- Cada decisión nueva que emerge durante la implementación se añade a "Decisiones pendientes".
- Los principios y el fuera-de-alcance NO se editan salvo que un ADR los modifique explícitamente.
