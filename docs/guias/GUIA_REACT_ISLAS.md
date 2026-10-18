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
      subida.js                    ← quita los comprimidos al elegir ficheros (wrapper de subida-comprimidos.js)
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
con páginas que no la usan sin romperlas. Acepta un tercer parámetro opcional
(`mountIsland('mi-isla', MiIsla, { propInicial: valor })`) para pasar props al montar —
lo usa la carga diferida del palette (#563, ver más abajo) para arrancar ya abierto.

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

## Isla global (vs isla por vista)

La mayoría de islas son **por vista**: una plantilla concreta pone el contenedor y monta el
bundle en su `{% block content %}` / `{% block extra_js %}`. Solo se cargan en esa página.

Una **isla global** se monta en el shell `base_app.html`, así que **se carga en TODAS las
páginas autenticadas**. Caso de referencia: el **Command Palette** (Ctrl+K, #532, ADR-018).

Diferencias frente a una isla por vista:

- **El contenedor lo pone el shell, no la vista.** Va al final de `base_app.html`, dentro de
  `{% if current_user.is_authenticated %}`:
  ```jinja
  <div data-react-island="command-palette"
       {{ user_ctx_attrs() }}
       data-nav='{{ palette_nav() | tojson }}'></div>
  {{ react_bundle('command-palette') }}
  ```
- **Se carga en todas las páginas → mantener el bundle ligero, o diferirlo.** Cada dependencia
  pesa en cada carga; no es el sitio para librerías grandes sin más. El palette resuelve esto
  con carga diferida (#563, ver abajo): lo que se carga en todas las páginas es un stub de
  unas pocas líneas, no React ni sus dependencias.
- **Datos del shell por data-attribute.** Además de `user_ctx_attrs()`, una isla global puede
  recibir datos calculados en servidor. El palette recibe `data-nav` con los atajos "IR A",
  derivados de `palette_nav()` (`app/utils/react_islas.py`) — **misma fuente que el sidebar**
  (`ModuleRegistry`), no una lista hardcodeada: un módulo nuevo aparece solo y una ruta
  inexistente nunca se enlaza.
- **Atajos de teclado globales.** Antes de la primera activación los captura el stub en JS
  plano (ver abajo); montado el componente real, sus propios `useEffect` toman el relevo. Si
  el atajo coincide con uno del shell (`app-shell.js`), el shell cede: Ctrl+K lo gobierna la isla.

### Carga diferida de una isla global pesada (#563)

Si la isla global arrastra una librería grande (el palette: `cmdk` + Radix, ~46 KB gzip) pero
solo se activa bajo demanda (Ctrl+K), no hace falta pagar ese peso en cada carga de página.
Patrón — ver `react-src/src/command-palette/` como referencia:

1. **El entry (`index.jsx`) es un stub sin React ni la librería pesada**: solo engancha los
   listeners planos que detectan la activación (`keydown` global, clic en el disparador del
   topbar).
2. **A la primera activación, `import()` dinámico** del componente real (y de `mountIsland.js`,
   que también arrastra React) y se monta ya con el estado que corresponda al gesto que lo
   disparó (p. ej. `abrirInicial: true`) — el usuario no pierde el gesto que activó la carga.
   Vite separa ese `import()` en su propio chunk: no se descarga hasta que se llama.
3. **El stub retira sus propios listeners al activar**, antes de que se resuelva el import: a
   partir de ahí el componente montado gobierna con los suyos (mismo `useEffect` que ya tenía).
4. **El CSS de la isla se importa dentro del componente pesado, no en el stub** (`import
   './styles/palette.css'` en `CommandPalette.jsx`), para que Vite lo asocie al chunk diferido
   y no al entry.
5. **`vite.config.js` necesita `base: '/static/js/react/'`** en el build. Sin ella, el código
   que Vite genera para resolver el `import()` dinámico (y el CSS que arrastra) construye URLs
   contra la raíz del dominio en vez de `/static/js/react/`, y el chunk da 404 — un límite que
   solo se nota en cuanto una isla usa `import()` dinámico por primera vez; los `<script>`/
   `<link>` estáticos no lo necesitan porque `react_bundle()` (Jinja) ya construye esas URLs
   a mano con `url_for('static', ...)`.
6. **`mountIsland(nombre, Component, props)` acepta props** para pasarle al componente montado
   el estado inicial derivado del gesto de activación (tercer parámetro opcional).

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

## Inspector overlay desde una isla React (ADR-023)

El inspector es un **overlay de shell** (`window.AppInspector`), no una columna del grid.
Las islas React interactúan con él sin definir `{% block inspector %}` — solo notifican al
shell cuándo abrir/cerrar y cuándo entrar/salir de edición.

### Patrón de selección ↔ inspector (bidireccional)

```js
// En el effect de selección del store (p.ej. al clicar un nodo):
AppInspector.mountReact({ selId: nodo.id })

// Al deseleccionar (o al recibir el evento de cierre desde el panel):
AppInspector.close()

// Escuchar el cierre desde el panel (clic en ×, Escape, light-dismiss):
document.addEventListener('inspector:closed', () => {
  store.deseleccionar()  // coherencia bidireccional
})
```

### Edición en el inspector

```js
// Al entrar en modo edición:
AppInspector.setLocked(true)   // activa backdrop bloqueante

// Al guardar o cancelar:
AppInspector.setLocked(false)  // desbloquea
AppInspector.refresh()         // si el contenido es un fragmento Jinja
```

### El marco (barra) lo pinta el shell, no la isla (ADR-053 §A, #1042)

La cabecera del nodo (tipo, título, estado, candado, semáforo) y los botones Editar / Guardar /
Cancelar-Cerrar **no se pintan en React**: los pinta una barra del shell
(`#app-inspector-bar`), y la isla solo la alimenta con datos por `AppInspector.setFrame(...)`.
El árbol lo hace con un hook, `usePuenteInspector` (`expediente-arbol/puenteInspector.js`), que
construye el descriptor a partir del store y lo empuja solo cuando cambia (el borrador cambia
con cada tecla; el descriptor casi nunca). Los gestos del descriptor (`onEditar`, `onGuardar`,
`onSalir`) leen el store en el momento de pulsar, no capturan estado de un render.

Una isla nueva con inspector copia ese patrón en vez de pintar su propia barra; la forma del
descriptor y el resto del contrato (qué enciende «Guardar», ancho mínimo, rótulos) están en
`GUIA_COMPONENTES_INTERACTIVOS.md` §«Marco único del inspector». El cuerpo de la isla (lo que
hay debajo de la barra) no hace scroll por su cuenta: hace scroll el cuerpo del shell.

### El cuerpo del inspector del árbol: un diseño por nodo (ADR-053 §C, #1043)

Lectura y edición pintan **la misma zona de datos**; la edición añade debajo las acciones. Qué se ve
en cada nodo está en la tabla del anexo a ADR-053 §C. El código, en `expediente-arbol/`:

| Pieza | Qué hace |
|---|---|
| `disenosDatos.js` | Un diseño por nodo (`DISENO_*`) y `disenoDeNodo(tipo, {tareaConDiseno})`: tarjetas, campos (`etiqueta` del payload, `campo` del esquema editable, `col`, `control`, `visibleSi`, `valorDe`, `opcional`) y `ocultas` (lo que ya está en la barra del marco). Lo que el payload trae y el diseño no conoce cae en «Otros datos»: no se pierde nada en silencio |
| `components/DatosNodo.jsx` | Pinta un diseño igual en los dos modos: control de solo lectura en lectura, vivo en edición, en el mismo sitio y con el mismo rótulo |
| `components/TarjetaDatos.jsx` | `TarjetaDatos`, `CampoDato`, `ValorSoloLectura`, `CasillaSoloLectura`, `ControlCampo` (el select conserva el tipo del valor de la opción) |
| `components/Inspector.jsx` | `ZonaDatos` (el diseño y las tarjetas propias del nodo) e `InspectorEdicion` (datos → Despensa → acciones propias → «Borrar» → pie «Copiar referencia») |
| `superficiesTarea.js` | Qué superficie lleva una tarea: tabla `SUPERFICIES_TAREA` con `defecto`, `variante(nodo)` y `porTramite` |

**Para migrar o crear un nodo:** añadir su diseño en `disenosDatos.js`; si tiene bloques propios,
llevar los de dato a `ZonaDatos` (tarjetas, en los dos modos) y los de acción al grupo de acciones de
`InspectorEdicion` (`hayPropias`), solo en edición. Nada más cambia.

**Una tarea es genérica por ausencia.** Su superficie la decide la combinación (tipo de tarea, trámite)
en `superficiesTarea.js`; lo que no figura en la tabla usa el diseño común sin tocar nada, aunque la
semilla no tenga ningún caso. Una variante la dice el nodo del árbol con un dato que pone el backend (el
de ANALIZAR, `analisis_extendido`, sale de una única lista de trámites), no una lista repetida en el
front. Una superficie nueva se añade a la tabla, a `SUPERFICIES_CON_DISENO` y a `ZonaDatos`.

**Criterios que no son obvios**

- **Estado y Tipo solo en la barra del marco.** No se repiten en el cuerpo (`ocultas`).
- **No se toca el payload ni el esquema editable** para igualar lectura y edición; el diseño decide el
  orden y qué es editable. Las incoherencias que parezcan un bug se anotan como hallazgo, no se
  corrigen de paso.
- **Un bloque que guarda por su cuenta** (secciones de ANALIZAR, registro y destinatario de NOTIFICAR,
  destinatario de ELABORAR) no pasa por el borrador del marco. Si al guardar refresca el árbol, usa
  `refrescarArbolSilencioso` o `refrescarDetalleSilencioso` (no `refrescarArbol`/`cargarDetalle`, que
  vacían el detalle y remontan la zona de datos: se perdería lo escrito en las demás tarjetas, como
  Notas sin guardar). El aviso de «Cerrar» sobre lo que quede sin guardar es #1055.
- **El estado que comparten una tarjeta y su acción** (notificaciones del trámite, análisis,
  destinatario, notificar) vive en un store de zustand con el id del nodo (`notificarEstado.js`,
  `analizarEstado.js`, `destinatarioEstado.js`, `useNotificacionesTramite`), para no parpadear al
  refrescar el árbol y para que la acción actualice la tarjeta sin depender de un remonte.
- **Un bloque que copia el payload a un formulario** (el registro de NOTIFICAR) no se pinta hasta que
  llega el payload de esa visita: el formulario se inicializa al montarse.
- **Medida:** ningún campo de texto por debajo de 110 px a 320 px de inspector; por eso se reparte 6+6 y
  no 8+4, y no se declara `minWidth`.

### Slot Jinja para islas

El `{% block inspector %}` sirve como punto de montaje para islas que pientan dentro
del cuerpo del panel. La isla no necesita gestionar el `<aside>` — solo su propio
contenedor dentro de `#app-inspector-body`.

```jinja
{% block inspector %}
  {# La isla árbol pinta aquí su slot de detalle #}
  <div id="arbol-inspector-slot"></div>
{% endblock %}
```

### Excepciones de los editores de tarea (bespoke)

*(Desde #1043 los editores de ANALIZAR, ELABORAR y NOTIFICAR son tarjetas de datos y acciones del
diseño común; el criterio de abajo sigue valiendo para lo que `InspectorEdicion` condiciona por
superficie, que #1047 sustituirá por un registro de editores.)*

Los editores de ANALIZAR, ELABORAR y NOTIFICAR condicionan a veces algo del contenedor
común (`InspectorEdicion`). Criterio para factorizar una excepción en un patrón
compartido: no basta con contar apariciones. Una excepción que aparece en un solo editor
sigue siendo un caso único (factorizarla sería generalizar a partir de N=1). Pero si una
**segunda** excepción nace de la **misma causa raíz** (p. ej. «el editor gestiona su
propio vínculo de documento y por eso el mecanismo genérico deja de tener sentido»), ya
es un patrón: señalarlo como candidato a factorizar con una interfaz (cada editor declara
si gestiona su propio vínculo) y no seguir apilando condicionales `esAnalizar`/`esX` en el
contenedor. No esperar a una tercera aparición ni copiar el condicional sin más.

---

## Verificación de una isla

- **Backend:** smoke test que la vista responde 200 y contiene `data-react-island="..."`.
- **Render:** Playwright MCP — la isla monta, renderiza y la consola no tiene errores rojos.
- **Permisos:** `tienePermiso(...)` devuelve lo correcto según el rol activo de sesión.
