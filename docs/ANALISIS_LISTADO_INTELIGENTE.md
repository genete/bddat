# Análisis: Listado Inteligente de Expedientes

> Fuente de verdad: `ESTRUCTURA_FTT.json`
> Última sincronización: 2026-03-26

**Issue de referencia:** #169
**Estado:** Borrador — pendiente de revisión

---

## 1. Concepto y decisiones de arquitectura

### Columnas configurables vía `metadata.json`

Las columnas del listado — incluidas las pistas — se definen en el `metadata.json` del módulo, siguiendo el patrón establecido en el resto de módulos (`app/modules/*/metadata.json`, leído por `app/utils/metadata.py`).

Cada pista es una entrada de tipo `"pista"` con los `tipos_fase` que le corresponden. Cambiar visibilidad, añadir o reordenar columnas = editar el JSON y hacer deploy. No requiere tocar código Python ni plantillas.

**No está expuesto a administración por UI** — lo cambia el programador o el técnico responsable del proyecto. Queda versionado en git. Es la granularidad correcta para este proyecto: los cambios de configuración de columnas son puntuales (detección de necesidad o consenso con usuarios) y no ocurren en producción de forma rutinaria.

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
| ~~**Última comunicación**~~ | — | **ELIMINADA.** Demasiado complejo de deducir (último doc externo por fecha) y sin utilidad clara en BDDAT. Queda en el detalle del expediente si se necesita. |

---

## 3. Pistas de seguimiento y su mapeo a tipos_fases

| Pista | tipos_fases en BD | Obligatoriedad |
|-------|-------------------|----------------|
| **SOL/REQ/SUB** | `ANALISIS_SOLICITUD` (id=1) | Siempre |
| **CONSULTAS** | `CONSULTAS` (id=5), `CONSULTA_MINISTERIO` (id=2) — y futuras fases de tipo similar | Según tipo solicitud (POS/N/A) |
| **MA** | `COMPATIBILIDAD_AMBIENTAL` (id=3), `FIGURA_AMBIENTAL_EXTERNA` (id=7), `AAU_AAUS_INTEGRADA` (id=8) | Según tipo solicitud |
| **IP** | `INFORMACION_PUBLICA` (id=6) | Según tipo solicitud (POS/N/A) |
| **RESOLUCIÓN** | `RESOLUCION` (id=9) | Siempre |

**Inteligencia de columna:** si una solicitud no tiene fases del tipo "principal" de una pista pero sí de un tipo alternativo (p.ej. no tiene `CONSULTAS` pero sí `CONSULTA_MINISTERIO`), la columna muestra el estado de la fase disponible. Si tiene varias fases abiertas en la misma pista, se muestra el estado más urgente; cuando hay más de un elemento en ese mismo nivel de urgencia se añade un contador entre paréntesis (ej: `rojo(2)`). Las fases cerradas no contribuyen al estado visible.

**Columna vacía (N/A):** si el tipo de solicitud hace que una pista sea no aplicable (p.ej. AAC no tiene IP), la celda aparece vacía — fondo limpio, sin texto ni icono. Diferente a FIN (verde).

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

## 7. Clasificación de administrados, prioridad y filtros

### 7.1 Motivación

Con 170+ solicitudes activas simultáneas, el listado puede ocultar casos urgentes entre el volumen masivo de la gran distribuidora. La diferenciación visual y los filtros por tipo de administrado permiten al tramitador no perder de vista los casos de mayor impacto social o político:

| `tipo_titular` | Por qué priorizar | Notas |
|----------------|-------------------|-------|
| **PROMOTOR** | Instalaciones cedidas o persona física — bloquean entrega de viviendas, apertura de negocios, instalaciones propias sin recursos de seguimiento | Incluye distribución cedida. Un ayuntamiento que promueve una instalación es ORGANISMO_PUBLICO, no PROMOTOR |
| **ORGANISMO_PUBLICO** | Presión política real — ayuntamientos, Junta de Andalucía, AGE, puertos del Estado | Políticamente sensible independientemente de si promueven o solo son titulares |
| **DISTRIBUIDOR_MENOR** | Eléctricas pequeñas — su viabilidad puede depender del expediente | |
| **GRAN_DISTRIBUIDORA** | Volumen masivo (EDISTRIBUCIÓN…) — tiene recursos para absorber tiempos | |
| **OTRO** | Resto | |

La prioridad se deriva del tipo — no se almacena un número en BD. La lógica puede evolucionar sin migración.

### 7.2 Campo propuesto en el modelo `Entidad`

El modelo actual (`app/models/entidad.py`) tiene roles booleanos (`rol_titular`, `rol_consultado`, `rol_publicador`) pero **no tiene ningún campo que clasifique el tipo de administrado**. Se propone añadir:

```python
tipo_titular = db.Column(
    db.String(30),
    nullable=True,
    comment='Categoría del administrado cuando actúa como titular. '
            'NULL para entidades sin rol_titular. '
            'Valores: GRAN_DISTRIBUIDORA | DISTRIBUIDOR_MENOR | '
            'PROMOTOR | ORGANISMO_PUBLICO | OTRO'
)
```

- `NULL` para entidades que no son titulares (`rol_titular=False`)
- Requiere migración manual (`flask db revision`)
- No requiere tabla maestra separada — los valores son un enum de negocio estable

### 7.3 Diferenciación visual en el listado

| `tipo_titular` | Estilo en columna Solicitante |
|----------------|-------------------------------|
| `PROMOTOR` | **Negrita** — máxima visibilidad |
| `ORGANISMO_PUBLICO` | **Negrita** + color distintivo (pendiente de definir) |
| `DISTRIBUIDOR_MENOR` | Normal |
| `GRAN_DISTRIBUIDORA` | Gris — menor urgencia relativa |
| `OTRO` | Normal |

