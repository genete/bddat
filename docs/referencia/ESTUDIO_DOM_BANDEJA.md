# Estudio DOM BandeJA — envío de comunicaciones a Port@firmas

Estudio de campo del DOM de BandeJA (`https://extranet.chie.junta-andalucia.es/bandeja/`),
verificado con navegador real el 2026-08-04. Insumo para el issue gemelo de #659 (envío
automatizado a firma desde BDDAT) y para #728 (datos institucionales del órgano emisor:
consejería, sede, firmantes).

No depende del repositorio `bandeja-downloader` — ese repo tiene un fin propio (descarga de
documentos de comunicaciones recibidas) y documenta su propio flujo por separado
(`docs/ESTUDIO_DOM_BANDEJA.md` en ese repo). Este documento cubre el flujo de **alta y
envío** de comunicaciones, que es el que necesita BDDAT.

---

## 1. Login SSO y selección de puesto

- Navegar a `https://extranet.chie.junta-andalucia.es/bandeja/` → redirige a SSO
  (`ssoweb.juntadeandalucia.es/SAML2/SSOService.php?...`).
- Tras autenticar, redirige a `/bandeja/inicio/accesoSSO.action`: diálogo "Obligaciones
  para el uso del Sistema" → botón **"Aceptar"**.
- Si el usuario tiene más de un puesto de trabajo, aparece "Seleccione puesto de trabajo":
  `combobox` (`select#usuarioSeleccionado`) + botón **"Acceder"**. Con un solo puesto no
  aparece este paso.
- URL tras login: `/bandeja/modulos/bandejaTrabajo/inicio.action` (Bandeja de Trabajo).

## 2. Abrir "Alta de comunicación"

Menú superior → enlace **"Nueva comunicacion"** (texto visible "NUEVA COMUNICACIÓN",
`href="#"`, abre modal vía JS — no navega). Abre el modal con `heading "Alta de
comunicación"`.

## 3. Campos del modal "Alta de comunicación"

| Campo | Tipo | Notas |
|---|---|---|
| Asunto * | textbox | Obligatorio. |
| Registro de Procedimientos y Servicios (RPS) | combobox select2 (`#codigoRPAAltaComunicacion`) | Ver §4 — catálogo cargado a demanda, filtro en cliente. |
| Código expediente relacionado | textbox libre | **Campo libre**, no vinculado a ningún RPS ni validación. BDDAT usa hoy este campo para el número de expediente AT, pero al ser libre admite más de un dato si hiciera falta. |
| Pestaña DOCUMENTACIÓN / MENSAJE | tabs (`#adjuntarDocs` / `#textoDocumentos`) | Al menos una de las dos es obligatoria. |
| Incorporar documentos | file input + drop zone | Botón "Choose File" o soltar ficheros sobre la zona ("o suelte los documentos aquí"). |
| Destinos de la comunicación * | buscador + árbol (select2) | Obligatorio. Ver §5 — árbol completo de centros directivos, cargado a demanda. |
| ¿Solicitar respuesta a destinatarios? | toggle No/Sí + Fecha límite | Fecha en formato `dd-mm-aaaa`. |

Botones del pie: **Cancelar** / **Guardar borrador** / **Enviar sin firmar** / **Enviar a
Port@firmas**.

⚠️ **Las comunicaciones son permanentes**: una vez creadas (incluso "Guardar borrador") no
se pueden borrar, solo cambian de visibilidad en los filtros. Por eso, durante la
exploración de este flujo, siempre se ha cerrado el modal con "Cancelar" — nunca se ha
llegado a pulsar ninguno de los tres botones de envío con datos de prueba.

## 4. Catálogo RPS (Registro de Procedimientos y Servicios)

- Backend: `select id="codigoRPAAltaComunicacion"` (select2), 0 `<option>` en el DOM en
  reposo — **no viene precargado en el HTML**.
- Al primer clic/foco sobre el campo se dispara **un único** `POST
  /bandeja/modulos/bandejaTrabajo/cargarRPA.action` (sin body, CSRF por cabecera
  `x-csrf-token`). La respuesta trae el **catálogo completo**: 2.651 RPS agrupados en 19
  claves (una por consejería/agencia), ~1,6 MB de JSON.
