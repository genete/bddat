# Analisis #167 — Generacion de escritos administrativos

> **Estado:** Puntos 1-4 completados. Pendiente punto 5 (analisis tecnico pre-implementacion).
> **Issues relacionados:** #167 (abierto), #189 (cerrado), #181 y #182 (vinculados via C3)
> **Fecha inicio analisis:** 2026-03-15
> **Sesiones:** 3 (todas 2026-03-15)

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

## Decisiones sesion 2 (2026-03-15)

### Cabo 1+2: CERRADO — Estructura de `tipos_escritos` y `tipos_documentos`

Se cierran conjuntamente los cabos 1 y 2 con 6 decisiones firmes:

| # | Decision | Motivo |
|---|----------|--------|
| 1 | **Renombrar `tipos_escritos` a `plantillas`** | El nombre actual induce a confusion; es un registro de plantillas concretas, no un catalogo de tipos |
| 2 | **Anadir `tipo_expediente_id` FK nullable a `plantillas`** | Completa la E que falta en ESFTT. NULL = cualquier tipo de expediente |
| 3 | **Eliminar `campos_catalogo` de `plantillas`** | Debe ser calculo dinamico segun contexto, no dato estatico. Evita inconsistencias |
| 4 | **Anadir `origen` (INTERNO/EXTERNO/AMBOS) a `tipos_documentos`** | Impide que una plantilla apunte a un tipo de documento externo. Distinto del `origen` eliminado en #191 (aquel era en la instancia `documentos`, este es en el catalogo `tipos_documentos`) |
| 5 | **Mantener `contexto_clase`** | Necesario para Capa 2 (Context Builders) |
| 6 | **Mantener `filtros_adicionales` JSONB** | Absorbe futuro sin migracion |

> **Nota sobre decision 4:** Lo que se propone es distinto de lo eliminado en #191.
> Anadir `origen` a `tipos_documentos` (el catalogo de tipos), no a `documentos`
> (la instancia). A nivel de tipo no hay ambiguedad: una RESOLUCION es siempre
> interna, una DR_NO_DUP es siempre externa. No entra en conflicto con la decision del #191.

---

### Cabo 4: CERRADO — Filtrado dinamico de tokens por contexto ESFTT

#### Decision 1: Tablas whitelist ESFTT — cadena completa E→S→F→T

Tres tablas whitelist editables cubren la cascada completa:

- **`expedientes_solicitudes`** (PK compuesta: `tipo_expediente_id` + `tipo_solicitud_id`) — que solicitudes son validas para cada tipo de expediente
- **`solicitudes_fases`** (PK compuesta: `tipo_solicitud_id` + `tipo_fase_id`) — que fases aplican a cada tipo de solicitud
- **`fases_tramites`** (PK compuesta: `tipo_fase_id` + `tipo_tramite_id`) — que tramites son validos dentro de cada fase

Caracteristicas acordadas:
- Seed inicial desde `Estructura_fases_tramites_tareas.json`
- CRUD editable por supervisor (legislacion cambiante)
- La cascada de selectores consume estas tablas como whitelist
- Solo definen **posibilidad** ("esta combinacion tiene sentido"), no obligatoriedad ni orden
- Capa 1 tokens (12 campos base) siempre los mismos — la dinamicidad llega con Capa 2
- Infraestructura AJAX preparada para refresco futuro del panel de tokens

#### Decision 2: Tipos de solicitud combinados como entidades propias

**Problema:** La tabla M:N `solicitudes_tipos` expresa combinaciones de tipos atomicos
(AAP+AAC, AAP+AAC+DUP...) pero esta flexibilidad es innecesaria — las combinaciones
legales son finitas y cerradas. La M:N complica el filtrado en cascada y hace imposible
un FK simple desde plantillas.

**Decision:** Extender `tipos_solicitudes` con tipos combinados como entradas propias.
La tabla contendra tanto tipos atomicos (AAP, AAC, DUP...) como combinaciones legales.

Tipos combinados a anadir:

| Siglas | Descripcion |
|---|---|
| AAP_AAC | Autorizacion Administrativa Previa y de Construccion |
| AAP_AAC_DUP | AAP + AAC + Declaracion de Utilidad Publica |
| AAP_AAC_AAU | AAP + AAC + Autorizacion Ambiental Unificada |
| AAP_AAC_AAU_DUP | AAP + AAC + AAU + Declaracion de Utilidad Publica |
| AAC_DUP | AAC + Declaracion de Utilidad Publica |
| AAE_DEFINITIVA_AAT | Explotacion Definitiva + Transmision de Titularidad |

**Justificacion:**
- Las combinaciones legales son ~6. No van a crecer arbitrariamente (requiere cambio legislativo)
- Cada combinacion tiene implicaciones procedimentales distintas (fases, texto de resoluciones)
- Las plantillas necesitan un FK directo para saber que texto administrativo usar
- El filtrado en cascada se resuelve con JOINs directos contra las whitelist, sin tabla puente
- Si aparece una nueva combinacion legal, es un INSERT + actualizacion de whitelist

**Impacto en tablas existentes:**

| Tabla | Cambio |
|---|---|
| `tipos_solicitudes` | Anadir ~6 tipos combinados |
| `solicitudes` | Anadir FK `tipo_solicitud_id` directa al tipo (atomico o combinado) |
| `solicitudes_tipos` | Mantener como historico, dejar de usar para logica de negocio |
| Wizard creacion solicitudes | Selector directo en vez de multiselect de checkboxes |
| Plantillas (ex `tipos_escritos`) | FK simple a `tipo_solicitud_id` |

> **Comentario del usuario:** "Las plantillas estan intimamente relacionadas con la
> cadena ESFTT (con S=las solicitudes presentadas). Si solicito AAP, la plantilla no
> puede decir en su texto '...de acuerdo con la solicitud de Autorizacion Administrativa
> de Construccion de fecha...' Todo influye. El lenguaje administrativo requiere de
> mucha precision, especialmente las resoluciones."

> **Comentario del usuario:** "El sistema de eleccion de las solicitudes compatibles
> deberia ser simplemente un listado de tipos de solicitud donde esten ya combinadas
> las compatibles. Aunque el listado de tipos de solicitud sea mas largo, no es
> harcodear, es poner en la tabla lo que es posible y ahora mismo las posibilidades
> de combinaciones de solicitudes son unas pocas, no infinitas."

> **Comentario del usuario:** "El documento `Estructura_fases_tramites_tareas.json`
> no es absolutamente completo. Es esencialmente correcto pero no exhaustivo.
> Mi idea es que el supervisor pueda completar estas jerarquias en el futuro,
> modificarlas o crear nuevas, pues la legislacion es muy cambiante."

---

### Principio de escape — Principio transversal de diseno

> **Comentario del usuario:** "Despues de anos tramitando expedientes, me encuentro la
> necesidad de realizar ciertos tramites que no estan exactamente recogidos en el flujo
> normal. Una alegacion fuera de contexto, cambio de rumbo del expediente en medio de la
> tramitacion de la IP, etc. En el motor de reglas, en el listado en cascada, etc., en
> definitiva en todos los lugares donde se impide realizar ciertas cosas, se debe dejar
> una via de escape para poder por ejemplo crear una FTT de un tipo donde no toca, de
> forma que no haya callejon sin salida. Por supuesto estas acciones de escape se
> documentan en la bitacora que esta prevista para estos casos."

Cristaliza como principio de diseno transversal a todo el sistema:
- **Toda cascada, filtro y regla debe tener via de escape**
- El usuario puede elegir opciones "fuera de contexto" con advertencia visual
- Toda accion de escape se registra en bitacora
- **Nunca crear callejones sin salida**

Aplica a: selectores en cascada ESFTT, motor de reglas, filtrado de plantillas,
y cualquier mecanismo futuro que restrinja opciones.

---

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

## Cabos sueltos — sesiones dedicadas pendientes

### Cabo 1+2: ~~Estructura de `tipos_escritos` y `tipos_documentos`~~ — CERRADO

Resuelto en sesion 2 con 6 decisiones firmes (ver seccion "Decisiones sesion 2").

### Cabo 3: ~~Sistematizacion de nombres de archivos~~ — CERRADO

Afecta a B4 y C8. Resuelto en sesion 3.

#### Convencion de nomenclatura

Separador: espacio. El nombre se compone concatenando los `nombre_en_plantilla`
de cada nivel ESFTT separados por espacios. BDDAT siempre compone el nombre,
nunca lo parsea — el nombre es solo para legibilidad humana, no para logica interna.

**Requisito previo:** Anadir campo `nombre_en_plantilla` en cada tabla tipo_
(`tipos_tareas`, `tipos_tramites`, `tipos_fases`, `tipos_solicitudes`, `tipos_expedientes`).
Texto corto legible que aparecera en los nombres de fichero.
Puede contener espacios (ej: "Requerimiento subsanacion").

**Nombre de plantilla** (sistema lo construye, supervisor lo acepta o ajusta):

```
{tarea} {tramite} {fase} {solicitud} {expediente} [V {variante}].docx
```

