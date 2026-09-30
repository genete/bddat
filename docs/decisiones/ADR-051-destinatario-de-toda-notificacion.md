# ADR-051 — Toda notificación tiene destinatario: fuentes por fase y trámite, poblado idempotente y dirección congelada

**Estado:** Adoptada — implementada en parte. La implementa **N5** (notificación multi-destinatario), partido en #967, #968 y #969 (`docs/diseño/ESTADO_ADR049.md`). **§B y §K, en #967 (N5a-1):** migración `967_destinatario_notificacion`; la fila con su fuente nace en `mutaciones_arbol.crear_tarea`, con las fuentes de cada trámite en una lista provisional en código (`notificaciones.FUENTES_POR_TRAMITE`) hasta la tabla `notificacion_fuentes` de #968; el destinatario se fija a mano con `mutaciones_arbol.fijar_destinatario` (`PUT …/notificar/destinatario`, sin interfaz hasta #929); el escape queda en bitácora con `accion: NOTIFICAR_SIN_DESTINATARIO`. **§C, §D, §E, §H, §L y §M, en #968 (N5a-2):** migración `968_fuentes_destinatarios` (catálogo `notificacion_fuentes`, que sustituye a `FUENTES_POR_TRAMITE`; `tramites_destinatario`; copia congelada del representado en `notificaciones`, `dest_en_nombre_de_*`); servicio `services/destinatarios_notificacion.py` («¿a quién falta notificar?» y sobrantes, calculado por solicitud y guardado solo hasta la siguiente escritura de la sesión); escribir es de `mutaciones_arbol` (`crear_tarea` rellena al crear, `fijar_destinatario` solo admite a quien corresponde por la fuente, `registrar_destinatario_tramite`, `anadir_notificaciones_que_faltan`; rutas `GET …/tramite/<id>/notificaciones` y `POST …/notificaciones/anadir_faltan`, sin interfaz hasta #929); invariante en `Tramite.finalizado`, rojo propio del trámite en el semáforo cuando sus tareas están en FIN (decisión de Carlos: el rojo es la caja que falta), relato por destinatario en `informe_instruccion`; escritos con `destinatario_*` y bloqueados sin destinatario. La clave de idempotencia usa al **titular** de la notificación (el representado, o la propia entidad), para que una notificación hecha no sobre si después se asigna un representante. La columna `norma` solo lleva los artículos ya leídos; el resto, pendiente. **§F y §G, en #969 (N5a-3):** migración `969_una_notificacion_dup` (se retiran `NOTIFICACION_ORGANISMOS` y `NOTIFICACION_INTERESADOS` con sus filas de catálogo y de `notificacion_fuentes`; aborta si algún trámite, plantilla o fila de `catalogo_plazos` cuelga de ellos); `notificaciones.es_notificar_del_solicitante` (antes `…_del_titular`) exige además la fuente `SOLICITANTE`; desaparece `_TRAMITES_CON_NOTIFICACION_MULTIPLE`. **§K enmendado, en #989:** migración `989_sede_solicitud` (`solicitudes.direccion_notificacion_id`, la sede del solicitante); el alta de expediente guarda al titular como solicitante y al autorizado o apoderado como representante; oficio y notificación se separan (`notificaciones.oficio_solicitante` y `destinatario_solicitante`); cambiar representante o sede en `mutaciones_arbol.editar_solicitud` refresca las `NOTIFICAR` al solicitante que no han salido y avisa del resto. Queda la interfaz (#929) y el poblado de propietarios e interesados (#431, #432)
**Fecha:** 2026-09-26
**Enmienda del 2026-09-27** (diseño de N5a con Carlos): el solicitante y su representante (§K); la fuente fija desde que nace la tarea y el bloqueo sin destinatario (§B); la lista de fuentes cerrada y el catálogo completo (§C); los sobrantes se borran (§D); el invariante del trámite en lugar de pendientes propios del certificado (§E); `SOLICITANTE` en lugar de `TITULAR` (§F); el destinatario siempre es un acto del usuario, y `tramites_destinatario` (§H, §L); cálculo por solicitud (§M). Las secciones tocadas lo dicen al principio.
**Enmienda del 2026-09-29** (#989, criterio de Carlos): la sede del solicitante, y el oficio separado de la notificación cuando hay representante (§K).
**Enmienda:** ADR-034 (la fila de `notificaciones` nace al crear la `NOTIFICAR`, no con el primer justificante, y guarda el destinatario) · ADR-046 §C (`NOTIFICACION_ORGANISMOS` y `NOTIFICACION_INTERESADOS` se funden en `NOTIFICACION`) · ADR-049 §E (la notificación que cumple el plazo se reconoce por su fuente, no solo por el trámite) y su «Lo que este ADR no decide» (primer punto: cómo se liga cada justificante a su destinatario) · #921, puntos 1-9 del mecanismo multi-destinatario (§J)
**Origen:** diseño de N5, sesiones del 2026-09-25, 2026-09-26 y 2026-09-27
**Base legal:** RD 1955/2000 arts. 128.3 (AAP), 131.8 (AAC) y 148.2 (DUP); Ley 39/2015 art. 40.1. Leídos en `legalize-es` (`BOE-A-2000-24019`, `BOE-A-2015-10565`)
**Relacionados:** ADR-021 (operaciones externas: el envío automático leerá de aquí a quién y adónde) · ADR-011 (`tramites_organismos`) · ADR-037 (`fases_tramites` es taxonomía, no cita norma) · #568 (edicto) · #929 (frontend de notificaciones) · #430, #431, #432, #924 (poblado de interesados) · #956 (certificado de cierre de fase) · #964 (anuncios de IP) · #966 (portal de transparencia)

---

## Contexto

### Qué sabe hoy BDDAT de una notificación

Sabe **qué** se notifica (el documento consumido por la `NOTIFICAR`) y **cómo acabó** (los justificantes vinculados y la fila de `notificaciones`: canal, resultado, intento, sede). No sabe **a quién ni a qué dirección**. Ese dato queda implícito y repartido:

- **Titular:** el generador de escritos toma `expediente.titular` y su dirección más reciente con rol TITULAR, o la principal de la entidad, y la imprime en el escrito (`app/services/escritos.py`, `_direccion_titular`). No queda en ningún otro sitio. No mira quién presentó la solicitud (`solicitudes.entidad_id`), que puede no ser el titular actual, ni si actúa por representante.
- **Organismo consultado:** `organismos_expediente.direccion_notificacion_id`, o si está vacío la dirección más reciente con rol CONSULTADO.
- **Boletines, ayuntamientos, órgano ambiental y, en la resolución, todos los demás:** solo en la cabeza del usuario. Hoy, en producción, el tramitador le dice expresamente al administrativo a quién notificar.

Mientras la notificación es manual no pasa nada. Un envío automático (ADR-021) solo puede leer la fila de `notificaciones`, y hoy esa fila no dice a quién va. Además las direcciones se editan sobre la misma fila (`app/modules/entidades/routes.py`, `editar_direccion`), así que ni siquiera guardar el id de la dirección dejaría constancia de adónde se envió.

### La resolución se notifica a varios, en todas las fases finalizadoras

La norma no lo limita a la DUP:

| Acto | Norma | A quién |
|---|---|---|
| AAP | RD 1955/2000 art. 128.3 | Solicitante y Administraciones, organismos y empresas de servicio público que intervinieron o pudieron intervenir |
| AAC | RD 1955/2000 art. 131.8 | Peticionario y organismos que emitieron condicionado técnico o debieron emitirlo |
| DUP | RD 1955/2000 art. 148.2 | Solicitante, organismos que informaron o debieron informar, titulares de bienes y derechos y restantes interesados |
| Todos | Ley 39/2015 art. 40.1 | Los interesados cuyos derechos e intereses se vean afectados |

ADR-046 §C resolvió solo la DUP, con dos trámites propios (`NOTIFICACION_ORGANISMOS`, `NOTIFICACION_INTERESADOS`). `RESOLUCION`, `RESOLUCION_AAP` y `RESOLUCION_AAC` notifican a varios desde su único `NOTIFICACION`. Es una asimetría: unos grupos tienen trámite con nombre propio y otros no.

### Por qué no vale el diseño heredado de #921

#921 preveía una sola `NOTIFICAR` con una lista de destinatarios (`Tarea.notificacion` a lista). Choca con el modelo por tres lados:

1. `notificaciones.tarea_id` es único: una fila por tarea.
2. Los justificantes cuelgan de la tarea sin decir de quién son. Para ligar cada uno a su destinatario haría falta un vínculo documento↔fila, que es justo lo que ADR-049 §B descartó.
3. Una tarea tiene un solo producido (`uq_tarea_un_producido`): los justificantes finales de todos los destinatarios no caben. De ahí salía un «certificado de notificación múltiple» como producido.

### Un riesgo latente en el plazo del acto

`notificaciones.calcular_documento_cumplimiento_fase` toma como notificación al titular cualquier `NOTIFICAR` del trámite `NOTIFICACION` de la fase finalizadora (`TRAMITE_NOTIFICACION_TITULAR`). Con organismos en ese mismo trámite —por ejemplo, una empresa de servicio público notificada por Notifica—, su puesta a disposición daría por cumplido el plazo de resolver del solicitante.

---

## Decisión

### A — Una `NOTIFICAR` por destinatario

Cada destinatario tiene su propia tarea `NOTIFICAR`, dentro del mismo trámite, con su fila en `notificaciones` (la relación sigue siendo 1:1 y `tarea_id` sigue siendo único).

- Los justificantes cuelgan de su tarea como hoy: **la posición dice de quién son**, que es el principio de ADR-049 §B.
- Fechas, resultado, sede, escalada del estado y `Tramite.finalizado` funcionan tarea a tarea, sin cambios. `Tramite.finalizado` ya exige todas las `NOTIFICAR` del trámite efectuadas, y el código ya contempla varias `NOTIFICAR` por trámite (`invariantes_esftt.py`).
- **No hay certificado de notificación múltiple** y `Tarea.notificacion` no pasa a lista. El certificado de cierre de la fase relata tarea a tarea.

### B — El destinatario vive en la fila de `notificaciones`

*Enmendada el 2026-09-27: representación, fuente fija, bloqueo sin destinatario y columnas.*

La fila de `notificaciones` es la que completa la tarea `NOTIFICAR` con sus datos propios, y es donde va el destinatario. No se añade ninguna columna a `tareas`: la tarea es genérica y no lleva datos propios de un tipo.

**La fila nace con la tarea.** Todo camino que crea una `NOTIFICAR` (creación genérica, motor, consultas, poblado de §D) crea su fila. El hook de `editar_tarea` deja de crearla y de borrarla; sigue fijando canal y documento, y cotejando. El canal admite vacío hasta el primer justificante (sigue saliendo del tipo de justificante, #712). La fila se borra con la tarea (`ON DELETE CASCADE`, ya existe).

**La fuente se fija al crear la tarea y no cambia nunca.** Es lo que distingue las `NOTIFICAR` apiladas en un trámite (y lo que permitirá pintarlas distintas en el árbol, #929). La pone el poblado; si se crea una a mano, la toma sola si el trámite tiene una fuente y la pregunta si tiene varias. No existe una `NOTIFICAR` sin fuente.

El destinatario es **entidad + en nombre de quién + dirección copiada**:

- **Entidad** a la que se envía (FK a `entidades`), no `interesados_expediente`: no todo notificado es interesado, y la dirección es de la entidad (`direcciones_notificacion`). Si hay representante (§K), es el representante.
- **En nombre de**: el representado, cuando lo hay.
- **Dirección copiada** en la fila, con el nombre y el NIF, y congelada (§D). Quien notifica —una persona o el automatismo de ADR-021— no necesita mirar nada más que la fila. Se anota de qué `direcciones_notificacion` se copió, solo como referencia.

**Sin destinatario, la `NOTIFICAR` no avanza:** no admite vínculos de documentos (consumidos ni producidos) ni se da por hecha. Es el gesto con el que el trámite entrega al administrativo «notifica este documento a este destinatario», y lo que permite a BDDAT constatar después a quién se notificó. Se puede forzar con justificación, como los demás escapes (en bitácora sobre la tarea, `escape: True`); el certificado de cierre lo relata como salvado. **Si la tarea tuvo escape sin destinatario, se deja así:** nadie exige más, y ya no admite rellenarlo. El destinatario real existe, en el justificante, pero BDDAT no lo constata.

**Cotejo:** si el justificante trae datos del destinatario (Notifica: el NIF), se avisa si no coinciden con la fila, como hoy con la remesa. Si todo cuadra en apariencia (un postal a otra entidad del mismo rol), no hay forma de detectarlo: hueco residual aceptado.

**Cada fuente lleva un rol, y el rol decide qué dirección de la entidad se copia**, igual que hoy `direcciones_notificacion.tipo_rol` distingue la dirección de titular de la de consultado. Consecuencia aceptada: **todo notificado es una entidad con dirección**. Los interesados son entidades (los propietarios de la DUP se darán de alta como entidades) y `tipo_rol` necesita los roles nuevos de #431 y #432.

Aplica a **todas** las `NOTIFICAR`, tengan uno o varios destinatarios.

### C — Qué se notifica en cada trámite: fuentes por (tipo de fase, tipo de trámite)

*Enmendada el 2026-09-27: lista cerrada y catálogo completo.*

Una tabla de catálogo, `notificacion_fuentes`, dice qué **fuentes** puebla cada (tipo de fase, tipo de trámite), con la norma que lo exige.

- **La clave incluye la fase** porque el mismo trámite (`NOTIFICACION`) está en varias fases y, al unificar (§G), quedaría indistinguible.
- **No va en `fases_tramites`**, que ADR-037 define como taxonomía que nunca cita norma. Tabla propia.
- **La tabla solo guarda roles, nunca entidades concretas.** El destinatario concreto es siempre un acto del usuario (§H).
- **Las fuentes son una lista cerrada en código**, cada una con su consulta y su dirección. El catálogo elige y el código sabe calcular, el mismo reparto que `{"calculado": …}` en `catalogo_plazos` (ADR-049 §E).

| Fuente | De dónde salen las entidades | Dirección que se copia |
|---|---|---|
| `SOLICITANTE` | La solicitud: su solicitante o su representante (§K) | La de §K |
| `ORGANISMO_DEL_TRAMITE` | `tramites_organismos` (separata, traslado al organismo) | `organismos_expediente.direccion_notificacion_id`, o la de consultado |
| `ORGANISMOS_CONSULTADOS` | `organismos_expediente` de la solicitud, incluidos los de declaración responsable | Igual que la anterior |
| `ORGANO_AMBIENTAL` | En su fase: `tramites_destinatario` (§L). En la resolución: el de la fase ambiental de la solicitud, si existe | La de consultado |
| `PROPIETARIOS_DUP` | `interesados_expediente` (vacío hasta #431) | La del rol de #431 |
| `INTERESADOS_RECONOCIDOS` | `interesados_expediente` (vacío hasta #432) | La del rol de #432 |
| `BOLETIN`, `AYUNTAMIENTO` | `tramites_destinatario` (§L), elegido entre entidades con dirección de publicador | La de publicador |
| `MINISTERIO`, `ORGANO_SUPERIOR` | `tramites_destinatario` (§L), elegido entre entidades con dirección de consultado | La de consultado |

- **Los organismos consultados incluyen aquellos por los que el titular presentó declaración responsable.** Ni la norma andaluza ni la estatal dicen que la declaración responsable excluya la notificación.
- **El órgano ambiental de evaluación es uno solo** (el servicio que hace las evaluaciones). Los órganos de afecciones (vías pecuarias, dominio público hidráulico, montes, espacios protegidos…) son organismos consultados. En la resolución, `ORGANO_AMBIENTAL` solo añade a alguien si la solicitud tiene fase ambiental (`COMPATIBILIDAD_AMBIENTAL`, `FIGURA_AMBIENTAL_EXTERNA`, `AAU_AAUS_INTEGRADA`; lista en código): si la fase existe es porque las reglas del motor la exigieron, así que no hace falta columna de obligatoriedad. Si el mismo órgano fue además consultado como organismo, recibe dos notificaciones (un rol, una notificación, §D).
- **Una fuente sin nadie no añade tareas.** Las que hoy no tienen datos (propietarios, reconocidos) quedan declaradas y vacías hasta #431, #432 y #924.
- Si alguna norma hiciera depender las fuentes del tipo de solicitud (`RESOLUCION` sirve a varios), la clave se amplía entonces: se siembra y se amplía el sembrado si aparece algo nuevo.

Contenido sembrado:

| (Fase, trámite) | Fuentes |
|---|---|
| `ANALISIS_SOLICITUD` · `COMUNICACION_INICIO_ADMISION`, `REQUERIMIENTO_SUBSANACION` | `SOLICITANTE` |
| `DATOS_CATASTRALES` · `REMISION_ACUERDO_DATOS`, `REQUERIMIENTO_CATASTRALES`, `TOMA_RAZON_RBDA` | `SOLICITANTE` |
| `CONSULTAS` · `CONSULTA_SEPARATA`, `CONSULTA_TRASLADO_ORGANISMO` | `ORGANISMO_DEL_TRAMITE` |
| `CONSULTAS` · `CONSULTA_TRASLADO_TITULAR` | `SOLICITANTE` (el organismo ligado al trámite es el asunto, no el destinatario) |
| `INFORMACION_PUBLICA` · `ANUNCIO_TITULAR`, `RECEPCION_ALEGACION` | `SOLICITANTE` (la alegación solo se traslada al solicitante; su respuesta se resuelve en la resolución) |
| `INFORMACION_PUBLICA` · `ANUNCIO_BOJA`, `ANUNCIO_BOP` | `BOLETIN` |
| `INFORMACION_PUBLICA` · `TABLON_AYUNTAMIENTOS` | `AYUNTAMIENTO` |
| `CONSULTA_MINISTERIO` · `SOLICITUD_INFORME` | `MINISTERIO` |
| `COMPATIBILIDAD_AMBIENTAL` · `SOLICITUD_COMPATIBILIDAD`; `FIGURA_AMBIENTAL_EXTERNA` · `SOLICITUD_FIGURA` | `ORGANO_AMBIENTAL` |
| `AAU_AAUS_INTEGRADA` · `REMISION_RESULTADO_IP_CONSULTAS`, `RECEPCION_DICTAMEN`, `RECEPCION_PROPUESTA_INF_VINC` | `ORGANO_AMBIENTAL` |
| `AAU_AAUS_INTEGRADA` · `DISCREPANCIA_INF_VINC` | `ORGANO_SUPERIOR` |
| `RESOLUCION`, `RESOLUCION_AAP`, `RESOLUCION_AAC` · `NOTIFICACION` | `SOLICITANTE`, `ORGANISMOS_CONSULTADOS`, `ORGANO_AMBIENTAL`, `INTERESADOS_RECONOCIDOS` |
| `RESOLUCION_DUP` · `NOTIFICACION` | `SOLICITANTE`, `ORGANISMOS_CONSULTADOS`, `PROPIETARIOS_DUP`, `INTERESADOS_RECONOCIDOS` |
| `RESOLUCION`, `RESOLUCION_AAP` · `PUBLICACION`; `RESOLUCION_DUP` · `PUBLICACION_BOE`, `PUBLICACION_BOJA`, `PUBLICACION_BOP` | `BOLETIN` |
| `RESOLUCION_DUP` · `REQUERIMIENTO_RBDA_DEFINITIVA` | `SOLICITANTE` |
| `RECONOCIMIENTO_INTERESADO` · `NOTIFICACION` | `SOLICITANTE` (quien pidió ser interesado) |

Fuera de la tabla, porque su `NOTIFICAR` desaparece: `ANUNCIO_BOE` y `ANUNCIO_PRENSA` (los publica el titular, #964) y `PORTAL_TRANSPARENCIA` (pasa a un solo ELABORAR que recopila lo expuesto y produce la URL, #966). Un test protege que todo trámite con `NOTIFICAR` en `tramites_tareas` tenga al menos una fuente.

- **Hecho en #964:** `ANUNCIO_BOE` y `ANUNCIO_PRENSA` son solo dos esperas en `tramites_tareas` (migración `964_anuncios_ip_secuencias`), y el test de fuentes ya no los exceptúa. Una `NOTIFICAR` forzada en ellos fuera de la secuencia no tiene fuente declarada y la pide a mano.
- **Hecho en #966:** `PORTAL_TRANSPARENCIA` es un solo ELABORAR (migración `966_portal_un_elaborar`), que produce `JUSTIFICANTE_PORTAL`. Con él, ningún trámite del catálogo tiene `NOTIFICAR` sin fuente, y el test de fuentes no exceptúa ninguno.

### D — Poblado idempotente, igual con uno o con varios destinatarios

*Enmendada el 2026-09-27: los sobrantes se borran; no hay escape para dejar de notificar.*

- **«¿Quién falta?»:** una sola función, que solo lee. Por cada fuente del (fase, trámite), las (fuente, entidad) que aún no tienen `NOTIFICAR` en el trámite; para una fuente cuya entidad aún no se ha elegido (§L vacía), el hueco sin entidad. Devuelve también los **sobrantes**: `NOTIFICAR` cuya entidad ya no sale de su fuente.
- **Botón «añadir los que faltan»:** rellena primero las `NOTIFICAR` del trámite con fuente y sin entidad, y crea una `NOTIFICAR` con su fila para el resto. Es el mismo botón en todos los trámites.
- **Clave de idempotencia: (trámite, fuente, entidad).** La búsqueda se hace solo entre las `NOTIFICAR` hijas del trámite, para no confundirla con una notificación a la misma entidad en otra fase o por otro motivo.
- **Un rol, una notificación.** Una entidad que aparece por dos fuentes recibe dos notificaciones, cada una con la dirección de su rol. Ejemplo: Edistribución como promotora de una línea de media tensión y, a la vez, organismo consultado por un cruzamiento con su alta tensión. Los efectos pueden no ser los mismos y las direcciones pueden ser distintas.
- **Cuándo se congela la dirección:** la copia se hace al rellenar. Mientras la fila no tenga ningún justificante, volver a pulsar el botón la refresca, porque todavía no se ha enviado nada. Desde el primer justificante, la fila queda fija. Así se absorbe el desfase entre elaborar y notificar (la firma): la dirección se fija justo antes de enviar.
- **Los sobrantes se borran, no se escapan.** Si a alguien no se le va a notificar (un organismo que desaparece, caso raro), se corrige su origen (se quita de las consultas, se da de baja el interesado) y se borra la `NOTIFICAR`, desvinculando y deshaciendo hacia atrás. Un escape en el trámite no vale: si quedaran `NOTIFICAR` válidas, cerraría el trámite en falso. Borrar la tarea sin corregir el origen no sirve: «¿quién falta?» la volvería a pedir.

### E — Nadie falta ni sobra: invariante del trámite

*Sustituida el 2026-09-27. Antes: «el certificado de cierre lee, no escribe», con pendientes propios en `CERT_CIERRE_FASE`.*

**Un trámite no está terminado mientras «¿quién falta?» devuelva a alguien o haya sobrantes**, además de lo que ya exige hoy (todas sus `NOTIFICAR` efectuadas). Es un invariante nuevo de `Tramite.finalizado`.

Con él, `CERT_CIERRE_FASE` (#956) no necesita pendientes propios: ya exige que todo lo creado en la fase esté terminado, así que hereda el bloqueo, sin escape posible (#956 D2). El relato del trámite, compartido por el informe «¿cómo voy?», `CERT_CIERRE_FASE` y `CERT_FIN_INSTRUCCION`, dice por qué no está terminado («falta notificar a X», «sobra la notificación a Y») y relata cada `NOTIFICAR` con su destinatario, su representación y su fuente, o como salvada si tuvo escape sin destinatario. La foto fija de #956 lo guarda tal cual. El bloque «Notificación al titular» pasa a «Notificación al solicitante».

El fin de instrucción queda cubierto por la misma coherencia de la cadena.

Se mantiene lo que se descartó: que el certificado pulse el botón por dentro (consultar el informe crearía tareas).

### F — La notificación al solicitante se reconoce por su fuente

*Enmendada el 2026-09-27: `SOLICITANTE`, no `TITULAR`.*

La notificación que cumple el plazo de resolver del acto (ADR-049 §A y §E) es la `NOTIFICAR` **de fuente `SOLICITANTE` en el trámite `NOTIFICACION`** de la fase que resuelve el acto. Hacen falta las dos condiciones:

- **La fuente**, porque en ese trámite hay también organismos e interesados.
- **El trámite**, porque otras `NOTIFICAR` de la misma fase también van al solicitante (por ejemplo, `REQUERIMIENTO_RBDA_DEFINITIVA` en `RESOLUCION_DUP`).

Sustituye a reconocerla solo por el trámite (`TRAMITE_NOTIFICACION_TITULAR`) y cierra el riesgo descrito en el contexto. Con §K vale también para `RECONOCIMIENTO_INTERESADO`, cuyo solicitante es quien pidió ser interesado: con `TITULAR` su acto no se habría cumplido nunca. Como la fuente es fija desde que nace la tarea (§B), una `NOTIFICAR` al solicitante cerrada con escape sin destinatario sigue contando.

`es_notificar_del_titular` y `TRAMITE_NOTIFICACION_TITULAR` se renombran a «del solicitante».

### G — Un solo trámite `NOTIFICACION`

`NOTIFICACION_ORGANISMOS` y `NOTIFICACION_INTERESADOS` se retiran y `RESOLUCION_DUP` notifica desde su `NOTIFICACION`, como las demás finalizadoras. Los grupos del art. 148.2 los distingue la fuente de cada tarea, y la interfaz puede agruparlas por fuente (#929). `_TRAMITES_CON_NOTIFICACION_MULTIPLE` desaparece: todos los trámites se pueblan igual.

Enmienda ADR-046 §C, que descartó la fusión «sin ganar nada a cambio». Ahora sí se gana algo: un solo mecanismo y la misma forma para la DUP que para la AAP y la AAC.

### H — El destinatario siempre es un acto del usuario; el ELABORAR lo imprime, no lo elige el código

*Sustituida el 2026-09-27. Antes: «ELABORAR no crea filas; consulta las fuentes sin escribir», y el generador dejaba el destinatario vacío si no salía uno.*

Ningún componente adivina un destinatario. Siempre lo fijó antes el usuario, en la tabla que le corresponde:

| Destinatario | Cuándo lo fija el usuario | Dónde |
|---|---|---|
| Solicitante, representante y sede | Al dar de alta la solicitud y en sus cambios | `solicitudes` (§K) |
| Organismos | Al rellenar las consultas | `organismos_expediente`, `tramites_organismos` |
| Interesados, propietarios DUP | Cuando aparecen | `interesados_expediente` |
| Destinatario único de un trámite que no está en otra tabla | En el trámite: al elaborar, o en su `NOTIFICAR` si no hay ELABORAR | `tramites_destinatario` (§L) |

- **Un servicio de destinatarios** reúne todo: resuelve el destinatario de un trámite leyendo esas tablas, registra la selección del usuario en `tramites_destinatario`, rellena la fila de la `NOTIFICAR` (§B, §D) y responde «¿quién falta?».
- **En los trámites ELABORAR → NOTIFICAR, el destinatario se decide al elaborar**, porque es el momento en que el documento y la notificación tienen que decir lo mismo. Si el servicio lo resuelve (solicitante, organismo del trámite), se toma sin ofrecer elegir; si no (ayuntamiento, órgano ambiental…), el usuario lo elige entre las entidades del rol, y después si va a su representante o directo. **Sin destinatario no se genera el escrito.** La `NOTIFICAR` nace después con ese mismo destinatario: el paso de ELABORAR a NOTIFICAR es la instrucción al administrativo de a quién notificar.
- **El constructor de contexto solo sirve al ELABORAR:** pide el destinatario al servicio y lo pone en las variables `destinatario_*` del escrito. No escribe ni decide. La `NOTIFICAR` nunca pasa por él.
- **Sin ELABORAR delante** (la notificación de la resolución, BOJA, publicaciones de la DUP), el destinatario sale del botón o se elige en la propia `NOTIFICAR`. En la resolución no hay oficio de remisión: a cada destinatario se le notifica el mismo documento y el motivo va en el asunto del envío. La ELABORACION de la finalizadora no imprime destinatario.
- Las variables del titular del escrito se quedan como están; cambiar los encabezados de los oficios a `destinatario_*` es trabajo de plantillas.

### I — Hallazgos del catálogo y cómo responde el código

Son hechos del catálogo `tramites_tareas` a 2026-09-26, **no reglas de cómo se modelan las fases y trámites**. Sirven para saber cómo tiene que responder el código ante lo que hay hoy.

- **Todo ELABORAR → NOTIFICAR del mismo trámite tiene un solo destinatario.** Cuando cada destinatario recibe su propio escrito, el trámite entero se repite por destinatario (`CONSULTA_SEPARATA`, `TABLON_AYUNTAMIENTOS`, `PUBLICACION_BOP`). Solo hay dos ELABORAR sin NOTIFICAR detrás en su trámite: `ELABORACION` de las fases finalizadoras y `REDACTAR_ANUNCIO`. En los dos casos el documento se notifica desde trámites hermanos.
- **La única `NOTIFICAR` con varios destinatarios es la de la resolución**, y en su trámite no hay otra tarea: ni ELABORAR delante ni ESPERAR_PLAZO detrás.
- *(2026-09-27)* El catálogo tenía `NOTIFICAR` donde el procedimiento no notifica: `ANUNCIO_BOE`, `ANUNCIO_PRENSA` (#964) y `PORTAL_TRANSPARENCIA` (#966).

**Cómo responde el código:** el poblado no comprueba el patrón; crea una `NOTIFICAR` por destinatario y nada más, y las tareas siguientes siguen como hoy. `tramites_destinatario` es de un solo destinatario por trámite porque así son hoy los trámites ELABORAR → NOTIFICAR. Si el catálogo cambia, el mecanismo no se rompe; como mucho habrá que ajustarlo en ese momento.

### J — Qué queda de los nueve puntos de #921

| # | Punto de #921 | Queda |
|---|---|---|
| 1 | Columna de destinatario en `notificaciones` | Sí, como entidad + en nombre de + fuente + dirección copiada (§B), no como FK a `interesados_expediente` |
| 2 | Quitar `UNIQUE(tarea_id)` | No: una fila por tarea (§A) |
| 3 | `Tarea.notificacion` a lista | No (§A) |
| 4 | `_estado_notificar` agregado | No hace falta: el estado es por tarea |
| 5 | Servicio de `_TRAMITES_CON_NOTIFICACION_MULTIPLE` | Desaparece: todos los trámites se pueblan igual (§G) |
| 6 | Poblado desde `interesados_expediente` | Sustituido por las fuentes (§C) |
| 7 | Certificado de notificación múltiple | No (§A) |
| 8 | `canal` por fila | Igual que hoy, vacío hasta el primer justificante |
| 9 | Error del parser con «Rechazada» | Ya corregido en #928 |

### K — «Notificar al solicitante»: solicitante o representante

*Nueva el 2026-09-27. Enmendada el 2026-09-29 (#989): la sede, y el oficio separado de la notificación.*

El titular es quien solicita las autorizaciones, pero no es constante: hay cambios de titularidad. Cada solicitud se contesta a **su** solicitante (`solicitudes.entidad_id`). Y el solicitante suele actuar por un representante o empresa autorizada para los trámites, que es a quien hay que notificar.

**Quién es quién** (criterio de Carlos, 29/09/2026):

- **Titular:** a quien se dirige siempre la resolución, y en la solicitud su solicitante. Casi siempre una sociedad. Se define por su NIF: con otro NIF es otra sociedad.
- **Apoderado:** quien figura como tal en las escrituras de la sociedad, con un poder normalmente genérico. Muchas veces presenta, firma y lee las notificaciones.
- **Autorizado:** un tercero al que la sociedad autoriza a actuar en su nombre, con un alcance muy variable (un expediente; solo entregar documentos; solicitar y desistir, pero no todo). El alcance no se modela: es texto libre en `autorizados_titular`.
- **Sede:** una misma sociedad, con el mismo NIF, puede tener varias sedes con distinta dirección y distinto correo (caso de Edistribución). Son sus filas de `direcciones_notificacion` de rol titular. Una sede no tiene NIF propio.

**Lo que guarda la solicitud:**

- **Su representante** (`solicitudes.representante_entidad_id`, opcional): un autorizado activo del solicitante (`autorizados_titular`) que actúa por él **en esta solicitud** y recibe sus notificaciones. Por solicitud, no por expediente ni por titular: sobrevive a los cambios de titularidad. Solo se admite a quien ya figura como autorizado (`validar_representante`, error sin escape): si no lo es, se le da de alta como autorizado desde la ficha del titular y después se elige; también un apoderado. El selector del alta solo lista autorizados. El representante no tiene sede: se usan siempre los datos de su ficha.
- **Su sede** (`solicitudes.direccion_notificacion_id`, opcional, #989): la del solicitante que figura en la solicitud. Tiene que ser suya, activa, de rol titular y sin otro NIF. Sin ella, los datos de la ficha. Ya no se toma la dirección de rol titular más reciente, que con varias sedes elegía por la fecha y no por la solicitud.

**La regla**, con el ejemplo de Carlos (titular Edistribución, NIF B12345678, ficha en Madrid con `registrogeneral@…`; sede en Sevilla con `registro_and_occidental@…`; autorizado Ingeniería SMART, NIF B98765432, `notificaciones@…`):

| Caso | Oficio (la dirección del papel) | Notificación (NIF y correo de aviso) |
|---|---|---|
| Sin representante, sin sede | Titular, dirección de su ficha (Madrid) | NIF del titular, correo de su ficha |
| Sin representante, con sede | Titular, dirección de la sede (Sevilla) | NIF del titular (el de la ficha: otro sería otra sociedad), correo de la sede |
| Con representante, sin sede | Titular, dirección de su ficha (Madrid) | NIF y correo del representante (su ficha) |
| Con representante, con sede | Titular, dirección de la sede (Sevilla) | NIF y correo del representante (su ficha) |

- **El oficio va siempre al solicitante**, a su sede o a su ficha, aunque la notificación la reciba el representante: la dirección del papel es la del titular (reminiscencia del envío en papel). `notificaciones.oficio_solicitante`; en el escrito, `destinatario_*` y `titular_dir`, y el representante en `destinatario_representante`.
- **La notificación va al representante** si lo hay, en nombre del solicitante; si no, al solicitante. `notificaciones.destinatario_solicitante`; la fila guarda a quién se envió y en nombre de quién (§B).
- La usan la fuente `SOLICITANTE`, el constructor de contexto y el certificado de cierre.

**Cambiar representante o sede** se admite siempre, sin bloquear (`mutaciones_arbol.editar_solicitud`). Las `NOTIFICAR` al solicitante que aún no tienen justificante se refrescan a la regla (bitácora `FIJAR_DESTINATARIO`, `origen: 'CAMBIO_SOLICITUD'`); las que ya lo tienen salieron así y no se tocan. Se avisa de lo que el cambio deja atrás, según el punto en que esté: notificaciones ya salidas y, si cambia la sede, oficios en redacción, a la firma, firmados o ya notificados con la dirección anterior (cambiar el representante no afecta al oficio). Si el usuario quiere otra cosa, deshace lo que pueda mientras no haya salido. La clave de idempotencia es el solicitante (§D), que no cambia: ninguna notificación pasa a sobrar.

Las tres puertas por las que nace o cambia una solicitud validan igual (`validar_representante`, `validar_sede`): el alta de expediente (que hasta #989 guardaba al autorizado como solicitante), `crear_solicitud` y `editar_solicitud`.

### L — `tramites_destinatario`: el destinatario elegido de un trámite

*Nueva el 2026-09-27.*

Para los trámites de un solo destinatario que no sale de ninguna otra tabla (fuentes `BOLETIN`, `AYUNTAMIENTO`, `MINISTERIO`, `ORGANO_AMBIENTAL` en su fase, `ORGANO_SUPERIOR`), la elección del usuario se guarda en el trámite: entidad y, si procede, su representante. Una fila por trámite, solo en trámites con `NOTIFICAR`; `REDACTAR_ANUNCIO`, por ejemplo, no lleva.

No duplica `notificaciones`: `tramites_destinatario` es lo **pretendido** (el dato del usuario, como `organismos_expediente`) y guarda solo quién; la fila de `notificaciones` es lo **realizado**, una copia congelada con la dirección.

### M — Cálculo por solicitud

*Nueva el 2026-09-27.*

`Tramite.finalizado` se evalúa muchas veces al pintar el árbol, y «¿quién falta?» consulta tablas. Se calcula una vez por solicitud, cargando fuentes y tablas de una sola vez, y se reutiliza para todos sus trámites, como `plazos_de_la_solicitud`. No se guarda: se recalcula en cada lectura, así que un nodo nuevo en el árbol lo actualiza sin mecanismo adicional.

---

## Consecuencias

- **BD:**
  - `solicitudes` gana `representante_entidad_id` (§K) y, con #989, `direccion_notificacion_id` (la sede).
  - `notificaciones` gana entidad, en nombre de, fuente, dirección de origen, la dirección copiada con nombre y NIF, y el momento de la copia; `canal` pasa a admitir vacío.
  - Tabla de catálogo nueva `notificacion_fuentes` (§C) y tabla operacional nueva `tramites_destinatario` (§L).
  - Se retiran `NOTIFICACION_ORGANISMOS` y `NOTIFICACION_INTERESADOS` y sus filas de catálogo.
  - Los datos de operación de desarrollo no se migran: se desechan y se recrean los expedientes tipo con los scripts actualizados.
- **Backend:**
  - Servicio de destinatarios: resolver, registrar la selección, rellenar la `NOTIFICAR`, «¿quién falta?» y sobrantes, calculado por solicitud (§M).
  - Toda creación de `NOTIFICAR` crea su fila con la fuente; el hook de `editar_tarea` deja de crear y de borrar filas.
  - Bloqueo de vínculos y de ejecución sin destinatario, con escape (§B).
  - Invariante nuevo de `Tramite.finalizado` (§E).
  - `es_notificar_del_titular` pasa a mirar la fuente `SOLICITANTE` (§F).
  - Relato de destinatarios en `informe_instruccion` y `cert_cierre_fase`.
  - Variables `destinatario_*` en el generador de escritos, vía el servicio (§H).
  - Desaparece `_TRAMITES_CON_NOTIFICACION_MULTIPLE`.
- **Invariantes de ADR-034/#928 que cambian:** «una fila existe solo si su tarea tiene, o tuvo, un justificante» pasa a «toda `NOTIFICAR` tiene su fila y su fuente desde que se crea, y sin destinatario no avanza».
- **Documentación a corregir en N5:**
  - `ESTRUCTURA_FTT` (.json y .md): `RESOLUCION_DUP` sin los dos trámites. Las notas «se notifica al titular u otro interesado, según la solicitud» se sustituyen por la referencia al catálogo de fuentes.
  - `DISEÑO_RESOLUCION_DUP.md` (lista blanca).
  - Docstrings de `Notificacion` y de `services/notificaciones.py`.
- **Issues:**
  - #929 recoge la interfaz: botón de poblado, selector de destinatario (en ELABORAR y en NOTIFICAR), tabla de destinatarios agrupada por fuente y `NOTIFICAR` pintadas según su fuente en el árbol.
  - #568 recoge el anuncio común del edicto.
  - #431 y #432, el alta de propietarios e interesados como entidades y sus roles.
  - #964 y #966 retiran las `NOTIFICAR` que el procedimiento no tiene; conviene cerrarlos antes de sembrar `notificacion_fuentes`.

---

## Lo que este ADR no decide

- **El anuncio del edicto común a varios destinatarios.** Un documento tiene un solo productor (`uq_documento_un_productor`), así que el anuncio del BOE no puede ser el producido de varias `NOTIFICAR`. Salidas posibles: relajar el índice para el anuncio, o una fila `Documento` por tarea sobre el mismo fichero (el pool ya lo admite), hecha a mano o por un botón. Lo decide #568.
- **Los roles nuevos de `tipo_rol`** y el alta de propietarios e interesados reconocidos como entidades: #431 y #432.
- **El envío automático** (ADR-021): este ADR le da el dato, no lo hace. Idea para entonces: que cada fuente lleve el texto del motivo para el asunto del envío.

---

## Alternativas descartadas

- **Una `NOTIFICAR` con varias filas** (#921, pre-ADR de ADR-049 §7.3): exige un vínculo documento↔fila, que ADR-049 §B descartó, además de un certificado múltiple y reescribir las reglas de fechas por fila.
- **Un trámite por destinatario para la resolución**, como `CONSULTA_SEPARATA`: ADR-046 §C, por la cantidad de propietarios.
- **El destinatario en `tareas`** (columna o tabla de vínculo): mete en la tarea genérica un dato propio de `NOTIFICAR`, que ya tiene su tabla.
- **El destinatario como FK a `interesados_expediente`:** no todo notificado es interesado y la dirección es de la entidad.
- **Apuntar a la dirección sin copiarla:** las direcciones se editan sobre la misma fila.
- **Una sola notificación por entidad**, eligiendo la fuente por prioridad: un rol, una notificación (§D).
- **La lista de destinatarios calculada siempre en vivo:** las tareas son objetos; se hace foto con el botón y se vuelve a pulsar si hace falta.
- **Que ELABORAR cree ya las filas de `notificaciones`:** la fila está anclada a la `NOTIFICAR`, que aún no existe. Lo que el ELABORAR fija va a `tramites_destinatario` (§L).
- **Que el certificado pulse el botón**, o que tenga pendientes propios (§E): basta el invariante del trámite.
- **Las fuentes en `fases_tramites`** (§C).
- **Mantener los trámites propios de la DUP:** deja la asimetría con AAP y AAC y dos mecanismos (§G).
- *(2026-09-27)* **Fuente `TITULAR`:** el titular cambia y cada solicitud se contesta a su solicitante; con `TITULAR`, `RECONOCIMIENTO_INTERESADO` no cumpliría nunca su plazo (§F, §K).
- *(2026-09-27)* **El representante tomado de `autorizados_titular`:** es general, puede haber varios y el ámbito va en texto libre; no dice quién representa en esta solicitud (§K).
- *(2026-09-27)* **Que el constructor de contexto deduzca el destinatario, o dejarlo vacío y escribirlo a mano en el escrito:** el destinatario es siempre un acto del usuario, y escribirlo a mano no deja rastro para notificar (§H).
- *(2026-09-27)* **Vincular justificantes sin destinatario, con solo un aviso:** saltaría la parte que el sistema garantiza (§B).
- *(2026-09-27)* **Escape en el trámite para no notificar a alguien:** cerraría el trámite en falso si quedaran `NOTIFICAR` válidas; se corrige el origen y se borra la tarea (§D).
- *(2026-09-27)* **Obligatoriedad de la fuente en una columna del catálogo:** la da la existencia de la fase ambiental, que deciden las reglas del motor (§C).
- *(2026-09-29)* **Corregir la dirección en cada `NOTIFICAR`, una a una** (`direccion_id` de `fijar_destinatario`), en lugar de la sede en la solicitud: el dato es de la solicitud y se repetiría en cada notificación (§K, #989).
- *(2026-09-29)* **Sede también para el representante:** el representante recibe con los datos de su ficha; la sede es del titular y es la dirección del oficio (§K, #989).
- *(2026-09-29)* **Sin sede, la dirección de rol titular más reciente:** con varias sedes elige por la fecha, no por la solicitud; sin sede, la ficha (§K, #989).
- *(2026-09-30)* **Representante no autorizado, con solo un aviso:** olvidar dar de alta la autorización no dejaría rastro; el representante es siempre un autorizado activo del solicitante (§K, #989).
