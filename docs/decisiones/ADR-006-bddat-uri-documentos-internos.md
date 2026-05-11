---
id: ADR-006
título: URI bddat:// para documentos internos del sistema en el pool de documentos
fecha: 2026-05-11
estado: decidida — pendiente de implementar (#365)
---

## Decisión
`documentos.url` admite tres esquemas: ruta local, `https?://`, y `bddat://`.
Los documentos generados internamente por BDDAT sin fichero físico (DIAGNOSTICO,
CERT_FIN_INSTRUCCION, CERT_PLAZO_CUMPLIDO…) se registran en el pool con una URI
`bddat://<recurso>/<id>` que apunta al registro de BD que los contiene.
El modelo `Documento` añade un helper `resolver_url()` que despacha según el esquema.

## Por qué
`ANALIZAR` y el motor de reglas producen decisiones estructuradas que no son ficheros
administrativos sino registros de BD. Sin un mecanismo de referencia dentro del pool,
esas decisiones no pueden actuar como `documento_usado_id` ni `documento_producido_id`,
lo que rompe la cadena de trazabilidad entre tareas. Asignarles una URI `bddat://`
los incorpora al pool universal sin forzar su serialización a disco y sin cambiar el
tipo de columna (ya es `Text`).

## Cómo implementar
- `documentos.url`: sin cambio de tipo; añadir validación de esquema en el modelo
- Helper `Documento.resolver_url()`: despacha a `open()` / `requests.get()` / ORM según esquema
- Tablas propias por tipo: `diagnosticos`, `cert_fin_instruccion`… con campos estructurados
- `fecha_administrativa = NULL` para todos los documentos `bddat://` (sin efecto jurídico propio)
- Tipos de documento afectados ya catalogados: `DIAGNOSTICO` (#365), `CERT_FIN_INSTRUCCION` (#373),
  `CERT_PLAZO_CUMPLIDO` (#362)
- Ver issue #365 para diseño detallado

## Alternativa descartada
Serializar las decisiones internas como PDF o JSON en disco.
Descartada: genera ficheros sin valor jurídico propio, duplica datos que ya viven en BD,
impide consultas estructuradas sobre el contenido de la decisión y rompe la BD como
fuente de verdad para los datos internos del sistema.
