# ADR-015 — Stack JS: React en islas sobre Bootstrap+JdA, sin SPA

**Estado:** Adoptada
**Fecha:** 2026-05-28
**Issue:** #499

---

## Contexto

El revamping de UI necesita decidir el stack tecnológico que se ejecuta en el navegador. La situación de partida:

- **Stack actual**: Jinja + Bootstrap 5.3 + CDN JdA + JS vanilla en clases (selector_busqueda, municipios_selector, v2-scroll-infinito, v3-breadcrumbs-*, etc.). 13 CSS y 16 JS.
- **POC React existente**: `react-diagramas/` es un proyecto Vite/Rollup con `@xyflow/react` integrado y compilado a un bundle IIFE (`app/static/js/react/diagrama-esftt.iife.js`) consumido por `demo/diagrama.html`. Datos mockeados.
- **ADR-014 ya fijó el layout**: `base_app.html` con slots `inspector` y `dock`. La vista de expediente (workbench) requiere componentes complejos — árbol expandible enriquecido con colores, estados, símbolos — que en vanilla salen caros y en React+xyflow salen ya construidos al 70%.
- **Trabajo realizado en 100 días**: 49 modelos, 15 servicios, 12 ADRs, 40 templates, 50 tests. Ratio de productividad alto (1 dev + IA).

Tres opciones consideradas en discusión de fase 3:

- **A. Jinja + JS vanilla (eventualmente con HTMX/Alpine)** — máximo reuso, sin pipeline JS, coherencia única.
- **B. Híbrido Jinja + React por componente** — React donde la UX lo justifica, Jinja para el resto.
- **C. SPA React completa** — descartar todo el frontend Jinja y reconstruir.

Argumentos decisivos para el caso BDDAT:

- **El árbol del expediente justifica React** — tres iteraciones previas (acordeón, tabs, breadcrumbs) demostraron que un layout lineal no comunica la jerarquía. El árbol enriquecido es la solución. xyflow + React lo facilita; vanilla lo encarece.
- **Si hay React vivo, el coste cognitivo de "dos stacks" ya está pagado** — la pregunta se vuelve "qué porcentaje React vs Jinja", no "React sí o no".
- **SPA completa es desproporcionada** — descarta trabajo de UI consolidado (login, admin de plantillas, usuarios, formularios) que no necesita rediseño profundo. Riesgo serio de 6-12 meses de migración sin valor visible nuevo.
- **El despliegue no es excusa** — `flask_console.py` con tkinter ya existe; añadir botón "build React" es trivial. Vite/Rollup ya configurado en el POC.

---

## Decisión

### 1. Modelo de integración: React en islas

El stack se materializa como **islas React montadas sobre templates Jinja**:

- Cada vista que necesita React es un template Jinja propio que extiende `base_app.html`.
- El template Jinja sirve la página inicial completa con sus `@require_permiso` decoradores, `viewbar`, sidebar, etc.
- El template monta UN componente React (o varios) en `<div id="app-root" data-*="...">`.
- El componente React se ejecuta en el navegador y gestiona la interactividad rica dentro de su `<div>`.
- **Navegar entre URLs grandes (expedientes, listados, secciones) recarga la página** — Flask responde rápido. No hay React Router.
- **Dentro de una vista, todo es React reactivo** sin recargas.

### 2. CSS: Bootstrap + CDN JdA como única paleta

Los componentes React **usan exclusivamente las clases CSS de Bootstrap + el CDN JdA**. Sin Tailwind, sin Material UI, sin Chakra, sin shadcn/ui, sin ninguna librería React que arrastre su propio sistema visual.

Cuando un componente externo viene con CSS propio (xyflow, cmdk, react-arborist), se aplica un pase de **tematizado** que sobrescribe sus variables CSS o clases para respetar la paleta JdA. Se documenta el patrón.

### 3. Autenticación y permisos: sin cambios

Las islas React no introducen autenticación cliente. Reutilizan la sesión Flask existente:

