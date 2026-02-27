# MOTOR_REGLAS — Arquitectura de diseño

> **Fecha:** 2026-02-27
> Documento derivado del análisis de dos ejemplos reales de tramitación AT en Andalucía.

---

## Decisión de partida

Se abandona la investigación legislativa exhaustiva (Perplexity) como prerequisito.
Motivo: el diseño del mecanismo de evaluación es más urgente que tener todas las reglas.
Las reglas se irán añadiendo progresivamente en producción — una, probarla, iterar.

Lo que sí se hace ahora (Fase 2): colocar hooks en las rutas y modelos ESFTT
con la firma definitiva del evaluador, devolviendo siempre PERMITIDO hasta que
el motor esté implementado en Fase 3.

---

## Principio rector

**Todo está permitido excepto lo expresamente prohibido.**

El motor no define qué está permitido — define qué está prohibido en cada momento.
La iniciativa es siempre del técnico tramitador; el motor valida o informa.
El motor no genera el flujo automáticamente; responde a la pregunta:
"¿Está esto prohibido ahora mismo en estas circunstancias?"

---

## Arquitectura: un solo evaluador, no múltiples motores

Un único evaluador con reglas etiquetadas por evento y entidad.
La diferencia entre "motor de creación" y "motor de cierre" es solo un filtro
`WHERE evento='CREAR'` — no código separado.

---

## Firma del evaluador

Asimetría necesaria entre CREAR y CERRAR/BORRAR:

```python
# CREAR: la entidad aún no existe
evaluar(evento='CREAR', entidad='FASE', tipo_id=8, padre_id=23, params={})

# CERRAR / BORRAR: la entidad ya existe; el motor lee el tipo desde la BD
evaluar(evento='CERRAR', entidad='FASE', entidad_id=45, params={})
```

Retorna: `EvaluacionResult(permitido: bool, nivel: str, mensaje: str, norma: str)`

`params` solo es necesario en un caso conocido: `organismo_id` para SEPARATAS.

---

## Tipos de criterio que emergen de los ejemplos

| Código | Qué evalúa |
|--------|-----------|
| EXISTE_DOCUMENTO_TIPO | ¿Hay documento de tipo X (ej: DR_NO_DUP) en esta solicitud/expediente? |
| VARIABLE_EXPEDIENTE | ¿Campo Y del expediente tiene valor Z? (ej: figura_ambiental = CA) |
| EXISTE_FASE_EXITO | ¿Hay fase de tipo X cerrada con éxito en esta solicitud? |
| EXISTE_DOC_ORGANISMO | ¿Hay DR de tipo X para organismo concreto? |

El motor hace los JOINs internamente subiendo el árbol jerárquico:
TAREA → TRAMITE → FASE → SOLICITUD → EXPEDIENTE.

---

## Declaraciones responsables (DRs)

Son documentos incorporados por el técnico como documentos tipificados individuales.
No se ocultan en zips. El motor las localiza por tipo de documento.
Se integran en el modelo documental existente mediante tabla secundaria
(patrón análogo a DocumentoProyecto), pendiente de definir.

---

## Mapa de (evento, entidad, tipo) con reglas conocidas

**Cómo leer las tablas:**
El motor evalúa la condición descrita. Si es **TRUE → aplica la acción**.
Si es **FALSE → operación permitida** (principio de todo permitido excepto prohibido).

---

### SOLICITUD — padre_id: expediente_id

| evento | tipo (siglas) | Condición (si TRUE → acción) | Acción |
|--------|--------------|------------------------------|--------|
| CREAR | AAP | EXISTS AAP activa en este expediente | BLOQUEAR |
| CREAR | DESISTIMIENTO | NOT EXISTS solicitud activa en este expediente (para afectar) | BLOQUEAR |
| CREAR | RENUNCIA | NOT EXISTS solicitud resuelta favorablemente en este expediente | BLOQUEAR |
| CREAR | RECURSO | NOT EXISTS resolución emitida en este expediente | BLOQUEAR |
| CREAR | RAIPEE_DEFINITIVA | NOT EXISTS RAIPEE_PREVIA resuelta en este expediente | ADVERTIR |
| CERRAR | cualquiera | NOT EXISTS fase RESOLUCION con fecha_fin not null AND exito=true en esta solicitud | BLOQUEAR |
| BORRAR | cualquiera | EXISTS tarea tipo NOTIFICAR o PUBLICAR con fecha_fin not null en esta solicitud | BLOQUEAR |

