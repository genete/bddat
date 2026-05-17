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
| `JUSTIFICANTE_BOE` | Justificante publicación BOE | EXTERNO | ANUNCIO_BOE.ESPERAR_PLAZO(1) (producido) | | Aportado por el promotor cuando publica en BOE |
| `JUSTIFICANTE_BOP` | Justificante publicación BOP | EXTERNO | ANUNCIO_BOP.ESPERAR_PLAZO(1) (producido) | | |
| `JUSTIFICANTE_BOJA` | Justificante publicación BOJA | EXTERNO | ANUNCIO_BOJA.ESPERAR_PLAZO(1) (producido) | | |
| `JUSTIFICANTE_PRENSA` | Justificante publicación prensa | EXTERNO | ANUNCIO_PRENSA.ESPERAR_PLAZO(1) (producido) | | Diario de mayor difusión; siempre aportado por el titular, que conoce cuándo y dónde publicó |
| `JUSTIFICANTE_TABLON` | Certificado de exposición en tablón | EXTERNO | TABLON_AYUNTAMIENTOS.ESPERAR_PLAZO (producido) | | Llega siempre a plazo vencido; fija la fecha de inicio de exposición |
| `JUSTIFICANTE_PORTAL` | URL de acto de exposición en portal de transparencia | EXTERNO | PORTAL_TRANSPARENCIA.ESPERAR_PLAZO (producido) | | URL única y permanente generada por DRUPAL; expone los documentos de IP publicados e indica si el período de IP está abierto o no |
| `CERT_PLAZO_CUMPLIDO` | Certificado de plazo cumplido | INTERNO | ESPERAR_PLAZO (producido) | LPACAP art. 22 | Generado por BDDAT cuando vence el plazo. Dos variantes: (A) espera de documento externo — constancia de ausencia de respuesta; (B) espera de transcurso de tiempo puro — el documento consumido es ANUNCIO_PUBLICADO, no se espera ningún documento externo, el certificado acredita el vencimiento del plazo de IP. Incluye en ambos casos: documento que inició la espera, contexto ESFTT, normativa y duración del plazo, cómputo de transcurso. fecha_administrativa = fecha de vencimiento (hecho objetivo). Ver #362 |
| `DIAGNOSTICO` | Diagnóstico de análisis | INTERNO | ANALIZAR (producido) | | Decisión estructurada persistida en BD. url = bddat://diagnosticos/{id}. fecha_administrativa = NULL por diseño (sin efecto jurídico propio). Consumible por ELABORAR como documento de entrada opcional (rol CONSUMIDO). Ver #365 |
| `OFICIO_REQUERIMIENTO` | Oficio de requerimiento de subsanación | INTERNO | REQUERIMIENTO_SUBSANACION.ELABORAR (producido) | | fecha_administrativa = fecha de firma. Lleva stamp ESFTT invisible. Norma: pendiente |
| `SUBSANACION` | Documentación de subsanación del titular | EXTERNO | REQUERIMIENTO_SUBSANACION.ESPERAR_PLAZO (consumido por ANALIZAR) | | Aportada por el administrado en respuesta al requerimiento. PDF legible; canal variable sin interés clasificatorio |
| `OFICIO_INICIO` | Oficio de comunicación de inicio de expediente | INTERNO | COMUNICACION_INICIO.ELABORAR (producido) | | fecha_administrativa = fecha de firma. Lleva stamp ESFTT invisible. Norma: pendiente. No incompatible con REQUERIMIENTO_SUBSANACION posterior |
| `OFICIO_114_RD1955` | Oficio de solicitud de informe preceptivo al Ministerio (art. 114 RD 1955/2000) | INTERNO | SOLICITUD_INFORME.ELABORAR (producido) | RD 1955/2000 art. 114 | fecha_administrativa = fecha de firma. Lleva stamp ESFTT invisible |
| `INFORME_114_RD1955` | Informe preceptivo del Ministerio (art. 114 RD 1955/2000) | EXTERNO | RECEPCION_INFORME.ESPERAR_PLAZO (consumido por ANALIZAR) | RD 1955/2000 art. 114 | |
| `DOC_SOLICITUD_AAU` | Solicitud de autorización ambiental unificada (modelo oficial) | EXTERNO | SOLICITUD_COMPATIBILIDAD (consumido) | Decreto 356/2010, de 3 de agosto (Anexo II); Instrucción Conjunta 1/2022 SGE/DGSAyCC (Anexo I, apt. 1) | Aportado por el administrado usando el modelo oficial. fecha_administrativa = fecha de registro. Debe incluir justificante de pago de tasa AAU |
| `OFICIO_COMPATIBILIDAD_AMBIENTAL` | Oficio de remisión de solicitud de compatibilidad ambiental (AAU/AAUS) | INTERNO | SOLICITUD_COMPATIBILIDAD.ELABORAR (producido) | | fecha_administrativa = fecha de firma. Lleva stamp ESFTT invisible. Norma: pendiente |
| `INFORME_COMPATIBILIDAD_AMBIENTAL` | Informe de compatibilidad ambiental del órgano ambiental | EXTERNO | RECEPCION_INFORME.ESPERAR_PLAZO (consumido por ANALIZAR) | | El sentido (compatible/incompatible) lo evalúa el técnico, no el tipo |
| `DOC_COMUNICACION_AUDIENCIA` | Escrito de comunicación de audiencia al interesado | EXTERNO | COMUNICACION_AUDIENCIA.ANALIZAR (consumido) | IC 1/2022, IV.3.3 | Emitido por el órgano ambiental simultáneamente con la apertura del trámite de audiencia a la persona interesada. Informa al órgano sustantivo de la posible incompatibilidad detectada. El sustantivo solo registra; no hay respuesta ni actuación. |
| `DOC_SEPARATA` | Separata del proyecto aportada por el solicitante | EXTERNO | CONSULTA_SEPARATA.ELABORAR (consumido) | | Sin calificación adicional; también consumido por NOTIFICAR junto a OFICIO_SEPARATA (primer caso N:M en consumo — ver #361) |
| `OFICIO_SEPARATA` | Oficio de consulta a organismo sectorial | INTERNO | CONSULTA_SEPARATA.ELABORAR (producido) | RD 1955/2000 arts. 127/131 | fecha_administrativa = fecha de firma. Lleva stamp ESFTT invisible |
| `RESPUESTA_ORGANISMO` | Respuesta del organismo sectorial a la consulta | EXTERNO | CONSULTA_SEPARATA.ESPERAR_PLAZO (producido — Caso A) | RD 1955/2000 arts. 127/131 | Cubre conformidad, oposición, reparos y condicionado. La calificación vive en organismos_expediente, no en el tipo |
| `OFICIO_TRASLADO_RESPUESTA` | Oficio de traslado de respuesta del organismo al titular | INTERNO | CONSULTA_TRASLADO_TITULAR.ELABORAR (producido) | RD 1955/2000 arts. 127.3/131.3 | fecha_administrativa = fecha de firma. Lleva stamp ESFTT invisible. Notificar consume este oficio + RESPUESTA_ORGANISMO (N:M) |
| `RESPUESTA_TITULAR` | Respuesta del titular a los reparos del organismo | EXTERNO | CONSULTA_TRASLADO_TITULAR.ESPERAR_PLAZO (producido — Caso A) | RD 1955/2000 arts. 127.3/131.3 | La calificación del sentido vive en el DIAGNOSTICO de ANALIZAR y en organismos_expediente |
| `OFICIO_TRASLADO_REPAROS` | Oficio de traslado de reparos del titular al organismo sectorial | INTERNO | CONSULTA_TRASLADO_ORGANISMO.ELABORAR (producido) | RD 1955/2000 arts. 127.3/131.3 | fecha_administrativa = fecha de firma. Lleva stamp ESFTT invisible. Notificar consume este oficio + RESPUESTA_TITULAR (N:M) |
| `DOC_PROYECTO` | Proyecto técnico del titular | EXTERNO | REDACTAR_ANUNCIO.ELABORAR (consumido) | | Proxy de entrada: aporta el contexto y características del proyecto necesarios para redactar el anuncio. Metadatos adicionales en tabla documentos_proyecto. REDACTAR_ANUNCIO es trámite nuevo pendiente de añadir al FTT (también falta ANUNCIO_BOJA) |
| `ANUNCIO_IP` | Anuncio de información pública | INTERNO | REDACTAR_ANUNCIO.ELABORAR (producido); consumido por ANUNCIO_TITULAR/BOP/BOJA.ELABORAR y NOTIFICAR (N:M) | | Parseable; firmado; stamp ESFTT invisible; fecha_administrativa = fecha de firma. Único para todos los trámites de publicación — no se genera uno por trámite. BOE y prensa gestionados íntegramente por el titular vía ANUNCIO_TITULAR |
| `OFICIO_PUBLICAR_TITULAR` | Oficio de publicación de anuncio al titular | INTERNO | ANUNCIO_TITULAR.ELABORAR (producido) | | Parseable; firmado; stamp ESFTT invisible; fecha_administrativa = fecha de firma. Indica al titular que remita copias de BOP, BOJA, BOE y prensa. NOTIFICAR consume este oficio + ANUNCIO_IP (N:M) |
| `OFICIO_PUBLICAR_BOLETIN` | Oficio de remisión de anuncio al boletín oficial | INTERNO | ANUNCIO_BOP.ELABORAR (producido) | | Parseable; firmado; stamp ESFTT invisible; fecha_administrativa = fecha de firma. Solo en BOP: ANUNCIO_BOJA usa la plataforma SIBOJA sin oficio previo. NOTIFICAR consume este oficio + ANUNCIO_IP (N:M) |
| `ANUNCIO_PUBLICADO` | Copia del anuncio publicado en boletín oficial | EXTERNO | ANUNCIO_BOP.ESPERAR_PLAZO(1) / ANUNCIO_BOJA.ESPERAR_PLAZO(1) (producido) | | La administración lo obtiene directamente de la plataforma publicadora (BOP/BOJA) e introduce manualmente como PDF — no requiere entrada registral del titular. Consumido por el segundo ESPERAR_PLAZO del mismo trámite (espera de transcurso de plazo) |
| `OFICIO_TABLON` | Oficio de solicitud de exposición en tablón de ayuntamiento | INTERNO | TABLON_AYUNTAMIENTOS.ELABORAR (producido) | | Firmado; stamp ESFTT invisible; fecha_administrativa = fecha de firma. La plantilla itera sobre los municipios del proyecto y genera un único docx multi-página; el usuario lo divide, firma cada página por separado y reutiliza en los trámites de los ayuntamientos restantes. NOTIFICAR consume este oficio + ANUNCIO_IP (N:M) |
| `CERT_PLAZO_TABLON` | Certificado de exposición en tablón de ayuntamiento | EXTERNO | TABLON_AYUNTAMIENTOS.ESPERAR_PLAZO (producido) | | Emitido por el ayuntamiento al transcurrir el plazo de exposición. Sustituye a CERT_PLAZO_CUMPLIDO en este trámite: el plazo lo acredita el organismo externo, no BDDAT. Un solo ESPERAR_PLAZO (sin ANUNCIO_PUBLICADO intermedio) |
| `ALEGACION_IP` | Alegación de información pública | EXTERNO | RECEPCION_ALEGACION.ANALIZAR (consumido); ANALISIS_ALEGACIONES.ANALIZAR (consumido — todas las del expediente) | | Aportada por el administrado durante el período de IP. Puede haber varias por expediente |
| `OFICIO_TRASLADO_ALEGACION` | Oficio de traslado de alegación al titular | INTERNO | RECEPCION_ALEGACION.ELABORAR (producido) | | Parseable; firmado; stamp ESFTT invisible; fecha_administrativa = fecha de firma. NOTIFICAR consume solo este oficio (sin N:M) |
| `RESPUESTA_TITULAR_ALEGACION` | Respuesta del titular a la alegación | EXTERNO | RECEPCION_ALEGACION.ESPERAR_PLAZO (producido); ANALISIS_ALEGACIONES.ANALIZAR (consumido — todas las del expediente) | | Una por alegación trasladada. El sentido de la respuesta lo evalúa ANALIZAR en ANALISIS_ALEGACIONES |
| `OFICIO_SOLICITUD_FIGURA` | Oficio de solicitud de figura ambiental externa | INTERNO | SOLICITUD_FIGURA.ELABORAR (producido) | Instrucción Conjunta 1/2022 | Parseable; firmado; stamp ESFTT invisible; fecha_administrativa = fecha de firma. Consumido: DOC_PROYECTO (proxy para verificar condición es_modificacion, no como fuente de contenido). ESPERAR_PLAZO indefinido: el promotor obtiene la figura por su cuenta con el órgano ambiental |
| `FIGURA_AMBIENTAL_EXTERNA` | Figura ambiental externa obtenida por el promotor | EXTERNO | SOLICITUD_FIGURA.ESPERAR_PLAZO (producido) | Instrucción Conjunta 1/2022 | Aportada por el promotor. Sin plazo definido (espera indefinida). Cubre cualquier figura ambiental aplicable a modificaciones de instalaciones ya autorizadas |
| `CERT_FIN_INSTRUCCION` | Certificado de fin de instrucción del expediente | INTERNO | RESOLUCION.ELABORACION (generado automáticamente por BDDAT al crear la fase) | LPACAP art. 82 | Generado por el motor de reglas cuando las fases requeridas para el tipo de expediente están cerradas con resultado. Recoge: tipo de expediente, solicitudes, fases completadas y sus resultados, fundamento jurídico que habilita la resolución. fecha_administrativa = fecha de generación (hecho objetivo). url = bddat://cert_fin_instruccion/{id}. Parseable; stamp ESFTT. No hay ANALIZAR en ELABORACION: el motor hace el análisis. Ver #373 |
| `RESOLUCION` | Resolución de autorización administrativa | INTERNO | RESOLUCION.ELABORACION.ELABORAR (producido) | RD 1955/2000 arts. 128 y 131 | Parseable; firmado; fecha_administrativa = fecha de firma (efecto jurídico propio). ELABORAR consume CERT_FIN_INSTRUCCION. NOTIFICACION consume esta resolución sin oficio adicional (el asunto del sistema de notificación es suficiente); múltiples instancias, una por interesado/organismo/titular. PUBLICACION la publica mediante trámites PUBLICAR_* |
| `RESOLUCION_PUBLICADA` | Resolución publicada en boletín oficial | EXTERNO | RESOLUCION.PUBLICACION.ESPERAR_PLAZO (producido) | | Una instancia por boletín (BOP, BOJA…); no aplica al titular. ELABORAR y NOTIFICAR de PUBLICACION reutilizan OFICIO_PUBLICAR_TITULAR y OFICIO_PUBLICAR_BOLETIN (misma plantilla con condicional, sin nombres nuevos). Sin segundo ESPERAR_PLAZO: la publicación de la resolución no abre plazo de alegaciones |
| `CERT_FIN_IP_CONSULTAS` | Certificado de fin de IP y consultas | INTERNO | REMISION_RESULTADO_IP_CONSULTAS.ELABORAR (consumido) | Instrucción Conjunta 1/2022, IV.4.5 | Generado automáticamente por el motor de reglas o a petición del usuario cuando las fases de IP y consultas han concluido con resultado. Acredita que la fase AAU_AAUS_INTEGRADA está habilitada. fecha_administrativa = fecha de finalización de la última fase habilitante. Firma opcional. Tipo de certificado pendiente de unificar con CERT_FIN_INSTRUCCION (ver #373) |
| `OFICIO_RESULTADO_IP_CON` | Oficio de remisión del resultado de IP y consultas al órgano ambiental | INTERNO | REMISION_RESULTADO_IP_CONSULTAS.ELABORAR (producido); consumido por NOTIFICAR del mismo trámite | Instrucción Conjunta 1/2022, IV.4.5 | Parseable; firmado; stamp ESFTT invisible. fecha_administrativa = fecha de firma. Comunica las contestaciones a consultas ambientales y alegaciones recibidas en una sola remisión |
| `DOC_DICTAMEN_AMBIENTAL` | Dictamen ambiental del órgano ambiental | EXTERNO | REMISION_RESULTADO_IP_CONSULTAS.ESPERAR_PLAZO (producido); consumido por RECEPCION_DICTAMEN.ANALIZAR | Instrucción Conjunta 1/2022, IV.5.1.1; Decreto 356/2010, art. 32.3 | Emitido por el órgano ambiental. Puede ser favorable, condicionado o desfavorable. La valoración y sus consecuencias viven en el DIAGNOSTICO de ANALIZAR |
| `OFICIO_OBS_DICTAMEN` | Oficio de observaciones al dictamen ambiental | INTERNO | RECEPCION_DICTAMEN.ELABORAR (producido); consumido por NOTIFICAR del mismo trámite | Instrucción Conjunta 1/2022, IV.5.1.1 | Parseable; firmado; stamp ESFTT invisible. fecha_administrativa = fecha de firma. Se emite siempre (incluso sin observaciones sustantivas) para activar el cómputo del plazo siguiente |
| `DOC_PROPUESTA_INF_VINC` | Propuesta de informe vinculante del órgano ambiental | EXTERNO | RECEPCION_DICTAMEN.ESPERAR_PLAZO (producido); consumido por RECEPCION_PROPUESTA_INF_VINC.ANALIZAR | Instrucción Conjunta 1/2022, IV.5.2; Decreto 356/2010, art. 32.4 | Emitido por el órgano ambiental tras la audiencia a interesados del procedimiento ambiental |
| `OFICIO_OBS_PROP_INF_VINC` | Oficio de observaciones a la propuesta de informe vinculante | INTERNO | RECEPCION_PROPUESTA_INF_VINC.ELABORAR (producido); consumido por NOTIFICAR del mismo trámite | Instrucción Conjunta 1/2022, IV.5.2 | Parseable; firmado; stamp ESFTT invisible. fecha_administrativa = fecha de firma. Se emite siempre |
| `DOC_INFORME_VINCULANTE` | Informe vinculante del órgano ambiental | EXTERNO | RECEPCION_PROPUESTA_INF_VINC.ESPERAR_PLAZO (producido); consumido por RECEPCION_INFORME_VINCULANTE.ANALIZAR | Instrucción Conjunta 1/2022, IV.5.3; Decreto 356/2010, arts. 32.5 y 33 | Incluye lista de interesados del procedimiento ambiental (ver #374). Sus condiciones se incorporan a la autorización |
| `OFICIO_DISCREPANCIA_INF_VINC` | Oficio de planteamiento de discrepancia sobre el informe vinculante | INTERNO | DISCREPANCIA_INF_VINC.ELABORAR (producido); consumido por NOTIFICAR del mismo trámite | Decreto 356/2010, art. 33 | Parseable; firmado; stamp ESFTT invisible. fecha_administrativa = fecha de firma. Condicional: solo si RECEPCION_INFORME_VINCULANTE.ANALIZAR diagnostica discrepancia |
| `RESOLUCION_DISCREPANCIA_INF_VINC` | Resolución del Consejo de Gobierno sobre discrepancia en informe vinculante | EXTERNO | DISCREPANCIA_INF_VINC.ESPERAR_PLAZO (producido) | Decreto 356/2010, art. 33 | Emitida por el Consejo de Gobierno. Vincula al órgano sustantivo. Sin segundo ESPERAR_PLAZO: la resolución cierra el trámite DISCREPANCIA_INF_VINC |

---

## Resultados válidos por tipo de notificación

> Para poblar `tipos_documentos_resultados_validos` (criterio: LPACAP arts. 40-46).

| tipo_doc (codigo) | resultado_valido | fundamento |
|-------------------|-----------------|------------|
| | | |

---

## Punto de retoma

> Última sesión: 2026-05-11
> Estado: catálogo COMPLETO — trabajo normativo de #337 terminado. Criterio 1 (tabla candidatos) cerrado.
> Fases cubiertas: todas — CONSULTAS, INFORMACION_PUBLICA, AAU_AAUS_INTEGRADA, FIGURA_AMBIENTAL_EXTERNA, RESOLUCION
> PORTAL_TRANSPARENCIA: sin tipos nuevos. Patrón NOTIFICAR+ESPERAR_PLAZO repetido según boletines — pendiente confirmar con jefatura (pares manuales vs certificado automático del sistema)
> Pendiente para cierre completo de #337: criterio 2 (migración Alembic), criterio 3 (poblar tipos_documentos_resultados_validos), criterio 4 (UI seleccionable)
> Issues abiertos relacionados: #361 #362 #363 #364 #365 #366 #367 #368 #369 #370 #371 #372 #373 #374

---

## Notas normativas

<!-- Ampliar aquí cuando un tipo requiera explicación que no cabe en la tabla -->

## Notas de diseño pendientes

**ANALISIS_ALEGACIONES → RESOLUCION:** el `DIAGNOSTICO` producido por `ANALISIS_ALEGACIONES.ANALIZAR` podría declararse como `documento_consumido` de `RESOLUCION.ELABORAR`, pero puede ser excesivo: al redactar la resolución el técnico tiene en cuenta todo el expediente, no solo ese diagnóstico. La alternativa más ligera es que la plantilla de resolución lo incorpore condicionalmente si existe, sin declararlo como dependencia formal del trámite. Pendiente de decidir al catalogar RESOLUCION.
