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
