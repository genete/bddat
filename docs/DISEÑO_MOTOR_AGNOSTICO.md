# Motor de reglas agnóstico — Decisiones de rediseño

> **Fecha:** 2026-03-31
> Sesión de reflexión arquitectural. Complementa `DISEÑO_MOTOR_REGLAS.md`.

---

## Decisión principal: motor agnóstico de dominio

El motor de reglas debe refactorizarse para ser completamente independiente de BDDAT.
En lugar de que el motor conozca el dominio (Fase, Tarea, Expediente, etc.) y haga
queries internos al árbol ESFTT, el flujo correcto es:

1. **BDDAT** ensambla un dict plano de variables antes de llamar al motor
2. **Motor** recibe `(accion, tipo, variables: dict)` y evalúa reglas en BD contra ese dict
3. El motor no importa modelos de BDDAT, no traversa el árbol ESFTT, no hace queries propias

```python
# BDDAT ensambla el contexto
variables = {
    'ia':                  'AAU',
    'es_modificacion':     False,
    'intermunicipal':      True,    # calculado por BDDAT: len(proyecto.municipios) > 1
    'fase_ip_cerrada':     False,   # calculado por BDDAT: query a Fase
    'tiene_doc_producido': True,    # calculado por BDDAT
    'plazo_vencido':       False,   # calculado por BDDAT: controlador de fechas
}

# Motor evalúa — sin saber de dónde vienen los valores
motor.evaluar(accion='INICIAR', tipo='TRAMITE', variables=variables)
```

**Principio:** es el procedimiento el que se engancha al API del motor, no al revés.
El motor es válido para cualquier tramitador (AT, subvenciones, reclamaciones).
BDDAT se adapta al API del motor.

**Por qué ahora:** las tablas `reglas_motor` y `condiciones_regla` aún no están pobladas
con reglas reales. El coste de refactorizar es mínimo ahora, altísimo después.

---

## Pieza nueva: ContextAssembler

Capa de BDDAT que, dado un evento + entidad, sube el árbol ESFTT y computa todas las
variables necesarias antes de llamar al motor. Esta capa sí conoce BDDAT a fondo.

**Complejidad propia pendiente de diseño:**
- ¿Qué variables computa para cada `(accion, tipo)`? ¿Hardcoded o configurable en BD?
- El Supervisor debe poder editar acciones, variables y condiciones → hay que equilibrar
  flexibilidad con que no todo sea personalizable
- Variables derivadas (`intermunicipal`, `plazo_vencido`, `tiene_fase_X_cerrada`) requieren
  queries específicas — cómo se declaran sin hardcodearlas es una decisión de diseño abierta
- El contrato entre ContextAssembler y Motor define qué variables existen: si es configurable,
  el Supervisor necesita UI para declarar variables nuevas

---

## Problemas que resuelve respecto al diseño actual

| Problema con diseño actual | Solución con motor agnóstico |
|---|---|
| `intermunicipal` requería query especial en el motor | ContextAssembler lo computa y pasa como variable |
| `documentos_tarea` (INCORPORAR multi-doc) no accesible al motor | ContextAssembler pasa `tiene_docs_incorporar: True` |
| No existía `VARIABLE_TRAMITE` ni `VARIABLE_FASE` como criterios | Desaparecen — todo son variables del dict |
| `_TIPOS_REQUIEREN_DOC_PRODUCIDO` hardcodeado en motor | ContextAssembler lo computa según tipo de tarea |
| Plazos/fechas inaccesibles al motor | ContextAssembler pasa `plazo_vencido`, `dias_transcurridos`, etc. |
| `solicitud.estado` sin integridad referencial | Pasa como variable; su validez la gestiona BDDAT |

---

## Deuda técnica identificada en diseño actual

### Criterios BDDAT-específicos a eliminar del motor
- `EXISTE_FASE_CERRADA` — el motor conoce el modelo Fase
- `EXISTE_TAREA_TIPO` — el motor conoce el modelo Tarea
- `_check_finalizar_tarea` — hardcoded con lógica de BDDAT
- `EXISTE_DOCUMENTO_TIPO`, `EXISTE_DOC_ORGANISMO` — stubs pendientes

### Valores inline sin integridad referencial
- `Solicitud.estado` — VARCHAR con `EN_TRAMITE|RESUELTA|DESISTIDA|ARCHIVADA`, sin FK a tabla.
  Si cambia en Python, los registros en `condiciones_regla` quedan huérfanos sin detección.
- `_TIPOS_REQUIEREN_DOC_PRODUCIDO` / `_TIPOS_REQUIEREN_DOC_USADO` — sets hardcodeados
  en `motor_reglas.py`; son propiedades funcionales de `TipoTarea` que deberían estar en BD.

### Estados derivados (@property) sin criterio genérico
Los `@property` (`planificada`, `en_curso`, `ejecutada`) son el contrato correcto del modelo.
El problema es que el motor actual no puede referenciarlos en reglas configurables.
Con el rediseño agnóstico esto deja de ser problema: ContextAssembler los computa y los pasa.

---

## Controlador de fechas — pieza no diseñada

**Estado:** No existe diseño, documento ni implementación.

