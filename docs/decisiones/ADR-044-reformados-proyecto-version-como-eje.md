# ADR-044 — Reformados de proyecto: la versión como eje de la instrucción

**Estado:** Adoptada — R1 y R2 implementados (#885, #887); R3-R6 pendientes (ver §Issues)
**Fecha:** 2026-09-08
**Depende de:** ADR-011 (vinculación trámites↔organismos) · ADR-016 (vista de árbol) · ADR-032 (ingesta y almacenamiento) · ADR-036 (sellado de fase cerrada) · ADR-041 §D bis (anclas documentales) · ADR-042 (sub-procesos de cardinalidad variable) · ADR-043 (certificado de fin de instrucción)
**Enmienda:** ADR-016 §1 (modelo de niveles del árbol) · ADR-043 §E (el registry por tipo de fase deja de ser necesario para el ámbito)
**Origen:** sesiones de análisis del 2026-09-07 y 2026-09-08. Análisis completo, con el barrido fase a fase y las alternativas descartadas, en `docs/referencia/ANALISIS_REFORMADOS_PROYECTO.md`.
**Issues:** #819 (la decisión que este ADR cierra) · #864 (desbloqueado por §F) · #885 (R1) · #887 (R2)

---

## Contexto

Un **reformado de proyecto** que entra durante la instrucción de una solicitud **que todavía no se
ha resuelto**. No es el supuesto del art. 115 RD 1955/2000 —modificación de una instalación ya
autorizada, que abre solicitud nueva o se resuelve en la autorización de explotación—, que ya está
mapeado en `NORMATIVA_MAPA_PROCEDIMENTAL.md` §2.6.

Encaje normativo: el órgano puede **recabar** la modificación (art. 68.3 LPACAP, con acta sucinta
que se incorpora al procedimiento) o el interesado puede aportarla **espontáneamente** en cualquier
momento anterior al trámite de audiencia (art. 76.1). La resolución ha de ser congruente con lo
pedido (art. 88.2), de modo que el sistema tiene que poder decir **sobre qué versión resuelve**.

**Lo que había.** `documentos_proyecto` —tabla puente con un `tipo` PRINCIPAL/MODIFICADO/REFUNDIDO/
ANEXO— existía desde el origen del modelo, con **cero filas** en desarrollo y **ninguna escritura en
el código**: su único consumidor era la guarda de borrado del pool. `tipo` era `varchar(20)` sin
CHECK ni FK. Es decir, el «ya contemplado en BDDAT» que daba por hecho #819 era una declaración de
intenciones, no una funcionalidad.

**Lo que sí estaba preparado**, y sostiene esta decisión: varias fases del mismo tipo por solicitud
ya son posibles (`crear_fase` no comprueba duplicidad); el árbol admite nodos sintéticos de
agrupación **de forma aditiva** (ADR-042); ADR-043 §E dejó un campo `ambito` vacío a propósito
declarando a #819 como su primer consumidor; y existe el gesto de deshacer el `CERT_FIN_INSTRUCCION`
(#838), que es la marcha atrás del reformado tardío.

---

## Decisión

### A — Vocabulario

Tres palabras, ninguna intercambiable:

| Término | Qué es |
|---|---|
| **Proyecto principal** | El documento que materializa el proyecto presentado. Uno por expediente |
| **Reformado de proyecto** | El documento que cambia el proyecto **con entidad suficiente para obligar a rehacer fases preceptivas**. Es una fila de `reformados_proyecto` |
| **Versión del proyecto** | El estado del proyecto en un momento dado. No es una entidad: es el tramo documental entre dos reformados |

**Modificado / modificación** queda reservado a las instalaciones existentes del art. 115 y su
relación con la AAU — lo que ya expresa `proyectos.es_modificacion`. «Reformado» es además lo que
los técnicos escriben en los títulos y lo que los organismos leen en el oficio de consulta.

### B — Se retira `documentos_proyecto`

Todo lo que contenía es deducible o frágil:

- `proyecto_id` es redundante: `expedientes.proyecto_id` es `NOT NULL` **y** `UNIQUE`, así que la
  1:1 está garantizada por constraint y un documento que sabe su expediente sabe su proyecto.
- «Todos los documentos del proyecto» es una consulta por `tipo_doc = DOC_PROYECTO` sobre el pool.
- El `tipo` era el único valor añadido y estaba construido sobre un `varchar` libre.

El **apellido `REFUNDIDO` no se rescata**: lo que importa no es si un documento es refundido, sino
si **produce corte**. Reformado y refundido a la vez, corte; refundido a secas, documento de ayuda a
la lectura que ni siquiera forma parte del proyecto hasta que alguna tarea lo consuma.

Consecuencia aceptada: un `DOC_PROYECTO` que no abre reformado ni es el principal pasa a ser
borrable del pool como cualquier otro documento, porque no es consumido ni producido.

### C — `reformados_proyecto`: cortes, no contenedores

Cada fila es un **corte** en la línea temporal de los `DOC_PROYECTO` del expediente. El conjunto
documental de una versión es el **tramo entre cortes**: la versión inicial es todo lo anterior al
primer reformado. Con eso, un proyecto que llega en varios ficheros —tomo I, tomo II, planos— cae en
su tramo sin necesitar clasificación propia.

El reformado **es** el documento que lo introduce, con el patrón de anclas documentales de ADR-041
§D bis. Con eso, «este documento obliga a rehacer fases» no necesita ni booleano que el técnico
pueda contradecir ni literal hardcodeado: **la fila existe o no existe**.

**Columnas:** `documento_id` —el ancla— y **`origen`**, que distingue el reformado **voluntario**
del promotor (art. 76.1) del **requerido** por la Administración (art. 68.3). Son dos supuestos
legales con documentación distinta y es lo único que no se deriva de nada; si algún día se modela el
acta del 68.3, su ancla natural es esta fila.

No lleva orden ni etiqueta —se derivan de `ORDER BY documentos.fecha_administrativa, id` y de la
composición del texto—, ni observaciones —están en `documentos`—, ni autor o momento de la
declaración: eso es un acto con consecuencias y su sitio es la **bitácora**.

**Puerta única de alta: la ingesta en el pool.** Al ingestar un documento y detectarse que es
`DOC_PROYECTO`, el sistema mira el estado del proyecto y pregunta una cosa u otra:

| Estado | Pregunta |
|---|---|
| Sin principal anclado | «¿Es este el proyecto?» → se ancla (§D) |
| Ya hay principal | «¿Produce un reformado de proyecto?», **por defecto no**, con advertencia de lo que significa una respuesta equivocada |

La distinción la hace el estado del ancla, no la cronología. Además: **fecha administrativa
obligatoria** para `DOC_PROYECTO` —sin cronología no hay tramos— y **reversión automática, solo del
último reformado**, porque el alta también es automática.

### D — El proyecto principal se ancla en `proyectos`

El proyecto original **no tiene fila** en `reformados_proyecto` —sería una contradicción— porque ya
está representado en `proyectos`: título, fecha técnica, descripción, finalidad y emplazamiento se
capturan en el alta. La tabla de reformados no parte en dos algo simétrico: rellena el hueco que
faltaba.

Lo que faltaba es su ancla documental: **`proyectos.documento_principal_id`**, *nullable* porque en
el alta el único documento que entra es el escrito de solicitud.

**Guarda: regla de motor, no invariante.** Sin ancla, el sistema no sabe si un `DOC_PROYECTO`
posterior abre reformado. Se bloquea seguir la solicitud mientras el proyecto no tenga principal, y
es regla de motor —no invariante— porque admite escape: los invariantes de `invariantes_esftt` son
los que **no** se justifican. Forma canónica, con dos precedentes (#582, #780): variable calculada +
una regla `BLOQUEAR CREAR ANY/ANY/ANY` con `tipo_sujeto_solicitado NEQ 'ANALISIS_SOLICITUD'`.

El **expediente heredado** se expresa como condición de la propia regla —`expedientes.heredado` ya
existe—, no como bypass manual repetido fase tras fase en un expediente que nunca tendrá el dato.

El ancla es además **la fuente** frente al requisito documental del checklist: si existe un
`RequisitoDocumental` de tipo `DOC_PROYECTO`, su cobertura apunta al mismo documento por otra vía,
en otro momento y con otro ámbito —el requisito es por solicitud, el ancla por expediente—. El
checklist se valida contra el ancla y avisa si divergen.

### E — El enganche: `fases.reformado_id`, y lo que necesita cada fase

La relación con la versión vive en **quien realmente la tiene**, no en la fase por comodidad. Esto
descarta el planteamiento original de #819 (vínculo directo fase↔documentos): en consultas quien se
relaciona con la versión es el organismo, y en el análisis, el requisito técnico —que no es fase, ni
trámite, ni tarea—.

Del barrido de las nueve fases resulta que **una columna `fases.reformado_id` basta para ocho**, y
que solo el análisis necesita algo por debajo:

| Fase | Qué necesita |
|---|---|
| `ANALISIS_SOLICITUD` | `fases.reformado_id` **y** el eje de coberturas (§E bis) |
| `CONSULTAS` | Solo la fase: con una por versión, el organismo **hereda** la versión de su fase. `UNIQUE (fase_id, organismo_id)` deja de estorbar y `organismos_expediente` se queda como está |
| `INFORMACION_PUBLICA` | Solo la fase: la IP se repite entera, no cabe parcial. El alcance lo redacta el anuncio y queda fuera del modelo |
| `COMPATIBILIDAD_AMBIENTAL`, `AAU_AAUS_INTEGRADA`, `FIGURA_AMBIENTAL_EXTERNA`, `CONSULTA_MINISTERIO` | Solo la fase: una interlocución con un solo órgano, sin cardinalidad variable |
| `RESOLUCION` | Nada: no se repite (§H) |
| `RECONOCIMIENTO_INTERESADO` | Nada: su objeto es la condición de un sujeto, no el proyecto |

`reformado_id` **NULL significa versión inicial**: no hay que crear filas retroactivas para los
expedientes existentes.

#### E bis — Las coberturas del análisis

Los tres ejes de `ANALISIS_SOLICITUD` no se comportan igual:

| Eje | Ámbito |
|---|---|
| Trámite `ANALISIS_DOCUMENTAL` | **Por versión**: el reformado es documentación que entra, se analiza y produce su propio `DIAGNOSTICO` con su fecha |
| Requisitos **documentales** | **Global por solicitud**, salvo los marcados como afectados por reformado |
| Requisitos **técnicos** | **Solicitud + versión**: la verificación se predica del contenido del proyecto |
| Requerimientos **particulares** | Ni una cosa ni otra: la versión es **atributo de nacimiento**, nunca clave |

El flag de afección por reformado en `requisitos_documentales` nace del caso de la **tasa**: si el
reformado cambia el presupuesto lo bastante, procede complementaria. En el análisis de la versión
nueva se revisa; si no cambia, se alimenta con la tasa antigua; si cambia, se pide el complemento.
Así la complementaria **no es un requisito nuevo** sino el mismo cubierto en otra versión con otro
documento —evita tocar la cardinalidad «un documento por requisito», y es la única vía viable
porque `RequisitoDocumental` es catálogo global sin requisitos *ad hoc*.

Los **particulares** son distintos porque un defecto libre nace en una versión y puede morir en
otra: el cálculo que falta nace con el proyecto original y se resuelve cuando llegue, con reformado
o sin él. Si la versión fuera clave, el defecto se duplicaría en cada versión y se perdería desde
cuándo está abierto.

### F — Una sola regla de motor sobre las fases

**Se prohíbe crear una fase que cubra una versión ya cubierta por otra fase del mismo tipo.**

Leída del derecho y del revés es la misma frase: sin reformado, la versión vigente es la que ya
cubrió la primera fase → bloqueo; con reformado, es otra → permitido, justificado y auditado. Lo que
antes era *«el usuario tiene un reformado que no sabe dónde meter y crea otra fase porque está
permitido»* pasa a ser *«hay un reformado, luego procede otra ronda»*.

El criterio no es de consultas: vale para el análisis y para las ambientales, así que admite **una
sola regla con sujeto genérico y condición de encuadre** —patrón de #582— en vez de una por fase.

Con la versión como sujeto, **#864 queda desbloqueado**: «el análisis de esta versión está cerrado»
es una pregunta formulable, sin caer en el existencial que hoy mentiría en la ronda del reformado.

### G — Árbol: nodo sintético de reformado

La lista de reformados dibuja una **metafase virtual**: un nodo intermedio que aparece solo cuando
hay algún reformado. Es el patrón de ADR-042 un nivel más arriba y hereda su mecánica **aditiva** —
el backend añade el payload y el front decide la agrupación, sin reparentar nada y sin coste para
los expedientes sin reformado.

En la interfaz el texto es el que ya entienden los organismos: «REFORMADO DE PROYECTO de fecha
\_\_\_\_», junto al «PROYECTO de fecha \_\_\_\_» de la versión inicial.

### H — La resolución no identifica la versión: la identifica el sello

No hace falta campo nuevo. La versión sobre la que se resuelve es **la vigente cuando se selló la
instrucción**, y eso ya está materializado en `solicitudes.documento_fin_instruccion_id`, con la
auditoría congelada y el informe redactado dentro. Encaja con el art. 82.1 y con lo que ya existe:
un reformado posterior al sello obliga a deshacerlo (#838) y re-emitirlo. Como la solicitud tiene
**una sola** FK al certificado, no caben dos vigentes.

El certificado gana cuatro cosas:

1. **Cabecera que dice sobre qué versión se resuelve**, con **dos redacciones**: sin reformados,
   texto llano, sin estructura de versiones ni menciones a algo que no ha pasado; con reformados, la
   versión vigente y la relación de las anteriores.
2. **`Bloque.ambito` relleno** desde `fases.reformado_id`. Para las fases de la versión inicial se
   redacta explícitamente —«sobre el proyecto en su redacción original»—, no se deja vacío.
3. **Relato agrupado por versión** cuando las hay.
4. **Observaciones del cierre de cada fase**, siempre, con «Observaciones al cierre: -» si no las
   hay.

### I — Principio rector: ninguna fase se salda por la existencia de una posterior

Una fase enganchada a una versión **conserva sus pendientes** aunque exista una versión posterior:
el apartado de cálculo que falta, la alegación sin contestar, el organismo enquistado. No hay
completitud por invariante — hay huecos que el reformado no cubre. El certificado los cubre todos,
cada uno con sus tiempos.

Ya está implementado sin tocar nada: `revisar()` recorre **todas** las fases de instrucción y
cualquiera con hueco sale como `PENDIENTE`.

**Excepción aparente, que no lo es:** en las ambientales el órgano suele incorporar el reformado a
lo que ya tenía y emitir **un solo pronunciamiento válido para las dos peticiones**. Eso no es que
la última prevalezca: las dos fases siguen contando y **las dos se cierran**, con el mismo documento
o con el segundo documentando la primera. `fases.documento_resultado_id` no tiene UNIQUE, así que ya
es posible; lo que explica por qué un documento cerró dos fases es **el comentario del técnico al
cerrar**, y si no escribió nada, el sistema no lo adivina.

---

## Consecuencias

### Lo que hay que corregir porque asume ronda única

| Pieza | Qué le pasa |
|---|---|
| `fase_ip_finalizada` | Existencial: con la IP inicial cerrada y la del reformado abierta afirma que la IP terminó, y **las reglas 38 y 1718 dejan pasar la resolución** — se vuelven permisivas justo cuando importan |
| `existe_fase_finalizadora_cerrada` | Mismo patrón |
| `tasa_impagada` | Cuenta requisitos cubiertos por solicitud; debe mirar la versión vigente |
| `cert_fin_ip_consultas._buscar_existente` | Busca por expediente + tipo: nunca re-emite, y tras la segunda ronda acreditaría la primera |
| `Solicitud.estado` | Coge la primera finalizadora sobre un backref sin `order_by` (#848) |
| Alegaciones | `ALEGACION_IP` y `RESPUESTA_TITULAR_ALEGACION` se consumen «todas las del expediente»: con dos IP mezclan rondas |

Lo que **no** hay que tocar: `tramite_analisis_con_deficiencias` ya está escrita en universal y
acierta; `organismos_expediente` se queda como está; el árbol no cambia de topología.

### Deuda que este ADR destapa pero no asume

- **Suspensión acumulada** (art. 22.1.d): `plazos.py` funde intervalos solapados, pero dos rondas
  son sucesivas y suman. Su docstring asume que el tope de tres meses «no muerde» porque cada plazo
  es de tres meses o menos: cierto por entrada, falso por acumulación. De fondo es **laguna de la
  ley** —la norma no dice nada de reformado tras reformado— y se deja anotada sin criterio inventado.
  El consumo de plazo solo preocupa cuando hay derechos de terceros y el vencimiento produce
  resolución desfavorable (silencio desestimatorio en AAP, art. 128, y AAC, art. 131.7; en DUP
  arrastra la expropiación).
- **Interprovincialidad y órgano tramitador**: si un reformado vuelve interprovincial el expediente,
  se archiva y se da traslado a servicios centrales. Modelar la pertenencia a órgano tramitador es
  refactor de exportación al resto de Andalucía, no de producción.
- **Trámites de la AAU modificada**: por el art. 74.6 de la Ley 2/2026 la modificación no sustancial
  se resuelve por comunicación y silencio de un mes, no por otro informe vinculante. La fase de la
  versión nueva llevará trámites distintos de los cinco de la primera; **no se inventan en el FTT**
  hasta que salga la nueva instrucción conjunta. Al implementar, no clonar la fase anterior.
- **Edición concurrente.** Con dos fases de análisis vivas, dos `ANALIZAR` conviven, y el conflicto
  —entre pestañas del mismo usuario y entre personas distintas— deja de ser de laboratorio. #884
  cubre lo primero por la vía optimista (merge en la lista de requerimientos, sin bloquear a nadie);
  lo segundo —un **candado por expediente en modo edición**, con la lectura siempre libre— queda
  para su propia sesión.

  Precedente de qué **no** hacer, en el mismo dominio y con los mismos usuarios:
  `ESTUDIO_DOM_PTWANDA.md` **§11 «Bloqueo y liberación — REGLA DE ORO»**. En PTWANDA
  `tramitarExpediente()` bloquea el expediente para el usuario actual, **no hay botón de liberar**,
  y **cerrar el navegador en seco lo deja bloqueado indefinidamente** — con un caso real anotado de
  un expediente tomado por un usuario de otra provincia. El repo `genete/ptwanda-tecnico` (§2.bis de
  `EXPLORACION_ASIGNACION_Y_FINALIZACION.md`) añade el detalle que lo explica todo: solo libera el
  **click** en «Ir a inicio», no un `GET` a esa misma URL. Es decir, **la liberación es puramente de
  cliente**: no hay expiración ni barrido en servidor. De ahí la exigencia mínima para el nuestro —
  que el candado lleve **quién y desde cuándo**, y expire solo.

---

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Vínculo directo fase↔documentos (#819 original) | Quien tiene la relación con la versión no siempre es la fase |
| Entidad de versión separada de los documentos | El reformado **es** el documento que lo introduce |
| Columna `produce_edicion` por fila, rellenada por el técnico | Pregunta dos veces lo mismo con oportunidad de contradecirse, y el error se propaga en silencio |
| Hardcodear el literal `'MODIFICADO'` | Se apoyaría en un `varchar` libre sin CHECK |
| Subir `tipo` a catálogo con flag | La existencia de la fila ya es la declaración |
| Meter el proyecto original como primera fila de `reformados_proyecto` | Contradice el nombre y es innecesario: ya está en `proyectos` |
| Flag «acumulativa / sustitutiva» en el tipo de fase | Se planteó para las ambientales y sobra: las dos fases se cierran, no prevalece una |
| Nombres `ediciones_`, `versiones_`, `modificados_proyecto` | «Edición» choca con *editar* (verbo de modificación en 34 sitios del código); «versiones» permitía meter el original en la tabla y no dice nada en el oficio; «modificados» colisiona con `proyectos.es_modificacion`, que es el art. 115 |

---

## Issues de implementación

Cuatro issues nuevos, encadenados, más tres que ya viven fuera. **R1 y R2 hechos; R3-R6
pendientes de crear.** Bajo cada uno, lo que la implementación corrigió de lo escrito aquí.

### R1 — `reformados_proyecto` y la retirada de `documentos_proyecto`

**Alcance:** modelo `ReformadoProyecto` (`documento_id`, `origen`) y migración manual; retirada de
`documentos_proyecto` y del modelo `DocumentoProyecto` (`git rm`); sustitución de la rama
`proyecto_vinculado` en la guarda del pool; fecha administrativa obligatoria para `DOC_PROYECTO`; la
bifurcación de la pregunta en la ingesta (§C); reversión automática solo del último; bitácora del
acto.

**Depende de:** nada. Es el primero.
**Arrastra:** sustituir el ejemplo de `DocumentoProyecto` en `DISEÑO_SUBSISTEMA_DOCUMENTAL.md` §2 —
el principio de particularización N:M sigue vivo, pero pierde su ejemplo canónico— y actualizar
`INVENTARIO_BACKEND.md`.

**Hecho — #885.** Tres cosas que la implementación corrigió de lo escrito arriba:

- La «puerta única» son en el código **cuatro rutas de alta más la reclasificación al editar
  metadatos**. La pregunta vive en el paso de metadatos, en una casilla que solo existe mientras
  el tipo elegido es `DOC_PROYECTO` y que se resetea al cambiarlo; el alta, en un servicio único
  al que llaman las cuatro.
- La fecha obligatoria **no cabe en `@validates`** —el validador de un campo no puede leer con
  fiabilidad otro—, así que es un listener de mapper. Y hace falta además una comprobación
  temprana en la ingesta multipart: el flush llega después de escribir el fichero y el rollback
  no lo borra.
- El corte **muere con su documento** (FK `CASCADE` + `delete-orphan` en el backref). Esa es la
  reversión por la vía del borrado; la otra es desmarcar la casilla, y solo sobre el último.

### R2 — El ancla del proyecto principal y su regla de motor

**Alcance:** `proyectos.documento_principal_id`; su rama en la guarda del pool y su mensaje en
`_MOTIVO_ANCLA`; variable calculada + regla `BLOQUEAR` con la condición de encuadre y la excepción
de expediente heredado (variable nueva en catálogo); validación del checklist contra el ancla.

**Depende de:** R1 (la pregunta de la ingesta es la misma puerta).

**Hecho — #887.** Dos correcciones de fondo y un efecto que alcanza a toda la suite:

- **Son dos reglas, y en AAP+AAC manda la del trámite más avanzado.** El fundamento no es uno:
  RD 1955/2000 **art. 123.1** (a la solicitud de AAP se acompaña el anteproyecto) y **art. 130.1**
  (la AAC se presenta junto con el proyecto de ejecución). Como `evaluar_multi` recorre
  `tipos_simples` en orden y devuelve el primer BLOQUEAR, una regla por sujeto sin más haría que
  una AAP+AAC citara el 123.1 cuando lo exigible es el 130.1: la regla de la AAP lleva la
  condición `solicitud_contiene_aac EQ false` y la de la AAC cubre también las combinadas.
- **Las variables son de dato, no calculadas**: `proyecto_sin_principal` y `expediente_heredado`
  leen un campo, sin consulta ni agregación, así que no necesitan la degradación por catálogo
  ausente de sus primas del checklist. `heredado` es nullable y NULL significa «no heredado».
- Con esta regla, **tener proyecto identificado pasa a formar parte del estado mínimo para
  avanzar**, igual que ya lo era cubrir la tasa (#582). Todo test que pase del análisis lo declara
  con `arbol.anclar_proyecto()`; el alta real sigue sin traerlo, a propósito. Cuenta para R3-R6:
  cada regla nueva del motor mueve ese mínimo y alcanza a los tests que lo dan por supuesto.

### R3 — `fases.reformado_id`, el nodo del árbol y la regla genérica

**Alcance:** columna en `fases`; nodo sintético aditivo en `arbol_expediente` + front; la regla de
motor de §F con su variable; verificación sobre el expediente-tipo.

**Depende de:** R1.
**Desbloquea:** #864, que puede implementarse en este issue o inmediatamente después.

### R4 — Las coberturas del análisis por versión

**Alcance:** flag de afección por reformado en `requisitos_documentales`; `reformado_id` en
`documentos_requisito` con índices únicos parciales (`(requisito, solicitud) WHERE reformado_id IS
NULL` para los no afectados, `(requisito, solicitud, reformado)` para los afectados) y en
`coberturas_item_tecnico`; reescritura de `tasa_impagada` para mirar la versión vigente;
`reformado_id` en `requerimientos_tarea` como atributo de nacimiento.

**Depende de:** R3, y **#884** para la parte de `requerimientos_tarea` — ese campo no sobrevive a un
guardado destructivo.

### R5 — Arrastres del motor y de los certificados

**Alcance:** `fase_ip_finalizada` y `existe_fase_finalizadora_cerrada` a universal (con las reglas 38
y 1718); `cert_fin_ip_consultas` re-emitible por ronda; `Solicitud.estado` a la última finalizadora
con `order_by` (#848); aislamiento de las alegaciones por ronda; el certificado de fin de instrucción
de §H —ámbito, dos redacciones, agrupación por versión y observaciones de cierre—.

**Depende de:** R3.
**Nota:** #848 ya existe y puede absorberse aquí o quedarse suelto.

### R6 — Expediente-tipo del reformado

**Alcance:** el expediente-tipo que faltaba en `scripts/expedientes_dummy/`, con dos versiones de
proyecto, la fase de la versión inicial con un hueco vivo y la del reformado limpia — el escenario
que verifica §I y la regla de §F.

**Depende de:** R3 como mínimo; idealmente R4 y R5.

### Ya abiertos, fuera de este ADR

| Issue | Relación |
|---|---|
| **#881** | Reforma del listado del pool: columna de usos, y cómo se presenta un documento con destino declarado sin tarea que lo consuma |
| **#882** | `publicadores_expediente` — destinatarios múltiples de publicación. Independiente: hace falta igual sin reformados |
| **#883** | La guarda del pool no cubre el documento de resultado de fase. Defecto de hoy que el cierre conjunto agrava |
| **#884** | El shuttle de requerimientos guarda por reemplazo total. **Precedente de R4** |

### Orden

```
R1 ──> R2
  └──> R3 ──> R4 (+ #884)
         └──> R5
         └──> R6
```
