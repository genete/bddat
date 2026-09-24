# ADR-049 — Las dos fechas de una notificación, el cumplimiento del plazo de resolver y los certificados de cierre

**Estado:** Propuesta — decisiones de diseño tomadas el 19-20/09/2026 y revisadas el 21-22/09/2026 tras el cambio de paradigma «el plazo es del acto» (§E); redacción pendiente de revisión por Carlos
**Fecha:** 2026-09-21
**Depende de:** ADR-034 (tabla `notificaciones`) · ADR-036 (sellado de fase cerrada) · ADR-041 (plazos y suspensiones, medida única) · ADR-043 (`CERT_FIN_INSTRUCCION`) · ADR-046 y ADR-047 (fases `RESOLUCION_*`) · ADR-048 (plazo de fase finalizadora)
**Enmienda:** ADR-034 (§1, §5 y el `CHECK` de `resultado`) · ADR-008 · ADR-041 §D bis (el plazo de resolver es del acto y ya no se ancla a `documento_cierre_id`) · ADR-048 §A–§C (las filas de nivel FASE de `catalogo_plazos` se retiran: el plazo es del acto, no de la fase) · `DISEÑO_FECHAS_PLAZOS` (§3.2 y §5.1) · `TIPOS_DOCUMENTOS_CATALOGO` · `MODELO_ESTADOS_SEMAFORO`
**Origen:** #921 y #801 (superados: se cierran y se sustituyen por los issues de `PRE-ADR-notificacion-cumplimiento-certificados-cierre.md` §7)
**Material de trabajo:** [`docs/diseño/PRE-ADR-notificacion-cumplimiento-certificados-cierre.md`](../diseño/PRE-ADR-notificacion-cumplimiento-certificados-cierre.md) (tablas completas, afecciones y alternativas) · base legal en `docs/referencia/NORMATIVA_NOTIFICACION_FECHAS_EFECTOS.html` y `NORMATIVA_NOTIFICACION_CUMPLIMIENTO_PLAZO.md`. **El pre-ADR queda congelado:** donde difiera de este ADR (el plazo del acto, las siete filas, el reparto de N2 en N2 y N2b) manda este ADR; y la lista real de issues es la de los propios issues, no la tabla de su §7

---

## Contexto

#921 (cierre propio de las fases finalizadoras) y #801 (certificado de cierre de la solicitud) se plantearon para dar `CUMPLIDO` al plazo de resolver y notificar. Al diseñarlos juntos aparecieron cuatro huecos:

1. **Con quién se mide el cumplimiento.** El art. 21.2 LPACAP obliga a notificar la resolución en plazo, pero no precisa si basta el solicitante o hacen falta todos los interesados.
2. **Una notificación tiene dos fechas:** cuándo la Administración cumple su deber de notificar (art. 40.4) y cuándo la notificación surte efecto frente al interesado. BDDAT las confunde.
3. **Las fechas viven duplicadas** en tres sitios sin que nada las obligue a coincidir: la fila de `notificaciones`, la fecha del justificante y el contenido del PDF. Solo la del `Documento` la leen los plazos.
4. **El certificado de cierre mezcla dos preguntas** con fechas y momentos distintos: «¿se notificó al titular a tiempo?» y «¿está hecho todo lo obligatorio?».

Además, #921 llevaba dentro el mecanismo de notificación multi-destinatario, que `RESOLUCION_DUP` necesita (ADR-046 §C) y que nada implementa todavía.

