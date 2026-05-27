---
id: ADR-006
título: URI bddat:// para documentos internos del sistema en el pool de documentos
fecha: 2026-05-11
estado: implementada (#365, enmendada #425)
---

## Decisión
`documentos.url` admite tres esquemas: ruta local, `http(s)://`, y `bddat://`.
Solo los documentos **sin fichero físico** usan `bddat://`. Los tipos que cumplen
esa condición son:

- `DIAGNOSTICO` — resultado estructurado de la tarea ANALIZAR, vive en la tabla
  `diagnosticos` → URI `bddat://diagnosticos/<id>`.
- `CERT_*` — certificados internos generados por el motor, viven en la tabla
  `certificados` → URI `bddat://certificados/<id>`. El tipo concreto se deduce de
  `documento.tipo_documento.codigo`. Tipos implementados o previstos:
    - `CERT_PLAZO_CUMPLIDO` — generado por `crear_cert()` al vencer ESPERAR_PLAZO (#362, #425).
    - `CERT_FIN_INSTRUCCION` — producido al cerrar la fase de instrucción (#373).
    - `CERT_FIN_IP_CONSULTAS` — producido al cerrar IP/consultas (issue futuro).

Los certificados `CERT_*` no generan PDF a disco; el PDF se genera on-demand vía
`GET /expedientes/cert/<cert_id>/pdf` usando reportlab (`app/services/cert_pdf.py`).

El modelo `Documento` añade el helper `resolver_url()` que despacha según el esquema.

## Contrato de resolver_url()
- Ruta local → file object (`open(..., 'rb')`)
- `http(s)://` → `http.client.HTTPResponse` (via `urllib.request.urlopen`)
- `bddat://` → **dict completo** del registro ORM destino (todos los campos del modelo)

Los consumidores reciben el dict completo y extraen los campos que necesiten.
Este contrato evita que cada consumidor reescriba acceso ad hoc al ORM.

## Por qué
`ANALIZAR` produce decisiones estructuradas que no son ficheros administrativos
sino registros de BD. Sin un mecanismo de referencia dentro del pool, esas
decisiones no pueden actuar como `documento_producido` en `documentos_tarea`,
lo que rompe la cadena de trazabilidad. Asignarles una URI `bddat://` los
incorpora al pool universal sin forzar su serialización a disco.

## Cómo está implementado
- `documentos.url`: sin cambio de tipo; `@validates('url')` valida el esquema
  y fuerza `fecha_administrativa = NULL` para `bddat://`
- `Documento.resolver_url()` + `_resolver_bddat()`: implementados en `app/models/documentos.py`
- Tabla destino activa: `diagnosticos` → URI `bddat://diagnosticos/<id>`
- Tabla destino activa: `certificados` → URI `bddat://certificados/<id>` (#425)
- `ContextoAnalisisDocumental` normalizado para usar `resolver_url()` en lugar de acceso directo ORM
- `app/services/certificados.py` — `crear_cert(tarea)` genera CERT_PLAZO_CUMPLIDO (#362, #425)
- `app/services/cert_pdf.py` — genera PDF on-demand por tipo de certificado (#425)

## Alternativa descartada
Serializar las decisiones internas como PDF o JSON en disco.
Descartada: genera ficheros sin valor jurídico propio, duplica datos que ya viven en BD,
impide consultas estructuradas sobre el contenido de la decisión y rompe la BD como
fuente de verdad para los datos internos del sistema.