Reglas para NULLs (comodines):
- NULL al final de la cadena → se omite
- NULL en medio de dos valores reales → se sustituye por `ANY`

El campo **variante** es texto libre que el supervisor introduce en el formulario
para distinguir plantillas del mismo contexto ESFTT (ej: "Favorable", "Denegatoria",
"Condicionada"). Resuelve el problema de las multiples plantillas sin inflar
el interfaz con campos para cada posibilidad.

**Nombre de documento generado** (sistema lo construye con datos reales del expediente):

Los niveles que eran NULL/ANY en la plantilla se rellenan con los valores reales
del expediente concreto.

**Almacenamiento de plantillas:** Directorio plano en `PLANTILLAS_BASE/`.
El contexto ESFTT vive en la BD (tabla `plantillas`), no en el filesystem.
La convencion de nombres evita colisiones sin necesidad de subdirectorios.

**Ejemplos:**

| Plantilla | Documento generado |
|---|---|
| `Redactar Elaboracion Resolucion V Favorable.docx` | `Redactar Elaboracion Resolucion AAP+AAC AT-13465-24 V Favorable.docx` |
| `Redactar Requerimiento subsanacion.docx` | `Redactar Requerimiento subsanacion AAP+AAC AT-13465-24.docx` |
| `Notificar Traslado condicionados Consultas ANY Transporte.docx` | `Notificar Traslado condicionados Consultas AAP+AAC+DUP AT-13465-24.docx` |
| `Redactar Elaboracion Resolucion ANY Transporte V Denegatoria.docx` | `Redactar Elaboracion Resolucion AAP+AAC AT-13465-24 V Denegatoria.docx` |

**TODO implementacion:** Secuencial automatico (`_2`, `_3`) cuando ya existe un documento
con el mismo nombre para el mismo expediente (ej: segundo requerimiento de subsanacion).
Pendiente de definir mecanismo exacto.

### Cabo 4: ~~Filtrado dinamico de tokens por contexto ESFTT~~ — CERRADO

Resuelto en sesion 3 (ver seccion "Decisiones sesion 2", actualizada).
- Cadena completa E→S→F→T con 3 tablas whitelist
- Tipos de solicitud combinados como entidades propias en `tipos_solicitudes`
- Principio de escape como principio transversal

### Cabo 5: ~~Nota sobre dependencias del #189~~ — CERRADO

El issue #189 (cerrado) dice `python-docx-template` como dependencia, pero el paquete
real es `docxtpl`. El commit 6b85fcf anadio correctamente las tres dependencias:
`docxtpl==0.20.2`, `python-docx==1.2.0`, `lxml==6.0.2`. El codigo es correcto;
solo el texto del issue tiene la discrepancia. No requiere accion.

### Cabo 6: Actualizar documentacion tras ejecutar migraciones — PENDIENTE (no bloqueante)

Al ejecutar las migraciones derivadas de este analisis, actualizar los .md que
referencian nombres antiguos. **No antes** — el codigo aun usa los nombres actuales.

| Fichero | Conceptos a actualizar |
|---|---|
| `docs/fuentesIA/GUIA_CONTEXT_BUILDERS.md` | `campos_catalogo`, `tipos_escritos`, ejemplo de migracion INSERT |
| `docs/fuentesIA/ARQUITECTURA_DOCUMENTOS.md` | `campos_catalogo`, `tipos_escritos` |
| `docs/fuentesIA/ROADMAP.md` | `tipos_escritos` |
| Issue #189 (cuerpo) | Estructura `tipos_escritos` obsoleta (renombrar a `plantillas`, eliminar `campos_catalogo`, anadir `tipo_expediente_id`, campo `variante`) |

---

## 2) Dependencias con otros modulos

Analisis sistematico de que componentes existentes se ven afectados por cada
decision del punto 1. Para cada componente se indica el origen (decision/necesidad)
que motiva el cambio y la naturaleza de la modificacion.

### 2.1 Matriz de impacto: Decision → Ficheros afectados

La siguiente tabla resume que decisiones del punto 1 impactan en cada fichero.
Las columnas usan codigos cortos: **R** = renombrar/restructurar, **A** = anadir campo/funcion,
**M** = modificar logica existente, **E** = eliminar campo/codigo, **N** = fichero nuevo.

| Fichero | C1D1 rename | C1D2 tipo_exp | C1D3 -campos | C1D4 origen | C3 nombres | C4 whitelist | C4 combinados | B1-B8 generacion | C1-C8 transversales |
|---------|:-----------:|:-------------:|:------------:|:-----------:|:----------:|:------------:|:-------------:|:----------------:|:------------------:|
| `models/tipos_escritos.py` | R | A | E | | A | | A | | |
| `models/tipos_documentos.py` | | | | A | | | | | |
| `models/tipos_expedientes.py` | | | | | A | | | | |
| `models/tipos_solicitudes.py` | | | | | A | | M | | |
| `models/tipos_fases.py` | | | | | A | | | | |
| `models/tipos_tramites.py` | | | | | A | | | | |
| `models/tipos_tareas.py` | | | | | A | | | | |
| `models/solicitudes.py` | | | | | | | A | | |
| `models/documentos.py` | | | | | | | | | M |
| `models/tareas.py` | | | | | | | | M | |
| `models/__init__.py` | R | | | | | N | | | |
| `models/` (NUEVOS) | | | | | | N×3 | | | |
| `modules/admin_plantillas/routes.py` | R | M | E | M | M | M | M | | |
| `modules/admin_plantillas/templates/` | R | M | E | | M | M | | | |
| `services/generador_escritos.py` | R | | | | M | | | M | M |
| `services/escritos.py` | | | | | | | | | |
| `services/motor_reglas.py` | | | | | | | M | | |
| `routes/vista3.py` | | | | | | | M | M | |
| `routes/wizard_expediente.py` | | | | | | | M | | |
| ~~`templates/vistas/vista3/`~~ | | | | | | | | | DEPRECADA |
| `config.py` | | | | | | | | | |

> **Clave:** C1D1 = Cabo1 Decision1, C3 = Cabo3, C4 = Cabo4, B1-B8 = necesidades tramitador, C1-C8 = transversales.

---

### 2.2 Base de datos — Migraciones necesarias

Todas las migraciones deben ser manuales (`flask db revision`). Nunca `flask db migrate`.

#### 2.2.1 ALTER TABLE sobre tablas existentes

| Tabla | Cambio | Origen | Detalle |
|-------|--------|--------|---------|
| `tipos_escritos` | RENAME TABLE → `plantillas` | C1D1 | Renombrar tabla, constraints, indices, FKs entrantes |
| `plantillas` (ex tipos_escritos) | ADD `tipo_expediente_id` FK nullable → `tipos_expedientes.id` | C1D2 | NULL = cualquier tipo expediente |
| `plantillas` (ex tipos_escritos) | DROP `campos_catalogo` | C1D3 | El catalogo de campos sera calculo dinamico |
| `plantillas` (ex tipos_escritos) | ADD `variante` TEXT nullable | C3 | Texto libre para distinguir plantillas del mismo contexto ESFTT |
| `tipos_documentos` | ADD `origen` VARCHAR(10) NOT NULL DEFAULT 'AMBOS' | C1D4 | CHECK (`origen` IN ('INTERNO','EXTERNO','AMBOS')). Seed: actualizar registros existentes |
| `tipos_solicitudes` | ADD ~6 filas combinadas | C4 | INSERT tipos combinados (AAP_AAC, AAP_AAC_DUP, etc.) |
| `solicitudes` | ADD `tipo_solicitud_id` FK NOT NULL → `tipos_solicitudes.id` | C4 | FK directa al tipo (atomico o combinado). NOT NULL — sin datos reales que migrar |
| `tipos_expedientes` | ADD `nombre_en_plantilla` TEXT nullable | C3 | Texto corto para nomenclatura de ficheros |
| `tipos_solicitudes` | ADD `nombre_en_plantilla` TEXT nullable | C3 | Idem |
| `tipos_fases` | ADD `nombre_en_plantilla` TEXT nullable | C3 | Idem |
| `tipos_tramites` | ADD `nombre_en_plantilla` TEXT nullable | C3 | Idem |
| `tipos_tareas` | ADD `nombre_en_plantilla` TEXT nullable | C3 | Idem |
| `solicitudes_tipos` | DROP TABLE | C4 | Reemplazada por `Solicitud.tipo_solicitud_id` directo. Sin datos reales que preservar |

#### 2.2.2 Tablas nuevas

| Tabla | Origen | Columnas | PK |
|-------|--------|----------|-----|
| `expedientes_solicitudes` | C4 | `tipo_expediente_id` FK, `tipo_solicitud_id` FK | PK compuesta (ambas FK) |
| `solicitudes_fases` | C4 | `tipo_solicitud_id` FK, `tipo_fase_id` FK | PK compuesta (ambas FK) |
| `fases_tramites` | C4 | `tipo_fase_id` FK, `tipo_tramite_id` FK | PK compuesta (ambas FK) |

