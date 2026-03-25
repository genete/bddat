# Tabla Inversa de Tareas Atómicas — ESFTT

> Fuente de verdad: `Estructura_fases_tramites_tareas.json`
> Última sincronización: 2026-03-05

**Propósito de este documento:**

El JSON de referencia está orientado jerárquicamente: Fase → Trámite → Tareas indicativas.
Eso es útil para diseñar flujos, pero dificulta responder preguntas como:

- ¿En cuántos trámites aparece `INCORPORAR`? ¿Con qué contextos distintos?
- Si cambio la definición de `ANALISIS`, ¿qué trámites se ven afectados?
- ¿Qué tareas producen documentos que luego consumen otras tareas, y en qué fases ocurre eso?

Este documento invierte esa jerarquía. **La tarea es el nudo primario.**

Sirve también como punto de partida para detectar desalineaciones entre la definición
original de las tareas atómicas (escrita antes del pool de documentos, `tipos_documentos`,
`fecha_administrativa` nullable, etc.) y la realidad actual del modelo.

---

## Resumen de presencia

| Tarea | Nº trámites (directa) | Nº trámites (opcional/condicional) | Patrón dominante |
|---|---|---|---|
| REDACTAR | 22 | — | B, C, AB, EC, D |
| FIRMAR | 21 | 1 (RESOLUCION.NOTIFICACION) | B, C, AB, EC, D |
| NOTIFICAR | 19 | — | B, C, AB, EC |
| ESPERAR_PLAZO | 15 | — | C, AC, D, EC |
| ANALISIS | 15 | — | A, AB, E, EC, EB |
| INCORPORAR | 14 | 6 (respuesta opcional en C) | E, G, EC |
| PUBLICAR | 2 | — | D |

> **Opcional/condicional:** trámites con patrón C donde INCORPORAR puede aparecer
> si llega respuesta externa (el técnico lo crea manualmente).

---

## INCORPORAR

**Semántica:** Única tarea que produce documento sin consumir.
Punto de entrada de documentación externa al expediente.
`documento_usado_id = NULL`, `documento_producido_id` obligatorio.

| Fase | Trámite | Patrón | Qué documento entra |
|---|---|---|---|
| REGISTRO_SOLICITUD | RECEPCION_SOLICITUD | G | Solicitud inicial + documentación técnica aportada por el titular |
| CONSULTA_MINISTERIO | RECEPCION_INFORME | E | Informe preceptivo del Ministerio |
| COMPATIBILIDAD_AMBIENTAL | AUDIENCIA | EC | Propuesta de declaración de incompatibilidad ambiental (MA) |
| COMPATIBILIDAD_AMBIENTAL | RECEPCION_INFORME | E | Informe vinculante de Medio Ambiente (compatible/incompatible) |
| ADMISION_TRAMITE | ALEGACIONES | EB | Alegaciones presentadas al informe de admisión |
| CONSULTAS | RECEPCION_INFORME | E | Informe de organismo sectorial (con condicionados o negativa) |
| CONSULTAS | TRASLADO_REPAROS | EC | Respuesta del titular a reparos del organismo |
| INFORMACION_PUBLICA | ANUNCIO_BOE | C+E+F | Justificante de publicación con fecha real del BOE |
| INFORMACION_PUBLICA | ANUNCIO_BOP | C+E+F | Justificante de publicación con fecha real del BOP |
| INFORMACION_PUBLICA | ANUNCIO_PRENSA | C+E+F | Justificante de publicación en prensa |
| INFORMACION_PUBLICA | TABLON_AYUNTAMIENTOS | C+E | Certificado de exposición en tablón |
| INFORMACION_PUBLICA | RECEPCION_ALEGACION | EC | Alegación individual de interesado |
| FIGURA_AMBIENTAL_EXTERNA | RECEPCION_FIGURA | E | Resolución AAU / AAUS / CA del órgano ambiental |
| AAU_AAUS_INTEGRADA | RECEPCION_DICTAMEN | E | Dictamen ambiental integrado (MA) |

**Apariciones condicionales** (si llega respuesta externa en trámites con patrón C):

| Fase | Trámite | Condición |
|---|---|---|
| ADMISIBILIDAD | REQUERIMIENTO_SUBSANACION | Si el titular responde la subsanación |
| ANALISIS_TECNICO | REQUERIMIENTO_MEJORA | Si el titular aporta documentación complementaria |
| CONSULTA_MINISTERIO | SOLICITUD_INFORME | Si llega informe antes de vencer el plazo |
| COMPATIBILIDAD_AMBIENTAL | SOLICITUD_COMPATIBILIDAD | Si MA devuelve documentación antes del informe |
| FIGURA_AMBIENTAL_EXTERNA | SOLICITUD_FIGURA | Si llega resolución ambiental |
| AAU_AAUS_INTEGRADA | REMISION_MEDIO_AMBIENTE | Si MA devuelve dictamen |