### FASE — padre_id: solicitud_id

| evento | tipo (codigo) | Condición (si TRUE → acción) | Acción |
|--------|--------------|------------------------------|--------|
| CREAR | INFORMACION_PUBLICA | EXISTS documento tipo DR_NO_DUP en esta solicitud AND figura_ambiental NOT IN {AAU, AAUs} | BLOQUEAR |
| CREAR | FIGURA_AMBIENTAL_EXTERNA | figura_ambiental NOT IN {CA} | BLOQUEAR |
| CREAR | AAU_AAUS_INTEGRADA | figura_ambiental NOT IN {AAU, AAUs} | BLOQUEAR |
| CREAR | RESOLUCION | figura_ambiental = CA AND NOT EXISTS fase FIGURA_AMBIENTAL_EXTERNA con exito=true | BLOQUEAR |
| CREAR | RESOLUCION | NOT EXISTS fase ANALISIS_TECNICO con fecha_fin not null (regla interna del servicio) | BLOQUEAR |
| CREAR | CONSULTA_MINISTERIO | tipo_expediente NOT IN {competencia compartida con Ministerio} | BLOQUEAR |
| CREAR | ADMISION_TRAMITE | tipo_expediente NOT IN {generación renovable} | BLOQUEAR |
| CERRAR | cualquiera | EXISTS trámite con fecha_fin IS NULL en esta fase | BLOQUEAR |
| BORRAR | cualquiera | EXISTS tarea con fecha_fin IS NOT NULL en algún trámite de esta fase | BLOQUEAR |

### TRÁMITE — padre_id: fase_id

| evento | tipo (codigo) | Condición (si TRUE → acción) | Acción | params |
|--------|--------------|------------------------------|--------|--------|
| CREAR | SEPARATAS | EXISTS documento tipo DR_ORGANISMO para organismo_id en esta solicitud | BLOQUEAR | organismo_id |
| CREAR | ANUNCIO_BOE / ANUNCIO_BOP / ANUNCIO_PRENSA | tipo de la fase padre NOT IN {INFORMACION_PUBLICA} | BLOQUEAR | — |
| CREAR | PUBLICACION_RESOLUCION | NOT EXISTS trámite ELABORACION_RESOLUCION con fecha_fin not null AND doc_producido_id not null | BLOQUEAR | — |
| CREAR | NOTIFICACION_RESOLUCION | NOT EXISTS trámite ELABORACION_RESOLUCION con fecha_fin not null AND doc_producido_id not null | BLOQUEAR | — |
| CERRAR | cualquiera | EXISTS tarea con fecha_fin IS NULL en este trámite | BLOQUEAR | — |
| BORRAR | cualquiera | EXISTS tarea con fecha_fin IS NOT NULL en este trámite | BLOQUEAR | — |

### TAREA — padre_id: tramite_id

Las tareas tienen solo 7 tipos genéricos. Sus reglas son de secuencia interna
(independientes del dominio legislativo) y de obligatoriedad de documento.

| evento | tipo (codigo) | Condición (si TRUE → acción) | Acción |
|--------|--------------|------------------------------|--------|
| CREAR | FIRMAR | NOT EXISTS tarea REDACTAR con fecha_fin not null AND doc_producido_id not null en este trámite | BLOQUEAR |
| CREAR | NOTIFICAR | NOT EXISTS tarea FIRMAR con fecha_fin not null AND doc_producido_id not null en este trámite | BLOQUEAR |
| CREAR | PUBLICAR | NOT EXISTS tarea FIRMAR con fecha_fin not null AND doc_producido_id not null en este trámite | BLOQUEAR |
| CERRAR | REDACTAR / FIRMAR / INCORPORAR | doc_producido_id IS NULL | BLOQUEAR |
| CERRAR | NOTIFICAR / PUBLICAR | doc_usado_id IS NULL | BLOQUEAR |
| BORRAR | cualquiera | fecha_fin IS NOT NULL | BLOQUEAR |

