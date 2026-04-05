# Diseño del subsistema de fechas y plazos — BDDAT

> **Fecha:** 2026-04-01
> **Estado:** En construcción — sesión inicial de diseño.
> **Fuente de verdad:** `docs/NORMATIVA_PLAZOS.md` — todo contenido legal (plazos, artículos, constantes) extrae de ahí. En caso de discrepancia, prevalece `NORMATIVA_PLAZOS.md`.
> Referencia de arquitectura: `DISEÑO_MOTOR_AGNOSTICO.md`
> Última sincronización: 2026-04-04

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

> **Estado:** En diseño — sesión 2026-04-01 / rev. 2026-04-02.
> Decisiones 3.3, 3.5 y 3.6 cerradas. Decisiones 3.1, 3.2, 3.4, 3.7 y 3.8 pendientes de sesión específica.

---

### 3.0 Inventario de fechas en el modelo

> **Estado:** Cerrado — sesión 2026-04-01. Campos de Fase/Trámite/Tarea pendientes de revisión tipo a tipo (§3.1).

Revisión exhaustiva de todos los modelos en `app/models/` buscando campos de tipo fecha y clasificando su semántica.

#### Inventario completo

| Modelo | Campo | Tipo BD | Semántica (comment en código) | ¿Administrativa? | ¿Relevante para plazos? |
|---|---|---|---|---|---|
| `Documento` | `fecha_administrativa` | Date nullable | Fecha con efectos administrativos (firma, registro, publicación) | **Sí** — fuente absoluta de verdad | **Sí** |
| `Solicitud` | `fecha_solicitud` | Date NOT NULL | Fecha oficial de presentación — entrada en registro electrónico | **Sí** — inicio del cómputo del plazo de resolución (art. 21) | **Sí** |
| `Solicitud` | `fecha_fin` | Date nullable | Cierre voluntario de la tramitación por el usuario (fecha de hoy) | **No** — sin valor jurídico propio | **No** — semáforo para el motor de reglas: NULL indica algo pendiente |
| `Fase` | `fecha_inicio` | Date | Manual — metadato administrativo | Depende del tipo | Depende — ver §3.1 |
| `Fase` | `fecha_fin` | Date | Manual | Depende del tipo | Depende — ver §3.1 |
| `Tramite` | `fecha_inicio` | Date | Tramitación | Depende del tipo | Depende — ver §3.1 |
| `Tramite` | `fecha_fin` | Date | Tramitación | Depende del tipo | Depende — ver §3.1 |
| `Tarea` | `fecha_inicio` | Date | Tramitación, cerca del documento | Depende del tipo | Depende — ver §3.1 |
| `Tarea` | `fecha_fin` | Date | Tramitación, cerca del documento | Depende del tipo | Depende — ver §3.1 |
| `Proyecto` | `fecha` | Date NOT NULL | Fecha técnica (firma/visado) — explícitamente NO administrativa | **No** | No |
| `DireccionNotificacion` | `fecha_inicio` | Date | Inicio de vigencia de la dirección postal | No | No |
| `DireccionNotificacion` | `fecha_fin` | Date nullable | Fin de vigencia de la dirección postal | No | No |
| `HistoricoTitularExpediente` | `fecha_desde` | DateTime | Inicio de vigencia del titular — ver nota ↓ | No (no genera plazos) | No — pero sujeta a restricciones de integridad administrativa |
| `HistoricoTitularExpediente` | `fecha_hasta` | DateTime nullable | Fin de vigencia del titular — ver nota ↓ | No (no genera plazos) | No — pero sujeta a restricciones de integridad administrativa |

> **Nota — HistoricoTitularExpediente:** aunque estas fechas no generan plazos, tienen restricciones de integridad administrativa que deben validarse: (1) `fecha_hasta` del registro saliente debe coincidir con `fecha_desde` del entrante, sin huecos; (2) `fecha_desde` no puede ser anterior a la fecha del documento de resolución que motivó el cambio de titular.

#### Modelos sin campos de fecha propios

