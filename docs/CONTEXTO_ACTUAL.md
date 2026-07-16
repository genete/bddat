# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #408 (sesión 2026-07-16, foco ANÁLISIS_SOLICITUD): poblado el primer bloque de `requisitos_documentales` — 8 documentos base y de tasa (Modelo de solicitud, Escrituras de sociedad, CIF/NIF, Poder de representación, Modelo 046, Modelo 909, Justificante de pago, Proyecto técnico), todos universales sin condición. Desbloquea de verdad la regla de motor #582 (`tasa_impagada` dejaba de degradar a `False` por catálogo vacío). Catálogo PARCIAL para desarrollo — pendiente el estudio andaluz completo de documentación requerida por tipo de instalación/solicitud/circunstancia, que se irá completando según necesidad (mismo patrón que `tipos_documentos`/#337). Textos descriptivos con redacción mejorable, pendientes de ajuste manual (commit `7da61aa`). PR #662 mergeado.

**Próximo:** Foco fijo (2026-07-16): dejar la fase `ANÁLISIS_SOLICITUD` completamente tramitable — interfaz, sistema documental, apertura, detección de documentos, notificación y elaboración — porque establece las bases que usarán el resto de fases. Se avanza alternando grupos de issues de este foco entre Próximo y Hecho hasta completarlo; ver exploración de necesidades/código de la sesión 2026-07-16. Activos ahora (2, 1 issue + 1 tarea de definición, ADR-031): **#602** (restaurar botón de navegación al pool documental del expediente, perdido al migrar a ADR-024), y **tarea de definición — organización documental completa**: sesión de estudio de alcance amplio (apuntada por Carlos el 2026-07-14) antes de tocar ninguna pieza suelta — cubre pertenencia lógica al EXPEDIENTE (#572/ADR-027), estructura física de carpetas por ESFTT (sin issue — #183 cerró solo con carpeta plana `AT-{numero_at}/`, su propio código se autoseñala "provisional"), filing de subidas manuales (N004), reconstrucción del expediente sin BD (N009) y rutas de filesystem configurables (N021). En cola tras estos, mismo foco: #441 (seed `catalogo_requerimientos`), #629 (diagnóstico sin representación visible entre ANALIZAR/ELABORAR), #407 (`siglas_escritos`), #657/#658 (UI + `id_remesa` de notificación), #444/#555 (plantillas `.docx` definitivas de esta fase), #630 (hub tramitador/radar huérfanos — depende en parte de la sesión de organización documental). Hueco de diseño sin issue, solo anotado: `ESPERAR_PLAZO` no admite N documentos simultáneos en respuesta a un requerimiento (`DISEÑO_ANALISIS_SOLICITUD.md` §5; ADR-010 no lo resolvió). Fuera de foco por decisión explícita: automatización externa de firma/notificación (ADR-021, 0%, la incorporación manual ya funciona) y #644-648 (bugs ajenos a esta fase), aparcados.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