- Escribir en el buscador (p.ej. "alta") **no** repite la llamada al servidor — select2
  filtra en cliente sobre lo ya cargado.
- Cada RPS trae: `codigoRPA`, `codigoSIA`, `nombre`, `nombrePantalla`, `codigoFamilia`,
  `familia`, `codigoMateria`, `materia`, `consejeria` (rótulo), `consejeriaDIR3`, `estado`,
  `vigente`, `fechaAlta`, `fechaBaja`.
- El grupo de nuestro dominio es la clave **"Consejería de Política Industrial y
  Energía"** (`consejeriaDIR3: A01041433`), 205 RPS. Es un **rótulo histórico** — no
  coincide con el nombre actual "Consejería de Industria, Energía y Minas"; el
  `codigoRPA`/`consejeriaDIR3` son los identificadores estables, el nombre de pantalla
  cambia con la legislatura (mismo síntoma que describe #728 sobre rótulos
  institucionales).
- **Volcado completo**: [app/data/bandeja_rps/rps_industria_energia_minas.csv](../../app/data/bandeja_rps/rps_industria_energia_minas.csv)
  (205 filas, ver README del directorio para más detalle). Pendiente de asociar cada
  `codigoRPA` relevante con el dominio de expedientes AT de BDDAT para autorrelleno.

## 5. Árbol de destinos (centros directivos)

- Backend: `POST /bandeja/modulos/bandejaTrabajo/obtieneArbolCentrosDirectivos.action`,
  disparado una vez al abrir el modal (igual patrón que el RPS: carga completa, filtro en
  cliente después).
- La respuesta trae el árbol de **toda** la Junta de Andalucía: 47 organismos raíz, cada
  uno con `id`, `text` (rótulo) e `inc` (hijos, recursivo).
- El nodo de nuestro dominio es `CPIE` — **"CONSEJERÍA DE INDUSTRIA, ENERGÍA Y MINAS
  (IND)"** —, subárbol de 73 nodos: servicios centrales (D.G. Minas, S.G. Energía, S.G.
  Industria y Minas, Secretaría General Técnica, Viceconsejería) y servicios periféricos
  por las 8 provincias, cada uno con sus departamentos internos (energía, industria,
  minas).
- **Doble uso del campo destino** (explicado por Carlos): cuando la comunicación va a un
  **tercero externo** a la Junta se selecciona ese tercero; pero para el envío a
  **Port@firmas** el destino que se usa es el **propio servicio emisor**, de forma que la
  respuesta (ya firmada) vuelve como comunicación **entrante** y puede asignarse a
  cualquier compañero del servicio, no solo a quien la creó.
- **Volcado completo**: [app/data/bandeja_destinos/destinos_industria_energia_minas.csv](../../app/data/bandeja_destinos/destinos_industria_energia_minas.csv)
  (73 filas, jerarquía aplanada con `nivel`/`padre_id`/`ruta`). Nota de calidad: 7 de los
  73 nodos llegan con `id` vacío en el JSON de origen (ver README del directorio).
- **Selección de destino (para automatizar)**: escribir en el buscador filtra sobre **todo**
  el árbol (no solo la raíz) y muestra la ruta completa hasta el nodo encontrado. El nodo
  hoja es un `<span onclick="javascript: seleccionarDestino('<indice>')"
  name="<texto exacto del destino>">`. Esa función es solo de UI: añade la clase
  `destinoSeleccionado` y un chip visual a `#destinosSeleccionados` usando el texto
  visible — **no** usa el `id` estable del árbol (p.ej. `SVENERGCA`).
  ⚠️ **El `<indice>`** (formato `"<raíz>-<hijo>-<nieto>"`, p.ej. `"35-6-2"`) es una **ruta
  posicional** dentro del array JSON de esa carga concreta, no un identificador estable —
  no debe hardcodearse en un script. Para automatizar: localizar en cada carga el
  `span[onclick*="seleccionarDestino"]` cuyo atributo `name` coincide con el texto exacto
  del destino buscado, y usar el índice que tenga en ese momento.
  Verificado en vivo el 2026-08-04 seleccionando "SV. ENERGIA (IND) (CADIZ)" (coincide con
  el servicio del usuario de prueba, `SVENERGCA` en el CSV).

