# Análisis: Listado Inteligente de Expedientes

> Fuente de verdad: `docs/ESTRUCTURA_FTT.json`
> Última sincronización: 2026-03-26

**Issue de referencia:** #169
**Estado:** Borrador — pendiente de revisión

---

## 1. Concepto

El listado de expedientes es una **cola de trabajo multi-pista**: cada fila representa una **solicitud** (no un expediente), con varias pistas de seguimiento cuyo estado se deduce automáticamente del árbol ESFTT.

El tramitador gestiona por lotes: filtra por estado de pista y trabaja secuencialmente ese grupo.

**Unidad de fila: solicitud.** El número AT puede repetirse si un expediente tiene varias solicitudes activas simultáneamente. Esa repetición es intencionada y se señaliza visualmente.

---

## 2. Columnas del listado

| Columna | Tipo | Notas |
|---------|------|-------|
| **Nº AT** | Texto + estilo | Si el AT aparece en más de una fila (varias solicitudes activas), se marca visualmente (badge, color) |
| **Tipo solicitud** | Texto | AAP_AAC, AAE, DUP… Indica de qué acto administrativo se trata |
| **Fecha solicitud** | Fecha | Ordenación principal por defecto |
| **Solicitante** | Texto + estilo | EDISTRIBUCIÓN = estilo distintivo; particulares = negrita; resto = normal |
| **Proyecto** | Texto | Descripción del proyecto |
| **SOL/REQ/SUB** | Estado | Pista de análisis y subsanación |
| **CONSULTAS** | Estado | Pista de separatas e informes |
| **MA** | Estado | Pista de tramitación ambiental |
| **IP** | Estado | Pista de información pública |
| **RESOLUCIÓN** | Estado | Pista de resolución |
| **FIN** | Booleano calculado | TRUE si todas las pistas son FIN o vacías. Permite filtrar activos/resueltos |
| **Notas** | Texto libre | A definir alcance en BDDAT |
| **Última comunicación** | Referencia | TBD — a decidir si se incluye |

---

## 3. Pistas de seguimiento y su mapeo a tipos_fases

| Pista | tipos_fases en BD | Obligatoriedad |
|-------|-------------------|----------------|
| **SOL/REQ/SUB** | `ADMISIBILIDAD` (id=2) | Siempre |
| **CONSULTAS** | `CONSULTAS` (id=7), `CONSULTA_MINISTERIO` (id=4) — y futuras fases de tipo similar | Según tipo solicitud (POS/N/A) |
| **MA** | `COMPATIBILIDAD_AMBIENTAL` (id=5), `FIGURA_AMBIENTAL_EXTERNA` (id=9), `AAU_AAUS_INTEGRADA` (id=10) | Según tipo solicitud |
| **IP** | `INFORMACION_PUBLICA` (id=8) | Según tipo solicitud (POS/N/A) |
| **RESOLUCIÓN** | `RESOLUCION` (id=11) | Siempre |

**Inteligencia de columna:** si una solicitud no tiene fases del tipo "principal" de una pista pero sí de un tipo alternativo (p.ej. no tiene `CONSULTAS` pero sí `CONSULTA_MINISTERIO`), la columna muestra el estado de la fase disponible. Si tiene varias fases abiertas en la misma pista, se muestra el estado más urgente. Las fases cerradas no contribuyen al estado visible.

**Columna vacía vs N/A:** si el tipo de solicitud hace que una pista sea no aplicable (p.ej. AAC no tiene IP), la celda aparece vacía/gris sin estado. Diferente a FIN (verde).

> **Pendiente de decisión:** `ESTRUCTURA_FTT.json` v5.5 define `ANALISIS_SOLICITUD` como código unificado que sustituye a `REGISTRO_SOLICITUD + ADMISIBILIDAD + ANALISIS_TECNICO`. En BD aún existen los tres códigos viejos. Mientras no se migre, la pista SOL/REQ/SUB mapea a `ADMISIBILIDAD`. Ver §8.

---

## 4. Paleta de estados

### 4.1 Semántica de colores

| Color | Significado |
|-------|-------------|
| **Rojo** | Acción pendiente del tramitador |
| **Amarillo** | En espera de algo interno que no depende del tramitador (firma) |
| **Azul** | En espera de un externo que no depende de la administración (publicador, titular) |
| **Naranja** | Listo para cerrar |
| **Gris** | Espera pasiva (plazo legal, respuesta de administrado u organismo) |
| **Verde** | Finalizado |

### 4.2 Estados válidos por pista

Cada pista tiene su propio subconjunto de estados posibles, determinado por el flujo de sus fases:

