# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** **#862 — segundo expediente-tipo: `CONSULTAS_VARIOS_ESTADOS`** ([PR #866](https://github.com/genete/bddat/pull/866)). Línea aérea 66 kV en Jerez de la Frontera (AAP+AAC, exenta, sin IP) con tres organismos consultados y la foto tomada a 40 días hábiles de notificar las separatas: silencio vencido sin analizar, ciclo cerrado con condicionados y traslado al titular todavía corriendo. El escenario se construye **hacia atrás desde hoy** —el ancla es la notificación, no el alta—, que es lo que decide qué plazos han vencido. Con él se van dos cosas: el `catalogo_expedientes.csv` (la base ya sabe qué expedientes-tipo hay, por la marca `[DUMMY:<CODIGO>]` de `Solicitud.observaciones`, y el CSV solo guardaba la última ejecución) y la duplicación entre scripts, ahora en `scripts/expedientes_dummy/_comun.py`. El catálogo de la carpeta vive en su `README.md`, y los dos expedientes-tipo alimentan ya la base de tests ([PR #867](https://github.com/genete/bddat/pull/867)) — no por cobertura, que ningún test los usa todavía, sino para que `preparar_bd_test.py --recrear` falle en el acto el día que un cambio de la aplicación rompa uno de los scripts. · **#863 — la condición de `DR_NO_DUP` estaba invertida** ([PR #865](https://github.com/genete/bddat/pull/865)): se exigía cuando la solicitud incluye DUP, y es al revés — la declaración de *no* necesidad se presenta cuando no se pide. En un expediente sin DUP el requisito no salía en el checklist y el documento se quedaba en el pool sin nada a lo que casarse.

**Próximo:**

1. **El expediente-tipo del modificado de proyecto**, que es el que falta para trabajar la segunda ronda —de consultas y de información pública— y el que obliga a decidir cómo se modela: una sola fase `ANALISIS_SOLICITUD` con varios `ANALISIS_DOCUMENTAL`, o varias fases. Esa decisión es **#819** (asociar consultas e IP al conjunto documental del proyecto y sus modificados) y es **requisito previo**, no una consecuencia: sin ella no se puede escribir el escenario ni la variable que necesita **#864** — la advertencia al abrir una fase con `ANALISIS_SOLICITUD` sin cerrar, diferida por lo mismo (una variable ingenua cogería la fase cerrada del proyecto original y callaría justo en la ronda del modificado).

**Ciclo de trabajo nuevo (#849):** tras cualquier migración que toque catálogo,
`scripts/preparar_bd_test.py --recrear` reconstruye la base de tests y
`scripts/comparar_catalogo.py` comprueba que sigue coincidiendo con desarrollo
—por contenido, no por conteos—. Si el comparador señala una divergencia, es la
migración la que hay que arreglar, no la base.

**Nota sobre el reloj de desarrollo:** el expediente-tipo de #862 lo **borra al terminar**, así que la base queda a fecha real y sus plazos se ven correr. El de #814 sigue dejándolo fijado en la última fecha de su escenario; si tras ejecutarlo la aplicación no deja fechar en el presente, es eso (`flask reloj show` / `clear`).

**Por qué #839 sigue sin foco.** El art. 87 es una particularidad de la **fase de resolución**, y esa fase tiene esa y muchas más; se aborda cuando el foco llegue ahí. Lo que #838 aclaró es que **ya no bloquea a nadie**: sin ese trámite la salida existe igual —dentro de la fase que resuelve, forzando el vocabulario, con constancia en bitácora—, y esa constancia es precisamente la señal de cuándo hace falta construirlo (ADR-043 §F bis).

**Fuera del foco:** #607 aplazado · #572 va con el compilador de expediente para recurso/contencioso · #568 diferido (sin casos en años) · #306/#304 son helpers —#428 estaba en esta lista y era un error de clasificación: no es un helper, es el ancla documental de la fecha de solicitud, y se cerró como tal— · #743, #570 (emparejable con #755) en la cola general · #773 espera la ampliación de `Usuario` · ADR-021 y #644-648 aparcados.

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
