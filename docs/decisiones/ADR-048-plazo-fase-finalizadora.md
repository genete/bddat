# ADR-048 — Las fases finalizadoras portan plazo propio, excepción acotada a #788

**Estado:** Adoptada
**Fecha:** 2026-09-17
**Depende de:** ADR-041 (plazos y suspensiones, medida única, #788 excluye FASE/TRAMITE) · ADR-046 (`RESOLUCION_DUP` fase propia) · ADR-047 (`RESOLUCION_AAP`/`RESOLUCION_AAC` fases propias)
**Enmienda:** `app/services/plazos.py` (docstring del módulo, #788) · `app/models/catalogo_plazos.py` (CheckConstraint, comentarios) · `docs/referencia/DISEÑO_FECHAS_PLAZOS.md` · `docs/decisiones/ADR-041-plazos-y-suspensiones-medida-unica.md` (nota) · `docs/referencia/NORMATIVA_PLAZOS.md` §2.2
**Origen:** Issue #892 — al ir a dar plazo propio a `RESOLUCION_DUP`/`RESOLUCION_AAP`/`RESOLUCION_AAC` (converge con ADR-046 §Consecuencias y ADR-047, tarea pendiente de #918) se encontró que #788 excluyó explícitamente el nivel FASE de `catalogo_plazos`, con un `CheckConstraint` puesto a propósito para impedir la vuelta. Sesión 2026-09-17.
**Issues:** #892 (implementación) · #921 (cierre propio por fase) · #922 (UI del plazo de fase)

---

## Contexto

#788 (`docs/referencia/DISEÑO_FECHAS_PLAZOS.md §8`) corrigió un error de #787: las 11 filas de plazo de resolución (arts. 128/131.7/132 bis/ter/133/138/145.4 RD 1955/2000) vivían en nivel FASE (`tipo_elemento_codigo='RESOLUCION'`), y #787 las había purgado de ahí con una justificación falsa ("el plazo de resolución vive a nivel FASE"). #788 las migró a nivel SOLICITUD —el plazo del art. 21.3.b LPACAP («resolver y notificar») es de la solicitud, no de la fase— y bloqueó la vuelta con `CheckConstraint tipo_elemento IN ('SOLICITUD', 'TAREA')`, razonando además que Fase y Trámite son taxonomía ESFTT, no figuras jurídicas: ninguna norma les fija plazo propio, porque no son actos, son contenedores procedimentales.

Esa premisa era cierta para toda fase existente en 2026-05: `RESOLUCION`, `CONSULTAS`, `ADMISIBILIDAD`, `INFORMACION_PUBLICA`... ninguna de ellas es el acto, todas instruyen hacia él. ADR-046 (2026-09-12) y ADR-047 (2026-09-17) cambian ese terreno: crean `RESOLUCION_DUP`, `RESOLUCION_AAP` y `RESOLUCION_AAC` como fases finalizadoras alternativas a `RESOLUCION` para cuando los actos se resuelven por separado. A diferencia de toda fase anterior, **estas tres SÍ son el acto** — la autorización administrativa o la declaración de utilidad pública en sí, cada una con su propio artículo (arts. 128, 131.7 y 148.1 RD 1955/2000) y, desde que existen, con su propia fecha administrativa: `Fase.documento_resultado_id` es el documento que formaliza ese acto concreto.

El propio ADR-046 §A ya lo decía ("cada acto... su propio plazo en catalogo_plazos") y su lista de "Código a tocar" fijaba la tarea como pendiente, convergiendo con #892; #918 dejó la misma nota para el AAP+AAC partido. Pero ninguno de los dos ADR se enfrentó al hecho de que `catalogo_plazos` lo prohíbe hoy a nivel de esquema.

---

## Decisión

### A — FASE vuelve a admitirse en `catalogo_plazos`, acotada a fases finalizadoras

El `CheckConstraint` pasa a `tipo_elemento IN ('SOLICITUD', 'FASE', 'TAREA')`. No es una reapertura general: el filtro real —que la fase sea finalizadora, no taxonómica— no lo impone el constraint (no puede: `tipos_fases.es_finalizadora` está en otra tabla), lo impone el catálogo mismo: solo existen filas para `RESOLUCION_DUP`/`RESOLUCION_AAP`/`RESOLUCION_AAC`, así que una fase taxonómica (`CONSULTAS`, `ADMISIBILIDAD`...) simplemente no tiene camino que case y `obtener_estado_plazo_fase()` devuelve `SIN_PLAZO` sin necesidad de comprobar el flag en tiempo de ejecución — mismo criterio de "el catálogo es el filtro" que ya rige el resto del servicio (una fila sin condición aplica siempre, una fila ausente no aplica nunca). El CRUD de administración sí valida `es_finalizadora` al dar de alta o editar una fila FASE, porque el constraint no cubre lo que se escribe sin pasar por él (mismo argumento que #788 dejó escrito para esta misma tabla).

Camino de 3 segmentos (`<expediente>/<siglas>/<fase>`), entre SOLICITUD (2) y TAREA (5) — mismo mecanismo de `compilar_camino` que ya recorría la ascendencia de FASE para construir el camino de 5 segmentos de una tarea; solo faltaba dejarlo compilar como camino propio.

### B — El disparo hereda la fecha de la solicitud; el cumplimiento queda sin resolver

Las dos fases finalizadoras de una misma solicitud (p. ej. `RESOLUCION_AAC` y `RESOLUCION_DUP` en `AAC+DUP`) arrancan su plazo el mismo día — la entrada de la solicitud en registro — y vencen en momentos distintos porque el artículo que les toca es distinto. `campo_fecha={'fk': 'documento_solicitud_id'}` sigue siendo el mismo vocabulario cerrado de #788; lo único nuevo es que `Fase` no tiene esa FK propia, así que `plazos.py._resolver_campo_fecha` sube a `elemento.solicitud` cuando el atributo no está en la propia fase. No es la indirección `via_tarea_tipo` que #788 retiró —aquella bajaba de trámite a tarea sin FK real de por medio; esta sube por una FK real, `Fase.solicitud_id`—.

El cumplimiento (`campo_fecha_cumplimiento`) queda **NULL a propósito**. `Fase.documento_resultado_id` es la fecha de **dictar** el acto, no de **notificarlo**: el art. 21.3.b LPACAP exige las dos, y `Solicitud.documento_cierre_id` existe justo para separar esa segunda fecha de la primera (ver su docstring en `app/models/solicitudes.py`). La Fase no tiene hoy nada equivalente — no hay certificado de cierre por fase, y `RESOLUCION_DUP` encima notifica a tres grupos de destinatarios distintos (ADR-046 §C), el mismo problema de cardinalidad que motivó `documento_cierre_id` en su día para la solicitud. Diseñar ese cierre propio por fase es #921, no de este ADR ni de #892: mientras no exista, el plazo de una fase finalizadora solo alcanza `EN_PLAZO`/`VENCIDO`, nunca `CUMPLIDO` — mismo patrón ya usado en `TABLON_AYUNTAMIENTOS` para un caso distinto.

Sin suspensión a nivel FASE: el art. 22 suspende el plazo del procedimiento, y decidir si eso debe alargar el plazo de cada acto por separado es alcance de #921, no de esta.

### C — No se toca ninguna fila SOLICITUD existente

Las filas de nivel SOLICITUD que ya cubrían `AAP`, `AAC`, `AAP+AAC`, `AAC+DUP`, `AAP+AAC+DUP`, `DUP` (sola, con su cita corregida en la migración de #892) siguen existiendo sin cambios de comportamiento: siguen alimentando `obtener_estado_plazo_solicitud`, que usan consumidores que no tienen por qué saber que ahora hay plazos de fase — `COMUNICACION_INICIO_ADMISION` es el caso real (`app/services/context_builders/contexto_comunicacion_inicio_admision.py`), y retirar la fila de `DUP` sola le dejaría sin plazo que comunicar al promotor. Las filas de FASE son un mecanismo **aditivo**, con un propósito distinto (el plazo del acto concreto) del que ya tenía el nivel SOLICITUD (el plazo global de la solicitud, art. 21.3.b).

---

## Consecuencias

**Código tocado por #892:**
- `app/services/plazos.py` — `_SEGMENTOS_CAMINO['FASE'] = 3`, `_resolver_campo_fecha` sube a `Fase.solicitud`, nueva `obtener_estado_plazo_fase()`.
- `app/services/variables/plazo.py` — `_resolver_elemento` devuelve `(fase, 'FASE')`, tercera rama en `_estado_plazo`.
- `app/models/catalogo_plazos.py` — `CheckConstraint` admite `FASE`.
- `app/modules/catalogo_plazos/routes.py`, `app/routes/api_catalogo_plazos.py`, plantillas y JS del módulo admin — `FASE` como nivel seleccionable, con validación de `es_finalizadora` en el alta/edición.
- Migración manual con la corrección de cita de `ANY/DUP` y las tres filas nuevas de FASE.

**Deuda que este ADR destapa pero no asume:**
- Cierre propio por fase (equivalente a `Solicitud.documento_cierre_id`, pero por acto) — #921.
- Superficie en UI del plazo de fase (análogo a `plazo_tarea()` en el árbol/inspector) — #922.
- Si el art. 22 debe suspender el plazo de cada acto por separado, o solo el de la solicitud — no decidido, converge con el cierre propio por fase.

---

## Lo que este ADR no decide

Cómo se representa el cierre (notificación) propio de una fase finalizadora. Dos vías evaluadas sin elegir, mismo espíritu que ADR-046 dejó abierto para el doble acto en su momento:

1. Columna `Fase.documento_cierre_id`, paralela a `Solicitud.documento_cierre_id`, con su propio tipo de certificado por fase finalizadora.
2. Reutilizar `Solicitud.documento_cierre_id` con algún mecanismo de desambiguación (rechazado a primera vista: ya hoy es una FK única que no distingue actos, es la raíz del problema, no la solución).

La decisión se toma en #921.

---

## Alternativas descartadas

**No excepcionar #788 y dejar el plazo de fase sin resolver**, documentando el hueco en el catálogo en vez de sembrarlo. Era la primera lectura de #892 antes de repasar ADR-046/047 con Carlos: descartada porque ambos ADR ya habían resuelto la representación del doble acto (fases finalizadoras con `documento_resultado_id` propio) y dejaban el plazo como la única pieza pendiente, explícitamente asignada a #892 — no había ninguna pregunta de modelado real que seguir aplazando.

**Extender `obtener_estado_plazo_solicitud` para devolver una lista de plazos, uno por fase finalizadora, sin tocar `_SEGMENTOS_CAMINO` ni el `CheckConstraint`.** Más fiel a la letra de #788 (el plazo sigue siendo "de la solicitud"), pero cambia el contrato de retorno de una función pública con varios consumidores reales (`EstadoPlazoSolicitud` único hoy) y no resuelve el problema real: identificar QUÉ fila de catálogo corresponde a QUÉ fase finalizadora sigue necesitando el camino de FASE como clave, así que la complejidad no desaparece, se mueve a un lugar peor iluminado.

**Añadir un `tipo_elemento='FASE_FINALIZADORA'` distinto de `'FASE'`** para que el propio valor del constraint documentara la restricción. Descartada por sobre-ingeniería: `tipo_elemento` ya es redundante con la longitud del camino (comentario de la columna, `app/models/catalogo_plazos.py`), y añadir un quinto literal solo para que el constraint diga lo mismo que ya dice el catálogo (sin filas para fases taxonómicas) no compra nada.
