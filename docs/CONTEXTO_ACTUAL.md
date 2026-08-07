# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #766 cerrado (PR #772) — la regla de recepción de #764 llega por fin a la interfaz: en `ESPERAR_PLAZO`, una línea de ayuda dice qué documento es el producido cuando llegan varios. Aparece en los dos sitios donde se toma esa decisión —la Despensa del árbol, que es donde se vincula de verdad, y el inspector de lectura de la cola administrativa, que prepara lo que se hará tras "Ir a tramitar"— y solo en `ESPERAR_PLAZO`. Nota de implementación que no está en el issue: la "redacción única" es **convención, no mecanismo**. No existe en el proyecto ningún canal de copy compartido entre Jinja y React, así que hay dos constantes `AYUDA_PRODUCIDO_ESPERAR_PLAZO` gemelas (`app/modules/tareas_y_subidas/routes.py` y `Despensa.jsx`) que se nombran mutuamente en su comentario; montar un origen único para una frase no compensaba, pero con una tercera superficie sí tocaría.

**También hecho:** **#684** cerrado (PR #771) y **acotado a la parte obligatoria, sin quedar a expensas de #28**: el endpoint de #440 exige ahora `gestionar_catalogo_requerimientos`, y en la interfaz conviven, en la misma posición y según permiso, "Guardar en catálogo" operativa (SUPERVISOR/ADMIN) y "Solicitar guardado en catálogo" deshabilitada (el resto). Todo lo que hereda #28 —habilitar esa casilla, el `mensaje_sistema`, y **no** reutilizar el endpoint de #440— vive ya en el cuerpo de #28; no se repite aquí.

**Próximo:** **#28** — mensajería interna, elegido por Carlos aun sabiendo que **vuelve a salir del foco de `ANÁLISIS_SOLICITUD`** y que sube desde M5. Antes de implementar hay que cerrar las dos decisiones de diseño anotadas en su cuerpo: el nombre de tabla `notificaciones` que pide **ya está ocupado** por la notificación administrativa de ADR-034, y el `usuario_id` singular no sirve para el aviso *broadcast* del comentario de #479. En la cola, no crítico: **#743** (idea de seguimiento). Aplazados: #698 (poblado puro de catálogo), #572 (ortogonal, diferido por Carlos), #444/#555 (plantillas — cubierto por la base ya creada en #726, no urge). Sin issue a propósito: el guardián "el resultado de fase debe reflejar el diagnóstico" corresponde a la revisión de la fase `RESOLUCIÓN`, donde el diagnóstico único *es* el veredicto tras el certificado de finalización de fases; fijarlo antes sería diseñar en abstracto. Detalle en #711 y #765. Fuera de foco: ADR-021 y #644-648, aparcados.

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
