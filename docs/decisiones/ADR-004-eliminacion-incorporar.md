---
id: ADR-004
título: Eliminación de la tarea INCORPORAR
fecha: 2026-05-11
estado: implementada (#370, migración 370_actualizar_tipos_tareas; cerrada en #361)
---

## Decisión
`INCORPORAR` se elimina como tarea atómica.
La recepción de un documento externo se modela exclusivamente como `documento_producido_id`
de `ESPERAR_PLAZO`. `ANALIZAR` consume ese documento directamente.

## Por qué
El único rol de `INCORPORAR` era registrar que un documento externo había llegado al pool.
`ESPERAR_PLAZO` ya cumple esa función: su `documento_producido_id` es precisamente el
documento recibido (Caso A) o el `CERT_PLAZO_CUMPLIDO` (Caso B, si vence sin respuesta).
`INCORPORAR` añadía un paso intermedio sin semántica propia, generaba confusión sobre
cuál de las dos tareas "produce" el documento, y obligaba a modelar una tarea cuyo único
efecto era enlazar lo que ya tenía enlace.

## Cómo implementar
- `ESTRUCTURA_FTT.json` — sección `tareas_atomicas`: eliminar `INCORPORAR`
- `ESTRUCTURA_FTT.json` — patrón E (`INCORPORAR → ANALIZAR`): eliminar; `ANALIZAR` solo pasa a ser patrón A
- `ESTRUCTURA_FTT.json` — `habilita_tareas` de `NOTIFICAR` y `ESPERAR_PLAZO`: eliminar referencia a `INCORPORAR`
- `ESTRUCTURA_FTT.json` — todos los `tareas_indicativas`: eliminar `"INCORPORAR"` de cada array
- Seed `tramites_tareas`: eliminar todas las filas con `tipo_tarea = INCORPORAR`
- Ver issue #370 para lista completa de artefactos

## Nota 2026-08-07 (#764) — qué documento es el producido

Revisado el caso de N documentos simultáneos en un mismo acto de recepción: **no exige
cambio de modelo**. Lo que llega de fuera trae siempre un documento que acredita el hecho
y porta su fecha administrativa —registro de entrada o solicitud (presentación electrónica
de la Junta o red estatal), justificante de BandeJA si el remitente es interno, o acuse o
certificado acreditativo si lo esperado es una publicación—, y ése es el `PRODUCIDO`, uno.
Los anexos que acompañan al registro entran al pool y los consume (0..N) el `ANALIZAR`
siguiente, que es donde se incorporan al expediente.

Corolario estructural: todo `ESPERAR_PLAZO` que pueda recibir documentación de terceros
exige un `ANALIZAR` posterior —propio, del trámite receptor hermano, o añadido tras él si
es el último trámite de la fase—. Esta exigencia se comprueba durante el desarrollo
mediante repaso de fase a fase, sin crear issues a futuro, sino sobre la marcha.
Ver `ESTRUCTURA_FTT.json` v6.3 y ADR-010.

## Alternativa descartada
Mantener `INCORPORAR` como tarea opcional ejecutada automáticamente por el sistema
al detectar un documento en el pool. Descartada: la automatización requeriría lógica de
detección que ya existe en `ESPERAR_PLAZO`; duplicar esa lógica en una tarea fantasma
añade complejidad sin ganancia funcional.
