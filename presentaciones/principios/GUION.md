# Guion — «Cómo funciona BDDAT» (borrador 2)

> ## Para retomar (traspaso del 16/10/2026)
>
> **Rama:** `claude/stoic-wright-2w0sy3` (la de los documentos de traspaso y la ADA). Todo
> está aquí: este guion y las fichas en `presentaciones/principios/fichas/`. No se trabaja
> en `develop` ni en otra rama.
>
> **Contexto:** presentación larga para el personal técnico de la ADA, tras la demo del
> 16/10. Trata de los principios de funcionamiento de BDDAT; la tecnología está en
> `../fundamentos/`, cuyo formato se copia (lienzo 1280×720, `data-paso`).
>
> **Hecho (8 fichas, cada una descrita abajo con ✔):**
> 1 El procedimiento de autorización · 2 Flujo rígido frente a libertad total ·
> 3 Principios de diseño · 4 El documento y el expediente · 5 Encapsulamiento y semántica ·
> 6 La tarea y el documento · 7 Las tareas encadenan documentos · 8 Entidades.
>
> **Siguiente:** la 9 (Normas → Contexto → Reglas → Prohibición → Escape), luego 10
> (invariantes) y el resto del guion. La 20 (usuarios y roles) se añadió al final.
>
> **Pendiente:**
> - Ficha 4: reordenar y añadir algo al lado del documento (lo dijo Carlos; aún sin concretar).
> - Reordenar el conjunto al final. La 18 y la 20 se solapan (roles): una absorbe a la otra.
> - Falta `compilar.py` e `index.html` (copiar los de `../fundamentos/` y poner `ORDEN`).
>   Hasta entonces cada ficha se abre sola en el navegador.
>
> **Cómo se trabaja (acordado con Carlos):**
> - Pocas palabras en pantalla, nada rimbombante; Carlos narra. Solo esquemas animados.
> - Carlos describe la animación; se hace un primer intento, se ajusta y, cuando está
>   madura, se pasa a limpio aquí (tabla de pasos, ✔ hecha). El estado de desarrollo solo
>   se marca internamente y va en una o dos fichas al final.
> - Principales en recuadro, secundarios en píldora. Azul lo que va, verde lo que vuelve,
>   morado el tiempo. Sin ámbar (en `fundamentos` significa «plan»).
> - Mecanismos ya usados en las fichas: `data-paso` (aparece en N), `data-hasta` (se
>   oculta en M), `data-solo` (solo en su paso), `#todo` y `#paso=N` en la dirección.
> - En la nube se revisa con Playwright (abrir el HTML con `#paso=N` y capturar) y se le
>   enseña a Carlos en el panel de la app. Citas legales, comprobadas en el BOE.

> **Para qué.** Presentación para el personal técnico de la ADA sobre los principios de
> funcionamiento de BDDAT. La tecnología queda en `../fundamentos/`.
>
> **Formato.** El de `../fundamentos/`: fichas HTML de 1280×720 en una sola línea, con
> esquemas animados por pasos. Cada ficha lleva un título y pocas frases: el resto lo
> cuenta Carlos.
>
> **Cómo leer cada ficha de este guion.**
> - **En pantalla:** lo único que se escribe en la ficha.
> - **Notas:** apoyo para hablar; no van en la ficha.
> - **Animación:** la define Carlos al hacer la ficha.
> - **Estado (interno):** cómo está en el código; no se muestra.
> - **[Carlos]** = punto pedido por Carlos; **[propuesta]** = añadido, a depurar.
>
> El orden se va ajustando ficha a ficha.

---

## 0. Portada — ✔ hecha (primer intento, sin revisar)

**Fichero:** `fichas/ficha_00_portada.html`

| Paso | Aparece |
|---|---|
| 1 | **BDDAT** · Cómo funciona, en grande y centrado · «Tramitación de autorizaciones de instalaciones eléctricas de alta tensión» |
| 2 | La cabecera sube y aparece el índice en ocho bloques: el problema y los principios · la estructura · el control · con quién y cuándo · fases del procedimiento · los documentos · las personas · de principio a fin (dónde estamos y lo que viene) |

**Notas:** el índice es el hilo de la presentación: cada bloque agrupa fichas que se
apoyan en las anteriores.

---

## 1. El procedimiento de autorización de instalaciones eléctricas — [Carlos] ✔ hecha

**Fichero:** `fichas/ficha_01_procedimiento.html`

**En pantalla:** una nube de conceptos, unos más grandes que otros, que da impresión de
complejidad. Principales en recuadro, secundarios en píldora. Los solapes son parte del
juego.

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | **Normativa** · RD 1955/2000 · LSE · RD 337/2014 · RD 223/2008 · decretos de simplificación · medidas urgentes |
| 3 | **Promotor** |
| 4 | **Distribuidora** |
| 5 | **Información pública** |
| 6 | **Organismos** |
| 7 | **Solicitudes** · AAP · AAC · DUP · AE · AAT · Modificación · Cierre · … |
| 8 | **Proyecto** · distribución · transporte · renovables |
| 9 | **Documentación** |
| 10 | **Recursos** |
| 11 | **Plazos** |
| 12 | **Excepciones** · suelo urbano · tensión |
| 13 | **Figura ambiental** · AAU · Licencia ambiental |
| 14–17 | Cuatro tandas de flechas curvas rotuladas que relacionan unos con otros (no pretenden ser exactas): requerimiento, requisitos, exime, separata, condicionados, espera de plazo, notificación, alegaciones, anuncio, informe, plazo, resolución, sin IP, exenta… Azul lo que va, verde lo que vuelve, morado lo que es tiempo |

**Notas:** Carlos narra cada concepto al aparecer.

**Estado (interno):** —

---

## 2. Flujo rígido frente a libertad total — [Carlos] ✔ hecha

