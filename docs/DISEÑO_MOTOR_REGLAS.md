# MOTOR_REGLAS — Arquitectura de diseño

> **Última revisión:** 2026-02-28
> Documento derivado del análisis de dos ejemplos reales de tramitación AT en Andalucía
> y revisión exhaustiva en sesión con el técnico del servicio.

---

## Decisión de partida

Se abandona la investigación legislativa exhaustiva como prerequisito.
Las reglas se irán añadiendo progresivamente en producción — una, probarla, iterar.

**Fase 2 (actual):** Hooks en rutas y modelos ESFTT con la firma definitiva del evaluador,
devolviendo siempre PERMITIDO hasta que el motor esté implementado en Fase 3.

---

## Principio rector

**Todo está permitido excepto lo expresamente prohibido.**

El motor no define qué está permitido — define qué está prohibido en cada momento.
La iniciativa es siempre del técnico tramitador; el motor valida o informa.
El motor no genera el flujo automáticamente; responde a la pregunta:
«¿Está esto prohibido ahora mismo en estas circunstancias?»

---

## Vocabulario de eventos del motor

El motor distingue cuatro eventos en el ciclo de vida de cualquier entidad ESFTT:

| Evento | Semántica | Tipo de acción habitual |
|--------|-----------|------------------------|
| **CREAR** | ¿Es conceptualmente válido planificar esto en este contexto? | ADVERTIR (absurdo pero no imposible) o BLOQUEAR (imposible) |
| **INICIAR** | ¿Están cumplidos los prerequisitos para comenzar a ejecutar? | BLOQUEAR (restricción dura) |
| **FINALIZAR** | ¿Pueden cerrarse sus hijos? ¿Tiene documento requerido? | BLOQUEAR |
| **BORRAR** | ¿Ha sido ya iniciada la entidad? | BLOQUEAR si `fecha_inicio IS NOT NULL` |

**Distinción CREAR vs INICIAR:**
- CREAR corresponde al momento de insertar el registro, que puede ser sin `fecha_inicio` (planificación). Valida coherencia conceptual con el contexto.
- INICIAR corresponde al momento de poner `fecha_inicio` por primera vez (puede ocurrir en el mismo formulario de creación o en una edición posterior). Valida que los prerequisitos estén cumplidos.

**SOLICITUD** no tiene `fecha_inicio` — se crea siempre activa con `fecha_solicitud` (NOT NULL).
Solo tiene CREAR, FINALIZAR y BORRAR.

**Sobre el borrado:**
Una entidad iniciada (`fecha_inicio IS NOT NULL`) implica actividad administrativa con posible rastro externo (documentos en servidor de archivos, notificaciones enviadas). El criterio es binario: si se ha iniciado, no se borra — se finaliza ordenadamente incluso si hay incumplimiento de otras reglas, dejando rastro justificado. Si una entidad finalizada impide crear una nueva por reglas, la solución es revisar las reglas, no permitir el borrado.

---

## Arquitectura: un solo evaluador, no múltiples motores

Un único evaluador con reglas etiquetadas por evento y entidad.
La diferencia entre «motor de creación» y «motor de cierre» es solo un filtro
`WHERE evento='INICIAR'` — no código separado.

---

## Firma del evaluador

Asimetría necesaria entre CREAR/INICIAR y FINALIZAR/BORRAR:

```python
# CREAR: la entidad aún no existe
evaluar(evento='CREAR', entidad='FASE', tipo_id=8, padre_id=23, params={})

# INICIAR: la entidad ya existe (está planificada); el motor lee el tipo desde la BD
evaluar(evento='INICIAR', entidad='FASE', entidad_id=45, params={})

# FINALIZAR / BORRAR: la entidad ya existe
evaluar(evento='FINALIZAR', entidad='FASE', entidad_id=45, params={})
evaluar(evento='BORRAR',    entidad='FASE', entidad_id=45, params={})
```

Retorna: `EvaluacionResult(permitido: bool, nivel: str, mensaje: str, norma: str)`

