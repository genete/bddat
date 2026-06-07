# ADR-023 — List-detail + inspector universal con negociación de espacio

**Estado:** Adoptada
**Fecha:** 2026-06-07
**Issue:** #534
**Depende de:** ADR-022 (#533) — escala densa y tabla unificada.
**Enmienda:** ADR-016 §14 (el inspector resizable se redefine como mecanismo de shell, ver §2).
**Origen:** PRE-ADR `docs/diseño/PRE-ADR-workbench-listados.md`.

---

## Contexto

La app tiene **dos paradigmas de interacción conviviendo**:

- **Árbol del expediente** (ADR-016): list-detail moderno. Seleccionas un nodo en `main` → el `inspector` muestra su detalle sin cerrar el árbol (ADR-016 §3/§5).
- **Listados v2**: navegación web clásica. Botón "Ver" por fila (`v2-scroll-infinito.js:208-216`, `window.location.href = detailUrl(id)`) → carga una página de detalle → botón "volver".

La coexistencia es el origen de la "maraña de accesos cruzados": cada vista de detalle necesita botones de retorno hacia su invocador. El inspector ya es, por nomenclatura (ADR-014), "el panel del elemento seleccionado en `main`" — pero solo el árbol lo explota.

Este ADR **unifica los listados bajo el mismo patrón list-detail** que el árbol, y formaliza el modelo de espacio que lo hace viable en pantallas reales.

---

## Decisión

### 1. Selección, no navegación

- Click en una fila → fila **seleccionada** + el `inspector` muestra su detalle en "modo reacción". El listado **no se cierra**.
- Desaparecen la columna "Ver"/acciones por fila y los botones de retorno.
- **Las vistas de detalle actuales se reaprovechan**, adaptadas al layout del inspector. No se tiran.
- Las acciones sobre el elemento (las que hoy se replican por fila) viven en el detalle del inspector.
- Sincronización con URL (`?sel=<id>`), igual que el árbol (ADR-016 §12): compartir enlace, recargar manteniendo selección, "atrás" coherente.

### 2. Inspector redimensionable a nivel de SHELL

El redimensionado del inspector sube de la isla React (ADR-016 §14) al **shell**:

- Implementación: CSS Grid del shell con `--inspector-width` como variable + un JS ligero y agnóstico que escucha el drag del splitter y persiste en `localStorage`.
- Funciona en **cualquier vista**, Jinja o React. Es lo que permite que los listados (Jinja puro) tengan inspector arrastrable, no solo el árbol.
- `react-resizable-panels` queda **solo para splitters internos de una isla** (p. ej. el split despensa/detalle del árbol en modo edición, ADR-016 §5). **Enmienda ADR-016 §14.**

### 3. Negociación de espacio — contrato de cuatro números (+1)

Cada vista declara sus mínimos; el shell reparte por aritmética:

- **`--main-min`**: lo declara el **listado**. Es el ancho de su **maestro reducido** (ver §6).
- **`[inspector_min, inspector_objetivo]`**: lo declara cada **tipo de detalle**.
  - `inspector_min` = ruptura: el ancho donde "todo tiene elipsis y ya no se puede apretar más". Por debajo → el inspector colapsa.
  - `inspector_objetivo` = lectura cómoda, sin apretar. Es el ancho al que el sistema lleva el inspector **automáticamente** al abrirlo, y el techo del crecimiento **automático** (no devora espacio que nadie pidió).
- **La viewbar entra en la negociación.** Comparte columna con `main` (`app-shell.css` grid: `"sidebar viewbar inspector"` / `"sidebar main inspector"`), así que sus controles no comprimibles fijan un suelo:

  > **`main_min = max(mínimo del contenido de main, mínimo de la viewbar)`**

  En la **isla árbol manda la viewbar**: el lienzo react-flow es elástico (zoom + pan absorben cualquier ancho), así que el árbol no aporta `main_min`; lo dicta la viewbar y sus botones.

### 4. Automático parco, manual libre

- **Automático** (al abrir/negociar): el inspector no pasa de su `inspector_objetivo`.
- **Manual** (drag del usuario): puede **superar el objetivo** para ganar aire (el contenido se relaja, como agrandar la ventana), hasta donde `main_min` lo permita. El objetivo es punto de partida inteligente, no jaula.
- Modelo "fractal": el inspector es a su contenido lo que la ventana es al workbench.

### 5. Regla de prioridad

Cuando los mínimos no caben todos a la vez, en este orden:

1. **`main_min` se respeta siempre** (calculado sobre el maestro reducido + viewbar, §3/§6).
2. El **sidebar colapsa** automáticamente (208 → 56 → 0) antes de que el inspector ceda. El drag manual de agrandar el inspector dispara esta misma cascada.
3. El **inspector cede** hasta su `inspector_min`.
4. Último recurso: **overlay** (§7).

### 6. Maestro reducido por tipo de listado

- Al abrir el inspector, el listado muestra solo sus **columnas esenciales** (técnica Gmail/Outlook/Linear): el detalle completo está en el inspector.
- Las columnas esenciales se **definen por tipo de listado**, no hay regla genérica "las N primeras". Expedientes/seguimiento tiene su esencial; Entidades el suyo.
- `--main-min` se calcula sobre ese maestro reducido.

### 7. Modo overlay (sustituye el corte duro de breakpoint)

- Hoy el responsive es un corte fijo `@media (max-width:768px)`: sidebar → off-canvas + backdrop, inspector → `display:none` (`app-shell.css:707-742`).
- Se generaliza: cuando push ya no respeta los mínimos (paso 4 de §5), sidebar e inspector pasan a **superponerse al `main`** (off-canvas + backdrop), accesibles por toggle. En vez de cerrarse y **perder** el detalle, el inspector se mantiene en overlay.
- **Disparo por espacio, no por píxel fijo**, con **histéresis** (umbral de entrada en overlay distinto del de salida) para no parpadear en el borde.
- Beneficia portátiles (≤1366) y pantallas verticales, donde el ancho es el recurso escaso.

---

## Reconciliación con ADR-016

- **§14 enmendado**: inspector resizable = mecanismo de shell (este ADR). `react-resizable-panels` solo para splitters internos de islas.
- **§3/§5 generalizados**: el patrón "seleccionar → inspector" del árbol se extiende a todos los listados.
- **§16 generalizado**: el endpoint de detalle lazy del árbol es el patrón a reutilizar para "detalle de entidad en inspector".

---

## Validación numérica (Expedientes)

Pantalla de referencia 1920×1080. Seguimiento (el listado más rico) = 53rem de columnas fijas (`custom.css:311`); sin la columna "Ver" = 48.5rem = **776px@16**.

- Inspector **900px** + sidebar colapsado (56) → `main` = **964px**. El seguimiento completo cabe con **~188px de holgura, incluso sin bajar el rem**.
- Conflicto solo en ≤1366px al combinar inspector muy grande + maestro completo: lo resuelven el maestro reducido (§6) y la regla de prioridad (§5).

Detalle de la tabla de reparto en el PRE-ADR §4.

---

## Alternativas descartadas

### A. Mantener el botón "Ver" + navegación
Es el origen de la maraña de retornos. Descartada.

### B. Split horizontal en `main` (maestro arriba / detalle abajo)
Genera scrolls verticales apilados antipáticos. Todo el detalle va al inspector. Descartada por decisión del usuario.

### C. Inspector resizable con `react-resizable-panels` a nivel de shell
No sirve: vive dentro de islas React; los listados Jinja no lo tendrían. El redimensionado debe ser del shell. Descartada.

### D. Bottom-sheet del inspector en pantallas verticales
Un tercer patrón distinto, más código. El overlay lateral (§7) ya cubre el caso. Descartada (sobre-diseño).

### E. Corte responsive por breakpoint fijo
El paso a overlay por píxel fijo (768) es arbitrario frente a la negociación de mínimos. Sustituido por disparo por espacio con histéresis (§7).
