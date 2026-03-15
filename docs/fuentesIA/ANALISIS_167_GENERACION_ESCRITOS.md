# Analisis #167 — Generacion de escritos administrativos

> **Estado:** En estudio. Documento de trabajo para retomar entre sesiones.
> **Issues relacionados:** #167 (abierto), #189 (cerrado)
> **Fecha inicio analisis:** 2026-03-15

---

## Inventario de lo implementado (#189 cerrado)

| Componente | Estado | Ubicacion |
|---|---|---|
| Modelo `TipoEscrito` | HECHO | `app/models/tipos_escritos.py` |
| Modelo `ConsultaNombrada` | HECHO | `app/models/consultas_nombradas.py` |
| Migracion BD (ambas tablas) | HECHO | `migrations/versions/20c5d1e9d782*.py` |
| `ContextoBaseExpediente` (Capa 1) | HECHO | `app/services/escritos.py` |
| `generar_escrito()` (orquestador) | HECHO (parcial) | `app/services/generador_escritos.py` |
| Dependencia `docxtpl` | HECHO | `requirements.txt` (commit 6b85fcf) |
| Admin plantillas — CRUD 4 pantallas | HECHO | `app/modules/admin_plantillas/` |
| Panel de tokens copiables | HECHO | `_panel_tokens.html` |
| Protocolo URI `bddat-explorador://` | HECHO | Issue #231 |
| Config `PLANTILLAS_BASE` | HECHO | `app/config.py` |
| Plantilla de prueba .docx | HECHO | `docs_prueba/plantillas_escritos/plantillas/` |
| Guia Context Builders | HECHO (doc) | `docs/fuentesIA/GUIA_CONTEXT_BUILDERS.md` |

**Pendiente del orquestador:**
- Ejecucion de consultas nombradas: `_ejecutar_consultas()` devuelve `{}` (stub)
- Context Builders (Capa 2): arquitectura lista, cero implementaciones
- No hay endpoint que dispare la generacion desde la UI de tramitacion

---

## 1) Mapa de necesidades (revisado)

### A. Supervisor — momento de crear/gestionar la plantilla

#### A0. Filtrado dinamico de tokens y contexto ESFTT en cascada — CRITICO, NO DIFERIBLE

**Necesidad:** Cuando el supervisor crea una plantilla nueva, selecciona el contexto ESFTT
(tipo solicitud, fase, tramite). Actualmente:
- Los selectores NO filtran en cascada (solicitudes por tipo de expediente, fases por solicitud, tramites por fase)
- El panel de tokens NO se actualiza en funcion del contexto seleccionado
- Los tokens mostrados son siempre los mismos (Capa 1 estatica)

**Implicacion:** El supervisor no sabe que tokens son relevantes para su contexto.
No conoce las tablas ni sus campos. Necesita que la interfaz le muestre solo lo aplicable.

**Relacion con motor de reglas:** El filtrado ESFTT usa la misma logica que el motor
de reglas para determinar que aplica a que contexto. El diseno de este mecanismo
no puede diferirse a cuando se implemente el motor completo — hay que establecerlo ahora.

**Preguntas de diseno abiertas:**
- Los tokens de Capa 1 son genericos (datos del expediente). Son siempre los mismos
  independientemente del contexto ESFTT?
- Los tokens de Capa 2 (Context Builders) si dependen del contexto. Como se descubren
  dinamicamente segun el contexto seleccionado?
- Las consultas nombradas: tienen contexto ESFTT propio o son transversales?

> **Comentario del usuario:** "Este contexto ESFTT implica que el descubrimiento de tokens
> a introducir en la plantilla cuando se crea, ha de estar sincronizado con dicho contexto.
> No se si esta actualmente hardcodeado o se puede extraer fuera."

---

#### A1. Validacion de sintaxis del .docx subido — NO DIFERIBLE

**Necesidad:** Comprobar que `python-docx-template` puede parsear la plantilla sin errores
Jinja2 antes de registrarla. Un token mal escrito (`{{titlar}}`) solo se detectaria al generar.

**Implementacion esperada:** Paso previo a la accion de registrar. Si falla, informar
del error exacto y no permitir el registro.

> **Comentario del usuario:** "Si, tiene toda la logica. Seria una validacion de sintaxis.
> Un paso previo a la accion de registrar. No diferible."