Las tres tablas son whitelists editables por supervisor. Seed inicial desde
`Estructura_fases_tramites_tareas.json`.

#### 2.2.3 Datos maestros (seed)

| Tabla | Accion | Origen |
|-------|--------|--------|
| `tipos_solicitudes` | INSERT 6 tipos combinados | C4 |
| `tipos_documentos` | UPDATE `origen` por cada tipo existente | C1D4 |
| `expedientes_solicitudes` | INSERT seed desde JSON de estructura | C4 |
| `solicitudes_fases` | INSERT seed desde JSON de estructura | C4 |
| `fases_tramites` | INSERT seed desde JSON de estructura | C4 |
| 5 tablas tipos_ | UPDATE `nombre_en_plantilla` para cada tipo existente | C3 |

---

### 2.3 Modelos Python — Cambios por fichero

#### `app/models/tipos_escritos.py` → renombrar a `app/models/plantillas.py`

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Renombrar clase `TipoEscrito` → `Plantilla` | C1D1 | `__tablename__ = 'plantillas'` |
| Renombrar fichero → `plantillas.py` | C1D1 | Coherencia nombre-clase |
| Anadir `tipo_expediente_id` + relationship | C1D2 | FK nullable a `TipoExpediente` |
| Eliminar `campos_catalogo` | C1D3 | Columna y comment |
| Anadir `variante` | C3 | `db.Column(db.Text, nullable=True)` |
| Actualizar constraints (uq, fk names) | C1D1 | Prefijo `plantillas_` en vez de `tipos_escritos_` |

#### `app/models/tipos_documentos.py`

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Anadir `origen` | C1D4 | `db.Column(db.String(10), nullable=False, default='AMBOS')` con CHECK |

#### `app/models/tipos_solicitudes.py`

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Anadir `nombre_en_plantilla` | C3 | `db.Column(db.Text, nullable=True)` |
| Considerar campo `es_combinado` (bool) | C4 | Opcional: distinguir tipos atomicos de combinados para UI |

#### `app/models/tipos_expedientes.py`, `tipos_fases.py`, `tipos_tramites.py`, `tipos_tareas.py`

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Anadir `nombre_en_plantilla` | C3 | `db.Column(db.Text, nullable=True)` en cada uno |

#### `app/models/solicitudes.py`

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Anadir `tipo_solicitud_id` FK NOT NULL | C4 | FK directa a `tipos_solicitudes.id`. Reemplaza la tabla puente `solicitudes_tipos` |
| Anadir relationship `tipo_solicitud` | C4 | `db.relationship('TipoSolicitud')` |

#### `app/models/__init__.py`

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Renombrar import `TipoEscrito` → `Plantilla` | C1D1 | Cambiar `from app.models.tipos_escritos` → `from app.models.plantillas` |
| Anadir imports de 3 modelos whitelist | C4 | `ExpedienteSolicitud`, `SolicitudFase`, `FaseTramite` |
| Actualizar `__all__` | C1D1, C4 | Reemplazar `TipoEscrito` por `Plantilla`, anadir 3 nuevos |
| Respetar orden de capas | todos | Las 3 whitelist son maestras (sin FKs operacionales) — van al inicio |

#### Nuevos ficheros de modelo (3)

| Fichero | Clase | Origen |
|---------|-------|--------|
| `app/models/expedientes_solicitudes.py` | `ExpedienteSolicitud` | C4 |
| `app/models/solicitudes_fases.py` | `SolicitudFase` | C4 |
| `app/models/fases_tramites.py` | `FaseTramite` | C4 |

Cada uno con PK compuesta y sin columnas adicionales salvo las dos FK.

---

### 2.4 Servicios — Cambios por fichero

#### `app/services/generador_escritos.py`

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Renombrar parametro `tipo_escrito` → `plantilla` | C1D1 | En `generar_escrito()` y helpers |
| Implementar `_ejecutar_consultas()` | C1 | Stub actual devuelve `{}`. Debe: parsear plantilla → detectar `{%tr for row in X %}` → ejecutar `ConsultaNombrada.query.filter_by(nombre=X)` → pasar resultado a contexto |
| Validacion de sintaxis pre-registro | A1 | Nueva funcion `validar_plantilla(ruta)` → intenta `DocxTemplate(ruta)` + parsear tokens |
| Inyeccion de metadatos (custom properties + QR) | C3 | Llamar a `python-docx` para escribir custom properties + generar QR con `qrcode` |
| Composicion de nombre de fichero | C3, B4 | Nueva funcion que construye nombre desde `nombre_en_plantilla` de cada nivel ESFTT |
| Guardado en FILESYSTEM_BASE | B4 | Escribir bytes a ruta dentro del arbol del expediente |
| Registro opcional en pool | B4 | Crear `Documento` con metadatos segun C4 |
| Asignacion opcional como doc producido | B4 | Asignar `tarea.documento_producido_id` |
| Auto-inicio de tarea REDACTAR | B8 | Si `tarea.fecha_inicio is None`: asignar `date.today()` |
| Gestion de errores con detalle | C7 | Try/catch Jinja2, campos inexistentes, consultas fallidas → mensaje legible |

> **Nota:** `app/services/escritos.py` (ContextoBaseExpediente) no requiere cambios
> estructurales. Sus 12 campos base permanecen estables. La unica modificacion posible
> es anadir al contexto los datos del tipo de solicitud combinado cuando este disponible.

#### `app/services/motor_reglas.py`

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Reescribir `_criterio_existe_tipo_solicitud` | C4 | Actualmente usa `SolicitudTipo` (tabla puente N:M). Con la eliminacion de la tabla puente, consultar directamente `Solicitud.tipo_solicitud_id` |
| Stubs de EXISTE_DOCUMENTO_TIPO | B4, C3 | Los stubs actuales (`lambda: False`) deben implementarse cuando el pool reciba documentos generados con tipo correcto |

---

### 2.5 Rutas / Endpoints — Cambios por fichero

#### `app/modules/admin_plantillas/routes.py` — IMPACTO ALTO

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Renombrar imports y referencias `TipoEscrito` → `Plantilla` | C1D1 | Todo el fichero |
| Anadir `TipoExpediente` a `_selects_context()` | C1D2 | Nuevo selector en formulario |
| Filtrar `TipoDocumento` por `origen != 'EXTERNO'` en `_selects_context()` | C1D4 | Solo mostrar tipos internos o ambos |
| Eliminar parsing/validacion de `campos_catalogo` en `_form_data_to_tipo()` | C1D3 | Eliminar textarea JSON del formulario |
| Anadir campo `variante` al formulario | C3 | Texto libre |
| Anadir campo `tipo_expediente_id` al formulario | C1D2 | Selector |
| Implementar selectores en cascada (AJAX) | A0 | Nuevos endpoints: `GET /api/admin/plantillas/solicitudes?tipo_expediente_id=X`, etc. |
| Validacion sintaxis .docx al registrar | A1 | Llamar a `validar_plantilla()` antes de `db.session.add()` |
| Parseo automatico del .docx | A3 | Tras subir, detectar campos/consultas/fragmentos usados |
| Actualizar `_build_tokens()` | C1D3, A0 | Eliminar referencia a `campos_catalogo`. Los tokens de Capa 2 se determinan por `contexto_clase`, no por datos estaticos |

#### `app/routes/vista3.py` — IMPACTO ALTO

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Nuevo endpoint `POST /api/vista3/tarea/<id>/generar` | B1 | Orquesta la generacion: seleccion plantilla → preview → generar → guardar |
| Nuevo endpoint `GET /api/vista3/tarea/<id>/plantillas` | B2 | Devuelve plantillas aplicables al contexto ESFTT de la tarea, con logica NULL-comodin |
| Nuevo endpoint `GET /api/vista3/tarea/<id>/preview-campos` | B3 | Devuelve campos de la plantilla seleccionada con valores del expediente |
| Simplificar `_get_solicitudes_con_stats()` | C4 | Actualmente obtiene tipos via `SolicitudTipo` JOIN. Sustituir por acceso directo a `Solicitud.tipo_solicitud_id` |
| Simplificar `crear_solicitud()` | C4 | Aceptar `tipo_solicitud_id` unico en vez de `tipo_solicitud_id[]` |

#### `app/routes/wizard_expediente.py` — IMPACTO MEDIO

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Paso 3: cambiar selector de solicitudes | C4 | De multiselect checkboxes (tipos atomicos + tabla puente) a selector unico (tipo combinado). Solo rellena `Solicitud.tipo_solicitud_id`; `SolicitudTipo` se elimina |

#### Nuevos endpoints necesarios (API)