| Estado | SOL/REQ/SUB | CONSULTAS | MA | IP | RESOLUCIÓN |
|--------|:-----------:|:---------:|:--:|:--:|:----------:|
| PENDIENTE_TRAMITAR | ✓ | ✓ | ✓ | ✓ | ✓ |
| PENDIENTE_ESTUDIO | ✓ | ✓ | ✓ | ✓ | ✓ |
| PENDIENTE_REDACTAR | — | ✓ | ✓ | ✓ | ✓ |
| PENDIENTE_FIRMA | ✓ | ✓ | ✓ | ✓ | ✓ |
| PENDIENTE_NOTIFICAR | ✓ | ✓ | ✓ | — | ✓ |
| PENDIENTE_PUBLICAR | — | — | — | ✓ | ✓ |
| PENDIENTE_SUBSANAR | ✓ | — | — | — | — |
| PENDIENTE_PLAZOS | — | ✓ | ✓ | ✓ | — |
| PENDIENTE_CERRAR | ✓ | ✓ | ✓ | ✓ | ✓ |
| FIN | ✓ | ✓ | ✓ | ✓ | ✓ |

> SOL/REQ/SUB no tiene PENDIENTE_REDACTAR porque su primera acción activa es siempre un análisis (ANALIZAR), no una redacción.

### 4.3 Definición de estados

| Estado | Color | Cuándo se aplica |
|--------|-------|------------------|
| **PENDIENTE_TRAMITAR** | rojo | Solicitud sin fases; fase sin trámites; trámite sin tareas creadas; FIRMAR sin borrador; NOTIFICAR/PUBLICAR sin doc firmado |
| **PENDIENTE_ESTUDIO** | rojo | ANALIZAR sin input o sin informe producido; INCORPORAR sin docs; ESPERAR_PLAZO vencido; fase con trámites cerrados y `resultado_fase IS NULL` |
| **PENDIENTE_REDACTAR** | rojo | REDACTAR sin borrador; trámite cuya primera tarea es REDACTAR, creado pero no iniciado |
| **PENDIENTE_FIRMA** | amarillo | FIRMAR con borrador presente pero sin doc firmado |
| **PENDIENTE_NOTIFICAR** | azul | NOTIFICAR con doc firmado pero sin justificante |
| **PENDIENTE_PUBLICAR** | azul | PUBLICAR con doc firmado pero sin justificante |
| **PENDIENTE_SUBSANAR** | gris | ESPERAR_PLAZO activo en pista SOL/REQ/SUB |
| **PENDIENTE_PLAZOS** | gris | ESPERAR_PLAZO activo en pistas CONSULTAS, MA o IP |
| **PENDIENTE_CERRAR** | naranja | Tarea/trámite/fase completos pero sin `fecha_fin` |
| **FIN** | verde | Fase finalizada (`fecha_fin IS NOT NULL`) |

### 4.4 Subestados internos por tipo de tarea

| Tarea | Situación | Estado | Color |
|-------|-----------|--------|-------|
| **ANALIZAR** | Falta `doc_usado` | PENDIENTE_ESTUDIO | rojo |
| | Tiene input, falta `doc_producido` | PENDIENTE_ESTUDIO | rojo |
| | Tiene ambos | PENDIENTE_CERRAR | naranja |
| **REDACTAR** | Sin borrador | PENDIENTE_REDACTAR | rojo |
| | Con borrador | PENDIENTE_CERRAR | naranja |
| **FIRMAR** | Falta borrador | PENDIENTE_TRAMITAR | rojo |
| | Tiene borrador, falta firmado | PENDIENTE_FIRMA | amarillo |
| | Tiene ambos | PENDIENTE_CERRAR | naranja |
| **NOTIFICAR** | Falta doc firmado | PENDIENTE_TRAMITAR | rojo |
| | Tiene firmado, falta justificante | PENDIENTE_NOTIFICAR | azul |
| | Tiene ambos | PENDIENTE_CERRAR | naranja |
| **PUBLICAR** | Falta doc firmado | PENDIENTE_TRAMITAR | rojo |
| | Tiene firmado, falta justificante | PENDIENTE_PUBLICAR | azul |
| | Tiene ambos | PENDIENTE_CERRAR | naranja |
| **ESPERAR_PLAZO** | `PLAZO_DIAS=0` o plazo activo | PENDIENTE_SUBSANAR / PENDIENTE_PLAZOS | gris |
| | Plazo vencido | PENDIENTE_ESTUDIO | rojo |
| **INCORPORAR** | Sin `documentos_tarea` | PENDIENTE_ESTUDIO | rojo |
| | Con ≥1 registro | PENDIENTE_CERRAR | naranja |

---

## 5. Algoritmo de deducción jerárquica

El servicio `app/services/seguimiento.py` (pendiente de crear) deduce el estado de cada pista recorriendo el árbol de abajo arriba. El estado más urgente prevalece.

**Prioridad de urgencia:** rojo > amarillo > azul > naranja > gris > verde