**Cambio de paradigma (21/09/2026).** Al diseñar cómo medir el cumplimiento apareció que el plazo de resolver no es de la solicitud (supuesto heredado de #788) ni de la fase finalizadora (ADR-048), sino de cada **acto**. Una solicitud `AAP+AAC+DUP` pide tres autorizaciones, cada una con su artículo, su plazo (3, 3 y 6 meses) y su fase resolutora; un plazo del contenedor no puede ser correcto para actos con plazos distintos. Ver §E.

---

## Decisión

### A — El cumplimiento se mide con el solicitante

La fecha de cumplimiento de la obligación de resolver y notificar en plazo se justifica con la notificación **al solicitante/titular**, no a todos los interesados. Solo en procedimientos iniciados a solicitud.

Es un criterio razonado **sin precedente directo, con confianza media**: la LPACAP no lo precisa (arts. 21.2, 24.1, 25.1, 40.4, 43.3) y el informe de jurisprudencia no encuentra sentencia directa; se apoya en la analogía con la caducidad y en la doctrina de «constancia externa». **Silencio de la DUP: desestimatorio** (art. 24.1 párr. 2 con el art. 56.2 de la Ley 24/2013, extendido a la propiedad privada por el art. 33.3 CE; y la DA 3.ª de la Ley 24/2013, cuya lectura, «se podrán entender desestimadas», es a valorar). No hay norma andaluza propia: se aplica la estatal.

### B — Las fechas solo salen de documentos

**Regla:** toda fecha con valor legal de una notificación es la `fecha_administrativa` de un documento del expediente. Si el hecho no tiene documento, no hay fecha.

- `notificaciones` deja de guardar `fecha_puesta_disposicion` y `fecha_resultado`. Guarda quién (destinatario), cómo (canal) y qué resultó.
- **Los documentos solo se asocian a las tareas** (`CONSUMIDO` o `PRODUCIDO`), nunca a otra entidad ni con roles «de significado». Lo que acredita lo dicen su tipo y su posición (fase → trámite → tarea). Excepción ya existente y aceptada: los certificados, anclados a fase o solicitud.
- Los documentos de puesta a disposición, los acuses de intento y el de sede se vinculan a la tarea `NOTIFICAR` como **`CONSUMIDO`**, porque son presupuesto del `PRODUCIDO` (el justificante final). No hay rol nuevo ni tabla de vínculo nueva. Vincularlos solo a `notificaciones` no vale: quedarían como huérfanos y sin carpeta ESFTT, que se fija con la primera vinculación a una tarea.
- **Tipos nuevos** (convención `JUSTIFICANTE_<CANAL>_<HITO>`): `JUSTIFICANTE_NOTIFICA_DISPOSICION`, `JUSTIFICANTE_POSTAL_1ER` y `JUSTIFICANTE_SEDE` (nombre a confirmar). No hay tipo para el 2.º intento postal.
- **`tramites_tareas_documentos` admite varias entradas por paso** (clave sustituta más índice único, en lugar de la clave `(tipo_tramite_id, orden_tarea, rol)`), para declarar los tipos nuevos junto a `RESOLUCION`.
- **Registrar una notificación exige su documento.** Se acaba el «registrar envío» sin fichero. En POSTAL, hasta que llegue el acuse, la tarea queda «pendiente de notificar».
- Un mismo PDF polivalente (el final de Notifica lleva las dos fechas; los acuses de Correos del 1.º y 2.º intento salen probablemente juntos) se sube dos veces con tipos distintos: el pool lo permite (mismo contenido, un fichero, dos filas `Documento`).
- **`Notificacion.documento_id` se mantiene** (hará falta en el caso multi-destinatario).
- **BDDAT no verifica el carácter del documento** (correcto o fallido): el tipo dice qué es y la responsabilidad es del usuario. Un documento de justificante de envío anulado o fallido no entra en el expediente.

### C — Cálculo de las dos fechas

Un único servicio (`services/notificaciones.py`) lee `Documento.fecha_administrativa` con dos reglas uniformes, sin ramificar por canal:

- **Cumplimiento del titular** = la fecha **más antigua** entre sus documentos de puesta a disposición, acuse del 1.er intento, justificante final y anuncio. **No lee `notificaciones.resultado`.**
- **Efectos** = la fecha más antigua entre el justificante final y el anuncio, **solo si el resultado es CORRECTA o RECHAZADA** (art. 41.7). Con INCORRECTA no hay efectos.

| Caso (titular) | Cumplimiento | Efectos |
|---|---|---|
| NOTIFICA, «Leída» | `JUSTIFICANTE_NOTIFICA_DISPOSICION` (43.3) | `JUSTIFICANTE_NOTIFICA`: lectura (43.2 p. 1) |
| NOTIFICA, «Rechazada» o «Rechazada por transcurso de plazo» | La misma | `JUSTIFICANTE_NOTIFICA`: fecha del rechazo (41.5; 43.2 p. 2) |
| NOTIFICA, «Caducada» → INCORRECTA | La misma | Ninguna |
| POSTAL, entrega o rechazo al 1.er intento | `JUSTIFICANTE_POSTAL` | `JUSTIFICANTE_POSTAL` |
| POSTAL, 1.º fallido y 2.º correcto | `JUSTIFICANTE_POSTAL_1ER` (40.4) | `JUSTIFICANTE_POSTAL` |
| POSTAL, dos fallidos y edicto | `JUSTIFICANTE_POSTAL_1ER` | `ANUNCIO_PUBLICADO` (BOE, art. 44) |
| Edicto directo, sin intentos previos | `ANUNCIO_PUBLICADO` | `ANUNCIO_PUBLICADO` |
| Otros interesados | No aplica | Igual que arriba |
| BANDEJA / SIR | No aplica | El justificante: fecha única |

- **POSTAL.** Si el 1.er intento falla, su acuse (`JUSTIFICANTE_POSTAL_1ER`) se vincula como consumido; si es correcto, no se duplica como consumido y va solo el `JUSTIFICANTE_POSTAL` como producido. Si el 2.º es correcto es el definitivo; si no, edicto. `numero_intento` solo tiene sentido en POSTAL. El edicto (art. 44) puede abrirse **sin intentos previos** cuando se ignora el lugar de la notificación o el interesado es desconocido.
- **Si falta el acuse del 1.er intento**, el cumplimiento sale de la entrega del 2.º (más tardía): responsabilidad del usuario.
- **Puesta a disposición en sede (art. 42.1).** Obligación paralela de toda notificación en papel; no es una notificación y nunca produce rechazo presunto. Tres estados derivados: puesta (`JUSTIFICANTE_SEDE`), justificada (`sede_justificacion` con texto y constancia en bitácora) o pendiente. La pendiente impide cerrar el trámite. Es un invariante, no una regla del motor. Solo canal POSTAL.

### D — El resultado de la notificación

`resultado` es un dato **vivo** de la fila: nace vacío y cambia hasta un valor final, y su significado depende del canal. Pasa de {CORRECTA, INCORRECTA} a {CORRECTA, RECHAZADA, INCORRECTA}.

| Resultado | NOTIFICA | POSTAL | BANDEJA / SIR |
|---|---|---|---|
| **CORRECTA** | Acceso al contenido; efectos desde el acceso (43.2 p. 1) | Entrega al interesado o a mayor de 14 años en el domicilio (42.2) | Recepción: fecha única. Criterio de proyecto (ADR-034), sin norma específica de notificación |
| **RECHAZADA** | **Expreso**: fecha del rechazo, con obligación o no (41.5). **Presunto**: 10 días naturales sin acceso, si la vía es obligatoria o elegida (43.2 p. 2) | Solo expreso del interesado o su representante (41.5). No hay presunto en papel | No aplica: no consta ningún rechazo |
| **INCORRECTA** | Solo «Caducada» sin obligación ni elección acreditadas: no hay notificación practicada; otro medio (41.3 p. 2) o BOE (44) | Intento infructuoso. El 1.º **cumple** el 40.4 pero no practica; se repite una vez (42.2); el 2.º fallido va al BOE (44) | Envío que no llega: repetir. Sin caso documentado |

- **Se presume que, si la Administración usa el canal NOTIFICA, la vía es obligatoria o elegida.** «Obligada o elegida» describe al interesado (arts. 14 y 41.1), no al tipo de notificación. La puesta a disposición en sede queda fuera de esa presunción.
- **Mapeo de estados de Notifica-PNT:** Leída → CORRECTA; Rechazada y Rechazada por transcurso de plazo → RECHAZADA; **Caducada → INCORRECTA con aviso**, que el usuario pasa a RECHAZADA si consta que el interesado (o su representado) estaba obligado (14.2) o eligió lo electrónico; si el destinatario tiene NIF de entidad la obligación es cierta (14.2.a y b) y el parser propone RECHAZADA directamente. Anulada y No entregada **no entran en BDDAT**: se reintenta la notificación. Hoy el registro es manual; el parser completo se implementará después.
- **Verificado en 12 justificantes reales:** «Rechazada por transcurso de plazo» sale siempre con «Obligado a relacionarse electrónicamente: Sí» y «Caducada» siempre con «No»; el desenlace se registra siempre el día 11 de calendario (10 días naturales, no hábiles). El check de obligado lo marca el administrativo y a veces se olvida (una SL y una comunidad de bienes con «No»), así que «Caducada» **no prueba** que el destinatario no estuviera obligado.

### E — El plazo de resolver es del acto y su cumplimiento se calcula

El cumplimiento se separa del certificado de cierre. Alternativas descartadas: un solo certificado con la fecha del titular (no quita la falsa alarma de «vencido»: solo puede emitirse con todo hecho) y dos certificados con gesto sin distinguir su momento.

**La unidad del plazo es el acto**, no la solicitud ni la fase. Un acto es cada tipo atómico de la solicitud (`Solicitud.tipos_simples`: `AAP+AAC` son dos actos aunque se resuelvan juntos en una `RESOLUCION`; `AE_DEFINITIVA+AAT`, dos actos de 1 y 3 meses). Es un valor derivado, sin tabla. El plazo corre *desde* el escrito de la solicitud pero es *de* cada acto, y existe desde el día 1, antes de que exista la fase que lo resuelve (la finalizadora nace al final de la instrucción). La solicitud es un contenedor: no cumple ni incumple; la fase es el vehículo que resuelve uno o varios actos.

- **Qué fase resuelve cada acto** es un invariante en código con una sola fuente (`actos_solicitud`), de la que también se alimenta `informe_instruccion` para saber contra qué fases audita el certificado de fin de instrucción.
- El cumplimiento de un acto depende **solo** de que exista, vinculado a la tarea `NOTIFICAR` del trámite `NOTIFICACION` de la fase que lo resuelve, el documento correspondiente (regla de C). No lee `resultado`. Cada acto es independiente (sin agregación entre actos) y una misma notificación cumple el plazo de todos los actos que resuelve su fase, cada uno contra el suyo.
- **Cómo lo lee el motor:** clave nueva y explícita del vocabulario de `catalogo_plazos`, `campo_fecha_cumplimiento = {"calculado": "documento_cumplimiento"}`, para que `fk` siga significando clave foránea real. Rama nueva en `plazos._resolver_campo_fecha`, que solo acepta los nombres de una lista cerrada. **Siete filas** de `catalogo_plazos` —las atómicas de nivel SOLICITUD: `AAP`, `AAC`, `DUP`, `AAT`, `AE_PROVISIONAL`, `AE_DEFINITIVA` y `CIERRE`— pasan a esa clave (migración de datos). Las cuatro filas de combinación (`AAP+AAC`, `AAP+AAC+DUP`, `AAC+DUP`, `AE_DEFINITIVA+AAT`) y las tres de nivel FASE son consecuencia del supuesto «una solicitud = un acto» (las de combinación esconden que la DUP son 6 meses y la AAT 3): se retiran en un issue posterior, que también renombra el nivel SOLICITUD a ACTO. Hasta entonces `obtener_estado_plazo_solicitud` sigue leyéndolas.
- `documento_cumplimiento` es una propiedad del **acto**: el más antiguo de los documentos de cumplimiento del titular en la fase que lo resuelve. No hay propiedad en la solicitud ni en la fase.
- **Cadena completa:** sin certificado emitido se calcula en directo; con `CERT_CUMPLIMIENTO_FASE` emitido, el certificado guarda el `documento_id` elegido y quien pinta lo lee sin buscar. El plazo compara la fecha de ese documento con la fecha límite y da `CUMPLIDO`, cumplido fuera de plazo o `VENCIDO`. **Ese resultado nunca se guarda: se pinta siempre.**
- **Costes asumidos:** el plazo ya no apunta a un documento guardado sino que recorre acto → fase → trámite → tarea → documento mientras no hay sello (reinterpreta el criterio de ADR-041 §D bis de anclar con FK y no navegar); y la valoración del art. 40.4 deja de ser un gesto explícito para quedar implícita en subir el documento correcto.
- **Fila `NOTIFICAR` (40.2) del catálogo:** no se toca (dato de catálogo, hoy dormida; se reevalúa si al mostrarla en la interfaz el aviso miente o no sirve). Toda notificación debe cursarse en 10 días desde que se dicta el acto (art. 40.2), obligación distinta del plazo de resolver (21.2); la fecha de cumplimiento de C sirve a las dos. Queda sin decidir que esa fila cierra hoy con el documento producido por la tarea, que probablemente no es la fecha en que se *cursó* la notificación (hallazgo H15 del issue de N2).
- **La suspensión (art. 22) es por acto** y la trata #796; mientras tanto el plazo del acto ya trae los datos de suspensión en «sin suspender», de modo que #796 solo los rellena.

### F — Certificados

**Concepto.** Un certificado es un documento del expediente que no firma nadie del servicio ni viene de fuera: **constata** algo del expediente que no se entiende leyendo BDDAT directamente. Al emitirse **sella** lo que dice, y lo sellado no se toca. Mientras no hay sello se calcula; con sello se lee.

**Cada fase finalizadora tiene dos certificados:**

| | `CERT_CUMPLIMIENTO_FASE` | `CERT_CIERRE_FASE` |
|---|---|---|
| Qué constata | Que se notificó al titular; guarda el `documento_id` del documento de cumplimiento | Que está hecho todo lo obligatorio: es el cierre de la fase |
| Cuándo | En cuanto consta la notificación al titular | Cuando no queda nada pendiente; exige el de cumplimiento (cuenta sellos) |
| Gesto | Manual | Manual: informe «¿cómo voy?» siempre disponible; se consolida solo sin pendientes (patrón `cert_fin_instruccion`) |
| Dónde | Tabla `certificados`, por `(fase_id, tipo)` | Ocupa `Fase.documento_resultado_id` |
| Qué protege | El documento citado, su vínculo con la tarea y la tarea (la fase sigue abierta) | Nada nuevo: el sellado de ADR-036 |

- **`CERT_CIERRE_FASE` ocupa `documento_resultado_id`**: no hay `Fase.documento_cierre_id`. Siguen tal cual `finalizada`, `PDTE_CIERRE` y ADR-036. `reabrir_fase` pasa a deshacer el certificado con justificación. En las fases no finalizadoras no existe el de cumplimiento; extender el de cierre a ellas es posterior.
- **`CERT_CIERRE_SOLICITUD` no sella nada, solo cuenta sellos.** Si falta el de alguna fase finalizadora no se genera y se informa; si están todos, se genera, **enumera por acto** (fecha de solicitud, fecha de resolución, plazo y cumplimiento sí/no, según §E) y su PDF se vincula a `Solicitud.documento_cierre_id`. Se mantiene aunque el plazo lo den las fases: deja constancia escrita y tiene uso posterior como consumido de otras solicitudes. `CERT_FIN_INSTRUCCION` también se mantiene.
- **El certificado guarda solo el `documento_id`, no su fecha** (una sola fuente). El documento citado queda **protegido por completo** (fecha, tipo, fichero, desvinculación, borrado) mientras algún certificado emitido lo cite: el CRUD de documentos pregunta al servicio de certificados «¿me usa algún certificado?». Un `documento_id` dentro de un JSON no es clave foránea, así que lo protege ese servicio.
- **El certificado no tiene fecha propia:** su `Documento` va con `fecha_administrativa` nula, como los diagnósticos; el momento de emisión consta en `certificados.generado_en`.
- **Tabla (opción B).** Los certificados nuevos nacen en `certificados` ampliada (`tipo`, `fase_id`, índices únicos con tipo). Como máximo un certificado emitido por tipo y elemento. **El borrador no se guarda** (se calcula y se muestra); al emitir se guarda `datos`. El certificado se ve en una **vista HTML**, la misma para el borrador calculado y para el emitido (solo cambia de dónde salen los datos), con una huella al pie que lleva a su fila de `certificados`; su paso a PDF es posterior, por gesto del usuario o por el compilador del expediente (decisión de #947: un PDF generado al vuelo no es una foto fija de nada).
- **Ser certificado es tener fila en `certificados`, nunca la url** (#947). `Documento.url` dice dónde está el papel (hoy `bddat://certificados/N`, «no hay papel, se pinta»; con PDF, su ruta); la fila dice qué sella y no cambia al pasar a PDF. Todo código que necesite saber si un documento es un certificado pregunta por su fila. `CERT_FIN_INSTRUCCION` sigue en `certificados_fase` (su única ocupante) con su mecanismo propio y su sello (#838), que funcionan; unificarlo en `certificados` es un issue aparte. **Hecho en #932 (N3):** `tipo` (obligatoria, copia del tipo del documento) y `fase_id` (`ON DELETE RESTRICT`, sin `reformado_id`: las fases finalizadoras no se repiten por ronda), con un solo índice nuevo, `(fase_id, tipo)` parcial; los dos índices por `solicitud_id` de `CERT_FIN_IP_CONSULTAS` no se tocan. El backref es `Fase.certificados_cumplimiento`, porque `Fase.certificados` ya es de `CertificadoFase`. Lo demás de este punto es de N4.
- **Un único módulo de sellos**, con una función por tipo de certificado y un solo punto de comprobación, sin motor declarativo genérico. Se mantienen los punteros de ruta caliente (`documento_resultado_id`, porque `finalizada` se consulta en SQL).
- **«La tarea» se lee como «la tarea no puede desaparecer»** (#947, D4), que ya garantiza el borrado hoja a hoja (una tarea con vínculos o con `Notificacion` no se borra). El resto de la `NOTIFICAR` sigue editable, porque el certificado se emite en cuanto consta la notificación al titular, antes de que la notificación termine: en POSTAL, el 2.º intento y su acuse llegan después a la misma tarea; en NOTIFICA, la lectura o el rechazo. Consecuencia buscada: un justificante con fecha anterior vinculado después no cambia el cumplimiento; la vía es deshacer el certificado y volver a emitirlo.
- **Hecho en #947 (N4):** `CERT_CUMPLIMIENTO_FASE` (`datos = {"documento_id": N}`), `services/sellos.py` (el módulo único, que nace con este tipo) y `services/cert_cumplimiento_fase.py` (revisar, emitir y deshacer con justificación, solo con la fase abierta; emitir también con la fase cerrada). `notificaciones.documento_cumplimiento_fase` lee el sello antes de calcular, y el acto, el plazo y #922 lo heredan sin cambios. El documento citado queda protegido en el pool (fecha, tipo, url y borrado) y en `editar_tarea` (su vínculo con la tarea de la fase). El certificado de cierre de la fase (`CERT_CIERRE_FASE`) se partió a un issue propio, N4b.

### G — Efecto sobre los plazos del interesado

Los plazos del interesado cuentan desde la fecha de **efectos** (arts. 30.3, 68.1, 73.1). Hoy BDDAT los cuenta desde la puesta a disposición (el pool autorrellena esa fecha). Con B y C se corrige sin tocar los plazos: el justificante final lleva la fecha de efectos y ya es lo que leen.

Cambian solo los plazos que se notifican al titular por NOTIFICA o POSTAL: `REQUERIMIENTO_SUBSANACION`, `CONSULTA_TRASLADO_TITULAR` y `REQUERIMIENTO_RBDA_DEFINITIVA`; y `CONSULTA_SEPARATA` cuando va por Notifica. No cambian los de organismos por BANDEJA o SIR, las publicaciones ni `COMUNICACION_INICIO_ADMISION`.

---

## Consecuencias

- **BD:** `notificaciones` sin las dos fechas y con destinatario; `tipos_documentos` con cinco tipos nuevos (tres justificantes y los dos certificados de fase); `tramites_tareas_documentos` con clave sustituta; `certificados` ampliada; 7 filas de `catalogo_plazos` (las atómicas, de acto) a `calculado`, y la retirada posterior de las 4 combinaciones y las 3 filas de nivel FASE.
- **Backend:** servicio de fechas, el acto (`actos_solicitud`: fuente única de qué fase resuelve cada acto, con la propiedad `documento_cumplimiento`), rama `calculado` en `plazos.py` y plazo por acto (`plazos_de_la_solicitud`, una entrada por acto), módulo de sellos, servicios de cumplimiento y cierre (fase y solicitud), `Tramite.finalizado` y `_estado_notificar` aceptan RECHAZADA, contrato de `NOTIFICAR` (consume también los justificantes previos), autorrelleno del pool por tipo. Lista completa en los issues (el pre-ADR §6 está congelado y desfasado en lo del acto).
- **Documentación a corregir:** `DISEÑO_FECHAS_PLAZOS` §5.1 (`NOTIFICACION_DIAS` mezcla el 40.2 con el plazo máximo del 21.2); las citas del 21.3.b, que solo fija desde cuándo se cuenta el plazo, cuando lo de «notificarse la resolución» está en el 21.2 (ADR-041 §D bis, docstring de `Solicitud.documento_cierre_id`, #801, #921); `MODELO_ESTADOS_SEMAFORO` («plazo de lectura»); `NORMATIVA_PLAZOS` §1.1 («BDDAT las aplica siempre que concurren» contradice el «se podrá suspender», #796 y la práctica).
- **Issues:** los de la cadena del pre-ADR §7 (N1 a N9, más #568 ampliado y los existentes) sustituyen a #921 y #801, con N2 partido en N2 (aditivo) y N2b (retira lo antiguo y renombra el nivel SOLICITUD a ACTO), #796 ampliado (suspensión por acto) y #922 reescrito (barras por acto).

---

## Lo que este ADR no decide

- **La suspensión del plazo (art. 22).** El 22.1 dice «se podrá suspender» y el 22.1.d exige comunicar petición y recepción a los interesados. Lo trata #796 (por acto) y, en la práctica, no se suspende; el código sigue infiriendo la suspensión de cuatro filas del catálogo (`suspende = true`) como dejó dicho ADR-041. Lo decidido aquí vale para cuando se modele: la suspensión del 22.1.a arranca en la fecha de efectos del requerimiento y dura el menor entre el cumplimiento y el plazo concedido.
- **Si el art. 30.5 (último día inhábil, prórroga al primer hábil) se aplica al plazo de 10 días naturales del 43.2.** La plataforma Notifica-PNT no lo prorroga nunca (7 de las 12 muestras tenían el 10.º día en fin de semana). Es práctica de la plataforma, no criterio jurídico.
- **Cómo se liga cada justificante final a su destinatario** en el caso multi-destinatario, ni si sus justificantes individuales cuelgan de la tarea como consumidos del certificado múltiple.
- **Si se pueden seguir vinculando consumidos** cuando ya están todos los tipos de entrada del catálogo (hoy `editar_tarea` no lo limita).
- **La fecha de fin de fase al ampliar el certificado de cierre a otras fases:** `informe_instruccion._fecha_cierre` y `cert_fin_ip_consultas` leen `documento_resultado.fecha_administrativa` y la perderían con un certificado sin fecha; lo decide el issue que elimine esa fecha.
- El parser completo de Notifica-PNT, el frontend (`NotificarEditor`, sede, cierre), saber si un interesado está obligado o eligió lo electrónico, la notificación defectuosa (40.3), el acceso voluntario en sede (41.7), y los recursos y la firmeza.
- La unificación de `CERT_FIN_INSTRUCCION` en `certificados` y la regla general de documentos usados (issues aparte).

---

## Alternativas descartadas

- **Rol `ACREDITA` en `documentos_tarea`** y **vínculo propio documento↔`notificaciones`**: mezclan significado con flujo o cuelgan el documento de otra entidad.
- **Certificado único con la fecha del titular** y **dos certificados sin distinguir momento** (E).
- **El plazo de resolver en la solicitud** (un plazo único del contenedor) **o en la fase** (E): miden mal cuando los actos tienen plazos distintos (la DUP contra los 3 meses de la AAC), y la fase no existe durante la instrucción, que es cuando el reloj ya corre.
- **Entrada polimórfica en el catálogo** (pierde la exactitud de `RESOLUCION`) y **no declarar los tipos** (el radar de huérfanos deja de ayudar).
- **`Fase.documento_cierre_id` como columna nueva** (#921): se reutiliza `documento_resultado_id`.
- **Certificado de solicitud que sella la reapertura de fases**, y **guardar la fecha además del `documento_id`** en el certificado: retiradas.
- **Guardar el borrador y una columna `estado`** en `certificados`.
- **Unificar ya `certificados_fase` en `certificados`** (A) y **dejar los nuevos en `certificados_fase`** (C).
- **Reintento con varias puestas a disposición** (D2c): el documento de justificante de envío fallido no entra en el expediente y no hay escape justificativo.
- **Motor declarativo genérico de sellos:** sobreingeniería para cuatro o cinco tipos.
