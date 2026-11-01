# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#1044** (2026-11-01, PR #1083): la fila común de documento en los inspectores. Una función del servidor (`detalle_nodo.documento_fila`) y dos renderizadores, el macro Jinja (la Cola ya pinta el subrol y abre diagnósticos y certificados en el modal) y el componente React; en el árbol, una sola lista de vinculados que en edición sale del borrador y lleva «Quitar vínculo», y el pool de la Despensa como selector. La fila son dos líneas: fichero y fecha arriba; debajo, iconos (rol, subrol, marcas, todos con tooltip) y la descripción. Incluye la mitad de la Despensa de #1036: el catálogo de tipos dice cuáles exigen fecha y el formulario de subida la exige y autorrellena la de los justificantes de Notifica. Sin migraciones: en el PC, recompilar React y reiniciar Flask. Diseño en el anexo a [`ADR-053`](decisiones/ADR-053-interfaz-inspector-listados-y-documentos.md) §E (con sus *Interpretación* por confirmar); detalle en [`ESTADO_ADR053.md`](diseño/ESTADO_ADR053.md).

**Próximo:** el objetivo vivo es llevar un expediente con DUP de principio a fin en el navegador. Quedan tres cadenas abiertas ([`ESTADO_ADR049.md`](diseño/ESTADO_ADR049.md): el frontend de las notificaciones; [`ESTADO_ADR053.md`](diseño/ESTADO_ADR053.md): la interfaz; [`ESTADO_ADR050.md`](diseño/ESTADO_ADR050.md): el almacén documental, con sus fases 2b y 4 a 7 aparcadas). En lugar de terminarlas una a una, se trabaja **por bloques según lo que desbloquea cada pieza**, en este orden *(propuesta del 18/10/2026; el orden de las piezas dentro de cada bloque, sin confirmar)*:

1. ~~**Cerrar el árbol**~~ Hecho.
   - ~~**#1055**: «Cerrar» sin aviso en los bloques interiores.~~ Hecho (PR #1073).
   - ~~**#1047**: registro de editores por tipo, que sustituye las banderas de `InspectorEdicion` (`superficiesTarea.js` es su germen).~~ Hecho (PR #1075).
2. ~~**Notificaciones, lo que ya está libre**~~ Hecho.
   - ~~**#1038** (zona D de #929): representante y sede de la solicitud.~~ Hecho (PR #1081).
   - ~~**#1037** (zona C de #929): marcar las notificaciones que van por edicto y aplicar el anuncio.~~ Hecho (PR #1082).
3. **Documentos y pool**. **Bloque en curso** (confirmado por Carlos el 01/11/2026, con el orden de las piezas).
   - ~~**#1044**: mini-listados de documentos, con la fila común de tres modos.~~ Hecho (PR #1083).
   - **#881**: listado del pool al estándar, con la mitad del pool de **#1036** (fecha del justificante) dentro; la mitad de la Despensa ya está hecha en #1044.
   - **#1008** (ADR-050): «Exportar expediente». El sitio del botón depende de #881. Va antes de producción.
   - **#1012** (ADR-050): papelera. Va después de #881 y de #1008 (usa sus tareas diarias y su marca de manifiesto).
   - **#1009** (ADR-050): plantillas y fragmentos al almacén. Va antes de producción. No depende de las anteriores: al final del bloque, salvo presión de producción.
4. **Cola y listados**
   - **#1039**: la cola de Mi trabajo al listado estándar.
   - **#1041**: los cinco listados fuera del estándar.
   - **Zona E de #929** (sin issue): visibilidad de las notificaciones; se abre después de la Cola.

**Sin bloque todavía:** #1045 (estudio del contrato), #1046 (huérfano), #1048 (el alta), #1079 (revocar una autorización no mira las solicitudes que tienen a esa entidad de representante), #1080 (alinear los selectores con el contrato de #1038; recoge #1065) y #1010, #1011 (ADR-050, al ritmo del despliegue). **Pendientes para el PC:** aplicar la migración `1037_marca_edicto_notificacion`; un escrito real con plantilla (zona A de #929) y, para el anuncio del edicto, su plantilla real con `{{ i }}` sobre `interesados_edicto`; y `/sync-derivados` de la fila de `INVENTARIO_BACKEND.md` (zona A de #929); ver [`ESTADO_ADR049.md`](diseño/ESTADO_ADR049.md). **Aparcado:** #1033 y #1034 (ADR-050).

> **Nota para quien actualice este fichero (reenfoque del 11/10/2026, al día el 01/11/2026).** El objetivo vivo es poder llevar un expediente con DUP de principio a fin en el navegador. El hilo era el frontend de las notificaciones de **ADR-049** (#929), cuya zona A se hizo el 11/10. Al analizarlo salió la revisión de la interfaz, que dio **ADR-053** (inspector, listados y documentos), cuya cadena (#1041 a #1051) se puso delante de las demás zonas de #929; de ella están hechas #1042 (13/10) y #1043 (18/10); #1055, que salió de #1042, se hizo el 18/10, y #1047, el 19/10. De las zonas de #929 están hechas también la D (#1038, el 23/10) y la C (#1037, el 30/10). Del bloque de documentos, #1044 se hizo el 01/11. **ADR-050** sigue aparcado en sus fases 2b y 4 a 7: no se pasa a él sin preguntar a Carlos. Al cerrar un issue, el «Próximo» sale de la lista de arriba y, agotada, de `ESTADO_ADR053.md` y de `ESTADO_ADR049.md`. El orden de los bloques del «Próximo» se propuso el 18/10 y se decide paso a paso con Carlos.
