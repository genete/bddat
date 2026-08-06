# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #729 cerrado (PR #762) — la casilla «abrir carpeta al generar» abría la carpeta por defecto de Windows por una carrera entre la apertura y el movimiento físico del fichero a su carpeta ESFTT (`mover_a_esftt`, ADR-032 §3). Corregido reordenando `ElaborarEditor.jsx` para abrir la carpeta después de `await onGenerado(...)`; verificado que la secuencia de red y el Explorador ya no tienen ventana de carrera.

**Próximo (2026-08-06):** Siguiente: **#730** (regenerar un escrito crea documento nuevo en vez de sustituir el anterior; requiere decidir antes si sustituir o versionar — ver issue). Foco fijo (2026-07-16): fase `ANÁLISIS_SOLICITUD` completamente tramitable. Al final de la cola, no crítico: **#743** (idea de seguimiento, no urgente). Aplazados: #698 (poblado puro de catálogo), #572 (ortogonal, diferido por Carlos), #444/#555 (plantillas — cubierto por la base ya creada en #726, no urge). Huecos de diseño sin issue: (a) `ESPERAR_PLAZO` no admite N documentos simultáneos (`DISEÑO_ANALISIS_SOLICITUD.md` §5); (b) el invariante de cierre de fase sigue siendo unidireccional — `_check_cierre_fase` corta en seco con resultado `DESFAVORABLE`, así que nunca comprueba el caso simétrico (cerrar DESFAVORABLE teniendo un diagnóstico favorable como última evidencia); #723 no lo tocó. Sin issue a propósito: el guardián "el resultado de fase debe reflejar el diagnóstico" corresponde a la revisión de la fase `RESOLUCIÓN`, donde el diagnóstico único *es* el veredicto tras el certificado de finalización de fases; fijarlo antes sería diseñar en abstracto. Detalle en #711. Fuera de foco: ADR-021 y #644-648, aparcados.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
