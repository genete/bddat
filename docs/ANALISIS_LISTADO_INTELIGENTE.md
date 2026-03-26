# Análisis: Listado Inteligente de Expedientes

> Fuente de verdad: `ESTRUCTURA_FTT.json`
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
| **CONSULTAS** | Separatas a organismos | `CONSULTAS` (id=7), `CONSULTA_MINISTERIO` (id=4), `COMPATIBILIDAD_AMBIENTAL` (id=5), `FIGURA_AMBIENTAL_EXTERNA` (id=9), `AAU_AAUS_INTEGRADA` (id=10) |
| **IP** | Información pública | `INFORMACION_PUBLICA` (id=8) |
| **RESOLUCIÓN** | Redacción y notificación de resolución | `RESOLUCION` (id=11) |

> **Pendiente de decisión:** `ESTRUCTURA_FTT.json` v5.5 define `ANALISIS_SOLICITUD` como código unificado que sustituye a `REGISTRO_SOLICITUD + ADMISIBILIDAD + ANALISIS_TECNICO`. En BD aún existen los tres códigos viejos. Mientras no se migre, la pista SOL/REQ/SUB mapea a `ADMISIBILIDAD`. Ver §6.

---

## 3. Deducción de estados de pista

El servicio `app/services/seguimiento.py` (pendiente de crear) lee la tarea **en curso** (fecha_inicio NOT NULL, fecha_fin NULL) dentro de las fases relevantes para cada pista:

| Tarea en curso | Estado deducido |
|----------------|-----------------|
| `ANALIZAR` | **PENDIENTE_ESTUDIO** |
| `REDACTAR` | **PENDIENTE_REDACTAR** |
| `FIRMAR` | **PENDIENTE_FIRMA** |
| `NOTIFICAR` | **PENDIENTE_NOTIFICAR** |
| `PUBLICAR` | **PENDIENTE_PUBLICAR** |
| `ESPERAR_PLAZO` tras `NOTIFICAR` completada | **PENDIENTE_SUBSANAR** (espera del administrado) |
| `ESPERAR_PLAZO` en otros contextos | **PENDIENTE_PLAZOS** (plazo legal u organismo) |
| `INCORPORAR` en curso | **PENDIENTE_PLAZOS** |
| Fase abierta sin tarea en curso | **PENDIENTE_ESTUDIO** (nadie ha dado el siguiente paso) |
| Sin fase de este tipo, o todas cerradas | **FIN** |

**Colores en UI:**
- Rojo: PENDIENTE_ESTUDIO / REDACTAR / FIRMA / NOTIFICAR / PUBLICAR → acción del tramitador
- Gris: PENDIENTE_SUBSANAR / PENDIENTE_PLAZOS → esperando a otro
- Sin color: FIN

---

## 4. Escenarios de prueba necesarios

Para testear el listado se necesitan al menos **10 expedientes** que cubran todas las combinaciones de estado:

| Exp | SOL/REQ/SUB | CONSULTAS | IP | RESOLUCIÓN | Propósito |
|-----|-------------|-----------|----|-----------|----|
| T01 | PENDIENTE_ESTUDIO | — | — | — | Análisis documental por hacer |
| T02 | PENDIENTE_REDACTAR | — | — | — | Requerimiento por redactar |
| T03 | PENDIENTE_FIRMA | — | — | — | Requerimiento por firmar |
| T04 | PENDIENTE_SUBSANAR | PENDIENTE_PLAZOS | — | — | Esperando subsanación + respuesta organismo |
| T05 | FIN | PENDIENTE_NOTIFICAR | — | — | Separata por enviar |
| T06 | FIN | FIN | PENDIENTE_PUBLICAR | — | Anuncio BOP/BOE por publicar |
| T07 | FIN | FIN | PENDIENTE_PLAZOS | PENDIENTE_ESTUDIO | IP en alegaciones + resolución por elaborar |
| T08 | FIN | FIN | FIN | PENDIENTE_NOTIFICAR | Resolución por notificar |
| T09 | FIN | FIN | FIN | FIN | Expediente resuelto (solicitud RESUELTA) |
| T10 | PENDIENTE_ESTUDIO | — | — | — | Sin responsable — multi-selección SUPERVISOR |

---

## 5. Estructura jerárquica de datos por escenario

Reglas de coherencia con el motor de reglas:
- Tarea iniciada → su trámite debe tener `fecha_inicio` NOT NULL
- Trámite iniciado → su fase debe tener `fecha_inicio` NOT NULL
- Fase finalizada → todos sus trámites con `fecha_fin` NOT NULL
- Solicitud `EN_TRAMITE` → puede tener fases abiertas

### T01 — SOL/REQ/SUB: PENDIENTE_ESTUDIO
```
Solicitud AAP_AAC (EN_TRAMITE)
  └─ Fase ADMISIBILIDAD (inicio=X, fin=NULL)
       └─ Trámite COMPROBACION_ADMISIBILIDAD (inicio=X, fin=NULL)
            └─ Tarea ANALIZAR (inicio=X, fin=NULL)  ← EN CURSO
```

### T02 — SOL/REQ/SUB: PENDIENTE_REDACTAR
```
Solicitud AAP_AAC (EN_TRAMITE)
  └─ Fase ADMISIBILIDAD (inicio=X, fin=NULL)
       └─ Trámite REQUERIMIENTO_SUBSANACION (inicio=X, fin=NULL)
            └─ Tarea REDACTAR (inicio=X, fin=NULL)  ← EN CURSO
```

