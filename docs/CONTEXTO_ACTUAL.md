# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #738 cerrado (PR #740) — desvincular/borrar el justificante de notificación era silencioso: `es_documento_critico` (prefijo `JUSTIFICANTE_*` del catálogo) unifica el criterio para los 9 tipos de justificante (notificación + publicación). `editar_tarea` registra en bitácora (sin bloquear) al desvincular un documento crítico; `_documento_es_referenciado` ahora mira también `doc.notificacion` (bugfix: sin esto, un justificante ya desvinculado se borraba arrastrando por cascada la fila `Notificacion` entera, sin rastro); `pool_borrar_documento` audita el borrado permitido de un documento crítico. Guarda temprana no bloqueante (ADVERTIR) en `editar_fase` si hay justificantes sin vincular en el pool del expediente. Mismo patrón de invariante hardcoded que #722/ADR-036.

**Próximo (2026-08-01):** Siguiente: **#715** los tests de `invariantes_esftt` mockean `db`; luego **#723** revisión de invariantes; **#725** creación y orden de ESFTT entre dato y motor (condiciona #719). Foco fijo (2026-07-16): fase `ANÁLISIS_SOLICITUD` completamente tramitable. En cola, mismo foco: #724, #719 (esperar a #725 si se quiere hacer de una vez), #712, #444/#555, #630. **#728** datos institucionales del órgano: en cola, no bloquea a nadie. Al final de la cola, no críticos: **#729** (la casilla «abrir carpeta al generar» abre la carpeta por defecto porque el fichero se muda justo después) y **#730** (regenerar un escrito crea documento nuevo en vez de sustituir el anterior; hay que decidir antes si sustituir o versionar). Aplazados: #698 (poblado puro de catálogo), #572 (ortogonal, diferido por Carlos). Huecos de diseño sin issue: (a) `ESPERAR_PLAZO` no admite N documentos simultáneos (`DISEÑO_ANALISIS_SOLICITUD.md` §5); (b) el invariante de cierre de fase es unidireccional — `_check_cierre_fase` corta en seco con resultado `DESFAVORABLE`, así que nunca comprueba el caso simétrico (cerrar DESFAVORABLE teniendo un diagnóstico favorable como última evidencia). Sin issue a propósito: el guardián "el resultado de fase debe reflejar el diagnóstico" corresponde a la revisión de la fase `RESOLUCIÓN`, donde el diagnóstico único *es* el veredicto tras el certificado de finalización de fases; fijarlo antes sería diseñar en abstracto. Detalle en #711. Fuera de foco: ADR-021 y #644-648, aparcados.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
