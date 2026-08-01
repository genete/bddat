# ADR-036 — Sellado de fase cerrada: invariante estructural + reapertura como acto propio

**Estado:** Adoptada — pendiente de implementación
**Fecha:** 2026-08-01
**Origen:** #720 (absorbe #716) — detectado al revisar la coherencia del cuadro de salvaguardas de #714 (sesión 2026-07-29)
**Relacionado:** #419/#711 (`_check_cierre_fase`, la puerta de entrada que sí se vigila), #714 (reversión de diagnóstico, mismo criterio de puerta cerrada), #722 (guardia de borrado del árbol, mismo patrón de invariante hardcoded no bypasseable)

---

## Contexto

`Fase.finalizada` ([app/models/fases.py:122](../../app/models/fases.py)) es una property que solo decora (`documento_resultado_id IS NOT NULL`). La consultan `arbol_expediente.py` y `detalle_nodo.py` para pintar el estado del nodo — **ninguna mutación la comprueba**. Verificado sobre datos reales (AT-2004): la fase 8 está cerrada con resultado FAVORABLE, y su diagnóstico 115 —el mismo que `_check_cierre_fase` consultó para permitir ese cierre— sigue siendo reversible sin fricción alguna después de cerrada. La regla vigila la puerta de entrada (#419/#711) y deja abierta la de atrás.

Alcance verificado de lo que hoy es mutable dentro de una fase cerrada: crear trámites/tareas, editar tareas, vincular/desvincular documentos, producir/revertir diagnósticos, registrar notificaciones, borrar trámites/tareas. Trece puntos de entrada distintos en `app/routes/api_expedientes.py`, solo cuatro de los cuales comparten servicio (`app/services/mutaciones_arbol.py`).

No es modelo legal — ninguna norma dice "una fase cerrada no se toca"; es coherencia estructural de la evidencia — así que **no va a `reglas_motor`**: es un invariante hardcoded, mismo criterio que #722.

---

## Decisión

### 1. Reapertura como acto propio (opción B del issue)

No se justifica cada mutación por separado (grano fino, pesado). En su lugar, `reabrir_fase(fase, *, justificacion)` en `mutaciones_arbol.py`:

- Justificación **obligatoria siempre** (no hay camino sin justificar).
- Retira `documento_resultado_id` y `resultado_fase_id` (`NULL`).
- Registra en bitácora (`ALTERAR`, `fases`, con la justificación).
- A partir de ahí se trabaja con normalidad; al volver a cerrar, pasa otra vez por `_check_cierre_fase`.

El propio invariante de mutación (§7) **no admite bypass propio** con justificación en el punto de la mutación — a diferencia de las reglas de motor, aquí el único camino de escape es pasar antes por `reabrir_fase`. Mismo criterio que `_check_borrar` (#722): "tiene fase cerrada" no es una regla de negocio forzable caso a caso, es una precondición de orden.

### 2. Nivel de sellado: solo Fase

`Tramite.finalizado` y `Tarea.ejecutada` son *properties* derivadas del estado de sus documentos vinculados — no tienen un campo de cierre propio (no hay `documento_resultado_id` a su nivel). Sellarlos exigiría añadir un acto de cierre formal nuevo a esos dos modelos: obra mayor, fuera del alcance del bug reportado. El bloqueo de mutación sobre los hijos de una fase cerrada (§7) cubre transitivamente trámites y tareas: no se puede tocar un trámite o una tarea cuya fase está cerrada, sin necesidad de un campo de cierre propio en esos niveles.

### 3. Solicitud: sellado transitivo, sin campo nuevo

`Solicitud.estado` ([app/models/solicitudes.py:139](../../app/models/solicitudes.py)) ya es `RESUELTA*` cuando **todas** las fases de la solicitud están `finalizada` — es derivado, sin columna propia. Sellar consistentemente a nivel Fase sella la Solicitud sin ningún trabajo adicional: cuando se cierra la última fase, la solicitud queda RESUELTA y, por construcción, todo su interior ya está bajo el invariante de §7.

### 4. Puerta cerrada: solicitud ya resuelta y notificada

Si la solicitud está en estado `RESUELTA*` y existe notificación registrada (tarea NOTIFICAR con fila en `notificaciones`) en su fase finalizadora, **ninguna fase de esa solicitud puede reabrirse** — mismo criterio LPACAP que #714/#722: el acto ya salió fuera y es firme; solo modificable, anulable o revocable por un acto administrativo expreso, fuera del alcance de este ADR. `reabrir_fase` comprueba esta condición y la rechaza sin posibilidad de bypass (ni siquiera con justificación) — es puerta cerrada, no un bloqueo forzable.

### 5. Quién puede reabrir

Mismo permiso que crear/borrar nodos del árbol: `gestionar_estructura_expediente` (ADMIN, SUPERVISOR, TRAMITADOR). No se crea un permiso nuevo — coherente con que son los mismos roles que ya cierran la fase (`editar_fase`) y borran hoja a hoja (#722).

### 6. Mecanismo técnico: cuatro capas, ninguna por enumeración de casos individuales

El primer diseño considerado —enganchar un check a mano en los trece puntos de mutación conocidos— se descartó (§Alternativas, A): es el mismo patrón que causó #716 ("el invariante colgado de un efecto colateral, no de un gesto de cierre"). Cualquier mutación nueva que no se acuerde de llamar al check se cuela igual que hoy.

Se adoptan cuatro capas, cada una cubriendo un tipo de olvido distinto:

| Capa | Dónde | Cubre | Protege contra |
|---|---|---|---|
| Resolver de nodo | `_resolver_nodo` en `api_expedientes.py`, condicionado al verbo HTTP (bloquea solo en POST/PUT/PATCH/DELETE) | Las 13 rutas de mutación de hoy — verificado: las 20 llamadas de lectura/escritura sobre nodos en `api_expedientes.py` pasan por aquí, directo o vía sus dos wrappers (`_resolver_tarea_analizar`, `_resolver_tarea_notificar`) — y cualquier ruta HTTP futura, porque sin pasar por aquí no se puede validar pertenencia al expediente | Olvido en un endpoint nuevo |
| Servicio de dominio | `check_invariante` en `invariantes_esftt.py`, nueva acción `MUTAR`, invocado desde `mutaciones_arbol.py` y `diagnosticos.py` (mismo patrón que `check_invariante('BORRAR', ...)` de #722) | Llamadas directas al servicio sin pasar por HTTP | Scripts, consola, tests que reutilizan el servicio |
| Hook de sesión | `before_flush` de SQLAlchemy sobre `Tramite`, `Tarea`, `DocumentoTarea`, `Notificacion` (los cuatro modelos con FK directa o indirecta a `fase`) | Cualquier escritura en esas tablas, sin importar qué código la disparó | **Código futuro que no conoce el invariante** — p. ej. un futuro asignador automático de justificantes de notificación (ecosistema bandeja/notifica) que inserte directo en `documentos_tarea` sin pasar por `editar_tarea` ni por ningún check explícito |
| Interfaz | Plantillas/islas que ya consultan `fase.finalizada` para pintar estado | Que el tramitador vea controles de mutación activos sobre un nodo congelado | Nada estructural — es experiencia, no garantía de integridad |

Las capas 1 y 2 dan mensajes de error específicos y tempranos (evitan un rollback feo). La capa 3 es la única incondicional: no depende de que el código que muta sepa que el invariante existe. Las tres, combinadas, cubren tanto el árbol accedido por HTTP como cualquier automatismo futuro que module `documentos_tarea`/`notificaciones` sin pasar por los servicios existentes.

`pool_subir_documento` (subida de documentos al pool del expediente, `app/modules/expedientes/routes.py`) queda **fuera de alcance**: no vincula a ninguna tarea, no hay fase en juego en el momento de la subida.

### 7. `MUTAR` en `check_invariante`

Nueva acción `check_invariante('MUTAR', sujeto, entidad_id)` en `invariantes_esftt.py`: resuelve la fase ancestro (`FASE` → ella misma; `TRAMITE` → `tramite.fase`; `TAREA` → `tarea.tramite.fase`) y bloquea si `fase.finalizada`, salvo que la mutación en curso sea el propio `editar_fase` de cierre o `reabrir_fase` (que deben poder tocar esos campos sin autobloquearse).

---

## Mapa de impacto (análisis previo a implementar, `REGLAS_DESARROLLO.md`)

| Ruta / función | Qué muta | Capa que lo cubre |
|---|---|---|
| `crear_hijo_nodo` → `crear_tramite`/`crear_tarea` | crea trámite/tarea dentro de la fase | 1 + 2 + 3 |
| `editar_nodo` → `editar_fase` | resultado/documento de cierre de la propia fase (el bug del issue) | 1 + 2 + 3 (con excepción del propio acto de cierre) |
| `editar_nodo` → `editar_tramite`/`editar_tarea` | observaciones, vínculos documentales | 1 + 2 + 3 |
| `borrar_nodo` → `borrar_tramite`/`borrar_tarea` | borra hijos de la fase | 1 + 2 + 3 |
| `post_analizar`/`delete_analizar` → `crear_diagnostico`/`revertir_diagnostico` | diagnóstico (caso concreto AT-2004) | 1 + 2 + 3 |
| `patch_notas_tarea` | `tarea.notas` | 1 + 3 |
| `vincular_requisito_documental`/`desvincular_requisito_documental` | `DocumentoRequisito` (cuelga de `solicitud_id`, sin FK a fase) + re-deriva consumidos vía `DocumentoTarea` | 1 (resuelve `tarea_id` antes de mutar) + 3 (sobre el `DocumentoTarea` derivado) |
| `guardar_cobertura_tecnica` | `CoberturaItemTecnico` (cuelga de `solicitud_id`) | 1 |
| `post_requerimientos`/`crear_requerimiento_catalogo` | `requerimientos` (cuelgan de `solicitud_id`) | 1 |
| `post_notificar`/`patch_notificar` | `Notificacion` | 1 + 3 |
| futuro asignador automático (bandeja/notifica) | `DocumentoTarea`, `Notificacion` directo, sin pasar por HTTP ni servicio | 3 (única capa que lo cubre) |

---

## Issues de implementación

Cuelga de #720 (que absorbe #716). Se desglosará en sub-tareas dentro del propio issue al iniciar la implementación (checklist en el body, `feedback_checklist_body_issue`).

---

## Alternativas descartadas

### A. Check disperso a mano en los 13 puntos de mutación conocidos
Es el diseño inicial considerado. Descartada: mismo patrón que causó #716 — depende de que cada punto (presente y futuro) se acuerde de llamar al check. No ofrece ninguna garantía estructural, solo una lista más larga que mantener sincronizada.

### B. Hook `before_flush` único, con whitelist de modelos, sin capas 1 y 2
Resuelve el olvido de *rutas* nuevas, pero no el olvido de *modelos* nuevos: si mañana aparece una tabla (p. ej. `interesados_expediente`) que también debería sellarse, hay que acordarse de añadirla a la whitelist del hook — mismo defecto trasladado de la ruta al modelo. Se mantiene el hook (capa 3) pero **solo como red de cierre** para los cuatro modelos nucleares del árbol, no como único mecanismo.

### C. Bloqueo solo en interfaz (UI)
Ocultar/deshabilitar controles cuando la fase está cerrada, sin ninguna garantía en backend. Descartada como única defensa: mismo argumento que descarta A y B, aplicado a la capa de presentación — una vista nueva puede olvidarse de consultar `fase.finalizada` igual que un endpoint puede olvidarse del check, y no protege contra llamadas directas a la API ni contra automatismos futuros. Se conserva como capa 4, de experiencia — evita que el tramitador vea el botón —, no como garantía de integridad.

### D. Sellar también Trámite y Tarea con un campo de cierre propio
Añadiría un acto de cierre formal (columna persistida) a dos modelos que hoy derivan su estado por completo de sus documentos vinculados. Descartada por ahora: no existe tal acto en el diseño actual, y el sellado transitivo desde Fase (§2) ya cubre el caso reportado sin tocar esos modelos. Queda como posible extensión futura si aparece una necesidad de negocio concreta que lo exija.
