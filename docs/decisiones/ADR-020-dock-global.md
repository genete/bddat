# ADR-020 — Dock global: bitácora por usuario + avisos de sesión

**Estado:** Adoptada
**Fecha:** 2026-05-29
**Issue:** #506

---

## Contexto

ADR-014 definió el dock como **slot Jinja opcional** (`{% block dock %}`) que cada vista podía rellenar o no. En ADR-016 §15 se esbozaron 3 tabs de contenido: Bitácora del expediente / Alertas del motor activas / Plazos vivos.

En la sesión de diseño detallado (2026-05-29) ese modelo evolucionó por tres razones:

1. **Alertas del motor y plazos vivos** son contexto del expediente abierto, no del dock. Su lugar natural es la **viewbar** (pendiente de diseñar en detalle).
2. **La bitácora** es por usuario, no por expediente. Tiene valor en cualquier vista autenticada, no solo en el workbench.
3. **Los toasts son efímeros** por diseño pero los usuarios necesitan releerlos. No existe ningún sitio donde recuperar un aviso que pasó demasiado rápido. El dock cierra ese agujero.

Además, la forma ancha-y-baja del dock encaja mejor con un **stream de líneas tipo consola** que con contenido navegable vertical. El nombre mismo ("dock") remite a los paneles anclables de IDEs (VS Code, IntelliJ, Photoshop) que alojan terminal, output y logs — nunca listas de datos.

La **campana 🔔 del topbar**, que ADR-014 dejó como placeholder de "notificaciones futuras", encaja exactamente con el toggle del dock: ambos son globales, el icono es reconocible y su función de "abrir el panel de avisos" es coherente con su posición.

---

## Decisión

### 1. El dock pasa a chrome global

El dock **deja de ser un bloque Jinja por vista** y pasa a ser un **partial del shell**, incluido siempre en `base_app.html` junto con topbar, sidebar y footer.

Consecuencias:
- Se elimina `{% block dock %}` y `dock_state` de la tabla de slots Jinja de ADR-014.
- El CSS grid mantiene el `grid-area: dock` pero la fila siempre existe (colapsa a `0` cuando cerrado, se abre al toggle).
- Las vistas no necesitan saber que el dock existe.

### 2. La campana del topbar es el toggle del dock

El `🔔` del topbar (ADR-014 §5, era placeholder) pasa a tener función definitiva: **abrir y cerrar el dock**. Estado persistido en `localStorage` (`bddat.dock.open`, key ya definida en ADR-014).

Si en el futuro el dock incorpora otros usos (hoy no previstos), el icono se puede revisar hacia algo más genérico. Por ahora la campana es semánticamente correcta.

### 3. Posición y dimensiones

El dock mantiene el span **main + inspector** (anchura completa menos sidebar), igual que en ADR-014. No se reduce a solo main — la anchura extra permite líneas más largas sin truncar y no hay razón de contenido para sacrificarla.

- Altura inicial: `clamp(160px, 25vh, 400px)` (igual que ADR-016 §14).
- Redimensionable con drag splitter en el borde superior.
- Estado de altura persistido en `sessionStorage` (no entre sesiones).

### 4. Dos tabs horizontales

