# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#922** (2026-10-09, PR #1035): barras del plazo de resolver por acto en el árbol y el inspector. El alcance y las decisiones están en el PR y en [`MODELO_ESTADOS_SEMAFORO.md`](referencia/MODELO_ESTADOS_SEMAFORO.md) §9. Los plazos de los actos siguen sin entrar en los contadores del árbol, el semáforo de la solicitud ni el KPI del supervisor: otro asunto, anotado en §11.

**Próximo:** **#929 zona A** (tramitar una `NOTIFICAR` en el navegador): es lo que falta para un expediente DUP completo. #929 se partió el 09/10 en zonas A–E; ver [`ESTADO_ADR049.md`](diseño/ESTADO_ADR049.md). Detrás, la cadena de interfaz de ADR-053 (propuesta), empezando por el marco del inspector (#1042); el orden está en [`ESTADO_ADR053.md`](diseño/ESTADO_ADR053.md). **Aparcado:** las fases 4 a 7 de ADR-050 (#1008 a #1012), que consumen piezas de esa cadena; ver [`ESTADO_ADR050.md`](diseño/ESTADO_ADR050.md).

> **Nota para quien actualice este fichero (reenfoque del 11/10/2026).** El objetivo vivo es poder llevar un expediente con DUP de principio a fin en el navegador. El hilo es el frontend de las notificaciones de **ADR-049** (#929). Al analizar #929 salió la revisión de la interfaz, que dio **ADR-053** (inspector, listados y documentos): es un desvío nacido de #929 y su cadena de issues (#1041 a #1051) va **detrás** de la zona A, no delante. **ADR-050** queda aparcado hasta nuevo aviso de Carlos. Al cerrar un issue, el «Próximo» sale de `ESTADO_ADR049.md` y, agotado, de `ESTADO_ADR053.md`; no se pasa a ADR-050 sin preguntar. El orden de `ESTADO_ADR053.md` es una propuesta sin confirmar, y la zona E de #929 (visibilidad) no tiene issue y se propuso para después del marco y de la Cola.