`Expediente`, `Entidad`, `AutorizadoTitular`, `FasesTramites`, `SolicitudesFases`, `ExpedientesSolicitudes`, `DocumentosProyecto`, `MotorReglas`, `Municipio`, `MunicipioProyecto`, `Plantilla`, `TiposFases`, `TiposTramites`, `TiposTareas`, `TiposSolicitudes`, `TiposExpedientes`, `TiposDocumentos`, `TiposResultadosFases`, `TiposIA`, `Usuarios`.

#### Modelos futuros

Todo modelo nuevo que incorpore campos de fecha debe declarar la semántica de cada uno en la tabla de control del mapa semántico (§3.1) desde el diseño inicial, indicando si tiene valor administrativo y qué instante del procedimiento representa.

---

### 3.1 Mapa semántico de fechas (pendiente — revisión tipo a tipo)

> **Estado:** Estructura cerrada. Contenido pendiente de revisión tipo a tipo con legislación en mano.

Las columnas `fecha_inicio`/`fecha_fin` de Fase, Trámite y Tarea **no se renombran ni se añaden columnas nuevas**. La semántica de cada fecha se almacena en una tabla BD `metadatos_fechas`, administrable por Supervisor o Admin.

#### Estructura de `metadatos_fechas`

| Campo | Tipo | Descripción |
|---|---|---|
| `tabla` | TEXT | Nombre de la tabla — `"fases"`, `"tramites"`... |
| `campo` | TEXT | Nombre del campo — `"fecha_inicio"`, `"fecha_fin"`... |
| `tipo_elemento_id` | INT nullable | FK al tipo concreto (`tipos_fases`, `tipos_tramites`, `tipos_tareas`, `tipos_solicitudes`). NULL = aplica a todos los tipos de esa tabla |
| `es_administrativa` | BOOLEAN | Si tiene valor legal para cómputo de plazos |
| `descripcion` | TEXT | Qué instante del procedimiento representa |

PK compuesta: `(tabla, campo, tipo_elemento_id)`.

La coherencia de `tipo_elemento_id` con la tabla elegida la garantiza la aplicación en dos niveles:
- **UI de Supervisión:** `tabla` se elige de una lista fija hardcodeada en Flask (cambia solo con migraciones). El desplegable de tipos se puebla dinámicamente desde la `tipos_*` correspondiente — el mapeo `tabla → tipos_tabla` son cuatro líneas en Flask.
- **Runtime (`plazos.py`):** al consultar la semántica de un campo, si no existe entrada en `metadatos_fechas` → error con alarma permanente visible al Supervisor hasta que se corrija.

El área de Supervisión incluirá una auditoría de **fechas huérfanas** (campos de fecha en el inventario §3.0 sin entrada en `metadatos_fechas`) para detección y corrección.

#### Contenido — revisión tipo a tipo (pendiente)

La clasificación de `es_administrativa` para los campos de Fase, Trámite y Tarea requiere sesión específica con la legislación en la mano (`NORMATIVA_PLAZOS.md` como fuente de verdad). En esa sesión se cruzan las fechas administrativas identificadas con los plazos del §5, lo que puede arrojar:

- Fecha administrativa sin plazo asociado → ¿correcto o hueco normativo?
- Plazo legal sin fecha administrativa en BDDAT → el sistema no puede computarlo; revisar el modelo.
- Coincidencia limpia → en orden.

Bloqueante para `plazos.py`, para la UI de aviso al tramitador y para completar `catalogo_plazos` (§3.2).

#### Nota — coherencia e imposibilidades de fechas

Al diseñar `plazos.py` (¿renombrar a `fechas_y_plazos.py`?) hay que contemplar la validación de imposibilidades lógicas entre fechas, especialmente en las parejas inicio/fin que el usuario puede rellenar manualmente o con fecha del pasado:

- `fecha_fin < fecha_inicio` — imposible en cualquier par.
- `fecha_desde` de nuevo titular anterior a `fecha_hasta` del titular saliente — hueco o solapamiento en el histórico.
- `fecha_desde` de cambio de titular anterior a la `fecha_administrativa` del documento de resolución que lo motiva.

Estos controles son de integridad administrativa, no de plazo. Deben decidirse en el diseño de `plazos.py`: si los valida ese módulo, la capa de negocio, o ambos.

---

### 3.2 Catálogo de plazos — CERRADO

> **Decisión:** Tabla separada `catalogo_plazos`, administrable por el Supervisor.

