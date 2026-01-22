# Guía General del Proyecto BDDAT

**Fecha de revisión:** 15/01/2026

---

## Índice

- [Propósito del Proyecto](#propósito-del-proyecto)
- [Desarrollo de la Base de Datos](#desarrollo-de-la-base-de-datos)
  - [Claves Técnicas](#claves-técnicas)
  - [Control de Versiones](#control-de-versiones)
  - [Estructura de Ficheros](#estructura-de-ficheros)
  - [Documentos a Proporcionar a la IA](#documentos-a-proporcionar-a-la-ia)
  - [Proceso de Iteración de Desarrollo con la IA](#proceso-de-iteración-de-desarrollo-con-la-ia)
  - [Proceso de Despliegue en Producción](#proceso-de-despliegue-en-producción)
- [Lógica de la Tramitación de Expedientes](#lógica-de-la-tramitación-de-expedientes)
  - [Relación Expediente, Solicitud, Proyecto, Fase, Trámite y Tarea](#relación-expediente-solicitud-proyecto-fase-trámite-y-tarea)
  - [Estructura de Negocio de la Tramitación](#estructura-de-negocio-de-la-tramitación)
  - [Separación Datos Estructurales vs. Datos Lógica de Negocio](#separación-datos-estructurales-datos-lógica-negocio)
  - [Lógica de Negocio - Enfoque Basado en Motor de Reglas](#lógica-de-negocio---enfoque-basado-en-motor-de-reglas)
- [Estructura de Tablas y Tipos](#estructura-de-tablas-y-tipos)
  - [El Expediente y sus Tipos](#el-expediente-y-sus-tipos)
  - [La Solicitud y sus Tipos](#la-solicitud-y-sus-tipos)
  - [La Fase y sus Tipos](#la-fase-y-sus-tipos)
  - [El Trámite y sus Tipos](#el-trámite-y-sus-tipos)
  - [La Tarea y sus Tipos](#la-tarea-y-sus-tipos)

---

## Propósito del Proyecto

El propósito de este proyecto es desarrollar una **base de datos** y un **interfaz** para gestionar tramitaciones de expedientes de solicitudes de instalaciones de alta tensión.

El proyecto tiene dos retos principales:

1. **Desarrollo técnico** de la base de datos y el interfaz.
2. **Definición de la lógica de negocio** de la tramitación de expedientes.

---

## Desarrollo de la Base de Datos

En el desarrollo de la base de datos vamos a enfrentarnos a la **organización de la información**, así como la necesidad de **concurrencia de los usuarios**.

Para la organización de la información se ha estudiado la lógica del proceso de tramitación de expedientes, y la relación entre la información que se maneja. De esta forma, la estructura de la base de datos está relacionada con la forma de tramitación de los expedientes.

Primero analizaremos las claves desde el punto de vista técnico, de implementación, conociendo las necesidades del entorno en el que vamos a desarrollar.

### Claves Técnicas

#### Entorno

- **Usuarios:** Windows 11, máximo 15, ampliable en red, con servidor de archivos mantenido por el entorno empresarial.
- **Base de datos:** PostgreSQL. El servidor de bases de datos se ejecuta inicialmente en el PC de un usuario en red y los clientes son otros usuarios en red. La base de datos y otros archivos se alojan en el mismo PC que corre el servidor. Se pretende que en el futuro el servidor de bases de datos se ejecute en el servidor central. Estoy, a fecha de hoy, negociando que me instalen PostgreSQL en modo servicio en mi PC corporativo pues la instalación portable falla al crear la base de datos.
- **Comunicación con la base de datos (Backend):** Se usará la extensión Flask-SQLAlchemy que permite comunicarse con la base de datos mediante Python de forma abstracta (SQLAlchemy) y generar los comandos GET/POST con la base de datos.
- **Comunicación con el usuario (Frontend):** Se usará Bootstrap 5.3.3 (versión actual de la Junta). Implementación mediante CDNs oficiales.

#### Flujo de Trabajo

El usuario interactúa con el frontend (HTML+Bootstrap) y el navegador genera una orden POST mediante Javascript. En el servidor, Flask recibe ese POST y mediante código Python se decide lo que hay que hacer con esa petición. SQLAlchemy traduce a PostgreSQL el comando. Flask prepara una respuesta al usuario (orden GET) ya bien sea en formato JSON o un nuevo HTML y lo remite al usuario que recibe la respuesta interpretada por el navegador mediante HTML+Bootstrap.

#### Estructura de Ficheros

El servidor de datos PostgreSQL y el servidor de interfaz web (Flask) deben ejecutarse en la misma máquina. Además, los ficheros de la base de datos deben estar en el mismo ordenador que el servidor de bases de datos para asegurar una latencia casi 0 y así evitar corrupciones. Esto debe ser así en cualquier sistema, tanto en el PC de usuario o en el servidor central.

#### Desarrollo

Se estructura la base de datos, se programan las macros y diseñan los formularios en el directorio `desarrollo` y luego para poner en producción hay que dar una serie de pasos que tenemos que definir más adelante.

#### Soporte

Para recibir soporte por parte de la IA para desarrollar la base de datos y su infraestructura, hay que proporcionarle un conjunto de ficheros a la misma. Se ubicarán en `desarrollo/fuentesIA`.

---

### Control de Versiones

El proyecto utiliza **Git** para control de versiones. Se hacen commits de los archivos principales cuando se consolidan cambios importantes. Esto permite:

- Volver a versiones anteriores si algo falla
- Tener historial de evolución del proyecto
- Trabajar de forma segura en desarrollo sin miedo a perder trabajo

Los archivos bajo control de versiones incluyen: **Pendiente de definir**

---

### Estructura de Ficheros

> **Nota:** Esta estructura será revisada durante el desarrollo/migración a PostgreSQL + Flask-SQLAlchemy.

| Directorio | Explicación |
|:---|:---|
| (Pendiente de definir) | ... |

---

### Documentos a Proporcionar a la IA

> **Nota:** Estos documentos serán revisados durante el desarrollo/migración a PostgreSQL + Flask-SQLAlchemy.

A la IA le debemos proporcionar los siguientes documentos para que nos proporcione soporte y constituya una fuente de conocimiento. Los documentos, su tipo y su procedencia (cómo se obtiene y utilidad) se listan a continuación:

| Nombre | Tipo | Procedencia | Script | Qué hace el script | Utilidad |
|:---|:---|:---|:---|:---|:---|
| `???` | `???` | Base de datos PostgreSQL | `???` | Crea un volcado de la estructura de la base de datos, sin datos | Conocer estructura base datos |
| `???.js` | `.js` | `???` | | | Proporciona los datos del interfaz y las reglas de los POST. Conocer estructura de formularios, controles, eventos y propiedades del interfaz |
| `???.html` | `.html` | | | | |
| `???.css` | `.css` | | | | |
| `???.py` | `.py` | `???` | | | Proporciona los datos de las reglas GET. Conocer estructura de las reglas GET |
| `Documentos.docx` | `.docx` | Ninguno. Editar y copiar en fuentesAI | Copia los `.docx` | | Documentos de resumen de las directrices de desarrollo del proyecto así como explicaciones de la estructura de las bases de datos, la lógica de los procedimientos, etc. |
| `datosmaestros.sql.txt` | `.sql` | Base de datos PostgreSQL | `???` | Extrae los datos de las tablas indicadas en `tablasmaestras.txt` y lo coloca en `fuentesIA/datosmaestros.sql.txt` | Conocer los datos que definen la lógica de negocio: `TIPOS_EXPEDIENTES`, `TIPOS_SOLICITUDES`, etc. |
| `tablasmaestras.txt` | `.txt` | Creada por el desarrollador | Edición manual en bloc de notas | Configuración del script `extraerdatosmaestros.py` | Contiene las tablas de datos maestros, que definen el negocio de la base de datos |
| `Estructura_fases_tramites_tareas.json` | `.json` | Manual (creada de forma interactiva con la IA) | Ninguno | Nada | Proporciona a la IA y al usuario las abstracciones en los elementos principales de los expedientes y la forma de organizar las tablas, identificando los mínimos datos necesarios |

---

### Proceso de Iteración de Desarrollo con la IA

Para la ayuda desde la IA en el proceso de desarrollo del proyecto, debo proporcionarle los archivos actualizados a medida que avanzo. El proceso sigue este flujo:

#### Ciclo de Iteración

1. Detecto necesidad
2. Le explico a la IA la necesidad y me ayuda a resolverla según el contexto actual de desarrollo
3. Realizo la implementación de la necesidad y la depuro de forma interactiva hasta que quedo satisfecho
4. Actualizo los ficheros pertinentes en las fuentes de la IA
5. Fin de iteración

#### Control de Versiones

El proyecto está bajo control de versiones (Git). Hago commits cuando hay cambios importantes consolidados. Esto garantiza que puedo volver atrás si algo no funciona.

#### Fases de Desarrollo

Esta forma de iterar con la IA para ir desarrollando todo el sistema tiene cuatro fases:

**Fase 1 - Estructura de Datos**

- Definición de tablas maestras (tipos de datos estructurales)
- Tablas de datos operacionales de expedientes
- Sin lógica de negocio implementada (todo está permitido)
- **Enfoque:** consolidar estructura de BD paso a paso

**Fase 2 - Interfaz de Usuario**

- Formularios de introducción de datos
- Macros de ayuda: navegación, filtrado, plantillas, apertura documentos
- Sin restricciones de lógica de negocio (el usuario controla qué hacer)
- **Enfoque:** consolidar interfaz funcional paso a paso
- Podría ponerse en producción al finalizar esta fase

**Fase 3 - Lógica de Negocio**

- Definición de tablas que configuran la lógica de negocio
- Interfaz para el supervisor del sistema (jefatura de servicio) para gestionar esas tablas
- Macros de validación basadas en consultas (no hardcoded)
- Despliegue progresivo en producción de nuevas funcionalidades
- **IMPORTANTE:** Aquí sí requiere mayor control porque ya hay usuarios y datos reales

**Fase 4 - Desarrollo Continuo**

- Mejoras y nuevas funcionalidades
- Base de datos en producción con usuarios activos
- Proceso de actualización y despliegue definido

#### Dependencias entre Archivos Fuente IA

Cuando modifico algo, debo actualizar los archivos correspondientes.

---

### Proceso de Despliegue en Producción

Para el despliegue en producción se necesitan tenemos los siguientes recursos:

- Servidores de bases de datos de producción, preprodducción y desarrollo.
- Los scripts se encuentran en sus carpetas correspondientes.

**Por definir.**

> **Nota:** Va a depender de los motores de bases de datos y formularios elegidos.

---

## Lógica de la Tramitación de Expedientes

Los expedientes de solicitudes de instalaciones de alta tensión se tramitan conforme a una normativa específica y mediante las reglas establecidas en las leyes sectoriales y la ley de procedimiento administrativo.

Tras analizar los distintos tipos de procedimientos se concluye que la tramitación tiene correlación con una serie de conceptos: **expediente**, **solicitud**, **proyecto**, **fase**, **trámite** y **tarea**.

---

### Relación Expediente, Solicitud, Proyecto, Fase, Trámite y Tarea

Se tramita un solo **expediente** cada vez, que dispone de un número único (por mantener el historial el número usado no será el ID del expediente en la base de datos, si no un número paralelo generado desde un valor base tomado de otra base de datos existente).

Cada expediente tiene un **único proyecto** asociado. Un proyecto puede tener modificaciones siempre que no desvirtúen su esencia (finalidad).

Cada expediente puede tener diferentes **solicitudes** (autorización administrativa previa, autorización administrativa de construcción, etc.) sobre el mismo proyecto inicial o el proyecto inicial con uno o más modificados.

Cada solicitud pasa por diferentes **fases** (ANÁLISIS SOLICITUD, INFORMACIÓN PÚBLICA, CONSULTAS, etc.) aunque hay casos en que puede haber más de una fase activa al mismo tiempo.

Cada fase puede tener uno o más **trámites** (por ejemplo la fase de información pública puede tener el trámite de publicación en BOE y el trámite de publicación en BOP) y cada trámite puede tener una o más **tareas** (redactar anuncio, poner en firma, notificar, esperar plazo, etc.).

#### Principio de Minimalismo Estructural

La estructura esquelética de la tramitación:

```
EXPEDIENTE → PROYECTO
EXPEDIENTE → SOLICITUD → FASE → TRAMITE → TAREA
```

es intencionalmente **simple en cuanto a campos**. La riqueza semántica **NO reside en múltiples campos** de cada tabla, sino en los **TIPOS** que definen cada entidad:

- `TIPO_EXPEDIENTE_ID`
- `TIPO_SOLICITUD_ID`
- `TIPO_FASE_ID`
- `TIPO_TRAMITE_ID`
- `TIPO_TAREA_ID`

Estos tipos son los que la legislación describe y nombra explícitamente: "Autorización Administrativa Previa", "Información Pública", "Consulta a Organismos", "Declaración de Utilidad Pública", etc. Son estos tipos los que determinan el procedimiento aplicable, no los campos individuales.

Por tanto, las **tablas estructurales** son contenedores de tiempo (fechas de inicio/fin) y conectores relacionales (claves foráneas), mientras que las **tablas de TIPOS** son diccionarios semánticos que dan significado procedimental.

Las reglas de negocio operan sobre estos tipos para determinar qué está permitido, qué es obligatorio y qué secuencias son válidas.

Esta arquitectura mantiene la base de datos **limpia, adaptable y alineada con la terminología legal**, delegando la complejidad procedimental al motor de reglas que se puede configurar y adaptar a los cambios normativos.

---

### Estructura de Negocio de la Tramitación

En nuestro caso queremos que la lógica de negocio **no sea rígida**, restringiendo lo que se puede o no se puede hacer en cada solicitud, fase, trámite, etc. de forma que no exista margen de maniobra para el usuario en tomar decisiones dentro de lo posible.

Deseamos que la lógica sea definida de la siguiente forma:

1. **En cualquier estado o situación del expediente, es posible hacer cualquier cosa que no esté expresamente prohibida.** En lugar de listar lo únicamente permitido, listar lo expresamente prohibido y permitir que se pueda hacer cualquier operación mientras no esté expresamente prohibida. Por ejemplo, una prohibición genérica sería que no se puede finalizar una fase si quedan trámites sin finalizar. Otra prohibición sería que no se puede iniciar la fase "resolver" si no se ha finalizado la fase "análisis solicitud".

2. **Las prohibiciones que definen la lógica de la tramitación ha de obtenerse de valores definidos en tablas, no internamente escrito en el código.** De esta forma la modificación de un precepto legal (y por tanto la lógica del procedimiento) no requiere modificar macros si no que solo requiere modificar los datos de las prohibiciones del procedimiento. Esto hace que el sistema se adapte rápidamente a los cambios.

La implementación técnica de este enfoque mediante tablas de reglas separadas de las tablas estructurales se detalla en la sección "Lógica de Negocio - Enfoque basado en Motor de Reglas" más adelante.

---

### Separación Datos Estructurales, Datos Lógica Negocio

Las tablas estructurales (`EXPEDIENTES`, `SOLICITUDES`, `PROYECTOS`, `FASES`, `TRAMITES`, `TAREAS`) contienen **ÚNICAMENTE datos (hechos) sobre lo que existe y ha ocurrido**.

Estas tablas **NO contienen campos** que implementen reglas de negocio como `REQUIERE_X`, `PERMITIDO_SI`, `SECUENCIA_OBLIGATORIA`, etc.

Las prohibiciones, validaciones, secuencias obligatorias y flujos procedimentales se definen en **tablas SEPARADAS** de configuración de reglas, que serán consultadas por el motor de reglas. Esta separación permite modificar el comportamiento del sistema sin alterar la estructura de datos ni el código.

#### Ejemplos de lo que NO va en tablas estructurales:

- `FASE.PERMITE_SIGUIENTE_FASE` → esto es una regla
- `TRAMITE.REQUIERE_DESTINATARIO` → esto es una regla
- `TIPO_SOLICITUD.FASES_OBLIGATORIAS` → esto es una regla

Estos conceptos se implementarán mediante tablas de reglas del tipo (ejemplos):

- `REGLAS_SECUENCIA_FASES`
- `REGLAS_VALIDACION_TRAMITES`
- `REGLAS_FLUJO_SOLICITUDES`

---

### Lógica de Negocio - Enfoque Basado en Motor de Reglas

#### Principio Fundamental

La lógica de negocio de la aplicación **NO se implementa mediante código duro** (funciones, procedimientos almacenados, triggers con lógica específica). En su lugar, se basa en un **motor de reglas genérico** alimentado por tablas de configuración.

#### Características del Sistema de Reglas

**1. Las reglas viven en tablas, no en código**

- Toda la lógica de validación, restricción y flujo se almacena como datos en tablas específicas
- Modificar el comportamiento del sistema implica modificar registros en estas tablas, no reescribir código
- Las reglas son versionables, auditables y reversibles como cualquier otro dato

**2. Las reglas leen valores de tablas estructurales**

- El motor de reglas consulta dinámicamente los datos de las tablas de estructura básica: `FASES`, `SOLICITUDES`, `EXPEDIENTES`, `PROYECTOS`, etc.
- Las reglas evalúan condiciones basándose en:
  - Valores de campos específicos (ej: `EXITO` de una fase)
  - Existencia o ausencia de registros relacionados
  - Relaciones entre entidades
  - Contexto del expediente (tipo de suelo, instrumento ambiental, etc.)

**3. Las reglas producen acciones**

Las reglas pueden generar diferentes tipos de acciones:

- **Bloquear:** Impedir al usuario realizar una acción (ej: crear una fase fuera de secuencia)
- **Sugerir:** Mostrar advertencias o recomendaciones sin impedir la acción
- **Obligar:** Forzar la creación/modificación de registros según condiciones
- **Calcular:** Derivar valores automáticamente basándose en otros datos
- **Validar:** Verificar la consistencia de los datos antes de confirmar cambios

**4. Las reglas son modificables sin tocar código**

- Los usuarios con permisos adecuados pueden modificar las reglas de negocio
- No se requiere intervención de programadores para ajustar el comportamiento del sistema
- Los cambios en las reglas tienen efecto inmediato
- Esto permite adaptación ágil a cambios normativos o procedimentales

#### Implicaciones para el Diseño Actual

**Fase de desarrollo/despliegue:**

**Fases 1 y 2 - Sin restricciones activas:**

- El usuario tiene libertad total
- **Indicadores visuales:** La interfaz muestra advertencias informativas (no bloqueantes) sobre datos incompletos o inconsistentes que son propios de la naturaleza de las tablas de datos (ej. dejar vacía un campo obligatorio)
- **Educación progresiva:** Los usuarios se familiarizan con el "debería ser" antes de que se active el "debe ser"

**Fase de producción con lógica activada (fases 3 y 4):**

- **Restricciones automáticas:** El motor de reglas evalúa y aplica las reglas definidas
- **Flujos guiados:** El sistema sugiere o impone el siguiente paso según el contexto. Se comenzará con el "sugiere" y en función de las decisiones de la dirección se implementa el "impone"
- **Validación en tiempo real:** Se previenen inconsistencias antes de que se confirmen
- **Flexibilidad mantenida:** Ajustar una regla no requiere nueva versión de software

#### Principio de No Redundancia

Los datos estructurales (como `EXITO` en `FASES`) no deben duplicar información que pueda deducirse de otros datos.

El motor de reglas es responsable de:

- Interpretar los datos básicos
- Aplicar las reglas configuradas
- Producir las acciones correspondientes

Los campos estructurales contienen únicamente información primaria, nunca derivada. En ocasiones la información se podría duplicar pero la fuente de la verdad debe permanecer a un único campo/tabla.

#### Validación No Obstructiva en la Interfaz

Las reglas de negocio se aplican mediante **validación en tiempo real** durante la edición de campos, sin interrumpir el flujo de trabajo del usuario.

El sistema **NO debe utilizar mensajes modales (MsgBox)** que bloqueen la interacción salvo riesgos de pérdidas de datos o rotura de la estructura del expediente o procedimiento.

En su lugar, las validaciones producen **indicadores visuales discretos**:

- **Validación exitosa:** El campo se muestra sin indicadores, guardado automático silencioso
- **Advertencia:** Asterisco rojo junto al campo con texto explicativo en gris debajo del mismo
- **Error (bloqueo):** Asterisco rojo más texto en rojo explicativo, y los campos dependientes se deshabilitan automáticamente hasta que se subsane el error

Este enfoque permite al usuario trabajar de forma natural (rellenando los campos administrativos -fechas de inicio y fin- directamente), mientras el motor de reglas valida en segundo plano y bloquea únicamente las acciones que violen restricciones fundamentales.

Por ejemplo, no se permite rellenar la fecha de inicio de una fase si la fase precedente obligatoria no tiene fecha de finalización, pero el sistema lo comunica deshabilitando el campo destino y mostrando la explicación, no mediante un popup intrusivo.

Todas las modificaciones de fechas quedan registradas automáticamente en el cuaderno de bitácora del sistema para auditoría y trazabilidad.

#### Flexibilidad en Fechas de Inicio y Fin

Los campos `FECHA`, `FECHA_INICIO` y `FECHA_FIN` en las tablas `SOLICITUDES`, `FASES` y `TRAMITES` permiten valores nulos (`NULL`). Esto permite modelar tres estados claramente diferenciados:

- **Fechas IS NULL:** La solicitud/fase/trámite está planificada o preparada pero no ha comenzado o finalizado formalmente
- **FECHA_INICIO NOT NULL y FECHA_FIN IS NULL:** La solicitud/fase/trámite está en curso
- **FECHA_INICIO NOT NULL y FECHA_FIN NOT NULL:** La solicitud/fase/trámite ha finalizado

Esta flexibilidad permite al usuario crear estructuras preparatorias y planificar la tramitación antes de iniciarla formalmente.

Las fechas representan las **fechas administrativas oficiales** (registro de entrada, cálculo de plazos, fechas de resoluciones) que deben introducirse manualmente o mediante macros de cálculo.

Las reglas de negocio determinarán cuándo es obligatorio que una fecha tenga valor mediante validaciones no intrusivas en el interfaz (por ejemplo, no se puede iniciar una fase dependiente si la fase precedente no tiene fecha de finalización).

---

## Estructura de Tablas y Tipos

### El Expediente y sus Tipos

Los tipos de expedientes se definen en la tabla maestra `TIPOS_EXPEDIENTES`. Como se puede apreciar está asociado al tipo de titular de la instalación y tipo de uso de la misma. Digamos que es una clasificación de las distintas particularidades que tiene la legislación respecto a la tramitación en cada caso.

El tipo de expediente define la lógica de la tramitación pues será una de las variables a tener en cuenta de cara a definir las restricciones o prohibiciones de la lógica de negocio.

El número de expediente (`NUMERO_AT`) es el nexo que une todo lo relativo a ese expediente desde el punto de vista del usuario tramitador. Internamente es el `ID` del expediente.

El **responsable ID** es la persona que es responsable de ese expediente por completo y en la estructura empresarial es la única persona que está permitida a actuar sobre es expedientes y todas las tablas y datos asociadas.

El sistema no impide a otro usuario actuar sobre ese expediente, pero en ese caso las actuaciones quedarán registradas en el cuaderno de bitácora, previa advertencia no intrusiva.

El campo **HEREDADO** indica que ese expediente viene heredado del sistema de tramitación anterior. Esto indica que solo tendrá como datos en tablas lo que ya existe en el sistema anterior de control, pero no tendrá todas las tablas normales de un expediente moderno. De esta forma si este campo es `SI`, la lógica de negocio y el usuario están informados de porqué no hay datos en muchas tablas.

---

### La Solicitud y sus Tipos

Los tipos de solicitudes (`TIPO_SOLICITUD_ID`) están claramente definidas en la legislación y definen el resultado buscado por el solicitante.

En cualquier caso siempre se pide un resultado de la misma desde el solicitante/peticionario/titular. Si no se obtiene el resultado esperado se produce una resolución de denegación, inadmisión, caducidad, aceptación renuncia, etc. para finalizar la solicitud.

Una solicitud siempre (si no fuese así deberíamos plantearnos sacarla fuera de estos tipos de solicitudes) termina con una fase "resolución".

La situación en la que se encuentra una solicitud depende de lo que hayan concluido sus fases. Con macros se puede crear un estado como conjunción de los distintos estados de cada fase/trámite/tarea.

El campo `FECHA` es la fecha de entrada de la solicitud en la Administración.

El campo `PROYECTO_ID` es la referencia al proyecto que se acompaña con la solicitud y que pertenece al expediente.

Hay tipos de solicitudes que se refieren a otras solicitudes que que hacen aquella se finalice. Estas son `DESISTIMIENTO` y `RENUNCIA`. El parámetro que las une es el campo `SOLICITUD_AFECTADA_ID` que es `NULL` por defecto para cualquier resolución, pero con la lógica de negocio será obligatorio dar un valor eligiendo la solicitud que se renuncia o desiste.

---

### La Fase y sus Tipos

Hay diferentes tipos de fases, muchas de ellas son comunes a los distintos tipos de solicitudes. Los tipos de fases se definen en la tabla `TIPOS_FASES`.

La característica principal de una fase es que tiene fechas de inicio y fin y que tiene un resultado de la misma.

Una fase es un conjunto de trámites para obtener un requisito para alcanzar el objetivo de la solicitud. Por ejemplo: obtención del pronunciamiento ambiental, de los condicionantes de los organismos, de la exposición del proyecto en información pública o de un informe favorable de un organismo externo.

#### Resumen de Conceptos y Flujo de Trabajo con el Diseño Simplificado de Fases

**Conceptos clave:**

**Tabla FASES** - cada fase del expediente tiene campos clave:

- `ID` de fase, `ID` de solicitud, tipo de fase, fecha de inicio, fecha de fin, observaciones.
- **Fecha de fin:** se define como la última fecha de finalización de todos los trámites asociados.
- **EXITO:** Es el valor booleano del resultado exitoso de la fase. Si es `SI`, la fase ha concluido exitosamente respecto a su tipo. Por ejemplo si la fase es "INFORME MINISTERIO" entonces se ha obtenido el informe favorable. Ese informe estará en el trámite/tarea correspondiente.
- **DOCUMENTO_RESULTADO_ID:** posible vínculo al documento oficial generado. Posiblemente desaparezca.

**Rellenado y flujo:**

- La fecha fin de la fase debe ser rellenada **manualmente por el usuario autorizado**. En fases posteriores del desarrollo, se podrá añadir una sugerencia automática basada en la fecha del último trámite cerrado, pero nunca será obligatoria ni se aplicará automáticamente.
- El éxito o no de la fase debe ser registrado **manualmente por el usuario autorizado** una vez analizada la documentación oficial correspondiente.
- Si `EXITO` es nulo, la fase está en curso o pendiente de cierre administrativo.
- Al tener el valor de éxito relleno (SÍ/NO) la fase se considera concluida y se puede permitir la creación o activación de fases sucesivas según reglas de negocio.

**Reglas de negocio y validación:**

- La fase sólo puede cerrarse tras completarse todos los trámites.
- La elección del resultado condiciona el flujo posterior y la posibilidad de nuevas fases.
- Campos manuales o semi-automatizados (fecha fin) y campos manuales (éxito) coexisten para flexibilidad y control.

Este diseño permite una gestión clara de la tramitación administrativa, manteniendo integridad, auditabilidad y control sobre el proceso mediante restricciones racionales y roles de usuario.

---

### El Trámite y sus Tipos

Tras la revisión detallada de los tipos de trámites en uno de los diagramas de flujo más completos, se concluye que:

- En los trámites, la secuencia de tareas sigue patrones.
- Los remitentes/destinatarios son variables. El elemento diferenciador es **a quién se dirige el trámite o de donde viene**: Ministerio, Medio Ambiente, Organismo, Solicitante, Interesado, Diarios, Ayuntamiento, etc.
- El tipo de comunicación/documento es variable: Informe, Subsanación/mejora, alegaciones, resolución, anuncio, etc.

Estos 3 datos diferenciales (secuencia, actores y documentos) se deberían poder deducir de la combinación `TIPO_TRAMITE` y de la tarea en si, así como de las reglas de negocio.

Por ejemplo, del trámite `ANUNCIO_BOP` se debería deducir que la secuencia es del tipo `REDACTAR→FIRMA→NOTIFICAR→PUBLICAR→ESPERAR`, que las tareas `REDACTAR` y `FIRMA` los documentos son el anuncio y el oficio que lo acompaña, que la tarea `NOTIFICAR` es al titular y a la Diputación encargada del BOP y que la tarea `ESPERAR` es el transcurso de tiempo.

Es por esto que un trámite es solo un **contenedor temporal y organizativo de tareas** dentro de una fase.

#### Tablas Necesarias para Conseguir el Objetivo

- Una tabla general de `TIPOS_TRAMITES` donde se listen todos los tipos y se incluya el nombre de la tabla asociada al tipo.
- Una tabla `TRAMITES` general que contenga los datos comunes a todos los tipos de trámites. Contiene instancias.
- No se necesita una tabla `TRAMITES_XXXXXX` por cada tipo con los campos específicos de ese tipo de trámite porque se ha condensado todo en los trámites, en las tareas y las reglas de negocio.

#### Implicaciones de la Solución Adoptada (consecuencias de la solución)

- Hay una relación uno a uno entre el nombre de la tabla específica para un tipo de trámite y el tipo en si en la tabla `TIPOS_TRAMITES`. Si esa relación se rompe se emitiría un error.
- Las instancias en `TRAMITES` sostienen la estructura real de los tramites que existan.

#### Ventajas (lo que nos ofrece)

- Integridad de datos fuerte
- Consultas SQL estándar
- Fácil validar datos específicos
- No requiere modificar la BD para nuevos tipos

#### Desventajas (lo que nos complica)

- Las reglas de negocio lo gobiernan todo.
- Cualquier desviación de un caso particular de esos patrones nos rompe la lógica. Hay que seguir estudiando casos particulares.

---

### La Tarea y sus Tipos

La tarea es la unidad de trabajo registrable con entrada de documento y salida de documento:

- **Relación unidireccional:** TAREA → DOCUMENTO (no al revés)
- **Documento agnóstico:** El documento no sabe de tareas, las tareas apuntan a documentos
- **Un documento, un productor:** Un documento solo puede ser producido por una tarea (índice único)
- **Un documento, múltiples consumidores:** Varias tareas pueden usar el mismo documento de entrada

Tras la revisión de las fases, trámites y tareas se concluye que solo hay **7 tipos de tareas**: `INCORPORAR`, `ANALISIS`, `REDACTAR`, `FIRMAR`, `NOTIFICAR`, `PUBLICAR` y `ESPERARPLAZO`.

La tarea tiene claves foráneas hacia documentos (documento usado y documento producido). Pueden ser nulas pero son sometidas a las comprobaciones de las reglas de negocio.

La tarea tiene una clave foránea hacia el trámite al que pertenece. No puede ser nula.

Tienen fechas de inicio y fecha de fin. Esas fechas se introducen manualmente por el usuario:

**Fecha de inicio:**

Puede ser la fecha administrativa del documento consumido, en la fecha en la que se inicia la tarea si no tiene plazo de inicio asociado, o en la fecha de inicio de plazos por el documento producido en la tarea anterior. Puede ser nula.

**Fecha de fin:**

Puede ser la fecha la fecha que tiene el documento producido, la fecha de finalización de un plazo o la fecha de finalización de la tarea si no tiene plazos asociados. Puede ser nula.

Las reglas de negocio comprobarán la coherencia entre la existencia de las claves foráneas de documentos y las fechas de inicio y fin, por ejemplo:

Una fecha de fin no nula implica que se debe comprobar que las tareas con salida obligatoria tienen que tener un id de documento producido no nulo.

---

**Documento creado:** 15 de enero de 2026  
**Versión:** Pendiente de revisión (duplicados con Tablas.md)
