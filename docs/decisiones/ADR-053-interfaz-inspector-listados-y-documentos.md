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

El inspector es el primer estándar para todos los casos: la isla del árbol (por ahora la única) y los fragmentos Jinja. Se monta **un marco** que estandariza ver / editar y guardar / cancelar / cerrar, y **lo pinta el shell una sola vez**. El árbol deja de pintar su barra y pasa a alimentar al shell con su estado de borrador (`hayCambios`, `guardando`, guardar, cancelar): es el «puente».

- **En vista:** cabecera y botón Editar, sin cruz. El inspector se cierra con clic exterior (no en otra fila, que cambia la selección), `Escape` o un clic en la franja de redimensionado.
- **En edición:** Guardar y Cancelar, solo habilitados con borrador vivo, y «Cerrar» siempre presente. El contrato de salida de ADR-023 §5 bis no cambia: con la superficie limpia, «Cerrar» sale sin revertir nada; con cambios sin guardar, la salida se comporta como Cancelar.
- **Visibilidad garantizada con cualquier ancho:** en edición se ve, al menos, «Cerrar». La barra del árbol ya lo consigue truncando la cabecera y no los botones; el marco del shell debe reproducirlo.
- **Qué declara cada caso:** el fragmento Jinja declara su título, la URL de su edición y su formulario; el árbol alimenta al shell con su estado. *Interpretación:* los nombres de los atributos y de la API de ese contrato, y cómo se aloja la cabecera del árbol (semáforo, tipo, título, estado, candado), los fija la fase 1 de #1042 prototipando, no este ADR. *Interpretación:* «Editar» vive en el marco, por lo que implica «ver / editar».
- **Contrato implementado en #1042** (13/10/2026; en la rama de trabajo hasta que se mergee su PR): los nombres de los atributos y de la API están en `docs/guias/GUIA_COMPONENTES_INTERACTIVOS.md`, §«Marco único del inspector». Las *Interpretación* de arriba siguen pendientes de que Carlos las confirme.

### B — Cuerpo flexible: ancho mínimo por caso y scroll horizontal (D11)

El interior se deja como lo necesite cada caso, flexible al ancho. **Cada caso define un ancho mínimo** para su visibilidad; por debajo de él, hay scroll horizontal. El usuario lo ve como señal y amplía el inspector, y cada caso no tiene que resolver el apilamiento por su cuenta.

- El scroll horizontal es **solo del cuerpo, nunca del marco**: `overflow-x: auto` en lugar de `hidden`. Por encima de su mínimo, las columnas de cada caso siguen valiendo, así que no hacen falta *container queries* (precisión técnica acordada el 11/10).
- El mínimo del marco sigue siendo el del shell (`MIN_WIDTH`, 320 px).
- Enmienda ADR-023 §8: el «mínimo de lectura», con cifra diferida a la implementación, es el de cada caso. ADR-023 §9: la «columna fluida» deja de ser la regla del interior.

### C — Lectura ≈ edición, también en el árbol (D15)

Lo que se ve antes de editar es casi lo mismo que se ve en modo edición: cambian ligeramente los componentes del formulario, para indicar que se está editando. Es el criterio de Carlos en todos los formularios, y busca coherencia visual. Los fragmentos Jinja ya lo cumplen; el inspector del árbol no, y se lleva a #1043. Qué bloques de lectura se quedan en edición y cuáles solo existen en ella se define en la fase 1 de ese issue.

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

### F — Listados: scroll infinito salvo excepciones (D5, D8, D16)

- **La norma:** el listado normal es el de scroll infinito con inspector (reglas E1 a E4 del pre-ADR, §3: `lista_v2_base` con `ScrollInfinito` en modo selección y marco visual común; la fila abre el inspector con `?sel=`; el cuerpo son fragmentos Jinja de lectura y de edición; las rutas GET de detalle y edición redirigen a `?sel=`). Los que hoy se desvían se tratan en **un issue** (#1041) y se decide **uno a uno** si adoptan el estándar —incluida una base de listado con varias listas por página— y, si no, el motivo. Delegación Territorial es la única de las cinco que no usa scroll infinito.
- **El pool** pasa a listado estándar con inspector, con las acciones desde el inspector (#881). El issue se queda como está, sin reformarlo ahora, con una mención a este ADR.
- **La cola de Mi trabajo** pasa a listado de scroll infinito, en Jinja por simplicidad, y su inspector, que ya es Jinja (`_inspector_cola.html`), se adapta al marco (#1039). Enmienda ADR-017, «Cómo implementar», punto 4: ya no es la isla `<Cola>`. *Interpretación:* lo que quede de la isla `mi-trabajo` (`SubirDocumento` y las dos pestañas de la viewbar) se resuelve al profundizar #1039.

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
- El contenedor de la edición del documento y qué más comparten los dos renderizadores (clases CSS, otros).
- El pool cargado una vez por vida de la isla, cómo se pinta `subrol` y si la cola conserva su cruz.
- Las decisiones por página de los cinco listados (#1041), y el destino de `SubirDocumento` y la viewbar de la isla `mi-trabajo` (#1039).
- Qué bloques de lectura se quedan en edición en el árbol (fase 1 de #1043).
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
