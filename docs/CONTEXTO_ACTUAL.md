# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#1042** (2026-10-13, PR #1056): el marco único del inspector. El shell pinta la barra (ver / editar, Guardar, Cancelar / Cerrar) para el árbol y los 17 inspectores Jinja, y el cuerpo hace scroll horizontal por debajo del ancho mínimo de cada caso (cifras confirmadas por Carlos, medidas con barras de scroll clásicas). El contrato está en [`GUIA_COMPONENTES_INTERACTIVOS.md`](guias/GUIA_COMPONENTES_INTERACTIVOS.md), §«Marco único del inspector». Abierto aparte: **#1055** («Cerrar» descarta sin avisar lo escrito en los bloques interiores del árbol).

**Próximo:** la cadena de interfaz de **ADR-053** (adoptado el 13/10/2026), con el marco del inspector ya hecho; la siguiente pieza está **por confirmar con Carlos** (el orden propuesto está en [`ESTADO_ADR053.md`](diseño/ESTADO_ADR053.md)). Con ella siguen pendientes las demás zonas de #929 (**#1036**, **#1037**, **#1038** y la zona E, sin issue) y los dos restos de la zona A que quedan para el PC; ver [`ESTADO_ADR049.md`](diseño/ESTADO_ADR049.md). **Aparcado:** las fases 4 a 7 de ADR-050 (#1008 a #1012), que consumen piezas de esa cadena; ver [`ESTADO_ADR050.md`](diseño/ESTADO_ADR050.md).

> **Nota para quien actualice este fichero (reenfoque del 11/10/2026).** El objetivo vivo es poder llevar un expediente con DUP de principio a fin en el navegador. El hilo era el frontend de las notificaciones de **ADR-049** (#929), cuya zona A se hizo el 11/10. Al analizarlo salió la revisión de la interfaz, que dio **ADR-053** (inspector, listados y documentos): su cadena de issues (#1041 a #1051) va ahora delante de las demás zonas de #929. **ADR-050** queda aparcado hasta nuevo aviso de Carlos. Al cerrar un issue, el «Próximo» sale de `ESTADO_ADR053.md` y, agotado, de `ESTADO_ADR049.md`; no se pasa a ADR-050 sin preguntar. De `ESTADO_ADR053.md`, #1042 fue la primera pieza y está hecha (13/10); el resto del orden sigue siendo una propuesta sin confirmar, y la zona E de #929 (visibilidad) se propuso para después del marco y de la Cola.
