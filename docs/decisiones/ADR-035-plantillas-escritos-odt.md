# ADR-035 — Plantillas de escritos en ODT con renderizador propio, no DOCX con docxtpl

**Estado:** Adoptada
**Fecha:** 2026-07-30
**Issues:** #182 (de donde sale la evidencia), #167 / #277 (motor de generación)
**Implementan esta decisión:** #726 (renderizador ODT), #727 (plantilla base canónica),
#728 (datos institucionales del órgano emisor)
**Relacionado:** ADR-021 §4 (datos a catalogar: unidades firmantes), ADR-025 (Context
Builders), #181 (inspección automática), #552, #553
**Documento de diseño:** `docs/referencia/DISEÑO_GENERACION_ESCRITOS.md`

---

## Contexto

La sesión de #182 (2026-07-30) medía si un código de trazabilidad embebido en el escrito
sobrevive al pipeline `.docx → Writer → PDF → BandeJA → Portafirmas`. La respuesta está
en el documento de diseño y en el propio issue: sobrevive **sólo el texto renderizado en
la página**; todos los canales de metadatos mueren.

Por el camino se midió algo que no se buscaba, y que abre esta decisión: **ninguno de los
mecanismos de protección de OOXML sobrevive a que Writer guarde el fichero.** Se probaron
tres, con el resultado siguiente:

| Mecanismo declarado en el `.docx` | Tras abrir y guardar en Writer |
|---|---|
| Protección de campos (`w:documentProtection`) | desaparece |
| Bloqueo de forma (`a:spLocks`) | desaparece |
| Anclaje bloqueado (`locked="1"`) | pasa a `locked="0"` |

LibreOffice no exporta las protecciones a OOXML. Con el bloqueo declarado, todos los
cuadros de texto se pudieron seleccionar, mover, editar y borrar. La conclusión no es que
falte una opción: es que el formato intermedio impide expresar lo que se quiere expresar,
porque en el camino hay una traducción entre dos modelos distintos.

De ahí la pregunta que este ADR contesta: si el editor es Writer y el destino es un PDF,
¿qué aporta pasar por un formato ajeno a los dos?

### Lo medido en ODF

Prueba de concepto ejecutada en la misma sesión (`docs_prueba/temp/odt_0*.py`, fuera de
git): plantilla con cuadros de texto en cabecera y pie, primera página distinta, dos
fragmentos multipárrafo con formato propio, bucle de filas de tabla y código de
seguimiento inyectado en el margen.

| | `.docx` con docxtpl | `.odt` con renderizador propio |
|---|---|---|
| Tokens en el XML | troceados en runs; docxtpl los recompone | **enteros**, texto plano |
| Cabeceras y pies | `word/header*.xml`, `word/footer*.xml` | `styles.xml` (master pages) |
| Primera página distinta | `titlePg` + partes separadas | master pages enlazadas, mecanismo nativo |
| Protección de objetos | no sobrevive nada | `style:protect` conserva `position size` |
| Fragmentos multipárrafo | se insertan **dentro** del párrafo → párrafos anidados que Word descarta; hay que parchear el ZIP | **sustituyen** al párrafo del marcador; no hay nada que reparar |
| Tokens dentro de un fragmento | no se rellenan | **se rellenan** (fragmentos antes de Jinja2) |
| Dependencias | `docxtpl`, `python-docx`, `docxcompose` | ninguna nueva: `zipfile` + `lxml` + Jinja2 |

Los dos parches que hoy existen en el generador por culpa de docxtpl/docxcompose
—`_elevar_parrafos_anidados` y `_corregir_anidados_en_zip`, unas 100 líneas— dejan de
tener razón de ser. No porque ODF sea más benévolo (tampoco admite un párrafo dentro de
otro), sino porque **la inserción la escribimos nosotros** y se hace a nivel de bloque.

---

## Decisión

### 1. Las plantillas de escritos se hacen en `.odt`

Y con ellas los fragmentos insertables. No hay plantillas en producción y las de
desarrollo son prescindibles: se rehacen en el formato nuevo.

### 2. Se escribe un renderizador ODT propio; el motor `.docx` se conserva

No se reescribe el existente. Se añade un motor hermano y la elección se hace **por la
extensión de `plantilla.ruta_plantilla`** — sin columna nueva ni migración.

Conservar el camino `.docx` cuesta dos motores que mantener y compra dos cosas: permite
migrar plantilla a plantilla en vez de de golpe, y deja una vía de vuelta si el motor
nuevo falla en algo no previsto. Se retira cuando no haya prisa.

### 3. El renderizador nace con el gancho de inyección del código

Aunque el código de seguimiento sea materia de #182, el motor debe exponer desde el
principio el punto donde se inyecta. Escribirlo sin ese hueco obliga a abrirlo dos veces.

