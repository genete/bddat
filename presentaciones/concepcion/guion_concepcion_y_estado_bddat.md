# Cómo está concebida BDDAT y cómo va

**Guion de la presentación a jefatura. Parte 2: qué es, principios de diseño, cómo se ha
trabajado, qué entra en producción y estado de implementación.**
Preparado el 2026-10-04. Viene después de la parte 1 (fundamentos tecnológicos) y alimenta el
«cómo voy y qué falta».

## Cómo leerlo

Cada punto lleva **idea ancla** (lo que dices), **cómo contarlo**, **dato real** (con su
fuente) y, donde procede, una marca:

- ✅ **Comprobado.** Contado hoy en el código, en la base de datos que construyen las migraciones
  o en GitHub.
- ⚠️ **Mi lectura.** Interpretación mía de los datos. La corriges tú, que estuviste allí.
- ❓ **A decidir o confirmar por ti.**

## Datos reales de este guion, y de dónde salen

| Dato | Valor | Fuente |
|---|---|---|
| Primer issue del proyecto | 19/01/2026 | GitHub, issue #1 |
| Pull requests fusionados | **405**, entre enero y el 4 de octubre | GitHub (búsqueda por mes) |
| Issues cerrados / abiertos | **478 / 135** | GitHub |
| Decisiones de diseño escritas (ADR) | **52**, con fecha cada una | `docs/decisiones/` |
| Pruebas automáticas | 184 ficheros; **2.222 pruebas** pasando el 29/09; cobertura del 71 % el 24/09 | #984; `tests/README.md` |
| Catálogo cargado por las migraciones | ver cuadro del punto 2 | Base de datos construida desde cero en esta sesión |
| Versiones publicadas | una sola (`v0.3.1`, febrero); el resto del trabajo va por `develop` | GitHub, releases |

**Dos avisos de vigencia que afectan a lo que cuentes:**

1. **La matriz de necesidades llega solo hasta el issue #765** (principios de agosto: cita el
   ADR-037 y el ADR-039, pero no la mensajería del ADR-040) y hoy vamos por el #1019. Le falta casi
   dos meses de trabajo (ADR-040 a ADR-052). Además, la matriz da por inexistente la mensajería
   interna, y el código ya tiene su módulo. Por eso en el punto 6 uso sus porcentajes como **punto
   de partida con fecha**, no como foto de hoy.
2. **El historial de git de esta copia está recortado** (122 commits). Por eso la línea de tiempo
   usa los pull requests y los ADR, que son completos y tienen fecha.

---

## 1. Qué es BDDAT

**Idea ancla:** «BDDAT es el tramitador de expedientes de alta tensión: una web donde el
técnico lleva el expediente paso a paso, con el procedimiento delante.»

**Cómo contarlo:**

- **De dónde venimos:** expedientes en hojas de cálculo y una base Access; para saber en qué
  estado estaba uno había que abrir carpetas del servidor y reconstruirlo.
- **Qué es:** una aplicación web para la Consejería de Industria, Energía y Minas. Se abre en el
  navegador y la usan cuatro perfiles: **tramitador**, **administrativo**, **supervisor** (jefatura
  de servicio) y **administrador** del sistema.
- **Qué hace**, en cuatro verbos:
  1. **Guía** el procedimiento: muestra el expediente como un árbol de fases, trámites y tareas, con
     lo que toca hacer y lo que falta.
  2. **Calcula** los plazos y avisa cuando algo no encaja con la norma.
  3. **Genera** los escritos a partir de plantillas con los datos del expediente.
  4. **Deja rastro**: qué se hizo, quién y cuándo.
- **Qué no es (todavía):** no firma, no notifica y no consulta el BOJA por sí mismo. Esas gestiones
  se hacen en las plataformas corporativas y BDDAT registra el resultado.

**Dato real (catálogo que ya trae cargado)** ✅:

| Qué | Cuántos |
|---|---|
| Tipos de expediente | 8 (transporte, distribución, distribución cedida, renovable, autoconsumo, línea directa, convencional, otros) |
| Tipos de solicitud | 22 (AAP, AAC, DUP, explotación, transmisión, cierre, recursos… y las combinadas, como AAP+AAC+DUP) |
| Tipos de fase | 13 |
| Tipos de trámite | 41 |
| Tipos de tarea | 4 (analizar, elaborar, notificar, esperar plazo) |
| Tipos de documento | 82 |
| Municipios | 8.132 (toda España, 52 provincias; 785 son andaluces) |

