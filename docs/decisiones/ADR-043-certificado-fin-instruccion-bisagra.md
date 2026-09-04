# ADR-043 — El certificado de fin de instrucción como bisagra entre instrucción y resolución

**Estado:** Adoptada — §A-§E implementados en #827 (**§E reescrita el 2026-09-04**: el gesto pasa
de puerta a revisión que se consolida); §F implementado en #838 salvo el trámite del art. 87 (#839)
**Fecha:** 2026-09-02
**Depende de:** ADR-001 (motor agnóstico), ADR-037 (vocabulario ESFTT vs permiso de motor), ADR-041 §D bis (anclas documentales de la solicitud), ADR-036 (sellado de fase cerrada)
**Precisa:** ADR-037 §Test operativo — qué separa de verdad a los dos árbitros, ver §B
**Origen:** hilo de revisión de alcance de #823 (2026-09-02), sobre el hallazgo `HUECO_PRECEDENCIA_AL_CREAR` de #814.

---

## Contexto

`check_invariante` no tiene rama `CREAR` (`invariantes_esftt.py:139-147`): ninguna precondición
de precedencia se evalúa al crear un nodo del árbol. `crear_tramite`/`crear_tarea` solo miran
`check_invariante('MUTAR', …)` sobre el padre —el sellado de ADR-036— y `crear_fase`
(`mutaciones_arbol.py:380`) no llama a invariantes en absoluto. Verificado en AT-15: la fase
`RESOLUCION` se creó con `ANALISIS_SOLICITUD` sin finalizar, sin usar ninguna vía de escape.

### Qué comprueba hoy el motor al abrir la fase de resolución

Seis reglas activas casan con el sujeto (4 específicas de `RESOLUCION` + 2 genéricas):

| Regla | Condición | Qué mira realmente | Norma |
|---|---|---|---|
| 36 | `tramite_requerimiento_sin_respuesta` | una **tarea**: `ESPERAR_PLAZO` de cualquier `REQUERIMIENTO_SUBSANACION` sin producido | — (`norma_id` NULL) |
| 37 | `organismos_todos_terminados = false` | el campo `resultado` de `organismos_expediente`, **no** la fase `CONSULTAS` | — (NULL) |
| 38 | `fase_ip_finalizada = false` AND `solicitud_incluye_dup` | la fase IP: existe + `documento_resultado_id NOT NULL` | — (NULL) |
| 1718 | `fase_ip_finalizada = false` AND `instrumento_ambiental = 'AAU'` | ídem | DL 26/2021 DF 4ª |
| 83 (`ANY/ANY/ANY`) | fase ≠ `ANALISIS_SOLICITUD` AND `tasa_impagada` | requisito documental | Ley 10/2021 art. 45.1 |
| 1471 (`Renovable/AAP/ANY`) | ídem + sin permiso de acceso | requisito documental | RDL 23/2020 art. 1 |

Ninguna comprueba "la fase precedente existe, está finalizada y es favorable", en tres
sentidos distintos:

1. **Nadie mira "favorable".** Ninguna condición lee `resultado_fase_id`. El patrón
   "finalizada + favorable" existe una vez —`tiene_solicitud_aap_favorable`— y lo consume
   `catalogo_plazos` (art. 131.1 RD 1955/2000), no el motor. `Fase.finalizada_favorable`
   (`fases.py:149`) no tiene ningún consumidor.
2. **Solo dos miran una fase.** La 37 agrega el estado de los organismos y devuelve `True`
   —no bloquea— si el expediente no tiene ninguno dado de alta. La 36 baja al nivel de tarea.
3. **Ninguna generaliza.** Cada regla nombra una fase o un trámite concreto; no hay ninguna
   para `RECONOCIMIENTO_INTERESADO`, la otra fase finalizadora.

`existe_fase_finalizadora_cerrada` está registrada y activa en `catalogo_variables` sin que
ninguna regla, plazo, requisito ni ítem técnico la consuma.

### El diseño que este ADR sustituye

#814 y #823 resolvían el hueco con un invariante: *no se abre una fase finalizadora mientras
otra fase de la solicitud siga sin finalizar*, con el argumento de que "no hay norma que citar".
El argumento es falso —el art. 82.1 LPACAP fija el orden con precisión— y el diseño comprueba
**el síntoma** (fases sin cerrar) en lugar de **el acto** (la instrucción se declara terminada).

---

## Decisión

### A — La bisagra es un documento, no un recuento de fases

La fase finalizadora no se abre porque el sistema recuente el estado de las demás fases: se
abre porque consta emitido el `CERT_FIN_INSTRUCCION` de esa solicitud.

> **Art. 82.1 LPACAP** — «Instruidos los procedimientos, e inmediatamente antes de redactar la
> propuesta de resolución, se pondrán de manifiesto a los interesados…»

El orden legal es instrucción concluida → audiencia → propuesta → resolución, y el art. 88.7
añade la propuesta de resolución cuando instruir y resolver no recaen en el mismo órgano. Ese
"instruidos los procedimientos" es un hecho que alguien declara, y el catálogo ya tiene el
documento que lo declara: `CERT_FIN_INSTRUCCION` (`tipos_documentos` id 3, origen INTERNO),
descrito como *«generado automáticamente por BDDAT al completarse todas las fases de instrucción
requeridas. Recoge el tipo de expediente, fases completadas, resultados y fundamento jurídico
que habilita la resolución»*, y declarado **ENTRADA obligatoria** del `ELABORAR` (orden 1) del
trámite `ELABORACION` — primer trámite de las dos fases finalizadoras.

### B — La instrucción concluye siempre, también en la terminación anormal

**No hay ningún caso en que la ley permita abrir la resolución con la instrucción sin concluir.**
"Instruidos los procedimientos" abarca la terminación normal y la anormal: en desistimiento,
renuncia y caducidad la instrucción también termina, solo que con otro resultado. El art. 21.1
párr. 2 no exceptúa nada — dice que en esos casos *«la resolución consistirá en la declaración
de la circunstancia que concurra, con indicación de los hechos producidos y las normas
aplicables»*: hay resolución, y para dictarla hay que haber constatado esa circunstancia, que es
precisamente actividad de instrucción y produce documento.

