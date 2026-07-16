# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #664 (sesión 2026-07-16, foco ANÁLISIS_SOLICITUD, bloque organización documental ADR-032): `Documento.url` (esquema local) pasa a almacenarse siempre relativa a `FILESYSTEM_BASE` — corrige la regresión no deliberada de `a41c80b` (#180, 2026-03-07), que la había dejado absoluta. `@validates('url')` rechaza ahora ruta absoluta o traversal fuera de la base; nuevo `Documento.ruta_absoluta()` resuelve al momento de uso (usado por `resolver_url()`); escritores (`pool_registrar_rutas`, `api_escritos.generar()`, `generador_cert.py`) guardan relativa — la ruta absoluta se sigue usando para escritura a disco y URI de explorador; lectores (`pool_descargar_documento`, `pool_abrir_en_carpeta`) resuelven vía `ruta_absoluta()`. `abrir_carpeta_expediente` no tocado: no lee `Documento.url`. La única fila real afectada en BD dev (id 1103) queda sin migrar por decisión explícita de Carlos: está referenciada, no se puede borrar por CRUD, y no tiene consecuencia real dejarla con una URL que ya no resuelve. Verificado con suite completa (950 passed) y en navegador (registrar/descargar/abrir documento del pool, generación de certificado de fase con rollback). PR #668 mergeado.

**Próximo:** Foco fijo (2026-07-16): dejar la fase `ANÁLISIS_SOLICITUD` completamente tramitable — interfaz, sistema documental, apertura, detección de documentos, notificación y elaboración — porque establece las bases que usarán el resto de fases. Se avanza alternando grupos de issues de este foco entre Próximo y Hecho hasta completarlo; ver exploración de necesidades/código de la sesión 2026-07-16. Activo ahora (1): **#665** — pool `AT-N/pool/` + convención de carpetas por código de catálogo: servicio de cálculo de ruta ESFTT legible a partir de `tipos_fases.codigo`/`tipos_tramites.codigo`/`tipos_tareas.codigo` (ADR-032 §4; solo cálculo, no mueve nada todavía). Segundo issue del bloque de organización documental (`docs/decisiones/ADR-032-ingesta-almacenamiento-fisico-documentos.md`): #664 (rutas relativas, cerrado, PR #668) desbloqueó #665, que a su vez bloquea a #666 (ingesta multipart al pool) y #667 (mover documento a su carpeta ESFTT al vincularse por primera vez a una tarea) — los cuatro en milestone M2. #572 (ADR-027, pertenencia al EXPEDIENTE) queda confirmado ortogonal a este bloque pero diferido a propósito por Carlos (para probarlo junto al resto), no reactivado. En cola, mismo foco: #441 (seed `catalogo_requerimientos`), #629 (diagnóstico sin representación visible entre ANALIZAR/ELABORAR), #407 (`siglas_escritos`), #657/#658 (UI + `id_remesa` de notificación), #444/#555 (plantillas `.docx` definitivas de esta fase), #630 (hub tramitador/radar huérfanos — depende en parte del bloque #664-#667). Hueco de diseño sin issue, solo anotado: `ESPERAR_PLAZO` no admite N documentos simultáneos en respuesta a un requerimiento (`DISEÑO_ANALISIS_SOLICITUD.md` §5; ADR-010 no lo resolvió). Fuera de foco por decisión explícita: automatización externa de firma/notificación (ADR-021, 0%, la incorporación manual ya funciona) y #644-648 (bugs ajenos a esta fase), aparcados.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
