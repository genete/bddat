# NORMATIVA — Excepciones, regímenes especiales y casos límite AT

> **Aplica a:** Motor de reglas — desviaciones respecto al procedimiento estándar AAP/AAC/AE.
> **Fuentes de verdad:** `docs/NORMATIVA_LEGISLACION_AT.md §6` · `docs/NORMATIVA_PLAZOS.md §2`.
> **Estado:** En construcción — sesión 2026-04-05. LSE + RD 1955/2000 + Decreto 9/2011 + DL 26/2021 + RDL 6/2022 + RDL 20/2022 + DL 2/2018 + Ley 21/2013 + Ley 2/2026 extraídos.

Este documento recoge las **Iteraciones 2 y 4** de `NORMATIVA_LEGISLACION_AT.md §5`:
- **Iteración 2:** excepciones al procedimiento estándar y regímenes especiales (renovables, <30 kV, simplificaciones).
- **Iteración 4:** casos límite y casuística especial (caducidades reutilizables, modificaciones, tramitación conjunta).

Para el procedimiento estándar sin excepciones: ver `docs/NORMATIVA_MAPA_PROCEDIMENTAL.md`.
Para los plazos concretos de cada trámite: ver `docs/NORMATIVA_PLAZOS.md §2`.

---

## Índice

