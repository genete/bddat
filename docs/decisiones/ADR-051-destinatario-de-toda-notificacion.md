# ADR-051 — Toda notificación tiene destinatario: fuentes por fase y trámite, poblado idempotente y dirección congelada

**Estado:** Adoptada — sin implementar. La implementa **N5** (notificación multi-destinatario, sin número todavía), siguiente de la cadena de ADR-049 (`docs/diseño/ESTADO_ADR049.md`)
**Fecha:** 2026-09-26
**Enmienda:** ADR-034 (la fila de `notificaciones` nace al crear la `NOTIFICAR`, no con el primer justificante, y guarda el destinatario) · ADR-046 §C (`NOTIFICACION_ORGANISMOS` y `NOTIFICACION_INTERESADOS` se funden en `NOTIFICACION`) · ADR-049 §E (la notificación al titular se reconoce por su fuente, no solo por el trámite) y su «Lo que este ADR no decide» (primer punto: cómo se liga cada justificante a su destinatario) · #921, puntos 1-9 del mecanismo multi-destinatario (§J)
**Origen:** diseño de N5, sesiones del 2026-09-25 y 2026-09-26
**Base legal:** RD 1955/2000 arts. 128.3 (AAP), 131.8 (AAC) y 148.2 (DUP); Ley 39/2015 art. 40.1. Leídos en `legalize-es` (`BOE-A-2000-24019`, `BOE-A-2015-10565`)
**Relacionados:** ADR-021 (operaciones externas: el envío automático leerá de aquí a quién y adónde) · ADR-011 (`tramites_organismos`) · ADR-037 (`fases_tramites` es taxonomía, no cita norma) · #568 (edicto) · #929 (frontend de notificaciones) · #430, #431, #432, #924 (poblado de interesados) · #956 (certificado de cierre de fase)

---

## Contexto

### Qué sabe hoy BDDAT de una notificación

Sabe **qué** se notifica (el documento consumido por la `NOTIFICAR`) y **cómo acabó** (los justificantes vinculados y la fila de `notificaciones`: canal, resultado, intento, sede). No sabe **a quién ni a qué dirección**. Ese dato queda implícito y repartido:

- **Titular:** el generador de escritos toma `expediente.titular` y su dirección más reciente con rol TITULAR, o la principal de la entidad, y la imprime en el escrito (`app/services/escritos.py`, `_direccion_titular`). No queda en ningún otro sitio.
- **Organismo consultado:** `organismos_expediente.direccion_notificacion_id`, o si está vacío la dirección más reciente con rol CONSULTADO.
- **Boletines y, en la resolución, todos los demás:** solo en la cabeza del usuario.

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

`notificaciones.calcular_documento_cumplimiento_fase` toma como notificación al titular cualquier `NOTIFICAR` del trámite `NOTIFICACION` de la fase finalizadora (`TRAMITE_NOTIFICACION_TITULAR`). Con organismos en ese mismo trámite —por ejemplo, una empresa de servicio público notificada por Notifica—, su puesta a disposición daría por cumplido el plazo de resolver del titular.

---

## Decisión

### A — Una `NOTIFICAR` por destinatario

Cada destinatario tiene su propia tarea `NOTIFICAR`, dentro del mismo trámite, con su fila en `notificaciones` (la relación sigue siendo 1:1 y `tarea_id` sigue siendo único).

- Los justificantes cuelgan de su tarea como hoy: **la posición dice de quién son**, que es el principio de ADR-049 §B.
- Fechas, resultado, sede, escalada del estado y `Tramite.finalizado` funcionan tarea a tarea, sin cambios. `Tramite.finalizado` ya exige todas las `NOTIFICAR` del trámite efectuadas, y el código ya contempla varias `NOTIFICAR` por trámite (`invariantes_esftt.py`).
- **No hay certificado de notificación múltiple** y `Tarea.notificacion` no pasa a lista. El certificado de cierre de la fase relata tarea a tarea.

### B — El destinatario vive en la fila de `notificaciones`

La fila de `notificaciones` es la que completa la tarea `NOTIFICAR` con sus datos propios, y es donde va el destinatario. No se añade ninguna columna a `tareas`: la tarea es genérica y no lleva datos propios de un tipo.

El destinatario es **entidad + fuente + dirección copiada**:

- **Entidad** (FK a `entidades`), no `interesados_expediente`. No todo notificado es interesado (el boletín es una entidad con rol PUBLICADOR), y la dirección de notificación es de la entidad (`direcciones_notificacion`).
- **Fuente:** por qué se le notifica (§C).
- **Dirección copiada** en la fila y congelada (§D). Quien notifica —una persona o el automatismo de ADR-021— no necesita mirar nada más que la fila.

