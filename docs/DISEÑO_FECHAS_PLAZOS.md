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
   - [2.8 Plazo condicionado de resolución propia](#28-plazo-condicionado-de-resolución-propia)
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

> **Estado:** Cerrado — sesión 2026-04-01 (rev. 2026-04-01).

---

### 2.1 Fecha

Una **fecha** es un hecho almacenado en BDDAT sobre cuándo ocurrió algo en el procedimiento.

**Fuente de verdad real:** el documento administrativo (notificación, resolución, acuse de recibo...). La transcripción a la BD puede ser automática o manual y es susceptible de error.

**Fuente de verdad operativa:** la BD. BDDAT opera sobre las fechas almacenadas asumiendo que son correctas.

#### Dos tipos de fecha

No todas las fechas de BD son iguales. Se distinguen dos categorías, que deben estar anotadas expresamente en el modelo y cuya semántica queda hardcodeada en `plazos.py`:

| Tipo | Nombre en BD | Significado | Cómo se rellena | Valor para plazos |
|---|---|---|---|---|
| **Administrativa** | `fecha_administrativa` | Fecha del acto administrativo con valor legal (notificación, firma, publicación, entrada en registro oficial) | **Siempre manual.** La UI advierte al usuario que esta fecha tiene valor legal. | **Sí** — es la única fecha válida para cómputo de plazos |
| **De tramitación** | `fecha_tramitacion` | Fecha de trabajo interno: cuándo se realizó la acción en BDDAT | Preferiblemente automática (timestamp del sistema); si no, manual sin advertencia especial | **No** — valor únicamente de seguimiento interno |

**Regla de diseño de UI:** los plazos (configuración legal) solo son accesibles al Supervisor. El tramitador solo introduce **fechas**. Los campos de `fecha_administrativa` deben mostrar un aviso explícito de que la fecha tiene valor legal. Los campos de `fecha_tramitacion` no requieren aviso especial.

#### Fechas en documentos

Un documento puede tener una fecha que tenga valor administrativo (p. ej. fecha de notificación al interesado) o solo valor decorativo (p. ej. fecha de redacción de un borrador interno). Si la fecha del documento no tiene valor administrativo, no aporta ni valor de cómputo ni de auditoría interna relevante — es un dato de descripción del documento.

> La dupla `fecha_tramitacion`/`fecha_administrativa` existe parcialmente en el modelo `Documento` (#191). Pendiente de confirmar cómo se extiende a Fase/Trámite/Tarea — ver §3.

---

### 2.2 Plazo

Un **plazo** es una restricción externa impuesta por la legislación sobre el tiempo para **resolver Y notificar** (arts. 21 y 22 LPACAP — la obligación no es solo resolver, sino notificar la resolución dentro del plazo). No es un hecho propio de BDDAT sino una norma que aplica sobre sus fechas.

**Jerarquía de fuentes:** norma sectorial > LPACAP como fallback (ver `NORMATIVA_PLAZOS.md`).

Un plazo no es solo un número. Es una **tupla** con tres elementos:

```
Plazo = (valor, unidad, asociación)
```

| Elemento | Descripción | Valores posibles |
|---|---|---|
| `valor` | Cantidad numérica | Entero positivo |
| `unidad` | Naturaleza del cómputo | `DIAS_HABILES` (defecto art. 30.2) · `DIAS_NATURALES` (debe ser expreso en la norma) · `MESES` · `ANOS` |
| `asociación` | A qué elemento ESFTT aplica | tipo de Fase · tipo de Trámite · tipo de Solicitud · tipo de recurso |

La unidad `DIAS_HABILES` es el valor por defecto cuando la norma no especifica (art. 30.2 LPACAP). `DIAS_NATURALES`, `MESES` y `ANOS` deben estar declarados expresamente en la norma.

---

### 2.3 Fecha límite efectiva

La **fecha límite** es el instante concreto hasta el cual es válido actuar. Se calcula a partir de la `fecha_administrativa` de inicio del cómputo y el plazo aplicable:

```
fecha_limite = calcular_fecha_fin(fecha_administrativa_inicio, plazo)
```

La función `calcular_fecha_fin` depende de la unidad del plazo:

| Unidad | Cálculo | Prorroga si último día inhábil |
|---|---|---|
| `DIAS_HABILES` | Suma `valor` días saltando inhábiles (calendario Junta). El último día es siempre hábil por construcción. | No aplica — imposible aterrizar en inhábil |
| `DIAS_NATURALES` | Suma `valor` días naturales. | Sí → art. 30.5: prorroga al primer día hábil siguiente |
| `MESES` | Mismo día ordinal del mes de vencimiento (art. 30.4). Si no existe ese día → último día del mes. | Sí → art. 30.5 |
| `ANOS` | Mismo día ordinal del año de vencimiento. | Sí → art. 30.5 |

> `habiles(inicio, fin)` es una función auxiliar que **cuenta** días hábiles entre dos fechas. Se usa para informar al usuario ("quedan N días hábiles"), pero **no** es la función de cómputo principal — lo es `calcular_fecha_fin`.

**Suspensiones:** la fecha límite efectiva incorpora los periodos de suspensión activos (art. 22 LPACAP) sumándolos al plazo. Ver §3 para el modelo de datos de suspensiones.

---

### 2.4 Estado de plazo y efectos

El **estado de plazo** es un valor derivado, calculado en tiempo real. No se almacena en BD.

```
estado_plazo = f(fecha_limite_efectiva, hoy())
```

| Estado | Condición | Efecto legal posible | Alerta en UI |
|---|---|---|---|
| `SIN_PLAZO` | No existe plazo legal asociado al tipo | Ninguno | Sin indicador |
| `EN_PLAZO` | `hoy() < fecha_limite - umbral_alerta` | — | Sin indicador |
| `PROXIMO_VENCER` | `fecha_limite - umbral_alerta ≤ hoy() < fecha_limite` | — | Aviso (amarillo) |
| `VENCIDO` | `hoy() ≥ fecha_limite` | Ver catálogo de efectos ↓ | Depende del efecto |

`umbral_alerta` = **5 días hábiles** (fijo).

#### Catálogo de efectos del vencimiento

El efecto del vencimiento determina la gravedad de la alerta y quién resulta perjudicado. Los efectos vienen de la LPACAP y de la norma sectorial. Se distingue si el perjudicado es la Administración o el administrado, porque la alerta en UI debe ser distinta:

| Efecto | Perjudicado | Automático | Alerta UI | Referencia |
|---|---|---|---|---|
| **Silencio estimatorio** | Administración — el acto se entiende concedido sin resolución expresa | Sí | **Crítica** (rojo) | Art. 24.1 LPACAP |
| **Responsabilidad disciplinaria** | Administración — el funcionario responde del incumplimiento | No (requiere expediente) | **Crítica** (rojo) | Art. 21.6 LPACAP |
| **Silencio desestimatorio** | Administrado — se entiende denegado, puede recurrir | Sí | Normal (naranja) | Arts. 24.1 y 25.1.a LPACAP |
| **Caducidad del procedimiento** | Administrado — se archivan las actuaciones por inactividad | No (requiere advertencia previa + resolución) | Normal (naranja) | Art. 95.1 LPACAP — **aplica en BDDAT**: inactividad del interesado > 3 meses |
| **Pérdida de trámite** | Administrado — pierde un trámite no indispensable, no el procedimiento | Sí | Normal (naranja) | Art. 95.2 LPACAP |
| **Apertura de recurso** | Ninguno directamente — abre la vía impugnatoria | Sí | Normal (naranja) | Arts. 122, 124 LPACAP |
| **Prescripción del derecho condicionado** | Administrado — el derecho otorgado por resolución propia caduca | No (requiere declaración) | Normal (naranja) | Ver §2.8 |
| **Sin efecto automático** | Ninguno — plazo de trámite interno sin consecuencia legal directa | No | Normal (naranja) | — |

> **Art. 25.1.b** (caducidad de procedimientos de oficio): no aplica en BDDAT — todos los expedientes son a instancia de parte. Si en el futuro se incorporan procedimientos de oficio, revisar.

> **Art. 95 — Caducidad por inactividad del interesado**: aplica íntegramente en BDDAT. El flujo es: inactividad > 3 meses → la Administración advierte → si persiste → resolución de archivo. Un procedimiento caducado no interrumpe la prescripción del derecho, pero si el derecho no ha prescrito, el interesado puede iniciar un nuevo procedimiento incorporando actos y trámites del anterior (ver §7 — reutilización de trámites entre expedientes).

El estado y el efecto se exponen como variables separadas del ContextAssembler:
- `estado_plazo`: `SIN_PLAZO` / `EN_PLAZO` / `PROXIMO_VENCER` / `VENCIDO`
- `efecto_plazo`: `NINGUNO` / `SILENCIO_ESTIMATORIO` / `RESPONSABILIDAD_DISCIPLINARIA` / `SILENCIO_DESESTIMATORIO` / `CADUCIDAD_PROCEDIMIENTO` / `PERDIDA_TRAMITE` / `APERTURA_RECURSO` / `PRESCRIPCION_CONDICIONADO` / `SIN_EFECTO_AUTOMATICO`

---

### 2.5 Suspensión del plazo

El plazo se **suspende** cuando concurre alguna de las causas del art. 22 LPACAP (ver `NORMATIVA_PLAZOS.md §1.1`). El reloj se para; el tiempo transcurrido antes se conserva; al reanudar se suma el periodo suspendido a la fecha límite.

> El art. 25.2 LPACAP habla de "interrupción" del cómputo por paralización imputable al interesado, pero dicho artículo no aplica en BDDAT (regula procedimientos de oficio, que no existen en el sistema). Se elimina la distinción suspensión/interrupción como irrelevante para BDDAT.

---

### 2.6 Régimen transitorio y procedimientos iniciados

**El problema:** cuando una norma nueva modifica plazos o exime de un procedimiento sin disposición transitoria expresa, no está claro qué aplica a procedimientos ya iniciados. El principio general (DT3ª-a LPACAP) dice que se sigue con la normativa anterior, lo que puede generar situaciones absurdas cuando la nueva norma es más favorable al administrado.

**Criterio de BDDAT:** no se procedimenta esta casuística. Cuando el tramitador necesite apartarse de las reglas por cambio normativo sin transitorio, usará la **puerta de escape del motor de reglas** (ya prevista) y lo anotará en el **cuaderno de bitácora** del expediente con la justificación. La responsabilidad jurídica de la decisión recae en el técnico tramitador, no en el sistema.

---

### 2.7 Retroactividad y tramitación simplificada

**Art. 39.3 LPACAP — Retroactividad:**
Permite otorgar eficacia retroactiva a actos favorables al interesado. Implicación para BDDAT: `fecha_administrativa_inicio` puede ser anterior a `fecha_tramitacion` (p. ej. inicio de fase resolución con fecha de resolución retroactiva). El sistema debe aceptar esa situación. La justificación queda en el cuaderno de bitácora y en el propio cuerpo de la resolución.

**Art. 96 LPACAP — Tramitación simplificada:**
Plazo especial de 30 días desde el acuerdo de tramitación simplificada. Sin casos reales conocidos en AT andaluz desde 2015. Pendiente de decisión sobre si merece implementación — documentar en issue cuando surja necesidad real.

---

### 2.8 Plazo condicionado de resolución propia

Un tipo de plazo que no proviene de ningún catálogo legal externo: es el que **BDDAT genera al emitir una resolución con condicionados**.

La palabra "prescribir" tiene aquí doble acepción (RAE):
- La resolución **prescribe** (ordena) que el interesado realice algo en un plazo máximo.
- Si no lo hace, el derecho otorgado **prescribe** (caduca).

**Ejemplo típico en AT:** una resolución de autorización dice "deberá presentar el certificado de fin de obra en un plazo máximo de X meses desde la notificación de la presente resolución". Si no se presenta, la autorización otorgada puede declararse prescrita.

Este plazo tiene características propias que lo diferencian de los plazos del catálogo:

| Característica | Plazo legal (catálogo) | Plazo condicionado de resolución |
|---|---|---|
| **Origen** | Norma sectorial o LPACAP | La propia resolución dictada por BDDAT |
| **Almacenamiento** | Tabla de plazos configurada por Supervisor | Se genera al redactar la resolución — pendiente de diseño (§3) |
| **Sujeto del plazo** | La Administración (para resolver/notificar) | El administrado (para cumplir el condicionado) |
| **Efecto del vencimiento** | Silencio, caducidad del procedimiento... | Prescripción del derecho — requiere declaración expresa |
| **¿Automático?** | Según el efecto (ver §2.4) | No — requiere acto administrativo de declaración |

El efecto `PRESCRIPCION_CONDICIONADO` del catálogo §2.4 corresponde a este tipo.

> Pendiente de diseño: cómo se almacena y vincula este plazo al expediente (§3), y cuándo y cómo BDDAT genera la alerta de vencimiento y asiste al tramitador en la declaración de prescripción.

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

### 5.3 Plazos para el administrado

Plazos que la LPACAP impone al administrado en su relación con la Administración:

| Constante | Valor | Referencia | Aplicación |
|---|---|---|---|
| `SUBSANACION_DIAS` | 10 días hábiles | Art. 68.1 | Plazo para subsanar deficiencias en la solicitud |
| `SUBSANACION_AMPLIACION_MAX_DIAS` | 5 días hábiles | Art. 68.2 | Ampliación máxima del plazo de subsanación |
| `AUDIENCIA_MIN_DIAS` | 10 días hábiles | Art. 82.2 | Mínimo del trámite de audiencia al interesado |
| `AUDIENCIA_MAX_DIAS` | 15 días hábiles | Art. 82.2 | Máximo del trámite de audiencia al interesado |
| `AUDIENCIA_RECURSO_MIN_DIAS` | 10 días hábiles | Art. 118.1 | Mínimo para alegaciones en recurso por hechos nuevos |
| `AUDIENCIA_RECURSO_MAX_DIAS` | 15 días hábiles | Art. 118.1 | Máximo para alegaciones en recurso por hechos nuevos |
| `CADUCIDAD_INACTIVIDAD_MESES` | 3 meses | Art. 95.1 | Inactividad del interesado → advertencia de caducidad |

### 5.4 Cómputo

| Constante | Valor | Referencia | Aplicación |
|---|---|---|---|
| `DIAS_POR_DEFECTO` | hábiles | Art. 30.2 | Días sin calificar → hábiles |
| `INICIO_COMPUTO` | día siguiente | Art. 30.3 | El cómputo empieza el día siguiente a la notificación |

---

## 6. Issues derivados

> Se crearán una vez definidos §2, §3 y §4.

Issues preexistentes relacionados (pendientes de revisar contra este diseño):
- **#172** — Plazos legales en días hábiles con calendario de festivos
- **#173** — Suspensión de plazos legales
- **#190** — Criterio `PLAZO_ESTADO` en motor *(probablemente obsoleto con rediseño agnóstico)*

---

## 7. Deudas y pendientes

- [x] **§2 Conceptos** — cerrado sesión 2026-04-01
- [ ] **§3 Modelo de datos** — sesión de diseño pendiente
- [ ] **§4 Cadena de evaluación** — formalizar contrato de interfaz `plazos.py`
- [ ] **Leyes sectoriales** — extraer plazos de RD 1955/2000, Decreto 9/2011, Ley 21/2013, Decreto-ley 26/2021 (ver `NORMATIVA_PLAZOS.md §2`)
- [ ] **Revisar #190** — determinar si el criterio `PLAZO_ESTADO` queda obsoleto o se reorienta
- [ ] **Revisar #172 y #173** — actualizar alcance según arquitectura agnóstica
- [ ] **Reutilización de trámites entre expedientes** — art. 95.3: procedimiento caducado cuyo derecho no ha prescrito permite nuevo procedimiento incorporando actos del anterior. Implica modelo de enlace entre expedientes y reutilización del pool documental. Diseñar cuando se estudie normativa sectorial.
