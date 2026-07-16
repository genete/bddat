# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #602 (sesión 2026-07-16, foco ANÁLISIS_SOLICITUD): restaurado el botón "Documentos" en el inspector del expediente (`_inspector_expediente.html`, junto a "Instalaciones", ADR-024 §4.2), enlazando a `expedientes.pool_documentos` — se había perdido al migrar el detalle del expediente al listado+inspector (ADR-024, #543). Los otros dos puntos del alcance del issue no requirieron cambio: el acceso directo desde "Mi trabajo" del administrativo ya existía (`SubirDocumento.jsx`, botón "Abrir gestor") y el breadcrumb de `pool_documentos.html` ya cerraba el ciclo correctamente vía `expedientes.detalle` → `listado_v2(sel=id)`. Verificado en navegador (ciclo inspector↔pool completo). PR #663 mergeado.

**Próximo:** Foco fijo (2026-07-16): dejar la fase `ANÁLISIS_SOLICITUD` completamente tramitable — interfaz, sistema documental, apertura, detección de documentos, notificación y elaboración — porque establece las bases que usarán el resto de fases. Se avanza alternando grupos de issues de este foco entre Próximo y Hecho hasta completarlo; ver exploración de necesidades/código de la sesión 2026-07-16. Activos ahora (1, tarea de definición, ADR-031): **tarea de definición — organización documental completa**: sesión de estudio de alcance amplio (apuntada por Carlos el 2026-07-14) antes de tocar ninguna pieza suelta — cubre pertenencia lógica al EXPEDIENTE (#572/ADR-027), estructura física de carpetas por ESFTT (sin issue — #183 cerró solo con carpeta plana `AT-{numero_at}/`, su propio código se autoseñala "provisional"), filing de subidas manuales (N004), reconstrucción del expediente sin BD (N009) y rutas de filesystem configurables (N021). Sin segundo activo por ahora — decisión explícita de Carlos (2026-07-16): la organización documental es un trabajo grande en sí mismo, no rellenar el cupo artificialmente con otro issue de la cola mientras esa sesión de definición no se aborde. En cola, mismo foco: #441 (seed `catalogo_requerimientos`), #629 (diagnóstico sin representación visible entre ANALIZAR/ELABORAR), #407 (`siglas_escritos`), #657/#658 (UI + `id_remesa` de notificación), #444/#555 (plantillas `.docx` definitivas de esta fase), #630 (hub tramitador/radar huérfanos — depende en parte de la sesión de organización documental). Hueco de diseño sin issue, solo anotado: `ESPERAR_PLAZO` no admite N documentos simultáneos en respuesta a un requerimiento (`DISEÑO_ANALISIS_SOLICITUD.md` §5; ADR-010 no lo resolvió). Fuera de foco por decisión explícita: automatización externa de firma/notificación (ADR-021, 0%, la incorporación manual ya funciona) y #644-648 (bugs ajenos a esta fase), aparcados.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
