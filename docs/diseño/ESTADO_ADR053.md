# Estado de la cadena de issues — ADR-053 (interfaz)

> Registro vivo. Las decisiones de diseño están en
> [`ADR-053`](../decisiones/ADR-053-interfaz-inspector-listados-y-documentos.md) (adoptada el 13/10/2026; redactada como propuesta el 11/10),
> redactado a partir del [`PRE-ADR`](PRE-ADR-interfaz-vistas-y-documentos.md) (§2, D1–D19), que queda
> congelado. Aquí solo se lleva la cuenta de
> qué tiene issue y qué no, qué está pendiente y en qué orden, para no perder el hilo entre sesiones. Se
> actualiza a mano, sin issue ni rama propios (documento de diseño vivo), cada vez que se crea o cierra un
> issue de la cadena. Mismo formato que [`ESTADO_ADR049.md`](ESTADO_ADR049.md) y
> [`ESTADO_ADR050.md`](ESTADO_ADR050.md), con los que se coordina (D19).
>
> **El orden de la tabla es una propuesta, sin confirmar.** D19 fija que este documento lo controla; no
> cuál es. Los issues por abrir se abren con Carlos, de uno en uno; al abrir cada uno hay que buscar los
> existentes, abiertos y cerrados (`REGLAS_DESARROLLO.md` §Issues y pull requests).

---

## Origen

La revisión de #929 contra el código (09/10/2026) destapó que el tratamiento de documentos está repartido
y que el inspector y los listados no siguen un estándar único. El PRE-ADR inventarió las vistas, el inspector
y los documentos; el 11/10/2026 Carlos fijó las posiciones (D5–D19). Alcance (PRE-ADR §8.14): el inspector (marco
y contrato), los listados estándar y los documentos en listados e inspectores. Fuera: el alta, el menú frente
al hub, el código muerto y la documentación obsoleta.

## Piezas, en orden (propuesta)

