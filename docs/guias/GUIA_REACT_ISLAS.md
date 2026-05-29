# Guía — Islas React sobre Jinja (BDDAT)

> Stack JS del revamping: **React montado como islas sobre templates Jinja**, sin SPA,
> sin React Router, reutilizando la sesión y los permisos de Flask.
> Decisión: [ADR-015](../decisiones/ADR-015-stack-js-react-islas.md). Scaffolding: issue #499.

---

## Qué es una "isla"

Una isla es **un componente React que se monta dentro de un `<div>` de una página Jinja
normal**. La página la sirve Flask (con sus `@require_permiso`, sidebar, viewbar, etc.);
React solo gobierna la interactividad rica dentro de su contenedor.

- **Entre vistas grandes** (expedientes, listados): navega recargando página. Flask responde.
- **Dentro de una vista**: todo es React reactivo, sin recargas.

Regla de oro: *¿necesito interactividad rica (árbol, drag, búsqueda en vivo)? → isla React.
Si no → Jinja + Bootstrap como siempre.*

---

## Estructura del proyecto

```
react-src/                         ← código fuente (NO se versiona node_modules)
  vite.config.js                   ← registro de islas (objeto ISLANDS) + build
  package.json
  index.html                       ← solo para `npm run dev` standalone
  src/
    shared/                        ← utilidades comunes a todas las islas
      mountIsland.js               ← auto-montaje en [data-react-island]
      auth.js                      ← getUser / tienePermiso / getRolActivo
      api.js                       ← wrapper fetch (401/403/CSRF)
      ui/
        toast.js                   ← toast Bootstrap imperativo
        Toast.jsx                  ← wrapper React del toast
    diagrama-esftt/                ← isla (POC #291, referencia)
      index.jsx                    ← entry: importa el componente y llama mountIsland
      DiagramaEsftt.jsx
      mockData.js
      styles/diagrama.css

app/static/js/react/               ← bundles compilados (gitignored salvo manifest.json)
  bundle.<isla>.<hash>.js
  asset.<isla>.<hash>.css
  manifest.json                    ← lo lee el helper Jinja react_bundle()
```

---

## Crear una isla nueva (paso a paso)

### 1. Carpeta y entry

Crea `react-src/src/mi-isla/` con un `index.jsx` que auto-monte el componente:

```jsx
// src/mi-isla/index.jsx
import { mountIsland } from '../shared/mountIsland.js'
import MiIsla from './MiIsla.jsx'

mountIsland('mi-isla', MiIsla)   // busca [data-react-island="mi-isla"] y monta ahí
```

`mountIsland` no hace nada si no encuentra el contenedor: la misma isla puede coexistir
con páginas que no la usan sin romperlas.

### 2. Registrar la entry en Vite

En `react-src/vite.config.js`, añade la isla al objeto `ISLANDS`:

```js
const ISLANDS = {
  'diagrama-esftt': resolve(__dirname, 'src/diagrama-esftt/index.jsx'),
  'mi-isla':        resolve(__dirname, 'src/mi-isla/index.jsx'),   // ← nueva
}
```

### 3. Montarla en un template Jinja

```jinja
{% extends "layout/base_app.html" %}

{% block content %}
  <div id="app-root"
       data-react-island="mi-isla"
       {{ user_ctx_attrs() }}></div>
{% endblock %}

{% block extra_js %}
  {{ react_bundle('mi-isla') }}
{% endblock %}
```

- `{{ user_ctx_attrs() }}` inyecta `data-user`, `data-permisos`, `data-rol` del usuario y
  rol activo actuales (ver más abajo).
- `{{ react_bundle('mi-isla') }}` lee `manifest.json` y emite los `<link>`/`<script
  type=module>` con el hash actual. Si la isla no está compilada, emite vacío y loguea
  un warning (la página sigue sirviéndose).

### 4. Compilar

- **Windows (recomendado):** botón **"Build React"** en `scripts/flask_console.py`.
- **Terminal:** `bash scripts/build_react.sh` (hace `npm install` + `npm run build`).

Tras compilar, recarga la página en el navegador.

---

## Inyectar contexto desde Jinja → React

El backend es la única fuente de verdad de auth. Las islas **no autentican**; solo leen el
contexto que Jinja vuelca en data-attributes para condicionar la UI.

`{{ user_ctx_attrs() }}` emite, sobre el contenedor:

```html
data-user='{"id":1,"siglas":"CLG","nombre_completo":"Carlos López G."}'
data-permisos='["acceder_expediente","editar_expediente", ...]'
data-rol="TRAMITADOR"
```

Desde React, con `shared/auth.js`:

```jsx
import { getUser, getRolActivo, tienePermiso } from '../shared/auth.js'

getUser()                       // { id, siglas, nombre_completo }
getRolActivo()                  // "TRAMITADOR"
tienePermiso('editar_expediente') // true | false

// Condicionar un botón:
{ tienePermiso('gestionar_plantillas') && <BotonEditar /> }
```

