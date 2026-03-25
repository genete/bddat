# Estructura de Fases, Trámites y Tareas (ESFTT)

> Fuente de verdad: `docs/ESTRUCTURA_FTT.json`
> Última sincronización: 2026-03-25

**Versión:** 5.5 | **Fecha:** 2026-03-25

Este documento es la versión legible por humanos del JSON estructural. El JSON es la fuente de verdad para código e IA; este MD es la referencia de consulta rápida.

Para decisiones de diseño, motivaciones y reglas del motor: ver documentos referenciados en cada sección.

---

## Tareas atómicas

| Código | Nombre | Entrada | Salida | Habilita |
|---|---|---|---|---|
| `ANALIZAR` | Análisis | documento_usado_id (oblig.) | documento_producido_id (oblig.) | REDACTAR |
| `REDACTAR` | Redactar | documento_usado_id (opt.) | documento_producido_id (oblig. — borrador) | FIRMAR |
| `FIRMAR` | Firmar | documento_usado_id (oblig. — borrador) | documento_producido_id (oblig. — firmado) | NOTIFICAR, PUBLICAR |
| `NOTIFICAR` | Notificar | documento_usado_id (oblig. — firmado) | documento_producido_id (oblig. — justificante) | ESPERAR_PLAZO, INCORPORAR |
| `PUBLICAR` | Publicar | documento_usado_id (oblig. — firmado) | documento_producido_id (oblig. — justificante) | ESPERAR_PLAZO |
| `ESPERAR_PLAZO` | Esperar Plazo | — | — | INCORPORAR (si respuesta), FIN (si vence) |
| `INCORPORAR` | Incorporar | — | documentos_tarea N:M (oblig. ≥1) | ANALIZAR |

**Nota INCORPORAR (v5.5):** usa tabla `documentos_tarea` en lugar de `documento_producido_id` (deprecado para esta tarea). Ver `DISEÑO_ANALISIS_SOLICITUD.md §5` y `DISEÑO_SUBSISTEMA_DOCUMENTAL.md`.

---

## Patrones de flujo

| Código | Nombre | Secuencia | Destinatario |
|---|---|---|---|
| A | Análisis Interno | ANALIZAR | Interno |
| B | Comunicación Simple | REDACTAR → FIRMAR → NOTIFICAR | Externo identificado |
| C | Comunicación con Espera | REDACTAR → FIRMAR → NOTIFICAR → ESPERAR_PLAZO | Externo identificado |
| D | Publicación Oficial | REDACTAR → FIRMAR → PUBLICAR → ESPERAR_PLAZO | Difusión pública |
| E | Recepción y Análisis | INCORPORAR → ANALIZAR | Interno |
| F | Espera Pasiva | ESPERAR_PLAZO | Sistema |

Los patrones son orientativos y combinables. `C+` = patrón C extendido con INCORPORAR+ANALIZAR al final.

---

## Fases y trámites

### ANÁLISIS_SOLICITUD
*Verificación de documentación, admisibilidad y análisis técnico en acto único. Fusiona REGISTRO_SOLICITUD + ADMISIBILIDAD + ANALISIS_TECNICO (v5.5). Ver `DISEÑO_ANALISIS_SOLICITUD.md`.*

| Trámite | Patrón | Tareas indicativas |
|---|---|---|
| `ANALISIS_DOCUMENTAL` | A | ANALIZAR |
| `REQUERIMIENTO_SUBSANACION` | C+ | REDACTAR → FIRMAR → NOTIFICAR → ESPERAR_PLAZO → INCORPORAR → ANALIZAR |
| `COMUNICACION_INICIO` | B | REDACTAR → FIRMAR → NOTIFICAR |

---

### CONSULTA_MINISTERIO
*Informe preceptivo al Ministerio competente. Exclusivo instalaciones de transporte.*

| Trámite | Patrón | Tareas indicativas |
|---|---|---|
| `SOLICITUD_INFORME` | C | REDACTAR → FIRMAR → NOTIFICAR → ESPERAR_PLAZO |
| `RECEPCION_INFORME` | E | INCORPORAR → ANALIZAR |

---

### COMPATIBILIDAD_AMBIENTAL
*Informe de compatibilidad ambiental. Exclusivo instalaciones con AAU o AAUS previas.*

