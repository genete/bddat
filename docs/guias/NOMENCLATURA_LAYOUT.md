# Nomenclatura de áreas del layout — referencia rápida

> Vocabulario fijo para hablar y escribir código sobre las áreas del layout `base_app.html` (ADR-014).
> Esta página es la fuente de verdad cuando haya duda.

---

## Mapa visual

### Modo página (sin inspector, sin dock)

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

### Modo workbench (con inspector y dock activos)

```
┌──────────────────────────────────────────────────────────────────────┐
│                              topbar                                  │
├──────────┬─────────────────────────────────────────┬─────────────────┤
│          │                viewbar                  │                 │
│          ├─────────────────────────────────────────┤                 │
│          │                                         │                 │
│ sidebar  │                  main                   │    inspector    │
│          │                                         │                 │
│          ├─────────────────────────────────────────┴─────────────────┤
│          │                       dock                                │
├──────────┴───────────────────────────────────────────────────────────┤
│                              footer                                  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Tabla de referencia

| # | Función | Nombre | grid-area | CSS class | Bloque Jinja | Etiqueta HTML |
|---|---|---|---|---|---|---|
| 1 | Barra superior global | **topbar** | `topbar` | `.app-topbar` | (partial) | `<header>` |
| 2 | Navegación lateral persistente | **sidebar** | `sidebar` | `.app-sidebar` | (partial) | `<nav aria-label="Principal">` |
| 3 | Cabecera contextual de la vista | **viewbar** | `viewbar` | `.app-viewbar` | `{% block viewbar %}` | `<header>` |
| 4 | Cuerpo de la vista | **main** | `main` | `.app-main` | `{% block content %}` | `<main>` |
| 5 | Panel lateral derecho | **inspector** | `inspector` | `.app-inspector` | `{% block inspector %}` | `<aside>` |
| 6 | Panel inferior | **dock** | `dock` | `.app-dock` | `{% block dock %}` | `<section>` |
| 7 | Pie global | **footer** | `footer` | `.app-footer` | (partial) | `<footer>` |

---

## Cuándo se activa cada área opcional

- **topbar, sidebar, viewbar, main, footer**: siempre presentes en `base_app.html`.
- **inspector**: opcional. Se activa cuando la vista define `{% block inspector %}...{% endblock %}`. Si no, el grid colapsa esa columna a `0fr`.
- **dock**: opcional. Se activa cuando la vista define `{% block dock %}...{% endblock %}`. Si no, el grid colapsa esa fila a `0fr`.

Una vista de listado/formulario no define ni inspector ni dock — automáticamente queda en "modo página". Una vista tipo workbench (expediente) los define ambos y queda en "modo workbench".

---

## Aclaraciones importantes

- **`<main>` y `<footer>`** son etiquetas HTML semánticas legítimas. Se usan coordinadamente con `.app-main` y `.app-footer`. **Coincidencia deseada**, no conflicto.
- **`<header>` aparece dos veces** (topbar y viewbar). Ambos `<header>` semánticos. Las clases los distinguen.
- **`dock` NO es el dock de macOS**. Es el panel inferior anclable de la app (metáfora de IDEs: VS Code, Photoshop).
- **`inspector` NO es el inspector del navegador**. Es el panel lateral derecho de la app (metáfora de DevTools: "inspecciono el elemento seleccionado en main").
- **`sidebar` usa `<nav>`** por su función principal de navegación, no `<aside>`. Si albergara contenido no navegacional, usaría `<aside>`.

---

## Variables CSS

```css
--topbar-height
--sidebar-width-expanded     /* 240px por defecto */
--sidebar-width-collapsed    /* 60px por defecto */
--viewbar-height
--inspector-width            /* 380px por defecto */
--dock-height                /* 240px por defecto */
--footer-height
```

---

## `localStorage` keys

| Key | Tipo | Propósito |
|---|---|---|
| `bddat.sidebar.collapsed` | boolean | Estado del sidebar (expandido/colapsado) |
| `bddat.inspector.open` | boolean | Última elección del usuario sobre el inspector |
| `bddat.dock.open` | boolean | Última elección del usuario sobre el dock |

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
