# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** **ADR-040** (commit directo a develop, doc de decisión vivo) — el diseño de #28 queda cerrado **antes** de tocar código, y su cuerpo reescrito con alcance y tareas: **ya no queda ninguna decisión abierta**. Las dos que estaban anotadas se resolvieron, y apareció una tercera que el issue no veía (la campana del topbar también estaba ocupada, por el dock de ADR-020). El *qué* y el *por qué* viven en el ADR y en el issue; no se repiten aquí. Lo que no está en ninguno de los dos: el diseño lo fijó la visión de Carlos en la propia sesión —bandeja del supervisor sin campo destinatario, `hecho`+notas, sobre aparte de la campana, CRUD list+inspector—, no el análisis previo de Claude, cuyas dos propuestas centrales (destinatario XOR usuario\|rol, tercer tab del dock) quedaron descartadas en el ADR §Alternativas.

**Nota de #766 que sigue viva** (no está en su issue): la "redacción única" de la ayuda de `ESPERAR_PLAZO` es **convención, no mecanismo**. No existe en el proyecto ningún canal de copy compartido entre Jinja y React, así que hay dos constantes `AYUDA_PRODUCIDO_ESPERAR_PLAZO` gemelas (`app/modules/tareas_y_subidas/routes.py` y `Despensa.jsx`) que se nombran mutuamente en su comentario; montar un origen único para una frase no compensaba, pero con una tercera superficie sí tocaría. No aplica al CRUD de #28: allí el render lo sirve el backend como fragmento Jinja (ADR-023), así que productor y renderizador son ambos Python.

**Próximo:** **implementar #28** — sin decisiones pendientes, salvo un dato que solo Carlos puede dar (correo destino y datos mínimos del modal de alta del login, anotado como tarea en el issue). Sigue **fuera del foco de `ANÁLISIS_SOLICITUD`**, elegido así a conciencia. **Tensión de milestone sin resolver, decisión de Carlos:** #28 sigue en **M5** mientras su dependencia #684 está en **M3** y dejó una casilla inerte esperando en la interfaz ("Solicitar guardado en catálogo"); no se ha movido unilateralmente. En la cola, no crítico: **#743** (idea de seguimiento). Aplazados: #698 (poblado puro de catálogo), #572 (ortogonal, diferido por Carlos), #444/#555 (plantillas — cubierto por la base ya creada en #726, no urge). Sin issue a propósito: el guardián "el resultado de fase debe reflejar el diagnóstico" corresponde a la revisión de la fase `RESOLUCIÓN`, donde el diagnóstico único *es* el veredicto tras el certificado de finalización de fases; fijarlo antes sería diseñar en abstracto. Detalle en #711 y #765. Fuera de foco: ADR-021 y #644-648, aparcados.

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
