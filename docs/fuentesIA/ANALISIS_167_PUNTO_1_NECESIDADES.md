> **Indice:** [ANALISIS_167_INDICE.md](ANALISIS_167_INDICE.md)

## 1) Mapa de necesidades (revisado)

### A. Supervisor — momento de crear/gestionar la plantilla

#### A0. Filtrado dinamico de tokens y contexto ESFTT en cascada — CRITICO, NO DIFERIBLE

**Necesidad:** Cuando el supervisor crea una plantilla nueva, selecciona el contexto ESFTT
(tipo expediente, tipo solicitud, fase, tramite). Actualmente:
- Los selectores NO filtran en cascada (solicitudes por tipo de expediente, fases por solicitud, tramites por fase)
- El panel de tokens NO se actualiza en funcion del contexto seleccionado
- Los tokens mostrados son siempre los mismos (Capa 1 estatica)

**Implicacion:** El supervisor no sabe que tokens son relevantes para su contexto.
No conoce las tablas ni sus campos. Necesita que la interfaz le muestre solo lo aplicable.

**Relacion con motor de reglas:** El filtrado ESFTT usa la misma logica que el motor
de reglas para determinar que aplica a que contexto. El diseno de este mecanismo
no puede diferirse a cuando se implemente el motor completo — hay que establecerlo ahora.

**Decisiones sesiones 2+3 (RESUELTO — ver Cabo 4 cerrado):**
- 3 tablas whitelist: `expedientes_solicitudes` (E→S), `solicitudes_fases` (S→F), `fases_tramites` (F→T)
- Tipos de solicitud combinados como entidades propias en `tipos_solicitudes`
- Tokens Capa 1 son siempre los mismos (12 campos base del expediente)
- La dinamicidad de tokens llega con Capa 2 / Context Builders
- AJAX preparado para refresco futuro del panel

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

Tras detectarlos, registrar en `plantillas` (ex `tipos_escritos`) lo que corresponda.

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

**Resuelto en sesion 2:** Decisions 2 y 4 de Cabo 1+2 (anadir `tipo_expediente_id`,
anadir `origen` a `tipos_documentos`).

**Pregunta de diseno sobre tipos_escritos (resuelta sesion 2):**

> "te das cuenta de que la estructura de tipos_escritos no esta funcionando??
> Tiene lo que tiene que tener o es excesivo? Que debe definir realmente????"

**Resuelto:** Decisiones 1-6 de Cabo 1+2 (renombrar, limpiar, completar).

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
2. El sistema ofrece guardar con nombre propuesto (ver Cabo 3: convencion de nomenclatura)
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
> Sistematizacion de nombres: resuelta en Cabo 3.

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

#### C3. Trazabilidad y codigo de clasificacion embebido — DECIDIDO (vincula #182 y #181)

**Contexto:** El `Documento` registrado en pool no lleva referencia a que plantilla lo genero.
Los issues #182 (codigos embebidos en PDFs internos) y #181 (inspeccion automatica de documentos)
se conectan directamente con #167: **el momento de generacion es el unico donde el sistema
tiene contexto ESFTT completo.**

**Ciclo de vida del documento generado:**

```
GENERAR (#167)          →  .docx con codigo embebido (#182)
   ↓
Usuario edita en Writer →  el codigo sobrevive
   ↓
Portafirmas             →  PDF firmado, codigo intacto
   ↓
INCORPORAR al pool      →  inspeccion automatica (#181) lee el codigo
   ↓
Clasificacion sin intervencion manual
```

**Decision: doble via de trazabilidad**

1. **Codigo embebido en el .docx generado (#182):** `generar_escrito()` inyecta automaticamente
   metadatos de clasificacion en el documento. El supervisor no interviene — el sistema lo hace.
   - **Via principal:** Custom properties del .docx (invisible, lectura programatica directa)
   - **Via fallback:** QR en pie de pagina (resistente a impresion, escaneo, conversion PDF)
   - El supervisor puede ubicar el QR con un token especial `{{qr_clasificacion}}`
     en la plantilla; si no lo pone, el sistema lo anade al final automaticamente

2. **Codigo estructurado:** `BDDAT|AT-12345|AAP_AAC|RESOLUCION|ELABORACION|RES_FAVORABLE|2026-03-15`
   (sistema, expediente, tipo solicitud, fase, tramite, plantilla, fecha generacion)

3. **Al reincorporar el PDF firmado (#181):** la inspeccion automatica lee el codigo embebido
   y preclasifica el documento (expediente, tipo, contexto) sin intervencion manual.
   Los documentos con codigo se clasifican con certeza; los sin codigo pasan por heuristicas.

**Sobre FK en BD:** No es estrictamente necesaria si el documento lleva el codigo dentro.
Pero tener ambas vias (FK `plantilla_id` en `documentos` + codigo embebido) da
verificacion cruzada. Pendiente de decidir si la FK justifica la migracion.

---

#### C4. Metadatos del documento generado — DECIDIDO

Al registrar el `Documento` en pool tras generar:

- **`fecha_administrativa`** = NULL — el .docx es un borrador sin valor juridico hasta la firma
- **`prioridad`** = 0 — la prioridad solo tiene sentido para documentos externos
  (urgencias, problemas potenciales). Los internos son 0 salvo que el usuario lo cambie
- **`asunto`** = descripcion de la plantilla + contexto ESFTT con datos reales del expediente.
  Si la instancia de plantilla esta bien rellena, su campo `descripcion` equivale al asunto.
  Se concatenan las cadenas legibles del contexto (expediente, solicitud, fase, tramite)
  con los mismos datos reales que se inyectan en el propio documento

---

#### ~~C5. Motor de reglas pre-generacion~~ — ELIMINADO

No aplica. Si el motor de reglas funciona, la tarea REDACTAR no puede existir
si no se cumplen los presupuestos. La validacion pre-generacion seria redundante
con la validacion de creacion de tareas.

---

#### ~~C6. Permisos y roles~~ — ELIMINADO

No procede. El control de acceso a las tareas lo gestiona el motor de reglas
(roles que pueden tramitar, mover tramites, etc.). La accion de generar un escrito
no requiere restriccion adicional: lo que tiene validez administrativa es la firma,
que es externa a BDDAT. Si alguien genera un escrito y al tramitador real no le gusta,
lo regenera o lo edita.

---

#### C7. Gestion de errores de generacion — NECESARIO

Si la plantilla tiene error Jinja2, o un campo no existe, o una consulta falla:
toast de error con detalle suficiente para que el tramitador informe al supervisor.

---

#### C8. Ruta de almacenamiento y sistematizacion de nombres — DECIDIDO (ver Cabo 3)

Vinculado con B4. El .docx generado se guarda en `FILESYSTEM_BASE` dentro del arbol
del expediente, con nombre sistematizado segun convencion definida en Cabo 3.

---
