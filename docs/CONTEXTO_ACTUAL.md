# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** **#849.A — la suite ya tiene base de datos propia** ([PR #857](https://github.com/genete/bddat/pull/857)). De 50 skips a 19, y la instalación desde cero —rota sin que nadie lo supiera— vuelve a funcionar. El interruptor que apunta la suite a esa base espera a #849.B. La reconstrucción limpia de las migraciones y el curado del catálogo son **#856** (M4).

**Próximo:**

1. **#428 — el wizard debe exigir el documento de la solicitud.** Hoy **nadie** asigna `documento_solicitud_id`, así que ninguna solicitud tiene la fecha que ancla el procedimiento: el plazo del art. 128 consta `SIN_PLAZO` en todos los expedientes. Su dependencia (#374) está cerrada desde mayo.
2. **#849.B — semilla de datos de negocio.** Detrás de #428 porque la semilla se crea con `alta_expediente()`. Al cerrar, el interruptor pasa a la base de tests y se comprueban los seis criterios del issue.
3. **Ampliar el catálogo de expedientes-tipo**, para poder trabajar en **consultas** con comodidad. En espera hasta que el 2 esté cerrado: los expedientes-tipo *son* la semilla, y construirlos antes obligaría a rehacerlos. El de #824 deja el patrón para las fechas: base derivada de `hoy()`, ventana en `catalogo_expedientes.csv`, ninguna fecha absoluta en el script.

**Aviso operativo:** el reloj de desarrollo sigue en **2026-08-10** —lo deja ahí el script del expediente-tipo— y con el bloqueo activo un reloj atrasado impide fechar en el presente (`flask reloj show` / `clear`).

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
