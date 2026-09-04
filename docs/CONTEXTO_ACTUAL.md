# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** **#827 — el certificado de fin de instrucción, la bisagra hacia la resolución.** [PR #841](https://github.com/genete/bddat/pull/841). El generador de #373 deja de estar desconectado —sus únicos invocadores eran los tests— y el `CERT_FIN_INSTRUCCION` se emite de verdad, como acto expreso del técnico y solo cuando la revisión sale sin pendientes. El diseño está en ADR-043 (§E reescrita, y §E bis/§E ter precisadas con lo que salió al implementarlo). Lo que no está allí y conviene tener a mano: **los 3 fallos de `test_765::TestBypassEnPatchDeFase` siguen vivos y son de datos** —cogen la primera fase del expediente seed y la asumen abierta—, y la tarea de fondo para desacoplarlos esperaba justamente este merge.

**Próximo:**

1. **#838 — el sello de la instrucción** (ADR-043 §F, primera pieza). Ya tiene su ancla: emitido el certificado, reabrir una fase de instrucción y crear una nueva son el mismo acto por sus dos extremos, y el mismo check los cubre. **Entra solo**: el trámite de actuaciones complementarias del art. 87 ([#839](https://github.com/genete/bddat/issues/839)) no va con él, ver abajo. Al abordarlo hay que decidir qué hacer mientras ese trámite no exista — §F lo plantea como puerta cerrada estructural, y sin el art. 87 la única salida ante un expediente gris es la que el sello prohíbe.
2. **#824 — fecha administrativa a futuro.** Deuda reciente. Afecta a producción pero no bloquea la construcción de expedientes.

Después, **ampliar el catálogo de expedientes-tipo**, con un objetivo concreto: poder trabajar en **consultas** con comodidad. Es la continuación natural del foco, que ha ido fase a fase —análisis de solicitud primero, consultas ahora—, y lo que se construye para eso son los scripts de `scripts/expedientes_dummy/`. La confianza que da un expediente-tipo alcanza solo a lo que ejercita: hoy, AAP+AAC exento sin IP ni consultas, con dos vueltas dentro de plazo.

**Por qué #839 no va con #838.** El art. 87 es una particularidad de la **fase de resolución**, y esa fase tiene esa y muchas más. Se aborda cuando el foco llegue ahí, no como apéndice del sello. Mismo criterio con el que se han ido abriendo las fases anteriores.

**Fuera del foco:** #607 aplazado · #572 va con el compilador de expediente para recurso/contencioso · #568 diferido (sin casos en años) · #306/#428/#304 son helpers · #743, #570 (emparejable con #755) en la cola general · #773 espera la ampliación de `Usuario` · ADR-021 y #644-648 aparcados.

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
