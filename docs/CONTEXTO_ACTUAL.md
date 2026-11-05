# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#1009** (2026-11-05, PR #1086): las plantillas y los fragmentos de escritos viven en el almacén y se suben desde el navegador (pestañas «Plantillas» y «Fragmentos» de `/plantillas/`). Una plantilla sin fichero no se puede activar (`CHECK` en BD) y un fragmento ausente detiene la generación. Fuera el explorador del servidor, `bddat-explorador://`, `scripts/cliente/` y `PLANTILLAS_BASE`. Un fragmento sirve a un solo formato (no se mezclan `.odt` y `.docx`); el motor de Word se mantiene. La semilla de tests y la de la BD de la nube registran plantillas de demostración (`DEMO_*`, `scripts/plantillas_demo.py`, que también se ejecuta a mano), así que un expediente dummy genera escritos por la ruta real; las ELABORAR de los dummies ya están ejecutadas, y para generar desde la interfaz hay que crear un trámite y una ELABORAR nuevos. Diseño en [`ADR-050`](decisiones/ADR-050-almacen-documental-privado-por-contenido.md) §J; detalle en [`ESTADO_ADR050.md`](diseño/ESTADO_ADR050.md).

**Próximo:** el objetivo vivo es llevar en el navegador un expediente **AAP+AAC+DUP** de principio a fin, con **organismos a consultar** y **notificación a los propietarios** (Carlos, 05/11/2026; es el caso habitual según `ESTRUCTURA_ESF.md`). En lugar de seguir las cadenas de los ADR, se trabaja **por tramos del procedimiento**, en este orden *(propuesta del 05/11/2026; el orden de las piezas dentro de cada tramo, sin confirmar)*. Para el ensayo basta la resolución conjunta (`RESOLUCION` + `RESOLUCION_DUP`). El registro de cada cadena sigue en [`ESTADO_ADR049.md`](diseño/ESTADO_ADR049.md), [`ESTADO_ADR053.md`](diseño/ESTADO_ADR053.md) y [`ESTADO_ADR050.md`](diseño/ESTADO_ADR050.md).

1. **Entrada y consultas** (fases ANALISIS_SOLICITUD y CONSULTAS)
   - **#1040**: el proyecto subido sin ser principal se admite y después bloquea el certificado de fin de instrucción.
   - **#1078**: alta de un organismo consultado desde la interfaz (el backend está hecho). Sin él, la resolución no notifica a ningún organismo y nada avisa.
   - **#652**: traslados al titular y al organismo (art. 147 RD 1955/2000; obligatorios ante una objeción).
   - **#982**: el silencio de un organismo (art. 146.1: sin objeción) cierra su consulta sin forzar la fase.
2. **Publicaciones y cierre de la instrucción** (fases INFORMACION_PUBLICA, RESOLUCION y RESOLUCION_DUP)
   - **#994**: remisión a boletín. La `NOTIFICAR` de `ANUNCIO_BOJA`, `ANUNCIO_BOP`, `PUBLICACION` y `PUBLICACION_BOP/BOJA/BOE` no tiene documento de salida, y no se puede terminar por el circuito normal.
   - **#1088**: botón del certificado de plazo cumplido: la segunda espera de los cuatro `ANUNCIO_*` solo tiene la ruta `generar_cert`, sin pantalla.
   - Cerrar las fases de instrucción sin forzar, **diseño conjunto**: **#955**, **#980**, **#805**.
3. **Propietarios** (fases DATOS_CATASTRALES y RESOLUCION_DUP)
   - **#431**: empieza por un hilo de diseño con la norma ya leída (RD 1955/2000, arts. 143.3.e, 144 y 148.2). Hoy nada convierte la RBDA en `interesados_expediente`, y `PROPIETARIOS_DUP` nunca devuelve a nadie.
4. **Ensayo**
   - **#986** (recrear la BD de desarrollo con todos los expedientes-tipo) y un **expediente-tipo AAP+AAC+DUP** (*sin issue*). Lo que falle en el navegador alimenta una lista nueva.
5. **Pre-producción** (después de la ruta)
   - **#1008** (ADR-050): «Exportar expediente». Va antes de producción.
   - **#1012** (ADR-050): papelera. Va después de #1008.
   - **#1010** y **#1011** (ADR-050): al ritmo del despliegue; esperan además la respuesta de la ADA sobre Microsoft 365 (`ESTUDIO_EDICION_ESCRITOS_M365.md`).
   - **#1085**, y el despliegue (#151, #330, #852, #851).
6. **Interfaz** (al ritmo que decida Carlos)
   - **#1039**: la cola de Mi trabajo al listado estándar. **#1041**: los cinco listados fuera del estándar. **Zona E de #929** (sin issue): visibilidad de las notificaciones; se abre después de la Cola.
   - **#1045** (estudio del contrato), **#1046** (huérfano), **#1048** (el alta), **#1080** (alinear los selectores con el contrato de #1038; recoge #1065).

**Sin bloque todavía:** #1079 (revocar una autorización no mira las solicitudes que tienen a esa entidad de representante). **Diferidos a propósito** *(no cortan la ruta con AAP+AAC+DUP; interpretación)*: #997, #998 y #1057.

**Pendientes para el PC:** un escrito real con plantilla (zona A de #929; las reales se suben ahora desde `/plantillas/`) y, para el anuncio del edicto, su plantilla real con `{{ i }}` sobre `interesados_edicto`; y `/sync-derivados` de la fila de `INVENTARIO_BACKEND.md` (zona A de #929); ver [`ESTADO_ADR049.md`](diseño/ESTADO_ADR049.md). **Aparcado:** #1033 y #1034 (ADR-050).

> **Nota para quien actualice este fichero (reenfoque del 11/10/2026, al día el 05/11/2026).** El objetivo vivo es poder llevar un expediente con DUP de principio a fin en el navegador. El hilo era el frontend de las notificaciones de **ADR-049** (#929), cuya zona A se hizo el 11/10. Al analizarlo salió la revisión de la interfaz, que dio **ADR-053** (inspector, listados y documentos), cuya cadena (#1041 a #1051) se puso delante de las demás zonas de #929; de ella están hechas #1042 (13/10) y #1043 (18/10); #1055, que salió de #1042, se hizo el 18/10, y #1047, el 19/10. De las zonas de #929 están hechas también la D (#1038, el 23/10) y la C (#1037, el 30/10). Del bloque de documentos, #1044 se hizo el 01/11 y #1009 el 05/11 (adelantado por Carlos). **ADR-050** sigue aparcado en sus fases 2b y 4 a 7: no se pasa a él sin preguntar a Carlos. Al cerrar un issue, el «Próximo» sale de la lista de arriba y, agotada, de `ESTADO_ADR053.md` y de `ESTADO_ADR049.md`. Reenfoque del 05/11/2026: el «Próximo» pasa de bloques por cadena de ADR a tramos del procedimiento, con AAP+AAC+DUP como expediente de referencia; el orden de los tramos se propuso ese día y se decide paso a paso con Carlos.