**Qué bloquea:**
- `PLAZO_DIAS`/`TIPO_DIAS` de ESPERAR_PLAZO vive en `tarea.notas` como texto libre
  → inaccesible para el motor y para cualquier cálculo automatizado
- Vista de seguimiento no puede mostrar expedientes vencidos o próximos a vencer
- Motor no puede evaluar condiciones temporales (`plazo_vencido`, `dias_transcurridos`)
- #279 (campos extra proyecto) puede incluir datos que afectan a plazos

**Preguntas de diseño abiertas (responder antes de implementar cualquier issue de fechas):**
1. ¿`PLAZO_DIAS` y `TIPO_DIAS` salen de `tarea.notas` y se convierten en campos reales de Tarea?
2. ¿El motor necesita evaluar "plazo vencido" como condición de BLOQUEAR, o solo es informativo?
3. ¿Fecha de vencimiento se calcula al vuelo o se persiste?
4. ¿El controlador de fechas es parte del ContextAssembler o una capa separada?

---

## Issues M2 afectados

### #290 — INCORPORAR multi-doc (tabla documentos_tarea)
**Estado: en standby** hasta resolver diseño del controlador de fechas.
La validación de FINALIZAR para INCORPORAR migrará del motor actual
(`doc_producido_id IS NULL → BLOQUEAR`) al ContextAssembler (`tiene_docs_incorporar`).
Implementar ahora requeriría cambiar esa lógica dos veces.

### #279 — Campos extra en Proyecto (tecnología, kV, kVA, tipo suelo...)
**Estado: requiere diseño previo.** Preguntas abiertas:
- ¿Qué campos van en `Proyecto` y cuáles en tabla catálogo propia?
- ¿Tipo de suelo es enum o tabla `tipos_suelo`?
- ¿Tensión/potencia son numéricos libres o rangos normalizados?
- ¿Qué reglas del motor los necesitan?

Con motor agnóstico, cualquier campo nuevo en `Proyecto` es automáticamente accesible
via ContextAssembler — no requiere cambios en el motor.

### #289 — Context Builders (Capa 2 generación escritos)
**Estado: bloqueado** por #279 y falta de datos reales. Los builders beben de campos
extra de proyecto que aún no existen.

---

## Orden de trabajo recomendado

1. Diseño motor agnóstico + API del motor
2. Diseño controlador de fechas (desbloquea #290 y #279)
3. Diseño ContextAssembler (qué variables, cómo se declaran, qué configura el Supervisor)
4. #279 — después de los diseños anteriores
5. #290 — después del controlador de fechas
6. #289 — después de #279 y con datos reales

---

## Advertencia: el refactor tiene riesgos reales

Esta sección recoge una reflexión crítica sobre si el rediseño es realmente lo correcto ahora,
para no tomarlo como decisión automática en la próxima sesión.

### Lo que sí es claramente mejor

El motor actual mezcla lógica de evaluación con conocimiento del dominio BDDAT. Eso no es
una opinión de arquitectura — es un problema práctico: cada vez que aparece una variable nueva
(intermunicipal, multi-doc, plazos) hay que tocar el motor. Con el diseño agnóstico desaparece.

El momento es el mejor posible: `reglas_motor` está vacía. Si se espera a tener 50 reglas en BD
referenciando `EXISTE_FASE_CERRADA`, el coste de migración es mucho mayor.

### Lo que hay que tener claro antes de ejecutar

**El ContextAssembler no es más simple que lo que tenemos.** Es la misma complejidad, reubicada.
El motor actual sube el árbol ESFTT y evalúa condiciones. El ContextAssembler sube el árbol ESFTT
y computa variables. La lógica es equivalente — lo que cambia es quién la contiene y dónde vive.
Eso tiene valor arquitectural, pero no reduce líneas de código ni elimina casos especiales.

**Riesgo concreto:** hacer el refactor del motor sin tener el diseño del ContextAssembler definido
significa desmontar algo que funciona sin tener claro qué lo reemplaza.

### La alternativa incremental

Existe un camino que da el 80% del beneficio con el 20% del trabajo:

1. Añadir `VARIABLE_SOLICITUD` y `VARIABLE_TRAMITE` como criterios genéricos — elimina la
   asimetría actual sin refactorizar la arquitectura
2. Mover `_TIPOS_REQUIEREN_DOC_PRODUCIDO` a columnas en `tipos_tareas` — saca lógica de
   dominio del motor sin tocar el diseño
3. Migrar `Solicitud.estado` a FK — resuelve el problema de integridad referencial

No es tan elegante, pero es ejecutable sin diseñar el ContextAssembler primero.

### Conclusión

Hacer el refactor completo **solo si** el diseño del ContextAssembler está cerrado antes:
qué variables existen, cómo se declaran, qué puede configurar el Supervisor.
Sin ese diseño, el refactor es un salto al vacío. Si el diseño no está listo, el camino
incremental es más prudente.

**Próxima sesión:** explorar la casuística real de BDDAT para definir el alcance del
ContextAssembler: qué variables necesita computar, de dónde las obtiene, y qué parte
debe poder editar el Supervisor.
