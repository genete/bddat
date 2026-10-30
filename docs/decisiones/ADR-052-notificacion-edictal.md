# ADR-052 — Notificación edictal: trámite transversal, intentos como documentos y canal EDICTO

**Estado:** Adoptada — implementada en #568 (2026-09-30): migración `568_notificacion_edictal`; `ESTRUCTURA_FTT` v6.9 (sección `TRAMITES_TRANSVERSALES`); `TIPOS_DOCUMENTOS_CATALOGO`. **§A (cómo se recoge lo que va por edicto) y §G (aplicar el anuncio) rehechos en #1037** (migración `1037_marca_edicto_notificacion`): el usuario marca qué `NOTIFICAR` van por edicto, el trámite las recoge al crearse y «Aplicar el anuncio» las cierra; la ruta `…/nodo/tramite/<id>/edicto` (GET y POST) y `mutaciones_arbol.aplicar_anuncio_edicto` siguen, con otra semántica; tarjeta de marcas, tarjeta del edicto y botón en el árbol
**Fecha:** 2026-09-30 (enmienda de #1037: 2026-10-30)
**Enmienda:** ADR-049 (§B tipos nuevos, §C caso POSTAL y `numero_intento`, §D resultado INCORRECTA; D15 de #928, canal del edicto) · ADR-051 («Lo que este ADR no decide», primer punto: el anuncio común del edicto; §C, la clave de `notificacion_fuentes` admite cualquier fase) · ADR-037 (un trámite puede declararse transversal, §A)
**Origen:** #568, sesión de diseño del 2026-09-30 con Carlos, partiendo del procedimiento legal y no del issue (redactado en junio y superado por ADR-049 y ADR-051). #1037, sesión de análisis de octubre de 2026 con Carlos: la selección de lo que va por edicto pasa de deducirse a marcarse
**Base legal:** Ley 39/2015 arts. 40, 41, 42, 43, 44, 45.2, 46 y DA 3.ª, leídos en `legalize-es` (`BOE-A-2015-10565`). El RD 1955/2000 (`BOE-A-2000-24019`) no regula la notificación infructuosa: se aplica la LPACAP, y la DA 3.ª.2 obliga al BOE aun con norma específica. LOPDGDD DA 7.ª (`BOE-A-2018-16673`, bloque `da-7`), para cómo se identifica al afectado en el anuncio (§G)
**Relacionados:** ADR-008 · ADR-034 · #928 (N1) · #929 (frontend de notificaciones) · #926 (fichero compartido por dos `Documento`) · #431, #432 (propietarios e interesados)

---

## Contexto

### El procedimiento, según la ley

- **Cuándo (art. 44):** interesado desconocido, lugar de notificación ignorado, o notificación intentada y no practicada. En papel, dos intentos fallidos: el segundo una sola vez, en otra franja horaria, dentro de los tres días siguientes (art. 42.2), que remite expresamente al 44.
- **En electrónico no hay edicto.** A quien está obligado o lo eligió, diez días naturales sin acceder es rechazo (art. 43.2), y el rechazo da la notificación por efectuada (art. 41.5). A quien no está obligado se le notifica en papel; la puesta a disposición en sede es la obligación paralela del art. 42.1, no una notificación ni una fecha de cumplimiento.
- **Qué:** anuncio en el BOE, obligatorio y gratuito, por su sistema telemático (DA 3.ª). Con carácter potestativo y previo, un boletín autonómico o provincial, el tablón del ayuntamiento o el consulado (art. 44 p. 2).
- **Contenido:** el del art. 40.2. El art. 46 (somera indicación) no aplica: lo que se notifica en este servicio siempre se publica.
- **Varios interesados:** un solo anuncio para todos (práctica del servicio; art. 45.2 p. 2 por analogía).
- **Plazos:** el de cursar toda notificación (art. 40.2). El art. 44 no abre ningún plazo tras publicar.
- **Fechas:** el deber de notificar en plazo se cumple con el primer intento acreditado (art. 40.4); los efectos, desde la publicación en el BOE.

### Qué no encajaba en BDDAT

1. El edicto directo no se podía registrar: la fila de `notificaciones` nace sin canal, `ANUNCIO_PUBLICADO` no da canal (D15 de #928 lo dejó a este issue) y `PATCH …/notificar` responde 422 sin canal. La tarea quedaba en azul para siempre.
2. El segundo intento fallido no tenía tipo. `numero_intento` se escribía a mano y el semáforo solo leía ese número, que podía contradecir a los documentos sin que nadie lo notara.
3. Un anuncio común a varios interesados exigía subir el mismo PDF una vez por notificación, tecleando cada vez la fecha de efectos.
4. La redacción, la firma y la remisión del anuncio no tenían sitio en el árbol.
5. `JUSTIFICANTE_SEDE` se tomaba por notificación en algún razonamiento; no lo es.

---

## Decisión

### A — `NOTIFICACION_EDICTAL`, un trámite transversal

Un trámite propio, porque un anuncio reúne a varios interesados y no puede vivir dentro de la `NOTIFICAR` de cada uno: **uno por anuncio**, no por interesado.

```
ELABORAR       consume: lo que se notifica a cada interesado   produce: ANUNCIO_EDICTO
NOTIFICAR      consume: ANUNCIO_EDICTO (fuente BOLETIN)        produce: JUSTIFICANTE_EDICTO
ESPERAR_PLAZO  consume: JUSTIFICANTE_EDICTO                    produce: ANUNCIO_PUBLICADO (BOE)
```

- **Transversal:** puede crearse en cualquiera de las 13 fases que notifican, sin límite por fase. Nuevo concepto en `ESTRUCTURA_FTT.json`: la sección `TRAMITES_TRANSVERSALES` declara el trámite una vez con la lista de sus fases, de la que la migración genera las filas de `fases_tramites`. ADR-037 no cambia en lo demás: sigue siendo taxonomía.
- **Manual, sin regla de motor.** La señal es la `NOTIFICAR` en rojo (agotada).
- **Sin segunda espera:** la espera no tiene fila en `catalogo_plazos`, como la primera espera de BOJA y BOP.
- **BOJA potestativo:** `NOTIFICAR` + `ESPERAR_PLAZO` adicionales en el mismo trámite, fuera de las tareas indicativas.
- **Destinatario:** el BOE, elegido en `tramites_destinatario` entre entidades con dirección de rol publicador, como BOJA y BOP. El BOE tiene que existir como entidad (dato, no código).
- **Los justificantes fallidos no pasan a este trámite:** se quedan en la `NOTIFICAR` de cada interesado, donde su posición dice de quién son (ADR-049 §B).
- **Qué va por edicto lo marca el usuario (#1037).** En el trámite de notificación de las fases finalizadoras, el usuario marca las `NOTIFICAR` que van por edicto. Solo admiten la marca las de fuente `INTERESADOS_RECONOCIDOS` y `PROPIETARIOS_DUP` (personas físicas: el resto notifica por vía electrónica obligada o a un organismo). No se deduce de que haya dos intentos fallidos: la marca es una decisión, y cubre también el edicto directo (interesado desconocido o lugar ignorado, art. 44).
- **Crear un `NOTIFICACION_EDICTAL` exige marcas.** La puerta de creación del trámite lo rechaza si la fase no tiene ninguna `NOTIFICAR` marcada y sin recoger, y dice qué hacer (marcar, en el trámite de notificación de la fase, y guardar). Al crearse, el edicto **recoge** las marcadas que no eran de otro edicto, de su misma fase; un segundo edicto en la fase recoge solo las marcadas después.
- **Dos estados de la marca:** *marcada* (`notificaciones.va_por_edicto`) y *recogida* (`tramite_edictal_id` del edicto que la recogió). Una recogida está marcada (`CHECK`). Si se borra el edicto, la recogida vuelve a marcada sin recoger.
- **El redactor del anuncio lee las recogidas** (`ContextoAnuncioEdictal`, `interesados_edicto`): el anuncio sabe exactamente a quién notifica en cuanto se redacta.

### B — Documentos

| Tipo | Rol | Qué acredita |
|---|---|---|
| `JUSTIFICANTE_POSTAL_1ER` | Consumido | 1.er intento postal, **siempre fallido** |
| `JUSTIFICANTE_POSTAL_2DO` (nuevo) | Consumido | 2.º intento postal fallido: habilita el edicto |
| `JUSTIFICANTE_POSTAL` | Producido | Entrega o rechazo, en el 1.er o el 2.º intento; nunca un fallido |
| `JUSTIFICANTE_SEDE` | Consumido | Puesta en sede de la notificación en papel (art. 42.1). No es notificación, no da fecha de cumplimiento |
| `ANUNCIO_EDICTO` (nuevo) | Producido por ELABORAR, consumido por NOTIFICAR del trámite | El anuncio firmado, uno para todos |
| `JUSTIFICANTE_EDICTO` (nuevo) | Producido por NOTIFICAR del trámite | La remisión al BOE por su plataforma; formato por concretar (captura o PDF) |
| `ANUNCIO_PUBLICADO` | Producido por la espera del trámite; una copia por interesado, producido de su `NOTIFICAR` | La publicación en el BOE: fecha de efectos |

Con los dos intentos fallidos consumidos, el producido de la `NOTIFICAR` queda vacío hasta la copia del anuncio. Sustituye a usar `JUSTIFICANTE_POSTAL` con un segundo significado (2.º intento, consumido).

### C — El número de intento sale de los documentos

`notificaciones.numero_intento` se retira, con su `CHECK` y su casilla. El semáforo de una `NOTIFICAR` postal lo deduce:

| Documentos | Estado |
|---|---|
| Sin intento ni producido | 🔵 pendiente |
| `_1ER`, sin producido | 🟠 primer intento fallido: toca el segundo |
| `_1ER` + `_2DO`, sin producido | 🔴 agotada: procede edicto |
| Producido | según el resultado (CORRECTA o RECHAZADA) |

Motivo: una sola fuente. ADR-049 lo conservaba porque no era derivable; con `_2DO` lo es.

### D — INCORRECTA se conserva como valor, pero la lógica no lo distingue

Con §B y §C no queda ningún caso que lo use: en papel los fallos los dicen los documentos; en Notifica a obligado, diez días es rechazo; a no obligado se notifica en papel; Anulada y No entregada no entran en BDDAT (ADR-049 §D). Sigue siendo admisible (`CHECK`, `resultados_validos`, propuesta del parser para «Caducada») por si falta un caso o la lectura es errónea, pero `_estado_notificar` lo trata como pendiente (🔵), sin efectos ni ejecución. Su docstring lo explica y dice que, si aparece un caso, se decide ahí el color, sin migrar datos.

### E — Canal: lo fija el primer justificante de la notificación; valor nuevo `EDICTO`

- **El canal lo fija quien practica la notificación:** el primer justificante que llega con canal. `JUSTIFICANTE_SEDE` **no** lo fija: es accesorio del papel. Mientras solo haya sede, la `NOTIFICAR` sigue sin canal y en azul (es cierto: no ha llegado ningún justificante de la notificación); la sede solo se comprueba al final, cuando el canal postal ya está.
- **Aviso de coherencia** (sin bloquear, en bitácora como los de #928): sede vinculada y canal distinto de `POSTAL`.
- **`EDICTO`**, nuevo valor de `ck_notificaciones_canal`. Solo admite `CORRECTA`; no exige sede. Lo dan:
  - `ANUNCIO_PUBLICADO`, **solo si no hay otro justificante con canal** (edicto directo). Tras intentos postales el canal se queda en `POSTAL`.
  - `JUSTIFICANTE_EDICTO`, justificante final de la `NOTIFICAR` de remisión al BOE.

### F — La fuente `BOLETIN` para cualquier fase

`notificacion_fuentes.tipo_fase_id` admite `NULL` = cualquier fase. La búsqueda de las fuentes de un trámite toma primero la pareja exacta (fase, trámite) y, si no existe, la fila del trámite con fase vacía; la exacta siempre gana, así que ningún trámite actual cambia. La unicidad se ajusta para que dos filas con fase vacía del mismo trámite y fuente choquen. El aviso de arranque (`pares_con_notificar_sin_fuente`) acepta la fila con fase vacía. `NOTIFICACION_EDICTAL` lleva una sola fila: fase vacía, `BOLETIN`, norma «art. 44 y DA 3.ª LPACAP».

### G — Aplicar el anuncio publicado a las notificaciones

Resuelve lo que ADR-051 dejó a este issue. **Rehecho en #1037:** el conjunto ya no lo ofrece el servidor entre postales agotadas y notificaciones sin justificante; lo fijó el usuario al marcar (§A) y lo recogió el edicto al crearse.

- **Una acción, sin lista de ids:** «Aplicar el anuncio», en el `NOTIFICACION_EDICTAL`, cierra las notificaciones que ese edicto recogió y siguen abiertas, con el anuncio publicado de su `ESPERAR_PLAZO`. `POST …/nodo/tramite/<id>/edicto`, sin cuerpo; `GET`, lo que la pantalla muestra (el anuncio con su fecha, las recogidas y por qué hoy no se puede aplicar).
- **Por cada una:** crea otra fila `Documento` sobre el mismo fichero y con la misma fecha (el pool lo admite; #926), la vincula como producido y fija `CORRECTA`. El canal sale solo (§E). No toca el índice `uq_documento_un_productor` (decisión de Carlos, #928 H1).
- **La pantalla:** tarjeta «Notificaciones por edicto» en el trámite de notificación (la marca, con el Guardar de siempre), tarjeta del anuncio y de lo recogido en el edicto, y el botón en la zona de acciones. El botón no pide confirmación: debajo dice cuántas notificaciones cerrará, y aplicar se deshace a mano desvinculando el producido (la tarea vuelve a «agotada»).
- **El anuncio identifica al afectado como manda la DA 7.ª LOPDGDD** (leída en `BOE-A-2018-16673`, bloque `da-7`): en las notificaciones por anuncios del art. 44 LPACAP, **por el número completo de su documento**; sin documento, **solo por nombre y apellidos**; **nunca el nombre junto al documento completo**. Por eso el contexto del redactor entrega ya la identificación publicable de cada interesado (un único elemento por afectado, sin dirección) y no nombre y documento por separado; el mismo interesado en dos notificaciones sale una vez. La parcela del propietario desconocido espera a #431.

**Interpretación** (se decidió al implementar y no figuraba en la conversación de diseño; se rectifica si Carlos lo ve distinto):

- La marca se puede quitar mientras el justificante de la remisión al BOE (`JUSTIFICANTE_EDICTO`) no esté vinculado; después, el conjunto del anuncio queda fijo.
- «Aplicar el anuncio» comprueba todo antes de cerrar nada (anuncio publicado, destinatario de cada una): si algo falla, no se cierra ninguna. Si el fallo llega a mitad, responde 422 con las ya cerradas.
- Con varios anuncios publicados en el edicto, se toma el de la primera `ESPERAR_PLAZO` por id (la indicativa).
- Las recogidas de canal postal que quedan con la sede pendiente (art. 42.1) se avisan tras aplicar; no impiden aplicar.

### H — Los certificados cuentan cómo y cuándo se notificó

La redacción de una `NOTIFICAR` terminada, compartida por el informe «¿cómo voy?», `CERT_CIERRE_FASE` y `CERT_FIN_INSTRUCCION`, pasa de «efectuada» a una línea uniforme con canal y fecha de efectos:

- «efectuada por Notifica / por correo postal / por BandeJA / por SIR, con efectos el …»; «rechazada por …» si RECHAZADA.
- Edicto: «efectuada por edicto, anuncio en el BOE de …, tras dos intentos postales fallidos (…, …)» o «sin intento previo (interesado desconocido o lugar ignorado)».

Todo sale de datos existentes. Los certificados ya emitidos no cambian (foto fija, #956). Las notificaciones a boletines se siguen relatando.

---

## Consecuencias

- **BD (una migración):** tipos `JUSTIFICANTE_POSTAL_2DO`, `ANUNCIO_EDICTO`, `JUSTIFICANTE_EDICTO`; tipo de trámite `NOTIFICACION_EDICTAL` con `tramites_tareas`, `tramites_tareas_documentos` y 13 filas de `fases_tramites` generadas desde el JSON; `ck_notificaciones_canal` con `EDICTO`; fuera `numero_intento` y sus dos `CHECK`; `notificacion_fuentes.tipo_fase_id` nulable, unicidad ajustada y la fila de `NOTIFICACION_EDICTAL`.
- **Backend:** `notificaciones` (canal por tipo sin sede, `EDICTO`, previos con `_2DO`); `mutaciones_arbol._hook_notificar` (canal, aviso de sede, sin `numero_intento`); `PATCH …/notificar` sin `numero_intento`; `estado_dominio._estado_notificar` y `cola_administrativo` (§C, §D); `destinatarios_notificacion` (§F); la acción de §G y su ruta; `informe_instruccion` (§H); `cert_cumplimiento_fase._CANAL_LEGIBLE`.
- **Datos de desarrollo:** los expedientes tipo con notificaciones postales de dos intentos, si los hay, se recrean.
- **Documentación:** `ESTRUCTURA_FTT` y `TIPOS_DOCUMENTOS_CATALOGO` (hecho); `MODELO_ESTADOS_SEMAFORO` §3; cabeceras de ADR-049 y ADR-051; `ESTADO_ADR049`.
- **Issues:** #929 recoge la pantalla (tipos nuevos en el registro, fuera la casilla de intento); la de la acción de §G pasó a #1037. Issue aparte: el justificante de remisión a boletín de BOJA, BOP y las publicaciones de la resolución (hoy sin salida declarada, no pueden registrarse) y «publicado el …» en los certificados.
- **#1037 (marcar y aplicar):** una migración (`va_por_edicto`, `tramite_edictal_id`, `CHECK` y un índice parcial); `notificaciones` (candidatas, marcadas, recogidas y los motivos de por qué una marca no se puede poner o quitar); `mutaciones_arbol` (`editar_tramite` con `notificaciones_edicto`, recogida al crear, `aplicar_anuncio_edicto` rehecha); `invariantes_esftt` (la puerta de creación); el contexto `ContextoAnuncioEdictal`; detalle y esquema editable del trámite; `PATCH …/nodo/tramite/<id>` con `notificaciones_edicto`; la pantalla (`MarcasEdicto.jsx`, `AnuncioEdicto.jsx`). Depende de #431 y #432 para que existan en uso real las `NOTIFICAR` de esas dos fuentes.

---

## Lo que este ADR no decide

- El justificante de remisión a boletín fuera del edicto (issue aparte).
- El formato de `JUSTIFICANTE_EDICTO` (captura o PDF): se concreta con el primer caso real.
- Acumular en un anuncio interesados de fases distintas: lo marcado se recoge solo dentro de su fase (§A); se amplía si hace falta.
- Si el art. 41.7 (primer cauce) haría valer un anuncio potestativo previo en el BOJA como fecha de efectos: el cálculo de efectos solo lee el producido, que es la copia del BOE.

---

## Alternativas descartadas

- **Cerrar la notificación original sin trámite propio:** la redacción, firma y remisión del anuncio quedaban fuera del árbol, y el anuncio común no tenía dónde vivir.
- **Repetir el trámite en las 13 fases del JSON:** 13 copias que mantener a la vez (§A).
- **Un mismo documento producido por dos tareas:** lo prohíbe `uq_documento_un_productor`, y Carlos decidió no tocarlo (#928 H1).
- **`JUSTIFICANTE_POSTAL` con un segundo significado** (2.º intento fallido, consumido): fuerza el tipo (§B).
- **Mantener `numero_intento` comprobando que coincide con los documentos:** el usuario seguiría escribiendo un dato que ya está (§C).
- **Retirar INCORRECTA del todo:** se conserva por si falta un caso (§D).
- **Canal vacío para el edicto directo:** una notificación hecha que no dice cómo; obligaba a excepciones en «registrada», el semáforo y la ruta (§E).
- **Que `JUSTIFICANTE_SEDE` fije `POSTAL`:** la sede no es una notificación y no debe decir de qué tipo es (§E).
- **13 filas de fuente, una por fase** (§F).
- **Copias del anuncio a mano:** la fecha de efectos de cada interesado dependería de teclearla bien (§G).
- **Deducir qué va por edicto de que haya dos intentos fallidos** (y ofrecerlo desde el botón): los intentos son siempre postales y no cubren el edicto directo; el servidor ofrecía de más y el usuario elegía entre lo que no había decidido él (#1037, §A y §G).
- **Nombre y documento juntos en el anuncio:** la DA 7.ª LOPDGDD lo prohíbe en las notificaciones por anuncios del art. 44 (§G).
- **Redactar «por edicto» solo en el edicto:** sería la única notificación que dice cómo y cuándo (§H).