## 6. Envío a Port@firmas: documentos y firmantes

Al pulsar **"Enviar a Port@firmas"** se abre un segundo modal, "Enviar petición a
Port@firmas", con tres bloques.

### 6.1 Selección de documentos

Tabla con checkbox "FIRMAR" por documento (`input.documentosFirmables`) + columna NOMBRE.
En la comunicación de prueba solo había un documento autogenerado, **"Extracto de la
comunicación.pdf"** — el PDF que representa el asunto+mensaje de la comunicación. En un
caso real sería el oficio/resolución subido como adjunto.

### 6.2 Selección de firmantes — el campo de búsqueda fiable es el DNI, no el nombre

- Campo "Buscar..." + botón BUSCAR + pestaña "FIRMANTES RECIENTES". ⚠️ Pulsar BUSCAR sin
  texto devuelve **miles de usuarios** (todo el directorio) — no usar así.
- Buscar por **nombre** puede dar **homónimos**: probado en vivo con "ISABEL DIAZ ROMERO"
  → 2 resultados, personas distintas en organismos distintos (una en Jaén/Igualdad, otra
  en Cádiz/Industria — la buscada). Hay que desambiguar por la columna ORGANISMO.
- Buscar por **DNI** (probado con el DNI del usuario de prueba) da **un resultado único**.
  **Es el campo fiable para automatizar** el catálogo de firmantes de #728 — no el nombre.
- Cada fila de resultado expone el identificador real vía
  `<tr ondblclick="javascript:addFirmante('<codigoFirmante>',<indice>);">` (también hay un
  `<img onclick="javascript:addFirmante(...)">` con el mismo valor). `codigoFirmante` tiene
  formato **`DNI|idInterno|`** (p.ej. `52264394E|7015410|`, o `75810782E|W204204571|` para
  otro firmante — el `idInterno` puede ser numérico o alfanumérico). Ese `idInterno` es el
  identificador estable de BandeJA para la persona+puesto — el dato a guardar en el
  catálogo de firmantes, no solo el DNI (una persona puede tener más de un puesto).

### 6.3 Firmantes del documento — orden y tipo de firma

Tabla con columnas Orden / Nombre / Puesto de trabajo / Organismo / **Tipo de firma**
(`<select name="tipoFirma">`, opciones `F` = Firma, `VB` = Visto Bueno).

- **El orden de arriba a abajo es el orden real de firma**: el/los Visto Bueno van
  siempre primero, la Firma (o cadena de firmas) va después. Nunca al revés — se añade en
  ese orden, no se reordena después.
- ⚠️ **Al añadir un firmante nuevo, todos los `tipoFirma` ya puestos se resetean a
  "Firma" (`F`)**. Confirmado en vivo: si se fija un Visto Bueno y luego se añade otro
  firmante, el Visto Bueno ya puesto vuelve a "Firma". Por eso el orden correcto de
  trabajo es: **añadir primero a todos los firmantes en su orden final, y solo al final —
  con la cadena completa — marcar cuáles son Visto Bueno**. Fijarlo antes es papel
  mojado.
- Prueba en vivo 2026-08-04: cadena de 2 — Carlos López González (posición 1, **Visto
  Bueno**) → Isabel Díaz Romero (posición 2, **Firma**) —, destino SV. ENERGIA (IND)
  (CADIZ) (el propio servicio, ver §5), enviada a Port@firmas de verdad. Resultado en §7.

## 7. Comunicación resultante — Comunic. recibidas / Comunic. enviadas

Tras enviar, el modal se cierra y vuelve al listado principal de la Bandeja de Trabajo, que
tiene dos áreas: **Comunic. recibidas** y **Comunic. enviadas**. Una comunicación creada y
enviada a Port@firmas aparece de entrada solo en **Comunic. enviadas** — hasta que vuelva
firmada, no está en recibidas (coherente con §5: el destino usado para Port@firmas es el
propio servicio, así que la vuelta sí generará una entrada en recibidas más adelante).

