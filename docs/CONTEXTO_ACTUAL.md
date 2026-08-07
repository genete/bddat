# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #765 cerrado (PR #770) — el invariante de cierre de fase deja de ser unidireccional. Cerrar `DESFAVORABLE` ya no cortocircuita el check: lo evalúa `_check_cierre_desfavorable`, que bloquea —forzable con justificación— cuando la fase tiene diagnósticos vigentes y ninguno es desfavorable. Criterios acordados de las tres preguntas de alcance: misma noción de vigencia que #711 (extraída a `_diagnosticos_vigentes_query`, base común de ambas ramas para que no diverjan); solo un `desfavorable` respalda el cierre —un `condicionado` no lo sostiene por sí solo—; `consumido` no se mira en este sentido, para que "requerido y no subsanado" cierre sin fricción. Sin diagnósticos vigentes no bloquea, así que no alcanza a `RESOLUCIÓN` (ninguno de sus trámites lleva `ANALIZAR`): el guardián general de esa fase sigue sin issue a propósito. Hallazgo colateral corregido en el mismo PR: el escape con justificación no llegaba al **Guardar del inspector** —`guardar()` descartaba `puede_escapar` y lo mostraba como toast, escape que solo existía al CREAR—, de modo que los tres bloqueos forzables del cierre de fase (completitud #723, desfavorable sin consumir #419/#711 y este) eran puertas cerradas en la interfaz y la única salida era guardar el resultado sin documento, la ventana que esquiva el check (N015).

**Próximo:** **#654** — sospecha de Carlos de que se cierra solo, confirmada en una comprobación previa: lo que el issue pedía ya está implementado, en parte por otra vía. `_creables_tarea` es desde #725 un listado didáctico (canónicos/resto, sin `permitido=False`), la UI distingue sugerida de permitida con el toggle "Mostrar todos" y `es_siguiente`, crear fuera del patrón ni siquiera bloquea (solo hay check de *orden*, `check_orden_tarea`, y es `puede_escapar=True`), y el docstring que el issue citaba está reescrito. El punto 1 —"dar al motor capacidad de discriminar por `tipo_tarea`"— quedó **disuelto**, no resuelto: ADR-037 §A decide que trámite→tarea no va por `reglas_motor` (sería reescribir `tramites_tareas` como reglas) sino por la categoría C. Queda cerrarlo formalmente dejando esa trazabilidad escrita en el issue. Sale del foco fijo de `ANÁLISIS_SOLICITUD` a propósito, por ser uno menos sin coste. En la cola: **#766** (ayuda en UI de la regla de recepción de #764, barato, dentro del foco) y, no crítico, **#743** (idea de seguimiento). Aplazados: #698 (poblado puro de catálogo), #572 (ortogonal, diferido por Carlos), #444/#555 (plantillas — cubierto por la base ya creada en #726, no urge). Sin issue a propósito: el guardián "el resultado de fase debe reflejar el diagnóstico" corresponde a la revisión de la fase `RESOLUCIÓN`, donde el diagnóstico único *es* el veredicto tras el certificado de finalización de fases; fijarlo antes sería diseñar en abstracto. Detalle en #711 y #765. Fuera de foco: ADR-021 y #644-648, aparcados.

**Nota de foco de fase — arrastrar a cada repaso (2026-08-07, #764):** todo `ESPERAR_PLAZO` que pueda recibir documentación de terceros exige un `ANALIZAR` posterior —propio, del trámite receptor hermano, o añadido tras él si es el último trámite de la fase—. Esta exigencia se comprueba durante el desarrollo mediante repaso de fase a fase, sin crear issues a futuro, sino sobre la marcha. Detectados y **sin issue a propósito**, por la fase en que se corrigen: en `AAU_AAUS_INTEGRADA`, `DISCREPANCIA_INF_VINC` (sin trámite receptor definido en catálogo) más `RECEPCION_DICTAMEN`, `RECEPCION_PROPUESTA_INF_VINC` y `REMISION_RESULTADO_IP_CONSULTAS`; en `FIGURA_AMBIENTAL_EXTERNA`, `SOLICITUD_FIGURA`. Estos cuatro últimos tienen receptor plausible pero no formalizado en `_TRAMITES_CIERRE` de `plazos.py` (sí lo están `SOLICITUD_INFORME` de `CONSULTA_MINISTERIO` y `SOLICITUD_COMPATIBILIDAD` de `COMPATIBILIDAD_AMBIENTAL`). `SOLICITUD_INFORME_OPERADOR` está en el JSON pero sin poblar en BD (#450): al poblarlo, darle receptor con `ANALIZAR`.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
