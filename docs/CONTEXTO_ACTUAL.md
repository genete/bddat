# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #479 — Selector de modo global del motor (BLOQUEAR/SOLO_ADVERTIR/
INACTIVO) en el hub del supervisor (ADR-028 bloque Gestión), sobre
`configuracion_sistema` ya sembrada en #323. De paso, unificado
`_aplicar_modo_global` (antes copiado en `mutaciones_arbol.py`,
`tipos_creables.py` y el `api_bc.py` muerto) en un único
`app/services/motor_modo_global.py`. Cada cambio de modo queda en bitácora
(quién, cuándo, de qué modo a qué modo) — pieza mínima para el futuro #614.
Semáforo permanente del modo en la topbar, visible a los 4 roles, con polling
cada 60s (sin infraestructura de push todavía). Verificado en navegador con
una regla real del motor (AAC no resuelta) en los tres modos. Suite completa:
824 passed, 24 skipped. PR #615. Del análisis surgió #614 (certificado fin de
instrucción / justificación retroactiva de desviaciones del motor, bloqueado
por un futuro ADR de bitácora ampliada a log completo de transacciones).

**Próximos:** #612 (N034 — asignación masiva de expedientes a técnico, abierto
en la sesión de reposición de #171).

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