---

#### A2. Probar plantilla con datos reales — DIFERIBLE

**Necesidad:** Boton "Generar prueba con expediente X" que descargue el .docx relleno
sin registrarlo en ningun pool.

> **Comentario del usuario:** "No le veo extrema necesidad. Si la sintaxis es correcta
> significa que los datos o consultas tienen reflejo en la base de datos o fragmentos existen.
> Incluso si los fragmentos no existen se informa pero no invalida el registro. Podria estar
> en fase de creacion del fragmento y necesita la plantilla vacia para darle forma al fragmento
> dentro de la plantilla y luego extraer el fragmento fuera. Es el momento de uso real cuando
> se alerta de la ausencia de datos o fragmentos e incluso en ese momento el usuario podria
> querer usar la plantilla. Podria diferirse."

---

#### A3. Gestion de fragmentos y parseo automatico del .docx — NECESARIO (parcial)

**Necesidad:** El sistema debe parsear el .docx subido y detectar automaticamente:
- Campos directos (`{{campo}}`)
- Campos de lista (`{%p for item in lista %}`)
- Consultas nombradas (`{%tr for row in query %}`)
- Fragmentos insertables (`{{r fragmento}}`)

Tras detectarlos, registrar en `tipos_escritos` lo que corresponda.

**Sobre fragmentos:** Son responsabilidad del supervisor. Se almacenan como .docx
en `PLANTILLAS_BASE/fragmentos/`. El panel de tokens los lista pero no hay CRUD.
Un historico de fragmentos seria interesante pero diferible como modulo aparte.

**REFLEXION IMPORTANTE del usuario sobre tipos_escritos vs tipos_documentos:**

> "tipos_escritos y tipos_documentos tienen dos funciones distintas. tipos_escritos
> encaja el escrito en el contexto (SFT) pero no tiene el tipo de expediente que tambien
> es contexto. Y tiene una FK a tipo de documento. Tipo de documento es la base de la
> seleccion del documento a consumir o generar en las tareas. Tiene una doble funcion pues
> los documentos no son todos internos, tambien clasifica los externos. El tipo de documento
> de un escrito generado por la plantilla no puede ser un tipo externo (algo hay que hacer)"
>
> **<<< Sesion dedicada pendiente sobre tipos_escritos vs tipos_documentos >>>**

**Pregunta de diseno sobre tipos_escritos:**

> "te das cuenta de que la estructura de tipos_escritos no esta funcionando??
> Tiene lo que tiene que tener o es excesivo? Que debe definir realmente????"

---

#### A4. CRUD de consultas nombradas — NECESARIO

**Necesidad:** Las consultas nombradas (SQL parametrizado) las crea el programador
(via migracion o directamente). El CRUD sirve para que el supervisor vea que consultas
existen, que hacen y en que contexto ESFTT aplican.

> **Comentario del usuario:** "Para la creacion de la consulta en si veo excesivo un CRUD.
> La consulta no hay otra forma que hacerla desde el propio programador y darle un nombre
> (migracion). Luego si acaso el programador puede usar un CRUD para estas consultas
> nombradas respecto a su tabla de exposicion al supervisor. Lo mas interesante es
> documentar que hace esa consulta cruzada para poder usarla correctamente y en que
> contexto ESFTT aplica. Si el CRUD es necesario."

---

#### A5. Versionado de plantillas — DIFERIBLE

**Necesidad:** Historico de versiones de las plantillas .docx.

