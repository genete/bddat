# NORMATIVA — Excepciones, regímenes especiales y casos límite AT

> **Aplica a:** Motor de reglas — desviaciones respecto al procedimiento estándar AAP/AAC/AE.
> **Fuentes de verdad:** `docs/NORMATIVA_LEGISLACION_AT.md §6` · `docs/NORMATIVA_PLAZOS.md §2`.
> **Estado:** En construcción — sesión 2026-04-03. LSE + RD 1955/2000 + Decreto 9/2011 + DL 26/2021 extraídos.

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

**Condiciones de aplicación:**

| Condición | Detalle |
|---|---|
| Competencia | **Administración General del Estado** — NO aplica directamente a CCAA (Andalucía) |
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

**Aplica exclusivamente a proyectos competencia AGE** — igual que el art. 7. Misma limitación para BDDAT/Andalucía.

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

**Implicación en BDDAT:** la suspensión del art. 13 opera sobre proyectos sin permiso de acceso/conexión — complementa la variable `tiene_punto_acceso_conexion` (ya definida en §6 de GUIA_NORMAS.md).
