# Capturas de BDDAT para la presentación con la ADA

19 capturas a 1920×1080, en el orden de la presentación, y el PDF con todas
(`capturas_bddat_presentacion_ADA.pdf`, una por página, para pasarlas seguidas
a pantalla completa).

**Origen.** Hechas el 16/10/2026 desde una sesión en la nube, no desde el PC de
desarrollo (que estaba sin disco C:). Interfaz de la rama
`claude/confident-clarke-yxvhks` (c5b9d55, la más avanzada: trabajo de #1043
sobre el inspector del árbol, sin mergear a `develop`). Datos **sintéticos**:
los cuatro expedientes-tipo de `scripts/expedientes_dummy/` más uno sin
responsable, y los usuarios de la semilla de tests.

| Captura | Usuario / rol | Qué enseña |
|---|---|---|
| 01 login | sin sesión | Pantalla de acceso |
| 02 dashboard | TTRA · tramitador | Panel de control |
| 03, 04 buscador | TTRA · tramitador | Ctrl+K buscando un expediente («AT-3») y una entidad («Jerez») |
| 05 Mi trabajo administrativo | TADV · administrativo | Cola de tareas, una seleccionada (inspector) |
| 06 Mi trabajo tramitador | TTRA · tramitador | Seguimiento, AT-3 seleccionado (inspector) |
| 07 Mi trabajo supervisor | TSUP · supervisor | Hub Control y Gestión (no tiene inspector) |
| 08 árbol AT-3 | TTRA · tramitador | Expediente con reformado y consultas, sin inspector |
| 09–11 árbol AT-1 | TTRA · tramitador | Inspector en la solicitud, en el trámite Análisis Documental y en su tarea ANALIZAR |
| 12 nuevo expediente | TTRA · tramitador | Formulario de alta, rellenado a medias y sin enviar |
| 13 usuarios | TSUP · supervisor | Usuario TMUL seleccionado (inspector) |
| 14–19 gestión | TSUP · supervisor | Tablas maestras, tipos de documento, requisitos documentales, catálogo de requerimientos, plazos legales y efectos de plazo, cada uno con una fila seleccionada |

**Para tener en cuenta.**

- Mi trabajo del supervisor es el hub Control y Gestión: no tiene inspector. Los
  listados de gestión (14–19) son los que lo enseñan.
- Con el inspector abierto, el árbol queda parcialmente tapado por la derecha:
  es el comportamiento conocido de la interfaz, no se ha retocado.
- La bitácora inferior solo se ve en 05 y 06; en el resto está cerrada.
- Las fechas y los textos de «Bitácora» salen del reloj y de los datos de la
  nube; no coinciden con los de la BD de desarrollo del PC.