Motivación: un tipo de Fase o Trámite no tiene el plazo como atributo propio — la relación es independiente y merece una tabla puente. Permite histórico de cambios legales, múltiples plazos por tipo (por tipo de expediente o vigencia temporal), y modificación sin alterar el catálogo de tipos.

**Estructura preliminar** (sujeta a revisión cuando se cierre 3.1 y 3.2):

```
catalogo_plazos
├── id
├── tipo_elemento       ENUM(SOLICITUD, FASE, TRAMITE, TAREA)
├── tipo_elemento_id    FK → tipos_solicitudes / tipos_fases / tipos_tramites / tipos_tareas
├── campo_fecha         TEXT  -- nombre del campo que actúa como inicio de cómputo
├── plazo_valor         INTEGER
├── plazo_unidad        ENUM(DIAS_HABILES, DIAS_NATURALES, MESES, ANOS)
├── efecto_vencimiento  FK → efectos_plazo  -- (tabla; sin enums hardcodeados)
├── norma_origen        TEXT  -- "Art. 21.3 LPACAP", "Art. 14 RD 1955/2000"...
├── vigencia_desde      DATE nullable
├── vigencia_hasta      DATE nullable
└── activo              BOOLEAN
```

> La FK `efecto_vencimiento` referencia una tabla de efectos (no ENUM hardcodeado). Ver decisión §3.3 nota.

---

### 3.3 Suspensiones de plazo (pendiente)

> **Estado:** Pendiente de estudio previo.

Antes de diseñar la tabla hay que estudiar qué **eventos concretos de BDDAT** activan y cierran una suspensión, y cómo cada causa del art. 22 LPACAP tiene reflejo en el sistema. Ver `NORMATIVA_PLAZOS.md §1.1` y `DISEÑO_FECHAS_PLAZOS §2.5`.

Preguntas abiertas:
- ¿Qué acción del tramitador en BDDAT desencadena cada causa de suspensión?
- ¿La suspensión se registra explícitamente (el tramitador la abre/cierra) o se infiere del estado de algún trámite?
- ¿Las causas van en una tabla de catálogo (preferido — sin enums hardcodeados) o en ENUM?

Estructura tentativa (sujeta al estudio previo):

```
suspensiones_plazo
├── id
├── fase_id      FK nullable → fases
├── tramite_id   FK nullable → tramites
│   -- CHECK: exactamente uno de los dos NOT NULL
├── causa_id     FK → causas_suspension  -- tabla, no ENUM
├── fecha_inicio DATE  (administrativa)
├── fecha_fin    DATE nullable  -- NULL = suspensión activa
└── observaciones TEXT
```

---

### 3.4 Calendario de inhábiles (pendiente)

> **Estado:** Pendiente de decisión sobre fuente y carga.

Estructura tentativa:

```
dias_inhabiles
├── fecha        DATE  PK
├── descripcion  TEXT  -- "Día de Andalucía", "Corpus Christi (Cádiz)"...
└── ambito       FK → ambitos_inhabilidad  -- tabla: NACIONAL / AUTONOMICO_AND / PROVINCIAL_CAD / ...
```

Puntos abiertos:
- **Sede y ámbito:** la sede del órgano tramitador es Cádiz (festivos provinciales de Cádiz), pero el sistema debe ser exportable a otras provincias. Los órganos tramitadores son provinciales → los festivos aplicables son nacionales + autonómicos andaluces + provinciales del órgano concreto.
- **Fuente de datos:** verificar si la Junta de Andalucía publica el calendario de inhábiles en formato CSV o similar, desglosado por provincia. Si es así, la carga sería un script anual ejecutado por el administrador.
- **Transición de año:** los cómputos de plazo pueden aterrizar en el año siguiente. Si el calendario del año N+1 no está cargado cuando se calcula una fecha límite que cae en ese año, el sistema debe emitir un **aviso a todos los usuarios** (con especial énfasis para el administrador) para que cargue el calendario antes de que el cómputo sea necesario.

---

### 3.5 Semántica de `fecha_limite` — CERRADO

> **Estado:** Cerrado — 2026-04-02.

**Decisiones acordadas:**

1. **`fecha_limite` se recalcula siempre; nunca se almacena en BD.** Las suspensiones son dinámicas (se abren y cierran a lo largo del procedimiento), por lo que una fecha límite cacheada quedaría desfasada. El coste de recálculo es bajo.

