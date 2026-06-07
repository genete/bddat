# ADR-022 — Sistema visual base: escala tipográfica única, tokens y tabla unificada

**Estado:** Adoptada
**Fecha:** 2026-06-07
**Issue:** #533
**Origen:** PRE-ADR `docs/diseño/PRE-ADR-workbench-listados.md` (sesión de revisión de altura del workbench).
**Relación:** prerrequisito de **ADR-023** (list-detail + inspector universal). Cierra parcialmente la decisión §5.5 de `ANALISIS_CRITICO.md` (sistema de diseño).

---

## Contexto

La base visual del revamping creció por capas (v0…v3, shell ADR-014) y no quedó unificada. Síntomas verificados en código:

- **Tres escalas tipográficas** conviven sin criterio único: `body` 16px (`v2-theme.css:92`), tablas 0.875rem/14px (`v2-components.css:120,137`), shell e inspector 13px hardcodeado en px (`app-shell.css:18,451`).
- **Dos sistemas de tabla** distintos: `data-table` (DIV + CSS Grid, `v2-data-table.css`) y `expedientes-table` (HTML `<table>`, `v2-components.css:99`). La base real de listados usa el segundo; el primero quedó sin consumir.
- **Truncados y recortes ad-hoc** por implementación: reglas `nth-child` por tabla, `plantillas-table td:nth-child(2){max-width:180px}`, media queries que ocultan columnas a mano. No hay un mecanismo general del que hereden las particularizaciones.
- **Recorte lateral ~95%** vía `--content-padding: max(1rem, 2.5vw)` (`v2-theme.css:14`), introducido para homogeneidad con los bloques redondeados (#202). Redundante cuando el listado vive en `main`, ya acotado por sidebar e inspector.

El principio de densidad ya estaba aterrizado (`ANALISIS_CRITICO §4.1`, "13-14px base") pero nunca se cerró en una decisión ni se ejecutó de forma global. Este ADR lo cierra.

Es **prerrequisito de ADR-023**: el patrón list-detail mete el detalle en el inspector y comprime el `main`; sin una escala densa y una tabla única, esa compresión rompe la legibilidad.

---

## Decisión

### 1. Escala tipográfica única y densa

- **Mando maestro por `rem` global.** Se fija `html { font-size: 14-15px }` (valor exacto a calibrar en implementación con verificación visual). Al estar Bootstrap y el CDN de la Junta dimensionados en `rem`, todo lo que va en `rem` se densifica de forma coherente con un único parámetro.
- **El shell pasa de `px` a `rem`.** Hoy el chrome (`app-shell.css`) usa px directos y queda fuera del mando. Se reexpresa en `rem` para que obedezca a la escala única.
- **Tokens tipográficos (`--fs-*`) solo para excepciones deliberadas** (p. ej. un dato numérico destacado en la cabecera del detalle, estilo Stripe). No son el mecanismo principal de densidad: el `rem` global lo es.

> Se descarta el enfoque de "solo tokens en px sin tocar el rem": perseguir cada componente uno a uno arriesga perpetuar la dualidad de escalas que este ADR elimina.

### 2. Tokens de color sin fugas

- Los hardcodeos del shell (`#ebebeb`, `#888`, `#666`, rgba sueltos…) se consolidan sobre las variables corporativas de `v2-theme.css` (`--primary`, `--gris-*`, `--border-color`, etc.).
- La identidad JdA se mantiene (principio §4.7): cambia la consistencia, no la paleta.

### 3. Componente de tabla único con overrides heredables

- **Un solo sistema de tabla** sustituye a la dualidad `data-table` / `expedientes-table`.
- **Mecanismo general de columnas y truncado**: ancho mínimo/máximo por columna, elipsis y **prioridad de ocultación responsive declarativa** (cada columna declara su prioridad; el sistema oculta de menor a mayor según el ancho disponible), en vez de `nth-child` ad-hoc por tabla.
- Las particularizaciones por listado **heredan** el general y solo añaden lo propio; no lo reescriben.

### 4. Retirada del recorte ~95% en `main`

- El listado en `main` ocupa el ancho disponible real; el recorte lateral por `--content-padding` deja de aplicarse a los listados del workbench. El recorte tenía sentido para bloques redondeados aislados, no para un maestro ya acotado por sidebar + inspector (ADR-023).

### 5. Excepciones tokenizadas — estudio de tamaños diferido

Dos áreas no escalan 1:1 con el contenido y se afinan por tokens propios **después** de fijar el rem global:

- **Dock**: panel tipo consola (líneas densas de bitácora/avisos), eje vertical. Su altura, densidad y el comportamiento del botón maximizar (listado completo / fetch ampliado) merecen estudio propio.
- **Sidebar**: alto de ítem e icono+label, token propio de navegación.

No bloquean este ADR; quedan como deuda acotada.

---

## Cómo implementar

1. Calibrar `html { font-size }` (14-15px) y reexpresar el shell en `rem`. Verificación visual con Playwright MCP de que el CDN Junta aguanta el reescalado sin descuadres.
2. Barrido de hardcodeos de color del shell → variables de `v2-theme.css`.
3. Diseñar el componente de tabla único (mecanismo de columnas + truncado + prioridad responsive) y migrar los listados existentes; eliminar `v2-data-table.css` si queda sin uso.
4. Retirar `--content-padding` de los listados del workbench.
5. Smoke tests pytest (ADR-019, Fase 1) de las vistas tocadas.

La migración de Plantillas y Usuarios a listado unificado (#281) se absorbe en este trabajo.

---

## Alternativas descartadas

### A. Solo tokens en px, sin tocar el `rem`
Control total pero exige tokenizar cada componente; lo que se escape perpetúa la dualidad de escalas. Descartada como mecanismo principal (sí se conserva para excepciones).

### B. Bajar el `rem` a 14px de golpe sin calibración
Riesgo de descuadrar componentes del CDN Junta sin red. Se prefiere calibrar el valor con verificación visual.

### C. Mantener los dos sistemas de tabla
Es el origen de los truncados ad-hoc y la deuda visual que cada listado nuevo reproduce. Descartada.