---

## Observaciones clave

1. **TAREAS primero:** Sus reglas son las más mecánicas y universales.
   Mejor candidato para implementar en primera iteración del motor.

2. **FASES son el nivel más legislativo:** Aquí viven las excepciones
   de los decretos de simplificación. Requieren el contexto más rico.

3. **El motor sube el árbol:** Una regla de TAREA puede necesitar
   el tipo del TRAMITE padre o el tipo de FASE abuelo. El motor hace
   los JOINs — no se necesita pasar contexto completo en la llamada.

4. **SEPARATAS es el único caso especial:** Es el único donde `params`
   es necesario (organismo_id). Todos los demás casos funcionan
   con (evento, entidad, tipo_id, padre_id/entidad_id) sin extras.

---

## Tablas del motor (pendiente de diseñar en detalle)

```
REGLAS_MOTOR
  id, evento, entidad, tipo_id (nullable=aplica a todos),
  accion (BLOQUEAR|ADVERTIR), mensaje, norma, activa

CONDICIONES_REGLA  (1:N con REGLAS_MOTOR)
  id, regla_id, tipo_criterio, parametros (JSON),
  negacion (bool), operador_con_siguiente (AND|OR)
```

---

## Estados de ESFTT — auditoría de modelos Python

> Revisado contra modelos .py reales, no contra esquema de BD.
> Distinción clave: campo persistido vs. @property calculada al vuelo.

### EXPEDIENTE
Sin campo `estado`, sin `fecha_inicio`/`fecha_fin`. Sin `@property` de estado.
Estado completamente derivado de sus solicitudes — no implementado aún.
El expediente vive mientras tenga solicitudes activas.

**Ciclo de vida:**
El expediente vive junto con el proyecto; su producto son las instalaciones en servicio.
Los expedientes con tramitaciones fallidas se finalizan con resoluciones desestimatorias.
Una vez archivado no tiene sentido en sí mismo — cualquier solicitud nueva tras el archivo
crea un nuevo expediente.

**Instalaciones (mundo aparte):**
Nacen con el proyecto pero una vez en servicio se independizan de él. Tienen vida propia:
cambian de estado por otros expedientes/proyectos posteriores. Sus estados
(solicitada, autorizada, en servicio, cerrada, desmantelada) referencian el
expediente/proyecto/solicitud/resolución que las dejó en ese estado.
No afectan al modelo ESFTT actual.

### SOLICITUD
`estado` es **campo persistido** (varchar, NOT NULL, default `EN_TRAMITE`).
Valores: `EN_TRAMITE`, `RESUELTA`, `DESISTIDA`, `ARCHIVADA`.

**@property ya implementadas:**
- `activa` → `estado == 'EN_TRAMITE'`
- `es_desistimiento_o_renuncia` → `solicitud_afectada_id is not None` *(temporal, ver TODO en modelo)*

**Tipos de solicitud — relación N:M deliberada:**
No hay `tipo_solicitud_id` directo. Los tipos se gestionan en tabla puente `SolicitudTipo`
(modelo `solicitudes_tipos.py`), permitiendo múltiples tipos simultáneos en una sola
solicitud (ej: AAP+AAC+DUP = 3 registros en `solicitudes_tipos`).
El motor de reglas evalúa cada tipo individualmente — diseño ya previsto en el modelo.

**Limitación del campo `estado`:** `RESUELTA` no distingue favorable de desfavorable.
Para reglas que necesiten esa distinción, el motor debe consultar `resultado_fase_id`
de la fase RESOLUCION asociada.

### FASE
`resultado_fase_id` es FK a `tipos_resultados_fases` (no boolean).
Valores: `FAVORABLE`, `FAVORABLE_CONDICIONADO`, `DESFAVORABLE`, `NO_PROCEDE`, `DESISTIDA`, `ARCHIVADA`.

