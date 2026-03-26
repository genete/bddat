# Análisis: Listado Inteligente de Expedientes

> Fuente de verdad: `docs/ESTRUCTURA_FTT.json`
> Última sincronización: 2026-03-26

**Issue de referencia:** #169
**Estado:** Borrador — pendiente de revisión

---

## 1. Concepto

El listado de expedientes no es un inventario sino una **cola de trabajo multi-pista**: cada expediente tiene varias pistas de seguimiento independientes y cada pista tiene su propio estado deducido automáticamente del árbol ESFTT.

El tramitador gestiona por lotes: todos los PENDIENTE_ESTUDIO, todos los PENDIENTE_NOTIFICAR, etc.

---

## 2. Pistas de seguimiento y su mapeo a tipos_fases

| Pista | Descripción | tipos_fases en BD |
|-------|-------------|-------------------|
| **SOL/REQ/SUB** | Solicitud principal, requerimientos y subsanaciones | `ADMISIBILIDAD` (id=2) |
| **CONSULTAS** | Separatas a organismos e informes de ministerio | `CONSULTAS` (id=7), `CONSULTA_MINISTERIO` (id=4) — y futuras fases de tipo similar |
| **MA** | Tramitación ambiental | `COMPATIBILIDAD_AMBIENTAL` (id=5), `FIGURA_AMBIENTAL_EXTERNA` (id=9), `AAU_AAUS_INTEGRADA` (id=10) |
| **IP** | Información pública | `INFORMACION_PUBLICA` (id=8) |
| **RESOLUCIÓN** | Redacción y notificación de resolución | `RESOLUCION` (id=11) |

**Inteligencia de columna:** si un expediente no tiene fases de tipo `CONSULTAS` (id=7) pero sí de tipo `CONSULTA_MINISTERIO` (id=4), la columna CONSULTAS muestra el estado de la consulta ministerio. Si tiene ambas, se muestra el estado más urgente. Lo mismo aplica a MA con sus tres tipos. Las fases cerradas no contribuyen al estado visible de la columna (solo las abiertas).

> **Pendiente de decisión:** `ESTRUCTURA_FTT.json` v5.5 define `ANALISIS_SOLICITUD` como código unificado que sustituye a `REGISTRO_SOLICITUD + ADMISIBILIDAD + ANALISIS_TECNICO`. En BD aún existen los tres códigos viejos. Mientras no se migre, la pista SOL/REQ/SUB mapea a `ADMISIBILIDAD`. Ver §6.

---

## 3. Paleta de estados

### 3.1 Semántica de colores

| Color | Significado |
|-------|-------------|
| **Rojo** | Acción pendiente del tramitador |
| **Amarillo** | En espera de algo interno que no depende del tramitador (firma) |
| **Azul** | En espera de un externo que no depende de la administración (publicador, titular) |
| **Naranja** | Listo para cerrar |
| **Gris** | Espera pasiva (plazo legal, respuesta de administrado u organismo) |
| **Verde** | Finalizado |

### 3.2 Estados