Prueba real 2026-08-04: la comunicación de §6.3 aparece en Comunic. enviadas con código
**`INT/2026/0000000002141695`**, origen `SV. ENERGIA (IND) (CADIZ)`, estado **"PENDIENTE
DE FIRMA"**. El estado confirma que el envío desde BandeJA solo pone la comunicación en la
cola de Port@firmas — la firma real ocurre en Port@firmas (sistema externo), no en
BandeJA. `INT/` es el prefijo de código para comunicaciones internas (mismo organismo
origen y destino), a diferencia de `EXT/` visto en otras filas del listado.

## 8. Cómo capturar el código de la comunicación recién creada (para automatizar)

Necesidad real de #728/gemelo-659: tras enviar desde BDDAT, hace falta el **código** de la
comunicación creada (el `INT/...`) para poder localizarla después. Se descartaron dos
caminos y se confirmó un tercero.

### 8.1 Filtro "Enviadas por mí" + fecha — insuficiente en solitario

En el sidebar de "Comunic. enviadas" hay checkbox **"Enviadas por mí"** (filtra en
**cliente**, no repite llamada al servidor — usa columnas ocultas del `<tr>`, ver más
abajo) + selector de **rango de fechas** con preset "Hoy". Combinados, filtran al
instante. Pero **no bastan por sí solos** para identificar una comunicación concreta: si en
el futuro el mismo usuario dispara varios envíos desde BDDAT el mismo día (o usa BandeJA
para otra cosa aparte de BDDAT ese día), el filtro puede devolver **más de una fila**.
Necesario, pero no suficiente.

### 8.2 ID interno en el `onclick` — curiosidad técnica, no el dato a priorizar

