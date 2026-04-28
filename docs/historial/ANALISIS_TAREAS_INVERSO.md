# Tabla Inversa de Tareas Atómicas — ESFTT

> Fuente de verdad: `ESTRUCTURA_FTT.json`
> Última sincronización: 2026-04-28

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
| REDACTAR | 19 | — | B, C, C+, AB, EC, D |
| FIRMAR | 18 | 1 (RESOLUCION.NOTIFICACION) | B, C, C+, AB, EC, D |
| NOTIFICAR | 16 | — | B, C, C+, AB, EC |
| ESPERAR_PLAZO | 15 | — | C, C+, D, EC |
| ANALIZAR | 13 | — | A, C+, AB, E, EC |
| INCORPORAR | 14 | 4 (respuesta opcional en C) | E, C+, EC |
| PUBLICAR | 2 | — | D |

> **Opcional/condicional:** trámites con patrón C donde INCORPORAR puede aparecer
> si llega respuesta externa (el técnico lo crea manualmente).
>
> **Nota v5.5:** Fases REGISTRO_SOLICITUD, ADMISIBILIDAD y ANALISIS_TECNICO eliminadas y
> fusionadas en ANALISIS_SOLICITUD. Patrón G (RECEPCION_SOLICITUD) eliminado.
> CONSULTAS reestructurado: SEPARATAS → CONSULTA_SEPARATA (por organismo, C+);
> TRASLADO_REPAROS → CONSULTA_TRASLADO_TITULAR + CONSULTA_TRASLADO_ORGANISMO (C+).

---

## INCORPORAR

**Semántica:** Única tarea que no consume documento.
Punto de entrada de documentación externa al expediente durante tramitación activa.
`documento_usado_id = NULL`. Desde v5.5: usa tabla `documentos_tarea` (N:M, ≥1 registro
obligatorio para `FECHA_FIN`). `documento_producido_id` deprecado para esta tarea.
Ver `DISEÑO_SUBSISTEMA_DOCUMENTAL.md §INCORPORAR` y `DISEÑO_ANALISIS_SOLICITUD.md §5`.

| Fase | Trámite | Patrón | Qué documento entra |
|---|---|---|---|
| ANALISIS_SOLICITUD | REQUERIMIENTO_SUBSANACION | C+ | Documentación de subsanación aportada por el titular |
| CONSULTA_MINISTERIO | RECEPCION_INFORME | E | Informe preceptivo del Ministerio |
| COMPATIBILIDAD_AMBIENTAL | AUDIENCIA | EC | Propuesta de declaración de incompatibilidad ambiental (MA) |
| COMPATIBILIDAD_AMBIENTAL | RECEPCION_INFORME | E | Informe vinculante de Medio Ambiente (compatible/incompatible) |
| CONSULTAS | CONSULTA_SEPARATA | C+ | Informe del organismo sectorial (conformidad, oposición, reparos, condicionado) |
| CONSULTAS | CONSULTA_TRASLADO_TITULAR | C+ | Respuesta del titular a los reparos del organismo |
| CONSULTAS | CONSULTA_TRASLADO_ORGANISMO | C+ | Respuesta final del organismo tras los reparos del titular |
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
| CONSULTA_MINISTERIO | SOLICITUD_INFORME | Si llega informe antes de vencer el plazo |
| COMPATIBILIDAD_AMBIENTAL | SOLICITUD_COMPATIBILIDAD | Si MA devuelve documentación antes del informe |
| FIGURA_AMBIENTAL_EXTERNA | SOLICITUD_FIGURA | Si llega resolución ambiental |
| AAU_AAUS_INTEGRADA | REMISION_MEDIO_AMBIENTE | Si MA devuelve dictamen |

---

## ANALIZAR

**Semántica:** Revisión técnica o jurídica con generación obligatoria de documento formal.
`documento_usado_id` obligatorio (el documento analizado), `documento_producido_id` obligatorio (informe/nota).

