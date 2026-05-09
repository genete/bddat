# Catálogo de tipos de documentos — ESFTT

> Documento de trabajo para el issue #337.
> Recoge los tipos de documento que producen o incorporan las tareas atómicas del flujo ESFTT,
> cruzando LPACAP, RD 1955/2000 y normativa sectorial AT.

---

## Tabla de tipos candidatos

| codigo | nombre | origen | tarea / trámite | norma de referencia | notas |
|--------|--------|--------|-----------------|---------------------|-------|
| `JUSTIFICANTE_NOTIFICA` | Justificante Notifica-PNT | EXTERNO | NOTIFICAR (producido) | LPACAP art. 43 | PDF parseable; helper extrae fecha_administrativa al incorporar al pool |
| `JUSTIFICANTE_BANDEJA` | Justificante BandeJA | EXTERNO | NOTIFICAR (producido) | | PDF parseable; fecha = transmisión electrónica (instantánea); helper la extrae |
| `JUSTIFICANTE_SIR` | Justificante SIR / ARIES | EXTERNO | NOTIFICAR (producido) | | No parseable (captura pantalla); fecha_administrativa manual |
| `JUSTIFICANTE_POSTAL` | Justificante notificación postal | EXTERNO | NOTIFICAR (producido) | | Parseabilidad por determinar; fecha_administrativa manual |
| `JUSTIFICANTE_BOE` | Justificante publicación BOE | EXTERNO | PUBLICAR (producido) | | |
| `JUSTIFICANTE_BOP` | Justificante publicación BOP | EXTERNO | PUBLICAR (producido) | | |
| `JUSTIFICANTE_BOJA` | Justificante publicación BOJA | EXTERNO | PUBLICAR (producido) | | |
| `JUSTIFICANTE_PRENSA` | Justificante publicación prensa | EXTERNO | PUBLICAR (producido) | | Diario de mayor difusión |
| `JUSTIFICANTE_TABLON` | Certificado de exposición en tablón | EXTERNO | PUBLICAR (producido) | | Llega siempre a plazo vencido; fija la fecha de inicio de exposición |
| `JUSTIFICANTE_PORTAL` | URL de acto de exposición en portal de transparencia | EXTERNO | PUBLICAR (producido) | | Generado por DRUPAL; URL fija y persistente; indica vigencia del plazo |
| `CERT_PLAZO_CUMPLIDO` | Certificado de plazo cumplido | INTERNO | ESPERAR_PLAZO (producido) | LPACAP art. 22 | Generado por BDDAT cuando vence el plazo sin recibir documento. Incluye: documento que inició la espera, contexto ESFTT (fase/trámite/tarea), normativa y duración del plazo, cómputo de transcurso, constancia de ausencia de documento recibido. fecha_administrativa = fecha de vencimiento (hecho objetivo), independiente de cuándo lo firme el técnico. Ver #362 |
| `DIAGNOSTICO` | Diagnóstico de análisis | INTERNO | ANALIZAR (producido) | | Decisión estructurada persistida en BD. url = bddat://diagnosticos/{id}. fecha_administrativa = NULL por diseño (sin efecto jurídico propio). Consumible por ELABORAR como documento_usado_id opcional. Ver #365 |
| `OFICIO_REQUERIMIENTO` | Oficio de requerimiento de subsanación | INTERNO | REQUERIMIENTO_SUBSANACION.ELABORAR (producido) | | fecha_administrativa = fecha de firma. Lleva stamp ESFTT invisible. Norma: pendiente |
| `SUBSANACION` | Documentación de subsanación del titular | EXTERNO | REQUERIMIENTO_SUBSANACION.ESPERAR_PLAZO (consumido por ANALIZAR) | | Aportada por el administrado en respuesta al requerimiento. PDF legible; canal variable sin interés clasificatorio |
| `OFICIO_INICIO` | Oficio de comunicación de inicio de expediente | INTERNO | COMUNICACION_INICIO.ELABORAR (producido) | | fecha_administrativa = fecha de firma. Lleva stamp ESFTT invisible. Norma: pendiente. No incompatible con REQUERIMIENTO_SUBSANACION posterior |
| `OFICIO_114_RD1955` | Oficio de solicitud de informe preceptivo al Ministerio (art. 114 RD 1955/2000) | INTERNO | SOLICITUD_INFORME.ELABORAR (producido) | RD 1955/2000 art. 114 | fecha_administrativa = fecha de firma. Lleva stamp ESFTT invisible |
| `INFORME_114_RD1955` | Informe preceptivo del Ministerio (art. 114 RD 1955/2000) | EXTERNO | RECEPCION_INFORME.ESPERAR_PLAZO (consumido por ANALIZAR) | RD 1955/2000 art. 114 | |
| `DOC_SOLICITUD_AAU` | Solicitud de autorización ambiental unificada (modelo oficial) | EXTERNO | SOLICITUD_COMPATIBILIDAD (consumido) | Decreto 356/2010, de 3 de agosto (Anexo II); Instrucción Conjunta 1/2022 SGE/DGSAyCC (Anexo I, apt. 1) | Aportado por el administrado usando el modelo oficial. fecha_administrativa = fecha de registro. Debe incluir justificante de pago de tasa AAU |
| `OFICIO_COMPATIBILIDAD_AMBIENTAL` | Oficio de remisión de solicitud de compatibilidad ambiental (AAU/AAUS) | INTERNO | SOLICITUD_COMPATIBILIDAD.ELABORAR (producido) | | fecha_administrativa = fecha de firma. Lleva stamp ESFTT invisible. Norma: pendiente |
| `INFORME_COMPATIBILIDAD_AMBIENTAL` | Informe de compatibilidad ambiental del órgano ambiental | EXTERNO | RECEPCION_INFORME.ESPERAR_PLAZO (consumido por ANALIZAR) | | El sentido (compatible/incompatible) lo evalúa el técnico, no el tipo |
| `DOC_SEPARATA` | Separata del proyecto aportada por el solicitante | EXTERNO | CONSULTA_SEPARATA.ELABORAR (consumido) | | Sin calificación adicional; también consumido por NOTIFICAR junto a OFICIO_SEPARATA (primer caso N:M en consumo — ver #361) |
| `OFICIO_SEPARATA` | Oficio de consulta a organismo sectorial | INTERNO | CONSULTA_SEPARATA.ELABORAR (producido) | RD 1955/2000 arts. 127/131 | fecha_administrativa = fecha de firma. Lleva stamp ESFTT invisible |
| `RESPUESTA_ORGANISMO` | Respuesta del organismo sectorial a la consulta | EXTERNO | CONSULTA_SEPARATA.ESPERAR_PLAZO (producido — Caso A) | RD 1955/2000 arts. 127/131 | Cubre conformidad, oposición, reparos y condicionado. La calificación vive en organismos_expediente, no en el tipo |
| `OFICIO_TRASLADO_RESPUESTA` | Oficio de traslado de respuesta del organismo al titular | INTERNO | CONSULTA_TRASLADO_TITULAR.ELABORAR (producido) | RD 1955/2000 arts. 127.3/131.3 | fecha_administrativa = fecha de firma. Lleva stamp ESFTT invisible. Notificar consume este oficio + RESPUESTA_ORGANISMO (N:M) |
| `RESPUESTA_TITULAR` | Respuesta del titular a los reparos del organismo | EXTERNO | CONSULTA_TRASLADO_TITULAR.ESPERAR_PLAZO (producido — Caso A) | RD 1955/2000 arts. 127.3/131.3 | La calificación del sentido vive en el DIAGNOSTICO de ANALIZAR y en organismos_expediente |

---

## Resultados válidos por tipo de notificación

> Para poblar `tipos_documentos_resultados_validos` (criterio: LPACAP arts. 40-46).

| tipo_doc (codigo) | resultado_valido | fundamento |
|-------------------|-----------------|------------|
| | | |

---

## Punto de retoma

> Última sesión: 2026-05-09
> Próximo trámite a catalogar: **CONSULTAS.CONSULTA_TRASLADO_ORGANISMO**
> Pendiente tras CONSULTAS: INFORMACION_PUBLICA (7 trámites), FIGURA_AMBIENTAL_EXTERNA, AAU_AAUS_INTEGRADA, RESOLUCION (3 trámites)
> Issues abiertos en esta sesión: #361 #362 #363 #364 #365 #366 #367

---

## Notas normativas

<!-- Ampliar aquí cuando un tipo requiera explicación que no cabe en la tabla -->
