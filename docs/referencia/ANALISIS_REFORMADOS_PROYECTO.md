# Análisis: reformados de proyecto — el proyecto que cambia dentro de la solicitud sin resolver

**Estado:** Análisis cerrado — la decisión vive en **ADR-044**. Este documento se congela en
`historial/` al arrancar la implementación (`REGLAS_ARQUITECTURA.md` §2, §3)
**Fecha de apertura:** 2026-09-07 · **Última sesión:** 2026-09-08
**Issues:** #819 (decisión de fondo) · #864 (bloqueado por esta) · #848 (arrastre)
**Relacionado:** `DISEÑO_CONSULTAS_ORGANISMOS.md` §6 bis y §8 · `DISEÑO_ANALISIS_SOLICITUD.md` §4 y §6 ·
`DISEÑO_SUBSISTEMA_DOCUMENTAL.md` §2 · ADR-011, ADR-016, ADR-032, ADR-038, ADR-041, ADR-042, ADR-043

> **La decisión está en [ADR-044](../decisiones/ADR-044-reformados-proyecto-version-como-eje.md)** —
> ahí van el qué y el porqué, y los issues de implementación. Este documento conserva **el camino**:
> el barrido fase a fase, lo verificado en código y BD, las alternativas que se cayeron y los cabos,
> cada decisión fechada con la sesión en que se acordó. Lo que sigue abierto, en §17.

---

## 0. Vocabulario

Tres palabras, y ninguna intercambiable:

| Término | Qué es |
|---|---|
| **Proyecto principal** | El documento que materializa el proyecto técnico presentado. Uno por expediente, anclado en `proyectos.documento_principal_id` (§7) |
| **Reformado de proyecto** | El documento que cambia el proyecto **con entidad suficiente para obligar a rehacer fases preceptivas**. Es una fila de `reformados_proyecto` (§6) |
| **Versión del proyecto** | El estado del proyecto en un momento dado: la **versión inicial** (el principal y lo que lo acompaña) o la resultante de cada reformado. No es una entidad: es el tramo documental entre dos reformados (§6) |

**Modificado / modificación** queda reservado para las **instalaciones existentes** y su relación
con la AAU —art. 115 RD 1955/2000, y el campo `proyectos.es_modificacion` que ya lo expresa—. No se
usa para este caso.

Nombres descartados para la tabla, con su motivo, en §18.

---

## 1. El caso

Un **reformado de proyecto que entra durante la instrucción de una solicitud que todavía no se ha
resuelto**. No es el supuesto del art. 115 RD 1955/2000 —modificación de una instalación ya
autorizada, que abre solicitud nueva de AAC o AAP+AAC, o se resuelve en la autorización de
explotación si encaja en el 115.3—: eso está mapeado en `NORMATIVA_MAPA_PROCEDIMENTAL.md` §2.6 y no
es objeto de este análisis.

Encaje en la LPACAP (texto consolidado verificado):

| Artículo | Qué aporta |
|---|---|
| **68.3** | El órgano *«podrá recabar del solicitante la modificación o mejora voluntarias de los términos de aquélla. De ello se levantará acta sucinta, que se incorporará al procedimiento»* — el reformado pedido por la Administración o por los organismos |
| **76.1** | El interesado puede aportar documentos *«en cualquier momento del procedimiento anterior al trámite de audiencia»* — el reformado espontáneo, con su límite temporal |
| **88.2** | La resolución será congruente con las peticiones formuladas → hay que poder decir **sobre qué versión** se resuelve |
| **22.1.a** | La suspensión del plazo es **potestativa** y solo si media requerimiento: el reformado espontáneo no suspende, y repetir consultas (30 días, arts. 127/131) e IP (30 días, art. 125.1 RD 1955/2000 en la redacción del RD-ley 23/2020) consume plazo vivo |

---

## 2. Punto de partida (estado verificado el 2026-09-07)

### Lo que había: nada operable

- `documentos_proyecto` (tipo PRINCIPAL/MODIFICADO/REFUNDIDO/ANEXO): tabla y modelo existen,
  **0 filas** en la BD de desarrollo y **ninguna escritura en el código**. Su único consumidor es
  `_documento_es_referenciado` (`app/modules/expedientes/routes.py:488`), que la lee para no borrar
  del pool. No hay ruta, servicio, template ni componente que dé de alta una fila.
- `tipo` es `varchar(20)` **sin CHECK ni FK**: los cuatro valores solo viven en un comentario.
- `Proyecto` es 1:1 con expediente y **no tiene versiones**; su docstring manda actualizar los
  metadatos cuando cambie algo esencial → sobrescritura destructiva.

### Lo que sí estaba preparado

- Varias fases del mismo tipo por solicitud: `crear_fase` (`app/services/mutaciones_arbol.py:434`)
  no comprueba duplicidad; solo miran el sello de instrucción y el motor.
- `organismos_expediente.fase_id` (#391/#396) y la regla de motor 1683 (`ADVERTIR`,
  `ANY/ANY/CONSULTAS`, «Nueva ronda de consultas…»).
- El árbol admite nodos sintéticos de agrupación **de forma aditiva**: `_serializar_organismos_fase`
  (`app/services/arbol_expediente.py:316`) no reparenta nada —`fase.tramites` queda intacta— y solo
  paga la query si la fase tiene organismos (ADR-042).
- ADR-043 §E dejó en `informe_instruccion.py` un campo **`ámbito` vacío a propósito** y un punto de
  extensión por fase, declarando a #819 como su primer consumidor real.
