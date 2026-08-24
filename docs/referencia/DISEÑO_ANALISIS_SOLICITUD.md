# Diseño: Fase ANÁLISIS_SOLICITUD y utilidades de redacción

**Fecha:** 21/03/2026
**Estado:** Implementado — decisiones originales llevadas a código; ver anotaciones "Implementado en #XXX" por sección (última revisión de vigencia: 24/08/2026)

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
9. [Impacto en ESTRUCTURA_FTT.json](#9-impacto-en-estructura_fases_tramites_tareasjson)

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

> **Resuelto en #442** (nota original de marzo/2026, ya no "a estudiar"): el mecanismo estructurado es el modelo `Diagnostico` (`app/models/diagnosticos.py`) — un registro por documento de tipo `DIAGNOSTICO` con `resultado` (favorable/condicionado/desfavorable) y `diagnostico_tiene_defectos` derivado, el semáforo que consulta el motor. No hizo falta la tabla `documentos_analizar` que aquí se anticipaba.

### Trámite: `REQUERIMIENTO_SUBSANACIÓN`

Combina el resultado del ANÁLISIS_DOCUMENTAL en un escrito de requerimiento dirigido al titular.

**Tareas:** `ELABORAR → NOTIFICAR → ESPERAR_PLAZO → ANALIZAR`

La plantilla del escrito usa el token `{{ resultado_analisis_documental }}` (resultado del trámite anterior, inyectado por el context builder). Si en ese resultado no hay defectos de un tipo concreto, el bloque correspondiente queda vacío en el documento.

Tras ESPERAR_PLAZO, el titular aporta la documentación subsanada. El documento recibido se vincula con rol PRODUCIDO a la tarea `ESPERAR_PLAZO` (ADR-004, ADR-010). ANALIZAR evalúa la subsanación: si persisten defectos, el motor puede habilitar un nuevo `REQUERIMIENTO_SUBSANACIÓN`; si la subsanación es correcta, habilita el cierre de la fase.

> El técnico dispone en la tarea ANALIZAR del selector de requerimientos tipo (ver sección 6) para redactar los defectos detectados. El documento producido por ANALIZAR es el que alimenta el ELABORAR posterior.

### Trámite: `COMUNICACIÓN_INICIO_ADMISION` (renombrado en #776)

Si no hay defectos, se comunica al titular el inicio y la admisión a trámite de la solicitud.

**Tareas:** `ELABORAR → NOTIFICAR`

**No es opcional** (esta sección lo anotaba así por error, corregido en #776): el art. 21.4 LPACAP exige informar al interesado, dentro de los 10 días siguientes a la recepción de la solicitud, del plazo máximo de resolución y del sentido del silencio administrativo. Lo opcional es el soporte (puede integrarse en otro acto dirigido al interesado), no la información en sí — y en un procedimiento iniciado a solicitud del interesado no hay acuerdo de iniciación de oficio en el que incorporarla, así que esta comunicación es la vía natural.

Para instalaciones renovables con permiso de acceso posterior al 27/12/2013, este escrito cumple además un segundo propósito: acredita el **Hito 1** del RD-ley 23/2020 (art. 1.2 in fine) ante el gestor de la red — su ausencia conlleva caducidad automática del permiso de acceso y ejecución de garantías del promotor (§7 bis).

**Implementado en #776** (Context Builder, plantilla, tipo de documento `OFICIO_INICIO_ADMISION`).

### Resumen

| Trámite | Patrón | Tareas |
|---|---|---|
| `ANÁLISIS_DOCUMENTAL` | A | ANALIZAR |
| `REQUERIMIENTO_SUBSANACIÓN` | C+A | ELABORAR → NOTIFICAR → ESPERAR_PLAZO → ANALIZAR |
| `COMUNICACIÓN_INICIO_ADMISION` | B | ELABORAR → NOTIFICAR |

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

### Estado real (nota 2026-07-03)

La implementación de #192 (2026-05-27, posterior tanto a esta sección como a la redacción original del propio #192) generalizó el modelo aquí previsto: en vez de columnas fijas `tipo_instalacion`/`tipo_solicitud`, la tabla real `requisitos_documentales` admite condiciones sobre cualquier variable del motor (`condiciones_requisito` → `catalogo_variables`, mismo patrón que `condiciones_regla`) — permite encuadrar por tensión, tipo de suelo o cualquier combinación normativa. La tabla `checklist_asociacion` de esta sección no se construyó; su lugar lo ocupa `documentos_requisito`, con clave por **solicitud** (no por trámite), lo que permite reutilizar una misma cobertura entre vueltas de subsanación. Esta sección no se actualizó en su momento — la mejora surgió al implementar, no estaba prevista aquí ni en la redacción original de #192.

UI pendiente: #495. Población de contenido: #408. Checklist gemelo de contenido técnico del proyecto (RD 223/2008, RD 337/2014 — ítems dentro del proyecto, no presencia de documento): #581.

---

## 5. Recepción externa vía ESPERAR_PLAZO (ADR-004)

### Contexto

Con la eliminación de INCORPORAR (ADR-004, #361), la recepción de un documento externo durante tramitación activa se modela como documento producido (vínculo PRODUCIDO en `documentos_tarea`) de la tarea `ESPERAR_PLAZO` que modelaba la espera. `ANALIZAR` consume ese documento directamente.

En `REQUERIMIENTO_SUBSANACIÓN`, el documento de subsanación del titular se vincula con rol PRODUCIDO al `ESPERAR_PLAZO` correspondiente.

### N documentos simultáneos: regla de recepción (#764, 2026-08-07)

El vínculo `PRODUCIDO` de `ESPERAR_PLAZO` es de cardinalidad 1 (`uq_tarea_un_producido`, ADR-010) y se reserva al documento que **acredita el hecho y porta su fecha administrativa**: el registro de entrada o la solicitud si viene de fuera de la Junta (presentación electrónica de la Junta o red estatal), el justificante de BandeJA si el remitente es una unidad interna, o el acuse/certificado acreditativo cuando lo esperado es una publicación.

Cuando el titular aporta N documentos como respuesta a un requerimiento, esos anexos **no se vinculan al `ESPERAR_PLAZO`**: entran al pool y los consume (0..N) el `ANALIZAR` siguiente del trámite, que es donde se incorporan al expediente. Con un solo documento vinculado queda reflejado administrativamente el acto de recepción completo, y ningún consumidor del producido (cómputo de plazos, cierre de suspensión del art. 22 LPACAP, context builders) necesita más de uno.

No hay, por tanto, cambio de modelo pendiente. La condición que sí debe verificarse en cada fase es estructural: **todo `ESPERAR_PLAZO` que pueda recibir documentación de terceros exige un `ANALIZAR` posterior** —propio, del trámite receptor hermano, o añadido tras él si es el último trámite de la fase—. Esta exigencia se comprueba durante el desarrollo mediante repaso de fase a fase, sin crear issues a futuro, sino sobre la marcha.

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

**Tabla `requerimientos_tarea`** (defectos libres de la solicitud, sin campos nullables en la tabla base; #679, ADR-033 §7):

| Campo | Descripción |
|---|---|
| `solicitud_id` | FK `solicitudes.id` — estado continuo entre vueltas de subsanación, no se reinicia por tarea |
| `catalogo_requerimientos_id` | FK `catalogo_requerimientos.id` — nullable si es texto libre |
| `texto_libre` | Texto manual — nullable si proviene del catálogo |
| `orden` | Entero — posición en el listado final |
| `resuelto` | Boolean — marca manual del técnico. Un requerimiento libre no tiene contra qué casar automáticamente (a diferencia de documental/técnico), su cierre es un juicio |

Exactamente uno de los dos campos de contenido (`catalogo_requerimientos_id` o `texto_libre`) tiene valor; el otro es NULL. La clave es por `solicitud_id` (mismo criterio que `documentos_requisito` y `coberturas_item_tecnico`), no por tarea: el segundo ANALIZAR de una vuelta de subsanación arranca con el estado acumulado.

### Dónde se usa

En la tarea **ANALIZAR** de los trámites `ANÁLISIS_DOCUMENTAL` y `REQUERIMIENTO_SUBSANACIÓN` (iteración) — no en ELABORAR. El técnico analiza → selecciona defectos → produce documento de análisis. ELABORAR ensambla el resultado con la plantilla y lo firma en acto único.

### Context builder y plantilla

El context builder de este tipo de escrito (`ContextoSubsanacion`) no lee `requerimientos_tarea` directamente — esa tabla es el borrador de trabajo vivo del shuttle, no el documento de salida (#406). Lee los defectos ya consolidados y congelados en el `Diagnostico` producido por el ANALIZAR anterior, y los separa por origen (#679, ADR-033 §7) en tres listas Python que entrega al renderizador de plantillas: `defectos_documentales`, `defectos_tecnicos`, `defectos_libres`. La plantilla itera cada una con un bloque Jinja2:

```
{%p for d in defectos_documentales %}
   ... {{ d }} ...
{%p endfor %}
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

**Regla del motor:** cualquier fase posterior a `ANÁLISIS_SOLICITUD` tiene como pre-condición que el requisito del checklist correspondiente a las tasas (`categoria = tasas`) esté cubierto en `documentos_requisito` (tabla real — ver §4; esta sección preveía `checklist_asociacion`, que no se construyó) para la solicitud.

Esta regla no bloquea el análisis de otros defectos ni la emisión del requerimiento — solo bloquea el avance a fases posteriores.

**Estado real (nota 2026-07-03):** a diferencia de otros bloqueos entre fases —p.ej. una consulta a organismo sin separata presentada, que simplemente no tiene documento que consumir en su ELABORAR, sin necesitar regla de motor— la tasa es la única condición que debe bloquear *toda* fase posterior sin excepción incluso si todo lo demás está completo, porque así lo exige la ley con independencia del resto del expediente. Por eso sí necesita una `ReglaMotor` explícita, y no basta con la imposibilidad natural de la tarea.

**Implementado en #582** (migración `07948f0f5f2c_582_regla_tasa_impagada`): una única regla `BLOQUEAR CREAR ANY/ANY/ANY` (sujeto de 3 segmentos → solo casa con creación de fase) con dos condiciones en AND: `tipo_sujeto_solicitado NEQ 'ANALISIS_SOLICITUD'` (variable genérica #388, evita enumerar las 7 fases posteriores una a una — cualquier fase nueva del catálogo queda cubierta automáticamente) y `tasa_impagada EQ true` (variable nueva en `app/services/variables/calculado.py`). La variable identifica el requisito de la tasa por `TipoDocumento.codigo='JUSTIFICANTE_PAGO_TASA'` — contrato que debe respetar #408 al poblar el catálogo; mientras esa fila no exista, la variable degrada a `False` (no bloquea) y loguea warning, mismo criterio que `evaluar_requisitos` (#347).

---

## 7 bis. Motor de reglas: permiso de acceso y conexión (AAP renovables)

El RD-ley 23/2020 (art. 1) establece que, para instalaciones de generación renovable, el permiso de acceso y conexión a la red no es un requisito documental subsanable más: es **condición de admisión a trámite** de la AAP (`NORMATIVA_MAPA_PROCEDIMENTAL.md §2.7`, punto 1). A diferencia de la tasa (§7), este permiso lo otorga un tercero (el gestor de la red), no depende de una gestión interna del promotor.

**Regla del motor:** cualquier fase posterior a `ANALISIS_SOLICITUD` de una AAP de instalación renovable tiene como pre-condición que el requisito del checklist correspondiente al permiso de acceso y conexión (`TipoDocumento.codigo='PERMISO_ACCESO_CONEXION'`) esté cubierto en `documentos_requisito` para la solicitud.

**Implementado en #780** (migraciones `93b1032b3b08_780_seed_permiso_acceso_conexion` y `0fa314d1c76e_780_regla_motor_permiso_acceso`): una única regla `BLOQUEAR CREAR Renovable/AAP/ANY` — a diferencia de la regla de la tasa (sujeto `ANY/ANY/ANY` con condición de encuadre añadida), aquí el propio sujeto ya acota por tipo de expediente (`Renovable`) y tipo de solicitud (`AAP`, siglas), sin necesitar una variable de encuadre nueva como `es_renovable_rdl23` (pendiente de implementar a propósito — ver `DISEÑO_CONTEXT_ASSEMBLER.md`). Dos condiciones en AND: `tipo_sujeto_solicitado NEQ 'ANALISIS_SOLICITUD'` (mismo uso que #582) y `tiene_punto_acceso_conexion EQ false` (variable nueva en `calculado.py`, polaridad positiva — a diferencia de `tasa_impagada`, degrada a `True`/no-bloquea si el catálogo aún no está poblado, porque lo contrario bloquearía todo expediente renovable antes de sembrar el requisito).

**Alcance deliberadamente acotado:** no se condiciona por fecha de obtención del permiso (`>27/12/2013`, ámbito literal del RD-ley 23/2020) — implicaría capturar `fecha_permiso_acceso`, dato sin captura hoy en BDDAT. El caso residual de permisos anteriores a esa fecha queda cubierto por el bypass genérico con justificación de toda regla `BLOQUEAR` del motor, sin diseño adicional.

---

## 8. Utilidades de redacción: firmantes y siglas

### Firmantes

**Decisión: no crear tabla de firmantes.** La tendencia es firma incrustada (no identificación nominal en el texto). El bloque de cierre del escrito se gestiona como fragmento `.docx` por tipo de plantilla, usando el mecanismo ya existente (`{{r NombreFragmento}}`). El supervisor mantiene los fragmentos sin necesidad de BD.

### Siglas de escritos

Se añade el campo `siglas_escritos` en el modelo `Usuario`. Su valor es las siglas históricas en orden directo (p.ej. `CLG` para López González, Carlos). Es distinto del campo de login (que usará el identificador de la Junta, p.ej. `LGC005`). Se usa como token en las plantillas de escritos.

---

## 9. Impacto en ESTRUCTURA_FTT.json

- Eliminar fases: `REGISTRO_SOLICITUD`, `ADMISIBILIDAD`, `ANÁLISIS_TÉCNICO`
- Añadir fase: `ANÁLISIS_SOLICITUD` con trámites `ANÁLISIS_DOCUMENTAL`, `REQUERIMIENTO_SUBSANACIÓN`, `COMUNICACIÓN_INICIO_ADMISION` (renombrado en #776, ver §3)
- Eliminar `INCORPORAR` del catálogo de tareas; recepción externa pasa a `ESPERAR_PLAZO` como documento producido (ADR-004)
- Reemplazar `REDACTAR`+`FIRMAR` por `ELABORAR` en todos los trámites (ADR-003)
- Versión actual: 6.0