`params` solo es necesario en casos especiales actualmente no confirmados tras la
revisión del patrón SEPARATAS (ver `docs/DISEÑO_CONSULTAS_ORGANISMOS.md`).

---

## Tipos de criterio que emergen de los ejemplos

| Código | Qué evalúa |
|--------|-----------|
| EXISTE_DOCUMENTO_TIPO | ¿Hay documento de tipo X (ej: DR_NO_DUP) en esta solicitud/expediente? |
| VARIABLE_EXPEDIENTE | ¿Campo Y del expediente tiene valor Z? (ej: tipo_expediente_id = 1) |
| VARIABLE_PROYECTO | ¿Campo Y del proyecto tiene valor Z? (ej: ia.siglas = CA, es_modificacion = true) |
| EXISTE_FASE_EXITO | ¿Hay fase de tipo X cerrada con resultado favorable en esta solicitud? |
| EXISTE_DOC_ORGANISMO | ¿Hay DR de tipo X para organismo concreto? |

El motor hace los JOINs internamente subiendo el árbol jerárquico:
TAREA → TRAMITE → FASE → SOLICITUD → EXPEDIENTE → PROYECTO.

`VARIABLE_PROYECTO` accede a `expediente.proyecto` (relación 1:1 garantizada).

---

## Campos en Proyecto necesarios para el motor

### `proyecto.ia_id` — ya implementado
FK a tabla `tipos_ia`. Instrumento ambiental del proyecto.

| id | siglas | Descripción |
|----|--------|-------------|
| 1 | AAI | Autorización Ambiental Integrada |
| 2 | AAU | Autorización Ambiental Unificada |
| 3 | AAUS | Autorización Ambiental Unificada Simplificada |
| 4 | CA | Calificación Ambiental |
| 5 | EXENTO | Exento de instrumento ambiental |

El motor accede como `proyecto.ia.siglas` (criterio `VARIABLE_PROYECTO`).

### `proyecto.es_modificacion` — **implementado** (`proyectos.py`)
`Boolean`, default `False`. Indica si el expediente tramita una modificación de
instalaciones existentes (frente a instalación nueva).
Afecta directamente a las reglas de tramitación ambiental (ver mapa de reglas).

---

## Mapa de (evento, entidad, tipo) con reglas conocidas

**Cómo leer las tablas:**
El motor evalúa la condición descrita. Si es **TRUE → aplica la acción**.
Si es **FALSE → operación permitida** (principio de todo permitido excepto prohibido).

---

### SOLICITUD — padre_id: expediente_id

| evento | tipo (siglas) | Condición (si TRUE → acción) | Acción |
|--------|--------------|------------------------------|--------|
| CREAR | AAP | EXISTS AAP activa en este expediente | BLOQUEAR |
| CREAR | DESISTIMIENTO | NOT EXISTS solicitud activa en este expediente (para afectar) | BLOQUEAR |
| CREAR | RENUNCIA | NOT EXISTS solicitud resuelta favorablemente en este expediente | BLOQUEAR |
| CREAR | RECURSO | NOT EXISTS resolución emitida en este expediente | BLOQUEAR |
| CREAR | RAIPEE_DEFINITIVA | NOT EXISTS RAIPEE_PREVIA resuelta en este expediente | ADVERTIR |
| FINALIZAR | cualquiera | NOT EXISTS fase RESOLUCION con `fecha_fin IS NOT NULL` en esta solicitud | BLOQUEAR |
| BORRAR | cualquiera | EXISTS fase con `fecha_inicio IS NOT NULL` en esta solicitud | BLOQUEAR |

**Nota FINALIZAR:** Solo se requiere que exista una fase RESOLUCION completada.
El resultado de la resolución (favorable o desfavorable) es irrelevante para el cierre
de la solicitud — una resolución denegatoria es el mecanismo ordinario de finalización.

---

### FASE — padre_id: solicitud_id

