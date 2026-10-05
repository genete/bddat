# Análisis de las notificaciones a entidades — BDDAT

> **Qué es esto:** una **foto de la situación a 2026-10-05**, no una decisión ni un diseño.
> Describe a quién se notifica, con qué dirección y en qué momento del procedimiento, tal
> como lo hace hoy el código, y lo contrasta con lo decidido (ADR-051 y ADR-052). No se
> mantiene: cuando cambie el código quedará desfasado. La fuente de verdad de lo decidido
> sigue siendo [ADR-051](../decisiones/ADR-051-destinatario-de-toda-notificacion.md) y
> [ADR-052](../decisiones/ADR-052-notificacion-edictal.md).
>
> **Método:** lectura del código (`app/models/direccion_notificacion.py`,
> `app/services/notificaciones.py`, `app/services/destinatarios_notificacion.py`,
> `app/services/mutaciones_arbol.py`, `app/services/escritos.py`,
> `app/modules/entidades/routes.py`), de las migraciones 967, 968, 969, 989 y 568 y de los
> ADR. El catálogo de la sección 4 se consultó en la BD de tests, sembrada desde las
> migraciones (32 filas). Los 61 tests de `test_300_direccion_titular.py`,
> `test_967_destinatario_notificacion.py` y `test_968_fuentes_destinatarios.py` pasan.
> **No se ha generado ningún escrito real ni se ha probado la interfaz.** Lo marcado
> «por lectura» no se ha reproducido en ejecución.
>
> **Estado de las piezas que faltan (a la fecha):** #929 (interfaz de notificaciones), #431
> (propietarios DUP) y #432 (reconocimiento de interesado) están abiertos.

---

## 1. Resumen

- Las notificaciones salen de **una tarea `NOTIFICAR` por destinatario**. La fila de
  `notificaciones` guarda a quién se envía, en nombre de quién, y una **copia congelada** de su
  nombre, NIF, dirección, email, DIR3 y SIR.
- Cada notificación tiene una **fuente** (por qué se notifica: solicitante, organismo
  consultado, boletín…). El catálogo `notificacion_fuentes` dice qué fuentes puebla cada trámite.
  Nada se adivina: el destinatario sale de datos que rellenó el usuario.
