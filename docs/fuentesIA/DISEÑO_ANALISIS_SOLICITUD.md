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
6. [Catálogo de items de requerimiento](#6-catálogo-de-items-de-requerimiento)
7. [Motor de reglas: restricción de tasas](#7-motor-de-reglas-restricción-de-tasas)
8. [Utilidades de redacción: firmantes y siglas](#8-utilidades-de-redacción-firmantes-y-siglas)
9. [Impacto en Estructura_fases_tramites_tareas.json](#9-impacto-en-estructura_fases_tramites_tareasjson)

---

## 1. Contexto y motivación

Las fases `REGISTRO_SOLICITUD`, `ADMISIBILIDAD` y `ANÁLISIS_TÉCNICO` modelaban por separado lo que en la práctica administrativa es un único acto intelectual del técnico: revisar la documentación presentada, comprobar su completitud formal y técnica, y emitir un requerimiento si procede.

La separación en tres fases generaba artificialidad: el técnico analiza todo de golpe (si faltan las escrituras de constitución y además el proyecto tiene deficiencias de cálculo, el requerimiento es uno solo). La única distinción legalmente relevante es la **restricción de tasas**: si las tasas no están correctas o no se presentaron, no pueden iniciarse las fases de información pública ni consultas (Ley de Tasas de la Junta de Andalucía). Esto no exige una fase separada — basta con una regla del motor.

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

El documento producido por ANALIZAR es el resultado formal del análisis: lista de documentos faltantes + defectos de contenido. Este documento es entrada del trámite REQUERIMIENTO_SUBSANACIÓN.

### Trámite: `REQUERIMIENTO_SUBSANACIÓN`

Combina el resultado del ANÁLISIS_DOCUMENTAL en un escrito de requerimiento dirigido al titular.

**Tareas:** `REDACTAR → FIRMAR → NOTIFICAR → ESPERAR_PLAZO → INCORPORAR (multi-doc) → ANALIZAR`

La plantilla del escrito usa el token `{{resultado_analisis_documental}}` (lista de defectos del trámite anterior). Si el análisis no detectó defectos de un tipo, el token produce vacío y la sección no aparece en el documento.

Tras ESPERAR_PLAZO, el titular aporta la documentación subsanada. INCORPORAR registra formalmente la recepción (puede ser N documentos — ver sección 5). ANALIZAR evalúa la subsanación y puede habilitar un nuevo REQUERIMIENTO_SUBSANACIÓN si persisten defectos, o el cierre de la fase si la subsanación es correcta.

> **Sobre el uso del catálogo de items de requerimiento:** el técnico dispone en la tarea ANALIZAR de un selector de items tipo para redactar los defectos detectados (ver sección 6). El resultado del ANALIZAR es el documento que alimenta el REDACTAR posterior.

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

Para cada combinación `(tipo_instalacion, tipo_solicitud)` existe una lista de documentos obligatorios. El técnico contrasta los documentos del pool contra esa lista. La fuente del checklist es un estudio en marcha a nivel andaluz (pendiente de formalizar — probablemente en hoja de cálculo). No se implementa ahora.

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

### Decisión: tabla puente `tarea_documentos`

Se añade una tabla `tarea_documentos (tarea_id, documento_id)` para las tareas de tipo INCORPORAR. Una sola tarea INCORPORAR = un acto formal de recepción → N documentos vinculados.

`documento_producido_id` en `public.tareas` queda **NULL** para tareas INCORPORAR que usen esta tabla. El motor detecta tareas INCORPORAR completadas por `fecha_fin IS NOT NULL`, no por `documento_producido_id`.

**UI:** El técnico abre la tarea INCORPORAR, ve los documentos del pool sin trámite de origen, selecciona en bloque los recibidos como respuesta, y confirma. La tarea queda completada con todos vinculados.

---

## 6. Catálogo de items de requerimiento

### Concepto

Los defectos documentales que se repiten entre expedientes (falta de justificación técnica, tasas incorrectas, ausencia de documentos específicos, etc.) se mantienen en un catálogo. El técnico selecciona los que aplican en lugar de redactarlos desde cero cada vez, garantizando imagen homogénea de la administración.

### Modelo de datos

**Tabla `item_requerimiento`:**

| Campo | Descripción |
|---|---|
| `id` | PK |
| `texto` | Texto del defecto (puede incluir huecos para completar) |
| `categoria` | Categoría: `documental`, `tecnica`, `administrativa`, `tasas` |
| `activo` | Boolean — visible o archivado |

### Dónde se usa

En la tarea **ANALIZAR** de los trámites `ANÁLISIS_DOCUMENTAL` y `REQUERIMIENTO_SUBSANACIÓN` (iteración) — no en REDACTAR. El técnico analiza → selecciona defectos → produce documento de análisis. REDACTAR solo ensambla con plantilla.

### Persistencia de la selección

Los items seleccionados por el técnico (IDs del catálogo + textos libres adicionales) se guardan como **campo JSON en la tarea ANALIZAR** (`public.tareas`). Permite recuperar el estado si el usuario cierra y vuelve. El context builder los lee para generar el documento de análisis con el bucle `{% for item in items_requerimiento %}`.

### UI: selector tipo shuttle

Panel lateral en la tarea ANALIZAR con dos columnas:

- **Izquierda:** catálogo de items, agrupados por categoría, con botón `→` por item
- **Derecha:** lista de items seleccionados, con botón `←` para devolver al catálogo (y editar si se desea)
- **Área de texto libre:** debajo del catálogo, con botón `→` para añadir item no catalogado. El área se vacía tras añadir para permitir redactar el siguiente. Botón `Limpiar` para descartar.
- **Opción "Guardar en catálogo":** al añadir un item libre, checkbox para persistirlo en `item_requerimiento`.

### Token en plantilla

La plantilla del escrito de requerimiento usa un bloque de iteración:

```
{% for item in items_requerimiento %}
   ... {{ item.texto }} ...
{% endfor %}
```

---

## 7. Motor de reglas: restricción de tasas

La Ley de Tasas de la Junta de Andalucía exige que las tasas estén correctamente presentadas y completas antes de iniciar la información pública o las consultas a organismos.

**Regla del motor:** las fases `INFORMACIÓN_PÚBLICA` y `CONSULTAS` tienen como pre-condición que el item del checklist correspondiente a las tasas (`categoria = tasas`) esté marcado como `validado = True` en la tabla `checklist_asociacion` del expediente.

Esta regla no bloquea el análisis de otros defectos ni la emisión del requerimiento — solo bloquea el avance a las fases siguientes.

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
- Actualizar definición de tarea `INCORPORAR`: `documento_producido_id` pasa a ser opcional cuando se usa `tarea_documentos`; añadir nota sobre soporte multi-documento
- Versión: 5.5
