# PRE-ADR — Interfaz: vistas, inspector, listados y tratamiento de documentos

> **Estado:** Borrador. Material de partida de un ADR todavía sin redactar. Recoge hallazgos y
> preguntas; **no contiene propuestas de diseño ni de planificación**.
> **Fecha:** 2026-10-10 (sesiones del 09 y 10/10/2026).
> **Origen:** la revisión de #929 contra el código (09/10) destapó que el tratamiento de documentos
> está repartido; de ahí se pasó a inventariar el inspector y las vistas, su acceso por ruta y el
> código muerto. Con ello el alcance ya no es solo «estandarizar el listado o el inspector».
> **Relación con los planes:** `ESTADO_ADR049.md` y `ESTADO_ADR050.md` **siguen igual**. Cómo encajan
> en ellos los issues que salgan de este ADR se fija en el hilo que lo redacte.
> **Convención:** `[VERIFICADO]` = leído en código, ADR o issue. `[LECTURA]` = deducido de leer código,
> **sin reproducir en el navegador** ni ejecutar tests. `[ABIERTO]` = pregunta que el ADR tiene que
> resolver. `[PROVISIONAL]` = indicación de unificación dada durante la sesión, **no decidida**: se
> revisa una a una.

---

## 0. Cómo retomar este documento

- Es autocontenido: las notas de trabajo de las sesiones estaban en `docs_prueba/temp/` (fuera de git)
  y su contenido útil está aquí.
- Las referencias a línea se mueven; los nombres de función, fichero y endpoint no.
- Método del inventario de código muerto (§7.5): script de apoyo no versionado que busca el nombre
  de cada plantilla, fichero estático, componente React y ruta en `app/` y `react-src/src/`. Da
  **candidatos**; todos los de este documento se verificaron a mano.
- Documentos que el ADR probablemente tenga que leer y **no se han revisado** en estas sesiones:
  `DECISIONES_UI.md`, `PRE-ADR-navegacion-administrativa.md`, `PRE-ADR-supervisor.md`, ADR-015, ADR-016,
  ADR-022, ADR-024, ADR-029.

## 1. Contexto: cómo se llegó aquí

1. **09/10.** Se revisó #929 (frontend de notificaciones) contra el código y se partió en zonas:
   #929 (A: tramitar una `NOTIFICAR` en el navegador), #1036 (B: fecha en la subida), #1037 (C: edicto),
   #1038 (D: representante y sede) y E (visibilidad, sin issue, listada en #929). Detalle en
   `ESTADO_ADR049.md`.
2. Carlos observó una tensión: al añadir particularidades al inspector por fase, trámite o tarea
   aparecen atajos a funcionalidades que viven en otro sitio, con uno concreto como sitio canónico.
   Casi todos giran alrededor de **documentos** (subir, enlazar, listar). Se hace de forma
   improvisada, sin unificación ni centralización. Lo que es particular de un caso se escribe en el
   caso, pero cuando se repite en distintos sitios molesta. Lo tenía pendiente como issue de
   «revisión y unificación de la interfaz».
3. Se inventarió el tratamiento de documentos (§6).
4. Carlos matizó que el principal es el listado del pool y que los «otros» están dispersos en cinco
   más (§2, P1–P6).
5. Se inventarió el estándar de listado e inspector y cada vista (§3, §4, §5).
6. Se añadió el acceso por ruta y el código muerto (§7).

## 2. Decisiones y posiciones de Carlos

### Decisiones tomadas

