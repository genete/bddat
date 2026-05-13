---
id: ADR-003
título: Fusión de REDACTAR y FIRMAR en tarea única ELABORAR
fecha: 2026-05-11
estado: implementada (#370, migración 370_actualizar_tipos_tareas; cerrada en #363)
---

## Decisión
`REDACTAR` y `FIRMAR` se eliminan como tareas atómicas independientes.
Se reemplazan por una sola tarea `ELABORAR` que encapsula borrador + firma.
`documento_producido_id` de `ELABORAR` es siempre el documento firmado.

## Por qué
En la práctica el tramitador nunca persiste un borrador sin firmarlo en el mismo acto.
Modelar dos tareas obligaba a registrar un documento intermedio (borrador) sin valor
administrativo propio: el único documento con efecto jurídico es el firmado.
La separación duplicaba filas en `tramites_tareas` y `documentos` sin aportar trazabilidad útil.

## Cómo implementar
- `ESTRUCTURA_FTT.json` — sección `tareas_atomicas`: eliminar `REDACTAR` y `FIRMAR`; añadir `ELABORAR`
- `ESTRUCTURA_FTT.json` — sección `patrones`: actualizar secuencias B, C, D (REDACTAR→FIRMAR → ELABORAR)
- `ESTRUCTURA_FTT.json` — todos los `tareas_indicativas`: sustituir pares `REDACTAR, FIRMAR` por `ELABORAR`
- Seed `tramites_tareas`: reemplazar filas REDACTAR+FIRMAR por una fila ELABORAR por trámite afectado
- Ver issue #370 para lista completa de artefactos

## Alternativa descartada
Mantener REDACTAR y FIRMAR separadas para modelar delegación (una persona redacta, otra firma).
Descartada: BDDAT no modela delegación de firma en esta versión; añadir esa semántica
requeriría un cambio de modelo más profundo que va más allá de dos tareas adicionales.
