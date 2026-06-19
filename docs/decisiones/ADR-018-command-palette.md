# ADR-018 — Command Palette (Ctrl+K) — búsqueda global y navegación

**Estado:** Adoptada
**Fecha:** 2026-05-28
**Issue:** #502 (sustituye al #75 cerrado)

---

## Contexto

El estudio de usuario fase 2 (§7.1) identificó la búsqueda como **operación de localización primaria** del tramitador: *"el dato principal de búsqueda en Access y Calc es el número de expediente"* + búsquedas secundarias por peticionario, municipio, nombre proyecto.

El análisis crítico fase 3 (§2.5 y §5.4) marcó como hallazgo:

- **Issue #75** ("Búsqueda global de expedientes") estaba mal-priorizado en M5 frente al uso real diario.
- El patrón a aplicar es claro: **command palette tipo Linear / GitHub** activable con `Ctrl+K`.

ADR-014 (layout) reservó un input de búsqueda en el topbar del shell `base_app.html`, anticipando que el componente sería un command palette y no un buscador clásico.

ADR-015 (stack JS) estableció React islas con CSS Bootstrap+JdA; el command palette encaja exactamente en ese modelo.

---

## Decisión

### 1. Componente único activable desde cualquier vista

Command palette modal-like activable con:

- **`Ctrl+K`** (también `Cmd+K` en Mac) como atajo primario universal.
- **`/`** como atajo secundario, estilo GitHub. Cero coste extra. Se ignora cuando hay un input de formulario en foco para no interferir con escritura normal.
- **Click en el input de búsqueda del topbar** lo abre con foco en su input.

Cierre con `Esc`, click fuera del modal, o `Enter` sobre un resultado.

### 2. Estructura visual

```
┌─ Modal centrado, ~720px ancho, backdrop semi-opaco ────────────┐
│ 🔍  [_______________________________________________]  Esc ⏎  │
│                                                                │
│  EXPEDIENTES                                                   │
│   📂 AT-1234  Sotogrande Solar — ENDESA SA                    │
│   📂 AT-1340  Almazara Olipampe — ALMENDRA SL                 │
│                                                                │
│  ENTIDADES                                                     │
│   🏢 ENDESA DISTRIBUCIÓN SAU — A82846817                      │
│                                                                │
│  IR A                                                          │
│   📥 Mi trabajo                                                │
│   📋 Listado de expedientes                                    │
│   ⚙ Reglas del motor                                          │
│                                                                │
│  ↑↓ navegar · ⏎ abrir · Esc cerrar           Ctrl+K            │
└────────────────────────────────────────────────────────────────┘
```

Resultados agrupados por categoría (EXPEDIENTES / ENTIDADES / IR A). Cada item: icono + nombre + breadcrumb contextual.

### 3. Comportamiento según contenido del input

- **Input vacío** → muestra **recientes** (últimos N expedientes visitados, desde `sessionStorage`) + atajos a áreas principales del sidebar.
- **Texto libre** → busca expedientes + entidades + áreas, agrupado y ordenado por relevancia.
- **Patrón `13/2023` o `AT-1234`** → match directo de número de expediente, primer resultado destacado.
- **Debounce 150ms** desde cliente para no saturar las APIs en cada tecla.

### 4. Navegación por teclado

| Tecla | Acción |
|---|---|
| `↑` / `↓` | Navegar entre resultados (cicla entre categorías) |
| `Enter` | Abrir resultado seleccionado |
| `Esc` | Cerrar |
| `Ctrl+K` | Toggle (cierra si está abierto) |
| `Backspace` con input vacío | Sin acción |

### 5. Alcance — versión básica (M4)

Esta es la decisión que se planifica para implementación inmediata previa al arranque oficial:

