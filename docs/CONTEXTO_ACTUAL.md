# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #723 cerrado (PR #744) — revisión de invariantes. Hallazgo de sesión (prueba en vivo): `editar_fase` no comprobaba ninguna completitud antes de cerrar — se podía cerrar una fase vacía o con un trámite sin tareas colgando sin ningún aviso. Nueva `_check_completitud_cierre` (`invariantes_esftt.py`): vacío estructural (sin trámites, o trámite sin tareas) queda como puerta cerrada, remite a borrar; incompleto con contenido real es forzable con justificación. `_check_cierre_fase` (diagnóstico desfavorable vigente) pasa a forzable de causa única. Fix de raíz en `Tramite.finalizado` (daba `True` por vacuidad con 0 tareas — afectaba también a la pista `PENDIENTE_CERRAR` del listado de seguimiento). Nueva `estado_dominio.motivo()` para redactar los bloqueos con el mismo vocabulario que ya ve el técnico en árbol/seguimiento. `_candado_diagnostico_producido` con motivo veraz (`diagnosticos.motivo_bloqueo_reversion`, caso 3 del issue). Invariantes forzables quedan ajenos al modo global — decisión ya vigente en el código, ahora documentada explícita en `check_invariante`. Derivados: **#742** (bug, prioridad alta: los editores bespoke de tarea ANALIZAR/ELABORAR/NOTIFICAR no tienen botón de borrar) y **#743** (idea: reutilizar `estado_dominio.motivo()` en el tooltip de seguimiento).

**Próximo (2026-08-02):** Siguiente: **#725** creación y orden de ESFTT entre dato y motor (condiciona #719). Foco fijo (2026-07-16): fase `ANÁLISIS_SOLICITUD` completamente tramitable. En cola, mismo foco: #724, #719 (esperar a #725 si se quiere hacer de una vez), #712, #444/#555, #630. **#742** (prioridad alta, fuera del foco actual pero regresión de UX activa) en cola cerca de la cabeza. **#728** datos institucionales del órgano: en cola, no bloquea a nadie. Al final de la cola, no críticos: **#729** (la casilla «abrir carpeta al generar» abre la carpeta por defecto porque el fichero se muda justo después), **#730** (regenerar un escrito crea documento nuevo en vez de sustituir el anterior; hay que decidir antes si sustituir o versionar) y **#743** (idea de seguimiento, no urgente). Aplazados: #698 (poblado puro de catálogo), #572 (ortogonal, diferido por Carlos). Huecos de diseño sin issue: (a) `ESPERAR_PLAZO` no admite N documentos simultáneos (`DISEÑO_ANALISIS_SOLICITUD.md` §5); (b) el invariante de cierre de fase sigue siendo unidireccional — `_check_cierre_fase` corta en seco con resultado `DESFAVORABLE`, así que nunca comprueba el caso simétrico (cerrar DESFAVORABLE teniendo un diagnóstico favorable como última evidencia); #723 no lo tocó. Sin issue a propósito: el guardián "el resultado de fase debe reflejar el diagnóstico" corresponde a la revisión de la fase `RESOLUCIÓN`, donde el diagnóstico único *es* el veredicto tras el certificado de finalización de fases; fijarlo antes sería diseñar en abstracto. Detalle en #711. Fuera de foco: ADR-021 y #644-648, aparcados.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
