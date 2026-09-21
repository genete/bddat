# PRE-ADR — Las dos fechas de una notificación, el cumplimiento del plazo de resolver y los certificados de cierre

> **Naturaleza de este documento:** Material preparatorio. Recoge las decisiones de diseño
> tomadas en las sesiones del 19 y 20 de septiembre de 2026 y lo verificado contra código y
> catálogos estructurales (los datos operacionales de la BD no se usan como evidencia). No
> está implementado. El output será un ADR formal (candidato a **ADR-049**, siguiente libre
> tras ADR-048) y la redefinición de #921 y #801.

**Estado:** Decisiones de diseño cerradas (19-21/09/2026); ADR-049 redactado como propuesta; issues por crear
**Fecha:** 2026-09-20
**Disparador:** «Próximo» de `CONTEXTO_ACTUAL.md` tras cerrar #892 — diseñar #921 y #801 en la misma sesión
**ADR formal:** [`ADR-049`](../decisiones/ADR-049-fechas-notificacion-cumplimiento-certificados-cierre.md) (redactado el 21/09/2026, pendiente de revisión). Este documento queda como material de trabajo: tablas completas, afecciones e issues (sección 7)
**Enmendaría:** ADR-034 (§1 y §5) · ADR-008 · ADR-041 (§D bis) · ADR-048 (§B) · `DISEÑO_FECHAS_PLAZOS` · `TIPOS_DOCUMENTOS_CATALOGO` · `MODELO_ESTADOS_SEMAFORO`
**Base legal (versionada en `docs/referencia/`):** [`NORMATIVA_NOTIFICACION_FECHAS_EFECTOS.html`](../referencia/NORMATIVA_NOTIFICACION_FECHAS_EFECTOS.html) (LPACAP arts. 37-46, más 21, 22, 24, 25 y 30) y [`NORMATIVA_NOTIFICACION_CUMPLIMIENTO_PLAZO.md`](../referencia/NORMATIVA_NOTIFICACION_CUMPLIMIENTO_PLAZO.md)
**Origen del contenido:** versiones 1 a 6 de un documento de trabajo no versionado (`docs_prueba/temp/analisis_dos_fechas_notificacion_bd_backend*.md`). Los cuerpos de #921 y #801 quedan superados en lo que se indica en la sección 7.

**Marcas:** ✔ decidido por Carlos · ◇ propuesta derivada, sin ratificación expresa (revisar al formalizar el ADR).

---

## 1. El problema

#921 (cierre propio de las fases finalizadoras) y #801 (certificado de cierre de la solicitud) se plantearon para dar `CUMPLIDO` al plazo de resolver y notificar. Al diseñarlos juntos aparecieron cuatro huecos que no estaban en ninguno de los dos:

1. **Con quién se mide el cumplimiento.** El art. 21.2 LPACAP obliga a resolver *y notificar* en plazo, pero no precisa si basta notificar al solicitante o hay que notificar a todos los interesados.
2. **Una notificación tiene dos fechas**, no una: cuándo la Administración cumple su deber de notificar y cuándo la notificación surte efecto. BDDAT las confunde.
3. **Las fechas viven duplicadas** en tres sitios sin que nada las obligue a coincidir (sección 2.1), y solo una se usa.
4. **El certificado de cierre mezcla dos preguntas** que no tienen la misma fecha ni el mismo momento: «¿se notificó al titular a tiempo?» y «¿está hecho todo lo obligatorio?».

Resolver los cuatro cambia el alcance de #921 y #801 (sección 7) y obliga a tocar el contrato de `catalogo_plazos`.

---

## 2. Cómo funciona hoy (verificado)

### 2.1 Fechas de una notificación

| Dato | Quién lo rellena | ¿Lo usa algo? |
|---|---|---|
| `notificaciones.fecha_puesta_disposicion` (obligatoria) | El usuario al «registrar envío», con autorrelleno opcional desde un PDF parseado en memoria que se descarta (ADR-034 §1); o el hook al vincular el justificante final | **No.** Solo la pantalla, la API y el hook |
| `notificaciones.fecha_resultado` | El usuario, o el hook desde el PDF. Vacía en una notificación caducada | **No** |
| `notificaciones.resultado`, `numero_intento` | Usuario o parser | Sí: semáforo y guardianes de cierre |
| `Documento.fecha_administrativa` del justificante | El usuario al subirlo | **Sí**: es la única fecha que leen los plazos |
| `notificaciones.documento_id` | El hook, al fijar el `PRODUCIDO` | Solo la guarda del pool y el JSON de la API. **Es una copia** del `PRODUCIDO` |

- La misma fecha llega a vivir en tres sitios: la fila de `notificaciones`, la fecha del justificante y el contenido del PDF.
- Las dos fechas de `notificaciones` son informativas: quitarlas no rompe ningún plazo.

### 2.2 Vínculo documento–tarea y catálogo