- El template Jinja que monta la isla lleva sus `@require_permiso` decoradores (post ADR-013).
- Las APIs JSON que el componente React consume llevan los mismos decoradores.
- La cookie de sesión Flask se envía sola en `fetch()` desde React.
- Los permisos del usuario se inyectan en el HTML inicial como `data-*` o JSON embebido para que los componentes condicionen botones (`tienePermiso('gestionar_X') && <BotonEditar />`).

**Cero patrones nuevos de auth**, cero tokens, cero CSRF custom para APIs idempotentes (las que muten datos siguen el patrón Flask-WTF + token en header — pasable a React con setup mínimo).

### 4. Build pipeline: Vite

Vite + Rollup (ya en uso en `react-diagramas/`). Configuración:

- **Modo desarrollo**: `npm run dev` levanta servidor Vite con HMR. Flask sirve los HTML; en desarrollo el HTML carga el bundle desde `http://localhost:5173/...` con HMR activo.
- **Modo producción**: `npm run build` genera bundles IIFE en `app/static/js/react/`. Flask los sirve estáticos. Hash en filename para cache busting.
- **Script `flask_console.py` extendido** con botón "Build React" para no salir de la GUI.

> **Nota de implementación (#499).** Al construir el scaffolding se afinaron dos puntos de §4:
> - **Modo desarrollo = rebuild**, no HMR. `npm run dev` (Vite standalone) sigue disponible para iterar un componente aislado, pero el flujo sobre Flask es "Build React → recargar". El HMR integrado en Flask (helper `react_bundle` ramificado dev/prod) se pospone a #500, donde la iteración del árbol del expediente lo justifica; meterlo ahora sería complejidad sin caso de uso.
> - **Formato ES modules**, no IIFE. IIFE en Vite solo admite una entry por build y duplicaría React en cada isla. Con módulos ES (`<script type="module">`) las islas comparten React y chunks comunes, y Vite genera el `manifest.json` (nombre→hash) que lee `react_bundle()`.

### 5. Estructura de carpetas

```
app/
  static/
    js/
      react/                    ← bundles compilados (gitignored excepto el manifest)
        bundle.expediente-arbol.js
        bundle.command-palette.js
        manifest.json           ← mapping nombre → hash
  templates/
    expedientes/
      arbol.html                ← template Jinja, monta el bundle del árbol

react-src/                       ← código fuente React (renombrado desde react-diagramas/)
  vite.config.js
  package.json
  src/
    expediente-arbol/
      index.jsx                 ← entry IIFE
      App.jsx
      components/
      hooks/
    command-palette/
      index.jsx
    shared/                     ← utilidades comunes (tienePermiso, fetch wrapper, etc.)
      auth.js
      api.js
      ui/                       ← componentes wrapper de Bootstrap (Button, Modal, Toast...)
```

### 6. Sub-stack interno (pendiente de cierre en implementación)

Decisiones técnicas concretas que se cierran al implementar el primer bundle real (probablemente el árbol del expediente), no en este ADR:

- **State**: arrancar con `useState` + `useReducer` nativos. Promover a Zustand solo si se demuestra dolor real.
- **Data fetching**: arrancar con `fetch` envuelto en helper propio. Promover a TanStack Query solo si hay caché compleja entre componentes.
- **Routing cliente**: no hay. Navegación entre vistas = recarga Flask. Dentro de la vista, estado en componente.
- **UI primitives**: wrappers propios sobre Bootstrap (`<Button>`, `<Modal>`, `<Toast>`, `<Tooltip>`). Se inicializan llamando a `bootstrap.Modal`, etc., del bundle JS de Bootstrap ya cargado por Jinja.
- **Componentes complejos externos**: `@xyflow/react` para el árbol; evaluar `cmdk` para command palette; evaluar `react-arborist` si xyflow se queda corto para árboles densos.

Cada librería externa que entre lleva ADR menor o nota en `DECISIONES_UI.md`.

### 7. Migración del POC existente

`react-diagramas/` se renombra a `react-src/` y se reestructura para acomodar múltiples bundles (uno por isla). El bundle actual del POC (`diagrama-esftt`) se conserva como referencia hasta que el árbol del expediente lo sustituya como primer bundle productivo.

### 8. Tests

- **Backend**: sin cambios, los 50 tests pytest siguen.
- **React**: arrancar sin tests automatizados (decisión 5.7 pendiente). Verificación manual con Playwright MCP por componente.
- **Smoke tests Jinja**: que las vistas con isla React renderizan HTTP 200 y contienen el `<div id="app-root">` esperado.

---

## Por qué

- **Resuelve el problema del árbol del expediente** sin descartar trabajo Jinja existente que funciona.
- **Coste cognitivo acotado**: una sola convención ("¿necesito interactividad rica? → isla React, si no → Jinja"). Mantenible por 1 dev + IA.
- **Coherencia visual garantizada** por disciplina CSS única (Bootstrap+JdA sin alternativas).
- **Autenticación sin reinventar**: la sesión Flask se reutiliza sin tokens.
- **Despliegue compatible** con el modelo actual (Flask sirve estáticos + scripts de build integrables en `flask_console.py`).
- **POC existente se promueve** en lugar de descartarse — cero coste hundido.
- **Reversible**: si una isla resulta ser demasiado para React, se reescribe en Jinja+vanilla. Si una vista Jinja necesita ascender a React, se monta isla. Sin migración global.

---

## Cómo implementar

1. **Renombrar** `react-diagramas/` → `react-src/`. Reestructurar `package.json` y `vite.config.js` para soportar múltiples entries (uno por isla).
2. **Crear estructura** `react-src/src/shared/` con helpers `auth.js` (lectura de data-attributes con user + permisos), `api.js` (wrapper `fetch` con manejo de 401/403 y CSRF).
3. **Crear primer wrapper** Bootstrap React: `<Toast>` o `<Modal>` como prueba de concepto del patrón "componente React que usa clases Bootstrap".
4. **Configurar build script** `scripts/build_react.sh` (ya existe — actualizar para múltiples entries y manifest).
5. **Extender `scripts/flask_console.py`** con botón "Build React" que invoca el script.
6. **Documentar el patrón** "isla React" en `docs/guias/GUIA_REACT_ISLAS.md` (nuevo): cómo crear una nueva isla, cómo inyectar contexto, cómo consumir APIs.
7. **Smoke test** Playwright MCP de que el POC actual (`demo/diagrama.html`) sigue funcionando tras el refactor.

El primer bundle productivo (no scaffolding) será el **árbol del expediente** (decisión 5.2 pendiente, ADR posterior).

---

## Alternativa descartada

### A. Jinja + JS vanilla (eventualmente con HTMX/Alpine)

Considerada con seriedad. Descartada por el caso del árbol del expediente: tres iteraciones fallidas previas en layout lineal indican que la solución pasa por una visualización 2D rica que vanilla puede hacer pero a coste alto (300-500 líneas para un árbol decente vs. 50 con react-arborist o xyflow).

HTMX cubre parciales del servidor y reactividad ligera, pero no es la herramienta adecuada para componentes con estado interno complejo y rendering optimizado (árbol expandible con cientos de nodos, command palette con búsqueda fuzzy en vivo).

### B. SPA React completa

Descartada por:

- Descarte del trabajo Jinja consolidado (login, admin de plantillas, usuarios, formularios) que no tiene problema de UX.
- 6-12 meses de migración pura sin valor visible nuevo para el usuario durante ese tiempo.
- Reconstrucción de autenticación cliente (tokens, refresh, CSRF, etc.) sin ganancia funcional.
- Riesgo serio de no acabarse a tiempo, contra el test de éxito del usuario ("no marcha atrás, métrica mala = retraso en tramitación").

### C. Mismo patrón pero con SPA-like dentro del área de tramitación (React Router para URLs internas)

Considerada. Descartada porque:

- Requiere setup de auth cliente (interceptor 401, refresh de sesión, CSRF en headers) sin ganancia operativa real — las recargas Flask en red corporativa son rápidas.
- El usuario no salta tanto entre expedientes; lo hace entre tareas dentro de uno. Dentro de un expediente, todo es React sin recargas — la SPA-like no aporta.
- Acumula complejidad para resolver un problema que las islas + recarga ya resuelven.
