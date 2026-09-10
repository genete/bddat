# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#907 (PR #908, mergeado 2026-09-10) — el listado de seguimiento (`GET /api/expedientes/seguimiento`) elimina el N+1 de `estado_solicitud()`.** `_acc_fase`/`_acc_tramite` (`seguimiento.py`) recorrían `fase.tramites`/`tramite.tareas` sin eager-loading; la query principal del endpoint ahora reutiliza `opciones_solicitud()` (`arbol_expediente.py`, pública desde #827), dejando la solicitud ya precargada en el identity map de la sesión cuando `estado_solicitud()` la vuelve a pedir. Medido con instrumentación real (SQL + tiempo colgados del proceso Flask, no una réplica): 237→27 sentencias SQL, ~379→~169 ms para el usuario CLG/TRAMITADOR (7 filas). Sin cambios en `seguimiento.py`.

**#909 (PR #910, mergeado 2026-09-10) — `flask_console.py` ya no puede bloquear el propio servidor Flask por el eco SQL.** Diagnosticado en la misma sesión: con `SQLALCHEMY_ECHO=True` (desarrollo), la consola Tkinter de `flask_console.py` lee stdout línea a línea e inserta cada una con parseo ANSI + autoscroll — si el volumen de eco supera lo que ese hilo consume, el pipe se llena y Flask se bloquea escribiendo (backpressure del SO). Medido: misma petición, ~400 ms con log a fichero vs. 3.650 ms con la consola real — nada que ver con el modo `debug`/reloader, ya descartado. Nuevo checkbox "Mostrar SQL en consola", desmarcado por defecto, que fija `SQLALCHEMY_ECHO` antes de lanzar `run.py`. El efecto general ya estaba anotado en `ANALISIS_ESCALABILIDAD.md` §6.1 para el panel del supervisor (#850); aquí se confirmó que aplica a cualquier pantalla.

**Próximo:** por decidir en la próxima sesión — la cadena de ADR-044 queda cerrada y no hay nada encolado todavía.

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
