# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** **#785** (PR #791) — `catalogo_plazos` identificado por camino SFTT, con la reconstrucción manual de `tipo_tramite` retirada de sus tres consumidores. El detalle está en el PR y los commits. Lo único que no vive ahí: al medir el coste que justificaba ese bypass salió **#790** (el ensamblador recompila cada variable 3 veces por recursión de `estado_plazo`/`efecto_plazo`, y `GET /analizar` hace 4 builds idénticos), abierto aparte porque toca el motor entero, no plazos.

**Sigue vivo de #577 + #585** (PR #775): `app/services/consultas_organismos.py` es un servicio sin caller, el único del proyecto en esa situación y a propósito — conserva el contrato `(jsonify, status)` del blueprint muerto en vez de `ResultadoMutacion`, y al reconectar la UI de consultas esa conversión es el primer paso (anotado en su docstring). Y la dependencia sin issue propio heredada de #28: la ampliación del modelo `Usuario` con los campos que exigen la automatización de bandeja y Notific@, de la que cuelga #773 y alrededor de la que orbitan #757, #758 y #659.

**Nota de #766 que sigue viva** (no está en su issue): la "redacción única" de la ayuda de `ESPERAR_PLAZO` es **convención, no mecanismo**. No existe en el proyecto ningún canal de copy compartido entre Jinja y React, así que hay dos constantes `AYUDA_PRODUCIDO_ESPERAR_PLAZO` gemelas (`app/modules/tareas_y_subidas/routes.py` y `Despensa.jsx`) que se nombran mutuamente en su comentario; montar un origen único para una frase no compensaba, pero con una tercera superficie sí tocaría. #28 lo confirmó por el lado contrario: cuando productor y renderizador son ambos Python (inspector = fragmento Jinja del backend, ADR-023), el "un solo sitio" sale estructural y no hay convención que recordar.

**Próximo: #787**, salto acordado (2026-08-17) por ser simple y dejar el catálogo limpio inmediatamente después de #785. Sigue el foco de `ANÁLISIS_SOLICITUD`. La auditoría de la fase (2026-08-08) cerró la duda de cuánto quedaba: **toda la cadena de diseño está cerrada** (#248, #192/#408/#583, #594/#581, #440/#441/#593, #442/#392, #406/#495, #455, #582, #679/#711/#714/#724/#765, #764) y el armazón está entero. Lo que falta no es armazón: son dos bugs con consecuencia jurídica, un trámite hueco, contenido de catálogo y cola barata. La fase es casi universal en `ESTRUCTURA_ESF.md` —es la puerta de entrada de casi todo tipo de solicitud—, así que lo que falle aquí falla en todas partes.

Cola por criticidad, no por tamaño:

1. **#787** — 14 filas "solicitud AAP" duplicadas en `catalogo_plazos` de la BD de desarrollo; sospecha de residuo de test sin limpiar. Investigar origen antes de depurar. *(Próximo: simple y deja el catálogo limpio tras #785.)*
2. **#786** — sin mecanismo que avise de duplicados ciegos o solape de condiciones entre filas de `catalogo_plazos`/`condiciones_plazo`. **Desbloqueado**: el diseño del que dependía ya está, y puede reducirse — con identificación por camino, un duplicado es un `camino` repetido, y la invariante "la hoja nunca es `ANY`" es validable sola.
3. **#788** — `campo_fecha` de `catalogo_plazos` para FASE no puede expresar dependencia de fases previas completadas. Sesión de diseño propia.
4. **#789** — `plazo_valor=0` ("plazo indefinido") es convención real de `ESTRUCTURA_FTT.md` (`EP(0)` en `AAU_AAUS_INTEGRADA`) sin ningún soporte en código ni en catálogo.
5. **#778** — la suspensión del art. 22 LPACAP no tiene tope: con un requerimiento sin respuesta, el expediente **nunca vence**. El caso que más urge detectar es el que el sistema oculta. Afecta también a `SOLICITUD_INFORME`/`CONSULTA_SEPARATA`/`SOLICITUD_COMPATIBILIDAD`. Prerrequisito de #781. Ya no lo bloquea la estructura (#785 hecho), pero **el tope no está fijado**: `CONTEXTO_ACTUAL` decía 3 meses y #785 decía 2 — la discrepancia queda registrada en #782 como ítem propio, y hay que zanjarla antes de leer el tope de `catalogo_plazos`.
6. **#779** — el vencimiento del plazo de subsanación está tipificado `PERDIDA_TRAMITE` (art. 73.3) cuando el art. 68.1 produce **desistimiento**: se comunica al técnico una consecuencia falsa, y no existe el efecto correcto en `efectos_plazo`. Mismo escenario que #778 y mucho más barato.
7. **#776** — `COMUNICACION_INICIO` existe en catálogo, el motor lo gobierna (regla 35) y está **hueco**: sin Context Builder ni plantilla. No es informativo: es el escrito con el que el promotor acredita el **Hito 1 del RD-ley 23/2020** ante el gestor de red, y de no emitirlo se siguen caducidad de sus permisos de acceso y ejecución de garantías.
8. **#777** — `condiciones_requisito` está a 0 filas: los 9 requisitos se exigen siempre, incluidos los que su propia prosa condiciona ("cuando sea persona jurídica", "mediante representante"). Contamina `todos_cubiertos` y, por `tasa_impagada`, al motor. Requiere variable nueva y decidir cómo se marca "no aplica".
9. **#780** — el permiso de acceso y conexión no se comprueba, aunque es **condición de admisión a trámite** de la AAP renovable: se puede tramitar entera una solicitud inadmisible. Pide decisión de diseño (requisito / regla de motor / inadmisión) antes de código.
10. **#698** — el `ANY` del nombre sugerido. Verificado más amplio de lo que dice el issue: `nombre_en_plantilla` es NULL en la fase *y en los tres trámites*. Carlos tiene ideas que cambian algo el concepto.
11. **#367** — asociar documento a tarea en el momento de la subida; el pool es la entrada del `ANALISIS_DOCUMENTAL`.
12. **#781** — la ampliación de 5 días del art. 68.1 no se puede reflejar. Latente hoy; en cuanto #778 aplique el tope, se vuelve error de cómputo real. Va detrás de #778 por eso.
13. **#782** — cinco filas de `catalogo_plazos` con `norma_origen` en `PLACEHOLDER` pese a que el peinado ya está hecho; incluye resolver si el anuncio cita el art. 125 o el 131. Absorbió de #785 la cita de `SOLICITUD_INFORME` (art. 80.2 vs. tope de suspensión) y la discrepancia 2/3 meses.
14. **#783** — `TipoResultadoFase.DESISTIDA` se llama "por el Solicitante" y también cubre el art. 68.1, que no es voluntario. Coordinar vocabulario con #779.

**Nota de sesión (2026-08-15/16):** #784 acotó los problemas de fondo de `catalogo_plazos` y se desglosó en #785 (hecho), #786, #787, #788 y #789 — todos en la cola de arriba. La razón para diferir #778 sigue valiendo con el matiz que ya recoge su entrada: BDDAT está en desarrollo y el bug es potencial, no real, así que no compensa escribir datos de catálogo antes de que la estructura y el tope estén fijados.

**Necesarios pero no bloqueantes** (recorte acordado con Carlos, 2026-08-08): **#751** (helper de UI), **#595** (bastan unos cuantos ítems técnicos para ejercitar lógica e interfaz, no el poblado completo — hoy hay 2 filas), **#444** (limitado a `requerimiento_subsanacion.docx`: la fila ya existe en BD apuntando a un fichero inexistente), **#555** (solo esa plantilla).

**Fuera del foco:** **#790** (coste del ensamblador, salido de #785 — toca el motor entero, no esta fase) · #607 aplazado · #572 va con el compilador de expediente para recurso/contencioso · #568 diferido (sin casos en años) · #306/#428/#304 son helpers · #743, #570 (emparejable con #755) en la cola general · #773 espera la ampliación de `Usuario` · ADR-021 y #644-648 aparcados.

**Sin issue a propósito:** el guardián "el resultado de fase debe reflejar el diagnóstico" corresponde a la revisión de la fase `RESOLUCIÓN`, donde el diagnóstico único *es* el veredicto tras el certificado de finalización de fases; fijarlo antes sería diseñar en abstracto. Detalle en #711 y #765.

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