> **Comentario del usuario (literal, incluye flujo completo del supervisor):**
>
> "Para entender el versionado de plantillas reviso el flujo: No existe una cierta plantilla.
> El supervisor abre un documento en blanco o copia otro documento existente con ciertas
> partes ya creadas (formato) y empieza a escribir la parte que no es ni fragmento ni campo.
> Deja migas de pan en los huecos donde quiere poner los campos (sabe lo que quiere).
> Termina y tiene una plantilla con texto, campos, tablas, campos calculados, y fragmentos
> nombrados, pero en formato personal (subrayado en amarillo por ejemplo). Esa plantilla
> no vale para nada, no toma datos reales. Habla con el programador y le dice las necesidades
> que tiene, especialmente en los consultas nombradas o campos calculados. Le explica el
> contexto donde se necesita esa plantilla. El programador comprueba si existen los campos
> en la capa 1 si hay campos de listados posibles, si hay tablas posibles por consultas
> nombradas o campos calculados. Incluso le puede advertir de que no hay fragmento registrado
> para eso. El programador crea lo necesario y comprueba que los tokens estan accesibles
> al supervisor para crear la plantilla. El supervisor crea (registra la plantilla nueva
> con los tokens ya dentro y funciona."
>
> "El control de versiones es responsabilidad del supervisor. [...] Puede diferirse."

---

#### ~~A6. Feedback sobre campos vacios~~ — ELIMINADA

> **Comentario del usuario:** "No lo veo necesario. Que aporta?"

---

### B. Tramitador — momento de usar la plantilla en tarea REDACTAR

#### B1. Accion "Generar escrito" en tarea REDACTAR — NECESARIO

**Necesidad:** Mecanismo en la UI de tarea para lanzar la generacion.
Boton en la card de tarea o en el dropdown de acciones.

---

#### B2. Seleccion de plantilla filtrada por contexto ESFTT — IMPRESCINDIBLE

**Necesidad:** Lista de plantillas aplicables al contexto actual (tipo solicitud + fase + tramite),
con logica de NULLs como comodines.

> **Comentario del usuario:** "Si no hay plantillas pues no puedo continuar la tarea.
> Boton generar deshabilitado."

---

#### B3. Previsualizacion de campos antes de generar — NECESARIO

**Necesidad:** Resumen de campos detectados en la plantilla, sus valores del expediente,
alerta si alguno esta vacio. El tramitador ve esto ANTES de pulsar "Generar".

---

#### B4. Guardado con nombre sistematizado + checkboxes opcionales — NECESARIO

**Flujo decidido:**
1. Generar sustituye campos por valores
2. El sistema ofrece guardar con nombre propuesto (sistematizado: codigo plantilla + numero expediente + solicitud)
3. La ruta debe estar DENTRO de `FILESYSTEM_BASE`, navegable con un explorador similar al del pool
4. **Checkbox 1:** Registrar en pool (opcional, advertencia si no se marca)
5. **Checkbox 2:** Asignar como documento producido (opcional)
6. Motivo de los checkboxes: permitir regeneracion tras corregir datos sin acumular registros

> **Comentario del usuario:** "Generar escrito sustituye los campos por valores y le da la
> opcion al usuario de guardar el escrito en un sitio en el servidor de archivos con un nombre
> propuesto (de la propia plantilla con alguna especificidad). [...] Registrar ESE documento
> guardado en el pool? Si, pero opcionalmente. Mediante marcado de checkbox junto al boton
> generar. Advirtiendoo que si no se marca lo debe registrar a mano. Asignar como documento
> producido. Igualmente. [...] Porque el usuario podria querer hacer una segunda iteracion
> al darse cuenta de que el documento tiene datos erroneos."
>
> **<<< Sesion dedicada pendiente: SISTEMATIZACION DE NOMBRES DE ARCHIVOS >>>**

---

#### B5. Abrir carpeta contenedora tras generar — NECESARIO

**Necesidad:** Checkbox adicional para abrir la carpeta del archivo generado en el explorador
de Windows, similar al comportamiento existente en el pool.

> **Comentario del usuario:** "Igual que hay un checkbox para registrar en pool y otro para
> asignar a documento producido, habria un checkbox para abrir carpeta contenedora tras generar."

---

#### B6. Regeneracion: sobrescritura transparente — NECESARIO

**Comportamiento decidido:**
- Si el usuario regenera con la misma ruta y nombre: aviso de sobrescritura
- Si acepta: el binario se reemplaza en disco
- Si estaba registrado en pool: la URL no cambia, el documento_producido_id tampoco.
  Solo se ha sustituido el contenido del fichero
- Cualquier otro comportamiento seria complejo e innecesario

> **Comentario del usuario:** "El usuario sabe lo que esta haciendo. Otra historia es que
> borre el archivo del sistema y no lo arregle en el pool. Pero eso se llama deteccion de
> huerfanos del pool. Que es otro area a tratar."

---

#### ~~B7. Edicion post-generacion y re-subida~~ — NO REQUIERE IMPLEMENTACION

**Decision:** Transparente a BDDAT. El usuario edita el .docx en Writer directamente.
Si le cambia el nombre lo deja huerfano; si solo edita el contenido, el sistema no nota nada.

---

#### B8. Generar = iniciar tarea (si no iniciada) — DECISION TOMADA

**Regla:** Si la tarea no tiene `fecha_inicio` y el usuario genera un escrito,
se establece `fecha_inicio = hoy` automaticamente. Es un indicador de interaccion.

Finalizar (`fecha_fin`) lo hace el usuario cuando esta satisfecho con el escrito.
La tarea finalizada es presupuesto para la siguiente tarea FIRMAR.

> **Comentario del usuario:** "El inicio de la tarea crear escrito es simplemente de
> auditoria interna, no tiene valor administrativo."

---

#### ~~B9. Generar desde tramite~~ — ELIMINADA, DEPRECAR EN ISSUE

> **Comentario del usuario:** "No existe posibilidad de redactar desde un tramite.
> La frase del issue no esta bien construida. No existe esa necesidad. Deprecar en el issue."

---

### C. Necesidades transversales

#### C1. Ejecucion de consultas nombradas — NECESARIO

El stub `_ejecutar_consultas()` debe implementarse para que las plantillas con tablas
(`{%tr for row in ...}`) funcionen. Sin esto, las tablas salen vacias.

---

#### C2. Context Builders (Capa 2) — DIFERIBLE (condicionado)

La arquitectura existe. Se implementaran bajo demanda cuando el primer tipo de escrito
complejo lo requiera. No es bloqueante para el flujo basico de generacion.

---

#### C3. Trazabilidad: quien genero, cuando, con que plantilla — PENDIENTE DE DECISION

El `Documento` registrado en pool no lleva referencia a que `TipoEscrito` lo genero.
Si alguien pregunta "con que plantilla se hizo este requerimiento?", no hay forma
de saberlo desde la BD.

**Pregunta abierta:** Es necesario? FK en documento a tipo_escrito? Campo observaciones?

---

#### C4. Metadatos del documento generado — PENDIENTE DE DECISION

Al crear `Documento` en pool: que `asunto` se pone? La `fecha_administrativa`
es la fecha de generacion o NULL (porque aun no esta firmado)? La `prioridad`?

**Propuesta:** Asunto = nombre del tipo_escrito + contexto minimo.
Fecha administrativa = NULL hasta firma. Prioridad = 0.

---

#### C5. Motor de reglas pre-generacion — PENDIENTE DE DECISION

Debe el motor evaluar algo antes de permitir generar? Ejemplo: "no generar resolucion
si no existe informe tecnico favorable". O solo se evalua al FINALIZAR la tarea
(que ya verifica `documento_producido`)?

---

#### C6. Permisos y roles — PENDIENTE DE DECISION

Todos los tramitadores pueden generar escritos? O solo ciertos roles?
El admin de plantillas ya esta protegido, pero la accion de generar?

---

#### C7. Gestion de errores de generacion — NECESARIO

Si la plantilla tiene error Jinja2, o un campo no existe, o una consulta falla:
toast de error con detalle suficiente para que el tramitador informe al supervisor.

---

#### C8. Ruta de almacenamiento y sistematizacion de nombres — NECESARIO

Vinculado con B4. El .docx generado se guarda en `FILESYSTEM_BASE` con:
- Ruta: dentro del arbol del expediente, navegable
- Nombre: sistematizado (codigo plantilla + numero expediente + solicitud + ?)

**<<< Sesion dedicada pendiente: SISTEMATIZACION DE NOMBRES DE ARCHIVOS >>>**

---

## Cabos sueltos — sesiones dedicadas pendientes

### Cabo 1: Estructura de `tipos_escritos`

La tabla actual tiene muchos campos. El usuario pregunta:
"Tiene lo que tiene que tener o es excesivo? Que debe definir realmente?"

Campos actuales: `id, codigo, nombre, descripcion, ruta_plantilla, tipo_documento_id,
contexto_clase, campos_catalogo, tipo_solicitud_id, tipo_fase_id, tipo_tramite_id,
filtros_adicionales, activo`.

Si el sistema parsea automaticamente el .docx y detecta que tokens usa,
algunos campos podrian ser redundantes o autocalculados.

### Cabo 2: `tipos_documentos` — internos vs externos

Los tipos de documento clasifican tanto documentos externos (incorporados)
como internos (generados). El `tipo_documento_id` de un `TipoEscrito` deberia
apuntar solo a tipos "internos". Hay que definir esa distincion o al menos
impedir que un escrito generado se clasifique como tipo externo.

> **Comentario del usuario:** "debemos tener una sesion dedicada a esto solamente
> (probablemente sea mas para reforzar mi comprension del funcionamiento del sistema
> que la tuya)"

### Cabo 3: Sistematizacion de nombres de archivos

Definir convencion de nombrado para archivos generados.
El usuario lo considera "un apartado muy interesante y util".
Afecta a B4 y C8.

### Cabo 4: Filtrado dinamico de tokens por contexto ESFTT

Mecanismo tecnico para que al cambiar el contexto S/F/T en la UI de admin,
los tokens disponibles se actualicen. Implica:
- Que tokens son estaticos (Capa 1) vs dinamicos (Capa 2, consultas nombradas)
- Como se descubren los Context Builders aplicables a un contexto dado
- Endpoint AJAX para devolver tokens filtrados

### Cabo 5: Nota sobre dependencias del #189

> **Comentario del usuario:** "el issue #189 requiere alguna actualizacion.
> los requerimientos no son exactamente python-docx-template.
> Ver commit 6b85fcf4d404730758c90314f393c6bbcef6af52"

---

## Proximos pasos (cuando se retome)

1. Resolver cabos sueltos (sesiones dedicadas)
2. Completar punto 2) Dependencias con otros modulos
3. Completar punto 3) Riesgos e inconsistencias
4. Completar punto 4) Orden logico de decisiones de diseno
5. Completar punto 5) Preguntas sin respuesta
6. Solo entonces: tocar codigo