**Fichero:** `fichas/ficha_02_rigido_libre.html`

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | Izquierda, **Flujo rígido** («el sistema decide el siguiente paso»): Solicitud → Requerimiento → Información pública → Consultas → Resolución → Recursos, en cascada vertical con flechas |
| 3 | Derecha, **Libertad total** («todo cabe, nada se controla»): los mismos seis elementos sin conexión, equidistantes en círculo y en otro orden |
| 4–8 | Saltos en la libertad total: una flecha entre dos bloques cualesquiera por paso; al aparecer la siguiente, la anterior se borra |
| 9 | La última flecha se quita y aparece en medio **BDDAT** · «se sitúa en un punto intermedio» |

**Notas:** en el flujo rígido lo imprevisto no cabe y el tramitador acaba trabajando
fuera; en la libertad total el estado depende de que alguien lo apunte. En BDDAT la
estructura legal guía, el tramitador tiene la iniciativa, el sistema prohíbe lo que no
debe pasar y siempre hay salida justificada.

**Fuente:** ficha 1 de octubre; `docs/historial/DISEÑO_MOTOR_REGLAS.md` §Principio de escape.

**Estado (interno):** hecho.

---

## 3. Principios de diseño de BDDAT — [Carlos] ✔ hecha

**Fichero:** `fichas/ficha_03_principios.html`

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2–8 | Un principio por clic, numerado: (1) Todo permitido mientras no esté prohibido · (2) Las prohibiciones se pueden saltar, pero siempre se justifican · (3) Una sola fuente de la verdad · (4) El documento es el núcleo del dato · (5) El estado se deriva, no se apunta · (6) La semántica vive en los tipos · (7) Las reglas son datos, no código |

Son principios, no lo que se construye con ellos. Carlos los explica hablando: no hay
ficha por principio.

**Notas** (del antiguo punto «Todo vale mientras no esté prohibido»): lista negra, no lista blanca. El motor no genera el flujo: solo responde a esa
pregunta. No hay que modelar todos los caminos, solo los que la norma veda. Por eso se
quitaron las listas blancas de combinaciones de la estructura.

**Fuente:** `DISEÑO_MOTOR_REGLAS.md` §Principio rector; ADR-007.

**Estado (interno):** hecho.

---

## 4. El documento y el expediente — [Carlos] ✔ hecha (pendiente: reordenar y añadir algo al lado del documento)

**Fichero:** `fichas/ficha_04_documento_expediente.html`

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | Izquierda, **Documento**: el fichero físico (`informe.pdf`) |
| 3–4 | Los metadatos que le pone BDDAT: tipo de documento · fecha administrativa |
| 5 | Art. 26.2 LPACAP: referencia temporal y metadatos mínimos |
| 6 | Derecha, **Expediente**: «conjunto ordenado de documentos y actuaciones que sirven de antecedente y fundamento a la resolución administrativa» (art. 70.1 LPACAP) |
| 7 | Cinco documentos entran numerados en una carpeta (el índice del art. 70.2) |
| 8 | Borradores, notas, información auxiliar: no forman parte del expediente (art. 70.4) |

Citas comprobadas en el BOE (BOE-A-2015-10565). El art. 40 es el de la notificación.

**Notas:** fecha administrativa, la que cuenta legalmente, no la del fichero; la
estructura no guarda fechas; nadie actualiza el estado a mano. Un documento sin
vincular no es del expediente (huérfano del pool).

**Fuente:** ADR-002, ADR-027; fichas 5 y 7 de octubre.

**Estado (interno):** hecho.

---

## 5. Encapsulamiento y semántica — [Carlos] ✔ hecha

**Fichero:** `fichas/ficha_05_encapsulamiento_tipos.html`

Dos conceptos en una ficha: primero el encapsulamiento (cada nivel envuelve al
siguiente), luego los tipos de cada nivel, que le dan la semántica.

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | Izquierda: **Expediente** |
| 3 | Derecha, «Tipos de expediente»: Transporte · Distribución · Distribución cedida · Renovable · Autoconsumo · Línea directa · Convencional · Otros |
| 4 | Llave horizontal (punta arriba, brazos abajo, medio ancho) y **Solicitud**; los tipos anteriores se quitan |
| 5 | «Tipos de solicitud»: AAP · AAC · DUP · AE provisional · AE definitiva · AAT · Modificación · Cierre · Desistimiento · Renuncia · Recurso · RAIPEE · y combinadas: AAP+AAC… |
| 6 | Llave y **Fase** |
| 7 | «Tipos de fase» (selección): Análisis de solicitud · Consultas · Información pública · Compatibilidad ambiental · Figura ambiental externa · Datos catastrales · Consulta al Ministerio · Resolución · Resolución DUP · … |
| 8 | Llave y **Trámite** |
| 9 | «Tipos de trámite» (selección): Análisis documental · Requerimiento de subsanación · Comunicación de inicio · Separata a organismo · Traslado al titular · Anuncio en el BOE · Tablón de ayuntamientos · … |
| 10 | Llave y **Tarea** |
| 11 | «Tipos de tarea»: ANALIZAR · ELABORAR · NOTIFICAR · ESPERAR PLAZO (se quedan) |

Los tipos de la derecha no se acumulan: se sustituyen al bajar de nivel para que quepan
grandes.

**Notas:** la **Fase** es nivel propio en el modelo. Los tipos son catálogo. Fases en
paralelo.

**Fuente:** fichas 1 y 5 de octubre; ADR-037; `docs/referencia/ESTRUCTURA_FTT.md`.

**Estado (interno):** hecho; la tabla de trámites por fase existe pero aún no se edita
desde la interfaz.

---

## 6. La tarea y el documento — [Carlos] ✔ hecha

**Fichero:** `fichas/ficha_06_tareas.html`

Una ficha secuencial para las cuatro tareas, sin acumular: cada una sustituye a la
anterior. La tarea es la unidad mínima de trabajo; consume (N) y produce (1) documentos.

