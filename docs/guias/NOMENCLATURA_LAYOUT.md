# Nomenclatura de áreas del layout — referencia rápida

> Vocabulario fijo para hablar y escribir código sobre las áreas del layout `base_app.html` (ADR-014).
> Esta página es la fuente de verdad cuando haya duda.

---

## Mapa visual

### Sin inspector

```
┌──────────────────────────────────────────────────────────────────────┐
│                              topbar                                  │
├──────────┬───────────────────────────────────────────────────────────┤
│          │                       viewbar                             │
│          ├───────────────────────────────────────────────────────────┤
│          │                                                           │
│ sidebar  │                                                           │
│          │                          main                             │
│          │                                                           │
│          │                                                           │
├──────────┴───────────────────────────────────────────────────────────┤
│                              footer                                  │
└──────────────────────────────────────────────────────────────────────┘
```

### Con inspector abierto (overlay sobre main)

```
┌──────────────────────────────────────────────────────────────────────┐
│                              topbar                                  │
├──────────┬───────────────────────────────────────────────────────────┤
│          │                       viewbar                             │
│          ├───────────────────────────────────────────────────────────┤
│          │                              ┌──────────────────────────┐ │
│ sidebar  │                              │       inspector          │ │
│          │        main                  │   (overlay, fixed right) │ │
│          │       (sin reflow)           │                          │ │
│          │                              └──────────────────────────┘ │
├──────────┴───────────────────────────────────────────────────────────┤
│                              footer                                  │
└──────────────────────────────────────────────────────────────────────┘
```

> El inspector **no empuja ni reflowa** el `main`. Es un panel `position:fixed`
> superpuesto sobre el borde derecho del viewport. Modelo de tres capas: **listado
> (main) → inspector (overlay) → modal grande (overlay sobre inspector)**.

---

## Tabla de referencia

| # | Función | Nombre | grid-area | CSS class | Bloque Jinja | Etiqueta HTML |
|---|---|---|---|---|---|---|
| 1 | Barra superior global | **topbar** | `topbar` | `.app-topbar` | (partial) | `<header>` |
| 2 | Navegación lateral persistente | **sidebar** | `sidebar` | `.app-sidebar` | (partial) | `<nav aria-label="Principal">` |
| 3 | Cabecera contextual de la vista | **viewbar** | `viewbar` | `.app-viewbar` | `{% block viewbar %}` | `<header>` |
| 4 | Cuerpo de la vista | **main** | `main` | `.app-main` | `{% block content %}` | `<main>` |
| 5 | Panel lateral derecho | **inspector** | *(overlay, no grid-area)* | `.app-inspector` | `{% block inspector %}` *(solo slot para islas React)* | `<aside>` |
| 6 | Panel inferior | **dock** | `dock` | `.app-dock` | (partial) | `<section>` |
| 7 | Pie global | **footer** | `footer` | `.app-footer` | (partial) | `<footer>` |

---

## Cuándo se activa cada área opcional

- **topbar, sidebar, viewbar, main, footer**: siempre presentes en `base_app.html`.
- **dock**: siempre presente en `base_app.html` como partial de chrome global. Su visibilidad la controla el usuario mediante la campana 🔔 del topbar (toggle). Estado en `localStorage` (`bddat.dock.open`). Las vistas no lo definen ni lo sobreescriben. Ver ADR-020.
- **inspector**: siempre presente en `base_app.html` como contenedor de shell (recogido por defecto). **No es una columna del grid**: es un overlay `position:fixed` en el borde derecho. Se abre/cierra mediante `window.AppInspector` (JS) al seleccionar un ítem en cualquier vista. El `{% block inspector %}` existe solo para que las islas React monten su slot dentro del body del panel; las vistas Jinja no lo definen.

El grid del shell es siempre `sidebar | main` (+ filas viewbar/dock/footer). El inspector no ocupa área de grid y **nunca reflowa** el contenido.

---

## Aclaraciones importantes

