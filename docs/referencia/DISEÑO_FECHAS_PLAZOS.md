# Diseño del subsistema de fechas y plazos — BDDAT

> **Fecha:** 2026-04-01
> **Estado:** En construcción — sesión inicial de diseño.
> **Fuente de verdad:** `docs/NORMATIVA_PLAZOS.md` — todo contenido legal (plazos, artículos, constantes) extrae de ahí. En caso de discrepancia, prevalece `NORMATIVA_PLAZOS.md`.
> Referencia de arquitectura: `DISEÑO_MOTOR_AGNOSTICO.md`
> Última sincronización: 2026-08-21 (§1.1 NORMATIVA_PLAZOS.md — art. 22.1.a, la medida única de #778 / ADR-041)

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
| `SIN_PLAZO` | No existe plazo legal asociado, o el documento de disparo aún no existe | Ninguno | Sin indicador |
| `EN_PLAZO` | `hoy() < fecha_limite - umbral_alerta` | — | Sin indicador |
| `PROXIMO_VENCER` | `fecha_limite - umbral_alerta ≤ hoy() < fecha_limite` | — | Aviso (amarillo) |
| `VENCIDO` | `hoy() ≥ fecha_limite`, sin cumplimiento | Ver catálogo de efectos ↓ | Depende del efecto |
| `CUMPLIDO` | Llegó el documento que acredita el cumplimiento (#778) | Ninguno | Verde |

`umbral_alerta` = **5 días hábiles** (fijo).

> **Las cuatro fechas acompañan siempre al estado (#778, ADR-041 §A).** Un plazo
> es una sola medida y produce **disparo**, **vencimiento**, **cumplimiento** (o
> nada) y **parada** — la primera de cumplimiento, vencimiento u hoy. Son el
> dato; el estado es la lectura cómoda de ese dato. `fecha_limite` conserva su
> nombre histórico y es el **vencimiento** (§3.5), ya con las suspensiones
> sumadas cuando se pregunta por una solicitud.
>
> **«Cumplido fuera de plazo» no es un valor del vocabulario.** Se lee comparando
> las dos fechas que el servicio ya devuelve (`cumplimiento > vencimiento`). El
> vocabulario no crece por algo derivable sin ambigüedad.
>
> **`suspendido` tampoco es un estado**, sino un dato aparte del plazo de la
> solicitud: es ortogonal, un plazo puede estar suspendido y a la vez próximo a
> vencer.
>
> **`CUMPLIDO` tiene dos lecturas y el vocabulario aguanta las dos.** En las
> esperas de un tercero el cierre puede llegar antes del vencimiento: alguien
> contestó. En las de mero transcurso —los 30 días de exposición— el
> `CERT_PLAZO_CUMPLIDO` lo emite el propio sistema y exige que el plazo haya
> vencido (`certificados.py`), así que ahí significa «está acreditado que el
> plazo transcurrió».

> **`SIN_PLAZO` cubre también el "plazo indefinido" de `ESTRUCTURA_FTT.md`
> (notación `EP(0)`) — decisión #789.** Varios `ESPERAR_PLAZO` no tienen plazo
> legal (dictamen/propuesta/informe vinculante de `AAU_AAUS_INTEGRADA`,
> `SOLICITUD_FIGURA`, la primera espera de los `ANUNCIO_*`). Se decidió a
> propósito **no** darles fila en `catalogo_plazos` con `plazo_valor=0`: la
> ausencia de fila ya produce `SIN_PLAZO`, que en `estado_dominio.py` escala a
> `PENDIENTE_TRAMITAR` — rojo permanente en el árbol hasta que llega el
> documento. Es el comportamiento correcto: sin plazo cierto no hay fecha en
> la que el sistema pueda escalar la alerta por sí solo (a diferencia de
> `EN_PLAZO`, que sabe pasar a `PROXIMO_VENCER`/`VENCIDO` solo), así que el
> rojo persistente — no un gris de "espera pasiva" — es la señal que evita
> que el tramitador lo pierda de vista. El frontend React tiene un estado
> `INDEFINIDO` ya construido (barra gris, distinto de `SIN_PLAZO`) que queda
> sin productor a propósito — no se borra, por si aparece un caso futuro
> genuino de "indefinido sin necesidad de seguimiento activo".

#### Catálogo de efectos del vencimiento

El efecto del vencimiento determina la gravedad de la alerta y quién resulta perjudicado. Los efectos vienen de la LPACAP y de la norma sectorial. Se distingue si el perjudicado es la Administración o el administrado, porque la alerta en UI debe ser distinta:

| Efecto | Perjudicado | Automático | Alerta UI | Referencia |
|---|---|---|---|---|
| **Silencio estimatorio** | Administración — el acto se entiende concedido sin resolución expresa | Sí | **Crítica** (rojo) | Art. 24.1 LPACAP |
| **Responsabilidad disciplinaria** | Administración — el funcionario responde del incumplimiento | No (requiere expediente) | **Crítica** (rojo) | Art. 21.6 LPACAP |
| **Silencio desestimatorio** | Administrado — se entiende denegado, puede recurrir | Sí | Normal (naranja) | Arts. 24.1 y 25.1.a LPACAP |
| **Caducidad del procedimiento** | Administrado — se archivan las actuaciones por inactividad | No (requiere advertencia previa + resolución) | Normal (naranja) | Art. 95.1 LPACAP — **aplica en BDDAT**: inactividad del interesado > 3 meses |
| **Tener por desistido** | Administrado — se le tiene por desistido de su solicitud; termina el procedimiento sin resolver el fondo | No (requiere resolución expresa, art. 21.1) | **Crítica** (rojo) | Art. 68.1 LPACAP — no confundir con el desistimiento voluntario del art. 94 (#779) |
| **Pérdida de trámite** | Administrado — pierde un trámite no indispensable, no el procedimiento | Sí | Normal (naranja) | Art. 95.2 LPACAP |
| **Apertura de recurso** | Ninguno directamente — abre la vía impugnatoria | Sí | Normal (naranja) | Arts. 122, 124 LPACAP |
| **Prescripción del derecho condicionado** | Administrado — el derecho otorgado por resolución propia caduca | No (requiere declaración) | Normal (naranja) | Ver §2.8 |
| **Sin efecto automático** | Ninguno — plazo de trámite interno sin consecuencia legal directa | No | Normal (naranja) | — |

> **Art. 25.1.b** (caducidad de procedimientos de oficio): no aplica en BDDAT — todos los expedientes son a instancia de parte. Si en el futuro se incorporan procedimientos de oficio, revisar.

> **Art. 95 — Caducidad por inactividad del interesado**: aplica íntegramente en BDDAT. El flujo es: inactividad > 3 meses → la Administración advierte → si persiste → resolución de archivo. Un procedimiento caducado no interrumpe la prescripción del derecho, pero si el derecho no ha prescrito, el interesado puede iniciar un nuevo procedimiento incorporando actos y trámites del anterior (ver §7 — reutilización de trámites entre expedientes).

El estado y el efecto se exponen como variables separadas del ContextAssembler:
- `estado_plazo`: `SIN_PLAZO` / `EN_PLAZO` / `PROXIMO_VENCER` / `VENCIDO` / `CUMPLIDO`
- `efecto_plazo`: `NINGUNO` / `SILENCIO_ESTIMATORIO` / `RESPONSABILIDAD_DISCIPLINARIA` / `SILENCIO_DESESTIMATORIO` / `CADUCIDAD_PROCEDIMIENTO` / `TENER_POR_DESISTIDO` / `PERDIDA_TRAMITE` / `APERTURA_RECURSO` / `PRESCRIPCION_CONDICIONADO` / `SIN_EFECTO_AUTOMATICO`

---

### 2.5 Suspensión del plazo

El plazo se **suspende** cuando concurre alguna de las causas del art. 22 LPACAP (ver `NORMATIVA_PLAZOS.md §1.1`). El reloj se para; el tiempo transcurrido antes se conserva; al reanudar se suma el periodo suspendido a la fecha límite.

> **Una suspensión no es un mecanismo aparte (#778, ADR-041).** Es **el plazo de
> un tercero visto desde la solicitud**, y la propia ley lo dice al fijar cuándo
> termina —art. 22.1.a: «por el tiempo que medie entre la notificación del
> requerimiento y su efectivo cumplimiento por el destinatario, **o, en su
> defecto, por el del plazo concedido**»—, que es el menor de los dos:
> exactamente la **parada** de §2.4. El intervalo suspendido va del disparo a la
> parada de esa misma medida, así que el tope de la suspensión existe por
> construcción y no hay lógica que escribir para él. Ver §3.3.

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

## 2.bis Principio arquitectónico — Ningún elemento ESFTT almacena fechas

> **Estado:** Cerrado — sesión 2026-04-18/19 (análisis tipo a tipo). Absorbe y cierra `ANALISIS_FECHAS_ESFTT.md`.

Esta sección establece el principio rector sobre fechas en ESFTT que supersede las decisiones abiertas de §3.0–§3.1 de versiones anteriores de este documento.

### Conclusión

**Ningún elemento ESFTT** (Expediente, Solicitud, Fase, Trámite, Tarea) **almacena fechas propias.** Esta conclusión aplica a los cinco niveles.

**Fechas no administrativas** (`fecha_inicio`, `fecha_fin` de fases, trámites, tareas): son marcas temporales de acciones del usuario en el sistema ("cuándo hice clic"). No tienen cliente real: no computan plazos legales, no tienen valor jurídico, no aportan nada que no esté ya en el cuaderno de bitácora. La mera existencia del registro con su `id` prueba que el usuario interactuó.

**Fechas administrativas** (`fecha_solicitud`, fechas de notificación, firma, publicación…): su único hogar válido es `Documento.fecha_administrativa` del documento que las porta. Leer una fecha administrativa es leer del Documento (fuente de verdad). Almacenar un duplicado en el modelo ESFTT crea un dato que puede divergir del documento real con consecuencias legales, y cuya consistencia no puede garantizarse.

**El estado tampoco se almacena.** Es deducible en tiempo de consulta a partir de las reglas del motor y de los documentos existentes.

### Trazabilidad por FK, no por duplicación

Los documentos son agnósticos: no saben quién los usa. La trazabilidad (quién los produce, a qué elemento pertenecen) vive en FKs en las tablas relacionadas. El FK señala dónde está la fuente de verdad, no duplica el dato.

**Implicación para `Solicitud`:** debe existir un FK `documento_solicitud_id` → `documentos.id` (nullable). Este FK permite localizar la fuente de verdad de los datos capitales de la solicitud: *cuándo* (`Documento.fecha_administrativa`) y *qué* (tipo deducible del PDF — issue #304). `documento_solicitud_id` no existe actualmente — debe añadirse.

### Cómo se capturan las fechas administrativas

1. El documento se sube al pool (requisito previo al acto que lo origina).
2. BDDAT analiza el documento: metadata del PDF, firma digital, OCR si hace falta.
3. El sistema **propone** la fecha extraída para validación del usuario — nunca asignación automática sin confirmación.
4. El usuario valida. La fecha queda en `Documento.fecha_administrativa`.
5. Solo en caso extremo el usuario introduce la fecha manualmente. La bitácora lo registra.

Este flujo aplica también al wizard de creación de expediente: el documento de solicitud debe estar en el pool antes de crear el expediente. La fecha de solicitud se extrae del documento, no de un campo `Solicitud.fecha_solicitud`.

### Mapa de fechas administrativas por fase

El análisis tipo a tipo reveló qué documento porta la fecha administrativa relevante en cada fase. Referencia para el seed de reglas del motor y para la UI.

| Fase | Fecha administrativa | Documento que la porta | Tarea productora |
|---|---|---|---|
| ANALISIS_SOLICITUD | — | No aplica (contenedor puro) | — |
| CONSULTA_MINISTERIO | Notificación al Ministerio | Doc. de notificación | NOTIFICAR en `SOLICITUD_INFORME` |
| COMPATIBILIDAD_AMBIENTAL | Notificación a Medio Ambiente | Doc. de notificación | NOTIFICAR en `SOLICITUD_COMPATIBILIDAD` |
| CONSULTAS | Notificación a cada organismo (30/15 días) | Doc. de separata/traslado | NOTIFICAR en `CONSULTA_SEPARATA` y traslados |
| INFORMACION_PUBLICA | Fecha de publicación en cada medio | Doc. producido/recibido por trámite de anuncio | NOTIFICAR (fecha de publicación efectiva por trámite) |
| FIGURA_AMBIENTAL_EXTERNA | Notificación al titular | Doc. de notificación al titular | NOTIFICAR en `SOLICITUD_FIGURA` |
| AAU_AAUS_INTEGRADA | Notificación al órgano ambiental | Doc. de notificación | NOTIFICAR en `REMISION_RESULTADO_IP_CONSULTAS` |
| RESOLUCION | Elaboración, notificación y publicación | Doc. de resolución / notif. / publicación | ELABORAR, NOTIFICAR, ESPERAR_PLAZO (un doc. por trámite) |

> **Nota RESOLUCION:** los tres trámites interiores portan fechas con efectos jurídicos distintos (inicio de plazo de recurso, publicidad registral, etc.). Se analizarán en detalle cuando se aborde el nivel Trámite.

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
| `Solicitud` | `fecha_solicitud` | Date NOT NULL | Fecha oficial de presentación — entrada en registro electrónico | **Sí** — inicio del cómputo del plazo de resolución (art. 21) | **Sí** | **[ELIMINADO — pasa a `Documento.fecha_administrativa` del doc de solicitud referenciado por `documento_solicitud_id`]** |
| `Solicitud` | `fecha_fin` | Date nullable | Cierre voluntario de la tramitación por el usuario (fecha de hoy) | **No** — sin valor jurídico propio | **No** | **[ELIMINADO — refactor fechas ESFTT]** |
| `Fase` | `fecha_inicio` | Date | Manual — metadato administrativo | Depende del tipo | Depende — ver §3.1 | **[ELIMINADO — refactor fechas ESFTT]** |
| `Fase` | `fecha_fin` | Date | Manual | Depende del tipo | Depende — ver §3.1 | **[ELIMINADO — refactor fechas ESFTT]** |
| `Tramite` | `fecha_inicio` | Date | Tramitación | Depende del tipo | Depende — ver §3.1 | **[ELIMINADO — refactor fechas ESFTT]** |
| `Tramite` | `fecha_fin` | Date | Tramitación | Depende del tipo | Depende — ver §3.1 | **[ELIMINADO — refactor fechas ESFTT]** |
| `Tarea` | `fecha_inicio` | Date | Tramitación, cerca del documento | Depende del tipo | Depende — ver §3.1 | **[ELIMINADO — refactor fechas ESFTT]** |
| `Tarea` | `fecha_fin` | Date | Tramitación, cerca del documento | Depende del tipo | Depende — ver §3.1 | **[ELIMINADO — refactor fechas ESFTT]** |
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

### 3.1 Mapa semántico de fechas

> **Estado:** OBSOLETO — 2026-04-19. Supersedido por `§2.bis Principio arquitectónico` de este documento (conclusión de la sesión 2026-04-18). Al eliminarse todos los campos `fecha_inicio`/`fecha_fin` de Fase, Trámite y Tarea, la tabla `metadatos_fechas` pierde su razón de ser para esos niveles. **No debe implementarse.** La referencia de inicio de cómputo para plazos pasa al campo `campo_fecha JSONB` de `catalogo_plazos` (ver §3.2 rediseñado).

~~Las columnas `fecha_inicio`/`fecha_fin` de Fase, Trámite y Tarea **no se renombran ni se añaden columnas nuevas**. La semántica de cada fecha se almacena en una tabla BD `metadatos_fechas`, administrable por Supervisor o Admin.~~

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

### 3.2 Catálogo de plazos — CERRADO (campo_fecha 2026-04-19, condiciones_plazo #341 2026-04-30, camino SFTT #785 2026-08-17, niveles SOLICITUD/TAREA #788 2026-08-19)

> **Decisión:** Tabla separada `catalogo_plazos`, administrable por el Supervisor.

Motivación: un tipo de Fase o Trámite no tiene el plazo como atributo propio — la relación es independiente y merece una tabla puente. Permite histórico de cambios legales, múltiples plazos por tipo (por tipo de expediente o vigencia temporal), y modificación sin alterar el catálogo de tipos.

**Estructura:**

```
catalogo_plazos
├── id
├── tipo_elemento              ENUM(SOLICITUD, TAREA)  -- prefiltro SQL (#788)
├── camino                     VARCHAR(250)  -- patrón ESFTT con comodín ANY (#785)
├── campo_fecha                JSONB  -- señalador del DISPARO (ver formato abajo)
├── campo_fecha_cumplimiento   JSON   -- señalador del CUMPLIMIENTO, opcional (#778)
├── suspende_plazo_solicitud   BOOLEAN  -- si este plazo suspende el de la solicitud (#778)
├── plazo_valor                INTEGER
├── plazo_unidad               ENUM(DIAS_HABILES, DIAS_NATURALES, MESES, ANOS)
├── efecto_vencimiento         FK → efectos_plazo  -- (tabla; sin enums hardcodeados)
├── norma_origen               TEXT  -- "Art. 21.3 LPACAP", "Art. 14 RD 1955/2000"...
├── vigencia_desde             DATE nullable
├── vigencia_hasta             DATE nullable
└── activo                     BOOLEAN
```

> **Los dos datos de #778.** `campo_fecha_cumplimiento` usa el **mismo
> vocabulario cerrado** que `campo_fecha` —el problema es el mismo, localizar un
> documento desde el elemento— y es opcional: sin él el plazo nunca alcanza
> `CUMPLIDO`, que es lo correcto en `TABLON_AYUNTAMIENTOS` (#416), donde disparo
> y cierre son el mismo documento. `suspende_plazo_solicitud` sustituye a la
> lista `_TRAMITES_SUSPENSION` que vivía en `plazos.py`: que la petición de un
> informe preceptivo suspenda el plazo para resolver cambia cuando cambia la ley
> y es citable a artículo concreto (art. 22.1.a / 22.1.d), luego es dato normativo
> (test de ADR-037). `CheckConstraint` al nivel TAREA: el art. 22 suspende el
> plazo de la solicitud, así que marcarla a ella sería suspenderse a sí misma.
>
> `campo_fecha_cumplimiento` se declara `JSON` y no `JSONB` como su gemela: se
> lee entera y se compara en Python, sin operadores ni índices de `jsonb`, y el
> resto del proyecto usa `db.JSON` por portabilidad a otros motores.

#### Identificación por camino SFTT (#785)

Hasta #785 la fila se identificaba por `tipo_elemento` + `tipo_elemento_codigo`
(el literal del tipo hoja). **No basta:** literales como `ESPERAR_PLAZO` o
`RESOLUCION` se repiten en puntos distintos del árbol, y la distinción se hacía
con filas de `condiciones_plazo` sobre variables que solo reexponían un dato de
posición que el grafo de FKs ya contiene — una FK disfrazada. El caso extremo:
la variable `tipo_tramite` nunca tuvo función en `app/services/variables/`, así
que por el camino general del motor resolvía siempre a `None`; solo funcionaba
porque tres consumidores la reconstruían a mano saltándose el ensamblador.

`camino` es un patrón calificado con comodín posicional `ANY`, **mismo formato y
mismo matcher** (`operadores.camino_casa`) que `reglas_motor.sujeto`, con un
nivel más de profundidad. La longitud codifica el nivel:

| Nivel de la fila | Segmentos | Forma |
|---|---|---|
| SOLICITUD | 2 | `<expediente>/<siglas>` |
| TAREA | 5 | `<expediente>/<siglas>/<fase>/<tramite>/<tarea>` |

> **FASE y TRAMITE no son niveles de fila desde #788** — ninguno de los dos
> porta fecha administrativa (§2.bis), así que un plazo no puede identificarse
> por Fase o Trámite: `CheckConstraint tipo_elemento IN ('SOLICITUD','TAREA')`
> lo hace explícito en BD. Sus posiciones (segmentos 3 y 4) siguen existiendo
> dentro del camino de 5 segmentos de una TAREA, como **ancestros** — la
> cascada del formulario sigue pidiendo fase y trámite al dar de alta una
> tarea, lo que desaparece es que sean niveles seleccionables por sí solos.

**Invariante:** el último segmento nunca es `ANY` — es el tipo del elemento
evaluado, siempre conocido. Una fila con hoja `ANY` no identificaría nada.

```
ANY/ANY/ANY/REQUERIMIENTO_SUBSANACION/ESPERAR_PLAZO   -- el plazo de subsanación
ANY/ANY/ANY/ANUNCIO_BOE/ESPERAR_PLAZO                 -- el de exposición en BOE
ANY/AAP/RESOLUCION                                    -- resolución de una AAP
```

`tipo_elemento` se conserva pese a ser derivable de la longitud: es el prefiltro
SQL de la query (filtrar por número de segmentos de un string no es viable).

**Reparto de responsabilidades con `condiciones_plazo`:** el camino dice DÓNDE
está el plazo; las condiciones, BAJO QUÉ SUPUESTO LEGAL aplica. Las que expresan
supuesto real siguen vivas (`max_tension_nominal_kv` en SOLICITUD/AAP,
`es_solicitud_aac_pura` + `tiene_solicitud_aap_favorable` en el plazo reducido de
consultas del art. 131.1 párr. 2). Meter posición en una condición vuelve a
crear el problema que #785 resolvió.

#### Formato de `campo_fecha` (JSONB)

`campo_fecha` no es código — es **configuración de dominio administrable por el Supervisor**. La legislación fija el valor y la unidad del plazo; también fija *desde qué momento* empieza a contar. Ese momento tiene un reflejo en BDDAT (algún `Documento.fecha_administrativa` accesible desde el elemento ESFTT). El Supervisor lo define en el catálogo; puede corregirlo sin tocar código si la norma cambia.

**Vocabulario cerrado desde #788.** Solo hay dos portadores de fecha
administrativa en BDDAT (§2.bis): la Solicitud, por `documento_solicitud_id`,
y la Tarea, por sus vínculos `documentos_tarea` (ADR-010). Fase y Trámite son
taxonomía ESFTT, no figuras jurídicas — ninguna norma les fija plazo propio, y
las dos indirecciones que existían antes (`fk: documento_resultado_id` en
Fase; `via_tarea_tipo` en Trámite, para bajar a su tarea hija) eran la huella
de filas declaradas en el nivel equivocado, no formas legítimas del
vocabulario: una fila que necesita trepar o bajar para encontrar su ancla
está mal ubicada. `campo_fecha` no es extensible — no hay un tercer portador
de fecha al que apuntar.

El campo `campo` es siempre `fecha_administrativa` (el resolver lo asume). Referencias por nivel:

| Nivel | Referencia al documento de inicio | Referencia al de cumplimiento (#778) |
|---|---|---|
| `SOLICITUD` | `fk: documento_solicitud_id` — sin alternativa | `fk: documento_cierre_id` — sin alternativa |
| `TAREA` | `rol: CONSUMIDO` o `rol: PRODUCIDO` (vínculo en `documentos_tarea`, ADR-010), con `tipo_documento` opcional | ídem, o **nada** — y entonces el plazo no alcanza `CUMPLIDO` |

> **Cada plazo se abre y se cierra en el mismo sitio (ADR-041 §D).** La estructura
> FTT ya lo cumple en **todos** los trámites con plazo, suspendan o no —
> verificado en `tramites_tareas_documentos`: el documento PRODUCIDO de cada
> `ESPERAR_PLAZO` es exactamente el que cierra esa espera (`SUBSANACION`,
> `INFORME_114_RD1955`, `RESPUESTA_ORGANISMO`, `RESPUESTA_TITULAR`,
> `INFORME_COMPATIBILIDAD_AMBIENTAL`, `CERT_PLAZO_CUMPLIDO`). Por eso #778 pudo
> retirar el rescate que buscaba el documento de cierre en un trámite hermano
> (`SOLICITUD_INFORME` → `RECEPCION_INFORME`, `SOLICITUD_COMPATIBILIDAD` →
> `RECEPCION_DICTAMEN`): nunca cubrió una necesidad estructural, cubría que el
> tramitador hubiera archivado el documento en otro sitio, y eso es un dato mal
> puesto, no algo que el cálculo deba compensar. Si algún día aparece una tarea
> con plazo cuyo documento de cierre viva necesariamente en otro trámite, es un
> problema de modelado del ESFTT y se discute como tal.
>
> **El cierre del plazo de la solicitud es `documento_cierre_id`, no
> `Fase(RESOLUCION).documento_resultado_id`** (ADR-041 §D bis): aquella es la
> resolución y su fecha es la de dictar, anterior a la de notificar, y el art.
> 21.3.b obliga a «resolver **y** notificar». El art. 40.4 fija con qué basta —la
> notificación o el intento debidamente acreditado—, y con varios interesados hay
> varios intentos: ninguno significa por sí solo «la solicitud está cerrada», de
> ahí un certificado del hecho agregado (`CERT_CIERRE_SOLICITUD`) y no un
> justificante bruto. Quién lo emite y cuándo quedó fuera de #778.

```jsonc
// Único caso directo — Solicitud: "fk" = atributo ORM con FK a documentos
{ "fk": "documento_solicitud_id" }

// Caso Tarea — el documento se obtiene por rol del vínculo documentos_tarea:
{ "rol": "CONSUMIDO" }

// Caso Tarea, retroactivo (#416) — el documento llega cuando el período ya
// concluyó; su fecha_administrativa es la de INICIO del período, no la de
// llegada. Uso: TABLON_AYUNTAMIENTOS (CERT_PLAZO_TABLON porta la fecha de
// inicio de la exposición).
{ "rol": "PRODUCIDO" }

// tipo_documento (opcional, #788 §2.3) — desempata cuando dos tareas del
// mismo tipo conviven en un trámite y comparten camino: las dos ESPERAR_PLAZO
// de un ANUNCIO_* (la que aguarda la publicación y la de los 30 días de
// exposición). El dato sale de tramites_tareas_documentos (#346); se omite
// cuando el documento de entrada es polimórfico por diseño (el justificante
// de CONSULTA_SEPARATA depende del canal — BANDEJA/NOTIFICA/POSTAL/SIR — y
// esa espera es única en su trámite, sin ambigüedad que desempatar).
{ "rol": "CONSUMIDO", "tipo_documento": "ANUNCIO_PUBLICADO" }
```

**UI de Supervisión:** selector en cascada (nivel ESFTT → si TAREA, rol y tipo de documento). El desplegable de tipo de documento sale de `tramites_tareas_documentos`, filtrado por el trámite/tarea/rol ya elegidos en la cascada del camino. El POST traduce la selección al JSON. La presentación inversa lo traduce a texto legible:
- `{"fk": "documento_solicitud_id"}` → "Fecha administrativa del documento de solicitud"
- `{"rol": "CONSUMIDO"}` → "Fecha administrativa del documento consumido por esta tarea"
- `{"rol": "PRODUCIDO", "tipo_documento": "CERT_PLAZO_TABLON"}` → "Fecha administrativa del documento producido («Certificado de plazo tablón»)"

**`plazos.py` — resolver:** recibe el objeto ORM del elemento y el JSON de `campo_fecha`. Dos ramas según si el dict trae `fk` o `rol` — no hace falta mirar `tipo_elemento`, el vocabulario ya identifica unívocamente la rama. Si `rol` trae `tipo_documento`, filtra el vínculo por ese tipo; si no, toma el primero. Devuelve `Documento.fecha_administrativa` o `None`.

> La FK `efecto_vencimiento` referencia una tabla de efectos (no ENUM hardcodeado). Ver decisión §3.3 nota.

> **Corrección de #787 (#788 §8):** #787 purgó correctamente las 14 filas de
> nivel SOLICITUD entonces existentes, pero atribuyó la purga a que «el nivel
> queda a cero, que es lo correcto — el plazo de resolución vive a nivel
> FASE». Esa justificación era falsa: el plazo de resolución (arts.
> 128/131.7/132 bis/ter/133/138/145.4 RD 1955/2000) es el plazo **de la
> solicitud** para resolver y notificar (art. 21.3.b LPACAP), y por tanto
> pertenece al nivel SOLICITUD, no FASE. #788 lo confirma: las 11 filas de
> RESOLUCION migran de FASE a SOLICITUD (§5.2), y el nivel FASE queda
> prohibido por el `CheckConstraint`.

#### §3.2.1 Condiciones de aplicabilidad — `_seleccionar_catalogo` (#341)

`obtener_estado_plazo` delega la selección de la entrada aplicable en
`_seleccionar_catalogo(elemento, tipo_elemento, variables_dict)`.

**Algoritmo** (paso 1.bis añadido en #785):

1. **Carga** todas las entradas activas de `catalogo_plazos` para
   `tipo_elemento` con `joinedload` de `condiciones` y la `variable` de cada
   condición (una sola query).
1. **bis. Filtra por camino:** compila el camino real del `elemento` subiendo por
   el ORM (`plazos.compilar_camino`) y descarta las entradas cuyo patrón `camino`
   no casa. Los datos de ascendencia ya están en memoria por los eager-loads de
   los consumidores, así que no añade queries.
1. **ter. Filtra por `tipo_documento` (#788 §2.3):** una fila que declara
   `tipo_documento` en `campo_fecha` solo es candidata si el elemento tiene un
   vínculo de ese tipo y rol. Necesario porque el filtro por camino no basta
   cuando dos tareas del mismo tipo comparten camino (las dos `ESPERAR_PLAZO`
   de un `ANUNCIO_*`): sin este predicado, la candidata de menor `orden`
   ganaría siempre para ambas y la resolución de fecha fallaría en silencio
   para la otra — `_seleccionar_catalogo` no reintenta con la siguiente
   candidata si la elegida no resuelve fecha.
2. **Ordena** por `orden ASC, id ASC` (menor `orden` = mayor prioridad;
   `id` como desempate estable ante empate de `orden`).
3. **Itera** en orden:
   - Entrada **sin condiciones** → candidata válida; se devuelve inmediatamente.
   - Entrada **con condiciones** → evalúa AND implícito:
     si todas las condiciones se cumplen → se devuelve;
     si alguna falla → se salta, se evalúa la siguiente.
4. Si ninguna entrada supera la evaluación → `None` + `log.warning`.
   El llamante devuelve `SIN_PLAZO` sin lanzar excepción.

**Semántica AND implícito:**

- Cada condición evalúa `variables_dict[nombre] OPERADOR valor`.
- Variable ausente en el dict → condición falla silenciosamente con `log.warning`
  (decisión F de IMPLEMENTACION_341.md: el catálogo nunca lanza excepción por
  variable no calculada).
- Operadores: los de `app/services/operadores.py`
  (`EQ`, `NEQ`, `GT`, `GTE`, `LT`, `LTE`, `IN`, `NOT_IN`).

**Compatibilidad hacia atrás:**

Sin `ctx` ni `variables`, `variables_dict = {}`. Solo las entradas sin condiciones
son candidatas válidas — reproduce el comportamiento pre-#341 para cualquier
llamada que no pase contexto.

**Caso de uso canónico — art. 131.1 párr. 2 RD 1955/2000:**

```
catalogo_plazos para CONSULTAS (fase válida para AAP y AAC — art. 131 RD 1955/2000):
  orden=10,  plazo=15 días naturales,
             condiciones: tiene_solicitud_aap_favorable=True
                        + es_solicitud_aac_pura=True
  orden=100, plazo=30 días naturales, sin condiciones (fallback)
```

Si las dos condiciones se cumplen → 15 días; en caso contrario → 30 días.

---

### 3.3 Suspensiones de plazo — la misma medida, sin tabla propia (#173, corregida #788, unificada #778)

> **Estado:** Cerrado. La estructura tentativa que este documento proponía en
> 2026-04-01 (tabla `suspensiones_plazo` con `causa_id` FK a un catálogo de
> causas) no se construyó: no hace falta un registro explícito de cada
> suspensión si se puede derivar del árbol documental que ya existe.

**Mecanismo real** (`app/services/plazos.py::obtener_estado_plazo_solicitud`,
reescrito en #778 sobre ADR-041): el plazo de la solicitud se mide como
cualquier otro (§2.4), y después se recorren sus tareas —`solicitud → fases →
trámites → tareas`— reteniendo las que tienen entrada de catálogo **marcada como
suspensora**. Cada una se mide **igual, sin nada añadido**, y aporta el intervalo
`[disparo, parada]`.

Recibe la **Solicitud** —no la Fase ni el Trámite— porque el art. 22 LPACAP
suspende «el plazo máximo legal para resolver un procedimiento y notificar la
resolución», que es el plazo de la solicitud y ninguno más.

Los intervalos resultantes se **funden en una sola unión** — vivos y cerrados
juntos: el reloj se para una vez, no una por cada causa concurrente — y se
cuentan como `(A, B]`: los días hábiles desde el día siguiente al acto hasta el
de cierre inclusive, que es la diferencia que exige la norma («por el tiempo que
**medie entre**…», arts. 22.1.a / 22.1.d), no un recuento inclusivo de ambos
extremos. Ver §3.5 decisión 5.

De ahí salen sin código adicional: si el plazo está **suspendido hoy** (lo está
si alguna tarea suspensora sigue corriendo), **desde cuándo** lo está de forma
continua —el inicio del bloque fusionado que alcanza hoy, que puede ser anterior
a la causa viva más antigua— y **cuánto tiempo** lleva parado.

**Qué suspende es dato del catálogo, no una lista en el código.** La columna
`suspende_plazo_solicitud` sustituyó a `_TRAMITES_SUSPENSION` (#778). Corolario
buscado: **un plazo sin entrada en el catálogo no suspende nada**. Hasta ese
cambio convivían un trámite marcado como suspensor en el código
(`SOLICITUD_COMPATIBILIDAD`) y sin fila en el catálogo, con lo que el sistema lo
pintaba como plazo no configurado a la vez que lo usaba para mover la fecha
límite de la solicitud.

**No toda espera externa suspende.** La información pública y los traslados al
peticionario (arts. 126 / 127.3 RD 1955/2000 — trámites `ANUNCIO_*` y
`CONSULTA_TRASLADO_*`) no llevan la marca: son instrucción ordinaria, corren
*dentro* del plazo y lo consumen, no lo paran.

#### Lo que se cayó, y por qué no debe volver

Hasta #778 este cálculo era **un segundo motor** que no consultaba
`catalogo_plazos` en ningún momento: tenía la lista de trámites escrita en el
código, navegaba el árbol por su cuenta y encadenaba tres tentativas de cierre,
con un rescate por trámite hermano receptor. Al no preguntar cuánto dura nada,
una suspensión **no podía vencer**: sin respuesta del interesado el cierre se
quedaba en «hoy» y se recalculaba cada día, de modo que la fecha límite se
alejaba un día por cada día que pasaba y el expediente no vencía nunca. El caso
que más urge detectar —el titular que calla— era justo el que el sistema
ocultaba.

También desapareció el flag `abierto` guardado como dato. No es un renombre:
significaba «no encontré documento de cierre», que es exactamente lo que hacía
crecer la suspensión sin límite. Su sustituto, `vivo`, se deriva del estado de la
propia espera —sigue corriendo— y una espera vencida sin respuesta no lo está.

**El tope del art. 22.1.d** («este plazo de suspensión no podrá exceder en ningún
caso de tres meses») **no se implementa en el cómputo**: recae sobre la
suspensión, no sobre el plazo concedido al informante, y en la práctica no muerde
—todos los plazos de informe que BDDAT maneja son de tres meses o menos—. Se
vigila **al dar de alta la entrada**, con un aviso no bloqueante del CRUD. Donde
la letra y esta decisión pueden diferir (organismo con dos meses para informar
que no contesta: ¿la suspensión acaba a los dos meses o sigue hasta tres?) se
adopta la lectura **corta**: la parada es el vencimiento del plazo del catálogo,
que da una fecha límite más temprana y avisa antes — la dirección conservadora
fijada en #796.

**Lo que queda fuera — remitido a #796.** El art. 22.1 dice «se **podrá**
suspender» (potestativo) para las cuatro causas de BDDAT, frente al 22.2 («se
**suspenderá**», imperativo), que no aplica aquí — ver `NORMATIVA_PLAZOS.md
§1.1`. Para los informes preceptivos, el art. 22.1.d exige además comunicar a
los interesados tanto la petición como la recepción del informe; hay
jurisprudencia (pendiente de verificar en CENDOJ) según la cual sin ese acto la
suspensión no se produce. #788 arregla la **lógica** del cómputo (nivel,
fusión, `(A,B]`, ámbito) manteniendo la inferencia actual de qué cuenta como
suspensión; #796 engancha después la **acreditación** —el acuerdo de
suspensión y su notificación al interesado— sobre esa lógica ya correcta.

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

5. **Suspensiones definidas por `(fecha_inicio, fecha_fin)`, contadas como intervalo `(A, B]`.** El día de inicio no cuenta (el reloj ya está parado desde que ocurre el acto); el día de cierre **sí** cuenta — es el último día en que el plazo sigue parado, y el cómputo se reanuda al siguiente. Esto da la **diferencia** entre los dos extremos (`B − A`), que es la lectura que exige la norma: «por el tiempo que **medie entre** la notificación… y su efectivo cumplimiento» (art. 22.1.a), «entre la petición… y la recepción del informe» (art. 22.1.d) — ni un recuento inclusivo de ambos extremos ni una exclusión de los dos. La semántica de `fecha_inicio`/`fecha_fin` (qué documento porta cada extremo) depende del tipo de causa y se fija en §3.3.

   > **Corrección (#788).** La versión anterior de este punto excluía también
   > el día de cierre y citaba «art. 22.2 LPACAP: el cómputo se reanuda desde
   > el día siguiente» como fundamento. Esa cita está mal atribuida: el
   > art. 22.2 LPACAP es la lista de causas de suspensión **obligatoria** («se
   > suspenderá»), no regula el reinicio del cómputo. La lectura correcta,
   > `(A, B]`, sale de aplicar por analogía el art. 30.3 (el cómputo de un
   > plazo empieza el día siguiente al acto que lo origina) al cierre de la
   > suspensión: el día que llega la respuesta el plazo todavía está parado;
   > al siguiente, corre.

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

> **Estado:** Cerrado — §4.1 cerrado 2026-04-23; contrato de interfaz formalizado en #190 (2026-04-28).

Arquitectura acordada en conversación (2026-04-01):

```
Motor agnóstico (evalúa variables, no conoce plazos)
    ↑  variables: estado_plazo, efecto_plazo  (operadores estándar EQ/IN/etc.)
ContextAssembler
    ↑  llama a variables/plazo.py (@variable 'estado_plazo', 'efecto_plazo')
    ↑  llama a plazos.py para derivar estado de tareas ESPERAR_PLAZO (§4.1)
plazos.py
    ├── Norma sectorial → plazo específico por tipo de Fase/Trámite
    │       Si no hay respuesta ↓
    └── Fallback LPACAP (constantes §5)
    +
    ├── Tabla suspensiones_plazo (periodos activos)
    └── Calendario inhábiles Junta de Andalucía
```

### Contrato de interfaz — `app/services/plazos.py`

```python
from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class EstadoPlazo:
    estado: str                          # 'SIN_PLAZO' | 'EN_PLAZO' | 'PROXIMO_VENCER'
                                         # | 'VENCIDO' | 'CUMPLIDO'
    efecto: str                          # 'NINGUNO' | 'SILENCIO_ESTIMATORIO' | … (§2.4)
    fecha_limite: Optional[date]         # el vencimiento (§3.5). None si SIN_PLAZO
    dias_restantes: Optional[int]        # None si SIN_PLAZO o CUMPLIDO; negativo si VENCIDO
    fecha_disparo: Optional[date]
    fecha_cumplimiento: Optional[date]
    fecha_parada: Optional[date]         # min(cumplimiento, vencimiento, hoy)

@dataclass
class EstadoPlazoSolicitud(EstadoPlazo):
    suspendido: bool                     # ortogonal al estado, no un valor suyo
    suspendido_desde: Optional[date]
    dias_suspendidos: int
    fecha_limite_sin_suspender: Optional[date]

def obtener_estado_plazo_tarea(tarea, ctx=None, variables=None) -> EstadoPlazo: ...
def obtener_estado_plazo_solicitud(sol, ctx=None, variables=None) -> EstadoPlazoSolicitud: ...
```

**Dos entradas, no un literal de nivel (#778, ADR-041 §G).** El servicio solo
habla de las dos cosas que pueden tener plazo. Sin literales de nivel y sin
niveles fantasma que siempre respondan «sin plazo»: cuando no hay entrada en el
catálogo la respuesta es «no hay plazo», y el consumidor no tiene que saber por
qué. Los consumidores que despachaban por *duck-typing* eligen ahora la función
(`variables/plazo.py`), y Fase y Trámite se resuelven ahí mismo sin tocar BD.

**No hay entrada para el trámite.** Los dos consumidores que preguntaban por
trámite (`consultas_organismos.py`, `variables/calculado.py`) llegaban con un
trámite en la mano porque el vínculo con el organismo cuelga de ahí, no porque el
trámite tenga plazo. «Dame la tarea de espera de este trámite» es navegación del
árbol ESFTT (`Tramite.tarea_espera`), no una entrada de este servicio: una
función llamada «plazo de un trámite» reintroduciría por la puerta de atrás el
nivel que #788 eliminó.

**Variables expuestas al motor** (registradas en `catalogo_variables`, ambas `activa=TRUE`):

| Variable | tipo_dato | Valores posibles |
|---|---|---|
| `estado_plazo` | texto | `SIN_PLAZO` · `EN_PLAZO` · `PROXIMO_VENCER` · `VENCIDO` · `CUMPLIDO` |
| `efecto_plazo` | texto | `NINGUNO` · `SILENCIO_ESTIMATORIO` · `RESPONSABILIDAD_DISCIPLINARIA` · `SILENCIO_DESESTIMATORIO` · `CADUCIDAD_PROCEDIMIENTO` · `TENER_POR_DESISTIDO` · `PERDIDA_TRAMITE` · `APERTURA_RECURSO` · `PRESCRIPCION_CONDICIONADO` · `CONFORMIDAD_PRESUNTA` · `SIN_EFECTO_AUTOMATICO` |

**Stub Fase 2 (#190):** `obtener_estado_plazo` devuelve `SIN_PLAZO`/`NINGUNO` siempre.
Ninguna regla del motor disparará por plazo hasta que #172 implemente la lógica real.

**M3 (#172):** la función leerá `catalogo_plazos`, resolverá `campo_fecha` JSONB → `Documento.fecha_administrativa`, calculará `fecha_limite` con `dias_inhabiles` y `suspensiones_plazo`, y devolverá el estado calculado según las condiciones de §2.4.

---

### 4.1 Estado de tareas ESPERAR_PLAZO — derivación temporal

> **Estado:** Cerrado — sesión 2026-04-23; rev. 2026-05-25 (#416). **Corregida 2026-08-16** — el diseño descrito aquí quedó superado por ADR-004 (2026-05-11) sin sincronizar esta sección; ver nota de corrección al final.

`ESPERAR_PLAZO` completa su tarea con la **misma regla que cualquier otra tarea**: existe vínculo `PRODUCIDO` en `documentos_tarea` → completada; no existe → pendiente. No es una excepción al modelo general de completitud (ADR-004).

El documento producido llega por una de dos vías:

- **Caso A — respuesta real:** el documento externo esperado (notificación, publicación, informe, justificante...) llega y se vincula directamente como `PRODUCIDO`.
- **Caso B — plazo agotado sin respuesta:** el tramitador dispara la generación de un certificado interno (`CERT_PLAZO_CUMPLIDO`), que se vincula como `PRODUCIDO`. La generación está controlada: solo se permite si `plazos.py` confirma que el plazo del elemento está `VENCIDO`; en caso contrario se rechaza. La `fecha_administrativa` del certificado generado es la fecha de vencimiento calculada.

`documento_referencia` (el documento cuyo rol está configurado en `campo_fecha.rol` del `catalogo_plazos`) sigue determinando **desde cuándo se cuenta el plazo**, no si la tarea está completa:
- **`rol: CONSUMIDO`** (caso habitual): el documento que inicia el período de espera llega antes de que el plazo empiece (p. ej. `ANUNCIO_PUBLICADO` para los trámites `ANUNCIO_BOP/BOJA`).
- **`rol: PRODUCIDO`** (caso retroactivo): el documento llega cuando el período ya ha concluido y porta como `fecha_administrativa` la fecha de inicio del período (p. ej. `CERT_PLAZO_TABLON` para `TABLON_AYUNTAMIENTOS` — el ayuntamiento certifica cuándo empezó la exposición). Ver #416.

**Papel real de `estado_plazo` para esta tarea:** no decide la completitud (eso lo decide, como siempre, la existencia del documento producido). Decide (1) si la acción de generar el certificado del Caso B está permitida, y (2) qué fecha administrativa lleva ese certificado. El Assembler consulta `plazos.py` para las variables `estado_plazo`/`efecto_plazo` de la tarea igual que para cualquier otro elemento con plazo — no hay una rama de cálculo separada para `ESPERAR_PLAZO`.

> **Desde #778 las dos cosas coinciden por construcción**, y conviene no
> confundirlas. El documento producido que completa la tarea (ADR-004) es el
> mismo que `campo_fecha_cumplimiento` señala, así que una tarea ejecutada tiene
> el plazo `CUMPLIDO`. Siguen siendo dos preguntas distintas —completitud de la
> tarea y estado del plazo— que hoy responden al mismo hecho.

| Condición | Estado de la tarea |
|---|---|
| sin documento producido | `PENDIENTE` — ni ha llegado respuesta (Caso A) ni se ha generado el certificado (Caso B) |
| con documento producido (cualquiera de los dos casos) | `COMPLETADA` |

**El plazo se declara en la tarea, no en su trámite** (#788): la fila vive en el
`ESPERAR_PLAZO`, con `{"rol": "CONSUMIDO"}` en el caso habitual o
`{"rol": "PRODUCIDO"}` en el retroactivo (§3.2). La indirección
`via_tarea_tipo` que bajaba del trámite a su tarea desapareció con ella.

**Ausencia de plazo configurado:** si `catalogo_plazos` no tiene entrada para el trámite padre, `plazos.py` devuelve `SIN_PLAZO`. En el Caso A la tarea puede completarse igualmente si llega el documento externo — no depende del catálogo. En el Caso B, sin plazo configurado no hay `VENCIDO` posible, así que la generación del certificado queda bloqueada: el Supervisor debe configurar el plazo para que ese camino de cierre esté disponible.

> **Nota de corrección (2026-08-16):** la versión anterior de esta sección describía `ESPERAR_PLAZO` como la única tarea cuya completitud no era derivable de la BD (`completada ↔ hoy() > fecha_límite`, sin documento propio). Ese diseño quedó superado por **ADR-004** ("Eliminación de la tarea INCORPORAR", 2026-05-11): `ESPERAR_PLAZO` absorbió el rol de `INCORPORAR` y su `documento_producido` pasó a ser el documento recibido (Caso A) o el certificado de cierre (Caso B). Esta sección no se sincronizó en su momento. Ver también la nota #764 de ADR-004 sobre qué documento concreto es el `PRODUCIDO` cuando llegan varios documentos a la vez en un mismo acto de recepción.

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

> **Nota 2026-04-19:** Las entradas que usan `campo_inicio = fecha_inicio` o `campo_inicio = fecha_solicitud (solicitud)` requieren reconceptualización conforme al rediseño de `campo_fecha` (§3.2). `fecha_solicitud` desaparece del modelo `Solicitud`; pasa a `Documento.fecha_administrativa` del doc de solicitud (`{"fk": "documento_solicitud_id"}`). `fecha_inicio` de Fase/Trámite tampoco existe: la referencia de inicio pasa al Documento navegable desde el elemento. **Marcar como PENDIENTE DE REDISEÑO `campo_fecha`** hasta confirmar el documento fuente en cada caso.

> **Nota 2026-05-22 (hotfix #448):** Los identificadores `RESOLUCION_AAP`, `RESOLUCION_AAC`, `RESOLUCION_AE_*`, `RESOLUCION_TRANSMISION`, `RESOLUCION_CIERRE`, `RESOLUCION_DUP` de la tabla siguiente son **etiquetas conceptuales** de cada plazo — **no códigos de `tipos_fases`**. En BD existe un único `tipos_fases.codigo = 'RESOLUCION'` (id=8). Los 7 plazos se modelan como 7 filas en `catalogo_plazos` con `tipo_elemento_codigo = 'RESOLUCION'`, diferenciadas por una condición en `condiciones_plazo` que usa la variable `tipo_solicitud` (texto, siglas literal) con operador `IN` enumerando las combinaciones cubiertas por la misma cita normativa. El seed real está en la migración `448_seed_plazos_resolucion`.

Desde #785 la combinación va en el **camino**, una fila por sigla (sin `IN` en el
segmento), no en una condición sobre `tipo_solicitud`:

| Camino | Valor | Unidad | Efecto vencimiento | Norma origen |
|---|---|---|---|---|
| `ANY/AE_PROVISIONAL/RESOLUCION` | 1 | MESES | SILENCIO_DESESTIMATORIO | Art. 132 bis RD 1955/2000 + DA 3ª LSE |
| `ANY/AE_DEFINITIVA/RESOLUCION` · `ANY/AE_DEFINITIVA+AAT/RESOLUCION` | 1 | MESES | SILENCIO_DESESTIMATORIO | Art. 132 ter RD 1955/2000 + DA 3ª LSE |
| `ANY/AAP/RESOLUCION` | 3 | MESES | SILENCIO_DESESTIMATORIO | Art. 128 RD 1955/2000 |
| `ANY/AAC/RESOLUCION` · `ANY/AAP+AAC/RESOLUCION` · `ANY/AAP+AAC+DUP/RESOLUCION` · `ANY/AAC+DUP/RESOLUCION` | 3 | MESES | SILENCIO_DESESTIMATORIO | Art. 131.7 RD 1955/2000 |
| `ANY/AAT/RESOLUCION` | 3 | MESES | SILENCIO_DESESTIMATORIO | Art. 133 RD 1955/2000 |
| `ANY/CIERRE/RESOLUCION` | 3 | MESES | SILENCIO_DESESTIMATORIO | Art. 138 RD 1955/2000 |
| `ANY/DUP/RESOLUCION` | 3 | MESES | SILENCIO_DESESTIMATORIO | Art. 145.4 RD 1955/2000 |

`campo_fecha` para todas las filas RESOLUCION_*: `{"fk": "documento_solicitud_id"}`.

> **`INFORMACION_PUBLICA` no es un plazo de RESOLUCION (#788) — nunca lo fue.**
> La fila anterior vivía aquí marcada `[PENDIENTE REDISEÑO campo_fecha]`
> heredando el error que #788 corrige: es el período de exposición de **cada
> publicación** (art. 125 RD 1955/2000), que corre desde la fecha de
> publicación de ese anuncio concreto, no desde la solicitud ni desde ningún
> acto de la fase `INFORMACION_PUBLICA`. Modelado hoy en nivel TAREA: la
> segunda `ESPERAR_PLAZO` de `ANUNCIO_BOE`/`ANUNCIO_BOP`/`ANUNCIO_PRENSA` (ids
> 8/9/10 en BD; 30 días naturales; `campo_fecha:
> {"rol":"CONSUMIDO","tipo_documento":"ANUNCIO_PUBLICADO"}`) — el
> `tipo_documento` distingue esa espera de la primera, que aguarda
> indefinidamente a que la publicación exista — sin fila propia en
> `catalogo_plazos` (**#789**, cerrado por diseño: ver §2.4).
> `ANUNCIO_BOJA` no tiene fila propia todavía (hueco de poblado señalado en
> #788 §10). Las tres filas existentes llevan `norma_origen` en `PLACEHOLDER`
> pendiente de cita exacta — deuda de **#782**, no de este issue.

**Diferencias respecto al seed previo (172, código muerto):** descartado `RESOLUCION_AE` (sin sufijo — no existe ese tipo_solicitud); añadido `RESOLUCION_DUP` (procedimiento DUP autónomo, ausente del 172); CIERRE corregido (art. 137 → art. 138; el 137 corresponde al informe del operador, no a la resolución; RD 88/2026 solo modifica art. 137); combinadas con AAC (`AAP+AAC`, `AAP+AAC+DUP`, `AAC+DUP`) consolidadas en la fila AAC porque art. 131.7 fija el plazo conjunto; `AE_DEFINITIVA+AAT` consume el plazo de AE_DEFINITIVA.

**Fuera de scope del hotfix (deuda de #247):** plazos de RESOLUCION para `RAIPEE_PREVIA`, `RAIPEE_DEFINITIVA`, `RADNE`, `AMPLIACION_PLAZO`, `CORRECCION_ERRORES`, `DESISTIMIENTO`, `RENUNCIA`, `RECURSO`, `INTERESADO`, `OTRO`.

> **Nota INFORMACION_PUBLICA:** trámite condicional. Suprimido bajo Decreto 9/2011 DA 1ª (AT 3ª categoría ≤ 30 kV, línea subterránea o CT interior, suelo urbano/urbanizable, sin DUP) y bajo DL 26/2021 DF 4ª (cualquier instalación del Título VII sin DUP y sin AAU). Ver `NORMATIVA_EXCEPCIONES_AT.md §3.1` y `§4.1`.

#### Plazos condicionados de resolución (sujeto: el administrado)

| Tipo elemento ID | Campo inicio cómputo | Valor | Unidad | Efecto vencimiento | Norma origen |
|---|---|---|---|---|---|
| FORMALIZACION_TRANSMISION | fecha_otorgamiento_autorizacion | 6 | MESES | PRESCRIPCION_CONDICIONADO | Art. 133 RD 1955/2000 — caducidad de la autorización de transmisión si no se formaliza |

#### Trámites — plazos de consultas y traslados

> **Nota 2026-04-19, superada por #788.** Esta nota proponía navegar desde el
> Trámite a su tarea hija (`via_tarea_tipo`) para alcanzar el documento. Esa
> indirección llegó a implementarse (`{"via_tarea_tipo": "ESPERAR_PLAZO",
> "rol": "CONSUMIDO"}`) y #788 la retiró: el nivel TRAMITE no porta fecha
> administrativa (§2.bis) y no puede tener fila propia. La fila vive
> directamente en la tarea `ESPERAR_PLAZO`, con `campo_fecha: {"rol":
> "CONSUMIDO"}` — sin indirección, porque ya es la tarea la que se evalúa.

| Tipo elemento ID | Campo inicio cómputo | Valor | Unidad | Efecto vencimiento | Norma origen |
|---|---|---|---|---|---|
| TRASLADO_ALEGACIONES_AAP | `{"rol": "CONSUMIDO"}` — formato resuelto por #788 | 15 | DIAS_NATURALES | SIN_EFECTO_AUTOMATICO | Art. 126 RD 1955/2000 |
| ~~INFORME_AAPP_AAP~~ | ~~INFORME_AAPP_AAP~~ no existe. El trámite canónico es **`CONSULTA_SEPARATA`** (DISEÑO_CONSULTAS_ORGANISMOS.md §4), a nivel de **TAREA** desde #788 (antes decía «fase CONSULTAS»: ninguna fase porta fecha, ver §2.bis). | — | — | — | — |
| TRASLADO_CONDICIONADO_AAP | `{"rol": "CONSUMIDO"}` — formato resuelto por #788 | 15 | DIAS_NATURALES | SIN_EFECTO_AUTOMATICO | Art. 127 RD 1955/2000 |
| REPLICA_AAPP_AAP | `{"rol": "CONSUMIDO"}` — formato resuelto por #788 | 15 | DIAS_NATURALES | CONFORMIDAD_PRESUNTA | Art. 127 RD 1955/2000 |
| ~~INFORME_AAPP_AAC~~ | ~~INFORME_AAPP_AAC~~ no existe. El plazo del art. 131 se gestiona a nivel de **TAREA** desde #788 (antes «fase CONSULTAS» — misma corrección). | — | — | — | — |
| TRASLADO_CONDICIONADO_AAC | `{"rol": "CONSUMIDO"}` — formato resuelto por #788 | 15 | DIAS_NATURALES | SIN_EFECTO_AUTOMATICO | Art. 131 RD 1955/2000 |
| REPLICA_AAPP_AAC | `{"rol": "CONSUMIDO"}` — formato resuelto por #788 | 15 | DIAS_NATURALES | CONFORMIDAD_PRESUNTA | Art. 131 RD 1955/2000 |
| INFORME_REE_CIERRE | `{"rol": "CONSUMIDO"}` — formato resuelto por #788 | 3 | MESES | SIN_EFECTO_AUTOMATICO | Art. 137 RD 1955/2000 (mod. RD 88/2026) — silencio: se continúa sin informe |
| INFORME_DGPEM | `{"rol": "CONSUMIDO"}` — formato resuelto por #788 | 2 | MESES | SIN_EFECTO_AUTOMATICO | Art. 114 RD 1955/2000 — solo instalaciones de transporte CCAA; se continúa sin informe |

> **Lo que #788 resuelve aquí y lo que no.** El formato de `campo_fecha` para
> estas filas queda cerrado: es directamente `{"rol": "CONSUMIDO"}` en la
> tarea `ESPERAR_PLAZO` del trámite, sin indirección. **Que cada fila exista
> ya en `catalogo_plazos` es otra pregunta, y no todas la superan.** El
> recuento real de #788 encuentra solo 10 filas de nivel TAREA en toda la
> tabla: `REQUERIMIENTO_SUBSANACION`, `SOLICITUD_INFORME` (una sola, genérica
> — 10 días hábiles art. 80.2, no las cifras específicas de abajo),
> `ANUNCIO_BOE`/`BOP`/`PRENSA` (dos cada uno, vía `CONSULTA_SEPARATA` — dos
> filas), `CONSULTA_TRASLADO_TITULAR`, `CONSULTA_TRASLADO_ORGANISMO` y
> `TABLON_AYUNTAMIENTOS`. `INFORME_REE_CIERRE` e `INFORME_DGPEM` son además
> plazos **del operador del sistema y de la DGPEM** —terceros, no la
> tramitadora— por lo que #788 §4.2 los excluye de la suspensión del art. 22 y
> puede que no lleguen a necesitar fila propia salvo para seguimiento
> informativo. Los nombres de esta tabla son identificadores heredados del
> seed original (#172); su correspondencia exacta con los trámites reales de
> `ESTRUCTURA_FTT.md` y con las filas ya pobladas no se ha vuelto a verificar
> aquí — deuda de catálogo, no de este issue.

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
- [x] **§3.1 Mapa semántico** — cerrado sesión 2026-04-15; poblar `metadatos_fechas` incrementalmente al implementar cada tipo
- [ ] **§3.3 Suspensiones** — estudiar qué eventos de BDDAT desencadenan cada causa del art. 22 LPACAP antes de diseñar la tabla
- [ ] **§3.4 Calendario inhábiles** — verificar disponibilidad de datos por provincia en la Junta; diseñar mecanismo de alerta de año N+1 sin cargar
- [x] **§3.5 Semántica de `fecha_limite`** — cerrado 2026-04-02
- [ ] **§3.6 Condicionados de resolución** — diseñar nombre y tipos de fase, régimen de plazos (sujeto = administrado), mecanismo de generación desde la resolución, reglas de colisión y distinción visual en UI
- [ ] **§4 Cadena de evaluación** — formalizar contrato de interfaz `plazos.py`
- [x] **Leyes sectoriales (parcial)** — ~~RD 1955/2000~~: ✅ añadido en §5.2 (sesión 2026-04-04). ~~Decreto 9/2011~~: sin plazos propios (suprime trámite). ~~DL 26/2021~~: sin plazos propios (suprime trámite). Pendiente: Ley 21/2013 (EIA) — en revisión previa, ver `normas_catalog.csv`.
- [x] **Revisar #190** — reorientado (2026-04-28): criterio `PLAZO_ESTADO` queda obsoleto; reemplazado por variables motor-agnósticas `estado_plazo`/`efecto_plazo` expuestas via `plazos.py` stub (Fase 2). Lógica real en #172.
- [x] **Revisar #172** — cerrado 2026-04-28: `calcular_fecha_fin` y tablas válidas; deuda de condiciones de aplicabilidad → #341
- [ ] **#341 Condiciones de aplicabilidad en `catalogo_plazos`** — tabla `condiciones_plazo` + campo `orden` + evaluador en `obtener_estado_plazo`; bloqueante para seed real de `catalogo_plazos` (§5.2)
- [ ] **Revisar #173** — actualizar alcance según arquitectura agnóstica
- [ ] **Reutilización de trámites entre expedientes** — art. 95.3: procedimiento caducado cuyo derecho no ha prescrito permite nuevo procedimiento incorporando actos del anterior. Implica modelo de enlace entre expedientes y reutilización del pool documental. Diseñar cuando se estudie normativa sectorial.
