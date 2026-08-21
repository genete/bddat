# ADR-041 — Plazos y suspensiones se miden con el mismo mecanismo

**Estado:** Aceptada — implementada en #778 (2026-08-21)
**Fecha:** 2026-08-20
**Issue:** #778
**Se apoya en:** ADR-002 (el ESFTT no almacena fechas), ADR-010 (documento vinculado a la tarea con rol)
**No enmienda ningún ADR anterior.**

---

## Contexto

BDDAT tiene plazos definidos en un catálogo. Cada entrada dice dónde se produce el plazo
(camino ESFTT), qué documento alberga la fecha que lo dispara, y cuánto dura.

Unos plazos obligan a la administración tramitadora y otros obligan a terceros —al
interesado que debe subsanar, al organismo que debe informar—, o son simples períodos que
han de transcurrir. **El único plazo de la tramitadora es el de la solicitud**: el plazo
máximo para resolver y notificar (art. 21.3 LPACAP), y es el único que puede suspenderse
(#788). Algunos plazos de terceros suspenden ese plazo y otros no.

El tramitador necesita dos cosas:

1. **Saber cómo va cada espera** —de un tercero o de simple transcurso del tiempo— para
   decidir si impulsa el procedimiento.
2. **Saber cuánto tiempo le queda** para resolver la solicitud.

### El problema

El servicio de plazos calcula esas dos cosas por **dos caminos distintos que no se hablan**:

- **Camino de plazos** (`obtener_estado_plazo`): consulta el catálogo, resuelve el documento
  de disparo, suma el valor, obtiene la fecha de vencimiento. Sabe cuánto dura cada cosa.
- **Camino de suspensiones** (`_obtener_suspensiones` / `_fecha_cierre_suspension`): **no
  consulta el catálogo en ningún momento**. Tiene una lista de trámites escrita en el código
  (`_TRAMITES_SUSPENSION`), navega el árbol por su cuenta buscando documentos, y arma
  intervalos con tres tentativas encadenadas de cierre.

El segundo camino no sabe cuánto dura nada, porque nunca pregunta. De ahí sale el bug de
#778 y no de otro sitio: **una suspensión no puede vencer si el mecanismo que la mide
desconoce que existe un plazo**. Cuando el interesado no contesta a un requerimiento, el
cierre se queda en «hoy» y se recalcula cada día: la suspensión crece indefinidamente, la
fecha límite se aleja un día por cada día que pasa, y el expediente nunca vence. El caso que
más urge detectar es el que el sistema oculta.

El tope que #778 pedía añadir es un dato que el catálogo **ya tiene** y que nadie le pasaba
a ese segundo camino.

### La observación que reordena todo

Una suspensión no es un mecanismo aparte. Es **el plazo de un tercero, visto desde la
solicitud**. Y la propia ley lo dice al fijar cuándo termina, art. 22.1.a:

> «por el tiempo que medie entre la notificación del requerimiento y su efectivo
> cumplimiento por el destinatario, **o, en su defecto, por el del plazo concedido**»

Es decir: **el menor de los dos**, el cumplimiento o el vencimiento del plazo concedido. Eso
es exactamente lo que hace falta para medir un plazo cualquiera. No hay dos mecanismos que
coordinar: hay uno solo, aplicado dos veces.

---

## Decisión

### A — La medida única

Un plazo es una sola medida. Dada la entrada del catálogo y el elemento donde se aplica,
produce cuatro fechas:

| Fecha | De dónde sale |
|---|---|
| **Disparo** | Fecha administrativa del documento que la entrada señala como origen del cómputo |
| **Vencimiento** | Disparo + valor del plazo, computado según el art. 30 LPACAP |
| **Cumplimiento** | Fecha administrativa del documento que acredita el cumplimiento, si existe |
| **Parada** | **La primera de tres: cumplimiento, vencimiento u hoy** |

La cuarta es la que resuelve todo, y las tres candidatas significan cosas distintas:

- gana el **cumplimiento** → llegó lo que se esperaba;
- gana el **vencimiento** → se agotó el plazo concedido y el procedimiento prosigue
  (art. 22.1.d in fine: *«En caso de no recibirse el informe en el plazo indicado,
  proseguirá el procedimiento»*);
- gana **hoy** → el plazo sigue corriendo, y mañana la cuenta será un día mayor.

Esta misma medida responde a las dos necesidades: para una tarea es «cómo va esta espera»;
para una suspensión, el intervalo suspendido va **del disparo a la parada**.

**Consecuencia directa: el tope existe por construcción.** Ninguna suspensión puede crecer
sin límite, porque su parada nunca pasa del vencimiento. #778 se cierra sin escribir lógica
de tope: se cierra porque el cálculo deja de ignorar el catálogo.

### B — El plazo de la solicitud

1. Se mide como cualquier otro plazo (entrada de nivel solicitud, disparo en el documento de
   solicitud).
2. Se recorren las tareas del expediente y se retienen las que tienen entrada de catálogo
   **marcada como suspensora**.
3. Cada una se mide igual, sin nada añadido, y aporta el intervalo `[disparo, parada]`.
4. Los intervalos que se solapan **se funden**: el art. 22 suspende «el transcurso del plazo
   máximo legal para resolver», en singular. Un reloj no se para dos veces (#788).
5. Los días hábiles de la unión se suman a la fecha de vencimiento de la solicitud.

De ahí salen sin código adicional: si el plazo está suspendido hoy (lo está si alguna tarea
suspensora sigue corriendo), desde cuándo lo está de forma continua (el inicio del bloque
fusionado que alcanza hoy, que puede ser anterior a la causa viva más antigua), y cuánto
tiempo lleva parado.

### C — Vocabulario del servicio

**Estado del plazo — cinco valores.** Los cuatro primeros ya existen; `CUMPLIDO` es nuevo.

| Valor | Cuándo |
|---|---|
| `SIN_PLAZO` | No hay entrada en el catálogo, o la hay pero el documento de disparo aún no existe |
| `EN_PLAZO` | Corriendo, con margen |
| `PROXIMO_VENCER` | Corriendo, quedan 5 días hábiles o menos (umbral de `DISEÑO_FECHAS_PLAZOS §2.4`) |
| `VENCIDO` | Sin cumplimiento, y el vencimiento ya pasó |
| `CUMPLIDO` | Llegó el documento que acredita el cumplimiento |

**«Cumplido fuera de plazo» no es un valor del vocabulario.** Se lee comparando las dos
fechas que el servicio ya devuelve (`cumplimiento > vencimiento`). El vocabulario no crece
por algo que es derivable sin ambigüedad.

**Las cuatro fechas acompañan siempre al estado**: disparo, vencimiento, cumplimiento (o
nada) y parada. Son el dato; el estado es la lectura cómoda de ese dato.

**Para el plazo de la solicitud, además**: si está suspendido hoy, desde cuándo, cuántos días
lleva acumulados, y la fecha de vencimiento ya con las suspensiones sumadas.

`suspendido` es un dato aparte y **no un valor del estado**, porque es ortogonal: un plazo
puede estar suspendido y a la vez próximo a vencer.

**El efecto del plazo** (silencio estimatorio, desestimatorio, caducidad…) no cambia: sigue
siendo un dato de la entrada del catálogo.

### D — El documento que cierra el plazo de una tarea vive en esa misma tarea

Cada plazo se abre y se cierra en el mismo sitio. La estructura FTT ya lo cumple en **todos**
los trámites con plazo, suspendan o no — verificado en `tramites_tareas_documentos`:

| Trámite | Espera | Disparo | Documento que cierra |
|---|---|---|---|
| `REQUERIMIENTO_SUBSANACION` | única | justificante (consumido) | `SUBSANACION` (producido) |
| `SOLICITUD_INFORME` | única | justificante (consumido) | `INFORME_114_RD1955` (producido) |
| `CONSULTA_SEPARATA` | única | justificante (consumido) | `RESPUESTA_ORGANISMO` (producido) |
| `SOLICITUD_COMPATIBILIDAD` | única | justificante (consumido) | `INFORME_COMPATIBILIDAD_AMBIENTAL` (producido) |
| `CONSULTA_TRASLADO_TITULAR` | única | justificante (consumido) | `RESPUESTA_TITULAR` (producido) |
| `CONSULTA_TRASLADO_ORGANISMO` | única | justificante (consumido) | `RESPUESTA_ORGANISMO` (producido) |
| `ANUNCIO_*` (BOE/BOP/BOJA/PRENSA) | 1ª, a la publicación | *(sin plazo — #789)* | `ANUNCIO_PUBLICADO` |
| `ANUNCIO_*` (BOE/BOP/BOJA/PRENSA) | 2ª, 30 días de exposición | `ANUNCIO_PUBLICADO` (consumido) | `CERT_PLAZO_CUMPLIDO` (producido) |
| `TABLON_AYUNTAMIENTOS` | única | `CERT_PLAZO_TABLON` (producido) | **el mismo documento** |

Ningún caso tiene el documento de cierre fuera de su tarea. Por tanto **desaparece el rescate
que hoy busca el documento de cierre en un trámite hermano** (`_TRAMITES_CIERRE` → `RECEPCION_INFORME`, `RECEPCION_DICTAMEN`). Ese rescate nunca
cubrió una necesidad estructural: cubría que el tramitador hubiera archivado el documento en
otro sitio. Con esta decisión, eso es un dato mal puesto, no algo que el cálculo deba
compensar. Que `RECEPCION_INFORME` vuelva a consumir el mismo informe para analizarlo es
correcto y no cambia nada: el plazo lo cierra el vínculo de la espera.

Si en el futuro aparece una tarea con plazo cuyo documento de cierre viva necesariamente en
otro trámite, es un problema de modelado del ESFTT y se discute como tal — no se resuelve
añadiendo rescates al cálculo.

**Cómo lo sabe el catálogo:** la entrada gana un segundo señalador de documento, opcional,
con el mismo vocabulario cerrado que el de disparo (#788 §2.1). En casi todas es
`{"rol": "PRODUCIDO"}`. Si no se declara, el plazo nunca alcanza `CUMPLIDO` y se comporta
igual que hoy: solo puede estar corriendo o vencido.

**Es opcional por un caso real, no por prudencia.** En `TABLON_AYUNTAMIENTOS` el disparo y el
único candidato a cierre son el mismo documento: el certificado del ayuntamiento llega tarde
y trae consigo la fecha de exposición, con efecto retroactivo (#416). Esa entrada se queda
sin señalador de cumplimiento, y ahí `VENCIDO` se lee como «la exposición se completó», que
es lo que el tramitador necesita ver.

**Cumplir un plazo tiene dos lecturas y el vocabulario aguanta las dos.** En las esperas de
un tercero, el cierre puede llegar antes del vencimiento: alguien contestó. En las de mero
transcurso —los 30 días de exposición— el `CERT_PLAZO_CUMPLIDO` lo emite el propio sistema y
exige que el plazo haya vencido (`certificados.py`), así que la parada es siempre el
vencimiento y `CUMPLIDO` significa «está acreditado que el plazo transcurrió». Mismo
mecanismo, lectura distinta; el nombre del propio tipo documental ya recoge ambas.

### D bis — El cierre del plazo de la solicitud: `documento_cierre_id` y su certificado

El plazo de la solicitud no se cierra con la resolución dictada, sino con su notificación.
Art. 21.3.b: el plazo es para «resolver **y notificar**». Y el art. 40.4 fija con qué basta:

> «a los solos efectos de entender cumplida la obligación de notificar dentro del plazo
> máximo de duración de los procedimientos, será suficiente la notificación que contenga,
> cuando menos, el texto íntegro de la resolución, así como **el intento de notificación
> debidamente acreditado**»

Eso descarta `Fase(RESOLUCION).documento_resultado_id` como ancla de cierre: es la
resolución, y su fecha es la de dictar, anterior a la de notificar. Usarla daría a la
Administración más margen del que tiene. `documento_resultado_id` sigue siendo lo que es —el
cierre de la fase como unidad organizativa— y queda fuera de los plazos.

**`solicitudes` gana `documento_cierre_id`**, pareja de `documento_solicitud_id`: uno ancla la
fecha de inicio del plazo, el otro la de fin. Mantiene intacto el vocabulario cerrado de #788
—nivel solicitud por `fk`, nivel tarea por `rol`— sin introducir una tercera forma de
localización que navegue hasta una tarea tres niveles más abajo.

**Lo que se ancla ahí es un certificado de cierre de la solicitud, no un justificante de
notificación.** Con varios interesados hay varios intentos, y ninguno de ellos significa por
sí solo «la solicitud está cerrada»: anclar uno haría que la FK mintiera sobre lo que
representa. Además, «entender cumplida la obligación de notificar» es una valoración jurídica
—si el intento estaba debidamente acreditado, si contenía el texto íntegro—, y eso cabe en un
certificado y no en un justificante bruto. El certificado constata que respecto de **todos**
los interesados hubo notificación o intento acreditado, y su fecha administrativa es la del
último de ellos.

Hay precedente exacto de esta figura: `CERT_FIN_INSTRUCCION` y `CERT_FIN_IP_CONSULTAS`
aparecen en `tramites_tareas_documentos` **solo como ENTRADA** — ningún trámite los produce.
Son certificados de constatación de un hecho agregado, emitidos fuera del patrón
trámite→tarea. El de cierre de solicitud es el tercero de esa familia, con una diferencia que
conviene dejar escrita: #788 §9 dejó dicho que los `CERT_FIN_*` «no son anclas de ningún
plazo»; **este sí lo es**.

Dos consecuencias asumidas:

- **Su fecha administrativa es retroactiva** respecto de su emisión, como ya ocurre con
  `CERT_PLAZO_TABLON` (#416). El mecanismo existe.
- **`CUMPLIDO` pasa a depender de un acto manual.** Sin certificado emitido, la solicitud
  nunca lo alcanza y acabará marcándose vencida aunque se resolviera a tiempo. Es el mismo
  comportamiento que una fase en `PDTE_CIERRE` —todo hecho, falta formalizar— y como señal es
  la correcta, pero es decisión, no efecto colateral.

**Punto abierto:** dónde nace ese certificado en la estructura FTT. Sus dos hermanos no los
produce ninguna tarea; si sigue el mismo patrón, tampoco.

> **Resuelto a medias en #778 (2026-08-21).** El issue implementó el **ancla** —la
> columna `documento_cierre_id`, el tipo documental `CERT_CIERRE_SOLICITUD` y su
> lectura por el servicio— y dejó fuera **la emisión**: quién crea ese certificado
> y en qué momento. Consecuencia asumida mientras tanto: el plazo de la solicitud
> no puede alcanzar `CUMPLIDO` y acabará marcándose vencido aunque se resolviera a
> tiempo. Es la misma señal que una fase en `PDTE_CIERRE` —todo hecho, falta
> formalizar— y no afecta a lo que #778 vino a arreglar, que es el plazo que no
> vencía nunca.

### E — Qué plazos suspenden es dato del catálogo, no una lista en el código

La entrada del catálogo declara si ese plazo suspende el plazo de la solicitud. Desaparece
`_TRAMITES_SUSPENSION`.

Aplicando el test de ADR-037: el hecho de que la solicitud de un informe preceptivo suspenda
el plazo para resolver **cambia cuando cambia la ley** y es citable a un artículo concreto
(art. 22.1.a y 22.1.d). No es taxonomía propia ni imposibilidad lógica: es dato normativo, y
va donde ya viven el valor del plazo y su efecto.

Corolario buscado: **un plazo sin entrada en el catálogo no suspende nada**. Hoy conviven un
trámite marcado como suspensor en el código y sin fila en el catálogo, con lo que el sistema
lo pinta como plazo no configurado a la vez que lo usa para mover la fecha límite de la
solicitud. Con esta decisión esa contradicción no puede existir.

### F — El valor del plazo es el del catálogo

Si la ley concede N días, el plazo es N días, y viene del catálogo. **No hay topes escritos
en el código.**

El art. 22.1.d añade que *«Este plazo de suspensión no podrá exceder en ningún caso de tres
meses»*. Ese límite recae sobre la suspensión, no sobre el plazo concedido al informante. En
la práctica no muerde: todos los plazos de informe que BDDAT maneja son de tres meses o
menos, así que la parada nunca los excede. Solo importaría si se diera de alta una entrada
suspensora con un plazo mayor — y eso se resuelve **avisando al dar de alta la entrada**, no
añadiendo lógica al cálculo.

Donde la letra y esta decisión pueden diferir —organismo con dos meses para informar que no
contesta: ¿la suspensión acaba a los dos meses o sigue hasta tres?— se adopta la lectura
**corta**: la parada es el vencimiento del plazo del catálogo. Da una fecha límite más
temprana y avisa antes, que es la dirección conservadora fijada en #796 al describir la
asimetría del riesgo (contar una suspensión que no existe oculta al tramitador que el
interesado ya puede recurrir; no contarla solo produce una alarma prematura).

### G — La interfaz del servicio tiene dos entradas

El servicio solo habla de las dos cosas que pueden tener plazo:

- **el plazo de una tarea**;
- **el plazo de una solicitud**, que ya incluye la suspensión.

Sin literales de nivel y sin niveles fantasma que siempre respondan «sin plazo». Cuando no
hay entrada en el catálogo, la respuesta es «no hay plazo», y el consumidor no tiene que
saber por qué.

**No hay entrada para el trámite.** Los dos consumidores que hoy preguntan por trámite
(`consultas_organismos.py`, `variables/calculado.py`) llegan con un trámite en la mano porque
el vínculo con el organismo cuelga de ahí, no porque el trámite tenga plazo. «Dame la tarea
de espera de este trámite» es una utilidad de navegación del árbol ESFTT, no una entrada del
servicio de plazos. La interfaz enseña el modelo: una función llamada «plazo de un trámite»
reintroduciría por la puerta de atrás el nivel que #788 eliminó.

---

## Consecuencias

**Se cae del código:** la lista de trámites que suspenden; la lista de trámites que cierran
la suspensión de otros; las tres tentativas encadenadas de cierre; la marca de «suspensión
abierta» guardada como dato —pasa a ser un estado derivado: hay suspensión viva si alguna
tarea suspensora está corriendo—; y el atajo por trámite.

**Se gana:** un solo motor; el tope por construcción; y la proyección a futuro casi gratis
—repetir el cálculo usando el vencimiento en vez de hoy da la fecha límite en el peor caso,
que es lo que #795 necesita.

**Hay que tocar fuera del servicio:**

- `solicitudes` gana la columna `documento_cierre_id` (migración), y el catálogo un tipo
  documental nuevo para el certificado de cierre de la solicitud.
- `estado_dominio._estado_esperar_plazo` gana una rama para `CUMPLIDO`. En la práctica no la
  alcanzará —solo se evalúa sobre esperas no ejecutadas, y una tarea con documento de
  cumplimiento está ejecutada—, pero debe ser explícita y no caer en el `else`.
- Las variables `estado_plazo` y `efecto_plazo` del motor dejan de despachar entre cuatro
  niveles: tarea, solicitud, y cualquier otra cosa sin plazo.
- Los dos consumidores que preguntan por trámite bajan a la tarea antes de preguntar.

**Riesgo asumido:** al pasar la marca de suspensión al catálogo, un trámite que hoy suspende
dejará de hacerlo hasta que exista su entrada. Es el comportamiento buscado —sin dato no hay
cómputo—, pero es un cambio de comportamiento y no solo de sitio del dato.

**La ausencia de datos no es un error.** Un plazo sin entrada en el catálogo es
incompletitud del sistema, no un caso a manejar: el servicio responde «no hay plazo» y nadie
tiene que preguntar más. El sistema debe funcionar igual de bien haya o no plazos definidos.

---

## Lo que este ADR no decide

- **Si la suspensión requiere acuerdo y comunicación al interesado** (#796). El art. 22.1
  dice «se **podrá** suspender» y el 22.1.d exige comunicar tanto la petición como la
  recepción. La suspensión sigue infiriéndose del árbol documental, como hasta ahora; #796
  engancha la acreditación encima de esta lógica ya correcta.
- **La proyección de plazos a futuro** (#795), que se apoya en esta medida pero es trabajo
  aparte.
- **El poblado del catálogo**: qué entradas faltan y con qué valores.

---

## Alternativas descartadas

**Añadir el tope como constante junto a la lista de trámites suspensores** (la vía que
proponía #778). Habría arreglado el síntoma dejando en pie los dos motores, y habría escrito
en el código un dato —cuánto dura un plazo— que el catálogo ya tiene. Además obliga a
mantener sincronizadas dos fuentes para el mismo hecho.

**Derivar el tope del plazo del `ESPERAR_PLAZO` sin marcar nada en el catálogo.** No
distingue un plazo que suspende de uno que no, que es precisamente la información que falta:
la información pública y los traslados al peticionario (arts. 126 / 127.3 RD 1955/2000)
tienen plazo y **no** suspenden — corren dentro del plazo de la solicitud y lo consumen.

**Mantener una entrada del servicio por trámite, como comodidad.** Descartada en G: la
interfaz enseña el modelo.

---

## Cómo quedó implementado (#778, 2026-08-21)

Los nombres y decisiones de detalle que el ADR no fijaba, para que el código y este
documento se lean juntos sin sorpresas:

| Decisión del ADR | Cómo se llama en el código |
|---|---|
| Marca de suspensión (§E) | `catalogo_plazos.suspende_plazo_solicitud`, con `CheckConstraint` al nivel TAREA |
| Segundo señalador de documento (§D) | `catalogo_plazos.campo_fecha_cumplimiento` (`JSON`, no `JSONB`: se lee entera y se compara en Python) |
| Las cuatro fechas (§A) | `fecha_disparo`, **`fecha_limite`**, `fecha_cumplimiento`, `fecha_parada` |
| Las dos entradas (§G) | `obtener_estado_plazo_tarea` · `obtener_estado_plazo_solicitud` |
| Bajar del trámite a su espera (§G) | `Tramite.tarea_espera`, property del modelo |

**El vencimiento conserva el nombre `fecha_limite`.** Es como lo llama todo el sistema
—árbol, cola, certificados, front— y `DISEÑO_FECHAS_PLAZOS §3.5` ya tenía cerrada su
semántica: último día hábil dentro del plazo. En el nivel solicitud llega ya con las
suspensiones sumadas, y `fecha_limite_sin_suspender` conserva el valor base.

**`dias_restantes` es `None` en `CUMPLIDO`.** «Quedan N días» no significa nada una vez
cumplido, y el Inspector lo pinta literalmente. Si llegó tarde o a tiempo se lee de las
fechas, como dice §C.

**`estado_dominio._estado_esperar_plazo` mapea `CUMPLIDO` a `PENDIENTE_TRAMITAR`.** La rama
no se alcanza con las entradas pobladas —el documento de cumplimiento es el PRODUCIDO, y una
tarea con producido está ejecutada, luego ya devolvió `FIN`—, pero sí sería alcanzable si
una entrada declarase el cumplimiento con rol `CONSUMIDO`: llegó el documento y la tarea no
lo ha producido, que es trabajo pendiente, no espera.

**Traslado del dato, no poblado.** La migración `778b` marcó como suspensoras las tres
entradas que la lista del código ya trataba como tales y tienen fila
(`REQUERIMIENTO_SUBSANACION`, `SOLICITUD_INFORME`, `CONSULTA_SEPARATA` ×2), y puso
`{"rol": "PRODUCIDO"}` como cumplimiento en todas las de nivel TAREA salvo el tablón.
`SOLICITUD_COMPATIBILIDAD` dejó de suspender por no tener fila: es el corolario buscado
en §E, y es un cambio de comportamiento real, no solo de sitio del dato.