- `documentos_tarea` solo admite los roles `CONSUMIDO` (0..N por tarea) y `PRODUCIDO` (0..1), con `CHECK` y dos índices únicos parciales. Son roles de flujo (entra o sale de la tarea), no de significado.
- La carpeta ESFTT de un documento se deduce de su **primera vinculación a una tarea** (`rutas_esftt.ruta_esftt_documento`, ADR-032 §3); sin ninguna lanza `ValueError`. El aviso de justificantes huérfanos (#738) y la guarda de borrado del pool también cuelgan de ese vínculo.
- `tramites_tareas_documentos` (catálogo de qué tipo de documento va en cada posición) tiene clave primaria `(tipo_tramite_id, orden_tarea, rol)`: **un solo tipo de entrada y uno de salida por paso**. La entrada de `NOTIFICACION`, `NOTIFICACION_ORGANISMOS` y `NOTIFICACION_INTERESADOS` es `RESOLUCION`; la salida es polimórfica. El catálogo es **orientativo**: lo consultan el radar de huérfanos, la sugerencia de tipo al subir, la pantalla del catálogo de plazos y el editor de tablas maestras, pero `editar_tarea` no valida contra él.

### 2.3 Certificados

- `certificados` (`Certificado`): equivalente de `Diagnostico`. Un registro por documento, contenido en `datos` (JSONB), ámbito por `solicitud_id` y `reformado_id`. Lo usan `CERT_PLAZO_CUMPLIDO` y `CERT_FIN_IP_CONSULTAS`, **sin PDF**: el documento es virtual (`bddat://certificados/{id}`). Su tipo se deduce del documento; dos índices únicos parciales por solicitud están pensados solo para `CERT_FIN_IP_CONSULTAS`.
- `certificados_fase` (`CertificadoFase`): guarda `CERT_FIN_INSTRUCCION`. Genera un PDF con reportlab en `AT-N/certificados/`, con un documento real que apunta al fichero, y una foto JSON de la auditoría del motor. El relato del informe solo está en el PDF.
- El `Documento` de un diagnóstico se crea **sin `fecha_administrativa`**; solo `DOC_PROYECTO` la exige.
- Los certificados citan hoy documentos así: `CERT_PLAZO_CUMPLIDO` uno (`documento_inicio_id`) y además **copia** dos fechas; `CERT_FIN_IP_CONSULTAS` ninguno, pero copia las fechas de fin de sus fases; `CERT_FIN_INSTRUCCION`, solo en el PDF. Hay fechas duplicadas sin protección.
- Cada certificado define a mano sus bloqueos en `invariantes_esftt.py`. El de `CERT_FIN_INSTRUCCION` impide abrir otra fase de instrucción y reabrir una cerrada, y lo lee de la FK `Solicitud.documento_fin_instruccion`. No hay un mecanismo genérico que lea lo que un certificado lista.

### 2.4 Cierre de fase y estado de la solicitud

- `Fase.finalizada` es `documento_resultado_id IS NOT NULL`; `PDTE_CIERRE` es «todos los trámites finalizados pero falta el documento de resultado». Una `NOTIFICAR` cuenta como finalizada solo con `resultado = CORRECTA`.
- Cerrada la fase, el sellado de ADR-036 bloquea cualquier mutación en su interior (`_check_mutar`); la única salida es `reabrir_fase` con justificación.
- `Solicitud.estado` es derivado: `RESUELTA*` cuando todas sus fases están finalizadas (ADR-036 §3). No hay acto de cierre de solicitud.
- `Solicitud` guarda tres anclas documentales: `documento_solicitud_id`, `documento_fin_instruccion_id` y `documento_cierre_id` (#778). Esta última nunca se llena todavía: nadie emite el certificado.
- Los consumidores de `Fase.documento_resultado` que lo leen como documento son pocos: `detalle_nodo`, `informe_instruccion._fecha_cierre`, `cert_fin_ip_consultas` (solo fases de instrucción) y el PATCH de `editar_fase`. El resto solo mira si es nulo.

### 2.5 Edición de documentos

`pool_editar_documento` permite cambiar tipo, fichero y `fecha_administrativa` de **cualquier** documento del expediente, esté o no vinculado a una tarea, sin `check_invariante` y sin bitácora (en lo leído). El sellado de ADR-036 no lo cubre: protege tareas, trámites y fases, no los metadatos del documento.

---

## 3. Principios

| # | Principio | Estado |
|---|---|---|
| P1 | **Las fechas con valor legal solo salen de documentos.** Si el hecho no tiene documento, no hay fecha; no se rellena a mano en otro sitio | ✔ |
| P2 | **Los documentos solo se asocian a las tareas** (`CONSUMIDO` o `PRODUCIDO`); no a otras entidades ni con roles «de significado». Lo que acredita lo dicen su tipo y su posición (fase → trámite → tarea). El expediente es el conjunto de documentos consumidos y producidos. Excepción ya existente y aceptada: los certificados, anclados a fase o solicitud | ✔ |
| P3 | **Un cumplimiento se demuestra con un certificado**, que constata algo que ocurre en el expediente y que BDDAT no puede leer directamente, y **sella** lo que dice. Sin sello se calcula; con sello se lee | ✔ |
| P4 | **Plazo cumplido no es fase completada.** Son hechos distintos, con momentos distintos | ✔ |
| P5 | **BDDAT no verifica el carácter del documento** (correcto o fallido). El tipo dice qué es; subir el equivocado es un error material del usuario y la interfaz debe decir expresamente qué se sube | ✔ |
| P6 | Ninguna fecha se guarda duplicada: se guarda la referencia al documento y se lee su fecha | ✔ |

---

## 4. Decisiones

### 4.1 Con quién se mide el cumplimiento del plazo (D0) ✔

La fecha de cumplimiento de la obligación de resolver y notificar en plazo se justifica con la notificación **al solicitante/titular**, no a todos los interesados. Solo en procedimientos iniciados a solicitud.

- La LPACAP no lo precisa (arts. 21.2, 24.1, 25.1, 40.4, 43.3). El informe `NORMATIVA_NOTIFICACION_CUMPLIMIENTO_PLAZO.md` no encuentra sentencia directa; medir con el solicitante es el criterio mejor fundado, por analogía con la caducidad y por la doctrina de «constancia externa». **Confianza media.** El ADR debe dejar constancia de que es un criterio razonado sin precedente directo.
- **Silencio de la DUP: desestimatorio**, por dos vías que convergen: (1) art. 24.1 párr. 2 con el art. 56.2 de la Ley 24/2013, extendido a la propiedad privada por el art. 33.3 CE; (2) la DA 3.ª de la Ley 24/2013, que el catálogo ya cita para 132 bis y 132 ter (esta segunda, lectura a valorar en el ADR: dice «se podrán entender desestimadas»). Norma andaluza: no existe; se aplica la estatal.
- La premisa de que el silencio beneficia a todos los interesados no se confirma como regla general. La cuestión aquí es solo el **cumplimiento**, no los efectos (firmeza, recursos), que no se producen frente a quien no ha recibido la resolución.

### 4.2 Las dos fechas y qué documento acredita cada hito

**Qué fechas hay y a quién afectan (1.1) ✔**

| Quién recibe | Canal | Fechas que importan |
|---|---|---|
| Titular (quien solicitó) | NOTIFICA | **Dos**: cumplimiento = puesta a disposición; efectos = lectura o caducidad |
| Titular, si va en papel | POSTAL | **Dos**: cumplimiento = primer intento acreditado; efectos = entrega, rechazo o edicto |
| Otros interesados | NOTIFICA o POSTAL | **Una**, de efectos |
| Organismos de la Junta | BANDEJA | **Una**, de efectos (recepción) |
| Organismos de fuera | SIR | **Una**, de efectos (recepción) |

- **Fecha de cumplimiento:** cuándo la Administración cumple su deber de notificar. Solo sirve para el plazo de resolver y notificar y solo se mide con la notificación al titular.
- **Fecha de efectos:** eficacia del acto, inicio de los plazos de quien recibe, suspensión por requerimiento, recursos.
- ✔ **Cálculo (1.4).** Un único servicio `services/notificaciones.py` lee `Documento.fecha_administrativa`, con dos reglas uniformes (no un caso por canal):
  - **Cumplimiento del titular** = la fecha **más antigua** entre sus documentos de puesta a disposición, acuse del 1.er intento, justificante final y anuncio (el diagrama de referencia: «la primera fecha que reúna los requisitos del 40.4»). **No lee `notificaciones.resultado`**, solo documentos.
  - **Efectos** = la fecha más antigua entre el justificante final y el anuncio, **solo si el resultado es CORRECTA o RECHAZADA** (41.7: con varios cauces vale el primero). Con INCORRECTA no hay efectos.

  | Caso (titular) | Cumplimiento | Efectos |
  |---|---|---|
  | NOTIFICA, «Leída» | `JUSTIFICANTE_NOTIFICA_DISPOSICION` (43.3) | `JUSTIFICANTE_NOTIFICA`: fecha de lectura (43.2 p. 1) |
  | NOTIFICA, «Rechazada» (expresa) | La misma | `JUSTIFICANTE_NOTIFICA`: fecha del rechazo (41.5) |
  | NOTIFICA, «Rechazada por transcurso de plazo» | La misma | `JUSTIFICANTE_NOTIFICA`: fecha que da la plataforma (43.2 p. 2) |
  | NOTIFICA, «Caducada» → INCORRECTA | La misma | Ninguna: no hay notificación practicada |
  | POSTAL, entrega o rechazo al 1.er intento | `JUSTIFICANTE_POSTAL` | `JUSTIFICANTE_POSTAL` (misma fecha) |
  | POSTAL, 1.º fallido y 2.º correcto | `JUSTIFICANTE_POSTAL_1ER` (40.4) | `JUSTIFICANTE_POSTAL` (entrega del 2.º) |
  | POSTAL, dos fallidos y edicto | `JUSTIFICANTE_POSTAL_1ER` | `ANUNCIO_PUBLICADO` (44) |
  | Edicto directo, sin intentos previos | `ANUNCIO_PUBLICADO` | `ANUNCIO_PUBLICADO` |
  | Otros interesados | No aplica | Igual que arriba |
  | BANDEJA / SIR | No aplica | El justificante: fecha única |

  - **Anuncio del edicto:** la fecha que vale es la del anuncio en el **BOE** (44, obligatorio). Los anuncios facultativos previos (44 p. 2) los trata el edicto (#568).
  - **Falta el acuse del 1.er intento:** si solo consta la entrega del 2.º, el cumplimiento sale de la entrega (más tardía); es responsabilidad del usuario (P5). Hoy los acuses del 1.º y 2.º intento salen probablemente juntos de la web de Correos, así que el riesgo es bajo; se suben con el mismo mecanismo del PDF polivalente.
  - **Los efectos no pasan por este servicio para los plazos del interesado:** estos leen la fecha del justificante final producido por el `NOTIFICAR`. El servicio sirve al cumplimiento, al semáforo y a los certificados.
  - Con varios destinatarios solo se cubre al titular (una fila); ligar cada justificante a su destinatario sigue aparcado (4.3).

**Documento de cada hito ✔ (principio P1)**

`notificaciones` **deja de guardar fechas** (`fecha_puesta_disposicion`, `fecha_resultado`) y guarda quién (destinatario), cómo (canal) y qué resultó. Las fechas se calculan leyendo documentos.

| Hito | Tipo de documento | Su fecha es | Sirve para | Tipo |
|---|---|---|---|---|
| Puesta a disposición (Notifica) | `JUSTIFICANTE_NOTIFICA_DISPOSICION` | La puesta a disposición | Cumplimiento (titular) | **Nuevo** |
| Lectura o caducidad (Notifica) | `JUSTIFICANTE_NOTIFICA` | Lectura o caducidad | Efectos | Existe |
| Intento fallido en papel | `JUSTIFICANTE_POSTAL_1ER` | El intento | Cumplimiento (titular en papel) | **Nuevo** |
| Entrega o rechazo en papel | `JUSTIFICANTE_POSTAL` | Entrega o rechazo | Efectos | Existe |
| Recepción de un organismo | `JUSTIFICANTE_BANDEJA` / `JUSTIFICANTE_SIR` | Recepción | Efectos | Existen |
| Sede (notificación en papel) | `JUSTIFICANTE_SEDE` (nombre a confirmar) | Esa puesta a disposición | Da por hecha la obligación paralela | **Nuevo** |
| Edicto | `ANUNCIO_PUBLICADO` | Publicación | Efectos (#568) | Existe |

- **Convención de nombres:** `JUSTIFICANTE_<CANAL>_<HITO>`. Verificado: el código compara estos códigos por igualdad (`mutaciones_arbol.py`, `pool_documentos.html`) y solo usa el prefijo `JUSTIFICANTE_` para el aviso de críticos y huérfanos, así que los nombres nuevos no confunden a nada existente.
- El usuario da la fecha al elegir el tipo al subir el documento; el parser la propone.
- **Reglas del POSTAL ✔.** No hay tipo para el 2.º intento. `JUSTIFICANTE_POSTAL_1ER` se vincula como consumido solo si el 1.er intento falla; si el 1.º es correcto no se duplica como consumido, va solo el `JUSTIFICANTE_POSTAL` como producido. Si el 2.º intento es correcto es el definitivo (producido); si no, se va a edictal (#568), que también puede abrirse **sin intentos previos** cuando se ignora el lugar de la notificación o el interesado es desconocido (art. 44; poco habitual). El detalle por caso se escribe en la descripción del tipo al migrar. `numero_intento` se queda: con estas reglas no es derivable de los documentos.
- **PDF polivalente ✔.** Si Notifica no emite la puesta a disposición como documento aparte, el certificado de lectura o caducidad (que lleva las dos fechas) se sube dos veces con tipos distintos: como puesta a disposición (consumido) y como justificante final (producido). El pool lo permite: `ingesta_pool.py` reutiliza el fichero y crea otra fila `Documento`. Es un paso más para el usuario, pero es lo que justifica administrativamente si hubo o no silencio.
- **Registrar una notificación exige su documento (D3) ✔.** Se acaba el «registrar envío» sin fichero. En POSTAL, hasta que llegue el acuse la tarea queda «pendiente de notificar».

### 4.3 Vínculo documento–tarea (D4, D4b) ✔

- **D4.** Sin roles nuevos ni tabla de vínculo nueva. Puesta a disposición, acuses de intento y sede se vinculan como **`CONSUMIDO` de la tarea `NOTIFICAR`**, porque son presupuesto del `PRODUCIDO` (el justificante final): sin puesta a disposición correcta no hay lectura ni caducidad que valga. Se descartaron, a propuesta de Claude, un rol `ACREDITA` (mezcla significado con flujo) y un vínculo propio documento↔`notificaciones` (cuelga el documento de otra entidad; P2). Vincularlos solo a `notificaciones` no vale: quedarían huérfanos y en el pool (sección 2.2).
- **Cambia el contrato de `NOTIFICAR`:** el docstring de `Tarea` dice que consume «documentos notificados»; pasa a consumir también los justificantes previos que fundamentan el producido. El front que hoy lista los consumidos como «lo que se notifica» tendrá que distinguirlos por tipo.
- **D4b.** El catálogo `tramites_tareas_documentos` admite **varias entradas por paso**: la clave primaria pasa a clave sustituta más índice único (por `COALESCE(tipo_documento_id, 0)`, porque `tipo_documento_id` es nulable). Descartadas: dejar la entrada polimórfica (pierde la exactitud de `RESOLUCION`) y no declarar los tipos (el radar de huérfanos dejaría de ayudar). Efectos: ajustar el editor de tablas maestras; `sugerencia_subida` queda en blanco (ambigua) en `NOTIFICAR`, coherente con que el usuario elige el tipo; en la implementación, decidir qué trámites reciben las filas (hay unos 31 con una tarea `NOTIFICAR`).
- **`Notificacion.documento_id` se mantiene** ✔: en el caso simple lo graba BDDAT junto al producido (el usuario ya no ve una entrada aparte); en el múltiple la tarea no genera un justificante sino muchos y su producido es el **certificado de notificación múltiple** que lo cierra todo, que es el que consume el edictal si procede. Se estudia cuando llegue el paso multi-destinatario. Idea a valorar entonces: los justificantes individuales podrían colgar de la tarea como consumidos de ese certificado, y `documento_id` solo diría de quién es cada uno (compatible con P2).

### 4.4 Sede y resultado de la notificación

**Puesta a disposición en sede (1.6) ✔.** Obligación paralela del art. 42.1 para toda notificación en papel. No es una notificación: si se pone a disposición y caduca sin acceso, no cuenta como notificada (art. 43.2). Tres estados derivados: **Puesta** (hay `JUSTIFICANTE_SEDE`), **Justificada** (`sede_justificacion` con texto y constancia en bitácora) o **Pendiente**. Solo los dos primeros dan la obligación por hecha; con la sede pendiente la tarea no llega a «hecha» y **no se puede cerrar el trámite**. Criterio: invariante (completitud del dato), no regla del motor. Solo canal POSTAL.

**✔ Resultado de la notificación (1.7).** `resultado` es un dato **vivo** de la fila: nace vacío (pendiente) y cambia hasta un valor final, y su significado depende del canal y del hecho que lo produce. Se propone pasar de {CORRECTA, INCORRECTA} a {CORRECTA, RECHAZADA, INCORRECTA}, con esta matriz (texto de la Ley 39/2015 vigente, leído en `legalize-es`). *Cerrado por Carlos el 20/09/2026; el único punto abierto es la duda del 30.5 (sección 8).*

| Resultado | NOTIFICA (electrónica) | POSTAL (papel) | BANDEJA (organismos de la Junta) | SIR (organismos de fuera) |
|---|---|---|---|---|
| **Sin resultado** (fila viva) | Puesta a disposición hecha; sin acceso ni rechazo aún. Corre el plazo de 10 días naturales. El cumplimiento ya está dado con el documento de puesta a disposición · 43.2 p. 2, 43.3 | Sin acuse todavía («pendiente de notificar») o intento en curso. El cumplimiento no está dado hasta el primer intento acreditado · 40.4, 42.2 | No existe: el envío es instantáneo y la fila nace ya con resultado · ADR-034 | Envío anotado a mano; recepción aún sin certificar · ADR-034 |
| **CORRECTA** | Acceso al contenido («Leída»). Practicada en ese momento; efectos desde la fecha de acceso · 43.2 p. 1 (validez: 41.1) | Entrega al interesado o a una persona mayor de 14 años que se identifica en el domicilio. Efectos desde la entrega. Si sale a la primera, cumplimiento y efectos coinciden · 42.2, 40.4 | Recepción por el organismo: fecha única, de efectos. Sin norma específica de notificación; criterio de proyecto · ADR-034 | Recepción certificada en ARIES (captura de pantalla): fecha única, de efectos. Base solo analógica: el asiento registral con fecha y hora (16.3 y 16.4). Criterio de proyecto · ADR-034 |
| **RECHAZADA** | Dos hechos con el mismo resultado. **Expreso** («Rechazada»): efectos desde la fecha del rechazo, anterior a los 10 días; se da con destinatarios obligados o no, porque el 41.5 vale para cualquier medio y no depende de la obligación · 41.5. **Presunto** («Rechazada por transcurso de plazo», destinatario **obligado**): 10 días naturales desde la puesta a disposición sin acceder · 43.2 p. 2. Con «Caducada» (check de obligado sin marcar) solo hay rechazo presunto si el interesado o su representado **estaba obligado** (14.2) o **eligió** la vía electrónica · 43.2 p. 2. En todos se hace constar y sigue el procedimiento (41.5); aplicar ese efecto al presunto es lectura de proyecto | Rechazo expreso del interesado o su representante. Se hacen constar las circunstancias del intento y el medio; trámite efectuado y sigue el procedimiento. **No existe rechazo presunto en papel** · 41.5 | No aplica: no hay figura de rechazo del organismo con efecto (el 41.5 habla del interesado) y no consta ningún rechazo en BandeJA | Ídem BANDEJA: no consta ningún rechazo en SIR |
| **INCORRECTA** | Solo «Caducada» si no consta que estaba obligado ni que eligió lo electrónico: sin presunción de rechazo, no hay notificación practicada; hay que notificar por otro medio (41.3 p. 2) o, si no se puede practicar, anuncio en el BOE (44). «Anulada» (la retira el usuario) y «No entregada» (error del sistema) **no entran en BDDAT**: en su justificante solo consta la puesta a disposición y se reintenta la notificación | Intento infructuoso (nadie se hace cargo, ausente…). El 1.º no practica pero **cumple** el 40.4 si está acreditado; se repite **una sola vez**, en otra franja y dentro de 3 días. 2.º infructuoso (`numero_intento = 2`) → anuncio en el BOE. El anuncio en el BOE puede abrirse **directamente, sin intentos**, si se ignora el lugar de la notificación o el interesado es desconocido (p. ej. solo consta el DNI); poco habitual, pero posible · 42.2, 40.4, 44 | Envío que no llega o es devuelto: sin recepción; hay que repetirlo. Sin caso documentado | Ídem BANDEJA |

- **Corrección de cita.** El 43.2 tiene **dos párrafos**: el primero es la práctica por acceso (CORRECTA); el segundo es el rechazo presunto de las electrónicas obligatorias o elegidas. El rechazo **expreso** es solo el 41.5 y vale para cualquier medio. Que el rechazo «dé por efectuado el trámite» sale del 41.5; aplicarlo al presunto del 43.2 p. 2 es una unión de proyecto (así consta ya en `NORMATIVA_NOTIFICACION_FECHAS_EFECTOS.html`).
- **Sin presunción de rechazo no hay notificación.** Si el interesado ni está obligado a la vía electrónica ni la ha elegido, la falta de acceso no produce efecto previsto (43.2). «Obligada o elegida» describe **al interesado** (arts. 14 y 41.1), no al tipo de notificación. ✔ **Se presume que, si la Administración usa el canal NOTIFICA, la vía es obligatoria o elegida.** Queda fuera de esa presunción la puesta a disposición en sede de una notificación en papel (42.1): es una obligación paralela, se registra como `JUSTIFICANTE_SEDE` del canal POSTAL y nunca produce rechazo presunto, sea cual sea la herramienta con la que se haga.
- **Doce justificantes reales (20/09/2026) frente al parser.** (1) Llevan todos el dato **«Obligado a relacionarse electrónicamente: Sí/No»**, que el parser no extrae. (2) Encajan con el 43.2, **12 de 12**: los 6 «Rechazada por transcurso de plazo» tienen «Obligado: Sí» (todos entidades) y los 6 «Caducada» tienen «Obligado: No» (4 personas físicas, una SL y una comunidad de bienes). Es una muestra, no una definición de la plataforma. **El check lo marca el administrativo al notificar** y Notifica permite cambiarlo. Pero «Caducada» **no prueba que el destinatario no estuviera obligado**: por el 14.2 lo están en todo caso las personas jurídicas (a), las entidades sin personalidad jurídica (b) y quienes representan a un obligado (d). La SL y la comunidad de bienes de las muestras con «Obligado: No» son un check olvidado, no una notificación de otra naturaleza (dato de Carlos). (3) En las 12 muestras el desenlace se registra siempre el día 11 de calendario (entre las 03:00 y las 09:25), sea cual sea el día de la semana: son **10 días naturales**, no hábiles (con hábiles serían, en las dos primeras muestras, el 23/09 y el 16/09). El 43.2 p. 2 dice expresamente «diez días naturales», excepción a la regla de días hábiles del 30.2, así que la plataforma cuenta bien; el 40.2 (cursar la notificación en 10 días) no lo dice y sigue siendo hábil. El 30.3 manda contar desde el día siguiente y los datos lo confirman. La fecha del justificante es la del registro de la plataforma, un día después del décimo día natural; se toma tal cual (P1). **Duda abierta (30.5):** en 7 de las 12 muestras el 10.º día natural cae en sábado o domingo y la plataforma **nunca lo prorroga**: registra el desenlace el día 11 igualmente. Si el 30.5 (último día del plazo inhábil, prórroga al primer hábil siguiente) se aplicara a este plazo, el rechazo no podría darse hasta un día hábil después y la fecha del justificante sería anterior a la legal. Es práctica de la plataforma, no criterio jurídico; sin respuesta en el repositorio. (4) La fecha del desenlace no lleva la etiqueta «Fecha de lectura» sino «Caducada:» o «Fecha de rechazo:»; el parser solo lee la primera. (5) El texto del estado es «Rechazada por transcurso de plazo» y el mapa del parser tiene la clave «Rechazada por plazo» (nombre del README de `notifica-poc`): con este justificante `resultado` sale nulo.
- **`numero_intento` solo tiene sentido en POSTAL** (los dos intentos son del 42.2). Hoy `_estado_notificar` lo aplica también a NOTIFICA (`NOTIFICACION_FALLIDA` = «queda un 2.º intento»).
- **Tratamiento en BDDAT.** CORRECTA y RECHAZADA dan por efectuada la notificación y permiten cerrar el trámite; INCORRECTA no. El cumplimiento del plazo **no lee** el resultado (D2).
- **El parser actual** mapea Leída a CORRECTA y todo lo demás a INCORRECTA; por eso el rechazo válido bloquea hoy el cierre. ✔ **Mapeo decidido:** Leída → CORRECTA; Rechazada → RECHAZADA; Rechazada por transcurso de plazo → RECHAZADA; **Caducada → INCORRECTA con aviso**, que el usuario pasa a RECHAZADA solo si consta que el interesado (o su representado) estaba obligado (14.2) o eligió lo electrónico; ✔ **refinamiento:** si el destinatario tiene NIF de entidad la obligación es cierta (14.2.a y b) y el parser propone RECHAZADA directamente, avisando de que el check de obligado estaba sin marcar en Notifica; Anulada y No entregada no entran en BDDAT (no se registran: en su justificante solo consta la puesta a disposición y se reintenta la notificación). El parser propone y el usuario decide (P5); hoy el registro es manual y el parser completo se implementará después. La lista de estados de Notifica-PNT viene de `notifica-poc`; solo «Leída», «Caducada» y «Rechazada por transcurso de plazo» están vistas en justificantes reales; «Rechazada», «Anulada» y «No entregada» no se han cotejado, porque hasta el parser completo no aportan.

### 4.5 El cumplimiento del plazo se calcula (D2, D2b, D2c) ✔

**D2.** El cumplimiento del plazo se separa del certificado de cierre. Alternativas descartadas: un solo certificado con la fecha del titular (no quita la falsa alarma de «vencido», porque solo se puede emitir con todo hecho) y dos certificados con gesto sin distinguir su momento.

- El cumplimiento depende **solo** de que exista, vinculado a la tarea `NOTIFICAR` del trámite `NOTIFICACION` de la fase, un documento de tipo puesta a disposición con su fecha. No lee `notificaciones.resultado` (que responde a los efectos).

| Situación | Cumplimiento |
|---|---|
| El usuario no ha subido el documento, o no con el tipo correcto y en su sitio | **No** |
| La puesta a disposición falló y el usuario no sube nada como tal | **No** (hay que repetirla) |
| El usuario sube el documento con el tipo de puesta a disposición y su fecha | **Sí** |

- **D2c (descartada).** No hay reintento con varias puestas a disposición: el documento de justificante de envío anulado o fallido no entra en el expediente; el usuario sube el correcto o nada. Si es imposible notificar al titular se resuelve fuera de BDDAT (contacto directo, SUR) y el plazo sigue sin cumplirse, que es la señal correcta. Sin escape justificativo.
- **La puesta a disposición no es una notificación aparte**: es el primer hito de la notificación al titular por NOTIFICA. No tiene fila propia en `notificaciones`; es un documento vinculado a la tarea.
- **Solo el titular.** Con organismos e interesados el cumplimiento no interviene.

**D2b — cómo lo lee el motor.** Clave nueva y explícita del vocabulario de `catalogo_plazos`: `campo_fecha_cumplimiento = {"calculado": "documento_cumplimiento"}`, para que `fk` siga significando clave foránea real (así lo documentan `DISEÑO_FECHAS_PLAZOS` §3.2 y el modelo). `calculado` significa «propiedad calculada del modelo que devuelve el documento». Requiere una rama nueva en `plazos._resolver_campo_fecha` (unas 3 líneas), la etiqueta legible en administración y actualizar el vocabulario documentado. **Las 14 filas de `catalogo_plazos`** (3 de FASE, previstas en #921; 11 de SOLICITUD, **no previstas**: consecuencia de separar plazo y certificado) pasan a `{"calculado": "documento_cumplimiento"}` (migración de datos, no de esquema). Las filas SOLICITUD siguen alimentando `obtener_estado_plazo_solicitud` (ADR-048 §C); solo cambia su cumplimiento.

`documento_cumplimiento`: en una fase finalizadora, el documento de cumplimiento de su trámite `NOTIFICACION` (el más antiguo entre los del titular, 4.2); en la solicitud, el más tardío entre sus fases finalizadoras. **Cadena completa:** sin certificado emitido se calcula en directo; con `CERT_CUMPLIMIENTO_FASE` emitido, el certificado guarda el `documento_id` que la regla eligió al emitirlo y quien pinta lo lee sin buscar (4.6). El plazo compara la fecha de ese documento con la fecha límite (registro de entrada más plazo del catálogo) y da CUMPLIDO, cumplido fuera de plazo o VENCIDO. **Ese resultado nunca se guarda: se pinta siempre.** Lo único que se guarda es el `documento_id` en el certificado.

**Costes asumidos.** (1) El plazo ya no apunta a un documento guardado: recorre fase → trámite → tarea → documento al evaluarse, pero solo mientras no hay sello (4.6); reinterpreta el criterio de ADR-041 §D bis de anclar con FK y no navegar. (2) La valoración del art. 40.4 (intento debidamente acreditado, texto íntegro) ya no la hace un gesto explícito: queda implícita en subir el documento correcto; el acto humano es la subida.

### 4.6 Certificados: cumplimiento y cierre (D5, D5a, D5b, D2d, D6, D8) ✔

**Concepto (P3).** Un certificado es un documento del expediente que no firma nadie del servicio ni viene de fuera: **constata** algo del expediente. Al emitirse sella lo que dice, y lo sellado no se toca. Servicios que pintan o evalúan el plazo: si hay certificado emitido, leen su contenido y lo toman por cierto; si no, calculan. Aplicarlo a todos los que pintan es un issue aparte (sección 7); en este trabajo solo lo aplica la clave `calculado`.

**Cada fase finalizadora tiene dos certificados (D5):**

| | `CERT_CUMPLIMIENTO_FASE` | `CERT_CIERRE_FASE` |
|---|---|---|
| Qué constata | Que se notificó al titular; guarda el `documento_id` del documento de cumplimiento | Que está hecho todo lo obligatorio: es el cierre de la fase |
| Cuándo se emite | En cuanto consta la notificación al titular, sin esperar al resto | Cuando no queda nada pendiente; exige que ya esté emitido el de cumplimiento (cuenta sellos) |
| Gesto | Manual, como los demás; sin urgencia porque el plazo ya sale cumplido por cálculo | Manual: informe «¿cómo voy?» siempre disponible; se consolida solo si no queda nada pendiente (patrón `cert_fin_instruccion`) |
| Dónde se guarda | Tabla `certificados`, localizado por `(fase_id, tipo)` | Ocupa `Fase.documento_resultado_id` (D5a) |
| Qué protege | El documento citado, su vínculo con la tarea y la tarea, porque la fase sigue abierta | Nada nuevo: el sellado de fase cerrada (ADR-036) ya protege el interior |

- En las fases no finalizadoras no existe el de cumplimiento. Extender el de cierre a las demás fases (un cierre homogéneo en vez de un documento distinto cada vez) es posterior y queda fuera.
- **D5a.** El certificado de cierre **ocupa `documento_resultado_id`**: es el documento que sella el resultado completo, que sostiene la fase (`resultado_fase_id`, que rellena el usuario). No se crea `Fase.documento_cierre_id`. Siguen tal cual `finalizada`, `PDTE_CIERRE` y el sellado de ADR-036. La resolución sigue siendo el producido de su tarea. `reabrir_fase` pasa a deshacer el certificado con justificación (patrón `cert_fin_instruccion.deshacer`, que borra todo el rastro).
- **Sin segunda columna en `fases`**: el de cumplimiento se localiza por `(fase_id, tipo)`; así no hay un hueco nulo en las fases no finalizadoras. Solo `documento_resultado_id` sigue como puntero, por ser ruta caliente (`finalizada` se consulta en SQL en el seguimiento).

**Certificado de solicitud (D5b).** `CERT_CIERRE_SOLICITUD` **no sella nada: solo cuenta sellos.** Si falta el de alguna fase finalizadora no se genera y se informa; si están todos, se genera y su PDF se vincula a `Solicitud.documento_cierre_id`. Se mantiene aunque el plazo de resolver lo den las fases: deja por escrito, en base de datos y PDF, que la solicitud se hizo, y tiene uso posterior como consumido de otras solicitudes (la explotación parcial o definitiva consume el de la AAC; la definitiva renovable, el de la parcial). Por lo mismo se mantiene `CERT_FIN_INSTRUCCION`, consumido del `ELABORAR` de la fase finalizadora. `Solicitud.documento_cierre_id` deja de ser el ancla de la fecha del plazo (#778) y pasa a ser la constancia de cierre.

**Contenido y fecha (D2d, D6).**
- El certificado guarda **solo el `documento_id`, no su fecha** (P6): la fecha la lee quien la necesita del documento. Para que sea verdad, el documento citado queda **protegido por completo** (fecha, tipo, fichero, desvinculación y borrado) mientras algún certificado emitido lo cite. El CRUD de documentos pregunta al servicio de certificados «soy el documento N, ¿me usa algún certificado?»; es viable con una consulta sobre `datos` y conviene una lista normalizada de documentos citados. Un `documento_id` dentro de un JSON no es clave foránea: el aviso del pool (`_documento_es_referenciado`) no lo ve.
- **Sin fecha propia (D6).** El certificado no guarda fecha ni la fila de `certificados` tampoco; su `Documento` va con `fecha_administrativa` nula, como los diagnósticos. El momento de emisión ya consta en `certificados.generado_en`. Nada de lo que hoy lee los certificados de fase finalizadora necesita esa fecha (el plazo lee la del documento citado).

**Tabla y sellos (D8, opción B).**
- Los certificados nuevos nacen en `certificados` ampliada: columna `tipo` (hoy se deduce del documento), `fase_id`, y corregir los dos índices únicos por solicitud para que incluyan el tipo. **Como máximo un certificado emitido por tipo y elemento** (`deshacer` borra todo el rastro; no hay versiones).
- **El borrador no se guarda**, ni en `datos`: se calcula y se muestra en pantalla, como los certificados actuales, porque siempre divergiría de la realidad y se muestra precisamente para corregirse. Al emitir el cierre se guardan el **PDF y `datos`**. Por eso no hace falta columna `estado` ni `documento_id` nulable. Un documento virtual no es un fichero: al compilar el expediente hará falta el PDF de los emitidos.
- **Un único módulo de sellos**, con una función por tipo de certificado y un solo punto de comprobación, para que la vigilancia no crezca con cada certificado nuevo. **Sin motor declarativo genérico** (sobreingeniería para cuatro o cinco tipos). Lo que cita el JSON no es clave foránea, así que quien lo protege es ese módulo.
- Se mantienen los punteros de ruta caliente y se quitan solo los que nadie consulta en SQL.
- `certificados_fase` y `CERT_FIN_INSTRUCCION` (con su sello de #838) **no se tocan** en este trabajo; unificarlos en `certificados` es un issue aparte.

### 4.7 Otras decisiones

- **D7 ✔ — la fila `NOTIFICAR` (40.2) del catálogo se deja como está.** Hoy está dormida (`plazo_tarea` solo se llama para `ESPERAR_PLAZO` y nada la muestra). Es dato de catálogo: si cuando se muestre en la interfaz el aviso miente o no sirve, se reevalúa.
- **D1 ✔.** Principio P1 y quitar `fecha_puesta_disposicion` y `fecha_resultado`.

---

## 5. Efecto sobre los plazos ✔

Lectura de la ley revisada y ratificada por Carlos el 20/09/2026: la suspensión del 22.1.a arranca en la fecha de **efectos** de la notificación del requerimiento, no en la de cumplimiento (el 40.4 limita esta última «a los solos efectos» de notificar la resolución en plazo). La suspensión dura el **menor** entre el cumplimiento por el destinatario y el plazo concedido (ya consolidado: `plazos._medir`, `parada = min(...)`, ADR-041 y `NORMATIVA_PLAZOS.md`). **La suspensión en sí queda fuera de este pre-ADR:** el art. 22.1 dice «se podrá suspender» y el 22.1.d exige comunicar a los interesados la petición y la recepción; lo trata #796 (abierto) y, según Carlos, en la práctica no se suspende. El código sigue infiriendo la suspensión de cuatro filas del catálogo (`suspende = true`), como dejó dicho ADR-041 mientras #796 no la modele; no se ha alineado con esa práctica. Lo ratificado aquí vale para cuando #796 la modele.

**Problema de fondo.** Los plazos del interesado arrancan de `{"rol": "CONSUMIDO"}`: la `fecha_administrativa` del justificante que produjo el `NOTIFICAR` anterior. La suspensión del plazo de resolver usa el mismo disparo (`plazos._causas_suspension`). Por defecto, al subir un justificante de Notifica el formulario propone la puesta a disposición, no el acceso. Cuando el destinatario es el titular: **el titular** ve su plazo contado antes de tiempo (con rechazo presunto, hasta 10 días naturales antes de que la notificación exista legalmente); **la Administración**, mientras el código infiera la suspensión (#796), la ve arrancar antes de tiempo (22.1.a, «desde la notificación del requerimiento»), con riesgo de silencio; si no se suspende, este efecto no existe. Con el modelo de 4.2 se arregla solo: el justificante final lleva la fecha de efectos y la puesta a disposición va en su propio documento.

Con organismos (BANDEJA, SIR) hay una sola fecha, así que **solo cambian los plazos que se notifican al titular**:

| Plazo (camino) | Norma en catálogo | Debe arrancar de | ¿Cambia? |
|---|---|---|---|
| `REQUERIMIENTO_SUBSANACION` · ESPERAR_PLAZO (10 d hábiles, suspende) | Art. 68.1 LPACAP | Efectos (22.1.a) | **Sí** |
| `CONSULTA_TRASLADO_TITULAR` · ESPERAR_PLAZO (15 d) | Arts. 127.3 y 131.3 RD 1955/2000 | Efectos | **Sí** |
| `REQUERIMIENTO_RBDA_DEFINITIVA` · ESPERAR_PLAZO (10 d) | Genérico LPACAP (73.1) | Efectos | **Sí** |
| `CONSULTA_TRASLADO_ORGANISMO`, `SOLICITUD_INFORME` (organismos por BANDEJA o SIR) | Arts. 127, 131 y 114 RD 1955/2000 | La misma (una sola fecha) | No |
| `CONSULTA_SEPARATA` | Arts. 127.2 y 131.1 RD 1955/2000 | Por BANDEJA o SIR: la misma (una sola fecha). **Por NOTIFICA:** efectos, para el plazo del organismo (la suspensión, aparte: #796) | **Solo si va por NOTIFICA.** POSTAL, muy improbable |
| `ANUNCIO_BOE` / `BOP` / `PRENSA` · ESPERAR_PLAZO (30 d) | Arts. 125.1 y 144 RD 1955/2000 | La publicación | No |
| `TABLON_AYUNTAMIENTOS` · ESPERAR_PLAZO (30 d naturales) | Art. 125 RD 1955/2000 | Inicio de la exposición | No |
| `COMUNICACION_INICIO_ADMISION` · ELABORAR (10 d) | Art. 21.4 LPACAP | Igual | No |
| `NOTIFICAR` (10 d hábiles, «Art. 40 LPACAP») | 40.2 | — | **No se toca** (D7) |
| `SOLICITUD` (11 filas) y `FASE` (DUP, AAP, AAC) | Arts. 128, 131.7, 148.1 | Cumplimiento = `{"calculado": "documento_cumplimiento"}` | **Sí** (arregla también la deuda de #892) |

**`CONSULTA_SEPARATA` por NOTIFICA.** Las separatas se envían por Notifica, BandeJA o SIR (Carlos). Cuando va por Notifica, el plazo de contestación del organismo cuenta desde efectos. La suspensión que hoy infiere el código para esta fila (`suspende = true`, 22.1.d) queda fuera de este pre-ADR: es potestativa, exige comunicar petición y recepción a los interesados y la trata #796.

**Correcciones de documentación que salen de esto:**
- `DISEÑO_FECHAS_PLAZOS` §5.1: la constante `NOTIFICACION_DIAS` mezcla el 40.2 (cursar en 10 días) con el plazo máximo del 21.2.
- El **21.3.b** solo fija desde cuándo se cuenta el plazo (entrada en el registro electrónico). Lo de «resolver y notificar» está en el **21.2** (y en el 22.1). Citan mal el 21.3.b: ADR-041 §D bis, el docstring de `Solicitud.documento_cierre_id`, #801 y #921.
- `MODELO_ESTADOS_SEMAFORO` habla de un «plazo de lectura» (10 días naturales del 43.2) que no coincide con la fila del catálogo (40.2, 10 días hábiles).
- ◇ `NORMATIVA_PLAZOS` §1.1 dice que BDDAT aplica las suspensiones del 22.1 «siempre que concurren, sin modelar una decisión discrecional»: contradice el «se podrá suspender» del propio artículo, #796 y la práctica de no suspender. A corregir junto con #796.

---

## 6. Afecciones (BD y backend)

Orientativo: las decisiones y el análisis exhaustivo de la implementación pueden ampliarlo. **Crear**, **Actualizar**, **Revisar**, **Dejar**.

| Área | Elemento | Acción | Qué |
|---|---|---|---|
| BD | `notificaciones` | Actualizar | Quitar `fecha_puesta_disposicion` y `fecha_resultado`. Añadir `destinatario_id` (multi) y `sede_justificacion`. Quitar `UNIQUE(tarea_id)` y sustituirlo por dos índices únicos parciales. `resultado` admite `RECHAZADA`. `documento_id` se mantiene |
| BD | `documentos_tarea` | Dejar | Sin cambio de esquema ni rol nuevo |
| BD | `tipos_documentos` | Crear / Actualizar | Cinco tipos: `JUSTIFICANTE_NOTIFICA_DISPOSICION`, `JUSTIFICANTE_POSTAL_1ER`, `JUSTIFICANTE_SEDE` (a confirmar), `CERT_CUMPLIMIENTO_FASE`, `CERT_CIERRE_FASE`. Descripción de la fecha de cada `JUSTIFICANTE_*` y del caso POSTAL |
| BD | `tramites_tareas_documentos` | Actualizar | Clave sustituta + índice único; declarar los tipos nuevos como entrada de `NOTIFICAR` en los trámites que corresponda |
| BD | `fases` | Dejar | Sin columna nueva: el cierre ocupa `documento_resultado_id` |
| BD | `certificados` | Actualizar | `tipo`, `fase_id`, índices únicos con tipo |
| BD | `certificados_fase` | Dejar | Hasta el issue aparte de unificación |
| BD | `catalogo_plazos` | Actualizar (datos) | 14 filas (11 SOLICITUD, 3 FASE) a `{"calculado": "documento_cumplimiento"}` |
| Modelos | `fases.py`, `solicitudes.py` | Actualizar | Propiedad calculada `documento_cumplimiento` (cuidar las consultas del árbol); docstring de `documento_cierre_id` (constancia de cierre; citas 21.2 / 21.3.b) |
| Modelos | `catalogo_plazos.py` | Actualizar | Comentarios de `campo_fecha_cumplimiento` y vocabulario con la clave `calculado` |
| Modelos | `notificaciones.py`, `tareas.py` | Actualizar | Columnas de `notificaciones`; `Tarea.notificacion` pasa a lista; docstring de `Tarea` |
| Modelos | `tramites.py` (`Tramite.finalizado`) | Actualizar | Hoy exige `resultado == 'CORRECTA'` (línea 117): RECHAZADA debe contar como notificación efectuada. Sin esto, el valor nuevo seguiría bloqueando el cierre |
| Servicios | **Nuevo** `services/notificaciones.py` | Crear | Fechas de cumplimiento y efectos leídas de los documentos, estado de sede, predicado «notificada» |
| Servicios | **Nuevo** módulo de sellos | Crear | Una función por tipo de certificado, un solo punto de comprobación; consulta «¿me usa algún certificado?» |
| Servicios | Nuevos servicios de cumplimiento y cierre (fase y solicitud), informe de pendientes | Crear | Patrón `cert_fin_instruccion`: informe, consolidación, `deshacer` |
| Servicios | `plazos.py` | Actualizar | Rama `calculado` en `_resolver_campo_fecha`: mira primero si hay certificado de cumplimiento y lee el documento que cita; si no, calcula |
| Servicios | `estado_dominio._estado_notificar` | Actualizar | Estados según documentos presentes; RECHAZADA → FIN; agregar sobre lista; estado «pendiente de sede» |
| Servicios | `invariantes_esftt` | Actualizar | Sede pendiente impide completar; INCORRECTA sigue bloqueando; borrar sobre lista; protección del documento citado |
| Servicios | `mutaciones_arbol._hook_657`, `parser_justificante_notifica` | Actualizar | Ya no escribe fechas; propone la fecha según el tipo; cotejo de remesas; el parser lee «Obligado a relacionarse electrónicamente» y la fecha de cada estado («Caducada:», «Fecha de rechazo:») y corrige el mapeo de «Rechazada por transcurso de plazo» (cuando se implemente el parser completo; hoy el registro es manual) |
| Servicios | `generador_cert.py` | Actualizar | Título y secciones del informe de cierre |
| Servicios | `cola_administrativo`, `seguimiento`, `detalle_nodo`, `arbol_expediente` | Actualizar | Recordatorio de sede, lista de notificaciones, datos del certificado (solo payload) |
| Servicios | `esquema_editable.py` | Revisar | No consta que consulte el catálogo; confirmar |
| Servicios | `context_builders/*` con `fecha_administrativa` de justificantes | Revisar | Probable sin cambio |
| Servicios | `advertir_documentos_criticos_huerfanos` (#738) | Dejar | Los tipos `JUSTIFICANTE_…` ya cuentan como críticos por el prefijo. Actualizar el recuento de «9 tipos» en docstring y catálogo |
| Rutas | `api_expedientes.py`: `/notificar`, `_TRAMITES_CON_NOTIFICACION_MULTIPLE`, endpoints de cierre | Actualizar / Crear | Sin fechas; fila por destinatario |
| Rutas | `modules/expedientes/routes.py`: `pool_parsear_justificante`, `_documento_es_referenciado`, `pool_editar_documento`, `_MOTIVO_ANCLA` | Actualizar | Fecha sugerida según tipo; pregunta al módulo de sellos; mensaje del certificado |
| Rutas | `modules/catalogo_plazos/routes.py` y `_campo_fecha_macro.html` | Actualizar | Reconocer `calculado` con etiqueta legible |
| Checks | `checks/catalogo_requerido.py` | Actualizar | Tipos nuevos y certificados |
| Scripts | `scripts/expedientes_dummy/*`, `comparar_catalogo.py` | Actualizar | Modelo nuevo |
| Tests | ~23 ficheros con `Notificacion` / `.notificacion`; `test_778_medida_unica`, `test_smoke_catalogo_plazos` | Actualizar | Y tests nuevos: dos fechas, RECHAZADA, sede, cierre |
| Docs | ADR-034, ADR-008, ADR-041 §D bis, ADR-048, `DISEÑO_FECHAS_PLAZOS`, `TIPOS_DOCUMENTOS_CATALOGO`, `MODELO_ESTADOS_SEMAFORO` | Actualizar | Ver 5 |
| Varios | `sellado_fase_sesion`, `diagnosticos`, `_solicitud_notificada_en_fase_finalizadora`, migraciones históricas | Dejar | Siguen válidos con la lista |

---

## 7. Alcance de #921 y #801, orden de trabajo e issues

### 7.1 Qué cambia respecto a los issues de partida ✔

| Concepto | #921 / #801 como estaban | Ahora |
|---|---|---|
| Fecha del plazo | El certificado de cierre ancla la fecha de fin del plazo (`{"fk": "documento_cierre_id"}`) | El plazo se calcula del documento del titular; con certificado de cumplimiento emitido, se lee de él |
| Cierre de fase (#921) | Columna nueva `Fase.documento_cierre_id` con `CERT_CIERRE_FASE` | Sin columna nueva: el certificado ocupa `documento_resultado_id`; además hay un `CERT_CUMPLIMIENTO_FASE` |
| Certificado de solicitud (#801) | Deriva de los cierres de fase; su fecha es la más tardía; ancla el plazo | Cuenta sellos, no sella nada, no ancla el plazo; sin fecha propia |
| Fecha del certificado | La del último acto | Ninguna (documento sin fecha) |
| Multi-destinatario | Prerrequisito estructural dentro de #921 (9 puntos) | Issue propio, previo al informe de cierre completo |
| Catálogo de plazos | 3 filas FASE pasan de vacío a `fk` | 14 filas (11 SOLICITUD + 3 FASE) pasan a `calculado` |

### 7.2 Cómo encaja con el foco de `CONTEXTO_ACTUAL`

El foco vigente desde el 12/09/2026 es **completar la fase DUP (ADR-045): tramitar una DUP, con o sin combinaciones, de principio a fin.** La cadena fijada era #911 y #893, ADR-046, #918, #891 y #892 (hechos), luego #801 y #912, después #894, con #431 en paralelo; #921 y #922 se añadieron el 17-18/09.

Este trabajo no desvía ese foco: es lo que hacía falta para poder cerrar y notificar una DUP.
- #921 llevaba dentro el **mecanismo de notificación multi-destinatario**, que `RESOLUCION_DUP` necesita (tres trámites de notificación, ADR-046 §C) y que **nada implementa todavía**. Separarlo lo hace visible como issue propio.
- Tramitar una DUP completa exige además el **edicto** (#568: en una DUP con muchos propietarios no es opcional) y el poblado de `interesados_expediente` (#431 propietarios DUP; #430 y #924 organismos; #432 interesados reconocidos).
- El cumplimiento calculado (N2) desbloquea antes de lo previsto el plazo `CUMPLIDO` de la fase, y con él la UI de #922.

### 7.3 Tabla ordenada de issues (nuevos y existentes)

Los nuevos se numeran **N1-N9** por orden de trabajo (equivalencia con el borrador anterior: I1→N1, I2→N2, I4→N3, I5→N4, I3→N5, I6→N6, I7→N7, I9→N8, I8→N9). Milestone propuesto para los nuevos: M3, el mismo que #921 y #801 (regla de milestones). Etiquetas y cuerpos, en la sesión de creación.

| Orden | Issue | Alcance | Depende de | Notas |
|---|---|---|---|---|
| **0** | #921 y #801 (existentes) | Cerrar con **el mismo comentario** en los dos, tras crear los nuevos: enlaza ADR-049 y los issues que los sustituyen | Los issues nuevos creados | Su contenido útil se traslada (7.4); no se reescriben |
| **1** | **N1** Notificaciones: las fechas solo salen de documentos | Tipos `JUSTIFICANTE_NOTIFICA_DISPOSICION`, `JUSTIFICANTE_POSTAL_1ER`, `JUSTIFICANTE_SEDE`; `tramites_tareas_documentos` con varias entradas por paso (clave sustituta) y su editor; quitar `fecha_puesta_disposicion` y `fecha_resultado`; `services/notificaciones.py` (cumplimiento y efectos); `resultado` con RECHAZADA (y `Tramite.finalizado`, `_estado_notificar`); `numero_intento` solo POSTAL; sede con tres estados; contrato de `NOTIFICAR`; autorrelleno del pool por tipo | — | Registro manual; el parser completo queda fuera |
| **2** | **N2** Cumplimiento del plazo calculado | Propiedad `documento_cumplimiento` (fase y solicitud); clave `calculado` en `_resolver_campo_fecha`; migración de datos de 14 filas de `catalogo_plazos`; etiqueta legible en administración | N1 | Da `CUMPLIDO` en cuanto se notifica al titular; resuelve la deuda de #892 |
| **2b** | #922 (existente) UI del plazo de fase | Sin cambio de alcance; ya no espera al cierre por fase: puede mostrar `CUMPLIDO` y «cumplido fuera de plazo» | N2 | |
| **3** | **N3** Certificados como objeto de primera clase | Ampliar `certificados` (`tipo`, `fase_id`, índices únicos con tipo); módulo único de sellos; PDF y `datos` al emitir; borrador no guardado; consulta «¿me usa algún certificado?» y protección del documento citado; tipos `CERT_CUMPLIMIENTO_FASE` y `CERT_CIERRE_FASE` | — (puede ir en paralelo a N1 y N2) | No toca `CERT_FIN_INSTRUCCION` |
| **4** | **N4** Certificados de cumplimiento y de cierre de la fase finalizadora (sustituye a #921) | `CERT_CUMPLIMIENTO_FASE` y `CERT_CIERRE_FASE` (= `documento_resultado_id`); informe «¿cómo voy?»; gesto manual; `reabrir_fase` como deshacer; el cierre exige el de cumplimiento; UI del inspector | N2, N3 | Los casos con un solo `NOTIFICACION` (AAP, AAC, `RESOLUCION`) no necesitan N5. La DUP completa necesita N5 y #568 |
| **5** | **N5** Notificación multi-destinatario | `destinatario_id`, quitar `UNIQUE(tarea_id)`, `Tarea.notificaciones` como lista, `_TRAMITES_CON_NOTIFICACION_MULTIPLE`, servicio que puebla desde `interesados_expediente`, certificado de notificación múltiple como producido, ligar cada justificante a su destinatario | N1 | Independiente de N3 y N4. Datos reales: #431, #430, #924, #432 |
| **5b** | #568 (existente, **ampliar alcance**) Edicto | Edicto tras notificación agotada **y directo, sin intentos previos** (interesado desconocido o lugar ignorado, art. 44); anuncio en el BOE como fecha | N1, N5 | Necesario para cerrar una DUP |
| **6** | **N6** Certificado de cierre de la solicitud (sustituye a #801) | `CERT_CIERRE_SOLICITUD`: cuenta sellos, no sella nada; PDF a `Solicitud.documento_cierre_id`; docstring; informe | N4 | Consumible por solicitudes posteriores (explotación) |
| **par.** | #431, #430, #924, #432 (existentes) | Poblado de `interesados_expediente` | — | En paralelo; N5 los necesita para funcionar con datos reales (hasta entonces, TITULAR y datos ficticios) |
| **par.** | #912, #894 (existentes) | Filtro de resultado del seguimiento; documentación ADR-045 | — | Independientes de este trabajo; se colocan cuando convenga |
| **aparte** | **N7** Los servicios que pintan leen primero el sello; los invariantes recogen lo que dice cada sello | Ver 4.6 | N3, N4 | |
| **aparte** | **N8** Regla general de documentos usados | Un documento vinculado a una tarea no se altera salvo corrección con bitácora; hoy `pool_editar_documento` no distingue ni registra | — | La protección total de los citados por un certificado va en N3 y N4 |
| **aparte** | **N9** Unificar `CERT_FIN_INSTRUCCION` en `certificados` | Con su sello de #838 | N3 | |
| **futuro** | Parser completo de Notifica-PNT | Dato «Obligado», fecha de cada estado, mapeo de estados | N1 | Hoy el registro es manual |
| **ajenos** | #796, #925, #839, #795 | Suspensión, actuaciones complementarias, proyección de plazos | — | Fuera de este trabajo |

**Orden lineal propuesto:** N1 → N2 → (#922) → N3 → N4 → N5 → #568 → N6. N5 puede adelantarse o ir en paralelo a N3-N4; #431 y los otros poblados, en paralelo desde el principio.

### 7.4 Qué hacer con #921 y #801, y qué se traslada

Se cierran con un comentario idéntico, sin reescribirlos. Antes hay que trasladar a los issues nuevos lo aprovechable:
- **De #921 a N5 y #568:** los 9 puntos del mecanismo multi-destinatario (columna de destinatario, quitar `UNIQUE(tarea_id)`, `Tarea.notificacion` a lista, `_estado_notificar` agregado, servicio de `_TRAMITES_CON_NOTIFICACION_MULTIPLE`, poblado desde `interesados_expediente`, certificado de notificación múltiple, `canal` por fila, corrección del parser).
- **De #921 a N4:** el patrón «recorre y escribe», el gesto manual como `cert_fin_instruccion`, `deshacer` con justificación y el permiso `gestionar_estructura`.
- **De #801 a N6:** la lista de tests (una finalizadora, varias cerradas, alguna sin cerrar, `CUMPLIDO`).
- **Desactualizado en #921** (no copiar tal cual): el «criterio de acreditación por canal» trata el rechazo por 10 días como INCORRECTA; ahora es RECHAZADA (4.4). Tampoco vale la columna `Fase.documento_cierre_id` ni el anclaje del plazo a los certificados.

### 7.5 Propuesta de «Próximo» para `CONTEXTO_ACTUAL` (a confirmar al crear los issues)

El foco sigue siendo completar la DUP. Pasa a N1 y N2 (con #922 a continuación), después N3 y N4 y luego N5 con #568, cerrando con N6. #431, #430, #924 y #432 en paralelo hasta que N5 los necesite; #912 y #894 se intercalan cuando convenga. Según la regla de `CLAUDE.md`, solo se propone: lo confirma Carlos.

---

## 8. Cuestiones aparcadas o a verificar en la implementación

- **Consumidos ilimitados.** ¿Se pueden seguir vinculando consumidos cuando ya están todos los tipos de entrada del catálogo? Hoy sí: `editar_tarea` no valida contra el catálogo ni limita el número, y solo lo impide el sellado de fase cerrada; el radar y la sugerencia dejan de ofrecer entradas cuando la tarea ya tiene producido. Se abre cuando surja la necesidad.
- **Fecha de fin de fase al ampliar el cierre a otras fases.** `informe_instruccion._fecha_cierre` y `cert_fin_ip_consultas` leen `documento_resultado.fecha_administrativa` como fecha de fin y la perderían con un certificado sin fecha (D6); lo decide el issue que elimine esa fecha.
- **Fichero compartido en el PDF polivalente.** Verificar que mover a la carpeta ESFTT el fichero compartido por dos filas `Documento` no deja a la otra con la ruta antigua.
- **Nombre de `JUSTIFICANTE_SEDE`** y del tipo del resto (a confirmar).
- **Consultas del árbol.** La propiedad `documento_cumplimiento` recorre varios niveles; evitar una consulta por elemento mientras no haya sello.
- **`esquema_editable.py`:** confirmar si consulta el catálogo.
- **Qué trámites reciben las filas de entrada** en `tramites_tareas_documentos` (unos 31 tienen una tarea `NOTIFICAR`).
- **Justificantes individuales del caso múltiple** (4.3): valorar consumidos del certificado múltiple.
- **Resultado por canal (4.4):** la notificación caducada de la primera muestra no era una sede en papel: el administrativo olvidó marcar el check de obligado (Carlos). Resuelto: el canal NOTIFICA implica vía obligatoria o elegida; `numero_intento` solo en POSTAL; no consta rechazo en BandeJA ni SIR. Pendiente de implementar: el edicto directo sin intentos previos (#568). **Decidido:** «Caducada» → INCORRECTA con aviso, con el refinamiento para NIF de entidad; Anulada y No entregada no entran en BDDAT; no se cotejan más muestras hasta implementar el parser. **Abierta:** si el 30.5 se aplica al plazo de 10 días naturales del 43.2 (investigación de jurisprudencia posible).

---

## 9. Fuera de alcance por ahora

- Todo el frontend: `NotificarEditor` (pierde los campos de fecha), autorrelleno del pool por tipo, interfaz de sede y de cierre, distinguir los consumidos de `NOTIFICAR` por tipo.
- Saber si un interesado está **obligado** a lo electrónico o lo **eligió** (arts. 14.2 y 43.2): hoy no hay dato en `entidades` ni en `interesados_expediente`.
- Si existe dato de notificación electrónica (email, SUR), hacerla: hoy es manual.
- Parsear automáticamente si una puesta a disposición fue fallida: futuro, cuando se automaticen las notificaciones.
- El parser completo de Notifica-PNT (dato «Obligado», fecha de cada estado, mapeo de estados de 4.4): se implementa después; hoy el registro del resultado es manual.
- El aviso del 41.6 como dato propio (se cubre con la justificación de sede).
- Notificación defectuosa (40.3) y fecha de conocimiento.
- Acceso voluntario en sede que adelanta la fecha de efectos (41.7).
- Recursos y firmeza: BDDAT no modela hoy esos plazos.