Los tabs van en la **cabecera del dock** (orientación horizontal, cabecera de 32px). Aunque el ADR original especificaba tabs verticales en el lateral izquierdo, en la sesión de implementación (#506) se adoptaron horizontales: el patrón es el estándar reconocible de paneles IDE (VS Code, DevTools) y la pérdida de altura (32px sobre ~220px de contenido) es menor que la mejora en usabilidad y familiaridad.

| Tab | Icono | Contenido | Persistencia |
|---|---|---|---|
| **Bitácora** | 📜 | Entradas del cuaderno de bitácora (issue #1) del usuario en sesión | BD (permanente); carga vía `GET /api/bitacora/reciente` |
| **Avisos** | 🔔 | Toasts capturados durante la sesión | `sessionStorage` vía `dock-buffer.js` (solo sesión) |

### 5. Comportamiento de cada tab

#### Tab Bitácora

- Muestra entradas de la bitácora filtradas por `usuario_actual`, ordenadas cronológicamente inverso.
- Sirve en cualquier vista: en el workbench muestra la actividad del usuario en ese expediente y sus acciones globales; en modo página muestra toda la actividad reciente.
- Formato de línea: `HH:MM · icono-acción · descripción breve · (AT-XXXX si aplica)`
- Las líneas más largas que el ancho del dock se truncan con `…`. Hover → tooltip con texto completo.
- **Botón modal** (icono en la cabecera del tab): abre un modal con la tabla completa de la bitácora + filtros + enlace "Ir al panel de bitácora".
- **Botón limpiar** (icono en la cabecera): limpia la vista del dock para esta sesión (no borra la BD — solo colapsa las entradas ya vistas). Al reabrir el dock se recargan.

#### Tab Avisos

- Captura **todos los toasts** emitidos en la sesión antes de que se autodestruyan (success, warning, error, info).
- Almacenados en `sessionStorage`. Se pierden al cerrar la pestaña o la sesión — correcto, no aportan valor permanente.
- Formato de línea: `HH:MM · icono-tipo · texto del toast`
- Resuelve el problema operativo: *"¿Qué me dijo el toast? No lo leí."*
- **Botón modal**: lista completa de avisos de la sesión.
- **Botón limpiar**: vacía el buffer de avisos de la sesión.

### 6. Badge de no leídos

Cada tab muestra un badge numérico con los mensajes no leídos. Un mensaje se marca como leído cuando:
- El dock está abierto y el tab está activo (visible).
- O el usuario hace clic en el tab.

El badge del tab Avisos es el sustituto del badge que podría haber tenido la campana del topbar — al abrir el dock y activar el tab, el contador se pone a cero.

### 7. Integración con el sistema de toasts existente

El sistema de toasts debe emitir cada mensaje al buffer del dock **antes de autodestruirse**. Implementación: un bus de eventos JS simple (o un módulo `dock-buffer.js`) al que el sistema de toasts llama con `{ tipo, texto, timestamp }`. El dock escucha el bus y añade la línea al tab Avisos.

---

## Por qué

- **El dock como chrome global** tiene valor en cualquier vista, no solo workbench. La bitácora por usuario y los avisos de sesión son transversales.
- **La forma ancha-y-baja** del dock es ideal para streams de líneas tipo consola — no para listas navegables. Dos tabs verticales con líneas cortas es el patrón correcto.
- **Los toasts son efímeros por diseño** pero los usuarios necesitan releerlos. El dock los retiene sin cambiar la naturaleza efímera del toast en sí.
- **La campana como toggle** es la solución más coherente: el icono ya estaba en el topbar, ya era "global", ya tenía la semántica de notificaciones. Solo faltaba darle función real.
- **No mezclar streams**: bitácora (eventos de dominio, permanentes) y avisos (eventos de UI, de sesión) son naturalezas distintas. Mezclarlos en un único stream generaría ruido y dificultaría la lectura.

---

## Impacto en ADRs anteriores

### ADR-014

- **§3 Slots Jinja**: se eliminan las filas `dock` y `dock_state` de la tabla. El dock ya no es un bloque que las vistas sobreescriben.
- **§5 Header**: la campana `🔔` ya no es placeholder — es el toggle del dock (enlaza a este ADR).
- **§2 Mockup**: el dock sigue apareciendo en el diagrama de modo workbench (su span no cambia), pero la nota "opcional" deja de aplicar: está siempre presente en el shell.

### ADR-016 §15

- Se anula la propuesta de "3 tabs: Bitácora / Alertas motor / Plazos vivos".
- Alertas del motor activas y plazos vivos quedan **pendientes de asignación a viewbar** (diseño futuro).
- El dock del workbench es el mismo dock global — no hay configuración especial para esa vista.

---

## Cómo implementar

1. **Mover el dock a partial global**: crear `app/templates/layout/_dock.html`. Incluirlo en `base_app.html` después del bloque de `inspector`, antes de `footer`.
2. **CSS Grid**: la fila `dock` ya existe en el grid. Añadir transición de altura para el toggle (similar al sidebar). `grid-template-rows` ajusta la fila dock según `data-dock="open|closed"` en el shell.
3. **Toggle desde campana**: el JS de la campana del topbar hace `dataset.dock = 'open' | 'closed'` en el shell y persiste en `localStorage`.
4. **Tabs verticales**: markup Bootstrap con `.nav.flex-column` en el lateral izquierdo del dock + `.tab-content` en el resto del ancho.
5. **Bus de eventos** `dock-buffer.js`: módulo JS que expone `DockBuffer.push({ tipo, texto, timestamp })`. El sistema de toasts lo llama antes de lanzar el toast visual.
6. **Tab Bitácora**: endpoint `GET /api/bitacora/reciente?usuario=<id>&limit=50` que devuelve las últimas N entradas del cuaderno del usuario. Se carga al abrir el dock / al cambiar al tab.
7. **Badge**: contador en `sessionStorage` por tab. Se resetea al activar el tab con el dock abierto.
8. **Modales**: Bootstrap modal estándar, lanzado desde el botón de cabecera de cada tab.
9. **Smoke test**: verificar que el dock aparece en `/` (dashboard), `/expedientes/` (listado) y `/expedientes/1234/arbol` (workbench) con HTTP 200 y el elemento `.app-dock` presente.

---

## Alternativa descartada

### A. Dock como slot opcional por vista (modelo ADR-014 original)

Descartada porque la bitácora por usuario y los avisos de sesión no pertenecen a ninguna vista concreta. Un slot opcional requiere que cada vista lo rellene — pero el contenido es transversal. Mantener el slot obligaría a duplicar el mismo partial en cada template de vista que quisiera el dock, lo que derrota el propósito del slot.

### B. Stream unificado (bitácora + avisos mezclados)

Considerado y descartado: bitácora (eventos de dominio, permanentes en BD, autorizados) y avisos (eventos de UI, efímeros, de cualquier tipo) tienen naturalezas distintas. El usuario necesita saber de qué tipo es cada mensaje de un vistazo. Dos tabs verticales con 30-40px de anchura cada uno resuelven la separación sin sacrificar espacio de línea.

### C. Badge en la campana del topbar (sin dock)

Considerado. No resuelve el problema de releer el texto del toast. El badge informa de que "hay algo" pero no muestra qué. El dock retiene el texto.