2. **`fecha_limite` = último día hábil dentro del plazo (inclusive).** El tramitador puede actuar ese día; al día siguiente el plazo está `VENCIDO`. Las condiciones de §2.4 quedan:
   - `VENCIDO` → `hoy > fecha_limite`
   - `PROXIMO_VENCER` → `dias_habiles(hoy, fecha_limite) ≤ umbral_alerta`
   - `EN_PLAZO` → resto

3. **El conteo empieza el día siguiente al acto** (art. 30.1 LPACAP). La función recibe `fecha_acto` y arranca desde `fecha_acto + 1 día`.

4. **Días inhábiles y días en suspensión se tratan igual:** el reloj no avanza. Solo cuentan días que sean hábiles *y* estén fuera de cualquier período de suspensión activo.

5. **Suspensiones definidas por `(fecha_inicio, fecha_fin)` en días naturales, ambos extremos inclusive.** El día de inicio no cuenta (el reloj ya está parado); el día de fin tampoco (art. 22.2 LPACAP: el cómputo se reanuda "desde el día siguiente"). La semántica de `fecha_inicio` (día de notificación, de envío de consulta, etc.) depende del tipo de causa y se decide en §3.3.

El algoritmo de cálculo (`plazos.py`) se formaliza en §4.

---

### 3.6 Condicionados de resolución — nueva fase dentro de la solicitud

> **Estado:** Decisión de arquitectura cerrada — 2026-04-02. Diseño detallado pendiente.

Las resoluciones de AT pueden imponer obligaciones al administrado con plazo propio (`PRESCRIPCION_CONDICIONADO`, §2.4): presentar documentos, solicitudes concretas (p.ej. AAE), estudios, medidas correctoras, etc. El caso habitual en energía es puntual; en medio ambiente puede ser periódico (estudios de avifauna), aunque la vigilancia de esos plazos periódicos recae en medio ambiente, no en BDDAT.

**Alternativas estudiadas (2026-04-02):**

Se evaluaron tres alternativas:

1. **Nueva entidad bajo `Expediente`** al mismo nivel que `Solicitud` — descartada. Rompe el modelo ESFTT: introduce una entidad raíz que no es una solicitud, sin encaje conceptual en el vocabulario del sistema. El coste de refactorización y de explicar el modelo resultante no compensa.

2. **Solicitud de oficio con fase previa artificial** — descartada. Una `Solicitud` implica que el interesado ha iniciado algo; aquí la genera la Administración. Colapsa para condicionados que no son "presentar una solicitud" (documentos, estudios, etc.).

3. **Nueva fase dentro de la solicitud que contiene la resolución** — **elegida**. El cierre de la solicitud es manual y comprobatorio: mientras exista una fase sin cerrar, la solicitud no puede cerrarse. La fase de resolución se cierra normalmente; lo que permanece abierto es la solicitud como contenedor de la deuda. La deuda nace de la resolución, que vive dentro de la solicitud — la ubicación es semánticamente correcta.

**Decisión de arquitectura acordada:** los condicionados de resolución se modelan como **un nuevo tipo de fase** dentro de la solicitud que contiene la resolución que los impone. Esa solicitud permanece abierta hasta que la fase de cumplimiento se cierre. No se introduce ninguna entidad raíz nueva; el árbol ESFTT no cambia estructuralmente.

Pendiente de diseño:
- **Nombre y tipos de fase:** cómo se denomina la fase de cumplimiento y sus posibles variantes (presentación de solicitud, entrega de documento, estudio, etc.).
- **Plazos:** `plazos.py` debe distinguir que el sujeto del plazo es el administrado (no la Administración) — el tipo de fase determinará el régimen de cálculo.
- **Mecanismo de generación:** cómo BDDAT crea la fase al redactar la resolución y qué datos toma de ella (plazo, descripción del condicionado).
- **Reglas de colisión:** qué ocurre si se intenta abrir una nueva solicitud del mismo tipo mientras la solicitud con el condicionado pendiente sigue abierta.
- **UI:** distinción visual entre solicitud "en tramitación" y solicitud "resuelta con condicionado pendiente" para evitar confusión al tramitador.
- **Alertas:** cuándo y cómo el sistema avisa del vencimiento y asiste en la declaración de prescripción.

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