| Orden | Issue | Qué es | Capa | Estado (11/10/2026) |
|---|---|---|---|---|
| 0 | — | **ADR-053** redactado a partir del PRE-ADR, con cabeceras «Enmendado por» en ADR-023 (§5 bis, §6, §8 y §9) y en ADR-017 | Diseño | Redactado el 11/10/2026 como Propuesta y **Adoptada por Carlos el 13/10/2026**. Las *Interpretación* de su texto (el puente del marco, el alcance del contrato, la isla `mi-trabajo` tras #1039) siguen sin confirmar por Carlos: las fijó la implementación de #1042 (el contrato está en la guía) salvo la de la isla `mi-trabajo`, que espera a #1039 |
| 1 | **#1042** | **Marco del inspector** (D9–D12, §8.15): el shell pinta la barra (cabecera, Editar, Guardar/Cancelar, Cerrar) con «Cerrar» visible a cualquier ancho; el árbol la alimenta con su estado de borrador (el puente); cuerpo con scroll y ancho mínimo por caso, con scroll horizontal por debajo. Primer paso: prototipar el puente. Un solo issue en cinco fases (prototipo del puente; marco en el shell y el árbol; fragmentos Jinja; ancho mínimo y scroll horizontal; documentación) | Frontend | **Hecho** el 13/10/2026, en las cinco fases y en un único PR (**#1056**, mergeado; issue cerrado): marco en el shell, puente del árbol, los 17 fragmentos Jinja (lectura y edición) y ancho mínimo con scroll horizontal; el contrato, en `GUIA_COMPONENTES_INTERACTIVOS.md` §«Marco único del inspector» y publicado como comentario en #1042. Cifras de ancho mínimo (medidas con barras de scroll clásicas) **confirmadas por Carlos**; no están medidas con barras superpuestas. Base previa: #676 y #688 (cerrados; marco del árbol) |
| 2 | **#1043** | **Inspector del árbol: lectura ≈ edición** (D15) | Frontend | **Hecho** el 18/10/2026 (PR #1061, mergeado por Carlos; issue cerrado), en cinco fases. Era la siguiente pieza, confirmada por Carlos el 13/10/2026. **Los nodos y las superficies de trabajo están migrados** (expediente, solicitud, versión, fase, organismo, trámite, tarea genérica, ANALIZAR simple y extendido, ELABORAR y NOTIFICAR) y la tabla definitiva está en el anexo a ADR-053 §C: las cinco fases hechas: layout medido en cada nodo a 320 px sin desborde y patrón documentado en `GUIA_REACT_ISLAS.md`. Los hallazgos, en issues aparte (#1058 a #1060 y #1062 a #1071; dos, comentados en #1044). Falta, sin comprobar, el scroll horizontal con barras superpuestas (#1070) |
| 3 | **#1041** | **Listados fuera del estándar** (D16): un issue y decisión una a una de cinco páginas —tablas maestras, normas y variables, seguimiento y huérfanos, configuración del motor, Delegación Territorial—: adoptan el estándar (incluida una base con varias listas por página) o se justifica el motivo | Frontend | Abierto (11/10/2026); las decisiones por página, sin tomar. Independiente del marco. Absorbió #755 y #644 (cerrados); la causa raíz de #644 es su primera tarea |
| 4 | **#1039** | Cola de Mi trabajo al listado estándar Jinja (D8). Su inspector se adapta al marco | Frontend | Abierto, sin profundizar. El listado puede ir antes que el marco; el inspector, después (*propuesta*) |
| 5 | **#881** | Listado del pool al listado estándar con inspector (D5); edición del documento con un único sitio (D17) | Frontend | Abierto, **sin reescribir** (D5): cuando haya ADR se le añade una mención. Después del marco (*propuesta*) |
| 6 | **#1044** | **Mini-listados de documentos** (D6, D13, D14): fila común con tres modos (vinculados, selector, edición); macro Jinja y componente React; estudio caso a caso de los sitios de §6.12, incluido pintar `subrol` | Frontend + backend (contrato del dato) | Abierto (11/10/2026), en cinco fases; la fase 1 es de definición, sin código, y no ha empezado |
| 7 | **#1045** | **Estudio de la forma del contrato** editor ↔ poseedor del dato (D13, §8.16) | Estudio | Abierto (11/10/2026), sin profundizar. Sin urgencia; puede acabar en «no se estandariza» |
| 8 | **#1046** | **Huérfano: «Vincular aquí»** va en un `<script>` en línea dentro de un fragmento, que el overlay no ejecuta (§7.3, §8.8) | Frontend | Abierto (11/10/2026), sin profundizar. Fallo de código por lectura, sin reproducir: reproducir antes de arreglar |
| 9 | **#1047** | **Refactor del despacho de editores por tipo** en el árbol, 7 banderas (§8.11) | Frontend | **Implementado** el 18/10/2026 (rama de trabajo, sin PR): registro de editores en `registroEditores.jsx`, ocho pasos, sin diferencias contra la base de comparación. Ver la entrada del 18/10 del historial |
| 10 | **#1048** | **El alta** (§8.6): issue propio y, si al estudiarlo lo merece, ADR | Frontend | Abierto (11/10/2026), sin profundizar. #793 (modales de alta con recarga) se mantiene abierto, condicionado a lo que se decida |

Orden propuesto por dependencias, no por prioridad: 1 antes de 4 (inspector), 5 y 2 porque los tres usan
el inspector; 3 es independiente de todos; 6 define la fila antes que sus renderizadores y se cruza con 4 y 5.

## Fuera del ADR (§8.9, §8.12, §8.13)

Tienen issue propio, los tres abiertos el 11/10/2026 y sin profundizar:

- **#1049** — código muerto y rutas sin consumidor (con `generar_cert` y `demo.diagrama` como decisiones aparte).
- **#1050** — documentos de la revisión de interfaz de mayo (`AUDITORIA_UI.md` y compañía) y dónde vive el mapa
  vivo de vistas.
- **#1051** — menú frente a hub.

## Sin issue a propósito

- **Tamaño del modal grande** (máximo fijo y mínimo definido por quien lo use): planes de Carlos, otro asunto
  (§8.7).

## Huecos por definir

- ~~**El puente del marco con el estado del árbol** (`hayCambios`, `guardando`, `guardar`)~~ — resuelto el
  13/10 en #1042: el hook `usePuenteInspector` empuja un descriptor al shell con `AppInspector.setFrame`.
- ~~**«Cerrar» descarta sin avisar lo escrito en los bloques interiores del árbol**~~ — implementado el 18/10
  en #1055 (rama de trabajo, sin PR): opción A, un canal «interior sucio» hacia el marco
  (`useInteriorSucio`); ver la entrada del 18/10 más abajo.
- **Dónde se aloja la edición del documento:** el inspector del pool o, desde otros sitios, el modal grande.
  Depende del marco y de que el formulario de edición del pool quepa en el inspector (§8.10, PRE-ADR §10).
- ~~**#755 frente al issue de D16**~~ — resuelto el 11/10: #1041 absorbió #755 y #644 (los dos cerrados), y
  #281 (Plantillas y Usuarios a listado V2, con la premisa desfasada) se cerró como hecho.

## Relación con ESTADO_ADR049 y ESTADO_ADR050 `[VERIFICADO]` salvo lo marcado *propuesta*

### Con la cadena de ADR-049

| Pieza | Cruce |
|---|---|
| **#929, zona A** | Independiente del marco. La decisión 1 (atajo de subida por tipo en el editor) se resolvió en «no» (PRE-ADR D1); `ESTADO_ADR049` lo tenía como «sin tomar» y se corrige el 11/10 |
| **#1036** (fecha en la subida) | Vive en `pool_documentos.html`, que #881 reescribe. Decidir si se arregla antes o dentro de #881. Con la decisión 1 en «no», no aplica la regla de fecha por tipo en el editor |
| **#1037** (aplicar el anuncio del edicto) | Sin choque con el marco. Es una acción nueva sobre documentos: no debe crear un selector propio (D14) |
| **#1038** (representante y sede de la solicitud) | **Hecho** (PR #1081, 23/10/2026). Tocaba el editor de la solicitud del árbol: la tarjeta «Solicitante» lee y edita representante y sede con el mismo texto (D15). El contrato del select quedó en la guía y solo lo cumple `ControlCampo` (#1080 alinea el resto) |
| **Zona E de #929** (sin issue) | Tres de sus ocho puntos tocan lo decidido o lo pendiente: inspector en lectura (D15), Mi trabajo (D8) y radar de huérfanos (fila provisional de Seguimiento y huérfanos). *Propuesta:* no abrirla antes del marco ni de la Cola |

### Con la cadena de ADR-050

| Pieza | Cruce |
|---|---|
| **#1012** (papelera, fase 7) | «Sigue en los listados, marcado; acción “sacar de la papelera”»: consume el listado del pool (D5) y la guarda `_documento_es_referenciado`, que #881 quiere convertir en lista de usos. *Propuesta:* #881 antes o junto a #1012 |
| **#1008** (fase 2b) | El sitio del botón «Exportar expediente» no está fijado: cae en el pool o en el inspector del expediente, ambos afectados por D5 y el marco. La señal junto a la bombilla de `base_app.html` es del shell, fuera del inspector: sin choque |
| **#1033** (aportar desde otro expediente, aparcado) | Su «listado plano de documentos de todos los expedientes» es el modo «selector» de D14 en un listado estándar. Cuando se retome, sobre el estándar y la fila común |
| **#1009** (fase 4) | Retira el explorador de plantillas y sube plantillas desde el navegador: toca el inspector de Plantillas, hoy parcial frente al estándar. Alinear con el marco |
| **#1010** (fase 5) | Botón «Editar» (WebDAV) en `ElaborarEditor`, el mismo editor que toca #929. El rótulo «Editar» convive con el del inspector: a vigilar en el texto, no en el código |
| «Orden de las fases 4–7: sin decidir» | Gana una restricción *(propuesta)*: #1012 después de #881 |

## Historial de esta tabla

- **11/10/2026** — Creada tras el hilo de posiciones del PRE-ADR de interfaz (D5–D19, con Carlos). Al
  comprobar el estado real para abrir el issue de listados salieron tres cosas que cambian el planteamiento:
  las cuatro páginas multi-lista **ya usan `ScrollInfinito`** (lo que copian a mano es el marco, y por eso
  les falta «volver arriba»: #755); la única sin scroll infinito es Delegación Territorial, que lo declara;
  y #676 y #688, que implementaron el marco de ADR-023 §5 bis, lo hicieron solo para los nodos del árbol,
  así que los 17 fragmentos Jinja nunca lo tuvieron. Corregida en `ESTADO_ADR049` la decisión 1 de #929.
- **11/10/2026** — Creado **#1041** (listados fuera del estándar, D16) y cerrado #755 como absorbido, con
  Carlos. Al buscar issues existentes salieron #644 (misma causa raíz, componentes de instancia única: sigue
  abierto y es la primera tarea de #1041), #647 (aspecto de las pestañas) y #281 (premisa desfasada).
- **11/10/2026** — Cerrados, con Carlos, #644 (absorbido por #1041) y #281 (hecho). Creado **#1042** (marco
  del inspector): un solo issue en cinco fases, con el análisis de impacto previo en el cuerpo (consumidores
  de shell, fragmentos Jinja, React, tests, scripts y documentación; ningún test referencia el marco).
- **11/10/2026** — Creado **#1043** (lectura ≈ edición en el inspector del árbol, D15): cinco fases, la
  primera de definición sin código, con el análisis de impacto previo en el cuerpo. Al levantarlo salió que
  la edición hace desaparecer los campos de solo lectura, los plazos, los documentos y los organismos, y
  que lectura y edición salen de dos serializadores distintos para el mismo nodo.
- **11/10/2026** — Creados con Carlos los demás issues de la cadena: **#1044** (mini-listados, en cinco fases
  con definición primero, el único redactado con detalle) y, sin profundizar, **#1045** (estudio del
  contrato), **#1046** («Vincular aquí» del huérfano), **#1047** (registro de editores del árbol), **#1048**
  (el alta), y los tres de fuera del ADR: **#1049** (código muerto), **#1050** (documentación obsoleta) y
  **#1051** (menú frente a hub). Antes se buscaron los existentes: ninguno decía lo mismo; relacionados #685,
  #915, #213, #958, #351, #793, #577, #275, #579, #709 y, en #1041, #1031.
