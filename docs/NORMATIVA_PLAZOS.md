# NORMATIVA — Plazos administrativos aplicables a BDDAT

> **Fuente:** Ley 39/2015, de 1 de octubre (LPACAP) — texto consolidado BOE. Leyes sectoriales pendientes de extracción (ver §2).
> **Aplica a:** Motor de plazos (`app/services/plazos.py`), ContextAssembler, diseño de BD de plazos.
> **Estado:** §1 completo (sesión 2026-04-01). §2 pendiente — diferido hasta tener estructura BD definida.

---

## Índice

1. [LPACAP — Marco general de plazos](#1-lpacap--marco-general-de-plazos)
   - [1.1 Plazo máximo para resolver (arts. 21-25)](#11-plazo-máximo-para-resolver-arts-21-25)
   - [1.2 Caducidad del procedimiento y prescripción (arts. 95, 21.1)](#12-caducidad-del-procedimiento-y-prescripción-arts-95-211)
   - [1.3 Plazos del administrado (arts. 68, 73, 82)](#13-plazos-del-administrado-arts-68-73-82)
   - [1.4 Instrucción: prueba, informes e información pública (arts. 77, 80, 83, 88)](#14-instrucción-prueba-informes-e-información-pública-arts-77-80-83-88)
   - [1.5 Tramitación simplificada (art. 96)](#15-tramitación-simplificada-art-96)
   - [1.6 Cómputo de plazos (arts. 29-32)](#16-cómputo-de-plazos-arts-29-32)
   - [1.7 Recursos y sus plazos (arts. 112-126)](#17-recursos-y-sus-plazos-arts-112-126)
2. [Particularizaciones sectoriales](#2-particularizaciones-sectoriales)
   - [2.1 Ley 24/2013 del Sector Eléctrico (LSE)](#21-ley-242013-de-26-de-diciembre-del-sector-eléctrico-lse)

---

## 1. LPACAP — Marco general de plazos

Actúa como **fallback** cuando la norma sectorial no fija un plazo específico.
Ver constantes derivadas en `DISEÑO_FECHAS_PLAZOS.md §5`.

---

### 1.1 Plazo máximo para resolver (arts. 21-25)

#### Art. 21 — Obligación de resolver
- La Administración está obligada a resolver y notificar en todos los procedimientos.
- Plazo máximo: el que fije la **norma sectorial** (máx. 6 meses salvo ley que autorice más).
- Si la norma no lo fija: **3 meses** por defecto.
- Inicio del cómputo:
  - Procedimiento de **oficio** → desde el acuerdo de iniciación.
  - Procedimiento a **solicitud del interesado** → desde la entrada en el registro electrónico.

#### Art. 22 — Suspensión del plazo para resolver
El cómputo se **suspende** (el reloj se para) en estos casos:

| Causa | Duración máxima de la suspensión |
|---|---|
| Requerimiento de subsanación al interesado | Hasta que conteste o expire el plazo concedido |
| Solicitud de informe preceptivo a otro órgano | Máx. 3 meses; si no llega, se reanuda |
| Pronunciamiento previo preceptivo de la UE | Hasta recibir el pronunciamiento |
| Procedimiento UE pendiente que condiciona la resolución | Hasta que se resuelva |
| Pruebas técnicas o análisis contradictorios | Hasta incorporar resultados al expediente |
| Negociaciones para pacto o convenio | Hasta conclusión sin efecto o acuerdo |
| Pronunciamiento judicial previo indispensable | Hasta que la Administración tenga constancia |
| Requerimiento de ilegalidad entre Administraciones (art. 39.5) | Hasta que se atienda o resuelva recurso contencioso |
| Actuaciones complementarias (art. 87) | Hasta su terminación |
| Recusación de funcionario | Hasta resolución por el superior jerárquico |

#### Art. 40 — Obligación de notificar
- La notificación debe cursarse en el plazo de **10 días hábiles** desde que se dicta el acto.
- La obligación de "resolver y notificar" (art. 21) no se cumple solo con dictar la resolución — también exige notificarla dentro de este plazo.

#### Art. 23 — Ampliación del plazo para resolver
- Solo en casos excepcionales (agotados los medios del art. 21.5).
- Máximo: igual al plazo del procedimiento. No cabe recurso contra el acuerdo de ampliación.

#### Art. 24 — Silencio administrativo (procedimientos a solicitud)
- Vencido el plazo sin resolución → silencio **estimatorio** como regla general.
- Silencio **desestimatorio** en: dominio público, servicio público, medio ambiente, impugnación de actos, revisión de oficio.
- Caso especial: recurso de alzada contra silencio desestimatorio → silencio en alzada es **estimatorio**.
- El silencio produce efectos desde el día del vencimiento.

#### Art. 25 — Falta de resolución en procedimientos de oficio
- Procedimientos favorables al interesado → silencio **desestimatorio**.
- Procedimientos de intervención/sanción → **caducidad**.
- Paralización por causa del interesado → el cómputo se **interrumpe** (no suspende).

---

### 1.2 Caducidad del procedimiento y prescripción (arts. 95, 21.1)

#### Art. 95 — Caducidad por inactividad del interesado

Aplica a procedimientos iniciados a solicitud del interesado (es decir, **todos los de BDDAT**).

**Tres escenarios:**

| Escenario | Condición | Efecto |
|---|---|---|
| **Caducidad del procedimiento** | Inactividad del interesado > 3 meses en actividad indispensable para continuar | Advertencia → si persiste → resolución de archivo |
| **Pérdida de trámite** | Inactividad en trámite **no** indispensable para resolver | Solo se pierde ese trámite; el procedimiento continúa |
| **Nuevo procedimiento tras caducidad** | Derecho aún no prescrito → el interesado puede reiniciar | Los actos y trámites del procedimiento caducado pueden incorporarse al nuevo (con obligación de repetir alegaciones, prueba y audiencia) |

**Relación caducidad–prescripción (art. 95.3):**
- La caducidad del procedimiento **no produce** por sí sola la prescripción del derecho.
- Los procedimientos caducados **no interrumpen** el plazo de prescripción del derecho.
- Consecuencia: si el derecho aún no ha prescrito al caducar el procedimiento, el interesado puede iniciar uno nuevo.

> **Implicación en BDDAT:** la reutilización de trámites y documentos de un expediente caducado en uno nuevo requiere diseño específico de modelo de datos y UI. Ver `DISEÑO_FECHAS_PLAZOS.md §7`.

#### Prescripción (art. 21.1 y remisiones)

La LPACAP menciona la prescripción como causa de terminación del procedimiento (art. 21.1) pero **no la regula**: cuando se produce, la resolución la declara. La prescripción del derecho sustantivo la regula la norma sectorial (RD 1955/2000 u otras).

En BDDAT aparece además en una segunda acepción: la resolución propia **prescribe** (ordena) condicionados con plazo, y si no se cumplen, el derecho **prescribe** (caduca). Ver `DISEÑO_FECHAS_PLAZOS.md §2.8`.

---

### 1.3 Plazos del administrado (arts. 68, 82)

#### Art. 68 — Subsanación de la solicitud
- Plazo para subsanar deficiencias: **10 días hábiles** desde el requerimiento.
- Ampliable hasta **5 días hábiles** más a petición del interesado o de oficio, cuando la aportación presente dificultades especiales (salvo procedimientos selectivos o de concurrencia competitiva).
- Si no subsana en plazo → se le tiene por desistido (requiere resolución expresa).

#### Art. 73 — Cumplimiento de trámites
- Plazo general para cumplir cualquier trámite requerido al interesado: **10 días hábiles** desde la notificación, salvo que la norma fije uno distinto.
- Si el acto no reúne los requisitos necesarios, la Administración concede otros **10 días hábiles** para cumplimentarlo.

#### Art. 82 — Trámite de audiencia
- Plazo: **entre 10 y 15 días hábiles** para que el interesado formule alegaciones y aporte documentos antes de la resolución.

---

### 1.4 Instrucción: prueba, informes e información pública (arts. 77, 80, 83, 88)

#### Art. 77 — Período de prueba
- El instructor puede abrir un período de prueba de **entre 10 y 30 días**.

#### Art. 80 — Emisión de informes facultativos
- Plazo para emitir informes: **10 días**, salvo que la norma o el cumplimiento del resto de plazos del procedimiento permita o exija otro plazo.
- Si no se emite en plazo → las actuaciones pueden proseguir salvo que sea preceptivo (ver art. 22 para efectos de suspensión).

#### Art. 83 — Información pública
- El período de información pública no puede ser inferior a **20 días** para formular alegaciones.

#### Art. 88 — Cuestiones conexas en resolución
- Si el órgano resolutor va a pronunciarse sobre cuestiones conexas no planteadas por el interesado, debe dársele audiencia por un plazo máximo de **15 días**.

---

### 1.5 Tramitación simplificada (art. 96)

#### Art. 96 — Tramitación simplificada
- Plazo de resolución: **30 días** desde la notificación del acuerdo de tramitación simplificada (salvo que reste menos para la ordinaria).
- Rechazo de solicitud de tramitación simplificada: **5 días**; transcurrido sin respuesta → desestimación presunta.
- Dictamen urgente del Consejo de Estado u órgano equivalente: **15 días** si así se solicita.
- Aplicación en BDDAT: sin casos conocidos en AT andaluz desde 2015 — ver `DISEÑO_FECHAS_PLAZOS.md §2.7`.

---

### 1.6 Cómputo de plazos (arts. 29-32)

#### Art. 29 — Los plazos obligan a ambas partes
Tanto a la Administración como a los interesados.

#### Art. 30 — Reglas de cómputo

| Tipo de plazo | Regla |
|---|---|
| En **horas** | Todas las horas de un día hábil son hábiles |
| En **días** (sin calificar) | **Hábiles** por defecto — excluye sábados, domingos y festivos |
| En **días naturales** | Debe declararlo expresamente la ley |
| En **meses o años** | Desde el día siguiente a la notificación; vence el mismo día ordinal del mes/año de vencimiento |
| Último día inhábil | Se prorroga al primer día hábil siguiente |
| Conflicto hábil/inhábil entre municipio e interesado y sede del órgano | **Inhábil en todo caso** |

- El cómputo empieza el **día siguiente** a la notificación o publicación del acto.
- Si el mes de vencimiento no tiene el día ordinal equivalente → último día del mes.
- Cada Comunidad Autónoma publica su calendario de inhábiles antes del 1 de enero.

#### Art. 31 — Registro electrónico
- Presentación en día inhábil → se entiende presentada en la **primera hora del primer día hábil siguiente**.
- La fecha de inicio del cómputo para la Administración = fecha y hora de presentación en registro.

#### Art. 32 — Ampliación de plazos (a petición o de oficio)
- Hasta la **mitad** del plazo original. Debe solicitarse antes del vencimiento.
- No cabe ampliar un plazo ya vencido.
- Incidencia técnica o ciberincidente → causa de ampliación general.

---

### 1.7 Recursos y sus plazos (arts. 112-126)

#### Recurso de alzada (arts. 121-122)
- Contra actos que **no ponen fin a la vía administrativa**.
- Plazo de interposición: **1 mes** (acto expreso) / en cualquier momento (acto presunto por silencio).
- Plazo de resolución: **3 meses**. Transcurrido sin resolución → desestimación presunta.
- Excepción: si el recurso de alzada impugna un silencio desestimatorio de solicitud → el nuevo silencio es **estimatorio**.
- Contra la resolución de alzada → no cabe recurso administrativo (solo revisión extraordinaria o contencioso-administrativo).

#### Recurso de reposición potestativo (arts. 123-124)
- Contra actos que **ponen fin a la vía administrativa**.
- Plazo de interposición: **1 mes** (acto expreso).
- Plazo de resolución: **1 mes**. Transcurrido sin resolución → desestimación presunta → abre vía contencioso-administrativa.
- No cabe segundo recurso de reposición contra la resolución.

#### Recurso extraordinario de revisión (arts. 113, 125-126)
- Solo contra actos **firmes en vía administrativa**, por causas tasadas (error de hecho, documentos nuevos esenciales, falsedad declarada, prevaricación...).
- Plazo de interposición:
  - Error de hecho → **4 años** desde la notificación de la resolución.
  - Resto de causas → **3 meses** desde el conocimiento de los documentos o sentencia firme.
- Plazo de resolución: **3 meses**. Transcurrido → desestimación presunta.

#### Otros aspectos relevantes (arts. 116-120)
- **Art. 116.d** — Inadmisión por plazo expirado de interposición.
- **Art. 117** — La interposición de recurso **no suspende** la ejecución del acto, salvo acuerdo motivado. Si no resuelven la solicitud de suspensión en **1 mes** → silencio positivo (suspensión automática).
- **Art. 118** — Audiencia en recursos por hechos nuevos: **10-15 días** para alegaciones.
- **Art. 120** — Pluralidad de recursos: cabe suspender el plazo para resolver si hay recurso judicial paralelo.

---

## 2. Particularizaciones sectoriales

> **Estado:** En desarrollo — sesión 2026-04-02.

Normas pendientes de extracción:
- **RD 1955/2000** — Plazos del procedimiento de autorización de instalaciones eléctricas.
- **Decreto 9/2011** (Junta de Andalucía) — Agilización; posibles modificaciones de plazos estándar.
- **Ley 21/2013** — Plazos del procedimiento de EIA (consultas, información pública, pronunciamiento ambiental).
- **Decreto-ley 26/2021** — Simplificación; excepciones procedimentales.

---

### 2.1 Ley 24/2013, de 26 de diciembre, del Sector Eléctrico (LSE)

> **BOE-A-2013-13645** — texto consolidado. Sesión 2026-04-02.

La LSE establece el **marco** del régimen de autorizaciones pero **no fija plazos concretos de resolución** para las autorizaciones ordinarias de instalaciones — los delega a sus disposiciones de desarrollo (principalmente RD 1955/2000 y, en Andalucía, Decreto 9/2011).

#### Art. 53 — Autorización de instalaciones

Define los tres tipos de autorización que estructuran el procedimiento en BDDAT:

| Tipo | Sigla | Descripción |
|---|---|---|
| Autorización administrativa previa | AAP | Se tramita con el anteproyecto; en su caso, conjuntamente con la EIA (Ley 21/2013). Otorga el derecho a realizar la instalación en determinadas condiciones. |
| Autorización administrativa de construcción | AAC | Permite ejecutar la obra. Requiere proyecto de ejecución y declaración responsable. Se analizan exclusivamente condicionados técnicos de otras Administraciones sobre bienes de su propiedad afectados. |
| Autorización de explotación | AE | Permite poner en tensión y explotar la instalación una vez ejecutado el proyecto. |

AAP y AAC pueden tramitarse de forma consecutiva, coetánea o conjunta (art. 53.1).

**Plazos fijados en el propio art. 53:**

| Supuesto | Plazo | Efecto del vencimiento |
|---|---|---|
| Resolución sobre solicitudes de **cierre definitivo** | 6 meses | Si vence y el operador del sistema lleva ≥ 3 meses con informe favorable → el titular puede cerrar sin resolución |
| Autorizaciones competencia de la **AGE** (no BDDAT) | 1 año | Silencio desestimatorio (art. 53.8) |

> Para instalaciones competencia de las **CCAA** (ámbito de BDDAT), el plazo concreto de resolución lo fija la norma autonómica de desarrollo. Ver §2.2 (RD 1955/2000) y §2.3 (Decreto 9/2011).

#### DA 3ª — Silencio administrativo

Regla general para todas las solicitudes amparadas en la LSE: **silencio desestimatorio**. El plazo a partir del cual opera lo establecen las disposiciones de desarrollo.

> **Implicación en BDDAT:** confirma que el silencio en los procedimientos de autorización de AT es desestimatorio. El plazo concreto vendrá del RD 1955/2000 / Decreto 9/2011.

#### Nomenclatura

La LSE utiliza "**autorización de explotación**" (sin "administrativa") en todos los casos (art. 53.1.c y concordantes). Si el RD 1955/2000 o el Decreto 9/2011 utilizan "autorización administrativa de explotación", prevalecerá el término de la norma procedimental aplicable. Pendiente de verificar en §2.2.