- El gesto de **deshacer** el `CERT_FIN_INSTRUCCION` existe (#838): es la marcha atrás para el
  reformado que llega con la instrucción ya sellada.

### La deuda que el caso despierta

| Pieza | Qué asume |
|---|---|
| `Solicitud.estado` | Coge la **primera** finalizadora, sobre un backref sin `order_by` (#848) |
| `fase_ip_finalizada`, `existe_fase_finalizadora_cerrada` | Existenciales («alguna cerrada») |
| `cert_fin_ip_consultas._buscar_existente` | Busca por expediente + tipo → **nunca re-emite** |
| Árbol | Dos fases del mismo tipo se pintan idénticas |
| `documentos_requisito`, `coberturas_item_tecnico` | Clave por **solicitud**: un reformado pisa la verificación anterior sin dejar rastro |

Y lo que ya está bien: `tramite_analisis_con_deficiencias`
(`app/services/variables/calculado.py:241`) recorre **todas** las fases y devuelve `True` si en
alguna el último `ANALIZAR` quedó desfavorable. Está escrita en universal y acierta con varias
versiones. El patrón que falla es «existe alguna».

---

## 3. Barrido: qué fases dependen del reformado

Criterio: qué sale de la fase portando el proyecto, y qué entra quedando referido a él.

| Fase | ¿Depende? | Qué sale / qué se somete |
|---|---|---|
| `ANALISIS_SOLICITUD` | **Sí** | Nada sale; el proyecto **entra** y se juzga |
| `CONSULTAS` | **Sí** | Separatas — **extracto** del proyecto y su reformado, y solo a los organismos a los que el reformado afecta |
| `INFORMACION_PUBLICA` | **Sí** | Se someten **el proyecto y sus reformados**; el anuncio es el vehículo, no el objeto |
| `CONSULTA_MINISTERIO` | **Sí** | Sale el **proyecto entero**, sin extracto (art. 114) |
| `COMPATIBILIDAD_AMBIENTAL` | **Sí** | Sale el **proyecto entero** |
| `AAU_AAUS_INTEGRADA` | **Sí** | Sale el proyecto y, además, el resultado de IP y consultas (fases que a su vez dependen de él) |
| `FIGURA_AMBIENTAL_EXTERNA` | **Sí**, indirecta | Sale el proyecto, pero la figura la tramitan promotor y órgano ambiental; si el reformado la invalida, lo decide aquél. Para BDDAT es un dato que entra, no un acto que repetir |
| `RESOLUCION` | **De otra forma** | No se repite: **decide**. Necesita identificar sobre qué versión resuelve (art. 88.2) |
| `RECONOCIMIENTO_INTERESADO` | **No** | Su objeto es la condición de un **sujeto** (art. 4 LPACAP). Un reformado no invalida un reconocimiento dictado. Asimetría: puede *generar* interesados nuevos, pero eso son solicitudes nuevas |
| `CONSULTA_OPERADOR_SISTEMA` | **Fuera** | Exclusiva del procedimiento CIERRE (art. 137); no poblada en BD (#450) |

### Hallazgo: la unidad de sometimiento no es la misma en todas

En `CONSULTAS` cada trámite es un destinatario distinto, así que un reformado que solo toca la
carretera afecta a Fomento y deja intactos a los demás: **la afección es parcial dentro de la
fase**. En `INFORMACION_PUBLICA` no: el `ANUNCIO_IP` es único para BOJA, BOP, prensa, tablón y
titular. No hay un solo nivel al que colgar la relación con la versión que valga para todas.

---

## 4. Principio rector: ninguna fase se salda por la existencia de una posterior

**Decidido (2026-09-08).** Una fase enganchada a una versión conserva sus pendientes aunque exista
una versión posterior. No hay completitud por invariante: hay huecos que el reformado no cubre.

- Falta un apartado de cálculo de la línea subterránea y el reformado solo afecta a la aérea: el
  análisis del reformado puede ser perfecto y el otro sigue pendiente.
- Puede haber alegaciones sin contestar de la primera IP, y una segunda IP sin alegaciones con
  todos los plazos vencidos.
- Un organismo afectado por el proyecto original puede tener sus trámites enquistados mientras la
  ronda del reformado está impecable.

**Corolario:** el certificado de fin de instrucción debe cubrirlo todo, cada uno con sus tiempos.

---

## 5. Decisión A — retirar `documentos_proyecto`

**Decidido (2026-09-08).** La tabla se aparca; lo que aportaba se obtiene por consulta.

| Columna | Por qué no hace falta |
|---|---|
| `proyecto_id` | `expedientes.proyecto_id` es `NOT NULL` **y** `UNIQUE` con FK a `proyectos`: la 1:1 está garantizada por constraint. Un documento que sabe su expediente sabe su proyecto |
| `documento_id` + `UNIQUE` | Deja de tener sentido sin la tabla |
| `tipo` | Es el único valor añadido real —el apellido del documento— y está construido frágil: `varchar` libre sin CHECK |
| `observaciones` | `documentos.observaciones` ya existe |

Con la tabla fuera, «todos los documentos del proyecto» es una consulta por `tipo_doc = DOC_PROYECTO`
sobre el pool del expediente. Lo que no da gratis la consulta es el **orden entre versiones**:
`documentos.fecha_administrativa` es *nullable* y dos documentos pueden compartir fecha, así que el
orden pasa a ser dato de la tabla nueva.

**Coste de la retirada:** ninguno en datos (0 filas, 0 escrituras). #856 ya prevé recrear las
migraciones desde cero antes de producción.

**Cabos:**

- **`REFUNDIDO` no necesita modelarse** (decidido 2026-09-08). La pregunta no es si el documento es
  refundido, es **si produce corte**: reformado y refundido a la vez, corte; refundido a secas, no.
  En ese caso es un documento de ayuda a la lectura, de valor aclaratorio, que ni siquiera forma
  parte del proyecto hasta que alguna tarea lo consuma. Era el único apellido que hacía dudar de
  retirar la tabla entera, y se cierra sin nada que construir.
- **`ANEXO`** se puede perder sin dolor: lo que importa de un anexo es qué requisito cierra, y eso
  vive en `documentos_requisito` y en el `ANALIZAR` que lo consume.
- **La guarda del pool** pierde su primera rama (`doc.proyecto_vinculado`) y se sustituye por
  `reformados_proyecto` y por el ancla de §7. Consecuencia aceptada: un `DOC_PROYECTO` que no abre
  reformado ni es el principal pasa a ser borrable como cualquier otro documento, porque no es
  consumido ni producido.
- **`DISEÑO_SUBSISTEMA_DOCUMENTAL.md` §2** usa `DocumentoProyecto` como el precedente canónico del
  patrón de particularización N:M. El principio sigue vivo (`documentos_tarea`,
  `documentos_requisito`, `organismos_expediente`); hay que sustituir el ejemplo.

---

## 6. Decisión B — `reformados_proyecto`

**Decidido (2026-09-08).** Tabla nueva con el mismo concepto que `organismos_expediente`: una lista
de entidades del expediente que estructura el árbol y a la que referencian los demás.

Contiene **los documentos que dividen el proyecto en versiones**. El reformado no es una entidad
abstracta: es la fila del documento que lo introduce —el mismo patrón de anclas documentales que ya
usan la solicitud (su escrito), la instrucción (su certificado) y el cierre (ADR-041 §D bis,
ADR-043 §D)—. Con eso, «este documento obliga a rehacer fases» no necesita ni booleano que el
técnico pueda contradecir ni literal hardcodeado: **la fila existe o no existe**.

### Cortes, no contenedores

Cada fila es un **corte** en la línea temporal de los `DOC_PROYECTO` del expediente. El conjunto
documental de una versión es el **tramo entre cortes**: la versión inicial es todo lo anterior al
primer reformado; la versión N, lo que va del reformado N al siguiente.

Esto resuelve que **un proyecto son N documentos** (tomo I, tomo II, planos) sin necesidad de
clasificar cada uno: caen en el tramo que les corresponde por su fecha. Un reformado que llega en
varios ficheros funciona igual: uno es el corte y los demás lo acompañan en su tramo.

### Puerta única de alta: la ingesta en el pool

Al ingestar un documento y detectarse que es `DOC_PROYECTO` (lo que todos tienen en común), el
sistema mira el estado del proyecto y pregunta una cosa u otra:

| Estado | Pregunta |
|---|---|
| El proyecto **no tiene principal** anclado | «¿Es este el proyecto?» → si sí, se ancla en `proyectos.documento_principal_id` (§7) |
| Ya **hay principal** | «¿Produce un reformado de proyecto?», **por defecto no**, y con advertencia de lo que significa una respuesta equivocada — obliga a rehacer las fases preceptivas que correspondan |

El sistema distingue los dos casos por si existe ya el ancla, no por cronología. Así toda
posibilidad de versión nueva pasa por un solo sitio.

- **Fecha administrativa obligatoria** para `DOC_PROYECTO` — a nivel de interfaz o de restricción
  SQL si es posible. Sin ella no hay cronología, y sin cronología no hay tramos.
- **Reversión automática**, no manual: al ser el alta automática, la reversión también lo es. **No
  se permite revertir un reformado que no sea el último.**
- **Corolario general:** toda referencia a un `documento_id` desde cualquier sitio debe impedir su
  borrado del pool, o dejar escape borrando la referencia con las consecuencias que tenga. Donde el
  CRUD es manual, revierte el usuario; donde es automático, revierte el sistema.

### Columnas (decidido 2026-09-08)

**El mínimo, porque casi todo lo demás ya está en otro sitio:** `documento_id` —el ancla— y
**`origen`**, que distingue si el reformado es **voluntario** del promotor (art. 76.1 LPACAP) o
**requerido** por la Administración (art. 68.3, el que obliga a levantar «acta sucinta que se
incorporará al procedimiento»). Son dos supuestos legales distintos, con documentación distinta, y
es lo único que no se deriva de nada. Si algún día se modela esa acta, su ancla natural es esta
misma fila.

Lo que **no** lleva, y por qué:

| Candidato | Dónde está ya |
|---|---|
| `orden` / número de reformado | Se deriva: `ORDER BY documentos.fecha_administrativa, id` — la fecha es obligatoria para `DOC_PROYECTO` y el `id` desempata. «Reformado 2» es una posición, no un dato |
| Etiqueta o nombre | Se compone: «REFORMADO DE PROYECTO de fecha 12/03/2026» |
| Observaciones | `documentos.observaciones` |
| Quién lo declaró y cuándo | **Bitácora**: es una decisión con consecuencias —obliga a rehacer fases—, igual que el resto de actos del árbol |

---

## 7. La entrada del proyecto principal

**Decidido (2026-09-08).** El proyecto original **no tiene fila** en `reformados_proyecto` —sería
una contradicción— porque ya está representado en `proyectos`: título, fecha técnica de firma o
visado, descripción, finalidad y emplazamiento se capturan en el alta
(`app/services/alta_expediente.py:169`). La tabla de reformados no parte en dos algo simétrico:
rellena el hueco que faltaba.

Lo que falta es su **ancla documental**: `proyectos.documento_principal_id`, *nullable*, mismo
patrón que las otras anclas del sistema. No se exige al crear el expediente —en ese momento el
único documento que entra es el escrito de solicitud— sino que se rellena cuando el documento llega
al pool, por la puerta de §6.

### La guarda: regla de motor, no invariante

Sin ancla, el sistema no sabe si un `DOC_PROYECTO` posterior abre reformado, y nada obliga hoy a
rellenarla. Hace falta una guarda que **impida seguir la solicitud mientras el proyecto no tenga
principal definido**.

Es **regla de motor**, no invariante, y la distinción importa: los invariantes de
`invariantes_esftt` son los que **no** admiten justificación (el sellado de fase cerrada, el
borrado). Aquí se quiere bloquear pero con escape para casos extremos, que es exactamente el
comportamiento de `BLOQUEAR` del motor — bloquea, admite bypass justificado y lo deja en bitácora.

Forma canónica, con dos precedentes exactos (`tasa_impagada` #582, `tiene_punto_acceso_conexion`
#780): variable calculada + una sola regla `BLOQUEAR CREAR ANY/ANY/ANY` con la condición
`tipo_sujeto_solicitado NEQ 'ANALISIS_SOLICITUD'`. «Seguir la solicitud» es crear cualquier fase
posterior al análisis; el análisis documental sigue siendo el sitio donde la falta se detecta y se
requiere.

**Escapes:**

- **Expediente heredado**: `expedientes.heredado` ya existe como campo
  (`app/models/expedientes.py:131`), así que la excepción se expresa como **condición de la propia
  regla**, no como bypass manual repetido fase tras fase en un expediente que nunca va a tener el
  dato. Cuesta una variable nueva en el catálogo y ahorra fricción permanente.
- **Motor apagado**: estado del sistema, sin tratamiento propio.
- Cualquier otro caso extremo: el bypass genérico con justificación de toda regla `BLOQUEAR`.

### Relación con el requisito documental del proyecto

Si el catálogo tiene un `RequisitoDocumental` de tipo `DOC_PROYECTO`, su cobertura en
`documentos_requisito` apunta también a un documento concreto: **la misma información que el ancla,
por otra vía, en otro momento y con otro ámbito** — el requisito es por solicitud, el ancla por
expediente. Con AAP y AAC en el mismo expediente puede haber dos coberturas apuntando a documentos
distintos; el ancla no puede divergir.

**Criterio:** el ancla es la fuente; el checklist se valida contra ella y avisa si el técnico cubre
el requisito con un documento distinto del anclado. Preguntar dos veces lo mismo y dejar que las
respuestas discrepen es el defecto que ya se rechazó al descartar el booleano por fila (§18).

---

## 8. `ANALISIS_SOLICITUD`

**Una fase por versión de proyecto, y todas igual de importantes.**

| Eje | Ámbito | Estado |
|---|---|---|
| Trámite `ANALISIS_DOCUMENTAL` | **Por versión** — el reformado es documentación que entra, se analiza y produce su propio `DIAGNOSTICO` con su fecha | Decidido |
| Requisitos **documentales** | **Global por solicitud**, salvo los marcados como afectados por reformado | Decidido |
| Requisitos **técnicos** (`coberturas_item_tecnico`) | **Solicitud + reformado**: la verificación se predica del contenido del proyecto | Decidido |
| Requerimientos **particulares** (`requerimientos_tarea`) | — | **Abierto** (§17) |

`reformado_id` **NULL significa versión inicial**, coherente con que el proyecto original vive en
`proyectos` y no en la tabla de reformados. No hay que crear filas retroactivas para los expedientes
existentes.

### El flag de afección por reformado, y el caso de la tasa

Un requisito documental puede estar **afectado por reformado** (columna en el catálogo
`requisitos_documentales`). El caso que lo motiva es la tasa: si el reformado cambia el presupuesto
lo bastante, procede tasa complementaria.

En el análisis documental de la versión nueva se revisa: si no cambia, se alimenta con la tasa
antigua y resuelto; si cambia, se pide el complemento y resuelto. Si algún día aparece otro
documento que dependa de la versión, se marca igual.

**Traducción física propuesta** (pendiente de confirmar): `reformado_id` *nullable* en
`documentos_requisito`, con dos índices únicos parciales — `(requisito, solicitud) WHERE
reformado_id IS NULL` para los no afectados y `(requisito, solicitud, reformado)` para los
afectados. En `coberturas_item_tecnico` el `reformado_id` también sería nullable, con NULL =
versión inicial.

Así la tasa complementaria **no es un requisito nuevo**, sino el mismo requisito cubierto en otra
versión con otro documento — lo que evita tocar la cardinalidad «un documento por requisito». Es
además la única vía viable: `RequisitoDocumental` es catálogo **global** con condiciones sobre
variables del motor, y no admite requisitos *ad hoc* para una solicitud concreta.

**Arrastre:** `tasa_impagada` (`calculado.py:320`) cuenta requisitos cubiertos **por solicitud**;
habrá que reescribirla para que mire la versión vigente.

---

## 9. `CONSULTAS`

**La ronda no *es* la versión: cuelga de ella.** Antes, una segunda fase CONSULTAS se creaba porque
estaba permitido y porque el usuario tenía en la mano un reformado que no sabía dónde meter y unas
separatas nuevas. Ahora: *hay un reformado, luego se puede hacer una nueva ronda, y queda
justificada*. Lo totalmente permitido pasa a estar registrado y auditado.

Consecuencias verificadas:

- Con una fase `CONSULTAS` por versión, **el organismo hereda la versión por su fase** y no necesita
  dato propio. El «solo los afectados» se expresa en qué filas de `organismos_expediente` nacen en
  la fase nueva.
- `UNIQUE (fase_id, organismo_id)` deja de estorbar: cada ronda es una fase distinta y el mismo
  organismo puede repetirse entre fases. `organismos_expediente` se queda como está.
- Las separatas nuevas no piden nada: son `DOC_SEPARATA` que consume el `ELABORAR` de la fase de la
  versión nueva.

---

## 10. `INFORMACION_PUBLICA`

**Decidido (2026-09-08). La IP se repite entera; no cabe parcial.**

- **Enganche: `fases.reformado_id`, y nada por debajo.** Es el más simple de los tres, y por razón
  distinta a la de consultas: allí el organismo hereda la versión de su fase porque solo se
  reconsulta a los afectados; aquí porque la exposición es indivisible.
- **El alcance lo redacta el anuncio, y queda fuera del modelo.** BDDAT registra que hubo una IP
  sobre el reformado N, no sobre qué versaba. La alegación presentada en la segunda IP contra la
  parte **no** modificada no se acepta, pero eso es juicio del técnico y va a la resolución: el
  sistema no lo evalúa.
- **Los canales dependen del tipo de solicitud** —solo BOP; BOP y BOJA; BOP, BOJA, BOE, diario y
  tablón…—. No son siempre los mismos ni siempre cinco.

### Deudas que el reformado destapa (ninguna la crea)

**1. Dos reglas de bloqueo se vuelven permisivas.** Las reglas **38** (`ANY/ANY/RESOLUCION`, con
`solicitud_incluye_dup`) y **1718** (ídem, con `instrumento_ambiental EQ AAU`) impiden abrir la
resolución mientras la IP no haya concluido, y ambas se apoyan en `fase_ip_finalizada EQ false` —
variable existencial. Con la IP de la versión inicial cerrada y la del reformado abierta, la
variable afirma que la IP terminó y las dos reglas **dejan pasar la resolución**, justo en el
escenario en que más importan. Hay que reescribir la variable en universal.

**2. Las alegaciones tienen que aislarse por ronda.** `ALEGACION_IP` y
`RESPUESTA_TITULAR_ALEGACION` los consume `ANALISIS_ALEGACIONES.ANALIZAR` **«todas las del
expediente»** (`TIPOS_DOCUMENTOS_CATALOGO.md`), lo que con dos IP mezcla rondas y choca con §4: si
las alegaciones de la primera siguen sin contestar, tienen que seguir contando **en su fase**. Las
alegaciones llevan además la ronda/versión que las aísla.

**3. Los destinatarios múltiples necesitan tabla.** `Tramite` no tiene destinatario —solo `fase_id`,
`tipo_tramite_id` y `observaciones`—: a los organismos se les adosa con la puente
`tramites_organismos` (ADR-011), y para las publicaciones no hay equivalente. Hoy N trámites
`TABLON_AYUNTAMIENTOS` son hermanos indistinguibles salvo por el oficio que cuelga de cada uno.

Y no es solo el tablón. El art. 144 RD 1955/2000 multiplica **tres** destinatarios en la misma
frase: el «Boletín Oficial de **las provincias afectadas**», «uno de los diarios de mayor
circulación de **cada una de las provincias** afectadas» y «**los Ayuntamientos** en cuyo término
municipal radiquen los bienes». Solo BOE, BOJA, portal y titular son únicos. Los vectores fijos ya
tienen su trámite; los indeterminados en nombre y número —diputación, diario, ayuntamiento— no
tienen dónde vivir.

Esta refactorización **habría hecho falta igual sin reformados**; lo que el reformado añade es que
se pueda repetir entre versiones, y eso sale gratis heredando la versión por la fase, igual que en
consultas. Por eso va por su cuenta: **issue #882**.

**Propuesta (a confirmar): `publicadores_expediente`**, calcada de `organismos_expediente`:

| Pieza | Cómo |
|---|---|
| Columnas | `expediente_id` + **`fase_id`** + `entidad_id`, con puente `tramites_publicadores` al estilo de `tramites_organismos` |
| Por qué puente y no FK en `Tramite` | Ese modelo es deliberadamente agnóstico; ADR-011 eligió el puente por eso, y el nodo sintético de ADR-042 ya sabe agrupar trámites por un id vía puente — el nodo del árbol sale gratis |
| Versión | **Heredada por la fase**, sin columna propia. Entre rondas se repite libremente |
| Canal | Sin columna: lo dice el tipo del trámite vinculado |

Dos piezas ya en el modelo hacen esto barato: `Entidad.rol_publicador` —«Puede publicar
anuncios/notificaciones. Ej: diputaciones, ayuntamientos» (`app/models/entidad.py:83`)— es el gemelo
exacto de `rol_consultado`, está en el CHECK de roles y **hoy no lo usa nadie** (0 entidades); y
`entidades.nif` es *nullable*, así que un diario cabe como entidad sin inventar texto libre ni tabla
aparte.

**Abierto:** si los publicadores únicos (BOE, BOJA) entran también por uniformidad o se quedan fuera
por no aportar nada.

**4. Interprovincialidad y órgano tramitador — para estudiar más adelante.** Cuando la instalación
afecta a más de una provincia el expediente se rescata y lo tramitan los servicios centrales.
Modelarlo bien exige que el expediente tenga pertenencia a un órgano tramitador y que ese traslado
sea posible: refactor grande, objetivo de **exportación al resto de Andalucía**, no de producción.

**Qué se le dice a BDDAT mientras tanto:** que el expediente **se archiva y se da traslado a los
servicios centrales**. Si para entonces no hay BDDAT en servicios centrales, se usa el mecanismo de
remisión de expediente que se usaría para cualquier tercero. Un reformado que convierta un
expediente en interprovincial no ocurre todos los años, así que no condiciona el diseño de ahora.

Tampoco bloquea la IP, porque **el registro de qué se publicó en cada ronda lo dan los trámites de
cada fase**, no la property. `Proyecto.es_interprovincial` y `provincias_afectadas`
(`app/models/proyectos.py:201`) se calculan sobre `municipios_proyecto`, que se sobrescribe: sirven
para decidir qué crear ahora, no para reconstruir el pasado.

---

## 11. Las fases ambientales

Tres fases con particularidades propias y un enganche común.

**Decidido (2026-09-08).**

- **Enganche: `fases.reformado_id` en las tres, y nada por debajo.** Ninguna tiene cardinalidad
  variable dentro: es una interlocución con un solo órgano, no N destinatarios.
- **Control: la regla genérica de §14, y ninguna regla propia.** «Impedir una segunda
  `COMPATIBILIDAD_AMBIENTAL` si no hay reformado» y «no crear una fase que cubra una versión ya
  cubierta» son la misma frase leída del derecho y del revés: sin reformado, la versión vigente es
  la que ya cubrió la primera fase → bloqueo; con reformado, es otra → permitido, justificado y
  auditado.
- **Sin trabas añadidas.** Lo que hará el órgano ambiental ante un reformado a mitad de tramitación
  es previsión de comportamiento, no consecuencia normativa: la Ley 2/2026 regula la modificación de
  actuaciones «ya autorizadas, ejecutadas o en proceso de ejecución» (arts. 63 AAI, 74 y 75 AAU, 85
  AAUS) y su art. 71 —el procedimiento completo de la AAU— **no contempla que el proyecto cambie por
  el camino**. BDDAT documenta lo que llegue y no pone condiciones.

### Cierre conjunto: dos fases, un resultado

El patrón que se repite en las tres: se remite el reformado, y el órgano ambiental —en vez de
resolver por separado— incorpora el modificado a lo que ya tenía y emite **un solo pronunciamiento
que vale para las dos peticiones**. Entonces se cierran las dos fases, a la vez o consecutivamente.

**Ya está soportado, sin tocar el modelo:** `fases.documento_resultado_id` no tiene UNIQUE (solo la
FK), y `editar_fase` solo valida que el documento pertenezca al mismo expediente
(`app/services/mutaciones_arbol.py:689`). Dos fases pueden por tanto cerrarse con el **mismo**
documento; y «cerrar la primera con los datos del segundo» es eso más `Fase.observaciones`.

El cierre forzado que a veces hará falta también existe: `editar_fase(…, justificacion=…)` salta los
bloqueos forzables y registra uno por invariante en bitácora (#723). La única puerta que no se
fuerza es la fase **vacía** —sin trámites—, donde la vía es borrarla, no cerrarla.

> **Hueco detectado aquí, corregido aparte (#883):** la guarda del pool no comprueba
> `fases_resultado`, así que el documento que cierra una fase se puede borrar. Es defecto de hoy,
> pero el cierre conjunto lo agrava: un solo borrado se llevaría varios cierres por delante.

> **Esto retira una propuesta intermedia de esta sesión.** Se llegó a plantear un flag
> acumulativa/sustitutiva en el tipo de fase, bajo la idea de que en las ambientales «prevalece la
> última». No es así: las dos fases **siguen contando y las dos se cierran**, con el mismo documento
> o con el segundo documentando la primera. §4 se cumple sin excepción y no hace falta flag alguno.

### `COMPATIBILIDAD_AMBIENTAL`

Se remite el proyecto y el estudio de impacto ambiental; vuelve un informe de compatibilidad. Si es
desfavorable llega en su lugar la notificación de audiencia previa al peticionario, que es lo que
recoge `COMUNICACION_AUDIENCIA` (IC 1/2022, IV.3.3). Si es favorable, además informa de los ámbitos
de la información pública y de las consultas, a efectos de los dos órganos.

Un reformado obliga a remitir de nuevo y a recibir otro informe: se repite tantas veces como haga
falta, una fase por versión. **Pueden solaparse**: lo previsible es que, sin haberse resuelto la
primera, incorporen el modificado y saquen una sola compatibilidad para ambas.

### `AAU_AAUS_INTEGRADA`

Sus trámites son consecutivos, así que lo que pase con el reformado depende de en qué punto esté el
órgano ambiental —dictamen, propuesta— y de si retrocede o no **en su propio procedimiento**, cosa
que no controlamos. Por nuestra parte, las dos fases se cierran cuando llegue el informe vinculante
definitivo conjunto.

**No clonar la fase anterior.** Si el informe vinculante ya se recibió, Medio Ambiente no reevalúa:
abre modificación no sustancial, y por el art. 74.6 eso **no produce otro informe vinculante** sino
una comunicación que el titular puede ejecutar si el órgano «no manifieste lo contrario en el plazo
de un mes mediante resolución motivada». La fase de la versión nueva llevará por tanto trámites
distintos de los cinco de la primera. A falta de la nueva instrucción conjunta **no se inventa ese
trámite en el FTT**: la fase se abre igual, sus trámites se crean según lo que Medio Ambiente
conteste, y cuando la instrucción salga se cataloga.

### `FIGURA_AMBIENTAL_EXTERNA`

Es la única con enganche pasivo: no se instruye nada, se espera —la fase existe como guarda para no
resolver sin haber recibido la figura—.

Ante un reformado: **se cierra la fase de la versión previa y se abre la de la nueva**, con cierre
forzado si hace falta. El oficio de la fase (`OFICIO_SOLICITUD_FIGURA`) se reemite para el
reformado.

Lo que llegue manda, y no se le ponen condiciones:

- Si se emiten **dos** figuras, cada una se coloca donde proceda y se cierran las dos fases.
- Si solo se emite la **segunda**, se cierra la primera con los datos de esa segunda y las
  observaciones que expliquen por qué.

El motivo de no reglar aquí no es comodidad: el comportamiento del órgano ambiental —y sobre todo el
de los ayuntamientos con la licencia ambiental— **no está claro cuando el cambio se coge en fases
intermedias**, y la Ley 2/2026 no lo aclara. Documentar es todo lo que cabe hacer con rigor.

---

## 12. `CONSULTA_MINISTERIO`

**Decidido (2026-09-08).** No hay nada que rascar aquí: es una consulta más, y de hecho **más simple
que las del art. 127**. Un solo destinatario fijo —la Dirección General de Política Energética y
Minas—, sin cardinalidad variable, así que ni siquiera necesita el equivalente de
`organismos_expediente`: **`fases.reformado_id` y nada por debajo**. Una fase por versión, la regla
genérica de §14 evita duplicar sobre la misma, y el cierre conjunto de §11 vale igual si el
Ministerio incorpora el reformado y emite un solo informe.

Del art. 114 RD 1955/2000, para no volver a leerlo: aplica a instalaciones de **transporte**
competencia de las CCAA; se remite «la solicitud y **la documentación que la acompañe**» —el
proyecto entero, sin extracto—; el informe se emite en **dos meses** y, si no llega, «se proseguirán
las actuaciones».

### Deuda transversal que esta fase destapa: la suspensión acumulada

`catalogo_plazos` marca esta entrada con `suspende_plazo_solicitud = true` (art. 22.1.d LPACAP),
igual que `CONSULTA_SEPARATA` (30 días) y `REQUERIMIENTO_SUBSANACION` (10 días). Y `plazos.py` funde
los intervalos **solapados**, porque «un reloj no se para dos veces» — pero **dos rondas no se
solapan: son sucesivas**, así que suman.

La premisa que hoy sostiene que no hace falta controlar el tope está escrita en el propio docstring
de `plazos.py`, y con reformados deja de ser cierta:

> «El art. 22.1.d añade que la suspensión "no podrá exceder en ningún caso de tres meses", límite
> que en la práctica no muerde —todos los plazos de informe que BDDAT maneja son de tres meses o
> menos— y que se vigila al dar de alta la entrada, no en el cómputo.»

Cierto **por entrada**, falso **por acumulación**: dos consultas al Ministerio son 2 + 2 = cuatro
meses de suspensión. El tope se vigila al dar de alta la fila del catálogo, y ahí nadie ve que la
misma fila se va a disparar dos veces. Enlaza con lo que #778 dejó anotado como no fijado.

**Pero el fondo no es un defecto de modelo, es una laguna de la ley.** El art. 22.1.d no aclara si
su tope es por cada informe pedido o acumulado, y **la norma no dice nada de reformado tras
reformado**: ni para las consultas, ni para la IP, ni para las ambientales, ni para esta. Con un
promotor que presenta un proyecto inmaduro y lo reforma varias veces, la Administración consume su
propio plazo por un defecto que no es suyo, y no hay regla que lo resuelva. Es de las lagunas que
crujen al modelarlas con un sistema determinista, y conviene no tapar el crujido con una decisión
inventada.

**Cuándo importa de verdad**, que es el criterio que sí está claro: consumir plazo no preocupa por
sí solo. Preocupa cuando hay **derechos de terceros** en juego y el vencimiento produce resolución
desfavorable — el silencio es **desestimatorio** en AAP (art. 128) y en AAC (art. 131.7)
(`NORMATIVA_MAPA_PROCEDIMENTAL.md`), y en DUP eso arrastra la expropiación. Ahí el cómputo tiene que
ser exacto; en el resto, informativo.

### Apunte para `RESOLUCION`

El art. 114 in fine obliga a notificar la resolución **a la DGPEM y a la CNE** (hoy CNMC).
Comprobar al barrer esa fase si `NOTIFICACION`/`PUBLICACION` lo contemplan o es un hueco.

---

## 13. `RESOLUCION` y el certificado de fin de instrucción

**Decidido (2026-09-08). La resolución no identifica la versión: la identifica el sello.**

No hace falta campo nuevo ni en la fase ni en la solicitud. La versión sobre la que se resuelve es
**la vigente en el instante en que se selló la instrucción**, y ese instante ya está materializado en
`solicitudes.documento_fin_instruccion_id`, con la auditoría congelada y el informe redactado
dentro. Encaja con el art. 82.1 —«instruidos los procedimientos, e inmediatamente antes de redactar
la propuesta»— y con lo que ya existe: un reformado posterior al sello obliga a **deshacerlo**
(#838) y a re-emitirlo. Como la solicitud tiene **una sola** FK al certificado, no caben dos
vigentes ni ambigüedad.

`RESOLUCION` tampoco se repite por versión: es fase finalizadora única, la regla genérica de §14 no
le aplica y ya la guardan las reglas 1787/1788 (sin certificado no se abre).

### Qué gana el certificado

**1. La cabecera dice sobre qué versión se resuelve, y se redacta distinto según haya reformados o
no.** El bloque de `_solicitud` (`app/services/informe_instruccion.py:419`) es su sitio: es lo que
la solicitud dice de sí misma, y lo que después reutiliza el contexto de la resolución.

- **Sin reformados** —el caso normal— el texto sigue siendo llano, sin estructura de versiones ni
  menciones a algo que no ha pasado.
- **Con reformados**, la versión vigente con su fecha y la relación de las anteriores.

**2. `Bloque.ambito` deja de ser `None`, y eso simplifica ADR-043.** El ADR previó un **registry de
particularidades por código de tipo de fase** con este argumento: el ámbito «solo lo sabe la fase que
consultó, y ninguna función genérica puede deducirlo». Con `fases.reformado_id` deja de ser cierto —
**el ámbito es un campo de la fase**, lo rellena el tronco leyendo un dato—. El registry seguirá
valiendo para otras particularidades, pero **no hace falta para esto**, que era su primer consumidor
declarado.

Para las fases de la versión inicial, `reformado_id` es NULL y el texto se redacta explícitamente
—«sobre el proyecto en su redacción original»—, no se deja vacío: un hueco parecería un dato que
falta.

**3. El relato se agrupa por versión** cuando las hay: *sobre el proyecto en su redacción original
se instruyó esto; sobre el reformado 1, esto otro*. Es presentación —los bloques y el ámbito ya
están—, y es el «cada uno con sus tiempos» de §4.

**4. Las observaciones del cierre de cada fase suben al relato**, y siempre: si no las hay, la línea
se escribe igual —«Observaciones al cierre: -»—.

Es lo que resuelve el **cierre conjunto** de §11 sin que el sistema infiera nada. Cuando dos fases
ambientales se cierran con el mismo documento, lo que explica por qué ese documento se consumió dos
veces es **el comentario que el técnico escribió al cerrar**. Si no escribió nada, el certificado no
dice nada, la resolución saldrá pobre y se corrige a mano o en el sitio adecuado. El sistema no
adivina el motivo de un cierre conjunto ni lo deduce de que dos fases compartan documento.

### Lo que ya funciona y no hay que tocar

`revisar()` recorre **todas** las fases de instrucción ordenadas por id, no solo las de la última
versión, y cualquiera con hueco sale como `PENDIENTE`, lo que deja `Informe.limpio` en falso e
impide consolidar. **El principio de §4 ya está implementado**: la fase de la versión inicial con su
cálculo pendiente bloquea el certificado aunque la del reformado esté impecable.

Y `_relato_reversiones` ya narra los certificados anteriores dejados sin efecto (#838). Con
reformados ese relato gana sentido —«se dejó sin efecto el de fecha X por la entrada del reformado
2»—; hoy el motivo es texto libre de la justificación y puede quedarse así.

### Apunte pendiente

El art. 114 in fine obliga a notificar la resolución **a la DGPEM y a la CNE** (hoy CNMC).
Comprobar si `NOTIFICACION`/`PUBLICACION` lo contemplan o es un hueco — no es cuestión de
reformados, pero se detectó barriéndolos.

---

## 14. Regla de motor sobre las fases

**Decidido (2026-09-08).** Se prohíbe crear una fase que cubra una versión ya cubierta por otra fase
del mismo tipo.

El criterio no es de consultas: vale igual para `ANALISIS_SOLICITUD` y para las ambientales, así que
admite **una sola regla con sujeto genérico y condición de encuadre** —el patrón de #582, que evita
enumerar las fases una a una— en vez de una regla por fase.

Con la versión como sujeto, **#864 queda desbloqueado**: «el análisis de esta versión está cerrado»
es una pregunta formulable, sin caer en el existencial que hoy mentiría en la ronda del reformado.

---

## 15. Árbol

La lista de reformados dibuja una **metafase virtual**: un nodo intermedio que aparece solo cuando
hay algún reformado. Es el patrón de ADR-042 un nivel más arriba y hereda su mecánica **aditiva**:
el backend añade el payload y el front decide la agrupación, sin reparentar nada y sin coste para
los expedientes sin reformado.

En la interfaz —nodo del árbol, inspector, oficios de consulta— el texto es el que ya entienden los
organismos: «REFORMADO DE PROYECTO de fecha \_\_\_\_», junto al «PROYECTO de fecha \_\_\_\_» de la
versión inicial.

---

## 16. El conjunto documental a resolver

El principal produce la versión inicial; los demás `DOC_PROYECTO` producen reformado o no, y todos
juntos —por consulta— forman el conjunto documental del proyecto sobre el que se resuelve. Con una
condición: que estén **consumidos o producidos por alguna tarea**, no huérfanos.

**Matiz de cuándo se evalúa** (verificado): el radar define huérfano **solo por ausencia de
`DocumentoTarea`** (`app/routes/api_huerfanos.py:135`); no mira ningún vínculo con el proyecto. Así
que entre la ingesta preparatoria en lote y el `ANALIZAR` que los consuma, el principal y los
reformados **aparecen en el radar como huérfanos** aunque tengan destino declarado. No invalida el
criterio —el conjunto se conforma después del análisis— pero un documento anclado como principal o
que abre reformado no debería listarse igual que uno sin destino ninguno. Se resuelve en la reforma
del listado del pool: **#881**.

---

## 17. Abierto

**El barrido de fases está cerrado** (§8 a §13): las nueve fases del ESFTT repasadas, con su
enganche decidido. **Los cabos también** (ver abajo). Lo que queda abierto no bloquea el diseño:
son decisiones de detalle, una espera normativa y una idea aparcada. Procede llevar la decisión a
ADR y congelar este documento en `historial/`.

| Punto | Qué falta decidir |
|---|---|
| **Trámites de la AAU modificada** | La fase AAU de la versión nueva llevará trámites que hoy no están en el FTT (§11): se catalogan cuando salga la instrucción conjunta |
| **Aislamiento de alegaciones** | Cómo lleva la alegación su ronda (§10 deuda 2) |
| **Ingesta en lote** | En el lote inicial preparatorio, si entran tres `DOC_PROYECTO` seguidos, el primero se lleva la pregunta de anclaje y los otros dos la de reformado, que en ese momento es ruido. Se mitiga con el «por defecto no», pero condiciona la pantalla |
| **Edición concurrente** | Un candado por expediente, idea aparcada para su propia sesión. No lo necesita este diseño: #884 basta para que dos shuttles no se pisen |

### Cerrados en la sesión del 2026-09-08

| Cabo | Cómo quedó |
|---|---|
| **`REFUNDIDO`** | Sin nada que modelar: lo que importa es si el documento produce corte, no su apellido (§5) |
| **Requerimientos particulares** | `reformado_id` como atributo de nacimiento, nunca clave. Depende de que el guardado deje de ser destructivo: **#884**, precedente |
| **Radar de huérfanos** | A la reforma del listado del pool: **#881** |
| **Suspensión acumulada** | Anotada como laguna de la ley (§12), sin tarea: no preocupa |
| **Columnas de `reformados_proyecto`** | `documento_id` y `origen` (voluntario / requerido). El resto se deriva o vive en la bitácora (§6) |
| **`publicadores_expediente`** | Con vida propia: **#882**. Aquí solo queda que herede la versión por la fase |

---

## 18. Alternativas descartadas

### De modelo

| Alternativa | Por qué no |
|---|---|
| Vínculo directo fase↔documentos (#819 original) | Quien tiene la relación con la versión no siempre es la fase: en consultas es el organismo, en el análisis el requisito técnico |
| Entidad de versión separada de los documentos | Innecesaria: el reformado **es** el documento que lo introduce, con el patrón de anclas ya establecido |
| Columna `produce_edicion_proyecto` por fila, rellenada por el técnico | Pregunta dos veces lo mismo con oportunidad de contradecirse, y el error se propaga en silencio a qué fases se consideran afectadas |
| Hardcodear el literal `'MODIFICADO'` | Se apoyaría en un `varchar` libre sin CHECK |
| Subir `tipo` a catálogo con flag | Resuelto por §6: la existencia de la fila ya es la declaración |
| Mantener `documentos_proyecto` añadiéndole columnas | Todo lo que contiene es deducible; lo único con valor es frágil y se rehace mejor |
| Meter el proyecto original como primera fila de la tabla | Chirría con el nombre, y es innecesario: el original ya está en `proyectos` (§7) |

### De nombre

| Nombre | Por qué no |
|---|---|
| `ediciones_proyecto` | «Edición» tiene los dos sentidos —versión y acto de editar— y en este repo *editar* está establecido como verbo de modificación (34 ocurrencias en 20 ficheros, `editar_fase`, `editar_expediente`, el permiso `'editar'`). Se leería como bitácora de modificaciones |
| `versiones_proyecto` | Correcto y ya usado en la docstring de `Proyecto`, pero permitía meter el original en la tabla y no dice nada a quien lea el oficio |
| `modificados_proyecto` | Colisiona con `proyectos.es_modificacion`, que significa modificación de instalación existente (art. 115): dos «modificado» distintos en el mismo modelo |

`reformados_proyecto` gana porque es lo que los técnicos escriben en los títulos, lo que los
organismos leen en el oficio de consulta, y no colisiona con nada.

---

## 19. Trazabilidad documental

Ningún ADR menciona `documentos_proyecto` (verificado con grep sobre `docs/decisiones/`): retirarla
no enmienda ninguna decisión adoptada. Quedan tocados por otras vías:

| Documento | Qué le pasa |
|---|---|
| ADR-016 + ADR-042 | El nodo de reformado es un nodo sintético más, entre solicitud y fase; ADR-042 enmendó ADR-016 §1 por lo mismo un nivel más abajo |
| ADR-032 | La ingesta gana un paso: la bifurcación de §6 y la fecha obligatoria para `DOC_PROYECTO` |
| ADR-038 | El criterio del radar de huérfanos, ante documentos con destino declarado sin tarea (§12) |
| ADR-041 §D bis | Dos anclas documentales nuevas: el principal del proyecto y cada reformado, esta con reversión automática y solo sobre la última |
| ADR-043 §E | El `ámbito` que quedó vacío a propósito se rellena aquí — y **sin el registry por tipo de fase** que el ADR preveía para ello: con `fases.reformado_id` el ámbito es un campo, no conocimiento específico de cada fase (§13) |
| ADR-002 | La fecha derivada del documento es este ADR aplicado |
| ADR-011 | Su patrón de tabla puente trámite↔destinatario es el que replica `publicadores_expediente` (§10) |
| ADR-033 §7 | Se cita; cambiaría solo si se toca `requerimientos_tarea` |
| `TIPOS_DOCUMENTOS_CATALOGO.md` | `ALEGACION_IP` y `RESPUESTA_TITULAR_ALEGACION` dicen «todas las del expediente»: hay que acotarlo por ronda (§10) |
| `DISEÑO_CONSULTAS_ORGANISMOS.md` §6 bis, §8 | Se queda con su parte y apunta aquí |
| `DISEÑO_ANALISIS_SOLICITUD.md` §4, §6 | Le entra el eje de versión |
| `DISEÑO_SUBSISTEMA_DOCUMENTAL.md` §2 | Sustituir el ejemplo del patrón N:M |
| `INVENTARIO_BACKEND.md` | Retirar `DocumentoProyecto`, dar de alta `ReformadoProyecto` |
| #819 | Su cuerpo propone lo descartado; hay que corregirlo |
