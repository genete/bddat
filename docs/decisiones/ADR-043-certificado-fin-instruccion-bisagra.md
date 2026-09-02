# ADR-043 — El certificado de fin de instrucción como bisagra entre instrucción y resolución

**Estado:** Adoptada — pendiente de implementación (ver §Issues de implementación)
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

### E — El emisor es donde vive la puerta cerrada

El invariante del punto 3 de #823 no desaparece: se muda del acto de crear la fase al acto de
emitir el certificado. **No se emite `CERT_FIN_INSTRUCCION` si alguna fase de la solicitud no
está finalizada**, contando las planificadas —una fase creada es una fase que alguien decidió
necesaria, por vía canónica o por escape; si sobra se borra, si hace falta se termina—. Ahí
entra intacto el análisis del punto 3, incluido el motivo por el que no es redundante con las
reglas #37/#38: esas vigilan que una fase necesaria se cree y se complete; ésta, que la
instrucción se declare terminada expresamente y sin flecos.

Lo que se exige es que las fases estén **finalizadas**, sea cual sea su resultado — por §B, un
desfavorable o un desistimiento cierran la instrucción igual que un favorable. El juicio sobre
el sentido del resultado no vive aquí: vive en el contenido del certificado y en la resolución
que lo consume.

La emisión reutiliza `generador_cert.generar_certificado_fase(expediente, fase, auditoria,
'CERT_FIN_INSTRUCCION')`, que ya existe, está probado (`tests/test_373_cert_fase.py`) y **no lo
llama nadie en producción**. Recibe un `AuditoriaResult` y lo congela —reglas evaluadas,
variables, sujeto—: eso es, literalmente, el «fundamento jurídico que habilita la resolución»
que el catálogo le atribuye. `motor_reglas.auditar()` se escribió con este destino declarado en
su docstring.

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
`COMPATIBILIDAD_AMBIENTAL`. Sin ese trámite, la única salida practicable ante un expediente gris
es la que este ADR prohíbe.

**Estado de la puerta hoy:** `_check_reabrir` solo bloquea si `Solicitud.estado` empieza por
`RESUELTA` **y** hay notificación en fase finalizadora, de modo que entre "resolución notificada"
y "solicitud marcada RESUELTA" cualquier fase se reabre.

---

## Consecuencias

**Se gana:** una comprobación en lugar de una lista de fases; cita normativa visible al bloquear
—hoy 3 de las 4 reglas de precedencia hacia `RESOLUCION` tienen `norma_id` NULL—; el certificado
catalogado desde el principio deja de estar sin dueño; y el guardián de reapertura gana su ancla.

**Hay que tocar:** migración (columna en `solicitudes`), una variable nueva + su fila en
`catalogo_variables`, dos filas de `reglas_motor` con su norma, el emisor del certificado y su
invariante, y la nota de cabecera de `invariantes_esftt.py`, que hoy enumera las familias de
invariantes sin contemplar precondiciones de creación.

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

## Issues de implementación

- **#827** — absorbe el punto 3 de #823: §A-§E completos (columna, variable, las dos reglas,
  emisor, invariante del emisor). Su alcance original —conectar el generador de certificados de
  fase al cierre— es la misma pieza vista desde el otro extremo.
- **#823** — se queda con los puntos 1 (`ESPERAR_PLAZO` exige su `NOTIFICAR` completo) y 2
  (cadena de subsanación, una vuelta cada vez), que sí son invariantes estructurales sin norma
  que citar y no dependen de nada de este ADR.
- **#838** — §F, primera pieza: el sello de la instrucción anclado al certificado, que cubre a la
  vez la reapertura de una fase cerrada y la creación de una fase de instrucción nueva. Borrador.
- **#839** — §F, segunda pieza: el trámite de actuaciones complementarias del art. 87 en el
  catálogo de la fase finalizadora, sin el cual el sello de #838 no deja salida practicable.
  Borrador.

---

## Lo que este ADR no decide

- **El momento de emisión** del certificado: al cerrar la última fase de instrucción, o como
  acto expreso del técnico. Va en #827.
- **Qué ocurre con el certificado al reabrir** una fase: si se revoca, se desvincula o se borra,
  y con qué acto. Va con el issue de §F.
- **El diseño del trámite del art. 87** (código, tareas, cardinalidad, entradas del catálogo de
  plazos, y si la audiencia del art. 82 merece trámite propio en la misma frontera): §F fija
  dónde vive —dentro de la fase finalizadora— y por qué, no cómo se escribe en el catálogo.
- Si `CERT_CIERRE_SOLICITUD` (ancla sin emisor desde #778) se resuelve en el mismo movimiento —
  mismo patrón, distinto momento del procedimiento.
- El contenido y formato del PDF del certificado.
- Qué se hace con las reglas 36/37/38 y su `norma_id` NULL: documentarlas con su norma o aceptar
  explícitamente que `reglas_motor` contiene reglas de workflow.

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

**Amparar en el art. 87 la apertura de una fase de instrucción con la finalizadora ya abierta**
(borrador anterior de este ADR, que lo llamaba "reverso" y lo mandaba a `reglas_motor` como
bloqueo escapable). Lectura equivocada del artículo: está en la sección de Resolución, lo acuerda
el órgano que resuelve y presupone la instrucción cerrada. Es una vía de escape para cuando los
actos de instrucción previstos no bastan y no caben en ningún otro sitio — y ese sitio es la
propia fase de resolución, no una fase de instrucción reabierta que desmentiría el certificado
(§F).