Por tarea, cuatro clics:

| Clic | Aparece |
|---|---|
| 1 | Arriba, el encuadre ESFTT con un ejemplo típico; en el centro, la tarea |
| 2 | Izquierda: qué hace |
| 3 | Derecha arriba: **Consume (N)** con icono de varios documentos y sus tipos; flecha en codo hasta la tarea |
| 4 | Derecha abajo: **Produce (1)** con icono de un documento («uno de estos tipos» si puede ser varios); flecha en codo desde la tarea |

| Tarea | Encuadre | Qué hace | Consume | Produce |
|---|---|---|---|---|
| ANALIZAR | Distribución › AAP › Análisis de solicitud › Análisis documental | Examina documentación y emite un diagnóstico | Modelo de solicitud · Proyecto técnico · Justificante de la tasa · Documentación de subsanación · Respuesta del organismo · Alegación de IP · … | Diagnóstico de análisis |
| ELABORAR | … › Análisis de solicitud › Requerimiento de subsanación | Redacta y firma un escrito, en un solo acto | Borrador del escrito · Diagnóstico de análisis | Oficio de requerimiento ✍ · Oficio de consulta ✍ · Resolución ✍ · … |
| NOTIFICAR | … › Consultas › Separata a organismo | Hace llegar el escrito a su destinatario | Los mismos escritos firmados ✍ · Acuse del primer intento postal · … | Justificante Notifica-PNT · BandeJA · SIR / ARIES · postal · … |
| ESPERAR PLAZO | … › Consultas › Separata a organismo | Cuenta el plazo y recoge lo que llega | Justificante de la notificación · Justificante publicación BOE · … | Respuesta del organismo · Documentación de subsanación · Informe del Ministerio · Certificado de plazo cumplido · … |

✍ = icono de firma (documento firmado).

**Notas:** eran siete: REDACTAR y FIRMAR se funden en ELABORAR; PUBLICAR es una
NOTIFICAR; INCORPORAR desaparece porque incorporar es vincular un documento. ANALIZAR
siempre produce un diagnóstico.

**Fuente:** `ESTRUCTURA_FTT.md` §Tareas atómicas; ADR-003, ADR-004, ADR-005; ficha 5b
de octubre.

**Estado (interno):** hecho.

---

## 7. Las tareas encadenan documentos — [Carlos] ✔ hecha

**Fichero:** `fichas/ficha_07_cadenas.html`

Tres trámites de `ESTRUCTURA_FTT` en columna, repartidos en horizontal. Entre cada dos
tareas, el documento que produce la de arriba y consume la de abajo. Un clic por
cadena, que cae en cascada.

| Clic | Cadena |
|---|---|
| 2 | **Requerimiento de subsanación** (Análisis de solicitud): Diagnóstico de análisis → ELABORAR → Oficio de requerimiento de subsanación ✍ → NOTIFICAR → Justificante Notifica-PNT → ESPERAR PLAZO → Documentación de subsanación → ANALIZAR → Diagnóstico de análisis |
| 3 | **Separata a organismo** (Consultas): Separata del proyecto → ELABORAR → Oficio de consulta a organismo ✍ → NOTIFICAR → Justificante BandeJA → ESPERAR PLAZO → Respuesta del organismo → ANALIZAR → Diagnóstico de análisis |
| 4 | **Anuncio en el BOP** (Información pública), contraejemplo con doble espera: Anuncio de información pública → ELABORAR → Oficio de remisión del anuncio ✍ → NOTIFICAR → Justificante SIR → ESPERAR PLAZO *publicación* → Anuncio publicado en el BOP → ESPERAR PLAZO *alegaciones* → Certificado de plazo cumplido |

**Notas:** ANALIZAR → diagnóstico → ELABORAR → escrito → NOTIFICAR → justificante →
ESPERAR PLAZO → documento recibido → ANALIZAR. Patrones combinables: A (analizar),
B (elaborar y notificar), C (con espera), F (espera pasiva). Toda espera que pueda
recibir documentación de terceros exige un ANALIZAR después.

**Fuente:** `ESTRUCTURA_FTT.md` §Tareas atómicas y §Patrones de flujo; ADR-010.

**Estado (interno):** hecho.

---

## 8. Entidades — [Carlos] ✔ hecha

**Fichero:** `fichas/ficha_08_entidades.html`

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | Izquierda, **Una tabla por tipo**: Titulares, Organismos, Ayuntamientos; «Distribuidora del Sur S.A.» está en dos, con teléfonos distintos |
| 3 | Las filas duplicadas se marcan en rojo: «La misma empresa, dos veces, con datos distintos» |
| 4 | Derecha, **Una sola tabla: entidades con roles**: la ficha de la entidad (NIF, dirección, teléfono) y sus roles como interruptores (Titular ✔, Consultado ✔, Publicador ✗) |
| 5 | Representación: «Gestora Técnica S.L. — actúa en su nombre», flecha «representa» |
| 6 | Direcciones de notificación por rol: como titular → Dpto. de tramitaciones; como consultada → Área técnica |

Nombres y datos ficticios. Fuera de pantalla: tipo de titular y la sede de la solicitud
para el solicitante.

**Notas:** titular en un expediente, organismo consultado en otro: roles, no una tabla
por tipo, para no duplicar datos (una sola fuente de la verdad). Representación.
Direcciones de notificación por rol. Al solicitante, la sede de su solicitud.

**Fuente:** fichas 1 y 6 de octubre.

**Estado (interno):** hecho; el tipo de titular aún solo sirve para filtrar.

---

## 8b. El estado se deriva, no se apunta — [propuesta, hueco] ✔ hecha (primer intento, sin revisar)

**Fichero:** `fichas/ficha_08b_estado.html`