**Cada fuente lleva un rol, y el rol decide qué dirección de la entidad se copia**, igual que hoy `direcciones_notificacion.tipo_rol` distingue la dirección de titular de la de consultado.

Consecuencia aceptada: **todo notificado es una entidad con dirección**. Los interesados son entidades (los propietarios de la DUP se darán de alta como entidades) y `tipo_rol`, que hoy solo tiene TITULAR, CONSULTADO y PUBLICADOR, necesita roles nuevos.

Aplica a **todas** las `NOTIFICAR`, tengan uno o varios destinatarios.

### C — Qué se notifica en cada trámite: fuentes por (tipo de fase, tipo de trámite)

Una tabla de catálogo dice qué **fuentes** puebla cada (tipo de fase, tipo de trámite), con la norma que lo exige.

- **La clave incluye la fase** porque el mismo trámite (`NOTIFICACION`) está en varias fases y, al unificar (§G), quedaría indistinguible.
- **No va en `fases_tramites`**, que ADR-037 define como taxonomía que nunca cita norma. Tabla propia.
- **Las fuentes son una lista cerrada en código**, cada una con su consulta. El catálogo elige y el código sabe calcular, el mismo reparto que `{"calculado": …}` en `catalogo_plazos` (ADR-049 §E). Lista orientativa, nombres a fijar al implementar: `TITULAR`, `ORGANISMO_DEL_TRAMITE` (vía `tramites_organismos`), `ORGANISMOS_CONSULTADOS` (los de la solicitud), `MEDIO_AMBIENTE`, `PUBLICADOR`, `PROPIETARIOS_DUP`, `INTERESADOS_RECONOCIDOS`.
- **Los organismos consultados incluyen aquellos por los que el titular presentó declaración responsable.** Ni la norma andaluza ni la estatal dicen que la declaración responsable excluya la notificación.
- **Una fuente sin nadie no añade tareas.** Las que hoy no tienen datos (propietarios, reconocidos, Medio Ambiente) quedan declaradas y vacías hasta #431, #432 y #924.
- Si alguna norma hiciera depender las fuentes del tipo de solicitud (`RESOLUCION` sirve a varios), la clave se amplía entonces.

Contenido para la notificación de la resolución, según la norma citada:

| (Fase, trámite) | Fuentes |
|---|---|
| `RESOLUCION` · `NOTIFICACION` | Titular, organismos consultados, interesados reconocidos |
| `RESOLUCION_AAP` · `NOTIFICACION` | Titular, organismos consultados, interesados reconocidos |
| `RESOLUCION_AAC` · `NOTIFICACION` | Titular, organismos consultados, interesados reconocidos |
| `RESOLUCION_DUP` · `NOTIFICACION` | Titular, organismos consultados (y Medio Ambiente), propietarios DUP, interesados reconocidos |

El resto de trámites con `NOTIFICAR` (requerimientos, consultas, traslados, anuncios…) se completa en N5 repasando el catálogo.

### D — Poblado idempotente, igual con uno o con varios destinatarios

