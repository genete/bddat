# Diseño: Fase de Consultas a Organismos y Análisis Técnico

**Fecha:** 20/03/2026
**Estado:** Decisiones tomadas — pendiente implementación y análisis DUP

---

## Índice

1. [Contexto y motivación](#1-contexto-y-motivación)
2. [Modelo de datos: organismos](#2-modelo-de-datos-organismos)
3. [Fase de análisis técnico: requerimientos y subsanaciones](#3-fase-de-análisis-técnico-requerimientos-y-subsanaciones)
4. [Trámites de la fase de consultas](#4-trámites-de-la-fase-de-consultas)
5. [Terminología legal consolidada](#5-terminología-legal-consolidada)
6. [Flujos por tipo de autorización](#6-flujos-por-tipo-de-autorización)
7. [Motor de reglas: cierre de fases](#7-motor-de-reglas-cierre-de-fases)
8. [Pendientes](#8-pendientes)

---

## 1. Contexto y motivación

La fase de consultas a organismos y la fase de análisis técnico presentan un patrón común: **sub-procesos de cardinalidad variable dentro de una fase**, donde cada sub-proceso tiene su propio ciclo de vida y la fase solo cierra cuando todos cierran. Este documento define cómo se modela ese patrón en BDDAT.

Base legal: RD 1955/2000, artículos 127 (AAP) y 131 (AAC). Ambos artículos regulan el procedimiento de consultas a organismos y condicionados técnicos.

---

## 2. Modelo de datos: organismos

### Decisión: una sola tabla `organismos_expediente`

Inicialmente se contempló separar `organismos_afectados` y `organismos_consultados`. Se decide **una sola tabla** porque ambos conceptos representan lo mismo: la relación de un organismo con un expediente concreto. La distinción es un atributo del registro, no una entidad diferente.

**Motivación del campo `via`:** Un cambio legislativo reciente permite que si el titular presenta una declaración responsable acreditando que ya dispone de la autorización del organismo, no se tramita la consulta. Esto introduce una segunda vía de resolución sin trámites.

### Estructura de `organismos_expediente`

| Campo | Descripción |
|---|---|
| `expediente_id` | FK `expedientes.id` |
| `organismo_id` | FK `entidades.id` (donde `rol_consultado = True`) |
| `via` | enum: `consulta` / `declaracion_responsable` |
| `documento_id` | FK `documentos.id` (solo si `via = declaracion_responsable`) |
| `estado` | Estado del ciclo de vida. Actualización manual por tramitador, con puerta abierta al motor de reglas |
| `num_iteraciones_organismo` | Contador de trámites `CONSULTA_TRASLADO_ORGANISMO` creados para este organismo. Permite al motor advertir o bloquear si se supera el límite de 1 iteración del bucle de reparos |

**Sobre `organismo_id`:** la tabla `entidades` centraliza todas las entidades del sistema con roles booleanos. Los organismos consultables tienen `rol_consultado = True`. No existe tabla de organismos separada.

**Sobre `estado`:** se actualiza manualmente por el tramitador al registrar el resultado de la tarea ANALIZAR de cada trámite. El campo está diseñado para que el motor de reglas pueda actualizarlo automáticamente en el futuro sin cambios de modelo.

**Sobre `num_iteraciones_organismo`:** se incrementa cada vez que se crea un trámite `CONSULTA_TRASLADO_ORGANISMO` para este registro. El motor puede leerlo para emitir advertencia (soft) o bloqueo (hard) si supera 1.

### Estados de `organismos_expediente`

`pendiente` → `separata_enviada` → `en_tramitacion` → `cerrado_favorable` / `cerrado_con_condicionados` / `audiencia_previa` / `exonerado`

El estado `exonerado` corresponde a `via = declaracion_responsable` y es terminal desde el inicio.

### Gaps de implementación en `tipos_tramites`

La fase CONSULTAS requiere los siguientes cambios en el catálogo:

| Acción | Código anterior | Código nuevo | Cambio |
|---|---|---|---|
| Redefinir | `SEPARATAS` | `CONSULTA_SEPARATA` | Uno por organismo; sin ANALISIS inicial; añadir INCORPORAR+ANALIZAR al final |
| Eliminar | `RECEPCION_INFORME_ORGANISMO` | — | Absorbido en `CONSULTA_SEPARATA` y `CONSULTA_TRASLADO_ORGANISMO` |
| Crear | — | `CONSULTA_TRASLADO_TITULAR` | Nuevo tipo, no existía |
| Redefinir | `TRASLADO_REPAROS` | `CONSULTA_TRASLADO_ORGANISMO` | Renombrar y cambiar patrón de EC a C+ |

Para `ANALISIS_TECNICO`: añadir tarea `INCORPORAR` al final de `REQUERIMIENTO_MEJORA` (actualmente patrón C, pasa a C+).

---

## 3. Fase de análisis técnico: requerimientos y subsanaciones

### Decisión: sin tabla de requerimientos

No se crea ninguna tabla `requerimientos_expediente`. Los requerimientos y subsanaciones son **trámites ordinarios** de tipos ya existentes (`REQUERIMIENTO_DE_MEJORA` y `COMPROBACION_DOCUMENTAL`). El tramitador gestiona la correspondencia entre ellos mediante numeración y notas en los propios trámites (Requerimiento_1, Subsanación_1…). El sistema no impone ni valida el encadenamiento: esa responsabilidad recae en el tramitador.

No se añade ningún campo FK de trámite-a-trámite por ahora. Si en el futuro se necesita una ligadura formal, se evaluaría una tabla de ligadura genérica entre trámites de la misma fase (no campos específicos en el modelo de trámite).

### Trámites implicados

**`COMPROBACION_DOCUMENTAL`** — Análisis técnico del proyecto o de la documentación presentada. Polivalente: sirve tanto para la primera revisión como para las revisiones posteriores a subsanaciones. Resultado: `OK` / `con_deficiencias`.

**`REQUERIMIENTO_DE_MEJORA`** — Comunicación formal al titular de los defectos detectados y solicitud de subsanación. Cadena de tareas:

```
REDACTAR → FIRMAR → NOTIFICAR → ESPERAR → INCORPORAR
```

La tarea **INCORPORAR** registra la recepción de la documentación subsanada aportada por el titular. El trámite se cierra **manualmente** por el tramitador, con comentario obligatorio, cuando considera el asunto subsanado. El comentario puede referenciar el documento producido por la tarea de análisis del `COMPROBACION_DOCUMENTAL` asociado.

### Casuística de secuencias posibles

El tramitador puede crear cualquier combinación. Ejemplo real:

```
Ra → Sa1 → Rab → Sa2 → Sb
```

Ra = requerimiento por asunto "a"; Sa1 = subsanación parcial de "a"; Rab = nuevo requerimiento por lo que queda de "a" y además por "b"; Sa2 = subsanación de "a"; Sb = subsanación de "b". El sistema no valida esta secuencia; el motor solo verifica las condiciones de cierre de fase.

---

## 4. Trámites de la fase de consultas

### Creación en bloque de separatas

La acción "Enviar consultas" lee todos los `organismos_expediente` con `via = consulta` y genera automáticamente un documento de separata por organismo (desde la misma plantilla) y un trámite `CONSULTA_SEPARATA` por organismo. Es una operación en bloque que respeta el modelo de un trámite por organismo.

### Tres tipos de trámite

| Tipo | Descripción | Plazo legal |
|---|---|---|
| `CONSULTA_SEPARATA` | Envío de separata (anteproyecto o proyecto) al organismo | 30 días (15 si AAP previa y solo AAC sin DUP) |
| `CONSULTA_TRASLADO_TITULAR` | Traslado al titular de la respuesta del organismo | 15 días |
| `CONSULTA_TRASLADO_ORGANISMO` | Traslado al organismo de los reparos del titular | 15 días |

Estos tres tipos son compartidos entre AAP, AAC y AAP+AAC. Las diferencias de nomenclatura legal y de plazos se resuelven por el contexto del expediente.

### Cadena de tareas en los trámites de traslado

Los trámites `CONSULTA_TRASLADO_TITULAR` y `CONSULTA_TRASLADO_ORGANISMO` incluyen la siguiente cadena de tareas:

```
REDACTAR → FIRMAR → NOTIFICAR → ESPERAR → INCORPORAR_RESPUESTA → ANALIZAR
```

La tarea **ANALIZAR** es la productora del documento con significado semántico que determina el resultado del trámite. Ese resultado es el que controla el estado del organismo y el siguiente paso en el flujo. Ver concepto "tarea productora" más abajo.

### Concepto: tarea productora de documento con significado semántico

Una tarea como ANALIZAR no solo produce un documento sino que su resultado (registrado como campo en la tarea) determina cómo termina el trámite padre y, por tanto, si el ciclo del organismo avanza, se cierra o requiere una nueva iteración. El motor de reglas lee ese resultado para cambiar el estado de `organismos_expediente`.

### Resultados por tipo de trámite

| Resultado | SEPARATA | TRASLADO_ORGANISMO | TRASLADO_TITULAR |
|---|:---:|:---:|:---:|
| `sin_respuesta` | ✓ | ✓ | ✓ |
| `conformidad` | ✓ | ✓ | ✓ |
| `oposicion` | ✓ | ✓ | — |
| `reparos_organismo` | ✓ | ✓ | — |
| `condicionado` | ✓ | ✓ | — |
| `reparos_titular` | — | — | ✓ |

**Nota:** el organismo puede responder con `condicionado` tanto tras la SEPARATA como tras un TRASLADO_ORGANISMO. El valor `condicionado` en TRASLADO_ORGANISMO indica que el organismo acepta pero con nuevas condiciones técnicas tras el intercambio de reparos.

---

## 5. Terminología legal consolidada

La terminología del RD 1955/2000 no es uniforme entre AAP (art. 127) y AAC (art. 131). Definiciones operativas adoptadas en BDDAT:

| Término | Quién | Significado operativo |
|---|---|---|
| **Oposición** | Organismo | Rechazo total. Requiere cambios en la instalación. NO de ninguna manera. |
| **Reparos (organismo)** | Organismo | Solicitud de aclaración. "No entiendo lo que me dices, acláralo." No es rechazo. |
| **Condicionado** | Organismo | Acepta la instalación pero establece condiciones técnicas que deben incorporarse a la resolución. |
| **Reparos (titular)** | Titular | Respuesta polivalente. Puede responder tanto a una oposición como a reparos del organismo. |

En AAP (art. 127) el RD usa "oposición" como término genérico. En AAC (art. 131) usa "condicionado técnico". Los diagramas de flujo de BDDAT distinguen los tres conceptos para el organismo porque tienen tratamiento diferente.

### Silencio administrativo según el RD

| Momento | Quién calla | Efecto |
|---|---|---|
| Tras SEPARATA (30 días, 127.2 / 131.1 / 146.1) | Organismo | Conformidad tácita |
| Tras TRASLADO_TITULAR (15 días, 127.3 / 131.3 / 147.1) | Titular | AAC: aceptación tácita de condicionados. AAP/DUP: criterio propio → audiencia previa a archivo |
| Tras TRASLADO_ORGANISMO (15 días, 127.4 / 131.4 / 147.2) | Organismo | Informe favorable tácito |

---

## 6. Flujos por tipo de autorización

Los flujos están documentados en diagramas SVG en `docs/diagramas_flujo/`:
- `AAP_RD1955.svg` — flujo literal del RD para AAP
- `AAP_PROPIO.svg` — flujo con criterio propio (flecos resueltos)
- `AAC_RD1955.svg` — flujo literal del RD para AAC
- `AAC_PROPIO.svg` — flujo con criterio propio
- `AAP+AAC_PROPIO.svg` — flujo unificado

> Los SVGs se generaron desde Miro y se procesaron con `docs/diagramas_flujo/fix_miro_svg.sh` para compatibilidad con Inkscape.

### Puntos indefinidos en el RD y criterio adoptado

| Caso | RD | Criterio adoptado |
|---|---|---|
| Titular no responde a traslado en AAP (127.3) | No lo contempla | Audiencia previa a archivo |
| Organismo mantiene oposición en segunda ronda AAP (127.4) | No lo contempla | Audiencia previa a archivo |
| Titular no responde a traslado de condicionados en AAC (131.3) | No lo contempla | Aceptación tácita de condicionados (incluir en resolución) |
| Organismo insiste tras reparos del titular en AAC | Art. 131.6: la DGPEM puede resolver incorporando condicionados o elevar al Consejo de Ministros | Podemos resolver |

### Limitación del bucle de reparos

El ciclo traslado-titular → reparos → traslado-organismo → nueva respuesta está acotado a **1 iteración**. El diamante de reparos en los diagramas puede recibir entradas tanto del flujo inicial como del flujo de segunda ronda del organismo. La anotación "1 VEZ?" en los diagramas indica que si ya se ha realizado una iteración completa y el organismo vuelve a responder con reparos u oposición, se corta el ciclo.

### AAP+AAC unificado

Cuando el expediente tiene ambas autorizaciones:
- La SEPARATA es **una sola** por organismo (cubre ambas autorizaciones, art. 127.1 y 131.1)
- El plazo inicial es 30 días (127.2 / 131.1)
- Los resultados son polivalentes y la jerarquía es: oposición > reparos > condicionado
- La resolución final debe indicar expresamente los condicionados cuando aplica

### DUP (Declaración de Utilidad Pública) — arts. 143-147

**Estructura de las consultas DUP (arts. 146-147):**

El procedimiento es idéntico en estructura al del art. 127 (AAP):
- Separata simultánea a la información pública → **30 días** → silencio = sin objeción (146.1)
- Si objeciones: traslado al titular → **15 días** → traslado al organismo → **15 días** → silencio = conformidad (147.1-147.2)

La terminología es "objeciones" (no oposición/reparos), pero el flujo y los plazos son equivalentes.

**Artículo 146.2 — regla de exención:**

> Cuando la DUP se solicita conjuntamente con la aprobación de proyecto de ejecución (AAC), el trámite de consultas de la DUP se entiende cumplido si se han seguido los trámites del **art. 127**.

Esto tiene las siguientes consecuencias prácticas según la combinación del expediente:

| Combinación | Consultas necesarias | Impacto en el sistema |
|---|---|---|
| AAP + DUP | Art. 127 (cubre ambas vía 146.2) | Una sola ronda de consultas por organismo |
| AAP + AAC + DUP | Art. 127 (AAP+DUP) + art. 131 (AAC) | Igual que AAP+AAC, sin consultas adicionales |
| AAC + DUP sin AAP previa | Art. 131 (AAC) + art. 146/147 (DUP, porque 146.2 solo exime si se sigue art. 127) | **Dos rondas de consultas independientes por organismo** |
| DUP posterior a AAP ya resuelta | Art. 146/147 autónomo | Ronda de consultas propia, plazos y estructura art. 147 |

**Combinaciones posibles verificadas:**

La AAP es presupuesto legal de la AAC (no puede existir AAC sin AAP previa o simultánea). La DUP requiere proyecto constructivo concreto y medible —no puede solicitarse para algo que puede cambiar—, por lo que siempre va sincronizada con la autorización principal. No hay nunca dos ciclos de consultas independientes.

| Combinación | Consultas |
|---|---|
| AAP + DUP (simultáneas) | Una sola ronda. Art. 127 cubre ambas vía 146.2. |
| AAP + AAC + DUP (simultáneas) | Una sola ronda al unísono para todos los efectos (AAP + AAC + DUP). Una separata, una respuesta del organismo. |
| AAP resuelta → AAC + DUP posteriores | Una sola ronda bajo art. 131 (AAC). DUP cubierta por 146.2 al haberse ejecutado art. 127 en la fase AAP. |

**Implicación de diseño:**

Siempre es una única ronda de consultas por organismo independientemente de cuántas autorizaciones ampare. Los tres tipos de trámite existentes son suficientes para todos los casos.

---

## 7. Motor de reglas: cierre de fases

### Fase de consultas
El motor comprueba el **estado de `organismos_expediente`**, no los trámites individuales:
- La fase de consultas no puede cerrarse si algún `organismo_expediente` no está en estado terminal (`cerrado_favorable`, `cerrado_con_condicionados`, `exonerado`, o `audiencia_previa` resuelta).

### Fase de análisis técnico
El motor comprueba sobre los trámites de la fase:
- Ningún `REQUERIMIENTO_DE_MEJORA` tiene la tarea INCORPORAR sin completar (el titular ha respondido a todos los requerimientos).
- Ninguna `COMPROBACION_DOCUMENTAL` tiene resultado distinto de `OK` (el análisis técnico da el visto bueno).

---

## 8. Pendientes

- **Diagrama de flujo DUP:** La casuística está analizada y documentada en la sección 6. Pendiente crear diagrama visual equivalente a los de AAP/AAC.
- **Renombrar tarea ANALISIS → ANALIZAR:** El JSON `ESTRUCTURA_FTT.json` ya usa ANALIZAR (v5.4). Pendiente migrar en base de datos: `UPDATE public.tipos_tareas SET codigo = 'ANALIZAR' WHERE codigo = 'ANALISIS'` (migración manual) y actualizar todas las referencias al código en el motor de reglas y en el código de la aplicación.
- **Implementación de `organismos_expediente`:** Tabla nueva, migración manual.
- **Redefinición de `REQUERIMIENTO_DE_MEJORA`:** Añadir tarea INCORPORAR al final de la cadena de tareas.
- **Definición de tipos de trámite** `CONSULTA_SEPARATA`, `CONSULTA_TRASLADO_TITULAR`, `CONSULTA_TRASLADO_ORGANISMO` en el catálogo de tipos.
- **Cadena de tareas** dentro de los trámites de traslado (REDACTAR → FIRMAR → NOTIFICAR → ESPERAR → INCORPORAR_RESPUESTA → ANALIZAR).
- **Acción en bloque** de creación de separatas desde `organismos_expediente`.
- ~~**Mover los diagramas PNG** de `docs_prueba/mockups/` a una ubicación permanente dentro de `docs/`.~~ **HECHO** — SVGs en `docs/diagramas_flujo/`.
