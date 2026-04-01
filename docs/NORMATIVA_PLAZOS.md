# NORMATIVA — Plazos administrativos aplicables a BDDAT

> **Fuente:** Ley 39/2015, de 1 de octubre (LPACAP) — texto consolidado BOE. Leyes sectoriales pendientes de extracción (ver §2).
> **Aplica a:** Motor de plazos (`app/services/plazos.py`), ContextAssembler, diseño de BD de plazos.
> **Estado:** §1 completo (sesión 2026-04-01). §2 pendiente — diferido hasta tener estructura BD definida.

---

## Índice

1. [LPACAP — Marco general de plazos](#1-lpacap--marco-general-de-plazos)
   - [1.1 Plazo máximo para resolver (arts. 21-25)](#11-plazo-máximo-para-resolver-arts-21-25)
   - [1.2 Cómputo de plazos (arts. 29-32)](#12-cómputo-de-plazos-arts-29-32)
   - [1.3 Recursos y sus plazos (arts. 112-126)](#13-recursos-y-sus-plazos-arts-112-126)
2. [Particularizaciones sectoriales](#2-particularizaciones-sectoriales)

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

### 1.2 Cómputo de plazos (arts. 29-32)

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

### 1.3 Recursos y sus plazos (arts. 112-126)

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

> **Estado:** Pendiente. Diferido hasta tener modelo de datos de plazos definido.
> Ver `DISEÑO_FECHAS_PLAZOS.md §7` para el plan de trabajo.

Normas a analizar:
- **RD 1955/2000** — Plazos del procedimiento de autorización de instalaciones eléctricas.
- **Decreto 9/2011** (Junta de Andalucía) — Agilización; posibles modificaciones de plazos estándar.
- **Ley 21/2013** — Plazos del procedimiento de EIA (consultas, información pública, pronunciamiento ambiental).
- **Decreto-ley 26/2021** — Simplificación; excepciones procedimentales.