| Trámite | Patrón | Tareas indicativas |
|---|---|---|
| `SOLICITUD_COMPATIBILIDAD` | C | REDACTAR → FIRMAR → NOTIFICAR → ESPERAR_PLAZO |
| `AUDIENCIA` | EC | INCORPORAR → ANALIZAR → REDACTAR → FIRMAR → NOTIFICAR → ESPERAR_PLAZO |
| `RECEPCION_INFORME` | E | INCORPORAR → ANALIZAR |

---

### ADMISION_TRAMITE
*Resolución de admisión a trámite. Solo instalaciones de generación renovable.*

| Trámite | Patrón | Tareas indicativas |
|---|---|---|
| `ANALISIS_ADMISION` | AB | ANALIZAR → REDACTAR → FIRMAR → NOTIFICAR |
| `ALEGACIONES` | EB | INCORPORAR → ANALIZAR → REDACTAR → FIRMAR → NOTIFICAR |

---

### CONSULTAS
*Informes sectoriales a organismos (RD 1955/2000). Un trámite por organismo. Ver `DISEÑO_CONSULTAS_ORGANISMOS.md`.*

| Trámite | Patrón | Plazo legal | Resultados ANALIZAR |
|---|---|---|---|
| `CONSULTA_SEPARATA` | C+ | 30 días (15 en AAC sin DUP con AAP previa) | sin_respuesta, conformidad, oposicion, reparos_organismo, condicionado |
| `CONSULTA_TRASLADO_TITULAR` | C+ | 15 días | sin_respuesta, conformidad, reparos_titular |
| `CONSULTA_TRASLADO_ORGANISMO` | C+ | 15 días | sin_respuesta, conformidad, oposicion, reparos_organismo, condicionado |

Tareas indicativas en los tres trámites: REDACTAR → FIRMAR → NOTIFICAR → ESPERAR_PLAZO → INCORPORAR → ANALIZAR

---

### INFORMACION_PUBLICA
*Exposición pública del proyecto para alegaciones.*

| Trámite | Patrón | Tareas indicativas | Nota |
|---|---|---|---|
| `ANUNCIO_BOE` | C+E(parcial)+F | R→F→N→EP→INC→EP | Doble espera: hasta publicación + plazo alegaciones |
| `ANUNCIO_BOP` | C+E(parcial)+F | R→F→N→EP→INC→EP | Doble espera: hasta publicación + plazo alegaciones |
| `ANUNCIO_PRENSA` | C+E(parcial)+F | R→F→N→EP→INC→EP | Doble espera: hasta publicación + plazo alegaciones |
| `TABLON_AYUNTAMIENTOS` | C+E(parcial) | R→F→N→EP→INC | Certificado llega al final del plazo |
| `PORTAL_TRANSPARENCIA` | D | REDACTAR→FIRMAR→PUBLICAR→EP | Controlamos fecha de publicación |
| `RECEPCION_ALEGACION` | EC | INC→ANALIZAR→R→F→N→EP | — |
| `ANALISIS_ALEGACIONES` | A | ANALIZAR | Resultado referenciado en plantilla de resolución |

*R=REDACTAR, F=FIRMAR, N=NOTIFICAR, EP=ESPERAR_PLAZO, INC=INCORPORAR*

---

### FIGURA_AMBIENTAL_EXTERNA
*AAU/AAUS/CA no integrada en tramitación sustantiva.*

| Trámite | Patrón | Tareas indicativas |
|---|---|---|
| `SOLICITUD_FIGURA` | C | REDACTAR → FIRMAR → NOTIFICAR → ESPERAR_PLAZO (plazo=0) |
| `RECEPCION_FIGURA` | E | INCORPORAR → ANALIZAR |

---

### AAU_AAUS_INTEGRADA
*AAU/AAUS integrada en el procedimiento sustantivo.*

| Trámite | Patrón | Tareas indicativas |
|---|---|---|
| `REMISION_MEDIO_AMBIENTE` | C | REDACTAR → FIRMAR → NOTIFICAR → ESPERAR_PLAZO (plazo=0) |
| `RECEPCION_DICTAMEN` | E | INCORPORAR → ANALIZAR |

---

### RESOLUCION
*Resolución finalizadora de la solicitud.*

| Trámite | Patrón | Tareas indicativas |
|---|---|---|
| `ELABORACION` | AB (sin NOTIFICAR) | ANALIZAR → REDACTAR → FIRMAR |
| `NOTIFICACION` | B (simplificado) | REDACTAR → NOTIFICAR |
| `PUBLICACION` | D (sin ESPERAR_PLAZO) | REDACTAR → FIRMAR → PUBLICAR |
