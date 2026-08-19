# Estructura de Fases, Trámites y Tareas (ESFTT)

> Fuente de verdad: `docs/referencia/ESTRUCTURA_FTT.json`
> Última sincronización: 2026-08-19 (#789 — notación EP(0)/plazo=0 corregida)

**Versión:** 6.3 | **Fecha:** 2026-08-07

Este documento es la versión legible por humanos del JSON estructural. El JSON es la fuente de verdad para código e IA; este MD es la referencia de consulta rápida.

Para decisiones de diseño, motivaciones y reglas del motor: ver documentos referenciados en cada sección.

---

## Tareas atómicas

| Código | Nombre | Entrada | Salida | Habilita |
|---|---|---|---|---|
| `ANALIZAR` | Análisis | 1..N consumidos (≥1 oblig.) | documento producido (oblig. — tipo DIAGNOSTICO) | ELABORAR |
| `ELABORAR` | Elaborar | consumidos (opt. — DIAGNOSTICO de ANALIZAR si existe) | documento producido (oblig.) | NOTIFICAR |
| `NOTIFICAR` | Notificar | 1..N consumidos (incluye doc de ELABORAR) | documento producido (oblig. — justificante) | ESPERAR_PLAZO |
| `ESPERAR_PLAZO` | Esperar Plazo | consumido (oblig. si plazo>0 — justificante de NOTIFICAR; ninguno si plazo=0) | — | FIN (si vence) |

**Cambios v6.3 (#764) — regla de recepción en `ESPERAR_PLAZO`:**
- El producido es **uno**: el documento que acredita el hecho y porta su fecha administrativa (registro de entrada o solicitud, justificante de BandeJA si el remitente es interno, acuse o certificado acreditativo si lo esperado es una publicación).
- Los anexos de ese registro no se vinculan a `ESPERAR_PLAZO`: entran al pool y los consume (0..N) el `ANALIZAR` siguiente, que es donde se incorporan al expediente.
- Corolario estructural: todo `ESPERAR_PLAZO` que pueda recibir documentación de terceros exige un `ANALIZAR` posterior — propio, del trámite receptor hermano, o añadido tras él si es el último trámite de la fase. Esta exigencia se comprueba durante el desarrollo mediante repaso de fase a fase, sin crear issues a futuro, sino sobre la marcha.

**Cambios v6.1 (ADR-010, #420):**
- Los vínculos documentales de la tarea viven en `documentos_tarea` (N:M con campo `rol`), no en FK propias. Una tarea consume 0..N documentos y produce 0..1.

**Cambios v6.0 (ADR-003/004/005, #371):**
- `ELABORAR` reemplaza a `REDACTAR`+`FIRMAR` (redacción y firma en acto único)
- `INCORPORAR` eliminado: recepción de documentación externa pasa a `ESPERAR_PLAZO.documento_producido`
- `PUBLICAR` eliminado: se modela como patrón C (ELABORAR → NOTIFICAR → ESPERAR_PLAZO)
- `ANALIZAR` siempre produce tipo `DIAGNOSTICO`

---

## Patrones de flujo

| Código | Nombre | Secuencia | Destinatario |
|---|---|---|---|
| A | Análisis Interno | ANALIZAR | Interno |
| B | Comunicación Simple | ELABORAR → NOTIFICAR | Externo identificado |
| C | Comunicación con Espera | ELABORAR → NOTIFICAR → ESPERAR_PLAZO | Externo identificado |
| F | Espera Pasiva | ESPERAR_PLAZO | Sistema |

Los patrones son orientativos y combinables (p.ej. `A+C` = ANALIZAR → ELABORAR → NOTIFICAR → ESPERAR_PLAZO).

---

## Fases y trámites

### ANÁLISIS_SOLICITUD
*Verificación de documentación, admisibilidad y análisis técnico en acto único. Fusiona REGISTRO_SOLICITUD + ADMISIBILIDAD + ANALISIS_TECNICO (v5.5). Ver `DISEÑO_ANALISIS_SOLICITUD.md`.*

| Trámite | Patrón | Tareas indicativas |
|---|---|---|
| `ANALISIS_DOCUMENTAL` | A | ANALIZAR |
| `REQUERIMIENTO_SUBSANACION` | C+A | ELABORAR → NOTIFICAR → ESPERAR_PLAZO → ANALIZAR |
| `COMUNICACION_INICIO` | B | ELABORAR → NOTIFICAR | Obligatoria para Renovable (Hito 1 RD-ley 23/2020 art. 1.2). Opcional para otros tipos. |

---

### CONSULTA_MINISTERIO
*Informe preceptivo al Ministerio competente. Exclusivo instalaciones de transporte.*

| Trámite | Patrón | Tareas indicativas |
|---|---|---|
| `SOLICITUD_INFORME` | C | ELABORAR → NOTIFICAR → ESPERAR_PLAZO |
| `RECEPCION_INFORME` | A | ANALIZAR |

---

### COMPATIBILIDAD_AMBIENTAL
*Informe de compatibilidad ambiental. Exclusivo instalaciones con AAU o AAUS previas.*

| Trámite | Patrón | Tareas indicativas |
|---|---|---|
| `SOLICITUD_COMPATIBILIDAD` | C | ELABORAR → NOTIFICAR → ESPERAR_PLAZO |
| `COMUNICACION_AUDIENCIA` | A | ANALIZAR (condicional: solo si MA aprecia incompatibilidad; IC 1/2022, IV.3.3) |
| `RECEPCION_INFORME` | A | ANALIZAR |

---

### CONSULTAS
*Informes sectoriales a organismos (RD 1955/2000). Un trámite por organismo. Ver `DISEÑO_CONSULTAS_ORGANISMOS.md`.*

| Trámite | Patrón | Plazo legal | Resultados ANALIZAR |
|---|---|---|---|
| `CONSULTA_SEPARATA` | C+A | 30 días (15 en AAC sin DUP con AAP previa) | sin_respuesta, conformidad, oposicion, reparos_organismo, condicionado |
| `CONSULTA_TRASLADO_TITULAR` | C+A | 15 días | sin_respuesta, conformidad, reparos_titular |
| `CONSULTA_TRASLADO_ORGANISMO` | C+A | 15 días | sin_respuesta, conformidad, oposicion, reparos_organismo, condicionado |

Tareas indicativas en los tres trámites: ELABORAR → NOTIFICAR → ESPERAR_PLAZO → ANALIZAR

---

### INFORMACION_PUBLICA
*Exposición pública del proyecto para alegaciones. Ver #368, #369.*

| Trámite | Patrón | Tareas indicativas | Nota |
|---|---|---|---|
| `REDACTAR_ANUNCIO` | A (solo ELABORAR) | ELABORAR | Produce ANUNCIO_IP; consumido por ANUNCIO_* y TABLON (#368) |
| `ANUNCIO_BOE` | F+F | NOTIFICAR → EP → EP | Doble espera: hasta publicación + plazo alegaciones |
| `ANUNCIO_BOP` | F+F | NOTIFICAR → EP → EP | Doble espera: hasta publicación + plazo alegaciones |
| `ANUNCIO_PRENSA` | F+F | NOTIFICAR → EP → EP | Doble espera: hasta publicación + plazo alegaciones |
| `ANUNCIO_BOJA` | F+F | NOTIFICAR → EP → EP | Doble espera: hasta publicación + plazo alegaciones (#368) |
| `TABLON_AYUNTAMIENTOS` | C (sin ELABORAR) | NOTIFICAR → EP | Certificado llega en EP.documento_producido |
| `PORTAL_TRANSPARENCIA` | C | ELABORAR → NOTIFICAR → EP | Patrón C (#371, elimina PUBLICAR) |
| `ANUNCIO_TITULAR` | B | ELABORAR → NOTIFICAR | Notificación al titular sobre publicación IP (#369) |
| `RECEPCION_ALEGACION` | A+C | ANALIZAR → ELABORAR → NOTIFICAR → EP | ANALIZAR clasifica al alegante |
| `ANALISIS_ALEGACIONES` | A | ANALIZAR | Resultado referenciado en plantilla de resolución |

*EP=ESPERAR_PLAZO*

---

### FIGURA_AMBIENTAL_EXTERNA
*AAU/AAUS/CA no integrada en tramitación sustantiva.*

| Trámite | Patrón | Tareas indicativas |
|---|---|---|
| `SOLICITUD_FIGURA` | C | ELABORAR → NOTIFICAR → ESPERAR_PLAZO (sin plazo legal) |
| `RECEPCION_FIGURA` | A | ANALIZAR |

---

### AAU_AAUS_INTEGRADA
*AAU/AAUS integrada en el procedimiento sustantivo. 2 → 5 trámites (#372).*

| Trámite | Patrón | Tareas indicativas | Nota |
|---|---|---|---|
| `REMISION_RESULTADO_IP_CONSULTAS` | C | ELABORAR → NOTIFICAR → EP* | Renombrado desde REMISION_MEDIO_AMBIENTE |
| `RECEPCION_DICTAMEN` | A+C | ANALIZAR → ELABORAR → NOTIFICAR → EP* | — |
| `RECEPCION_PROPUESTA_INF_VINC` | A+C | ANALIZAR → ELABORAR → NOTIFICAR → EP* | Nuevo #372 |
| `RECEPCION_INFORME_VINCULANTE` | A | ANALIZAR | Nuevo #372 |
| `DISCREPANCIA_INF_VINC` | C | ELABORAR → NOTIFICAR → EP* | Condicional; nuevo #372 |

*EP\*=ESPERAR_PLAZO sin plazo legal (dictamen/propuesta/informe vinculante de
Medio Ambiente no tienen plazo cierto). Decisión #789: no se registra fila en
`catalogo_plazos` para estas tareas — la ausencia de fila ya produce el estado
`SIN_PLAZO` (rojo permanente en el árbol hasta que llega el documento), que es
el comportamiento correcto: sin plazo cierto no hay fecha en la que el sistema
pueda escalar la alerta por sí solo. Distinto del tope de 3 meses del art.
22.1.d LPACAP sobre la *suspensión* del plazo de la Solicitud, que es cuestión
aparte (#778, no fijado todavía).

---

### CONSULTA_OPERADOR_SISTEMA
*Consulta preceptiva al operador del sistema o gestor de red antes de resolver el cierre (art. 137 RD 1955/2000, mod. RD 88/2026). Silencio positivo en 3 meses. Exclusivo del procedimiento CIERRE.*

| Trámite | Patrón | Tareas indicativas | Nota |
|---|---|---|---|
| `SOLICITUD_INFORME_OPERADOR` | C | ELABORAR → NOTIFICAR → ESPERAR_PLAZO | PLAZO_DIAS=90, silencio=positivo |
| `RECEPCION_INFORME_OPERADOR` | A | ANALIZAR | Condicional: solo si el operador responde en plazo |

---

### RECONOCIMIENTO_INTERESADO
*Resolución sobre condición de interesado (art. 4 LPACAP). Fase finalizadora exclusiva de solicitudes tipo INTERESADO.*

| Trámite | Patrón | Tareas indicativas |
|---|---|---|
| `ELABORACION` | B (sin NOTIFICAR) | ELABORAR |
| `NOTIFICACION` | B (solo NOTIFICAR) | NOTIFICAR |

---

### RESOLUCION
*Resolución finalizadora de la solicitud.*

| Trámite | Patrón | Tareas indicativas |
|---|---|---|
| `ELABORACION` | B (sin NOTIFICAR) | ELABORAR (consume CERT_FIN_INSTRUCCION — #373) |
| `NOTIFICACION` | B (solo NOTIFICAR) | NOTIFICAR |
| `PUBLICACION` | C | ELABORAR → NOTIFICAR → ESPERAR_PLAZO |
