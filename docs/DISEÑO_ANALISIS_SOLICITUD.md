# Diseño: Fase ANÁLISIS_SOLICITUD y utilidades de redacción

**Fecha:** 21/03/2026
**Estado:** Decisiones tomadas — pendiente implementación

---

## Índice

1. [Contexto y motivación](#1-contexto-y-motivación)
2. [Fusión de fases: nueva fase ANÁLISIS_SOLICITUD](#2-fusión-de-fases-nueva-fase-análisis_solicitud)
3. [Trámites y tareas de ANÁLISIS_SOLICITUD](#3-trámites-y-tareas-de-análisis_solicitud)
4. [Checklist documental](#4-checklist-documental)
5. [INCORPORAR multi-documento](#5-incorporar-multi-documento)
6. [Catálogo de requerimientos y selector de defectos](#6-catálogo-de-requerimientos-y-selector-de-defectos)
7. [Motor de reglas: restricción de tasas](#7-motor-de-reglas-restricción-de-tasas)
8. [Utilidades de redacción: firmantes y siglas](#8-utilidades-de-redacción-firmantes-y-siglas)
9. [Impacto en Estructura_fases_tramites_tareas.json](#9-impacto-en-estructura_fases_tramites_tareasjson)

---

## 1. Contexto y motivación

Las fases `REGISTRO_SOLICITUD`, `ADMISIBILIDAD` y `ANÁLISIS_TÉCNICO` modelaban por separado lo que en la práctica administrativa es un único acto intelectual del técnico: revisar la documentación presentada, comprobar su completitud formal y técnica, y emitir un requerimiento si procede.

La separación en tres fases generaba artificialidad: el técnico analiza todo de golpe (si faltan las escrituras de constitución y además el proyecto tiene deficiencias de cálculo, el requerimiento es uno solo). La única distinción legalmente relevante es la **restricción de tasas**: el art. 45.1 de la Ley 10/2021, de 28 de diciembre, de tasas y precios públicos de la Comunidad Autónoma de Andalucía establece literalmente que ninguna actuación administrativa «se realizará o tramitará sin que se haya efectuado el pago correspondiente». En la práctica, por economía procesal, se completa el análisis documental antes de detener la tramitación, pero la restricción afecta a **cualquier fase posterior**. Esto no exige una fase separada — basta con una regla del motor.

**Decisión:** fusionar las tres fases en una sola: `ANÁLISIS_SOLICITUD`.

---

## 2. Fusión de fases: nueva fase ANÁLISIS_SOLICITUD

### Fases eliminadas

| Fase eliminada | Absorbida en |
|---|---|
| `REGISTRO_SOLICITUD` | `ANÁLISIS_SOLICITUD` |
| `ADMISIBILIDAD` | `ANÁLISIS_SOLICITUD` |
| `ANÁLISIS_TÉCNICO` | `ANÁLISIS_SOLICITUD` |

### Fase nueva

**`ANÁLISIS_SOLICITUD`** — Verificación de documentación (existencia y contenido), análisis de admisibilidad y análisis técnico en un único acto. Produce un requerimiento de subsanación si existen defectos, o una comunicación de inicio si la solicitud es completa.

---

## 3. Trámites y tareas de ANÁLISIS_SOLICITUD

### Trámite: `ANÁLISIS_DOCUMENTAL`

El técnico abre el pool del expediente, asigna el tipo correcto a cada documento (inicialmente clasificados como `OTROS` por el administrativo), contrasta contra el checklist de documentación requerida (ver sección 4), y emite un documento con el resultado del análisis (lista de documentos presentes/faltantes y evaluación de contenido).

**Tareas:** `ANALIZAR`

> No precede INCORPORAR. Los documentos ya están en el pool (cargados por el administrativo antes de la asignación al técnico). La cualificación de tipos y el análisis checklist es trabajo intelectual del técnico → es ANALIZAR directamente, igual que en RECEPCION_SOLICITUD (v5.3).

El documento producido por ANALIZAR es el resultado formal del análisis. Su contenido (con o sin defectos) determina el camino que habilita el motor:

- **Con defectos** → el motor habilita `REQUERIMIENTO_SUBSANACIÓN` y bloquea `COMUNICACIÓN_INICIO`.
- **Sin defectos** → el motor habilita `COMUNICACIÓN_INICIO` y bloquea `REQUERIMIENTO_SUBSANACIÓN`.

Los dos trámites son mutuamente excluyentes: no tiene sentido comunicar el inicio de un procedimiento con defectos pendientes, ni emitir un requerimiento cuando no hay nada que subsanar.

> **A ESTUDIAR — tabla `documentos_analizar`:** para que el motor pueda leer el resultado del ANALIZAR (con/sin defectos) se necesita un mecanismo estructurado, análogo a `documentos_proyecto`. Una tabla `documentos_analizar` extendería el documento producido con al menos un campo `tiene_defectos` (boolean), que sería el semáforo que el motor consulta. Pendiente de diseño propio.

### Trámite: `REQUERIMIENTO_SUBSANACIÓN`

Combina el resultado del ANÁLISIS_DOCUMENTAL en un escrito de requerimiento dirigido al titular.

**Tareas:** `REDACTAR → FIRMAR → NOTIFICAR → ESPERAR_PLAZO → INCORPORAR (multi-doc) → ANALIZAR`

La plantilla del escrito usa el token `{{ resultado_analisis_documental }}` (resultado del trámite anterior, inyectado por el context builder). Si en ese resultado no hay defectos de un tipo concreto, el bloque correspondiente queda vacío en el documento.

Tras ESPERAR_PLAZO, el titular aporta la documentación subsanada. INCORPORAR registra formalmente la recepción (puede ser N documentos — ver sección 5). ANALIZAR evalúa la subsanación: si persisten defectos, el motor puede habilitar un nuevo `REQUERIMIENTO_SUBSANACIÓN`; si la subsanación es correcta, habilita el cierre de la fase.

> El técnico dispone en la tarea ANALIZAR del selector de requerimientos tipo (ver sección 6) para redactar los defectos detectados. El documento producido por ANALIZAR es el que alimenta el REDACTAR posterior.

### Trámite: `COMUNICACIÓN_INICIO`

Si no hay defectos, se comunica al titular el número de expediente e inicio del procedimiento.

**Tareas:** `REDACTAR → FIRMAR → NOTIFICAR`

Opcional según política organizativa.

### Resumen

| Trámite | Patrón | Tareas |
|---|---|---|
| `ANÁLISIS_DOCUMENTAL` | A | ANALIZAR |
| `REQUERIMIENTO_SUBSANACIÓN` | C+ | REDACTAR → FIRMAR → NOTIFICAR → ESPERAR_PLAZO → INCORPORAR → ANALIZAR |
| `COMUNICACIÓN_INICIO` | B | REDACTAR → FIRMAR → NOTIFICAR |

---

## 4. Checklist documental

### Concepto

Para cada combinación `(tipo_instalacion, tipo_solicitud)` existe una lista de documentos obligatorios. El técnico contrasta los documentos del pool contra esa lista. La fuente del checklist es un estudio en marcha a nivel andaluz (pendiente de formalizar — probablemente en hoja de cálculo). **No se implementa ahora — puede hacerse de forma independiente incluso en una fase post-producción del sistema, sin afectar al resto del diseño.**

### Modelo de datos (cuando esté listo el estudio)

Tabla `requisito_documental`:

| Campo | Descripción |
|---|---|
| `tipo_instalacion` | Tipo de instalación (renovable, distribución, etc.) |
| `tipo_solicitud` | Tipo de solicitud |
| `tipo_documento_id` | FK `tipos_documentos.id` — tipo de documento requerido |
| `obligatorio` | Boolean — si es requisito imprescindible o recomendado |

### Asociación manual técnico → checklist

El técnico no delega en el sistema la verificación. Para cada item del checklist, arrastra desde el pool el documento concreto que cumple el requisito, estableciendo una asociación `(item_checklist, documento_id)`.

El sistema valida que el tipo del documento arrastrado coincide con el tipo esperado por el item, pero emite solo un **aviso no bloqueante** — la decisión jurídica la toma el técnico. Un documento puede estar bien clasificado como tipo X pero no cumplir el requisito legal (p.ej. tasas incompletas).

Esta asociación se almacena en una tabla `checklist_asociacion`:

| Campo | Descripción |
|---|---|
| `tramite_id` | FK `tramites.id` (el ANÁLISIS_DOCUMENTAL del expediente) |
| `requisito_id` | FK `requisito_documental.id` |
| `documento_id` | FK `documentos.id` (documento del pool que cumple el requisito) |
| `validado` | Boolean — el técnico confirma que cumple el requisito |

---

## 5. INCORPORAR multi-documento

### Problema

La tarea INCORPORAR tiene `documento_producido_id` (FK simple). En la respuesta a un requerimiento de subsanación el titular puede aportar N documentos simultáneamente. Crear una tarea INCORPORAR por documento es trabajo ímprobo e innatural.

### Decisión: tabla puente `documentos_tarea` y deprecación de `documento_producido_id`

Se añade una tabla `documentos_tarea (tarea_id, documento_id)` para las tareas INCORPORAR. Una sola tarea INCORPORAR = un acto formal de recepción → N documentos vinculados. Aunque solo llegue un documento, se usa igualmente esta tabla — no existe mecanismo dual.

`documento_producido_id` en `public.tareas` queda **deprecado para tareas INCORPORAR**. Esto simplifica el motor (un solo sitio donde buscar) y elimina el riesgo de duplicidad entre ambos mecanismos. Los registros existentes con `documento_producido_id` en tareas INCORPORAR se migran a `documentos_tarea`.

**Validación:** una tarea INCORPORAR no puede completarse (`fecha_fin`) si no existe al menos un registro en `documentos_tarea` para esa tarea. Esta validación se aplica tanto en la UI como en el motor.

**UI:** El técnico abre la tarea INCORPORAR, ve los documentos del pool sin trámite de origen, selecciona en bloque los recibidos como respuesta, y confirma. La tarea queda completada con todos vinculados.

---

## 6. Catálogo de requerimientos y selector de defectos

### Concepto

Los defectos que se repiten entre expedientes (falta de justificación técnica, tasas incorrectas, ausencia de documentos específicos, etc.) se mantienen en un catálogo. El técnico selecciona los que aplican en lugar de redactarlos desde cero cada vez, garantizando imagen homogénea de la administración.

### Modelo de datos

**Tabla `catalogo_requerimientos`:**

| Campo | Descripción |
|---|---|
| `id` | PK |
| `texto` | Texto del defecto (puede incluir huecos para completar) |
| `categoria` | Categoría: `documental`, `tecnica`, `administrativa`, `tasas` |
| `activo` | Boolean — visible o archivado |

**Tabla `requerimientos_tarea`** (enriquecimiento de la tarea ANALIZAR, sin campos nullables en la tabla base):

| Campo | Descripción |
|---|---|
| `tarea_id` | FK `tareas.id` |
| `catalogo_requerimientos_id` | FK `catalogo_requerimientos.id` — nullable si es texto libre |
| `texto_libre` | Texto manual — nullable si proviene del catálogo |
| `orden` | Entero — posición en el listado final |

Exactamente uno de los dos campos de contenido (`catalogo_requerimientos_id` o `texto_libre`) tiene valor; el otro es NULL.

### Dónde se usa

En la tarea **ANALIZAR** de los trámites `ANÁLISIS_DOCUMENTAL` y `REQUERIMIENTO_SUBSANACIÓN` (iteración) — no en REDACTAR. El técnico analiza → selecciona defectos → produce documento de análisis. REDACTAR solo ensambla con plantilla.

### Context builder y plantilla

El context builder de este tipo de escrito consulta `requerimientos_tarea` para la tarea ANALIZAR y construye la lista Python `requerimientos` que entrega al renderizador de plantillas. La plantilla itera esa lista con un bloque Jinja2:

```
{% for r in requerimientos %}
   ... {{ r.texto }} ...
{% endfor %}
```

> Ver `docs/GUIA_CONTEXT_BUILDERS.md` para el rol del context builder y su relación con el renderizador.

### UI: selector tipo shuttle

Panel lateral en la tarea ANALIZAR con dos columnas:

**Columna izquierda — Catálogo:**
- Items de `catalogo_requerimientos` agrupados por categoría, filtrable
- Botón `→` por item para pasarlo a la columna derecha
- Área de texto libre al pie con botón `→` para añadir un requerimiento no catalogado; el área se vacía tras añadir (listo para el siguiente). Botón `Limpiar` para descartar sin añadir
- Opción "Guardar en catálogo" (checkbox): al añadir un texto libre, si está marcado, el texto se persiste en `catalogo_requerimientos`

**Columna derecha — Seleccionados:**
- Lista de requerimientos que se incluirán en el documento, en el orden que se insertarán
- Items del catálogo: botón `←` para devolverlos al catálogo (desaparecen de la derecha)
- Items de texto libre: botón `←` para devolverlo al área de texto libre (desaparece de la derecha y el texto vuelve al campo para editar); alternativamente, edición inline con icono lápiz que convierte el texto en textarea editable en su sitio
- Ordenamiento por drag-and-drop (handler visual con puntos/rayas) o con botones ↑ / ↓ al seleccionar un item
- Todos los botones son inteligentes: `↑` deshabilitado si el item es el primero, `↓` si es el último, `←` siempre activo si hay item seleccionado

---

## 7. Motor de reglas: restricción de tasas

El art. 45.1 de la Ley 10/2021, de 28 de diciembre, de tasas y precios públicos de la Comunidad Autónoma de Andalucía establece que ninguna actuación administrativa «se realizará o tramitará sin que se haya efectuado el pago correspondiente». En la práctica, por economía procesal, el análisis se completa antes de detener la tramitación (la tasa es siempre subsanable y conviene agotar el análisis en la primera iteración).

**Regla del motor:** cualquier fase posterior a `ANÁLISIS_SOLICITUD` tiene como pre-condición que el item del checklist correspondiente a las tasas (`categoria = tasas`) esté marcado como `validado = True` en la tabla `checklist_asociacion` del expediente.

Esta regla no bloquea el análisis de otros defectos ni la emisión del requerimiento — solo bloquea el avance a fases posteriores.

---

## 8. Utilidades de redacción: firmantes y siglas

### Firmantes

**Decisión: no crear tabla de firmantes.** La tendencia es firma incrustada (no identificación nominal en el texto). El bloque de cierre del escrito se gestiona como fragmento `.docx` por tipo de plantilla, usando el mecanismo ya existente (`{{r NombreFragmento}}`). El supervisor mantiene los fragmentos sin necesidad de BD.

### Siglas de escritos

Se añade el campo `siglas_escritos` en el modelo `Usuario`. Su valor es las siglas históricas en orden directo (p.ej. `CLG` para López González, Carlos). Es distinto del campo de login (que usará el identificador de la Junta, p.ej. `LGC005`). Se usa como token en las plantillas de escritos.

---

## 9. Impacto en Estructura_fases_tramites_tareas.json

- Eliminar fases: `REGISTRO_SOLICITUD`, `ADMISIBILIDAD`, `ANÁLISIS_TÉCNICO`
- Añadir fase: `ANÁLISIS_SOLICITUD` con trámites `ANÁLISIS_DOCUMENTAL`, `REQUERIMIENTO_SUBSANACIÓN`, `COMUNICACIÓN_INICIO`
- Actualizar definición de tarea `INCORPORAR`: `documento_producido_id` deprecado; los documentos se vinculan mediante `documentos_tarea`; fecha_fin requiere al menos un registro en `documentos_tarea`
- Versión: 5.5
