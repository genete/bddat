# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** **#804** (PR #807) — `documentos.tipo_contenido` VARCHAR(50) → Text; bloqueaba el guardado en BD de cualquier escrito `.docx` real (MIME de 74 caracteres desbordaba la columna). **#776** — Context Builder, plantilla y plazos de `COMUNICACION_INICIO_ADMISION` (art. 21.4 LPACAP), cerrado tras verificar en navegador el flujo generar → guardar completo (documento #17280).

**Próximo: #777** — `condiciones_requisito` está a 0 filas: los 9 requisitos se exigen siempre, incluidos los que su propia prosa condiciona ("cuando sea persona jurídica", "mediante representante"). Contamina `todos_cubiertos` y, por `tasa_impagada`, al motor. Requiere variable nueva y decidir cómo se marca "no aplica". Sigue el foco de `ANÁLISIS_SOLICITUD`. La auditoría de la fase (2026-08-08) cerró la duda de cuánto quedaba: **toda la cadena de diseño está cerrada** (#248, #192/#408/#583, #594/#581, #440/#441/#593, #442/#392, #406/#495, #455, #582, #679/#711/#714/#724/#765, #764) y el armazón está entero. La fase es casi universal en `ESTRUCTURA_ESF.md` —es la puerta de entrada de casi todo tipo de solicitud—, así que lo que falle aquí falla en todas partes.

Cola por criticidad, no por tamaño:

1. **#780** — el permiso de acceso y conexión no se comprueba, aunque es **condición de admisión a trámite** de la AAP renovable: se puede tramitar entera una solicitud inadmisible. Pide decisión de diseño (requisito / regla de motor / inadmisión) antes de código.
2. **#698** — el `ANY` del nombre sugerido. Verificado más amplio de lo que dice el issue: `nombre_en_plantilla` es NULL en la fase *y en los tres trámites*. Carlos tiene ideas que cambian algo el concepto.
3. **#367** — asociar documento a tarea en el momento de la subida; el pool es la entrada del `ANALISIS_DOCUMENTAL`.
4. **#781** — la ampliación de 5 días del art. 68.1 no se puede reflejar. Ya **no es latente**: con #778 hecho, el vencimiento de la espera se alcanza de verdad, así que la ampliación que no se puede registrar es un error de cómputo real.
5. **#782** — cinco filas de `catalogo_plazos` con `norma_origen` en `PLACEHOLDER` pese a que el peinado ya está hecho; incluye resolver si el anuncio cita el art. 125 o el 131. Absorbió de #785 la cita de `SOLICITUD_INFORME` (art. 80.2 vs. tope de suspensión). La discrepancia 2/3 meses que también arrastraba **queda zanjada por #778**: el tope del art. 22.1.d no vive en el cómputo, la parada es el vencimiento del catálogo.
6. **#783** — `TipoResultadoFase.DESISTIDA` se llama "por el Solicitante" y también cubre el art. 68.1, que no es voluntario. Si desdobla el resultado de fase, alinear el código con `TENER_POR_DESISTIDO` (#779, ya hecho).

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
