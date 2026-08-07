# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #684 cerrado (PR #771) — el alta en `catalogo_requerimientos` desde el shuttle de `ANALIZAR` deja de ser una puerta trasera al CRUD de #593: el endpoint de #440 exige ahora `gestionar_catalogo_requerimientos` además del gate de expediente. Resuelta la duda que quedaba abierta sobre el checkbox: **misma posición, dos casillas según permiso** —SUPERVISOR/ADMIN mantienen "Guardar en catálogo" operativa (para ellos es el CRUD real, no una solicitud), el resto ve "Solicitar guardado en catálogo" deshabilitada—, que describe el flujo previsto sin prometerlo mientras no haya destinatario. El issue **se cerró acotado a eso**, sin dejarse abierto a expensas de #28: quien habilita la casilla y crea el contrato entre las dos partes es #28, y el checklist correspondiente vive ya en su cuerpo (habilitar la casilla, mandar el `mensaje_sistema` con texto+categoría, y **no** reutilizar el endpoint de #440 — ese sigue siendo escritura directa en el catálogo). Las dos decisiones de diseño de #28 también quedan anotadas allí: el nombre de tabla `notificaciones` **ya está ocupado** por la notificación administrativa de ADR-034, y el `usuario_id` singular no sirve para el aviso *broadcast* del comentario de #479.

**Próximo:** **#766** — ayuda en UI de la regla de recepción de #764: qué documento es el producido cuando en un `ESPERAR_PLAZO` llegan varios. Barato y **reencauza el foco a `ANÁLISIS_SOLICITUD`** tras el paréntesis de #684, que salió del área a propósito. En la cola: **#28** (mensajería interna, sube desde M5 por acuerdo; arrastra las dos decisiones de diseño citadas arriba) y, no crítico, **#743** (idea de seguimiento). Aplazados: #698 (poblado puro de catálogo), #572 (ortogonal, diferido por Carlos), #444/#555 (plantillas — cubierto por la base ya creada en #726, no urge). Sin issue a propósito: el guardián "el resultado de fase debe reflejar el diagnóstico" corresponde a la revisión de la fase `RESOLUCIÓN`, donde el diagnóstico único *es* el veredicto tras el certificado de finalización de fases; fijarlo antes sería diseñar en abstracto. Detalle en #711 y #765. Fuera de foco: ADR-021 y #644-648, aparcados.

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