| # | Decisión |
|---|---|
| D1 | **#929 zona A: sin interfaz nueva de documentos ni atajo.** La decisión 1 de #929 (atajo «subir justificante por tipo» en el editor) queda resuelta en «no». |
| D2 | `Cola.jsx` (Mi trabajo) también es candidato a convertirse al estándar, como el listado del pool. Issue abierto: **#1039**. |
| D3 | Lo de este PRE-ADR se fija en otro hilo (un ADR). `ESTADO_ADR049` sigue igual de momento. |
| D4 | B, C y D (#1036, #1037, #1038) se redactan sin profundizar y se profundizan uno a uno cuando toque. |

### Posiciones y reflexiones (no son decisiones)

- **P1.** #881 (reforma del listado del pool) surgió porque el listado se montó antes de que existiera
  el estándar. Carlos lo dejó abierto sin implementar porque entendía que debía montarse como
  cualquier otro listado: clic en fila → inspector, acciones desde el inspector.
- **P2.** Los minilistados que se necesitan **junto a la vinculación en las tareas** impiden reutilizar
  el listado general porque son **dos conceptos distintos**.
- **P3.** Duda planteada: ¿dejar el listado general como scroll infinito + clic en fila → inspector +
  acciones, por coherencia con los demás, y montar un módulo exclusivo para los listados «mini», que
  solo necesitan funcionalidades limitadas? Observaciones suyas: el candado de «referenciado» no dice
  cuántas vinculaciones tiene el documento ni dónde; el inspector podría evitar el modal para editar
  sus datos; la edición masiva y los dos bloques de subida (*interpretación:* «Subir fichero» y
  «Añadir URL externa» del pool) seguirían necesitándose fuera del inspector.
- **P4.** Alternativa que Carlos considera: **un solo módulo especializado, sin inspector, que valga
  para los dos usos**, y en ese caso iría por React. Pidió ventajas e inconvenientes.
- **P5.** Idea anterior: un solo módulo de listado que se incrusta en cada sitio, con columnas
  flexibles y prescindibles en el inspector, que es el sitio potencialmente más estrecho.
- **P6.** La tecnología (Jinja o React) para los mini-listados, y si el estándar de listados cambia,
  **no está decidida**: se propone cuando termine la reflexión.

## 3. El estándar vigente (ADR-022 y ADR-023)

`[VERIFICADO]` ADR-023 (adoptada 2026-06-07; revisada 06-10, 07-18 y 07-29) y ADR-022:

| # | Regla |
|---|---|
| E1 | El listado extiende `layout/lista_v2_base.html` y usa `ScrollInfinito` en modo `selection`, con el marco visual C.1 (`.lista-cabecera`, filtros y contador) y C.2 (`.lista-scroll-container`, tabla en `.card.tabla-bloque` / `.lista-table`) |
| E2 | Clic en fila abre `AppInspector.open({fragmentUrl})`. La selección se sincroniza con `?sel=<id>` |
| E3 | El cuerpo del inspector es un fragmento Jinja de lectura (`/<id>/fragmento`) y otro de edición (`/<id>/editar-fragmento`). El guardado es un POST por XHR que devuelve JSON con los errores; las mutaciones POST redirigen a `?sel` |
| E4 | `GET /<id>` y `GET /<id>/editar` **redirigen** a `?sel=<id>` (no son destinos de navegación; se conservan por los enlaces externos) |
| E5 | Lo que no cabe en el inspector —colecciones o relaciones con CRUD propio— va a un **modal grande** (`data-modal-large-url`, `AppModalLarge`), lanzado desde el inspector |
| E6 | El mecanismo del inspector funciona «en Jinja o en React». El árbol (isla React) monta su inspector con `AppInspector.mountReact` y un slot |
| E7 | Marco de edición (§5 bis): barra fija con cabecera y control de salida; «nodo-de-campos» frente a «superficie-de-trabajo» (sub-bloques que persisten por su cuenta); Cerrar / Guardar / Cancelar |

**Capacidades de `ScrollInfinito`** (`v2-scroll-infinito.js`): modo legacy (expedientes); **modo
genérico con columnas declaradas** (`columns: [{key, label, type}]`, con tipos como `text`, `badge`,
`bool`, `acciones`); **modo selección** (E2); **modo checkbox masivo** opt-in (`bulkCheckbox` /
`setBulkMode`, v1.5, #612): checkbox por fila y «seleccionar todos» en la cabecera, y **suspende la
selección hacia el inspector mientras está activo**. Precedente de uso: «Asignación masiva» de
`listado_v2` de expedientes.

**Registro de módulos:** `app/modules/<x>/routes.py` expone `bp` y `ModuleRegistry` lo registra por
descubrimiento. El menú lo construye `ModuleRegistry.get_navigation()` leyendo
`metadata.json` (`navigation`, `order`, `permissions.list`). `metadata.json` puede llevar además
`listado_v2.columns` (columnas declarativas).

## 4. Inventario de vistas con inspector

Leyenda: ✅ cumple el estándar · ⚠ no lo cumple. Las indicaciones **`[PROVISIONAL] →`** dentro de las
celdas son las dadas en la sesión del 10/10: no están decididas.

### 4.1 Listados que siguen el estándar `[VERIFICADO]`

Jinja, extienden `lista_v2_base`, `ScrollInfinito` en modo selección, inspector con fragmentos
Jinja (E1–E4).

| Std | Vista | Inspector: fragmentos | Especialización |
|---|---|---|---|
| ✅ | Expedientes (`expedientes.listado_v2`) | `_inspector_expediente` + `_editar_fragmento_expediente` | Modal grande «gestionar municipios». Modo masivo de asignación. Enlaces a árbol y pool (páginas aparte) |
| ✅ | Entidades (`entidades.index`) | `_detalle` + `_editar` | Modal grande ×2: direcciones y autorizaciones. Alta en página aparte (§4.4) |
| ✅ | Catálogo de plazos | `_detalle` + `_editar` | JS propio de cascada en edición (`catalogo-plazos-cascada.js`) |
| ✅ | Usuarios, Tipos de documento, Catálogo de requerimientos, Efectos de plazo, Firmantes, Ítems técnicos, Requisitos documentales, Mensajes internos | `_detalle` + `_editar` (el mismo molde) | Ninguna por tipo. Requisitos lleva `requisitos-inspector.js` |
| ⚠ parcial | Plantillas de escritos | `_detalle` + `_editar` | Modal grande de tokens y modal del explorador de ficheros (este desaparece con #1009). Alta en página completa (`form.html`) |

### 4.2 Vistas que ofrecen el estándar pero no lo cumplen `[VERIFICADO]`

| Std | Vista | Vista_tecnología | Inspector_tecnología | Especialización |
|---|---|---|---|---|
| ⚠ | **Tablas maestras** | Jinja, extiende `base_app` y no `lista_v2_base`; marco copiado a mano; `ScrollInfinito` con selección por pestaña. `[PROVISIONAL] →` una base de listado que admita varias listas por página (`lista_v2_base` asume una; el «volver arriba» queda muerto, #755) | Fragmento `/<tipo>/<id>/fragmento` + `editar-fragmento`, un molde parametrizado por `TIPOS` (`config.py`) | 5 tipos: expediente, solicitud, fase, trámite, tarea. Editor de pasos con `tablas-maestras-pasos.js` |
| ⚠ | **Normas y variables** | Idéntico: `base_app`, 2 pestañas, marco copiado. `[PROVISIONAL] →` misma base multi-lista | Dos pares de fragmentos (norma / variable) | 2 tipos |
| ⚠ | **Seguimiento y huérfanos** (hub del tramitador) | Idéntico: `base_app`, 2 pestañas. Tiene su propio «volver arriba» y su propio «abrir documento» en JS. `[PROVISIONAL] →` base multi-lista y pintado común de documentos | `_inspector_seguimiento` (por solicitud) y `_inspector_huerfano`. El huérfano lleva un `<script>` en línea que el overlay no ejecuta (§7.3). `[PROVISIONAL] →` ese JS a un fichero global con delegación | 2 fragmentos distintos |
| ⚠ | **Configuración del motor** | `base_app`; la sección Reglas reproduce a mano la cabecera y tabla de `lista_v2_base`; sin «volver arriba». `[PROVISIONAL] →` misma base multi-lista | Fragmento `reglas/<id>/fragmento` + `editar-fragmento` | Modal grande «Gestionar excepciones» con sus propios fragmentos (alta y edición por `fetch` dentro del modal; es el patrón E5) |
| ⚠ justificado | **Delegación Territorial** (`organo_propio.index`) | Jinja, `base_app`, tablas fijas (1 + 8 filas) sin `ScrollInfinito` (lo declara su cabecera). `[PROVISIONAL] →` mantener la tabla fija y abrir el inspector por atributo `data-inspector-sel` con delegación, sin `onclick` en línea | `unidades/<id>/fragmento` + `editar-fragmento`, abierto con `onclick="AppInspector.open(...)"` en la fila | Ninguna |
| ⚠ | **Cola de Mi trabajo** (`tareas_y_subidas.index`) | React (isla `mi-trabajo`, `Cola.jsx`). Reutiliza las **clases CSS** del marco, pero implementa por su cuenta el scroll infinito por cursor y los filtros (un `useState` por filtro con debounce), y no tiene «volver arriba» (caso 4 de #755). `[PROVISIONAL] →` listado estándar (#1039) | Fragmento Jinja de solo lectura `_inspector_cola`. Ignora `abrir_en` y `puede_abrir` de los documentos. `[PROVISIONAL] →` pintado común de documentos | Ninguna |
| ⚠ | **Pool de documentos** (`expedientes.pool_documentos`) | Jinja, `base_app`, ~1.550 líneas. Tabla entera desde el servidor y filtros en el cliente. `[PROVISIONAL] →` listado estándar con inspector (#881 reescrito) | **Sin inspector:** 4 modales Bootstrap propios (subir, URL externa, editar, sustituir), alimentados con 12 atributos `data-*` | Ninguna por tipo. Para `DOC_PROYECTO`, lógica de principal y reformado (ADR-044) |

### 4.3 El árbol del expediente (E6, excepción prevista) `[VERIFICADO]`

React (isla `expediente-arbol`, estado en un store zustand). El inspector es `Inspector.jsx`,
montado por portal en `#arbol-inspector-slot`; el overlay se abre con `AppInspector.mountReact`.

- **Lectura:** `Cabecera`, `Campos`, `Agregados`, `Plazo`, `PlazosActos`, `Organismos`, `Documentos`,
  `Acciones`. El detalle lo sirve `detalle_de_nodo` para 7 tipos de nodo (expediente, solicitud,
  versión, fase, trámite, tarea, organismo).
- **Edición:** `InspectorEdicion` = `BarraEdicion` fija + un contenedor con scroll con el editor y la
  `Despensa`.
- Existe además un menú contextual (`MenuContextual.jsx`) con su propio detalle y acceso a documentos.

| Nodo | Editor | Bloques añadidos | Despensa |
|---|---|---|---|
| Expediente, Versión | solo lectura (sin esquema editable) | — | Expediente: crear solicitudes |
| Solicitud | Editor genérico (solo observaciones) | Certificado de fin de instrucción y su sello, cierre de la solicitud, modal del informe | Crear fases; ancla de solicitud |
| Fase | Editor genérico | Reabrir fase | Crear trámites |
| Fase `CONSULTAS` | Editor genérico | + acciones de consultas | idem |
| Fase finalizadora | Editor genérico | + certificado de cumplimiento, cierre y modal de confirmación | idem |
| Trámite | Editor genérico | — | Crear tareas |
| Tarea `ANALIZAR` | `AnalizarEditor` | Borrar tarea | Documentos; **se oculta** si las secciones son extendidas |
| Tarea `ELABORAR` | `ElaborarEditor` | Borrar tarea | Documentos |
| Tarea `NOTIFICAR` | `NotificarEditor` (roto, #929) | Borrar tarea | Documentos |
| Tarea `ESPERAR_PLAZO` | Editor genérico | — | Documentos, con ayuda de recepción |
| Otra tarea | Editor genérico | — | Documentos |
| Organismo | Editor genérico con selects | — | no comprobado |

⚠ Dos puntos del árbol que no siguen lo definido:

- **El despacho por tipo es una cadena de 7 banderas** en `InspectorEdicion` (`esAnalizar`,
  `esElaborar`, `esNotificar`, `esEsperarPlazo`, `esFaseConsultas`, `esSolicitud`, `esFase`).
  `GUIA_REACT_ISLAS.md` («Excepciones de los editores de tarea») dice que a la segunda excepción por la
  misma causa raíz hay que señalarla como patrón a factorizar y no seguir apilando condicionales.
  `[PROVISIONAL] →` un registro de editores por tipo.
- **El pintado de documentos está repetido** en `Documentos` (Inspector), `AccionesApertura` y
  `FichaDoc` (Despensa), `ItemDoc` (menú contextual) y los desplegables de elegir documento.
  `[PROVISIONAL] →` componente común de mini-lista de documentos.

### 4.4 El alta (lo que el estándar no define) `[VERIFICADO]`

| Variante | Dónde | Observación |
|---|---|---|
| Modal Bootstrap con recarga de página | 11 listados con un `modal fade` en su plantilla: tipos de documento, efectos de plazo, config. del motor, catálogo de requerimientos, tablas maestras, catálogo de plazos, firmantes, requisitos, usuarios, normas y variables, ítems técnicos | **#793** (abierto) describe el parpadeo al fallar la validación en 10 de ellos. Tablas maestras no figura en #793 (`[LECTURA]`: su modal es de alta) |
| Página completa | Nueva entidad (`entidades.nueva`), nueva plantilla (`admin_plantillas.nueva`, `form.html`), alta de expediente (`alta_expediente.nuevo`) | — |
| Crear hijo por la Despensa | Árbol | Propio del árbol |

### 4.5 Modal grande: usos `[VERIFICADO]`

E5 lo reserva a sub-colecciones con CRUD: direcciones y autorizaciones de entidades, excepciones del
motor, municipios del expediente. Se usa **también para ver un documento generado** (certificados,
informe de fin de instrucción, diagnósticos), mediante `abrir_en: 'modal'`, desde el árbol, el pool y
el seguimiento. Ese segundo uso no figura en ADR-023 §6.

### 4.6 Sin inspector

Dashboard, hub del supervisor, estadísticas (isla React), perfil, demo del diagrama, paleta de
comandos, y la pestaña «Subir documento» de Mi trabajo (solo enlaza al pool).

## 5. Hechos sobre el contenedor del inspector `[VERIFICADO]`

Condicionan qué tecnología puede pintar cada contenido.

- En el **árbol**, el cuerpo del inspector lo pinta la propia isla React.
- En **todos los demás módulos**, incluido Mi trabajo, el overlay global (`inspector-overlay.js`) hace
  `fetch` de un fragmento Jinja y lo inyecta con `innerHTML`. Esto no depende de que el listado de
  origen sea Jinja o React (la cola es React y su inspector es un fragmento Jinja).
- **React no se monta en un fragmento inyectado:** `mountIsland` busca su contenedor
  (`[data-react-island="<nombre>"]`) cuando carga el bundle; no existe mecanismo para montar uno
  después. El light-dismiss de `inspector-overlay.js` no cierra el panel por un clic en el área de una
  isla (`[data-react-island]`), porque «las islas React gestionan su propia selección».
- **Los `<script>` de un fragmento del inspector no se ejecutan.** Lo documentan cuatro ficheros JS
  (`reglas-motor-cascada.js`, `catalogo-plazos-cascada.js`, `requisitos-inspector.js`,
  `plantillas-inspector.js`), que por eso usan delegación global. `modal-large.js` **sí** re-ejecuta los
  scripts de su fragmento.
- `AppInspector` expone `open`, `mountReact`, `close`, `refresh`, `setLocked`, `isOpen`, `currentSel` y
  emite `inspector:opened|swapped|closed|saved`. `AppModalLarge` expone `open`, `close`, `refresh`; sus
  formularios `[data-modal-form]` se envían por XHR.
- La edición del inspector de listados se envía por XHR con la cabecera `X-Requested-With`.

## 6. Inventario del tratamiento de documentos

### 6.1 Resumen `[VERIFICADO]`

| Verbo | Backend | Interfaz |
|---|---|---|
| Abrir | Una función: `detalle_nodo.info_apertura_documento` (5 llamadores) | 6 pintados distintos, más los certificados por otro camino |
| Nombrar | Un método del modelo: `Documento.nombre_visible()` (24 apariciones en 10 ficheros) | Todos lo consumen |
| Subir | Un embudo: `ingesta_pool.ingestar_en_pool` → `almacenamiento.contenido.subir` | 5 entradas (pool ×2, Despensa ×2, alta) y una pestaña que solo enlaza al pool |
| Listar | 6 serializadores a mano de la misma entidad, con campos distintos | 5 componentes que dejan elegir un documento del pool |
| Enlazar | Un servicio principal (`editar_tarea`) más otros destinos | 9 gestos |
| Editar / sustituir / borrar | Rutas en `modules/expedientes` | Solo en la página del pool; el árbol no puede |
| Proteger / avisar | Varias guardas (sellos, referenciado, contenido) | Cada pantalla enseña lo suyo |

El backend está más centralizado que la interfaz. Donde se centralizó en el servidor (`nombre_visible`,
`info_apertura_documento`, `ingesta_pool`, `contenido`) no hay dispersión.

### 6.2 Listar

| Dónde | Campos | Lo consume |
|---|---|---|
| `modules/expedientes/routes.py::pool_documentos` (`GET /expedientes/<id>/documentos`) | Filas completas: extensión, URL externa, `puede_sustituir`, `es_referenciado`, `apertura`, reformado, principal | Página Jinja del pool |
| `…::pool_documentos_json` (`GET …/documentos/json`) | `{v, t}` con «nombre — tipo — fecha» | **Sin consumidor** (§7.2) |
| `api_expedientes.py::pool_documentos` (`GET /api/expedientes/<id>/pool`) | `id`, `nombre`, `tipo_doc`, `tipo_doc_codigo`, `fecha` (dd/mm/aaaa), apertura | Despensa, `NotificarEditor`, `AnalizarEditor`, `AnclaSolicitud`, por el store (una carga por vida de la isla) |
| `esquema_editable._pool_docs` | `{valor, texto = nombre}`; sin tipo ni fecha | Selects del editor genérico (`documento_resultado_id` de la fase, `documento_id` del organismo) |
| `detalle_nodo._serializar_documento` | `id`, `rol`, `nombre`, `tipo_doc`, `fecha`, apertura (y `subrol` en `NOTIFICAR`) | Inspector en lectura, cola, menú contextual |
| `api_huerfanos.py::listar_huerfanos` | + `asunto`, expediente, responsable; sin `tipo_doc_codigo` | Radar de huérfanos |

El checklist de `AnalizarEditor` trae además su propio `item.documento`, y los certificados el suyo.
Un mismo documento se enseña de formas distintas según la pantalla («tipo · fecha», «fecha · nombre»,
«nombre — tipo — fecha», solo el nombre), y la fecha viaja en dos formatos en la misma lista (§6.10).

**Listado del pool, columnas y funciones:** selección por fila; documento (con su apertura); asunto;
extensión; tipo con marcas `PROYECTO` y `REFORMADO`; fecha administrativa; prioritario; acciones por
fila (editar, sustituir, borrar o candado). Edición masiva (tipo, fecha, prioridad); cuatro filtros en
el cliente (nombre o asunto, extensión, tipo, prioridad); todas las filas cargadas de golpe. El
candado sale de `_documento_es_referenciado`, que recorre seis relaciones
(`proyecto_vinculado`, `vinculos_tarea`, `notificacion`, `anclado_en_solicitud`,
`anclado_en_fin_instruccion`, `anclado_en_cierre`) y devuelve un booleano.

### 6.3 Abrir

Backend: `info_apertura_documento` decide enlace, si es externo, si se puede abrir y cómo
(`abrir_en`: `enlace` o `modal`) y resuelve los `bddat://`. Lo llaman el detalle del nodo, el pool
Jinja, `/pool`, el radar y `cert_cierre_solicitud`.

Interfaz, cada sitio reinterpreta `puede_abrir` y `abrir_en`:

| Dónde | Cómo abre |
|---|---|
| `Inspector.jsx::Documentos` | botón con `data-modal-large-url` (delegación), `<a>` o texto |
| `Despensa.jsx::AccionesApertura` | `window.AppModalLarge.open(...)` directo (el `stopPropagation` de la ficha impide la delegación) o `<a>` |
| `MenuContextual.jsx::ItemDoc` | `data-modal-large-url` o `<a>` |
| `seguimiento_y_huerfanos/index.html` (JS del listado) | `AppModalLarge.open` en línea o `<a>` |
| `tareas_y_subidas/_inspector_cola.html` | `<a href="{{ d.enlace }}">`, **sin mirar `abrir_en` ni `puede_abrir`** |
| `pool_documentos.html` | usa `apertura` |
| `Inspector.jsx` (certificados) | `enlace_vista` + `AppModalLarge`, por otro camino |

### 6.4 Subir y crear

Embudo del backend: `ingesta_pool.ingestar_en_pool` → `contenido.subir`, usado por la ruta del pool y
por el alta de expediente (sin HTTP).

| # | Entrada | Particularidades |
|---|---|---|
| 1 | Pool, `modal-subir` (varios ficheros) | Metadatos por fichero, reformado de `DOC_PROYECTO`, aviso «ya está» en JS plano, parseo especulativo de Notifica, `EntradaFecha` |
| 2 | Pool, `modal-url-externa` | La propia ruta construye el `Documento(`; no pasa por el embudo |
| 3 | Despensa, `SubidaInline` | Un fichero; sugerencia de tipo y asunto (#367); aviso «ya está» en React; `<input type="date">`; deja el documento en staging |
| 4 | Despensa, `SubidaAncla` | Mismo endpoint con tipo fijo `MODELO_SOLICITUD`; fecha obligatoria |
| 5 | Alta de expediente (Jinja) | Llama al servicio directamente |
| — | Mi trabajo, `SubirDocumento` | No sube: elige expediente y enlaza al pool. Su comentario: «un único método, un único sitio» |

Producción de documentos sin subida: generar escrito (`/api/escritos/generar`); diagnósticos y cinco
servicios de certificados (seis sitios que construyen `Documento(` con `bddat://`, cada uno buscando
su `TipoDocumento` por código); copia del edicto (`copiar_documento`).

Duplicados dentro de la subida:

- El aviso «ya está en el expediente» existe dos veces (`shared/avisoYaExiste.jsx` y el JS del pool).
  El propio código lo dice: «Gemelo del aviso de pool_documentos.html. Si cambia uno, cambiar el otro».
- `quitarComprimidos` ya está resuelto con un wrapper React sobre el JS único
  (`shared/subida.js` → `static/js/subida-comprimidos.js`).
- Selector de tipo: el pool lo pinta el servidor (con `data-codigo`); la Despensa lo pide a
  `GET /api/tipos-documento?limit=100`, ruta de la sección de administración
  (`acceder_tipos_documentos`, que tienen los cuatro roles). Hay unos 69 tipos y no se sigue el cursor.
- Tipo por defecto `1` en cuatro sitios: `|| '1'` (JS del pool), `|| 1` (Despensa), `or 1` (ruta de
  subida) y `or 1` (ruta de edición).
- Tres widgets de fecha: `EntradaFecha` (JS plano) y `<input type="date">` en tres componentes React.

### 6.5 Enlazar o elegir un documento

El gesto del usuario es el mismo —elegir un documento del pool, a veces filtrado, a veces subiéndolo
ahí mismo—. Cambia el destino:

| Gesto | Dónde vive | Destino | Servicio |
|---|---|---|---|
| «+ Consumido / + Producido», luego Guardar | `Despensa.jsx` + `store.vincularDoc` | tarea ↔ documento, con rol | `editar_tarea` |
| Desplegable de justificante | `NotificarEditor` (`PATCH …/notificar documento_id`) | producido de la `NOTIFICAR` | `editar_tarea` + hook |
| Generar escrito | `ElaborarEditor.onGenerado` | consumido del `ELABORAR` | `editar_tarea` vía guardar |
| «Vincular aquí» / «Ir a la tarea» | `_inspector_huerfano.html` (JS plano) | tarea ↔ documento | `vincular_huerfano` → `editar_tarea`; o `?doc_pendiente=` → Despensa |
| Aplicar anuncio de edicto | sin pantalla (#1037) | producido de varias `NOTIFICAR` | `aplicar_anuncio_edicto` → `editar_tarea` |
| Requisito documental | `AnalizarEditor::FilaRequisitoDocumental` | requisito ↔ documento | endpoint propio |
| Anclar proyecto principal | `AnalizarEditor` y pool | proyecto ↔ documento | `anclar-principal` |
| `documento_resultado_id` / `documento_id` | editor genérico (select de `_pool_docs`) | fase / organismo ↔ documento | `editar_fase` / `editar_organismo` |
| Escrito de solicitud | `AnclaSolicitud` y alta | solicitud ↔ documento | `crear_solicitud` |

El estado del vínculo vive en tres sitios del cliente: el borrador del store, el payload propio de
cada editor y la recarga del detalle. `NotificarEditor` y `AnalizarEditor` persisten por su cuenta,
fuera del ciclo Guardar/Cancelar (ADR-023 §5 bis lo prevé como «superficie-de-trabajo»).

### 6.6 Editar, sustituir, borrar

Solo en la página del pool (`modal-editar-doc`, `modal-sustituir`, `borrar`, edición masiva) y, para
borrar, en el listado del radar. Campos editables: tipo, fecha, asunto, prioridad, observaciones, URL
(solo externas), principal, reformado. Las únicas rutas del pool que llama React son `anclar-principal`,
`ya-existe` y `subir`: **desde el árbol no se puede corregir un documento**.

### 6.7 Proteger y avisar

| Mecanismo | Dónde se ve |
|---|---|
| `sellos.motivo_sellado` (documento citado por un certificado, o el propio certificado) | 422 al editar en el pool |
| `_documento_es_referenciado` (6 relaciones, booleano) | Candado del pool |
| `estaSellado` (`sellado.js`) | La Despensa dice «Fase cerrada: reábrala…» |
| `contenido.comprobar_para_vincular` | Error al vincular un documento sin contenido utilizable |
| Bloqueo sin destinatario (ADR-051 §B) | 422 en el `PATCH` de la `NOTIFICAR` |

### 6.8 Nombrar

`Documento.nombre_visible()` (ADR-050 §C) es el único punto: nombre del fichero; o, para `bddat://`, el
nombre del tipo; o el último tramo de una URL externa; o «Documento <id>». **#958 («nombre legible de
diagnósticos y certificados») está desactualizado:** describe 7 sitios que componían el nombre por su
cuenta, anterior a #1007. Lo que queda abierto en #958 es «algo que distinga» un certificado de otro.

### 6.9 Contrato de apertura

Un documento llega al navegador con `enlace`, `externo`, `puede_abrir` y `abrir_en` (`enlace`, `modal`
o `None`). Distinguen: ficheros propios y URL externas (`pool_descargar_documento`), certificados con
vista HTML (cumplimiento y cierre de fase, cierre de solicitud), certificados con PDF (`cert_pdf`) y
diagnósticos (`diagnostico_modal`).

### 6.10 Hallazgos de comportamiento `[LECTURA]`

1. **La Despensa mete en el pool un documento recortado tras subirlo.** `store.subirDocumentoDespensa`
   añade `{id, nombre, tipo_doc, fecha}`: sin `tipo_doc_codigo`, sin `enlace` ni `abrir_en`, y con la
   fecha en ISO cuando `/pool` la sirve en dd/mm/aaaa. Su gemela `subirAnclaSolicitud` sí copia
   `tipo_doc_codigo`. Consecuencia: el documento recién subido no tiene botón de abrir y, en una
   `NOTIFICAR`, no aparece en el desplegable de justificantes (filtra por `tipo_doc_codigo`) hasta
   recargar. Despensa y `NotificarEditor` conviven en el mismo inspector.
2. **La cola de Mi trabajo ignora `abrir_en`:** un diagnóstico se abre como enlace a un fragmento de
   modal en pestaña nueva; en el caso raro de un documento sin acción de apertura (certificado de cierre
   de solicitud sin solicitud anclada) sale con `href="None"`.
3. **El autorrelleno de fecha del pool propone la fecha equivocada en los justificantes de Notifica**
   (detalle y issue: #1036; ADR-049 §G). `pool_documentos.html` solo reacciona a
   `JUSTIFICANTE_NOTIFICA`, no envía `tipo_doc_codigo` y lee `fecha_puesta_disposicion` en lugar de
   `fecha_sugerida`; nadie en el frontend lee `fecha_sugerida`. Hay que reproducirlo.
4. **«Vincular aquí» del radar probablemente no funciona** (§7.3).
5. Ninguna API dice al frontend qué tipos de documento exigen fecha (`TIPOS_FECHA_OBLIGATORIA` no se
   expone; `GET /api/tipos-documento` devuelve `id`, `codigo`, `nombre`, `descripcion`, `origen`,
   `protegido`).
6. El código señala sus gemelos a mano: `AYUDA_PRODUCIDO_ESPERAR_PLAZO` (Python y JS) y el aviso «ya
   está» (JS plano y React), ambos con «si cambia uno, cambiar el otro».

### 6.11 Lo que dicen los documentos

- `GUIA_REACT_ISLAS.md` («Excepciones de los editores de tarea (bespoke)») fija un umbral para
  factorizar: una excepción en un solo editor es un caso único, pero si una segunda nace de la misma
  causa raíz ya es un patrón, y no hay que esperar a una tercera. La causa raíz de su
  ejemplo —«el editor gestiona su propio vínculo de documento»— la cumplen hoy `AnalizarEditor`,
  `NotificarEditor` y `ElaborarEditor`.
- ADR-023 §5 bis describe la «superficie-de-trabajo» con sub-bloques que persisten por su cuenta
  (vincular documento incluido); no dice cómo se reutilizan.
- `SubirDocumento.jsx`: «un único método, un único sitio» para subir. Las entradas 3 y 4 de §6.4
  vinieron después (#367, #428).

## 7. Acceso por ruta y código muerto

### 7.1 Acceso por ruta `[VERIFICADO]`

| Vista (endpoint) | Cómo se llega |
|---|---|
| Expedientes (`expedientes.listado_v2`) | Menú (orden 10) |
| Entidades (`entidades.index`) | Menú (20) |
| Usuarios (`usuarios.index`) | Menú (30) y hub |
| Mi trabajo (`mi_trabajo.index`) | Menú (5); redirige según el rol |
| Cola (`tareas_y_subidas.index`) | Menú (6) y la redirección del administrativo |
| Control y Gestión (`supervisor.index`) | Menú (7) |
| Seguimiento y huérfanos (`seguimiento_y_huerfanos.index`) | Menú (8) y la redirección del tramitador |
| Estadísticas (`supervisor.estadisticas`) | Solo desde el hub |
| Tablas maestras, Config. del motor, Normas y variables, Ítems técnicos, Tipos de documento, Requisitos, Catálogo de requerimientos, Plantillas, Catálogo de plazos, Efectos de plazo, Delegación Territorial, Firmantes (12) | Solo desde el hub; ninguna tiene entrada de menú |
| Mensajes internos | Icono de la barra superior |
| Perfil | Menú de usuario de la barra superior y tarjeta del dashboard |
| Pool (`expedientes.pool_documentos`) | Desde el inspector del expediente y desde «Abrir gestor» de Mi trabajo. Sin menú |
| Árbol (`expedientes.arbol`) | Desde el inspector del expediente, el buscador Ctrl+K, la cola, el seguimiento y el pool. Sin menú |
| Alta de expediente, nueva entidad, nueva plantilla | Botón en su listado |
| **Proyectos** (`proyectos.index`) | ⚠ Entrada de menú (orden 15) que **redirige al listado de Expedientes** |
| **Demo del diagrama** (`demo.diagrama`) | ⚠ **Solo URL, y pública** (sin `@login_required`). POC de la isla `diagrama-esftt`; solo la usa un smoke test |
| **`/mis_expedientes`** (`dashboard.mis_expedientes`) | ⚠ Alias que redirige a Expedientes; ningún enlace |

El menú tiene 8 módulos con `navigation` en su `metadata.json`: `mi_trabajo`, `tareas_y_subidas`,
`supervisor`, `seguimiento_y_huerfanos`, `expedientes`, `proyectos`, `entidades`, `usuarios`.

### 7.2 Código muerto (sin consumidor en `app/` ni en `react-src/`) `[VERIFICADO]`

| Qué | Evidencia |
|---|---|
| Blueprint `app/routes/proyectos.py` | No se importa en `create_app`. Listado de proyectos con filtros propios; tiene el mismo nombre `proyectos` que el módulo vivo |
| `GET /api/proyectos` | Sin consumidor, ni en tests. Su único cliente era `proyectos_listado.js`, muerto |
| `GET /api/entidades/consultables` | Sin consumidor en la app; solo un test de sus helpers (#461) |
| `GET /api/documentos/<id>/candidatas` | Sin consumidor en la app (el fragmento del huérfano calcula las candidatas en el servidor); solo un smoke test |
| `GET /plantillas/api/tokens` | Sin consumidor; su docstring dice «stub» |
| `GET /expedientes/<id>/documentos/json` | Sin consumidor (solo mencionado en `INVENTARIO_BACKEND.md`) |
| `POST /expedientes/tarea/<id>/generar_cert` | Sin botón en ninguna pantalla. Es el único llamador de `certificados.crear_cert` (certificado de plazo cumplido) en la app; los tests sí lo ejercitan |
| `static/js/proyectos_listado.js`, `municipios_selector.js`, `v2-scroll-to-top.js` | Sin referencia (el vivo es `v2-tabla-scroll-to-top.js`) |
| `static/css/v3-tramitacion.css` | Sin referencia |
| `templates/macros/bc_cards.html`, `templates/vistas/vista3_bc/_tabla_hijos.html` | Sin referencia; el directorio `vistas/` solo contiene ese fichero (resto del sistema BC, retirado en #500) |
| Rama `modo == 'editar'` de `admin_plantillas/form.html` | La plantilla solo se renderiza con `modo='nueva'` (6 llamadas); el GET de editar redirige al inspector |
| `listado_v2.columns` en `proyectos/metadata.json` | Configura un listado que ya no existe |
| React `shared/ui/Toast.jsx` | Sin importar; todo usa `showToast`. La guía lo cita como disponible |
| React, exports sin uso: `FILA_TAREA_H` (`layout.js`), `fechaCorta` (`plazoActo.js`), `faseDeSeleccion` (`sellado.js`), `getUser`, `getPermisos`, `getRolActivo` (`shared/auth.js`) | Sin uso. La guía recomienda los tres de `auth.js` |

### 7.3 Código que existe pero no es alcanzable o no funciona

| Qué | Por qué |
|---|---|
| «Vincular aquí» del huérfano (`POST api.vincular_huerfano`) `[LECTURA]` | Su lógica va en un `<script>` en línea dentro de `_inspector_huerfano.html`; el overlay no ejecuta scripts (§5) y no hay otro manejador de `data-vincular-directo` en `app/`. Sin reproducir |
| `postNotificar` y `postNotificarParsear` (`api.js` del árbol) `[VERIFICADO]` | Apuntan a rutas que ya no existen: es el `NotificarEditor` roto (#929) |

### 7.4 No es código muerto

Los redirects de compatibilidad: `GET /<id>` y `GET /<id>/editar` de cada módulo, y
`proyectos.detalle` y `proyectos.editar_proyecto`. Mantienen vivos los enlaces antiguos (E4).

### 7.5 Método y límites

- El script busca el nombre de cada elemento en el texto de los demás ficheros. **No ve referencias
  dinámicas**: dio dos falsos positivos (`pool_editar_documento` y `pool_sustituir_documento`, cuya URL
  se compone en JS) que se descartaron a mano.
- Un fichero muerto puede estar «referenciado» solo por otro muerto, o por la docstring de la propia
  ruta: se repitió el análisis ignorando ambos casos.
- Los tests no se cuentan como consumidores; se anotan aparte.
- Documento obsoleto: `docs/diseño/AUDITORIA_UI.md` (corte del 27/05/2026, antes de ADR-023) describe
  un sistema que ya no existe (tramitación BC de 5 niveles, `api_bc`, wizard).

## 8. Cuestiones abiertas para el ADR

Preguntas, no respuestas. Cada una se revisa por separado.

1. `[ABIERTO]` **Listados con varias tablas por página.** `lista_v2_base` asume una sola. Cuatro
   páginas copian el marco a mano (tablas maestras, normas y variables, seguimiento y huérfanos,
   configuración del motor) y comparten problemas (#755).
2. `[ABIERTO]` **Tecnología de los listados.** Hoy el estándar es Jinja; `Cola.jsx` lo reproduce en
   React. ¿Se mantiene el estándar Jinja, se admite React, o se decide por caso? ¿Afecta al resto de
   listados de la aplicación o solo a documentos?
3. `[ABIERTO]` **Listado general de documentos frente a mini-listados.** ¿Son dos conceptos o uno?
   Opciones planteadas por Carlos en P3 y P4. Lo que condiciona la respuesta, `[VERIFICADO]`: los
   mini-listados viven dentro del inspector y el general lo abre; el estándar ya tiene modo masivo
   y columnas declarativas; el cuerpo del inspector fuera del árbol es un fragmento Jinja (§5).
4. `[ABIERTO]` **Qué contenedor pinta cada contenido** (árbol React frente a fragmentos Jinja) y qué
   se comparte entre ambos (serializador del servidor, clases CSS, otros).
5. `[ABIERTO]` **Contrato único del dato de documento** frente a los seis serializadores actuales, y
   qué hacer con el pool cargado una vez por vida de la isla.
6. `[ABIERTO]` **El alta.** Tres variantes y ningún ADR que diga cuál vale (§4.4).
7. `[ABIERTO]` **Uso del modal grande para ver documentos generados** (§4.5): ¿se amplía E5, o es otra
   capa?
8. `[ABIERTO]` **Scripts en fragmentos del inspector.** Regla para el JS de un fragmento (hoy se
   documenta en cuatro ficheros, y el huérfano la incumple).
9. `[ABIERTO]` **Menú frente a hub.** Solo 8 módulos tienen entrada de menú y 12 viven en el hub. ¿Qué
   regla decide cuándo una vista entra al menú?
10. `[ABIERTO]` **Edición de un documento desde el árbol.** Hoy exige salir a la página del pool.
11. `[ABIERTO]` **Despacho de editores por tipo en el árbol** (§4.3, 7 banderas) y su relación con el
    criterio de `GUIA_REACT_ISLAS.md`.
12. `[ABIERTO]` **Código muerto y rutas sin consumidor** (§7.2): qué se retira y cómo se evita que
    vuelva a acumularse. En particular `generar_cert`, que es una función de negocio sin interfaz y no
    un resto de limpieza, y `demo.diagrama`, que es pública.
13. `[ABIERTO]` **Documentación obsoleta** (`AUDITORIA_UI.md`) y dónde queda el mapa vivo de vistas.
14. `[ABIERTO]` **Alcance.** Qué entra en el ADR (listados, inspector, documentos, altas, menú, código
    muerto) y qué va a otro.

## 9. Relación con issues y planes `[VERIFICADO]`

| Issue | Estado | Relación |
|---|---|---|
| #929 | Abierto | Zona A (registro y destinatario). Sin interfaz nueva de documentos ni atajo (D1) |
| #1036 | Abierto | Fecha equivocada en el autorrelleno de la subida (hallazgo 3 de §6.10) |
| #1037 | Abierto | Edicto: pantalla de aplicar el anuncio (usa el gesto «aplicar anuncio» de §6.5) |
| #1038 | Abierto | Representante y sede de la solicitud |
| #1039 | Abierto | `Cola.jsx` al listado estándar (D2) |
| #881 | Abierto | Reforma del listado del pool, escrita contra el estándar de entonces (P1). Cita la columna de usos y el N+1 de `_documento_es_referenciado` |
| #958 | Abierto | Nombre legible de `bddat://`; en buena parte resuelto por `nombre_visible()` (§6.8) |
| #755 | Abierto | «Volver arriba» roto o ausente en 4 listados; el caso 4 es `Cola.jsx` |
| #793 | Abierto (M5) | Modales de alta con recarga completa en 10 módulos (§4.4) |
| #935 | Abierto | `sugerencia_subida` pierde la sugerencia con varias `ENTRADA`; afecta a los pasos `NOTIFICAR` |
| #1009, #1010 | Abiertos | Tocan `ElaborarEditor.jsx` (aviso de plantilla desfasada; botón «Editar» por WebDAV) |

`ESTADO_ADR049.md` (zonas A–E de #929) y `ESTADO_ADR050.md` (fases 4–7 y diferidos) no cambian con este
documento. Cómo encajan los issues que salgan de este ADR en esos dos planes se fija en el hilo que lo
redacte.

## 10. No comprobado

- Nada de lo marcado `[LECTURA]` en el navegador ni con tests. Los hallazgos 1 a 4 de §6.10 conviene
  reproducirlos.
- El inspector de `Organismo` en edición (qué muestra la Despensa).
- Si el formulario de edición del inspector aguanta la complejidad del pool (ADR-044: principal y
  reformado; rectificación de URL) y la subida de un fichero para «sustituir».
- Que `/documentos/json` esté realmente sin uso fuera de `app/`, `react-src/`, `tests/` y `scripts/`.
- Las plantillas de `supervisor/`, `_inspector_expediente.html` y los fragmentos de certificados, solo
  contados; `perfil` por dentro.
- Los permisos por rol de cada entrada del hub y del menú.
