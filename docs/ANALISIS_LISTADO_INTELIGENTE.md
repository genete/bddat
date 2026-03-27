# Análisis: Listado Inteligente de Expedientes

> Fuente de verdad: `ESTRUCTURA_FTT.json`
> Última sincronización: 2026-03-26

**Issues:** #169 (análisis/infraestructura) · #262 (implementación vista)
**Estado:** Decisiones completas — pendiente de implementación (#262)

---

## 1. Concepto

El listado de expedientes es una **cola de trabajo multi-pista**: cada fila representa una **solicitud** (no un expediente), con varias pistas de seguimiento cuyo estado se deduce automáticamente del árbol ESFTT.

El tramitador gestiona por lotes: filtra por estado de pista y trabaja secuencialmente ese grupo.

**Unidad de fila: solicitud.** El número AT puede repetirse si un expediente tiene varias solicitudes activas simultáneamente. Esa repetición es intencionada y se señaliza visualmente.

### Columnas configurables vía `metadata.json`

Las columnas del listado — incluidas las pistas — se definen en el `metadata.json` del módulo, siguiendo el patrón establecido en el resto de módulos (`app/modules/*/metadata.json`, leído por `app/utils/metadata.py`).

Cada pista es una entrada de tipo `"pista"` con los `tipos_fase` que le corresponden. Cambiar visibilidad, añadir o reordenar columnas = editar el JSON y hacer deploy. No requiere tocar código Python ni plantillas.

**No está expuesto a administración por UI** — lo cambia el programador o el técnico responsable del proyecto. Queda versionado en git. Es la granularidad correcta para este proyecto: los cambios de configuración de columnas son puntuales (detección de necesidad o consenso con usuarios) y no ocurren en producción de forma rutinaria.

---

## 2. Columnas del listado

| Columna (visible) | Clave interna | Tipo | Notas |
|-------------------|---------------|------|-------|
| **Nº AT** | `num_at` | Texto + estilo | Badge si el AT aparece en más de una fila (varias solicitudes activas simultáneas) |
| **SOLICITUD** | `tipo_solicitud` | Texto + color | AAP_AAC, AAE, DUP… El color de fondo codifica el estado global de la solicitud: sin fondo = EN_TRAMITE con pistas en curso; **naranja** = todas las pistas en FIN pero solicitud aún EN_TRAMITE (pendiente de cierre formal); **verde** = solicitud cerrada (RESUELTA / DESISTIDA / ARCHIVADA). Tooltip muestra el estado BD exacto. |
| **FECHA** | `fecha_solicitud` | Fecha | Ordenación principal por defecto desc |
| **TITULAR** | `titular_nombre` | Texto + estilo | Titular directo del expediente. PROMOTOR = negrita; ORGANISMO_PUBLICO = negrita+color; GRAN_DISTRIBUIDORA = gris; resto = normal |
| **PROYECTO** | `proyecto_descripcion` | Texto | Descripción del proyecto |
| **ANÁLISIS** | `pista_analisis` | Estado | Pista de análisis y subsanación (antes SOL/REQ/SUB) |
| **CONSULTAS** | `pista_consultas` | Estado | Pista de separatas e informes |
| **MA** | `pista_ma` | Estado | Pista de tramitación ambiental |
| **IP** | `pista_ip` | Estado | Pista de información pública |
| **RESOLUCIÓN** | `pista_resolucion` | Estado | Pista de resolución |
| **Notas** | — | Texto libre | **DIFERIDO** — ver §8 |
| ~~**Última comunicación**~~ | — | — | **ELIMINADA.** Demasiado complejo de deducir (último doc externo por fecha) y sin utilidad clara en BDDAT. Queda en el detalle del expediente si se necesita. |

---

## 3. Pistas de seguimiento y su mapeo a tipos_fases

| Pista (cabecera visible) | Clave interna | tipos_fases en BD | Obligatoriedad |
|--------------------------|---------------|-------------------|----------------|
| **ANÁLISIS** | `pista_analisis` | `ANALISIS_SOLICITUD` (id=1) | Siempre |
| **CONSULTAS** | `pista_consultas` | `CONSULTAS` (id=5), `CONSULTA_MINISTERIO` (id=2) — y futuras fases de tipo similar | Según tipo solicitud (POS/N/A) |
| **MA** | `pista_ma` | `COMPATIBILIDAD_AMBIENTAL` (id=3), `FIGURA_AMBIENTAL_EXTERNA` (id=7), `AAU_AAUS_INTEGRADA` (id=8) | Según tipo solicitud |
| **IP** | `pista_ip` | `INFORMACION_PUBLICA` (id=6) | Según tipo solicitud (POS/N/A) |
| **RESOLUCIÓN** | `pista_resolucion` | `RESOLUCION` (id=9) | Siempre |

**Inteligencia de columna:** si una solicitud no tiene fases del tipo "principal" de una pista pero sí de un tipo alternativo (p.ej. no tiene `CONSULTAS` pero sí `CONSULTA_MINISTERIO`), la columna muestra el estado de la fase disponible. Si tiene varias fases abiertas en la misma pista, se muestra el estado más urgente; cuando hay más de un elemento en ese mismo nivel de urgencia se añade un contador entre paréntesis (ej: `TRAMITAR (2)`). Las fases cerradas no contribuyen al estado visible.

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

La columna **Prioridad** determina qué estado se muestra cuando hay varias fases abiertas en la misma pista (gana el de menor número). El criterio principal es la accionabilidad: primero los estados en que el tramitador puede actuar (1–4), luego los que esperan a otro (5–9). El contador `TRAMITAR (2)` se añade solo cuando hay >1 elemento en el **mismo estado interno** (misma fila).

| Prioridad | Estado interno | Texto en celda | ANÁLISIS | CONSULTAS | MA | IP | RESOLUCIÓN |
|:---------:|----------------|:--------------:|:--------:|:---------:|:--:|:--:|:----------:|
| 1 | PENDIENTE_TRAMITAR | TRAMITAR | ✓ | ✓ | ✓ | ✓ | ✓ |
| 2 | PENDIENTE_ESTUDIO | ESTUDIAR | ✓ | ✓ | ✓ | ✓ | ✓ |
| 3 | PENDIENTE_REDACTAR | REDACTAR | — | ✓ | ✓ | ✓ | ✓ |
| 4 | PENDIENTE_CERRAR | CERRAR | ✓ | ✓ | ✓ | ✓ | ✓ |
| 5 | PENDIENTE_FIRMA | FIRMAR | ✓ | ✓ | ✓ | ✓ | ✓ |
| 6 | PENDIENTE_NOTIFICAR | NOTIFICAR | ✓ | ✓ | ✓ | — | ✓ |
| 7 | PENDIENTE_PUBLICAR | PUBLICAR | — | — | — | ✓ | ✓ |
| 8 | PENDIENTE_SUBSANAR | SUBSANAR | ✓ | — | — | — | — |
| 9 | PENDIENTE_PLAZOS | PLAZOS | — | ✓ | ✓ | ✓ | — |
| 10 | FIN | FIN | ✓ | ✓ | ✓ | ✓ | ✓ |

> ANÁLISIS no tiene PENDIENTE_REDACTAR porque su primera acción activa es siempre un análisis (ANALIZAR), no una redacción.

### 4.3 Definición de estados

| Estado interno | Texto celda | Color | Cuándo se aplica |
|----------------|:-----------:|-------|------------------|
| PENDIENTE_TRAMITAR | TRAMITAR | rojo | Solicitud sin fases; fase sin trámites; trámite sin tareas creadas; FIRMAR sin borrador; NOTIFICAR/PUBLICAR sin doc firmado; ANALIZAR sin `doc_usado`; REDACTAR sin `doc_usado` ni `doc_producido`; INCORPORAR sin `documentos_tarea`; ESPERAR_PLAZO sin `PLAZO_DIAS` configurado |
| PENDIENTE_ESTUDIO | ESTUDIAR | rojo | ANALIZAR con `doc_usado` pero sin `doc_producido`; ESPERAR_PLAZO vencido; fase con trámites cerrados y `resultado_fase IS NULL` |
| PENDIENTE_REDACTAR | REDACTAR | rojo | REDACTAR con `doc_usado` presente pero sin `doc_producido` |
| PENDIENTE_FIRMA | FIRMAR | amarillo | FIRMAR con borrador presente pero sin doc firmado |
| PENDIENTE_NOTIFICAR | NOTIFICAR | azul | NOTIFICAR con doc firmado pero sin justificante |
| PENDIENTE_PUBLICAR | PUBLICAR | azul | PUBLICAR con doc firmado pero sin justificante |
| PENDIENTE_SUBSANAR | SUBSANAR | gris | ESPERAR_PLAZO activo en pista ANÁLISIS |
| PENDIENTE_PLAZOS | PLAZOS | gris | ESPERAR_PLAZO activo en pistas CONSULTAS, MA o IP |
| PENDIENTE_CERRAR | CERRAR | naranja | Tarea/trámite/fase completos pero sin `fecha_fin` |
| FIN | FIN | verde | Fase finalizada (`fecha_fin IS NOT NULL`) |

### 4.4 Subestados internos por tipo de tarea

| Tarea | Situación | Estado interno | Texto celda | Color |
|-------|-----------|----------------|:-----------:|-------|
| **ANALIZAR** | Sin `doc_usado` | PENDIENTE_TRAMITAR | TRAMITAR | rojo |
| | Con `doc_usado`, sin `doc_producido` | PENDIENTE_ESTUDIO | ESTUDIAR | rojo |
| | Con ambos | PENDIENTE_CERRAR | CERRAR | naranja |
| **REDACTAR** | Sin `doc_usado` ni `doc_producido` | PENDIENTE_TRAMITAR | TRAMITAR | rojo |
| | Con `doc_usado`, sin `doc_producido` | PENDIENTE_REDACTAR | REDACTAR | rojo |
| | Con `doc_producido` (independiente `doc_usado`) | PENDIENTE_CERRAR | CERRAR | naranja |
| **FIRMAR** | Falta borrador | PENDIENTE_TRAMITAR | TRAMITAR | rojo |
| | Tiene borrador, falta firmado | PENDIENTE_FIRMA | FIRMAR | amarillo |
| | Tiene ambos | PENDIENTE_CERRAR | CERRAR | naranja |
| **NOTIFICAR** | Falta doc firmado | PENDIENTE_TRAMITAR | TRAMITAR | rojo |
| | Tiene firmado, falta justificante | PENDIENTE_NOTIFICAR | NOTIFICAR | azul |
| | Tiene ambos | PENDIENTE_CERRAR | CERRAR | naranja |
| **PUBLICAR** | Falta doc firmado | PENDIENTE_TRAMITAR | TRAMITAR | rojo |
| | Tiene firmado, falta justificante | PENDIENTE_PUBLICAR | PUBLICAR | azul |
| | Tiene ambos | PENDIENTE_CERRAR | CERRAR | naranja |
| **ESPERAR_PLAZO** | `PLAZO_DIAS` no configurado (= 0) | PENDIENTE_TRAMITAR | TRAMITAR | rojo |
| | Plazo activo (días restantes > 0) | PENDIENTE_SUBSANAR / PENDIENTE_PLAZOS | SUBSANAR / PLAZOS | gris |
| | Plazo vencido (días restantes ≤ 0) | PENDIENTE_ESTUDIO | ESTUDIAR | rojo |
| **INCORPORAR** | Sin `documentos_tarea` | PENDIENTE_TRAMITAR | TRAMITAR | rojo |
| | Con ≥1 registro | PENDIENTE_CERRAR | CERRAR | naranja |

---

## 5. Algoritmo de deducción jerárquica

El servicio `app/services/seguimiento.py` (ya implementado en #169) deduce el estado de cada pista recorriendo el árbol de abajo arriba. El estado de mayor prioridad prevalece.

**Prioridad de urgencia:** ver tabla §4.2. Dentro del mismo color el orden numérico es determinante. El contador (`TRAMITAR (2)`) se aplica solo cuando >1 elemento está en el mismo estado interno.

El algoritmo se ejecuta para cualquier solicitud visible, independientemente de su `estado` en BD — el filtro `estado_solicitud` del listado determina qué solicitudes se muestran.

```
Para cada pista de la solicitud visible:
  1. Buscar fases del tipo correspondiente en esa solicitud
  2. Si no existe ninguna → celda vacía (N/A) o PENDIENTE_TRAMITAR según tipo solicitud
  3. Si todas cerradas → FIN (verde)
  4. Para cada fase abierta:
     a. No iniciada (fecha_inicio IS NULL) → PENDIENTE_TRAMITAR
     b. Iniciada, sin trámites → PENDIENTE_TRAMITAR
     c. Iniciada, con trámites:
        · Trámite no iniciado → PENDIENTE_TRAMITAR
        · Trámite iniciado, sin tareas → PENDIENTE_TRAMITAR
        · Trámite iniciado, con tareas:
          - Sin tarea activa, todas finalizadas → PENDIENTE_CERRAR
          - Sin tarea activa, hay planificadas → PENDIENTE_TRAMITAR
          - Con tarea activa → aplicar §4.4
        · Todos los trámites cerrados:
          - resultado_fase IS NULL → PENDIENTE_ESTUDIO
          - resultado_fase IS NOT NULL → PENDIENTE_CERRAR
  5. Devolver estado de mayor prioridad (§4.2) entre todas las fases abiertas de esa pista
```

---

## 6. Escenarios de prueba necesarios

Fila = solicitud. El AT puede repetirse. Los valores de pista son **estados internos** (`PENDIENTE_X`); el texto visible en celda se deriva de §4.2. Columnas relevantes para el test:

| AT | Tipo sol. | ANÁLISIS | CONSULTAS | MA | IP | RESOLUCIÓN | Propósito |
|----|-----------|----------|-----------|----|----|------------|-----------|
| T01 | AAP_AAC | PENDIENTE_ESTUDIO | — | — | — | — | ANALIZAR con doc_usado, sin doc_producido |
| T02 | AAP_AAC | PENDIENTE_REDACTAR | — | — | — | — | Requerimiento: doc_usado presente, por redactar |
| T03 | AAP_AAC | PENDIENTE_FIRMA | — | — | — | — | Borrador OK, por firmar |
| T04 | AAP_AAC | PENDIENTE_SUBSANAR | PENDIENTE_PLAZOS | — | — | — | Esperando subsanación + organismo |
| T04 | AAE | PENDIENTE_ESTUDIO | — | — | — | — | Mismo AT, segunda solicitud activa |
| T05 | AAP_AAC | FIN | PENDIENTE_NOTIFICAR | — | — | — | Separata por enviar |
| T06 | AAP_AAC | FIN | FIN | PENDIENTE_PLAZOS | — | — | Esperando dictamen ambiental |
| T07 | AAP_AAC | FIN | FIN | FIN | PENDIENTE_PUBLICAR | — | Anuncio BOP por publicar |
| T08 | AAP_AAC | FIN | FIN | FIN | PENDIENTE_PLAZOS | PENDIENTE_ESTUDIO | IP en alegaciones + resolución en marcha |
| T09 | AAP_AAC | FIN | FIN | FIN | FIN | PENDIENTE_NOTIFICAR | Resolución por notificar |
| T10 | AAP_AAC | FIN | FIN | FIN | FIN | FIN | Todas las pistas en FIN — celda SOLICITUD naranja |
| T11 | AAP_AAC | PENDIENTE_TRAMITAR | — | — | — | — | Sin fases creadas |

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

### 7.2 Campo `tipo_titular` en el modelo `Entidad`

**Ya implementado en #169** (migración `f77b09ef7c1e`). Campo añadido a `app/models/entidad.py`:

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
- Titulares existentes poblados con `'OTRO'` hasta revisión manual
- No requiere tabla maestra separada — los valores son un enum de negocio estable

### 7.3 Diferenciación visual en el listado

| `tipo_titular` | Estilo en columna TITULAR |
|----------------|--------------------------|
| `PROMOTOR` | **Negrita** — máxima visibilidad |
| `ORGANISMO_PUBLICO` | **Negrita** + color distintivo (pendiente de definir paleta exacta) |
| `DISTRIBUIDOR_MENOR` | Normal |
| `GRAN_DISTRIBUIDORA` | Gris — menor urgencia relativa |
| `OTRO` | Normal |

### 7.4 Filtros sin columna visible

Además del filtro por `tipo_titular`, el listado necesita filtros que no tienen columna propia porque son criterios de búsqueda, no información permanente en pantalla:

| Filtro | Fuente en BD | Default | Estado |
|--------|-------------|---------|--------|
| **Estado solicitud** | `solicitud.estado` | EN_TRAMITE | Existe. Las solicitudes cerradas (RESUELTA/DESISTIDA/ARCHIVADA) son historial del tramitador, no cola de trabajo. |
| **Tipo de expediente** | `expediente.tipo_expediente_id` → `tipos_expedientes.tipo` | todos | Existe |
| **Tecnología** | No existe campo en BD | — | Requiere nuevo campo en `Proyecto` — diferido (§8) |
| **Tipo de administrado** | `tipo_titular` en `Entidad` (ver §7.2) | todos | **Hecho** (#169) |

**Tecnología:** útil principalmente para técnicos de generación renovable (solar, eólica, hidráulica, etc.). El `tipo_expediente` "Renovable" agrupa todas las tecnologías sin distinguirlas. Se necesitaría un campo nuevo en `Proyecto` (p.ej. `tecnologia VARCHAR(30)`) o una tabla maestra `tipos_tecnologia`. Pendiente de decisión — ver §8.

---

## 8. Pendientes de decisión

- [x] **Migración `tipo_titular` en `Entidad`** — **DECISIÓN: PROCEDER.** Campo `nullable=True`, default `'OTRO'`. Sin riesgo de datos: todas las entidades existentes quedarán como `OTRO` hasta revisión manual. Valores: `GRAN_DISTRIBUIDORA | DISTRIBUIDOR_MENOR | PROMOTOR | ORGANISMO_PUBLICO | OTRO`. Migración manual con `flask db revision`.
- [ ] **Campo `tecnologia` en `Proyecto`** — **DIFERIDO.** Útil para técnicos de generación renovable, pero no bloquea el listado. Pendiente de decidir si VARCHAR libre, enum fijo o tabla maestra `tipos_tecnologia`. Placeholder en §9.
- [x] **Fase ADMISION_TRAMITE** — **DECISIÓN: ELIMINAR.** Se absorbe completamente en `ANALISIS_SOLICITUD`. Los requisitos específicos de renovables (capacidad legal, técnica, económica, permiso de acceso y conexión) se cubren mediante el checklist de `ANALISIS_DOCUMENTAL`, que varía por `(tipo_instalacion, tipo_solicitud)` — ver `DISEÑO_ANALISIS_SOLICITUD.md §4`. `ANALISIS_ADMISION` y `ALEGACIONES` desaparecen como trámites: ALEGACIONES = REQUERIMIENTO_SUBSANACION (alegar ante inadmisión provisional es idéntico a subsanar un defecto).
- [x] **Prioridad con múltiples fases abiertas en la misma pista** — **DECISIÓN: prioridad numérica completa + contador.** Se muestra el estado de mayor prioridad según la tabla §4.2 (orden numérico, no solo por color — desempata dentro del mismo color). Contador solo cuando >1 elemento está en el **mismo estado interno**: `TRAMITAR (2)`. Ver §4.2.
- [x] **N/A vs vacío** — **DECISIÓN: celda vacía.** Fondo limpio, sin texto ni icono. Ver §3.
- [ ] **Notas** — **DIFERIDO.** En el diseño hoja de cálculo es un campo persistente. Opciones abiertas: (a) tooltip en la columna de la pista, (b) columna recolectora de notas de pistas, (c) campo `observaciones` ya existente en el modelo. Pendiente de decidir presentación.
- [x] **Última comunicación** — **DECISIÓN: ELIMINAR del listado.** Deducir el último documento externo por fecha es demasiado complejo y sin utilidad clara en BDDAT. Si se necesita, queda en el detalle del expediente.
- [x] **Diseño columnas pista (frontend)** — **DECISIÓN: verbo en infinitivo + color de fondo de celda según estado** (paleta §4.1). Sin badge separado — el color de celda ya actúa como indicador visual. Texto fijo por estado: TRAMITAR, ESTUDIAR, REDACTAR, FIRMAR, NOTIFICAR, PUBLICAR, SUBSANAR, PLAZOS, CERRAR, FIN. Contador si hay >1 elemento en el mismo nivel: `TRAMITAR (2)`. Layout: `Nº AT`, `SOLICITUD`, `FECHA` y pistas con `white-space: nowrap`; `TITULAR` y `PROYECTO` con ellipsis controlado; contenedor de tabla con `overflow-x: auto` para pantallas menores o zoom. Referencia 1920×1080.
- [x] **Prefijo `docs/`** en la línea `Fuente de verdad` de este fichero — **DECISIÓN: corrección aplicada.**
- [x] **Ruta de la vista del listado** — **DECISIÓN: `/expedientes/seguimiento/`**, nueva ruta que coexiste con `/expedientes/` (inventario). Audiencias distintas: inventario = buscar/crear; seguimiento = cola de trabajo diario por estado de pista.
- [x] **Filtro por usuario por defecto** — **DECISIÓN: `mis` por defecto**, toggle `todos` accesible para todos los roles (no solo supervisores). Si `mis` devuelve 0 filas → toast informativo, sin fallback automático. Patrón FiltrosListado JS (sin URL params), homogéneo con el resto de vistas.
- [x] **Filtro de estado de solicitud** — **DECISIÓN: `EN_TRAMITE` por defecto.** Opciones: EN_TRAMITE / RESUELTA / DESISTIDA / ARCHIVADA / todos. Las solicitudes no-EN_TRAMITE son historial del tramitador (auditoría propia), no cola de trabajo. No existe filtro separado "activos/finalizadas" para las pistas: el motor de reglas impide cerrar una solicitud si tiene hijos sin cerrar, por tanto las pistas no-FIN solo existen en solicitudes EN_TRAMITE. La distinción visual entre "EN_TRAMITE con pistas activas" y "EN_TRAMITE con todas las pistas en FIN" se resuelve con el color naranja en la celda SOLICITUD — sin campo calculado `fin`.
- [x] **Color de celda SOLICITUD** — **DECISIÓN: codifica el estado global de la solicitud.** Sin fondo = EN_TRAMITE con pistas en curso (las pistas mandan). Naranja = EN_TRAMITE con todas las pistas en FIN (pendiente de cierre formal). Verde = solicitud cerrada (RESUELTA / DESISTIDA / ARCHIVADA). Tooltip con el estado BD exacto para distinguir RESUELTA de DESISTIDA/ARCHIVADA sin añadir columna.

---

## 9. Próximos pasos

1. ~~Revisar y aprobar este análisis (especialmente §8)~~ — en curso
2. ~~Migración `tipo_titular` en `Entidad`~~ — **HECHO** (issue #169). Migración `f77b09ef7c1e`, campo `tipo_titular VARCHAR(30) nullable`. Titulares existentes poblados con `'OTRO'` hasta revisión manual.
3. ~~Crear script `docs_prueba/seed_listado.py` con los escenarios de §6~~ — hecho
4. ~~**Limpieza BD ADMISION_TRAMITE**~~ — **HECHO** (issue #257). JSON actualizado a v5.6. Scripts promovidos a `scripts/`. Sin migración Alembic — los maestros FTT nunca se insertan por migración, siempre por `reset_maestros_ftt.py`.
5. ~~Terminar decisiones §8 pendientes~~ — en curso. Quedan diferidos: `tecnologia` en `Proyecto` y presentación de `Notas`.
5b. ~~**Escribir `scripts/verificar_seed.py`**~~ — **HECHO** (issue #257). 77 checks T01-T11: tipos de fase/trámite/tarea, campos doc_usado/doc_producido/notas. Test de regresión para cuando exista `seguimiento.py`.
6. ~~Implementar `app/services/seguimiento.py`~~ — **HECHO** (issue #169). Servicio `app/services/seguimiento.py` con deducción jerárquica de estados de pista.
7. Implementar la vista `/expedientes/seguimiento/` — **issue #262**
8. Vista de auditoría — ver issue #256
9. **Decidir campo `tecnologia` en `Proyecto`** (diferido de §8): VARCHAR libre, enum fijo o tabla maestra. No bloquea el listado.
10. **Decidir presentación de Notas** (diferido de §8): tooltip en columna de pista, columna recolectora, o `observaciones` del modelo.
