# ADR-023 — List-detail + inspector universal (overlay y capas)

**Estado:** Adoptada
**Fecha:** 2026-06-07
**Revisado:** 2026-06-10 — (1) el inspector pasa de columna negociada (*push*) a **overlay nativo**, eliminando la negociación de espacio; (2) se define el modelo de **tres capas** (listado · inspector · modal grande) con **navegación por capas, no por rutas**, y el inspector como base de **lectura y edición de campos**. Ver §"Historial de la decisión".
**Issue:** #534
**Depende de:** ADR-022 (#533) — escala densa y tabla unificada.
**Enmienda:** ADR-016 §14 (el inspector resizable se redefine como mecanismo de shell, ver §3).
**Origen:** PRE-ADR `docs/diseño/PRE-ADR-workbench-listados.md`.

---

## Contexto

La app tiene **dos paradigmas de interacción conviviendo**:

- **Árbol del expediente** (ADR-016): list-detail moderno. Seleccionas un nodo en `main` → el `inspector` muestra su detalle sin cerrar el árbol (ADR-016 §3/§5).
- **Listados v2**: navegación web clásica. Botón "Ver" por fila (`v2-scroll-infinito.js:208-216`, `window.location.href = detailUrl(id)`) → carga una **página de detalle** (ruta propia) → botón "volver".

La coexistencia es el origen de la **"maraña de accesos cruzados"**: cada vista de detalle es una ruta con sus botones de retorno hacia el invocador. La causa raíz no es "dónde se muestra el detalle", sino que **detalle y edición son rutas distintas** a las que se navega.

Este ADR unifica los listados bajo el patrón del árbol y, sobre todo, **sustituye la navegación entre rutas por capas superpuestas en una misma página** (§1), apoyadas en un inspector overlay (§2-§5) y un tercer modo modal para la gestión compleja (§6).

---

## Decisión

### 1. Selección por capas, no navegación

El modelo es de **tres capas superpuestas en una sola página**, no de rutas encadenadas:

```
listado (main)            ◄── capa base, nunca se abandona
  └─ inspector (overlay)        ◄── lectura + edición de los campos del elemento (§5)
       └─ modal grande (overlay) ◄── gestión compleja que no cabe en el panel (§6)
```

- Click en una fila → fila **seleccionada** + el `inspector` muestra su detalle. El listado **no se cierra**.
- **"Volver" = cerrar la capa de encima**, no navegar atrás. No hay botones de retorno porque **no hay cambio de ruta**: cerrar el modal reaparece el inspector que estaba debajo; cerrar el inspector deja el listado con su fila seleccionada. La capa inferior **siempre sigue ahí**, solo tapada.
- **Las páginas de detalle/edición dejan de ser destinos de navegación.** Su **contenido se reaprovecha** troceado en fragmentos (inspector / modal); **no se tira**. Desaparecen la columna "Ver"/acciones por fila y los botones de retorno.
- **Rutas** (ver §9): la ruta de detalle de página (`/entidades/<id>`) se **conserva** pero **redirige a `/entidades?sel=<id>`** (enlaces externos y marcadores siguen vivos, sin maraña). Las rutas **POST de mutación se conservan**, devolviendo fragmento/JSON para refrescar la capa.
- Sincronización con URL (`?sel=<id>`), igual que el árbol (ADR-016 §12): compartir enlace, recargar manteniendo selección, "atrás" coherente. La navegación de UI, sin embargo, es por **capas**, no por la pila del navegador.

### 2. Inspector = overlay a nivel de SHELL

El inspector **no es una columna del grid**: es un **panel overlay anclado al borde derecho** del shell, superpuesto sobre `viewbar` + `main`. **No empuja ni reflowa** el contenido.

- **Anclaje vertical**: desde debajo del `topbar` hasta encima del `footer`, descontando el `dock` cuando esté abierto. Es decir, **tapa la `viewbar` y el `main`; respeta `topbar`, `dock` y `footer`**. El razonamiento:
  - **`viewbar` tapada**: muestra acciones/título *de la vista*, no del elemento; nada en ella se necesita accionar con el detalle abierto. Se gana su altura.
  - **`topbar` respetado**: es la navegación e identidad global (buscador/command palette, campana del `dock` con su badge de avisos, menú de usuario). Taparlo desorienta y oculta avisos en vivo.
  - **`dock` respetado**: es feedback en vivo (bitácora/avisos) que las acciones del inspector **generan**; además es *toggleable*, así que quien quiera ese espacio vertical cierra el `dock` él mismo (descontar da control; tapar lo quita).
  - **`footer` respetado**: romper el marco inferior por ~28px no compensa.
- **Mecanismo de shell**: CSS del shell + un JS ligero y agnóstico + `localStorage`. Funciona en **cualquier vista**, Jinja o React. Es lo que permite que los listados (Jinja puro) tengan inspector, no solo el árbol.
- **Sin selección → recogido** (no ocupa espacio): el `main` usa el 100 % del ancho. Esto sustituye al "panel vacío con texto" que el árbol muestra hoy.
- `react-resizable-panels` queda **solo para splitters internos de una isla** (p. ej. el split despensa/detalle del árbol, ADR-016 §5). **Enmienda ADR-016 §14.**

### 3. Estados y transiciones — `popup`/`popdown` vs `swap`

Dos ejes de estado **independientes**: *visible/oculto* y *selección actual*. Las animaciones se atan a *visible/oculto*, **no** a la selección:

| Transición | Comportamiento |
|---|---|
| oculto → seleccionar un ítem | **popup** (slide-in desde la derecha) |
| visible → cambiar de ítem (A→B) | **swap del contenido in-place** (crossfade); el panel **no se mueve** — actúa como fijo |
| visible → clic en fondo / Escape / cerrar | **popdown** (slide-out) |
| oculto → reclicar el último ítem | **popup instantáneo** con el detalle retenido (§7) |

Mientras navegas encadenado, el inspector se queda quieto y solo cambia el detalle: no hay parpadeo de entrada/salida entre ítems.

### 4. Dismiss y no-modalidad en lectura

En **lectura** el inspector es **no modal**: el `main` sigue vivo bajo el overlay. (Edición del inspector y modal grande sí son modales — §5, §6.)

- **No hay backdrop bloqueante** en lectura (a lo sumo, atenuado visual con `pointer-events: none`). La franja **visible** del `main` (izquierda) conserva sus interacciones: **scroll** por rueda/teclado/trackpad, **hover** de filas y **tooltips**. La franja **tapada** por el overlay no es apuntable (inocuo: su información está en el detalle).
- **Light-dismiss** disparado por **clic en fondo no seleccionable**, no por "clic fuera del panel":
  - clic en **otra** fila/nodo → cambia la selección (*swap*), **no** cierra.
  - reclic en la fila **seleccionada** → toggle-cerrar.
  - clic en zona **vacía** / fondo → cerrar.
  - **rueda/scroll** → nunca cierra.
- La **fila seleccionada** lleva un estado visual **persistente**, distinto del *hover* (los listados hoy solo tienen *hover*; hay que añadirlo).
- **Scrollbar**: en listados, la scrollbar vertical del `main` queda **tapada** por el overlay (ambos en el borde derecho). Es inocuo y reversible al cerrar; el scroll por rueda/teclado sigue operativo. **No se reserva hueco** para ella (reflowaría el `main`). En el árbol no aplica (react-flow es pan/zoom, sin scrollbar clásica).
- **Tooltips**: vigilar que el `z-index` del tooltip quede **por encima** del overlay, para que el globo de una celda visible pegada al borde no quede cortado.

### 5. Inspector: lectura y edición de campos

El inspector es la base de **lectura y de edición de los campos directos** del elemento (sus atributos escalares: nombre, NIF, email, dirección, roles, activo, notas…). No es solo lectura.

- En **lectura** es no modal (§4).
- Al **entrar en edición** de campos, comportamiento idéntico al actual del árbol:
  - **Backdrop bloqueante** sobre el resto de la UI (captura clics y avisa "Guarda o cancela primero").
  - **Light-dismiss desactivado** (clic fuera no recoge el inspector).
  - `beforeunload` si hay cambios sin guardar.
- **Guardar** persiste (POST de mutación, §9) y refresca el inspector en lectura. El overlay + backdrop *es*, literalmente, un modal lateral: encaja con la decisión de bloqueo ya tomada en ADR-016.

### 6. Tercer modo — modal grande para gestión compleja

Lo que **no cabe** en el inspector escala a un **modal grande** (maximizado con margen), no a una página:

- **Criterio inspector vs modal** (generalizable, no caso por caso):
  - **campo escalar / directo** del registro → **inspector** (§5).
  - **colección / relación con CRUD propio** (sub-tablas con su alta/edición: p. ej. "Direcciones de notificación" y "Autorizaciones" de la entidad) → **modal grande**.
- **Comportamiento**:
  - Se lanza **desde el inspector** (botón "Gestionar …" en la sección correspondiente).
  - **Maximizado con margen** (casi pantalla completa, dejando ver el borde del contexto), apilado **sobre** el inspector (capa 3); es **modal** (backdrop bloqueante).
  - Al **cerrarse** vuelve a la capa inferior (el inspector), que **se refresca** con los datos que el modal modificó. No hay navegación: es cerrar una capa (§1).
  - Gestiona **una sección concreta**, no la ficha entera — así no degenera en "la página de antes con otro nombre".
- Es un **mecanismo de shell** disponible para cualquier vista; el árbol puede no usarlo todavía (su gestión —despensa— ya vive en el inspector).

### 7. Retención del detalle

- **Ocultar ≠ destruir**: se conserva el **último** detalle cargado. Reabrir **ese mismo** ítem es **instantáneo**, sin nueva petición.
- **Solo se retiene el último**: no hay caché multi-ítem. Reseleccionar un ítem distinto del último recarga su detalle (y al hacerlo se invalida cualquier estado obsoleto de una mutación previa).

### 8. Ancho del inspector

- **Ancho de apertura por defecto: 900px** (base). Ajustable: si una vista de detalle concreta necesita más, se sube cuando aparezca esa necesidad, no antes.
- **Resize** por arrastre del borde **izquierdo** del panel; ancho **persistido** en `localStorage`.
- Acotado por un **mínimo de lectura** (cifra concreta diferida a la implementación, cuando un detalle real defina dónde rompe) y por el ancho del *viewport*. **No negocia con el `main`**: el overlay se superpone; si el *viewport* es estrecho, el panel se aproxima al ancho completo.
- No hay "automático parco / manual libre" ni `inspector_min`/`inspector_objetivo` como contrato de negociación: el ancho lo gobierna el usuario, no la aritmética del shell.

### 9. Incrustación del contenido y rutas

- **Mecanismo**: un endpoint sirve el **fragmento** del detalle (generaliza el detalle lazy de ADR-016 §16) → se **inyecta** en el contenedor del inspector. El mismo mecanismo sirve el contenido del **modal grande**. Es **idéntico** en Jinja o React.
- El **layout interno** se **adapta** a su capa: el detalle del inspector a una **columna fluida** (panel estrecho); el modal grande puede usar varias columnas. Se **reaprovecha contenido y datos** de las vistas existentes; no se reescriben desde cero.
- **Rutas** (ver §1):
  - Las páginas **GET** de detalle/edición dejan de ser destinos; su contenido pasa a fragmentos.
  - La ruta de detalle de página se **conserva** como **redirect a `…?sel=<id>`** (no rompe enlaces externos).
  - Las rutas **POST de mutación se conservan**, devolviendo fragmento/JSON para refrescar la capa que toca (inspector o modal).

---

## Reconciliación con ADR-016

- **§14 enmendado**: inspector resizable = mecanismo de shell (este ADR). `react-resizable-panels` solo para splitters internos de islas.
- **§3/§5 generalizados**: el patrón "seleccionar → inspector" del árbol se extiende a todos los listados, con edición de campos en el inspector y gestión compleja en modal grande.
- **§16 generalizado**: el endpoint de detalle lazy del árbol es el patrón a reutilizar para el fragmento del inspector y del modal (§9).

---

## Historial de la decisión

- **2026-06-07** — Adoptada con el inspector como **columna del grid con negociación de espacio**: contrato de "cuatro números + uno" (`--main-min`, `inspector_min`, `inspector_objetivo`), colapso en cascada del sidebar, maestro reducido por tipo de listado, y overlay solo como **último recurso** responsive con histéresis.
- **2026-06-10** — Revisión en dos pasos:
  1. **Overlay nativo** sustituye a la negociación. Motivo: la negociación era la parte más frágil y cara (estados acoplados, *reflow* del `main` —lienzo react-flow y `ResizeObserver` del seguimiento—, parpadeo en umbrales). El overlay ya estaba en el plan como último recurso; promoverlo a modelo único elimina negociación, cascada del sidebar, histéresis y maestro reducido obligatorio. Como el issue **no se había implementado**, el coste fue casi solo documental. Pérdida asumida: la visibilidad simultánea total en el árbol, mitigada por pan/zoom y por el *swap in-place* (§3). La validación numérica del PRE-ADR §4 queda como memoria: ya no aplica.
  2. **Modelo de tres capas + edición en el inspector + modal grande.** Al acotar el alcance se vio que "el inspector muestra lectura y para editar/gestionar se navega a la página" **reintroduce la maraña** que el ADR mata: la causa raíz es la *navegación entre rutas*, no dónde se muestra el detalle. Se decide que toda la interacción ocurra como **capas en una misma página** (listado · inspector · modal grande), donde "volver" = cerrar capa. El inspector edita los **campos** del elemento; lo que no cabe (sub-colecciones con CRUD) escala a un **modal grande** que vuelve solo. Las páginas de detalle/edición dejan de ser rutas-destino (su contenido se trocea en fragmentos; la ruta de detalle redirige a `?sel`).

---

## Alternativas descartadas

### A. Mantener el botón "Ver" + navegación
Es el origen de la maraña de retornos. Descartada.

### B. Split horizontal en `main` (maestro arriba / detalle abajo)
Genera scrolls verticales apilados antipáticos. Todo el detalle va al inspector. Descartada por decisión del usuario.

### C. Inspector *push* con negociación de espacio (modelo del 2026-06-07)
Complejidad y riesgo altos (estados acoplados, *reflow*, parpadeo en umbrales) frente al overlay, que ya había que implementar de todas formas como último recurso. Descartada — ver Historial.

### D. Híbrido overlay + opción de "anclar" a *push*
Reintroduce toda la negociación que el overlay elimina; sobre-diseño. Si el uso real del árbol pide lado-a-lado persistente, se reevalúa. Descartada (de momento).

### E. Reservar hueco para la scrollbar del `main` bajo el overlay
Empujar la scrollbar a la izquierda del panel reflowa el contenido del `main` — justo lo que el overlay evita. Descartada: la scrollbar tapada es inocua y el scroll por rueda sigue activo (§4).

### F. Bottom-sheet del inspector en pantallas verticales
Un tercer patrón distinto, más código. El overlay lateral ya cubre el caso. Descartada (sobre-diseño).

### G. Inspector solo-lectura + "Abrir ficha completa" que navega a la página de detalle
Reintroduce la navegación entre rutas y, con ella, la maraña de retornos que este ADR elimina. Descartada — la edición vive en el inspector (§5) y la gestión compleja en el modal grande (§6), todo por capas.

### H. Inspector solo-lectura + modal grande con la ficha de edición completa
Mete *toda* la edición en el modal, dejando el inspector como mero visor: el modal acaba siendo "la página de antes con otro nombre". Descartada: el inspector edita los campos (§5); el modal queda reservado a sub-colecciones concretas (§6).