### 7.4 Filtros sin columna visible

Además del filtro por `tipo_titular`, el listado necesita filtros que no tienen columna propia porque son criterios de búsqueda, no información permanente en pantalla:

| Filtro | Fuente en BD | Estado |
|--------|-------------|--------|
| **Tipo de expediente** | `expediente.tipo_expediente_id` → `tipos_expedientes.tipo` | Existe |
| **Tecnología** | No existe campo en BD | Requiere nuevo campo en `Proyecto` |
| **Tipo de administrado** | `tipo_titular` en `Entidad` (ver §7.2) | Requiere migración |

**Tecnología:** útil principalmente para técnicos de generación renovable (solar, eólica, hidráulica, etc.). El `tipo_expediente` "Renovable" agrupa todas las tecnologías sin distinguirlas. Se necesitaría un campo nuevo en `Proyecto` (p.ej. `tecnologia VARCHAR(30)`) o una tabla maestra `tipos_tecnologia`. Pendiente de decisión — ver §8.

---

## 8. Pendientes de decisión

- [x] **Migración `tipo_titular` en `Entidad`** — **DECISIÓN: PROCEDER.** Campo `nullable=True`, default `'OTRO'`. Sin riesgo de datos: todas las entidades existentes quedarán como `OTRO` hasta revisión manual. Valores: `GRAN_DISTRIBUIDORA | DISTRIBUIDOR_MENOR | PROMOTOR | ORGANISMO_PUBLICO | OTRO`. Migración manual con `flask db revision`.
- [ ] **Campo `tecnologia` en `Proyecto`** — **DIFERIDO.** Útil para técnicos de generación renovable, pero no bloquea el listado. Pendiente de decidir si VARCHAR libre, enum fijo o tabla maestra `tipos_tecnologia`. Placeholder en §9.
- [x] **Fase ADMISION_TRAMITE** — **DECISIÓN: ELIMINAR.** Se absorbe completamente en `ANALISIS_SOLICITUD`. Los requisitos específicos de renovables (capacidad legal, técnica, económica, permiso de acceso y conexión) se cubren mediante el checklist de `ANALISIS_DOCUMENTAL`, que varía por `(tipo_instalacion, tipo_solicitud)` — ver `DISEÑO_ANALISIS_SOLICITUD.md §4`. `ANALISIS_ADMISION` y `ALEGACIONES` desaparecen como trámites: ALEGACIONES = REQUERIMIENTO_SUBSANACION (alegar ante inadmisión provisional es idéntico a subsanar un defecto).
- [x] **Prioridad con múltiples fases abiertas en la misma pista** — **DECISIÓN: estado más urgente con contador.** Se muestra el color más urgente presente (rojo > amarillo > azul > naranja > gris > verde). Cuando hay más de un elemento en ese nivel se añade un contador: `rojo(2)`. Ver §3.
- [x] **N/A vs vacío** — **DECISIÓN: celda vacía.** Fondo limpio, sin texto ni icono. Ver §3.
- [ ] **Notas** — **DIFERIDO.** En el diseño hoja de cálculo es un campo persistente. Opciones abiertas: (a) tooltip en la columna de la pista, (b) columna recolectora de notas de pistas, (c) campo `observaciones` ya existente en el modelo. Pendiente de decidir presentación.
- [x] **Última comunicación** — **DECISIÓN: ELIMINAR del listado.** Deducir el último documento externo por fecha es demasiado complejo y sin utilidad clara en BDDAT. Si se necesita, queda en el detalle del expediente.
- [x] **Diseño columnas pista (frontend)** — **DECISIÓN: texto abreviado o nombre completo cuando quepa, con color de fondo/texto según estado.** Las 5 columnas de pista deben ser compactas con `white-space: nowrap`. Sin badge separado — el color de celda ya actúa como indicador visual. El resto de columnas: `Nº AT` y `Tipo solicitud` también `nowrap`; `Solicitante` y `Proyecto` con ellipsis controlado; contenedor de tabla con `overflow-x: auto` para scroll horizontal.
- [x] **Prefijo `docs/`** en la línea `Fuente de verdad` de este fichero — **DECISIÓN: corrección aplicada.**

---

## 9. Próximos pasos

1. ~~Revisar y aprobar este análisis (especialmente §8)~~ — en curso
2. ~~Migración `tipo_titular` en `Entidad`~~ — **DECIDIDA** (§8). Pendiente de ejecutar: `flask db revision` manual, campo `tipo_titular VARCHAR(30) nullable` con default `'OTRO'`, poblar entidades existentes.
3. ~~Crear script `docs_prueba/seed_listado.py` con los escenarios de §6~~ — hecho
4. **Ejecutar limpieza BD por decisión ADMISION_TRAMITE:** borrar `tipos_fases` id=4, `tipos_tramites` ids 8 y 9, pares `fases_tramites` (4,8) y (4,9). Eliminar regla del motor `CREAR FASE ADMISION_TRAMITE` de `DISEÑO_MOTOR_REGLAS.md`. Actualizar `seed_listado.py`.
5. ~~Terminar decisiones §8 pendientes~~ — en curso. Quedan diferidos: `tecnologia` en `Proyecto` y presentación de `Notas`.
6. Implementar `app/services/seguimiento.py`
7. Implementar la vista del listado (issue #169)
8. Vista de auditoría — ver issue #256
9. **Decidir campo `tecnologia` en `Proyecto`** (diferido de §8): VARCHAR libre, enum fijo o tabla maestra. No bloquea el listado.
10. **Decidir presentación de Notas** (diferido de §8): tooltip en columna de pista, columna recolectora, o `observaciones` del modelo.