- **`<main>` y `<footer>`** son etiquetas HTML semánticas legítimas. Se usan coordinadamente con `.app-main` y `.app-footer`. **Coincidencia deseada**, no conflicto.
- **`<header>` aparece dos veces** (topbar y viewbar). Ambos `<header>` semánticos. Las clases los distinguen.
- **`dock` NO es el dock de macOS**. Es el panel inferior anclable de la app (metáfora de IDEs: VS Code, Photoshop).
- **`inspector` NO es el inspector del navegador**. Es el panel lateral derecho de la app (metáfora de DevTools: "inspecciono el elemento seleccionado en main").
- **`sidebar` usa `<nav>`** por su función principal de navegación, no `<aside>`. Si albergara contenido no navegacional, usaría `<aside>`.

---

## Variables CSS

**Escala tipográfica — mando maestro** (`v2-theme.css`, ADR-022 / #533): un único
parámetro gobierna la densidad; como el shell, Bootstrap y el CDN Junta van en
`rem`, cambiarlo los reescala de forma coherente.

```css
html { font-size: 15px; }   /* a 15px: datos de tabla ~13px, chrome ~14px */
```

**Dimensiones del shell** (`app-shell.css`):

```css
--topbar-height              /* 48px */
--viewbar-height             /* 44px */
--footer-height              /* 28px */
--sidebar-width-expanded     /* 208px */
--sidebar-width-collapsed    /* 56px */
--inspector-width            /* 900px (default de apertura; ajustable por el usuario) */
--dock-height                /* 240px */
```

> Los `font-size` del shell van en `rem` y obedecen al mando maestro. Las
> alturas/anchuras de layout permanecen en px. La densidad propia de **sidebar**
> y **dock** queda diferida (ADR-022 §5).

---

## Clases de estado del shell

| Clase | Sobre | Significado |
|---|---|---|
| `.app-shell.is-inspector-open` | `<body>` | Inspector visible (overlay desplegado) |
| `.app-shell.is-inspector-locked` | `<body>` | Inspector en modo edición — backdrop bloqueante activo |

---

## `localStorage` keys

| Key | Tipo | Propósito |
|---|---|---|
| `bddat.sidebar.collapsed` | boolean | Estado del sidebar (expandido/colapsado) |
| `bddat.inspector.width` | number (px) | Ancho del inspector persistido tras resize (default 900) |
| `bddat.dock.open` | boolean | Última elección del usuario sobre el dock |

> `bddat.inspector.open` ha quedado en desuso (ADR-023 #534): el inspector ya no se
> "deja abierto vacío"; se abre al seleccionar un ítem y se cierra al deseleccionar.

---

## Modelo de tres capas (ADR-023)

Las vistas list-detail operan con tres capas superpuestas en una sola página:

```
listado (main)                     ← capa base, nunca se abandona
  └─ inspector (overlay)           ← lectura + edición de campos del elemento
       └─ modal grande (.modal-app-xl) ← gestión compleja (sub-colecciones, CRUD)
```

- **Capa 1 — listado**: la vista Jinja/React en `main`. Siempre visible.
- **Capa 2 — inspector**: overlay `position:fixed`, anclado al borde derecho. Se abre
  al seleccionar una fila (`AppInspector.open()`). En lectura es no modal (el main sigue
  interactivo). En edición de campos, `AppInspector.setLocked(true)` activa el backdrop
  bloqueante (`is-inspector-locked`).
- **Capa 3 — modal grande**: Bootstrap modal con clase `.modal-app-xl` (maximizado con
  margen), apilado sobre el inspector. Se lanza desde el inspector para gestión compleja
  que no cabe en el panel (sub-tablas con CRUD propio). Al cerrarse refresca el inspector.

---

## Convención de lenguaje

En conversación, commits, issues y ADRs:

- **Sustantivos**: "el topbar", "el sidebar", "la viewbar", "el inspector", "el dock", "el footer".
- **Verbos**: "colapsar el sidebar", "abrir el inspector", "anclar/desanclar el dock", "renderizar la viewbar".
- **Prefijo de commits que tocan estas áreas**: `[UI][topbar]`, `[UI][sidebar]`, `[UI][viewbar]`, `[UI][inspector]`, `[UI][dock]`, `[UI][footer]`.

---

## Referencias

- **ADR-014** — `docs/decisiones/ADR-014-layout-app-unificado.md` (decisión completa con justificación)
- **Issue #498** — implementación del layout
