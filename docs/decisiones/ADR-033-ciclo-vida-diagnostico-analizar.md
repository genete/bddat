# ADR-033 — Ciclo de vida del diagnóstico de ANALIZAR: borrador, producción y reversión controlada

**Estado:** Adoptada — pendiente de implementación (ver §Issues de implementación)
**Fecha:** 2026-07-18
**Depende de:** ADR-005 (ANALIZAR produce DIAGNOSTICO), ADR-023 (inspector universal), ADR-006 (URIs `bddat://`)
**Enmienda:** ADR-005 — de "un solo tiro, inmutable" a "reversible bajo condiciones"
**Origen:** sesión de crítica ergonómica del flujo de la tarea ANALIZAR de principio a fin (2026-07-18).

---

## Contexto

Se revisó el flujo completo de la tarea ANALIZAR del trámite `ANÁLISIS_DOCUMENTAL`, de la creación al cierre, desde el punto de vista ergonómico y funcional. El hallazgo central no fue un bug de código, sino un **error semántico** con consecuencias reales:

- El bloque etiquetado **"Defectos consolidados"** se rellenaba solo, en vivo, con los requisitos documentales no cubiertos. Como el catálogo `requisitos_documentales` es global por tipo de solicitud, dos expedientes del mismo tipo mostraban la misma lista sin ninguna fuga de datos entre ellos — pero "consolidado" sugería un acto de cierre consciente que nunca había ocurrido. Una tarea recién creada aparecía "consolidada" de entrada, y nada impedía emitir un diagnóstico **favorable con defectos a la vista**.
- ADR-005 fijó que ANALIZAR produce un DIAGNOSTICO en un solo tiro, inmutable. El trabajo real de subsanación exige poder **corregir un diagnóstico erróneo** mientras no se haya consumido aguas abajo.
- Sobre la misma superficie conviven mecanismos construidos en momentos distintos sin remirarse (Pool de documentos, par Guardar/Cancelar muerto, radio con "Condicionado" sin camino de motor, campo `notas` inaccesible).

Este ADR fija el **ciclo de vida completo del diagnóstico** —de borrador a producido a revertido— y la semántica de cada bloque de la superficie. El marco de edición del inspector (Cerrar/Guardar/Cancelar, superficie-de-trabajo vs nodo-de-campos), por ser transversal a todo nodo, se decide en la enmienda de ADR-023 (2026-07-18), no aquí.

---

## Decisión

### 1. Un único bloque que muta de nombre según el estado

No hay dos bloques de defectos (el "consolidado" automático y el "Resultado" del producido). Es **el mismo bloque**, que cambia de nombre y de naturaleza al producir:

- **"Borrador defectos"** mientras se trabaja: agregado vivo de los tres orígenes (documental, técnico, libre). Muta libremente al editar cualquier bloque. **No dispara ningún aviso** — es un borrador, no se ha producido nada; el técnico solo se lo está pensando.
- **"Resultado diagnóstico"** tras producir: foto congelada del DIAGNOSTICO (ADR-005). Es la vista del documento producido; su resultado queda fijado.

Se **elimina** el bloque "Defectos consolidados" automático. El estado en curso de cada eje vive en la cabecera-resumen de su acordeón (ADR-023 §layout interno); el borrador agregado es su suma.

### 2. El acto consciente es Producir; no hay consolidación intermedia

No existe un paso "Consolidar" separado. El único acto consciente es **Producir el documento de diagnóstico**, con su confirmación de dos pasos (ya existente) como punto de revisión: ahí se muestra el borrador agregado y se aplica el gate del §4. Producir congela el borrador en `Diagnostico.defectos` (ya lo hace hoy `crear_diagnostico`) y lo vincula como PRODUCIDO.

### 3. Resultado derivado del borrador; sin "Condicionado" en ANÁLISIS_DOCUMENTAL

El resultado **no es una elección libre**, es un reflejo confirmado del borrador:

- Borrador vacío → **favorable** → el motor habilita `COMUNICACIÓN_INICIO`.
- Borrador con defectos → **desfavorable** → el motor habilita `REQUERIMIENTO_SUBSANACIÓN`.

