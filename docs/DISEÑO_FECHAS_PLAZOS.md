# Diseño del subsistema de fechas y plazos — BDDAT

> **Fecha:** 2026-04-01
> **Estado:** En construcción — sesión inicial de diseño.
> **Fuente de verdad:** `docs/NORMATIVA_PLAZOS.md` — todo contenido legal (plazos, artículos, constantes) extrae de ahí. En caso de discrepancia, prevalece `NORMATIVA_PLAZOS.md`.
> Referencia de arquitectura: `DISEÑO_MOTOR_AGNOSTICO.md`
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

> **Estado:** En diseño — sesión 2026-04-01.
> Decisiones 3.3 y 3.6 cerradas. Decisiones 3.1, 3.2, 3.4, 3.5, 3.7 y 3.8 pendientes de sesión específica.

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

> **Decisión:** `fecha_limite` se **recalcula siempre**; nunca se almacena en BD.

Las suspensiones son dinámicas (se abren y cierran con el procedimiento en curso), por lo que una fecha límite cacheada quedaría desfasada inmediatamente. El coste de recálculo es bajo.

Pendiente aún de cerrar: ¿es `fecha_limite` el **último día dentro de plazo** (inclusive, el tramitador puede actuar ese día) o el **primer día fuera de plazo** (límite+1)? Esta decisión afecta a las condiciones del estado `VENCIDO` de §2.4 y debe cerrarse antes de implementar `plazos.py`.

---

### 3.6 Nueva entidad: condicionado de resolución (pendiente)

> **Estado:** Pendiente de diseño y nombre definitivo.

Las resoluciones de AT imponen obligaciones al administrado con plazo propio (`PRESCRIPCION_CONDICIONADO`, §2.4). Estas obligaciones se escapan del árbol ESFTT actual: no las inicia el administrado (no son `Solicitud`), sino que las genera la Administración de oficio al dictar la resolución.

**Decisión de arquitectura acordada:** crear una nueva entidad al mismo nivel que `Solicitud` bajo `Expediente`, generada de oficio. Tendrá su propia jerarquía FTT (Fases, Trámites, Tareas). El motor, `ContextAssembler` y `plazos.py` la tratarán sin distinción respecto a las demás entidades ESFTT.

Pendiente:
- **Nombre de la entidad:** ¿`Condicionado`? ¿`Obligacion`? A decidir en próxima sesión.
- **Modelo de datos** de la entidad y sus FTT asociados.
- **Mecanismo de generación:** cómo BDDAT crea la instancia al redactar la resolución.
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

> ⚠ **Revisión pendiente:** dar otro repaso a la LPACAP buscando plazos definidos (términos: "plazo", "días", "diez", "quince", "meses", etc.) para verificar que no falta ninguna constante. Excluir los títulos de responsabilidad patrimonial, procedimiento sancionador y los artículos que modifican otras leyes.

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
- [x] **§3.0 Inventario de fechas** — cerrado sesión 2026-04-01; campos Fase/Trámite/Tarea pendientes de revisión tipo a tipo en §3.1
- [ ] **§3.1 Mapa semántico** — estructura cerrada; pendiente revisión tipo a tipo con legislación en mano y cruce con §5
- [ ] **§3.3 Suspensiones** — estudiar qué eventos de BDDAT desencadenan cada causa del art. 22 LPACAP antes de diseñar la tabla
- [ ] **§3.4 Calendario inhábiles** — verificar disponibilidad de datos por provincia en la Junta; diseñar mecanismo de alerta de año N+1 sin cargar
- [ ] **§3.5 Semántica exacta de `fecha_limite`** — ¿último día válido (inclusive) o primer día fuera de plazo?; bloqueante para implementar `plazos.py`
- [ ] **§3.6 Nombre y modelo del condicionado de resolución** — decidir nombre (`Condicionado`/`Obligacion`/otro) y diseñar la entidad y su jerarquía FTT
- [ ] **§4 Cadena de evaluación** — formalizar contrato de interfaz `plazos.py`
- [ ] **Leyes sectoriales** — extraer plazos de RD 1955/2000, Decreto 9/2011, Ley 21/2013, Decreto-ley 26/2021 (ver `NORMATIVA_PLAZOS.md §2`)
- [ ] **Revisar #190** — determinar si el criterio `PLAZO_ESTADO` queda obsoleto o se reorienta
- [ ] **Revisar #172 y #173** — actualizar alcance según arquitectura agnóstica
- [ ] **Reutilización de trámites entre expedientes** — art. 95.3: procedimiento caducado cuyo derecho no ha prescrito permite nuevo procedimiento incorporando actos del anterior. Implica modelo de enlace entre expedientes y reutilización del pool documental. Diseñar cuando se estudie normativa sectorial.