```
Para cada pista de la solicitud EN_TRAMITE:
  1. Buscar fases del tipo correspondiente en esa solicitud
  2. Si no existe ninguna → celda vacía (N/A) o PENDIENTE_TRAMITAR según tipo solicitud
  3. Si todas cerradas → FIN (verde)
  4. Para cada fase abierta:
     a. No iniciada (fecha_inicio IS NULL) → PENDIENTE_TRAMITAR
     b. Iniciada, sin trámites → PENDIENTE_TRAMITAR
     c. Iniciada, con trámites:
        · Trámite no iniciado → PENDIENTE_TRAMITAR
          (excepción: si primera tarea es REDACTAR → PENDIENTE_REDACTAR)
        · Trámite iniciado, sin tareas → PENDIENTE_TRAMITAR
        · Trámite iniciado, con tareas:
          - Sin tarea activa, todas finalizadas → PENDIENTE_CERRAR
          - Sin tarea activa, hay planificadas → PENDIENTE_TRAMITAR
          - Con tarea activa → aplicar §4.4
        · Todos los trámites cerrados:
          - resultado_fase IS NULL → PENDIENTE_ESTUDIO
          - resultado_fase IS NOT NULL → PENDIENTE_CERRAR
  5. Devolver estado más urgente entre todas las fases abiertas de esa pista
```

---

## 6. Escenarios de prueba necesarios

Fila = solicitud. El AT puede repetirse. Columnas relevantes para el test:

| AT | Tipo sol. | SOL/REQ/SUB | CONSULTAS | MA | IP | RESOLUCIÓN | FIN | Propósito |
|----|-----------|-------------|-----------|----|----|------------|-----|-----------|
| T01 | AAP_AAC | PENDIENTE_ESTUDIO | — | — | — | — | N | ANALIZAR sin input |
| T02 | AAP_AAC | PENDIENTE_REDACTAR | — | — | — | — | N | Requerimiento por redactar |
| T03 | AAP_AAC | PENDIENTE_FIRMA | — | — | — | — | N | Borrador OK, por firmar |
| T04 | AAP_AAC | PENDIENTE_SUBSANAR | PENDIENTE_PLAZOS | — | — | — | N | Esperando subsanación + organismo |
| T04 | AAE | PENDIENTE_ESTUDIO | — | — | — | — | N | Mismo AT, segunda solicitud activa |
| T05 | AAP_AAC | FIN | PENDIENTE_NOTIFICAR | — | — | — | N | Separata por enviar |
| T06 | AAP_AAC | FIN | FIN | PENDIENTE_PLAZOS | — | — | N | Esperando dictamen ambiental |
| T07 | AAP_AAC | FIN | FIN | FIN | PENDIENTE_PUBLICAR | — | N | Anuncio BOP por publicar |
| T08 | AAP_AAC | FIN | FIN | FIN | PENDIENTE_PLAZOS | PENDIENTE_ESTUDIO | N | IP en alegaciones + resolución en marcha |
| T09 | AAP_AAC | FIN | FIN | FIN | FIN | PENDIENTE_NOTIFICAR | N | Resolución por notificar |
| T10 | AAP_AAC | FIN | FIN | FIN | FIN | FIN | S | Solicitud resuelta — filtro FIN=TRUE |
| T11 | AAP_AAC | PENDIENTE_TRAMITAR | — | — | — | — | N | Sin responsable, sin fases creadas |

> T04 aparece dos veces con el mismo AT para verificar el indicador visual de AT con múltiples solicitudes.

---

## 7. Diferenciación visual de solicitante

| Tipo de solicitante | Estilo |
|--------------------|--------|
| EDISTRIBUCIÓN REDES DIGITALES S.L.U. | Fondo/texto distintivo (gris oscuro) — principal administrado AT en Andalucía |
| Persona física (particular) | Negrita |
| Resto de compañías | Normal |

La diferenciación se puede derivar de un flag o campo en la entidad `Entidad` del modelo, o de una lista configurable en tablas maestras.

---

## 8. Pendientes de decisión

- [ ] **Migración ANALISIS_SOLICITUD**: ¿Se crea el tipo nuevo en BD o se mantienen los 3 viejos? Afecta al mapeo de SOL/REQ/SUB.
- [ ] **Fase ADMISION_TRAMITE** (id=6): Específica de renovables. ¿Pista propia o agrupada en SOL/REQ/SUB?
- [ ] **Prioridad con múltiples fases abiertas en la misma pista**: se propone el estado más urgente (rojo > … > verde). ¿Correcto o se necesita desglose?
- [ ] **N/A vs vacío**: cuando una pista no aplica al tipo de solicitud, ¿celda vacía, texto "N/A" o icono?
- [ ] **Notas**: ¿campo libre por solicitud, o algo más estructurado (etiquetas, categorías)?
- [ ] **Última comunicación**: ¿se incluye como columna o queda en el detalle del expediente?
- [ ] **Diferenciación visual de solicitante**: ¿flag en tabla `entidades` o lista configurable en maestras?
- [ ] **Prefijo `docs/`** en la línea `Fuente de verdad` de este fichero (actualmente sin prefijo). Corrección menor pendiente.

---

## 9. Próximos pasos

1. Revisar y aprobar este análisis (especialmente §8)
2. Crear script `docs_prueba/seed_listado.py` con los escenarios de §6
3. Implementar `app/services/seguimiento.py`
4. Implementar la vista del listado (issue #169)
5. Vista de auditoría — ver issue #[pendiente]
