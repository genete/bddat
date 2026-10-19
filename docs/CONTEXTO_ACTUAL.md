# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#1047** (2026-10-19, PR #1075): el inspector del árbol decide lo que lleva cada nodo con un registro de editores (`registroEditores.jsx`) y no con banderas en `InspectorEdicion`: cada tipo de nodo y cada superficie de tarea declara sus tarjetas, acciones, modales, Despensa y si se borra, y añadir un tipo o una acción ya no toca `Inspector.jsx`. Lo decidido al implementar (las acciones de la solicitud y la fase en `AccionesNodo.jsx`; `visible` pasado a `hay`) sigue marcado como *interpretación*, pendiente de confirmar por Carlos, en [`ESTADO_ADR053.md`](diseño/ESTADO_ADR053.md); el patrón, en [`GUIA_REACT_ISLAS.md`](guias/GUIA_REACT_ISLAS.md). Con los datos sintéticos de la nube quedaron comprobados en pantalla los tres casos que #1055 dejó sin comprobar (ítem técnico y destinatario con selector de NOTIFICAR y de ELABORAR).

**Próximo:** el objetivo vivo es llevar un expediente con DUP de principio a fin en el navegador. Quedan tres cadenas abiertas ([`ESTADO_ADR049.md`](diseño/ESTADO_ADR049.md): el frontend de las notificaciones; [`ESTADO_ADR053.md`](diseño/ESTADO_ADR053.md): la interfaz; [`ESTADO_ADR050.md`](diseño/ESTADO_ADR050.md): el almacén documental, con sus fases 2b y 4 a 7 aparcadas). En lugar de terminarlas una a una, se trabaja **por bloques según lo que desbloquea cada pieza**, en este orden *(propuesta del 18/10/2026; el orden de las piezas dentro de cada bloque, sin confirmar)*:

1. ~~**Cerrar el árbol**~~ Hecho.
   - ~~**#1055**: «Cerrar» sin aviso en los bloques interiores.~~ Hecho (PR #1073).
   - ~~**#1047**: registro de editores por tipo, que sustituye las banderas de `InspectorEdicion` (`superficiesTarea.js` es su germen).~~ Hecho (PR #1075).
2. **Notificaciones, lo que ya está libre**
   - **#1038** (zona D de #929): representante y sede de la solicitud. La tarjeta «Solicitante» ya está preparada.
   - **#1037** (zona C de #929): aplicar el anuncio del edicto a las notificaciones agotadas.
3. **Documentos y pool**
   - **#1044**: mini-listados de documentos, con la fila común de tres modos. Unifica los documentos que hoy salen repetidos en el inspector.
   - **#881**: listado del pool al estándar, con **#1036** (fecha del justificante) dentro o antes.
   - **#1012** (ADR-050): papelera. Va después de #881.
   - **#1008** (ADR-050): «Exportar expediente». El sitio del botón depende de #881. Va antes de producción.
   - **#1009** (ADR-050): plantillas y fragmentos al almacén. Va antes de producción.
4. **Cola y listados**
   - **#1039**: la cola de Mi trabajo al listado estándar.
   - **#1041**: los cinco listados fuera del estándar.
   - **Zona E de #929** (sin issue): visibilidad de las notificaciones; se abre después de la Cola.

**Sin bloque todavía:** #1045 (estudio del contrato), #1046 (huérfano), #1048 (el alta) y #1010, #1011 (ADR-050, al ritmo del despliegue). **Pendientes para el PC:** un escrito real con plantilla y `/sync-derivados` de la fila de `INVENTARIO_BACKEND.md` (zona A de #929); ver [`ESTADO_ADR049.md`](diseño/ESTADO_ADR049.md). **Aparcado:** #1033 y #1034 (ADR-050).

> **Nota para quien actualice este fichero (reenfoque del 11/10/2026, al día el 19/10/2026).** El objetivo vivo es poder llevar un expediente con DUP de principio a fin en el navegador. El hilo era el frontend de las notificaciones de **ADR-049** (#929), cuya zona A se hizo el 11/10. Al analizarlo salió la revisión de la interfaz, que dio **ADR-053** (inspector, listados y documentos), cuya cadena (#1041 a #1051) se puso delante de las demás zonas de #929; de ella están hechas #1042 (13/10) y #1043 (18/10); #1055, que salió de #1042, se hizo el 18/10, y #1047, el 19/10. **ADR-050** sigue aparcado en sus fases 2b y 4 a 7: no se pasa a él sin preguntar a Carlos. Al cerrar un issue, el «Próximo» sale de la lista de arriba y, agotada, de `ESTADO_ADR053.md` y de `ESTADO_ADR049.md`. El orden de los bloques del «Próximo» se propuso el 18/10 y se decide paso a paso con Carlos.