El principio 5 en imagen, y el listado de la antigua 18. Una fase de consultas con tres
separatas en distinto punto.

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | Las tareas con su color y por qué: ADIF (ELABORAR firmado 🟢 · NOTIFICAR justificante 🟢 · ESPERAR PLAZO corre el plazo ⚪), Ayuntamiento (ELABORAR PDF para firma 🟡), CHG (ELABORAR firmado 🟢 · NOTIFICAR falta el justificante 🔵) · «el color de una tarea sale de sus documentos» |
| 3 | Los trámites toman el color más urgente de sus tareas: ⚪ · 🟡 · 🔵 |
| 4 | La fase **Consultas**, 🟡 · «hacia arriba, manda lo más urgente» |
| 5 | El **listado de seguimiento**: AT-7 · AAP+AAC · Análisis FIN · Consultas FIRMA · IP PLAZOS · «el listado lee el mismo cálculo: nadie actualiza el estado a mano» |
| 6 | **Qué dice cada color**: actúa el tramitador · gestión nuestra · en firma · espera a un externo · corre un plazo · terminado |

**Notas:** ningún nivel guarda su estado: se recorre el árbol de abajo arriba y prevalece
el de mayor prioridad. El árbol y el listado leen el mismo cálculo, así que no pueden
contradecirse. Rojo: el tramitador tiene que actuar (incluida la notificación agotada,
que pide el edicto); naranja: gestión nuestra (cerrar una fase, segundo intento postal,
puesta en sede); amarillo: en firma; azul: falta el justificante de la notificación;
gris: corre un plazo; verde: terminado. Trabajar por lotes es filtrar el listado.

**Fuente:** ADR-002; `docs/referencia/MODELO_ESTADOS_SEMAFORO.md` §2 y §5; ficha 9 de
octubre.

**Estado (interno):** hecho.

---

## 9. Normas → Contexto → Reglas → Prohibición → Escape — [Carlos] ✔ hecha (primer intento, sin revisar)

**Fichero:** `fichas/ficha_09_reglas.html` · título «De la norma al escape»

Cinco columnas encadenadas con flechas, una por clic, con un mismo ejemplo de punta a
punta (abrir la resolución con AAU y la información pública sin cerrar).

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | **Normas**: píldoras LSE · RD 1955/2000 · LPACAP · DL 26/2021 · Decreto 9/2011 · …; tarjeta azul «DL 26/2021 · DF 4.ª — Con AAU, la información pública es obligatoria» |
| 3 | **Contexto**: «Dónde estoy» (Distribución › AAP, crear fase Resolución) y «Qué es cierto ahora» (instrumento ambiental AAU, información pública abierta, tensión 66 kV, plazo de la IP vencido) |
| 4 | **Reglas**: la regla como fila (al crear Resolución · si AAU y la IP sin cerrar · efecto BLOQUEAR · norma); píldoras «un registro, no código», «con excepciones», «la vigencia es de la regla» |
| 5 | **Prohibición**: Bloquea / Advierte y el aviso que ve el tramitador, con la norma enlazada |
| 6 | **Escape**: «Seguir de todos modos», justificación obligatoria, flecha a la **Bitácora** (quién · cuándo · qué regla · por qué) |
| 7 | Abajo, **Modo del motor**: el cursor recorre Inactivo → Solo avisa → Bloquea · «de la libertad al control, pasando por el aviso» |

**Notas:** las reglas son registros, no código, y citan su norma; la vigencia es de la
regla. Contexto: dónde estoy en la estructura y qué es cierto ahora (datos del
proyecto, calculados, plazos). Regla con excepciones. Prohibición: bloquear o advertir.
Escape: seguir justificándolo, queda en la bitácora. Tres modos del motor: inactivo,
avisa, bloquea.

**Fuente:** ficha 1 de octubre; ADR-001, ADR-026; `docs/diseño/INVENTARIO_BACKEND.md` §3.

**Estado (interno):** hecho.

---

## 10. Invariantes estructurales — [Carlos] ✔ hecha (primer intento, sin revisar)

**Fichero:** `fichas/ficha_10_invariantes.html` · título «La norma cambia, la estructura no»

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | El recorrido de una acción: Acción → **Reglas** («la norma»: catálogo · modo del motor · escape) → Se hace, con un hueco antes de las reglas |
| 3 | En el hueco, **Invariantes** («la estructura»: en el código · antes que las reglas · siempre activos) |
| 4 | Tarjeta azul **Con escape justificado**: reabrir una fase cerrada (acto propio) · notificar sin destinatario — «se puede, explicando por qué» |
| 5 | Tarjeta **Puerta cerrada**: borrar lo que tiene contenido · esperar un plazo sin haber notificado · certificar lo que no ha pasado — «se deshace hacia atrás, paso a paso» |
| 6 | Tarjeta roja **Irreversible**: lo notificado no se deshace · resuelta y notificada, lo que venga es otra solicitud — «se corrige con actos posteriores» |

**Notas:** fijos en el código y previos al motor. No borrar lo que tiene hijos ni una
tarea con documentos; fase cerrada sellada (reabrir es un acto propio); toda
notificación tiene destinatario. Casi todos tienen escape; lo ya notificado al exterior
no: se corrige con actos posteriores.

**Fuente:** ficha 1 de octubre; ADR-036, ADR-051 §E; `INVENTARIO_BACKEND.md` §3.5.

**Estado (interno):** hecho.

---

## 11. Certificados: constatar y sellar — [propuesta] ✔ hecha (primer intento, sin revisar)

