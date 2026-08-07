# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #764 cerrado (PR #767) — el hueco «`ESPERAR_PLAZO` no admite N documentos simultáneos» resultó no ser un problema de modelo. Todo lo que llega de fuera trae un documento que acredita el hecho y porta su fecha administrativa —registro de entrada o solicitud, justificante de BandeJA si el remitente es interno, acuse acreditativo si lo esperado es una publicación—, y ése es el `PRODUCIDO`, uno; los anexos entran al pool y los consume (0..N) el `ANALIZAR` siguiente, que es donde se incorporan al expediente. Cardinalidad `PRODUCIDO` 0..1 y `uq_tarea_un_producido` se mantienen: ADR-010 no se reabre (su cláusula de reapertura de `es_principal` queda examinada y cerrada). Regla escrita en `ESTRUCTURA_FTT.json` v6.3 —fuente de verdad— y su MD, ADR-004, ADR-010 y `DISEÑO_ANALISIS_SOLICITUD.md` §5. La ayuda en interfaz derivada (tooltip en la Despensa y en el inspector de la cola) queda en **#766**.

**Próximo:** **#765** — el invariante de cierre de fase sigue siendo unidireccional: `_check_cierre_fase` corta en seco con resultado `DESFAVORABLE`, así que nunca comprueba el caso simétrico (cerrar DESFAVORABLE teniendo un diagnóstico favorable como última evidencia); #723 no lo tocó. Sigue vigente el foco fijo (2026-07-16): fase `ANÁLISIS_SOLICITUD` completamente tramitable. En la cola: **#766** (ayuda en UI de la regla de recepción, barato) y, no crítico, **#743** (idea de seguimiento). Aplazados: #698 (poblado puro de catálogo), #572 (ortogonal, diferido por Carlos), #444/#555 (plantillas — cubierto por la base ya creada en #726, no urge). Sin issue a propósito: el guardián "el resultado de fase debe reflejar el diagnóstico" corresponde a la revisión de la fase `RESOLUCIÓN`, donde el diagnóstico único *es* el veredicto tras el certificado de finalización de fases; fijarlo antes sería diseñar en abstracto. Detalle en #711. Fuera de foco: ADR-021 y #644-648, aparcados.

**Nota de foco de fase — arrastrar a cada repaso (2026-08-07, #764):** todo `ESPERAR_PLAZO` que pueda recibir documentación de terceros exige un `ANALIZAR` posterior —propio, del trámite receptor hermano, o añadido tras él si es el último trámite de la fase—. Esta exigencia se comprueba durante el desarrollo mediante repaso de fase a fase, sin crear issues a futuro, sino sobre la marcha. Detectados y **sin issue a propósito**: `DISCREPANCIA_INF_VINC` (sin trámite receptor definido en catálogo) y, con receptor plausible pero no formalizado en `_TRAMITES_CIERRE` de `plazos.py`, `RECEPCION_DICTAMEN`, `RECEPCION_PROPUESTA_INF_VINC`, `SOLICITUD_FIGURA` y `REMISION_RESULTADO_IP_CONSULTAS`. Se corrigen al repasar la fase en que viven. `SOLICITUD_INFORME_OPERADOR` está en el JSON pero sin poblar en BD (#450): al poblarlo, darle receptor con `ANALIZAR`.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
