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

### SOLICITUD — padre_id: expediente_id

| evento | tipo (siglas) | Regla | Nivel |
|--------|--------------|-------|-------|
| CREAR | AAP | ¿Ya existe AAP activa en este expediente? | BLOQUEAR |
| CREAR | DESISTIMIENTO | ¿Existe solicitud activa afectable? (SOLICITUD_AFECTADA_ID obligatoria) | BLOQUEAR |
| CREAR | RENUNCIA | ¿Existe solicitud resuelta favorablemente afectable? | BLOQUEAR |
| CREAR | RECURSO | ¿Existe resolución en el expediente? | BLOQUEAR |
| CREAR | RAIPEE_DEFINITIVA | ¿Existe RAIPEE_PREVIA resuelta? | ADVERTIR |
| CERRAR | cualquiera | ¿Existe fase RESOLUCION con fecha_fin y exito=true? | BLOQUEAR |
| BORRAR | cualquiera | ¿Hay tareas NOTIFICAR/PUBLICAR ejecutadas en esta solicitud? | BLOQUEAR |

### FASE — padre_id: solicitud_id

| evento | tipo (codigo) | Regla | Nivel |
|--------|--------------|-------|-------|
| CREAR | INFORMACION_PUBLICA | DR_NO_DUP presente AND figura_ambiental ∉ {AAU,AAUs} | BLOQUEAR |
| CREAR | FIGURA_AMBIENTAL_EXTERNA | figura_ambiental ≠ CA | BLOQUEAR |
| CREAR | AAU_AAUS_INTEGRADA | figura_ambiental ∉ {AAU,AAUs} | BLOQUEAR |
| CREAR | RESOLUCION | CA y sin FIGURA_AMBIENTAL_EXTERNA cerrada con éxito | BLOQUEAR |
| CREAR | RESOLUCION | Sin ANALISIS_TECNICO cerrado (regla interna del servicio) | BLOQUEAR |
| CREAR | CONSULTA_MINISTERIO | Solo instalaciones de competencia compartida | BLOQUEAR |
| CREAR | ADMISION_TRAMITE | Solo generación renovable (tipo_expediente específico) | BLOQUEAR |
| CERRAR | cualquiera | ¿Existe trámite sin fecha_fin en esta fase? | BLOQUEAR |
| BORRAR | cualquiera | ¿Existe tarea con fecha_fin not null en esta fase? | BLOQUEAR |

### TRÁMITE — padre_id: fase_id

| evento | tipo (codigo) | Regla | Nivel | params |
|--------|--------------|-------|-------|--------|
| CREAR | SEPARATAS | DR_ORGANISMO existe para organismo_id | BLOQUEAR | organismo_id |
| CREAR | ANUNCIO_BOE/BOP/PRENSA | Solo en fase INFORMACION_PUBLICA | BLOQUEAR | — |
| CREAR | PUBLICACION_RESOLUCION | ¿Existe ELABORACION_RESOLUCION cerrado con doc? | BLOQUEAR | — |
| CREAR | NOTIFICACION_RESOLUCION | ¿Existe ELABORACION_RESOLUCION cerrado con doc? | BLOQUEAR | — |
| CERRAR | cualquiera | ¿Existe tarea sin fecha_fin en este trámite? | BLOQUEAR | — |
| BORRAR | cualquiera | ¿Existe tarea con fecha_fin not null en este trámite? | BLOQUEAR | — |

### TAREA — padre_id: tramite_id

Las tareas tienen solo 7 tipos genéricos. Sus reglas son de secuencia interna
(independientes del dominio legislativo) y de obligatoriedad de documento.

| evento | tipo (codigo) | Regla | Nivel |
|--------|--------------|-------|-------|
| CREAR | FIRMAR | NOT EXISTS REDACTAR cerrada con doc_producido en este trámite | BLOQUEAR |
| CREAR | NOTIFICAR | NOT EXISTS FIRMAR cerrada con doc_producido en este trámite | BLOQUEAR |
| CREAR | PUBLICAR | NOT EXISTS FIRMAR cerrada con doc_producido en este trámite | BLOQUEAR |
| CERRAR | REDACTAR / FIRMAR / INCORPORAR | doc_producido_id es null | BLOQUEAR |
| CERRAR | NOTIFICAR / PUBLICAR | doc_usado_id es null | BLOQUEAR |
| BORRAR | cualquiera | fecha_fin not null (ya ejecutada) | BLOQUEAR |

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