| Endpoint | Origen | Descripcion |
|----------|--------|-------------|
| `GET /api/admin/plantillas/tipos-solicitud?tipo_expediente_id=X` | A0, C4 | Tipos de solicitud validos para un tipo de expediente (via whitelist `expedientes_solicitudes`) |
| `GET /api/admin/plantillas/tipos-fase?tipo_solicitud_id=X` | A0, C4 | Fases validas para un tipo de solicitud (via `solicitudes_fases`) |
| `GET /api/admin/plantillas/tipos-tramite?tipo_fase_id=X` | A0, C4 | Tramites validos para una fase (via `fases_tramites`) |
| `POST /api/vista3/tarea/<id>/generar` | B1 | Genera escrito desde tarea REDACTAR |
| `GET /api/vista3/tarea/<id>/plantillas` | B2 | Plantillas aplicables al contexto de la tarea |
| CRUD consultas nombradas (4-5 endpoints) | A4 | CRUD basico de `ConsultaNombrada` para el supervisor |

---

### 2.6 Templates / Vistas — Cambios necesarios

#### `app/modules/admin_plantillas/templates/admin_plantillas/`

| Template | Cambio | Origen |
|----------|--------|--------|
| `form.html` | Anadir selector `tipo_expediente_id` | C1D2 |
| `form.html` | Anadir campo `variante` | C3 |
| `form.html` | Eliminar textarea `campos_catalogo` | C1D3 |
| `form.html` | Implementar selectores en cascada con JS | A0 |
| `form.html` | Filtrar tipos de documento (excluir EXTERNO) | C1D4 |
| `detalle.html` | Mostrar tipo de expediente y variante | C1D2, C3 |
| `listado.html` | Anadir columna tipo expediente / variante | C1D2, C3 |
| `_panel_tokens.html` | Eliminar seccion campos_catalogo | C1D3 |
| Todas | Renombrar variables `tipo`/`tipo_escrito` → `plantilla` | C1D1 |

#### ~~`app/templates/vistas/vista3/`~~ — DEPRECADA

La vista de acordeones (vista3) se va a deprecar. Los cambios de B1-B6 (generacion
desde tarea REDACTAR) y C4 (tipo solicitud directo) se implementaran en la vista
breadcrumb BC (`app/templates/vistas/vista3_bc/`) o su sucesora.

#### `app/templates/expedientes/wizard_paso3.html`

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Cambiar multiselect tipos atomicos → selector tipo combinado | C4 | El selector muestra tipos atomicos Y combinados. `SolicitudTipo` desaparece; solo se usa `Solicitud.tipo_solicitud_id` |

#### Templates nuevos necesarios

| Template | Origen | Descripcion |
|----------|--------|-------------|
| Parcial de generacion en vista tarea (BC) | B1-B6 | UI de seleccion plantilla + preview + checkboxes + resultado |
| CRUD consultas nombradas (listado, form, detalle) | A4 | 3-4 templates |
| CRUD whitelist ESFTT (opcional fase 1) | C4 | Si se implementa admin de whitelists, 3 listados editables |

---

### 2.7 JavaScript afectado

| Componente | Cambio | Origen |
|------------|--------|--------|
| Admin plantillas: formulario | Selectores en cascada AJAX (E→S→F→T) | A0, C4 |
| Admin plantillas: formulario | Refrescar panel tokens segun contexto (preparado, no implementado aun) | A0 |
| Vista tramitacion BC: tarea | Logica boton "Generar escrito" → AJAX al endpoint de generacion | B1 |
| Vista tramitacion BC: tarea | Selector plantilla filtrado + preview campos | B2, B3 |
| Vista tramitacion BC: tarea | Checkboxes pool/doc_producido/abrir_carpeta + submit | B4, B5 |
| Wizard paso 3 | Cambiar de multiselect a selector unico (o selector con buscador) | C4 |

> **Consultar `docs/GUIA_COMPONENTES_INTERACTIVOS.md`** antes de implementar cualquier JS.
> Componentes existentes reutilizables: `SelectorBusqueda` (para selectores con busqueda),
> `ScrollInfinito` (no aplica aqui), `FiltrosListado` (no aplica aqui).

---

### 2.8 Dependencias externas (pip)

