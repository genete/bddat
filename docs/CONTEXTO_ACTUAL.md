# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#982** (2026-11-10, PR #1101, con #1100 de paso): el silencio de un organismo se cierra por la vía limpia en el expediente-tipo `RESOLUCION_CON_ORGANISMOS` (certificado de plazo cumplido en la espera, `ANALIZAR` favorable y `CONSULTAS` sin forzar la fase). El issue se cerró como cubierto por #1098: el catálogo no era lo que impedía cerrar (`crear_cert` no lo mira); lo que falta es la pantalla para emitir el certificado. #1100 arregló de paso la semilla de desarrollo, que no terminaba (el requisito `DR_NO_DUP` en `ANALISIS_DOC_DOS_VUELTAS` y el sentido del diagnóstico en `CONSULTAS_VARIOS_ESTADOS`). Detalle en [`DISEÑO_CONSULTAS_ORGANISMOS.md`](referencia/DISEÑO_CONSULTAS_ORGANISMOS.md) §7, caso A.

**Próximo:** el objetivo vivo es llevar en el navegador un expediente **AAP+AAC+DUP** de principio a fin, con **organismos a consultar** y **notificación a los propietarios** (Carlos, 05/11/2026; es el caso habitual según `ESTRUCTURA_ESF.md`). En lugar de seguir las cadenas de los ADR, se trabaja **por tramos del procedimiento**, en este orden *(propuesta del 05/11/2026; el orden de las piezas dentro de cada tramo, sin confirmar)*. Para el ensayo basta la resolución conjunta (`RESOLUCION` + `RESOLUCION_DUP`). El registro de cada cadena sigue en [`ESTADO_ADR049.md`](diseño/ESTADO_ADR049.md), [`ESTADO_ADR053.md`](diseño/ESTADO_ADR053.md) y [`ESTADO_ADR050.md`](diseño/ESTADO_ADR050.md).

1. **Entrada y consultas** (fases ANALISIS_SOLICITUD y CONSULTAS)
   - ~~**#1040**: el proyecto subido sin ser principal se admite y después bloquea el certificado de fin de instrucción.~~ *(hecho el 06/11, PR #1091)*
   - ~~**#1078**: alta de un organismo consultado desde la interfaz (el backend está hecho). Sin él, la resolución no notifica a ningún organismo y nada avisa.~~ *(hecho el 06/11, PR #1090)*
   - ~~**#652**: traslados al titular y al organismo (art. 147 RD 1955/2000; obligatorios ante una objeción).~~ *(hecho el 10/11, PR #1094 y #1096)*
   - ~~**#982**: el silencio de un organismo (art. 146.1: sin objeción) cierra su consulta sin forzar la fase.~~ *(hecho el 10/11, PR #1101; cerrado como cubierto por #1098)*
   - **#1097**: el diagnóstico cierra el organismo, y el certificado de consultas comprueba los organismos (hoy el resultado del organismo es manual y `CERT_FIN_IP_CONSULTAS` no los mira; sale de #652).
   - **#1098**: el certificado de plazo cumplido en toda espera de un documento externo (catalogado, emisible a demanda y ofrecido al vencer); absorbe #982 y generaliza #1088 (tramo 2, con el que se puede fundir), y sale de #652. Sin él nadie puede cerrar el silencio de un organismo desde el navegador: hoy `generar_cert` no tiene pantalla.
2. **Publicaciones y cierre de la instrucción** (fases INFORMACION_PUBLICA, RESOLUCION y RESOLUCION_DUP)
   - **#994**: remisión a boletín. La `NOTIFICAR` de `ANUNCIO_BOJA`, `ANUNCIO_BOP`, `PUBLICACION` y `PUBLICACION_BOP/BOJA/BOE` no tiene documento de salida, y no se puede terminar por el circuito normal.
   - **#1088**: botón del certificado de plazo cumplido: la segunda espera de los cuatro `ANUNCIO_*` solo tiene la ruta `generar_cert`, sin pantalla.
   - Cerrar las fases de instrucción sin forzar, **diseño conjunto**: **#955**, **#980**, **#805**.
3. **Propietarios** (fases DATOS_CATASTRALES y RESOLUCION_DUP)
   - **#431**: empieza por un hilo de diseño con la norma ya leída (RD 1955/2000, arts. 143.3.e, 144 y 148.2). Hoy nada convierte la RBDA en `interesados_expediente`, y `PROPIETARIOS_DUP` nunca devuelve a nadie.
