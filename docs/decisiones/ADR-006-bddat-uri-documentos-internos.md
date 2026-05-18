---
id: ADR-006
título: URI bddat:// para documentos internos del sistema en el pool de documentos
fecha: 2026-05-11
estado: implementada (#365)
---

## Decisión
`documentos.url` admite tres esquemas: ruta local, `http(s)://`, y `bddat://`.
Solo los documentos **sin fichero físico** usan `bddat://`. Los tipos que cumplen
esa condición son:

- `DIAGNOSTICO` — resultado estructurado de la tarea ANALIZAR, vive en la tabla
  `diagnosticos` → URI `bddat://diagnosticos/<id>`.
- `CERT_PLAZO_CUMPLIDO` — certificado interno generado por el motor cuando vence
  un plazo, vive en la tabla `certificados` (pending #425) → URI
  `bddat://certificados/<id>`.

`CERT_FIN_INSTRUCCION` sí produce un PDF en disco (vía `generador_cert.py`) y
apunta a ruta local; no usa `bddat://`.

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
- Tabla destino stub: `certificados` → URI `bddat://certificados/<id>` (pending #425;
  hasta entonces el Documento se crea con placeholder `bddat://certificados/0`)
- `ContextoAnalisisDocumental` normalizado para usar `resolver_url()` en lugar de acceso directo ORM
- `app/services/certificados.py` — `crear_cert(tarea)` genera CERT_PLAZO_CUMPLIDO (#362)

## Alternativa descartada
Serializar las decisiones internas como PDF o JSON en disco.
Descartada: genera ficheros sin valor jurídico propio, duplica datos que ya viven en BD,
impide consultas estructuradas sobre el contenido de la decisión y rompe la BD como
fuente de verdad para los datos internos del sistema.
