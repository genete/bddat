# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#907 (PR #908, mergeado 2026-09-10) — el listado de seguimiento (`GET /api/expedientes/seguimiento`) elimina el N+1 de `estado_solicitud()`.** `_acc_fase`/`_acc_tramite` (`seguimiento.py`) recorrían `fase.tramites`/`tramite.tareas` sin eager-loading; la query principal del endpoint ahora reutiliza `opciones_solicitud()` (`arbol_expediente.py`, pública desde #827), dejando la solicitud ya precargada en el identity map de la sesión cuando `estado_solicitud()` la vuelve a pedir. Medido con instrumentación real (SQL + tiempo colgados del proceso Flask, no una réplica): 237→27 sentencias SQL, ~379→~169 ms para el usuario CLG/TRAMITADOR (7 filas). Sin cambios en `seguimiento.py`.

**#909 (PR #910, mergeado 2026-09-10) — `flask_console.py` ya no puede bloquear el propio servidor Flask por el eco SQL.** Diagnosticado en la misma sesión: con `SQLALCHEMY_ECHO=True` (desarrollo), la consola Tkinter de `flask_console.py` lee stdout línea a línea e inserta cada una con parseo ANSI + autoscroll — si el volumen de eco supera lo que ese hilo consume, el pipe se llena y Flask se bloquea escribiendo (backpressure del SO). Medido: misma petición, ~400 ms con log a fichero vs. 3.650 ms con la consola real — nada que ver con el modo `debug`/reloader, ya descartado. Nuevo checkbox "Mostrar SQL en consola", desmarcado por defecto, que fija `SQLALCHEMY_ECHO` antes de lanzar `run.py`. El efecto general ya estaba anotado en `ANALISIS_ESCALABILIDAD.md` §6.1 para el panel del supervisor (#850); aquí se confirmó que aplica a cualquier pantalla.

**Próximo:** el foco sigue en completar la fase DUP en todos sus aspectos — tramitar una DUP, con o sin combinaciones, de principio a fin. **ADR-046 ya está adoptada** (doble acto, `RESOLUCION_DUP` + `DATOS_CATASTRALES`): cierra la pregunta que ADR-045 dejaba abierta, con detalle estructural completo en `DISEÑO_RESOLUCION_DUP.md`. **#911 se cerró, absorbido por #914** — el alta de `AAP+DUP` en `tipos_solicitudes` no podía darse por completa sin decidir antes si `DATOS_CATASTRALES` le aplica también (sí, ADR-046 §Consecuencias), así que pasa a ser una tarea dentro de #914 en vez de un issue propio. Empezamos por **#914**: actualizar primero la fuente de verdad (`ESTRUCTURA_ESF.md`/`.json`, `ESTRUCTURA_FTT.md`/`.json`, hoy en v2.3/v6.3, anteriores a ADR-046) y solo después construir las migraciones. Cadena completa por orden de dependencia: #914+#893 → #891, #892 → #801, #912 → #894; #431 en paralelo. #891, #892, #801, #912 y #894 se re-estudian con el detalle exacto (anclaje de motor, plazo, catálogo de documentos) una vez #914 esté cerrado — hoy sus cuerpos siguen redactados solo contra ADR-045. Detalle de dependencias en ADR-045, ADR-046 y `PRE-ADR-resolucion-doble-acto-dup.md`.

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