**Estados deducibles** (descritos en docstring, sin `@property` implementada aún):
- `PENDIENTE`: `fecha_inicio IS NULL`
- `EN_CURSO`: `fecha_inicio IS NOT NULL AND fecha_fin IS NULL`
- `COMPLETADA`: `fecha_fin IS NOT NULL`
- `EXITOSA`: `fecha_fin IS NOT NULL AND resultado_fase_id` indica resultado favorable

### TRÁMITE
Sin campo de resultado — solo fechas. Sin `@property` implementada.

**Estados deducibles** (descritos en docstring):
- `PENDIENTE`: `fecha_inicio IS NULL`
- `EN_CURSO`: `fecha_inicio IS NOT NULL AND fecha_fin IS NULL`
- `COMPLETADO`: `fecha_fin IS NOT NULL`

No distingue entre cierre exitoso y no exitoso. Pendiente de decidir si necesita
`resultado_tramite_id` análogo al de FASE.

### TAREA
Sin `@property` implementada. Semántica por tipo documentada en docstring del modelo.

**Estados deducibles:**
- `PENDIENTE`: `fecha_inicio IS NULL`
- `EN_CURSO`: `fecha_inicio IS NOT NULL AND fecha_fin IS NULL`
- `EJECUTADA`: `fecha_fin IS NOT NULL`
- `EJECUTADA_CON_DOC`: `fecha_fin IS NOT NULL AND documento_producido_id IS NOT NULL`

---

## Vocabulario de estados para @property (pendiente de implementar)

El motor referencia nombres de estado, no condiciones SQL crudas.
Las `@property` son el contrato entre el modelo y el motor.
Solo `Solicitud.activa` existe hoy — el resto está pendiente.

| Entidad | @property | Condición |
|---------|-----------|-----------|
| Solicitud | `activa` ✅ | `estado == 'EN_TRAMITE'` |
| Solicitud | `cerrada` ⬜ | `estado in ('RESUELTA','DESISTIDA','ARCHIVADA')` |
| Solicitud | `resuelta_favorable` ⬜ | `estado == 'RESUELTA'` AND fase RESOLUCION con resultado favorable |
| Fase | `planificada` ⬜ | `fecha_inicio is None` |
| Fase | `en_curso` ⬜ | `fecha_inicio is not None and fecha_fin is None` |
| Fase | `cerrada` ⬜ | `fecha_fin is not None` |
| Fase | `cerrada_favorable` ⬜ | `fecha_fin is not None and resultado_fase.codigo in ('FAVORABLE','FAVORABLE_CONDICIONADO')` |
| Tramite | `en_curso` ⬜ | `fecha_fin is None` |
| Tramite | `cerrado` ⬜ | `fecha_fin is not None` |
| Tarea | `pendiente` ⬜ | `fecha_inicio is None` |
| Tarea | `en_curso` ⬜ | `fecha_inicio is not None and fecha_fin is None` |
| Tarea | `ejecutada` ⬜ | `fecha_fin is not None` |
| Tarea | `ejecutada_con_doc` ⬜ | `fecha_fin is not None and documento_producido_id is not None` |

✅ implementada · ⬜ pendiente (se añadirán antes de implementar el motor)

---

## Pendiente de sesión

- Actualizar GuiaGeneralNueva: `exito` (bool) → `resultado_fase_id` (FK a tipos_resultados_fases)
- Decidir si TRÁMITE necesita `resultado_tramite_id` análogo al de FASE
- Decidir si EXPEDIENTE necesita `@property estado` explícito o derivado de solicitudes
- Añadir `@property` de estado a FASE, TRÁMITE y TAREA antes de implementar el motor
- Definir tabla secundaria para tipificar documentos (DRs y otros)
- Diseño detallado de REGLAS_MOTOR y CONDICIONES_REGLA con ejemplos concretos
- Decidir dónde vive `figura_ambiental` en el modelo (expediente, solicitud o proyecto)
