# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #657/#658 (sesión 2026-07-23, tarea NOTIFICAR — interfaz `NotificarEditor`: "Registrar envío"/"Completar resultado", `notificaciones` corregida a tabla de seguimiento anclada a `tarea_id` con cotejo de remesa no bloqueante, ADR-034). PR #710. Verificación posterior en AT-2004 destapó #711 (bug preexistente de #419: invariante de cierre de fase no reconoce diagnóstico superado por vuelta de subsanación) y #712 (mejora de `NotificarEditor`: vínculo del justificante en dos actos + cotejo de canal).

**Próximo:** Cabeza de cola (2026-07-23): #688 — unificar emplazamiento de Guardar/Cancelar de campos directos en la cabecera del inspector; transversal a ANALIZAR/ELABORAR/NOTIFICAR, resuelve el punto abierto en la sesión de #657/#658 sobre dónde debe vivir el Guardar del pie de `NotificarEditor`. Foco fijo (2026-07-16): fase `ANÁLISIS_SOLICITUD` completamente tramitable. #698 (nombre "ANY") aplazado: es poblado puro de catálogo (`tipos_tramites.nombre_en_plantilla` vacío en 31/31, `tipos_solicitudes` de AT-2004 con valor incorrecto), sin código de por medio. #572 (ADR-027) sigue ortogonal, diferido por Carlos. En cola, mismo foco: #444/#555, #630. Hueco de diseño sin issue: `ESPERAR_PLAZO` no admite N documentos simultáneos (`DISEÑO_ANALISIS_SOLICITUD.md` §5). Fuera de foco: ADR-021 y #644-648, aparcados.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
