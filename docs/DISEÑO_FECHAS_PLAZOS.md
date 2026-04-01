# Diseño del subsistema de fechas y plazos — BDDAT

> **Fecha:** 2026-04-01
> **Estado:** En construcción — sesión inicial de diseño.
> Complementa `NORMATIVA_PLAZOS.md` (marco legal) y `DISEÑO_MOTOR_AGNOSTICO.md` (arquitectura del motor).
> Fuente de verdad: `docs/NORMATIVA_PLAZOS.md`
> Última sincronización: 2026-04-01

---

## Índice

1. [Contexto y motivación](#1-contexto-y-motivación)
2. [Conceptos y vocabulario](#2-conceptos-y-vocabulario)
   - [2.1 Fecha](#21-fecha)
   - [2.2 Plazo](#22-plazo)
   - [2.3 Fecha límite efectiva](#23-fecha-límite-efectiva)
   - [2.4 Estado de plazo de un elemento ESFTT](#24-estado-de-plazo-de-un-elemento-esftt)
   - [2.5 Suspensión vs. interrupción](#25-suspensión-vs-interrupción)
   - [2.6 Zona gris: régimen transitorio](#26-zona-gris-régimen-transitorio-y-procedimientos-iniciados)
   - [2.7 Retroactividad y tramitación simplificada](#27-retroactividad-y-tramitación-simplificada-en-relación-con-plazos)
3. [Modelo de datos](#3-modelo-de-datos)
4. [Cadena de evaluación](#4-cadena-de-evaluación)
5. [Constantes LPACAP — valores de fallback](#5-constantes-lpacap--valores-de-fallback)
6. [Issues derivados](#6-issues-derivados)
7. [Deudas y pendientes](#7-deudas-y-pendientes)

---

## 1. Contexto y motivación

Los plazos administrativos afectan a BDDAT en tres niveles:

1. **Datos** — dónde se almacenan las fechas de inicio, fin, suspensiones y plazos legales.
2. **Lógica** — `plazos.py` calcula fechas límite efectivas (descontando inhábiles y suspensiones) y expone el estado del plazo.
3. **Motor** — `ContextAssembler` solicita a `plazos.py` las variables de plazo y las pasa al motor agnóstico como parte del contexto de evaluación.

Issues de referencia previos: **#172** (plazos en días hábiles), **#173** (suspensión de plazos), **#190** (criterio `PLAZO_ESTADO` en motor). Con el rediseño agnóstico (#190 queda obsoleto: ya no hay criterio `PLAZO_ESTADO` en el motor — `plazos.py` computa el estado y lo pasa como variable).

---

## 2. Conceptos y vocabulario

> **Estado:** Cerrado — sesión 2026-04-01.

---

### 2.1 Fecha

Una **fecha** es un hecho registrado en BDDAT sobre cuándo ocurrió algo en el procedimiento.

**Fuente de verdad real:** el documento administrativo (notificación, resolución, acuse de recibo...). La transcripción a la BD puede ser automática o manual y es susceptible de error.

**Fuente de verdad operativa:** la BD. BDDAT opera sobre las fechas almacenadas, asumiendo que son correctas. Cualquier discrepancia con el documento es un problema de calidad de datos, no de lógica del sistema.

**No todas las fechas de BD son válidas para cómputo de plazos.** Las fechas operativas relevantes para plazos son siempre la fecha del acto administrativo que inicia o cierra el cómputo — no la fecha de registro en BD. Esto requiere una **dupla**:

| Campo | Significado | Ejemplo |
|---|---|---|
| `fecha_registro` | Cuándo se introdujo el dato en BDDAT | Hoy, mientras tramita el técnico |
| `fecha_administrativa` | Fecha del acto administrativo (notificación, firma, publicación...) | La fecha que figura en el documento |

El cómputo de plazos usa siempre `fecha_administrativa`. `fecha_registro` es auditoría interna.

> Esta dupla ya existe parcialmente en el modelo `Documento` (#191). Pendiente de confirmar si se extiende a Fase/Trámite/Tarea o si se resuelve por referencia al documento asociado.

---

### 2.2 Plazo

Un **plazo** es una restricción externa impuesta por la legislación. No es un hecho propio de BDDAT sino una norma que aplica sobre sus fechas.

**Jerarquía de fuentes:** norma sectorial > LPACAP como fallback (ver `NORMATIVA_PLAZOS.md`).

Un plazo no es solo un número. Es una **tupla** con tres elementos:

```
Plazo = (valor, unidad, asociación)
```

| Elemento | Descripción | Valores posibles |
|---|---|---|
| `valor` | Cantidad numérica | Entero positivo |
| `unidad` | Naturaleza del cómputo | `DIAS_HABILES` (defecto LPACAP art. 30.2) · `DIAS_NATURALES` (debe ser expreso) · `MESES` · `ANOS` |
| `asociación` | A qué elemento ESFTT aplica | tipo de Fase · tipo de Trámite · tipo de Solicitud · tipo de recurso |

La unidad `DIAS_HABILES` es el valor por defecto cuando la norma no especifica (art. 30.2 LPACAP). `DIAS_NATURALES` y `MESES` deben estar declarados expresamente en la norma.

---

### 2.3 Fecha límite efectiva

La **fecha límite** es el instante concreto hasta el cual es válido actuar. Se calcula a partir de la fecha de inicio del cómputo y el plazo aplicable:

```
fecha_limite = calcular_fecha_fin(fecha_administrativa_inicio, plazo)
```

La función `calcular_fecha_fin` depende de la unidad del plazo:

| Unidad | Cálculo |
|---|---|
| `DIAS_HABILES` | Suma `valor` días hábiles usando el calendario de inhábiles de la Junta. Último día inhábil → prorroga al siguiente hábil (art. 30.5). |
| `DIAS_NATURALES` | Suma `valor` días naturales. Último día inhábil → **no** prorroga (son naturales). |
| `MESES` | Mismo día ordinal del mes de vencimiento (art. 30.4). Si no existe ese día en el mes → último día del mes. |
| `ANOS` | Mismo día ordinal del año de vencimiento. |

> `hábiles(inicio, fin)` es una función auxiliar que cuenta días hábiles entre dos fechas. La necesitamos para informar al usuario ("quedan N días hábiles"), pero **no** es la función principal de cómputo — lo es `calcular_fecha_fin`.

**Suspensiones:** la fecha límite efectiva descuenta los periodos de suspensión activos (art. 22 LPACAP). Ver §3 para el modelo de datos de suspensiones.

---

### 2.4 Estado de plazo de un elemento ESFTT

El **estado de plazo** es un valor derivado, calculado en tiempo real. No se almacena en BD.

```
estado_plazo = f(fecha_limite_efectiva, hoy())
```

| Estado | Condición | Uso |
|---|---|---|
| `SIN_PLAZO` | No existe plazo legal asociado al tipo | Elemento sin restricción temporal |
| `EN_PLAZO` | `hoy() < fecha_limite - umbral_alerta` | Normal |
| `PROXIMO_VENCER` | `fecha_limite - umbral_alerta ≤ hoy() < fecha_limite` | Alerta visual en UI y semáforo |
| `VENCIDO` | `hoy() ≥ fecha_limite` | Alerta crítica; posible silencio o caducidad |

`umbral_alerta` es configurable (propuesta: 10 días hábiles por defecto).

El estado se expone como variable del ContextAssembler para que el motor pueda evaluarlo como condición sin conocer la lógica de fechas.

---

### 2.5 Suspensión vs. interrupción

| Concepto | Efecto sobre el cómputo | Referencia LPACAP |
|---|---|---|
| **Suspensión** | El reloj se para. El tiempo transcurrido antes se conserva. Al reanudar, se suma el periodo suspendido. | Art. 22 |
| **Interrupción** | El cómputo se reinicia desde cero. | Art. 25.2 (paralización por causa del interesado) |

---

### 2.6 Zona gris: régimen transitorio y procedimientos iniciados

> **Estado:** Pendiente de decisión de criterio propio. No implementar hasta cerrar este punto.

**El problema:** cuando una norma nueva modifica plazos o exime de un procedimiento y no incluye disposición transitoria expresa, no está claro qué aplica a los procedimientos ya iniciados.

**Referencia general:** Disposición Transitoria 3ª LPACAP, apartado a):
> *"A los procedimientos ya iniciados antes de la entrada en vigor de la Ley no les será de aplicación la misma, rigiéndose por la normativa anterior."*

Y el apartado e) como cláusula de cierre para lo no previsto.

**La paradoja:** este principio (*tempus regit actum* — el procedimiento se rige por la ley vigente al inicio) genera situaciones absurdas cuando la norma nueva es más favorable al administrado. Ejemplo: si una ley posterior elimina un procedimiento por completo (porque los mismos efectos se obtienen por otro medio), la DT3ª-a) obliga a seguir tramitando el procedimiento obsoleto.

En la práctica del mundillo administrativo de AT andaluz, esto se resuelve caso a caso sin criterio uniforme.

**Decisión pendiente para BDDAT:** definir si el sistema permite marcar un procedimiento como "tramitado bajo normativa X" y qué ocurre cuando X cambia. Opciones:
1. Congelar el plazo asociado a la norma vigente en la fecha de inicio (inmutable histórico).
2. Permitir al Supervisor actualizar manualmente el plazo aplicable a un expediente concreto.
3. Combinación: congelado por defecto, editable con justificación auditada.

---

### 2.7 Retroactividad y tramitación simplificada (en relación con plazos)

**Art. 39.3 LPACAP — Retroactividad:**
Permite otorgar eficacia retroactiva a actos que produzcan efectos favorables al interesado, siempre que los supuestos de hecho existieran ya en la fecha de retroacción y no se lesionen derechos de terceros. Implicación para plazos: una resolución retroactiva puede reabrir o cerrar periodos de cómputo en fechas pasadas — `calcular_fecha_fin` debe soportar `fecha_administrativa_inicio` anterior a `fecha_registro`.

**Art. 96 LPACAP — Tramitación simplificada:**
Plazo máximo de resolución: **30 días** desde la notificación del acuerdo de tramitación simplificada (salvo que reste menos para la ordinaria). Suspensión automática si se solicita Dictamen al Consejo de Estado (apartado g). Implicación: el plazo aplicable puede cambiar a mitad del procedimiento si se acuerda tramitación simplificada — el sistema debe poder reasignar el plazo sin perder el historial del cómputo anterior.

---

## 3. Modelo de datos

> **Estado:** Pendiente de sesión de diseño.

Preguntas abiertas:
- ¿Dónde se almacena el plazo legal aplicable a cada tipo de Fase/Trámite? (¿tabla `tipos_fase`, config externa, BD?)
- ¿Cómo se registran los periodos de suspensión? (tabla `suspensiones_plazo` ligada a Fase/Trámite)
- ¿Dónde vive el calendario de inhábiles de la Junta de Andalucía?
- ¿Se almacena la fecha límite calculada o se recalcula siempre?

---

## 4. Cadena de evaluación

> **Estado:** Pendiente de sesión de diseño.

Arquitectura acordada en conversación (2026-04-01):

```
Motor agnóstico (evalúa variables, no conoce plazos)
    ↑  variables: plazo_vencido, dias_transcurridos, fecha_limite, silencio_producido...
ContextAssembler
    ↑  llama a plazos.py para obtener variables de plazo
plazos.py
    ├── Norma sectorial → plazo específico por tipo de Fase/Trámite
    │       Si no hay respuesta ↓
    └── Fallback LPACAP (constantes §5)
    +
    ├── Tabla suspensiones_plazo (periodos activos)
    └── Calendario inhábiles Junta de Andalucía
```

Pendiente de formalizar: contrato de interfaz de `plazos.py` (qué recibe, qué devuelve).

---

## 5. Constantes LPACAP — valores de fallback

Valores extraídos del texto consolidado de la Ley 39/2015 (sesión 2026-04-01).
Fuente detallada: `NORMATIVA_PLAZOS.md §1`.

### 5.1 Plazos para resolver

| Constante | Valor | Referencia | Aplicación |
|---|---|---|---|
| `PLAZO_DEFECTO_MESES` | 3 meses | Art. 21.3 | Cuando la norma sectorial no fija plazo |
| `PLAZO_MAXIMO_MESES` | 6 meses | Art. 21.2 | Techo salvo ley que autorice más |
| `SUSPENSION_INFORME_PRECEPTIVO_MAX_MESES` | 3 meses | Art. 22.1.d | Suspensión por informe a otro órgano |
| `SILENCIO_SUSPENSION_MESES` | 1 mes | Art. 117.3 | Silencio positivo en solicitud de suspensión de recurso |

### 5.2 Plazos de recursos

| Constante | Valor | Referencia | Aplicación |
|---|---|---|---|
| `ALZADA_INTERPOSICION_MESES` | 1 mes | Art. 122.1 | Plazo para interponer recurso de alzada (acto expreso) |
| `ALZADA_RESOLUCION_MESES` | 3 meses | Art. 122.2 | Plazo para resolver recurso de alzada |
| `REPOSICION_INTERPOSICION_MESES` | 1 mes | Art. 124.1 | Plazo para interponer recurso de reposición |
| `REPOSICION_RESOLUCION_MESES` | 1 mes | Art. 124.2 | Plazo para resolver recurso de reposición |
| `REVISION_INTERPOSICION_ANOS_ERROR_HECHO` | 4 años | Art. 125.2 | Revisión extraordinaria, causa error de hecho |
| `REVISION_INTERPOSICION_MESES_RESTO` | 3 meses | Art. 125.2 | Revisión extraordinaria, resto de causas |
| `REVISION_RESOLUCION_MESES` | 3 meses | Art. 126.3 | Plazo para resolver revisión extraordinaria |

### 5.3 Cómputo

| Constante | Valor | Referencia | Aplicación |
|---|---|---|---|
| `DIAS_POR_DEFECTO` | hábiles | Art. 30.2 | Días sin calificar → hábiles |
| `INICIO_COMPUTO` | día siguiente | Art. 30.3 | El cómputo empieza el día siguiente a la notificación |
| `AUDIENCIA_RECURSO_MIN_DIAS` | 10 días | Art. 118.1 | Mínimo para alegaciones en recurso por hechos nuevos |
| `AUDIENCIA_RECURSO_MAX_DIAS` | 15 días | Art. 118.1 | Máximo para alegaciones en recurso por hechos nuevos |

---

## 6. Issues derivados

> Se crearán una vez definidos §2, §3 y §4.

Issues preexistentes relacionados (pendientes de revisar contra este diseño):
- **#172** — Plazos legales en días hábiles con calendario de festivos
- **#173** — Suspensión de plazos legales
- **#190** — Criterio `PLAZO_ESTADO` en motor *(probablemente obsoleto con rediseño agnóstico)*

---

## 7. Deudas y pendientes

- [x] **§2 Conceptos** — cerrado sesión 2026-04-01 (pendiente: decisión §2.6 régimen transitorio)
- [ ] **§3 Modelo de datos** — sesión de diseño pendiente
- [ ] **§4 Cadena de evaluación** — formalizar contrato de interfaz `plazos.py`
- [ ] **Leyes sectoriales** — extraer plazos de RD 1955/2000, Decreto 9/2011, Ley 21/2013, Decreto-ley 26/2021 (ver `NORMATIVA_PLAZOS.md §2`)
- [ ] **Revisar #190** — determinar si el criterio `PLAZO_ESTADO` queda obsoleto o se reorienta
- [ ] **Revisar #172 y #173** — actualizar alcance según arquitectura agnóstica