---

## ANALISIS

**Semántica:** Revisión técnica o jurídica con generación obligatoria de documento formal.
`documento_usado_id` obligatorio (el documento analizado), `documento_producido_id` obligatorio (informe/nota).

| Fase | Trámite | Patrón | Qué analiza | Qué produce |
|---|---|---|---|---|
| ADMISIBILIDAD | COMPROBACION_ADMISIBILIDAD | A | Documentación de capacidad/legitimación | Informe de admisibilidad |
| ANALISIS_TECNICO | COMPROBACION_DOCUMENTAL | A | Documentación técnica del proyecto | Informe técnico |
| CONSULTA_MINISTERIO | RECEPCION_INFORME | E | Informe del Ministerio (incorporado) | Nota/informe de análisis |
| COMPATIBILIDAD_AMBIENTAL | AUDIENCIA | EC | Propuesta de incompatibilidad (incorporada) | Informe para redactar alegaciones |
| COMPATIBILIDAD_AMBIENTAL | RECEPCION_INFORME | E | Informe vinculante MA | Nota de análisis |
| ADMISION_TRAMITE | ANALISIS_ADMISION | AB | Documentación de admisión | Informe de admisión |
| ADMISION_TRAMITE | ALEGACIONES | EB | Alegaciones incorporadas | Nota de análisis |
| CONSULTAS | SEPARATAS | AC | Identifica organismos afectados | Informe de organismos (habilita REDACTAR separatas) |
| CONSULTAS | RECEPCION_INFORME | E | Informe de organismo sectorial | Nota de análisis de condicionados |
| CONSULTAS | TRASLADO_REPAROS | EC | Respuesta del titular a reparos | Nota de análisis |
| INFORMACION_PUBLICA | RECEPCION_ALEGACION | EC | Alegación individual | Clasifica alegante/interesado |
| INFORMACION_PUBLICA | ANALISIS_ALEGACIONES | AB | Conjunto de alegaciones recibidas | Informe técnico-jurídico de alegaciones |
| FIGURA_AMBIENTAL_EXTERNA | RECEPCION_FIGURA | E | Resolución ambiental (AAU/AAUS/CA) | Nota: puede paralizar expediente |
| AAU_AAUS_INTEGRADA | RECEPCION_DICTAMEN | E | Dictamen MA integrado | Nota: puede condicionar autorización |
| RESOLUCION | ELABORACION | AB | Conjunto de informes y trámites previos | Base para redactar resolución |

---

## REDACTAR

**Semántica:** Creación de documento administrativo (borrador).
`documento_usado_id` opcional (informe ANALISIS si existe), `documento_producido_id` obligatorio (borrador).

| Fase | Trámite | Patrón | Qué redacta |
|---|---|---|---|
| REGISTRO_SOLICITUD | COMUNICACION_INICIO | B | Acuse de recibo con número de expediente |
| ADMISIBILIDAD | REQUERIMIENTO_SUBSANACION | C | Requerimiento de subsanación de defectos formales |
| ANALISIS_TECNICO | REQUERIMIENTO_MEJORA | C | Requerimiento de mejora/complemento técnico |
| CONSULTA_MINISTERIO | SOLICITUD_INFORME | C | Solicitud de informe preceptivo al Ministerio |
| COMPATIBILIDAD_AMBIENTAL | SOLICITUD_COMPATIBILIDAD | C | Solicitud de compatibilidad ambiental a MA |
| COMPATIBILIDAD_AMBIENTAL | AUDIENCIA | EC | Alegaciones a propuesta de incompatibilidad |
| ADMISION_TRAMITE | ANALISIS_ADMISION | AB | Comunicación de resultado de admisión |
| ADMISION_TRAMITE | ALEGACIONES | EB | Respuesta a alegaciones de admisión |
| CONSULTAS | SEPARATAS | AC | Separatas por organismo afectado (con plantillas) |
| CONSULTAS | TRASLADO_REPAROS | EC | Traslado de reparos del titular al organismo |
| INFORMACION_PUBLICA | ANUNCIO_BOE | C+E+F | Anuncio para el BOE |
| INFORMACION_PUBLICA | ANUNCIO_BOP | C+E+F | Anuncio para el BOP |
| INFORMACION_PUBLICA | ANUNCIO_PRENSA | C+E+F | Anuncio para diario de mayor difusión |
| INFORMACION_PUBLICA | TABLON_AYUNTAMIENTOS | C+E | Oficio a ayuntamientos afectados |
| INFORMACION_PUBLICA | PORTAL_TRANSPARENCIA | D | Anuncio para portal institucional |
| INFORMACION_PUBLICA | RECEPCION_ALEGACION | EC | Traslado de alegación al titular |
| INFORMACION_PUBLICA | ANALISIS_ALEGACIONES | AB | Respuesta consolidada a alegaciones |
| FIGURA_AMBIENTAL_EXTERNA | SOLICITUD_FIGURA | C | Solicitud de instrumento ambiental |
| AAU_AAUS_INTEGRADA | REMISION_MEDIO_AMBIENTE | C | Traslado a MA del resultado de IP y consultas |
| RESOLUCION | ELABORACION | AB | Borrador de resolución |
| RESOLUCION | NOTIFICACION | B simplificado | Oficio de notificación de resolución |
| RESOLUCION | PUBLICACION | D | Anuncio de publicación de resolución |

