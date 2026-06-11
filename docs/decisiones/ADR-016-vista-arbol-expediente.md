# ADR-016 — Vista de árbol del expediente

**Estado:** Adoptada
**Fecha:** 2026-05-28
**Issue:** #500
**Enmendada:** 2026-05-30 (#500, sesión de implementación) — añadidos §16 (contrato de endpoints), agregadores en colapso (§11), tooltip-peek de hover (§2.4/§15); iteración de trámite fuera de v1 (§2).
**Enmendada:** 2026-06-03 (#500, sesión S3b-4) — §7 y §8: Borrar eliminado del menú contextual; vive exclusivamente en inspector modo edición con flujo de dos pasos. §9: doble clic funcional (`zoomOnDoubleClick=false`, commit 71d9b5e); atajos F2 y Supr eliminados.
**Enmendada:** 2026-06-07 (ADR-023, #534) — §14: el redimensionado del inspector pasa a ser **mecanismo de shell** (CSS Grid + JS + `localStorage`), no `react-resizable-panels`; esta librería queda solo para splitters internos de la isla (split despensa/detalle). El inspector entra en la negociación de espacio global de ADR-023.

---

## Contexto

La vista de tramitación de un expediente ha pasado por tres iteraciones fallidas en el desarrollo previo: acordeón lateral, tabs y breadcrumbs profundos (5 templates `tramitacion_bc_*`). El problema raíz: un layout lineal vertical **no comunica la jerarquía completa** del expediente (Solicitudes → Fases → Trámites → Tareas) ni el estado del conjunto de un vistazo.

ADR-014 fijó el layout `base_app.html` con slots `inspector` y `dock`. La vista del expediente es el caso paradigmático del **modo workbench**.

ADR-015 fijó el stack: React montado como isla sobre el template Jinja, CSS Bootstrap + CDN JdA, build Vite.

Esta vista es la **pieza estrella del revamping** porque:

- Resuelve los tres intentos previos fallidos.
- Es la primera isla React productiva (no POC).
- Materializa la varita mágica nº 2 del estudio de usuario fase 2: "estado del expediente accesible de un vistazo".
- Permite ver "ramas cojas" del árbol — qué falta por hacer en cada solicitud.

---

## Decisión

### 1. Topología visual

Árbol top-down con jerarquía estricta:

```
                Expediente AT-XXXX
                       │
        ┌──────────────┼──────────────┐
    Solicitud A    Solicitud B    Solicitud C
        │              │              │
   ┌────┼────┐    ┌────┼────┐    ┌────┼────┐
  Fase Fase Fase Fase Fase Fase  Fase Fase
   │    │    │    │    │    │    │    │
  Tr   Tr   Tr   Tr   Tr   Tr   Tr   Tr
   │    │    │    │    │    │    │    │
  Ta   Ta   Ta   Ta   Ta   Ta   Ta   Ta
```

- **5 niveles fijos**: Expediente (raíz) → Solicitudes → Fases → Trámites → Tareas (hojas).
- **Solicitudes en paralelo** (mismo nivel horizontal).
- **Fases en paralelo** dentro de su solicitud (mismo nivel horizontal — sin ordenar por dependencias en v1, ver §15).
- **Trámites en paralelo** dentro de su fase.
- **Tareas en stack vertical** sin ramificación (las hojas son siempre una columna).
- **Líneas estructurales padre-hijo únicamente**: ortogonales con ángulos rectos redondeados. Estilo sólido gris medio.
- **No hay líneas hermano-hermano** (dependencias). Deuda futura — ver §15.

### 2. Bloques (nodos)

#### Forma y dimensiones

- **Forma**: rectángulo redondeado para todos los niveles. Misma forma; diferenciación por **color y tamaño**.
- **Tamaño aproximado** (ajustable en construcción):
  - Solicitud: ~260×64 px, borde grueso.
  - Fase: ~220×52 px.
  - Trámite: ~200×44 px.
  - Tarea: ~180×40 px (la más pequeña, pero también la más rica en decoradores).
- **Color principal** por nivel, paleta JdA (a definir en implementación). Modulado por estado.

#### Contenido del bloque

- **Nombre del item** (todos los niveles).
- **Decoradores específicos por tipo** (Solicitud / Fase / Trámite / Tarea):
  - **Solicitud**: siglas + descripción + estado deducido + (opcional) fecha presentación.
  - **Fase**: tipo + estado + resultado si finalizada + indicador de plazo si aplica.
  - **Trámite**: tipo + estado. (La **iteración** —nº de vuelta de consultas a organismos— **queda fuera de v1**: se computa con la variable de motor `organismo_supera_iteraciones` y depende de #471; se añadirá como decorador cuando esa pieza exista.)
  - **Tarea**: tipo (ANALIZAR/ELABORAR/NOTIFICAR/ESPERAR_PLAZO) + 2 puntos de documento (consumido arriba-derecha, producido abajo-derecha — gris=ausente, verde=presente, `(n)` para múltiples) + plazo con semáforo si ESPERAR_PLAZO + resultado ✓/✗ si NOTIFICAR.

#### Color por estado

Modulación del color principal según estado deducido por las properties existentes (`Solicitud.estado`, `Fase.estado`, `Tramite.estado`, `Tarea.estado`). Paleta coherente con `services/seguimiento.py`:

- Gris claro → PLANIFICADA / planificada (sin actividad).
- Amarillo / azul / naranja → EN_CURSO / pendientes según tipo.
- Verde → FIN / FINALIZADA / ejecutada favorable.
- Rojo / atenuado → vencido, urgente.

#### Hover

Hover sobre un bloque resalta visualmente (sombra suave, borde más marcado) sin abrir tooltip. El detalle completo va al inspector tras selección.

> **Enmienda (#500, 2026-05-30):** el resalte instantáneo se mantiene tal cual. Como mejora futura se contempla un *tooltip-peek* de detalle que aparece **solo tras ratón quieto** (delay / hover-intent) sobre el nodo, reutilizando el endpoint de detalle lazy (§16) con caché y cancelación. No es instantáneo, así que no reintroduce el ruido que esta decisión evita. Diferido — ver §15.

### 3. Selección

- **Selección única**. Un nodo seleccionado a la vez.
- **Click sobre nodo** → selecciona + inspector muestra detalle.
- **Click sobre fondo (sin nodo)** → deselecciona + inspector vacío (placeholder "Selecciona un elemento del árbol").
- **Estado visual del seleccionado**: marco reforzado (borde grueso + sombra). Distintivo claro.

### 4. Modo lectura vs modo edición

#### Modo lectura (por defecto)

- Lectura rica: colores, hover, inspector con detalle del seleccionado.
- Inspector es read-only.

#### Modo edición

- Activable por: botón `✏️ Editar` en viewbar **o** right-click → `Editar`.
- Doble clic sobre nodo → selecciona + activa edición + enfoca primer editable.
- **Fondo del árbol cambia de tono** (señal visual inequívoca de que estás en edición).
- Botón viewbar cambia a `Guardar` / `Cancelar`.

#### Lock de edición

Mientras estás en modo edición con cambios pendientes:

- Inspector destacado visualmente (borde grueso, sombra).
- Resto de UI (topbar, sidebar, viewbar acciones, árbol, dock) **atenuado** con `opacity 0.5` + `pointer-events: none`.
- Click en zona bloqueada → **toast warning no interactivo** (8s): *"Tienes cambios sin guardar — Guarda o cancela primero."*
- Navegación URL (atrás, cerrar pestaña) → diálogo nativo `beforeunload`.
- `Guardar` o `Cancelar` → la UI vuelve a interactiva.

#### Detección de cambios

Comparación entre estado actual del formulario y estado inicial al entrar en edición. Si difieren → lock activo. Si vuelves a editar todo a su valor original → lock se desactiva.

### 5. Inspector — adaptativo al nodo seleccionado

#### En modo lectura

Inspector muestra:

- Cabecera del nodo (tipo + nombre + estado).
- Datos completos del nodo (read-only).
- Documentos asociados si aplica (lista clicable que abre cada doc).
- Estado del plazo si aplica.
- Acciones rápidas no destructivas (abrir documento, abrir carpeta, copiar referencia).

**Contenido fino por nivel** (concretado en implementación S3a, #500 — cierra la deuda §15; el `estado`/semáforo, el nombre y los `agregados` los toma el front del nodo ya cargado en el árbol, el endpoint lazy §16 aporta solo lo que el árbol no trae):

| Nivel | Datos read-only | Documentos | Plazo | Acciones |
|---|---|---|---|---|
| **Expediente** | Tipo · Titular (+NIF) · Responsable · Heredado · nº solicitudes · Proyecto (título, emplazamiento, finalidad) | — | — | Abrir carpeta · Copiar ref. |
| **Solicitud** | Estado · Tipo · Fecha presentación · Solicitante (+NIF) · nº fases · (afectada si desist./renuncia) · Observaciones | Doc. solicitud (consumido) | — | Abrir doc · Abrir carpeta · Copiar ref. |
| **Fase** | Estado · Resultado (si finalizada) · nº trámites · Observaciones · agregados de plazos del subárbol | Doc. resultado (si finalizada) | resumen vía agregados | Abrir doc · Abrir carpeta · Copiar ref. |
| **Trámite** | Estado · nº tareas · Observaciones · agregados de plazos del subárbol | — | resumen vía agregados | Abrir carpeta · Copiar ref. |
| **Tarea** | Estado · Tipo · (NOTIFICAR: resultado) · Notas | Consumidos[] + Producido (asunto, tipo_doc, fecha, enlace) | bloque plazo si ESPERAR_PLAZO | Abrir doc(s) · Abrir carpeta del doc · Copiar ref. |

Fuera de v1 (alcance S3a): plazo de solicitud, lectura de notificación por intento, iteración de trámite. El inspector mantiene margen de iteración: añadir/quitar/reordenar un campo es una línea en `services/detalle_nodo.py` (payload de campos genérico), sin tocar el front.

#### En modo edición

Inspector se **divide en split vertical** mediante un splitter ajustable por el usuario:

- **Zona superior**: detalle = editor. Mismos campos, ahora editables. Botones `Guardar` y `Cancelar`.
- **Zona inferior**: **despensa**, contenido adaptativo al tipo de nodo seleccionado:
  - **Nodo no-tarea** (Solicitud / Fase / Trámite): **despensa de tipos creables**. Lista filtrada por el motor (qué tipos se permiten crear como hijo del seleccionado). Drag desde la despensa al nodo padre crea el hijo. Toggle "Mostrar todos..." muestra también los tipos NO permitidos atenuados con tooltip de norma + artículo + motivo (coherente con principio "el motor explica lo que prohíbe", ADR-007).
  - **Nodo tarea**: **despensa de documentos** del pool del expediente. Drag al nodo de tarea seleccionado lo vincula como consumido o producido (ver §10).

#### Tras drop exitoso (creación de hijo o vinculación de doc)

- El nuevo elemento se añade al árbol.
- Auto-select del nuevo nodo.
- Inspector muestra el detalle del nuevo nodo en modo edición con el primer campo editable enfocado (o sin foco si no hay editables).

### 6. Edición — guardar y cancelar

- **Botón `Guardar`** persiste cambios vía API. Toast `success` al completar. Sale de modo edición; el lock se libera.
- **Botón `Cancelar`** descarta cambios. Toast suave informativo. Sale de modo edición; el lock se libera.
- **No hay autosave** (decisión A2 de la discusión).
- **No hay edición inline** en los nodos del árbol — toda edición vive en el inspector.

### 7. Acciones sobre nodo

**Tres acciones únicas**: `Crear`, `Editar`, `Borrar`.

Otras "acciones" (finalizar fase, cerrar trámite, registrar resultado de notificación, marcar diagnóstico) son **resultados de edición + guardar**, no acciones independientes. Ejemplo: cerrar una fase = editar la fase + rellenar `resultado_fase_id` y `documento_resultado_id` + Guardar.

**Borrar es una modificación** y vive exclusivamente en modo edición (inspector). No es accesible desde modo lectura — ni por menú contextual ni por atajo de teclado. El inspector en modo edición muestra `Cancelar | Borrar | Guardar`.

**Flujo de borrado (dos pasos, inline en inspector):**
1. Clic "Borrar" → el motor valida. Si 422 → toast con motivo, permanece en edición.
2. Si el motor permite → el inspector muestra las consecuencias usando los `agregados` ya disponibles en el store (contadores del subárbol) con aviso de irreversibilidad y botón "Borrar definitivamente".
3. Clic "Borrar definitivamente" → DELETE → toast success + refrescar árbol + deseleccionar + salir edición.

El overlay de edición (commit 898094b) bloquea el árbol cuando hay cambios pendientes, por lo que el menú contextual (modo lectura) nunca aparece en edición — la separación es estructural.

### 8. Menú contextual (right-click)

#### Sobre nodo no-tarea (Solicitud / Fase / Trámite)

```
➕ Crear hijo                  ▶   (submenú con tipos creables filtrados por motor;
                                     "Mostrar todos..." expande con atenuados + tooltip norma)
✏️ Editar
─────────────────────────────────
📂 Abrir carpeta del expediente
📋 Copiar referencia
```

#### Sobre nodo tarea

```
📄 Abrir documento producido       (solo si lo tiene)
📄 Abrir consumido(s)           ▶   (submenú si hay >1, directo si 1)
✏️ Editar
─────────────────────────────────
📂 Abrir carpeta del documento     (si tarea tiene doc; texto adaptativo)
📂 Abrir carpeta del expediente    (si no tiene doc — fallback)
📋 Copiar referencia
```

> **Enmendado (2026-06-03):** Borrar eliminado del menú contextual. Ver §7 — vive en inspector modo edición.

#### Prioridad para "Abrir carpeta del documento"

Cuando la tarea tiene varios documentos vinculados:

1. **Documento producido** (lo que "vive" en esta tarea).
2. **Primer documento consumido** (si no hay producido todavía).
3. Fallback: **carpeta del expediente**.

#### "Crear hijo" desde el menú

El submenú comparte la misma fuente de datos que la despensa de tipos del inspector (consulta única al motor, cacheada). Click en un tipo del submenú = crea el hijo de ese tipo + auto-select + modo edición.

Las dos vías (drag desde despensa lateral / click en menú contextual) son **equivalentes** y conviven — cubren preferencias distintas de los usuarios.

#### `Copiar referencia`

Copia al portapapeles algo como: `AT-1234 · AAP · Fase Información Pública · Trámite Anuncio BOJA`.

### 9. Interacciones

| Gesto | Acción |
|---|---|
| **Click izquierdo** sobre nodo | Selecciona |
| **Click izquierdo** sobre fondo | Deselecciona |
| **Click derecho** sobre nodo | Menú contextual (§8) |
| **Doble clic** sobre nodo | Selecciona + activa edición + enfoca primer editable (`zoomOnDoubleClick=false`, commit 71d9b5e) |
| **Drag-drop** desde despensa (tipos) sobre nodo padre | Crea hijo del tipo arrastrado |
| **Drag-drop** desde despensa (documentos) sobre tarea | Vincula documento a la tarea |
| **Scroll del ratón** sobre área del árbol | Zoom in/out de xyflow |
| **Drag con botón medio o arrastre del fondo** | Pan del lienzo |

**No hay drag-drop de mover** (mover una tarea de un trámite a otro, mover una fase de una solicitud a otra, etc.). Descartado explícitamente en v1 por riesgo de implicar acciones compuestas del motor.

### 10. Drag-drop de documentos pool ↔ tareas

Decisión estructural confirmada (detalles concretos a refinar en implementación):

- Despensa de documentos vive en el **inspector** cuando hay una tarea seleccionada en modo edición.
- Drag de un documento sobre la tarea seleccionada → vincula (rol consumido o producido, según contexto a definir).
- El motor valida cada vínculo. Si rechaza → toast con motivo.

Refinamiento detallado pendiente de implementación (qué rol asigna por defecto cada tarea, qué tipos de documento admite, cómo se refleja en `DocumentoTarea`).

### 11. Filtros y control de profundidad

- **Toggle "Colapsar finalizados"** en viewbar. Colapsa visualmente (no oculta) los nodos en estado finalizado, permitiendo concentrarse en lo vivo.
- **Toggles adicionales de colapso/expansión por nivel** (propuestos, a refinar en implementación): "Colapsar trámites", "Expandir hasta fases", etc. Útiles en expedientes complejos.
- **Agregadores en nodos colapsados.** Cada nodo no-hoja lleva en el contrato un objeto `agregados` con **contadores de todo su subárbol** por métrica accionable (plazos vencidos / próximos / en plazo, pendientes de notificar; "pendientes de firma" diferido — §15). Se calculan **en el backend** de abajo arriba (mismo recorrido que `services/seguimiento.py`). Regla de presentación: el badge se muestra **solo cuando el nodo está colapsado**; el agregado es **total y fijo**. Como un nodo colapsado oculta todo su subárbol, no hay doble conteo ni recálculo dinámico en cliente — el front solo decide mostrar/ocultar según el estado de colapso de cada nodo. Resuelve también el "indicador de plazo de fase" de §2 (la fase agrega los plazos de sus tareas).
- **Filtros por pista, por estado, por plazo vencido** → **iteración posterior**, no v1.

### 12. Sincronización con URL

- Selección del nodo refleja en URL como query param: `/expedientes/1234/arbol?nodo=tarea-789`.
- Implementación: `history.replaceState` al seleccionar (sin recarga); el componente lee el query param al montar para restaurar selección.
- Permite compartir enlaces a nodos concretos, recargar manteniendo selección, "atrás" del navegador funciona como esperaría el usuario.

### 13. Minimapa

> **Revertida (#500, 2026-05-31):** el minimapa se **elimina**. En la implementación no aportaba valor (además salía sin tematizar): los controles de zoom (+/−), el fit-view y el pan del fondo con el ratón cubren toda la navegación. Decisión del usuario durante S3a.

~~Minimapa de xyflow activado por defecto, esquina inferior derecha del área del árbol. Botón discreto para ocultarlo si molesta. Estado en sessionStorage.~~

### 14. Redimensionamiento de paneles

Aplica lo decidido en ADR-014 + refinamientos posteriores:

- **Sidebar**: dos estados (expandido 240px / colapsado 60px) con chevron. Sin drag.
- **Inspector**: ~~redimensionable con drag splitter (borde izquierdo). Valor inicial `clamp(320px, 25vw, 600px)`. Persistido en `sessionStorage` (no entre sesiones).~~ **Enmendado por ADR-023 (#534, 2026-06-10):** el inspector pasa a ser **overlay de shell** (mecanismo CSS + JS + `localStorage`), no `react-resizable-panels`. El resize se hace arrastrando la franja izquierda del panel; el ancho se persiste en `localStorage` (`bddat.inspector.width`). Default 900 px. Ver ADR-023 §2 y §8.
- **Dock**: redimensionable con drag splitter (borde superior). Valor inicial `clamp(160px, 25vh, 400px)`. Persistido en `sessionStorage`.
- ~~Librería propuesta: `react-resizable-panels` (headless, ligera).~~ **Enmendado:** `react-resizable-panels` queda **solo para splitters internos de una isla** (p. ej. el split despensa/detalle del árbol). El inspector ya no la usa.

### 15. Deudas explícitas

#### Líneas de dependencia hermano-hermano

Descartadas en v1 por imposibilidad de inferirlas desde el motor agnóstico mientras las reglas no estén completamente seeded. El motor devuelve `PERMITIDO` sin información cuando ninguna regla aplica, así que no se puede anotar la dependencia post-hoc.

**Retomable cuando**:

- el motor esté completamente seeded y `PERMITIDO` con condiciones evaluadas devuelva la información que permitan anotarlas (cambio de interfaz del motor), o
- se modele una tabla de dependencias entre tipos como referencia (opción descartada en discusión pero recuperable), o
- emerja otra solución.

Mientras tanto, el técnico humano interpreta el orden por contexto del dominio (sabe que CONSULTAS va antes que RESOLUCION).

#### Modo "solo camino activo"

Diferido a v2. El toggle "Colapsar finalizados" (§11) cubre el 80% del valor con menos complejidad.

#### Vista alternativa timeline

Diferida. La viewbar puede preparar el espacio para un toggle "🌳 árbol / 📅 timeline" en el futuro sin necesidad de implementarlo ahora.

#### Resumen-mini de pistas en viewbar

Propuesta planteada en discusión: en la viewbar de la vista de expediente, mostrar las 5 pistas del seguimiento (SOL / CONSULTAS / MA / IP / RES) con sus colores actuales como recordatorio permanente del estado. Refinable en implementación; no afecta a la decisión del árbol.

#### Contenido específico del inspector

**Resuelto en S3a (#500):** el contenido fino del inspector en modo lectura por nivel está concretado en la tabla de §5 (cabecera + datos + documentos + plazo + agregados + acciones rápidas). El contrato del endpoint de detalle lazy está en §16. La despensa adaptativa (modo edición) sigue diferida a S3b.

#### Dock

La propuesta original de 3 tabs (Bitácora / Alertas motor / Plazos vivos) quedó **anulada por ADR-020**: el dock pasó a ser chrome global con bitácora por usuario y avisos de sesión. Las alertas del motor activas y los plazos vivos quedan pendientes de asignación a la viewbar (diseño futuro).

#### Agregador "pendientes de firma"

El catálogo de agregadores de nodo colapsado (§11) arranca con los directos: plazos y pendientes de notificar. **"Pendientes de firma"** (tareas ELABORAR cuyo documento producido aún no tiene valor administrativo firme) queda **fuera de v1**: requiere primero **definir el criterio de dominio**, porque `Documento.fecha_administrativa` NULL también lo usan los informes sin valor jurídico propio. Añadirlo después toca solo el serializador del árbol y el componente de badges — deuda barata.

#### Tooltip-peek en hover

§2.4 mantiene el resalte instantáneo sin tooltip. Como mejora futura se contempla un *tooltip* de detalle tras **ratón quieto** (hover-intent con delay) que reutiliza el endpoint de detalle lazy (§16) con caché y `AbortController`. Disponible **igual en lectura y en edición**: el tooltip es consulta de información (lectura), y la lectura fluye idéntica en ambos modos — lo único que distingue a la edición es poder editar. La única limitación es física: durante el **lock** con cambios pendientes el árbol tiene `pointer-events: none` (§4), así que no hay hover de ninguna clase —ni resalte ni tooltip— hasta guardar o cancelar. Diferido; el contrato lazy ya lo soporta sin cambios de backend.

### 16. Contrato de los endpoints del árbol

Decidido durante la sesión de implementación de #500 (2026-05-30). Concreta los puntos 1-3 de «Cómo implementar».

#### `GET /api/expediente/<exp_id>/arbol`

- **Forma:** JSON **anidado de dominio** `expediente → solicitudes[] → fases[] → tramites[] → tareas[]`. El frontend deriva los `nodes`/`edges` y el layout de xyflow; el backend es **agnóstico** de la librería de diagramas.
- **Estado semántico, nunca color:** cada nodo lleva su `estado` deducido de las properties `.estado` de los modelos (PLANIFICADA / EN_CURSO / PDTE_CIERRE / FINALIZADA, etc.). El mapeo estado→color de la paleta JdA vive en el tematizado de xyflow (un único punto en el front).
- **Una sola query** con `joinedload` de toda la jerarquía + relaciones de decorador.
- **Decoradores por nodo** según §2. El `plazo` de las tareas ESPERAR_PLAZO se resuelve **en el backend** (`services/plazos.obtener_estado_plazo`) porque su cómputo depende del calendario hábil, suspensiones y `catalogo_plazos` — inaccesibles desde el cliente —; viaja como `{estado, fecha_limite, dias_restantes}` y el front solo mapea `estado` → icono de semáforo.
- **Agregadores** (`agregados`) por nodo no-hoja: ver §11.

#### `GET /api/expediente/<exp_id>/nodo/<tipo>/<nodo_id>` — detalle lazy

- El árbol **no** lleva el detalle completo de cada nodo: solo decoradores. El detalle del inspector se pide **bajo demanda** al seleccionar (y, en el futuro, al hacer hover con delay — §2.4).
- Ventaja: árbol ligero, detalle siempre fresco, payload acotado en expedientes grandes.
- **Ruta** (implementada en S3a, #500): `GET /api/expedientes/<exp_id>/nodo/<tipo>/<nodo_id>`, `<tipo>` ∈ {expediente, solicitud, fase, tramite, tarea}. Sirve también la raíz (uniforme).
- **Payload**: `{nodo:{tipo,id}, campos:[{etiqueta,valor}], documentos:[{id,rol,nombre,tipo_doc,fecha,enlace,externo,puede_abrir_carpeta}], plazo:{estado,fecha_limite,dias_restantes}|null, referencia}`. La cabecera (nombre/estado/semáforo) y los `agregados` NO viajan aquí: el front los toma del árbol ya cargado. El servicio es `services/detalle_nodo.py`, defensivo ante catálogo y con `ValueError`→404 si el nodo no pertenece al expediente. Contenido por nivel: §5.

#### `GET /api/expediente/<exp_id>/nodo/<tipo>/<nodo_id>/tipos-creables`

- Como «Cómo implementar»·2: **misma fuente** para la despensa de tipos del inspector y el submenú «Crear hijo» del menú contextual (consulta única cacheada). Devuelve los tipos de hijo creables según motor + reglas FTT.

---

## Cómo implementar

1. **Servicio backend** `GET /api/expediente/<id>/arbol`: devuelve el árbol completo serializado (todos los niveles + estados deducidos + decoradores). Joinedload optimizado de toda la jerarquía en una sola query.
2. **Servicio backend** `GET /api/expediente/<id>/nodo/<tipo>/<id>/tipos-creables`: devuelve los tipos de hijo creables según motor y FTT. Misma fuente para despensa lateral y menú contextual.
3. **Endpoints CRUD** existentes (`api_bc`) extendidos o sustituidos según necesidad.
4. **Isla React** `react-src/src/expediente-arbol/` siguiendo el patrón establecido en ADR-015:
   - Entry IIFE que expone `window.ExpedienteArbol.mount(element, props)`.
   - `<App>` con xyflow + componentes propios por nivel (`<NodoSolicitud>`, `<NodoFase>`, `<NodoTramite>`, `<NodoTarea>`).
   - State con `useState`/`useReducer` nativos (escalable a Zustand si crece).
   - Data fetching con wrapper propio sobre `fetch`.
   - Permisos vía `tienePermiso()` leído del data-attribute inyectado por Jinja (ADR-013).
5. **Tematizado de xyflow** para que respete paleta Bootstrap + JdA. Documentar el patrón.
6. **Template Jinja** `app/templates/expedientes/arbol.html` que extiende `base_app.html`:
   - `inspector_state="open"` (el dock es chrome global, no se configura por vista).
   - Monta `<div id="app-root" data-expediente-id="..." data-user="..." data-permisos="...">`.
7. **Ruta Flask** `GET /expedientes/<id>/arbol` con `@require_permiso('acceder_expediente')` (ADR-013).
8. **Smoke test** Playwright MCP del flujo: cargar, seleccionar, entrar en edición, crear hijo desde despensa, guardar, cancelar.

Las 5 vistas `tramitacion_bc_*` y `base_bc.html` se **eliminan** al cerrar este issue (era ya el plan de ADR-014).

---

## Alternativa descartada

### A. Mantener la vista BC actual con mejoras incrementales

Probada en el desarrollo previo a través de tres iteraciones (acordeón → tabs → breadcrumbs). Las tres fallaron por la misma razón: un layout 1D no comunica la jerarquía del expediente. Descartada por evidencia operativa acumulada.

### B. Árbol con líneas de dependencia hermano-hermano desde v1

Descartada por imposibilidad de inferir las dependencias desde el motor agnóstico con reglas incompletas (ver §15). Retomable cuando el contexto cambie.

### C. Drag-drop de mover (cambiar padre de un nodo)

Descartada por requerir acciones compuestas validadas por motor (CREAR-en-destino + BORRAR-en-origen con rollback si una falla). Riesgo alto, retorno bajo. Borrar + recrear cubre el caso operativo sin riesgo.

### D. Vista de detalle/edición en modal flotante

Considerada. Descartada porque ocultaría el árbol durante la edición — pierde el valor de "ver el conjunto mientras edito una rama". El inspector adyacente al árbol es la elección correcta.
