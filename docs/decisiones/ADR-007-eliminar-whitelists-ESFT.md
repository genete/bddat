# ADR-007 — Eliminar whitelists E-S-F-T y refactorizar verbos del motor

**Estado:** Adoptada  
**Fecha:** 2026-05-14  
**Issue:** #387

---

## Contexto

El sistema dispone de un motor de reglas gobernado por el principio **"todo permitido salvo lo expresamente prohibido"** (blacklist), y de un conjunto de tablas whitelist (`expedientes_solicitudes`, `solicitudes_fases`, `fases_tramites`) que restringen qué combinaciones son válidas en la cadena ESFTT.

Durante la sesión de análisis del 2026-05-14 se detectaron dos inconsistencias estructurales:

### 1. Contradicción whitelist / motor

Las tablas whitelist operan con lógica positiva (solo lo listado es posible), mientras que el motor opera con lógica negativa (todo es posible salvo lo prohibido). Al ocultar opciones en el selector, la whitelist actúa como una blacklist implícita sin base legal visible para el técnico. Esto:

- Duplica la responsabilidad de definir qué está permitido
- Oculta la razón normativa de cada restricción
- Obliga a tocar el interfaz cuando cambia la legislación, además del motor

### 2. Verbos zombie: INICIAR y FINALIZAR

Los verbos INICIAR y FINALIZAR nacieron para gestionar el estado intermedio "planificada" (entidad creada con fecha vacía). Ese estado desapareció con ADR-002, que eliminó las fechas explícitas de ESFTT. Desde entonces:

- `iniciada` = estado derivado: tiene al menos un hijo creado
- `finalizada` = estado derivado: todos los hijos en estado terminal

No existe acción de usuario que dispare INICIAR o FINALIZAR — son efectos secundarios de CREAR/BORRAR sobre los hijos. Las reglas de estos verbos en `reglas_motor` son código zombie que no se puede disparar de forma natural.

---

## Decisión

### A — Eliminar las tres tablas whitelist E-S-F-T

Las tablas `expedientes_solicitudes`, `solicitudes_fases` y `fases_tramites` se eliminan mediante migración Alembic.

Las restricciones normativas que contenían (implícitamente) pasan al motor como reglas **CREAR** con referencia legal explícita y mensaje visible al técnico. Algunas ya existen parcialmente en el motor; el resto se completa en #387.

### B — Eliminar verbos INICIAR y FINALIZAR del motor

- Se eliminan todas las filas de `reglas_motor` con `evento IN ('INICIAR', 'FINALIZAR')`
- El CHECK constraint de `reglas_motor.evento` se reduce a `('CREAR', 'BORRAR')`
- La firma del evaluador `evaluar()` acepta solo `CREAR` y `BORRAR`
- El código de evaluación de estos verbos se elimina de `motor_reglas.py`

El motor pasa a tener **dos verbos genuinos** (acciones explícitas del usuario) en lugar de cuatro.

### C — Mantener T-T-D como capa de sugerencias

Las tablas `tramites_tareas` y `tramites_tareas_documentos` se conservan, pero su semántica cambia:

- **Antes:** whitelist positiva — las tareas listadas son las únicas disponibles
- **Después:** mapa de sugerencias — la UI pre-popula tareas y documentos a partir de esta tabla, pero el técnico puede ir más allá; el motor bloquea solo lo que tiene regla CREAR explícita

El campo `tramites_tareas.doc_consumido_tipo_id` se elimina (dead code: NULL en 74 de 75 filas; la información está cubierta por `tramites_tareas_documentos`).

---

## Razonamiento

**¿Por qué no una tabla de excepciones en lugar de eliminar las whitelists?**  
La excepción añade complejidad sin resolver el problema de fondo: la lógica de negocio seguiría dividida entre dos sistemas con semánticas opuestas. El motor es el lugar correcto y único para las reglas normativas.

**¿Por qué mantener T-T-D?**  
La secuencia de tareas (ANALIZAR → ELABORAR → NOTIFICAR → ESPERAR_PLAZO) tiene base normativa (LPACAP, actos administrativos firmados), pero su aplicación cotidiana es evidente para el técnico y no requiere bloqueo explícito. La tabla sirve además como mapa de automatización para pre-poblar el árbol de tareas al crear un trámite — función de utilidad, no de restricción.

**¿Por qué no una whitelist plana E-S-F-T-Ta-D exhaustiva?**  
A escala real (~15 tipos de solicitud × las fases que comparten) produciría 1.500-2.000 filas con alta redundancia. Cualquier cambio en un trámite requeriría N actualizaciones. La vista plana que necesita el análisis se obtiene mediante query, no almacenando la denormalización.

---

## Consecuencias

- #192 (requisitos documentales) requiere rediseño: usa FINALIZAR como punto de anclaje y propone tabla `procedimientos` que solapa con tipos existentes.
- Los selectores ESFTT en la UI consultan al motor antes de renderizar: las opciones con resultado BLOQUEAR se ocultan por defecto. Un checkbox "mostrar opciones no permitidas" permite al técnico verlas y forzarlas, quedando el intento registrado en bitácora con justificación obligatoria. Las opciones con resultado ADVERTIR se muestran siempre pero con indicación visual. Esto convierte al motor en la única fuente de verdad tanto para la lógica de negocio como para el comportamiento del interfaz.
- El principio de escape (el técnico puede salir de la sugerencia) pasa de ser una excepción a ser el comportamiento por defecto.
