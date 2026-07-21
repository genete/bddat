# ADR-034 — `notificaciones`: tabla de seguimiento del acto de notificar, no vitaminado de documento

**Estado:** Adoptada
**Fecha:** 2026-07-20
**Issues:** #657, #658
**Corrige/amplía:** ADR-008 (tabla `notificaciones` como documento vitaminado)
**Relacionado:** #655 (parser de justificante Notifica-PNT), ADR-005 (patrón documento vitaminado), ADR-032 (ingesta de documentos)

---

## Contexto

ADR-008 diseñó `notificaciones` como documento vitaminado 1:1 con un único `Documento`
(`UNIQUE(documento_id) NOT NULL`), siguiendo el patrón de ADR-005 (`diagnosticos` para
ANALIZAR). La sesión de planificación de #657/#658 (2026-07-20) revisó ese encuadre en
dos pasos.

### Paso 1 — el acto de notificar produce dos justificantes, no uno

Notifica-PNT entrega **dos documentos en momentos distintos** del mismo envío:

1. **Justificante de puesta a disposición** — inmediato al enviar, antes de que el
   destinatario lo lea.
2. **Justificante final** (Leída/Caducada/Rechazada/...) — cuando la notificación se
   resuelve.

Evidencia técnica (`D:\notifica-poc\notifica.py`): `Estado.PUESTA_A_DISPOSICION = "0"` es
un estado real e independiente en el catálogo de Notifica-PNT, y `descargar_informe()`
genera el mismo `Informe.pdf`/`InformeENI.xml` en cualquier momento del ciclo — mismo
formato, dos descargas posibles.

Esto ya estaba anotado sin llevarlo a schema, en el comentario de cierre de #655 y en el
planteamiento original de #658 (ambos citados en la versión anterior de este documento).

### Paso 2 — el justificante intermedio no debe ser un `Documento` del expediente

El justificante **final**, por sí solo, ya trae ambos datos temporales dentro de su
propio contenido — muestra real de #655: `"Puesta a disposición: 28/05/26 11:46"` y
`"Fecha de lectura: 01/06/26 11:16"` aparecen juntos en el mismo `Informe.pdf`. Una vez
que esos datos quedan capturados en `notificaciones`, el justificante intermedio no
aporta ningún valor administrativo propio que el definitivo no reconfirme — y LPACAP no
da cabida en el expediente a un documento que duplica al definitivo sin aportar nada
distinto. En la práctica, el equipo raramente descarga siquiera ese justificante
intermedio — lo único que se usa de él es la remesa.

### Paso 3 — corrección de encuadre: no es un vitaminado de documento

ADR-005 (patrón "documento vitaminado", `diagnosticos`) asume un documento **inmutable**
al que se le añade estructura fija. `notificaciones` no encaja ahí: `resultado` y
`numero_intento` son mutables a lo largo de la vida del acto de notificar — no son un
atributo fijo de un documento concreto. `notificaciones` es, en realidad, una tabla de
**seguimiento de proceso ligada a la tarea** (mismo tipo de patrón que otras tablas de
seguimiento del proyecto que anclan por `tramite_id`/`tarea_id`, no por `documento_id`) —
el documento es, como mucho, una evidencia que puede o no estar presente en cada momento,
nunca el ancla de la fila.

Consecuencia directa: sin una referencia propia a la tarea, la fila queda "coja" en
cuanto el documento deja de ser obligatorio — no habría forma de descubrir a la inversa
"¿qué está pasando con la tarea de NOTIFICAR de este trámite?" sin inventar una ruta
artificial (como subir el justificante intermedio solo para tener un `DocumentoTarea`
del que colgar la consulta, exactamente lo que el Paso 2 acaba de descartar).

---

## Decisión

### 1. El justificante de puesta a disposición nunca es un `Documento`

