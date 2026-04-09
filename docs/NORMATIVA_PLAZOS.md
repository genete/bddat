# NORMATIVA — Plazos administrativos aplicables a BDDAT

> **Fuente:** Ley 39/2015, de 1 de octubre (LPACAP) — texto consolidado BOE. Leyes sectoriales pendientes de extracción (ver §2).
> **Aplica a:** Motor de plazos (`app/services/plazos.py`), ContextAssembler, diseño de BD de plazos.
> **Estado:** §1 completo (sesión 2026-04-01). §2.1 LSE, §2.2 RD1955, §2.3 RD-ley 23/2020, §2.4 RD-ley 6/2022+20/2022, §2.5 Ley 21/2013 EIA completos (sesión 2026-04-09). Decreto 9/2011, DL 2/2018, RAT y LAT revisados — sin plazos de autorización propios, notas en listado §2 (sesión 2026-04-09). §2.6 Ley 2/2026 y §2.7 Decreto 356/2010 pendientes.

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
   - [2.2 Real Decreto 1955/2000](#22-real-decreto-19552000-de-1-de-diciembre-rd-19552000)
   - [2.3 RD-ley 23/2020 — hitos del administrado](#23-rd-ley-232020-de-23-de-junio--hitos-del-administrado)
   - [2.4 RD-ley 6/2022 + RD-ley 20/2022 — afección ambiental y tramitación conjunta renovables](#24-rd-ley-62022-de-29-de-marzo--rd-ley-202022-de-27-de-diciembre)
   - [2.5 Ley 21/2013 — EIA: plazos del procedimiento ambiental](#25-ley-212013-de-9-de-diciembre--eia-plazos-del-procedimiento-ambiental)
   - [2.6 Ley 2/2026 — AAU y AAUS: plazos del procedimiento de prevención ambiental](#26-ley-22026-de-12-de-marzo--aau-y-aaus-plazos-del-procedimiento-de-prevención-ambiental)
   - [2.7 Decreto 356/2010 — AAU y AAUS: plazos régimen GICA (expedientes < 20/06/2026)](#27-decreto-3562010--aau-y-aaus-plazos-régimen-gica-expedientes--20062026)
3. [API de días inhábiles — Junta de Andalucía](#3-api-de-días-inhábiles--junta-de-andalucía)
   - [3.1 Descripción](#31-descripción)
   - [3.2 Endpoints](#32-endpoints)
   - [3.3 Parámetros del endpoint principal](#33-parámetros-del-endpoint-principal)
   - [3.4 Estructura de cada registro en la respuesta](#34-estructura-de-cada-registro-en-la-respuesta)
   - [3.5 Festivos locales de Cádiz capital (referencia)](#35-festivos-locales-de-cádiz-capital-referencia)
   - [3.6 Nota de implementación](#36-nota-de-implementación)

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

> **Decisión de diseño BDDAT (art. 30.2):** la regla del "inhábil en todo caso" exigiría conocer el municipio del interesado para tomar la unión de calendarios. En la práctica esto no es computable: (a) ningún formulario de la Consejería recoge ese dato a efectos del art. 30.2; (b) para personas jurídicas no está definido qué domicilio aplica (social, fiscal o el de notificaciones); (c) con administración electrónica el supuesto de hecho casi no se da. **BDDAT calcula los plazos exclusivamente con el calendario de la sede del órgano (Cádiz/Cádiz).** Si la SGE decide incorporar el municipio del interesado en el futuro, será una decisión jurídica externa al sistema.

- El cómputo empieza el **día siguiente** a la notificación o publicación del acto.
- Si el mes de vencimiento no tiene el día ordinal equivalente → último día del mes.
- Cada Comunidad Autónoma publica su calendario de inhábiles antes del 1 de enero. → [Calendario de días inhábiles de la CA y Municipios de Andalucía](https://www.juntadeandalucia.es/servicios/tramites/conoce-mas-cts.html#toc-c-mo-calcular-los-plazos-de-un-tr-mite)

#### Art. 31 — Registro electrónico
- Presentación en día inhábil → se entiende presentada en la **primera hora del primer día hábil siguiente**.
- La fecha de inicio del cómputo para la Administración = fecha y hora de presentación en registro.

#### Art. 32 — Ampliación de plazos (a petición o de oficio)
- Hasta la **mitad** del plazo original. Debe solicitarse antes del vencimiento.
- No cabe ampliar un plazo ya vencido.
- Incidencia técnica o ciberincidente → causa de ampliación general.

> **Implicación en BDDAT:** la ampliación es un evento que modifica la fecha de vencimiento de un plazo ya en curso. Los plazos no pueden modelarse como fechas fijas — necesitan soportar extensiones registradas. Cada ampliación debe guardar: fecha del acuerdo, plazo original, días ampliados (≤ mitad del original) y nueva fecha de vencimiento. El motor de plazos debe rechazar ampliaciones sobre plazos ya vencidos. Ver `DISEÑO_FECHAS_PLAZOS.md` cuando se desarrolle.

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

> **Estado:** En desarrollo — sesiones 2026-04-02/03/05/06.

Normas pendientes de extracción:
- ~~**RD 1955/2000**~~ — ✅ Extraído en §2.2.
- ~~**Decreto 9/2011**~~ — ✅ Sin plazos propios; suprime la información pública (30 días) para AT tercera categoría en suelo urbano sin DUP. Nota añadida en §2.2. Ver `NORMATIVA_EXCEPCIONES_AT.md §3.1`.
- **Ley 21/2013** — Plazos del procedimiento de EIA (consultas, información pública, pronunciamiento ambiental).
- ~~**Decreto-ley 26/2021**~~ — ✅ Sin plazos propios; exime de información pública instalaciones sin DUP y sin AAU (DF 4ª). Ver `NORMATIVA_EXCEPCIONES_AT.md §4.1`.
- ~~**RD-ley 23/2020**~~ — ✅ Extraído en §2.3. Plazos son del administrado (promotor), no de la Administración.
- ~~**Decreto-ley 2/2018**~~ — ✅ Sin plazos de resolución propios. Modifica AE para instalaciones de producción ≤ 500 kW → puesta en servicio industrial (DA única apdo. 2). Nota añadida en `NORMATIVA_MAPA_PROCEDIMENTAL.md §2.3`. Ver `NORMATIVA_EXCEPCIONES_AT.md §7.2`.
- ~~**RD 337/2014 (RAT)**~~ — ✅ Sin plazos de autorización propios para AAP/AAC/AE. Introduce silencio **positivo** de 3 meses para aprobación de especificaciones particulares de PTD (art. 14.4). Plazos de explotación/inspección fuera del alcance del motor. Ver `NORMATIVA_EXCEPCIONES_AT.md §10`.
- ~~**RD 223/2008 (LAT)**~~ — ✅ Sin plazos de autorización propios. Mismo silencio positivo de 3 meses para especificaciones PTD (art. 15.4). Plazos de mantenimiento/inspección (3 años periódicas, 6 años puesta a tierra) fuera del alcance del motor. Ver `NORMATIVA_EXCEPCIONES_AT.md §11`.

---

### 2.1 Ley 24/2013, de 26 de diciembre, del Sector Eléctrico (LSE)

> **BOE-A-2013-13645** — texto consolidado. Sesión 2026-04-02.

La LSE establece el **marco** del régimen de autorizaciones pero **no fija plazos concretos de resolución** para las autorizaciones ordinarias de instalaciones — los delega a sus disposiciones de desarrollo (principalmente RD 1955/2000).

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

> Para instalaciones competencia de las **CCAA** (ámbito de BDDAT), el plazo concreto de resolución lo fija la norma autonómica aplicable. Ver §2.2 (RD 1955/2000 como referencia).

#### DA 3ª — Silencio administrativo

Regla general para todas las solicitudes amparadas en la LSE: **silencio desestimatorio**. El plazo a partir del cual opera lo establecen las disposiciones de desarrollo.

> **Implicación en BDDAT:** confirma que el silencio en los procedimientos de autorización de AT es desestimatorio. El plazo concreto vendrá del RD 1955/2000 (§2.2).

#### Nomenclatura

La LSE utiliza "**autorización de explotación**" (sin "administrativa") en todos los casos (art. 53.1.c y concordantes). El RD 1955/2000 (§2.2) **confirma** el mismo término — no "autorización administrativa de explotación".

---

### 2.2 Real Decreto 1955/2000, de 1 de diciembre (RD 1955/2000)

> **BOE-A-2000-24019** — texto consolidado. Sesión 2026-04-02.

#### Advertencia de base legal

El RD 1955/2000 fue dictado en desarrollo de la **Ley 54/1997** del Sector Eléctrico (derogada). Sigue vigente pero con adaptaciones sucesivas: sus referencias a la Ley 54/1997 deben leerse como referencias a la **Ley 24/2013** (LSE vigente), y sus referencias a la **Ley 30/1992** (derogada) como referencias a la **Ley 39/2015** (LPACAP).

> **Implicación en BDDAT:** cuando el RD cite plazos o efectos vinculados a artículos de leyes derogadas, verificar si el artículo equivalente de la norma vigente mantiene el mismo régimen. En caso de duda, prevalece la LSE 24/2013 y la LPACAP 39/2015.

#### Ámbito de aplicación (art. 111)

El **Título VII** del RD 1955/2000 regula el procedimiento de autorización para instalaciones cuyo aprovechamiento **afecta a más de una Comunidad Autónoma** (competencia AGE).

Para instalaciones **intra-CCAA** (ámbito de BDDAT), la competencia corresponde a la Comunidad Autónoma. Andalucía no tiene norma procedimental propia equivalente — el RD 1955/2000 actúa como **norma de referencia** para el esquema de trámites.

#### Informe DGPEM para instalaciones de transporte competencia CCAA (art. 114)

Cuando la CCAA tramita una autorización de instalación de **transporte**, debe solicitar informe previo a la Dirección General de Política Energética y Minas (DGPEM):

| Plazo de emisión | Efecto del silencio |
|---|---|
| **2 meses** | Se prosiguen las actuaciones (silencio no equivale a favorable ni a desfavorable) |

> **Naturaleza del informe:** solicitarlo es **obligatorio** para la CCAA. Cuando se emite en plazo, su contenido es **vinculante** — la CCAA debe tenerlo en cuenta en la resolución (art. 114 in fine). La no respuesta en plazo permite continuar formalmente, pero en la práctica la resolución suele esperar al informe: si la instalación no encaja en la planificación estatal de la red, REE no puede construirla ni percibirla en retribución con independencia de lo que resuelva la CCAA. Se han dado casos de informes desfavorables en plazo.
>
> **Efecto sobre plazos:** la solicitud del informe puede suspender el plazo de resolución al amparo del art. 22 LPACAP (solicitud de informe preceptivo a otro órgano, máx. 3 meses de suspensión). Aunque el RD no lo califica expresamente de "preceptivo", la obligatoriedad de solicitarlo y el carácter vinculante de su respuesta apuntan a que opera como tal a efectos de suspensión.

---

#### Procedimiento de Autorización Administrativa Previa — AAP (arts. 122-128)

##### Información pública (art. 125)

| Trámite | Plazo | Efecto del silencio / vencimiento |
|---|---|---|
| Información pública | **30 días** | Fin del período; alegaciones fuera de plazo no se admiten |

> **Excepción — Decreto 9/2011 DA 1ª:** trámite **suprimido** (junto con la publicación en BOP, art. 128.3) para instalaciones AT de tercera categoría (U ≤ 30 kV), línea subterránea o CT interior, suelo urbano/urbanizable, sin DUP. Ver `NORMATIVA_EXCEPCIONES_AT.md §3.1`.

La publicación se efectúa en el BOE y en el Boletín Oficial de la provincia o CCAA. Si se solicita simultáneamente la declaración de utilidad pública, la información pública se efectúa de forma conjunta.

##### Traslado de alegaciones al peticionario (art. 126)

| Trámite | Plazo | Efecto |
|---|---|---|
| Traslado al peticionario para que conteste las alegaciones recibidas | **15 días** (máximo) | — |

##### Informes a otras Administraciones (art. 127)

| Trámite | Plazo | Efecto del silencio |
|---|---|---|
| Informe / conformidad de otras AAPP, organismos y empresas de servicio público sobre bienes a su cargo | **30 días** | **Conformidad presunta** |
| Traslado del resultado al peticionario para que preste conformidad o formule reparos | **15 días** | — |
| Réplica de la AAPP a los reparos del peticionario | **15 días** | **Conformidad** con la contestación del peticionario |
| Informe CNMC sobre capacidad del solicitante (solo AGE; ver nota) | **15 días hábiles** | **Favorable** |

> El informe CNMC (art. 127.6) está previsto para la AGE. En el procedimiento autonómico de la Junta de Andalucía no hay un equivalente identificado hasta ahora.

##### Resolución AAP (art. 128)

| Plazo | Cómputo | Silencio |
|---|---|---|
| **3 meses** | Desde la presentación de la solicitud | **Desestimatorio** |

La resolución debe publicarse en BOE y en el Boletín Oficial de las provincias afectadas.

La autorización fija un **plazo** para que el titular solicite la AAC (aprobación del proyecto de ejecución): si vence sin solicitarla → **caducidad de la AAP** (art. 128.4). El titular puede pedir prórrogas por razones justificadas.

---

#### Procedimiento de Autorización Administrativa de Construcción — AAC / Aprobación proyecto ejecución (arts. 130-131)

##### Condicionados de otras Administraciones (art. 131)

| Trámite | Plazo | Efecto del silencio |
|---|---|---|
| Condicionado técnico de otras AAPP, organismos y empresas de servicio público sobre bienes a su cargo | **30 días** | **Conformidad presunta** |
| — Reducción: si la instalación ya tiene AAP y la tramitación es solo AAC (sin DUP ni modificación de AAP) | **15 días** | **Conformidad presunta** |
| Traslado del condicionado al peticionario para conformidad o reparos | **15 días** | — |
| Réplica de la AAPP a los reparos del peticionario | **15 días** | **Conformidad** con la contestación del peticionario |

##### Resolución AAC (art. 131.7)

| Plazo | Cómputo | Silencio |
|---|---|---|
| **3 meses** | Desde la presentación de la solicitud | **Desestimatorio** |

La resolución fija el período previsto para la ejecución de la instalación (art. 131.10).

---

#### Procedimiento de Autorización de Explotación — AE (arts. 132, 132 bis, 132 ter, 132 quater)

El RD 1955/2000 distingue según tipo de instalación:

| Tipo de instalación | Fase | Plazo desde solicitud | Silencio |
|---|---|---|---|
| Transporte y distribución | AE definitiva (única) | **1 mes** | No regulado → LPACAP + DA 3ª LSE: **desestimatorio** |
| Generación | AE provisional para pruebas | **1 mes** | Ídem |
| Generación | AE definitiva | **1 mes** | Ídem |

La AE provisional para pruebas habilita la puesta en tensión y las pruebas de la instalación antes de la autorización definitiva.

> **Nomenclatura confirmada:** el RD usa "autorización de explotación" (sin "administrativa") — coherente con la LSE 24/2013.

---

#### Procedimiento de transmisión de titularidad (arts. 133-134)

| Trámite / Plazo | Duración | Efecto |
|---|---|---|
| Resolución sobre autorización de transmisión | **3 meses** | Silencio: **desestimatorio** |
| Plazo para formalizar la transmisión una vez autorizada | **6 meses** desde el otorgamiento | Caducidad de la autorización si vence sin transmisión efectiva |
| Comunicación de la transmisión hecha efectiva a la DGPEM | **1 mes** desde que se hace efectiva | Obligación del adquirente |

---

#### Procedimiento de cierre de instalaciones (arts. 135-139)

| Trámite / Plazo | Duración | Efecto del silencio |
|---|---|---|
| Informe del operador del sistema (REE) sobre la solicitud de cierre | **3 meses** | Se continúa el procedimiento sin informe |
| Resolución sobre autorización de cierre | **3 meses** | **Desestimatorio** |

La resolución fija el plazo para ejecutar el cierre (y en su caso el desmantelamiento); si vence → **caducidad** de la autorización de cierre (art. 138.2).

> Para instalaciones CCAA (BDDAT), el plazo de resolución de cierre lo fija la norma autonómica aplicable. La LSE (art. 53) fija 6 meses para el régimen especial de cierre unilateral de instalaciones AGE.

---

#### Suspensiones del plazo específicas del RD 1955/2000

El RD **no regula causas propias de suspensión** del plazo de resolución. Las únicas suspensiones aplicables son las del art. 22 LPACAP. Las más relevantes en la práctica:

| Causa LPACAP (art. 22) | Concreción en este procedimiento |
|---|---|
| Solicitud de informe preceptivo a otro órgano | Informe DGPEM (art. 114) para instalaciones de transporte CCAA — 2 meses. Obligatorio solicitarlo y vinculante si se emite; opera en la práctica como preceptivo a efectos de suspensión (ver nota §2.2 art. 114) |
| Pronunciamiento previo preceptivo (EIA) | Cuando la instalación requiere EIA ordinaria (Ley 21/2013), la AAP no puede resolverse sin la DIA — suspensión de facto mientras dura el trámite ambiental. Ver §2.4 |
| Pruebas técnicas o análisis contradictorios | Puede aplicar en la fase de comprobaciones técnicas previas a la AE |

---

#### Resumen de plazos — tabla consolidada RD 1955/2000

| Procedimiento | Trámite | Plazo | Silencio |
|---|---|---|---|
| **AAP** | Información pública | 30 días | — |
| **AAP** | Traslado alegaciones al peticionario | 15 días (máx.) | — |
| **AAP** | Informe otras AAPP sobre bienes a su cargo | 30 días | Conformidad |
| **AAP** | Traslado condicionado al peticionario | 15 días | — |
| **AAP** | Réplica AAPP a reparos del peticionario | 15 días | Conformidad |
| **AAP** | Informe CNMC (AGE) | 15 días hábiles | Favorable |
| **AAP** | **Resolución** | **3 meses** | **Desestimatorio** |
| **AAC** | Condicionado otras AAPP (régimen general) | 30 días | Conformidad |
| **AAC** | Condicionado otras AAPP (solo AAC, sin DUP) | 15 días | Conformidad |
| **AAC** | Traslado condicionado al peticionario | 15 días | — |
| **AAC** | Réplica AAPP a reparos del peticionario | 15 días | Conformidad |
| **AAC** | **Resolución** | **3 meses** | **Desestimatorio** |
| **AE** (transporte/distribución) | **Resolución** | **1 mes** | Desestimatorio (DA 3ª LSE) |
| **AE provisional pruebas** (generación) | **Resolución** | **1 mes** | Desestimatorio (DA 3ª LSE) |
| **AE definitiva** (generación) | **Resolución** | **1 mes** | Desestimatorio (DA 3ª LSE) |
| **Transmisión** | **Resolución** | **3 meses** | **Desestimatorio** |
| **Transmisión** | Plazo para formalizar tras autorización | 6 meses | Caducidad |
| **Cierre** | Informe REE | 3 meses | Continúa sin informe |
| **Cierre** | **Resolución** | **3 meses** | **Desestimatorio** |
| **Transporte CCAA** | Informe DGPEM (art. 114) | 2 meses | Continúa sin informe |

---

### 2.3 RD-ley 23/2020, de 23 de junio — Hitos del administrado

> **BOE-A-2020-6621** — texto consolidado. Modificado por RD-ley 8/2023 (arts. 28-29). Sesión 2026-04-04.

Los plazos del RD-ley 23/2020 son **obligaciones del promotor** (no del órgano tramitador): son los plazos máximos dentro de los cuales el promotor debe acreditar cada hito ante el gestor de la red para mantener la vigencia de sus permisos de acceso y conexión. La Administración tramita igual independientemente de su estado de cumplimiento.

Para el detalle del régimen de hitos, condiciones y excepciones, ver `NORMATIVA_MAPA_PROCEDIMENTAL.md §2.7`.

#### Plazos de hitos — Grupo A (permiso de acceso obtenido entre 28/12/2013 y 31/12/2017)

Cómputo desde el 25/06/2020.

| Hito | Descripción | Plazo máximo | Cómputo |
|---|---|---|---|
| 1 | Solicitud AAP presentada y admitida | 3 meses | Desde 25/06/2020 |
| 2 | DIA favorable | 27 meses | Desde 25/06/2020 |
| 3 | AAP obtenida | 30 meses | Desde 25/06/2020 |
| 4 | AAC obtenida | 33 meses | Desde 25/06/2020 |
| 5 | Autorización de explotación definitiva | 5 años | Desde 25/06/2020 |

#### Plazos de hitos — Grupo B (permiso de acceso obtenido desde 01/01/2018)

Cómputo desde el 25/06/2020 (permisos anteriores a esa fecha) o desde la fecha de obtención del permiso (permisos desde el 25/06/2020).

| Hito | Descripción | Plazo estándar | Plazo ampliado (RDL 8/2023) |
|---|---|---|---|
| 1 | Solicitud AAP presentada y admitida | 6 meses | — |
| 2 | DIA favorable | 31 meses | — |
| 3 | AAP obtenida | 34 meses | — |
| 4 | AAC obtenida | 37 meses | **49 meses** |
| 5 | Autorización de explotación definitiva | 5 años | **Hasta 8 años** (a solicitud) |

> Plazos son en **meses naturales** — no hay distinción entre hábiles e inhábiles en este contexto.

---

### 2.4 RD-ley 6/2022, de 29 de marzo + RD-ley 20/2022, de 27 de diciembre

> **BOE-A-2022-4972** (RDL 6/2022) · **BOE-A-2022-22685** (RDL 20/2022) — textos consolidados. Sesión 2026-04-04.
> Para el detalle del procedimiento y las condiciones de activación, ver `NORMATIVA_EXCEPCIONES_AT.md §5` y `§6`.

Los plazos de estas normas corresponden al **procedimiento de determinación de afección ambiental** (alternativo a la EIA ordinaria) y a la **tramitación conjunta AAP+AAC** para renovables. Afectan tanto al órgano tramitador como al órgano ambiental.

#### Procedimiento de determinación de afección ambiental (art. 6 RDL 6/2022 · art. 22 RDL 20/2022)

Ambos artículos establecen plazos idénticos. La diferencia entre ellos es el ámbito de aplicación (condiciones de activación), no los plazos. Ver `NORMATIVA_EXCEPCIONES_AT.md §5.1` y `§6.1`.

| Trámite | Plazo | Tipo | Cómputo | Silencio |
|---|---|---|---|---|
| Remisión al órgano ambiental por el órgano sustantivo | **10 días hábiles** | Obligación del órgano sustantivo | Desde recepción de la solicitud completa | — |
| Emisión del informe de determinación de afección ambiental | **2 meses** | Plazo del órgano ambiental | Desde recepción de documentación completa | **Desestimatorio** — si no se emite en plazo, el proyecto debe someterse al procedimiento EIA de la Ley 21/2013 |
| Validez del informe favorable | **2 años** | Plazo de vigencia | Desde la notificación del informe al promotor | — |

> **Ventana temporal de aplicación:**
> - Art. 6 RDL 6/2022: solicitudes presentadas ante el órgano sustantivo **antes del 31/12/2024**.
> - Art. 22 RDL 20/2022: solicitudes presentadas **desde el 28/12/2022 hasta el 31/12/2024**.
> En 2026, ambos artículos solo afectan a expedientes con solicitud previa al 31/12/2024 aún en tramitación.

#### Tramitación conjunta AAP+AAC — plazos reducidos (art. 7 RDL 6/2022 · art. 23 RDL 20/2022)

> ⚠️ **Solo aplica a proyectos competencia AGE** (producción > 50 MW peninsular, LSE art. 3.13.a). Los expedientes de BDDAT (Andalucía, ≤ 50 MW) **no siguen este régimen** directamente. Se documenta como referencia para el caso en que Andalucía adopte un procedimiento análogo.

| Trámite | Plazo estándar (RD 1955/2000) | Plazo reducido (arts. 7/23) | Tipo |
|---|---|---|---|
| Consultas a AAPP (arts. 127+131 RD 1955/2000) | 30 días hábiles | **15 días hábiles** (mitad) | Plazo del órgano tramitador |
| Información pública AAP (art. 125 RD 1955/2000) | 30 días hábiles | **15 días hábiles** (mitad) | Plazo del administrado/publicación |
| Información pública AAC (art. 126 RD 1955/2000) | 20 días hábiles | **10 días hábiles** (mitad) | Plazo del administrado/publicación |

#### Suspensión en nudos con concurso de acceso (art. 13 RDL 20/2022)

| Evento | Fecha |
|---|---|
| Inicio de la suspensión | 28/12/2022 (entrada en vigor RDL 20/2022) |
| Fin de la suspensión | ≈ junio 2024 (18 meses naturales desde el 28/12/2022) |

> Este artículo ya ha **agotado su período de vigencia**. Solo es relevante para expedientes con trámites que quedaron suspendidos entre diciembre 2022 y junio 2024 y aún están activos.

---

### 2.5 Ley 21/2013, de 9 de diciembre — EIA: plazos del procedimiento ambiental

> **BOE-A-2013-12913** — texto consolidado (last_updated 2025-11-06). Sesión 2026-04-05.
> Para los umbrales que determinan cuándo se requiere EIA ordinaria o simplificada, ver `NORMATIVA_EXCEPCIONES_AT.md §8`.
> Para la suspensión de facto de la AAP mientras se tramita la DIA, ver `NORMATIVA_EXCEPCIONES_AT.md §2.2`.

Los plazos de la Ley 21/2013 son **plazos del órgano ambiental** y del órgano sustantivo dentro del procedimiento de EIA. Son independientes —y se superponen— con los plazos del procedimiento de autorización sectorial (RD 1955/2000).

**Regla de oro (art. 10):** la falta de emisión de la DIA o del informe de impacto ambiental **en ningún caso equivale a evaluación favorable**. No existe silencio positivo ambiental.

#### EIA ordinaria — plazos (arts. 33-43)

| Trámite | Plazo | Quién | Artículo |
|---|---|---|---|
| Documento de alcance del EsIA (potestativo) | **2 meses** | Órgano ambiental | Art. 33.2 / Art. 34 |
| Remisión del doc. inicial al órgano ambiental | **10 días hábiles** | Órgano sustantivo | Art. 34.2 |
| Consultas previas al doc. de alcance | **20 días hábiles** | AAPP y personas interesadas | Art. 34.4 |
| Validez del doc. de alcance | **2 años** desde notificación al promotor | — | Art. 34.5 |
| Validez del EsIA | **1 año** desde conclusión para presentarlo | — | Art. 35.4 |
| Información pública (proyecto + EsIA) | **≥ 30 días hábiles** | Órgano sustantivo | Art. 36.1 |
| Consultas a AAPP y personas interesadas | **30 días hábiles** | AAPP y personas interesadas | Art. 37.4 |
| Vigencia de los trámites de IP y consultas | **1 año** desde finalización | — | Art. 33.3 |
| Traslado de alegaciones al promotor | **30 días hábiles** desde fin IP+consultas | Órgano sustantivo | Art. 38.1 |
| Inadmisión de la solicitud de EIA ordinaria | **20 días hábiles** | Órgano ambiental | Art. 39.4 |
| Subsanación del expediente (si incompleto) | **3 meses** | Órgano sustantivo | Art. 40.1 |
| Análisis técnico + formulación de la DIA | **4 meses** desde recepción del expediente completo | Órgano ambiental | Art. 33.4 |
| Publicación de la DIA en diario oficial | **10 días hábiles** desde formulación | Órgano ambiental | (implícito) |
| Extracto de la resolución de autorización | **15 días hábiles** desde autorización o denegación | Órgano sustantivo | Art. 42.4 |

**Vigencia de la DIA (art. 43):**
- **4 años** desde publicación para inicio de ejecución.
- Prórroga: **2 años** adicionales si no hay cambios sustanciales en los elementos esenciales.
- Plazo para resolver la prórroga: **3 meses** desde solicitud (silencio: desestimatorio).

#### EIA simplificada — plazos (arts. 45-47)

| Trámite | Plazo | Quién | Artículo |
|---|---|---|---|
| Inadmisión solicitud EIA simplificada | **20 días hábiles** | Órgano ambiental | Art. 45.4 |
| Consultas a AAPP y personas interesadas | **20 días** | AAPP y personas interesadas | Art. 46.2 |
| Formulación del informe de impacto ambiental (IIA) | **3 meses** desde recepción solicitud | Órgano ambiental | Art. 47.1 |
| Publicación del IIA | **10 días hábiles** desde formulación | — | Art. 47.3 |

**Vigencia del IIA (art. 47.4):**
- **4 años** desde publicación para autorizar el proyecto.
- Prórroga: **2 años** adicionales si no hay cambios sustanciales.
- Plazo para resolver la prórroga: **3 meses** desde solicitud (silencio: desestimatorio).

#### Resumen de plazos — tabla consolidada Ley 21/2013

| Procedimiento | Trámite | Plazo | Tipo | Silencio |
|---|---|---|---|---|
| **EIA ordinaria** | Doc. alcance EsIA (potestativo) | 2 meses | Órgano ambiental | — |
| **EIA ordinaria** | Información pública | ≥ 30 días hábiles | Trámite | — |
| **EIA ordinaria** | Consultas a AAPP | 30 días hábiles | AAPP | Continúa sin respuesta |
| **EIA ordinaria** | Análisis técnico + formulación DIA | **4 meses** | Órgano ambiental | No hay silencio favorable |
| **EIA ordinaria** | Vigencia DIA | **4 años** | Vigencia | — |
| **EIA ordinaria** | Prórroga DIA | + 2 años | Órgano ambiental | **Desestimatorio** |
| **EIA simplificada** | Consultas a AAPP | 20 días | AAPP | Continúa sin respuesta |
| **EIA simplificada** | Formulación IIA | **3 meses** | Órgano ambiental | No hay silencio favorable |
| **EIA simplificada** | Vigencia IIA | **4 años** | Vigencia | — |
| **EIA simplificada** | Prórroga IIA | + 2 años | Órgano ambiental | **Desestimatorio** |

> **Implicación en BDDAT:** los expedientes con EIA pueden tener la AAP bloqueada entre 4 y 8+ meses por el solo trámite de la DIA. Los hitos del RD-ley 23/2020 (Grupo B, hito 2: DIA favorable en 31 meses) presuponen este orden temporal. El motor debe gestionar la DIA como evento desbloqueante de la AAP, no como trámite interno del expediente sectorial.

---

### 2.6 Ley 2/2026, de 12 de marzo — AAU y AAUS: plazos del procedimiento de prevención ambiental

> **BOJA núm. 54 de 20/03/2026** — sedeboja id_tecnico 40751. Entrada en vigor **20/06/2026**. Sesión 2026-04-05.
> Para los instrumentos y umbrales que determinan cuál aplica: ver `NORMATIVA_EXCEPCIONES_AT.md §9`.
> Los plazos del procedimiento de EIA que se integra en AAU (DIA) y AAUS (IIA) están en `§2.5`.
> **Régimen transitorio:** procedimientos iniciados antes del 20/06/2026 siguen por GICA (Ley 7/2007) y Decreto 356/2010 (DT 1ª).

Los plazos de esta sección son **plazos del órgano ambiental autonómico** (Consejería de Medio Ambiente) dentro del procedimiento de AAU o AAUS. Se superponen con los plazos del RD 1955/2000 porque la AAP no puede resolverse hasta que el instrumento ambiental sea favorable.

**Regla de oro:** el silencio en todos los plazos de resolución de la AAU y AAUS es **desestimatorio**. No existe silencio positivo ambiental (coherente con art. 10 Ley 21/2013).

#### AAU — Autorización Ambiental Unificada (arts. 70-78)

| Trámite | Plazo | Quién | Artículo |
|---|---|---|---|
| Consultas previas — doc. de alcance (potestativo) | **2 meses** | Órgano ambiental | Art. 70.1 |
| Validez del doc. de alcance | **2 años** desde notificación | — | Art. 70.4 |
| Informe compatibilidad urbanística (ayuntamiento) | **1 mes** | Ayuntamiento | Art. 71.2.b |
| Inadmisión de solicitud | **20 días hábiles** | Órgano ambiental | Art. 71.3 |
| Información pública | **≥ 30 días hábiles** | Órgano ambiental | Art. 71.4 |
| Consultas simultáneas a AAPP e interesados | **30 días hábiles** (preceptivos vinculantes: máx. 3 meses) | AAPP e interesados | Art. 71.5 |
| Traslado de alegaciones de IP a AAPP | **10 días hábiles** desde fin IP | AAPP | Art. 71.4 |
| Audiencia — dictamen ambiental | **10 días hábiles** | Promotor e interesados | Art. 71.6 |
| **Resolución** | **6 meses** (excepcionalmente hasta 8 meses) | Órgano ambiental | Art. 71.8 |
| Modificación sustancial — resolución | **4 meses** | Órgano ambiental | Art. 75.1.d |
| Vigencia para iniciar actividad | **5 años** desde notificación | — | Art. 76.1 |
| Prórroga de vigencia — resolución | **6 meses** | Órgano ambiental | Art. 76.3 |
| Cese definitivo — resolución del órgano ambiental | **2 meses** | Órgano ambiental | Art. 78 |

**Silencio en resolución AAU (art. 71.8):** desestimatorio al cumplirse 6 meses (o 8 en ampliación). La ampliación a 8 meses debe notificarse antes de que expire el plazo original.

#### AAUS — Autorización Ambiental Unificada Simplificada (arts. 79-88)

| Trámite | Plazo | Quién | Artículo |
|---|---|---|---|
| Informe compatibilidad urbanística (ayuntamiento) | **1 mes** | Ayuntamiento | Art. 82.2.b |
| Inadmisión de solicitud | **20 días hábiles** | Órgano ambiental | Art. 82.3 |
| Consultas a AAPP e interesados | **20 días hábiles** | AAPP e interesados | Art. 82.4 |
| Audiencia — dictamen ambiental | (sin plazo explícito distinto) | Promotor e interesados | Art. 82.5 |
| **Resolución** | **5 meses** | Órgano ambiental | Art. 82.8 |
| Revisión de oficio / a instancia | **3 meses** | Órgano ambiental | Art. 84.8 |
| Vigencia para iniciar actividad | **5 años** desde notificación | — | Art. 86.1 |
| Prórroga de vigencia — resolución | **6 meses** | Órgano ambiental | Art. 86.3 |
| Cese definitivo — resolución del órgano ambiental | **2 meses** | Órgano ambiental | Art. 88 |

**Silencio en resolución AAUS (art. 82.8):** desestimatorio al cumplirse 5 meses.

**Escalado a AAU (art. 82.7.a):** si el IIA determina que el proyecto necesita EIA ordinaria, la AAUS se convierte en AAU. El promotor elabora EsIA y puede solicitar doc. de alcance conforme al art. 53.2.

#### Cuadro consolidado — plazos de resolución y silencio

| Instrumento | Trámite | Plazo | Silencio |
|---|---|---|---|
| **AAU** | Resolución | **6 meses** (máx. 8) | Desestimatorio |
| **AAU** | Modificación sustancial | **4 meses** | Desestimatorio |
| **AAU** | Prórroga de vigencia | **6 meses** | Desestimatorio |
| **AAUS** | Resolución | **5 meses** | Desestimatorio |
| **AAUS** | Revisión | **3 meses** | — |
| **AAUS** | Prórroga de vigencia | **6 meses** | Desestimatorio |

> **Implicación en BDDAT:** la AAU o AAUS es el instrumento ambiental de competencia autonómica que debe obtenerse antes de la AAP (o de forma coordinada). Sus plazos de resolución (5-6 meses) se superponen con el procedimiento del RD 1955/2000. El motor debe gestionar la AAU/AAUS como evento desbloqueante, en paralelo pero condicionante de la resolución de la AAP. La vigencia de 5 años para iniciar actividad es independiente de la vigencia de la DIA/IIA que integra (que tiene sus propios plazos de 4 años, §2.5).

### 2.7 Decreto 356/2010 — AAU y AAUS: plazos (régimen GICA, expedientes < 20/06/2026)

> **Base:** Decreto 356/2010, de 3 de agosto (sedeboja id 21892), versión consolidada 2024-05-25. Sesión 2026-04-06.
> **Ámbito temporal:** procedimientos de instrumento ambiental iniciados **antes del 20/06/2026** (DT 1ª Ley 2/2026). Para expedientes desde esa fecha: §2.6.
> Para fases y trámites del procedimiento: `NORMATIVA_MAPA_PROCEDIMENTAL.md §3`.

#### AAU — Autorización Ambiental Unificada

| Trámite | Plazo | Tipo de días | Quién | Artículo |
|---|---|---|---|---|
| Consultas previas — plazo a consultados | 30 días | Naturales | AAPP consultadas | Art. 13 |
| Consultas previas — respuesta al promotor | 20 días desde fin consultas | Naturales | Órgano ambiental | Art. 14 |
| Informe compatibilidad urbanística | 1 mes | — | Ayuntamiento | Art. 17.1 |
| Subsanación de solicitud | 10 días | Naturales | Promotor | Art. 16.3 |
| Información pública | Mín. **30 días** | **Naturales** | Órgano ambiental | Art. 19.2 |
| Consultas simultáneas | **30 días** | **Naturales** | AAPP | Art. 20.1 |
| Audiencia | Máx. 10 días | Naturales | Interesados | Art. 22 |
| **Resolución** | **8 meses** (ampliable a 10) | — | Órgano ambiental | Art. 24.1 |
| Modificación sustancial — resolución | **6 meses** | — | Órgano ambiental | Art. 9.1.a |
| Consulta sobre carácter sustancial de modificación | 1 mes | — | Órgano ambiental | Art. 9.5 |
| Modificación de oficio | 3 meses | — | Órgano ambiental | Art. 34.3 |
| Modificación a instancia del titular | 3 meses | — | Órgano ambiental | Art. 36 |
| Vigencia para iniciar ejecución | **4 años** desde notificación | — | — | Art. 37.1 |
| Prórroga de vigencia — resolución | 6 meses; prórroga máx. 2 años | — | Órgano ambiental | Art. 37.5 |
| Cese definitivo — resolución condiciones desmantelamiento | 2 meses | — | Órgano ambiental | Art. 38 |

**Silencios AAU:**
- Resolución: **desestimatorio** (art. 24.1)
- Consulta carácter sustancial modificación: **positivo** = silencio → no sustancial (art. 9.5)
- Modificación a instancia del titular: **positivo** = condiciones propuestas incorporadas (art. 36.3)
- Cese definitivo (2 meses): **positivo** = puede iniciar desmantelamiento (art. 38)

#### AAUS — Autorización Ambiental Unificada Simplificada

| Trámite | Plazo | Tipo de días | Quién | Artículo |
|---|---|---|---|---|
| Informe compatibilidad urbanística | 1 mes | — | Ayuntamiento | Art. 17.1 |
| Consultas | **20 días** | **Naturales** | AAPP e interesados | Art. 27 quáter |
| Audiencia (si no efectos significativos) | 10 días | — | Interesados | Art. 27 quinquies.b |
| **Resolución** | **5 meses** | — | Órgano ambiental | Art. 27 sexies.1 |

**Silencio AAUS resolución:** desestimatorio.

#### Cuadro de contradicciones — D356/2010 vs. Ley 2/2026 (la Ley prevalece)

| Aspecto | D356/2010 (GICA) | Ley 2/2026 | Impacto |
|---|---|---|---|
| Resolución AAU | **8 meses** (máx. 10) | **6 meses** (máx. 8) | Reducción plazo órgano ambiental |
| Modificación sustancial AAU | **6 meses** | **4 meses** | Reducción plazo |
| Vigencia AAU para iniciar | **4 años** + prórroga máx. 2 años | **5 años** + prórroga | Ampliación (favorable al promotor) |
| IP — tipo de días | **Naturales** (30 días) | **Hábiles** (30 días hábiles) | Mayor plazo efectivo |
| Consultas AAU — tipo de días | **Naturales** (30 días; sin distinción vinculantes) | **Hábiles** (30 días hábiles; vinculantes hasta 3 meses) | Mayor plazo efectivo + nueva categoría |
| Consultas AAUS — tipo de días | **Naturales** (20 días) | **Hábiles** (20 días hábiles) | Mayor plazo efectivo |
| Resolución AAUS | 5 meses | 5 meses | **Igual** |
| Cese definitivo — resolución | 2 meses | 2 meses | **Igual** |

**Implicación en BDDAT:** la variable `fecha_inicio_expediente_ambiental` selecciona el régimen de plazos:
- `< 20/06/2026` → D356/2010: AAU en 8 meses, IP en 30 días naturales
- `≥ 20/06/2026` → Ley 2/2026: AAU en 6 meses, IP en 30 días hábiles

---

## 3. API de días inhábiles — Junta de Andalucía

> **Fuente:** API pública consumida por la página oficial de la Junta.
> **URL página:** `https://www.juntadeandalucia.es/servicios/sede/tramites/calendario-dias-inhabiles.html`
> **Aplica a:** Motor de plazos (`app/services/plazos.py`). Implementación pendiente — ver nota al pie.
> **Estado:** API documentada (sesión 2026-04-02). Integración en motor pendiente.

### 3.1 Descripción

La página oficial de la Junta no es una fuente estática — consume en tiempo real una API REST pública sin autenticación. Es la **fuente de verdad programable** para días inhábiles en Andalucía, más fiable que extraer el texto del BOJA, ya que:

- Se actualiza automáticamente cuando la Junta carga los datos de un año nuevo (el endpoint `/years` lo refleja de inmediato).
- Incluye los tres niveles necesarios: autonómico, provincial y municipal.
- La respuesta ya incorpora sábados y domingos, eliminando la necesidad de calcularlos por separado.

### 3.2 Endpoints

**Base:** `https://www.juntadeandalucia.es/ssdigitales/datasets/work-calendar/`

| Endpoint | Método | Descripción |
|---|---|---|
| `/years` | GET | Años con datos disponibles. Ej: `{"result":["2024","2025","2026"]}` |
| `/provinces` | GET | Provincias disponibles (las 8 + vacío para ámbito autonómico) |
| `/municipalities` | GET | Todos los municipios de Andalucía (sin filtro por provincia) |
| `/work-calendar/get/search_calendar_weekends` | GET | Días inhábiles del ámbito y año solicitados |

### 3.3 Parámetros del endpoint principal

```
GET /work-calendar/get/search_calendar_weekends?municipality={m}&province={p}&year={y}
```

| `province` | `municipality` | Resultado |
|---|---|---|
| *(vacío o `-`)* | *(vacío o `-`)* | Festivos autonómicos + sábados/domingos |
| `CÁDIZ` | `-` | Autonómicos + festivos locales de todos los municipios de Cádiz + sáb/dom |
| `CÁDIZ` | `CÁDIZ` | Autonómicos + festivos locales de Cádiz capital + sáb/dom |

> Los valores de `province` y `municipality` son en **mayúsculas exactas** tal como devuelve `/provinces` y `/municipalities`.

### 3.4 Estructura de cada registro en la respuesta

```json
{
  "date": 20260101,
  "dateformat": "2026-01-01T00:00:00Z",
  "description": "AÑO NUEVO",
  "event": "VEVENT",
  "id": "20261",
  "municipality": "",
  "province": "",
  "type": "LABORAL",
  "year": "2026"
}
```

- `date`: entero `YYYYMMDD` — útil para comparación directa.
- `municipality` y `province`: vacíos en festivos autonómicos/nacionales; rellenos en locales.
- La respuesta puede contener duplicados cuando se consulta con `province` + `municipality=-` (se devuelven los autonómicos repetidos junto a los locales). Deduplicar por `date` al procesar.

### 3.5 Festivos locales de Cádiz capital (referencia)

Configuración base del proyecto: **provincia CÁDIZ / municipio CÁDIZ**.

| Año | Fecha | Descripción |
|---|---|---|
| 2025 | Por confirmar — consultar API con `year=2025` | — |
| 2026 | 2026-02-16 | Fiesta local (Carnaval) |
| 2026 | 2026-10-07 | Fiesta local (Virgen del Rosario) |

### 3.6 Nota de implementación

Los JSON estáticos en `app/data/dias_inhabiles/` (2025.json, 2026.json) contienen los festivos autonómicos extraídos del BOJA y son válidos como fallback o para tests offline. En `plazos.py`, la estrategia de integración (consulta en tiempo real vs. caché al arrancar vs. JSON estático) queda pendiente de decisión en el momento de implementar el motor.
