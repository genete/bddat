# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #730 cerrado (PR #763) — regenerar un escrito ELABORAR creaba un documento nuevo en vez de sustituir el draft anterior, porque la localización comparaba `Documento.url` y esa comparación dejó de servir en cuanto `mover_a_esftt` empezó a reescribirla (#665). Corregido con `evaluar_regeneracion()`/`ejecutar_regeneracion()` (nuevo servicio `regeneracion_escritos.py`), que localizan el draft por su vínculo (rol+tipo_doc) e implementan la matriz de 8 casos acordada en el issue; el escrito se genera ya en su carpeta ESFTT definitiva en vez de un intermedio que había que mover después. `ElaborarEditor.jsx` añade las cards de confirmación (sustitución de contenido / colisión de nombre) para los casos que requieren decisión del usuario, con contraste de texto corregido sobre fondos success/warning.

**Próximo:** **#764** — `ESPERAR_PLAZO` no admite N documentos simultáneos en la recepción (`DISEÑO_ANALISIS_SOLICITUD.md` §5; milestone M3, etiqueta `design`). Es issue de decisión antes que de código: el enunciado está desfasado —habla de «FK simple», pero desde #420/ADR-010 el obstáculo real es el índice parcial `uq_tarea_un_producido` más el accesor singular `Tarea.documento_producido`—, y la decisión de fondo es si se reabre la nota de ADR-010 («la producción múltiple no es un caso real») o el caso se resuelve sin tocar la cardinalidad del rol `PRODUCIDO`. Sigue vigente el foco fijo (2026-07-16): fase `ANÁLISIS_SOLICITUD` completamente tramitable. Al final de la cola, no crítico: **#743** (idea de seguimiento, no urgente). Aplazados: #698 (poblado puro de catálogo), #572 (ortogonal, diferido por Carlos), #444/#555 (plantillas — cubierto por la base ya creada en #726, no urge). Otro hueco de diseño con issue (2026-08-06): **#765** — el invariante de cierre de fase sigue siendo unidireccional: `_check_cierre_fase` corta en seco con resultado `DESFAVORABLE`, así que nunca comprueba el caso simétrico (cerrar DESFAVORABLE teniendo un diagnóstico favorable como última evidencia); #723 no lo tocó. Sin issue a propósito: el guardián "el resultado de fase debe reflejar el diagnóstico" corresponde a la revisión de la fase `RESOLUCIÓN`, donde el diagnóstico único *es* el veredicto tras el certificado de finalización de fases; fijarlo antes sería diseñar en abstracto. Detalle en #711. Fuera de foco: ADR-021 y #644-648, aparcados.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
