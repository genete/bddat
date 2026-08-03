# ADR-037 — Vocabulario ESFTT (tabla) vs. permiso normativo (motor): refinamiento de ADR-007

**Estado:** Propuesta
**Fecha:** 2026-08-03
**Issue:** #725
**Enmienda:** ADR-007 (no la revierte — precisa qué contaba como "whitelist")

---

## Contexto

#725 partía de un criterio rector que, leído contra ADR-007, generaba una contradicción real:
"lo posible y su orden → dato estático (tabla), las excepciones → motor" es, literalmente, la
arquitectura de whitelist-más-excepción que ADR-007 eliminó en #387 razonando que divide la
lógica de negocio entre dos sistemas con semánticas opuestas y esconde la razón normativa de
cada restricción.

Al mismo tiempo, #719 (orden canónico de tareas, trámite→tarea) ya había resuelto ese nivel con
el criterio contrario: el motor es el único árbitro de "¿es posible?"; la tabla (`tramites_tareas`)
solo aporta una secuencia sugerida, no vinculante, saltable con justificación.

La pregunta de fondo: ¿#725 debía reabrir ADR-007 para fase→trámite, o el criterio de #719 debía
generalizarse también hacia arriba? Un análisis nivel a nivel (expediente→solicitud,
solicitud→fase, fase→trámite, trámite→tarea) muestra que ADR-007 tenía razón en cuanto al
**permiso**, pero su lenguaje ("tablas whitelist") no distinguía dos cosas distintas que convivían
en esas mismas tablas eliminadas:

1. **Permiso normativo** — ¿está permitida esta combinación dado este caso concreto? Siempre
   citable a una norma, cambia cuando cambia la ley.
2. **Vocabulario ESFTT** — ¿qué tipos de trámite pertenecen conceptualmente a qué tipos de fase?
   Nunca citable a una norma — es la propia taxonomía que BDDAT inventó para organizar el
   procedimiento (ADR-016 §8/§16); otra idealización de tramitador podría decomponerlo distinto.

Las tres tablas que ADR-007 eliminó (`expedientes_solicitudes`, `solicitudes_fases`,
`fases_tramites`) mezclaban ambas cosas bajo una sola fila binaria "permitido/no permitido", sin
separar cuál de las dos preguntas respondía cada restricción. Por eso funcionaban como blacklist
implícita sin razón visible — el diagnóstico de ADR-007 era correcto. Pero de ahí no se sigue que
el vocabulario en sí mismo no deba existir como dato: solo que no debe **gatear permiso**.

## Test operativo

Para decidir dónde vive un hecho concreto, una sola pregunta:

> **Si este hecho cambiara mañana, ¿el origen sería una norma nueva (BOE/BOJA) o una decisión
> nuestra de reorganizar el ESFTT?**