- **11/10/2026** — Redactado **ADR-053** como *Propuesta* (pieza 0) y congelado el PRE-ADR. Cabeceras
  «Enmendado por» en ADR-023 y en ADR-017. Sin cambios en los issues ni en su orden. Las interpretaciones
  del ADR (el puente del marco, el alcance del contrato, qué hace la isla `mi-trabajo` tras #1039) van
  marcadas *Interpretación* en su texto, y falta que Carlos las confirme.
- **13/10/2026** — **ADR-053 pasa a Adoptada** (Carlos). Se actualizan sus punteros en las cabeceras de ADR-017 y ADR-023 y en `docs/README.md`; el PRE-ADR, congelado, no se toca. Las *Interpretación* no cambian de estado con la adopción. Carlos confirma que #1042 (marco del inspector) es lo que toca ahora; el resto del orden de la tabla sigue siendo una propuesta.
- **13/10/2026** — **#1042 implementado** en sus cinco fases (rama de trabajo, sin PR): el shell pinta la
  barra del marco (cabecera, Editar, Guardar, Cancelar/Cerrar, sin icono junto al verbo); el árbol la
  alimenta con el puente; los 17 fragmentos Jinja pasan a declarar su marco con atributos `data-*` y pierden
  sus botones; el cuerpo hace scroll horizontal por debajo del mínimo de cada caso. Decisiones de Carlos en el
  camino: «Guardar» solo con borrador vivo, el interior se respeta como está y el marco solo responde a sus
  avisos de «sucio», y la cruz de la Cola se queda hasta su rediseño. Salió un hueco nuevo, ahora con issue (#1055, arriba). Carlos confirma las cifras de ancho mínimo; el contrato se publica en #1042 y todo va en un único PR de cierre.
- **13/10/2026** — **#1042 cerrado**: PR #1056 mergeado por Carlos y rama remota borrada. `CONTEXTO_ACTUAL.md`
  pasa su «Hecho» a #1042. Quedan abiertos, de esta cadena: #1055 (nuevo, «Cerrar» sin aviso en los bloques
  interiores del árbol, sin empezar) y el resto de la tabla (#1043, #1041, #1039, #881 y #1044 a #1048). No medido: el scroll horizontal
  con barras superpuestas (el navegador de la Consejería). La clase `min-w-0`, usada en `_panel_tokens.html`, no
  existe en ninguna hoja: sin efecto visible hoy, sin issue (decisión pendiente de Carlos).
- **13/10/2026** — Carlos confirma **#1043** como siguiente pieza de la cadena; `CONTEXTO_ACTUAL.md` lo recoge
  en su «Próximo». El resto del orden de la tabla sigue siendo una propuesta. #1055 (mismos ficheros que #1043)
  queda con sus dudas abiertas en el propio issue.
- **18/10/2026** — **#1043, fases 1 a 3 hechas** (rama de trabajo, sin PR). Se migran, con Carlos y nodo a
  nodo, el trámite, la tarea genérica, las dos variantes de ANALIZAR, ELABORAR y NOTIFICAR; con ellas se
  retiran el `Editor` genérico y la rama heredada de `InspectorEdicion`. La tabla definitiva de lectura y
  edición se anota como **anexo a ADR-053 §C**. Decisiones de Carlos en el camino: «genérica» se decide por
  (tipo de tarea, trámite) y no por el tipo solo; los bloques que guardan por su cuenta siguen así (los
  controles del destinatario de ELABORAR y de NOTIFICAR, que guardan con un `PUT` inmediato, se anotan en
  #1055, que Carlos cuestiona); las listas de documentos repetidas se quedan hasta #1044. Se añade al
  árbol el dato `analisis_extendido` (única fuente de la variante de ANALIZAR). Después, la fase 5
  (patrón documentado en `GUIA_REACT_ISLAS.md`), los issues de hallazgos y el PR de cierre.
- **18/10/2026** — **#1043 cerrado**: PR #1061 mergeado por Carlos. Hallazgos abiertos como issues
  (#1058 a #1060 y #1062 a #1071; los de documentos, comentados en #1044; la variable huérfana de
  `catalogo_variables` ya era #879). `CONTEXTO_ACTUAL.md` pasa su «Hecho» a #1043. Con Carlos se ordena el
  resto **por bloques según lo que desbloquea cada pieza** y no cadena a cadena *(propuesta, a decidir
  paso a paso)*: 1) cerrar el árbol (#1055, #1047); 2) notificaciones libres (#1038, #1037); 3) documentos
  y pool (#1044, #881 con #1036, y de ADR-050 #1012, #1008 y #1009); 4) Cola y listados (#1039, #1041 y
  la zona E de #929). Sin bloque: #1045, #1046, #1048. Lo que #1043 deja desbloqueado: #1038 (la tarjeta
  «Solicitante» está preparada) y #1037.
- **18/10/2026** — **#1055 implementado** (rama de trabajo, sin PR). Carlos delega las dudas del issue en la
  implementación (*interpretación*: lo decidido queda pendiente de su confirmación): **opción A** (los
  bloques avisan al marco; la barra dice «Cancelar» sin encender «Guardar»); «Cancelar» descarta directo con
  el toast de siempre; sin «Descartar» propio en cada bloque; el destinatario de ELABORAR y de NOTIFICAR
  **sigue guardando con el `PUT` inmediato** (el generador de escritos lo necesita guardado dentro de la misma
  edición) y solo cuenta como «sin guardar» la entidad elegida y sin confirmar. Hueco añadido: el «Guardar» de
  la barra con interior sucio pide decisión (guardar sale a lectura y tiraría ese texto) y el cierre de la
  pestaña también avisa. Cubre ítem técnico, requerimientos (lista y texto libre y edición en curso), registro
  de la notificación y los dos destinatarios. Comprobado en el navegador con la BD sintética: requerimientos,
  registro, `beforeunload` y el aviso del «Guardar»; el destinatario de ELABORAR, con la respuesta del servidor
  simulada. **No comprobado**: el ítem técnico (la semilla no trae ítems técnicos) y el destinatario de
  NOTIFICAR (la semilla no tiene un caso con selector).
- **18/10/2026** — **#1047 implementado** (rama de trabajo, sin PR). El despacho de editores por tipo pasa de
  banderas a un **registro** (`expediente-arbol/registroEditores.jsx`): cada tipo de nodo y cada superficie de
  tarea declara sus tarjetas, acciones, modales, Despensa y si se borra, y `InspectorEdicion` y `ZonaDatos` solo
  ejecutan la entrada. Decisiones de Carlos: el registro vive en un fichero nuevo (`superficiesTarea.js` se queda
  como la parte de las tareas), ADR-053 no se toca, los hooks van en un único `useHechosDelNodo` (las entradas son
  puras) y la migración se hace tipo a tipo, con el camino viejo y el nuevo conviviendo hasta terminar. Se hizo en
  ocho pasos, cada uno comparado con una base capturada **sobre el código original**: 29 nodos en lectura y edición,
  23 escenarios de interacción sin guardado y 7 que guardan (elegir y cambiar destinatario, enviar consultas,
  producir el diagnóstico), sin una diferencia. Para tener esos casos se crearon datos sintéticos en la BD de la
  nube (ítem técnico, segunda entidad publicadora, fases de Información pública y de consultas en el expediente 5,
  y el expediente de resolución «sin notificar»): con ellos quedan comprobados en pantalla los tres casos que #1055
  dejó sin comprobar (ítem técnico, y destinatario con selector de NOTIFICAR y de ELABORAR). *Interpretación*,
  pendiente de confirmar por Carlos: las acciones de la solicitud y la fase salieron de `Inspector.jsx` a
  `components/AccionesNodo.jsx` para evitar un ciclo de imports, y `visible` pasó a `hay` (la zona de acciones se
  pinta si alguna tiene algo que enseñar y entonces van todas, que es lo que hacía el código anterior). El patrón,
  en [`GUIA_REACT_ISLAS.md`](../guias/GUIA_REACT_ISLAS.md) §«El registro de editores del árbol».
- **23/10/2026** — **#1038 cerrado** (PR #1081): la solicitud del árbol muestra y edita representante y sede, con
  el mismo texto en lectura y en edición (D15). `ControlCampo` gana el **contrato de un selector** (el texto del
  vacío dice qué implica no elegir; «!» con el motivo si el valor guardado no es una opción, también en lectura;
  elegir «nada» de nuevo sin perder el foco) y `shared/ui/toast.js` gana `showAvisos` (un toast resumen y cada
  aviso como línea del panel Avisos). Se aplica a todos los select del esquema: con los datos de la nube ninguno
  de fase, organismo ni solicitud tiene hoy el valor fuera de sus opciones, pero un organismo de vía «declaración
  responsable» sí lo tendría (`exonerado`, #1065). Decisión de Carlos: crear solicitud no lleva campos. El
  contrato, en [`GUIA_COMPONENTES_INTERACTIVOS.md`](../guias/GUIA_COMPONENTES_INTERACTIVOS.md) §«Contrato de un
  selector»; alinear el resto de selectores es **#1080**. Medido: dentro de un `input-group` de Bootstrap el tema
  pinta el campo más alto y con más letra que el suelto, así que la marca va superpuesta en el propio control.