Los tres casos tienen (o deben tener) mecanismo de cierre propio, no excepción:

- **Desistimiento tácito por falta de subsanación** (art. 68.1): el plazo vence y
  `certificados.crear_cert()` emite el `CERT_PLAZO_CUMPLIDO` de esa `ESPERAR_PLAZO`
  —exige `estado == 'VENCIDO'` y lo vincula como PRODUCIDO de la tarea
  (`certificados.py:19-20, 97-102, 67`)—. Con eso la tarea queda ejecutada, el trámite puede
  finalizar y la fase cerrarse; la resolución consume ese resultado y toma
  `TENIDA_POR_DESISTIDA` (`tipos_resultados_fases` id 7, junto a `DESISTIDA` y `ARCHIVADA`).
- **Renuncia**: es expresa — hay escrito del interesado que instruir e incorporar.
- **Caducidad** (art. 95): por paralización imputable al interesado, con advertencia previa; el
  transcurso se acredita igual que cualquier otro plazo.

De aquí se sigue el reparto:

| Hecho | Dónde vive | Régimen |
|---|---|---|
| Sin certificado de fin de instrucción no se abre la fase finalizadora | `reglas_motor`, LPACAP art. 82.1 | bloqueo con cita; escapable con justificación en bitácora |
| No se emite el certificado con fases de la solicitud sin cerrar | invariante, en el **emisor** (§E) | puerta cerrada |

**Qué significa el escape, ya que no hay excepción legal.** No representa "la ley admite otra
cosa": representa "el sistema todavía no sabe reflejar esto" — un mecanismo de cierre que aún no
existe, un catálogo incompleto, un dato mal cargado. Es una válvula de tramitación bajo
responsabilidad, con constancia en bitácora de que se avanzó sin fundamento documental, y su uso
repetido es la señal de que falta construir un mecanismo de cierre, no de que sobre la regla. Lo
que el escape **no** permite en ningún caso es falsear el fundamento: el certificado sigue sin
poder emitirse (§E, puerta cerrada), también con el motor en modo global `INACTIVO`.

**Precisión sobre ADR-037.** Su test operativo se ha venido leyendo como "¿hay norma que citar?
→ motor; ¿no la hay? → invariante", y así lo aplicó #823 para clasificar este check como
estructural. El criterio que de verdad separa a los dos árbitros es otro:

- A `reglas_motor` va el **contenido normativo**: citable a norma y artículo, mostrable al
  usuario al bloquear, y susceptible de cambiar cuando cambie la ley o de variar por tipo de
  expediente o de solicitud. Es el caso de §A.
- Al invariante va la **afirmación sobre la realidad del propio sistema**: aquella cuya negación
  no sería una excepción sino una falsedad. Certificar que la instrucción terminó cuando no ha
  terminado no es un juicio de negocio discutible: es un documento que miente. Es el caso de §E.

La ausencia de norma nunca fue el criterio; era un síntoma que coincidía en los ejemplos de
ADR-037 (integridad hoja a hoja, sellado, completitud de cierre) y que aquí no coincide.

### C — Sujetos explícitos, una regla por fase finalizadora

Cada fase finalizadora lleva su propia fila, con el sujeto nombrando la fase —y el tipo de
solicitud cuando es él quien la determina—, no una regla única con sujeto genérico:

| Acción | Sujeto | Condición | Norma |
|---|---|---|---|
| `CREAR` | `ANY/ANY/RESOLUCION` | `solicitud_tiene_cert_fin_instruccion = false` | LPACAP art. 82.1 |
| `CREAR` | `ANY/INTERESADO/RECONOCIMIENTO_INTERESADO` | ídem | LPACAP art. 82.1 |

`RECONOCIMIENTO_INTERESADO` es la fase finalizadora de la solicitud `INTERESADO`
(`tipos_solicitudes` id 14, "Condición de Interesado en el Expediente"): una **solicitud
paralela con vida propia**, que se presenta durante la tramitación del expediente y cuya
resolución se vincula a ella, no a la solicitud original. Lo que ésta produce sobre aquélla es
indirecto —el interesado reconocido se añade a los interesados **del expediente**, y aparecerá
entre los destinatarios cuando se notifique la resolución de la solicitud original—. Las dos
finalizadoras nunca conviven en la misma solicitud; por eso el alcance del check es **por
solicitud**, y no por haberlo elegido entre varias opciones posibles.