- Búsqueda de **expedientes** (número, titular, peticionario, municipio, nombre proyecto).
- Búsqueda de **entidades** (nombre, NIF).
- Búsqueda de **usuarios** (siglas, nombre, apellidos) — *ampliado en la implementación (#532)*. Todos los roles pueden **localizar** usuarios (`acceder_usuarios` es de todos); la **edición** sigue restringida a ADMIN/SUPERVISOR (`gestionar_usuarios`) en sus propias rutas.
- **Navegación** a áreas principales del sidebar (Mi trabajo, Expedientes, Entidades, Plantillas, Usuarios, Motor, Plazos).
- **Recientes** desde `sessionStorage` (últimos expedientes visitados en la sesión actual).
- Teclado completo (`Ctrl+K`, `/`, `↑↓`, `Enter`, `Esc`).

### 6. Iteraciones posteriores (M5)

Funcionalidad atractiva pero no crítica, planificada para post-arranque:

- **Acciones de creación inline** ("Nuevo expediente", "Nueva entidad") desde el palette.
- **Tokens avanzados**: `is:vivo`, `responsable:CLG`, `pendiente:notificar`, `tipo:Renovable`. Sintaxis de filtros embebida en la búsqueda.
- **Prefijos de modo**: `>` solo comandos, `#` solo expedientes por número, `@` solo entidades, `?` ayuda.
- **Cambio de rol** desde el palette (sin pasar por el dropdown del topbar).
- **Pinned items** que el usuario marca como favoritos.
- **Comandos del motor** ("Validar regla X", "Auditar expediente Y"), comandos del supervisor.
- **Historial persistente** entre sesiones (`localStorage` en lugar de `sessionStorage`).

Estas iteraciones se materializarán en uno o varios issues nuevos en M5, sin precondicionarlas en este ADR.

### 7. Implementación técnica

#### Frontend

- **Librería**: `cmdk` (Vercel, ~30KB, headless, accesible). Patrón usado por Linear, Vercel, Raycast extensions.
- **Wrapper** con clases Bootstrap+JdA para mantener identidad — coherente con la disciplina CSS de ADR-015.
- **Isla React** `react-src/src/command-palette/` siguiendo el patrón de ADR-015 (entry IIFE, expone `window.CommandPalette.mount`).
- **Integración global**: el bundle se carga en `base_app.html`. Un listener global de `keydown` captura `Ctrl+K` / `Cmd+K` / `/` y abre el modal.

#### Backend — endpoints nuevos

**Endpoint unificado (#532):**

- **`GET /api/search?q=...&tipos=expedientes,entidades,usuarios,plantillas&limit=10`** → `{'grupos': [{'tipo', 'resultados': [...]}]}`. Recorre un **registro** `BUSCADORES` (tipo → permiso + helper `_buscar_*`) en el orden de `tipos`, **saltando** los tipos cuyo permiso no tenga el rol activo (igual que el sidebar). Añadir una entidad buscable = un helper `_buscar_X(q, limit)` + una línea en el registro (backend) + una línea de config en la isla (frontend).

Búsqueda por entidad (campos): **expedientes** en `numero_at`, `titular.nombre_completo`, `proyecto.titulo`, `municipio.nombre` (match exacto de número primero); **entidades** en `nombre_completo`, `nif`; **usuarios** en `siglas`, `nombre`, `apellido1/2`; **plantillas** en `nombre`, `codigo`, `descripcion`, `variante`. **Sin filtro de `activo`** (#532): el palette busca TODO (activos e inactivos), como los listados, que por defecto no distinguen estado.

Permisos por tipo: expedientes/entidades `acceder_expediente`, usuarios `acceder_usuarios`, plantillas `acceder_plantillas` — todos de los 4 roles tras ADR-013; la **edición** de cada dominio sigue restringida en sus propias rutas.

**Histórico:** las rutas por-entidad `GET /api/search/{expedientes,entidades,usuarios}` (#531) se **retiraron** al unificar la búsqueda (#532 fase 2), una vez validado el endpoint unificado en vivo.

#### Recientes en `sessionStorage`

Key: `bddat.palette.recientes`. Estructura: array de `{tipo, id, label, timestamp}` con tope de 10. Se actualiza al abrir cualquier expediente/entidad desde el palette.

### 8. Encaje en el layout

- Es **overlay sobre el shell `base_app.html`**. No ocupa slot del grid.
- Disponible desde cualquier vista (topbar siempre visible).
- El input del topbar es el "ancla visual" — clic ahí abre el palette; cerrar el palette devuelve foco al input.

---

## Por qué

- **Cubre la operación primaria de localización** identificada en el estudio de usuario (número de expediente como dato principal).
- **Reemplaza el flujo actual** "ir al listado → filtrar → encontrar" por "Ctrl+K → escribir → Enter".
- **Encaja con el principio de "convivencia, no kiosko"** (ADR-014): el usuario puede acceder a cualquier expediente desde cualquier vista sin perder contexto.
- **El input del topbar de ADR-014 ya está pensado para esto** — no se desperdicia el espacio.
- **Coherente con el lenguaje moderno** de las apps de referencia (Linear, GitHub, Stripe) sin sacrificar identidad JdA (es solo CSS).
- **Trabajo acotado** (~1-2 semanas) con valor desproporcionado por usuario.

---

## Cómo implementar (versión básica M4)

1. **Backend — endpoints de búsqueda**:
   - `GET /api/search/expedientes?q=...`.
   - `GET /api/search/entidades?q=...`.
   - Ambos con búsqueda fuzzy + tope `limit=10` + permisos.
2. **Frontend — isla React** `react-src/src/command-palette/`:
   - Componente `<CommandPalette>` con `cmdk`.
   - Wrapper con clases Bootstrap+JdA.
   - Listener global de teclado en el script de entrada.
   - Lectura/escritura de `sessionStorage` para recientes.
3. **Integración** en `base_app.html`:
   - Cargar el bundle compilado.
   - El input del topbar invoca la función de apertura al focus.
4. **Documentación**:
   - Actualizar `docs/guias/GUIA_REACT_ISLAS.md` con el patrón de "isla global" (vs "isla por vista").
5. **Tests**:
   - Smoke test pytest: los dos endpoints responden 200 con query mínima.
   - Smoke test Playwright MCP: `Ctrl+K` abre el palette, escribir filtra, `Enter` navega.

---

## Alternativa descartada

### A. Buscador clásico en el topbar (sin modal)

Considerada. Descartada porque limita la riqueza: un buscador inline solo cabe para una categoría, sin navegación ni recientes. El modal permite agrupar EXPEDIENTES + ENTIDADES + IR A + recientes en un solo cuadro de búsqueda.

### B. Sin atajo de teclado, solo click en el input

Descartada. El atajo `Ctrl+K` es el patrón estándar de las apps modernas y reduce la fricción de localización a una pulsación. Es lo que diferencia un command palette de un buscador.

### C. Componente custom sin librería externa

Considerada. Descartada por coste/beneficio: `cmdk` es estable, ~30KB, accesible por defecto (ARIA correcto, foco gestionado, navegación por teclado). Reescribirlo desde cero no aporta y consume tiempo que rinde más en otras islas.