### T03 — SOL/REQ/SUB: PENDIENTE_FIRMA
```
Solicitud AAP_AAC (EN_TRAMITE)
  └─ Fase ADMISIBILIDAD (inicio=X, fin=NULL)
       └─ Trámite REQUERIMIENTO_SUBSANACION (inicio=X, fin=NULL)
            ├─ Tarea REDACTAR (inicio=X, fin=Y)     ← completada
            └─ Tarea FIRMAR (inicio=Y, fin=NULL)     ← EN CURSO
```

### T04 — SOL: PENDIENTE_SUBSANAR + CONSULTAS: PENDIENTE_PLAZOS
```
Solicitud AAP_AAC (EN_TRAMITE)
  ├─ Fase ADMISIBILIDAD (inicio=X, fin=NULL)
  │    └─ Trámite REQUERIMIENTO_SUBSANACION (inicio=X, fin=NULL)
  │         ├─ Tarea REDACTAR (fin=Y)
  │         ├─ Tarea FIRMAR (fin=Z)
  │         ├─ Tarea NOTIFICAR (fin=W)
  │         └─ Tarea ESPERAR_PLAZO (inicio=W, fin=NULL)  ← EN CURSO (tras NOTIFICAR → SUBSANAR)
  └─ Fase CONSULTAS (inicio=X, fin=NULL)
       └─ Trámite SEPARATAS (inicio=X, fin=NULL)
            ├─ Tarea NOTIFICAR (fin=V)
            └─ Tarea ESPERAR_PLAZO (inicio=V, fin=NULL)  ← EN CURSO (organismo)
```

### T05 — CONSULTAS: PENDIENTE_NOTIFICAR
```
Solicitud AAP_AAC (EN_TRAMITE)
  ├─ Fase ADMISIBILIDAD (inicio=X, fin=Y)   ← cerrada (SOL=FIN)
  └─ Fase CONSULTAS (inicio=X, fin=NULL)
       └─ Trámite SEPARATAS (inicio=X, fin=NULL)
            ├─ Tarea REDACTAR (fin=Y)
            ├─ Tarea FIRMAR (fin=Z)
            └─ Tarea NOTIFICAR (inicio=Z, fin=NULL)  ← EN CURSO
```

### T06 — IP: PENDIENTE_PUBLICAR
```
Solicitud AAP_AAC (EN_TRAMITE)
  ├─ Fase ADMISIBILIDAD (fin=X)    ← cerrada
  ├─ Fase CONSULTAS (fin=X)        ← cerrada
  └─ Fase INFORMACION_PUBLICA (inicio=X, fin=NULL)
       └─ Trámite PORTAL_TRANSPARENCIA (inicio=X, fin=NULL)
            ├─ Tarea REDACTAR (fin=Y)
            ├─ Tarea FIRMAR (fin=Z)
            └─ Tarea PUBLICAR (inicio=Z, fin=NULL)  ← EN CURSO
```

### T07 — IP: PENDIENTE_PLAZOS + RESOLUCIÓN: PENDIENTE_ESTUDIO
```
Solicitud AAP_AAC (EN_TRAMITE)
  ├─ Fase ADMISIBILIDAD (fin=X)
  ├─ Fase CONSULTAS (fin=X)
  ├─ Fase INFORMACION_PUBLICA (inicio=X, fin=NULL)
  │    └─ Trámite ANUNCIO_BOP (inicio=X, fin=NULL)
  │         ├─ Tarea PUBLICAR (fin=Y)
  │         └─ Tarea ESPERAR_PLAZO (inicio=Y, fin=NULL)  ← EN CURSO (alegaciones)
  └─ Fase RESOLUCION (inicio=X, fin=NULL)
       └─ Trámite ELABORACION_RESOLUCION (inicio=X, fin=NULL)
            └─ Tarea ANALIZAR (inicio=X, fin=NULL)  ← EN CURSO
```

### T08 — RESOLUCIÓN: PENDIENTE_NOTIFICAR
```
Solicitud AAP_AAC (EN_TRAMITE)
  ├─ Fase ADMISIBILIDAD (fin=X)
  ├─ Fase CONSULTAS (fin=X)
  ├─ Fase INFORMACION_PUBLICA (fin=X)
  └─ Fase RESOLUCION (inicio=X, fin=NULL)
       └─ Trámite NOTIFICACION_RESOLUCION (inicio=X, fin=NULL)
            └─ Tarea NOTIFICAR (inicio=X, fin=NULL)  ← EN CURSO
```

### T09 — Expediente resuelto
```
Solicitud AAP_AAC (RESUELTA)
  └─ todas las fases cerradas
```

### T10 — Expediente huérfano (sin responsable)
Igual que T01 pero con `expediente.responsable_id = NULL`.

---

## 6. Pendientes de decisión

- [ ] **Migración ANALISIS_SOLICITUD**: ¿Se crea el tipo nuevo en BD y se migran los datos existentes, o se mantienen los 3 viejos hasta una fase de limpieza? Afecta al mapeo de la pista SOL/REQ/SUB.
- [ ] **Fase ADMISION_TRAMITE**: Es específica de renovables (generación). ¿Tiene pista propia en el listado o queda agrupada en SOL/REQ/SUB?
- [ ] **Estado "sin tarea en curso, fase abierta"**: ¿Cuenta como PENDIENTE_ESTUDIO o como un estado diferente (p.ej. SIN_INICIAR)?
- [ ] **Múltiples fases CONSULTAS abiertas simultáneamente**: ¿El estado de la pista es el "peor" (más urgente) de todas, o se muestran varias columnas?

---

## 7. Próximos pasos

1. Revisar y aprobar este análisis (especialmente §6)
2. Crear script `docs_prueba/seed_listado.py` con los 10 expedientes
3. Implementar `app/services/seguimiento.py`
4. Implementar la vista del listado (issue #169)