---

## 2. Principios fundamentales de diseño

Son el «porqué» de las decisiones. Cada uno se apoya en una decisión escrita (ADR) y se puede
contar con un ejemplo.

### P1. El documento es el centro del expediente

**Idea ancla:** «Lo que prueba que algo ocurrió es el documento, no un campo que alguien rellenó.»

**Cómo contarlo:**

- Ningún elemento del procedimiento (expediente, solicitud, fase, trámite, tarea) guarda fechas
  propias. Las fechas son las de los **documentos** que las portan (ADR-002, abril). El estado se
  deduce al consultar.
- Razón: una fecha duplicada puede divergir del documento y, en un procedimiento administrativo,
  esa diferencia tiene consecuencias legales.
- El **expediente** es, por definición legal (art. 70 de la LPACAP), el conjunto ordenado de
  documentos que sirven de antecedente y fundamento a la resolución. En BDDAT un documento forma
  parte del expediente solo si está vinculado a una tarea (ADR-027). Un fichero suelto es un
  «huérfano»: el técnico decide si lo enlaza o lo descarta.
- Cada escrito generado lleva en el pie un **código de trazabilidad** (`BDDAT-<tarea>-<letra>`) que
  sobrevive a pasarlo a PDF. Hoy lo usa el requerimiento de subsanación para acreditar de qué tarea
  es el escrito; reconocer así cualquier fichero que se suba (volver a asociarlo a su tarea aunque
  cambie de ruta) es plan (#181, abierto). *(Corregido el 2026-10-04: antes decía que ya servía para
  esto en general.)*

### P2. El procedimiento son cajas dentro de cajas (ESFTT)

**Idea ancla:** «Un expediente contiene solicitudes; una solicitud, fases; una fase, trámites; un
trámite, tareas. Cada caja solo conoce lo que tiene dentro.»

**Cómo contarlo:**

- Esa jerarquía (**E**xpediente → **S**olicitud → **F**ase → **T**rámite → **T**area) es el esqueleto
  de todo.
- Las cajas son **simples**; la riqueza está en sus **tipos**, que son los nombres que da la propia
  norma («Información Pública», «Consulta a organismos», «Declaración de Utilidad Pública»…).
- Solo hay **cuatro tipos de tarea**: analizar, elaborar, notificar y esperar un plazo. Todo
  trámite es una combinación de esos cuatro.
- **Encapsulado** quiere decir también protegido: cuando se cierra una fase, queda **sellada**.
  Nadie puede cambiar su contenido sin reabrirla expresamente y dejando justificación (ADR-036).
- Una solicitud siempre termina en una fase de **resolución**.

**Dato real** ✅: la secuencia de trabajo viene cargada en datos, no en el código: **63** relaciones
«este trámite pertenece a esta fase», **101** pasos «esta tarea va en este trámite» y **241**
relaciones «este documento se espera en esta tarea».

### P3. La norma vive en datos, no en código

**Idea ancla:** «Cuando cambia la ley no se reprograma: se cambia una regla.»

**Cómo contarlo:**

- Hay un **motor de reglas** que no sabe nada del dominio (ADR-001). Recibe «quiero hacer X en este
  contexto» y contesta «adelante», «advierto» o «bloqueo, y por esto». Las reglas están en tablas
  de la base de datos.
- Un **ensamblador** traduce los datos del expediente a las variables que las reglas entienden
  («¿requiere evaluación ambiental?», «¿hay organismos pendientes de responder?»).
- Cadena de conocimiento: **ley** → extracción de la norma → variable documentada → regla →
  tramitación real. Quien herede el sistema puede seguir esa cadena cuando cambie una norma.
- Hay dos cosas que **no** son configurables a propósito: las reglas de integridad estructural
  («no cierres una fase si quedan trámites abiertos») y el ensamblador. Test para decidir dónde vive
  un hecho (ADR-037): *si mañana cambiara, ¿el origen sería una norma nueva o una decisión nuestra
  de organizar el procedimiento?* Si es una norma, va a las reglas; si es una decisión nuestra de
  organizar el procedimiento, va a una tabla de vocabulario (dato de catálogo, p. ej. qué trámites
  lleva cada fase); si es una imposibilidad lógica del sistema (negarla sería una falsedad, no una
  excepción), va al código como invariante (ADR-037, afinado en ADR-043 §B). *(Corregido el
  2026-10-04: antes decía que lo nuestro va al código; el ADR da tres destinos, no dos.)*