| Estado | Color | Cuándo se aplica |
|--------|-------|------------------|
| **PENDIENTE_TRAMITAR** | rojo | Solicitud sin fases; fase sin trámites; trámite sin tareas creadas; FIRMAR sin borrador asociado; NOTIFICAR/PUBLICAR sin doc firmado asociado |
| **PENDIENTE_ESTUDIO** | rojo | Tarea ANALIZAR iniciada sin input o con input pero sin informe producido; tarea INCORPORAR iniciada sin registros en `documentos_tarea`; ESPERAR_PLAZO con `PLAZO_DIAS > 0` y plazo vencido; fase con todos los trámites cerrados y `resultado_fase IS NULL` |
| **PENDIENTE_REDACTAR** | rojo | Tarea REDACTAR iniciada sin borrador; trámite cuya primera tarea es REDACTAR, creado pero no iniciado |
| **PENDIENTE_FIRMA** | amarillo | Tarea FIRMAR con borrador asociado pero sin documento firmado producido |
| **PENDIENTE_NOTIFICAR** | azul | Tarea NOTIFICAR con doc firmado asociado pero sin justificante de notificación |
| **PENDIENTE_PUBLICAR** | azul | Tarea PUBLICAR con doc firmado asociado pero sin justificante de publicación |
| **PENDIENTE_SUBSANAR** | gris | Tarea ESPERAR_PLAZO activa en contexto SOL/REQ/SUB (esperando respuesta del administrado) |
| **PENDIENTE_PLAZOS** | gris | Tarea ESPERAR_PLAZO activa en contexto CONSULTAS, MA o IP (esperando respuesta de organismo o plazo legal) |
| **PENDIENTE_CERRAR** | naranja | Tarea con todos sus docs completos y fecha_fin NULL; trámite con todas las tareas cerradas y fecha_fin NULL; fase con todos los trámites cerrados, `resultado_fase IS NOT NULL` y `fecha_fin IS NULL` |
| **FIN** | verde | Fase finalizada (`fecha_fin IS NOT NULL`) |

### 3.3 Subestados internos por tipo de tarea

#### ANALIZAR
| Situación interna | Estado | Color |
|---|---|---|
| Falta `documento_usado_id` | PENDIENTE_ESTUDIO | rojo |
| Tiene input, falta `documento_producido_id` | PENDIENTE_ESTUDIO | rojo |
| Tiene ambos documentos | PENDIENTE_CERRAR | naranja |

#### REDACTAR
| Situación interna | Estado | Color |
|---|---|---|
| Sin `documento_producido_id` | PENDIENTE_REDACTAR | rojo |
| Con borrador generado | PENDIENTE_CERRAR | naranja |

#### FIRMAR
| Situación interna | Estado | Color |
|---|---|---|
| Falta `documento_usado_id` (el borrador) | PENDIENTE_TRAMITAR | rojo |
| Tiene borrador, falta doc firmado | PENDIENTE_FIRMA | amarillo |
| Tiene ambos | PENDIENTE_CERRAR | naranja |

#### NOTIFICAR
| Situación interna | Estado | Color |
|---|---|---|
| Falta `documento_usado_id` (doc firmado) | PENDIENTE_TRAMITAR | rojo |
| Tiene firmado, falta justificante | PENDIENTE_NOTIFICAR | azul |
| Tiene ambos | PENDIENTE_CERRAR | naranja |

#### PUBLICAR
| Situación interna | Estado | Color |
|---|---|---|
| Falta `documento_usado_id` (doc firmado) | PENDIENTE_TRAMITAR | rojo |
| Tiene firmado, falta justificante | PENDIENTE_PUBLICAR | azul |
| Tiene ambos | PENDIENTE_CERRAR | naranja |

#### ESPERAR_PLAZO
| Situación interna | Estado | Color |
|---|---|---|
| `PLAZO_DIAS = 0` (indefinido) | PENDIENTE_SUBSANAR o PENDIENTE_PLAZOS según pista | gris |
| `PLAZO_DIAS > 0`, plazo activo | PENDIENTE_SUBSANAR o PENDIENTE_PLAZOS según pista | gris |
| `PLAZO_DIAS > 0`, plazo vencido | PENDIENTE_ESTUDIO | rojo |

#### INCORPORAR
| Situación interna | Estado | Color |
|---|---|---|
| Sin registros en `documentos_tarea` | PENDIENTE_ESTUDIO | rojo |
| Con ≥1 registro | PENDIENTE_CERRAR | naranja |

---

## 4. Algoritmo de deducción jerárquica

El servicio `app/services/seguimiento.py` (pendiente de crear) deduce el estado de cada pista recorriendo el árbol de abajo arriba. El estado más urgente prevalece cuando hay varios elementos abiertos.