| evento | tipo (codigo) | Condición (si TRUE → acción) | Acción |
|--------|--------------|------------------------------|--------|
| CREAR | CONSULTA_MINISTERIO | `expediente.tipo_expediente_id` NOT IN {1} (Transporte) | BLOQUEAR |
| INICIAR | INFORMACION_PUBLICA | EXISTS documento tipo DR_NO_DUP en esta solicitud AND `proyecto.ia.siglas` NOT IN {AAU, AAUS} | BLOQUEAR |
<!-- DR_NO_DUP = documento que acredita que la instalación no requiere Declaración de Utilidad Pública para su implantación (condición objetiva, no declaración de intención).
Fuente: Disposición Final Cuarta del Decreto-ley 26/2021, de 14 de diciembre (simplificación administrativa Andalucía).
Texto legal: "No se someterán al trámite de información pública aquellas solicitudes [...] que no requieran de declaración de utilidad pública para su implantación y que no estén sometidas a la autorización ambiental unificada".
La exención de IP requiere AMBAS condiciones: (1) no necesita DUP + (2) no sujeta a AAU.
El motor implementa esto como: EXISTS DR_NO_DUP (condición 1) AND ia NOT IN {AAU, AAUS} (condición 2) → BLOQUEAR IP.
Nota: el texto legal solo menciona AAU; la extensión a AAUS es decisión de política interna del servicio, no está en la norma. -->
| INICIAR | FIGURA_AMBIENTAL_EXTERNA | `proyecto.ia.siglas` NOT IN {CA, AAI} AND NOT (`proyecto.ia.siglas` IN {AAU, AAUS} AND `proyecto.es_modificacion` = true) | BLOQUEAR |
| INICIAR | AAU_AAUS_INTEGRADA | `proyecto.ia.siglas` NOT IN {AAU, AAUS} OR `proyecto.es_modificacion` = true | BLOQUEAR |
| INICIAR | RESOLUCION | (`proyecto.ia.siglas` IN {CA, AAI} OR (`proyecto.ia.siglas` IN {AAU, AAUS} AND `proyecto.es_modificacion` = true)) AND NOT EXISTS fase FIGURA_AMBIENTAL_EXTERNA con `cerrada_favorable` = true | BLOQUEAR |
| INICIAR | RESOLUCION | NOT EXISTS fase ANALISIS_SOLICITUD con `fecha_fin IS NOT NULL` (regla interna del servicio) | BLOQUEAR |
| FINALIZAR | cualquiera | EXISTS trámite con `fecha_fin IS NULL` en esta fase | BLOQUEAR |
| BORRAR | cualquiera | `fecha_inicio IS NOT NULL` | BLOQUEAR |

**Notas sobre tramitación ambiental:**
- **CA:** siempre se tramita externamente (FIGURA_AMBIENTAL_EXTERNA)
- **AAI:** siempre se tramita externamente (FIGURA_AMBIENTAL_EXTERNA)
- **AAU/AAUS + instalación nueva:** se tramita integrada (AAU_AAUS_INTEGRADA)
- **AAU/AAUS + modificación (`es_modificacion=true`):** se tramita externamente (FIGURA_AMBIENTAL_EXTERNA)
- La existencia de FIGURA_AMBIENTAL_EXTERNA favorable es prerequisito de INICIAR RESOLUCION para CA, AAI y AAU/AAUS en modificaciones

**Tipos de expediente en BD** (tabla `tipos_expedientes`):
`1=Transporte, 2=Distribución, 3=Distribución cedida, 4=Renovable, 5=Autoconsumo, 6=LineaDirecta, 7=Convencional, 8=Otros`

---

### TRÁMITE — padre_id: fase_id

| evento | tipo (codigo) | Condición (si TRUE → acción) | Acción |
|--------|--------------|------------------------------|--------|
| CREAR | ANUNCIO_BOE / ANUNCIO_BOP / ANUNCIO_PRENSA | tipo de la fase padre NOT IN {INFORMACION_PUBLICA} | BLOQUEAR |
| INICIAR | PUBLICACION_RESOLUCION | NOT EXISTS trámite ELABORACION_RESOLUCION con `fecha_fin IS NOT NULL` AND `doc_producido_id IS NOT NULL` | BLOQUEAR |
| INICIAR | NOTIFICACION_RESOLUCION | NOT EXISTS trámite ELABORACION_RESOLUCION con `fecha_fin IS NOT NULL` AND `doc_producido_id IS NOT NULL` | BLOQUEAR |
| FINALIZAR | cualquiera | EXISTS tarea con `fecha_fin IS NULL` en este trámite | BLOQUEAR |
| BORRAR | cualquiera | `fecha_inicio IS NOT NULL` | BLOQUEAR |