> Revisión LPACAP ejecutada sesión 2026-04-01 — arts. 73, 77, 80, 83, 88, 96 añadidos.

### 5.1 Plazos para resolver

| Constante | Valor | Referencia | Aplicación |
|---|---|---|---|
| `PLAZO_DEFECTO_MESES` | 3 meses | Art. 21.3 | Cuando la norma sectorial no fija plazo |
| `PLAZO_MAXIMO_MESES` | 6 meses | Art. 21.2 | Techo salvo ley que autorice más |
| `NOTIFICACION_DIAS` | 10 días hábiles | Art. 40.2 | Plazo para notificar al interesado desde que se dicta el acto — culmina la obligación de "resolver y notificar" |
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
| `TRAMITE_CUMPLIMIENTO_DIAS` | 10 días hábiles | Art. 73.1 | Plazo general para que el interesado cumpla cualquier trámite requerido (salvo que la norma fije otro) |
| `SUBSANACION_DIAS` | 10 días hábiles | Art. 68.1 | Plazo para subsanar deficiencias en la solicitud |
| `SUBSANACION_AMPLIACION_MAX_DIAS` | 5 días hábiles | Art. 68.2 | Ampliación máxima del plazo de subsanación |
| `AUDIENCIA_MIN_DIAS` | 10 días hábiles | Art. 82.2 | Mínimo del trámite de audiencia al interesado |
| `AUDIENCIA_MAX_DIAS` | 15 días hábiles | Art. 82.2 | Máximo del trámite de audiencia al interesado |
| `AUDIENCIA_RECURSO_MIN_DIAS` | 10 días hábiles | Art. 118.1 | Mínimo para alegaciones en recurso por hechos nuevos |
| `AUDIENCIA_RECURSO_MAX_DIAS` | 15 días hábiles | Art. 118.1 | Máximo para alegaciones en recurso por hechos nuevos |
| `ALEGACIONES_CONEXAS_MAX_DIAS` | 15 días hábiles | Art. 88.1 | Máximo para alegaciones del interesado sobre cuestiones conexas no planteadas por él |
| `CADUCIDAD_INACTIVIDAD_MESES` | 3 meses | Art. 95.1 | Inactividad del interesado → advertencia de caducidad |

### 5.4 Instrucción

| Constante | Valor | Referencia | Aplicación |
|---|---|---|---|
| `PRUEBA_MIN_DIAS` | 10 días | Art. 77.2 | Mínimo del período de prueba |
| `PRUEBA_MAX_DIAS` | 30 días | Art. 77.2 | Máximo del período de prueba |
| `INFORME_FACULTATIVO_DIAS` | 10 días | Art. 80.2 | Plazo para emitir informes facultativos (salvo que la norma fije otro) |
| `INFORMACION_PUBLICA_MIN_DIAS` | 20 días | Art. 83.2 | Mínimo del período de información pública para alegaciones |
| `TRAMITACION_SIMPLIFICADA_DIAS` | 30 días | Art. 96.6 | Plazo de resolución en tramitación simplificada |
| `TRAMITACION_SIMPLIFICADA_RECHAZO_DIAS` | 5 días | Art. 96.3 | Plazo para rechazar solicitud de tramitación simplificada; transcurrido → desestimación presunta |

### 5.5 Cómputo

| Constante | Valor | Referencia | Aplicación |
|---|---|---|---|
| `DIAS_POR_DEFECTO` | hábiles | Art. 30.2 | Días sin calificar → hábiles |
| `INICIO_COMPUTO` | día siguiente | Art. 30.3 | El cómputo empieza el día siguiente a la notificación |

---

## 5.2 Constantes sectoriales — RD 1955/2000

Plazos del Título VII RD 1955/2000 (arts. 111-139) trasladados desde `NORMATIVA_PLAZOS.md §2.2` (sesión 2026-04-04).
Estos valores son el seed del `catalogo_plazos` para las fases y trámites del procedimiento ordinario de AT.

> Los nombres de `Tipo elemento ID` son descriptivos — se ajustarán cuando se consoliden los tipos en BD (§3.1 pendiente).

