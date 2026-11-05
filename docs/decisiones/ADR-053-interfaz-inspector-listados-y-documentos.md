# ADR-053 — Interfaz: marco único del inspector, listados estándar y mini-listados de documentos

**Estado:** Adoptada (2026-10-13) — decisiones tomadas por Carlos el 11/10/2026 en el hilo de posiciones (D5–D19 del pre-ADR); sin implementar (lo implementa la cadena #1041 a #1051). Lo marcado *Interpretación* en el texto sigue siéndolo hasta que Carlos lo confirme o lo fije la fase de un issue
**Fecha:** 2026-10-11
**Depende de:** ADR-015 (islas React sobre Jinja) · ADR-016 (el árbol del expediente como isla) · ADR-022 (sistema visual base) · ADR-023 (list-detail + inspector universal)
**Enmienda:** ADR-023 §5 bis (el marco de edición pasa a ser de todos los inspectores y lo pinta el shell) · §6 (el modal grande también sirve para ver documentos generados) · §8 (el «mínimo de lectura» se sustituye por un ancho mínimo definido por cada caso) · §9 (la «columna fluida» deja de ser la regla del interior) · ADR-017 «Cómo implementar», punto 4 (la cola de Mi trabajo pasa a listado Jinja)
**Issues:** #1041 a #1051 (el orden y lo que falta, en [`ESTADO_ADR053.md`](../diseño/ESTADO_ADR053.md)). Cerrados con él: #755, #644 y #281. Afectados sin cambio de número: #1039, #881 y #793
**Origen:** revisión de #929 contra el código (09/10/2026), que destapó que el tratamiento de documentos y la interfaz del inspector y los listados no seguían un estándar único; hilo de posiciones del 11/10/2026 con Carlos
**Material de trabajo:** [`docs/diseño/PRE-ADR-interfaz-vistas-y-documentos.md`](../diseño/PRE-ADR-interfaz-vistas-y-documentos.md): inventario completo de las vistas, el inspector, los documentos y el acceso por ruta, y las decisiones D1–D19 tal como las dijo Carlos. **El pre-ADR queda congelado:** donde difiera de este ADR, manda este ADR
**Relacionados:** ADR-029 (menú y hub, fuera de este ADR) · ADR-038 (hub del tramitador) · ADR-050 (almacén y `nombre_visible`) · ADR-049 y ADR-051 (el frontend de las notificaciones, #929)

---

## Contexto

ADR-022 y ADR-023 fijan el estándar: un listado con `ScrollInfinito` en modo selección, y un inspector que se abre al pulsar una fila, con fragmentos Jinja de lectura y de edición. El árbol del expediente, una isla React (ADR-015, ADR-016), monta su propio inspector. La revisión de la interfaz que se hizo a partir de #929 (el inventario completo está en el pre-ADR, §4 a §7; todo leído en código el 10 y el 11/10) encontró lo siguiente.

1. **El marco de edición solo existe en el árbol.** La barra fija con cabecera y control de salida de ADR-023 §5 bis la pintan los componentes React del árbol (`BarraEdicion`, #676 y #688). Los 17 inspectores Jinja no tienen barra: cada fragmento de edición pega su bloque «Cancelar / Guardar» dentro de la zona que hace scroll, y cada uno de lectura su botón «Editar» (16 con `btn-primary` y el del expediente con `btn-success`; el del árbol es otro distinto, `btn-outline-primary`).
2. **El inspector puede quedarse corto de ancho sin avisar.** Mide 900 px por defecto y puede bajar a 320. El cuerpo recorta lo que no cabe (`overflow-x: hidden`), así que «Cerrar» puede quedar fuera de vista; y en edición el clic exterior está bloqueado, de modo que ese control es la única salida.
3. **En el árbol, lectura y edición son cosas distintas.** Al pulsar Editar desaparecen los campos de solo lectura, los plazos, los documentos y los organismos, y aparece un formulario con solo los campos editables más los bloques de acción. En los fragmentos Jinja no pasa: son las mismas tarjetas con controles `readonly` o vivos.
4. **Los documentos dentro de los inspectores están dispersos.** Seis serializadores del mismo dato, seis maneras de abrir un documento, cuatro listas (dos en lectura y dos en la Despensa) y cinco desplegables del pool; el mismo documento sale con textos y formatos de fecha distintos según la pantalla, y `subrol` se serializa sin que nadie lo pinte.
5. **Cinco páginas de listado se desvían del estándar.** Cuatro de ellas ya usan `ScrollInfinito`, pero copian el marco a mano porque `lista_v2_base` asume una sola lista por página y los componentes JS compartidos asumen una sola instancia; la quinta, Delegación Territorial, son tablas de tamaño fijo. Aparte, la cola de Mi trabajo es una isla React que reimplementa el scroll infinito.
6. **El contenedor del inspector lo decide dónde vive, no cómo es su listado.** El del árbol lo pinta la propia isla React por portal. En todos los demás sitios el shell hace `fetch` de un fragmento Jinja y lo inyecta con `innerHTML`: sus `<script>` no se ejecutan y React no se monta dentro de un fragmento inyectado (no está construido). La cola, una isla React, abre un inspector cuyo cuerpo es Jinja; se comprobó en la app el 11/10.

---

## Decisión

### A — Un marco único, pintado por el shell (D9, D10, D12)

El inspector es el primer estándar para todos los casos: la isla del árbol (por ahora la única) y los fragmentos Jinja. Se monta **un marco** que estandariza ver / editar y guardar / cancelar / cerrar, y **lo pinta el shell una sola vez**. El árbol deja de pintar su barra y pasa a alimentar al shell con su estado de borrador (`hayCambios`, `interiorSucio`, `guardando`, guardar, cancelar): es el «puente».

- **En vista:** cabecera y botón Editar, sin cruz. El inspector se cierra con clic exterior (no en otra fila, que cambia la selección), `Escape` o un clic en la franja de redimensionado.
- **En edición:** Guardar y Cancelar, solo habilitados con borrador vivo, y «Cerrar» siempre presente. El contrato de salida de ADR-023 §5 bis no cambia: con la superficie limpia, «Cerrar» sale sin revertir nada; con cambios sin guardar, la salida se comporta como Cancelar.
- **Visibilidad garantizada con cualquier ancho:** en edición se ve, al menos, «Cerrar». La barra del árbol ya lo consigue truncando la cabecera y no los botones; el marco del shell debe reproducirlo.
- **Qué declara cada caso:** el fragmento Jinja declara su título, la URL de su edición y su formulario; el árbol alimenta al shell con su estado. *Interpretación:* los nombres de los atributos y de la API de ese contrato, y cómo se aloja la cabecera del árbol (semáforo, tipo, título, estado, candado), los fija la fase 1 de #1042 prototipando, no este ADR. *Interpretación:* «Editar» vive en el marco, por lo que implica «ver / editar».
- **Contrato implementado en #1042** (13/10/2026, PR #1056): los nombres de los atributos y de la API están en `docs/guias/GUIA_COMPONENTES_INTERACTIVOS.md`, §«Marco único del inspector». Las *Interpretación* de arriba siguen pendientes de que Carlos las confirme.

### B — Cuerpo flexible: ancho mínimo por caso y scroll horizontal (D11)

El interior se deja como lo necesite cada caso, flexible al ancho. **Cada caso define un ancho mínimo** para su visibilidad; por debajo de él, hay scroll horizontal. El usuario lo ve como señal y amplía el inspector, y cada caso no tiene que resolver el apilamiento por su cuenta.

- El scroll horizontal es **solo del cuerpo, nunca del marco**: `overflow-x: auto` en lugar de `hidden`. Por encima de su mínimo, las columnas de cada caso siguen valiendo, así que no hacen falta *container queries* (precisión técnica acordada el 11/10).
- El mínimo del marco sigue siendo el del shell (`MIN_WIDTH`, 320 px).
- Enmienda ADR-023 §8: el «mínimo de lectura», con cifra diferida a la implementación, es el de cada caso. ADR-023 §9: la «columna fluida» deja de ser la regla del interior.

### C — Lectura ≈ edición, también en el árbol (D15)

Lo que se ve antes de editar es casi lo mismo que se ve en modo edición: cambian ligeramente los componentes del formulario, para indicar que se está editando. Es el criterio de Carlos en todos los formularios, y busca coherencia visual. Los fragmentos Jinja ya lo cumplen; el inspector del árbol no, y se lleva a #1043. Qué bloques de lectura se quedan en edición y cuáles solo existen en ella se define en la fase 1 de ese issue: la tabla definitiva está en el [anexo a §C](#anexo-a-c--tabla-definitiva-del-inspector-del-árbol-1043).

#### Anexo a §C — tabla definitiva del inspector del árbol (#1043)

Se definió implementando nodo a nodo, de arriba abajo y de genérico a especializado, con Carlos (13 a 18/10/2026). La lectura y la edición pintan **la misma zona de datos**; la edición añade debajo las acciones y, al final, «Borrar».

**Criterio, en este orden de zonas**

1. **Datos**, idéntica en los dos modos: tarjetas, y debajo los plazos, los organismos y los documentos del nodo. Lo editable es un control de solo lectura en lectura y uno vivo en edición, en el mismo sitio y con el mismo rótulo. Lo que sale en edición también se ve en lectura.
2. **Acciones y creación**, solo en edición: Despensa → lo propio del nodo → «Borrar».
3. **Pie**: «Copiar referencia», en los dos modos.

«Estado» y «Tipo» solo en la barra del marco (§A). No se tocan el payload `detalle_de_nodo`, el esquema editable ni dónde se edita cada dato.

**Tabla**

| Nodo | Tarjetas de la zona de datos (los dos modos) | Editable | Acciones (solo edición, antes de «Borrar») |
|---|---|---|---|
| Expediente | «Datos administrativos» (tipo, heredado, responsable, titular, NIF, nº de solicitudes) y «Datos del proyecto» (título, finalidad, emplazamiento) | Nada en el nodo (se edita en el listado) | Despensa |
| Solicitud | «Datos de la solicitud» y «Solicitante» | Observaciones | Despensa → certificado de fin de instrucción y cierre de la solicitud |
| Versión | «Datos de la versión» | Nada | — |
| Fase | «Datos de la fase» (resultado, nº de trámites, documento resultado, observaciones) | Resultado, documento resultado, observaciones | Despensa → consultas, cumplimiento, cierre, reabrir (según fase) |
| Organismo | «Datos del organismo» | Vía, resultado, dirección, documento | Despensa |
| Trámite | «Datos del trámite» y «Notificaciones del trámite» (a quién falta o sobra notificar) | Observaciones | Despensa → «Añadir las notificaciones que faltan» |
| Tarea genérica | «Datos de la tarea» | Notas | Despensa |
| ANALIZAR simple | «Datos de la tarea» y «Resultado diagnóstico» | Notas | Despensa (sin «+ Producido») → «Producir diagnóstico» mientras falte |
| ANALIZAR extendido | «Datos de la tarea», Check documental, Check técnico, Requerimientos y «Borrador defectos» o «Resultado diagnóstico» | Notas y cada sección (guardan por su cuenta, con la reversión y la justificación de ADR-033) | «Producir diagnóstico» mientras falte (sin Despensa, ADR-033 §1) |
| ELABORAR | «Datos de la tarea» y «Destinatario del escrito» (solo si el trámite tiene destinatario único) | Notas; el destinatario, con su selector dentro de la tarjeta | Despensa → «Generar escrito» |
| NOTIFICAR | «Datos de la tarea», aviso «Notificación al solicitante», «Destinatario», «Registro de la notificación» y «Justificantes previos» | Notas; el registro, con su «Guardar» propio; el destinatario, con sus controles dentro de la tarjeta | Despensa |

«Borrar» es lo último de las acciones, y no se ofrece en el expediente, en la versión ni en una fase cerrada; en esta última, dentro no se crea ni se borra nada y su único camino es «Reabrir fase».

**Qué superficie lleva una tarea.** Lo decide la combinación (tipo de tarea, trámite) en `superficiesTarea.js`, no el tipo solo: una combinación que no figura en la tabla es **genérica** y usa el diseño común, aunque la semilla no tenga ningún caso. La variante de ANALIZAR la dice el nodo del árbol (`analisis_extendido`, de la lista única `TRAMITES_CON_SECCIONES_ANALISIS`); la de ELABORAR (si hay destinatario y si se elige) y la de NOTIFICAR (si va al solicitante) las resuelven sus tarjetas con el endpoint de la tarea. Es el germen del registro de editores de #1047.

**Lo que se deja como estaba, por decisión de Carlos**

- Los bloques que guardan por su cuenta —secciones de ANALIZAR, registro y destinatario de NOTIFICAR, destinatario de ELABORAR— no pasan por el borrador del marco. Lo que llevan escrito sin guardar sí avisa al marco por otro canal (#1055, 18/10/2026; *interpretación*, decidido al implementar y pendiente de confirmar por Carlos): el botón de salida pasa a «Cancelar» y descarta con el aviso de siempre, «Guardar» no se enciende (el bloque tiene su botón), el «Guardar» de la barra pide decisión antes de tirar ese texto y el cierre de la pestaña avisa. El destinatario sigue guardando con un `PUT` inmediato, porque el generador de escritos de ELABORAR lo necesita guardado dentro de la misma edición; solo cuenta como «sin guardar» la entidad elegida y sin confirmar.
- Los mismos documentos salen en más de un sitio (la lista «Documentos» de la zona de datos, la de la Despensa, el select del registro de NOTIFICAR) hasta que #1044 los unifique.
- Las incoherencias que puedan ser un bug no se corrigen en #1043: están anotadas como hallazgos.
- El texto «Tarea ejecutada» de ELABORAR sigue siendo opcional: lo pinta quien calcula el estado a partir de los documentos vinculados.

### D — Dos renderizadores, un contrato; el cuerpo del árbol sigue en React (D13)

- El cuerpo del inspector del árbol sigue en React y el de los demás en Jinja. No se unifica el cuerpo en una sola tecnología.
- El **contrato** es la forma que tiene el editor del inspector de pasar la información al poseedor del dato y viceversa (el poseedor pasa el dato para pintarlo). Es el trabajo de fondo que permite la estandarización. *Interpretación:* en este ADR el contrato concreta dos piezas, lo que el marco necesita de cada caso (§A) y el dato del documento (§E).
- **La forma de un contrato general de campos no se decide.** Carlos no ve necesario ese nivel de generalización: estudio previo y decidir si cabe estandarizar (#1045). Puede acabar en «no se estandariza».
- **Regla de scripts en fragmentos, ratificada:** el JS de un fragmento del inspector va a un fichero global con delegación de eventos en `document`; el modal grande sí ejecuta los scripts de su fragmento. El fragmento del huérfano la incumple (#1046).
- El despacho de editores por tipo del árbol (siete banderas en `InspectorEdicion`) se refactoriza en #1047; es interno del árbol.

### E — Documentos dentro de los inspectores: una fila común con tres modos (D6, D7, D14, D17, D18)

- Los mini-listados de documentos son un concepto distinto del listado general del pool y tienen su propia definición. Se descartan un solo módulo para los dos usos, con o sin inspector, y un módulo incrustable con columnas flexibles: serían salirse del estándar en un listado sin necesidad y complicarían el código adaptando uno a otro con distintas funcionalidades.
- **Una definición de fila común con tres modos:** lista de vinculados, selector del pool y edición del documento. Si el origen del dato difiere, quien lo entrega se adapta al contrato único. Habrá como mínimo dos tipos de mini-listado, uno por renderizador (macro Jinja y componente React), y se asume: otro listado de scroll infinito puede necesitar listar documentos dentro de su inspector. Se estudia caso a caso qué sitios admiten la unificación (#1044).
- **Un documento tiene un único sitio donde se edita** (editar, no crear). Qué contenedor lo aloja, el inspector del pool o, desde otros sitios, el modal grande, depende del marco (§A) y de que el formulario del pool quepa en el inspector; se decide en #1042, #881 y #1044.
- **El modal grande también sirve para ver documentos generados** (certificados, informes, diagnósticos). No es otra capa. Enmienda ADR-023 §6, que lo reserva a colecciones con CRUD propio.
- La definición de la fila, de sus tres modos y la tabla caso a caso (fase 1 de #1044) están en el [anexo a §E](#anexo-a-e--la-fila-común-de-documentos-1044).

#### Anexo a §E — la fila común de documentos (#1044)

Fase 1 de #1044 (definición, sin código), con Carlos, el 01/11/2026. Va como **decisión** lo que fijó él y como *Interpretación* lo que salió al redactarlo, hasta que lo confirme o lo fije la fase de un issue. Se contrastó con un mockup hecho con las hojas de estilo reales de la app (320 y 480 px; no versionado) y con el código del 01/11.

**Decidido por Carlos**

1. **La fila es de dos líneas apiladas, no de columnas.** Es lo que cabe a 320 px con el criterio de #1043 (ningún texto por debajo de 110 px). *Enmendado por Carlos el 01/11/2026, tras verla en la app:* **línea 1**, el nombre del fichero con su extensión (el enlace que lo abre) y, detrás, su fecha, en la misma fila, con las acciones a la derecha; **línea 2**, los detalles como iconos —rol, subrol y marcas— y, detrás, la descripción (el tipo de documento). Antes, la línea 1 era el nombre y las acciones, y la línea 2 el rol con un rótulo de texto, la fecha, las marcas y el tipo.
2. **Sin espacio, la fila no hace scroll propio y trunca.** Lo que no cabe se trunca con puntos suspensivos y el valor completo va en el `title`. El scroll horizontal es del cuerpo del caso (§B), nunca de la fila. A 320 px el nombre y la descripción se recortan; a 480 px caben enteros. Carlos lo acepta.
3. **Los detalles son iconos con tooltip, no etiquetas de texto.** Primero las marcas (`PROYECTO`, `REFORMADO` y `PRIORITARIO` en mayúsculas llenaban dos líneas más de una sola fila) y, el 01/11/2026, también el rol: los badges de «Consumido» y «Producido» no eran coherentes con el árbol ni con el detalle del seguimiento, y se leían peor que el icono. El rol usa **los mismos iconos que el árbol y el seguimiento** (`bi-box-arrow-in-down` consumido, `bi-box-arrow-up` producido), en gris neutro. **Todos los iconos de la fila llevan tooltip** (`title`) y `aria-label`, también el del fichero.
4. **El asunto no va en la fila:** va en el `title` y en el texto de opción de los desplegables, que es donde distingue los duplicados (`oficio_separata.pdf` ×3).
5. **Los cinco desplegables del pool se quedan como `<select>`** (justificante final, requisito del checklist, escrito de solicitud, documento resultado de la fase, documento del organismo), con un **texto de opción común**. No pasan a filas ricas.
6. **Edición del documento: el principio queda fijado** —un único fragmento Jinja del formulario, con el inspector del pool y el modal grande como contenedores— y **el botón «Editar» en las filas de los demás sitios se difiere a después de #881**, que es quien mueve el formulario. #1044 implementa dos modos (vinculados y selector); el de edición llega con #881. *Estado tras #881 (01/11/2026):* el fragmento Jinja existe y su contenedor es el inspector del pool ([anexo a §F](#anexo-a-f--el-pool-881)); el botón «Editar» de las filas del árbol de React **sigue sin hacer y fuera de #881**: lo decide Carlos al final del hilo, por la fluidez de trabajo.
7. **Una sola lista de vinculados en edición.** La zona de datos y la Despensa dejan de enseñar los mismos documentos: queda la de la zona de datos, que en edición gana «quitar» y se alimenta del borrador (D15).

**Confirmado por Carlos el 01/11/2026** (salió al redactar o al implementar, y él lo confirmó, punto por punto): la función única `documento_fila` y sus campos, el texto de opción dentro de la fila (`texto_opcion`), el subrol como segundo icono (avión de papel y clip), `text-secondary` en la línea de detalle, los modos vinculados y selector, el botón del modal como enlace, el documento recién subido arriba del pool y el autorrelleno solo en los tipos que exigen fecha. Cada uno está donde corresponde más abajo, sin la marca de *Interpretación*.

**Interpretación** (la fijó la redacción, sin confirmar por Carlos): las dos piezas (enlace y fila), que el pool se cargue una vez por vida de la isla, el orden de truncado, los iconos concretos de las marcas, la medida y las filas de la tabla «caso a caso» que no son decisión suya. Lo demás de la lista es lo confirmado de arriba.

- **Dos piezas:** el *enlace* (el nombre como lo que abre: `puede_abrir`, `abrir_en`, `enlace`; lo usan también los sitios de un solo documento, como «Descargar» de `ElaborarEditor` o el documento de cada requisito del checklist) y la *fila*, que lo contiene.
- **Datos del contrato:** `id`, `nombre`, `tipo_doc`, `tipo_doc_codigo`, `fecha` en ISO (cada renderizador la pinta dd/mm/aaaa, y «sin fecha» si falta), `asunto`, `enlace`, `externo`, `puede_abrir`, `abrir_en`, `rol`, `subrol` y `marcas`. Una función única del servidor junto a `info_apertura_documento` (propuesta de nombre: `documento_fila`), a la que se adaptan los demás: `_serializar_documento`, `/api/expedientes/<id>/pool`, `_documento_notificar_json` y los `justificantes_previos` de NOTIFICAR, `api_huerfanos` (añade sus extras) y la respuesta de `pool_subir_documento` (hoy sin apertura y con la fecha en ISO, de ahí el recorte de `subirDocumentoDespensa`). `pool_documentos_json` se retira: no tiene consumidor. Son ocho los serializadores, no seis (el inventario del pre-ADR no contaba el de NOTIFICAR ni la respuesta de la subida).
- **El pool cargado una vez por vida de la isla se mantiene**: alimenta el selector y las listas de vinculados de la Despensa; lo que cambia es que sus entradas, y la del documento recién subido, son del mismo contrato.
- **Orden de supervivencia** cuando falta sitio: se trunca primero el nombre y, en la línea 2, la descripción; la fecha (de ella cuelgan los plazos), los iconos y las acciones conservan su ancho.
- **Rol y subrol.** Rol: `CONSUMIDO` o `PRODUCIDO`, del vínculo documento-tarea (decisión de Carlos: los iconos del árbol, ver 3). Subrol: solo en NOTIFICAR, afina el consumido en `A_NOTIFICAR` y `JUSTIFICANTE_PREVIO`; *confirmado por Carlos:* se pinta como un segundo icono junto al del rol, un avión de papel (`bi-send`, el de la tarea NOTIFICAR del árbol) para «A notificar» y un clip (`bi-paperclip`, el de la tarjeta «Justificantes previos») para «Justificante previo». Los textos van en el tooltip. El texto de la línea 2 y la fecha usan `text-secondary` y no `text-muted`, que en el tema es demasiado claro y se leía mal sobre el fondo del selector.
- **Modo vinculados:** el nombre es el enlace y «quitar» solo existe en el borrador de una tarea. **Modo selector:** el nombre selecciona y la acción de la fila es abrir, en la caja de 120 px de la Despensa, sin una línea más.
- **Iconos de las marcas:** bandera (proyecto), capas (reformado) y estrella (prioritario), con tooltip. Pendiente que se descubra en pantalla táctil, donde no hay `hover`.
- **Texto de opción común** de los desplegables: «nombre — tipo — fecha — asunto» (lo que falta se omite, y en un `bddat://` el tipo no se repite). *Cambia respecto a lo redactado el 01/11:* se define **una sola vez**, en el servidor (`detalle_nodo.texto_opcion_documento`), y viaja en la fila como `texto_opcion`; los desplegables de React lo leen en vez de componerlo, para no tener un gemelo que mantener. Lo usa ya `esquema_editable._pool_docs` (los de la fase y el organismo). Los filtros (solo `JUSTIFICANTE_*`, solo con fecha) siguen siendo de cada editor.
- **Medida, no estimación:** las fases 3 y 4 miden la fila con el barrido de #1043 (de 320 a 960 px, de 20 en 20, en lectura y en edición) antes de darla por buena.

**Caso a caso** (de los sitios del §6.12 del pre-ADR; las filas 3, 7 y 8 son decisión de Carlos, el resto es *Interpretación*)

| # | Sitio | Después |
|---|---|---|
| 1 | Lectura del árbol, `Inspector.jsx::Documentos` (M1) | Fila común, modo vinculados; pinta el subrol |
| 2 | Cola de Mi trabajo, `_inspector_cola.html` (M2) | Macro Jinja, modo vinculados; arregla `abrir_en` y `href="None"`. #1039 la reestructura después |
| 3 | Despensa, «Documentos de esta tarea» (M3) | Se unifica con la 1: una sola lista (decisión 7) |
| 4 | Despensa, «Pool de documentos», `FichaDoc` (M4) | Fila común, modo selector |
| 5 | `BloqueJustificantesPrevios` y `EnlaceDocumento` (#929) | Fila común, modo vinculados; `EnlaceDocumento` pasa a ser la pieza «enlace» |
| 6 | Documentos únicos (`ElaborarEditor`, requisito del checklist, botones de certificado) | Usan la pieza «enlace», no la fila |
| 7 | Desplegables S1 a S5 | Se quedan `<select>` con texto común (decisión 5) |
| 8 | Edición del documento | Principio fijado, botón diferido (decisión 6) |
| 9 | `MenuContextual::ItemDoc` | Se queda; lee el mismo contrato: es un ítem de menú, no una fila |
| 10 | `seguimiento_y_huerfanos` (JS propio e `_inspector_huerfano.html`) | Se quedan; el contrato no los rompe. Los decide #1041 |
| 11 | `pool_documentos.html` | Fuera: el listado general es #881 (D6) |

**Hallazgo del «hoy», confirmado en la app el 01/11/2026:** `FichaDoc` es un `.btn` y con el tema los nombres de fichero del pool de la Despensa salen en mayúsculas (`JUSTIFICANTE_NOTIFICA.PDF`); también el botón que abre un diagnóstico en el inspector. No se corrige en #1044: lo decide la fila común al pintar el nombre.

**Fase 2 implementada (01/11/2026).** El contrato queda en `detalle_nodo.documento_fila` (id, nombre, tipo_doc, tipo_doc_codigo, `fecha` en ISO, asunto, marcas, texto_opcion, apertura y, si se piden, rol y subrol) y lo sirven el detalle de un nodo, `/api/expedientes/<id>/pool`, la respuesta de la subida, la NOTIFICAR (`documento_producido`, `justificantes_previos`, `fechas.*.documento`, el anuncio del edicto), el radar de huérfanos y el documento del checklist. Se retiró `pool_documentos_json`. Los consumidores de la fecha (inspector, Despensa, justificantes previos, anuncio del edicto y la Cola) leen ahora la ISO y la pintan dd/mm/aaaa; ninguna fila cambia de forma hasta las fases 3 y 4. Las listas con documentos cargan los backrefs de las marcas con `opciones_fila_documento()` para no pagar dos consultas por documento.

**Fase 3 implementada (01/11/2026).** El renderizador Jinja es el macro `macros/documento_fila.html`, con las dos piezas: `enlace_documento(d)` (el nombre como lo que abre el documento) y `fila_documento(d)` (las dos líneas apiladas). Las clases `.fila-doc*` están en `v2-components.css` y las compartirá el componente React de la fase 4. La Cola (`_inspector_cola.html`) es su primer consumidor: pinta el subrol (con iconos desde la enmienda del 01/11, ver arriba), abre un diagnóstico o un certificado en el modal grande en vez de seguir su fragmento en otra pestaña y ya no puede pintar `href="None"`. Es el único inspector Jinja que lista documentos: el del huérfano enseña un solo documento y se queda para #1041 y #1046. *Confirmado por Carlos:* el botón que abre el modal se pinta como un enlace y no como un `.btn`, para que el nombre del fichero no salga en mayúsculas según cómo se abra (el diagnóstico del árbol sale hoy en mayúsculas por eso). Comprobado en el navegador, dentro del inspector real, a 320 y 560 px.

**Fase 4 implementada (01/11/2026), con la mitad de #1036 que le toca a la Despensa.** El componente React es `components/FilaDocumento.jsx`, con la fila (modos *vinculados* y *selector*) y la pieza `EnlaceDocumento`, y lleva las mismas clases `.fila-doc*` que el macro Jinja. Qué cambia en el inspector del árbol:

- **Una sola lista de vinculados** (decisión 7): la lista «Documentos» de la zona de datos. En una tarea en edición con Despensa y sin sellar sale del borrador (`documentosBorrador.js`) y cada fila lleva «Quitar vínculo»; la Despensa ya no repite «Documentos de esta tarea». En lectura y en los nodos sin Despensa es la lista del detalle, sin acciones.
- **El pool de la Despensa** es la fila en modo selector, con la acción de abrir como icono; las filas que ya están vinculadas llevan el icono del rol del borrador. `FichaDoc` y `AccionesApertura` desaparecen.
- **Las subidas** (`subirDocumentoDespensa` y `subirAnclaSolicitud`) meten en el pool la fila que devuelve el servidor, completa y con apertura, y arriba, que es donde la pone el servidor; ya no se fabrica un recorte.
- **Los desplegables** del justificante final de NOTIFICAR, del requisito del checklist y del escrito de solicitud leen `texto_opcion`. **Los justificantes previos** son filas comunes y el anuncio del edicto, el documento que acredita cada fecha de NOTIFICAR y el documento casado de un requisito usan la pieza «enlace» (el `EnlaceDocumento` de `notificar/` se retira).
- **Subida desde la Despensa: la mitad de #1036** (decidida por Carlos el 01/11/2026). `GET /api/tipos-documento` trae por tipo `fecha_obligatoria` y `ayuda_fecha`, que salen de `fechas.TIPOS_FECHA_OBLIGATORIA` y `mensaje_fecha_obligatoria`, la misma lista que valida el servidor al guardar. El formulario de `SubidaInline`, cuando el tipo exige fecha, marca el campo con asterisco, enseña la ayuda del tipo (qué fecha es) y desactiva «Subir y vincular» hasta que la haya; el 422 del servidor sigue siendo la guarda. Al elegir fichero y ese tipo, pide `parsear_justificante` con el código del tipo y pone la `fecha_sugerida` que devuelva el servidor (hoy, solo para los dos justificantes de Notifica; para el resto, nada): nunca pisa lo que el usuario haya tecleado, nunca bloquea y siempre es editable. *Confirmado por Carlos:* el autorrelleno solo se pide en los tipos que exigen fecha, para no parsear cualquier fichero que se suba. La mitad del pool (`pool_documentos.html`, que sigue leyendo `fecha_puesta_disposicion`) queda para #881.
- *Confirmado por Carlos:* en el selector el icono del rol sustituye al borde verde de «vinculado»; el modo selector no es un `.btn`, así que el nombre del fichero deja de salir en mayúsculas en la Despensa; el documento recién subido entra arriba del pool y no abajo.
- **Decidido por Carlos (01/11/2026): los justificantes previos de una NOTIFICAR se quedan en su tarjeta y también en la lista «Documentos»** (con el icono del clip). Si en el futuro molesta, se quitan de la lista «Documentos»; la tarjeta se queda.
- **No comprobado en pantalla:** el desplegable del requisito del checklist y el documento casado (las tareas ANALIZAR de la semilla traen su diagnóstico producido y no muestran el checklist), la tarjeta de justificantes previos y el anuncio del edicto (la semilla no tiene casos) y el desplegable del escrito de solicitud.

**Fase 5 implementada (01/11/2026): la documentación.** `GUIA_REACT_ISLAS.md` §«Los documentos en el inspector» (el componente, el borrador de vinculados y las reglas), `GUIA_COMPONENTES_INTERACTIVOS.md` §«Fila de documento» (el macro Jinja y el contrato de la fila) y `REGLAS_DESARROLLO.md` §«Documentos» (no se añaden serializadores ni pintados de documento nuevos). Con ella quedan hechas las cinco fases de #1044; el anexo recoge las decisiones de Carlos y, como *Interpretación*, lo que salió al implementar.

### F — Listados: scroll infinito salvo excepciones (D5, D8, D16)

- **La norma:** el listado normal es el de scroll infinito con inspector (reglas E1 a E4 del pre-ADR, §3: `lista_v2_base` con `ScrollInfinito` en modo selección y marco visual común; la fila abre el inspector con `?sel=`; el cuerpo son fragmentos Jinja de lectura y de edición; las rutas GET de detalle y edición redirigen a `?sel=`). Los que hoy se desvían se tratan en **un issue** (#1041) y se decide **uno a uno** si adoptan el estándar —incluida una base de listado con varias listas por página— y, si no, el motivo. Delegación Territorial es la única de las cinco que no usa scroll infinito.
- **El pool** pasa a listado estándar con inspector, con las acciones desde el inspector (#881). El issue se queda como está, sin reformarlo ahora, con una mención a este ADR. Implementado el 01/11/2026: ver el [anexo a §F](#anexo-a-f--el-pool-881).
- **La cola de Mi trabajo** pasa a listado de scroll infinito, en Jinja por simplicidad, y su inspector, que ya es Jinja (`_inspector_cola.html`), se adapta al marco (#1039). Enmienda ADR-017, «Cómo implementar», punto 4: ya no es la isla `<Cola>`. *Interpretación:* lo que quede de la isla `mi-trabajo` (`SubirDocumento` y las dos pestañas de la viewbar) se resuelve al profundizar #1039.
- **Dos listados en una pantalla: pestañas** (`nav-tabs` de Bootstrap), como Seguimiento y huérfanos, Tablas maestras y Normas y variables (decisión de Carlos, 2026-11-05). Un botón es una acción, no una alternancia entre listados. Consecuencias: la viewbar de Mi trabajo, que hoy alterna la cola y «Subir documento» con un `btn-group` de botones (`aria-pressed`), se alinea al resolver #1039; y el hub de Plantillas y Fragmentos (#1009) nace con pestañas y, como las demás, copia el marco de `lista_v2_base` (que asume una sola lista) hasta que #1041 entregue la base de varias listas.

#### Anexo a §F — el pool (#881)

Implementación de #881 (01/11/2026), con Carlos. Va como **decisión** lo que fijó él y como *Interpretación* lo que salió al implementarlo, hasta que lo confirme o lo fije otro issue.

**Decidido por Carlos**

1. **Todo uso bloquea el borrado.** Un documento al que apunta cualquier otra fila del sistema no se borra.
2. **`_documento_es_referenciado` pasa a ser `bool(usos_documento(doc))`**, y la lista de usos se completa con las siete FK hacia `documentos` que no estaban: eran dieciséis y la guarda miraba nueve.
3. **La edición masiva se mantiene**, sobre el modo de casillas del estándar (#612), que se generaliza con la opción `bulkParams` en lugar de dejarlo atado al filtro «sin asignar» de los expedientes.
4. **El radar de huérfanos marca los documentos con destino declarado, no los excluye.** Huérfano sigue siendo «sin vínculo a tarea» (ADR-027 §2).
5. **Se parte #1036:** la mitad del pool se arregla dentro de #881 y #1036 se cierra con ella (la de la Despensa se hizo en #1044).
6. **El botón «Editar» en las filas del árbol de React no forma parte de #881.** Se decide al final del hilo: es lo que más preocupa a Carlos por la fluidez de trabajo.

**Interpretación** (la fijó la implementación, sin confirmar por Carlos)

- **El listado.** `GET /api/expedientes/<id>/documentos` (cursor por `id` descendente, `search`, `ext`, `tipo`, `prioridad`; `total` siempre) y la página `pool_documentos.html` sobre `lista_v2_base`: columnas Documento, Asunto, Tipo, Fecha adm., Ext. y **Usos** (el número y, en el tooltip, cuáles). El nombre y la extensión se calculan en SQL con la regla de `nombre_visible()`, que queda duplicada a propósito (filtrar en Python obligaba a traer todo el pool). Es otro contrato que `GET /api/expedientes/<id>/pool`, que se queda para la Despensa y los editores del árbol.
- **Los usos** son un registro único (`services/usos_documento.py`) con una entrada por FK y un chequeo que al arrancar avisa si el modelo y el registro se desajustan (`app/checks/usos_documento.py`, mismo patrón que #587); el certificado que cita un documento por su id, que no es FK, se suma aparte. Se cargan por lotes: con 42 documentos, de 143 consultas a 31.
- **El nombre del documento es el enlace** (abre el fichero) y el clic en él no abre el inspector. Es el tercer pintado de la pieza «enlace» de §E —junto al macro Jinja y `FilaDocumento.jsx`—, hecho en el JS de la fila del `ScrollInfinito`, que pinta cada fila desde el cliente. Lo mismo las marcas. `REGLAS_DESARROLLO.md` §«Documentos» dice que no se añaden pintados de documento nuevos: *aceptado por Carlos (01/11/2026) como excepción*, porque un `ScrollInfinito` pinta sus filas en el cliente.
- **El inspector** (`_inspector_documento.html`): lectura con tarjeta de usos y las acciones «Sustituir» y «Borrar»; con usos, «Borrar» es un candado con el motivo. Edición con **un único fragmento** (`_editar_fragmento_documento.html`, `POST …/guardar`), que es el tercer modo de la fila de §E: el fragmento nace aquí y su contenedor es el inspector del pool. Cabe a 320 px sin desbordar (medido de 320 a 960 px de 20 en 20). Las dos altas (subir fichero, URL externa) y «Sustituir» siguen siendo modales: crear no es editar (§E).
- **Una sola puerta de edición.** Las reglas de editar un documento (rectificar la URL, el sello de un certificado, la fecha obligatoria, el ancla del proyecto y el corte de un reformado) viven en `_aplicar_edicion_documento`, que comparten la ruta JSON (`…/editar`, la de la edición masiva) y la del formulario. El contrato del formulario es el de #832: lo que no viaja no se toca, la casilla solo cuenta con el centinela `_form_completo` y las marcas del proyecto solo con su marcador, que va dentro de un `<fieldset>` que se deshabilita entero.
- **La mitad del pool de #1036**, en `pool_alta.js`: los tipos que exigen fecha (`TIPOS_FECHA_OBLIGATORIA`) la marcan, dicen qué fecha es y no dejan subir sin ella, y la fecha propuesta es la que devuelve `parsear_justificante` para ese tipo —la lectura para el justificante final, la puesta a disposición para el de disposición—, no siempre la puesta a disposición.
- **El radar** pinta junto al tipo una marca «con destino» con el detalle en el tooltip, cambia el borrar de ese documento por un candado con el motivo y su inspector lista los usos («Con destino declarado, aún sin tarea»). Los casos reales en la BD sintética: el documento que abre un reformado y el escrito de una solicitud.
- **Pendiente de decidir, sin código:** el botón «Editar» de las filas del árbol (ver la decisión 6 y el anexo a §E).

### G — Fuera de este ADR, y cómo se registra (D19)

- **Fuera, cada uno con su issue:** el alta (#1048; ADR si lo merece), el menú frente a hub (#1051), el código muerto (#1049) y la documentación obsoleta (#1050).
- **Registro:** `ESTADO_ADR053.md` controla qué tiene issue y qué no, qué está pendiente y en qué orden, coordinado con `ESTADO_ADR049.md` y `ESTADO_ADR050.md`, que llevan solo sus líneas de cruce.

---

## Consecuencias

- **Código:** shell (`base_app.html`, `app-shell.css`, `inspector-overlay.js`); los 17 fragmentos de edición y los 17 de lectura pierden su bloque de botones; en el árbol, `Inspector.jsx`, `App.jsx` y `store.js`; `Cola.jsx` se retira cuando #1039 la convierta. Sin cambios de BD ni migraciones.
- **Tests:** ninguno referencia el marco (`inspector-overlay`, `data-inspector-*`, `AppInspector`, `BarraEdicion`). Los smoke de fragmentos y los que llaman a los serializadores de documento se revisan uno a uno al tocar cada pieza (`tests/README.md` §3).
- **Documentación:** `REGLAS_DESARROLLO.md` (fragmentos del inspector y del modal grande), `GUIA_COMPONENTES_INTERACTIVOS.md`, `GUIA_REACT_ISLAS.md`, `NOMENCLATURA_LAYOUT.md`, ADR-014 y ADR-038 donde citen la barra o los botones del fragmento; cabeceras «Enmendado por» en ADR-023 y ADR-017.
- **Issues** (el orden, en `ESTADO_ADR053.md`):

| Decisión | Issue |
|---|---|
| §A, §B — marco y ancho mínimo | #1042 |
| §C — lectura ≈ edición | #1043 |
| §E — mini-listados | #1044 |
| §D — contrato (estudio), huérfano, registro de editores | #1045, #1046, #1047 |
| §F — listados | #1041 (las cinco páginas), #1039 (cola), #881 (pool) |
| §G — fuera del ADR | #1048 (alta), #1049, #1050, #1051 |

---

## Lo que este ADR no decide

- La forma exacta del puente del marco y de lo que declara cada fragmento (fase 1 de #1042).
- La forma de un contrato general de campos (#1045).
- ~~El contenedor de la edición del documento~~ (el principio, decidido en el [anexo a §E](#anexo-a-e--la-fila-común-de-documentos-1044); el fragmento nació en #881, [anexo a §F](#anexo-a-f--el-pool-881)) y qué más comparten los dos renderizadores (clases CSS, otros).
- El botón «Editar» de las filas de documento del árbol de React: fuera de #881, a decidir (anexo a §E, decisión 6).
- ~~El pool cargado una vez por vida de la isla, cómo se pinta `subrol`~~ (propuestos en el anexo a §E, como *Interpretación*) y si la cola conserva su cruz.
- Las decisiones por página de los cinco listados (#1041), y el destino de `SubirDocumento` y la viewbar de la isla `mi-trabajo` (#1039).
- ~~Qué bloques de lectura se quedan en edición en el árbol (fase 1 de #1043)~~: decidido, en el anexo a §C.
- Si el scroll horizontal del cuerpo se ve como señal en el navegador de la Consejería: los Chromium recientes en Windows pueden pintar barras superpuestas que se ocultan solas. Sin comprobar.
- El tamaño del modal grande (un máximo fijo y un mínimo definido por quien lo use): planes de Carlos, otro asunto.
- El sitio del botón «Exportar expediente» de #1008.

---

## Alternativas descartadas

- **Dos implementaciones del marco con un contrato visual común** (una macro Jinja y la `BarraEdicion` React): es lo más barato, pero deja dos sitios que mantener —el patrón «gemelo: si cambia uno, cambiar el otro» que ya duele— y el shell no garantizaría nada: cada fragmento seguiría pudiendo salirse (§A).
- **Cuerpo único del inspector:** todo en Jinja obligaba a reescribir unas 4.050 líneas de editores del árbol acopladas al store; todo en React, a reescribir 17 pares de fragmentos con sus APIs JSON y a montar islas dentro de fragmentos, contra ADR-015 (§D).
- **Montar islas React en fragmentos Jinja:** no existe y no hace falta con estas decisiones (§D).
- ***Container queries* para apilar según el ancho del inspector:** el ancho mínimo por caso con scroll horizontal da lo mismo con menos mecanismo (§B).
- **Una cruz en el modo vista:** no se añade; se mantienen clic exterior, `Escape` y la franja (§A).
- **Un solo módulo para el listado del pool y los mini-listados, con o sin inspector, o un módulo incrustable con columnas flexibles:** §E.
- **Un esquema declarativo de campos como contrato general:** no se descarta, se aplaza a estudio (#1045).