---

## FIRMAR

**Semántica:** Firma autorizada del borrador.
`documento_usado_id` obligatorio (borrador de REDACTAR), `documento_producido_id` obligatorio (documento firmado).
El documento firmado proviene del portafirmas corporativo.

| Fase | Trámite | Patrón | Nota |
|---|---|---|---|
| REGISTRO_SOLICITUD | COMUNICACION_INICIO | B | — |
| ADMISIBILIDAD | REQUERIMIENTO_SUBSANACION | C | — |
| ANALISIS_TECNICO | REQUERIMIENTO_MEJORA | C | — |
| CONSULTA_MINISTERIO | SOLICITUD_INFORME | C | — |
| COMPATIBILIDAD_AMBIENTAL | SOLICITUD_COMPATIBILIDAD | C | — |
| COMPATIBILIDAD_AMBIENTAL | AUDIENCIA | EC | — |
| ADMISION_TRAMITE | ANALISIS_ADMISION | AB | — |
| ADMISION_TRAMITE | ALEGACIONES | EB | — |
| CONSULTAS | SEPARATAS | AC | — |
| CONSULTAS | TRASLADO_REPAROS | EC | — |
| INFORMACION_PUBLICA | ANUNCIO_BOE | C+E+F | — |
| INFORMACION_PUBLICA | ANUNCIO_BOP | C+E+F | — |
| INFORMACION_PUBLICA | ANUNCIO_PRENSA | C+E+F | — |
| INFORMACION_PUBLICA | TABLON_AYUNTAMIENTOS | C+E | — |
| INFORMACION_PUBLICA | PORTAL_TRANSPARENCIA | D | — |
| INFORMACION_PUBLICA | RECEPCION_ALEGACION | EC | — |
| INFORMACION_PUBLICA | ANALISIS_ALEGACIONES | AB | — |
| FIGURA_AMBIENTAL_EXTERNA | SOLICITUD_FIGURA | C | — |
| AAU_AAUS_INTEGRADA | REMISION_MEDIO_AMBIENTE | C | — |
| RESOLUCION | ELABORACION | AB | — |
| RESOLUCION | NOTIFICACION | B simplificado | **Opcional**: puede reutilizar documento firmado de ELABORACION |
| RESOLUCION | PUBLICACION | D | — |

---

## NOTIFICAR

**Semántica:** Comunicación a destinatario identificado.
`documento_usado_id` obligatorio (documento firmado), `documento_producido_id` obligatorio (justificante: acuse, certificado postal, etc.).
El justificante proviene de Notifica o similar (sistema corporativo externo).

