# ADR-026 — La vigencia normativa es una propiedad de la regla, no de la variable

**Estado:** Adoptada
**Fecha:** 2026-06-18
**Issue:** #556 (efecto colateral detectado durante el diseño) · #561 (implementación del drop de `activa` y la red de seguridad)
**Relacionado con:** ADR-001 (motor agnóstico) · ADR-025 (#553, ensamblador del escrito). Fuentes de verdad afectadas: `docs/referencia/DISEÑO_CONTEXT_ASSEMBLER.md` y el modelo `app/models/motor_reglas.py`.

---

## Contexto

Al abordar #556 (exponer las variables del motor en las plantillas de escritos) se cuestionó qué significaba que una variable pudiera "estar activa o no", y en concreto el valor `obsoleta = (norma derogada, …)` del eje **Estado** del diccionario de variables (`DISEÑO_CONTEXT_ASSEMBLER.md`).

El modelo mental implícito era: *la variable nace de una norma; si la norma se deroga, la variable se obsoleta.* Es un **error conceptual**:

1. **Una variable es un hecho del expediente** — una realidad física (tensión, longitud, subterránea) o administrativa (tiene AAU, es PTD) — **evaluable con independencia de qué norma esté vigente**. Que la norma que dio origen al concepto se derogue no impide ni desaconseja medir la realidad.
2. **Una variable puede alimentar varias reglas de normas distintas.** El propio diccionario ya lo refleja: `tension_nominal_kv` cita Decreto 9/2011 + RD 337/2014; `requiere_aau` cita D356/2010 + DL 26/2021 + Ley 2/2026. Atar la vida de la variable a "su" norma es incoherente: si se deroga una de ellas pero otra regla sobre la misma variable sigue vigente, desactivar la variable rompería esa segunda regla.
3. **La derogación no es retroactiva** a los expedientes en curso. El sistema ya modela transitoriedad por fecha (p. ej. `fecha_inicio_expediente_ambiental` discrimina GICA vs Ley 2/2026). Mientras haya expedientes bajo la norma anterior, ni la regla está muerta ni, mucho menos, su variable.
4. **Dejar de evaluar una variable no es neutro, es descontrolado.** Si una variable pasara a `null`, las actuaciones del motor condicionadas a su `true` se dejarían de bloquear (la condición ya no se cumple) y, en las plantillas, un fragmento gobernado por `true`/`false` quedaría en estado incierto. La ausencia de cómputo no equivale a "no aplica".

La vigencia normativa, por tanto, es una propiedad de la **decisión** (la regla), no del **hecho** (la variable). El modelo ya lo soporta: `reglas_motor.activa` y `excepciones_motor.activa` existen precisamente para desactivar reglas preservando trazabilidad; `obsoleta` como estado de variable nunca llegó a existir en BD — vivía solo en el documento.

---

## Decisión

### 1. La vigencia normativa es de la regla, nunca de la variable

Cuando una norma se deroga: se desactiva la **regla** (`reglas_motor.activa = false`) y/o se crea la regla complementaria. La variable **se sigue computando igual**. El "uso" de una variable (qué reglas o plantillas la referencian) es derivado e informativo: **nunca impide computarla**.

### 2. Se elimina `obsoleta` como estado de variable

El eje **Estado** del diccionario refleja **un único eje: la implementación** (de papel a código): `definida` → `pendiente de implementar` → `implementada`. Se retira el valor `obsoleta = (norma derogada)`. Si en algún caso extremo una variable hubiera de retirarse, el disparador sería que **el concepto desaparece del dominio** (se elimina el campo del modelo, deja de existir la distinción) **y** ningún consumidor la usa — **nunca** la derogación de una norma.

### 3. `norma_id` de la variable es documental

Indica dónde apareció el concepto; puede ser múltiple. **No es dueña del ciclo de vida** de la variable. Que una de esas normas se derogue no la afecta.

### 4. `catalogo_variables.activa` no es vigencia (y su drop se trata aparte)

El flag `activa` **no codifica vigencia normativa**: es la **compuerta de implementación** ("¿existe la función en el Variable Registry?"). La verificación durante #556 mostró que **es portante** (filtra `build()` en `app/services/assembler.py:183`), no vestigial como se había supuesto. Su posible eliminación —y la red de seguridad que debe acompañarla— se decide en **#561**, no en este ADR.

### 5. La red de seguridad vive en los tests, no en un registro de usos

La protección contra romper consumidores (reglas y, sobre todo, plantillas) al borrar el código de cómputo de una variable se construye con **tests de existencia/resolubilidad** sobre conjuntos enumerables (registry, consultas nombradas, plantillas registradas), no con un registro de qué plantilla usa qué variable (ataría la libertad de creación). Detalle y alcance en **#561**.

---

## Consecuencias

- **`DISEÑO_CONTEXT_ASSEMBLER.md`** se actualiza: eje Estado sin `obsoleta`, recuadro de principio (vigencia = regla; la variable se computa siempre; `null` = descontrolado), `norma_id` documental, y la descripción de `build()` ajustada a la realidad (consulta `catalogo_variables` con `activa=True` e invoca el registry).
- **#556** se corrige: la afirmación de su cuerpo de que `activa` es "vestigial / todas `true` / drift de doc a ajustar a la realidad" era **inexacta** — el flag es portante.
- **No hay cambio de esquema en este ADR.** El drop de la columna `activa` y la red de tests son **#561**.

---

## Alternativas descartadas

### A. Mantener `obsoleta` como estado de la variable

Confunde la vigencia (propiedad de la regla) con la existencia (propiedad de la variable) y rompe el caso real de variables compartidas por varias normas: derogar una desactivaría una variable que otra regla vigente todavía necesita.

### B. Registro variable↔plantilla para detectar consumidores

Llevar un registro de qué plantilla usa qué variable ataría la libertad de creación de plantillas (se crean como parte del trabajo diario, sin intervención del programador). La red correcta son tests de existencia (variables + consultas) y de resolubilidad de tokens (plantillas, que **sí** son enumerables) — ver #561.