**Prioridad de urgencia:** rojo > amarillo > azul > naranja > gris > verde

```
Para cada pista del expediente:
  1. Buscar fases del tipo correspondiente en la solicitud EN_TRAMITE
  2. Si no existe ninguna → columna vacía (pista no aplica aún)
  3. Si todas están cerradas (fecha_fin IS NOT NULL) → FIN (verde)
  4. Para cada fase abierta:
     a. Si no iniciada (fecha_inicio IS NULL) → PENDIENTE_TRAMITAR
     b. Si iniciada, sin trámites → PENDIENTE_TRAMITAR
     c. Si iniciada, con trámites:
        - Para cada trámite abierto:
          · Si no iniciado → PENDIENTE_TRAMITAR (o PENDIENTE_REDACTAR
            si su primera tarea es REDACTAR)
          · Si iniciado, sin tareas → PENDIENTE_TRAMITAR
          · Si iniciado, con tareas:
            - Buscar tarea activa (fecha_inicio NOT NULL, fecha_fin NULL)
            - Si no hay tarea activa y todas finalizadas → PENDIENTE_CERRAR
            - Si no hay tarea activa y hay tareas sin iniciar → PENDIENTE_TRAMITAR
            - Si hay tarea activa → aplicar subestado según §3.3
        - Si todos los trámites cerrados:
          · resultado_fase IS NULL → PENDIENTE_ESTUDIO
          · resultado_fase IS NOT NULL → PENDIENTE_CERRAR
  5. Devolver el estado de mayor urgencia entre todas las fases abiertas
```

---

## 5. Escenarios de prueba necesarios

Para testear el listado se necesitan al menos **10 expedientes** que cubran las combinaciones principales de estado. La tabla incluye las 5 pistas; `—` indica que esa pista no tiene fases creadas para ese expediente.

| Exp | SOL/REQ/SUB | CONSULTAS | MA | IP | RESOLUCIÓN | Propósito |
|-----|-------------|-----------|----|----|------------|-----------|
| T01 | PENDIENTE_ESTUDIO | — | — | — | — | ANALIZAR en curso sin input |
| T02 | PENDIENTE_REDACTAR | — | — | — | — | Requerimiento por redactar |
| T03 | PENDIENTE_FIRMA | — | — | — | — | Requerimiento por firmar (borrador OK) |
| T04 | PENDIENTE_SUBSANAR | PENDIENTE_PLAZOS | — | — | — | Esperando subsanación + respuesta organismo |
| T05 | FIN | PENDIENTE_NOTIFICAR | — | — | — | Separata por enviar |
| T06 | FIN | FIN | PENDIENTE_PLAZOS | — | — | Esperando dictamen ambiental |
| T07 | FIN | FIN | FIN | PENDIENTE_PUBLICAR | — | Anuncio BOP por publicar |
| T08 | FIN | FIN | FIN | PENDIENTE_PLAZOS | PENDIENTE_ESTUDIO | IP en alegaciones + resolución por elaborar |
| T09 | FIN | FIN | FIN | FIN | PENDIENTE_NOTIFICAR | Resolución por notificar |
| T10 | PENDIENTE_TRAMITAR | — | — | — | — | Sin responsable — multi-selección SUPERVISOR |

---

## 6. Estructura jerárquica de datos por escenario

Reglas de coherencia con el motor de reglas:
- Tarea iniciada → su trámite debe tener `fecha_inicio` NOT NULL
- Trámite iniciado → su fase debe tener `fecha_inicio` NOT NULL
- Fase finalizada → todos sus trámites con `fecha_fin` NOT NULL
- Solicitud `EN_TRAMITE` → puede tener fases abiertas