**Fichero:** `fichas/ficha_11_certificados.html`

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | La vida de una solicitud: **Instrucción** (Análisis de solicitud, Consultas, Información pública, en paralelo) → **Resolución** (elaborar · notificar) |
| 3 | Sello morado pequeño bajo la información pública: **Plazo cumplido** (el más sencillo: constata que un plazo venció) |
| 4 | Sello **Fin de instrucción** en la bisagra: «sin él no se abre la resolución» |
| 5 | Sello **Cierre de fase**: «notificado al solicitante y nada pendiente» |
| 6 | Sello **Cierre de solicitud**: «cada acto: ¿en plazo?» |
| 7 | Abajo, el informe **¿Cómo voy?** del fin de instrucción: dos fases ✓ y la información pública ✗ «falta cerrar»; el botón Emitir apagado |
| 8 | La fila pasa a ✓, Emitir se enciende, flecha al documento con sello: **Emitido** «lo que constata ya no se toca» · «Mientras no se emite, se calcula; emitido, se lee» |

**Notas:** un certificado no lo firma nadie del servicio ni viene de fuera: constata algo
del expediente que no se ve leyendo BDDAT directamente, y al emitirse sella lo que dice.
La acción siguiente se presenta como petición de un certificado: el informe «¿cómo voy?»
está siempre disponible y solo se consolida sin pendientes. El de fin de instrucción es la
bisagra del art. 82.1 LPACAP («instruidos los procedimientos…»): una regla impide abrir la
resolución sin él (con escape), y un invariante impide emitirlo con fases sin cerrar
(puerta cerrada: sería un documento que miente). El cierre de fase exige antes el de
cumplimiento (notificado al solicitante). El de la solicitud resume por acto: plazo,
fecha de resolución y si se cumplió.

**Fuente:** ADR-043; ADR-049 §F; ficha 5 de octubre.

**Estado (interno):** hecho.

---

## 12. Plazos — [propuesta] ✔ hecha (primer intento, sin revisar)

**Fichero:** `fichas/ficha_12_plazos.html`

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | Izquierda, una entrada del **Catálogo de plazos** (editable), la del requerimiento de subsanación: dónde · desde (el justificante de la notificación) · cuánto (10 días hábiles, en morado) · cumple (la documentación de subsanación) · si vence (se le tiene por desistido, en rojo) · norma (LPACAP art. 68.1) |
| 3 | Derecha, el calendario del 4 al 18: el día del justificante, los fines de semana rayados, la cuenta 1…10 de hábiles y «vence» el 18 · «sin sábados, domingos ni festivos» |
| 4 | «hoy» el 11: la barra morada corre hasta hoy · «En plazo · quedan 5 días» |
| 5 | Llega la documentación de subsanación el 13: la barra para ahí, en verde · «Cumplido» · «Para en lo primero que llegue: cumplimiento, vencimiento u hoy» |
| 6 | Abajo, el **Plazo de resolver y notificar** de la AAP (3 meses desde la solicitud): una barra de la solicitud al vencimiento |
| 7 | El tramo del requerimiento queda rayado («suspende») y el vencimiento se desplaza: «más tarde» |

**Notas:** cada plazo dice a qué se aplica, desde qué documento se cuenta, qué
documento acredita el cumplimiento y qué pasa si vence (silencio, caducidad…).
Suspensión como medida única. Plazo de resolver de cada acto.

**Fuente:** ADR-041, ADR-048.

