# ADR-011 — Vinculación trámites↔organismos y evaluación de completitud en fase CONSULTAS

**Estado:** Adoptada
**Fecha:** 2026-05-24
**Issue:** #456

---

## Contexto

El campo `organismos_expediente.tramite_id` vinculaba únicamente al trámite
`CONSULTA_SEPARATA` de cada organismo. Los trámites `CONSULTA_TRASLADO_TITULAR`
y `CONSULTA_TRASLADO_ORGANISMO` no tenían FK directa al registro de organismo,
lo que impedía a los Context Builders de traslado (#457) identificar a qué
organismo pertenecían en expedientes con múltiples organismos.

El campo `num_iteraciones_organismo` era un contador desnormalizado cuya
sincronización dependía de la capa de aplicación.

No existían criterios formales para determinar cuándo una consulta a un organismo
está completamente resuelta ni, por tanto, cuándo puede cerrarse la fase CONSULTAS
de forma favorable.

---

## Decisión

### 1. Nueva tabla `tramites_organismos`

```sql
CREATE TABLE public.tramites_organismos (
    id                       SERIAL PRIMARY KEY,
    tramite_id               INTEGER NOT NULL UNIQUE  REFERENCES public.tramites(id)             ON DELETE CASCADE,
    organismo_expediente_id  INTEGER NOT NULL         REFERENCES public.organismos_expediente(id) ON DELETE CASCADE
);
```

El `UNIQUE` en `tramite_id` garantiza que cada trámite pertenece a un solo
organismo. Un organismo puede tener N trámites (SEPARATA + 0–2 TRASLADOs).

**Se eliminan de `organismos_expediente`:**
- Campo `tramite_id` y su `UNIQUE` `uq_org_exp_tramite`.
- Campo `num_iteraciones_organismo` — derivable como `COUNT` de filas con tipo
  `CONSULTA_TRASLADO_ORGANISMO` en `tramites_organismos`.

### 2. Campo `condicionados_doc_id` en `organismos_expediente`

Se añade `condicionados_doc_id` (FK nullable → `documentos.id`). Solo es no nulo
cuando concurren simultáneamente:

- El organismo respondió con `condicionado` en cualquier punto de la cadena.
- El titular no respondió al TRASLADO_TITULAR (`sin_respuesta`) en un expediente AAC.

En ese caso el tramitador produce manualmente un documento `CONDICIONADO_OFICIO`
con los condicionados pasados a limpio y lo enlaza aquí. El CB de resolución lo
consume directamente desde `organismos_expediente.condicionados_doc_id`.

### 3. Tipo documental `CONDICIONADO_OFICIO`

Nuevo tipo en `tipos_documentos`. Representa el documento producido por el
tramitador cuando el titular no responde al traslado de condicionados en AAC.
Se distingue de `RESPUESTA_TITULAR` porque es generado internamente y el CB de
resolución lo trata con texto específico: "condicionados incorporados de oficio
por falta de respuesta del titular".

### 4. Regla de creación de TRASLADO_TITULAR

`CONSULTA_TRASLADO_TITULAR` se crea **siempre** que el organismo haya dado
cualquier respuesta (resultado ≠ `sin_respuesta`). Motivo: el titular debe
conocer y pronunciarse explícitamente sobre todo lo que obra en el expediente
—incluidos condicionados— antes de la resolución, evitando que esta incluya
condicionados desconocidos para el peticionario y eliminando la necesidad de
traslado separado de la propuesta de resolución.

Cuando el resultado del organismo es `sin_respuesta` (conformidad por silencio,
arts. 127.2, 131.1 y 146.1 RD 1955/2000) no hay nada que trasladar: no se crea
TRASLADO_TITULAR.

Esta regla aplica tanto tras `CONSULTA_SEPARATA` como tras
`CONSULTA_TRASLADO_ORGANISMO`.

### 5. Evaluación de resultado por tipo de trámite

| Trámite | Resultado | Evaluación |
|---|---|---|
| CONSULTA_SEPARATA | `conformidad`, `condicionado`, `sin_respuesta` | OK |
| CONSULTA_SEPARATA | `oposicion`, `reparos_organismo` | NOK |
| CONSULTA_TRASLADO_ORGANISMO | `conformidad`, `condicionado`, `sin_respuesta` | OK |
| CONSULTA_TRASLADO_ORGANISMO | `oposicion`, `reparos_organismo` | NOK |
| CONSULTA_TRASLADO_TITULAR | `conformidad`, `reparos_titular` | OK |
| CONSULTA_TRASLADO_TITULAR | `sin_respuesta` | NOK (ver §6 para casos especiales) |

`sin_respuesta` en trámites de organismo es siempre OK (conformidad tácita, RD
1955/2000). `sin_respuesta` en TRASLADO_TITULAR es siempre NOK: el titular debe
pronunciarse explícitamente.

### 6. Evaluación conjunta de completitud de una consulta

Una consulta (`via = consulta`) está completa y cuenta como favorable cuando se
cumple **uno** de estos casos:

**Caso A — Organismo no respondió:** resultado del trámite de organismo es
`sin_respuesta`. No se crea TRASLADO_TITULAR. La consulta cierra favorable.

**Caso B — Organismo respondió OK (sin NOK previo):** el trámite de organismo
tiene resultado OK ≠ `sin_respuesta` y existe un TRASLADO_TITULAR posterior con
resultado OK (`conformidad` o `reparos_titular`).

**Caso C — Organismo respondió NOK:** existe un trámite de organismo con NOK y,
posteriormente, un trámite de organismo con OK seguido de un TRASLADO_TITULAR con
resultado `conformidad`. El ciclo NOK→OK→TRASLADO_TITULAR está acotado a
**1 iteración**.

**Caso D — Titular sin respuesta ante condicionado (AAC):** el trámite de
organismo tiene resultado `condicionado` y el TRASLADO_TITULAR tiene
`sin_respuesta`. El tramitador produce un `CONDICIONADO_OFICIO` y lo enlaza en
`organismos_expediente.condicionados_doc_id`. La consulta cierra con condicionados
incorporados de oficio.

**Fuera de alcance (#456):** el caso TRASLADO_TITULAR `sin_respuesta` + organismo
NOK (audiencia previa a archivo en AAP) se gestiona en la fase RESOLUCION.

Los organismos con `via = declaracion_responsable` tienen estado `exonerado`
desde el inicio y no participan en esta evaluación.

---

## Razonamiento

**Por qué tabla de vínculo y no FK en `Tramite`.**
Una FK `organismo_expediente_id` en `Tramite` introduciría lógica de negocio
específica de CONSULTAS en un modelo genérico. La tabla de vínculo mantiene
`Tramite` agnóstico y cubre los tres tipos de trámite con el mismo mecanismo.

**Por qué eliminar `num_iteraciones_organismo`.**
Con `tramites_organismos`, el número de iteraciones es derivable por COUNT. Un
contador desnormalizado es deuda técnica inmediata: requiere sincronización
explícita y puede desincronizarse.

**Por qué `condicionados_doc_id` en `organismos_expediente` y no documento suelto.**
El documento está semánticamente ligado al organismo que impuso las condiciones.
Anclarlo en `organismos_expediente` permite al CB de resolución navegarlo
directamente (`organismo → condicionados_doc_id`) sin búsqueda por tipo ni por fase.

**Por qué `CONDICIONADO_OFICIO` y no reusar `RESPUESTA_TITULAR`.**
El CB de resolución genera texto diferente según si el titular respondió
explícitamente o si los condicionados se incorporan de oficio. Con tipos distintos
el CB ramifica por tipo documental sin inspeccionar el protocolo URI ni el contexto
del trámite.

**Por qué TRASLADO_TITULAR obligatorio cuando hay respuesta del organismo.**
Garantiza que el titular conoce y se pronuncia sobre todos los condicionados antes
de la resolución. Elimina la necesidad de un traslado separado de la propuesta de
resolución y previene la inclusión de condicionados desconocidos.

---

## Consecuencias

- `ContextoConsultaSeparata` y los CBs de traslado (#457) navegan al organismo
  vía `TramiteOrganismo.query.filter_by(tramite_id=...)` en lugar de
  `OrganismoExpediente.query.filter_by(tramite_id=...)`.
- La variable del motor `organismo_supera_iteraciones` (#460) se calcula con COUNT
  de filas `CONSULTA_TRASLADO_ORGANISMO` en `tramites_organismos`.
- Tests que usaban `tramite_id` en stubs o INSERTs de `organismos_expediente`
  se actualizan para usar `tramites_organismos`.
- El invariante "un organismo → una SEPARATA" no tiene constraint de BD en la
  tabla de vínculo; se garantiza en la capa de aplicación en la acción
  "Enviar consultas" (#462).