### T01 — SOL/REQ/SUB: PENDIENTE_ESTUDIO (ANALIZAR sin input)
```
Solicitud AAP_AAC (EN_TRAMITE)
  └─ Fase ADMISIBILIDAD (inicio=X, fin=NULL)
       └─ Trámite COMPROBACION_ADMISIBILIDAD (inicio=X, fin=NULL)
            └─ Tarea ANALIZAR (inicio=X, fin=NULL, doc_usado=NULL)  ← EN CURSO, falta input
```

### T02 — SOL/REQ/SUB: PENDIENTE_REDACTAR
```
Solicitud AAP_AAC (EN_TRAMITE)
  └─ Fase ADMISIBILIDAD (inicio=X, fin=NULL)
       └─ Trámite REQUERIMIENTO_SUBSANACION (inicio=X, fin=NULL)
            └─ Tarea REDACTAR (inicio=X, fin=NULL, doc_producido=NULL)  ← EN CURSO
```

### T03 — SOL/REQ/SUB: PENDIENTE_FIRMA
```
Solicitud AAP_AAC (EN_TRAMITE)
  └─ Fase ADMISIBILIDAD (inicio=X, fin=NULL)
       └─ Trámite REQUERIMIENTO_SUBSANACION (inicio=X, fin=NULL)
            ├─ Tarea REDACTAR (fin=Y, doc_producido=borrador_id)     ← completada
            └─ Tarea FIRMAR (inicio=Y, fin=NULL, doc_usado=borrador_id, doc_producido=NULL)
                                                                      ← EN CURSO, amarillo
```

### T04 — SOL: PENDIENTE_SUBSANAR + CONSULTAS: PENDIENTE_PLAZOS
```
Solicitud AAP_AAC (EN_TRAMITE)
  ├─ Fase ADMISIBILIDAD (inicio=X, fin=NULL)
  │    └─ Trámite REQUERIMIENTO_SUBSANACION (inicio=X, fin=NULL)
  │         ├─ Tarea REDACTAR (fin=Y)
  │         ├─ Tarea FIRMAR (fin=Z)
  │         ├─ Tarea NOTIFICAR (fin=W)
  │         └─ Tarea ESPERAR_PLAZO (inicio=W, fin=NULL)  ← gris, pista SOL → SUBSANAR
  └─ Fase CONSULTAS (inicio=X, fin=NULL)
       └─ Trámite CONSULTA_SEPARATA (inicio=X, fin=NULL)
            ├─ Tarea NOTIFICAR (fin=V)
            └─ Tarea ESPERAR_PLAZO (inicio=V, fin=NULL)  ← gris, pista CONSULTAS → PLAZOS
```

### T05 — CONSULTAS: PENDIENTE_NOTIFICAR
```
Solicitud AAP_AAC (EN_TRAMITE)
  ├─ Fase ADMISIBILIDAD (inicio=X, fin=Y)  ← cerrada
  └─ Fase CONSULTAS (inicio=X, fin=NULL)
       └─ Trámite CONSULTA_SEPARATA (inicio=X, fin=NULL)
            ├─ Tarea REDACTAR (fin=Y)
            ├─ Tarea FIRMAR (fin=Z)
            └─ Tarea NOTIFICAR (inicio=Z, fin=NULL, doc_usado=firmado_id, doc_producido=NULL)
                                                        ← EN CURSO, azul
```

### T06 — MA: PENDIENTE_PLAZOS
```
Solicitud AAP_AAC (EN_TRAMITE)
  ├─ Fase ADMISIBILIDAD (fin=X)
  ├─ Fase CONSULTAS (fin=X)
  └─ Fase AAU_AAUS_INTEGRADA (inicio=X, fin=NULL)
       └─ Trámite REMISION_MEDIO_AMBIENTE (inicio=X, fin=NULL)
            ├─ Tarea NOTIFICAR (fin=Y)
            └─ Tarea ESPERAR_PLAZO (inicio=Y, fin=NULL, PLAZO_DIAS=0)  ← gris, indefinido
```