---

## ANEXO — Comentarios del usuario (2026-03-15, literal)

Yo me había planteado algunas preguntas que parcialmente están contestadas por ti.
Por ejemplo: Cuando el supervisor crea una plantilla completamente nueva, se le pregunta cual es el contexto de esta plantilla ESFTT, se le pide que lo defina. Pero sin embargo no hay sistema que detecte esos datos introducidos y actualice el listado de tokens disponibles en función del contexto. Tampoco se produce filtrado de las solicitudes en función del tipo de expediente, de las fases en función de la solicitud seleccionada y de los trámites en función de la fase. El sistema de contexto de donde se puede usar una plantilla está directamente relacionado con su creación. Y para crearlo el supervisor (que no conoce los nombres de las tablas ni sus campos) tiene que poder saber que es cada campo y que significa. (listado de tokens disponibles) Es un asunto relacionado con el motor de reglas pero no se puede diferir a cuando se implemente. Hay que establecer su diseño ahora. <<< IMPORTANTE.
Este contexto ESFTT implica que el descubrimiento de tokens a introducir en la plantilla cuando se crea, ha de estar sincronizado con dicho contexto. No se si está actualmente harcodeado o se puede extraer fuera. Habría que tenerlo en cuenta en las necesidades.

Sobre el resto de necesidades te comento:
A1: Si, tiene toda la lógica. Sería una validación de sintaxis. Un paso previo a la acción de registrar. No diferible.
A2: No le veo extrema necesidad. Si la sintaxis es correcta significa que los datos o consultas tienen reflejo en la base de datos o fragmentos existen. Incluso si los fragmentos no existen se informa pero no invalida el registro. Podría estar en fase de creación del fragmento y necesita la plantilla vacía para darle forma al fragmento dentro de la plantilla y luego extraer el fragmento fuera. Es el momento de uso real cuando se alerta de la ausencia de datos o fragmentos e incluso en ese momento el usuario podría querer usar la plantilla. Podría diferirse.
A3: Los fragmentos los considero responsabilidad absoluta del supervisor. Sería interesante establecer un sistema de histórico de fragmentos, ya que permiten volver a atrás. El problema es que el fragmento metido dentro de la base de datos podría incluir formateado docx necesario para darle profesionalidad al mismo, y eso complica que el fragmento se incluya como dato en la bb. Si te refieres a que el fichero del fragmento se controle dentro de la base de datos, evidentemente debería haber un sistema que ligue la plantilla con los fragmentos que usa. Se podría hacer de forma automática: El supervisor, en un contexto determinado ofrecido por la interfaz y elegido por el, crea un documento y lo sube a registrar. El sistema parsea el documento y detecta campos directos, campos de lista, consultas nombradas y fragmentos. (Los campos pueden ser del contexto base o del contextbuilder). De alguna forma el sistema sabe que campos y fragmentos usa. Entonces los registra. tipos_escritos tiene varios campos que ya contemplan eso me parece a mi.  REFLEXIÓN: Pero hay algo que se nos escapa. tipos_escritos y tipos documentos tienen dos funciones distintas. tipos_escritos encaja el escrito en el contexto (SFT) pero no tiene el tipo de expediente que también es contexto. Y tiene una FK a tipo de documento. Tipo de documento es la base de la selección del documento a consumir o generar en las tareas. Tiene una doble función pues los documentos no son todos internos, también clasifica los externos. El tipo de documento de un escrito generado por la plantilla no puede ser un tipo externo (algo hay que hacer) <<< debemos tener una sesión dedicada a esto solamente. (probablemente sea más para reforzar me comprensión del funcionamiento del sistema que la tuya)
A4: Efectivamente las consultas nombradas las tenemos que hacer persistentes de alguna forma. Para la creación de la consulta en si veo excesivo un CRUD. La consulta no hay otra forma que hacerla desde el propio programador y darle un nombre (migración). Luego si acaso el programador puede usar un CRUD para estas consultas nombradas respecto a su tabla de exposición al supervisor. Lo más interesante es documentar que hace esa consulta cruzada para poder usarla correctamente y en que contexto ESFTT aplica. Si el CRUD es necesario.
A5: Para entender el versionado de plantillas reviso el flujo: No existe una cierta plantilla. El supervisor abre un documento en blanco o copia otro documento existente con ciertas partes ya creadas (formato) y empieza a escribir la parte que no es ni fragmento ni campo. Deja migas de pan en los huecos donde quiere poner los campos (sabe lo que quiere). Termina y tiene una plantilla con texto, campos, tablas, campos calculados, y fragmentos nombrados, pero en formato personal (subrayado en amarillo por ejemplo). Esa plantilla no vale para nada, no toma datos reales. Habla con el programador y le dice las necesidades que tiene, especialmente en los consultas nombradas o campos calculados. Le explica el contexto donde se necesita esa plantilla. El programador comprueba si existen los campos en la capa 1 si hay campos de listados posibles, si hay tablas posibles por consultas nombradas o campos calculados. Incluso le puede advertir de que no hay fragmento registrado para eso. El programador crea lo necesario y comprueba que los tokens están accesibles al supervisor para crear la plantilla. El supervisor crea (registra la plantilla nueva con los tokens ya dentro y funciona. Bien. El sistema tras parsear la plantilla y los datos del interfaz, detecta que campos usa, que consultas nombradas y que campos calculados ha usado, el contexto ESFT, así como que fragmentos ha usao (sus url) y rellena lo necesario en el registro de la tabla tipos_escritos al registrar. (te das cuenta de que la estructura de tipos_escritos no está funcionando?? Tiene lo que tiene que tener o es excesivo? Que debe definir realmente????)
En un momento dado el supervisor se da cuenta de que la redacción no es correcta, que comitió errores y los tiene que corregir. El supervisor, bajo su responsabilidad modifica la plantilla (no debería cambiar su contexto, solo el interior por ejemplo si quiere o no un fragmento o un campo concreto, o cambiarlo de sitio o cambiar simplemente el texto propio de la plantilla). El control de versiones es responsabilidad del supervisor. Es necesario que el sistema tenga control de las versiones? EL sistema, entiendo, tiene una plantilla que tiene que funcionar para sustituir con datos el interior de la misma. Nada más. El usuario quiere que la plantilla funcione, no le importa si hubo una versión anterior. Si esa necesidad existe y se quiere registrar en la base de datos el histórico de las plantillas, sería un módulo aparte que incluiría los fragmentos igualmente. Puede diferirse. (no heches en barbecho estos comentarios intermedios de este punto.
A6: Feedback sobre campos vacíos en los expedientes existentes. No lo veo necesario. Qué aporta? Supongamos que la plantilla es para expedientes intermunicipales exclusivamente. Es importante que el supervisor vea que no hay expedientes intermunicipales o no? Yo creo que esto no es una necesidad.

B1: si, claro. Necesario.
B2: Imprescindible. Si no hay plantillas pues no puedo continuar la tarea. Botón generar deshabilitado.
B3: Si necesario.
B4: Generar escrito sustituye los campos por valores y le da la opción al usuario de guardar el escrito en un sitio en el servidor de archivos con un nombre propuesto (de la propia plantilla con alguna especificidad (por ejemplo el número de expediente y la solicitud<<< de esto debemos hablar también es un apartado muy interesante y util, SISTEMATIZAR los NOMNBRES DE ARCHIVOS). Ese ofrecimiento es a través del sistema general, donde el usuario puede guardar la ruta FUERA del la RUTA BASE? NO DEBERÍA. Creo que es mejor que la ruta deba existir y sea navegable por un sistema parecido al de incorporar documentos del pool. Si dejamos que el usuario navegue por ahí fuera del propio expediente luego hay problemas. Registrar ESE documento guardado en el pool? Si, pero opcionalmente. Mediante marcado de checkbox junto al botón generar. Adviertiendo que si no se marca lo debe registrar a mano. Asignar como documento producido. Igualmente. El registro en pool es antes de colocar su id en el campo documento producido. Por qué dejar la opción de diferir? Porque el usuario podría querer hacer una segunda iteración al darse cuenta de que el documento tiene datos erróneos (el valor de un campo) y por tanto en lugar de tocarlo a mano, debería corregir el dato y regenerar el documento.
B5: Tras generar el documento el sistema (registrado en el pool o no y asociado al campo documento de salida o no) ofrece abrir el documento generado (conoce la ruta que eligió el usuario). Yo lo haría de la siguiente forma: igual que hay un checkbox para registrar en pool y otro para asignar a documento prodicido, habría un checkbox para abrir carpeta contenedora tras generar. Esto facilita la revisión. Similar al pool.
B6: Que pasa si el documento producido está ya registrado y quiere volverlo a generar? Como se comporta el sistema? Registra dos veces en el pool? Sustituye el id? o simplemente reemplaza el archivo en disco. Yo creo que el comportamiento depende de si se registró o no y como emplea el sistema de selección del emplazamiento y nombre del archivo a crear (regenerar) si todo coincide solo advierte al usuario que está sobrescribiendo un archivo existente y si acepta el archivo se modifica con todas las consecuencias: Si está en el pool, el documento tiene la url y lo que ha pasado es que se ha sustituido el binario, pero el id y el documento producido id siguen sin cambiar. Cualquier otro comportamiento es complejo e innecesario. El usuario sabe lo que está haciendo. Otra historia es que borre el archivo del sistema y no lo arregle en el pool. Pero eso se llama detección de huérfanos del pool. Que es otro área a tratar.
B7: La edición postgeneración pues igual que en B6, es transparente a BBDAT y responsabilidad del usuario. Si le cambia el nombre, lo deja huérfano, si solo lo edita, entonces el sistema no nota nada. No hay que resubir.
B8: Generar el escrito es iniciar la tarea? El inicio de la tarea crear escrito es simplemente de auditoría interna, no tiene valor administrativo. Decisión: Si no está iniciada, se inicia en ese momento. Al fin y al cabo es un indicador de que el usuario hay interactuado con la tarea. Cuando la termine (fecha fin) es cuando está satisfecho con el escrito y si que sería un dato (para el motor de reglas) que debería ser presupuesto para la tarea firmar (siguiente natural).
B9: No existe posibilidad de redactar desde un trámite. Otra cosa es que se permita redactar en cualquier trámite. Eso es otra historia. Creo que la frase "acción disponible desde el nivel de Tarea o Trámite según el tipo" no está bien construida. No existe esa necesidad. Deprecar en el issue
Con estos comentarios, creo que procede por tu parte actualizar el análisis de necesidades y reescribir.
Hemos dejado cabos sueltos a discutir.
Se me agota el tiempo delante del ordenador. Podemos crear un documento md que englobe esta conversación y podamos retormarlo en otro momento? Tras las reflexiones y reescritura tuya. Mete estos comentarios míos literalmente para no perder nada si los resumes. Luego si quieres los matizas en el propio md.

Nota: el issue #189 requiere alguna actualización. los requerimientos no son exactamente pyton-docx-template. Ver commit 6b85fcf4d404730758c90314f393c6bbcef6af52
