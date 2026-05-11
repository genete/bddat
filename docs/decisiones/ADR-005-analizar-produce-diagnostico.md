---
id: ADR-005
título: ANALIZAR siempre produce un documento DIAGNOSTICO
fecha: 2026-05-11
estado: decidida — pendiente de implementar (#370)
---

## Decisión
Toda tarea `ANALIZAR`, sin excepción, produce exactamente un documento de tipo `DIAGNOSTICO`.
`DIAGNOSTICO` es un documento interno de BDDAT con `url = bddat://diagnosticos/{id}`
y `fecha_administrativa = NULL` (no tiene efecto jurídico propio).
`ELABORAR` posterior puede consumirlo como `documento_usado_id` opcional.

## Por qué
Sin `documento_producido_id`, `ANALIZAR` no tiene evidencia de cierre formal: el técnico
puede marcarla completa sin que quede rastro de su decisión. El `DIAGNOSTICO` persiste
la valoración del técnico (favorable / condicionado / desfavorable + observaciones) y
la hace consumible por la tarea `ELABORAR` siguiente, que lo usa como base para redactar
el documento de salida. Garantiza trazabilidad completa del análisis en el expediente.

## Cómo implementar
- Seed `tramites_tareas`: toda fila `ANALIZAR` lleva `documento_producido_tipo = DIAGNOSTICO`
- Modelo `Documento`: `url` para diagnósticos sigue patrón `bddat://diagnosticos/{id}`,
  análogo a `bddat://cert_fin_instruccion/{id}` (#373)
- `fecha_administrativa = NULL` por diseño: el diagnóstico no es un acto administrativo
- `DIAGNOSTICO` ya está catalogado en `docs/referencia/TIPOS_DOCUMENTOS_CATALOGO.md` (#337)
- La URI `bddat://diagnosticos/{id}` sigue el patrón definido en ADR-006 (issue #365)

## Alternativa descartada
Permitir `ANALIZAR` sin documento producido cuando el análisis es implícito o auxiliar.
Descartada: cualquier `ANALIZAR` sin `DIAGNOSTICO` deja la tarea sin cierre verificable,
impide al motor saber si la tarea se completó o se saltó, y elimina la posibilidad de
auditar la decisión técnica que habilitó los pasos siguientes.
