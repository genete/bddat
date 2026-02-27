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

## Pendiente de sesión

- Definir tabla secundaria para tipificar documentos (DRs y otros)
- Diseño detallado de REGLAS_MOTOR y CONDICIONES_REGLA con ejemplos concretos
- Decidir dónde vive `figura_ambiental` en el modelo (expediente, solicitud o proyecto)