| Fase | Trámite | Patrón | Qué analiza | Qué produce |
|---|---|---|---|---|
| ANALISIS_SOLICITUD | ANALISIS_DOCUMENTAL | A | Documentación del pool (cualifica tipos, contrasta checklist) | Informe de resultado (admisible / con defectos) |
| ANALISIS_SOLICITUD | REQUERIMIENTO_SUBSANACION | C+ | Documentación de subsanación aportada por el titular | Informe de evaluación de subsanación |
| CONSULTA_MINISTERIO | RECEPCION_INFORME | E | Informe del Ministerio (incorporado) | Nota/informe de análisis |
| COMPATIBILIDAD_AMBIENTAL | AUDIENCIA | EC | Propuesta de incompatibilidad (incorporada) | Informe para redactar alegaciones |
| COMPATIBILIDAD_AMBIENTAL | RECEPCION_INFORME | E | Informe vinculante MA | Nota de análisis |
| CONSULTAS | CONSULTA_SEPARATA | C+ | Respuesta del organismo (conformidad, reparos, condicionado…) | Nota de análisis con resultado |
| CONSULTAS | CONSULTA_TRASLADO_TITULAR | C+ | Respuesta del titular a los reparos | Nota de análisis con resultado |
| CONSULTAS | CONSULTA_TRASLADO_ORGANISMO | C+ | Respuesta final del organismo | Nota de análisis con resultado |
| INFORMACION_PUBLICA | RECEPCION_ALEGACION | EC | Alegación individual | Clasifica alegante/interesado |
| INFORMACION_PUBLICA | ANALISIS_ALEGACIONES | A | Conjunto de alegaciones recibidas | Informe técnico-jurídico de alegaciones |
| FIGURA_AMBIENTAL_EXTERNA | RECEPCION_FIGURA | E | Resolución ambiental (AAU/AAUS/CA) | Nota: puede paralizar expediente |
| AAU_AAUS_INTEGRADA | RECEPCION_DICTAMEN | E | Dictamen MA integrado | Nota: puede condicionar autorización |
| RESOLUCION | ELABORACION | AB | Conjunto de informes y trámites previos | Base para redactar resolución |

---

## REDACTAR

**Semántica:** Creación de documento administrativo (borrador).
`documento_usado_id` opcional (informe ANALIZAR si existe), `documento_producido_id` obligatorio (borrador).

| Fase | Trámite | Patrón | Qué redacta |
|---|---|---|---|
| ANALISIS_SOLICITUD | REQUERIMIENTO_SUBSANACION | C+ | Requerimiento de subsanación de defectos |
| ANALISIS_SOLICITUD | COMUNICACION_INICIO | B | Acuse de recibo con número de expediente |
| CONSULTA_MINISTERIO | SOLICITUD_INFORME | C | Solicitud de informe preceptivo al Ministerio |
| COMPATIBILIDAD_AMBIENTAL | SOLICITUD_COMPATIBILIDAD | C | Solicitud de compatibilidad ambiental a MA |
| COMPATIBILIDAD_AMBIENTAL | AUDIENCIA | EC | Alegaciones a propuesta de incompatibilidad |
| CONSULTAS | CONSULTA_SEPARATA | C+ | Separata al organismo afectado |
| CONSULTAS | CONSULTA_TRASLADO_TITULAR | C+ | Traslado al titular de la respuesta del organismo |
| CONSULTAS | CONSULTA_TRASLADO_ORGANISMO | C+ | Traslado al organismo de los reparos del titular |
| INFORMACION_PUBLICA | ANUNCIO_BOE | C+E+F | Anuncio para el BOE |
| INFORMACION_PUBLICA | ANUNCIO_BOP | C+E+F | Anuncio para el BOP |
| INFORMACION_PUBLICA | ANUNCIO_PRENSA | C+E+F | Anuncio para diario de mayor difusión |
| INFORMACION_PUBLICA | TABLON_AYUNTAMIENTOS | C+E | Oficio a ayuntamientos afectados |
| INFORMACION_PUBLICA | PORTAL_TRANSPARENCIA | D | Anuncio para portal institucional |
| INFORMACION_PUBLICA | RECEPCION_ALEGACION | EC | Traslado de alegación al titular |
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
| ANALISIS_SOLICITUD | REQUERIMIENTO_SUBSANACION | C+ | — |
| ANALISIS_SOLICITUD | COMUNICACION_INICIO | B | — |
| CONSULTA_MINISTERIO | SOLICITUD_INFORME | C | — |
| COMPATIBILIDAD_AMBIENTAL | SOLICITUD_COMPATIBILIDAD | C | — |
| COMPATIBILIDAD_AMBIENTAL | AUDIENCIA | EC | — |
| CONSULTAS | CONSULTA_SEPARATA | C+ | — |
| CONSULTAS | CONSULTA_TRASLADO_TITULAR | C+ | — |
| CONSULTAS | CONSULTA_TRASLADO_ORGANISMO | C+ | — |
| INFORMACION_PUBLICA | ANUNCIO_BOE | C+E+F | — |
| INFORMACION_PUBLICA | ANUNCIO_BOP | C+E+F | — |
| INFORMACION_PUBLICA | ANUNCIO_PRENSA | C+E+F | — |
| INFORMACION_PUBLICA | TABLON_AYUNTAMIENTOS | C+E | — |
| INFORMACION_PUBLICA | PORTAL_TRANSPARENCIA | D | — |
| INFORMACION_PUBLICA | RECEPCION_ALEGACION | EC | — |
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
| ANALISIS_SOLICITUD | REQUERIMIENTO_SUBSANACION | C+ | Titular | Acuse requerimiento subsanación |
| ANALISIS_SOLICITUD | COMUNICACION_INICIO | B | Titular/Solicitante | Acuse de recibo |
| CONSULTA_MINISTERIO | SOLICITUD_INFORME | C | Ministerio | Acuse solicitud informe |
| COMPATIBILIDAD_AMBIENTAL | SOLICITUD_COMPATIBILIDAD | C | Medio Ambiente | Acuse solicitud compatibilidad |
| COMPATIBILIDAD_AMBIENTAL | AUDIENCIA | EC | MA (alegaciones) | Acuse alegaciones audiencia |
| CONSULTAS | CONSULTA_SEPARATA | C+ | Organismo afectado | Acuse por organismo |
| CONSULTAS | CONSULTA_TRASLADO_TITULAR | C+ | Titular | Acuse traslado al titular |
| CONSULTAS | CONSULTA_TRASLADO_ORGANISMO | C+ | Organismo | Acuse traslado al organismo |
| INFORMACION_PUBLICA | ANUNCIO_BOE | C+E+F | BOE | Acuse envío BOE |
| INFORMACION_PUBLICA | ANUNCIO_BOP | C+E+F | BOP | Acuse envío BOP |
| INFORMACION_PUBLICA | ANUNCIO_PRENSA | C+E+F | Diario | Acuse envío prensa |
| INFORMACION_PUBLICA | TABLON_AYUNTAMIENTOS | C+E | Ayuntamientos afectados | Acuse envío a ayuntamientos |
| INFORMACION_PUBLICA | RECEPCION_ALEGACION | EC | Titular (traslado alegación) | Acuse traslado |
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

