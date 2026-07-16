# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** Prototipo y librería de parseo del justificante de notificación Notifica-PNT (sesión 2026-07-16): #655 entrega `app/services/parser_justificante_notifica.py` — parsea PDF y ZIP (Informe.pdf + InformeENI.xml) y devuelve estado/resultado/fechas en JSON, con cotejo de coherencia PDF↔XML (`coherente_con_xml`); validado contra justificantes reales, sin integración en interfaz todavía (PR #656 mergeado). Necesidad nueva N084 (ninguna necesidad existente cubría extracción de datos de un justificante externo — alta formal en `DETALLE_NECESIDADES_BDDAT.md` pendiente, ver ADR-031 §7). Abiertos como continuación, sin promover a Próximo: #657 (UI para registrar resultado — subida al pool / tarea NOTIFICAR), #658 (persistir `id_remesa` para cotejar justificante contra expediente), #659 (diseño de automatización Playwright del envío, issue de diseño no de implementación).

**Próximo:** _pendiente de decidir — candidatos: #644-#647 (bugs de UI diferidos, cada uno necesita antes una decisión de diseño) o #648 (refactor de sistema de componentes)._

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