Se **retira "Condicionado"** del selector en esta tarea: el propio código lo documenta (`app/services/variables/calculado.py`: "ANALISIS_DOCUMENTAL nunca emite resultado 'condicionado'"). El motor de esta fase es binario. "Condicionado" pertenece, si acaso, a otro tipo de ANALIZAR (una resolución con condicionantes), fuera del alcance de este ADR.

Consecuencia: el "favorable con defectos" deja de ser posible por construcción — no es que el sistema avise, es que no es representable.

### 4. Gate de completitud solo técnico

Los tres bloques tienen semánticas de completitud distintas, y solo uno debe bloquear la producción:

- **Técnico — indirecto.** Máquina de tres estados (no revisado / cumple / no cumple). "No revisado" es un estado real distinto de "revisado y falta", así que un ítem sin revisar **sí** bloquea la producción con un gate **salvable con justificación** (ya funciona hoy: "no has revisado todos los ítems técnicos; justifica para seguir"). Se conserva.
- **Documental — directo.** Binario: no casado = falta = defecto. No existe "sin revisar"; la ausencia **es** el dato. Un requisito no casado es un defecto legítimo, no un pendiente — producir un desfavorable por documentos faltantes es el caso normal y **no debe friccionar**.
- **Libre — voluntario.** Vacío no bloquea; con contenido es defecto.

Por tanto el cómputo de `completo` en `consolidar_defectos` debe pasar a ser **solo técnico**. Hoy es `completo_documental and completo_tecnico`, lo que hace que producir con documentos faltantes pida justificación indebidamente. Se retira el documental (y el libre nunca contó) del gate.

### 5. Puerta hacia atrás: reversión controlada del diagnóstico producido

ADR-005 se enmienda: el diagnóstico deja de ser inmutable de por vida y pasa a ser **reversible mientras no se haya consumido**. La fricción de cada marcha atrás es proporcional a lo que destruye — escalera de tres peldaños, capturada en los **tres puntos de persistencia reales** de cada bloque (documental: botón *Vincular*; técnico: *Guardar* del ítem; libre: *Guardar cambios* de la cabecera del shuttle):

1. **Sin diagnóstico producido** — editar un bloque solo cambia el borrador. → **toast** informativo, sin confirmación. Nada formal se destruye.
2. **Diagnóstico producido, no consumido** — editar un bloque invalidaría el resultado. → **confirmación destructiva** (patrón inline de ADR-023, no diálogo nativo): "Al modificar los defectos con el diagnóstico producido, se invalidará el resultado y el diagnóstico se eliminará. ¿Continuar?" — con mención de **qué** se pierde. Si confirma: se elimina el DIAGNOSTICO y se vuelve a "Borrador defectos".
3. **Diagnóstico consumido por un ELABORAR** — la puerta está **cerrada**. Es coherencia estructural **no soslayable** (no forzable con justificación, a diferencia de los bloqueos de motor): primero hay que deshacer el consumidor. El mensaje dice por qué y qué deshacer antes.

**Regla de dominio:** un ELABORAR de `REQUERIMIENTO_SUBSANACIÓN` solo consume diagnósticos **con defectos**; un favorable no es consumible. Por tanto, si al revertir un desfavorable el resultado pasa a favorable, el `REQUERIMIENTO_SUBSANACIÓN` que dependía de él queda **sin justificación y sin progreso** — su destino es borrarse, no bloquea la reversión.

**Trazabilidad:** la eliminación de un diagnóstico no consumido es una corrección legítima, no una falta. Podrá registrarse en bitácora, pero qué registra la bitácora y qué no se decide en su propia sesión, ítem a ítem — fuera del alcance de este ADR.

### 6. Colapso post-producción

Al producir el diagnóstico (vínculo PRODUCIDO automático), los acordeones de los tres bloques **se colapsan a su resumen** (siguen siendo abribles). Cede espacio visible al "Resultado diagnóstico". Es una segunda señal de que la tarea está agotada. Regla: *diagnóstico producido → colapsados al entrar en edición*.

### 7. Continuidad de defectos entre vueltas

