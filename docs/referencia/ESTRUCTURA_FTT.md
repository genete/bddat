# Estructura de Fases, Trámites y Tareas (ESFTT)

> Fuente de verdad: `docs/referencia/ESTRUCTURA_FTT.json`
> Última sincronización: 2026-09-23 (#928 — COMUNICACION_INICIO → COMUNICACION_INICIO_ADMISION; destinatario del NOTIFICAR en las notas del JSON)

**Versión:** 6.6 | **Fecha:** 2026-09-23

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

**Trámites con el receptor pendiente de formalizar** (detectados en el repaso de fase del 2026-08-07, deliberadamente sin issue: se corrigen en la fase en que toquen).

| Fase | Trámite | Situación |
|---|---|---|
| `AAU_AAUS_INTEGRADA` | `DISCREPANCIA_INF_VINC` | sin trámite receptor definido en el catálogo |
| `AAU_AAUS_INTEGRADA` | `RECEPCION_DICTAMEN` | receptor plausible, no formalizado |
| `AAU_AAUS_INTEGRADA` | `RECEPCION_PROPUESTA_INF_VINC` | receptor plausible, no formalizado |
| `AAU_AAUS_INTEGRADA` | `REMISION_RESULTADO_IP_CONSULTAS` | receptor plausible, no formalizado |
| `FIGURA_AMBIENTAL_EXTERNA` | `SOLICITUD_FIGURA` | receptor plausible, no formalizado |
| `CONSULTA_OPERADOR_SISTEMA` | `SOLICITUD_INFORME_OPERADOR` | está en el JSON pero sin poblar en BD (#450): al poblarlo, darle receptor con `ANALIZAR` |

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

| Trámite | Patrón | Tareas indicativas | Nota |
|---|---|---|---|
| `ANALISIS_DOCUMENTAL` | A | ANALIZAR | — |
| `REQUERIMIENTO_SUBSANACION` | C+A | ELABORAR → NOTIFICAR → ESPERAR_PLAZO → ANALIZAR | Se notifica al titular |
| `COMUNICACION_INICIO_ADMISION` | B | ELABORAR → NOTIFICAR | Renombrado desde `COMUNICACION_INICIO` (#776). Plazo máximo y silencio (art. 21.4 LPACAP) y, para Renovable, admisión a trámite (Hito 1 RD-ley 23/2020 art. 1.2, obligatoria); opcional para otros tipos. Se notifica al titular |

---

### DATOS_CATASTRALES
*Fase propia de la solicitud DUP (sin tasa) para mediar el acceso a datos catastrales de titularidad necesarios para redactar el RBDA. Obligatoria antes de INFORMACION_PUBLICA/CONSULTAS de esa solicitud (ADR-046 §F). Ver `DISEÑO_RESOLUCION_DUP.md` §2.*

| Trámite | Patrón | Tareas indicativas | Nota |
|---|---|---|---|
| `SOLICITUD_CATASTRALES` | A | ANALIZAR | Condicional: solo camino con mediación catastral |
| `REQUERIMIENTO_CATASTRALES` | C+A | ELABORAR → NOTIFICAR → EP → ANALIZAR | Condicional y repetible: solo si el diagnóstico previo es desfavorable. Se notifica al titular |
| `REMISION_ACUERDO_DATOS` | C | ELABORAR → NOTIFICAR → EP | Condicional: solo camino con mediación catastral. El acuerdo de cesión se notifica al titular (promotor). EP espera la RBDA remitida por el promotor |
| `ANALISIS_RBDA` | A | ANALIZAR | Siempre (con o sin mediación previa) |
| `TOMA_RAZON_RBDA` | B | ELABORAR → NOTIFICAR | Siempre. Cierra la fase, anuncia inicio de IP/consultas. Se notifica al titular |

**Dos caminos:** con mediación catastral (el promotor no tiene acceso directo al Catastro) corren los cinco trámites; sin mediación (p. ej. operadoras con acceso directo) se salta `SOLICITUD_CATASTRALES`/`REQUERIMIENTO_CATASTRALES`/`REMISION_ACUERDO_DATOS` y solo corren `ANALISIS_RBDA` → `TOMA_RAZON_RBDA`. Camino elegido libremente por el tramitador, sin regla de motor (candidato de regla futura, no implementado: bloquear `CREAR ANALISIS_RBDA` sin `RBDA`/`RBDA_DIRECCIONES` en el pool).

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

Destinatario del NOTIFICAR: en `CONSULTA_SEPARATA`, cada organismo por su canal correspondiente; en `CONSULTA_TRASLADO_TITULAR`, el titular.

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
| `RECEPCION_ALEGACION` | A+C | ANALIZAR → ELABORAR → NOTIFICAR → EP | ANALIZAR clasifica al alegante. El traslado de la alegación (NOTIFICAR) se dirige al titular |
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

| Trámite | Patrón | Tareas indicativas | Nota |
|---|---|---|---|
| `ELABORACION` | B (sin NOTIFICAR) | ELABORAR | — |
| `NOTIFICACION` | B (solo NOTIFICAR) | NOTIFICAR | Se notifica al solicitante que pidió el reconocimiento de interesado |

---

### RESOLUCION
*Resolución finalizadora de la solicitud.*

| Trámite | Patrón | Tareas indicativas | Nota |
|---|---|---|---|
| `ELABORACION` | B (sin NOTIFICAR) | ELABORAR (consume CERT_FIN_INSTRUCCION — #373) | — |
| `NOTIFICACION` | B (solo NOTIFICAR) | NOTIFICAR | Se notifica al titular u otro interesado, según la solicitud |
| `PUBLICACION` | C | ELABORAR → NOTIFICAR → ESPERAR_PLAZO | — |

---

### RESOLUCION_DUP
*Resolución finalizadora del acto de declaración de utilidad pública (DUP), separado del acto de autorización (ADR-046). Sustituye a `RESOLUCION` en la solicitud DUP sola; convive como fase hermana en `AAC+DUP`, `AAP+AAC+DUP` y `AAP+DUP` (en esta última la fase existe desde el alta, con la emisión diferida — ver `ESTRUCTURA_ESF.md`). Ver `DISEÑO_RESOLUCION_DUP.md` §1.*

| Trámite | Patrón | Tareas indicativas | Destinatario / nota |
|---|---|---|---|
| `REQUERIMIENTO_RBDA_DEFINITIVA` | C | ELABORAR → NOTIFICAR → EP | Obligatorio y exclusivo de esta fase, previo a `ELABORACION`. Plazo 10 días (genérico LPACAP). Requiere RBDA definitiva (solo parcelas a expropiar, propietarios, DNI, direcciones) o confirmación de la ya publicada |
| `ELABORACION` | B (sin NOTIFICAR) | ELABORAR | Consume `RBDA_DEFINITIVA`. Mismo código de trámite que `RESOLUCION.ELABORACION` — colisión resuelta vía `nombres_documentos.py:_SUSTITUCIONES` |
| `NOTIFICACION` | B (solo NOTIFICAR) | NOTIFICAR | Titular (promotor), que es quien solicitó la DUP |
| `NOTIFICACION_ORGANISMOS` | B (solo NOTIFICAR) | NOTIFICAR | `interesados_expediente.tipo_origen IN ('ORGANISMO_CONSULTADO', 'MEDIO_AMBIENTE')` |
| `NOTIFICACION_INTERESADOS` | B (solo NOTIFICAR) | NOTIFICAR | `interesados_expediente.tipo_origen IN ('DUP', 'INTERESADO_RECONOCIDO')` |
| `PUBLICACION_BOP` | F+F | NOTIFICAR → EP → EP | Una instancia por provincia afectada |
| `PUBLICACION_BOJA` | F+F | NOTIFICAR → EP → EP | Instrucción 1/2016 DG Industria, DÉCIMO |
| `PUBLICACION_BOE` | F+F | NOTIFICAR → EP → EP | Art. 148.2 RD 1955/2000 (rango superior a la Instrucción 1/2016, que no lo cita para la resolución) |

**`REQUERIMIENTO_RBDA_DEFINITIVA`, previo a `ELABORACION`:** su `ESPERAR_PLAZO` recibe directamente `RBDA_DEFINITIVA` (aportada por el promotor, o su confirmación de la ya publicada) sin anexos que incorporar — no exige `ANALIZAR` posterior (mismo caso que `TABLON_AYUNTAMIENTOS` en `INFORMACION_PUBLICA`). Produce el documento que consume `ELABORACION.ELABORAR` para redactar la resolución con los datos de expropiación definitivos.

**Notificaciones y publicaciones, un trámite por grupo/boletín** (no genéricos): art. 148.2 RD 1955/2000 distingue tres grupos de destinatarios además del solicitante; `NOTIFICACION_ORGANISMOS`/`NOTIFICACION_INTERESADOS` activan una vista de sub-lista en el inspector vía `_TRAMITES_CON_NOTIFICACION_MULTIPLE` (mismo mecanismo que `_TRAMITES_CON_SECCIONES_ANALISIS`). Las publicaciones siguen el patrón ya usado por `ANUNCIO_BOE`/`ANUNCIO_BOP`/`ANUNCIO_BOJA` de `INFORMACION_PUBLICA` en vez de un `PUBLICACION` único — aquí sin `ELABORAR` propio, porque el documento ya se elaboró en `ELABORACION`.

**Bloqueos de motor:** duplicado quirúrgico de los 5 de `RESOLUCION` (sujeto `ANY/ANY/RESOLUCION_DUP`) — `organismos_todos_terminados`, `fase_ip_finalizada`, `tramite_requerimiento_sin_respuesta`, `instrumento_ambiental=AAU`, `solicitud_tiene_cert_fin_instruccion`. Más la regla de orden de #891 (no resolver DUP sin AAC previa aprobada en `AAP+DUP`), anclada en `ELABORACION.ELABORAR` (ADR-046 §E). No se hereda de `RESOLUCION` — se duplica deliberadamente (decisión ADR-046 §E, alternativa de herencia descartada).

**Plazo:** propio, 6 meses (art. 148.1 RD 1955/2000) — converge con #892, no fijado en esta alta.

---

### RESOLUCION_AAP
*Resolución finalizadora del acto de AAP cuando `AAP+AAC`(`+DUP`) se resuelve partida en vez de conjunta (ADR-047 §A). `RESOLUCION` conserva su código y significado para el acto conjunto; `RESOLUCION_AAP`/`RESOLUCION_AAC` son la alternativa, elección del técnico, mutuamente excluyente con `RESOLUCION` (ver `ESTRUCTURA_ESF.md`).*

| Trámite | Patrón | Tareas indicativas | Nota |
|---|---|---|---|
| `ELABORACION` | B (sin NOTIFICAR) | ELABORAR (consume CERT_FIN_INSTRUCCION de la solicitud) | — |
| `NOTIFICACION` | B (solo NOTIFICAR) | NOTIFICAR | Se notifica al titular u otro interesado, según la solicitud |
| `PUBLICACION` | C | ELABORAR → NOTIFICAR → ESPERAR_PLAZO | — |

Mismo código de trámite `ELABORACION` que `RESOLUCION` — colisión de nombre de fichero resuelta vía `nombres_documentos.py:_SUSTITUCIONES` (#918). **Bloqueos de motor:** duplicado quirúrgico de los 5 de `RESOLUCION` (sujeto `ANY/ANY/RESOLUCION_AAP`), más exclusión mutua con `RESOLUCION` al `CREAR` la fase (condición `existe_resolucion_conjunta`, ADR-047 §B). Publica (art. 128.3 RD 1955/2000) igual que `RESOLUCION`, a diferencia de `RESOLUCION_AAC`.

---

### RESOLUCION_AAC
*Resolución finalizadora del acto de AAC cuando `AAP+AAC`(`+DUP`) se resuelve partida en vez de conjunta (ADR-047 §A). Solo elaborable con `RESOLUCION_AAP` de la misma solicitud finalizada favorable (ADR-047 §F).*

| Trámite | Patrón | Tareas indicativas | Nota |
|---|---|---|---|
| `ELABORACION` | B (sin NOTIFICAR) | ELABORAR (consume CERT_FIN_INSTRUCCION de la solicitud) | — |
| `NOTIFICACION` | B (solo NOTIFICAR) | NOTIFICAR | Sin PUBLICACION: el art. 131.8 RD 1955/2000 solo exige notificar (#918). Se notifica al titular u otro interesado, según la solicitud |

Sin `PUBLICACION`: a diferencia de `RESOLUCION_AAP`, el art. 131.8 RD 1955/2000 solo exige notificar, no publicar (#918). Mismo código de trámite `ELABORACION` que `RESOLUCION` — colisión resuelta vía `nombres_documentos.py:_SUSTITUCIONES`. **Bloqueos de motor:** duplicado quirúrgico de los 5 de `RESOLUCION` (sujeto `ANY/ANY/RESOLUCION_AAC`); exclusión mutua con `RESOLUCION` al `CREAR` la fase (condición `existe_resolucion_conjunta`). Más la **regla de orden AAP→AAC** (ADR-047 §F, RD 1955/2000 arts. 128.4/130.1/131.1 párr. 2): `RESOLUCION_AAP` de la misma solicitud debe constar finalizada favorable. Por límite del motor —no compila sujeto a nivel de tarea—, la regla ancla en `CREAR` el trámite `ELABORACION` (sujeto `ANY/RESOLUCION_AAC/ELABORACION`), **no** en la tarea `ELABORAR` como el resto de reglas de orden de este documento.