- **Al crear una `NOTIFICAR` se crea su fila** en `notificaciones`, con el destinatario vacío.
- **Botón «añadir los que faltan»:** lee las fuentes del (fase, trámite) y, por cada (fuente, entidad) que aún no tenga fila en el trámite, rellena primero las filas vacías y crea una `NOTIFICAR` con su fila para el resto. Es el mismo botón en todos los trámites; en uno de un solo destinatario rellena su única fila.
- **Clave de idempotencia: (trámite, fuente, entidad).** La búsqueda se hace solo entre las `NOTIFICAR` hijas del trámite, para no confundirla con una notificación a la misma entidad en otra fase o por otro motivo.
- **Un rol, una notificación.** Una entidad que aparece por dos fuentes recibe dos notificaciones, cada una con la dirección de su rol. Ejemplo: Edistribución como promotora de una línea de media tensión y, a la vez, organismo consultado por un cruzamiento con su alta tensión. Los efectos pueden no ser los mismos y las direcciones pueden ser distintas.
- **Cuándo se congela la dirección:** la copia se hace al pulsar el botón. Mientras la fila no tenga ningún justificante, volver a pulsarlo la refresca, porque todavía no se ha enviado nada. Desde el primer justificante, la fila queda fija. Así se absorbe el desfase entre elaborar y notificar (la firma): la dirección se fija justo antes de enviar.
- El canal sigue saliendo del tipo de justificante (#712), así que queda vacío hasta el primero.

### E — Quién falta: el certificado de cierre lee, no escribe

Hay una sola función, «¿quién falta?», que devuelve las (fuente, entidad) de las fuentes sin fila en el trámite. El botón la aplica. `CERT_CIERRE_FASE` (#956) y su informe «¿cómo voy?» solo la leen: listan a los que faltan como pendientes y el certificado no se emite mientras haya alguno.

Se descarta que el certificado pulse el botón por dentro: consultar el informe crearía tareas. El resultado es el mismo —nadie se queda sin notificar al cerrar— y el usuario ve a quién se va a añadir antes de añadirlo. Cerrar la finalizadora sin notificar a un interesado es la zona de nulidad que #956 ya quiso cerrar.

### F — La notificación al titular se reconoce por su fuente

La notificación al titular que cumple el plazo de resolver del acto (ADR-049 §A y §E) es la `NOTIFICAR` **de fuente `TITULAR` en el trámite `NOTIFICACION`** de la fase que resuelve el acto. Hacen falta las dos condiciones:

- **La fuente**, porque en ese trámite hay también organismos e interesados.
- **El trámite**, porque otras `NOTIFICAR` de la misma fase también van al titular (por ejemplo, `REQUERIMIENTO_RBDA_DEFINITIVA` en `RESOLUCION_DUP`).

Sustituye a reconocerla solo por el trámite (`TRAMITE_NOTIFICACION_TITULAR`) y cierra el riesgo descrito en el contexto.

### G — Un solo trámite `NOTIFICACION`

`NOTIFICACION_ORGANISMOS` y `NOTIFICACION_INTERESADOS` se retiran y `RESOLUCION_DUP` notifica desde su `NOTIFICACION`, como las demás finalizadoras. Los grupos del art. 148.2 los distingue la fuente de cada tarea, y la interfaz puede agruparlas por fuente (#929). `_TRAMITES_CON_NOTIFICACION_MULTIPLE` desaparece: todos los trámites se pueblan igual.

Enmienda ADR-046 §C, que descartó la fusión «sin ganar nada a cambio». Ahora sí se gana algo: un solo mecanismo y la misma forma para la DUP que para la AAP y la AAC.

### H — ELABORAR no crea filas; consulta las fuentes sin escribir

- La fila está anclada a la `NOTIFICAR` (ADR-034), que al elaborar todavía no existe. Crearla antes de tiempo iría contra el orden del flujo, y el desfase de la firma aconseja congelar tarde (§D).
- El generador del escrito puede consultar la misma función de fuentes, sin escribir, para imprimir al destinatario. Así «¿a quién va?» tiene una sola respuesta. Si la función devuelve más de un destinatario, el generador no elige y deja el destinatario sin rellenar.

### I — Hallazgos del catálogo y cómo responde el código

Son hechos del catálogo `tramites_tareas` a 2026-09-26, **no reglas de cómo se modelan las fases y trámites**. Sirven para saber cómo tiene que responder el código ante lo que hay hoy.

- **Todo ELABORAR → NOTIFICAR del mismo trámite tiene un solo destinatario.** Cuando cada destinatario recibe su propio escrito, el trámite entero se repite por destinatario (`CONSULTA_SEPARATA`, `TABLON_AYUNTAMIENTOS`, `PUBLICACION_BOP`). Solo hay dos ELABORAR sin NOTIFICAR detrás en su trámite: `ELABORACION` de las fases finalizadoras y `REDACTAR_ANUNCIO`. En los dos casos el documento se notifica desde trámites hermanos.
- **La única `NOTIFICAR` con varios destinatarios es la de la resolución**, y en su trámite no hay otra tarea: ni ELABORAR delante ni ESPERAR_PLAZO detrás.

**Cómo responde el código:** el poblado no comprueba el patrón; crea una `NOTIFICAR` por destinatario y nada más, y las tareas siguientes siguen como hoy. El generador del escrito solo rellena el destinatario si la función de fuentes da uno. Si el catálogo cambia, el mecanismo no se rompe; como mucho habrá que ajustarlo en ese momento.

### J — Qué queda de los nueve puntos de #921

| # | Punto de #921 | Queda |
|---|---|---|
| 1 | Columna de destinatario en `notificaciones` | Sí, como entidad + fuente + dirección copiada (§B), no como FK a `interesados_expediente` |
| 2 | Quitar `UNIQUE(tarea_id)` | No: una fila por tarea (§A) |
| 3 | `Tarea.notificacion` a lista | No (§A) |
| 4 | `_estado_notificar` agregado | No hace falta: el estado es por tarea |
| 5 | Servicio de `_TRAMITES_CON_NOTIFICACION_MULTIPLE` | Desaparece: todos los trámites se pueblan igual (§G) |
| 6 | Poblado desde `interesados_expediente` | Sustituido por las fuentes (§C) |
| 7 | Certificado de notificación múltiple | No (§A) |
| 8 | `canal` por fila | Igual que hoy |
| 9 | Error del parser con «Rechazada» | Ya corregido en #928 |

---

## Consecuencias

- **BD:**
  - `notificaciones` gana entidad, fuente y la dirección copiada; `canal` pasa a admitir vacío hasta el primer justificante.
  - Tabla de catálogo nueva de fuentes por (tipo de fase, tipo de trámite), con norma.
  - Se retiran `NOTIFICACION_ORGANISMOS` y `NOTIFICACION_INTERESADOS` y sus filas de catálogo.
  - Los datos de operación de desarrollo no se rellenan: se desechan si hace falta.
- **Backend:**
  - Servicio de fuentes, con «¿quién falta?» y el poblado.
  - El hook de `editar_tarea` deja de crear y de borrar filas: la fila nace con la tarea. Sigue fijando canal y documento, y cotejando.
  - `notificaciones.es_notificar_del_titular` pasa a mirar la fuente (§F).
  - `cert_cierre_fase` lee «¿quién falta?».
  - El generador de escritos consulta las fuentes (§H).
  - Desaparece `_TRAMITES_CON_NOTIFICACION_MULTIPLE`.
- **Invariante de ADR-034/#928 que cambia:** «una fila existe solo si su tarea tiene, o tuvo, un justificante» pasa a «toda `NOTIFICAR` tiene su fila desde que se crea».
- **Documentación a corregir en N5:**
  - `ESTRUCTURA_FTT` (.json y .md): `RESOLUCION_DUP` sin los dos trámites. Las notas «se notifica al titular u otro interesado, según la solicitud» se sustituyen por la referencia al catálogo de fuentes.
  - `DISEÑO_RESOLUCION_DUP.md` (lista blanca).
  - Docstrings de `Notificacion` y de `services/notificaciones.py`.
- **Issues:**
  - #929 recoge la interfaz: botón de poblado, tabla de destinatarios agrupada por fuente y nombre del destinatario en el nodo.
  - #568 recoge el anuncio común del edicto.
  - #431 y #432, el alta de propietarios e interesados como entidades y sus roles.

---

## Lo que este ADR no decide

- **El anuncio del edicto común a varios destinatarios.** Un documento tiene un solo productor (`uq_documento_un_productor`), así que el anuncio del BOE no puede ser el producido de varias `NOTIFICAR`. Salidas posibles: relajar el índice para el anuncio, o una fila `Documento` por tarea sobre el mismo fichero (el pool ya lo admite), hecha a mano o por un botón. Lo decide #568.
- **Los roles nuevos de `tipo_rol`** y el alta de propietarios e interesados reconocidos como entidades: #431 y #432.
- **Las columnas exactas de la dirección copiada** (postal, correo, DIR3, SIR…) y si vincular un justificante exige tener destinatario: N5.
- **El catálogo de fuentes de los trámites no finalizadores:** N5, repasando el catálogo.
- **La notificación de `RECONOCIMIENTO_INTERESADO`**, cuyo destinatario es un tercero que pidió ser interesado, no el titular: con #432.
- **El envío automático** (ADR-021): este ADR le da el dato, no lo hace.

---

## Alternativas descartadas

- **Una `NOTIFICAR` con varias filas** (#921, pre-ADR de ADR-049 §7.3): exige un vínculo documento↔fila, que ADR-049 §B descartó, además de un certificado múltiple y reescribir las reglas de fechas por fila.
- **Un trámite por destinatario para la resolución**, como `CONSULTA_SEPARATA`: ADR-046 §C, por la cantidad de propietarios.
- **El destinatario en `tareas`** (columna o tabla de vínculo): mete en la tarea genérica un dato propio de `NOTIFICAR`, que ya tiene su tabla.
- **El destinatario como FK a `interesados_expediente`:** no todo notificado es interesado y la dirección es de la entidad.
- **Apuntar a la dirección sin copiarla:** las direcciones se editan sobre la misma fila.
- **Una sola notificación por entidad**, eligiendo la fuente por prioridad: un rol, una notificación (§D).
- **La lista de destinatarios calculada siempre en vivo:** las tareas son objetos; se hace foto con el botón y se vuelve a pulsar si hace falta.
- **Que ELABORAR cree ya las filas** (§H).
- **Que el certificado de cierre pulse el botón** (§E).
- **Las fuentes en `fases_tramites`** (§C).
- **Mantener los trámites propios de la DUP:** deja la asimetría con AAP y AAC y dos mecanismos (§G).