No se sube al pool, no se guarda en disco, no entra en el árbol ESFTT ni en `pool/`. Se
usa de forma transitoria: una acción **"registrar envío"** dentro de la propia tarea
NOTIFICAR (`NotificarEditor`, #657) donde el usuario adjunta el PDF/ZIP solo para
parsearlo en memoria (mismo parser de #655, mismo patrón sin persistencia que el
endpoint de preview del enganche 1 de subida al pool). Se extraen los datos, se escriben
en `notificaciones`, y el fichero se descarta — si el usuario quiere conservarlo fuera de
BDDAT, es cosa suya.

Este registro es **opcional**: si el usuario va directo a subir el justificante
definitivo sin pasar por aquí, no pasa nada — el definitivo trae todos los datos por sí
solo (Paso 2 del contexto).

### 2. `tarea_id` nuevo — la tarea es el ancla, no el documento

```sql
tarea_id INTEGER NOT NULL REFERENCES public.tareas(id) ON DELETE CASCADE
```

Toda fila `notificaciones` pertenece a una tarea desde el momento en que se crea, tanto
si nace del registro temprano (camino A) como del documento definitivo (camino B, más
abajo). El semáforo (`_estado_notificar`) pasa a consultar
`Notificacion.query.filter_by(tarea_id=tarea.id).first()` directamente, sin navegar por
`tarea.documento_producido`.

### 3. `documento_id` pasa a `NULLABLE`

```sql
documento_id INTEGER UNIQUE REFERENCES public.documentos(id) ON DELETE CASCADE
```

`UNIQUE` se mantiene (Postgres admite múltiples `NULL` en una columna única — no hay
conflicto). La fila puede vivir sin documento mientras se espera el definitivo (camino A)
y se completa cuando este llega (camino B).

### 4. `resultado` pasa a `NULLABLE`

```sql
resultado VARCHAR(12) CHECK (resultado IS NULL OR resultado IN ('CORRECTA', 'INCORRECTA'))
```

Sin resultado mapeable todavía (registro temprano, o justificante definitivo con estado
no reconocido) — no es `INDIFERENTE` (ADR-008 ya lo descartó explícitamente), es
"pendiente del definitivo".

### 5. Dos fechas, no una

- **`fecha_puesta_disposicion`** (`DATE NOT NULL`) — se conoce desde que existe fila,
  por cualquiera de los dos caminos.
- **`fecha_notificacion`** se renombra a **`fecha_resultado`** (`DATE`, nullable) — fecha
  del acto resuelto (lectura/caducidad/rechazo). Confirmado sin consumidores reales en
  código hoy (`grep` de `fecha_notificacion` solo aparece en la definición del modelo) —
  el rename no rompe nada existente.

### 6. Dos caminos de escritura, un solo punto de verdad: `tarea_id`

**Camino A — registro temprano (opcional).** Endpoint dedicado del `NotificarEditor`:
recibe el PDF/ZIP transitorio, lo parsea, crea `Notificacion(tarea_id=..., documento_id=None,
identificador_envio=remesa, canal=..., fecha_puesta_disposicion=..., resultado=None)`.

**Camino B — justificante definitivo.** La creación/actualización real de la fila ocurre
en el **hook de `editar_tarea`** (`mutaciones_arbol.py`), al fijar/cambiar
`documento_producido_id` en una tarea `NOTIFICAR` — no en el momento de subida al pool
(ahí todavía no se conoce a qué tarea pertenece el documento; vincular a tarea es un
paso posterior y separado, ADR-032). En ese hook:

- Parsear el documento producido (ya en disco).
- Buscar `Notificacion` por **`tarea_id`** (no por `identificador_envio` — `tarea_id`
  siempre se conoce aquí, es una clave de búsqueda más simple y no depende de que el
  parser haya reconocido nada).
- **Existe** (creada por el camino A) → actualizar `documento_id`, `resultado`,
  `fecha_resultado`. Cotejo: si `identificador_envio` ya registrado no coincide con la
  remesa recién parseada, aviso no bloqueante (posible asociación al justificante
  equivocado — el riesgo original que motivó #658).
- **No existe** (el usuario fue directo al definitivo) → crear la fila completa de una
  vez, con todos los datos que el propio definitivo aporta.

El enganche 1 de subida al pool (#657) queda reducido a **autorrelleno de UX**: mostrar
al usuario preview de lo detectado (útil, p. ej., para `fecha_administrativa` genérica
del `Documento`), sin escribir en `notificaciones` — la escritura real vive en el hook de
vinculación a tarea (camino B).

### 7. Schema resultante de `notificaciones`

```sql
CREATE TABLE public.notificaciones (
    id                        SERIAL PRIMARY KEY,
    tarea_id                  INTEGER NOT NULL
                                  REFERENCES public.tareas(id) ON DELETE CASCADE,
    documento_id              INTEGER UNIQUE
                                  REFERENCES public.documentos(id) ON DELETE CASCADE,
    identificador_envio       VARCHAR(30),
    resultado                 VARCHAR(12)
                                  CHECK (resultado IS NULL OR resultado IN ('CORRECTA', 'INCORRECTA')),
    canal                     VARCHAR(10) NOT NULL
                                  CHECK (canal IN ('NOTIFICA', 'BANDEJA', 'SIR', 'POSTAL')),
    fecha_puesta_disposicion  DATE NOT NULL,
    fecha_resultado           DATE,
    numero_intento            SMALLINT NOT NULL DEFAULT 1 CHECK (numero_intento IN (1, 2)),
    observaciones             TEXT
);
```

### 8. Semáforo — nuevo estado intermedio

`_estado_notificar` (`app/services/estado_dominio.py`) gana el estado que el propio
ADR-008 dejaba anotado como pendiente de implementación
(`PENDIENTE_RESULTADO_NOTIFICACION`):

| Consulta por `tarea_id` | Estado |
|---|---|
| Sin fila | `PENDIENTE_NOTIFICAR` (como hoy) |
| Fila con `resultado IS NULL` | `PENDIENTE_RESULTADO_NOTIFICACION` (nuevo) |
| Fila con `resultado = 'CORRECTA'` | `FIN` (como hoy) |
| Fila con `resultado = 'INCORRECTA'`, `numero_intento = 2` | `NOTIFICACION_AGOTADA` (como hoy) |
| Fila con `resultado = 'INCORRECTA'`, `numero_intento = 1` | `NOTIFICACION_FALLIDA` (como hoy) |

---

## Generalización a los otros canales (BANDEJA, SIR)

`notificaciones` es multipropósito (los 4 canales comparten tabla, ver ADR-008). El
diseño de este ADR se revisó contra el comportamiento real de los otros dos canales con
parser o registro previsible, para no dejar huecos.

### BANDEJA — encaja sin cambios de schema

La notificación es instantánea: en el momento en que se firma (o se envía directamente,
sin pasar por Portafirmas), el documento se remite electrónicamente y el destinatario ya
lo tiene en su sistema — a esos efectos, notificado. El estado interno `PENDIENTE` de
asignación a una persona en el organismo destino es irrelevante para LPACAP, igual que
asignar un expediente a un tramitador en BDDAT no altera la fecha de entrada.

Consecuencia: para BANDEJA **no existe un estado intermedio real** — un único acto
rellena `fecha_puesta_disposicion` y `fecha_resultado` a la vez (mismo instante). El
camino A (registro temprano) simplemente no se usa en la práctica para este canal; se va
siempre directo al camino B con todos los datos completos de una tacada. Ningún cambio
de schema necesario — el diseño de dos caminos ya admite "solo B, con todo relleno de
una vez" como caso particular.

El documento de BandeJA es parseable en principio (bien detectando el formato por
bifurcación interna del parser, bien porque el tipo de documento elegido en la subida ya
se lo indica) — **queda fuera de alcance de #657/#658** por falta de muestras reales
validadas (mismo motivo que ya recogía `MATRIZ_COBERTURA_BDDAT.md` para este canal). El
diseño no cierra la puerta: cuando exista un parser de BandeJA, se conecta exactamente en
el mismo punto que hoy usa NOTIFICA (autorrelleno opcional en camino A/B), sin retocar el
schema ni el flujo.

### SIR (ARIES) — obliga a que el formulario funcione sin ningún fichero

No hay justificante descargable — los administrativos hacen una captura de pantalla de lo
que ARIES muestra; no se ha encontrado ninguna opción de "descargar justificante". Todo
el registro es manual, hoy y sin fecha prevista de automatización:

- **Camino A sin documento**: se anota a mano el `identificador_envio` (número de
  identificación del envío que ARIES ofrece en pantalla) y `fecha_puesta_disposicion`.
  Sin fichero que subir en este paso.
- **Camino B sin documento o con captura de pantalla como evidencia**: al certificarse la
  recepción, se anotan a mano `resultado` y `fecha_resultado`. La captura de pantalla
  puede subirse y vincularse como `JUSTIFICANTE_SIR`/PRODUCIDO por el mecanismo genérico
  de siempre (Despensa), pero **no dispara ningún autorrelleno** — es evidencia
  documental desacoplada de los datos de `Notificacion`, que el usuario sigue rellenando
  a mano en el mismo formulario.

Consecuencia de diseño para #657 (`NotificarEditor`): los dos formularios (registrar
envío / completar resultado) son **formularios manuales por defecto**, con el
autorrelleno por parser como mejora opcional encima, que solo aplica hoy a NOTIFICA. Dos
implicaciones concretas:

1. **`canal` no siempre se deriva de un documento.** La derivación automática desde
   `tipo_doc.codigo` (§6) solo aplica cuando hay fichero de por medio. El formulario de
   registro temprano necesita un selector explícito de `canal` para cuando no hay ningún
   documento (SIR, siempre).
2. **La vinculación del documento producido queda desacoplada de rellenar
   `Notificacion`.** Son dos acciones independientes que pueden ocurrir en cualquier
   orden: vincular el documento (Despensa, mecanismo genérico ya existente) y completar
   los datos de la notificación (`NotificarEditor`). Para NOTIFICA/futuro BANDEJA
   coinciden en la práctica porque el parser rellena ambas cosas a la vez; para SIR no.

---

## Por qué

- **Sin `Documento` intermedio**: coherente con LPACAP (el expediente no lleva piezas que
  duplican al definitivo sin aportar nada distinto) y con la práctica real del equipo
  (rara vez se descarga ese justificante; lo único que se usa es la remesa).
- **`tarea_id` como ancla**: sin él, la fila es indescubrible a la inversa en cuanto el
  documento deja de ser obligatorio — forzaría a inventar un vínculo artificial
  (justo lo que el punto 1 evita).
- **Búsqueda por `tarea_id` en vez de `identificador_envio`** en el camino B: más simple
  y siempre disponible, no depende de que el parser haya reconocido el documento.
  `identificador_envio` pasa de "clave de búsqueda" a "campo de cotejo" — su función
  original (detectar asociación al expediente equivocado, motivo real de #658) se
  cumple igual, mediante comparación explícita en vez de mediante `WHERE`.
- **Registro temprano opcional**: el dato relevante (remesa) puede anotarse en cuanto se
  conoce, sin bloquear el flujo si el usuario prefiere ir directo al justificante final.

---

## Consecuencias

- La migración de #418 no se toca (ya aplicada); esta es una migración incremental sobre
  `notificaciones`.
- `Tarea.resultado`, `Tramite.finalizado`, `_check_finalizar_fase`/
  `_check_finalizar_tramite` (hoy navegan `documento.notificacion`) pasan a consultar por
  `tarea_id` — cambio de ruta de acceso, mismo dato.
- #657 (enganche 1, subida al pool) se simplifica: sin escritura en `notificaciones`,
  solo preview/autorrelleno de metadatos del propio `Documento`.
- #657 (enganche 2, `NotificarEditor`) gana el formulario de registro temprano (camino A)
  además del backstop ya previsto (canales sin parser, corrección posterior).
- El hook de cotejo (#658) vive en `editar_tarea`, disparado al fijar/cambiar
  `documento_producido_id` en una tarea NOTIFICAR — sustituye al diseño anterior de
  "upsert por `identificador_envio` en la subida al pool".

---

## Alternativas descartadas

### A. Mantener el justificante intermedio como `Documento` real, desvinculado tras el definitivo

Descartada por Carlos: no resuelve el problema de fondo (sigue siendo una pieza que entra
al expediente sin aportar valor distinto del definitivo, aunque se saque después del
árbol de la tarea) y añade complejidad de limpieza sin necesidad.

### B. `identificador_envio` como clave de búsqueda del upsert (versión anterior de este ADR)

Descartada al introducir `tarea_id`: obligaba a que el parser reconociera el documento
para poder localizar la fila a actualizar. Con `tarea_id` disponible siempre en el
momento de vinculación, la búsqueda es directa y `identificador_envio` queda libre para
su función real — el cotejo.

### C. Dos filas en `notificaciones` (una por documento)

Descartada — ver ADR-008 y la versión anterior de este documento: el acto de notificar es
conceptualmente uno.

### D. Persistir la remesa esperada en un campo manual sobre la tarea, capturado al enviar

Descartada — el justificante de puesta a disposición ya aporta el mismo dato sin
necesidad de un campo de anotación manual separado.
