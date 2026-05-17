# Tabla Inversa de Tareas Atómicas — ESFTT

> Fuente de verdad: `ESTRUCTURA_FTT.json`
> Última sincronización: 2026-05-17

**Propósito de este documento:**

El JSON de referencia está orientado jerárquicamente: Fase → Trámite → Tareas indicativas.
Eso es útil para diseñar flujos, pero dificulta responder preguntas como:

- Si cambio la definición de `ANALIZAR`, ¿qué trámites se ven afectados?
- ¿Qué tareas producen documentos que luego consumen otras tareas, y en qué fases ocurre eso?

Este documento invierte esa jerarquía. **La tarea es el nudo primario.**

---

## Resumen de presencia

| Tarea | Nº trámites | Patrón dominante |
|---|---|---|
| ELABORAR | 21 | B, C, C+A, A+C, A+B, C+F |
| NOTIFICAR | 21 | B, C, C+A, A+C, F+F |
| ESPERAR_PLAZO | 19 | C, C+A, A+C, F+F |
| ANALIZAR | 14 | A, C+A, A+C, A+B |

> **Cambios v6.0 (ADR-003/004/005, #371):**
> `REDACTAR` y `FIRMAR` → fusionados en `ELABORAR` (ADR-003).
> `INCORPORAR` → eliminado; recepción externa pasa a `ESPERAR_PLAZO.documento_producido_id` (ADR-004).
> `PUBLICAR` → eliminado; trámites que lo usaban pasan a patrón C (ELABORAR → NOTIFICAR → ESPERAR_PLAZO).

---

## ANALIZAR

**Semántica:** Revisión técnica o jurídica con generación obligatoria de documento formal.
`documento_usado_id` obligatorio (el documento analizado), `documento_producido_id` obligatorio (tipo DIAGNOSTICO, ADR-005).

| Fase | Trámite | Patrón | Qué analiza | Qué produce |
|---|---|---|---|---|
| ANALISIS_SOLICITUD | ANALISIS_DOCUMENTAL | A | Documentación del pool (cualifica tipos, contrasta checklist) | Informe de resultado (admisible / con defectos) |
| ANALISIS_SOLICITUD | REQUERIMIENTO_SUBSANACION | C+A | Documentación de subsanación (`ESPERAR_PLAZO.documento_producido`) | Informe de evaluación de subsanación |
| CONSULTA_MINISTERIO | RECEPCION_INFORME | A | Informe del Ministerio (`ESPERAR_PLAZO.documento_producido`) | Nota/informe de análisis |
| COMPATIBILIDAD_AMBIENTAL | COMUNICACION_AUDIENCIA | A | Escrito de MA comunicando apertura de audiencia al interesado (IC 1/2022, IV.3.3) | Registro informativo — sin documento producido formal |
| COMPATIBILIDAD_AMBIENTAL | RECEPCION_INFORME | A | Informe vinculante MA (`ESPERAR_PLAZO.documento_producido`) | Nota de análisis |
| CONSULTAS | CONSULTA_SEPARATA | C+A | Respuesta del organismo (`ESPERAR_PLAZO.documento_producido`) | Nota de análisis con resultado |
| CONSULTAS | CONSULTA_TRASLADO_TITULAR | C+A | Respuesta del titular (`ESPERAR_PLAZO.documento_producido`) | Nota de análisis con resultado |
| CONSULTAS | CONSULTA_TRASLADO_ORGANISMO | C+A | Respuesta final del organismo (`ESPERAR_PLAZO.documento_producido`) | Nota de análisis con resultado |
| INFORMACION_PUBLICA | RECEPCION_ALEGACION | A+C | Alegación individual (`ESPERAR_PLAZO.documento_producido`) | Clasifica alegante/interesado |
| INFORMACION_PUBLICA | ANALISIS_ALEGACIONES | A | Conjunto de alegaciones recibidas | Informe técnico-jurídico de alegaciones |
| FIGURA_AMBIENTAL_EXTERNA | RECEPCION_FIGURA | A | Resolución ambiental (`ESPERAR_PLAZO.documento_producido`) | Nota: puede paralizar expediente |
| AAU_AAUS_INTEGRADA | RECEPCION_DICTAMEN | A+C | Dictamen MA integrado (`ESPERAR_PLAZO.documento_producido`) | Nota: puede condicionar autorización |
| AAU_AAUS_INTEGRADA | RECEPCION_PROPUESTA_INF_VINC | A+C | Propuesta de informe vinculante de MA | Respuesta a la propuesta |
| RESOLUCION | ELABORACION | A+B | Conjunto de informes y trámites previos | Base para elaborar resolución |

---

## ELABORAR

**Semántica:** Redacción y firma de documento administrativo en acto único (ADR-003).
Produce documento con validez jurídica inmediata. El borrador es estado interno de la tarea, no se registra en el pool.
`documento_usado_id` opcional (DIAGNOSTICO de ANALIZAR previo si existe). `documento_producido_id` obligatorio.

| Fase | Trámite | Patrón | Qué elabora |
|---|---|---|---|
| ANALISIS_SOLICITUD | REQUERIMIENTO_SUBSANACION | C+A | Requerimiento de subsanación de defectos |
| ANALISIS_SOLICITUD | COMUNICACION_INICIO | B | Acuse de recibo con número de expediente |
| CONSULTA_MINISTERIO | SOLICITUD_INFORME | C | Solicitud de informe preceptivo al Ministerio |
| COMPATIBILIDAD_AMBIENTAL | SOLICITUD_COMPATIBILIDAD | C | Solicitud de compatibilidad ambiental a MA |
| CONSULTAS | CONSULTA_SEPARATA | C+A | Separata al organismo afectado |
| CONSULTAS | CONSULTA_TRASLADO_TITULAR | C+A | Traslado al titular de la respuesta del organismo |
| CONSULTAS | CONSULTA_TRASLADO_ORGANISMO | C+A | Traslado al organismo de los reparos del titular |
| INFORMACION_PUBLICA | REDACTAR_ANUNCIO | solo ELABORAR | Anuncio de información pública (produce ANUNCIO_IP) |
| INFORMACION_PUBLICA | PORTAL_TRANSPARENCIA | C | Anuncio para portal institucional |
| INFORMACION_PUBLICA | RECEPCION_ALEGACION | A+C | Traslado de alegación al titular |
| INFORMACION_PUBLICA | ANUNCIO_TITULAR | B | Comunicación al titular de la publicación del anuncio IP |
| INFORMACION_PUBLICA | ANUNCIO_BOP | C+F | Oficio de remisión de anuncio al BOP (produce OFICIO_PUBLICAR_BOLETIN) |
| INFORMACION_PUBLICA | TABLON_AYUNTAMIENTOS | C | Oficio de solicitud de exposición en tablón (produce OFICIO_TABLON) |
| FIGURA_AMBIENTAL_EXTERNA | SOLICITUD_FIGURA | C | Solicitud de instrumento ambiental |
| AAU_AAUS_INTEGRADA | REMISION_RESULTADO_IP_CONSULTAS | C | Traslado a MA del resultado de IP y consultas |
| AAU_AAUS_INTEGRADA | RECEPCION_DICTAMEN | A+C | Propuesta de resolución sustantiva tras dictamen MA |
| AAU_AAUS_INTEGRADA | RECEPCION_PROPUESTA_INF_VINC | A+C | Respuesta a propuesta de informe vinculante |
| AAU_AAUS_INTEGRADA | DISCREPANCIA_INF_VINC | C | Escrito de discrepancia al órgano superior |
| RESOLUCION | ELABORACION | A+B | Resolución definitiva |
| RESOLUCION | PUBLICACION | C | Anuncio de publicación de resolución |

---

## NOTIFICAR

**Semántica:** Comunicación a destinatario identificado con justificante de notificación.
`documento_usado_id` obligatorio (documento producido por ELABORAR). `documento_producido_id` obligatorio (justificante: acuse, certificado postal, etc.).
El justificante proviene de Notifica o sistema corporativo externo.

| Fase | Trámite | Patrón | Destinatario | Justificante producido |
|---|---|---|---|---|
| ANALISIS_SOLICITUD | REQUERIMIENTO_SUBSANACION | C+A | Titular | Acuse requerimiento subsanación |
| ANALISIS_SOLICITUD | COMUNICACION_INICIO | B | Titular/Solicitante | Acuse de recibo |
| CONSULTA_MINISTERIO | SOLICITUD_INFORME | C | Ministerio | Acuse solicitud informe |
| COMPATIBILIDAD_AMBIENTAL | SOLICITUD_COMPATIBILIDAD | C | Medio Ambiente | Acuse solicitud compatibilidad |
| CONSULTAS | CONSULTA_SEPARATA | C+A | Organismo afectado | Acuse por organismo |
| CONSULTAS | CONSULTA_TRASLADO_TITULAR | C+A | Titular | Acuse traslado al titular |
| CONSULTAS | CONSULTA_TRASLADO_ORGANISMO | C+A | Organismo | Acuse traslado al organismo |
| INFORMACION_PUBLICA | ANUNCIO_BOP | C+F | BOP | Acuse remisión OFICIO_PUBLICAR_BOLETIN + ANUNCIO_IP |
| INFORMACION_PUBLICA | ANUNCIO_BOJA | F+F | BOJA (vía SIBOJA) | Acuse de carga en plataforma SIBOJA |
| INFORMACION_PUBLICA | TABLON_AYUNTAMIENTOS | C | Ayuntamientos afectados | Acuse envío a ayuntamientos |
| INFORMACION_PUBLICA | PORTAL_TRANSPARENCIA | C | Portal institucional | Acuse publicación portal |
| INFORMACION_PUBLICA | RECEPCION_ALEGACION | A+C | Titular (traslado alegación) | Acuse traslado |
| INFORMACION_PUBLICA | ANUNCIO_TITULAR | B | Titular | Acuse notificación IP al titular |
| FIGURA_AMBIENTAL_EXTERNA | SOLICITUD_FIGURA | C | Órgano ambiental | Acuse solicitud instrumento |
| AAU_AAUS_INTEGRADA | REMISION_RESULTADO_IP_CONSULTAS | C | Medio Ambiente | Acuse remisión |
| AAU_AAUS_INTEGRADA | RECEPCION_DICTAMEN | A+C | Medio Ambiente (respuesta a dictamen) | Acuse respuesta |
| AAU_AAUS_INTEGRADA | RECEPCION_PROPUESTA_INF_VINC | A+C | Medio Ambiente | Acuse respuesta propuesta |
| AAU_AAUS_INTEGRADA | DISCREPANCIA_INF_VINC | C | Órgano superior | Acuse discrepancia |
| RESOLUCION | NOTIFICACION | B (solo NOTIFICAR) | Interesados | Justificante notificación resolución |
| RESOLUCION | PUBLICACION | C | Medios oficiales | Acuse publicación resolución |

---

## ESPERAR_PLAZO

**Semántica:** Suspensión temporal con fecha límite (`PLAZO_DIAS=0`: indefinida hasta evento externo).
`documento_usado_id` obligatorio si plazo > 0 (justificante de NOTIFICAR que inicia el cómputo); NULL si plazo = 0.
`documento_producido_id`: el documento externo recibido al vencer la espera (ADR-004); NULL si vence sin respuesta.

| Fase | Trámite | Patrón | Tipo de espera | `documento_producido` al vencer |
|---|---|---|---|---|
| ANALISIS_SOLICITUD | REQUERIMIENTO_SUBSANACION | C+A | Plazo de subsanación | Documentación subsanada del titular |
| CONSULTA_MINISTERIO | SOLICITUD_INFORME | C | Indefinida (plazo=0) hasta informe | Informe del Ministerio |
| COMPATIBILIDAD_AMBIENTAL | SOLICITUD_COMPATIBILIDAD | C | Indefinida (plazo=0) hasta compatibilidad | Informe de compatibilidad MA |
| CONSULTAS | CONSULTA_SEPARATA | C+A | Plazo de respuesta del organismo | Informe del organismo (o NULL: conformidad tácita) |
| CONSULTAS | CONSULTA_TRASLADO_TITULAR | C+A | Plazo respuesta del titular | Respuesta del titular (o NULL: aceptación tácita) |
| CONSULTAS | CONSULTA_TRASLADO_ORGANISMO | C+A | Plazo respuesta final del organismo | Respuesta final (o NULL: conformidad tácita) |
| INFORMACION_PUBLICA | ANUNCIO_BOE | F+F | ×1: indefinida hasta que promotor aporte JUSTIFICANTE_BOE | JUSTIFICANTE_BOE (aportado por el promotor) |
| INFORMACION_PUBLICA | ANUNCIO_BOE | F+F | ×2: transcurso del plazo de IP | NULL |
| INFORMACION_PUBLICA | ANUNCIO_BOP | C+F | ×1: hasta publicación efectiva | ANUNCIO_PUBLICADO (la administración lo obtiene de la plataforma BOP e introduce manualmente) |
| INFORMACION_PUBLICA | ANUNCIO_BOP | C+F | ×2: transcurso del plazo de IP | NULL |
| INFORMACION_PUBLICA | ANUNCIO_PRENSA | F+F | ×1: indefinida hasta que el titular aporte JUSTIFICANTE_PRENSA | JUSTIFICANTE_PRENSA (siempre del titular, que conoce cuándo y dónde publicó) |
| INFORMACION_PUBLICA | ANUNCIO_PRENSA | F+F | ×2: transcurso del plazo de IP — puede consumirse de inmediato | NULL |
| INFORMACION_PUBLICA | ANUNCIO_BOJA | F+F | ×1: hasta publicación efectiva | ANUNCIO_PUBLICADO (la administración lo obtiene de la plataforma BOJA e introduce manualmente) |
| INFORMACION_PUBLICA | ANUNCIO_BOJA | F+F | ×2: transcurso del plazo de IP | NULL |
| INFORMACION_PUBLICA | TABLON_AYUNTAMIENTOS | C | Hasta recibir certificado del ayuntamiento | CERT_PLAZO_TABLON (emitido por el ayuntamiento) |
| INFORMACION_PUBLICA | PORTAL_TRANSPARENCIA | C | Plazo de alegaciones | NULL (vence sin documento esperado) |
| FIGURA_AMBIENTAL_EXTERNA | SOLICITUD_FIGURA | C | Indefinida (plazo=0) hasta resolución ambiental | Resolución AAU/AAUS/CA |
| AAU_AAUS_INTEGRADA | REMISION_RESULTADO_IP_CONSULTAS | C | Indefinida (plazo=0) hasta dictamen MA | Dictamen ambiental integrado (MA) |
| AAU_AAUS_INTEGRADA | RECEPCION_DICTAMEN | A+C | Indefinida (plazo=0) hasta propuesta inf. vinculante | Propuesta de informe vinculante |
| AAU_AAUS_INTEGRADA | RECEPCION_PROPUESTA_INF_VINC | A+C | Indefinida (plazo=0) hasta inf. vinculante | Informe vinculante definitivo |
| AAU_AAUS_INTEGRADA | DISCREPANCIA_INF_VINC | C | Indefinida hasta resolución discrepancia | Resolución de discrepancia |
| RESOLUCION | PUBLICACION | C | Plazo de publicación oficial | Justificante de publicación de resolución |

> **Nota normativa pendiente:** el caso `AAU_AAUS_INTEGRADA / REMISION_RESULTADO_IP_CONSULTAS` puede requerir `plazo=0` porque Medio Ambiente no tiene plazo legalmente definido. Pendiente confirmar apartado normativo. (#296 pregunta abierta 2).

---

## Observaciones de desalineación detectadas

### 1. `fecha_administrativa` en documentos producidos internamente

`fecha_administrativa` en `Documento` es la única fuente de verdad para la fecha del acto jurídico (ver `DISEÑO_FECHAS_PLAZOS.md §2.bis`):
- Documentos de `ELABORAR`: `documento_producido.fecha_administrativa` porta la fecha del acto de firma.
- Documentos de `NOTIFICAR`: `documento_producido.fecha_administrativa` porta la fecha de notificación.
- Documentos de `ESPERAR_PLAZO` (receptor externo): `fecha_administrativa` es la fecha de registro del documento recibido.
- Documentos de `ANALIZAR`: sin fecha administrativa (`fecha_administrativa = NULL` por diseño — informe interno sin efectos jurídicos directos).

### 2. NOTIFICAR produce justificante externo — analogía con ESPERAR_PLAZO receptor

El justificante que produce NOTIFICAR viene de Notifica/bandeja (sistema corporativo externo).
El documento recibido que registra ESPERAR_PLAZO también viene de un sistema externo.
La distinción es que NOTIFICAR los encadena con el documento elaborado previo.
Esto es relevante para definir `tipo_doc_id` en los justificantes.

### 3. Señal de resultado en NOTIFICAR — resultado INCORRECTA (#296)

Solo `NOTIFICAR` puede producir un documento con `efecto_tarea = INCORRECTA` (notificación caducada o fallida).
El resultado se registra en `resultados_documentos` vinculado al `documento_producido_id`.
Sin fila → resultado `INDIFERENTE` (valor por defecto).

Cuando una tarea NOTIFICAR tiene resultado INCORRECTA:
- `Tramite.finalizado` devuelve `False` aunque el `documento_producido_id` esté presente.
- Los invariantes `_check_finalizar_tramite` y `_check_finalizar_fase` bloquean el cierre.
- El técnico debe subsanar la notificación (nueva tarea NOTIFICAR) antes de poder cerrar.