4. **Ensayo**
   - **#986** (recrear la BD de desarrollo con todos los expedientes-tipo) y un **expediente-tipo AAP+AAC+DUP** (*sin issue*). Tras #1040 los expedientes-tipo traen el proyecto en el alta; los de la BD del PC anteriores no tienen ancla y se recrean. Lo que falle en el navegador alimenta una lista nueva.
5. **Pre-producción** (después de la ruta)
   - **#1008** (ADR-050): «Exportar expediente». Va antes de producción.
   - **#1012** (ADR-050): papelera. Va después de #1008.
   - **#1010** y **#1011** (ADR-050): al ritmo del despliegue; esperan además la respuesta de la ADA sobre Microsoft 365 (`ESTUDIO_EDICION_ESCRITOS_M365.md`).
   - **#1085**, y el despliegue (#151, #330, #852, #851).
6. **Interfaz** (al ritmo que decida Carlos)
   - **#1039**: la cola de Mi trabajo al listado estándar. **#1041**: los cinco listados fuera del estándar. **Zona E de #929** (sin issue): visibilidad de las notificaciones; se abre después de la Cola.
   - **#1045** (estudio del contrato), **#1046** (huérfano), **#1048** (el alta), **#1080** (alinear los selectores con el contrato de #1038; recoge #1065).

**Sin bloque todavía:** #1079 (revocar una autorización no mira las solicitudes que tienen a esa entidad de representante), #1089 (retirar el gesto de mover el ancla del proyecto principal, `anclar-principal`; sale de #1040, fuera del foco ahora), #1092 (plazo de cada consulta: una sola fuente para los días y vencimiento visible en el organismo y el trámite; sale de #1078) y #1099 (el sujeto de crear tarea y de crear o borrar organismo compila menos tramos de los que tiene el objeto; sale de #652). **Diferidos a propósito** *(no cortan la ruta con AAP+AAC+DUP; interpretación)*: #997, #998 y #1057, y, sin issue y acordado con Carlos en #652, el silencio del titular por rama y la enmienda de ADR-011 (que conserva `reparos_titular` como OK; `DISEÑO_CONSULTAS_ORGANISMOS.md` lo deja anotado).

**Pendientes para el PC:** aplicar la migración `1040_comentario_documento_principal` (`flask db upgrade`; solo cambia el comentario de una columna) y las tres `652_*` (`652_reglas_orden_4_tramos`, `652_reglas_traslados` y `652_sentido_diagnostico`; la primera **falla con error** si alguna de las reglas de orden o el aviso de vuelta tiene la descripción editada a mano en esa base: se revisa esa regla, no se salta la comprobación), y después `scripts/comparar_catalogo.py`; un escrito real con plantilla (zona A de #929; las reales se suben ahora desde `/plantillas/`) y, para el anuncio del edicto, su plantilla real con `{{ i }}` sobre `interesados_edicto`; y `/sync-derivados` de la fila de `INVENTARIO_BACKEND.md` (zona A de #929); ver [`ESTADO_ADR049.md`](diseño/ESTADO_ADR049.md). **Aparcado:** #1033 y #1034 (ADR-050).

> **Nota para quien actualice este fichero (reenfoque del 11/10/2026, al día el 10/11/2026).** El objetivo vivo es poder llevar un expediente con DUP de principio a fin en el navegador. El hilo era el frontend de las notificaciones de **ADR-049** (#929), cuya zona A se hizo el 11/10. Al analizarlo salió la revisión de la interfaz, que dio **ADR-053** (inspector, listados y documentos), cuya cadena (#1041 a #1051) se puso delante de las demás zonas de #929; de ella están hechas #1042 (13/10) y #1043 (18/10); #1055, que salió de #1042, se hizo el 18/10, y #1047, el 19/10. De las zonas de #929 están hechas también la D (#1038, el 23/10) y la C (#1037, el 30/10). Del bloque de documentos, #1044 se hizo el 01/11 y #1009 el 05/11 (adelantado por Carlos). Ya con los tramos, #1040 y #1078, los dos primeros del tramo 1, se hicieron el 06/11, y #652 y #982 el 10/11. **ADR-050** sigue aparcado en sus fases 2b y 4 a 7: no se pasa a él sin preguntar a Carlos. Al cerrar un issue, el «Próximo» sale de la lista de arriba y, agotada, de `ESTADO_ADR053.md` y de `ESTADO_ADR049.md`. Reenfoque del 05/11/2026: el «Próximo» pasa de bloques por cadena de ADR a tramos del procedimiento, con AAP+AAC+DUP como expediente de referencia; el orden de los tramos se propuso ese día y se decide paso a paso con Carlos.