- **El rol decide la dirección, salvo para el solicitante.** Para organismos, boletines y
  ayuntamientos se busca la dirección de la entidad con el rol de la fuente. Para el solicitante
  no hay búsqueda por rol: se usa la **sede indicada en la solicitud** o, si no hay, la **ficha**
  de la entidad (#989).
- **El sistema no elige canal.** El canal se deduce del justificante que se vincula después.
- Hay dos fuentes sembradas que hoy **nunca devuelven a nadie** (propietarios DUP e interesados
  reconocidos), y no hay interfaz para elegir destinatario ni para cambiar sede o representante
  desde el árbol.

---

## 2. Cómo se elige la dirección

Cadena de resolución (`destinatarios_notificacion.como_destinatario` y
`notificaciones.copiar_destinatario`):

1. **Dirección explícita** que fijó el usuario, si sigue activa: la sede de la solicitud
   (`solicitudes.direccion_notificacion_id`) o la del organismo
   (`organismos_expediente.direccion_notificacion_id`).
2. Si no hay, la **más reciente activa del rol de la fuente** (`notificaciones.direccion_de_rol`):
   consultado, publicador o titular. El solicitante no entra aquí.
3. Si no hay, los datos de la **ficha de la entidad** (`entidades.direccion`, `email`…).

DIR3 y SIR solo vienen de una dirección de notificación; la ficha no los tiene.

### 2.1. Dirección de notificación y roles

`direcciones_notificacion.tipo_rol` son bits: 1 titular, 2 consultado, 4 publicador,
combinables. Una dirección solo admite roles que la entidad tiene
(`modules/entidades/routes.py: _recoger_datos_direccion`). Una entidad con varias direcciones
del mismo rol no tiene un criterio propio de elección: «la más reciente» (ver 7.3).

### 2.2. Qué dirección usa cada fuente

| Fuente | De dónde sale la entidad | Dirección | Quién la decide |
|---|---|---|---|
| `SOLICITANTE` | La solicitud: su solicitante o su representante | Sede de la solicitud o ficha. Con representante, la ficha del representante | Alta de expediente o edición de la solicitud |
| `ORGANISMO_DEL_TRAMITE` | `tramites_organismos` | La elegida en la consulta o la más reciente de consultado | Quien edita el organismo |
| `ORGANISMOS_CONSULTADOS` | `organismos_expediente` de la solicitud, incluida la declaración responsable | Igual | Igual |
| `ORGANO_AMBIENTAL` | En su fase, `tramites_destinatario`; en la resolución, el de la fase ambiental | Más reciente de consultado | El usuario |
| `MINISTERIO`, `ORGANO_SUPERIOR` | `tramites_destinatario`, entre entidades con `rol_consultado` | Más reciente de consultado | El usuario |
| `BOLETIN`, `AYUNTAMIENTO` | `tramites_destinatario`, entre entidades con `rol_publicador` | Más reciente de publicador | El usuario |
| `PROPIETARIOS_DUP`, `INTERESADOS_RECONOCIDOS` | `interesados_expediente` | Más reciente de titular (provisional) | El usuario, cuando exista el alta (7.1) |

Una entidad que sale por dos fuentes (por ejemplo, Edistribución como solicitante y como
organismo consultado en el mismo expediente) recibe **dos notificaciones**, cada una con la
dirección de su rol (ADR-051 §D, «un rol, una notificación»). La clave de idempotencia es
(trámite, fuente, titular).

---

## 3. La sede

«Sede» tiene dos sentidos en el código.

### 3.1. La sede del solicitante (#989, ADR-051 §K)

- Una sociedad con un mismo NIF puede tener varias sedes con distinta dirección y correo
  (caso de Edistribución). Son filas suyas de `direcciones_notificacion` con rol titular.
- La solicitud guarda **cuál** (`solicitudes.direccion_notificacion_id`, opcional).
  `notificaciones.sede_invalida` exige que sea del solicitante, esté activa, tenga rol titular y
  no lleve otro NIF (con otro NIF sería otra sociedad). Sin sede, o si dejó de valer, se usa la
  ficha.
- Antes de #989 se tomaba la dirección de rol titular más reciente. Con varias sedes elegía por
  la fecha y no por la solicitud, y por eso se retiró (docstring de
  `escritos.ContextoBaseExpediente._direccion_titular`). El test
  `test_sin_representante_va_a_la_sede_de_la_solicitud` lo fija: sin sede indicada sale la
  ficha, aunque exista una dirección de titular más reciente.
- El **oficio** (la dirección del papel) va siempre al solicitante; la **notificación** (NIF y
  correo de aviso) va al representante si la solicitud lo tiene:

| Caso | Oficio | Notificación |
|---|---|---|
| Sin representante, sin sede | Titular, ficha | Titular, ficha |
| Sin representante, con sede | Titular, sede | NIF del titular, correo de la sede |
| Con representante, sin sede | Titular, ficha | NIF y correo del representante (su ficha) |
| Con representante, con sede | Titular, sede | NIF y correo del representante (su ficha) |

- El representante es siempre un autorizado activo del solicitante en `autorizados_titular`
  (`mutaciones_arbol.validar_representante`) y no tiene sede.
- Cambiar sede o representante (`mutaciones_arbol.editar_solicitud`) se admite siempre. Refresca
  las `NOTIFICAR` al solicitante que no han salido y avisa de las que ya salieron y de los oficios
  hechos con la sede anterior.
- Se fija en el alta de expediente (`/api/entidades/<id>/sedes` lista las válidas) y en el PATCH
  de la solicitud. El árbol React no tiene pantalla para cambiarlos.

### 3.2. La sede electrónica (art. 42.1 LPACAP, ADR-049)

Es otra cosa: la obligación paralela de poner a disposición en sede una notificación en papel
(`JUSTIFICANTE_SEDE`, `notificaciones.sede_justificacion`, `notificaciones.estado_sede`: PUESTA,
JUSTIFICADA o PENDIENTE). Solo aplica al canal POSTAL y no interviene en la elección de dirección.

---

## 4. Los momentos en que se envía un escrito a una entidad

Catálogo `notificacion_fuentes` (32 filas). Según ADR-051 §H, si el trámite tiene ELABORAR el
destinatario se decide al elaborar el escrito; si no, en la propia `NOTIFICAR`. Cuando la fuente
sale de datos del expediente no se elige: se calcula.

| Fase | Trámite (secuencia de tareas) | Fuente | A quién | De dónde sale / dónde se elige |
|---|---|---|---|---|
| ANALISIS_SOLICITUD | COMUNICACION_INICIO_ADMISION (E>N) | SOLICITANTE | Solicitante o su representante | Solicitud |
| ANALISIS_SOLICITUD | REQUERIMIENTO_SUBSANACION (E>N>EP>AN) | SOLICITANTE | Ídem | Solicitud |
| DATOS_CATASTRALES | REMISION_ACUERDO_DATOS, REQUERIMIENTO_CATASTRALES, TOMA_RAZON_RBDA | SOLICITANTE | Ídem | Solicitud |
| CONSULTAS | CONSULTA_SEPARATA, CONSULTA_TRASLADO_ORGANISMO | ORGANISMO_DEL_TRAMITE | Organismo ligado al trámite | `tramites_organismos` y `organismos_expediente` |
| CONSULTAS | CONSULTA_TRASLADO_TITULAR | SOLICITANTE | Solicitante o representante (el organismo es el asunto) | Solicitud |
| INFORMACION_PUBLICA | ANUNCIO_TITULAR (E>N) | SOLICITANTE | Solicitante o representante | Solicitud |
| INFORMACION_PUBLICA | RECEPCION_ALEGACION (AN>E>N>EP) | SOLICITANTE | Solicitante | Solicitud |
| INFORMACION_PUBLICA | ANUNCIO_BOJA (N>EP>EP) | BOLETIN | Boletín | En la NOTIFICAR (sin ELABORAR) |
| INFORMACION_PUBLICA | ANUNCIO_BOP (E>N>EP>EP) | BOLETIN | Boletín | Al elaborar |
| INFORMACION_PUBLICA | TABLON_AYUNTAMIENTOS (E>N>EP) | AYUNTAMIENTO | Ayuntamiento (rol publicador) | Al elaborar |
| CONSULTA_MINISTERIO | SOLICITUD_INFORME (E>N>EP) | MINISTERIO | Ministerio (rol consultado) | Al elaborar |
| COMPATIBILIDAD_AMBIENTAL | SOLICITUD_COMPATIBILIDAD | ORGANO_AMBIENTAL | Órgano ambiental | Al elaborar |
| FIGURA_AMBIENTAL_EXTERNA | SOLICITUD_FIGURA | ORGANO_AMBIENTAL | Ídem | Al elaborar |
| AAU_AAUS_INTEGRADA | REMISION_RESULTADO_IP_CONSULTAS, RECEPCION_DICTAMEN, RECEPCION_PROPUESTA_INF_VINC | ORGANO_AMBIENTAL | Ídem | Al elaborar |
| AAU_AAUS_INTEGRADA | DISCREPANCIA_INF_VINC | ORGANO_SUPERIOR | Órgano superior (rol consultado) | Al elaborar |
| RESOLUCION, RESOLUCION_AAP, RESOLUCION_AAC | NOTIFICACION (N) | SOLICITANTE, ORGANISMOS_CONSULTADOS, ORGANO_AMBIENTAL, INTERESADOS_RECONOCIDOS | Una `NOTIFICAR` por destinatario | Solicitud; consultas; fase ambiental; interesados (vacío) |
| RESOLUCION_DUP | NOTIFICACION (N) | SOLICITANTE, ORGANISMOS_CONSULTADOS, PROPIETARIOS_DUP, INTERESADOS_RECONOCIDOS | Ídem | Propietarios e interesados: vacío hoy |
| RESOLUCION, RESOLUCION_AAP | PUBLICACION (E>N>EP) | BOLETIN | Boletín | Al elaborar |
| RESOLUCION_DUP | PUBLICACION_BOE, PUBLICACION_BOJA, PUBLICACION_BOP (N>EP>EP) | BOLETIN | Boletín | En la NOTIFICAR |
| RESOLUCION_DUP | REQUERIMIENTO_RBDA_DEFINITIVA (E>N>EP) | SOLICITANTE | Solicitante o representante | Solicitud |
| RECONOCIMIENTO_INTERESADO | NOTIFICACION (N) | SOLICITANTE | Quien pidió ser interesado | Su solicitud |
| 13 fases (transversal) | NOTIFICACION_EDICTAL (E>N>EP) | BOLETIN | El BOE | Al elaborar (`tramites_destinatario`). Anuncio común; las copias por interesado, por una acción (ADR-052 §G) |

Abreviaturas: E = ELABORAR, N = NOTIFICAR, EP = ESPERAR_PLAZO, AN = ANALIZAR.

Fuera del catálogo:

- `ANUNCIO_BOE`, `ANUNCIO_PRENSA` (los publica el titular, #964) y `PORTAL_TRANSPARENCIA` (#966)
  no tienen `NOTIFICAR`. No hay escrito a entidad en ellos.
- Una `NOTIFICAR` creada a mano en un trámite sin fuentes se resuelve a mano
  (`mutaciones_arbol._destino_sin_fuentes`): la fuente `SOLICITANTE` sola; las demás, con la
  entidad indicada y la dirección de su rol.

### 4.1. Según el tipo de entidad

| Entidad | Cómo se le llega | Dirección |
|---|---|---|
| Titular o solicitante (sociedad, persona) | Fuente SOLICITANTE | Sede de la solicitud o ficha. NIF siempre el de la ficha |
| Representante (autorizado o apoderado) | Recibe la notificación en nombre del solicitante | Siempre su ficha |
| Organismo consultado | ORGANISMO_DEL_TRAMITE y ORGANISMOS_CONSULTADOS | La elegida en la consulta o la más reciente de consultado |
| Órgano ambiental, ministerio, órgano superior | Elegidos en el trámite | Más reciente de consultado |
| Boletín, ayuntamiento, BOE | Elegidos en el trámite | Más reciente de publicador |
| Propietario DUP, interesado reconocido | Fuentes propias | Más reciente de titular (provisional). Sin alta implementada |

`entidades.tipo_titular` (gran distribuidora, promotor…) no interviene en la notificación.

---

## 5. Canal

`notificaciones.canal` queda vacío hasta el primer justificante y se deduce del tipo de
documento vinculado (`notificaciones.canal_de_vinculos`; EDICTO si hay anuncio publicado sin otro
justificante). Los datos de contacto copiados (`dest_email`, `dest_dir3`, `dest_sir`) no los lee
ningún código salvo el eco en la API (`routes/api_expedientes.py`, payload de notificar). El
envío automático (ADR-021) no existe.

---

## 6. Qué cubre y qué bloquea el sistema

- **Sin destinatario, la `NOTIFICAR` no avanza** (no admite vínculos de documentos) salvo escape
  justificado en bitácora; tras el escape ya no se puede rellenar.
- **Sin destinatario elegido, el escrito no se genera** (trámites con ELABORAR).
- **Nadie falta ni sobra:** un trámite no termina mientras `destinatarios_notificacion` devuelva
  a alguien sin notificar o una notificación que sobra (ADR-051 §E).
- **La dirección se congela con el primer justificante.** Antes se refresca (botón «añadir los que
  faltan», cambio de sede o de representante).
- **Cotejo:** si el justificante trae NIF, se avisa si no coincide con la fila.

---

## 7. Lo decidido que no sale de la implementación

### 7.1. Decidido y sin implementar

1. **Roles nuevos de `tipo_rol` para propietarios e interesados** (ADR-051 §B y §C; #431 y
   #432). El CHECK sigue en `BETWEEN 1 AND 7` (tres bits).
2. **Propietarios DUP e interesados reconocidos no se rellenan nunca.** El único código que
   escribe en `interesados_expediente` crea o actualiza el origen `TITULAR`
   (`models/expedientes.py`, `services/alta_expediente.py`). Las dos fuentes están sembradas en
   las cuatro resoluciones y devuelven vacío sin error ni aviso (ADR-051 §C lo acepta: «una
   fuente sin nadie no añade tareas»).
3. **«Todo notificado es una entidad con dirección»** (ADR-051 §B, consecuencia aceptada). No se
   ha encontrado comprobación alguna (por lectura): `copiar_destinatario` copia lo que haya, y
   una entidad sin dirección de rol ni dirección en la ficha genera una notificación con
   `dest_direccion` vacío que avanza sin aviso.
4. **Interfaz de destinatarios** (#929): elegir destinatario, botón «añadir los que faltan»,
   fuente y destinatario en el árbol, representante y sede en el inspector. Existe el backend
   (`PUT …/notificar/destinatario`, `GET …/notificaciones`, `POST …/notificaciones/anadir_faltan`)
   y no la pantalla.
5. **Envío automático** (ADR-021): el ADR-051 dice que leerá de la fila a quién y adónde; la fila
   lo guarda y nadie lo lee.
6. **`notificacion_fuentes.norma`**: solo lleva los artículos leídos al diseñar; el resto, NULL
   (lo dice la migración 968).

### 7.2. Desajustes entre decisión y código (por lectura)

1. **`crear_organismo` no admite dirección.** El comentario de la columna
   `organismos_expediente.direccion_notificacion_id` dice «elegida al añadir el organismo», pero
   solo se fija después con `editar_organismo`.
2. **`editar_organismo` solo comprueba que la dirección exista**, no que sea del organismo, esté
   activa o tenga rol consultado. El desplegable (`esquema_editable._esquema_organismo`) filtra
   por entidad y bit consultado, pero no por `activo`. `como_destinatario` descarta una dirección
   inactiva, no una ajena.
3. **«La más reciente» no desempata.** `DireccionNotificacion.obtener_direccion_notificacion`
   ordena por `fecha_inicio DESC` (por defecto, la fecha del día) sin `id` como segundo criterio:
   dos direcciones del mismo rol dadas de alta el mismo día salen en orden indeterminado.
   Tampoco mira `fecha_fin`. Es el defecto que #989 corrigió para el solicitante y que sigue en
   consultado, publicador y propietarios.
4. **«Añadir los que faltan» pisa una dirección fijada a mano.** `fijar_destinatario` acepta un
   `direccion_id` por `NOTIFICAR` (la ruta PUT lo pasa), pero el botón recalcula con
   `como_destinatario` y, mientras no haya justificante, vuelve a la dirección del dato de origen.
   El ADR-051 (2026-09-29) descartó la corrección «una a una» como solución a la sede, y el
   parámetro sigue en el código.
5. **`editar_direccion` sobrescribe la fila** (`modules/entidades/routes.py`). El historial solo
   se conserva si se desactiva y se crea otra. Es la razón por la que ADR-051 copia la dirección
   en la notificación.

---

## 8. Presentación POC: la frase sobre direcciones por rol

La diapositiva `presentaciones/poc/slides/s05b_feat_entidades.md` (bullet 6, y
`presentaciones/poc/index.html`) dice: «Cada entidad puede tener además distintas direcciones de
notificación según el rol que desempeña: e-distribución como titular recibe los escritos en su
departamento de tramitaciones; como empresa consultada, en su área técnica. El sistema sabe
siempre a quién dirigirse — y en qué canal.»

| Afirmación | Contraste |
|---|---|
| Distintas direcciones según el rol | Cierto (2.1) |
| Como consultada, en su área técnica | Cierto (2.2) |
| Como titular, en su departamento de tramitaciones | **No describe el código.** Al solicitante no se le busca dirección por rol: sede de la solicitud o ficha (3.1) |
| «Recibe los escritos» | Impreciso: oficio y notificación van a destinatarios distintos si hay representante (3.1) |
| «Sabe siempre a quién dirigirse» | Cierto salvo huecos y las dos fuentes vacías (6, 7.1) |
| «Y en qué canal» | **Falso.** El canal se deduce después del justificante (5) |

Dos frases del popup de esa diapositiva tampoco son exactas: «El sistema usa siempre la más
reciente activa para el rol» (no para el solicitante ni para un organismo con dirección elegida)
y «Cambiar la dirección no elimina el historial» (`editar_direccion` sobrescribe; ver 7.2.5).

---

## 9. Límites de esta foto

- No se ha generado un escrito real (las plantillas de la BD de la nube apuntan a ficheros que no
  existen) ni abierto la interfaz.
- De los issues #431, #432 y #929 solo se ha leído el estado y el alcance.
- No se ha comprobado si las plantillas ODT usan ya `destinatario_*` en los encabezados (ADR-051
  §H lo deja como trabajo de plantillas).