#### Fases — plazo de resolución (sujeto: la Administración)

| Tipo elemento ID | Campo inicio cómputo | Valor | Unidad | Efecto vencimiento | Norma origen |
|---|---|---|---|---|---|
| RESOLUCION_AAP | fecha_solicitud (solicitud) | 3 | MESES | SILENCIO_DESESTIMATORIO | Art. 128 RD 1955/2000 |
| RESOLUCION_AAC | fecha_solicitud (solicitud) | 3 | MESES | SILENCIO_DESESTIMATORIO | Art. 131.7 RD 1955/2000 |
| RESOLUCION_AE (transporte/distribución) | fecha_solicitud (solicitud) | 1 | MESES | SILENCIO_DESESTIMATORIO | Art. 132 RD 1955/2000 + DA 3ª LSE |
| RESOLUCION_AE_PROVISIONAL (generación) | fecha_solicitud (solicitud) | 1 | MESES | SILENCIO_DESESTIMATORIO | Art. 132 bis RD 1955/2000 + DA 3ª LSE |
| RESOLUCION_AE_DEFINITIVA (generación) | fecha_solicitud (solicitud) | 1 | MESES | SILENCIO_DESESTIMATORIO | Art. 132 ter RD 1955/2000 + DA 3ª LSE |
| RESOLUCION_TRANSMISION | fecha_solicitud (solicitud) | 3 | MESES | SILENCIO_DESESTIMATORIO | Art. 133 RD 1955/2000 |
| RESOLUCION_CIERRE | fecha_solicitud (solicitud) | 3 | MESES | SILENCIO_DESESTIMATORIO | Art. 137 RD 1955/2000 |
| INFORMACION_PUBLICA | fecha_inicio | 30 | DIAS_NATURALES | SIN_EFECTO_AUTOMATICO | Art. 125 RD 1955/2000 |

> **Nota INFORMACION_PUBLICA:** trámite condicional. Suprimido bajo Decreto 9/2011 DA 1ª (AT 3ª categoría ≤ 30 kV, línea subterránea o CT interior, suelo urbano/urbanizable, sin DUP) y bajo DL 26/2021 DF 4ª (cualquier instalación del Título VII sin DUP y sin AAU). Ver `NORMATIVA_EXCEPCIONES_AT.md §3.1` y `§4.1`.

#### Plazos condicionados de resolución (sujeto: el administrado)

| Tipo elemento ID | Campo inicio cómputo | Valor | Unidad | Efecto vencimiento | Norma origen |
|---|---|---|---|---|---|
| FORMALIZACION_TRANSMISION | fecha_otorgamiento_autorizacion | 6 | MESES | PRESCRIPCION_CONDICIONADO | Art. 133 RD 1955/2000 — caducidad de la autorización de transmisión si no se formaliza |

#### Trámites — plazos de consultas y traslados

| Tipo elemento ID | Campo inicio cómputo | Valor | Unidad | Efecto vencimiento | Norma origen |
|---|---|---|---|---|---|
| TRASLADO_ALEGACIONES_AAP | fecha_inicio | 15 | DIAS_NATURALES | SIN_EFECTO_AUTOMATICO | Art. 126 RD 1955/2000 |
| INFORME_AAPP_AAP | fecha_inicio | 30 | DIAS_NATURALES | CONFORMIDAD_PRESUNTA | Art. 127 RD 1955/2000 |
| TRASLADO_CONDICIONADO_AAP | fecha_inicio | 15 | DIAS_NATURALES | SIN_EFECTO_AUTOMATICO | Art. 127 RD 1955/2000 |
| REPLICA_AAPP_AAP | fecha_inicio | 15 | DIAS_NATURALES | CONFORMIDAD_PRESUNTA | Art. 127 RD 1955/2000 |
| INFORME_AAPP_AAC | fecha_inicio | 30 | DIAS_NATURALES | CONFORMIDAD_PRESUNTA | Art. 131 RD 1955/2000 |
| INFORME_AAPP_AAC_REDUCIDO | fecha_inicio | 15 | DIAS_NATURALES | CONFORMIDAD_PRESUNTA | Art. 131 RD 1955/2000 — solo AAC sin DUP con AAP previa |
| TRASLADO_CONDICIONADO_AAC | fecha_inicio | 15 | DIAS_NATURALES | SIN_EFECTO_AUTOMATICO | Art. 131 RD 1955/2000 |
| REPLICA_AAPP_AAC | fecha_inicio | 15 | DIAS_NATURALES | CONFORMIDAD_PRESUNTA | Art. 131 RD 1955/2000 |
| INFORME_REE_CIERRE | fecha_inicio | 3 | MESES | SIN_EFECTO_AUTOMATICO | Art. 136 RD 1955/2000 — silencio: se continúa sin informe |
| INFORME_DGPEM | fecha_inicio | 2 | MESES | SIN_EFECTO_AUTOMATICO | Art. 114 RD 1955/2000 — solo instalaciones de transporte CCAA; se continúa sin informe |