**Semántica:** Suspensión temporal con fecha límite (`PLAZO_DIAS=0`: indefinida hasta evento externo).
`documento_producido_id = NULL` siempre. `documento_usado_id` **obligatorio en todos los casos** — es el justificante de NOTIFICAR o PUBLICAR cuya `fecha_administrativa` inicia el cómputo del plazo o ancla el evento externo.

**Pendiente normativo (`plazo=0`):** El caso `AAU_AAUS_INTEGRADA / REMISION_MEDIO_AMBIENTE` puede requerir `plazo=0` porque Medio Ambiente no tiene plazo legalmente definido. Está por determinar qué apartado normativo lo regula y si `documento_usado_id` es igualmente obligatorio en ese caso. Derivar en issue específico cuando se implemente ese trámite. (#296 pregunta abierta 2).

| Fase | Trámite | Patrón | Tipo de espera | ¿Puede generar INCORPORAR? |
|---|---|---|---|---|
| ANALISIS_SOLICITUD | REQUERIMIENTO_SUBSANACION | C+ | Plazo de subsanación | Sí (documentación subsanada) |
| CONSULTA_MINISTERIO | SOLICITUD_INFORME | C | Indefinida hasta informe | Sí (el informe llega vía INCORPORAR) |
| COMPATIBILIDAD_AMBIENTAL | SOLICITUD_COMPATIBILIDAD | C | Indefinida hasta compatibilidad | Sí |
| COMPATIBILIDAD_AMBIENTAL | AUDIENCIA | EC | Plazo audiencia | Sí, si llega respuesta |
| CONSULTAS | CONSULTA_SEPARATA | C+ | Plazo de respuesta del organismo | Sí (informe llega vía INCORPORAR) |
| CONSULTAS | CONSULTA_TRASLADO_TITULAR | C+ | Plazo respuesta del titular | Sí, si llega respuesta |
| CONSULTAS | CONSULTA_TRASLADO_ORGANISMO | C+ | Plazo respuesta final del organismo | Sí, si llega respuesta |
| INFORMACION_PUBLICA | ANUNCIO_BOE | C+E+F | ×1: hasta publicación efectiva | Sí (justificante BOE) |
| INFORMACION_PUBLICA | ANUNCIO_BOE | C+E+F | ×2: plazo de alegaciones | No (plazo sin respuesta esperada) |
| INFORMACION_PUBLICA | ANUNCIO_BOP | C+E+F | ×1: hasta publicación efectiva | Sí (justificante BOP) |
| INFORMACION_PUBLICA | ANUNCIO_BOP | C+E+F | ×2: plazo de alegaciones | No |
| INFORMACION_PUBLICA | ANUNCIO_PRENSA | C+E+F | ×1: hasta publicación efectiva | Sí (justificante prensa) |
| INFORMACION_PUBLICA | ANUNCIO_PRENSA | C+E+F | ×2: plazo de alegaciones | No |
| INFORMACION_PUBLICA | TABLON_AYUNTAMIENTOS | C+E | Hasta recibir certificado | Sí (certificado de exposición) |
| INFORMACION_PUBLICA | PORTAL_TRANSPARENCIA | D | Plazo de alegaciones | No |
| INFORMACION_PUBLICA | RECEPCION_ALEGACION | EC | Plazo respuesta titular | Sí, si llega respuesta |
| FIGURA_AMBIENTAL_EXTERNA | SOLICITUD_FIGURA | C | Indefinida (`plazo=0`) hasta resolución ambiental | Sí (la resolución llega vía INCORPORAR) |
| AAU_AAUS_INTEGRADA | REMISION_MEDIO_AMBIENTE | C | Indefinida (`plazo=0`) hasta dictamen MA | Sí (el dictamen llega vía INCORPORAR) |

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
asociar un tipo al documento producido. Igual para ANALIZAR, FIRMAR, NOTIFICAR, PUBLICAR.
Candidato a enriquecer la definición de cada tarea atómica.

### 3. `INCORPORAR` y el pool masivo

La tarea `INCORPORAR` se define como acto del técnico en el flujo de tramitación.
La pantalla de gestión masiva (#180) también introduce documentos al pool, pero sin
pasar por ninguna tarea. Son dos vías de entrada distintas al mismo pool.
El JSON no contempla esta segunda vía. Hay que decidir si se documenta o se deja
como funcionalidad de soporte fuera del flujo ESFTT.

### 4. `fecha_administrativa` en documentos producidos internamente

El JSON no menciona `fecha_administrativa` en ningún tipo de tarea.
Según la conclusión arquitectónica de `ANALISIS_FECHAS_ESFTT.md` (absorbida en `DISEÑO_FECHAS_PLAZOS.md §2.bis`), ningún campo `fecha_fin` existe en Tarea. La `fecha_administrativa` vive exclusivamente en el `Documento`:
- Documentos de `INCORPORAR`: la fecha administrativa es conocida en el acto (fecha de registro).
- Documentos de `FIRMAR`: `documento_producido.fecha_administrativa` porta la fecha del acto de firma.
- Documentos de `NOTIFICAR`/`PUBLICAR`: `documento_producido.fecha_administrativa` porta la fecha del acto.
- Documentos de `REDACTAR`/`ANALIZAR`: sin fecha administrativa (el borrador y el informe
  no tienen efectos jurídicos directos). Son candidatos a `fecha_administrativa = NULL` por diseño,
  no por incompletos.
La semántica de NULL en `fecha_administrativa`: no solo "pendiente de revisión" sino también
"documento sin valor jurídico propio (borrador/informe interno)".

### 5. NOTIFICAR produce justificante externo — igual que INCORPORAR en el sentido inverso

El justificante que produce NOTIFICAR viene de Notifica/bandeja (sistema corporativo externo).
El justificante que produce PUBLICAR+BOE viene del BOE.
Ambos son documentos que "entran" desde sistemas externos, como INCORPORAR.
La distinción es que NOTIFICAR/PUBLICAR los encadenan con el documento firmado previo.
Esto es relevante para definir `tipo_doc_id` en estos justificantes.

### 6. Señal de resultado en NOTIFICAR — resultado INCORRECTA (#296)

Solo `NOTIFICAR` puede producir un documento con `efecto_tarea = INCORRECTA` (notificación caducada
o fallida). El resultado se registra en `resultados_documentos` vinculado al `documento_producido_id`
de la tarea. Sin fila en `resultados_documentos` → resultado `INDIFERENTE` (valor por defecto).

Cuando una tarea NOTIFICAR tiene resultado INCORRECTA:
- `Tramite.finalizado` devuelve `False` aunque el `documento_producido_id` esté presente.
- El invariante `_check_finalizar_tramite` bloquea el cierre del trámite.
- El invariante `_check_finalizar_fase` bloquea el cierre de la fase.
- El técnico debe subsanar la notificación (nueva tarea NOTIFICAR) antes de poder cerrar.

La whitelist `tipos_documentos_resultados_validos` (N:M) declara qué resultados son válidos
para cada `tipo_documento`. Se popula a medida que se registran los tipos de documentos de
notificación en `tipos_documentos`.
