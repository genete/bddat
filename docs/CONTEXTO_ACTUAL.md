# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** **#577 + #585** (PR #775) — retirada de código muerto. Lo que no está en los issues ni en los cinco commits:

- **La premisa de "código muerto" falló en los dos, en direcciones opuestas.** En #577 lo muerto era la *superficie HTTP* de `api_bc.py`, no su contenido: dentro vivían los helpers de bypass que `api_expedientes` ya consumía (#616) y todo el trámite de consultas (#247/#462/#471/#475), huérfano de UI desde #519 pero no de valor. Esa distinción —superficie vs. contenido— decidió el alcance real y el issue no la hacía. En #585 la premisa se quedó corta: no era solo "sin consumidores", era un diseño que ADR-013 descartó sin nombrarlo, y la tabla a 0 filas lo confirmó.
- **Queda `app/services/consultas_organismos.py` como servicio sin caller**, el único del proyecto en esa situación y a propósito. Conserva el contrato `(jsonify, status)` del blueprint muerto en vez de `ResultadoMutacion`: al reconectar la UI de consultas, esa conversión es el primer paso, y está anotada en su docstring.
- **Dependencia futura que sigue sin issue propio** (heredada de #28): la ampliación del modelo `Usuario` con los campos que exigen la automatización de bandeja y Notific@. De ella cuelga #773, y a su alrededor orbitan #757, #758 y #659.

**Nota de #766 que sigue viva** (no está en su issue): la "redacción única" de la ayuda de `ESPERAR_PLAZO` es **convención, no mecanismo**. No existe en el proyecto ningún canal de copy compartido entre Jinja y React, así que hay dos constantes `AYUDA_PRODUCIDO_ESPERAR_PLAZO` gemelas (`app/modules/tareas_y_subidas/routes.py` y `Despensa.jsx`) que se nombran mutuamente en su comentario; montar un origen único para una frase no compensaba, pero con una tercera superficie sí tocaría. #28 lo confirmó por el lado contrario: cuando productor y renderizador son ambos Python (inspector = fragmento Jinja del backend, ADR-023), el "un solo sitio" sale estructural y no hay convención que recordar.

**Próximo: se entra en el foco de `ANÁLISIS_SOLICITUD`**, tras dos turnos consecutivos fuera de él. La auditoría de la fase (2026-08-08) cerró la duda de cuánto quedaba: **toda la cadena de diseño está cerrada** (#248, #192/#408/#583, #594/#581, #440/#441/#593, #442/#392, #406/#495, #455, #582, #679/#711/#714/#724/#765, #764) y el armazón está entero. Lo que falta no es armazón: son dos bugs con consecuencia jurídica, un trámite hueco, contenido de catálogo y cola barata. La fase es casi universal en `ESTRUCTURA_ESF.md` —es la puerta de entrada de casi todo tipo de solicitud—, así que lo que falle aquí falla en todas partes.

Cola por criticidad, no por tamaño:

1. **#778** — la suspensión del art. 22 LPACAP no tiene tope: con un requerimiento sin respuesta, el expediente **nunca vence**. El caso que más urge detectar es el que el sistema oculta. Afecta también a `SOLICITUD_INFORME`/`CONSULTA_SEPARATA`/`SOLICITUD_COMPATIBILIDAD` (tope de 3 meses del art. 22.1.d). Prerrequisito de #781.
2. **#779** — el vencimiento del plazo de subsanación está tipificado `PERDIDA_TRAMITE` (art. 73.3) cuando el art. 68.1 produce **desistimiento**: se comunica al técnico una consecuencia falsa, y no existe el efecto correcto en `efectos_plazo`. Mismo escenario que #778 y mucho más barato.
3. **#776** — `COMUNICACION_INICIO` existe en catálogo, el motor lo gobierna (regla 35) y está **hueco**: sin Context Builder ni plantilla. No es informativo: es el escrito con el que el promotor acredita el **Hito 1 del RD-ley 23/2020** ante el gestor de red, y de no emitirlo se siguen caducidad de sus permisos de acceso y ejecución de garantías.
4. **#777** — `condiciones_requisito` está a 0 filas: los 9 requisitos se exigen siempre, incluidos los que su propia prosa condiciona ("cuando sea persona jurídica", "mediante representante"). Contamina `todos_cubiertos` y, por `tasa_impagada`, al motor. Requiere variable nueva y decidir cómo se marca "no aplica".
5. **#780** — el permiso de acceso y conexión no se comprueba, aunque es **condición de admisión a trámite** de la AAP renovable: se puede tramitar entera una solicitud inadmisible. Pide decisión de diseño (requisito / regla de motor / inadmisión) antes de código.
6. **#698** — el `ANY` del nombre sugerido. Verificado más amplio de lo que dice el issue: `nombre_en_plantilla` es NULL en la fase *y en los tres trámites*. Carlos tiene ideas que cambian algo el concepto.
7. **#367** — asociar documento a tarea en el momento de la subida; el pool es la entrada del `ANALISIS_DOCUMENTAL`.
8. **#781** — la ampliación de 5 días del art. 68.1 no se puede reflejar. Latente hoy; en cuanto #778 aplique el tope, se vuelve error de cómputo real. Va detrás de #778 por eso.
9. **#782** — cinco filas de `catalogo_plazos` con `norma_origen` en `PLACEHOLDER` pese a que el peinado ya está hecho; incluye resolver si el anuncio cita el art. 125 o el 131.
10. **#783** — `TipoResultadoFase.DESISTIDA` se llama "por el Solicitante" y también cubre el art. 68.1, que no es voluntario. Coordinar vocabulario con #779.

**Necesarios pero no bloqueantes** (recorte acordado con Carlos, 2026-08-08): **#751** (helper de UI), **#595** (bastan unos cuantos ítems técnicos para ejercitar lógica e interfaz, no el poblado completo — hoy hay 2 filas), **#444** (limitado a `requerimiento_subsanacion.docx`: la fila ya existe en BD apuntando a un fichero inexistente), **#555** (solo esa plantilla).

**Fuera del foco:** #607 aplazado · #572 va con el compilador de expediente para recurso/contencioso · #568 diferido (sin casos en años) · #306/#428/#304 son helpers · #743, #570 (emparejable con #755) en la cola general · #773 espera la ampliación de `Usuario` · ADR-021 y #644-648 aparcados.

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
