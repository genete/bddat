# NORMATIVA — Excepciones, regímenes especiales y casos límite AT

> **Aplica a:** Motor de reglas — desviaciones respecto al procedimiento estándar AAP/AAC/AE.
> **Fuentes de verdad:** `docs/NORMATIVA_LEGISLACION_AT.md §6` · `docs/NORMATIVA_PLAZOS.md §2`.
> **Estado:** En construcción — sesión 2026-04-02. LSE + RD 1955/2000 extraídos.

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
| [§3](#3-normas-pendientes-de-extracción) | Normas pendientes |

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

## 3. Normas pendientes de extracción

| Norma | Excepciones esperadas | Prioridad |
|---|---|---|
| **Decreto 9/2011** (Junta) | Exenciones de fases para instalaciones menores; agilizaciones específicas | Alta |
| **Ley 21/2013** (EIA) | Régimen de consultas previas, información pública ambiental, plazos DIA | Alta |
| **DL 26/2021** (Junta) DF 4ª | Exención de información pública para instalaciones sin DUP y sin AAU | Alta |
| **RD-ley 23/2020 + 8/2023** | Hitos administrativos para renovables; condicionan admisión a trámite de AAP | Media |
| **RD-ley 6/2022 + 20/2022** | Tramitación conjunta AAP+AAC para renovables; afección ambiental simplificada | Media |
| **RD-ley 7/2025** | Almacenamiento hibridado: tramitación conjunta, plazos reducidos; repotenciación | Media |
| **Ley 4/2025** (Espacios productivos) | DA 7ª: acometidas de un solo titular; arts. 59-61: líneas directas, redes cerradas | Media |
| **Art. 95.3 LPACAP** | Reutilización de actos de expediente caducado en nuevo procedimiento | Baja — casos límite |
| **Modificaciones** (RD 1955/2000) | Cuándo una modificación requiere nueva AAP vs. solo AAC vs. comunicación | Alta — frecuente |