**La inyección debe recorrer todas las master pages.** En la prueba, con primera página
distinta, el código no apareció en la página 1: se insertó en el pie de una master page y
la primera usaba otra. Es el equivalente a recorrer todas las secciones en OOXML.

Los **tokens** no tienen ese problema: Jinja2 procesa `styles.xml` completo de una pasada,
así que llegan a todas las cabeceras y pies.

### 4. Reparto entre token, fragmento y plantilla

Regla de decisión, derivada del análisis caso a caso de los contenidos reutilizables
reales (logo, datos de sede, rótulo de consejería, párrafos estandarizados):

| Lo variable es… | Mecanismo | Casos |
|---|---|---|
| Un bloque con estructura propia, en el flujo del cuerpo | **Fragmento** | Fundamentos de derecho, pie de recurso |
| Un valor dentro de una estructura que la plantilla ya tiene | **Token** | Sede, consejería, provincia, órgano |
| Nada, en la práctica | **Parte de la plantilla** | Logo |

- **El logo no es token.** Vive en la cabecera de la master page, viaja con la plantilla y
  el renderizador no lo toca: cero código. Hacerlo token exigiría gestionar el fichero de
  imagen, la carpeta `Pictures/`, el `manifest.xml` y el dimensionado, para algo que ha
  cambiado dos veces en la historia de la Junta. Se asume una década de vigencia.
- **Los cuadros de texto de cabecera y pie llevan tokens, no fragmentos.** Medido: el
  cuadro ya dibujado en la plantilla, con `{{ organo }}` o `{{ sede.direccion }}` dentro,
  se rellena como cualquier token — es sustitución de texto en `styles.xml`. Lo difícil
  (el cuadro, su posición, su formato) es de la plantilla; lo variable es sólo el texto.
- **Los fragmentos son para párrafos estandarizados del cuerpo**, donde la
  homogeneidad entre escritos es lo que se persigue.

### 5. Plantilla base canónica, con validación en el alta y marca de versión

Ninguna plantilla nace de un `.odt` en blanco: **todas derivan de una plantilla base** que
define la hoja de estilos y, en particular, **declara las fuentes explícitamente**.

El motivo se midió: si el estilo no declara fuente y LibreOffice la resuelve del tema
(Calibri → Carlito), el PDF **se ve bien** pero su texto extraíble sale con los acentos
descompuestos — `'Cá \x03diz, Consejerí\x03á'` en vez de `'Cádiz, Consejería'`. Con la
fuente declarada, limpio. El paso por ODT no influye; se comprobó por separado. Afecta a
#181, a la búsqueda de texto del usuario sobre el PDF y a lo que se lleva quien copie y
pegue del documento.

La base resuelve además el único cabo serio de los fragmentos: si plantillas y fragmentos
comparten hoja de estilos, no hay que fusionar estilos al insertar. Los dos problemas
tenían la misma raíz —cada documento traía sus propios estilos— y la misma solución.

Dos piezas, con funciones distintas:

- **Marca de versión** en `meta.xml` (`meta:user-defined`), que dice de qué base deriva la
  plantilla. Medido: sobrevive a que Writer abra y guarde.
- **Validación en el alta**, que decide si la plantilla entra. Comprueba lo que importa —
  que se declaren las fuentes, que existan los estilos que los fragmentos esperan— y se
  engancha donde ya se valida la sintaxis (`admin_plantillas/routes.py`).

La marca **no es la puerta**: se hereda al copiar y sobrevive aunque el supervisor cambie
la fuente a mano después. Dice de dónde viene, no si cumple. Y frena descuidos, no a
alguien decidido: copiar dos líneas de `meta.xml` es trivial. No es un control de acceso.

### 6. Lo que no cambia

La capa de contexto es agnóstica del formato: `ContextoBaseExpediente`, los Context
Builders (ADR-025) y las consultas nombradas producen un diccionario. No se tocan. Tampoco
la lógica de pool, el protocolo `bddat-explorador://` ni el reparto de responsabilidades
del modal de generación.

---

## Requisitos que esta decisión impone

1. **LibreOffice pasa a ser requisito de instalación de BDDAT**, con la asociación nativa
   de `.odt`. Coste cero: software libre.
2. **Las condiciones de uso advierten** de que un `.odt` que se vaya a devolver a BDDAT no
   se abra con Word. Quien tenga Word o Office 365 queda avisado; no se soporta ese
   camino.
3. **El flujo legado deja de funcionar** al entrar BDDAT en producción: la combinación de
   plantillas desde la base de datos Access requiere MS Office 2000. No es un efecto
   colateral a mitigar, es un objetivo — la presión por esas licencias es una de las
   motivaciones del proyecto, y hay personas del servicio que no tienen acceso a esa base
   de datos.

---

## Fuera de esta decisión

- **Dónde se coloca el código de seguimiento.** Sin decidir. Dos candidatos, ambos
  supervivientes del circuito: margen izquierdo en vertical (único sitio que el
  portafirmas no reclama, exige cuadro girado) y pie de página sin giro (más legible,
  previsiblemente más simple de insertar). Detalle en el documento de diseño.
