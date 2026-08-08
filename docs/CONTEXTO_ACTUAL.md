# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** **#28** (PR #774) — la bandeja de mensajes internos, construida tal cual la fijó ADR-040. El *qué* y el *por qué* viven en el ADR, en el issue y en los siete commits; no se repiten aquí. Lo que no está en ninguno de ellos:

- **La tensión de milestone anotada aquí se disolvió sin tocar nada.** #28 se implementó estando en **M5** y su dependencia #684 en **M3**: al hacerlo antes de que llegara su milestone, la casilla inerte que #684 dejó esperando en la interfaz ("Solicitar guardado en catálogo") dejó de serlo, y ya no hay nada que decidir sobre milestones.
- **Aparece una dependencia futura que aún no tiene issue propio:** la ampliación del modelo `Usuario` con los campos que exigen la **automatización de bandeja y Notific@**. De ella cuelga #773 (el §9 de ADR-040, diferido por eso), y a su alrededor orbitan #757, #758 y #659. Nadie la ha filed todavía como issue de modelo.

**Nota de #766 que sigue viva** (no está en su issue): la "redacción única" de la ayuda de `ESPERAR_PLAZO` es **convención, no mecanismo**. No existe en el proyecto ningún canal de copy compartido entre Jinja y React, así que hay dos constantes `AYUDA_PRODUCIDO_ESPERAR_PLAZO` gemelas (`app/modules/tareas_y_subidas/routes.py` y `Despensa.jsx`) que se nombran mutuamente en su comentario; montar un origen único para una frase no compensaba, pero con una tercera superficie sí tocaría. #28 lo confirmó por el lado contrario: cuando productor y renderizador son ambos Python (inspector = fragmento Jinja del backend, ADR-023), el "un solo sitio" sale estructural y no hay convención que recordar.

**Próximo:** **#577 + #585** — retirada de código muerto: `api_bc.py` (sin consumidores desde #519) y `tabla_metadata` (#85, modelo sin consumidores que además contradice ADR-013). Los dos en **M2**, elegidos por Carlos como consolidación barata antes de abrir frente nuevo; generan código de borrado, no de poblado. Aplican `git rm` en el mismo issue, sin dejar ficheros huérfanos sin importar. Sigue **fuera del foco de `ANÁLISIS_SOLICITUD`**, elegido así a conciencia por segunda vez consecutiva. En la cola, no crítico: **#743** (idea de seguimiento), **#751** (señal en el borrador, línea de #724/#711), **#570** (filtros de listados v2 en la URL, emparejable con #755). Aplazados: #698 (poblado puro de catálogo), #572 (ortogonal, diferido por Carlos), #444/#555 (plantillas — cubierto por la base ya creada en #726, no urge), #773 (a la espera de la ampliación de `Usuario`). Sin issue a propósito: el guardián "el resultado de fase debe reflejar el diagnóstico" corresponde a la revisión de la fase `RESOLUCIÓN`, donde el diagnóstico único *es* el veredicto tras el certificado de finalización de fases; fijarlo antes sería diseñar en abstracto. Detalle en #711 y #765. Fuera de foco: ADR-021 y #644-648, aparcados.

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
