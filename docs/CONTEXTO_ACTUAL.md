# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** **#782 — norma_origen de catalogo_plazos verificada contra el BOE.** Las 5 filas TAREA con `PLACEHOLDER` ya citan su norma exacta, leída del texto consolidado vigente (no solo del resumen NBLM): `SOLICITUD_INFORME` resultó ser en exclusiva el informe DGPEM de transporte (art. 114 RD 1955/2000 — plazo corregido de 10 días a **2 meses**, no el art. 80.2 LPACAP que sugería el placeholder; camino explicitado a la fase `CONSULTA_MINISTERIO`); `ANUNCIO_BOE`/`ANUNCIO_BOP` citan el art. 125.1 RD 1955/2000 (no el 131, que regula condicionados AAC); `ANUNCIO_PRENSA` cita el art. 144 (información pública de la DUP, único que exige prensa). De paso, `plazo_unidad` de los tres anuncios se corrigió de `DIAS_NATURALES` a `DIAS_HABILES` (LPACAP art. 30.2, sin declaración expresa de naturales en el RD). La discrepancia 2/3 meses del tope de suspensión que el issue pedía zanjar ya estaba resuelta por #778/ADR-041, sin acción. [PR #815](https://github.com/genete/bddat/pull/815).

**Próximo:** **#783** — `TipoResultadoFase.DESISTIDA` se llama "por el Solicitante" y también cubre el art. 68.1, que no es voluntario. Si desdobla el resultado de fase, alinear el código con `TENER_POR_DESISTIDO` (#779, ya hecho).

Cola por criticidad, no por tamaño:

1. **#783** — `TipoResultadoFase.DESISTIDA` se llama "por el Solicitante" y también cubre el art. 68.1, que no es voluntario. Si desdobla el resultado de fase, alinear el código con `TENER_POR_DESISTIDO` (#779, ya hecho).

**Nota de sesión (2026-08-15/16):** #784 acotó los problemas de fondo de `catalogo_plazos` y se desglosó en #785 (hecho), #787 (hecho, alcance ampliado a `reglas_motor`), #786 (hecho), #788 (hecho) y #789 (hecho). #778 cerró la serie el 2026-08-21: la razón para diferirlo —no escribir datos de catálogo antes de fijar el tope— desapareció al descubrirse que el tope no era un dato que añadir sino uno que el catálogo ya tenía y que el cálculo no leía.

**Nota de sesión (2026-08-22):** de la sesión de #776 salió además **#805** (vigilante de creaciones posibles — obligatoriedad condicionada de trámites y aviso de "pendiente de crear"), motivado por #776 pero de alcance propio: se aborda en otra conversación, fuera de esta cola.

**Necesarios pero no bloqueantes** (recorte acordado con Carlos, 2026-08-08): **#751** (helper de UI), **#595** (bastan unos cuantos ítems técnicos para ejercitar lógica e interfaz, no el poblado completo — hoy hay 2 filas), **#444** (limitado a `requerimiento_subsanacion.docx`: la fila ya existe en BD apuntando a un fichero inexistente), **#555** (solo esa plantilla).

**Fuera del foco:** **#790** (coste del ensamblador, salido de #785 — toca el motor entero, no esta fase) · #607 aplazado · #572 va con el compilador de expediente para recurso/contencioso · #568 diferido (sin casos en años) · #306/#428/#304 son helpers · #743, #570 (emparejable con #755) en la cola general · #773 espera la ampliación de `Usuario` · ADR-021 y #644-648 aparcados.

**Sin issue a propósito:** el guardián "el resultado de fase debe reflejar el diagnóstico" corresponde a la revisión de la fase `RESOLUCIÓN`, donde el diagnóstico único *es* el veredicto tras el certificado de finalización de fases; fijarlo antes sería diseñar en abstracto. Detalle en #711 y #765.

**Nota de foco de fase — arrastrar a cada repaso (2026-08-07, #764):** todo `ESPERAR_PLAZO` que pueda recibir documentación de terceros exige un `ANALIZAR` posterior —propio, del trámite receptor hermano, o añadido tras él si es el último trámite de la fase—. Esta exigencia se comprueba durante el desarrollo mediante repaso de fase a fase, sin crear issues a futuro, sino sobre la marcha. Detectados y **sin issue a propósito**, por la fase en que se corrigen: en `AAU_AAUS_INTEGRADA`, `DISCREPANCIA_INF_VINC` (sin trámite receptor definido en catálogo) más `RECEPCION_DICTAMEN`, `RECEPCION_PROPUESTA_INF_VINC` y `REMISION_RESULTADO_IP_CONSULTAS`; en `FIGURA_AMBIENTAL_EXTERNA`, `SOLICITUD_FIGURA`. Estos cuatro últimos tienen receptor plausible pero no formalizado en el catálogo ESFTT. **Ojo al leer notas anteriores a #778:** hablaban de formalizarlo en `_TRAMITES_CIERRE` de `plazos.py`, lista que ya no existe — el plazo lo cierra el documento producido de su propia espera (`campo_fecha_cumplimiento`), no un trámite hermano. La exigencia del `ANALIZAR` posterior sigue en pie por lo que es: quien recibe documentación de terceros tiene que estudiarla. `SOLICITUD_INFORME_OPERADOR` está en el JSON pero sin poblar en BD (#450): al poblarlo, darle receptor con `ANALIZAR`.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