> **CONFORMIDAD_PRESUNTA:** efecto del silencio de un organismo consultado — el procedimiento sigue como si hubiera conformidad expresa. Diferente del silencio estimatorio del §2.4 (que recae sobre la Administración resolutora, no sobre un organismo consultado). Añadir `CONFORMIDAD_PRESUNTA` a la tabla `efectos_plazo`.

### Ley 21/2013 — Umbrales EIA instalaciones eléctricas AT

| Constante | Valor | Norma |
|---|---|---|
| EIA_ORDINARIA_TENSION_KV | 220 kV (≥) | Ley 21/2013 Anexo I Grupo 3g |
| EIA_ORDINARIA_LONGITUD_KM | 15 km (>) | Ley 21/2013 Anexo I Grupo 3g |
| EIA_SIMPLIFICADA_TENSION_KV | 15 kV (≥) | Ley 21/2013 Anexo II Grupo 4b |
| EIA_SIMPLIFICADA_LONGITUD_KM | 3 km (>) | Ley 21/2013 Anexo II Grupo 4b |
| EIA_SIMPLIFICADA_DIST_POBLACION_M | 200 m (<) | Ley 21/2013 Anexo II Grupo 4b |
| EIA_SIMPLIFICADA_DIST_VIVIENDA_M | 100 m (<) | Ley 21/2013 Anexo II Grupo 4b |

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
- [x] **§3.0 Inventario de fechas** — cerrado sesión 2026-04-01; campos Fase/Trámite/Tarea pendientes de revisión tipo a tipo en §3.1
- [ ] **§3.1 Mapa semántico** — estructura cerrada; pendiente de: (1) completar `NORMATIVA_PLAZOS.md` con revisión LPACAP del §5, y (2) revisión tipo a tipo con legislación en mano y cruce con §5
- [ ] **§3.3 Suspensiones** — estudiar qué eventos de BDDAT desencadenan cada causa del art. 22 LPACAP antes de diseñar la tabla
- [ ] **§3.4 Calendario inhábiles** — verificar disponibilidad de datos por provincia en la Junta; diseñar mecanismo de alerta de año N+1 sin cargar
- [x] **§3.5 Semántica de `fecha_limite`** — cerrado 2026-04-02
- [ ] **§3.6 Condicionados de resolución** — diseñar nombre y tipos de fase, régimen de plazos (sujeto = administrado), mecanismo de generación desde la resolución, reglas de colisión y distinción visual en UI
- [ ] **§4 Cadena de evaluación** — formalizar contrato de interfaz `plazos.py`
- [x] **Leyes sectoriales (parcial)** — ~~RD 1955/2000~~: ✅ añadido en §5.2 (sesión 2026-04-04). ~~Decreto 9/2011~~: sin plazos propios (suprime trámite). ~~DL 26/2021~~: sin plazos propios (suprime trámite). Pendiente: Ley 21/2013 (EIA) — en revisión previa, ver `NORMATIVA_LEGISLACION_AT.md §6`.
- [ ] **Revisar #190** — determinar si el criterio `PLAZO_ESTADO` queda obsoleto o se reorienta
- [ ] **Revisar #172 y #173** — actualizar alcance según arquitectura agnóstica
- [ ] **Reutilización de trámites entre expedientes** — art. 95.3: procedimiento caducado cuyo derecho no ha prescrito permite nuevo procedimiento incorporando actos del anterior. Implica modelo de enlace entre expedientes y reutilización del pool documental. Diseñar cuando se estudie normativa sectorial.