> `data-permisos` se calcula del dict `PERMISOS` (`app/utils/permisos.py`) para el rol
> activo. **Esto solo oculta/muestra controles.** La autorización real la imponen los
> decoradores del backend en cada ruta/API — nunca confíes en el cliente para autorizar.

---

## Consumir APIs

`shared/api.js` envuelve `fetch` con el comportamiento estándar del proyecto:

```jsx
import { api, ApiError } from '../shared/api.js'

const data = await api.get('/api/expedientes/42')
await api.post('/api/expedientes/42/notas', { texto: 'Hola' })
```

El wrapper:

- Envía la **cookie de sesión Flask** (`credentials: 'same-origin'`).
- **401** → toast + redirección a `/auth/login`.
- **403** → toast de permiso denegado.
- **POST/PUT/DELETE** → añade `X-CSRFToken` desde el meta tag `csrf-token`.
- Otros errores → lanza `ApiError` con `status` y `payload`.

### Nota CSRF (pendiente de backend)

El proyecto **aún no instala Flask-WTF/CSRFProtect**. El meta tag de `base_app.html`
emite token vacío y, mientras esté vacío, `api.js` no añade el header. El cliente ya queda
preparado: al instalar Flask-WTF (cuando llegue la primera API mutante desde React, ADR-015
§3), el meta `csrf-token` se autorrellena con `csrf_token()` y el header empieza a viajar
sin tocar el JS.

---

## Usar componentes Bootstrap desde React

Bootstrap (bundle JS del CDN JdA) ya está cargado en todas las páginas como `window.bootstrap`.
Los wrappers de `shared/ui/` lo orquestan sin arrastrar CSS propio.

Toast (imperativo, desde cualquier JS):

```js
import { showToast } from '../shared/ui/toast.js'
showToast('Guardado', 'success')   // success | danger | warning | info
```

Toast (declarativo, desde React):

```jsx
import Toast from '../shared/ui/Toast.jsx'
{ guardadoOk && <Toast mensaje="Guardado" categoria="success" /> }
```

Para nuevos primitives (`Modal`, `Tooltip`…), seguir el mismo patrón: un helper que invoca
`new window.bootstrap.X(el)` y, si procede, un wrapper React encima.

---

## CSS: Bootstrap + JdA, sin excepciones

Los componentes React **usan exclusivamente las clases de Bootstrap 5.3 + el CDN JdA**.
Sin Tailwind, sin Material UI, sin shadcn/ui, sin ninguna librería con sistema visual propio.

### Tematizar una librería externa con CSS propio

Cuando una librería trae su CSS (xyflow, cmdk, react-arborist), se importa su hoja y se
**sobrescriben sus variables/clases** para respetar la paleta JdA. Ejemplo con xyflow en
`diagrama-esftt/styles/diagrama.css`:

```css
@import '@xyflow/react/dist/style.css';

/* Tematizado: sobrescribir las variables de xyflow con la paleta JdA */
.react-flow {
  --xy-node-background-color: var(--bs-primary);
  --xy-edge-stroke: var(--bs-border-color);
}
```

El CSS importado en JS lo extrae Vite a `asset.<isla>.<hash>.css` y `react_bundle()` lo
enlaza automáticamente. **Todo CSS externo nuevo requiere un pase de tematizado documentado**
(regla en `REGLAS_DESARROLLO.md`).

---

## Build y flujo de desarrollo

| | Desarrollo | Producción |
|---|---|---|
| Compilar | botón "Build React" / `build_react.sh` | `npm run build` en el deploy |
| Servir | Flask sirve los bundles estáticos | igual |
| Cambio en .jsx | recompilar + recargar navegador | — |

**Modo actual: rebuild** (editar → Build React → recargar). No hay dev server con HMR
integrado en Flask todavía: se decidió posponerlo a **#500** (árbol del expediente), donde
la iteración intensiva de UI compleja lo justifica (ADR-015 §4). `npm run dev` (Vite
standalone con `index.html`) sigue disponible para iterar un componente aislado.

### Formato de bundle: ES modules

Los bundles son **módulos ES** (`<script type="module">`), no IIFE. Esto permite **compartir
React y dependencias comunes** en un chunk entre todas las islas (con IIFE cada isla
duplicaría React). El navegador resuelve los imports del módulo automáticamente; `react_bundle()`
además emite `modulepreload` de los chunks compartidos.

---

## Verificación de una isla

- **Backend:** smoke test que la vista responde 200 y contiene `data-react-island="..."`.
- **Render:** Playwright MCP — la isla monta, renderiza y la consola no tiene errores rojos.
- **Permisos:** `tienePermiso(...)` devuelve lo correcto según el rol activo de sesión.