Cada fila del listado de enviadas tiene, en las imágenes de acción ("Información
detallada", "Vincular", "Evolución", "Anular"), un `onclick="abrirModal('info','<id>')"`
con un **ID interno numérico** (p.ej. `16229229`) distinto del código `INT/...` visible.
Se comprobó exportando el listado a CSV que **ese ID no aparece en la exportación** — solo
vive en el DOM.

Verificado en vivo 2026-08-04: el ID **persiste dentro de la misma sesión** ante un cambio
de estado real — `16229229` fue el mismo antes y después de que la comunicación pasara de
"PENDIENTE DE FIRMA" a "PENDIENTE" al firmarla en Port@firmas y forzar "ACTUALIZAR ESTADO"
(§8.4). Sigue sin comprobarse si persiste **entre sesiones de login distintas** (hipótesis
de Carlos: no persiste ahí) — no es bloqueante porque, dentro de una misma sesión de envío
automatizado, el diff de §8.3 ya resuelve la captura sin necesitar este ID.

**Aclaración de Carlos (importante, corrige el énfasis de esta sección)**: el ID interno
no es el dato que importa. Lo que importa para BDDAT es el **código `INT/...`**, porque es
el valor que **el usuario humano puede usar** si necesita localizar la comunicación a mano
(buscarla en BandeJA, referenciarla en una conversación, etc.) — y es único. El ID interno
no tiene ningún uso de cara al usuario, solo sirve para las llamadas JS internas de
BandeJA. §8.3 (diff de listado) es por tanto **el método a implementar**; este §8.2 queda
como nota técnica de contexto, no como alternativa a considerar.

**Nota aparte sobre la exportación a CSV** (botón "Exportar", probado sin querer como
efecto colateral): mismas columnas que el DOM (visibles + 3 ocultas: remitente, destino
entre corchetes, estado entre corchetes) — no aporta nada que no esté ya en el DOM. Ojo si
se automatiza: viene en **Windows-1252/Latin-1**, no UTF-8, y con entidades HTML sin
decodificar en la cabecera (`Creaci&oacute;n`).

### 8.3 Método confirmado: diff del listado filtrado antes/después del envío

El camino robusto, verificado en vivo 2026-08-04:

1. Antes de crear la comunicación, con el filtro "Enviadas por mí" + fecha de hoy activo
   en **Comunic. enviadas**, guardar la lista de códigos `INT/...` visible (en la prueba:
   `[2141695]`).
2. Abrir **"Nueva comunicación" desde la propia vista de Enviadas** (el enlace existe
   también ahí, no solo en la Bandeja principal) y completar el envío a Port@firmas.
3. Al volver, el filtro sigue activo **sin necesidad de reaplicarlo** y la lista ya
   incluye la fila nueva arriba del todo (orden por fecha de creación descendente): en la
   prueba, `[2141700, 2141695]`.
4. El código nuevo es el que no estaba en el paso 1: `INT/2026/0000000002141700`. Estado
   nada más enviar: **"BORRADOR"** (no "PENDIENTE DE FIRMA" todavía — hay un margen antes
   de que el backend lo procese; aparece un toast: *"Las comunicaciones se han creado
   correctamente y se han enviado los documentos seleccionados a Port@firmas."*).

Es el método a replicar en la automatización: memorizar el listado filtrado justo antes de
enviar, comparar justo después, quedarse con la fila nueva.

### 8.4 Modal "Información detallada" (enviadas) y ciclo de estados tras la firma

Se abre con doble clic en la fila, o con el icono "Información detallada" de la columna
Estado (oculto hasta hover: `div.acciones` con `style="display: none;"`, contiene también
"Vincular", "Evolución"/"Anular" según el estado). Automatizable en JS directamente vía
`abrirModal('info', '<id>')` con el ID interno de §8.2, sin necesidad de hover real.

Campos mostrados: Origen, Destino, Remitente (nombre + puesto), Asignada a, Asunto,
Mensaje, **Registro de Procedimientos y Servicios**, Expediente relacionado, Fecha límite,
Número de registro, pestañas DOCUMENTACIÓN ASOCIADA / NOTAS, tabla de documentos
(Fecha/Nombre/Abrir) + enlace "Descargar documentos".

**RPS mostrado en el detalle**: el texto de RPS que aparece en el modal de detalle
("Autorización de explotación para instalaciones de distribución y transporte
secundario...") lo introdujo Carlos a mano al crear la comunicación de prueba — no es un
valor por defecto de BandeJA ni relleno automático del modal. Aclaración de Carlos, importante
para #757: el campo **no lleva asterisco** (no es obligatorio en el formulario), pero **sí
importa usarlo bien** — precedente real de una auditoría que detectó el mismo código de
RPS reutilizado indiscriminadamente para todo. No vale dejarlo vacío por sistema ni poner
uno cualquiera solo porque el formulario lo permite.

**Botón "ACTUALIZAR ESTADO"**: fuerza una relectura del estado real en Port@firmas en el
momento, sin esperar al proceso de fondo que sincroniza BandeJA con Port@firmas
periódicamente (lo que Carlos anticipó: "hay un backend que va leyendo el estado de
Port@firmas en background y actualizando bandeja poco a poco. Pero es forzable"). Probado
en vivo: tras firmar de verdad en Port@firmas y pulsar "ACTUALIZAR ESTADO", el estado pasó
de **"PENDIENTE DE FIRMA" a "PENDIENTE"** (toast: *"La comunicación se ha actualizado
correctamente."*), el documento pasó a llamarse `58566692_DocGenerado.pdf` (nombre distinto
al `Extracto de la comunicación.pdf` original — el documento se regenera/sustituye tras el
procesado), y el desplegable "MÁS ACCIONES" perdió la opción "ANULAR" en favor de solo
"EVOLUCIÓN" (coherente con que ya no está pendiente de firma). El ID interno del `onclick`
se mantuvo igual (§8.2).

## 9. Pendiente de documentar

- Formato exacto esperado en "Código expediente relacionado" si se decide usarlo para más
  de un dato (hoy solo se ha confirmado que es campo libre, sin formato impuesto).
- Qué significa exactamente el estado **"PENDIENTE"** post-firma (¿pendiente de asignar?
  ¿pendiente de otra cosa?) y qué aspecto toma cuando aparezca también en **Comunic.
  recibidas** — no observado todavía en esta sesión.
- Si el ID interno del `onclick` (§8.2) persiste entre sesiones de login — no verificado
  (sí se confirmó que persiste ante un cambio de estado dentro de la misma sesión).