| Origen del cambio | Mecanismo | Ejemplo |
|---|---|---|
| Norma, citable, cambia por ley | `reglas_motor` | RAIPEE exige `es_expediente_produccion` (RD 1183/2020, #410) |
| Taxonomía ESFTT propia, nunca citable a un artículo | Tabla de vocabulario | `CONSULTA_SEPARATA` es trámite de la fase `CONSULTAS` |
| Imposibilidad lógica del modelo, nunca es una decisión | Invariante en código | No se puede `NOTIFICAR` un documento inexistente |

## Decisión

### A — Dos árbitros de permiso, no uno: `reglas_motor` (normativo) y categoría C (estructural)

`reglas_motor` decide "¿es posible?" allí donde el contenido es genuinamente normativo —citable
a una norma, candidato a cambiar cuando cambia la ley—: expediente→solicitud y solicitud→fase
siempre; fase→trámite en la capa condicional sobre el vocabulario (p. ej. `COMUNICACION_INICIO`
obligatorio si Renovable, `ANUNCIO_BOE` solo si hay DUP).

Donde el contenido es estructural —no hay margen de maniobra real y no hay norma que citar, solo
LPACAP en sentido genérico y la forma en que hemos organizado el ESFTT— el árbitro es la
**categoría C** (§C), nunca una fila de `reglas_motor`. Trámite→tarea es el caso puro: forzar esa
comprobación por `reglas_motor` exigiría una regla por cada tipo de trámite —el sujeto no
generaliza sin repetir la propia secuencia que ya declara `tramites_tareas`—, es decir, reescribir
el dato de la tabla como regla: duplicado y propenso a divergir. La comprobación de
vocabulario/cardinalidad/orden lee la tabla directamente, en código, una sola vez, genérica para
todos los tipos — sin pasar por `reglas_motor`.

`reglas_motor` no queda vacío en ningún nivel con contenido normativo real que evaluar; en
trámite→tarea, hoy, ese contenido no existe más allá del veto global de `modo_global`, que sigue
aplicando igual — es ortogonal: apaga el motor entero, no evalúa nada por tipo. Esto no reabre
ADR-007: ninguna tabla gatea permiso por sí sola en ningún nivel; solo cambia cuál de los dos
árbitros (`reglas_motor` o categoría C) responde según de qué tipo de contenido se trate.

### B — Vocabulario ESFTT como dato de catálogo, nunca como permiso

Se recrea `fases_tramites` (tipo_fase_id, tipo_tramite_id, cardinalidad_maxima nullable) — **sin**
columna de orden: no hay caso de uso confirmado hoy (los trámites de una fase son mayormente
paralelos), se añade si aparece uno real. Confirmado como N:M genuino, no jerarquía 1:1: códigos
como `RECEPCION_INFORME`, `ELABORACION`, `NOTIFICACION` se reutilizan bajo más de una fase
(`ESTRUCTURA_FTT.json`), y `tipos_tramites.codigo` es único en BD — necesita tabla puente de
verdad. `tramites_tareas` (trámite→tarea) ya existe con este mismo espíritu desde #345.

Cardinalidad es un concepto transversal a los cuatro niveles (no exclusivo de fase→trámite ni
trámite→tarea) — se construye la columna donde hay necesidad real hoy (`CONSULTA_SEPARATA` se
crea en bucle, uno por organismo, `api_bc.py:740-748`), no por anticipación.

### C — Categoría C: familia de bloqueos estructurales escapables, no un mecanismo único

Cuando un tipo creado no está en el vocabulario esperado (o excede su cardinalidad), el bloqueo
no es de motor (no hay norma que citar) ni invariante de estado (no es sobre el momento, es sobre
el tipo). Comparte tubería con un precedente real ya en producción —`_check_cierre_fase`/
`_check_completitud_cierre` (#723, `invariantes_esftt.py:484-620`): `EvaluacionResult` con
`puede_escapar=True` explícito, sin cita normativa, y `mutaciones_arbol._bloquea()` tratando ese
escape con la misma bitácora que un bloqueo de motor.

Lo que se reutiliza es **solo esa tubería**, no un chequeo único que cubra cualquier caso futuro.
Los dos precedentes de #723 son de otra naturaleza (completitud de cierre, consumo de
diagnóstico) y se escribieron a mano, caso a caso. El chequeo de vocabulario+cardinalidad
(fase→trámite y trámite→tarea) es un miembro más de esta familia, generalizable entre sí porque
ambos comparten exactamente la misma forma (pertenencia + cardinalidad contra una tabla) — no
porque "categoría C" sea un motor genérico. Al estudiar otras fases en profundidad aparecerán
probablemente más miembros, cada uno con su propia lógica de negocio, escrito a mano como los de
#723 — la tubería de escape se reutiliza, el contenido no se deriva automáticamente.

La pieza de vocabulario+cardinalidad absorbe y cierra #719: el orden no vinculante de
`tramites_tareas` (trámite→tarea) es la misma mecánica aplicada a secuencia en vez de a
existencia/cardinalidad.

### D — Listado (despensa) y creación real son dos momentos distintos, con checks distintos

Separación explícita, motivada por rendimiento (`evaluar()` recarga con `joinedload` de 4 tablas
todo el ruleset activo en cada llamada, sin caché — `motor_reglas.py:196-202`; hoy se invoca una
vez por candidato) y por UX (mostrar 31 tipos de trámite con veredicto de motor es inabarcable):

- **Listado** — solo tablas de vocabulario (más, si es barato, invariantes de estado O(1) como
  `fase.finalizada`). Nunca invoca al motor. Tres grupos: canónicos (vocabulario), resto del
  catálogo (mismo camino, tras un "ver todos"), excluidos de esta vía (tienen su propia acción de
  creación — p. ej. `CONSULTA_TRASLADO_*`, que no producen un objeto válido por el camino
  genérico; nunca aparecen aquí, ni tras el toggle).
- **Creación/borrado real** — único lugar donde se evalúa motor, en orden: hardcode de rutina
  (sin escape) → invariante de estado (sin escape salvo acto explícito) → vocabulario no
  respetado (categoría C, escapable) → motor (escapable).

## Razonamiento

**¿Por qué no reabrir ADR-007 sin más y volver a whitelists de permiso?** Porque el argumento
de fondo de ADR-007 sigue siendo válido: una tabla que gatea permiso sin cita normativa visible
es una blacklist implícita. Lo que ADR-007 no distinguió es que una tabla puede existir sin
gatear permiso — sirviendo solo de vocabulario/orden/cardinalidad — sin reproducir ese problema,
porque no hay ninguna razón normativa que esconder: no la hay.

**¿Por qué no dejarlo todo en motor, como pedía la lectura estricta de ADR-007?** Combinatoria:
9 fases × 31 trámites son 279 combinaciones nominales: la inmensa mayoría no son excepciones
normativas, son conceptos que no existen (nadie propondría `ANUNCIO_BOE` bajo `CONSULTAS`). Sin
vocabulario, la única barrera contra eso es que a nadie se le ocurra escribir una regla motor
para prohibir lo absurdo — y "todo permitido salvo lo prohibido" aplicado a un vocabulario sin
límites long deja pasar exactamente eso. El vocabulario no es una regla de negocio: es la
definición de qué tipos son conceptos reales en cada nivel.

## Consecuencias

- `fases_tramites` se recrea, con guardas explícitas para que ningún consumidor la use como
  gate de permiso — solo `tipos_creables.py` (listado) y la categoría C (creación real).
- `TRAMITES_CADENA_SUBSANACION` (`invariantes_esftt.py`) se deriva de patrón de tareas (¿el
  trámite tiene `ANALIZAR` en su secuencia, dentro de esta fase?), no de cardinalidad — la
  cardinalidad no distingue `ANALISIS_DOCUMENTAL` (cardinalidad 1, sí pertenece a la cadena) de
  lo que no pertenece.
- `_CODIGOS_TRASLADO` (triplicado en `api_bc.py`, `mutaciones_arbol.py`, `tipos_creables.py`) se
  centraliza en una columna de catálogo — deuda de mantenimiento ortogonal a esta decisión.
- #719 se cierra al implementar la categoría C para trámite→tarea.
- El caché ausente en `evaluar()` (`motor_reglas.py`) se fila como issue aparte — no bloquea
  esta decisión, pero el modelo D reduce ya el número de invocaciones por construcción.
- El docstring de módulo de `invariantes_esftt.py` prometía una migración a variables de
  `ContextAssembler`/`reglas_motor` que nunca se planificó y que, con este ADR, tampoco procede:
  su contenido (integridad hoja-a-hoja #722, sellado ADR-036, completitud #723) no es normativo
  ni citable — moverlo a `reglas_motor` no ganaría nada y perdería la semántica de "precondición
  estructural, no forzable" que varias de sus ramas tienen a propósito. Se corrige el docstring
  para reflejar que el módulo es permanente, no un paso intermedio.

## Referencias

- ADR-007 — `docs/decisiones/ADR-007-eliminar-whitelists-ESFT.md` (enmendada aquí)
- #725, #719, #723, #410, #387, #345
- `docs/referencia/ESTRUCTURA_FTT.json`, `docs/referencia/ESTRUCTURA_ESF.json`