**Dato real** ✅:

| Qué | Cuántos |
|---|---|
| Reglas del motor activas | **38** (36 que bloquean y 2 que advierten), de las cuales **15 están enlazadas a su norma** |
| Condiciones de esas reglas | 53 |
| Variables que entiende el motor | 37 |
| Normas indexadas | 11 (RD 1955/2000, Ley del Sector Eléctrico, LPACAP, Decreto 9/2011, Decretos-ley andaluces 2/2018 y 26/2021, RD 244/2019, RD 1183/2020, RD 88/2026, Ley de tasas 10/2021 y RDL 23/2020) |
| Plazos legales en catálogo | 21 |

**Ojo** ⚠️: de las 38 reglas, 23 todavía no están enlazadas a una norma del catálogo (puede que su
descripción sí la mencione; no lo he comprobado una a una). El contenido normativo es la parte que
más iteración necesita y se afina tramitando casos reales.

### P4. Permisivo, con salida y con rastro

**Idea ancla:** «El sistema avisa y razona, no estorba. Si hay que salirse del camino, se puede,
dejando constancia.»

**Cómo contarlo:**

- Se parte de que el técnico tiene criterio. El sistema **avisa** o **bloquea con motivo y norma
  legibles**, nunca en silencio.
- Tres grados: **avisa** (se sigue adelante); **bloquea con salida** (todas las reglas del motor: se
  fuerza escribiendo una justificación obligatoria, que queda en la bitácora); y **puerta cerrada**
  (la mayoría de los invariantes: lo estructural, como no borrar una fase con trámites, y lo
  irreversible, como una resolución ya notificada, que es firme). Ante una fase cerrada la salida es
  otro acto: reabrirla, con justificación. *(Corregido el 2026-10-04: antes decía que todo bloqueo
  tiene salida y que el bloqueo duro era solo para lo irreversible; el código tiene también puertas
  cerradas estructurales.)*
- Por eso se puede ir probando sin miedo y, a la vez, hay trazabilidad completa.

### P5. Plazos: un único mecanismo, calculado de los documentos

**Idea ancla:** «Un plazo y una suspensión se miden igual, desde los documentos, para que nunca
puedan contradecirse.»

**Cómo contarlo:**

- El plazo máximo para resolver y notificar es el único que obliga a la administración; los demás
  obligan a terceros (el interesado que debe subsanar, el organismo que debe informar).
- Hubo un fallo real en agosto: la suspensión y el plazo se calculaban por dos caminos distintos,
  y el expediente podía no vencer nunca. Se resolvió unificando el mecanismo (ADR-041).
- Después se afinó que el plazo de resolver es **del acto** y que se da por cumplido con la
  **notificación** al titular (ADR-049, septiembre).

