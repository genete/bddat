# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** **#838 — el sello de la instrucción y el acto que lo retira** (ADR-043 §F, primera pieza). [PR #845](https://github.com/genete/bddat/pull/845). El diseño está en el ADR (§F bis y §F ter, escritas al implementarlo). Lo que no está allí ni en los issues y conviene tener a mano:

- **La suite deja 5 fallos vivos, todos por datos de la BD de desarrollo, ninguno de código.** Tres (`test_smoke_pool_documentos` ×2, `test_smoke_expedientes_pool`) por un documento con url `bddat://ui-827` —residuo de las pruebas de #827— que revienta el render del pool con `NotImplementedError`; dos de `test_738` por justificantes huérfanos. Verificado con `git stash` que fallan igual sin la rama. El primer grupo se arregla borrando ese documento, no tocando código.
- **Los datos de prueba de AT-15 cambiaron al verificar:** la solicitud 3570 se quedó **sin** certificado (deshecho a propósito) y la 3572 se recertificó, así que su certificado es el 1006 y no el 978. La 3102 sigue certificada con el 901, que es el caso útil de «certificado anterior a 827b, con `documento_id` a NULL».

**Próximo:**

1. **#824 — fecha administrativa a futuro.** Deuda reciente. Afecta a producción pero no bloquea la construcción de expedientes.
2. Después, **ampliar el catálogo de expedientes-tipo**, con un objetivo concreto: poder trabajar en **consultas** con comodidad. Es la continuación natural del foco, que ha ido fase a fase —análisis de solicitud primero, consultas ahora—, y lo que se construye para eso son los scripts de `scripts/expedientes_dummy/`. La confianza que da un expediente-tipo alcanza solo a lo que ejercita: hoy, AAP+AAC exento sin IP ni consultas, con dos vueltas dentro de plazo.

**Por qué #839 sigue sin foco.** El art. 87 es una particularidad de la **fase de resolución**, y esa fase tiene esa y muchas más; se aborda cuando el foco llegue ahí. Lo que #838 aclaró es que **ya no bloquea a nadie**: sin ese trámite la salida existe igual —dentro de la fase que resuelve, forzando el vocabulario, con constancia en bitácora—, y esa constancia es precisamente la señal de cuándo hace falta construirlo (ADR-043 §F bis).

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
