# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #588, #589, #590 (ADR-029 completa — hub Control y Gestión universal + Tareas y Subidas extraído de mi_trabajo, dashboard 1:1 de module_nav + criterio de sidebar revisado (§1bis) + Mi Perfil migrado, retirar prefijo /admin de Plantillas/Requisitos documentales), #609 (pool de documentos de la despensa de tareas: enlace de apertura + abrir carpeta para cualquier documento del pool, no solo los ya vinculados a la tarea — reformulado durante la sesión tras verificar que el modo lectura ya resolvía el enlace, así que el hueco real no era el descrito originalmente), #610 (enlaces bddat:// del inspector — despacho por recurso: certificados enlaza a `cert_pdf`, diagnósticos sin enlace explícito (`puede_abrir`) en vez de 404 silencioso, recurso desconocido falla alto; spinoff #629: diagnóstico sin representación visible entre ANALIZAR y ELABORAR), #574 (fecha_administrativa en certificados internos: `_validar_url` ya no la fuerza a NULL para el esquema bddat://; CERT_PLAZO_CUMPLIDO y CERT_FIN_IP_CONSULTAS asignan su fecha real; alcance reducido sin tocar #572; CERT_FIN_INSTRUCCION queda fuera, su generador no está conectado al flujo real de creación de fase), #566 (abrev de la tarea ANALIZAR en el árbol — corrección de dato vía CRUD de tablas maestras, sin código).

**Próximo:** (vacío — pendiente de decidir el siguiente foco).

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
