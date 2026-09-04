# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** **#824 — la fecha administrativa nunca es futura** ([PR #846](https://github.com/genete/bddat/pull/846)). De su verificación salieron tres issues: **#847** (un `bddat://` no contemplado tumba el listado del pool, con los 3 fallos vivos de la suite dentro), **#848** (`Solicitud.estado` llama resuelta a la que solo está entre fases) y la ampliación de **#428**, que pasa a Próximo. Aviso operativo: el reloj de desarrollo quedó en **2026-08-10** —lo deja ahí el script del expediente-tipo—, y con el bloqueo activo un reloj atrasado impide fechar en el presente (`flask reloj show` / `clear`).

**Próximo:**

1. **#428 — el wizard debe exigir el documento de la solicitud.** Sube a prioritario: hoy **nadie** asigna `documento_solicitud_id` (el wizard lo fija a `None`), así que toda solicitud nace sin la fecha que ancla el procedimiento entero — el plazo de resolución consta `SIN_PLAZO` y las suspensiones se restan contra nada. Mientras siga así, cualquier expediente-tipo que construyamos nace cojo, sea del tipo que sea. Su dependencia (#374) está cerrada desde mayo.
2. **Ampliar el catálogo de expedientes-tipo**, con un objetivo concreto: poder trabajar en **consultas** con comodidad. Es la continuación natural del foco, que ha ido fase a fase —análisis de solicitud primero, consultas ahora—, y lo que se construye para eso son los scripts de `scripts/expedientes_dummy/`. La confianza que da un expediente-tipo alcanza solo a lo que ejercita: hoy, AAP+AAC exento sin IP ni consultas, con dos vueltas dentro de plazo. El de #824 deja el patrón a copiar para las fechas: base derivada de `hoy()`, ventana publicada en `catalogo_expedientes.csv`, y ninguna fecha absoluta dentro del script.

**Por qué #839 sigue sin foco.** El art. 87 es una particularidad de la **fase de resolución**, y esa fase tiene esa y muchas más; se aborda cuando el foco llegue ahí. Lo que #838 aclaró es que **ya no bloquea a nadie**: sin ese trámite la salida existe igual —dentro de la fase que resuelve, forzando el vocabulario, con constancia en bitácora—, y esa constancia es precisamente la señal de cuándo hace falta construirlo (ADR-043 §F bis).

**Fuera del foco:** #607 aplazado · #572 va con el compilador de expediente para recurso/contencioso · #568 diferido (sin casos en años) · #306/#304 son helpers —#428 estaba en esta lista y era un error de clasificación: no es un helper, es el ancla documental de la fecha de solicitud (ver Próximo)— · #743, #570 (emparejable con #755) en la cola general · #773 espera la ampliación de `Usuario` · ADR-021 y #644-648 aparcados.

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
