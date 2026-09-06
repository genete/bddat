# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** **#849.B — la suite corre contra su propia base** ([PR #860](https://github.com/genete/bddat/pull/860)). **1680 pasan, 0 saltados, 0 fallos**, y el tope de skips baja a 0. Los seis criterios del issue, comprobados —incluidos determinismo (tres pasadas, una tras `--recrear`) y estanqueidad (huella de la BD de desarrollo y del árbol de ficheros, idéntica antes y después)—. Por el camino apareció algo que la fase A daba por bueno: **el catálogo que producen las migraciones no era el de desarrollo**, y no fallaba —once divergencias, entre ellas una regla del motor que dejaba abrir RESOLUCION sin IP concluida en un `AAC+DUP`, seis plazos con la cita en PLACEHOLDER y `nombre_en_plantilla` cruzado en 30 filas—. Las corrige `849_catalogo_replicado` por clave natural, y `scripts/comparar_catalogo.py` es la comprobación reutilizable. Queda dicho en `REGLAS_DESARROLLO.md`: una migración de datos nunca localiza la fila por `id`, y el curado de estructurales va por migración, nunca a mano.

Antes: **#428 — el wizard debe exigir el documento de la solicitud** ([PR #858](https://github.com/genete/bddat/pull/858)). La columna `documento_solicitud_id` es NOT NULL, las dos vías de alta escriben el ancla y el plazo del art. 128 corre. El wizard de 3 pasos se retira en favor de un formulario único. · **#849.A — la suite ya tiene base de datos propia** ([PR #857](https://github.com/genete/bddat/pull/857)): la instalación desde cero, rota sin que nadie lo supiera, vuelve a funcionar. La reconstrucción limpia de las migraciones y el curado del catálogo siguen siendo **#856** (M4).

**Próximo:**

1. **Ampliar el catálogo de expedientes-tipo**, para poder trabajar en **consultas** con comodidad (#862 — `CONSULTAS_VARIOS_ESTADOS`). Ya no está bloqueado: los expedientes-tipo *son* la semilla, y la semilla ya existe. El de #824 deja el patrón para las fechas —base derivada de `hoy()`, ninguna fecha absoluta en el script— y desde #849.B también el de la doble vida: `main(app, efectos_desarrollo=False)`, para que cada expediente-tipo nuevo sirva a la vez de escenario en desarrollo y de semilla de la base de tests.

**Ciclo de trabajo nuevo (#849):** tras cualquier migración que toque catálogo,
`scripts/preparar_bd_test.py --recrear` reconstruye la base de tests y
`scripts/comparar_catalogo.py` comprueba que sigue coincidiendo con desarrollo
—por contenido, no por conteos—. Si el comparador señala una divergencia, es la
migración la que hay que arreglar, no la base.

**Aviso operativo:** el reloj de desarrollo sigue en **2026-08-12** —lo deja ahí el script del expediente-tipo, que hoy generó **AT-29** y dejó AT-28 en `[RECICLAR]`— y con el bloqueo activo un reloj atrasado impide fechar en el presente (`flask reloj show` / `clear`).

**Por qué #839 sigue sin foco.** El art. 87 es una particularidad de la **fase de resolución**, y esa fase tiene esa y muchas más; se aborda cuando el foco llegue ahí. Lo que #838 aclaró es que **ya no bloquea a nadie**: sin ese trámite la salida existe igual —dentro de la fase que resuelve, forzando el vocabulario, con constancia en bitácora—, y esa constancia es precisamente la señal de cuándo hace falta construirlo (ADR-043 §F bis).

**Fuera del foco:** #607 aplazado · #572 va con el compilador de expediente para recurso/contencioso · #568 diferido (sin casos en años) · #306/#304 son helpers —#428 estaba en esta lista y era un error de clasificación: no es un helper, es el ancla documental de la fecha de solicitud (ver Hecho)— · #743, #570 (emparejable con #755) en la cola general · #773 espera la ampliación de `Usuario` · ADR-021 y #644-648 aparcados.

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