- **Si el código va en todas las páginas o sólo en la primera.**
- **El formato exacto del código**, que debe llevar id de instancia (#711) y dígito de
  control (#182).
- **Los datos institucionales** que los tokens de cabecera y pie necesitan —sede,
  consejería, provincia, firmantes— no existen hoy en BDDAT. Van en #728; los firmantes
  ya estaban identificados en ADR-021 §4. No bloquean al renderizador.
- **Fragmentos e imágenes en el render**: la inserción de fragmentos está probada, pero
  la fusión de estilos entre documentos con hojas distintas y el equivalente ODF de
  `InlineImage` quedan para la implementación, y puede que el segundo no haga falta si las
  imágenes viven en el estilo de página.

---

## Por qué

- **El formato intermedio era el que impedía proteger.** No es que falte una opción en
  Writer: es que la traducción a OOXML descarta lo que se quiere declarar. En su formato
  nativo no hay traducción, y sobrevive lo que se declara — parcialmente, pero sobrevive.
- **El editor es Writer y el destino es un PDF.** OOXML no es ni el formato del editor ni
  el del resultado: es un tercero que sólo añade una traducción en cada extremo.
- **Escribir el motor sale más barato que sufrir el ajeno.** docxtpl obliga a parchear el
  ZIP para reparar lo que él mismo rompe. El renderizador ODT de la prueba hace más
  —fragmentos con tokens dentro— con menos código y sin dependencias nuevas.
- **Dos motores en paralelo, no una abstracción común.** docxtpl impone su modelo
  (`Subdoc`, `InlineImage`) y ODF el suyo; una interfaz única sería un traductor entre dos
  cosas que no se parecen. Dos funciones hermanas con la misma firma y una elección
  explícita por extensión.
- **La plantilla base no es burocracia.** Sin ella, cada plantilla trae su hoja de
  estilos, y de ahí salían dos defectos distintos: los acentos descompuestos en el texto
  extraíble y la fusión de estilos al insertar fragmentos.

---

## Consecuencias

- Tres issues de implementación: **#726** (renderizador ODT), **#727** (plantilla base
  canónica con su validación) y **#728** (datos institucionales del órgano emisor). Sólo el
  primero bloquea a #182.
- #182 se apoya en el renderizador: su parte de inyección depende del formato y se
  tiraría si se hiciera ahora sobre `.docx`. Sus otras dos piezas —composición del código
  y extracción del PDF— son agnósticas, pero no sirven sin la primera.
- #181 mejora por partida doble: el código embebido le da certeza donde hoy tendría
  heurísticas, y las plantillas con fuente declarada le dan un texto extraíble limpio.
- El alta de plantillas (`admin_plantillas`) cambia en varios puntos: navegador de
  ficheros del servidor, validación de sintaxis, panel de tokens y textos.
- Las plantillas y fragmentos de desarrollo se rehacen. No hay migración de datos.
- El PDF que entra en BandeJA es indiferente al formato intermedio: el circuito externo no
  se ve afectado por esta decisión.

---

## Alternativas descartadas

### A. Seguir en `.docx` y renunciar a proteger el código

Es lo que había. Descartada porque el motivo original —que el tramitador no rompa el
código sin querer— no tiene ninguna respuesta en OOXML, y porque el resto de las ventajas
del ODT (tokens enteros, fragmentos sin parches, tokens dentro de fragmentos) se pierden
con ella.

### B. Abstraer los dos formatos bajo una interfaz común de plantilla

Descartada: los modelos de docxtpl y de ODF no se parecen, y la abstracción sería un
traductor entre ambos. Dos motores hermanos con elección por extensión es más simple y
deja el camino existente intacto.

### C. Usar un motor de plantillas ODT de terceros (`appy.pod`, `relatorio`, `py3o.template`)

No descartada por principio, pero innecesaria para el alcance actual: la prueba de
concepto cubre tokens, bucles de fila, fragmentos e inyección sin dependencias nuevas. Se
reconsidera si aparece una necesidad que salga caro implementar (condicionales complejos,
composición de documentos).

### D. Convertir el logo en token para poder cambiarlo en un sitio

Descartada por Carlos: obliga a montar la maquinaria de inserción de imágenes para algo
que cambia dos veces por siglo. La variante intermedia —imágenes enlazadas a un fichero
único en `PLANTILLAS_BASE/recursos/`, no incrustadas— queda anotada pero no probada, y
tiene el inconveniente de que el logo no viaja con el `.odt` y desaparece si la ruta no
está accesible.

### E. Meter los cuadros de cabecera y pie como fragmentos

Descartada tras medirlo: insertar contenido multipárrafo dentro de un cuadro de texto que
vive en una master page es la combinación más incómoda posible, y no hace falta. El cuadro
lo dibuja la plantilla y su texto es un token.