| Fase | Trámite | Patrón | Destinatario | Justificante producido |
|---|---|---|---|---|
| REGISTRO_SOLICITUD | COMUNICACION_INICIO | B | Titular/Solicitante | Acuse de recibo |
| ADMISIBILIDAD | REQUERIMIENTO_SUBSANACION | C | Titular | Acuse requerimiento subsanación |
| ANALISIS_TECNICO | REQUERIMIENTO_MEJORA | C | Titular | Acuse requerimiento mejora |
| CONSULTA_MINISTERIO | SOLICITUD_INFORME | C | Ministerio | Acuse solicitud informe |
| COMPATIBILIDAD_AMBIENTAL | SOLICITUD_COMPATIBILIDAD | C | Medio Ambiente | Acuse solicitud compatibilidad |
| COMPATIBILIDAD_AMBIENTAL | AUDIENCIA | EC | MA (alegaciones) | Acuse alegaciones audiencia |
| ADMISION_TRAMITE | ANALISIS_ADMISION | AB | Titular | Acuse resultado admisión |
| ADMISION_TRAMITE | ALEGACIONES | EB | Titular (respuesta) | Acuse respuesta alegaciones |
| CONSULTAS | SEPARATAS | AC | Organismos afectados (uno por separata) | Acuse por organismo |
| CONSULTAS | TRASLADO_REPAROS | EC | Organismo (reparos trasladados) | Acuse traslado reparos |
| INFORMACION_PUBLICA | ANUNCIO_BOE | C+E+F | BOE | Acuse envío BOE |
| INFORMACION_PUBLICA | ANUNCIO_BOP | C+E+F | BOP | Acuse envío BOP |
| INFORMACION_PUBLICA | ANUNCIO_PRENSA | C+E+F | Diario | Acuse envío prensa |
| INFORMACION_PUBLICA | TABLON_AYUNTAMIENTOS | C+E | Ayuntamientos afectados | Acuse envío a ayuntamientos |
| INFORMACION_PUBLICA | RECEPCION_ALEGACION | EC | Titular (traslado alegación) | Acuse traslado |
| INFORMACION_PUBLICA | ANALISIS_ALEGACIONES | AB | Titular (respuesta consolidada) | Acuse respuesta |
| FIGURA_AMBIENTAL_EXTERNA | SOLICITUD_FIGURA | C | Órgano ambiental | Acuse solicitud instrumento |
| AAU_AAUS_INTEGRADA | REMISION_MEDIO_AMBIENTE | C | Medio Ambiente | Acuse remisión |
| RESOLUCION | NOTIFICACION | B simplificado | Interesados | Justificante notificación resolución |

---

## PUBLICAR

**Semántica:** Publicación en medios oficiales bajo control propio (fecha de publicación conocida).
`documento_usado_id` obligatorio (documento firmado), `documento_producido_id` obligatorio (justificante de publicación).
Distinta de NOTIFICAR+BOE/BOP/PRENSA donde NO controlamos la fecha de publicación.

| Fase | Trámite | Patrón | Dónde publica | Nota |
|---|---|---|---|---|
| INFORMACION_PUBLICA | PORTAL_TRANSPARENCIA | D | Portal institucional | Controlamos fecha → flujo simple |
| RESOLUCION | PUBLICACION | D sin ESPERAR | BOE/BOP/medios oficiales | Sin espera porque la publicación es el acto final |

> **Distinción clave PUBLICAR vs NOTIFICAR+BOE:**
> - `PUBLICAR` = controlamos nosotros la fecha de publicación (portal, acto propio).
> - `NOTIFICAR` → `ESPERAR_PLAZO` → `INCORPORAR` = enviamos al BOE/BOP/prensa y esperamos
>   a que lo publiquen (no controlamos la fecha).

---

## ESPERAR_PLAZO

**Semántica:** Suspensión temporal con fecha límite (0 = indefinida hasta evento externo).
Sin documentos: `documento_usado_id = NULL`, `documento_producido_id = NULL`.