Escribir el sujeto explícito, en vez de un `ANY/ANY/ANY` con una condición del tipo
"es_finalizadora", evita **permeabilidad en la permisividad**: el sujeto es lo que documenta a
quién aplica la regla y lo que el supervisor lee en la UI del motor. Con el sujeto genérico, el
filtro real se escondería en una función Python y la fila quedaría ilegible; y cualquier error
en esa función abriría o cerraría la puerta en fases que nadie nombró. El precio —acordarse de
añadir fila si algún día aparece una tercera finalizadora— se paga con una comprobación de
arranque en el manifiesto de catálogo (`app/checks/catalogo_requerido.py`, #347) que avise de un
`TipoFase.es_finalizadora` sin regla que lo nombre.

**Sobre el ámbito de la variable.** `solicitud_tiene_cert_fin_instruccion` es booleana, y por sí
solo el nombre no dice de qué solicitud habla; el motor tampoco lo sabe, porque solo recibe el
dict ya calculado. Quien fija el ámbito es el assembler: al crear una fase, el objeto actuado es
`{'solicitud': …, 'tipo_fase': …}` y `ctx.solicitud` devuelve **esa** solicitud
(`assembler.py:59-60`), que es contra la que se evalúa —el mismo mecanismo que ya usan
`fase_ip_finalizada` y `tramite_requerimiento_sin_respuesta`—. La preocupación está fundada de
todos modos, porque el precedente contrario existe: `organismos_todos_terminados` lee
`ctx.expediente.organismos` y **sí** es permeable entre solicitudes del mismo expediente. Para
que aquí no ocurra, tres condiciones expresas:

1. Nombre que declara el ámbito (`solicitud_tiene_...`), no `existe_cert_...`.
2. Lectura por la **FK propia de la solicitud** (§D), nunca buscando el tipo documental en el
   pool del expediente.
3. Docstring que lo haga explícito, junto al aviso de que el pool es del expediente y no
   distingue solicitudes por sí solo.

### D — Anclaje: `solicitudes.documento_fin_instruccion_id`

`Documento` tiene un solo FK, a expediente (`documentos.py:18-27`). El patrón de anclaje a
solicitud ya existe dos veces, y ADR-041 §D bis lo razonó: `documento_solicitud_id` ancla la
fecha de inicio del plazo (art. 21.3.b) y `documento_cierre_id` la de fin (art. 40.4,
`CERT_CIERRE_SOLICITUD`). El fin de instrucción es la bisagra entre ambos y toma la tercera
columna, con la misma forma: **entrada → fin de instrucción → cierre**.

Es también lo que hace verdadera la variable de §C. No vale localizar el certificado buscando su
tipo en el pool del expediente: es lo que hace hoy
`cert_fin_ip_consultas._buscar_existente(expediente_id, solicitud_id)`, que **recibe
`solicitud_id` y no lo usa** —filtra por expediente + tipo—, de modo que con dos solicitudes en
el mismo expediente la segunda reutiliza el certificado de la primera. Deuda existente que este
ADR pone a la vista y que la solución no debe heredar.

Tampoco cuelga de una tarea ni de una fase: cada tarea produce lo que su trámite le dice y no
hay ninguna a la que este certificado corresponda, y una fase no representa el conjunto de la
instrucción (`CertificadoFase.fase_id` quedaría NULL, sin vínculo con la solicitud).

### E — El gesto es una revisión que a veces se consolida

> **Reescrita el 2026-09-04 (#827).** La redacción anterior hacía del emisor una puerta que
> concede o deniega, y de la emisión un acto que sigue adelante aunque el motor siga bloqueando
> —«esas son contenido normativo escapable y bloquean donde les toca»—. Al implementarlo se vio
> el efecto: un certificado que declara bloqueada la resolución **ocupa el ancla de §D** y, como
> deshacerlo es #838, impide emitir el bueno cuando se resuelva lo que faltaba. El texto que
> sigue lo sustituye. Lo que no cambia: §A, §B, §C, §D y §F.

El técnico puede preguntar **en cualquier momento** «¿cómo va esto?», desde el primer día de la
solicitud. La respuesta es siempre un **informe**, y solo cuando el informe sale sin pendientes
ese mismo informe **se consolida** como el certificado. El certificado deja de ser un permiso que
se concede y pasa a ser el acta de una revisión que salió limpia.

Dos desenlaces, ningún error:

| Informe | Qué ve el técnico | Qué queda |
|---|---|---|
| con pendientes | modal: qué falta, por qué, y el resumen de lo instruido | nada — se puede volver a preguntar mañana |
| sin pendientes | el PDF | `CertificadoFase` + `Documento` + la FK de §D |

**Por qué no se consolida con pendientes.** Un certificado que dice «esto no está listo» no
acredita nada: no sirve como ENTRADA del `ELABORAR` que el catálogo le exige ser, no sirve de
ancla para el sello de #838, y ocupa el sitio del certificado válido. La emisión con constancia
del bloqueo era peor que no emitir.

**Las tres categorías del informe.** No basta con «pasa / no pasa», porque el técnico necesita
distinguir lo que le queda por hacer de lo que ya resolvió bajo su responsabilidad:

1. **Pendiente** — una comprobación no pasa y nada la explica. Impide consolidar.
2. **Salvado con criterio** — el acto se realizó por la vía de escape, con justificación en
   bitácora. **Se relata en el certificado y no impide consolidar**: el criterio motivado del
   tramitador es superior a la regla —para eso existe el escape— y por eso queda escrito, no
   escondido. Como el certificado es ENTRADA del `ELABORAR` de la resolución, quien la redacta
   tiene delante las desviaciones que debe motivar; hoy esa información muere en la bitácora.
3. **Pasa** — nada que decir.

El sistema **no correlaciona** hoy el escape con la regla que se saltó: el registro de bitácora
guarda `{escape, justificacion, sujeto}` y no qué regla se esquivó, y `evaluar()` cortocircuita
en la primera, de modo que en el momento del escape ni siquiera se conocen todas. El informe
presenta por tanto **dos listas separadas** —lo que hoy no pasa, y los actos realizados bajo
justificación— y deja la correlación al lector. Automatizarla es de #614.

**Qué comprueba el informe.** Tres fuentes, y ninguna reemplaza a las otras:

- **El motor**, una sola vez, sobre el acto que importa: crear la fase finalizadora. Las reglas
  de precedencia hacia ella *son* el veredicto normativo sobre si la instrucción está lista
  (requerimientos sin respuesta, organismos, IP, tasa). No se pregunta al motor nodo a nodo: sus
  reglas son de un acto, no de un nodo, y re-evaluar sobre lo ya creado es arqueología —las
  reglas cambian, y un nodo de junio dispararía hoy una regla que no existía.
- **El estado del árbol**, consumiendo `estado_dominio` en vez de reimplementarlo: es el núcleo
  único de las reglas de estado, y duplicarlo repetiría la divergencia que #558 tuvo que unificar.
- **El invariante estructural** de esta sección, que sigue siendo el mismo y ahora se expresa como
  un pendiente más de la lista, no como un 422 que corta la conversación.

**Quién produce ese pendiente, en realidad (precisión de #827 al implementarlo).** No hace falta
preguntarle al invariante para redactarlo: sus dos supuestos ya los dice el árbol por sí mismo —una
fase de instrucción sin cerrar levanta su propio pendiente, y la solicitud sin ninguna fase habla
de sí misma con el vocabulario del árbol, que es como se cubre el agujero de vacuidad donde no hay
nodos que hablen—. El invariante sigue existiendo y **se comprueba igualmente antes de crear nada**:
es la puerta cerrada, la que seguiría aplicando con el motor en modo global `INACTIVO`, y la que
tiene la última palabra si alguna vez discrepara del informe. Que ambos digan lo mismo por caminos
distintos es deliberado; que puedan divergir en silencio, no.

**El invariante** (el punto 3 de #823, mudado del acto de crear la fase al de certificar): **no se
consolida si alguna fase de instrucción de la solicitud no está finalizada**, contando las
planificadas —una fase creada es una fase que alguien decidió necesaria; si sobra se borra, si
hace falta se termina—. Y tampoco si no hay ninguna fase: `all([])` es `True` y certificaría una
instrucción inexistente, mismo agujero de vacuidad que #723 tapó en `Tramite.finalizado`.

Dos precisiones sobre esa frase, ambas de #827:

- **Son las fases de instrucción** (`es_finalizadora = False`), no todas las de la solicitud.
  Contar la finalizadora se muerde la cola: §A admite abrirla por la vía de escape, y entonces
  esa fase queda sin finalizar y el certificado sería inemitible para siempre salvo borrándola —
  justamente el estado en que #814 encontró AT-15. Y «instruidos los procedimientos» no abarca la
  fase que resuelve.
- **Se exige finalizadas, sea cual sea el resultado**: por §B un desfavorable o un desistimiento
  cierran la instrucción igual que un favorable. El juicio sobre el sentido del resultado vive en
  el contenido del certificado y en la resolución que lo consume.

Sigue sin ser redundante con las reglas #37/#38: esas vigilan que una fase **necesaria** se cree y
se complete; ésta, que no queden flecos abiertos de lo que sí se abrió. El motor mira lo que
debería haber; el invariante, lo que hay.

**Puerta cerrada, y por eso vive aquí y no en `reglas_motor`** (§B): certificar que la instrucción
terminó cuando no ha terminado no es un juicio de negocio discutible, es un documento que miente.
Sigue aplicando con el motor en modo global `INACTIVO`.

#### E bis — La forma del informe: definido en las hojas, compuesto hacia arriba

> **Precisada el 2026-09-04, al implementarla (#827).** La redacción anterior tomaba de
> `estado_dominio` más de lo que debía: daba por hecho que hacia arriba viajaría **dato**, y que
> el tronco lo redactaría. Lo que sube es prosa ya escrita por cada nodo, y el porqué está más
> abajo.

El informe **no lo produce un script que barre el árbol conociendo las particularidades de cada
tipo**. Cada nodo aporta lo que sabe de sí mismo y el resultado se compone hacia arriba:

```
informe(solicitud) = lo propio de la solicitud + agregación de informe(fase_i)
informe(fase)      = lo propio de la fase      + agregación de informe(tramite_j)
informe(tramite)   = lo propio del trámite     + agregación de informe(tarea_k)
```

Un nodo sin particularidades no dice nada por sí mismo y se limita a lo que digan sus hijos.

**Lo que sube es prosa, no dato en bruto.** Cada nodo entrega un bloque **ya redactado por él**, y
su padre recibe bloques —no datos— y decide si los cita, los resume en una línea o los descarta.
No es una preferencia de estilo. Si subiera dato, el tronco tendría que **entenderlo** para poder
redactarlo —saber que esta ronda de consultas se hizo sobre el Anexo 1 y aquella sobre el proyecto
original—, y eso devuelve la especialización al tronco por la puerta de atrás, que es exactamente
lo que este apartado prohíbe. Y produce además un documento ilegible para una persona: impecable
como estructura de datos, inservible como certificado. La alternativa —un compilador en el tronco
que sepa presentar cada caso— es la misma especialización, escrita en otro sitio.

**Lo único que el tronco interpreta es la categoría** (pendiente / salvado / pasa), que es
agnóstica: cualquier fase sabe decir «esto impide cerrar» sin que el tronco sepa por qué. De
`estado_dominio` se toma exactamente ese reparto —un dato mínimo para decidir, y todo lo demás
como decoración de quien lo muestra—, no la forma concreta de su contrato.

**Tres textos por nodo, no uno**, porque los destinos no comparten registro: el certificado
**narra** lo instruido, el modal del inspector **enumera** lo que falta y lleva al nodo, y los
actos salvados con criterio van en su propia sección (§E: dos listas separadas, sin correlacionar).
El nodo escribe los tres, y así ningún destino tiene que reescribir el que no le sirve.

**Redactado, no maquetado.** Los párrafos suben en texto llano, sin marcado, porque sus
consumidores usan motores distintos: reportlab en el PDF, HTML en el modal del inspector y
—previsto desde ahora— el contexto del escrito de resolución, que convertirá estos mismos párrafos
en tokens de plantilla en vez de recomponer el relato por su cuenta. Si el nodo maquetara, se
ataría al primero de los tres.

**No es un patrón nuevo en este proyecto**: es el de `estado_dominio.py`, con su contrato
`(estado, propio)` —donde `propio` significa «el nodo tiene algo que decir POR SÍ MISMO»—, un
núcleo único y dos consumidores que ponen encima su propia decoración. El punto de extensión
natural para las particularidades es un registry por código de tipo, como el `@variable` del
motor, con «sin particularidades» de comportamiento por defecto.

**Por qué no basta con el genérico, con nombre y apellidos.** Un modificado de proyecto puede
obligar a repetir consultas, trámite ambiental e información pública, y **cada ronda se somete
sobre un conjunto documental distinto** (Proyecto; Proyecto + Anexo 1; …). El certificado tiene
que reflejarlo, porque es la base sobre la que se redacta la resolución: quien resuelve necesita
saber sobre qué versión del proyecto lo hace. Eso solo lo sabe la fase que consultó, y ninguna
función genérica puede deducirlo. Es el contenido de **#819**, que además es hoy el primer
consumidor real del punto de extensión.

**Orden de construcción (decisión de #827, 2026-09-04):** primero el **contrato** y el esqueleto
recursivo, probados por su primer consumidor —este certificado—; el **registry** de
particularidades cuando #819 defina el vínculo fase↔conjunto documental, porque diseñar el punto
de extensión sin conocer la forma del dato sería adivinar. El contrato debe admitir desde ahora
que un hallazgo se refiera a un **ámbito documental**, aunque hoy ese ámbito sea siempre «el
proyecto del expediente»: no impedirlo es barato ahora y caro después.

Implementado así en `app/services/informe_instruccion.py`: el punto de extensión de #819 es la
función que redacta el bloque de una fase, hoy única y genérica, y el `ámbito` es un campo del
bloque que hoy va siempre vacío. Cuando el registry sustituya a esa función, el resto del módulo
no se entera — sigue recibiendo un bloque redactado, igual que ahora.

#### E ter — Lo que se congela, y el orden que lo hace posible

La consolidación reutiliza `generador_cert.generar_certificado_fase(…, 'CERT_FIN_INSTRUCCION')`,
que ya existe, está probado (`tests/test_373_cert_fase.py`) y **no lo llamaba nadie en
producción**. Congela el `AuditoriaResult` —reglas evaluadas, variables, sujeto—;
`motor_reglas.auditar()` se escribió con este destino declarado en su docstring.

**El orden no es libre.** Las dos reglas de §C casan con el sujeto de la fase finalizadora, así
que mientras el certificado no conste, disparan: auditar y consolidar sin cuidado produce un
snapshot que declara bloqueada la resolución por falta del certificado que lo lleva. El orden es
por tanto: **evaluar primero, sin crear nada; consolidar después**, y la regla del art. 82.1 se
excluye del criterio de «¿limpio?» **por definición** — es la única que este acto satisface, y
esperar a que deje de disparar sola sería esperar a nunca.

**Qué deja ese orden en el snapshot congelado (precisión de #827 al implementarlo).** La regla del
art. 82.1 **consta disparada**, y debe constar: la auditoría es de un momento anterior a que el
certificado existiera, y era cierto que entonces disparaba. Lo que impide que el documento parezca
desmentirse a sí mismo no es maquillar el snapshot —eso sería falsear el fundamento, justo lo que
§B prohíbe—, sino que el PDF la presente como **satisfecha por este certificado** en vez de como
bloqueo. El dato en BD dice la verdad del momento; el PDF la interpreta. La garantía real del
orden es la otra: en el snapshot de un certificado emitido no puede quedar **ninguna otra** regla
bloqueante viva, porque con ella no se habría consolidado.

El contenido del PDF es el que el catálogo describe —*«tipo de expediente, fases completadas,
resultados y fundamento jurídico»*—: el resumen de lo instruido con sus fechas, los actos salvados
con criterio, y la auditoría del motor como respaldo. No solo la tabla de reglas, que es lo que
#373 producía.

### F — El certificado sella la instrucción: reabrir y abrir de nuevo son la misma cara

Emitido el certificado, la instrucción de esa solicitud queda declarada terminada. Hay dos
formas de contradecir esa declaración, y los dos huecos que #823 deja fuera de alcance son
justamente ellas: **reabrir** una fase de instrucción ya cerrada, y **crear** una fase de
instrucción nueva. No son problemas distintos: son el mismo acto —volver a instruir lo ya
certificado— por sus dos extremos, y el mismo check los cubre.

Ninguna de las dos es la vía legítima cuando falta algo para resolver. Las vías son estas:

1. **Recabar algo más antes de resolver → art. 87 LPACAP, dentro de la fase finalizadora.** El
   artículo no autoriza a volver a la instrucción: autoriza a completar dentro de la resolución.
   Vive en el Capítulo V (Finalización), Sección 2.ª (Resolución), después del art. 84, y lo
   acuerda *«el órgano competente para resolver»*, no el instructor — opera cuando la instrucción
   ya cerró y aun así el expediente sigue gris. Se modela como **trámite previo optativo de la
   fase finalizadora**: acuerdo motivado (`ELABORAR`) → `NOTIFICAR` → `ESPERAR_PLAZO` de los 7
   días de alegaciones → `ANALIZAR`, con sus plazos como dato de catálogo (15 días de práctica y
   suspensión del plazo para resolver, ADR-041 §E). **No rompe el certificado**: es un acto
   posterior, dentro de la fase que el certificado habilitó. Su límite lo pone el propio
   artículo — no son actuaciones complementarias los informes que preceden inmediatamente a la
   resolución final.
2. **La instrucción no estaba terminada de verdad → deshacer el certificado.** Desvincular y
   borrar el certificado, deshacer los pasos dados en la fase finalizadora y borrarla; solo
   entonces vuelve a haber instrucción abierta. Acto expreso y caro a propósito.

Por eso el bloqueo es aquí puerta cerrada estructural y no regla de motor: no hay excepción que
citar, porque la ley no abre una excepción — señala otra vía. El mensaje del bloqueo debe
**nombrar esa vía** en vez de prohibir a secas, que es lo que convierte el check en ayuda y no
en obstáculo.

**Hueco de catálogo que esto destapa:** no existe tipo de trámite para las actuaciones
complementarias, y `fases_tramites` no tiene ningún trámite previo en `RESOLUCION` —solo
`ELABORACION`, `NOTIFICACION` y `PUBLICACION`—. `COMUNICACION_AUDIENCIA` existe, pero cuelga de
`COMPATIBILIDAD_AMBIENTAL`.

#### F bis — Puerta cerrada también sin el art. 87 (decisión de #838, 2026-09-04)

> El borrador de §F terminaba diciendo que «sin ese trámite, la única salida practicable ante un
> expediente gris es la que este ADR prohíbe», y de ahí que #838 heredara abierta la pregunta de
> qué hacer mientras #839 no exista. Al implementarlo se comprobó que **esa premisa no se
> sostiene**, y la sección se cierra en firme: puerta cerrada, sin escape transitorio.

Son dos escenarios distintos y ninguno queda encerrado:

- **La instrucción no estaba terminada de verdad** → deshacer el certificado, que es la vía 2 de
  esta misma sección y la construye #838. Cara a propósito, pero existe.
- **La instrucción sí terminó y hace falta recabar algo más** → eso se practica **dentro** de la
  fase finalizadora, y el sello no lo toca: lo que prohíbe es abrir o reabrir fases de
  **instrucción**. Lo que falta es el tipo de trámite en el catálogo, no permiso. Y mientras
  falte, `check_vocabulario_tramite` es forzable con justificación (ADR-037 §B), así que crear un
  trámite atípico en `RESOLUCION` es practicable de forma tosca y **con constancia en bitácora**
  — que es exactamente la señal de que #839 hace falta, el mismo razonamiento que §B aplica al
  escape de la regla del art. 82.1.

El argumento decisivo contra un escape transitorio es su precio relativo: **sería más barato que
deshacer el certificado**. Un clic con justificación frente a un rebobinado. El técnico elegiría
siempre el escape, y el resultado sería un certificado emitido y contradicho — el estado que §E
declaró inaceptable y que el orden evaluar→consolidar se construyó para evitar. No sería una
válvula: sería la vía principal, y desactivaría la bisagra entera.

#### F ter — Qué se hace con el certificado al deshacer (decisión de #838, 2026-09-04)

**Se borra todo el rastro documental**: la FK de §D, el `CertificadoFase`, el `Documento` y el
PDF. Las alternativas eran desvincular —que deja en el pool un certificado huérfano afirmando que
la instrucción terminó, el «documento que miente» que §E declaró inaceptable— y revocar, que
exigiría un concepto de anulación inexistente para un documento interno autogenerado que nadie ha
notificado a nadie. La traza del acto vive donde vive la de todos los actos excepcionales: en
bitácora, y desde ahí la relata el informe del certificado siguiente.

**La precondición es el espejo exacto de la emisión.** Emitir exige que no quede abierta ninguna
fase de instrucción (§E); deshacer, que no exista ninguna de las fases que el certificado
habilitó. Entre las dos, el estado al que se vuelve deshaciendo es el mismo del que se salió al
emitir, y no un híbrido —una resolución a medias apoyada en un certificado que ya no existe—.

**No cascadea nada, y ahí está lo caro.** El rebobinado de la fase que resuelve lo hace el técnico
con lo que ya tiene —reabrirla, que el sello no toca a propósito, y borrarla hoja a hoja (#722)—,
de modo que cada paso pasa por su propio check. Un servicio que arrasara con la resolución entera
para levantar el sello sería justamente lo contrario de un acto caro.

**Y no se registra como escape.** `escape: True` significa una cosa concreta en todo el sistema
—se forzó un bloqueo del motor— y `informe_instruccion._relato_escapes` la da por supuesta al
redactar. Deshacer no fuerza nada: la puerta se abre porque sus condiciones se cumplen. Por eso el
hecho va al **relato** de la solicitud y no a la lista de actos salvados con criterio: es historia
de la instrucción, no desviación.

**Estado de la puerta antes de #838:** `_check_reabrir` solo bloqueaba si `Solicitud.estado`
empezaba por `RESUELTA` **y** había notificación en fase finalizadora, de modo que entre
"resolución notificada" y "solicitud marcada RESUELTA" cualquier fase se reabría. Y `crear_fase`
no llamaba a `check_invariante` en absoluto — era el único `crear_*` sin ninguna precondición
estructural, porque el sellado de ADR-036 no le aplica (una fase no cuelga de otra fase).

**Cuando las dos puertas de `_check_reabrir` aplican, manda la resolución firme (#720).** Una
solicitud resuelta y notificada tiene además su certificado, y lo que cambia es el consejo: con la
resolución firme no hay nada que hacer dentro de este flujo, mientras que el sello sí tiene
salida. Decir «deshaga el certificado» a quien ya notificó la resolución sería mandarle por un
camino que no le corresponde.

**Una guarda que faltaba, y que el sello habría dejado a la vista** (#838). La regla del pool es
«si algo lo usa, no se borra», pero `_documento_es_referenciado` solo miraba proyecto, vínculos de
tarea y notificación: las tres anclas documentales de la solicitud (ADR-041 §D bis y §D de este
ADR) son FK a `documentos` y no estaban en esa lista. Faltaba desde que se creó cada una; lo
destapa el `CERT_FIN_INSTRUCCION` porque es el primero al que **ninguna** de las tres referencias
vigiladas alcanza —no lo consume ninguna tarea mientras la fase que resuelve no exista—. Las FK
son `NO ACTION`, así que el borrado no llegaba a hacer daño, pero moría en un `IntegrityError` en
vez de decir quién estaba usando el documento; y con el sello encima, borrarlo del pool habría
sido la forma barata de levantarlo por la puerta de atrás.

---

## Consecuencias

**Se gana:** una comprobación en lugar de una lista de fases; cita normativa visible al bloquear
—hoy 3 de las 4 reglas de precedencia hacia `RESOLUCION` tienen `norma_id` NULL—; el certificado
catalogado desde el principio deja de estar sin dueño; y el guardián de reapertura gana su ancla.

**Hay que tocar:** migración (columna en `solicitudes`), una variable nueva + su fila en
`catalogo_variables`, dos filas de `reglas_motor` con su norma, el emisor del certificado y su
invariante, y la nota de cabecera de `invariantes_esftt.py`, que hoy enumera las familias de
invariantes sin contemplar precondiciones de creación. Con §E reescrita, además: el informe
recursivo con su contrato, el consumo de `estado_dominio`, la lectura de escapes de bitácora y el
contenido del PDF. Con §F: la rama `CREAR/FASE` del invariante y la llamada que le faltaba a
`crear_fase`, la segunda puerta de `_check_reabrir`, el verbo `DESHACER` con su check, el servicio
que retira el certificado y su endpoint (DELETE sobre el mismo path), el bloque del inspector, y
las tres anclas en la guarda del pool.

**Lo que este ADR cierra sin haberlo abierto:** el diseño de #373 —emitir el certificado *al
crear* la fase `RESOLUCION`, como efecto de esa creación— queda **invertido**, no matizado. Su
ejecución pendiente vivía en #586, que se cierra por eso: si se hubiera implementado después, la
regla del art. 82.1 habría quedado insatisfacible por construcción. El generador de #373 arrastra
ese ADN y hay que corregirlo donde asome (acepta una `fase` y guarda `fase_id`; su PDF hablaba de
«autorizar la creación de la fase indicada» y llevaba el título fijo de un tipo documental
concreto). Los issues que colgaban de aquel diseño heredaron su premisa y hay que revisarla
—#430 la nombra literalmente—.

**Una carencia del registro de escapes, para que no se dé por hecha:** la bitácora guarda
`(tabla, registro_id)` y un detalle con `{escape, justificacion, sujeto}`. No guarda la solicitud,
así que reunir los escapes de una hay que hacerlo desde los ids vivos de su árbol — y un escape
sobre algo que después se borró **es irrecuperable**. Añadir `solicitud_id` a ese detalle lo
resuelve donde ya se compone, y no depende del log completo de transacciones que #614 espera.

**Frente que esto deja a la vista:** los mecanismos de cierre de la terminación anormal (§B).
El del desistimiento tácito existe y funciona (`certificados.crear_cert` sobre la `ESPERAR_PLAZO`
vencida); los de renuncia expresa y caducidad no están comprobados. Mientras falte alguno, el
escape de §B será la vía de hecho para esos expedientes — y esa es exactamente la señal que
indica cuál construir.

**Dependencia asumida:** sin emisor, la regla bloquearía siempre. Y no admite la degradación de
`tasa_impagada` ("catálogo sin poblar → no bloquear"): degradar a permitir deja la regla
decorativa, y degradar a bloquear para la tramitación. Por eso el punto 3 se implementa con el
emisor, no antes.

**Riesgo de repetir un patrón conocido:** ADR-041 §D bis dejó el ancla de `CERT_CIERRE_SOLICITUD`
implementada (#778) y la emisión sin dueño; el efecto es que el plazo de la solicitud no alcanza
`CUMPLIDO` nunca. Este ADR sería el segundo certificado con ancla y sin emisor si se implementa
a medias. Declarado aquí para que no ocurra por omisión.

---

## Mapa de issues del `CERT_FIN_INSTRUCCION`

Ocho issues tocan esta pieza, y hasta 2026-09-04 dos de ellos proponían diseños opuestos. El
mapa vive aquí para que no vuelva a ocurrir: **antes de abrir uno nuevo sobre el certificado, se
mira esta tabla**.

| Issue | Qué le corresponde | Estado tras este ADR |
|---|---|---|
| **#373** | diseño original: emitir el certificado al crear la fase `RESOLUCION` | cerrado en mayo — **superado**: §A lo invierte |
| **#586** | ejecutar el diseño de #373 (la llamada en `crear_fase`) | **cerrado** por incompatible con §A |
| **#827** | §A-§E: columna, variable, las dos reglas, el gesto, el informe recursivo con su contrato, el resumen de lo instruido, los escapes relatados y la consolidación condicionada | activo |
| **#614** | la contradicción del motor apagado (§E, motor global) y la correlación automática escape↔regla | activo, esperando su ADR de bitácora |
| **#819** | el vínculo fase↔conjunto documental de cada ronda; primer consumidor del registry de §E bis | activo |
| **#430** | proyectar `organismos_expediente` → `interesados_expediente` al consolidar | activo, con la premisa corregida |
| **#838** | §F, primera pieza: el sello de la instrucción anclado al certificado —cubre a la vez reabrir una fase cerrada y crear una de instrucción nueva— y el acto que lo retira | **implementado** (§F bis/§F ter) |
| **#839** | §F, segunda pieza: el trámite de actuaciones complementarias del art. 87 | activo — **ya no bloquea a #838** (§F bis): sin él la vía existe, solo que tosca y forzando el vocabulario |

Fuera de la tabla pero emparentados: **#823** se queda con sus puntos 1 y 2 (invariantes
estructurales sin norma que citar, independientes de este ADR), y **#801** es el hermano
`CERT_CIERRE_SOLICITUD` — mismo patrón de ancla sin emisor, otro momento del procedimiento.

**La contradicción que #614 hereda, para que no se «arregle» al revés.** `auditar()` no pasa por
`motor_modo_global` — está escrito a propósito en la cabecera de ese módulo. Con el motor en
`INACTIVO` eso produce un callejón: la auditoría del informe ve reglas disparadas, pero al crear
los nodos el motor no bloqueó, así que no hubo escape ninguno que relatar y el certificado no
puede consolidarse por una vía que nunca estuvo abierta. **La salida no es hacer que `auditar`
respete el modo global**: eso produciría certificados que afirman «todo satisfecho» porque el
comprobador estaba apagado. La contradicción es el precio de que el certificado sea honesto, y se
resuelve en #614 por otro camino.

---

## Lo que este ADR no decide

- ~~**El momento de emisión** del certificado~~ — **decidido en #827 (2026-09-03): acto expreso
  del técnico**, desde el inspector del nodo solicitud. «Instruidos los procedimientos» es un
  hecho que alguien declara (§B): automatizarlo al cerrar la última fase lo volvería efecto
  colateral de otro acto, «la última fase» no es determinable —nada impide que aparezca otra
  después— y sería opaco justo cuando el invariante de §E impida la emisión. El certificado se
  ancla solo como parte del gesto: no hay vinculación manual desde el pool.
- ~~**Qué ocurre con el certificado al reabrir** una fase: si se revoca, se desvincula o se borra,
  y con qué acto~~ — **decidido en #838 (2026-09-04)**: no se reabre nada con el certificado
  puesto; el acto es retirarlo, y retirarlo **borra** la FK, el `CertificadoFase`, el `Documento`
  y el PDF (§F ter).
- **El diseño del trámite del art. 87** (código, tareas, cardinalidad, entradas del catálogo de
  plazos, y si la audiencia del art. 82 merece trámite propio en la misma frontera): §F fija
  dónde vive —dentro de la fase finalizadora— y por qué, no cómo se escribe en el catálogo.
- Si `CERT_CIERRE_SOLICITUD` (ancla sin emisor desde #778) se resuelve en el mismo movimiento —
  mismo patrón, distinto momento del procedimiento (#801).
- ~~El contenido y formato del PDF~~ — **§E ter fija el contenido** (el que el catálogo describe:
  fases, resultados, fechas, actos salvados con criterio, auditoría como respaldo). El formato
  sigue abierto.
- **La forma del punto de extensión** del informe recursivo: §E bis decide que lo habrá y por qué,
  y aplaza su diseño a que #819 defina el vínculo fase↔conjunto documental.
- Qué se hace con las reglas 36/37/38 y su `norma_id` NULL: documentarlas con su norma o aceptar
  explícitamente que `reglas_motor` contiene reglas de workflow. **Sube de prioridad con §E**: el
  informe promete decir «qué falta y **por qué**», y esas tres son las que vigilan la instrucción
  — dos de cada tres respuestas se quedarían sin el porqué delante del usuario.

---

## Alternativas descartadas

**Invariante "todas las fases finalizadas" al crear la finalizadora** (el diseño de #814/#823).
Comprueba el síntoma en vez del acto; no generaliza a la otra fase finalizadora sin repetir la
lista; y deja el `CERT_FIN_INSTRUCCION` catalogado, declarado obligatorio y sin nadie que lo
emita. Su análisis no se pierde: es el contenido de §E.

**Regla única con sujeto `ANY/ANY/ANY` y una condición "el tipo de fase es finalizadora".**
Cubriría de una vez las finalizadoras presentes y futuras, pero el sujeto dejaría de documentar
a quién aplica la regla: el filtro real viviría en una función Python y el supervisor leería una
fila ilegible. Permeabilidad en la permisividad — §C.

**Anclar el certificado a una tarea o a una fase.** No hay tarea natural —cada tarea produce lo
que su trámite le dice— y la fase no representa el conjunto de la instrucción.

**Buscar el certificado por tipo en el pool del expediente, sin FK.** Es lo que hace hoy
`CERT_FIN_IP_CONSULTAS`, y confunde solicitudes distintas del mismo expediente (§D).

**Tratar desistimiento, renuncia y caducidad como excepción a §A** (borrador anterior de este
ADR). Parte de una lectura incorrecta: en los tres casos la instrucción concluye y la fase se
cierra con su resultado; lo que hace falta no es una excepción, son los mecanismos de cierre
de §B.

**Emitir el certificado aunque queden reglas bloqueantes, dejando constancia** (redacción
original de §E). Produce un documento que no acredita nada —no sirve como ENTRADA del `ELABORAR`
ni de ancla para #838— y que además **ocupa el ancla de §D**, de modo que impide emitir el válido
cuando se resuelva lo que faltaba, porque deshacerlo es #838. Sustituida por la consolidación
condicionada.

**Un certificado volátil, que no persista.** Tentador desde el momento en que se ve que el
contenido es una auditoría del motor: bastaría un modal informativo. Pero el catálogo lo declara
**ENTRADA obligatoria** del `ELABORAR` de `ELABORACION` —una foto no se vincula como entrada de
una tarea— y #838 se quedaría sin nada que sellar. Lo que sí es volátil es **la consulta**: por eso
§E separa el informe (repetible, sin efectos) de su consolidación (única, con efectos).

**Escapar de la auditoría con justificación** (#614, punto 2, segunda mitad). La auditoría no
prohíbe nada, así que ese escape no sería una excepción a una regla: sería una excepción sobre el
acto de certificar — el certificado eximiéndose a sí mismo. Lo que el informe hace es señalar la
desviación no salvada; la salida es tramitar. Los escapes **previos**, en cambio, sí se relatan
(§E, categoría 2): esos ampararon un acto real y llevan justificación del tramitador.

**Preguntar al motor nodo a nodo en el barrido recursivo.** Las reglas del motor son de un acto,
no de un nodo: la única pregunta posible sobre lo ya creado es «¿se permitiría crear esto hoy?»,
que es arqueología y no estado — las reglas cambian, y un nodo antiguo dispararía reglas que no
existían al crearlo. Además es innecesario: las reglas de precedencia hacia la fase finalizadora
ya son el veredicto sobre si la instrucción está lista, en una sola pregunta.

**Un sello escapable con justificación mientras el trámite del art. 87 no exista** (la pregunta
que #838 heredaba abierta). Parte de una premisa que el código desmiente: sí hay salida sin ese
trámite (§F bis). Y sería contraproducente aunque no la hubiera, porque el escape resultaría **más
barato que deshacer el certificado** —un clic frente a un rebobinado—, de modo que dejaría de ser
una válvula excepcional para convertirse en la vía normal, con el certificado emitido y
contradicho que §E declaró inaceptable.

**Desvincular el certificado en vez de borrarlo, o revocarlo** (§F ter). Desvincular deja en el
pool un documento que sigue afirmando que la instrucción terminó; revocar exige un concepto de
anulación que no existe, para un documento interno autogenerado que nadie ha notificado a nadie.

**Que el servicio de deshacer borre en cascada la fase finalizadora.** Convertiría en un clic lo
que §F describe como «acto expreso y caro a propósito», y saltaría los checks que cada paso del
rebobinado tiene por su cuenta (#722 hoja a hoja, #720 sellado). Lo caro no es fricción
decorativa: es que cada borrado se mire.

**Amparar en el art. 87 la apertura de una fase de instrucción con la finalizadora ya abierta**
(borrador anterior de este ADR, que lo llamaba "reverso" y lo mandaba a `reglas_motor` como
bloqueo escapable). Lectura equivocada del artículo: está en la sección de Resolución, lo acuerda
el órgano que resuelve y presupone la instrucción cerrada. Es una vía de escape para cuando los
actos de instrucción previstos no bastan y no caben en ningún otro sitio — y ese sitio es la
propia fase de resolución, no una fase de instrucción reabierta que desmentiría el certificado
(§F).
