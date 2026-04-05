# Guía General del Proyecto BDDAT

**Fecha de revisión:** 25/03/2026
> ⚠️ **Pendiente de actualizar:** sección de subsistema documental (decisiones post #191). Consultar `DISEÑO_SUBSISTEMA_DOCUMENTAL.md` para esa área.
> La sección del motor de reglas en este documento recoge los principios y la arquitectura general; para el mapa completo de reglas, esquema de tablas y pendientes de implementación ver `DISEÑO_MOTOR_REGLAS.md`.

---

## Índice

- [Propósito del Proyecto](#propósito-del-proyecto)
- [Filosofía del Diseño — Sostenibilidad e Herencia Institucional](#filosofía-del-diseño--sostenibilidad-e-herencia-institucional)
- [Desarrollo de la Base de Datos](#desarrollo-de-la-base-de-datos)
  - [Claves Técnicas](#claves-técnicas)
  - [Control de Versiones](#control-de-versiones)
  - [Estructura de Ficheros](#estructura-de-ficheros)
  - [Documentos a Proporcionar a la IA](#documentos-a-proporcionar-a-la-ia)
  - [Proceso de Iteración de Desarrollo con la IA](#proceso-de-iteración-de-desarrollo-con-la-ia)
  - [Proceso de Despliegue en Producción](#proceso-de-despliegue-en-producción)
- [Lógica de la Tramitación de Expedientes](#lógica-de-la-tramitación-de-expedientes)
  - [Relación Expediente, Solicitud, Proyecto, Fase, Trámite y Tarea](#relación-expediente-solicitud-proyecto-fase-trámite-y-tarea)
  - [Lógica de Negocio - Motor de Reglas](#lógica-de-negocio---motor-de-reglas)
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

## Filosofía del Diseño — Sostenibilidad e Herencia Institucional

### El problema real: legislación acumulada, no diseñada

La normativa de AT en Andalucía no es un sistema coherente. Es un palimpsesto: cada norma parcheó la anterior sin refactorizar el conjunto. El resultado son umbrales que se solapan o dejan huecos, conceptos que parecen idénticos pero tienen significado jurídico distinto según la ley que los usa, y competencias repartidas entre tres administraciones con secuencias que hay que deducir porque nadie las escribió explícitamente.

BDDAT no es un gestor de legislación. Es un tramitador con trabajo real y administrados que piden soluciones. El reto de diseño es precisamente ese: traducir ese galimatías a un sistema que funcione en el día a día y que además sea mantenible cuando cambie la norma, porque siempre cambia.

### Por qué la configurabilidad del motor es una decisión de sostenibilidad, no solo técnica

La tentación de hardcodear la lógica jurídica es real: la legislación es compleja, codificarla directamente en Python es más limpio y más rápido. El problema no es técnico, es institucional.

El escenario real es este: entra en vigor una nueva ley. El tramitador pita. Quien la diseñó ya no está, o está ocupado, o se ha jubilado. La Agencia Digital de Andalucía recibe el aviso. El técnico informático pregunta: "¿qué variable hay que cambiar?". La persona que conoce la ley no sabe qué es una variable. La persona que sabe de variables no conoce la ley. Resultado: parálisis, expedientes bloqueados, soluciones manuales mientras el sistema espera que alguien construya el puente entre ambos mundos.

**La configurabilidad del motor es ese puente.** No porque cualquiera pueda configurarlo sin conocimiento, sino porque con la documentación adecuada alguien con conocimiento jurídico limitado puede identificar qué cambiar, y alguien con conocimiento técnico limitado puede ejecutar el cambio sin tocar código.

Esto no significa exponer todo al Supervisor. La elegibilidad jurídica compleja (¿requiere esta instalación AAU, AAUS o Licencia Ambiental?) no es configurable por un técnico tramitador: requiere código con la ley en la mano. Lo que sí debe ser configurable son plazos, umbrales numéricos, documentos requeridos, y el árbol de fases que genera cada tipo de solicitud.

### La cadena de conocimiento: el verdadero activo del proyecto

El valor más duradero de BDDAT no está en el código. Está en la cadena de traducción entre el mundo jurídico y el sistema:

```
Ley (texto consolidado)
    → Extracción normativa (NORMATIVA_*.md)
        → Variables documentadas (DISEÑO_CONTEXT_ASSEMBLER.md)
            → Reglas del motor (reglas_motor + condiciones_regla en BD)
                → Tramitación real
```

Cada eslabón de esa cadena es documentación. Cuando esa cadena está completa y actualizada, alguien que no participó en el diseño puede:

1. Leer qué cambió en la ley
2. Encontrar qué variable está afectada y por qué existe
3. Entender qué reglas usan esa variable
4. Decirle al desarrollador exactamente qué tocar y dónde

Sin esa cadena, cada cambio normativo es una crisis. Con ella, es un procedimiento.

### La parte más difícil: las reglas que funcionan en casos reales

El motor agnóstico y el ContextAssembler son el marco. La extracción normativa y el diccionario de variables son el mapa. Pero lo que determina si el sistema funciona de verdad es si las reglas concretas —las filas en `reglas_motor` y `condiciones_regla`— cubren la casuística real de los expedientes.

Esa es la parte más difícil y la que requiere más iteración: casos límite, excepciones a excepciones, instalaciones que encajan en dos categorías a la vez, expedientes heredados con datos incompletos. Ningún diseño previo los anticipa todos. Se descubren tramitando.

Por eso BDDAT se despliega en fases con lógica progresiva: primero los técnicos usan el sistema sin restricciones activas, aprenden sus patrones, reportan los casos raros. Cuando las reglas se activan, ya hay evidencia empírica de qué casuística existe. Ese conocimiento no se puede derivar solo de la ley: requiere observación real.

### Resumen

| Decisión | Por qué |
|---|---|
| Motor configurable, no hardcodeado | Sostenibilidad cuando cambia la norma y cambian las personas |
| Configurabilidad parcial (no todo al Supervisor) | La elegibilidad jurídica compleja requiere código; los parámetros operativos, no |
| Documentación exhaustiva de variables y normas | Es la herencia institucional; sin ella el sistema es opaco para quien venga después |
| Despliegue progresivo con reglas activas por fases | Las reglas reales se aprenden tramitando, no solo leyendo la ley |

---

## Desarrollo de la Base de Datos

En el desarrollo de la base de datos vamos a enfrentarnos a la **organización de la información**, así como la necesidad de **concurrencia de los usuarios**.

Para la organización de la información se ha estudiado la lógica del proceso de tramitación de expedientes, y la relación entre la información que se maneja. De esta forma, la estructura de la base de datos está relacionada con la forma de tramitación de los expedientes.

Primero analizaremos las claves desde el punto de vista técnico, de implementación, conociendo las necesidades del entorno en el que vamos a desarrollar.

### Claves Técnicas

#### Entorno

- **Usuarios:** Windows 11, máximo 15, ampliable en red, con servidor de archivos mantenido por el entorno empresarial.
- **Base de datos:** PostgreSQL. El servidor de bases de datos se ejecuta inicialmente en el PC de un usuario en red y los clientes son otros usuarios en red. La base de datos y otros archivos se alojan en el mismo PC que corre el servidor. Se pretende que en el futuro el servidor de bases de datos se ejecute en el servidor central.
- **Comunicación con la base de datos (Backend):** Se usará la extensión Flask-SQLAlchemy que permite comunicarse con la base de datos mediante Python de forma abstracta (SQLAlchemy) y generar los comandos GET/POST con la base de datos.
- **Comunicación con el usuario (Frontend):** Se usará Bootstrap 5.3.3 (versión actual de la Junta). Implementación mediante CDNs oficiales.

#### Flujo de Trabajo

El usuario interactúa con el frontend (HTML+Bootstrap) y el navegador genera una orden POST mediante Javascript. En el servidor, Flask recibe ese POST y mediante código Python se decide lo que hay que hacer con esa petición. SQLAlchemy traduce a PostgreSQL el comando. Flask prepara una respuesta al usuario (orden GET) ya bien sea en formato JSON o un nuevo HTML y lo remite al usuario que recibe la respuesta interpretada por el navegador mediante HTML+Bootstrap.

#### Estructura de Ficheros

El servidor de datos PostgreSQL y el servidor de interfaz web (Flask) deben ejecutarse en la misma máquina. Además, los ficheros de la base de datos deben estar en el mismo ordenador que el servidor de bases de datos para asegurar una latencia casi 0 y así evitar corrupciones. Esto debe ser así en cualquier sistema, tanto en el PC de usuario o en el servidor central.

#### Soporte desde la IA

Se usará Claude Code. Permite acceso directo al repositorio y junto con los complementos MCP de postgre, Windows, Playright y Github, se puede obtener soporte para cambios en el código, conocimiento de la estructura real de la base de datos (postgre MCP), redimentsionado de ventanas (Windows MCP) e interacción automática con el navegador (playright MCP). Con este conjunto de complementos se pueden desarrollar la base de datos las rutas, los modelos, las migraciones y realizar tests para comprobación de las funcionalidades.

---

### Control de Versiones

El proyecto utiliza **Git** para control de versiones y Github par ael alojamiento remoto. Esto permite:

- Volver a versiones anteriores si algo regresiones.
- Tener historial de evolución del proyecto.
- Documentar los errores o nuevas características. 
- Realizar peticiones de mezcla con la rama de desarrollo.
- En general todo el flujo git y Github

---

### Estructura de Ficheros

La estructura de ficheros aproximada es la que se muestra en el README.
Ver https://github.com/genete/bddat?tab=readme-ov-file#-estructura-del-proyecto

---

### Documentos de Referencia para Claude Code

Claude Code lee directamente el repositorio y dispone de acceso a PostgreSQL via MCP.
Los documentos de referencia activos están listados en `CLAUDE.md` (raíz del repo) y en `docs/README.md`.

---

### Proceso de Iteración de Desarrollo con la IA

Para la ayuda desde la IA en el proceso de desarrollo del proyecto se sigue un flujo de trabajo que se detalla a continuación:

#### Ciclo de Iteración

1. Detecto necesidad
2. Le explico a la IA la necesidad y me ayuda a resolverla según el contexto actual de desarrollo
3. La IA realiza la implementación de la necesidad y los tests qe sean necesarios.
4. Superviso las implementaciones y se cierra la necesidad con un PR, merge a develop o incluso a main si el cambio es estable y permite un tag
5. Fin de iteración

#### Fases del proyecto

El proyecto en su desrrollo completo pasa por cuatro fases:

**Fase 1 - Estructura de Datos**

- Definición de tablas maestras (tipos de datos estructurales)
- Tablas de datos operacionales de expedientes
- Sin lógica de negocio implementada (todo está permitido)
- **Enfoque:** consolidar estructura de BD paso a paso

**Fase 2 - Interfaz de Usuario**

- Formularios de introducción de datos
- Implementación de rutas, operaciones GET/POST, navegación, filtrado, generación de plantillas, apertura documentos, creación de expedientes, solicitudes, fases, trámites y tareas. 
- Control de entrada de usuarios. Roles de usuarios.
- Sin restricciones de lógica de negocio (el usuario controla qué hacer)
- **Enfoque:** consolidar interfaz funcional paso a paso
- Podría ponerse en producción al finalizar esta fase

**Fase 3 - Lógica de Negocio**

- Definición de tablas que configuran la lógica de negocio
- Interfaz para el supervisor del sistema (jefatura de servicio) para gestionar esas tablas
- Scripts de validación basadas en consultas (no hardcoded)
- Despliegue progresivo en producción de nuevas funcionalidades
- **IMPORTANTE:** Aquí sí requiere mayor control porque ya hay usuarios y datos reales

**Fase 4 - Desarrollo Continuo**

- Mejoras y nuevas funcionalidades
- Base de datos en producción con usuarios activos
- Proceso de actualización y despliegue definido

---

### Proceso de Despliegue en Producción

Para el despliegue en producción se necesitan tenemos los siguientes recursos:

- Servidores de bases de datos de producción, preprodducción y desarrollo.
- Los scripts se encuentran en sus carpetas correspondientes.

**Por definir.**

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

### Lógica de Negocio - Motor de Reglas

#### Principios Fundamentales

**1. Enfoque permisivo:** En cualquier estado del expediente, es posible hacer cualquier cosa que no esté expresamente prohibida. En lugar de listar lo únicamente permitido, se listan las prohibiciones expresas, permitiendo flexibilidad operativa dentro del marco legal.

**2. Separación de datos y reglas:** Las tablas estructurales (`EXPEDIENTES`, `SOLICITUDES`, `PROYECTOS`, `FASES`, `TRAMITES`, `TAREAS`) contienen **únicamente datos sobre lo que existe y ha ocurrido**. Las prohibiciones, validaciones y flujos procedimentales se definen en **tablas separadas** de configuración de reglas.

**3. Reglas configurables:** Las reglas viven en tablas, no en código. Modificar el comportamiento del sistema implica modificar registros en tablas de reglas, no reescribir código. Esto permite adaptación ágil a cambios normativos.

**4. Principio de escape:** Todo filtro, cascada o regla debe tener vía de escape. El técnico tramitador puede encontrar situaciones no previstas en el flujo normal (alegaciones fuera de contexto, cambio de rumbo del expediente, etc.). El sistema nunca crea callejones sin salida: el usuario puede elegir opciones «fuera de contexto» con advertencia visual, y toda acción de escape queda registrada en el cuaderno de bitácora.

#### Implementación del Motor de Reglas

**Cómo funcionan las reglas:**

- El motor lee dinámicamente datos de las tablas estructurales
- Evalúa condiciones basándose en valores de campos, existencia de registros relacionados y contexto del expediente
- Produce dos tipos de acción: **BLOQUEAR** (impedir la operación) o **ADVERTIR** (advertencia no bloqueante que el técnico puede ignorar)
- Opera sobre cuatro eventos del ciclo de vida de cada entidad ESFTT: **CREAR**, **INICIAR**, **FINALIZAR** y **BORRAR**

> Ver esquema completo de reglas y condiciones en `DISEÑO_MOTOR_REGLAS.md`.

**Ejemplos de reglas:**

- No se puede finalizar una fase si quedan trámites sin finalizar
- No se puede iniciar la fase "resolver" si no se ha finalizado la fase "análisis solicitud"
- No se puede rellenar fecha de inicio de una fase si la fase precedente obligatoria no tiene fecha de finalización

**Ejemplos de lo que NO va en tablas estructurales:**

- `FASE.PERMITE_SIGUIENTE_FASE` → esto es una regla
- `TRAMITE.REQUIERE_DESTINATARIO` → esto es una regla
- `TIPO_SOLICITUD.FASES_OBLIGATORIAS` → esto es una regla

Estos conceptos se implementan mediante las tablas `REGLAS_MOTOR` (una fila por regla, indexada por evento y entidad) y `CONDICIONES_REGLA` (condiciones 1:N por regla, con lógica AND/OR). Ver `DISEÑO_MOTOR_REGLAS.md` para el esquema completo.

#### Validación No Obstructiva en la Interfaz

Las reglas se aplican mediante **validación en tiempo real** sin interrumpir el flujo de trabajo. El sistema **NO utiliza mensajes modales (MsgBox)** salvo riesgos de pérdidas de datos o rotura de estructura.

**Indicadores visuales discretos:**

- **Validación exitosa:** Campo sin indicadores, guardado automático silencioso
- **Advertencia:** Asterisco rojo junto al campo con texto explicativo en gris debajo
- **Error (bloqueo):** Asterisco rojo más texto en rojo explicativo, campos dependientes deshabilitados hasta subsanar

**Ejemplo:** No se permite rellenar fecha de inicio de una fase si la fase precedente obligatoria no tiene fecha de finalización, pero el sistema lo comunica deshabilitando el campo y mostrando la explicación, no mediante popup.

Todas las modificaciones quedan registradas automáticamente en el cuaderno de bitácora del sistema.

#### Evolución por Fases

**Fases 1 y 2 - Sin restricciones activas:**

- Libertad total del usuario
- Indicadores visuales informativos (no bloqueantes) sobre datos incompletos o inconsistentes propios de la naturaleza de las tablas
- Educación progresiva: usuarios se familiarizan con el "debería ser" antes del "debe ser"

**Fase 3 en adelante - Con lógica activada:**

- Restricciones automáticas según reglas definidas
- La iniciativa es siempre del técnico; el motor informa o bloquea, no genera el flujo por sí mismo
- Validación en tiempo real previene inconsistencias
- Flexibilidad mantenida: ajustar reglas no requiere nueva versión de software

#### Flexibilidad en Fechas

Los campos `FECHA`, `FECHA_INICIO` y `FECHA_FIN` permiten valores nulos (`NULL`), modelando tres estados:

- **IS NULL:** Planificada pero no iniciada/finalizada
- **FECHA_INICIO NOT NULL y FECHA_FIN IS NULL:** En curso
- **FECHA_INICIO NOT NULL y FECHA_FIN NOT NULL:** Finalizada

Las fechas representan **fechas administrativas oficiales** que se introducen manualmente o mediante macros. Las reglas determinarán cuándo es obligatorio que tengan valor mediante validaciones no intrusivas.

> El diseño completo del subsistema de fechas y plazos (vocabulario, modelo de datos, cálculo de `fecha_limite`, calendario de inhábiles, suspensiones) está en `docs/DISEÑO_FECHAS_PLAZOS.md`.
> La normativa legal de referencia (LPACAP + leyes sectoriales AT) está en `docs/NORMATIVA_PLAZOS.md`.

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

La relación entre la solicitud y el proyecto se deduce de manera indirecta. El proyecto consta de documentos sucesivos en el tiempo: proyecto original, modificado_1, modificado_2, etc. Las solicitudes que se realicen se refieren al proyecto y sus modificaciones a fecha de la solicitud. De esta forma podemos saber que proyecto y sus modificados son sobre los que se solicita la solicitud. Si el modificado se produce con una solicitud en curso y requiere un inicio de la solicitud (porque el cambio invalida lo realizado) la solicitud incial se debe finalizar con resolución de archivo y la nueva se inicia con fecha posterior al modificado. Si el proyecto se modifica cuando se ha resuelto la solicitud inicial, se inicia una nueva solicitud conincidente con el modificado. 

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
- **RESULTADO_FASE_ID:** FK a `tipos_resultados_fases`. Registra el resultado al cerrar la fase. Valores del catálogo: `FAVORABLE`, `FAVORABLE_CONDICIONADO`, `DESFAVORABLE`, `NO_PROCEDE`, `DESISTIDA`, `ARCHIVADA`. Una fase "exitosa" ≡ `resultado_fase.codigo IN ('FAVORABLE', 'FAVORABLE_CONDICIONADO')`. NULL = fase en curso o pendiente de cierre.
- **DOCUMENTO_RESULTADO_ID:** posible vínculo al documento oficial generado. Posiblemente desaparezca.

**Rellenado y flujo:**

- La fecha fin de la fase debe ser rellenada **manualmente por el usuario**. En fases posteriores del desarrollo, se podrá añadir una sugerencia automática basada en la fecha del último trámite cerrado, pero nunca será obligatoria ni se aplicará automáticamente.
- El resultado de la fase debe ser registrado **manualmente por el usuario** una vez analizada la documentación oficial correspondiente, eligiendo uno de los valores del catálogo `tipos_resultados_fases`.
- Si `RESULTADO_FASE_ID` es nulo, la fase está en curso o pendiente de cierre administrativo.
- Al tener `RESULTADO_FASE_ID` relleno, la fase se considera concluida y se puede permitir la creación o activación de fases sucesivas según reglas de negocio. Las reglas que requieren "fase exitosa" evalúan `resultado_fase.codigo IN ('FAVORABLE', 'FAVORABLE_CONDICIONADO')`.

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

#### Ventajas (lo que nos ofrece)

- Integridad de datos fuerte
- Consultas SQL estándar
- Fácil validar datos específicos
- No requiere modificar la BD para nuevos tipos

#### Desventajas (lo que nos complica)

- Las reglas de negocio lo gobiernan todo.
- Cualquier desviación de un caso particular de esos patrones nos rompe la lógica. Habría que seguir estudiando casos particulares.

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