**Nota SEPARATAS:** Eliminada de las reglas conocidas. Requiere diseño previo de
la tabla `entidades_consultadas`. Ver `docs/DISEÑO_CONSULTAS_ORGANISMOS.md`.

---

### TAREA — padre_id: tramite_id

Las tareas tienen solo 7 tipos genéricos. Sus reglas son de secuencia interna
(independientes del dominio legislativo) y de obligatoriedad de documento.

**Criterio de qué es una tarea ESFTT:**
- Una tarea es una unidad de trabajo **registrable con fecha inicio/fin**. Si una actividad nunca se registra como pendiente o completada, no es una tarea ESFTT.
- Las funcionalidades de interfaz (preparar documentación, calcular fechas, calcular plazos) **no son tareas** — son utilidades de soporte que no generan registro administrativo.

| evento | tipo (codigo) | Condición (si TRUE → acción) | Acción |
|--------|--------------|------------------------------|--------|
| INICIAR | FIRMAR | NOT EXISTS tarea REDACTAR con `fecha_fin IS NOT NULL` AND `doc_producido_id IS NOT NULL` en este trámite | BLOQUEAR |
| INICIAR | NOTIFICAR | NOT EXISTS tarea FIRMAR con `fecha_fin IS NOT NULL` AND `doc_producido_id IS NOT NULL` en este trámite | BLOQUEAR |
| INICIAR | PUBLICAR | NOT EXISTS tarea FIRMAR con `fecha_fin IS NOT NULL` AND `doc_producido_id IS NOT NULL` en este trámite | BLOQUEAR |
| FINALIZAR | REDACTAR / FIRMAR / INCORPORAR | `doc_producido_id IS NULL` | BLOQUEAR |
| FINALIZAR | NOTIFICAR / PUBLICAR | `doc_usado_id IS NULL` | BLOQUEAR |
| BORRAR | cualquiera | `fecha_inicio IS NOT NULL` | BLOQUEAR |

---

## Zona gris — consultas a organismos