| § | Contenido |
|---|---|
| [§1](#1-excepciones-lse-242013) | Excepciones identificadas en la LSE 24/2013 |
| [§2](#2-excepciones-rd-19552000) | Excepciones identificadas en el RD 1955/2000 |
| [§3](#3-decreto-92011-de-18-de-enero-junta-de-andalucía) | Decreto 9/2011 — exención AT 3ª categoría suelo urbano |
| [§4](#4-decreto-ley-262021-de-14-de-diciembre-junta-de-andalucía) | DL 26/2021 — exención general instalaciones sin DUP y sin AAU |
| [§5](#5-rd-ley-62022-de-29-de-marzo) | RD-ley 6/2022 — afección ambiental simplificada + tramitación conjunta (primera ola) |
| [§6](#6-rd-ley-202022-de-27-de-diciembre) | RD-ley 20/2022 — régimen ampliado (segunda ola) + suspensión nudos concurso |
| [§7](#7-decreto-ley-22018-de-26-de-junio-junta-de-andalucía) | DL 2/2018 — umbral 500 kW, anti-fraccionamiento, DR consultas, incidencia territorial |
| [§8](#8-ley-212013-de-9-de-diciembre--umbrales-eia-y-condiciones-de-obligatoriedad) | Ley 21/2013 — umbrales EIA ordinaria/simplificada para instalaciones eléctricas AT |
| [§9](#9-ley-22026-de-12-de-marzo--instrumentos-de-prevención-ambiental-aplicables-a-instalaciones-at) | Ley 2/2026 — instrumentos de prevención ambiental (AAU, AAUS, Licencia Ambiental) y régimen transitorio |

---

## 1. Excepciones identificadas en la LSE 24/2013

> Sesión 2026-04-02.

### 1.1 Tramitación conjunta AAP + AAC (art. 53.1)

**Regla estándar:** AAP → AAC son procedimientos sucesivos.

**Excepción:** el art. 53.1 permite que AAP y AAC se tramiten de forma **coetánea o conjunta**.
La información pública y los informes a AAPP pueden efectuarse de forma simultánea para ambas.

**Implicación en BDDAT:** en un expediente con tramitación conjunta, las fases de AAP y AAC
se solapan en el tiempo. El motor debe permitir que AAC se inicie sin que AAP esté resuelta.
Diseño pendiente de sesión específica.

### 1.2 Cierre unilateral sin resolución — instalaciones AGE (art. 53)

**Regla estándar:** el cierre requiere resolución administrativa.

**Excepción (solo AGE):** si transcurren **6 meses** desde la solicitud de cierre
y el operador del sistema lleva **≥ 3 meses** con informe favorable emitido,
el titular puede cerrar la instalación **sin esperar resolución**.

> **Aplicabilidad a BDDAT:** este régimen está previsto para instalaciones de competencia
> de la AGE. Para instalaciones de competencia autonómica (BDDAT), la norma aplicable
> es la autonómica. Pendiente de verificar si Andalucía tiene régimen equivalente.

### 1.3 Silencio desestimatorio para CCAA (DA 3ª)

**Regla:** el silencio en todos los procedimientos de autorización amparados en la LSE
es **desestimatorio**, también para CCAA. El plazo concreto a partir del cual opera
lo establece la norma autonómica aplicable (o el RD 1955/2000 como referencia).

**Implicación en BDDAT:** no hay posibilidad de silencio positivo en AAP, AAC, AE,
transmisión ni cierre. Ver plazos en `NORMATIVA_PLAZOS.md §2.1` y `§2.2`.

### 1.4 Exención de autorizaciones para infraestructuras de recarga VE de potencia ≤3.000 kW (art. 53.1)

**Regla estándar:** cualquier instalación eléctrica contemplada en la LSE requiere AAP, AAC y AE (art. 53.1).

**Excepción implícita:** el art. 53.1 incluye expresamente en el ámbito de autorización las
«infraestructuras eléctricas, incluidos los accesos y extensiones de red, así como los centros
de transformación y de seccionamiento, de las estaciones de recarga de vehículos eléctricos
de **potencia superior a 3.000 kW**». La delimitación por umbral implica que las infraestructuras
eléctricas de estaciones de recarga de **potencia ≤3.000 kW quedan fuera del ámbito del art. 53**
y no requieren AAP, AAC ni AE.

**Condición de aplicación:**

| Condición | Detalle |
|---|---|
| Tipo de instalación | Infraestructura eléctrica (acceso/extensión de red, CT, seccionamiento) asociada a estación de recarga VE |
| Potencia | ≤ 3.000 kW |

**Implicación en BDDAT:** si `es_infraestructura_recarga_ve = true` y `potencia_recarga_ve_kw ≤ 3.000`,
la instalación queda exenta del procedimiento de autorización — el motor no debe generar fases AAP/AAC/AE.
Solo las infraestructuras de recarga VE con potencia superior a 3.000 kW siguen el procedimiento estándar.

---

## 2. Excepciones identificadas en el RD 1955/2000

> Sesión 2026-04-02.

### 2.1 Reducción del plazo de consultas en AAC sin DUP (art. 131)

**Regla estándar:** consultas a AAPP en AAC → **30 días**.

**Excepción:** si la instalación **ya tiene AAP concedida** y la tramitación es
exclusivamente la AAC (sin DUP y sin modificación de la AAP), el plazo de consultas
se reduce a **15 días**.

**Condición de aplicación:** AAP previa existente + no se solicita DUP + no se modifica la AAP.

**Implicación en BDDAT:** el motor debe detectar si la solicitud de AAC tiene AAP previa
para aplicar el plazo reducido. Requiere cruce con el estado de la solicitud anterior
del mismo expediente.

### 2.2 Suspensión de facto por EIA (arts. 122-128 + Ley 21/2013)

**Regla estándar:** la AAP se resuelve en 3 meses desde la solicitud.

**Excepción:** cuando la instalación requiere **Evaluación de Impacto Ambiental ordinaria**
(Ley 21/2013), la resolución de la AAP no puede dictarse sin la Declaración de Impacto
Ambiental (DIA). La tramitación ambiental y la tramitación administrativa discurren en
paralelo, pero la resolución de la AAP queda bloqueada hasta que la DIA se emite.

**Naturaleza jurídica:** es una suspensión del plazo de resolución al amparo del
art. 22.1.d LPACAP (solicitud de pronunciamiento previo preceptivo de otro órgano).
Ver `NORMATIVA_PLAZOS.md §2.2 — Suspensiones`.

**Implicación en BDDAT:** los expedientes con EIA pueden tener la AAP en estado "en instrucción"
durante meses o años mientras espera la DIA. El motor debe distinguir la suspensión
por EIA de la inactividad. Diseño de suspensiones: ver `DISEÑO_FECHAS_PLAZOS.md §3.3`.

### 2.3 Informe DGPEM en instalaciones de transporte tramitadas por CCAA (art. 114)

**Aplicabilidad:** solo instalaciones de **transporte** (no distribución) cuya competencia
corresponde a la CCAA.

**Excepción procedimental:** la CCAA debe solicitar informe previo a la DGPEM antes de
resolver la AAP. Si el informe no se emite en **2 meses**, la CCAA puede continuar
las actuaciones.

**Carácter vinculante:** si el informe se emite en plazo, su contenido es vinculante
para la resolución de la CCAA. En la práctica, las resoluciones suelen esperar al informe
aunque haya vencido el plazo, dado que un informe desfavorable posterior puede
bloquear la operación de la instalación (REE no la incorpora a la red retribuida).

**Implicación en BDDAT:** expedientes de instalaciones de transporte intra-CCAA deben
registrar si se ha solicitado el informe DGPEM y si está pendiente de recibir.
La suspensión del plazo de resolución puede activarse por este trámite.

### 2.4 Tramitación conjunta de información pública AAP + DUP (art. 125)

**Regla:** la información pública de la AAP y la de la DUP (Declaración de Utilidad Pública)
pueden efectuarse de forma conjunta en un único trámite de 30 días.

**Condición:** el titular debe haberlo solicitado conjuntamente al presentar la solicitud de AAP.

**Implicación en BDDAT:** el motor debe permitir que una solicitud con DUP comparta
el trámite de información pública con la AAP, sin duplicar el período de exposición.

---

## 3. Decreto 9/2011, de 18 de enero (Junta de Andalucía)

> [BOJA 2011/22](https://www.juntadeandalucia.es/boja/2011/22/1) — Sesión 2026-04-03.

### 3.1 Exención de información pública para AT de tercera categoría en suelo urbano (DA 1ª)

**Regla estándar:** la AAP requiere información pública de 30 días (art. 125 RD 1955/2000)
y publicación de la resolución en el BOP (art. 128.3 RD 1955/2000).

**Excepción (DA 1ª, apartados 1-3):** ambos trámites quedan suprimidos cuando se cumplen
**todas** las condiciones siguientes:

| Condición | Detalle |
|---|---|
| Categoría de la instalación | **Tercera categoría AT** — tensión nominal 1 kV < U ≤ 30 kV (media tensión) |
| Tipo de instalación | **Línea subterránea** o **centro de transformación interior** |
| Suelo | **Urbano o urbanizable** |
| DUP | **No requerida** (la instalación no necesita declaración de utilidad pública en concreto) |
| Titularidad / destino | Indistinto: instalaciones del distribuidor o instalaciones a ceder al distribuidor para integrarse en su red |

**Alcance:** instalaciones **nuevas**, **ampliaciones** y **modificaciones** de instalaciones existentes.

**Trámites suprimidos:**
- Información pública (art. 125 RD 1955/2000) — **30 días eliminados**
- Publicación de la resolución de AAP/AAC/AE en el Boletín Oficial de la Provincia (art. 128.3)

**Trámites que se mantienen:** el resto del procedimiento AAP sigue igual — consultas a AAPP,
traslado de alegaciones (si las hubiera pese a no haber información pública) y resolución en 3 meses.

**Implicación en BDDAT:** la fase INFORMACION_PUBLICA en el motor debe ser **condicional**,
no obligatoria, para solicitudes que cumplan los cuatro criterios. El motor necesita evaluar:
- ¿Tensión ≤ 30 kV? (tercera categoría)
- ¿Instalación subterránea o CT interior?
- ¿Suelo urbano/urbanizable?
- ¿Sin DUP?

Si los cuatro son verdaderos → INFORMACION_PUBLICA y publicación en BOP se omiten.
Ver `NORMATIVA_MAPA_PROCEDIMENTAL.md §2.1` (fase 3 de AAP marcada como condicional).

**Relación con DL 26/2021 DF 4ª:** el DL 26/2021 contiene una exención más amplia
(instalaciones sin DUP y sin AAU — independiente de la tensión y el tipo de suelo).
En la práctica, la exención del DL 26/2021 **absorbe** la del Decreto 9/2011 para el trámite de
información pública. El Decreto 9/2011 sigue siendo relevante en lo no cubierto por el DL 26/2021:
la supresión de la **publicación en BOP** (art. 128.3 RD 1955/2000), que el DL 26/2021 no contempla.
Ver análisis completo en §4.

---

## 4. Decreto-ley 26/2021, de 14 de diciembre (Junta de Andalucía)

> [BOJA 2021/241](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=33520) — Sesión 2026-04-03.

### 4.1 Exención de información pública para instalaciones sin DUP y sin AAU (DF 4ª)

**Regla estándar:** la AAP requiere información pública de 30 días (art. 125 RD 1955/2000).

**Excepción (DF 4ª, ap. 1):** quedan exentas del trámite de información pública las solicitudes
de autorización administrativa del **Título VII del RD 1955/2000** que cumplan **simultáneamente**:

| Condición | Detalle |
|---|---|
| Sin DUP | La instalación no requiere declaración de utilidad pública para su implantación |
| Sin AAU | La instalación no está sometida a autorización ambiental unificada (Ley 7/2007, de 9 de julio, GICA) |

**Alcance:** cualquier autorización del Título VII RD 1955/2000 — AAP, AAC, AE, transmisión, cierre —
sin restricción de tensión, tipo de instalación (aérea/subterránea) ni clasificación de suelo.

**Modificabilidad (ap. 2):** las excepciones de esta disposición pueden modificarse por norma reglamentaria.

**Relación con el Decreto 9/2011 DA 1ª:**

| Aspecto | Decreto 9/2011 DA 1ª | DL 26/2021 DF 4ª |
|---|---|---|
| Tensión | Solo AT 3ª categoría (1 kV < U ≤ 30 kV) | Sin restricción |
| Tipo de instalación | Solo línea subterránea o CT interior | Cualquier instalación del Título VII |
| Clasificación de suelo | Solo urbano o urbanizable | Sin restricción |
| Condición sin DUP | Sí | Sí |
| Condición sin AAU | No mencionado | Sí (condición expresa) |
| Suprime publicación en BOP (art. 128.3) | Sí | No |

**Conclusión:** el DL 26/2021 **subsume y amplía** la exención del Decreto 9/2011 en cuanto al
trámite de información pública — al no estar limitado por tensión, tipo de instalación ni suelo.
Sin embargo, **no lo sustituye** en lo relativo a la supresión de la publicación en BOP (art. 128.3),
que el Decreto 9/2011 suprime expresamente para AT 3ª categoría y el DL 26/2021 no menciona.

**Implicación en BDDAT:** las condiciones de evaluación para omitir INFORMACION_PUBLICA son:

```
¿Requiere DUP? = false
¿Sometida a AAU? = false
→ INFORMACION_PUBLICA se omite (DL 26/2021 DF 4ª)
```

La exención del Decreto 9/2011 queda absorbida en la práctica. La supresión de publicación en BOP
(Decreto 9/2011 DA 1ª) se evalúa de forma independiente con sus propias condiciones (AT 3ª categoría
+ subterránea/CT + suelo urbano/urbanizable + sin DUP).

> **Cola de trabajo:** las normas pendientes de extracción se gestionan en `docs/GUIA_NORMAS.md §4`.

---

## 5. RD-ley 6/2022, de 29 de marzo

> [BOE-A-2022-4972](https://www.boe.es/eli/es/rdl/2022/03/29/6/con) — Sesión 2026-04-04.

### 5.1 Procedimiento de determinación de afección ambiental para renovables (art. 6)

**Regla estándar:** un proyecto de generación renovable que figure en los Anexos I o II de la Ley 21/2013 debe someterse al procedimiento de evaluación ambiental ordinaria o simplificada antes de obtener la AAP.

**Excepción (art. 6):** los proyectos que cumplan **todas** las condiciones siguientes pueden seguir un procedimiento de **determinación de afección ambiental** más ágil (no es una EIA): el informe resultante determina si hace falta EIA o no.

**Condiciones de aplicación:**

| Condición | Detalle |
|---|---|
| Tipo de proyecto | Generación renovable incluida en Anexo I Grupo 3 (i,j) o Anexo II Grupo 4 (g,i) de la Ley 21/2013 |
| Potencia | Eólica ≤ **75 MW** · Fotovoltaica ≤ **150 MW** |
| Evacuación | Líneas aéreas de evacuación **no** incluidas en Anexo I Grupo 3.g) (< 220 kV o cortas) |
| Ubicación | **No** en Red Natura 2000 · **No** en medio marino |
| Zona sensibilidad | Íntegramente en zona de **sensibilidad baja** según la herramienta MITECO "Zonificación ambiental para la implantación de energías renovables" |
| Ventana temporal | Solicitud presentada ante el órgano sustantivo **antes del 31/12/2024** |

**Procedimiento (art. 6.3):**

1. Promotor presenta: solicitud + anteproyecto (art. 53.1.a LSE) + estudio de impacto ambiental + resumen ejecutivo.
2. Órgano sustantivo remite al órgano ambiental en **10 días**.
3. Órgano ambiental emite **informe de determinación de afección ambiental** en **2 meses** (máx.) desde recepción de documentación.
4. El informe determina:
   - Resultado **favorable**: el proyecto puede continuar la tramitación de autorización **sin EIA** (puede imponer condiciones medioambientales).
   - Resultado **desfavorable**: el proyecto debe someterse al procedimiento de EIA de la Ley 21/2013.
5. El informe **no es recurrible** de forma autónoma (solo junto a la resolución de autorización).

**Validez del informe favorable:** 2 años desde su notificación. Para proyectos del ámbito del RD-ley 23/2020, el informe favorable equivale al cumplimiento de los Hitos 2 (DIA) de los permisos de acceso.

**Aplicabilidad a la CCAA (art. 6.6):** El procedimiento **no tiene carácter básico** → aplica a la AGE. Las CCAA **pueden** aplicarlo a los proyectos de su competencia. La Junta de Andalucía puede adoptar este procedimiento para expedientes en BDDAT, pero su aplicación depende de que la CCAA lo haya asumido formalmente (pendiente de verificar: Instrucción Conjunta 1/2022).

**DT 3ª — Aplicación a expedientes en tramitación:** A la entrada en vigor del RDL 6/2022, los proyectos ya en tramitación que cumplan los requisitos del art. 6 pueden acogerse a este procedimiento o continuar por el anterior.

**Implicación en BDDAT:**
- Si la CCAA aplica el art. 6, la fase ambiental de la AAP puede resolverse mediante el informe de afección (2 meses) en lugar del procedimiento EIA estándar.
- El motor debe distinguir si un expediente tiene un informe de afección ambiental favorable (variable `tiene_informe_afeccion_ambiental_favorable`) o si sigue el camino EIA ordinario/simplificado.
- La condición de "zona sensibilidad baja" requiere una variable de dato nueva (`zona_sensibilidad_ambiental_miteco`).

---

### 5.2 Tramitación conjunta AAP+AAC para renovables — Procedimiento simplificado (art. 7)

**Regla estándar:** AAP y AAC son procedimientos sucesivos (AAP debe resolverse antes de iniciar AAC).

**Excepción (art. 7):** para proyectos renovables que hayan obtenido informe de afección ambiental favorable (art. 6), se declaran de urgencia y se tramitan conjuntamente. **Solo aplica a proyectos competencia de la AGE.**

> **Base legal de la competencia AGE:** LSE art. 3.13.a — corresponde a la AGE autorizar instalaciones peninsulares de producción con **potencia eléctrica instalada superior a 50 MW eléctricos** (incluyendo sus infraestructuras de evacuación), así como instalaciones de transporte primario y acometidas ≥ 380 kV. Las instalaciones ≤ 50 MW son competencia de la CCAA (Andalucía → BDDAT).
>
> **Definición de «potencia instalada» en instalaciones fotovoltaicas:** el **RD 1183/2020 DF 3ª** (modifica art. 3 RD 413/2014) introduce una nueva definición que sustituyó a la anterior «potencia pico» (solo DC):
> `potencia instalada FV = min(Σ potencia máxima módulos en STC [DC], Σ potencia máxima inversores [AC])`
> Esto resolvió el problema que existía con plantas FV con alta relación DC/AC («overplanting»), que antes se clasificaban con su potencia pico DC — más alta que la capacidad real de inyección AC. La transición al registro tardó hasta 12 meses (DT 7ª RD 1183/2020).

**Condiciones de aplicación:**

| Condición | Detalle |
|---|---|
| Competencia | **Administración General del Estado** (producción > 50 MW peninsular, LSE art. 3.13.a) — NO aplica a CCAA (Andalucía/BDDAT ≤ 50 MW) |
| Requisito previo | Informe de determinación de afección ambiental **favorable** (art. 6) |
| Solicitud | El promotor opta por el procedimiento simplificado **antes del 31/12/2024** |

**Especialidades del procedimiento conjunto:**

| Aspecto | Tramitación estándar | Procedimiento simplificado (art. 7) |
|---|---|---|
| AAP y AAC | Sucesivas (AAP → AAC) | Tramitación y resolución **conjunta** |
| Documentación inicial | Anteproyecto (AAP) + proyecto de ejecución (AAC) por separado | **Proyecto de ejecución** + informe art. 6 en una sola solicitud |
| Consultas (arts. 127+131 RD 1955/2000) | Trámites independientes por cada autorización | **Unificados**, plazos reducidos a la **mitad** |
| Información pública (arts. 125+126 RD 1955/2000) | 30 días (AAP) + 20 días (AAC) | **Simultánea** para ambas, plazos reducidos a la **mitad** (→ 15 días) |
| DUP | Tramitación separada o conjunta con AAP | Simultánea con AAP+AAC en el mismo expediente |

**Implicación en BDDAT:**
- Este procedimiento aplica solo a proyectos AGE; en principio, los expedientes de BDDAT (Andalucía) **no siguen este régimen** directamente.
- Sin embargo, BDDAT puede recibir expedientes que lleguen con un informe de afección ambiental ya obtenido (si la CCAA adoptó el art. 6), lo que altera el flujo ambiental de la AAP.
- En el futuro, si Andalucía adopta un procedimiento análogo (p. ej., vía Ley 4/2025 o DL propio), el motor necesitará las mismas variables.

---

## 6. RD-ley 20/2022, de 27 de diciembre

> [BOE-A-2022-22685](https://www.boe.es/eli/es/rdl/2022/12/27/20/con) — Sesión 2026-04-04.

El RD-ley 20/2022 introduce dos mecanismos paralelos a los del RDL 6/2022 y los amplía. **No deroga ni sustituye** al RDL 6/2022: se aplica a solicitudes presentadas desde el 28/12/2022 y hasta el 31/12/2024. Los expedientes ya en tramitación al entrar en vigor el RDL 20/2022 continúan rigiéndose por la normativa anterior.

### 6.1 Procedimiento de determinación de afección ambiental — Régimen ampliado (art. 22)

**Diferencias respecto al art. 6 del RDL 6/2022:**

| Aspecto | RDL 6/2022 art. 6 | RDL 20/2022 art. 22 |
|---|---|---|
| Ventana temporal | Solicitudes hasta 31/12/2024 | Solicitudes desde 28/12/2022 hasta 31/12/2024 |
| Umbrales de potencia | Eólica ≤ 75 MW · Fotovoltaica ≤ 150 MW | **Sin umbrales de potencia** |
| Zona de sensibilidad | Solo zonas de sensibilidad **baja** MITECO | **Sin restricción de zona** (salvo exclusiones) |
| Exclusiones | Red Natura 2000 · Medio marino | Red Natura 2000 · Espacios naturales protegidos (art. 28 Ley 42/2007) · Medio marino · Líneas aéreas ≥ 220 kV y > 15 km |
| Tipos de renovable | Solo proyectos del Anexo I Gr.3 y Anexo II Gr.4 de Ley 21/2013 | Cualquier proyecto de generación renovable (excepto exclusiones) |
| Aplicabilidad a CCAA | CCAAs **pueden** aplicar (art. 6.6) | CCAAs **pueden** aplicar (art. 22.6) — sin restricción de tipo |

**El procedimiento interno es idéntico al art. 6** (documentación, 10 días remisión, 2 meses para informe, validez 2 años, no recurrible). Ver §5.1 para el detalle.

**Relación entre RDL 6/2022 art. 6 y RDL 20/2022 art. 22:**
- **Paralelos, no sustitutivos:** el art. 22 aplica a nuevas solicitudes desde el 28/12/2022; el art. 6 rige los expedientes iniciados antes.
- El art. 22 es más amplio en cobertura (sin umbrales de potencia, sin restricción de zona) pero más exigente en exclusiones (suma espacios protegidos al listado).
- En la práctica, en 2026 ambos ya solo afectan a proyectos con solicitudes previas al 31/12/2024.

**Implicación en BDDAT:** igual que §5.1, con la diferencia de que no se necesita verificar zona de sensibilidad MITECO ni umbral de potencia. La variable `zona_sensibilidad_ambiental_miteco` **no es condición** bajo este artículo.

---

### 6.2 Tramitación conjunta AAP+AAC — Régimen obligatorio (art. 23)

Idéntico en estructura al art. 7 del RDL 6/2022 (§5.2), con dos diferencias clave:

| Aspecto | RDL 6/2022 art. 7 | RDL 20/2022 art. 23 |
|---|---|---|
| Carácter | Optativo — el promotor solicita acogerse | **Obligatorio** — "se tramitarán en todo caso" si cumplen condiciones |
| Ventana temporal | Solicitudes hasta 31/12/2024 | Solicitudes desde 28/12/2022 hasta 31/12/2024 |

**Aplica exclusivamente a proyectos competencia AGE** (producción > 50 MW peninsular, LSE art. 3.13.a) — igual que el art. 7. Ver nota sobre competencia y definición de potencia instalada FV en §5.2.

---

### 6.3 Suspensión de tramitaciones en nudos sujetos a concurso de acceso (art. 13)

**Regla general:** los proyectos solicitan acceso y conexión y, si disponen de permiso, pueden tramitar la autorización administrativa.

**Excepción excepcional y temporal (art. 13.1):** durante **18 meses** desde el 28/12/2022 (≈ hasta junio 2024), en los nudos donde la Secretaría de Estado de Energía hubiera acordado la celebración de un **concurso de capacidad de acceso** (art. 20.5 RD 1183/2020), quedan **suspendidos** los procedimientos instados por promotores sin permiso de acceso/conexión, incluyendo:
- Presentación de garantías para tramitar permisos de acceso.
- Solicitudes de AAP y AAC (art. 53 LSE).
- Solicitudes de determinación ambiental (EIA o afección ambiental).

**Excepciones a la suspensión (art. 13.2):** no se suspenden los proyectos que:
- Ya tienen permisos de acceso y conexión.
- Son hibridaciones (art. 27 RD 1183/2020).
- Presentaron solicitud de permiso de acceso antes de la resolución de concurso en ese nudo.
- Obtuvieron acceso al amparo del art. 8 del RDL 6/2022.

**Vigencia:** Este artículo ya ha agotado su período de 18 meses (venció ≈ junio 2024). Solo es relevante para expedientes con trámites suspendidos entre diciembre 2022 y junio 2024 que aún estén activos.

**Implicación en BDDAT:** la suspensión del art. 13 opera sobre proyectos sin permiso de acceso/conexión — complementa la variable `tiene_punto_acceso_conexion` (definida en `DISEÑO_CONTEXT_ASSEMBLER.md`).

---

## 7. Decreto-ley 2/2018, de 26 de junio (Junta de Andalucía)

> [BOJA 2018/125 — ID sedeboja 26974](https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId=26974) — Sesión 2026-04-04.
> Versión consolidada: BOJA 34/2024 (vigencia 17/02/2024). Modificado por DL 26/2021 (art. 3.2) y DL 3/2024 (DA única apdo. 4).

La **Disposición Adicional única** de este DL es el instrumento normativo principal que regula el procedimiento de tramitación en Andalucía para las autorizaciones eléctricas de instalaciones de producción. Sus cuatro apartados contienen reglas directamente aplicables al motor:

### 7.1 Cauce procedimental único para instalaciones de producción en Andalucía (DA única, apdo. 1)

**Regla:** los procedimientos de autorizaciones del **art. 53 LSE** (AAP, AAC, AE), incluidos los asociados a instalaciones fotovoltaicas, se tramitan en Andalucía conforme al **Título VII del RD 1955/2000**, con las excepciones de los siguientes apartados.

**Relevancia histórica:** antes de este DL existía un cauce paralelo para FV (Decreto 50/2008), que generaba duplicidad. La DA única apdo. 1 unifica el cauce y deroga el Decreto 50/2008 (salvo art. 5 y DA 2ª). Los expedientes FV pendientes bajo el Decreto 50/2008 a la entrada en vigor del DL se tramitan igualmente conforme a la DA única (DT única).

**Implicación en BDDAT:** no cambia la lógica del motor (el mapa procedimental ya usa RD 1955/2000 Título VII como referencia), pero confirma que este cauce es también el aplicable a instalaciones FV competencia autonómica. No hay bifurcación de cauce por tipo de renovable.

---

### 7.2 Umbral 500 kW — puesta en servicio en lugar de autorización de explotación (DA única, apdo. 2)

**Regla estándar:** la AE (autorización de explotación, art. 53.1.c LSE) es un trámite obligatorio antes de poner en tensión la instalación.

**Excepción:** para instalaciones de **producción de energía eléctrica con potencia instalada ≤ 500 kW**, la AE se tramita en Andalucía mediante la **puesta en servicio** regulada por la Orden de 5 de marzo de 2013 (desarrollo del Decreto 59/2005) — es decir, el trámite de legalización industrial de baja tensión, no una autorización administrativa separada.

**Condición de aplicación:**

| Condición | Detalle |
|---|---|
| Tipo de instalación | Instalación de **producción** de energía eléctrica (no aplica a distribución, transporte ni autoconsumo puro) |
| Potencia instalada | **≤ 500 kW** |
| Sin anti-fraccionamiento | No concurre ninguna de las condiciones del apdo. 2 párr. 2 (ver §7.3) |

**Trámite resultante:** en lugar de AE → puesta en servicio (Decreto 59/2005 / Orden 5/3/2013 / Ficha técnica AT Resolución 23/03/2026 si es AT).

**Implicación en BDDAT:** el motor debe evaluar si la fase AE requiere autorización administrativa o basta puesta en servicio:

```
es_instalacion_produccion_electrica = true
AND potencia_instalada_mw ≤ 0.5 (500 kW)
AND NO aplica_regla_anti_fraccionamiento
→ AE = PUESTA_EN_SERVICIO (Decreto 59/2005), no autorización administrativa
```

Variable reutilizada: `potencia_instalada_mw` (ya definida — añadir DL 2/2018 como norma de origen adicional con umbral 0.5 MW).

---

### 7.3 Anti-fraccionamiento — agrupación de instalaciones con evacuación común (DA única, apdo. 2 párr. 2)

**Regla:** la excepción del §7.2 **no aplica** cuando concurren simultáneamente las siguientes condiciones, y las instalaciones agrupadas pasan al régimen completo de AAP+AAC:

| Condición | Detalle |
|---|---|
| Línea de evacuación | Las instalaciones **comparten línea de evacuación común** |
| Suma de potencia | La **suma total** de potencia instalada del grupo **supera 500 kW** |
| Criterio de proximidad | **Al menos una** de estas dos sub-condiciones se cumple: (a) están en la **misma referencia catastral**, o (b) están ubicadas a **menos de 3.000 metros** entre sí |

Cuando se activa la regla, se comunica la circunstancia al **órgano ambiental competente** (calificación ambiental, AAU o AAU simplificada) a efectos de su consideración en la evaluación ambiental.

**Implicación en BDDAT:** el motor necesita detectar si una instalación de producción forma parte de un grupo anti-fraccionamiento. Esto requiere variables nuevas:

- `tiene_linea_evacuacion_comun` — boolean, `dato` · Proyecto: la instalación comparte línea de evacuación con otras instalaciones del mismo promotor o con punto de interconexión compartido.
- `suma_potencia_grupo_evacuacion_kw` — numérico (kW), `calculado`: suma de potencias instaladas de todas las instalaciones que comparten la línea de evacuación. Se calcula si `tiene_linea_evacuacion_comun = true`.
- `misma_referencia_catastral_grupo` — boolean, `dato` · Proyecto: alguna instalación del grupo comparte referencia catastral con otra del mismo grupo.
- `distancia_minima_instalaciones_grupo_m` — numérico (m), `dato` · Proyecto: distancia mínima entre cualquier par de instalaciones del grupo (en metros). Solo relevante si `misma_referencia_catastral_grupo = false`.

Condición de activación del anti-fraccionamiento:

```
tiene_linea_evacuacion_comun = true
AND suma_potencia_grupo_evacuacion_kw > 500
AND (misma_referencia_catastral_grupo = true
     OR distancia_minima_instalaciones_grupo_m < 3000)
→ aplica_regla_anti_fraccionamiento = true
→ régimen completo: AAP + AAC + AE (no puesta en servicio)
→ comunicar al órgano ambiental (calificación / AAU / AAU simplificada)
```

---

### 7.4 Declaración responsable de consultas previas (DA única, apdo. 3)

**Regla estándar:** el órgano competente envía separatas a todos los organismos con bienes o intereses afectados (art. 123.d y art. 130.3 RD 1955/2000) en la fase de consultas de la AAP y AAC.

**Simplificación:** el promotor puede **potestativamente** presentar una **declaración responsable** de haber realizado por su cuenta las consultas previas e identificar qué órganos han emitido pronunciamiento favorable o condicionado.

**Efecto:** si se presenta la DR, el órgano competente solo envía separatas a los organismos **no cubiertos** por la DR (o a los que considere oportuno revisar). Reduce la carga del trámite de consultas previas cuando el promotor ha gestionado proactivamente los informes.

**Implicación en BDDAT:** no altera las fases obligatorias, pero sí el alcance de las separatas en la fase de consultas. El motor puede registrar si el promotor presentó esta DR para ajustar el número de organismos a los que se envían separatas.

- `promotor_presento_dr_consultas` — boolean, `derivado_documento` · Expediente: existe documento de tipo DR_CONSULTAS_PREVIAS presentado por el promotor junto a la solicitud de AAP o AAC.

---

### 7.5 Verificación de incidencia territorial (DA única, apdo. 4) — Vigente desde DL 3/2024 art. 260

> Añadido a la DA única por el **art. 260 del DL 3/2024** (vigencia: 17/02/2024).

**Regla:** antes de presentar la solicitud de autorización de instalaciones de energía eléctrica sometidas a autorización, el promotor debe **comprobar** si el proyecto está en alguno de los supuestos del **art. 71 del Reglamento General de la LISTA** (Decreto 550/2022, de 29 de noviembre).

**Opciones resultantes:**

| Resultado del análisis | Documentación a aportar con la solicitud |
|---|---|
| El proyecto **sí cae** en art. 71 Reglamento LISTA | Documentación para valorar la incidencia en ordenación del territorio y paisaje → informe de incidencia territorial (art. 72 Reglamento LISTA), emitido por la Consejería competente en ordenación del territorio y urbanismo |
| El proyecto **no cae** en art. 71 | **Declaración responsable** de que el proyecto no requiere el informe de incidencia territorial |

El órgano competente puede requerir el análisis realizado por el promotor en cualquier momento.

**Condición de aplicación:** instalaciones de energía eléctrica sometidas a autorización (art. 53 LSE) — todas las instalaciones del ámbito de BDDAT.

**Implicación en BDDAT:** es un requisito previo a la solicitud formal, análogo al punto de acceso/conexión. El motor debe verificar que se ha aportado documentación de incidencia territorial (o DR de no-incidencia) antes de dar por completa la solicitud.

- `requiere_informe_incidencia_territorial` — boolean, `calculado`: el promotor ha concluido que el proyecto cae en algún supuesto del art. 71 Reglamento LISTA; deriva del análisis del promotor y debe constar en la solicitud.
- `promotor_aporto_doc_incidencia_territorial` — boolean, `derivado_documento` · Expediente: existe documento de tipo DR_NO_INCIDENCIA_TERRITORIAL o INFORME_INCIDENCIA_TERRITORIAL asociado a la solicitud.

> **Nota:** el art. 71 del Reglamento LISTA (Decreto 550/2022) define los supuestos de actuaciones sometidas a informe de incidencia territorial. Pendiente de revisar su contenido para completar la lógica de `requiere_informe_incidencia_territorial`.

---

## 8. Ley 21/2013, de 9 de diciembre — Umbrales EIA y condiciones de obligatoriedad

> **BOE-A-2013-12913** — texto consolidado (last_updated 2025-11-06). Sesión 2026-04-05.
> Para los plazos del procedimiento ambiental (DIA, IIA, vigencias): ver `NORMATIVA_PLAZOS.md §2.5`.
> La norma autonómica andaluza que regula los procedimientos ambientales aplicables en Andalucía (AAU, Calificación Ambiental) es la **Ley 2/2026** — pendiente de extraer; depende conceptualmente de esta sección.

La Ley 21/2013 es el marco estatal de evaluación ambiental. Para instalaciones de AT, determina cuándo la AAP queda condicionada a obtener primero la DIA (EIA ordinaria) o el IIA (EIA simplificada). El órgano ambiental es la CCAA cuando la instalación sea de competencia autonómica.

### 8.1 EIA ordinaria — Umbral Anexo I (art. 7.1.a + Anexo I, Grupo 3g)

Requieren **Declaración de Impacto Ambiental (DIA)** previa a la AAP:

> **Líneas eléctricas** con voltaje **≥ 220 kV** y longitud **> 15 km**, así como sus **subestaciones asociadas**.
>
> **Excepción al umbral:** quedan fuera del Anexo I (no requieren EIA ordinaria por este punto) las líneas que discurran **íntegramente en subterráneo por suelo urbanizado**, aunque superen ambos umbrales.

Adicionalmente, cualquier proyecto del Anexo II sube a EIA ordinaria si:
- el órgano ambiental lo decide caso por caso por los criterios del Anexo III (art. 7.1.b), o
- el promotor lo solicita voluntariamente (art. 7.1.d), o
- una modificación de un proyecto ya incluido en el Anexo I cumple por sí sola los umbrales del Anexo I (art. 7.1.c).

### 8.2 EIA simplificada — Umbral Anexo II (art. 7.2.a + Anexo II, Grupo 4b y 4c)

Requieren **Informe de Impacto Ambiental (IIA)**:

> **Grupo 4b** — Líneas eléctricas **≥ 15 kV** y longitud **> 3 km**, no incluidas en el Anexo I, con sus subestaciones asociadas. También por debajo de estos umbrales cuando se dé cualquiera de estas condiciones:
> - Afectan a espacios protegidos Red Natura 2000, espacios naturales protegidos, Ramsar u otros espacios especiales (criterio general 1 del Anexo II).
> - Se solapan con corredores ecológicos declarados, áreas críticas de especies amenazadas u otras áreas de protección especial de especies (criterio general 2 del Anexo II).
> - No incluyen las medidas del **RD 1432/2008** de protección de avifauna contra colisión y electrocución.
> - Discurren a **< 200 m de población** o a **< 100 m de viviendas aisladas** en algún tramo.
>
> **Excepción:** quedan fuera del Grupo 4b las líneas que discurran íntegramente en subterráneo por suelo urbanizado. Esta excepción aparece al final de toda la frase del Grupo 4b en el Anexo II, por lo que **exime de todos los criterios del Grupo 4b** (umbral tensión/longitud, RD 1432/2008, proximidad a viviendas/población y criterios generales 1 y 2 del Anexo II). La única captura que sobrevive es la del **art. 7.2.b** (afectación apreciable a Red Natura 2000 desde fuera del perímetro — proyectos no incluidos en ningún Anexo), documentada en §8.3.

> **Grupo 4c** — Repotenciación de líneas de transmisión existentes cuando cumplan los criterios generales 1 o 2 del Anexo II (espacios protegidos o corredores ecológicos).

#### Criterios generales del Anexo II (aplicables como cláusula de captura por debajo de umbrales)

| Criterio | Contenido |
|---|---|
| **1** | Proyectos en espacios Red Natura 2000, espacios naturales protegidos, humedales Ramsar, sitios Patrimonio Mundial, zonas OSPAR/ZEPIM, zonas núcleo/tampón de Reservas de Biosfera UNESCO. No aplica a proyectos expresamente permitidos por la zonificación del espacio ni a proyectos sin efectos adversos apreciables (informe del órgano gestor). |
| **2** | Proyectos solapados con corredores/conectores ecológicos declarados, áreas críticas de planes de recuperación/conservación de especies amenazadas, otras áreas de protección especial de especies, hábitats de interés comunitario en estado desfavorable, o áreas para protección de especies de pesca/marisqueo. Salvo informe del órgano gestor de ausencia de efectos adversos. |

### 8.3 EIA simplificada por afección a Red Natura 2000 — proyecto fuera de Anexos (art. 7.2.b)

Aunque el proyecto no esté en el Anexo I ni en el Anexo II, si puede afectar de forma **apreciable, directa o indirectamente, a Espacios Protegidos Red Natura 2000**, requiere EIA simplificada. En este caso el EsIA solo analiza las repercusiones sobre Red Natura 2000 (art. 45.1.e).

### 8.4 Silencio ambiental — regla general (art. 10)

La falta de emisión de la DIA o del IIA en plazo **en ningún caso** equivale a evaluación ambiental favorable. No existe silencio positivo ambiental. Si no se emite en plazo, la AAP no puede resolverse favorablemente.

Contrastar con el régimen excepcional del **art. 6 RDL 6/2022 / art. 22 RDL 20/2022** (procedimiento de determinación de afección ambiental para renovables), donde el silencio del órgano ambiental en 2 meses sí obliga a pasar por el procedimiento EIA de la Ley 21/2013 — lo que equivale en la práctica a un silencio desestimatorio del procedimiento simplificado, aunque la instalación pueda continuar por la vía EIA ordinaria.

### 8.5 Cuadro resumen — umbrales para instalaciones eléctricas AT

| Caso | Tipo de EIA | Instrumento | Condición de escape |
|---|---|---|---|
| Línea AT **≥ 220 kV** y **> 15 km** | EIA ordinaria | DIA | Íntegramente subterránea por suelo urbanizado |
| Subestación asociada a línea anterior | EIA ordinaria | DIA | Ídem |
| Línea AT **≥ 15 kV** y **> 3 km** (< 220 kV o ≤ 15 km) | EIA simplificada | IIA | Íntegramente subterránea por suelo urbanizado |
| Subestación asociada a línea anterior | EIA simplificada | IIA | Ídem |
| Línea cualquier tensión/longitud + criterio gral. 1 o 2 | EIA simplificada | IIA | Sin escape |
| Línea cualquier tensión/longitud + sin medidas RD 1432/2008 | EIA simplificada | IIA | Sin escape |
| Línea cualquier tensión/longitud + < 200 m población o < 100 m vivienda aislada | EIA simplificada | IIA | Sin escape |
| Repotenciación de línea existente + criterio gral. 1 o 2 | EIA simplificada | IIA | Sin escape |
| Cualquier proyecto (no en Anexo I ni II) + afección apreciable Red Natura 2000 | EIA simplificada | IIA | Sin escape |
| Resto (sin criterios anteriores) | Sin EIA | — | — |

### 8.6 Variables de contexto — MAPEO_CONTEXTO

Ley 2/2026 extraída. Deduplicación completada contra `DISEÑO_CONTEXT_ASSEMBLER.md` (sesión 2026-04-05).

| Variable | Decisión |
|---|---|
| `tension_kv` | ELIMINAR — ya existe `tension_nominal_kv` (l.97 ContextAssembler) |
| `longitud_km` | NUEVA |
| `discurre_integra_subterranea_suelo_urbanizado` | REDISEÑAR → se separa en `discurre_integra_subterranea` (boolean, condición "íntegramente") + `clasificacion_suelo_lista` (enum LISTA). Ver §9.8 y DISEÑO_CONTEXT_ASSEMBLER para definición final. |
| `ubicacion_red_natura_2000` | REUTILIZAR la existente (l.122) para criterio 1 del Grupo 4b |
| `puede_afectar_red_natura_2000` | NUEVA — para art. 7.2.b ("puedan afectar de forma apreciable, directa o indirectamente"); dato, distinta de `ubicacion_` |
| `requiere_eia_ordinaria` | REUTILIZAR existente (l.113) |
| `requiere_eia_simplificada` | NUEVA |
| `hito_dia_obtenida` | ELIMINAR — ya existe `hito_dia_favorable` (l.110) |
| `hito_iia_obtenido` | NUEVA |

---

## 9. Ley 2/2026, de 12 de marzo — Instrumentos de prevención ambiental aplicables a instalaciones AT

> **BOJA núm. 54 de 20/03/2026** — sedeboja id_tecnico 40751. Entrada en vigor **20/06/2026**.
> Para plazos del procedimiento AAU y AAUS: ver `NORMATIVA_PLAZOS.md §2.6`.
> Para umbrales EIA que determinan cuál instrumento aplica: ver `NORMATIVA_EXCEPCIONES_AT.md §8` (Ley 21/2013).
> Para régimen transitorio y derogaciones: ver análisis previo `docs_prueba/temp/ley2026_analisis_EV_DD_DT.md`.

La Ley 2/2026 sustituye a la GICA (Ley 7/2007) como norma autonómica de prevención ambiental. Para instalaciones AT, determina el instrumento ambiental autonómico exigible en función de los umbrales de la Ley 21/2013.

### 9.1 Jerarquía de instrumentos (art. 52)

Los instrumentos de prevención ambiental son, por orden de prioridad descendente:

1. **Autorización Ambiental Integrada (AAI)** — art. 57: instalaciones del anejo 1 del TRLPCIC (grandes instalaciones industriales). No aplica a líneas eléctricas AT convencionales.
2. **Autorización Ambiental Unificada (AAU)** — art. 67: proyectos del **Anexo I de la Ley 21/2013**. Integra la DIA (EIA ordinaria). Competencia: Consejería de Medio Ambiente.
3. **Autorización Ambiental Unificada Simplificada (AAUS)** — art. 79: proyectos del **Anexo II de la Ley 21/2013** + proyectos que puedan afectar apreciablemente a Red Natura 2000 aunque no estén en ningún Anexo. Integra el IIA (EIA simplificada). Competencia: Consejería de Medio Ambiente.
4. **Licencia Ambiental** — art. 89: actuaciones del Anexo I de la Ley 2/2026 (lista propia). Competencia: **ayuntamiento**. No aplica a instalaciones AT de líneas de cierta longitud (estas quedan en AAUS o AAU); puede aplicar a centros de transformación o subestaciones de distribución de pequeño tamaño si figuran en el Anexo I.
5. **Declaración Responsable de los Efectos Ambientales** — art. 100: actuaciones residuales del Anexo I de Ley 2/2026 marcadas para este régimen. Competencia: ayuntamiento.

### 9.2 Instrumento aplicable a instalaciones AT — cuadro resumen

| Umbral (Ley 21/2013) | Instrumento ambiental autonómico | EIA integrada | Competencia ambiental |
|---|---|---|---|
| Línea AT **≥ 220 kV** y **> 15 km** (no ínteg. subterránea urb.) | **AAU** (art. 67.1.a) | DIA (EIA ordinaria) | Consejería Medio Ambiente |
| Subestación asociada a línea anterior | **AAU** (art. 67.1.a) | DIA | Consejería Medio Ambiente |
| Línea AT **≥ 15 kV** y **> 3 km** (fuera de Anexo I) o criterios Red Natura 2000 | **AAUS** (art. 79.1.a/b) | IIA (EIA simplificada) | Consejería Medio Ambiente |
| Subestación asociada a línea anterior | **AAUS** (art. 79.1.a/b) | IIA | Consejería Medio Ambiente |
| Proyecto AT no en Anexo I ni II, pero afecta apreciablemente Red Natura 2000 | **AAUS** (art. 79.1.b) | IIA | Consejería Medio Ambiente |
| Instalación AT de competencia estatal (REE, red transporte) | **Sin AAU/AAUS autonómica** (arts. 67.3 y 79.3) | Pronunciamiento ambiental estatal | Ministerio (MITECO) |
| Subestación o CT pequeño en Anexo I Ley 2/2026 | **Licencia Ambiental** (art. 89) | No integra EIA | Ayuntamiento |

### 9.3 Exclusión de AAU/AAUS para instalaciones de competencia estatal (arts. 67.3 y 79.3)

"Las actuaciones cuya evaluación ambiental sea de competencia estatal, no estarán sometidas a autorización ambiental unificada [/ simplificada]."

→ Instalaciones de la red de transporte (competencia del Ministerio de Industria + MITECO): sin AAU ni AAUS autonómica. El promotor debe obtener pronunciamiento ambiental favorable del órgano ambiental estatal (DIA/IIA de competencia estatal) antes de que se otorgue la AAP.

→ Instalaciones de distribución o generación de competencia autonómica (Junta de Andalucía): sí requieren AAU o AAUS según umbrales.

> ⚠️ **Cambio de régimen respecto a la GICA — pendiente de verificar al analizar GICA + Decreto 356/2010 + Instrucción Conjunta 1/2022:**
> Bajo el régimen anterior (GICA + Decreto 356/2010), las instalaciones de transporte intra-CCAA sí requerían AAU autonómica, y la **Instrucción Conjunta 1/2022** establecía que dicha AAU se tramitaba de forma **integrada** en el procedimiento de AAP (instrucción conjunta AAP+AAU). Con la Ley 2/2026, arts. 67.3 y 79.3 excluyen expresamente la AAU/AAUS para instalaciones de competencia ambiental estatal, de modo que el EIA lo tramita MITECO por separado. Esto **rompe la instrucción conjunta** para este tipo de instalaciones: ya no hay AAU autonómica que integrar en la AAP. Al analizar la GICA y el Decreto 356/2010 verificar el alcance exacto de ese régimen anterior y el impacto del cambio en expedientes en curso (DT 1ª).

### 9.4 Régimen especial — instalaciones declaradas de utilidad e interés general o promovidas por la Junta (arts. 67.4 y 79.4)

Estas actuaciones se someten igualmente al procedimiento AAU/AAUS, pero la resolución del órgano ambiental adopta la forma de **informe de carácter vinculante** en lugar de resolución de autorización. El procedimiento tiene carácter instrumental respecto al procedimiento de autorización o aprobación de la actuación principal.

Implicación para BDDAT: cuando el expediente está declarado de utilidad e interés general, el hito de "obtención de la AAU/AAUS" puede materializarse como informe vinculante del órgano ambiental, no como resolución de otorgamiento clásica.

### 9.5 Régimen transitorio — expedientes en curso (DT 1ª)

Los procedimientos de AAU (antes llamada igual bajo la GICA) y demás instrumentos de prevención ambiental **iniciados antes del 20/06/2026** siguen su tramitación íntegra conforme a la **GICA (Ley 7/2007)** y sus normas de desarrollo (Decreto 356/2010, etc.).

→ El motor debe conocer la fecha de inicio del expediente ambiental para aplicar la norma correcta:
- Iniciado antes del 20/06/2026 → GICA + Decreto 356/2010
- Iniciado desde el 20/06/2026 → Ley 2/2026

### 9.6 Variables de contexto — MAPEO_CONTEXTO

Deduplicación completada contra `DISEÑO_CONTEXT_ASSEMBLER.md` (sesión 2026-04-05).

| Variable | Decisión |
|---|---|
| `requiere_aau` | REUTILIZAR existente (l.102); actualizar norma_origen añadiendo Ley 2/2026 art. 67 |
| `requiere_aaus` | NUEVA |
| `competencia_ambiental_estatal` | NUEVA |
| `declarada_utilidad_interes_general` | NUEVA pero estado=pendiente_de_revisar; nota: aplica solo a instalaciones promovidas por la Administración sin ser distribución/transporte (esas ya son de interés general per se); casos muy raros en BDDAT |
| `fecha_inicio_expediente_ambiental` | NUEVA — date, dato; distingue si tramitación por GICA (< 20/06/2026) o Ley 2/2026 (≥ 20/06/2026) |
| `hito_aau_obtenida` | NUEVA |
| `hito_aaus_obtenida` | NUEVA |

> **Distinción `requiere_aau` / `requiere_eia_ordinaria`:** `requiere_aau` es el instrumento autonómico (Andalucía); `requiere_eia_ordinaria` cubre también el caso de competencia estatal (donde existe EIA ordinaria pero sin AAU autonómica). Mantener ambas variables con significado separado.
>
> **`requiere_aau` bajo GICA (antes 20/06/2026):** la variable lógica es la misma; cambia la norma que la activa (Decreto 356/2010 + GICA vs Ley 2/2026). Cuando se extraiga el Decreto 356/2010 verificar que los umbrales coinciden con los de Ley 21/2013.

---

### 9.7 Licencia Ambiental — Categoría 3 Anexo I Ley 2/2026 (competencia municipal)

> Instrumento de competencia del **Ayuntamiento** (art. 91 Ley 2/2026). Sustituye a la Calificación Ambiental de la GICA.
> **Previa a la AAP:** art. 89.4 — *"No podrá otorgarse licencia o autorización sustantiva de cualquier Administración... sin haber obtenido previamente la licencia ambiental."*

#### Diseño de umbrales — continuidad y exclusividad con AAUS/AAU

La Ley 2/2026 diseña la Categoría 3 del Anexo I para que sus umbrales sean **continuos y excluyentes** respecto a los de AAUS (Ley 21/2013 Anexo II): si se activan los criterios\* que remiten a la EIA, el proyecto sale de la Categoría 3 y entra en AAUS; si no se activan, queda en Licencia Ambiental. No hay solapamiento ni hueco entre tramos de distinto instrumento.

El sistema AAU / AAUS / LA / sin instrumento es **monotónico** respecto a las tres variables principales, verificado mediante análisis matricial exhaustivo (sesión 2026-04-05):

- **Tensión:** a mayor tensión nominal, igual o mayor instrumento (T < 15 kV → LA o sin instrumento; T ≥ 15 kV → LA o AAUS; T ≥ 220 kV y L > 15 km → AAU).
- **Longitud:** a mayor longitud, igual o mayor instrumento para un tipo y suelo dados. No existe ninguna combinación en que cruzar un umbral de longitud reduzca el instrumento requerido.
- **Clasificación de suelo (modelo concéntrico LISTA):** el suelo se organiza en capas concéntricas de menor a mayor antropización — rústico / urbanizable / urbano / urbanizado. A mayor antropización (capas interiores), mayor longitud o tensión puede tener la instalación sin requerir instrumento, porque las capas interiores ya no tienen valores naturales que proteger. El escape de LA para suelo urbano y el escape de EIA para suelo urbanizado son consecuencia de este principio, no vacíos legales.

Los casos sin instrumento son siempre: (a) instalaciones por debajo de todos los umbrales aplicables, o (b) instalaciones en capas de suelo suficientemente antropizadas. No existe ninguna combinación en que una instalación con mayor impacto (T, L o suelo más exterior) quede sin instrumento mientras una de menor impacto sí lo requiere.

#### Umbrales — líneas eléctricas y subestaciones asociadas

Escape general de toda la Categoría 3: **íntegramente subterránea por suelo urbano** (clasificación LISTA, Ley 7/2021 art. 21).

> ⚠️ **Distinción normativa crítica:** el escape de Licencia Ambiental usa **"suelo urbano"** (LISTA) y el escape de EIA ordinaria/simplificada (Ley 21/2013) usa **"suelo urbanizado"** (concepto del TRLSRU estatal). Son marcos normativos distintos. En la práctica "suelo urbano" LISTA probablemente equivale a "suelo urbanizado" TRLSRU, pero requiere verificación jurídica. Las variables de contexto los tratan como campos separados hasta que se cierre esa verificación.

| Subcategoría | Tensión | Tipo / Longitud | Condición | Instrumento |
|---|---|---|---|---|
| **3.1** | T ≥ 15 kV | Aérea — **1 km < L ≤ 3 km** | Sin criterios\* | LA |
| **3.2** | T < 15 kV | Aérea — **L > 1 km** | Sin criterios\* | LA |
| **3.3** | T < 15 kV | Subterránea — **L > 3 km** | Sin criterios\* + suelo rústico | LA |

> **Criterios\*** — si concurre cualquiera de estos, el proyecto va a AAUS (no LA):
> - Criterios generales 1 o 2 del Anexo III Ley 21/2013 (Red Natura 2000, corredores ecológicos)
> - No incluye medidas del RD 1432/2008 (protección avifauna AT)
> - Discurre a < 200 m de población o < 100 m de viviendas aisladas en algún tramo
> - *Excepción a la excepción:* lo anterior no aplica si la línea discurre íntegramente en subterráneo por suelo urbanizado (Ley 21/2013)

> **Nota clasificación suelo (Anexo I nota \*\*):** para la Licencia Ambiental, la clasificación del suelo sigue la Ley 7/2021 (LISTA). Categorías relevantes: **suelo urbano** (escapa de LA), **suelo urbanizable** (no escapa), **suelo rústico** (no escapa; es el equivalente al antiguo "suelo no urbanizable"). La condición 3.3 requiere explícitamente suelo rústico.

#### Relación procedimental con la AAP

```
Licencia Ambiental (Ayuntamiento) → previa → AAP (Delegación Territorial)
```

La resolución de la Licencia Ambiental (plazo máximo 3 meses — art. 92.6; silencio desestimatorio) debe producirse **antes** de que la Delegación Territorial pueda otorgar la AAP. El hito `hito_licencia_ambiental_obtenida = true` es condición necesaria para resolver la fase AAP cuando `requiere_licencia_ambiental = true`.

#### Instalaciones sin línea asociada

Las subestaciones y CTs **asociadas** a una línea de la Categoría 3 siguen el mismo instrumento. Pendiente de verificar si existen CTs de distribución independientes (sin línea asociada) con categoría propia en el Anexo I.

### 9.8 Variables de contexto — MAPEO_CONTEXTO Licencia Ambiental

| Variable | Decisión |
|---|---|
| `clasificacion_suelo_lista` | NUEVA — enum `'urbano'`/`'urbanizable'`/`'rustico'`; clasifica el suelo según LISTA (Ley 7/2021); alimenta: escape LA (solo `'urbano'`), escape EIA 21/2013 (probable equivalencia `'urbano'` ≈ "urbanizado" — pendiente verificación), condición Decreto 9/2011 (`'urbano'` O `'urbanizable'`). Supersede `es_suelo_urbano_o_urbanizable` (l.100) que mezcla ambas categorías en un boolean sin distinción |
| `discurre_integra_subterranea` | NUEVA — boolean; la línea discurre íntegramente en subterráneo en toda su longitud; distinto de `es_linea_subterranea` (ese no captura "íntegramente"). Combinado con `clasificacion_suelo_lista` determina el escape de LA y de los umbrales EIA. **Redesign:** reemplaza la variable `discurre_integra_subterranea_suelo_urbanizado` (§8.6) que combinaba dos condiciones separables en un solo boolean |
| `requiere_licencia_ambiental` | NUEVA |
| `hito_licencia_ambiental_obtenida` | NUEVA |