**Estado (interno):** hecho, con el plazo de resolver de cada acto en el árbol (#922) y
la suspensión por acto (#796); pendiente la proyección de plazos.

---

## 12b. Una solicitud, varios actos — [propuesta, hueco] ✔ hecha (primer intento, sin revisar)

**Fichero:** `fichas/ficha_12b_actos.html`

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | **Solicitud AAP + AAC + DUP**, que se abre en tres actos: AAP (autorización previa) · AAC (de construcción) · DUP (utilidad pública) |
| 3 | Una barra morada por acto, desde la misma solicitud: 3 meses · 3 meses · 6 meses · «desde la misma solicitud: cada acto, su plazo» |
| 4 | Detrás, al principio de las tres barras: «una instrucción común» |
| 5 | **Resolución AAP y AAC** («juntas o por separado») y **Resolución DUP** («siempre en acto aparte») |
| 6 | Abajo, por qué: **Autorizaciones** (se consideran dictadas por la Dirección General · recurso de alzada) frente a **Declaración de utilidad pública** (la Consejería · agota la vía administrativa: reposición) |

**Notas:** una solicitud es un contenedor: no cumple ni incumple plazos; lo hace cada
acto. El plazo corre desde la solicitud pero es de cada acto, y existe desde el primer
día, antes de que exista la fase que lo resuelve. La instrucción se comparte (una ronda
de consultas por organismo para todo lo que ampara el mismo proyecto). En Andalucía la
autorización y la DUP no pueden ir en el mismo acto: no las dicta el mismo órgano ni
agotan la misma vía (Resolución de la DG de Energía de 11/03/2022 y Orden de 05/06/2013,
art. 5.6). La DUP no se puede declarar sin aprobar antes o a la vez el proyecto de
ejecución. Conecta con la 12 (el plazo de resolver de la AAP) y con la de certificados
(el cierre de la solicitud enumera por acto).

**Fuente:** ADR-045, ADR-046, ADR-047, ADR-049 §E.

**Estado (interno):** hecho; la fase de resolución de la DUP, en curso.

---

## 13. Notificaciones — [propuesta] ✔ hecha (primer intento, sin revisar)

**Fichero:** `fichas/ficha_13_notificaciones.html`

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | Izquierda, **A quién** («una notificación por destinatario, con la dirección de su rol»): la resolución firmada se abre en cuatro NOTIFICAR (solicitante, dos organismos consultados, órgano ambiental) |
| 3 | Quinta fila discontinua en rojo, «FALTA: Ayuntamiento de Jerez» · «el trámite no termina mientras falte alguien» |
| 4 | Derecha, **Cómo** («el canal no se elige: lo dice el justificante»): Justificante Notifica-PNT → canales Notifica-PNT (marcado) · BandeJA · SIR · Postal · Edicto en el BOE |
| 5 | **Cuándo** («dos fechas, cada una con su efecto»): 3 jun puesta a disposición, «cumple el deber de notificar» (azul) · 6 jun leída, «surte efectos: corren sus plazos» (verde) |
| 6 | Abajo a la izquierda, **En papel**: 1.er intento fallido → 2.º intento fallido → anuncio en el BOE |

**Notas:** el canal no se elige: se deduce del justificante vinculado. Fechas de
notificación, de cumplimiento y de efectos. Notificación edictal.

**Fuente:** ADR-034, ADR-049, ADR-051, ADR-052; `ESTRUCTURA_FTT.md` §Trámites transversales.

**Estado (interno):** modelo hecho, y tramitar una notificación con su destinatario en el
navegador (#929, zona A); quedan pantallas: aplicar el edicto (#1037), representante y
sede del solicitante (#1038), fecha en la subida (#1036) y la visibilidad (zona E).

---

## 13b. Análisis de la solicitud — [propuesta, hueco] ✔ hecha (primer intento, sin revisar)

**Fichero:** `fichas/ficha_13b_analisis.html`

La primera fase del procedimiento, y el arranque del ejemplo que recorre la
presentación (requerimiento de subsanación: cadena, plazo, escrito).

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | **Este proyecto**: AAP · persona jurídica · con representante · sin DUP |
| 3 | La lista de requisitos de esta solicitud y **por qué** se exige cada uno (siempre · persona jurídica · con representante · sin DUP); la relación de bienes y derechos, tachada («con DUP») |
| 4 | La columna **Documento**: cada requisito con su fichero (✓) o «✗ falta» en la tasa · «Check documental: 5 de 6 · lo vincula el técnico; el sistema solo avisa» |
| 5 | **Diagnóstico DESFAVORABLE** con tres defectos y su origen: del check documental, del catálogo de requerimientos y texto libre |
| 6 | Flecha a **Requerimiento de subsanación** («con defectos: diez días para subsanar»); en gris y discontinua, **Comunicación de inicio** («sin defectos») |
| 7 | Píldoras: «lo que se exige es catálogo, con condiciones como las reglas» · «sin la tasa no se pasa de fase · Ley 10/2021, art. 45.1» |

**Notas:** los requisitos documentales son un catálogo con condiciones sobre los datos
del proyecto (tensión, suelo, DUP, instrumento ambiental…), con el mismo mecanismo que
las reglas. El técnico vincula cada requisito con el documento del pool que lo cumple;
el sistema avisa si el tipo no casa, pero el juicio es suyo. Hay además un check técnico
(contenido del proyecto según los reglamentos). Los defectos que se repiten salen del
catálogo de requerimientos: imagen homogénea de la Administración. El diagnóstico es lo
que produce ANALIZAR (6) y lo que consume el ELABORAR del requerimiento (escritos).
Requerimiento y comunicación de inicio son excluyentes; la comunicación de inicio es
obligatoria (art. 21.4 LPACAP) y en renovables acredita el hito 1 ante el gestor de red.

**Fuente:** `docs/referencia/DISEÑO_ANALISIS_SOLICITUD.md` §3, §4, §6 y §7; ADR-033;
captura 12 de la demo de la ADA.

**Estado (interno):** hecho.

---

## 14. Organismos consultados — [propuesta] ✔ hecha (primer intento, sin revisar)

**Fichero:** `fichas/ficha_14_organismos.html`

Una calle por organismo, que avanza a su ritmo: lo que va en azul (separata, traslados),
lo que vuelve en verde (la respuesta), el silencio en morado.

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | **Fase Consultas** «un camino propio por organismo, cada uno a su ritmo»; cuatro organismos (ADIF, Distribuidora, Ayuntamiento, Confederación) con su Separata, en bloque |
| 3 | ADIF: calla 30 días → ✓ conformidad |
| 4 | Distribuidora: condicionado → Traslado al titular → conforme → ✓ condicionado aceptado |
| 5 | Ayuntamiento: oposición → Traslado al titular → reparos → Traslado al organismo → calla 15 días → ✓ favorable |
| 6 | Confederación: informe → Traslado al titular → conforme → ✓ favorable; abajo, píldoras «si el organismo calla: conformidad» · «una sola vuelta de reparos» · «RD 1955/2000, arts. 127 y 131» |
| 7 | Sello: **Todos terminados** «la fase se cierra con su certificado» |

**Notas:** separata, respuesta, traslado al titular, silencio. Número variable de
organismos por fase.

**Fuente:** ADR-011, ADR-042; expediente-tipo `CONSULTAS_VARIOS_ESTADOS`.

**Estado (interno):** hecho (fase de consultas completa).

---

## 15. Reformados de proyecto — [propuesta] ✔ hecha (primer intento, sin revisar)

**Fichero:** `fichas/ficha_15_reformados.html` · título «Reformados de proyecto: la versión como eje»

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | La línea de los documentos del proyecto; el **Proyecto** abre la **Versión 1** |
| 3 | De la versión 1 cuelgan sus fases: Análisis de solicitud · Consultas · Información pública |
| 4 | Llega un **Anexo de planos**: «¿Produce un reformado? No» — sigue la versión 1 |
| 5 | Llega un **Reformado** (requerido o voluntario): «¿Produce un reformado? Sí» — corte y **Versión 2** |
| 6 | De la versión 2 cuelgan Consultas e Información pública (2.ª ronda); las de la versión 1 pasan a discontinuas · «la historia de la versión 1 se conserva» |
| 7 | **Resolución** «sobre la versión 2» · píldoras «repetir una fase en la misma versión: la regla lo bloquea» · «la resolución, congruente con lo pedido» |

**Notas:** un reformado corta las fases, que se repiten para la nueva versión sin perder
la historia.

**Fuente:** ADR-044; expediente-tipo `REFORMADO_ANALISIS_Y_CONSULTAS`.

**Estado (interno):** hecho.

---

## 16. Escritos y plantillas — [propuesta] ✔ hecha (primer intento, sin revisar)

**Fichero:** `fichas/ficha_16_escritos.html`

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | Arriba, dónde estoy (Distribución › AAP › Análisis de solicitud › Requerimiento de subsanación › ELABORAR); a la izquierda, **Plantillas para este punto** (la del requerimiento marcada, su reiteración y «Ver todas…» en discontinua) · «se ofrecen según dónde estoy; las mantiene el supervisor, sin programar» |
| 3 | La **Plantilla**: texto fijo, huecos (titular, proyecto, defecto), condiciones («si falta la tasa», «para cada defecto») y el código en el pie |
| 4 | Flecha al **Borrador** con los datos del expediente resaltados y la lista de defectos |
| 5 | Se recuadra el código del pie (`BDDAT-4711-L`) · «el código del pie dice de qué tarea es el escrito» |
| 6 | A la derecha, hasta la firma: se retoca si hace falta → PDF para firma → **Firmado** ✍ «lo produce ELABORAR» |

**Notas:** plantillas `.odt`, elegidas por la posición en la estructura (con escape),
con código de trazabilidad en el pie.

**Fuente:** ADR-025, ADR-035; fichas 8 y 8b de octubre.

**Estado (interno):** generación hecha; plantillas al almacén, edición y PDF para firma
pendientes.

---

## 17. Almacén documental — [propuesta] ✔ hecha (primer intento, sin revisar)

**Fichero:** `fichas/ficha_17_almacen.html`

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | Izquierda, **Antes**: Usuarios y BDDAT escriben en la misma Carpeta de red |
| 3 | «✗ resolución.pdf, cambiada desde Windows» · «BDDAT no se entera: dos fuentes de la verdad» |
| 4 | Derecha, **Ahora**: Usuarios → BDDAT → Almacén (archivador con candado) · «los usuarios no tocan los ficheros: solo BDDAT entra» |
| 5 | **Con su huella**: «si cambia, se nota» |
| 6 | **Un manifiesto por expediente**: «sin BDDAT, se recuperan las carpetas», con el árbol de carpetas de un AT |

**Notas:** almacén propio por contenido, sin acceso directo de los usuarios; el
manifiesto permite reconstruir las carpetas sin BDDAT. El pool son los documentos sin
vincular.

**Fuente:** ADR-050; ficha 7 de octubre.

**Estado (interno):** almacén hecho; ZIP del expediente, papelera y limpieza pendientes.

---

## 18. Roles, vistas y bitácora — [propuesta] → absorbida

Se reparte: los roles van a la 20 (usuarios y roles); el listado que se calcula del
árbol, a una ficha propia sobre el estado derivado; la bitácora, al escape (9) y al
permiso blando (20).

**Fuente:** ADR-012, ADR-013, ADR-023, ADR-053; fichas 3, 4b y 9 de octubre.

---

## 20. Usuarios y roles — [Carlos] ✔ hecha (primer intento, sin revisar; absorbe los roles de la 18)

**Fichero:** `fichas/ficha_20_usuarios_roles.html`

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2–5 | Un rol por clic, cada uno con su icono, qué hace y su «Mi trabajo»: **Tramitador** (lleva sus expedientes: decide, avanza por el árbol y genera los escritos · Seguimiento) · **Administrativo** (da soporte: sube documentos, notifica y vigila tareas y plazos · Tareas y subidas) · **Supervisor** (ve todos los expedientes, asigna y configura catálogos, plantillas y reglas · Control y Gestión) · **Administrador** (configuración técnica y operaciones delicadas · Control y Gestión) |
| 6 | **Un usuario, varios roles**: Tramitador y Supervisor; «Entra con [Supervisor ▾] y cambia cuando quiera» |
| 7 | **Ver: todos, todo** (catálogos, reglas, plantillas y expedientes ajenos) · **Actuar: según el rol** («se restringen los actos, no las miradas») |
| 8 | **¿Un expediente que no es suyo?** «se puede actuar, y queda en la bitácora» |

**Notas:** tramitador: lleva sus expedientes, genera escritos, avanza por el árbol.
Administrativo: da soporte, sube documentos al pool y vigila tareas y plazos (los plazos
ya los calcula BDDAT). Supervisor: ve todos los expedientes, asigna, supervisa usuarios y
configura catálogos y reglas. Administrador: configuración técnica y operaciones
delicadas (bajas físicas, archivado). Mínimo privilegio y permisos blandos. Mi trabajo
según el rol: cola de tareas (administrativo), seguimiento (tramitador), Control y
Gestión (supervisor). Se solapa con la 18 (roles, vistas y bitácora): al reordenar, una
de las dos absorbe a la otra.

**Fuente:** ficha 3 de octubre; ADR-012, ADR-013, ADR-017, ADR-028, ADR-029, ADR-038;
`app/modules/mi_trabajo/routes.py`.

**Estado (interno):** hecho.

---

## 20b. Un expediente de principio a fin — [propuesta, hueco] ✔ hecha (primer intento, sin revisar)

**Fichero:** `fichas/ficha_20b_recorrido.html`

La síntesis: liga las fichas con el procedimiento. Cada pieza ya se ha visto; aquí se ve
dónde actúa.

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | El procedimiento en siete etapas: Solicitud (entra por registro) › Análisis (¿está completa?) › Instrucción (en paralelo: Consultas, Información pública, Ambiental) › **Fin de instrucción** › Resolución (elaborar y firmar) › Notificación (a todos) › **Cierre** |
| 3 | «Lo que pone BDDAT», bajo Solicitud (entidades y roles · uno o varios actos · el reloj de cada acto empieza) y Análisis (requisitos según el proyecto · diagnóstico · requerimiento y su plazo) |
| 4 | Bajo Instrucción: un camino por organismo · anuncios y alegaciones · reformados: nueva versión |
| 5 | Bajo Fin de instrucción (certificado: la bisagra) y Resolución (plantilla con los datos · firma) |
| 6 | Bajo Notificación (un destinatario cada una · el canal, del justificante · cumplimiento y efectos) y Cierre (certificados de cierre · ¿en plazo?, acto por acto); «Después: recurso, modificación, explotación… es otra solicitud» |
| 7 | «De principio a fin»: Reglas e invariantes (en cada paso, con escape) · Estado calculado (árbol y listado) · Documentos (en el almacén, con fecha) · Bitácora (quién, cuándo, por qué) |

**Notas:** sirve de repaso antes del estado de desarrollo. Las etapas son las del RD
1955/2000 y la LPACAP para una autorización; la instrucción tiene más fases según el
caso (consulta al Ministerio, datos catastrales para la DUP…). Lo que viene después de
una solicitud resuelta y notificada es otra solicitud (invariante de la 10).

**Estado (interno):** —

---

## 19. Estado de desarrollo — ✔ hecha (primer intento, sin revisar)

**Fichero:** `fichas/ficha_19_estado.html` · título «Dónde estamos»

Una sola ficha para hecho, en curso y antes de producción; lo de después de producción
va en fichas propias (19b y siguientes).

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | **Hecho** (verde): estructura y árbol del expediente · reglas con escape e invariantes · plazos por acto, con su catálogo · certificados (fin de instrucción y cierres) · análisis de la solicitud y consultas · reformados de proyecto · notificaciones (destinatarios, fechas y edicto) · escritos desde plantillas y almacén · roles, listados y bitácora |
| 3 | **En curso** (azul): interfaz (inspector y listados homogéneos) · notificaciones: las pantallas que faltan (edicto, sede del solicitante, visibilidad) · fase de resolución de la DUP |
| 4 | **Antes de producción**: el resto de fases y lo particular de cada una · importar los expedientes de Access · almacén: lo que queda (exportar en ZIP, plantillas, PDF para firma, papelera) · proyección de plazos · puesta en producción (HTTPS, ENS, copias de seguridad, servidor) |
| 5 | Abajo, en discontinua: **Fuera de BDDAT, por ahora**: la firma (Port@firmas) y el envío de las notificaciones (Notifica-PNT, BandeJA): se sube el resultado |

**Notas:** sale de los «Estado (interno)» de este guion, de las fichas 10 y 11 de
octubre y de los documentos de estado vivos (`ESTADO_ADR049`, `ESTADO_ADR050`,
`ESTADO_ADR053`) a 16/10/2026. Si cambia algo antes de la presentación, se retoca la
lista en el propio HTML (un array al principio del script).

---

## 19b. Después de producción — [propuesta] ✔ hecha (primer intento, sin revisar)

**Fichero:** `fichas/ficha_19b_despues.html` · «mejoras que no hacen falta para funcionar»

Mapa de ideas en una rejilla de 3×3, una fila por clic. Las que tocan el procedimiento van
en recuadro oscuro y tienen ficha propia a continuación (19c a 19f).

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | **Firmar y notificar sin salir** · **Lo que vuelve, se coloca solo** · **El expediente que sale** |
| 3 | **Ver venir los vencimientos** · Avisos y encargos · **La instalación en el mapa** |
| 4 | Ayuda donde se trabaja · A hoja de cálculo · Titularidad en bloque |
| 5 | «las que tocan el procedimiento: se ven a continuación» |

**Notas:** son las nueve de la ficha 12 de octubre, agrupadas y con nombres de
procedimiento. «Lo que vuelve, se coloca solo» une dos piezas que ya existen a medias: el
código del pie (hoy solo comprueba el vínculo del requerimiento) y el registro manual de
los justificantes (el lector completo de Notifica-PNT está decidido, sin hacer). «Avisos
y encargos» amplía la bandeja de peticiones al supervisor que ya existe.

**Fuente:** ficha 12 de octubre; ADR-021; ADR-040; `PLAN_ESTRATEGIA.md` §A (bloques 6, 7,
13 y 14); `INVENTARIO_BACKEND.md` §12.

---

## 19c. Firmar y notificar sin salir de BDDAT — [propuesta, post producción] ✔ hecha (primer intento, sin revisar)

**Fichero:** `fichas/ficha_19c_firma_notifica.html`

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | **Hoy** («cada salida y cada vuelta pasan por una persona»): borrador listo para firma → a mano: alta en BandeJA y envío a Port@firmas → a mano: bajar el firmado y subirlo → a mano: alta en Notifica-PNT → a mano: bajar el justificante, subirlo y poner su fecha |
| 3 | **Después** («BDDAT hace los recados»): borrador listo → BDDAT lo envía a firma (azul) → vuelve solo: firmado, se reconoce por su pie y se coloca (verde) → BDDAT lo notifica al destinatario de la tarea (azul) → vuelve solo: justificante, fechas y resultado leídos (verde) |
| 4 | Píldoras: «actúa en nombre del funcionario, con sus credenciales» · «todo queda en la bitácora» · «el procedimiento no cambia: se ahorran pasos» |

**Notas:** une dos ideas de la 19b. Lo que ya está hecho la hace posible: el código del
pie, el destinatario guardado en cada notificación (lo que necesita un envío automático,
ADR-051) y las fechas que salen de los documentos (ADR-049). El automatismo usa un
usuario virtual que actúa con las credenciales del funcionario, de modo que en BandeJA y
Notifica consta quien de verdad actúa; solo añade, no cambia el modelo (ADR-021). Hay una
prueba de concepto de consulta de estado en Notifica-PNT.

**Fuente:** ADR-021; ADR-049; ADR-051; `DISEÑO_ECOSISTEMA_MANAGERS.md`.

**Estado (interno):** diseñado (ADR-021, implementación aparcada).