| Fase | Trámite | Patrón | Tipo de espera | ¿Puede generar INCORPORAR? |
|---|---|---|---|---|
| ADMISIBILIDAD | REQUERIMIENTO_SUBSANACION | C | Plazo de subsanación | Sí, si llega respuesta |
| ANALISIS_TECNICO | REQUERIMIENTO_MEJORA | C | Plazo de mejora técnica | Sí, si llega documentación |
| CONSULTA_MINISTERIO | SOLICITUD_INFORME | C | Indefinida hasta informe | Sí (el informe llega vía INCORPORAR) |
| COMPATIBILIDAD_AMBIENTAL | SOLICITUD_COMPATIBILIDAD | C | Indefinida hasta compatibilidad | Sí |
| COMPATIBILIDAD_AMBIENTAL | AUDIENCIA | EC | Plazo audiencia | Sí, si llega respuesta |
| CONSULTAS | SEPARATAS | AC | Plazo de respuesta de organismos | Sí (cada informe llega vía INCORPORAR) |
| CONSULTAS | TRASLADO_REPAROS | EC | Plazo respuesta tras reparos | Sí, si llega respuesta |
| INFORMACION_PUBLICA | ANUNCIO_BOE | C+E+F | ×1: hasta publicación efectiva | Sí (justificante BOE) |
| INFORMACION_PUBLICA | ANUNCIO_BOE | C+E+F | ×2: plazo de alegaciones | No (plazo sin respuesta esperada) |
| INFORMACION_PUBLICA | ANUNCIO_BOP | C+E+F | ×1: hasta publicación efectiva | Sí (justificante BOP) |
| INFORMACION_PUBLICA | ANUNCIO_BOP | C+E+F | ×2: plazo de alegaciones | No |
| INFORMACION_PUBLICA | ANUNCIO_PRENSA | C+E+F | ×1: hasta publicación efectiva | Sí (justificante prensa) |
| INFORMACION_PUBLICA | ANUNCIO_PRENSA | C+E+F | ×2: plazo de alegaciones | No |
| INFORMACION_PUBLICA | TABLON_AYUNTAMIENTOS | C+E | Hasta recibir certificado | Sí (certificado de exposición) |
| INFORMACION_PUBLICA | PORTAL_TRANSPARENCIA | D | Plazo de alegaciones | No |
| INFORMACION_PUBLICA | RECEPCION_ALEGACION | EC | Plazo respuesta titular | Sí, si llega respuesta |
| FIGURA_AMBIENTAL_EXTERNA | SOLICITUD_FIGURA | C | Indefinida (plazo=0) hasta resolución ambiental | Sí (la resolución llega vía INCORPORAR) |
| AAU_AAUS_INTEGRADA | REMISION_MEDIO_AMBIENTE | C | Indefinida (plazo=0) hasta dictamen MA | Sí (el dictamen llega vía INCORPORAR) |

---

## Observaciones de desalineación detectadas

Notas para la sesión de revisión del JSON. No son cambios — son preguntas abiertas.

### 1. Referencias obsoletas a `TAREA_ORIGEN_ID` / `TAREA_DESTINO_ID`

El JSON (incluidas `NOTAS_IMPLEMENTACION.validaciones_documentales`) sigue referenciando
`T.DOCUMENTOS.TAREA_ORIGEN_ID` y `T.DOCUMENTOS.TAREA_DESTINO_ID`.
El modelo actual invirtió esa relación: las FKs viven en `T.TAREAS`
(`documento_producido_id`, `documento_usado_id`), no en `T.DOCUMENTOS`.
El pool es agnóstico. Hay que actualizar todas estas referencias en el JSON.

### 2. `tipos_documentos` no existe en el JSON

Ninguna tarea, trámite ni patrón menciona el tipo semántico del documento que produce o consume.
Con `tipos_documentos` ya en el modelo, cada aparición de INCORPORAR podría (y debería)
asociar un tipo al documento producido. Igual para ANALISIS, FIRMAR, NOTIFICAR, PUBLICAR.
Candidato a enriquecer la definición de cada tarea atómica.

### 3. `INCORPORAR` y el pool masivo

La tarea `INCORPORAR` se define como acto del técnico en el flujo de tramitación.
La pantalla de gestión masiva (#180) también introduce documentos al pool, pero sin
pasar por ninguna tarea. Son dos vías de entrada distintas al mismo pool.
El JSON no contempla esta segunda vía. Hay que decidir si se documenta o se deja
como funcionalidad de soporte fuera del flujo ESFTT.

### 4. `fecha_administrativa` en documentos producidos internamente

El JSON no menciona `fecha_administrativa` en ningún tipo de tarea.
Sin embargo, la propuesta de hacer el campo nullable (#191) implica que:
- Documentos de `INCORPORAR`: la fecha administrativa es conocida en el acto (fecha de registro).
- Documentos de `FIRMAR`: la fecha es `FECHA_FIN` de la tarea (acto de firma).
- Documentos de `NOTIFICAR`/`PUBLICAR`: la fecha es `FECHA_FIN` de la tarea.
- Documentos de `REDACTAR`/`ANALISIS`: sin fecha administrativa (el borrador y el informe
  no tienen efectos jurídicos directos). Son candidatos a `fecha_administrativa = NULL` por diseño,
  no por incompletos.
Esto modifica la semántica de NULL: no solo "pendiente de revisión" sino también
"documento sin valor jurídico propio (borrador/informe interno)".

### 5. NOTIFICAR produce justificante externo — igual que INCORPORAR en el sentido inverso

El justificante que produce NOTIFICAR viene de Notifica/bandeja (sistema corporativo externo).
El justificante que produce PUBLICAR+BOE viene del BOE.
Ambos son documentos que "entran" desde sistemas externos, como INCORPORAR.
La distinción es que NOTIFICAR/PUBLICAR los encadenan con el documento firmado previo.
Esto es relevante para definir `tipo_doc_id` en estos justificantes.