### T07 — IP: PENDIENTE_PUBLICAR
```
Solicitud AAP_AAC (EN_TRAMITE)
  ├─ Fase ADMISIBILIDAD (fin=X)
  ├─ Fase CONSULTAS (fin=X)
  ├─ Fase AAU_AAUS_INTEGRADA (fin=X)
  └─ Fase INFORMACION_PUBLICA (inicio=X, fin=NULL)
       └─ Trámite PORTAL_TRANSPARENCIA (inicio=X, fin=NULL)
            ├─ Tarea REDACTAR (fin=Y)
            ├─ Tarea FIRMAR (fin=Z)
            └─ Tarea PUBLICAR (inicio=Z, fin=NULL, doc_usado=firmado_id, doc_producido=NULL)
                                                   ← EN CURSO, azul
```

### T08 — IP: PENDIENTE_PLAZOS + RESOLUCIÓN: PENDIENTE_ESTUDIO
```
Solicitud AAP_AAC (EN_TRAMITE)
  ├─ Fase ADMISIBILIDAD (fin=X)
  ├─ Fase CONSULTAS (fin=X)
  ├─ Fase AAU_AAUS_INTEGRADA (fin=X)
  ├─ Fase INFORMACION_PUBLICA (inicio=X, fin=NULL)
  │    └─ Trámite ANUNCIO_BOP (inicio=X, fin=NULL)
  │         ├─ Tarea PUBLICAR (fin=Y)
  │         └─ Tarea ESPERAR_PLAZO (inicio=Y, fin=NULL, PLAZO_DIAS=20)  ← gris, plazo activo
  └─ Fase RESOLUCION (inicio=X, fin=NULL)
       └─ Trámite ELABORACION_RESOLUCION (inicio=X, fin=NULL)
            └─ Tarea ANALIZAR (inicio=X, fin=NULL, doc_usado=NULL)  ← rojo, falta input
```

### T09 — RESOLUCIÓN: PENDIENTE_NOTIFICAR
```
Solicitud AAP_AAC (EN_TRAMITE)
  ├─ Fase ADMISIBILIDAD (fin=X)
  ├─ Fase CONSULTAS (fin=X)
  ├─ Fase AAU_AAUS_INTEGRADA (fin=X)
  ├─ Fase INFORMACION_PUBLICA (fin=X)
  └─ Fase RESOLUCION (inicio=X, fin=NULL)
       └─ Trámite NOTIFICACION_RESOLUCION (inicio=X, fin=NULL)
            └─ Tarea NOTIFICAR (inicio=X, fin=NULL, doc_usado=firmado_id, doc_producido=NULL)
                                                    ← EN CURSO, azul
```

### T10 — Expediente huérfano: PENDIENTE_TRAMITAR
```
Expediente (responsable_id=NULL)
  └─ Solicitud AAP_AAC (EN_TRAMITE)
       (sin fases creadas)
```

---

## 7. Pendientes de decisión

- [ ] **Migración ANALISIS_SOLICITUD**: ¿Se crea el tipo nuevo en BD y se migran los datos existentes, o se mantienen los 3 viejos? Afecta al mapeo de la pista SOL/REQ/SUB.
- [ ] **Fase ADMISION_TRAMITE** (id=6): Específica de renovables. ¿Pista propia o agrupada en SOL/REQ/SUB?
- [ ] **Prioridad con múltiples fases abiertas en la misma pista**: se propone mostrar el estado más urgente (rojo > amarillo > azul > naranja > gris). ¿Correcto o se necesita desglose?
- [ ] **Cabecera del fichero**: corregir prefijo `docs/` en la línea `Fuente de verdad` (actualmente sin prefijo).

---

## 8. Próximos pasos

1. Revisar y aprobar este análisis (especialmente §7)
2. Crear script `docs_prueba/seed_listado.py` con los 10 expedientes de prueba
3. Implementar `app/services/seguimiento.py`
4. Implementar la vista del listado (issue #169)