**Dato real** ✅: calendario de días inhábiles cargado: **solo 2025 (10 días) y 2026 (9 días)**. Hay
una carga anual desde la API de la Junta (#385), pero habrá que repetirla cada año y hoy no hay
datos de 2027 en adelante. Merece revisarse antes de producción. *(Añadido el 2026-10-04, verificado
en `plazos._obtener_inhabiles_bd`: si un año no tiene datos, el cálculo no avisa y cuenta solo
fines de semana; y los datos cargados son de ámbito nacional y autonómico, sin festivos locales.
Además, hoy solo suspende el plazo de resolver el requerimiento de subsanación, art. 22.1.a: los
informes de organismos dejaron de suspender por el criterio de #796, 22/09/2026.)*

### P6. Visibilidad abierta, actos controlados

**Idea ancla:** «Evitamos los manazas, no los ojos.»

**Cómo contarlo:**

- Cualquier usuario autenticado **puede ver** casi todas las pantallas, incluidas las reglas y los
  plazos. El conocimiento compartido ayuda a aprender y da continuidad cuando alguien se jubila
  (ADR-013).
- Lo que los roles restringen son los **actos**: crear, editar, borrar, activar, generar.
- Un tramitador puede actuar sobre un expediente que no es suyo, con aviso visible y registro en la
  bitácora (ADR-012).

### P7. Una sola verdad

**Idea ancla:** «Cada cosa se calcula en un único sitio, y el resto la muestra.»

**Cómo contarlo:**

- El servidor calcula el estado, los plazos y las reglas; el navegador solo los pinta. Si hubiera
  dos versiones de una regla (una en Python y otra en JavaScript), con el tiempo discreparían.
- Las fechas viven en los documentos (P1). Los códigos de los catálogos son inmutables y es lo que
  usa el código para referirse a ellos.

### P8. Que otro pueda heredarlo

**Idea ancla:** «El valor más duradero no es el código: es la cadena que explica por qué.»

**Cómo contarlo:**

- 52 decisiones escritas con su contexto y las alternativas descartadas, la normativa extraída por
  fuentes oficiales, el diccionario de variables y las guías.
- Licencia europea EUPL v1.2; software libre.
- Tests que fijan el comportamiento.

---

## 3. Principios de diseño del backend y del frontend

(Lo dejaste abierto. Esto es lo que sale de las decisiones; podas tú.)

### Backend: lo que decide y guarda

1. **Un solo sitio para cada verdad.** Estado, reglas y plazos se calculan en el servidor y se envían
   ya resueltos.
2. **Servicios de dominio y pantallas finas.** La pantalla no calcula plazos ni decide reglas:
   llama a un servicio. Hay más de medio centenar de servicios.
3. **Motor agnóstico + ensamblador** (ADR-001). Añadir una variable nueva no obliga a tocar el motor.
4. **Estructura y datos por migración.** Todo cambio de tablas y de catálogo es un fichero
   versionado: cualquier instalación nueva se reconstruye igual. Los datos de catálogo
   también van en migraciones (PR #355).
5. **Defensivo ante lo ausente.** Si falta un catálogo o cae la base de datos, la aplicación degrada
   con mensaje y no se rompe entera (PR #352).
6. **Editar sin borrar por accidente.** Una petición que no menciona un campo no lo toca; solo se
   vacía un campo cuando se pide expresamente. Nació de un fallo real que vació campos en silencio.
7. **Sin estado en el proceso.** Nada compartido en la memoria de un proceso; todo en la base de
   datos. Es lo que permitirá repartir la carga.
8. **Los ficheros no se mezclan con los datos** (ver parte 1) y los toca un único subsistema.

### Frontend: lo que se ve y se toca

1. **Un solo caparazón.** Todas las vistas autenticadas comparten el mismo layout (cabecera, menú
   lateral, zona principal, panel de detalle) y la identidad visual de la Junta (ADR-014, ADR-022).
2. **Capas, no rutas.** Un listado abre un panel de detalle encima, y este un modal si hace falta.
   «Volver» es cerrar la capa de encima; no hay laberinto de enlaces (ADR-023).
3. **El árbol del expediente es el mapa.** Es la vista central: muestra dónde está el expediente y qué
   falta, con color por estado (ADR-016).
4. **Interactividad solo donde compensa.** Páginas clásicas y cinco «islas» interactivas (ADR-015).
5. **Avisos sin interrumpir.** Sin ventanas emergentes que corten el trabajo; el aviso aparece junto
   al campo y el control se desactiva con su explicación.
6. **Una puerta por rol de trabajo.** «Mi trabajo» para el tramitador y el administrativo, panel de
   control para el supervisor, seguimiento y huérfanos (ADR-017, 028, 038).
7. **Atajos para quien tramita.** Paleta de comandos con Ctrl+K y panel de bitácora y avisos
   (ADR-018, ADR-020).

---

## 4. Cómo ha evolucionado el desarrollo

**Idea ancla:** «Se ha ido de abajo arriba: primero la estructura, luego el aspecto, luego la
norma, y ahora estamos afinando procedimiento a procedimiento.»

**Dato real** ✅: pull requests fusionados por mes y decisiones escritas por mes.

| Periodo | PR fusionados | ADR escritas | Qué predomina ⚠️ |
|---|---:|---:|---|
| Enero a marzo | 99 | 0 | **Estructura y primeras pantallas.** Tablas, entidades, proyectos, autorizados, 785 municipios andaluces, dashboard por roles, listados, colores oficiales. En febrero, la única versión publicada (`v0.3.1`) |
| Abril | 16 | 2 | **Normativa y diseño de fondo.** Motor de reglas agnóstico, fechas fuera del procedimiento, prueba de concepto del árbol interactivo, presentación para técnicos, limpieza de las vistas antiguas |
| Mayo | 66 | 18 | **Rediseño del backend y, a final de mes, del frontend.** Cuatro tipos de tarea, documentos vinculados a tareas, plazos en días hábiles, calendario de inhábiles, semillas en migraciones. El 28 de mayo se decide el nuevo layout, los permisos, las islas, el árbol, la paleta y el dock |
| Junio | 31 | 8 | **Rediseño del frontend.** Sistema visual, panel de detalle universal, ensamblador de escritos, vigencia de la norma, vista del supervisor |
| Julio | 65 | 7 | **Estabilización.** Dataset ficticio y matriz de necesidades (7 y 8 de julio), ingesta de documentos, ciclo del diagnóstico y de la notificación, plantillas en formato abierto, navegación administrativa |
| Agosto | 47 | 7 | **Estabilización y rigor.** Fase cerrada sellada, vocabulario del procedimiento, datos del órgano propio, hub del tramitador, mensajería, plazos y suspensiones unificados, sub-procesos |
| Septiembre | 71 | 10 | **Foco en fases y tipos de expediente.** Certificado de fin de instrucción, reformados de proyecto, DUP, resolución de AAP y AAC como actos separados, plazo de la fase finalizadora, fechas de notificación, notificación edictal y el almacén documental |
| Octubre (1 a 4) | 10 | 0 | Almacén documental (ADR-050), primeras fases |

**Cómo contarlo:**

- El ritmo es sostenido: entre 30 y 70 cambios integrados por mes, salvo abril, que fue el mes de
  pensar.
- **Mayo concentra las decisiones** (18 de las 52): ahí se fijaron las bases que se han mantenido.
- Desde julio el trabajo se organiza por **necesidades** (la matriz) y desde septiembre por
  **procedimientos**: qué hace falta para que una autorización de cada tipo se tramite de punta a
  punta.
- **Ahora** el foco es el procedimiento por tipo de solicitud y de expediente, y en paralelo el
  almacén documental, que es la última pieza antes de producción.

**Ojo** ⚠️: las fronteras entre etapas son aproximadas (se solapan). Los nombres de las etapas son
los tuyos; los periodos son los que salen de las fechas.

---

## 5. Producción: lo mínimo y lo diferido

### Cómo se decidió, y qué ha cambiado desde entonces

**Idea ancla:** «Pregunta clave: qué pasa si arrancamos sin esto. Si no se puede tramitar, es
imprescindible; si se puede con un apaño temporal, puede esperar.»

El criterio viene de `PLAN_ESTRATEGIA.md` (abril de 2026) ❓:

| Categoría (abril) | Bloques |
|---|---|
| **Bloqueantes** | Tramitación del procedimiento; sistema documental; importación de los expedientes del sistema anterior |
| **Necesarios** (el apaño no aguanta) | Generación de escritos; configuración de reglas y catálogos; carga y usuarios; listado inteligente |
| **Posproducción** | Motor de reglas; plazos; proyectos e instalaciones; auditoría configurable; manual; mensajería |
| **Opcional** | Cartografía (GIS) |

**Lo que ha cambiado desde abril** ⚠️:

1. **El motor de reglas y los plazos no esperaron.** Se pensaron como posproducción y están ya
   construidos y dentro de la tramitación (reglas, calendario, suspensiones, certificados). Siguen
   afinándose, pero ya son núcleo.
2. **Aparece un bloque que no estaba:** la **infraestructura** (servidor, copias, seguridad,
   despliegue) y los **datos estructurales mínimos** (catálogo real cargado). La matriz los añadió
   en julio como bloques 15 y 16: son lo que de verdad frena producción.
3. **El almacén documental** se ha convertido en requisito: el ADR-050 se ejecuta «antes de
   producción», para que los usuarios dejen de tener acceso de escritura a las carpetas.

### Propuesta de lo mínimo y lo diferido ❓

(Esta división es una **propuesta mía para que decidas**; no existe aprobada.)

| Mínimo para arrancar | Diferido a después |
|---|---|
| Tramitación completa de los procedimientos que se vayan a usar | Cartografía (mapa) |
| Documentos con el almacén propio y copias de seguridad | Edición de los elementos técnicos del proyecto (líneas, CT, subestaciones) |
| Escritos con plantillas reales, órgano propio y firmantes | Panel de alertas de vencimiento de toda la unidad y desglose avanzado de estadísticas |
| Motor de reglas y plazos con el contenido normativo de esos procedimientos | Informes y exportaciones agregadas (Excel/CSV) |
| Gestión de usuarios, asignación de expedientes y roles | Auditoría configurable y consulta de logs técnicos |
| Listado de seguimiento y «Mi trabajo» | Manual de usuario y ayuda contextual |
| Infraestructura: servidor, base de datos, carpetas con permisos, copias de seguridad, HTTPS, clave secreta | Mensajería avanzada (peticiones, avisos técnicos) |
| Catálogo estructural completo y calendario de inhábiles de los años en servicio | Compilación del expediente para remisión, con foliado (la exportación a ZIP del almacén cubre parte) |
| ❓ **Migración del sistema anterior** (Access): decisión tuya | Automatizar firma y notificación (BandeJA, Port@firmas, Notifica) |

### Necesidades en la interfaz

**Idea ancla:** «Cada rol necesita una puerta de entrada y unas pocas herramientas. Lo demás es
lujo.»

| Rol | Ya está ✅ | Falta para el mínimo ⚠️ | Diferido |
|---|---|---|---|
| **Tramitador** | Alta de expediente en tres pasos, árbol con panel de detalle, generación de escritos, seguimiento con estado por pista, radar de huérfanos, aviso al actuar sobre expedientes ajenos | Interfaz de **notificaciones** (registro, destinatarios, subida; #929), plazo de resolver visible en el árbol (#922), editar el borrador desde el navegador (almacén, fase 5) | Bitácora narrativa por expediente, mis vencimientos como vista propia |
| **Administrativo** | Cola común de tareas, subida de documentos, ver todos los expedientes | — | Delegación dirigida de tareas |
| **Supervisor** | Panel de control, estadísticas por técnico y estado, usuarios y roles, tablas maestras, reglas, plazos, plantillas, requisitos y requerimientos, órgano propio, firmantes | Poblar el catálogo (firmantes, ítems técnicos, requerimientos); tabla de vocabulario de fases sin interfaz (#746) | Alertas de vencimiento (#74), informes (#76), auditoría configurable |
| **Administrador** | Gestión de usuarios y roles | Sobreescritura de emergencia (hoy, solo por base de datos) | Logs técnicos |
| **Para todos** | Paleta de comandos, panel de avisos, layout y tema de la Junta | **Ayuda** (hoy no existe manual ni ayuda contextual) | Manual completo |

**Dato real** ✅ (GitHub): de los **135 issues abiertos**, solo **10** llevan la etiqueta
`production` (6 son las fases del almacén y 3 son de infraestructura: clave secreta #45,
infraestructura con Informática #151 y entornos #330) y **4** llevan `post-MVP`. La separación
entre mínimo y diferido está en documentos, no en las etiquetas. Si quieres que se pueda ver en
GitHub, habría que etiquetar.

---

## 6. Estado de implementación por bloques

**Advertencia de vigencia:** los porcentajes son de la **matriz de necesidades**, cuya última
actualización llega al issue #765 (principios de agosto). La columna «Después» recoge lo que **sé que ha cambiado** desde
entonces por las decisiones y el código ⚠️. Actualizar la matriz entera sería un trabajo aparte
(existe la herramienta `/cobertura` para hacerlo; puedo lanzarla).

| Bloque | Necesidades | Media en la matriz | Con ≥80 % | Después de la matriz ⚠️ |
|---|---:|---:|---:|---|
| 1. Tramitación del procedimiento | 7 | **71 %** | 4 | Certificado de fin de instrucción, reformados, DUP, resolución AAP/AAC, plazo de la fase finalizadora, fechas de notificación; notificación edictal diseñada (ADR-052) |
| 2. Sistema documental | 10 | **70 %** | 6 | **Almacén en curso** (ADR-050): fase 0 y segunda entrega de la fase 1 hechas; prueba de edición en un puesto real de la Junta pasada |
| 3. Generación de escritos | 7 | **63 %** | 4 | Estable. Plantillas en formato abierto, órgano propio, tres plantillas base |
| 4. Motor de reglas y configuración | 9 | **43 %** | 4 | Estable. CRUD completo; faltan sobreescritura de emergencia y selector de modo en pantalla |
| 5. Plazos legales | 7 | **65 %** | 3 | Mucho avance: plazos y suspensiones unificados (ADR-041), plazo de la fase finalizadora (ADR-048), cumplimiento por notificación y certificados (ADR-049) |
| 6. Proyectos e instalaciones | 4 | **53 %** | 2 | Reformados de proyecto (ADR-044). Elementos técnicos anidados siguen sin hacerse |
| 7. Cartografía | 2 | **0 %** | 0 | Sin cambios (diferido) |
| 8. Carga y usuarios | 6 | **40 %** | 2 | Sin cambios relevantes |
| 9. Listado inteligente | 4 | **63 %** | 0 | Seguimiento por pista, «Mi trabajo» |
| 10. Auditoría | 4 | **25 %** | 1 | Sin cambios. Falta consulta por expediente |
| 11. Importación del sistema anterior | 3 | **17 %** | 0 | ❓ Sin cambios: no hay ningún dato heredado cargado |
| 12. Manual de usuario | 2 | **0 %** | 0 | Sin cambios |
| 13. Mensajería interna | 5 | **6 %** | 0 | **Desactualizado:** el módulo existe (ADR-040, agosto). La matriz es anterior |
| 14. Compilación del expediente | 1 | **0 %** | 0 | Parcialmente cubierto por la exportación del almacén (fase 2b, pendiente) |
| 15. Infraestructura y operación | 8 | **11 %** | 0 | Entorno de desarrollo y pruebas en la nube, prueba de WebDAV en la Junta; **todo lo demás pendiente** (servidor, copias, HTTPS, despliegue) |
| 16. Datos estructurales para producción | 1 | **35 %** | 0 | Catálogo del punto 1 y 3 cargado; **huecos conocidos** abajo |

**Cómo contarlo:**

- **El núcleo del trabajo (bloques 1, 2, 3, 5, 9) está entre el 60 y el 70 % en la matriz de
  agosto**, y desde entonces ha subido sobre todo en tramitación, documentos y plazos.
- **Lo que menos avance tiene es lo que no es programación:** infraestructura (11 %), importación
  del sistema anterior (17 %) y manual (0 %). Dependen de Informática y de decisiones, no de
  escribir código.
- **Lo diferido por diseño** (cartografía, auditoría configurable, mensajería avanzada) está donde se
  esperaba.
- No uses la media global (**43,6 %** sobre 80 necesidades) como titular: mezcla lo imprescindible con lo
  diferido y subestima el estado real del núcleo.

**Huecos conocidos del catálogo para producción** ✅ (contados hoy):

| Hueco | Dato |
|---|---|
| Ítems técnicos del proyecto (RD 223/2008, RD 337/2014) | 0 cargados (#595) |
| Firmantes de Port@firmas | 0; los rellena el supervisor |
| Calendario de días inhábiles | Solo 2025 y 2026 |
| Reglas enlazadas a su norma | 15 de 38 |
| Datos de sede del órgano propio | Sin poblar (no hay fuente identificada) |
| Plantillas de escritos | 5 sembradas por migración; apuntan a ficheros que solo existen en el PC de desarrollo (en otros entornos quedan desactivadas hasta registrar plantillas reales) |

**Qué queda por delante del almacén** (ADR-050, issues abiertos con etiqueta `production`):
fase 1 (#1007, en curso), exportación de expediente (#1008), plantillas y fragmentos al almacén
con retirada del motor de Word (#1009), botón «Editar» con LibreOffice (#1010), PDF para firma
generado en el servidor (#1011) y papelera e integridad (#1012). ADR-050 situó todo esto antes de
producción.

---

## Hilo sugerido entre las tres partes

1. **Parte 1 (tecnología):** vocabulario común, qué máquinas y qué le pedimos a Informática.
2. **Parte 2, puntos 1 a 3:** qué es BDDAT y por qué está diseñada así. Remite a la parte 1 para
   dónde guarda qué.
3. **Parte 2, punto 4:** cómo hemos llegado hasta aquí, con el ritmo real.
4. **Parte 2, puntos 5 y 6:** qué falta para arrancar, separando lo que es programación de lo que
   depende de otros.

## Preguntas que solo puedes contestar tú

1. **¿Sigue siendo bloqueante la migración del sistema anterior?** En abril lo era; la matriz la
   deja en el 17 % y no hay datos cargados. De tu respuesta depende la tabla de mínimos.
2. **¿Subimos el motor de reglas y los plazos a «núcleo»?** Mi propuesta es que sí, porque ya
   están dentro de la tramitación.
3. **¿Quieres que lance `/cobertura` para actualizar la matriz** antes de la presentación (más
   fiable que mi columna «Después»), o prefieres presentar con la nota de fecha?
4. **¿Quieres etiquetar en GitHub** los issues del mínimo de producción para poder enseñar el
   estado en directo?
