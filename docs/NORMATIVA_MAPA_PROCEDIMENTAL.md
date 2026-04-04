# NORMATIVA — Mapa procedimental por tipo de solicitud

> **Aplica a:** Motor de reglas — fases obligatorias, su orden y base legal por tipo de solicitud.
> **Fuentes de verdad:** `docs/NORMATIVA_LEGISLACION_AT.md §6` (catálogo normativo) · `docs/NORMATIVA_PLAZOS.md §2` (plazos concretos).
> **Estado:** En construcción — sesiones 2026-04-02 / 2026-04-04. LSE + RD 1955/2000 (incl. modificaciones) extraídos.

Este documento responde a la **Iteración 1** de `NORMATIVA_LEGISLACION_AT.md §5`:
para cada tipo de solicitud, qué procedimiento define la legislación, qué fases lo componen,
en qué orden son obligatorias y cuál es su base legal.

El mapeo a tipos BDDAT (relación entre tipos de solicitud del sistema y procedimientos legales)
se documenta en `docs/NORMATIVA_SOLICITUDES.md`.

---

## Índice

| § | Contenido |
|---|---|
| [§1](#1-lse-242013--procedimientos-autorizatorios) | LSE 24/2013 — tipos de autorización y relación entre ellos |
| [§2](#2-rd-19552000--fases-detalladas-por-procedimiento) | RD 1955/2000 — fases detalladas por procedimiento |

---

## 1. LSE 24/2013 — Procedimientos autorizatorios

> Base: **art. 53 LSE**. Sesión 2026-04-02.

La LSE define tres autorizaciones para instalaciones nuevas y cuatro procedimientos
adicionales para situaciones posteriores a la puesta en servicio:

| Procedimiento | Sigla | Momento | Base legal |
|---|---|---|---|
| Autorización administrativa previa | AAP | Antes de construir (anteproyecto) | Art. 53.1.a LSE |
| Autorización administrativa de construcción | AAC | Antes de ejecutar obra (proyecto de ejecución) | Art. 53.1.b LSE |
| Autorización de explotación | AE | Antes de poner en tensión/explotar | Art. 53.1.c LSE |
| Declaración de utilidad pública | DUP | Puede tramitarse junto a AAP | Art. 54 LSE |
| Transmisión de titularidad | Trans. | Cambio de titular | Art. 53 + RD 1955/2000 |
| Modificación de instalación | Mod. | Cambios sobre instalación autorizada | Art. 53 + RD 1955/2000 |
| Cierre definitivo | Cierre | Fin de vida de la instalación | Art. 53 + RD 1955/2000 |

### Relación entre procedimientos

- **Secuencia estándar:** AAP → AAC → AE (pueden tramitarse de forma consecutiva, coetánea o conjunta — art. 53.1 LSE).
- **DUP:** puede tramitarse conjuntamente con la AAP en una misma información pública (RD 1955/2000 art. 125).
- **AAC sin AAP previa:** posible cuando la instalación no requiere AAP por estar exenta o por haberse tramitado en un procedimiento conjunto.
- **Modificaciones:** si el cambio es sustancial puede requerir nueva AAP+AAC; si es menor, solo AAC o comunicación.

### Competencia (Andalucía — BDDAT)

Para instalaciones **intra-CCAA** (ámbito de BDDAT), la competencia de tramitación y resolución
corresponde a la Junta de Andalucía, delegada en las Delegaciones Territoriales
(Resolución de 9 de marzo de 2016 — ver `NORMATIVA_LEGISLACION_AT.md §6.1`).

La norma procedimental aplicable es el RD 1955/2000 como referencia (Andalucía no tiene
norma procedimental propia equivalente — ver §2.2 NORMATIVA_PLAZOS).

---

## 2. RD 1955/2000 — Fases detalladas por procedimiento

> Base: **arts. 111-139 RD 1955/2000** (Título VII). Sesión 2026-04-02.
> Plazos concretos de cada trámite: ver `docs/NORMATIVA_PLAZOS.md §2.2`.

### 2.1 AAP — Autorización Administrativa Previa (arts. 122-128)

Fases en orden:

| # | Fase / Trámite | Obligatorio | Base |
|---|---|---|---|
| 1 | Presentación de solicitud con anteproyecto | ✅ | Art. 122-123 |
| 2 | Verificación de documentación / subsanación | ✅ | LPACAP art. 68 |
| 3 | Información pública (30 días) | ⚠️ Condicional — ver nota | Art. 125 |
| 3b | Información pública conjunta con DUP | Condicional — si se solicita DUP | Art. 125 |
| 4 | Traslado de alegaciones al peticionario (15 días) | ✅ si hay alegaciones | Art. 126 |
| 5 | Consultas e informes a otras AAPP sobre bienes a su cargo (30 días, silencio = conformidad) | ✅ | Art. 127 |
| 6 | Traslado del resultado al peticionario (15 días) | ✅ | Art. 127 |
| 7 | Réplica de las AAPP a los reparos del peticionario (15 días, silencio = conformidad) | Condicional — si hay reparos | Art. 127 |
| 8 | Informe DGPEM — solo instalaciones de transporte tramitadas por CCAA (2 meses) | Condicional | Art. 114 |
| 9 | **Resolución** (3 meses desde solicitud; silencio desestimatorio) | ✅ | Art. 128 |

> **Nota información pública (fase 3):** la información pública es **obligatoria con carácter general**, pero queda **suprimida** cuando se cumplen los cuatro criterios del Decreto 9/2011 DA 1ª: tensión ≤ 30 kV (tercera categoría AT), línea subterránea o centro de transformación interior, suelo urbano/urbanizable, y sin DUP. En ese caso también se suprime la publicación de la resolución en el BOP (art. 128.3). Ver `NORMATIVA_EXCEPCIONES_AT.md §3.1`.

> **Nota EIA:** cuando la instalación requiere Evaluación de Impacto Ambiental ordinaria
> (Ley 21/2013), la AAP no puede resolverse sin la Declaración de Impacto Ambiental (DIA).
> La tramitación ambiental corre en paralelo pero su finalización es condición de la resolución.
> Esto implica una suspensión de facto del plazo de resolución. Ver `NORMATIVA_EXCEPCIONES_AT.md §2`.

### 2.2 AAC — Autorización Administrativa de Construcción (arts. 130-131)

Fases en orden:

| # | Fase / Trámite | Obligatorio | Base |
|---|---|---|---|
| 1 | Presentación de solicitud con proyecto de ejecución | ✅ | Art. 130 |
| 2 | Verificación de documentación / subsanación | ✅ | LPACAP art. 68 |
| 3 | Consultas a AAPP sobre bienes afectados (30 días o 15 días — ver nota) | ✅ | Art. 131 |
| 4 | Traslado del condicionado al peticionario (15 días) | ✅ | Art. 131 |
| 5 | Réplica de las AAPP a los reparos del peticionario (15 días, silencio = conformidad) | Condicional — si hay reparos | Art. 131 |
| 6 | **Resolución** (3 meses desde solicitud; silencio desestimatorio) | ✅ | Art. 131.7 |

> **Plazo reducido:** si la instalación ya tiene AAP y la tramitación es solo AAC
> (sin DUP ni modificación de AAP), el plazo de consultas a AAPP se reduce de 30 a 15 días.
> Ver `NORMATIVA_EXCEPCIONES_AT.md §2.2`.

### 2.3 AE — Autorización de Explotación (arts. 132, 132 bis, 132 ter, 132 quater)

El procedimiento varía según el tipo de instalación:

#### Instalaciones de transporte y distribución

| # | Fase / Trámite | Obligatorio | Base |
|---|---|---|---|
| 1 | Presentación de solicitud con acta de puesta en servicio / certificado final | ✅ | Art. 132 |
| 2 | **Resolución AE definitiva** (1 mes; silencio desestimatorio — DA 3ª LSE) | ✅ | Art. 132 |

#### Instalaciones de generación

| # | Fase / Trámite | Obligatorio | Base |
|---|---|---|---|
| 1 | Presentación de solicitud | ✅ | Art. 132 bis |
| 2 | **Resolución AE provisional** para pruebas (1 mes; silencio desestimatorio) | ✅ | Art. 132 bis |
| 3 | Período de pruebas de la instalación | ✅ | Art. 132 bis |
| 4 | **Resolución AE definitiva** (1 mes desde solicitud; silencio desestimatorio) | ✅ | Art. 132 ter |

### 2.4 Transmisión de titularidad (arts. 133-134)

| # | Fase / Trámite | Obligatorio | Base |
|---|---|---|---|
| 1 | Solicitud conjunta del transmitente y adquirente | ✅ | Art. 133 |
| 2 | **Resolución** (3 meses; silencio desestimatorio) | ✅ | Art. 133 |
| 3 | Formalización de la transmisión (plazo 6 meses desde otorgamiento; si vence → caducidad) | ✅ | Art. 133 |
| 4 | Comunicación del adquirente a la DGPEM (1 mes desde que se hace efectiva) | ✅ | Art. 134 |

### 2.5 Cierre definitivo (arts. 135-139)

| # | Fase / Trámite | Obligatorio | Base |
|---|---|---|---|
| 1 | Solicitud del titular | ✅ | Art. 135 |
| 2 | Informe del operador del sistema (REE) (3 meses; silencio: se continúa sin informe) | ✅ | Art. 136 |
| 3 | **Resolución** (3 meses; silencio desestimatorio) | ✅ | Art. 137 |
| 4 | Ejecución del cierre en el plazo fijado en la resolución (si vence → caducidad) | ✅ | Art. 138 |

> **Régimen especial cierre AGE (LSE art. 53):** si pasan 6 meses desde la solicitud
> y el operador del sistema lleva ≥3 meses con informe favorable, el titular puede cerrar
> sin esperar resolución. Este régimen es de la AGE; para instalaciones CCAA ver norma autonómica.
> Ver `NORMATIVA_EXCEPCIONES_AT.md §2.3`.

### 2.6 Modificación de instalación (art. 115)

> Base: **art. 115 RD 1955/2000** (última actualización: 24-07-2025) + **art. 53.2 LSE 24/2013**.

El art. 115 define tres niveles de exigencia para las modificaciones de instalaciones
que ya cuentan con autorización. El nivel determina qué autorizaciones se requieren:

| Nivel | Denominación | Autorizaciones requeridas | Base legal |
|---|---|---|---|
| 1 | Modificación sustancial | Nueva AAP + AAC (+ AE) | Art. 115.1 — régimen general |
| 2 | Modificación con AAC sin nueva AAP | Solo AAC (+ AE) | Art. 115.2 |
| 3 | Modificación no sustancial | Solo AE | Art. 115.3 + art. 53.2 LSE |

> **Secuencia de evaluación:** comprobar primero el nivel 3 (solo AE); si no lo cumple, nivel 2 (solo AAC); si tampoco, nivel 1 (AAP + AAC completa).

#### Nivel 1 — Modificación sustancial (art. 115.1)

**Regla general:** toda modificación requiere nueva AAP + AAC + AE (procedimiento completo).
Se aplica cuando no se cumplen las condiciones de nivel 2 ni de nivel 3.
El procedimiento es idéntico al de una instalación nueva — ver §2.1 (AAP) y §2.2 (AAC).

#### Nivel 2 — Modificación con AAC sin nueva AAP (art. 115.2)

Puede obtenerse AAC sin requerir nueva AAP cuando se cumplen **todas** las condiciones del grupo aplicable según el tipo de instalación.

**Instalaciones de generación:**

| Condición | Descripción |
|---|---|
| Sin EIA ordinaria | Las modificaciones no son objeto de evaluación ambiental ordinaria (art. 7.1 Ley 21/2013) |
| Terrenos en poligonal | Los terrenos afectados no exceden la poligonal del proyecto autorizado, o si la exceden: sin expropiación forzosa y con compatibilidad urbanística |
| Potencia ≤ 15% | La potencia instalada tras la modificación no excede en más del 15% la del proyecto original |
| Sin cambio de tecnología | No hay cambio en la tecnología de generación |
| Sin riesgo de seguridad | No hay alteraciones de seguridad de la instalación principal ni de sus auxiliares en servicio |
| Sin DUP | No se requiere declaración de utilidad pública para las modificaciones |
| Sin afección a terceros | Las modificaciones no producen afecciones sobre otras instalaciones de producción en servicio |

**Instalaciones de transporte y distribución:**

| Condición | Descripción |
|---|---|
| Sin EIA ordinaria | Las modificaciones no son objeto de evaluación ambiental ordinaria (art. 7.1 Ley 21/2013) |
| Sin exceder AAP/DIA | No se producen cambios que excedan las condiciones de la AAP concedida y de la DIA |
| Sin riesgo de seguridad | No hay alteraciones de seguridad de la instalación principal ni de sus auxiliares en servicio |
| Sin DUP | No se requiere declaración de utilidad pública para las modificaciones |
| *(subestaciones)* Posiciones de reserva | Exclusivamente: equipamiento de posiciones de reserva ya autorizadas, o renovación de equipos sin cambio de características técnicas |
| *(líneas)* Repotenciación | Retensado o cambio de conductores, recrecido de apoyos, o instalación de dispositivos electrónicos |

> Las dos últimas condiciones son específicas de cada tipo de elemento (subestación o línea), no es necesario cumplir ambas.

#### Nivel 3 — Modificación no sustancial (art. 115.3 + art. 53.2 LSE)

Solo se requiere AE cuando se cumplen **todas** las condiciones siguientes:

| Condición | Descripción |
|---|---|
| Sin EIA | No está dentro del ámbito de aplicación de la Ley 21/2013 |
| Variación técnica ≤ 10% | No supone alteración de características técnicas básicas (potencia, capacidad de transformación o transporte, etc.) superior al 10% de la potencia de la instalación |
| Sin riesgo de seguridad | No supone alteraciones de seguridad de la instalación principal ni de sus auxiliares en servicio |
| Sin DUP | No se requiere declaración de utilidad pública |
| *(líneas)* Sin cambio de servidumbre | Las modificaciones de líneas no provocan cambios de servidumbre sobre el trazado |
| *(líneas)* Cambio de servidumbre con acuerdo | Si hay cambio de servidumbre sin modificar el trazado: acuerdo mutuo con los afectados (art. 151 RD 1955/2000) |
| *(líneas)* Sustitución por deterioro | Sustitución de apoyos o conductores por deterioro o rotura, manteniendo las condiciones del proyecto original |
| *(subestaciones)* Sin variación de calles/posiciones | La modificación de configuración de subestación no varía el número de calles ni de posiciones |
| *(transporte/distribución)* Sin cambios retributivos | La modificación no implica cambios retributivos |

> **Implicación en BDDAT:** el motor debe evaluar el nivel de modificación antes de asignar las solicitudes requeridas. Los plazos de AAP y AAC en modificaciones son los mismos que para instalaciones nuevas — ver `NORMATIVA_PLAZOS.md §2.2`.

> **Cola de trabajo:** las normas pendientes de extracción se gestionan en `docs/GUIA_NORMAS.md §4`.
