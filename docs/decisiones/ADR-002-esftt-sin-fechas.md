---
id: ADR-002
título: Ningún elemento ESFTT almacena fechas propias
fecha: 2026-04-19
estado: implementado (migración 95c2e862e8d6)
---

## Decisión
Expediente, Solicitud, Fase, Trámite y Tarea no almacenan fecha_inicio ni fecha_fin.
Las fechas administrativas viven en Documento.fecha_administrativa.
El estado es derivable en tiempo de consulta.

## Por qué
Una fecha duplicada en el modelo ESFTT puede divergir del documento que la porta,
con consecuencias legales. La mera existencia del registro prueba la interacción.

## Cómo está implementado
Campos eliminados en migración 95c2e862e8d6.
FK documento_solicitud_id → documentos.id en Solicitud (migración b7f95d61a7a9).

## Alternativa descartada
Tabla metadatos_fechas para anotar semántica campo a campo.
Descartada al concluir que ningún campo fecha de ESFTT tiene valor administrativo propio.
