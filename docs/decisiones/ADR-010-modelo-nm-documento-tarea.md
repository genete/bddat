# ADR-010 — Modelo N:M documento↔tarea: tabla multiusos con rol

**Estado:** Adoptada
**Fecha:** 2026-05-17
**Issue:** #420

---

## Contexto

El modelo `Tarea` vincula documentos mediante dos FK simples en la tabla `tareas`:

- `documento_usado_id` — documento de entrada (1 documento).
- `documento_producido_id` — documento de salida (1 documento, `UNIQUE`).

Todo el ciclo de vida de la tarea se **deduce** de esos dos campos: `Tarea.ejecutada`
⇔ `documento_producido_id` poblado, y de ahí derivan `estado`, `Tramite.finalizado`
y el servicio de seguimiento. No existe ningún campo de estado explícito en `tareas`
— decisión deliberada de ADR-002 (ESFTT sin fechas ni estados materializados).

### El problema

El modelo "1 documento por tarea" no refleja la realidad operativa. Hay casos
reales de **consumo múltiple**:

- NOTIFICAR consume varios documentos en un mismo acto: oficio de información
  pública + anuncio firmado; oficio de traslado de separata + la separata.
- ANALIZAR la documentación de inicio consume N documentos (confrontación del
  checklist documental).

La tabla `documentos_tarea` (N:M `tarea_id + documento_id`) se diseñó en su día
para la tarea INCORPORAR — que recibía N documentos en un acto de recepción. Con
INCORPORAR eliminada (ADR-004), la tabla quedó huérfana, sin consumidor, marcada
"NO USAR". El modelo quedó partido en dos mecanismos incoherentes: FK simple para
casi todo, N:M sin uso para nada.

### Lo que no es un problema

La **producción múltiple no es un caso real**. Cada ELABORAR/ANALIZAR/NOTIFICAR
produce un único documento (escrito, diagnóstico, justificante). El caso del
oficio masivo a varios destinatarios se modela como N trámites independientes
—uno por organismo, p.ej. CONSULTA_SEPARATA describe "envío a un organismo
concreto y gestión de su respuesta"—, cada uno con su tarea y su documento 1:1.
Por tanto el lado producido mantiene cardinalidad 1.

### Issues afectados

Este ADR sustituye el planteamiento de **#380** (decidir destino de
`documentos_tarea`) y de **#376** (generalizar la UI multi-documento), ambos
cerrados por superación. El rediseño se implementa en el issue **#420**.

---

## Decisión

Sustituir las dos FK de `tareas` por una **tabla multiusos N:M** tarea↔documento,
materializada sobre la `documentos_tarea` ya existente (hoy vacía).

Los vínculos `documento_usado_id` presentes en `tareas` son datos de desarrollo
no productivos: **no se migran**, se regeneran al re-ejecutar los seeds. La
migración se limita al esquema y al catálogo (`catalogo_plazos`); la coherencia
de los datos operacionales se restablece por seed/script, no por migración.

### Modelo

- Una sola tabla con un campo `rol` que distingue entrada y salida. No se duplican
  tablas: entrada y salida son el mismo vínculo con rol distinto.
- Cardinalidad: `CONSUMIDO` 0..N por tarea; `PRODUCIDO` 0..1 por tarea.
- La unicidad "un documento tiene un único productor" —hoy garantizada por el
  `UNIQUE` de `tareas.documento_producido_id`— se conserva, mudada a un índice
  parcial único sobre la tabla nueva.
- Las columnas `documento_usado_id` y `documento_producido_id` se eliminan de
  `tareas`, junto con su `UNIQUE` y el índice `idx_tareas_documento_usado`.

### Schema de `documentos_tarea`

```sql
-- Columna nueva
rol VARCHAR(12) NOT NULL CHECK (rol IN ('CONSUMIDO', 'PRODUCIDO'))

-- Sustituye a uq_documentos_tarea
UNIQUE (tarea_id, documento_id, rol)

-- Un documento es producido como máximo por una tarea
CREATE UNIQUE INDEX uq_documento_un_productor
    ON public.documentos_tarea (documento_id) WHERE rol = 'PRODUCIDO';

-- Una tarea produce a lo sumo un documento
CREATE UNIQUE INDEX uq_tarea_un_producido
    ON public.documentos_tarea (tarea_id) WHERE rol = 'PRODUCIDO';
```

Columnas `id`, `tarea_id` (FK `tareas` ON DELETE CASCADE), `documento_id`
(FK `documentos` ON DELETE CASCADE) se mantienen como están.

### Criterio de terminación de tarea