> **Obsoleto.** Esta sección ha sido superada por `docs/DISEÑO_CONSULTAS_ORGANISMOS.md`,
> que contiene el diseño completo y cerrado de la fase de consultas a organismos (#247).
> Conservada aquí solo como referencia histórica del diseño tentativo original.

---

## Principio de escape

**Principio transversal de diseño:** toda cascada, filtro y regla debe tener vía de escape.

El técnico tramitador puede encontrar situaciones no previstas en el flujo normal
(alegación fuera de contexto, cambio de rumbo del expediente, etc.). El sistema
no debe crear callejones sin salida.

**Implementación:**
- El usuario puede elegir opciones "fuera de contexto" con advertencia visual
- Toda acción de escape se registra en bitácora
- Toggle "Solo aplicables al contexto" (defecto = todas las opciones visibles)

Aplica a: selectores en cascada ESFTT, motor de reglas, filtrado de plantillas,
y cualquier mecanismo futuro que restrinja opciones.

---

## Whitelist E→S→F→T — tablas de estructura ESFTT

Tres tablas whitelist editables por el Supervisor cubren la cascada completa:

| Tabla | PK compuesta | Semántica |
|-------|-------------|-----------|
| `expedientes_solicitudes` | `tipo_expediente_id` + `tipo_solicitud_id` | Qué solicitudes son válidas para cada tipo de expediente |
| `solicitudes_fases` | `tipo_solicitud_id` + `tipo_fase_id` | Qué fases aplican a cada tipo de solicitud |
| `fases_tramites` | `tipo_fase_id` + `tipo_tramite_id` | Qué trámites son válidos dentro de cada fase |

**Características:**
- Seed inicial desde `ESTRUCTURA_FTT.json`
- CRUD editable por Supervisor (legislación cambiante — no hardcoded)
- Solo definen **posibilidad** ("esta combinación tiene sentido"), no obligatoriedad ni orden
- La cascada de selectores consume estas tablas como whitelist
- El principio de escape permite al técnico salir de la whitelist con advertencia visual

**Implementación:** Issue #167 Fase 1. Ver `docs/DISEÑO_GENERACION_ESCRITOS.md`.

---

## Tipos de solicitud combinados como entidades propias

Las combinaciones de tipos de solicitud (AAP+AAC, AAP+AAC+DUP...) son entidades
propias en `tipos_solicitudes`, no una tabla puente M:N.

**Motivación:** Las combinaciones legales son ~6, finitas y cerradas (cambio legislativo
para añadir una nueva). Cada combinación tiene implicaciones procedimentales distintas
(fases, texto de resoluciones). Las plantillas necesitan FK directo.

Ver catálogo completo en `docs/NORMATIVA_SOLICITUDES.md`.

**Impacto en modelos:**
- `tipos_solicitudes` → añadir ~6 tipos combinados
- `solicitudes` → añadir FK `tipo_solicitud_id` directa (reemplaza tabla puente `solicitudes_tipos`)
- `solicitudes_tipos` → mantener como histórico, dejar de usar para lógica de negocio

**Implementación:** Issue #167 Fase 1.

---

## Compatibilidad de tipos en una solicitud

Con la decisión de tipos combinados como entidades propias, la compatibilidad entre
tipos se gestiona mediante la whitelist `expedientes_solicitudes` y la propia tabla
`tipos_solicitudes` (que solo contiene combinaciones legales).

**Tabla de referencia histórica** (previa a la migración de Fase 1 del #167):
```
TIPOS_SOLICITUDES_COMPATIBLES
  tipo_a_id  FK → tipos_solicitudes  (par siempre en orden: tipo_a < tipo_b)
  tipo_b_id  FK → tipos_solicitudes
  nota        texto explicativo / referencia normativa si aplica
```

Ejemplos:
- `AAP + AAE` → PROHIBIDO (AAE implica instalación construida; AAP es anterior)
- `DUP + CIERRE` → PROHIBIDO (DUP implica que no se pudo construir; CIERRE implica existente)
- `AAP + AAC` → PERMITIDO → entrada directa en `tipos_solicitudes` como `AAP_AAC`

**Pendiente:** definir la lista completa de pares compatibles con el técnico del servicio.

---

## Tablas del motor

```
REGLAS_MOTOR
  id, evento (CREAR|INICIAR|FINALIZAR|BORRAR), entidad (SOLICITUD|FASE|TRAMITE|TAREA|EXPEDIENTE),
  tipo_id (nullable = aplica a todos), accion (BLOQUEAR|ADVERTIR),
  mensaje, norma, activa

CONDICIONES_REGLA  (1:N con REGLAS_MOTOR)
  id, regla_id, tipo_criterio, parametros (JSON),
  negacion (bool), orden (int), operador_siguiente (AND|OR)
```

**Tipos de criterio en `CONDICIONES_REGLA.tipo_criterio`:**
- `EXISTE_DOCUMENTO_TIPO` — params: `{tipo_doc_codigo, ambito}`
- `EXISTE_DOC_ORGANISMO` — params: `{tipo_doc_codigo}` + organismo via params_extra
- `EXISTE_FASE_CERRADA` — params: `{tipo_fase_codigo}`
- `EXISTE_FASE_CON_RESULTADO` — params: `{tipo_fase_codigo, resultado_codigos: []}`
- `VARIABLE_EXPEDIENTE` — params: `{campo, operador, valor}`
- `VARIABLE_PROYECTO` — params: `{campo, operador, valor}` (accede via expediente.proyecto)
- `TIPO_FASE_PADRE_ES` — params: `{tipo_fase_codigo}`
- `EXISTE_TAREA_TIPO` — params: `{tipo_tarea_codigo, cerrada, requiere_doc_producido}`
- `EXISTE_TRAMITE_TIPO` — params: `{tipo_tramite_codigo, cerrado, requiere_doc_producido}`
- `ESTADO_SOLICITUD` — params: `{estado}`
- `EXISTE_TIPO_SOLICITUD` — params: `{tipo_solicitud_codigo}`

---

## Estados ESFTT — auditoría de modelos Python

> Revisado contra modelos .py reales.
> Distinción clave: campo persistido vs. @property calculada al vuelo.

### EXPEDIENTE
Sin campo `estado`, sin `fecha_inicio`/`fecha_fin`. Sin `@property` de estado.
Estado completamente derivado de sus solicitudes — no implementado aún.

**Ciclo de vida:**
El expediente vive junto con el proyecto. Los expedientes con tramitaciones fallidas
se finalizan con resoluciones desestimatorias. Una vez archivado, cualquier solicitud
nueva tras el archivo crea un nuevo expediente.

**Instalaciones (mundo aparte):**
Nacen con el proyecto pero una vez en servicio se independizan de él. Sus estados
referencian el expediente/proyecto/solicitud/resolución que las dejó en ese estado.
No afectan al modelo ESFTT actual.

### SOLICITUD
`estado` es **campo persistido** (varchar, NOT NULL, default `EN_TRAMITE`).
Valores: `EN_TRAMITE`, `RESUELTA`, `DESISTIDA`, `ARCHIVADA`.

**@property ya implementadas:**
- `activa` → `estado == 'EN_TRAMITE'`
- `es_desistimiento_o_renuncia` → `solicitud_afectada_id is not None` *(temporal — ver TODO en modelo)*

**Tipos de solicitud — relación N:M deliberada:**
No hay `tipo_solicitud_id` directo. Los tipos se gestionan en tabla puente `SolicitudTipo`.

**Limitación del campo `estado`:** `RESUELTA` no distingue favorable de desfavorable.
Para reglas que necesiten esa distinción, el motor debe consultar `resultado_fase_id`
de la fase RESOLUCION asociada.

### FASE
`resultado_fase_id` es FK a `tipos_resultados_fases` (NO boolean — GUIA_GENERAL
desactualizada; el modelo Python ya usa FK).
Valores: `FAVORABLE`, `FAVORABLE_CONDICIONADO`, `DESFAVORABLE`, `NO_PROCEDE`, `DESISTIDA`, `ARCHIVADA`.

**Estados deducibles** (sin `@property` implementada aún):
- `PLANIFICADA`: `fecha_inicio IS NULL`
- `EN_CURSO`: `fecha_inicio IS NOT NULL AND fecha_fin IS NULL`
- `FINALIZADA`: `fecha_fin IS NOT NULL`
- `FINALIZADA_FAVORABLE`: `fecha_fin IS NOT NULL AND resultado_fase.codigo IN ('FAVORABLE','FAVORABLE_CONDICIONADO')`

### TRÁMITE
Sin campo de resultado — solo fechas. Sin `@property` implementada.

**Estados deducibles:**
- `PLANIFICADO`: `fecha_inicio IS NULL`
- `EN_CURSO`: `fecha_inicio IS NOT NULL AND fecha_fin IS NULL`
- `FINALIZADO`: `fecha_fin IS NOT NULL`

### TAREA
Sin `@property` implementada.

**Estados deducibles:**
- `PLANIFICADA`: `fecha_inicio IS NULL`
- `EN_CURSO`: `fecha_inicio IS NOT NULL AND fecha_fin IS NULL`
- `EJECUTADA`: `fecha_fin IS NOT NULL`
- `EJECUTADA_CON_DOC`: `fecha_fin IS NOT NULL AND documento_producido_id IS NOT NULL`

---

## Vocabulario de estados para @property

El motor referencia nombres de estado, no condiciones SQL crudas.
Las `@property` son el contrato entre el modelo y el motor.
Fase, Trámite y Tarea implementadas. Pendientes en Solicitud: `cerrada` y `resuelta_favorable`.

| Entidad | @property | Condición |
|---------|-----------|-----------|
| Solicitud | `activa` ✅ | `estado == 'EN_TRAMITE'` |
| Solicitud | `cerrada` ⬜ | `estado in ('RESUELTA','DESISTIDA','ARCHIVADA')` |
| Solicitud | `resuelta_favorable` ⬜ | `estado == 'RESUELTA'` AND fase RESOLUCION con resultado favorable |
| Fase | `planificada` ✅ | `fecha_inicio is None` |
| Fase | `en_curso` ✅ | `fecha_inicio is not None and fecha_fin is None` |
| Fase | `finalizada` ✅ | `fecha_fin is not None` |
| Fase | `finalizada_favorable` ✅ | `fecha_fin is not None and resultado_fase.codigo in ('FAVORABLE','FAVORABLE_CONDICIONADO')` |
| Tramite | `planificado` ✅ | `fecha_inicio is None` |
| Tramite | `en_curso` ✅ | `fecha_fin is None and fecha_inicio is not None` |
| Tramite | `finalizado` ✅ | `fecha_fin is not None` |
| Tarea | `planificada` ✅ | `fecha_inicio is None` |
| Tarea | `en_curso` ✅ | `fecha_inicio is not None and fecha_fin is None` |
| Tarea | `ejecutada` ✅ | `fecha_fin is not None` |
| Tarea | `ejecutada_con_doc` ✅ | `fecha_fin is not None and documento_producido_id is not None` |

✅ implementada · ⬜ pendiente

---

## Observaciones clave

1. **TAREAS primero:** Sus reglas son las más mecánicas y universales.
   Mejor candidato para implementar en primera iteración del motor.

2. **FASES son el nivel más legislativo:** Aquí viven las excepciones
   de los decretos de simplificación. Requieren el contexto más rico.

3. **El motor sube el árbol:** Una regla de TAREA puede necesitar
   el tipo del TRAMITE padre o el tipo de FASE abuelo. El motor hace
   los JOINs — no se necesita pasar contexto completo en la llamada.
   El árbol completo es: TAREA → TRAMITE → FASE → SOLICITUD → EXPEDIENTE → PROYECTO.

4. **CREAR valida coherencia conceptual; INICIAR valida prerequisitos:**
   Una fase puede planificarse aunque sus prerequisitos no estén cumplidos.
   El motor bloquea el inicio, no la planificación. Esto permite al técnico
   preparar el expediente con antelación sin violar reglas de negocio.

5. **Consultas a organismos elevadas a nivel expediente/proyecto:**
   El patrón de «lista de organismos consultados» no debe implementarse
   ad-hoc en el HTML de un trámite concreto. Está pendiente de diseño
   general reutilizable (issue draft separatas).

---

## Pendientes

- ✅ Implementar campo `proyecto.es_modificacion` (Boolean, default=False) + migración
- ✅ Cambiar CHECK constraint `reglas_motor.evento` — incluye `CREAR`, `INICIAR`, `FINALIZAR`, `BORRAR`
- ✅ Actualizar GUIA_GENERAL: sección FASE — `exito` (bool) → `resultado_fase_id` (FK a tipos_resultados_fases)
- ✅ Añadir `@property` de estado a FASE, TRÁMITE y TAREA
- ✅ Implementar evaluador `app/services/motor_reglas.py` con handlers por entidad
- ⬜ Añadir `Solicitud.cerrada` y `Solicitud.resuelta_favorable`
- ⬜ Definir tabla `entidades_consultadas` y su integración con SEPARATAS (issue draft)
- ⬜ Poblar `reglas_motor` + `condiciones_regla` con las reglas del mapa anterior
- ⬜ Definir pares compatibles en `tipos_solicitudes_compatibles` (con el técnico del servicio) — #276
- ⬜ Decidir si TRÁMITE necesita `resultado_tramite_id` análogo al de FASE
- ⬜ Decidir si EXPEDIENTE necesita `@property estado` explícito o derivado de solicitudes
