# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** Prototipo y librería de parseo del justificante de notificación Notifica-PNT (sesión 2026-07-16): #655 entrega `app/services/parser_justificante_notifica.py` — parsea PDF y ZIP (Informe.pdf + InformeENI.xml) y devuelve estado/resultado/fechas en JSON, con cotejo de coherencia PDF↔XML (`coherente_con_xml`); validado contra justificantes reales, sin integración en interfaz todavía (PR #656 mergeado). Necesidad nueva N084 (ninguna necesidad existente cubría extracción de datos de un justificante externo — alta formal en `DETALLE_NECESIDADES_BDDAT.md` pendiente, ver ADR-031 §7). Abiertos como continuación, sin promover a Próximo: #657 (UI para registrar resultado — subida al pool / tarea NOTIFICAR), #658 (persistir `id_remesa` para cotejar justificante contra expediente), #659 (diseño de automatización Playwright del envío, issue de diseño no de implementación). #601/#660 (sesión 2026-07-16, foco ANÁLISIS_SOLICITUD): `requisitos.py`/`items_tecnicos.py` reimplementaban su propio evaluador de condiciones y solo soportaban 6 de los 12 operadores del motor — GT/GTE/LT/LTE/BETWEEN/NOT_BETWEEN se daban por cumplidos en vez de evaluarse; corregido delegando en `app.services.operadores._OPERADORES` (mismo patrón que `motor_reglas`/`plazos`), ensanchando también el CHECK constraint de BD y el desplegable de operadores en `admin_requisitos`/`items_tecnicos` (sin esto el fix habría quedado inerte). #660 es un duplicado exacto del mismo bug en `items_tecnicos.py`, hallado durante el análisis de impacto de #601 y corregido en el mismo PR (#661 mergeado).

**Próximo:** Foco fijo (2026-07-16): dejar la fase `ANÁLISIS_SOLICITUD` completamente tramitable — interfaz, sistema documental, apertura, detección de documentos, notificación y elaboración — porque establece las bases que usarán el resto de fases. Se avanza alternando grupos de issues de este foco entre Próximo y Hecho hasta completarlo; ver exploración de necesidades/código de la sesión 2026-07-16. Activos ahora (3, mezcla issues + 1 tarea de definición, ADR-031): **#408** (poblar `requisitos_documentales` real — activa el checklist documental y desbloquea la regla de tasa #582, hoy inerte por falta de `JUSTIFICANTE_PAGO_TASA` en catálogo), **#602** (restaurar botón de navegación al pool documental del expediente, perdido al migrar a ADR-024), y **tarea de definición — organización documental completa**: sesión de estudio de alcance amplio (apuntada por Carlos el 2026-07-14) antes de tocar ninguna pieza suelta — cubre pertenencia lógica al EXPEDIENTE (#572/ADR-027), estructura física de carpetas por ESFTT (sin issue — #183 cerró solo con carpeta plana `AT-{numero_at}/`, su propio código se autoseñala "provisional"), filing de subidas manuales (N004), reconstrucción del expediente sin BD (N009) y rutas de filesystem configurables (N021). En cola tras estos, mismo foco: #441 (seed `catalogo_requerimientos`), #629 (diagnóstico sin representación visible entre ANALIZAR/ELABORAR), #407 (`siglas_escritos`), #657/#658 (UI + `id_remesa` de notificación), #444/#555 (plantillas `.docx` definitivas de esta fase), #630 (hub tramitador/radar huérfanos — depende en parte de la sesión de organización documental). Hueco de diseño sin issue, solo anotado: `ESPERAR_PLAZO` no admite N documentos simultáneos en respuesta a un requerimiento (`DISEÑO_ANALISIS_SOLICITUD.md` §5; ADR-010 no lo resolvió). Fuera de foco por decisión explícita: automatización externa de firma/notificación (ADR-021, 0%, la incorporación manual ya funciona) y #644-648 (bugs ajenos a esta fase), aparcados.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