La terminación sigue siendo **derivada**, no un estado materializado: se mantiene
la filosofía de ADR-002. Cambia solo el predicado:

| | Antes | Después |
|---|---|---|
| `Tarea.ejecutada` | `documento_producido_id IS NOT NULL` | existe fila con `rol='PRODUCIDO'` |

No se añade ningún campo de estado a `tareas`. El cierre de la tarea sigue anclado
a la evidencia documental, como exigen ADR-002 y ADR-005.

### Coexistencia con `tramites_tareas_documentos` (#346)

`documentos_tarea` y `tramites_tareas_documentos` son tablas **complementarias y
no se fusionan**:

| Tabla | Naturaleza | Referencia |
|---|---|---|
| `documentos_tarea` | **Operacional** — qué documento concreto consumió/produjo una tarea concreta | instancias (`tareas`, `documentos`) |
| `tramites_tareas_documentos` | **Semántica / catálogo** — qué tipo de documento corresponde a cada posición de cada tipo de trámite (whitelist indicativa, ADR-007) | catálogos (`tipos_tramites`, `tipos_documentos`) |

---

## Razonamiento

**Por qué una sola tabla con rol y no dos tablas separadas.**
Entrada y salida son el mismo hecho —un documento vinculado a una tarea— visto
desde dos lados. Un campo `rol` lo captura sin duplicar estructura ni lógica.

**Por qué se eliminan las FK de `tareas`.**
Mantener FK simples para algunos casos y N:M para otros deja el modelo partido e
incoherente. Una vez que el consumo es N, la salida (cardinalidad 1) también cabe
en la tabla N:M con un constraint de unicidad; unificar es más simple que sostener
dos mecanismos.

**Por qué terminación derivada y no estado explícito (Vía A descartada).**
Añadir un estado de "completada" a `tareas` rompería ADR-002 (ESFTT eliminó
fechas y estados materializados a propósito) y permitiría cerrar una tarea sin
evidencia documental, en contra de ADR-005. La terminación derivada de la
existencia de un documento producido conserva ambos invariantes y reduce el
rediseño a un cambio de predicado homogéneo.

**Por qué `es_principal` queda fuera.**
Un campo `es_principal` solo tendría sentido si una tarea produjera N documentos
con jerarquía principal/adjunto. Como la producción es siempre de un único
documento, el campo sería estructura muerta. Si en el futuro apareciera un caso
real de producción múltiple jerárquica, se reabriría esta decisión.

> **Nota 2026-08-07 (#764) — cláusula de reapertura examinada y cerrada.** El caso
> candidato era `ESPERAR_PLAZO` recibiendo N documentos en un mismo acto (respuesta a
> un requerimiento de subsanación). No exige producción múltiple: lo que llega de fuera
> trae siempre un documento que acredita el hecho y porta su fecha administrativa
> (registro de entrada, justificante de BandeJA, acuse de publicación), y ése es el
> `PRODUCIDO`; los anexos los consume (0..N) el `ANALIZAR` siguiente. La cardinalidad
> `PRODUCIDO` 0..1 y el índice `uq_tarea_un_producido` se mantienen. Ver ADR-004
> (nota del mismo issue) y `ESTRUCTURA_FTT.json` v6.3.

**Por qué reutilizar `documentos_tarea` y no crear tabla nueva.**
La tabla ya existe, está vacía, su nombre es semánticamente correcto y ya tiene
las dos FK con `ON DELETE CASCADE`. La migración solo añade una columna y
constraints; crear una tabla nueva y eliminar la vieja sería trabajo equivalente
sin beneficio.

---

## Consecuencias

- `Tarea` deja de tener relación directa con sus documentos; el acceso pasa por
  la relación N:M. Se exponen accesores de conveniencia (documentos consumidos,
  documento producido) para no romper la legibilidad del código consumidor.
- La regla `NOT_IN` del motor es indiferente al cambio: es un operador genérico
  sobre condiciones, no depende de la cardinalidad del vínculo documento↔tarea.
- Las filas de `catalogo_plazos` cuyo `campo_fecha` referencia
  `documento_usado_id` deben migrarse al nuevo mecanismo de resolución; es un
  punto crítico de la migración (#420).
- Este rediseño es **prerrequisito de #418 y #419**: ambos reescriben los
  invariantes `_check_finalizar_fase`/`_check_finalizar_tramite`, y #419 define
  "consumo" en términos de `documento_usado_id`. Orden de implementación:
  #420 → #418 → #419.
- La UI de tarea pasa de dos selectores de documento único a gestión de listas
  por rol (trabajo absorbido de #376).