| Paquete | Estado | Necesidad | Origen |
|---------|--------|-----------|--------|
| `docxtpl` (python-docx-template) | Instalado | Generacion .docx | Ya presente (#189) |
| `python-docx` | Instalado | Custom properties, inspeccion | Ya presente (#189) |
| `qrcode` | **NUEVO** | QR de clasificacion en pie de pagina | C3 |
| `Pillow` | Probablemente instalado | Dependencia de `qrcode` para generar imagen | C3 |

---

### 2.9 Configuracion

| Fichero | Cambio | Origen |
|---------|--------|--------|
| `app/config.py` | Sin cambios estructurales | — |
| `FILESYSTEM_BASE` (env) | Ya existe. Usado para guardar .docx generados | B4 |
| `PLANTILLAS_BASE` (env) | Ya existe. Directorio de plantillas .docx | — |

> No se necesitan nuevas variables de configuracion.

---

### 2.10 Modulos no afectados

Los siguientes modulos/componentes **no requieren cambios** por las decisiones del punto 1:

| Componente | Motivo de no afectacion |
|------------|-------------------------|
| `app/modules/expedientes/` | Las rutas de expediente no referencian plantillas ni tipos_escritos |
| `app/modules/entidades/` | Sin relacion con generacion de escritos |
| `app/modules/proyectos/` | Sin relacion directa (Proyecto se consume via ContextoBaseExpediente, que no cambia) |
| `app/modules/usuarios/` | Sin relacion |
| `app/routes/auth.py` | Sin relacion |
| `app/routes/dashboard.py` | Sin relacion |
| `app/routes/perfil.py` | Sin relacion |
| `app/routes/api_entidades.py` | Sin relacion |
| `app/routes/api_expedientes.py` | Sin relacion |
| `app/routes/api_municipios.py` | Sin relacion |
| `app/routes/api_proyectos.py` | Sin relacion |
| `app/models/municipios.py` | Sin relacion |
| `app/models/proyectos.py` | Sin relacion |
| `app/models/entidad.py` | Sin relacion |
| `app/models/direccion_notificacion.py` | Sin relacion |
| `app/models/autorizados_titular.py` | Sin relacion |
| `app/models/historico_titular_expediente.py` | Sin relacion |
| `app/models/municipios_proyecto.py` | Sin relacion |
| `app/models/documentos_proyecto.py` | Sin relacion |
| `app/models/motor_reglas.py` (modelo) | El modelo no cambia; la logica que cambia esta en el servicio |
| `app/services/escritos.py` (ContextoBaseExpediente) | Los 12 campos base no cambian. Posible extension menor para incluir tipo solicitud combinado |

---

### 2.11 Resumen cuantitativo

| Categoria | Ficheros existentes modificados | Ficheros nuevos | Tablas ALTER | Tablas nuevas |
|-----------|:-------------------------------:|:---------------:|:------------:|:-------------:|
| Modelos | 9 | 3 | 8 | 3 |
| Servicios | 2 | 0 | — | — |
| Rutas | 3 | ~1 (API cascada) | — | — |
| Templates | ~8 | ~5 | — | — |
| JS | ~3 bloques | — | — | — |
| **Total** | **~25** | **~9** | **8** | **3** |

---

### 2.12 Grafo de dependencias entre cambios

Algunos cambios son prerequisitos de otros. Este grafo define el orden minimo:

```
[C4: Tablas whitelist + seed]
    ↓
[C4: Tipos combinados en tipos_solicitudes]
    ↓
[C4: FK tipo_solicitud_id en solicitudes]       [C1D1: Rename tipos_escritos → plantillas]
    ↓                                                ↓
[C1D2: FK tipo_expediente_id en plantillas]     [C1D3: DROP campos_catalogo]
    ↓                                                ↓
[C3: nombre_en_plantilla en 5 tablas tipos_]    [C1D4: origen en tipos_documentos]
    ↓                                                ↓
[C3: variante en plantillas]                    [Modelo TipoDocumento actualizado]
    ↓                                                ↓
 ─────────────── convergen ──────────────────────────
                    ↓
            [Admin plantillas: selectores cascada + formulario]
                    ↓
            [A1: Validacion sintaxis .docx]
                    ↓
            [A3: Parseo automatico]
                    ↓
            [C1: _ejecutar_consultas()]
                    ↓
            [B1-B6: Flujo generacion en Vista 3]
                    ↓
            [C3: Codigo embebido + QR]
                    ↓
            [B8: Auto-inicio tarea REDACTAR]
```

> **Nota:** Los bloques sin flechas entre ellos pueden ejecutarse en paralelo.
> En particular, el rename C1D1 y las tablas whitelist C4 son independientes entre si.

---

## 3) Riesgos e inconsistencias

Analisis sistematico de riesgos tecnicos, inconsistencias con el codigo actual
y puntos que requieren decision explicita antes de implementar.

### 3.1 Riesgos criticos — Bloquean implementacion si no se resuelven

#### R1. Cambio semantico en motor de reglas: tipos atomicos vs. combinados

**Problema:** La funcion `_criterio_existe_tipo_solicitud()` en `motor_reglas.py` (linea 458)
comprueba si una solicitud tiene un tipo atomico concreto via la tabla puente M:N:

```python
# Actual (motor_reglas.py:462-466)
resultado = (db.session.query(SolicitudTipo)
             .join(TipoSolicitud, SolicitudTipo.tiposolicitudid == TipoSolicitud.id)
             .filter(SolicitudTipo.solicitudid == ctx.solicitud.id,
                     TipoSolicitud.siglas == siglas)
             .first())
```

Una solicitud AAP+AAC tiene DOS filas en `solicitudes_tipos` (una para AAP, otra para AAC).
La regla `EXISTE_TIPO_SOLICITUD:AAP` devuelve `True` para esa solicitud.

**Tras el cambio:** `Solicitud.tipo_solicitud_id` apunta a un tipo combinado `AAP_AAC`.
La comparacion directa `solicitud.tipo_solicitud.siglas == 'AAP'` devolveria `False`.

Actualmente no hay reglas JSON que invoquen este criterio (solo esta registrado en Python),
pero la implementacion DEBE reescribirse porque `SolicitudTipo` desaparece. La reescritura
requiere decidir la semantica de la comparacion con tipos combinados.

**Opciones de diseno:**

| Opcion | Mecanismo | Pros | Contras |
|--------|-----------|------|---------|
| A | `'AAP' in siglas.split('_')` | Simple | Fragil si las siglas usan `_` internamente |
| B | Tabla auxiliar `tipo_solicitud_componentes` | Consulta inversa exacta | Tabla adicional, complejidad |
| C | Usar siglas combinadas en las reglas (`AAP_AAC`) | Semantica limpia | Cada combinacion necesita regla propia |
| D | Campo `componentes` JSON en `tipos_solicitudes` | Flexible | Requiere parsear JSON en cada evaluacion |

> **Recomendacion:** Opcion C. Una solicitud AAP_AAC es un procedimiento distinto de AAP
> — tiene fases y plazos propios. Las reglas deben reflejar esa realidad. Opcion A como
> fallback si hay reglas que deben matchear "cualquier solicitud que incluya AAP".

**Decision necesaria antes de implementar:** Cual es la semantica correcta de
`EXISTE_TIPO_SOLICITUD` con tipos combinados.

---

#### R2. Atomicidad migracion + codigo al eliminar `solicitudes_tipos`

**Problema:** La tabla `solicitudes_tipos` tiene queries activas en 4 ficheros:

| Fichero | Funcion | Lineas | Tipo de uso |
|---------|---------|--------|-------------|
| `services/motor_reglas.py` | `_criterio_existe_tipo_solicitud()` | 462-466 | JOIN + filter |
| `routes/vista3.py` | `_get_solicitudes_con_stats()` | 160-161 | JOIN + filter |
| `routes/vista3.py` | `crear_solicitud()` / eliminar | 491, 519 | INSERT / DELETE |
| `routes/wizard_expediente.py` | `crear_expediente_completo()` | 357-360 | INSERT en bucle |
| `routes/api_expedientes.py` | endpoint tipos por solicitud | 420-421 | JOIN + filter |

Si la migracion elimina la tabla antes de que el codigo deje de usarla, cualquier
acceso a esas rutas lanza `ProgrammingError: relation "solicitudes_tipos" does not exist`.

**Mitigacion:** Una sola migracion que:
1. Crea `Solicitud.tipo_solicitud_id` (nullable inicialmente)
2. Backfill: para cada solicitud, deduce el tipo combinado desde `solicitudes_tipos`
3. Convierte `tipo_solicitud_id` a NOT NULL
4. DROP `solicitudes_tipos`

El deploy de codigo (5 ficheros) y migracion debe ser atomico. En entorno dev
esto es trivial (se ejecuta todo junto), pero debe documentarse para evitar
estados intermedios.

---

#### R3. Backfill de `tipo_solicitud_id` en solicitudes existentes

**Problema:** El modelo `solicitudes.py` tiene un comentario explicito (linea 65):
`"v3.0: ELIMINADO tipo_solicitud_id (movido a SOLICITUDES_TIPOS N:M)"`.
El campo existio, fue eliminado, y ahora se restaura.

Aunque estamos en entorno de desarrollo, SI existen solicitudes de prueba
creadas via wizard. Estas solicitudes tienen sus tipos SOLO en `solicitudes_tipos`.

**Casuistica del backfill:**

| Caso | Ejemplo | Mapeo |
|------|---------|-------|
| Solicitud con 1 tipo atomico | Solo AAP | FK directa a `AAP` |
| Solicitud con N tipos atomicos | AAP + AAC | Buscar tipo combinado `AAP_AAC` |
| Combinacion no prevista | Combinacion sin tipo combinado definido | **Requiere decision** |

**Mitigacion:** Script en la migracion que haga el mapeo automatico:
- Obtener los tipos atomicos de cada solicitud desde `solicitudes_tipos`
- Si es un solo tipo, mapeo directo
- Si son N tipos, buscar tipo combinado que contenga exactamente esos componentes
- Los casos no mapeables se loguean como WARNING para revision manual

---

### 3.2 Riesgos altos — Requieren atencion durante implementacion

#### R4. Amplitud del rename `tipos_escritos` → `plantillas`

**Problema:** El rename afecta simultaneamente multiples capas:

| Capa | Elementos a renombrar |
|------|-----------------------|
| Tabla PostgreSQL | `tipos_escritos` → `plantillas` |
| Constraints FK | `fk_tipos_escritos_*` (x4) |
| Constraint unique | `uq_tipos_escritos_codigo` |
| Clase Python | `TipoEscrito` → `Plantilla` |
| Fichero Python | `tipos_escritos.py` → `plantillas.py` |
| Imports directos | `__init__.py` (linea 25), `admin_plantillas/routes.py` (linea 26) |
| Variables en rutas | `tipo`/`tipo_escrito` → `plantilla` (routes + templates) |
| Strings en mensajes | `generador_escritos.py` (lineas 86, 117) |

**Riesgo:** Olvidar una referencia produce `ImportError`, `AttributeError` o query
contra tabla inexistente. Los errores no se detectan hasta que se ejecuta la ruta concreta.

**Mitigacion:** Busqueda exhaustiva post-rename con grep de `tipo.escrito` y `tipos.escritos`.
No dejar alias de retrocompatibilidad — en entorno dev los errores deben ser ruidosos.

---

#### R5. Principio de escape — declarado pero sin diseno de implementacion

**Problema:** El principio de escape se declaro como transversal ("toda cascada, filtro
y regla debe tener via de escape") pero no se ha definido COMO se implementa en UI.

Los selectores en cascada ESFTT (A0) filtran opciones segun whitelist. Si el supervisor
necesita una combinacion no prevista, el selector no debe ser un callejon sin salida.

**Opciones de implementacion:**

| Opcion | Mecanismo | Implicacion en API |
|--------|-----------|---------------------|
| Toggle "Mostrar todos" | Switch en cada selector que desactiva filtro | Endpoint devuelve `{compatibles, otros}` |
| Entrada "Otros..." | Opcion fija al final que abre selector completo | Segundo endpoint sin filtro |
| Bypass global | Checkbox que desbloquea todos los selectores | Parametro `?sin_filtro=1` |

**Impacto:** Afecta al diseno de los endpoints AJAX de cascada ANTES de implementarlos.
El endpoint `GET /api/.../tipos-solicitud?tipo_expediente_id=X` debe devolver tambien
las opciones fuera de whitelist si hay mecanismo de escape.

**Decision necesaria:** Mecanismo concreto antes de implementar A0.

> **Recomendacion:** Opcion 1 (toggle). El endpoint devuelve dos listas (`compatibles` +
> `otros`). El JS renderiza con estilo diferenciado (badge de advertencia en los `otros`).
> Sencillo, no requiere endpoints adicionales y el escape es explicito.

---

#### R6. Bug preexistente: `__str__` en modelo `Documento` referencia campo eliminado

**Problema:** El campo `nombre_display` fue eliminado de la tabla `documentos` en la
migracion del #191 (`fd2bc02d2474`). El propio modelo lo documenta en linea 87:
`"v4.1: ELIMINADOS origen, nombre_display"`. Pero `__str__` aun lo referencia:

```python
# documentos.py:172-174
def __str__(self):
    """Representación legible para interfaz."""
    return self.nombre_display or f'Documento {self.id}'
```

**Impacto:** `AttributeError` cuando Python convierte un `Documento` a string
(logging, f-strings, mensajes de error). No afecta al rendering de templates porque
la ruta `pool_documentos` calcula `nombre_display` como clave de dict desde la URL
(`expedientes/routes.py:549-559`), no desde el modelo.

**Accion:** Corregir `__str__` antes de iniciar implementacion del #167. La generacion
(B4) registra documentos en pool → si hay logging que use `str(documento)`, crash.
Es un fix independiente, no incluir en la migracion de #167.

---

### 3.3 Riesgos medios — Gestionables con precaucion

#### R7. Eliminacion de `campos_catalogo` → ventana sin tokens de Capa 2

**Problema:** Actualmente `_build_tokens()` en `admin_plantillas/routes.py` (linea 87-89)
fusiona `CAMPOS_BASE` (12 campos fijos de Capa 1) con `tipo_escrito.campos_catalogo`
(campos adicionales definidos por plantilla). Al eliminar `campos_catalogo`, el panel
de tokens mostrara SOLO los 12 campos base hasta que se implemente Capa 2
(Context Builders).

**Impacto:** Si ya hay plantillas registradas con `campos_catalogo` rellenado,
el supervisor pierde visibilidad de esos tokens en la interfaz. Las plantillas
seguiran funcionando si los tokens existen en el contexto, pero no se mostraran
en el panel copiable.

**Mitigacion:** Antes de ejecutar la migracion, exportar los `campos_catalogo`
existentes como referencia para la futura implementacion de Context Builders.
Consulta: `SELECT codigo, nombre, campos_catalogo FROM tipos_escritos WHERE campos_catalogo IS NOT NULL`.

---

#### R8. Seed de whitelist desde JSON incompleto

**Problema:** El usuario confirmo que `Estructura_fases_tramites_tareas.json`
"no es absolutamente completo" y "es esencialmente correcto pero no exhaustivo".

El seed inicial de las 3 tablas whitelist (`expedientes_solicitudes`,
`solicitudes_fases`, `fases_tramites`) estara incompleto por definicion.
Las combinaciones faltantes haran que los selectores en cascada no ofrezcan
ciertas opciones validas.

**Mitigacion:**
- El principio de escape (R5) mitiga esto si se implementa
- El CRUD de whitelist editable por supervisor (previsto en C4) permite completar
- Priorizar que el CRUD de whitelist este disponible desde el primer momento,
  no como fase posterior

---

#### R9. Cadena de downgrade en Alembic

**Problema:** La migracion `20c5d1e9d782` crea la tabla `tipos_escritos`. Si una nueva
migracion renombra la tabla a `plantillas`, el downgrade de `20c5d1e9d782` intentaria
`DROP TABLE tipos_escritos` sobre una tabla que ya no existe con ese nombre.

**Mitigacion:** No tocar migraciones antiguas. La nueva migracion que renombra tiene
su propio downgrade que revierte el rename. La cadena completa de downgrades
(revertir TODO hasta el inicio) puede no funcionar, pero eso es aceptable en
entorno de desarrollo sin despliegues en produccion.

---

#### R10. Supervivencia del codigo embebido en pipeline .docx → PDF

**Problema:** La trazabilidad C3 define dos vias: custom properties (principal)
y QR en pie de pagina (fallback). El pipeline completo es:
`.docx` → edicion en Writer → portafirmas → `.pdf` firmado.

| Via | Edicion Writer | Conversion a PDF | Portafirmas |
|-----|:-:|:-:|:-:|
| Custom properties | Preservadas | **Depende del conversor** | **Desconocido** |
| QR en pie de pagina | Preservado (es imagen) | Preservado | Preservado |

**Riesgo:** Si las custom properties no sobreviven la conversion PDF del portafirmas,
la via principal de trazabilidad se pierde silenciosamente. El QR seria la unica
via fiable.

**Mitigacion:** Probar el pipeline completo con un documento real antes de invertir
esfuerzo en la implementacion de custom properties. Si no sobreviven, el QR pasa
de "fallback" a "via principal" y las custom properties pasan a "complemento local".

---

### 3.4 Inconsistencias detectadas en el analisis

#### I1. Endpoints de generacion en `vista3.py` vs. deprecacion de Vista 3

**Inconsistencia:** La seccion B1-B6 define endpoints como
`POST /api/vista3/tarea/<id>/generar` y `GET /api/vista3/tarea/<id>/plantillas`.
Pero la seccion 2.6 dice que la vista de acordeones (Vista 3) esta DEPRECADA
y los cambios se implementaran en la vista breadcrumb BC.

**Resolucion necesaria:** Decidir donde van los endpoints de generacion:
- En `routes/vista3.py` (incoherente con deprecacion)
- En un fichero API dedicado (ej: `routes/api_escritos.py`)
- En el futuro fichero de vista BC

Actualizar las rutas en el mapa de necesidades tras decidir.

---

#### I2. Nomenclatura de ficheros — ambiguedad del separador espacio

**Observacion:** La convencion de Cabo 3 usa espacio como separador entre niveles ESFTT,
pero `nombre_en_plantilla` puede contener espacios internos ("Requerimiento subsanacion").
Ejemplo: `Redactar Requerimiento subsanacion Resolucion AAP_AAC AT-13465-24.docx`
— no es parseable para distinguir "Requerimiento subsanacion" (un tramite) de dos
niveles separados.

El documento establece que "BDDAT siempre compone, nunca parsea" — correcto y coherente.

**Impacto actual:** Ninguno. Documentar la limitacion para que futuras funcionalidades
(ej: buscador de documentos por componentes del nombre) no asuman parseabilidad.

---

#### I3. Secuencial automatico (`_2`, `_3`) sin mecanismo definido

**Observacion:** Cabo 3 menciona "secuencial automatico cuando ya existe un documento
con el mismo nombre" pero no define:
- Donde se comprueba (filesystem directo? BD? ambos?)
- Formato exacto (antes de `.docx`? despues de variante?)
- Comportamiento ante acceso concurrente (dos usuarios generan simultaneamente)

**Resolucion necesaria:** Definir mecanismo concreto antes de implementar B4.

> **Propuesta:** Comprobar en filesystem. Sufijo ` (2)`, ` (3)` antes de `.docx`.
> Sin lock especial — la probabilidad de colision en acceso concurrente es minima
> dado el volumen de usuarios esperado.

---

#### I4. FK `plantilla_id` en tabla `documentos` — sin decidir

**Observacion:** La seccion C3 dice "pendiente de decidir si la FK justifica la migracion".
Sin FK, la unica trazabilidad plantilla→documento es el codigo embebido.
Si el documento se edita y se pierde el codigo (usuario borra el QR, o las custom
properties no sobreviven la conversion), no hay forma de saber que plantilla lo genero.

> **Recomendacion:** Anadir `plantilla_id` FK nullable en `documentos`. Es una columna
> mas en una migracion que ya toca varias tablas. El coste es minimo y la redundancia
> aporta verificacion cruzada (C3 ya lo menciona como posibilidad).

---

#### I5. `filtros_adicionales` JSONB sin schema de validacion

**Observacion:** La decision 6 de Cabo 1+2 mantiene `filtros_adicionales` para
"absorber futuro sin migracion". Pero no define que claves son validas,
que tipo tiene cada valor, ni quien lee este campo.

**Impacto actual:** Ninguno — no hay codigo que lea `filtros_adicionales`.
Documentar que necesita schema explicito antes del primer uso.

---

### 3.5 Resumen cuantitativo de riesgos

| Nivel | Cant. | IDs | Requiere decision previa |
|-------|:-----:|-----|:------------------------:|
| Critico | 3 | R1, R2, R3 | Si (todos) |
| Alto | 3 | R4, R5, R6 | R5 (decidir escape), R6 (fix previo) |
| Medio | 4 | R7, R8, R9, R10 | No (gestionables) |
| Inconsistencia | 5 | I1-I5 | I1 y I3 (si) |

**Decisiones bloqueantes antes de implementar:**

1. **R1:** Semantica de `EXISTE_TIPO_SOLICITUD` con tipos combinados
2. **R3:** Estrategia de backfill de `tipo_solicitud_id` (script en migracion)
3. **R5:** Mecanismo concreto del principio de escape en selectores en cascada
4. **I1:** Ubicacion de endpoints de generacion (vista3.py, API dedicada, o vista BC)
5. **I3:** Mecanismo de secuencial automatico para nombres duplicados

**Acciones previas a la implementacion (no requieren decision):**

6. **R6:** Corregir `__str__` en `Documento` (fix independiente)
7. **R7:** Exportar `campos_catalogo` existentes antes de DROP

---

## 4) Orden logico de decisiones de diseno

Plan de implementacion en fases. Cada fase es una rama independiente que deja
Flask funcional tras merge. Si hay que parar, el sistema queda operativo
con la funcionalidad completada hasta ese punto.

### 4.1 Principios de la planificacion

- **Cada fase = una rama** `feature/167-fase-N-*` → PR → merge a `develop`
- **Migracion + codigo van juntos** en la misma rama (atomicidad R2)
- **Tras merge de cada fase:** Flask arranca, las rutas existentes funcionan
- **Si hay que revertir:** `git revert` del merge commit devuelve `develop` al estado anterior
- **Fases 1, 2 y 3 son independientes** entre si — pueden hacerse en cualquier orden
- **Fases 4+ son secuenciales** — cada una depende de las anteriores

### 4.2 Diagrama de fases

```
                Fase 0: Decisiones + fix R6
                (commit directo en develop)
                         |
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
   Fase 1:          Fase 2:        Fase 3:
   Solicitudes      Plantillas     Nomenclatura
   (whitelist +     (rename +      (nombre_en_
    FK directa)     limpieza)      plantilla ×5)
          |              |              |
          └──────────────┼──────────────┘
                         ↓
                    Fase 4:
                    Admin plantillas
                    (cascada + form)
                         |
                         ↓
                    Fase 5:
                    Motor generacion
                    (B1-B8, UI tarea)
                         |
                         ↓
                    Fase 6:
                    Trazabilidad
                    (C3 + A1 + A3)
```

> Fases 1, 2 y 3 son **tres operaciones en distintas partes del cuerpo** —
> se pueden hacer en paralelo o en cualquier orden.
> Fases 4-6 operan en la misma zona y **requieren que cicatricen las anteriores**.

---

### 4.3 Fase 0 — Decisiones previas + fix independiente

**No es rama.** Se resuelve antes de tocar codigo funcional.

#### Decisiones bloqueantes (documentar resultado en este analisis)

| ID | Decision | Afecta a |
|----|----------|----------|
| R1 | Semantica de `EXISTE_TIPO_SOLICITUD` con tipos combinados | Fase 1 |
| R5 | Mecanismo concreto del principio de escape en selectores | Fase 4 |
| I1 | Ubicacion endpoints de generacion (vista3.py / api nueva / vista BC) | Fase 5 |
| I3 | Mecanismo de secuencial automatico en nombres duplicados | Fase 5 |

#### Acciones (commit directo en develop, sin rama)

| Accion | Detalle |
|--------|---------|
| Fix R6 | `Documento.__str__`: reemplazar `self.nombre_display` por `(self.url or '').rsplit('/', 1)[-1] or f'Documento {self.id}'` |
| Export R7 | Consulta SQL: `SELECT codigo, nombre, campos_catalogo FROM tipos_escritos WHERE campos_catalogo IS NOT NULL` → guardar en `docs_prueba/temp/` como referencia |

**Criterio de avance:** 4 decisiones documentadas. Fix R6 mergeado. Export R7 guardado.

---

### 4.4 Fase 1 — Solicitudes: FK directa + whitelist ESFTT

**Rama:** `feature/167-fase-1-tipo-solicitud-directo`
**Consume:** R1 (semantica combinados), R3 (backfill), R8 (seed incompleto)
**Gestiona:** R2 (atomicidad drop solicitudes_tipos)

#### Migracion (1 fichero, `flask db revision`)

| Paso | SQL | Nota |
|------|-----|------|
| 1 | CREATE TABLE `expedientes_solicitudes`, `solicitudes_fases`, `fases_tramites` | PK compuestas, sin datos aun |
| 2 | INSERT tipos combinados en `tipos_solicitudes` (~6 filas) | AAP_AAC, AAP_AAC_DUP, etc. |
| 3 | ADD `tipo_solicitud_id` INT nullable + FK en `solicitudes` | Nullable para permitir backfill |
| 4 | **Backfill:** para cada solicitud, deducir tipo desde `solicitudes_tipos` | Script Python en `op.execute()` o `op.get_bind()` |
| 5 | ALTER `tipo_solicitud_id` SET NOT NULL | Tras backfill exitoso |
| 6 | DROP TABLE `solicitudes_tipos` | Punto de no retorno para la tabla puente |
| 7 | INSERT seed en 3 tablas whitelist desde JSON de estructura | Parsear JSON → bulk insert |

> **Punto critico:** Los pasos 3-6 son la ventana de cirugia. Si el backfill (paso 4)
> falla, la migracion aborta limpiamente antes de hacer DROP.

#### Codigo (ver punto 2.3-2.5 para detalle de cada fichero)

| Accion | Ficheros |
|--------|----------|
| Crear 3 modelos whitelist | `models/expedientes_solicitudes.py`, `solicitudes_fases.py`, `fases_tramites.py` (NUEVOS) |
| Actualizar modelo Solicitud | `models/solicitudes.py` — añadir `tipo_solicitud_id` + relationship |
| Reescribir queries (4 ficheros) | `services/motor_reglas.py`, `routes/vista3.py`, `routes/wizard_expediente.py`, `routes/api_expedientes.py` |
| Actualizar template wizard | `templates/expedientes/wizard_paso3.html` — multiselect → selector unico |
| Eliminar modelo obsoleto | `models/solicitudes_tipos.py` → BORRAR |
| Actualizar barrel | `models/__init__.py` — añadir 3, eliminar SolicitudTipo |

#### Flask tras merge

| Componente | Estado | Nota |
|------------|:------:|------|
| Flask arranca | ✓ | |
| Wizard crear expediente | ✓ | Selector tipo unico (atomico o combinado) |
| Vista3 solicitudes | ✓ | FK directa en vez de JOIN a tabla puente |
| Motor de reglas | ✓ | Reescrito segun decision R1 |
| API expedientes | ✓ | |
| Admin plantillas | ✓ | Sin cambios — sigue usando `TipoEscrito` (nombre antiguo) |
| CRUD whitelist (UI) | ✗ | Tablas existen pero sin interfaz (diferido) |

#### Verificacion

- `flask run` arranca
- Crear expediente via wizard con tipo de solicitud combinado (AAP_AAC)
- Abrir expediente existente → solicitud muestra tipo correcto (backfill ok)
- Motor de reglas: verificar que evalua solicitudes correctamente
- `grep -ri "SolicitudTipo\|solicitudes_tipos" app/` → cero resultados

---

### 4.5 Fase 2 — Plantillas: rename + limpieza + nuevos campos

**Rama:** `feature/167-fase-2-rename-plantillas`
**Gestiona:** R4 (amplitud rename), R7 (campos_catalogo), R9 (downgrade Alembic)

#### Migracion (1 fichero, `flask db revision`)

| Paso | SQL | Nota |
|------|-----|------|
| 1 | ALTER TABLE `tipos_escritos` RENAME TO `plantillas` | Tabla base |
| 2 | RENAME constraints FK y UQ | `fk_tipos_escritos_*` → `fk_plantillas_*`, idem UQ |
| 3 | ADD `tipo_expediente_id` FK nullable → `tipos_expedientes.id` | NULL = cualquier tipo |
| 4 | DROP COLUMN `campos_catalogo` | Export previo en Fase 0 |
| 5 | ADD `variante` TEXT nullable | Texto libre (ej: "Favorable", "Denegatoria") |
| 6 | ADD `origen` VARCHAR(10) NOT NULL DEFAULT 'AMBOS' en `tipos_documentos` | CHECK: INTERNO/EXTERNO/AMBOS |
| 7 | UPDATE `tipos_documentos` SET `origen` para tipos existentes | Clasificar cada tipo |

#### Codigo (ver punto 2.3-2.5 para detalle)

| Accion | Ficheros |
|--------|----------|
| Renombrar fichero + clase | `models/tipos_escritos.py` → `models/plantillas.py` (`Plantilla`, `__tablename__='plantillas'`) |
| Añadir campos al modelo | `tipo_expediente_id`, `variante` en `models/plantillas.py` |
| Añadir campo a TipoDocumento | `origen` en `models/tipos_documentos.py` |
| Actualizar barrel | `models/__init__.py` — `Plantilla` en vez de `TipoEscrito` |
| Actualizar admin routes | `modules/admin_plantillas/routes.py` — imports, queries, form, tokens |
| Actualizar admin templates (×4) | `listado.html`, `form.html`, `detalle.html`, `_panel_tokens.html` |
| Actualizar generador | `services/generador_escritos.py` — import, docstrings, mensajes |

> **Punto critico:** TODOS estos cambios deben ser coherentes. Si falta uno,
> Flask no arranca (`ImportError` o `AttributeError`). Hacer todos los cambios
> en la rama, probar, y solo entonces crear PR.

#### Flask tras merge

| Componente | Estado | Nota |
|------------|:------:|------|
| Flask arranca | ✓ | |
| Admin plantillas: listado | ✓ | Usa `Plantilla`, muestra variante y tipo expediente |
| Admin plantillas: crear/editar | ✓ | Form con variante, tipo_expediente, sin campos_catalogo |
| Admin plantillas: detalle | ✓ | Panel tokens solo Capa 1 (12 campos base) |
| Tipos documentos | ✓ | Campo `origen` visible |
| Generador escritos | ✓ | Usa `Plantilla` (stub sin cambios funcionales) |
| Selectores cascada en admin | ✗ | Aun no implementados (Fase 4) |
| Filtrado por origen en admin | ✗ | Columna existe pero form no filtra aun (Fase 4) |

#### Verificacion

- `flask run` arranca
- Admin plantillas: CRUD completo funcional (listar, crear, editar, ver)
- `grep -ri "TipoEscrito\|tipo_escrito\|tipos_escritos" app/` → cero resultados
- Verificar en BD: `\dt public.plantillas` existe, `\dt public.tipos_escritos` no

---

### 4.6 Fase 3 — Nomenclatura: `nombre_en_plantilla` en 5 tablas

**Rama:** `feature/167-fase-3-nombre-en-plantilla`
**Fase mas segura.** Solo ADD COLUMN nullable × 5.

#### Migracion (1 fichero)

ADD `nombre_en_plantilla` TEXT nullable en: `tipos_expedientes`, `tipos_solicitudes`,
`tipos_fases`, `tipos_tramites`, `tipos_tareas`. UPDATE seed con valores legibles
para los tipos existentes.

#### Codigo

Añadir `nombre_en_plantilla = db.Column(db.Text, nullable=True)` en los 5 modelos.
Sin mas cambios — la columna no se consume hasta Fase 5.

#### Flask tras merge

**Todo funciona identicamente.** 5 columnas nuevas nullable sin codigo que las lea.

#### Verificacion

- `flask run` arranca
- Consulta BD: verificar columnas y valores seed

---

### 4.7 Fase 4 — Admin plantillas: selectores en cascada + form completo

**Rama:** `feature/167-fase-4-admin-cascada`
**Requiere:** Fases 1 + 2 + 3 completadas (las tres convergen aqui)
**Consume:** R5 (principio de escape)

#### Contenido

| Bloque | Detalle |
|--------|---------|
| Endpoints AJAX cascada | `GET /api/admin/plantillas/tipos-solicitud?tipo_expediente_id=X` (y analoga para fases y tramites). Devuelve `{compatibles, otros}` si se adopta toggle de escape |
| JS selectores cascada | E → filtra S → filtra F → filtra T. Con mecanismo de escape (segun R5) |
| Filtrar tipos_documentos | Excluir `origen='EXTERNO'` en el selector del form |
| Actualizar panel tokens | Preparar endpoint AJAX para refresco futuro (Capa 2). Hoy solo muestra Capa 1 |
| Validacion sintaxis (A1) | `validar_plantilla(ruta)` — try `DocxTemplate(ruta)` antes de registrar |

#### Flask tras merge

| Componente | Estado | Nota |
|------------|:------:|------|
| Admin plantillas: form | ✓ | Selectores en cascada E→S→F→T con escape |
| Admin plantillas: validacion | ✓ | Error claro si plantilla .docx tiene sintaxis Jinja2 rota |
| Tipos documentos: filtro | ✓ | Solo internos/ambos en selector |
| Panel tokens | ✓ | Capa 1 fija, AJAX preparado para Capa 2 |
| Generacion desde tarea | ✗ | Aun no implementada (Fase 5) |

#### Verificacion

- Crear plantilla nueva → selectores filtran en cascada
- Toggle escape: al activar, aparecen opciones fuera de whitelist con advertencia
- Subir .docx con token mal escrito → error de validacion
- Subir .docx correcto → registro exitoso

---

### 4.8 Fase 5 — Motor de generacion (B1-B8)

**Rama:** `feature/167-fase-5-generacion`
**Requiere:** Fase 4 completada
**Consume:** I1 (ubicacion endpoints), I3 (secuencial automatico)

#### Contenido

| Bloque | Necesidades cubiertas |
|--------|----------------------|
| Endpoint generacion | B1. Nuevo endpoint (ubicacion segun I1) |
| Selector plantilla filtrado | B2. Plantillas aplicables al contexto ESFTT de la tarea, con NULL-comodin |
| Preview campos | B3. Valores del expediente para tokens de la plantilla seleccionada |
| Guardado + checkboxes | B4. Nombre sistematizado (Cabo 3), ruta en FILESYSTEM_BASE, checkboxes pool/doc_producido |
| Abrir carpeta | B5. Checkbox → protocolo `bddat-explorador://` |
| Regeneracion | B6. Sobrescritura transparente si misma ruta y nombre |
| Auto-inicio tarea | B8. Si `fecha_inicio is None`: asignar `date.today()` |
| Ejecutar consultas | C1. Implementar `_ejecutar_consultas()` (stub actual) |
| Errores | C7. Try/catch Jinja2 → toast con detalle |
| Nombre sistematizado | C8. Composicion desde `nombre_en_plantilla` de cada nivel ESFTT |

#### Flask tras merge

| Componente | Estado | Nota |
|------------|:------:|------|
| Tarea REDACTAR: boton generar | ✓ | Visible en vista BC |
| Selector plantilla | ✓ | Filtrado por contexto ESFTT |
| Preview antes de generar | ✓ | Campos con valores reales |
| Generacion .docx | ✓ | Sustitucion de campos, consultas, fragmentos |
| Guardado en disco | ✓ | Nombre sistematizado, ruta dentro de FILESYSTEM_BASE |
| Registro en pool (opcional) | ✓ | Via checkbox |
| Trazabilidad: codigo embebido | ✗ | Aun no (Fase 6) |
| Validacion pre-generacion | ✗ | La validacion de registro es Fase 4. Pre-generacion es redundante (C5 eliminada) |

#### Verificacion

- Abrir tarea REDACTAR → boton "Generar escrito" visible
- Seleccionar plantilla → preview de campos con valores del expediente
- Generar → .docx creado en ruta correcta con nombre sistematizado
- Marcar checkbox pool → documento registrado en pool del expediente
- Regenerar con misma plantilla → aviso sobrescritura → binario reemplazado
- Tarea sin fecha_inicio → tras generar, fecha_inicio = hoy

---

### 4.9 Fase 6 — Trazabilidad y parseo (C3, A3)

**Rama:** `feature/167-fase-6-trazabilidad`
**Requiere:** Fase 5 completada
**Consume:** R10 (supervivencia codigo embebido), I4 (FK plantilla_id)

#### Contenido

| Bloque | Detalle |
|--------|---------|
| Custom properties | Inyectar metadatos BDDAT en el .docx generado (python-docx) |
| QR clasificacion | Generar QR con codigo estructurado. Insertar en pie de pagina (o donde `{{qr_clasificacion}}`) |
| Parseo automatico (A3) | Al registrar plantilla: detectar campos, consultas, fragmentos usados |
| FK plantilla_id (I4) | Si se decide: ADD FK nullable en `documentos` + migración |

> **Prerequisito R10:** Antes de implementar custom properties, probar manualmente
> si sobreviven el pipeline .docx → portafirmas → PDF. Si no sobreviven,
> priorizar QR como via principal.

#### Flask tras merge

Feature #167 completamente funcional. Ciclo completo:
crear plantilla → generar escrito → codigo embebido → reincorporar con clasificacion.

---

### 4.10 Resumen: estado de Flask en cada punto de parada

Si se para el trabajo tras completar la fase N, este es el estado del sistema:

| Parada tras | Admin plantillas | Wizard solicitudes | Motor reglas | Generacion escritos | Trazabilidad |
|-------------|:----:|:----:|:----:|:----:|:----:|
| Fase 0 | ✓ (sin cambios) | ✓ (sin cambios) | ✓ (sin cambios) | ✗ | ✗ |
| Fase 1 | ✓ (sin cambios) | ✓ (selector unico) | ✓ (FK directa) | ✗ | ✗ |
| Fases 1+2 | ✓ (rename + campos) | ✓ | ✓ | ✗ | ✗ |
| Fases 1+2+3 | ✓ | ✓ | ✓ | ✗ | ✗ |
| Fase 4 | ✓✓ (cascada + escape) | ✓ | ✓ | ✗ | ✗ |
| Fase 5 | ✓✓ | ✓ | ✓ | ✓ | ✗ |
| Fase 6 | ✓✓ | ✓ | ✓ | ✓ | ✓ |

> **Clave:** ✓ = funcional, ✓✓ = funcional con mejoras de #167, ✗ = no implementado aun.
> En ningun punto de parada hay funcionalidad ROTA. Lo que no esta implementado
> simplemente no existe aun — el sistema funciona con lo que tiene.

### 4.11 Estimacion de complejidad por fase

| Fase | Migracion | Codigo | Complejidad | Dependencias |
|------|:---------:|:------:|:-----------:|:------------:|
| 0 | — | 1 fix trivial | Baja | Ninguna |
| 1 | 1 (7 pasos) | ~10 ficheros | **Alta** | Decision R1, R3 |
| 2 | 1 (7 pasos) | ~8 ficheros | **Alta** | Export R7 |
| 3 | 1 (simple) | 5 ficheros | Baja | Ninguna |
| 4 | — | ~4 ficheros + JS | Media-Alta | Fases 1+2+3, decision R5 |
| 5 | — | ~6 ficheros + JS + templates | **Alta** | Fase 4, decisiones I1/I3 |
| 6 | 0-1 | ~3 ficheros + dependencia pip | Media | Fase 5, verificacion R10 |

---

## Proximos pasos

**Puntos 1-4 completados.** Cabos 1-5 cerrados. Cabo 6 diferido a Fase 2.

Pendiente (analisis tecnico pre-implementacion, sin intervencion del usuario):
1. ~~Completar punto 1) Mapa de necesidades~~ — HECHO
2. ~~Completar punto 2) Dependencias con otros modulos~~ — HECHO
3. ~~Completar punto 3) Riesgos e inconsistencias~~ — HECHO
4. ~~Completar punto 4) Orden logico de decisiones de diseno~~ — HECHO
5. Completar punto 5) Preguntas sin respuesta
6. Al ejecutar migraciones: actualizar documentacion (Cabo 6)
7. Solo entonces: tocar codigo

---

## Anexos

Comentarios literales del usuario de las sesiones 1 y 2 (2026-03-15):
ver `docs/fuentesIA/ANALISIS_167_GENERACION_ESCRITOS_ANEXOS.md`
