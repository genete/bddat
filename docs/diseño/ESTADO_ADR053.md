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
| 0 | — | **ADR-053** redactado a partir del PRE-ADR, con cabeceras «Enmendado por» en ADR-023 (§5 bis, §6, §8 y §9) y en ADR-017 | Diseño | Redactado el 11/10/2026 como Propuesta y **Adoptada por Carlos el 13/10/2026**. Las *Interpretación* de su texto (el puente del marco, el alcance del contrato, la isla `mi-trabajo` tras #1039) siguen sin confirmar: las fija la fase 1 de #1042 o la profundización del issue que toque |
| 1 | **#1042** | **Marco del inspector** (D9–D12, §8.15): el shell pinta la barra (cabecera, Editar, Guardar/Cancelar, Cerrar) con «Cerrar» visible a cualquier ancho; el árbol la alimenta con su estado de borrador (el puente); cuerpo con scroll y ancho mínimo por caso, con scroll horizontal por debajo. Primer paso: prototipar el puente. Un solo issue en cinco fases (prototipo del puente; marco en el shell y el árbol; fragmentos Jinja; ancho mínimo y scroll horizontal; documentación) | Frontend | Abierto. **Implementado el 13/10/2026 en las cinco fases**, en la rama `claude/stoic-lamport-0ps7sn` y sin PR todavía: marco en el shell, puente del árbol, los 17 fragmentos Jinja (lectura y edición) y ancho mínimo con scroll horizontal; el contrato, en `GUIA_COMPONENTES_INTERACTIVOS.md` §«Marco único del inspector». Pendiente de Carlos: confirmar las cifras de ancho mínimo (propuesta, medidas con barras de scroll clásicas) y si el contrato se publica como comentario en #1042. Base previa: #676 y #688 (cerrados; marco del árbol) |
| 2 | **#1043** | **Inspector del árbol: lectura ≈ edición** (D15) | Frontend | Abierto (11/10/2026), en cinco fases; la fase 1 es de definición, sin código, y no ha empezado. Se mira junto al marco: toca la lectura de `Inspector.jsx` y el `Editor` genérico |
| 3 | **#1041** | **Listados fuera del estándar** (D16): un issue y decisión una a una de cinco páginas —tablas maestras, normas y variables, seguimiento y huérfanos, configuración del motor, Delegación Territorial—: adoptan el estándar (incluida una base con varias listas por página) o se justifica el motivo | Frontend | Abierto (11/10/2026); las decisiones por página, sin tomar. Independiente del marco. Absorbió #755 y #644 (cerrados); la causa raíz de #644 es su primera tarea |
| 4 | **#1039** | Cola de Mi trabajo al listado estándar Jinja (D8). Su inspector se adapta al marco | Frontend | Abierto, sin profundizar. El listado puede ir antes que el marco; el inspector, después (*propuesta*) |
| 5 | **#881** | Listado del pool al listado estándar con inspector (D5); edición del documento con un único sitio (D17) | Frontend | Abierto, **sin reescribir** (D5): cuando haya ADR se le añade una mención. Después del marco (*propuesta*) |
| 6 | **#1044** | **Mini-listados de documentos** (D6, D13, D14): fila común con tres modos (vinculados, selector, edición); macro Jinja y componente React; estudio caso a caso de los sitios de §6.12, incluido pintar `subrol` | Frontend + backend (contrato del dato) | Abierto (11/10/2026), en cinco fases; la fase 1 es de definición, sin código, y no ha empezado |
| 7 | **#1045** | **Estudio de la forma del contrato** editor ↔ poseedor del dato (D13, §8.16) | Estudio | Abierto (11/10/2026), sin profundizar. Sin urgencia; puede acabar en «no se estandariza» |
| 8 | **#1046** | **Huérfano: «Vincular aquí»** va en un `<script>` en línea dentro de un fragmento, que el overlay no ejecuta (§7.3, §8.8) | Frontend | Abierto (11/10/2026), sin profundizar. Fallo de código por lectura, sin reproducir: reproducir antes de arreglar |
| 9 | **#1047** | **Refactor del despacho de editores por tipo** en el árbol, 7 banderas (§8.11) | Frontend | Abierto (11/10/2026), sin profundizar. Mismos ficheros que #929, #1010, #1042 y #1043: cuidado con el orden |
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
- **«Cerrar» descarta sin avisar lo escrito en los bloques interiores del árbol** (ítem técnico y shuttle
  de requerimientos de ANALIZAR; registro de la notificación de NOTIFICAR): guardan por su cuenta y no
  encienden la barra del marco, que sigue diciendo «Cerrar». Carlos lo separó de #1042 el 13/10. **Sin
  issue todavía:** hay un borrador con opciones y preguntas pendiente de su visto bueno.
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
| **#1038** (representante y sede de la solicitud) | Acoplado al marco y a D15: toca el editor de la solicitud del árbol, el genérico con solo «observaciones», que hoy tiene lectura ≠ edición |
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
  avisos de «sucio», y la cruz de la Cola se queda hasta su rediseño. Salió un hueco nuevo, sin issue (arriba).