El estado de verificación es **por solicitud**, no por tarea, y es continuo entre vueltas de subsanación:

- **Documental** (`documentos_requisito`) y **técnico** (`coberturas_item_tecnico`) ya persisten por `solicitud_id` — el segundo ANALIZAR (el de `REQUERIMIENTO_SUBSANACIÓN`) ya arranca con el estado acumulado. Se matan (al casar/verificar) y nacen (al examinar lo aportado) solos.
- **Libre** (`requerimientos_tarea`) hoy es por `tarea_id` — se reinicia cada vuelta. Se **eleva a `solicitud_id`** y se le añade un campo `resuelto` (marca manual del técnico: un requerimiento libre no tiene contra qué casar, su cierre es un juicio, coherente con "la decisión jurídica es del técnico").
- El "Borrador defectos" en subsanación muestra **pendientes + resueltos** (progreso), no solo pendientes — para no tener que abrir el escrito notificado como fuente de cotejo.
- El `Diagnostico` congelado de cada vuelta es **evidencia de lo notificado** (auditoría), no insumo operativo. El insumo es el estado vivo por solicitud.

No se crea una entidad "Defecto" unificada: el ciclo de vida del defecto **emerge** de los tres ejes continuos + la vista de borrador, no se materializa en una tabla nueva.

---

## Piezas ya construidas que se reconstruyen

Este ADR no diseña de cero: **corrige lo que chirría** sobre mecanismos ya implementados. Lo que cambia en cada uno:

| Pieza | Issue original | Qué cambia con este ADR |
|---|---|---|
| Contenedor `AnalizarEditor` | #442 | Renombrado Borrador/Resultado (§1); un solo bloque (§1); resultado derivado y sin "Condicionado" (§3); colapso post-producción (§6); se retira el Pool/Despensa y el par Guardar/Cancelar muertos (ver ADR-023) |
| Check documental | #495 | Directo, fuera del gate de completitud (§4); casar ⇒ consumido derivado |
| Check técnico | #581 | Único gate de completitud, salvable con justificación (§4); sin cambios de comportamiento propio |
| Shuttle de requerimientos | #440 | Eje libre elevado a `solicitud_id` + `resuelto` (§7) |
| Modelo `Diagnostico` / `crear_diagnostico` | #392 | Reversibilidad controlada (§5) — ya no es un solo tiro inmutable |
| `ContextoSubsanacion` | #406 | Lee el estado vivo por solicitud / diagnóstico congelado como evidencia (§7) |

---

## Issues de implementación

Cuelgan de este ADR y de la enmienda de ADR-023, agrupados por coherencia (no monolíticos):

- **#677 — Rediseño semántico del inspector de ANALIZAR** — §1, §3, §4, §6 + ocultaciones. Reconstruye #442/#495/#581.
- **#678 — Reversión controlada del diagnóstico** — §5. Extiende #392, enmienda ADR-005.
- **#679 — Continuidad de defectos entre vueltas** — §7. Toca modelo (`requerimientos_tarea`), migración. Reconstruye #440.
- **#676 — Marco de edición unificado del inspector** — transversal, ver enmienda ADR-023 §5 bis.

---

## Alternativas descartadas

### A. Mantener "Defectos consolidados" como bloque automático permanente
Es el origen del error: un borrador vivo con nombre de acto de cierre. Simula que ya consolidaste sin haber hecho nada, y habilita el favorable-con-defectos. Descartada — es justo lo que este ADR corrige.

### B. Dos actos: "Consolidar" + "Producir"
Un botón intermedio que congela la foto antes de emitir. Descartada: el acto de Producir, con su confirmación de dos pasos, ya es el punto de revisión consciente. Un segundo acto es sobrecarga sin ganancia; el renombrado Borrador→Resultado (§1) da la señal de estado que se buscaba.

### C. Entidad "Defecto" unificada con ciclo de vida propio (tabla nueva)
Duplicaría lo que los tres ejes ya capturan y crearía un problema de sincronización (¿fuente de verdad o espejo?). Descartada: el ciclo de vida emerge de los tres ejes continuos por solicitud + la vista de borrador (§7).
