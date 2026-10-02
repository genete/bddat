# ADR-050 — BDDAT, único dueño de los ficheros: almacén privado direccionado por contenido y edición sin acceso al servidor de ficheros

**Estado:** Adoptada — en implementación: fase 0 hecha (#1000, #1001, §M revalidada y los issues de las fases creados el 2026-10-02); próxima, la fase 1 (#1007). Se implementa **después de N6** (cierre de la cadena de ADR-049) y **antes de producción** (§I)
**Fecha:** 2026-09-25 · **Enmendada:** 2026-09-26 — **sin sistema de versiones** en ningún sitio: un documento apunta a un fichero y editarlo lo sustituye (§C, §F); el PDF para firma es un documento sincronizado con su borrador (§D); una sola plantilla vigente en BDDAT, con el versionado a cargo del supervisor y la trazabilidad por hash (§J); «Guardar como» (§D), el mismo fichero en otro expediente (§H) y qué fichero subir (§E) · **Enmendada (revisión de diseño), mismo día:** el almacén se habla desde un puerto agnóstico, con la identidad de almacenamiento (`ref`) separada de la identidad de contenido (`contenido_sha256`, calculada por BDDAT) — pensado para poder sustituir el adaptador de filesystem por un gestor documental corporativo el día de mañana (§B, §C); manifiestos particionados por año de solicitud (§H); el buzón por usuario se aparca hasta que haya métricas que lo justifiquen (Alternativas) · **Enmendada (salvaguardas de riesgo), 2026-10-01:** la edición por WebDAV se prueba en un puesto de la Junta en la fase 0 y la fase 1 no empieza sin ese resultado (§D, §I); el manifiesto y el exportador pasan a la fase 1, el exportador lee solo el manifiesto y funciona sin BDDAT, y los manifiestos se rehacen de noche y antes de cada exportación (§H); solo el subsistema de almacenamiento ve `ficheros` y la `ref`, y desde ya no entran consumidores nuevos del modelo de rutas (§B, §I); la migración es de ida, sin camino de vuelta (§L, Alternativas O) · **Enmendada (prueba en un puesto de la Junta, #1000), 2026-10-01:** el botón «Editar» usa `vnd.libreoffice.command:`, que registra el LibreOffice corporativo, sin instalador en el cliente; `HEAD` entre los verbos, el dueño del bloqueo es el nombre del tramitador y la carpeta del token responde con y sin barra final (§D); puerta de la fase 1 pasada (§I) · **Enmendada (revalidación de §M, fase 0), 2026-10-02:** la fase 1 absorbe la 2 y la 3 — corta a la vez todos los escritores de rutas, vincular deja de mover, y en el mismo issue se retiran el modelo de rutas y los botones de carpeta, que tras la migración no quedan en pie (§I); la papelera pasa a la fase 7, con el documento a la vista y marcado hasta el borrado definitivo, y la bitácora de la limpieza guarda la `ref` de lo borrado (§G); el motor de Word se retira en la fase 4 (§J); §M revalidada
**Sobrepasa:** ADR-032 §1-§4 (entrada al pool, rutas relativas en `Documento.url`, movimiento al vincular, naming con MD5 en `pool/`). ADR-032 no queda derogado: describe lo que hay implementado hasta que este ADR se ejecute, y su nota de cabecera lo remite aquí
**Amplía:** ADR-006 (el esquema «ruta local» de `documentos.url` desaparece; `http(s)://` y `bddat://` siguen) · ADR-035 (plantillas y fragmentos pasan al almacén y se suben desde el navegador; §6 «lo que no cambia» deja de ser cierto en lo del pool y del protocolo `bddat-explorador://`; el motor `.docx` que conservaba §2 se retira, §J)
**No cambia:** ADR-010 (N:M documento-tarea) · ADR-027 (pertenencia al expediente por naturaleza, no por mecanismo de almacenamiento) · ADR-044 (reformados como documentos aparte) · el sellado de ADR-036 y de #947 (§F se apoya en él)
**Origen:** discusión del 2026-09-25 a raíz de #953 (validador de `Documento.url` dependiente del sistema operativo), revisada el 2026-09-26
**Evidencia:** prueba de concepto en [`scripts/poc_webdav/`](../../scripts/poc_webdav/README.md): LibreOffice 24.2 abriendo, bloqueando y guardando un `.odt` contra un WebDAV mínimo en Flask; y los tres casos de «Guardar como» de §D, probados contra ella el 2026-09-26; y la prueba en un puesto de la Junta del 2026-10-01 (#1000), con el LibreOffice corporativo 7.6, contra la IP de red y desde una segunda máquina por la VPN
**Relacionados:** #151 (carpetas y permisos pedidos a Informática, comentario del 2026-09-25, corregido el 2026-10-01: dos carpetas, sin buzón) · #573 (remisión del expediente con índice, distinta de la exportación de §H) · #852 (resiliencia del share, sigue vigente) · #853 (`explorer /select` en el servidor, lo absorbe la fase 1) · #193 y #444 (cerrados el 2026-10-02: los dejan sin objeto la integridad de la fase 7 y la retirada de Word de la fase 4) · #330 (entornos y despliegue) · #954 (sellado de datos en el pool) · N009, N021, N077
**Issues de implementación:** fase 0 — #1000 (prueba de la edición WebDAV en un puesto de la Junta, puerta de la fase 1; pasada el 2026-10-01) y #1001 (congelar los consumidores del modelo de rutas; hecho el 2026-10-02, PR #1003) · fase 1, que absorbe la 2 y la 3 — #1007 · fase 2b — #1008 · fase 4 — #1009 · fase 5 — #1010 · fase 6 — #1011 · fase 7 — #1012

---

## Contexto

### Cómo funciona hoy

Un documento pasa por tres estados (ADR-032):

1. Está fuera de BDDAT: en el disco del usuario, en una carpeta de red, recién descargado de una plataforma.
2. Entra por un ingestor y se copia a `AT-N/pool/<prefijo-md5>_<nombre>`, bajo `FILESYSTEM_BASE`. O se registra «in situ», sin copiarlo, donde el usuario lo dejó.
3. Al vincularse a una tarea se **mueve** del pool a una carpeta ESFTT legible (`AT-N/<solicitud>/<fase>/<trámite>/<tarea>/`), con sufijos si el nombre choca. Si pierde su último vínculo, vuelve al pool.

`Documento.url` guarda la ruta relativa. Los ficheros no van a la BD por su tamaño, y se dejaron en una carpeta de red para que el usuario pudiera **retocar el `.odt` en Writer** antes de pasarlo a PDF y firmarlo. De ahí la obligación de que todo usuario tenga acceso de escritura al servidor de ficheros, además de a la aplicación.

### Qué falla, con evidencia del código

Todos los problemas salen de la misma decisión: **la identidad del documento es una ruta dentro de una carpeta en la que los usuarios pueden escribir.** Hay dos fuentes de verdad, la BD y el disco, que se pueden separar sin que nadie lo detecte.

- **Puerta trasera.** Cualquier usuario puede borrar, renombrar o sustituir un fichero de un expediente desde Windows. BDDAT solo lo descubre cuando alguien intenta abrirlo, y no hay garantía de recuperarlo.
- **Integridad.** Los documentos registrados in situ no tienen hash (`hash_md5` es nullable precisamente para ellos): un PDF firmado se puede cambiar por otro con el mismo nombre sin que nada lo note. `pool_editar_documento` permite cambiar la `url` de un documento, y el fichero anterior desaparece del mapa sin rastro.
- **Ficheros huérfanos.** `pool_borrar_documento` borra la fila pero deja el fichero. `regeneracion_escritos._apartar_fichero_anterior` aparta con sufijo de fecha ficheros que ya no referencia nadie.
- **Complejidad que solo existe porque el fichero se mueve y su nombre importa:** el patrón copiar → commit → borrar; el caso de dos documentos que comparten fichero (#926); los sufijos por colisión; la matriz de 8 casos de la regeneración (#730); el viaje de vuelta al pool al desvincular.
- **Rutas entre plataformas:** #953, #699, los nombres reservados de Windows y el límite de 260 caracteres, que las rutas ESFTT profundas bajo `\\HACACL0102\…` pueden alcanzar.
- **Funciones que solo sirven si Flask corre en el PC del usuario:** `pool_abrir_en_carpeta` y `abrir_carpeta_expediente` lanzan `explorer` en el servidor (#853), y el protocolo `bddat-explorador://` exige instalar un manejador en cada cliente.
- **El servidor Linux y los clientes Windows sobre el mismo share:** permisos CIFS, cuentas, y un montaje `hard` que puede colgar los workers (ANALISIS_ESCALABILIDAD §3.2-§3.3, #852).

Cada síntoma tiene su parche, pero la causa sigue ahí y seguirá produciendo problemas nuevos.

### Por qué ahora

BDDAT no está en producción: no hay documentos reales que migrar. Es el momento más barato del proyecto para cambiar esto.

---

## Decisión

### A — BDDAT es el único dueño de los bytes: tres zonas en el servidor de ficheros

Los usuarios dejan de necesitar acceso a los ficheros de los expedientes. La custodia sigue en el servidor de ficheros corporativo (ANALISIS_DESPLIEGUE §6: no es una debilidad a eliminar), pero en carpetas con permisos distintos. Pedido a Informática en #151:

| Zona | Configuración | Escribe | Lee | Contenido |
|---|---|---|---|---|
| **Almacén** | `ALMACEN_BASE` | solo la cuenta de servicio de BDDAT | solo la cuenta de servicio | el contenido de cada fichero, una vez |
| **Archivo** | `ARCHIVO_BASE` | solo BDDAT | los usuarios, solo lectura | exportación legible de los expedientes finalizados (§H) |

Una tercera zona, **Buzón** (`BUZON_BASE/<usuario>/`, escritura de cada usuario en la suya), se valoró para no obligar a pasar por el navegador ficheros que ya están en el share. Se aparca sin pedirla a Informática hasta que haga falta (§H, Alternativas descartadas §N).

Si la política del servidor de ficheros no permite una carpeta sin acceso de usuarios, la alternativa es el almacén en el disco del servidor de la aplicación con réplica nocturna al share. Funciona igual para BDDAT, pero saca la custodia de donde está hoy.

### B — Puerto de almacenamiento agnóstico, y su adaptador de filesystem

BDDAT no toca el disco directamente: todo lo que necesita leer, escribir o borrar contenido pasa por un **puerto de almacenamiento**, una interfaz mínima e independiente de dónde vivan los bytes:

- `escribir(bytes) -> ref`
- `leer(ref) -> bytes`
- `existe(ref) -> bool`
- `borrar(ref)`

`ref` es **opaca** para el resto de BDDAT: ningún servicio de negocio asume su formato, su longitud, ni que dos contenidos iguales produzcan la misma `ref`. Eso es asunto exclusivo de cada adaptador.

**Solo el subsistema de almacenamiento ve `ficheros` y la `ref`** (enmienda del 2026-10-01). Un **módulo de contenido** ofrece las operaciones sobre la ficha: subir, leer, sustituir con motivo y servir la descarga. Él, el puerto con sus adaptadores, el manifiesto, la limpieza y la integridad son lo único que lee o escribe `ficheros`, `fichero_ref`, `plantilla_ref` o una `ref`. El resto de BDDAT, frontend incluido, trabaja con `documentos.id` (o con `plantillas.id` y el nombre del fragmento), y la API nunca devuelve una `ref` ni una ruta. No es solo orden: las comprobaciones que dan coherencia al contenido (un documento sellado no cambia de contenido, §F; cada cambio va a la bitácora, §C) viven en ese módulo, y un servicio que escribiera `fichero_ref` por su cuenta se las saltaría sin que nada lo detectase. Lo vigila un test con la lista de ficheros permitidos (§I).

**Identidad de contenido, aparte de identidad de almacenamiento.** Deduplicar, avisar de «este fichero ya está en otro expediente» (§H) y dar trazabilidad (§J) son necesidades de BDDAT, no del backend. Por eso `ficheros` (§C) guarda las dos cosas por separado: `ref` (lo que entiende el adaptador) y `contenido_sha256` (el hash del contenido, calculado por BDDAT mientras el fichero entra, con independencia de qué adaptador esté detrás).

Flujo de escritura, igual con cualquier adaptador:

1. BDDAT calcula el SHA-256 **a trozos**, sin cargar el fichero entero en memoria, mientras lo recibe.
2. Si ya existe una fila en `ficheros` con ese `contenido_sha256`, se reutiliza su `ref`: no se llama al adaptador.
3. Si no, se llama a `escribir()`, que devuelve una `ref` nueva, y se crea la fila en `ficheros` con esa `ref` y ese `contenido_sha256`.
4. Solo entonces las filas de negocio (`documentos`...) y el commit. Si el commit falla, queda una fila de `ficheros` sin referencias, que no hace daño y que recoge la limpieza (§G).

**Un contenido ya escrito no se modifica nunca.** Cambiar el contenido de un documento es escribir uno nuevo y apuntar la ficha a él (§F). **Ninguna petición web borra nada del almacén.** Solo `borrar(ref)`, invocado por el proceso de limpieza (§G).

**Por qué importa la separación:** un adaptador futuro contra un gestor documental corporativo (p. ej. Alfresco, que ya usa la Junta) identifica el contenido por un `nodeId` de su propio repositorio, no por su hash, y puede darle dos nodos distintos a dos subidas del mismo contenido si nadie se lo impide antes. Con el puerto agnóstico, ese adaptador solo tiene que implementar las cuatro operaciones de arriba — la deduplicación, el aviso de duplicado y la trazabilidad siguen funcionando igual, porque dependen de `contenido_sha256`, que calcula BDDAT y nunca el backend.

**El adaptador de hoy: filesystem direccionado por contenido.**

```
ALMACEN_BASE/
  sha256/3a/f1/3af1c9…e07b      ← 64 caracteres hexadecimales, sin extensión
  .tmp/                          ← escrituras en curso
  manifiestos/2026/AT-123.json   ← §H, particionado por año de solicitud
```

- **El nombre en disco es el SHA-256 completo del contenido**, y ese SHA-256 hace de `ref` en este adaptador — coincide con `contenido_sha256` porque este backend concreto es, precisamente, un almacén direccionado por contenido; no es un contrato que el resto de BDDAT pueda dar por hecho con otro adaptador. Sin extensión ni nombre original: eso vive en la BD. Sin extensión, nadie abre el fichero con doble clic, y el nombre no choca con nada de Windows (caracteres prohibidos, nombres reservados, longitud).
- **Dos niveles de subcarpetas** (2 + 2 caracteres, del propio hash): listar en SMB una carpeta con decenas de miles de ficheros es lento. 256 × 256 = 65.536 carpetas hoja reparten el árbol.
- **Escritura interna de `escribir()`:** a trozos en `.tmp/`; `fsync`; si el destino ya existe (mismo hash) se borra el temporal y se reutiliza — red de seguridad ante una carrera entre dos subidas simultáneas del mismo contenido, además de la comprobación de BDDAT del paso 2 de arriba; si no, se renombra, atómico dentro del mismo share.

### C — Modelo de datos

**Sin sistema de versiones** (enmienda del 2026-09-26, motivo en §F): una ficha apunta a un fichero, y cambiar el contenido cambia ese puntero.

**`ficheros`**: el contenido, más su identidad frente al almacén. No sabe nada de expedientes, nombres ni tareas.

| Columna | Nota |
|---|---|
| `ref` `text` PK | identidad frente al adaptador de almacenamiento (§B); con el adaptador de filesystem de hoy es el SHA-256 hex |
| `contenido_sha256` `char(64)` UNIQUE | identidad de contenido, calculada por BDDAT con independencia del adaptador; la usan la deduplicación, el aviso de «ya existe» (§H) y la integridad (§G) |
| `tamano` `bigint` | |
| `formato` `text` | MIME **detectado por el contenido** (§E) |
| `creado_en`, `verificado_en` | la segunda la actualiza la comprobación de integridad |
| `estado` | `OK` · `CORRUPTO` · `AUSENTE` |
| `sin_referencias_desde` null | el reloj de la papelera (§G) |

**`documentos`** (existe): la ficha.

| Columna | Qué pasa |
|---|---|
| `id`, `expediente_id`, `tipo_doc_id`, `fecha_administrativa`, `asunto`, `prioridad`, `observaciones` | sin cambios |
| `nombre` | **nueva**: nombre visible y de descarga, editable. Al subir, el nombre del fichero tal cual llegó (UTF-8, sin sanear). Hoy se deduce de la `url` |
| `fichero_ref` | **nueva**, FK a `ficheros.ref`: el contenido actual |
| `contenido_modificado_en` | **nueva**: cuándo cambió el contenido por última vez. Es la `getlastmodified` del WebDAV (§D) |
| `origen_sha256` | **nueva**, solo en el PDF para firma: el hash **de contenido** del borrador del que salió (§D) — identidad de contenido, no de almacenamiento. **No** es FK ni cuenta como referencia para la limpieza |
| `plantilla_ref` | **nueva**, solo en borradores generados, FK a `ficheros.ref`: la plantilla exacta con que se generó (§J) |
| `url` | **solo** `http(s)://` y `bddat://` (ADR-006). `NULL` para un fichero propio |
| `hash_md5` | **desaparece**: la identidad de almacenamiento es `fichero_ref`; la deduplicación por contenido la da `ficheros.contenido_sha256` |
| `tipo_contenido` | **desaparece**: el formato es `ficheros.formato` |
| `borrado_en` | **nueva**: papelera (fase 7, §G) |

Restricción: `CHECK ((url IS NULL) <> (fichero_ref IS NULL))`. Un documento es un fichero propio o una referencia, nunca las dos cosas ni ninguna.

**`generacion_fragmentos`** (`documento_id`, `nombre_fragmento`, `fichero_ref` FK a `ficheros.ref`): los fragmentos exactos insertados en un borrador generado (§J). Es la única tabla nueva además de `ficheros`, `fragmentos` y `sesiones_edicion`.

**`sesiones_edicion`**: la edición por WebDAV (§D). Está en BD y no en memoria porque, con varios workers, cada petición puede caer en uno distinto (ANALISIS_DESPLIEGUE §3).

| Columna | Nota |
|---|---|
| `documento_id`, `usuario_id` | |
| `token_hash` | se guarda el **hash** del token, no el token |
| `caduca_en` | fin de la jornada |
| `lock_token`, `lock_caduca_en` | bloqueo WebDAV |
| `abierta_en`, `cerrada_en` | |
| `sha256_al_abrir` | para anotar en la bitácora un solo cambio por sesión (§D) |

**Cada cambio de contenido va a la bitácora:** hash anterior, hash nuevo, quién, cuándo y por qué vía (`EDICION`, `REGENERACION`, `SUSTITUCION`, con el motivo en esta última).

**No cambian:** `documentos_tarea`, `reformados_proyecto`, `certificados`, `diagnosticos`, `notificaciones`, los sellos y la bitácora apuntan a `documentos.id`, que se conserva. **Vincular un documento a una tarea es insertar una fila en `documentos_tarea`, y no mueve ningún fichero.**

**Operaciones**

| Operación | BD | Almacén |
|---|---|---|
| Subir, aportar desde otro expediente (§H) | ficha nueva | escribe (o reutiliza) |
| Vincular / desvincular | fila en `documentos_tarea` | **nada** |
| Generar escrito | ficha del borrador con `plantilla_ref` y `generacion_fragmentos` | escribe |
| Regenerar | cambia `fichero_ref` si el contenido cambia; confirmación expresa si el borrador se retocó a mano (§F) | escribe |
| Editar en LibreOffice | cada `PUT` cambia `fichero_ref`; una entrada de bitácora por sesión | escribe |
| Descargar el PDF para firma | si está desfasado, se regenera antes de servirlo (§D) | escribe si regenera |
| Descargar / abrir cualquier otro | nada | lee |
| Sustituir por error | cambia `fichero_ref`, con motivo; prohibida si está sellado (§F) | escribe |
| Borrar | `borrado_en = now()` (hasta la fase 7, borra la ficha, §G) | **nada** |

La matriz de 8 casos de #730 se reduce a dos: mismo contenido que el actual, no pasa nada; contenido distinto, se sustituye. Desaparecen las colisiones de nombre y los ficheros apartados.

### D — Borrador, PDF para firma y firmado; edición sin acceso al share

**Tres documentos distintos** (ADR-027):

1. **Borrador `.odt`**: auxiliar, no forma parte del expediente (#608). Identidad de #730: tarea + rol + tipo de la plantilla. **Siempre es el definitivo:** se edita, no se versiona.
2. **PDF para firma**: un documento más, con su ficha, su fichero en el almacén, su vínculo con la tarea y **la descarga de siempre**. Tampoco forma parte del expediente: existe para llevarlo al Portafirmas.
3. **PDF firmado**: documento del expediente, PRODUCIDO de la tarea. Sellado.

**El PDF para firma lo genera el servidor** (decisión de Carlos: «preferentemente el servidor»), con `soffice --headless --convert-to pdf`. Exige LibreOffice en la imagen del servidor (pedido en #151) con las fuentes permitidas por ADR-035 §5.

**Siempre sincronizado con el borrador.** Su ficha guarda `origen_sha256`, el hash de contenido del borrador del que salió. Si el borrador actual tiene otro, el PDF está desfasado:

- **al descargarlo**, si está desfasado, BDDAT lo regenera antes de servirlo. Es la garantía: el PDF que llega al Portafirmas sale siempre del último borrador guardado;
- **en segundo plano**, al cerrarse una sesión de edición, se regenera también, para que la descarga sea inmediata. Es una comodidad, no la garantía.

Regenerar cambia el `fichero_ref` de la ficha del PDF. El PDF anterior se queda sin referencias y lo recoge la limpieza (§G). El paso de descarga muestra la hora de la última edición guardada en BDDAT (ver «Guardar como», abajo).

**Al vincular el PDF firmado, el borrador y su PDF quedan congelados:** no se pueden editar, regenerar ni sustituir. Así el borrador conservado es siempre el que dio lugar a la firma, y la cadena **firmado ← borrador ← plantilla + fragmentos** (§J) se sostiene sin versiones. El enlace del firmado con su tarea sale del código del pie (`BDDAT-<tarea>-<letra>`, #182), porque el Portafirmas reescribe el PDF y su hash no coincide.

**Edición: WebDAV servido por BDDAT, sobre el puerto de almacenamiento (§B).** El botón «Editar» abre el `.odt` en LibreOffice desde una URL con token (`/dav/<token>/<nombre>.odt`), envuelta en el esquema `vnd.libreoffice.command:ofe|u|<url>` («ofe»: abrir para editar). Ese esquema lo registra el instalador de LibreOffice en Windows, así que no hay nada que instalar en el puesto (#1000). Cada «Guardar» de LibreOffice hace un `PUT` contra BDDAT — el primer salto, igual que hoy. BDDAT recibe esos bytes y sigue el mismo camino que cualquier otra entrada de documento (§B): calcula su `contenido_sha256` y, si es nuevo, llama a `escribir()` del puerto — el segundo salto, hacia el almacén agnóstico. El resultado es la nueva `fichero_ref` del borrador. La prueba de concepto lo verificó con LibreOffice 24.2 contra el adaptador de filesystem, y con la 7.6 corporativa en un puesto de la Junta (#1000); de las dos salen cuatro requisitos de implementación:

1. **`getlastmodified` estable**: `contenido_modificado_en`, no «ahora». LibreOffice la compara al abrir, tras el `LOCK` y antes del `PUT`; si cambia sin motivo, **aborta el guardado sin enviarlo** (`ErrorCodeIOException 0x11b`).
2. **Guardar sin cambios no produce los mismos bytes** (LibreOffice reescribe `styles.xml` y `settings.xml`). Sin versiones esto no acumula nada: cada `PUT` sustituye al anterior. Para no llenar la bitácora, se anota **un cambio por sesión**: de `sha256_al_abrir` al último hash, al cerrarse.
3. **Conceder los 180 s de bloqueo que pide LibreOffice.** Renueva cuando le quedan ~30 s; con un bloqueo más corto entra en una lluvia de renovaciones. Si se cuelga, el bloqueo caduca solo: mejor que los `.~lock` del share, que alguien tiene que borrar a mano. **El dueño del bloqueo lo pone BDDAT** (`owner` en `lockdiscovery`) y es lo que lee el segundo usuario en «Más detalles» del aviso de LibreOffice: tiene que ser el nombre del tramitador, no un identificador.
4. **Verbos:** `OPTIONS`, `PROPFIND` (`Depth: 0`, también sobre la carpeta padre), `GET`, `HEAD`, `LOCK`, `PUT`, `UNLOCK` (`HEAD` lo usa la 7.6, #1000). Se rechazan `DELETE`, `MOVE`, `COPY`, `MKCOL` y `PROPPATCH`: el almacén nunca pierde nada por esta vía. **La carpeta del token responde con y sin barra final** (`/dav/<token>` y `/dav/<token>/`): ante una redirección, la 7.6 abandona en silencio el «Guardar como» dentro de esa carpeta en vez de llegar al `PUT` y recibir el 403 (fila 2 de la tabla de abajo).

Un segundo usuario que abre un documento bloqueado lo ve en solo lectura. Un token caducado no abre. **Alternativa sin nada instalado:** descargar, editar y volver a subir; BDDAT reconoce la tarea por el código del pie y ofrece sustituir el borrador.

**«Guardar como».** Probado el 2026-09-26 contra la prueba de concepto. El usuario puede hacerlo (el menú de LibreOffice no se puede limitar solo para estos documentos) y hay tres casos:

| Qué hace el usuario | Qué pasa | ¿Llega a BDDAT? |
|---|---|---|
| «Guardar como» a su disco, y sigue editando | LibreOffice pasa a trabajar sobre la copia local, suelta el bloqueo de BDDAT al instante (`UNLOCK`) y los guardados siguientes van al disco | **No**, sin error ni aviso |
| «Guardar como» con otro nombre en la carpeta WebDAV | Con la 24.2, BDDAT rechaza el `PUT` (403) y LibreOffice da error de escritura. Con la 7.6 corporativa, el diálogo de Windows ni ofrece esa carpeta (propone «Documentos»: en la práctica es la primera fila), y con el de LibreOffice no llegó a intentarlo ni avisó (requisito 4). En todos los casos el documento sigue apuntando a BDDAT | No; con la 24.2 el usuario ve el error |
| «Guardar una copia» | la copia va al disco y el documento sigue en BDDAT | **Sí**: el siguiente «Guardar» llega |

El primer caso **no se puede detectar**: un desbloqueo sin guardado es lo mismo que abrir, leer y cerrar. Las únicas mitigaciones posibles, y las que se adoptan:

1. **La descarga del PDF para firma muestra el PDF generado y la hora de la última edición guardada en BDDAT.** Quien hizo «Guardar como» ve que faltan sus cambios antes de firmar.
2. **La copia local se puede devolver:** al subir ese `.odt`, BDDAT reconoce la tarea por el código del pie y ofrece sustituir el borrador.
3. **Aviso junto a «Editar»:** «Guarda con Ctrl+S; "Guardar como" crea una copia que BDDAT no ve».

**Verificado en un puesto de la Junta el 2026-10-01 (#1000)**, en la fase 0 y antes de escribir código (enmienda del 2026-10-01; es la puerta de la fase 1, §I), con la prueba de concepto y el LibreOffice corporativo 7.6.7.2, en tres casos: el propio puesto contra `127.0.0.1`, el propio puesto contra su IP de red, y una segunda máquina por la VPN (con LibreOffice 26.2). Resultados:

- El botón abre Writer sin pedir credenciales. El navegador pide confirmación para abrir LibreOffice la primera vez desde cada dirección; se puede recordar, o fijarlo Informática por directiva del navegador.
- El proxy de LibreOffice, en «Sistema», no interfiere contra la IP de red.
- El segundo usuario, desde otra máquina, ve el aviso de bloqueo («Otro usuario ha bloqueado este archivo», con el nombre del primero en «Más detalles») y abre en solo lectura. En la 7.6 los botones de ese aviso salen sin traducir («Open R/O», «Open Copy»).
- Una edición de más de 3 minutos renueva el bloqueo sin que el usuario lo note, y el guardado final entra.
- Los tres casos de «Guardar como» se comportan como dice la tabla de arriba.
- Un token caducado no abre: LibreOffice da un error genérico («Error al leer los datos desde Internet», con el 403), cuyo texto no se puede personalizar desde el servidor.
- La autorrecuperación de LibreOffice guarda su copia en el perfil del usuario y no escribe en BDDAT. El guardado es manual (Ctrl+S) y el autoguardado no se configura en los puestos (decisión de Carlos).

El registro de `vnd.libreoffice.command:` solo se ha comprobado en ese puesto. **HTTPS con el certificado corporativo** espera al servidor real (#151, #330) y queda en la fase 5.

### E — Qué se puede subir

**Lista cerrada**, detectada por los primeros bytes del contenido y no por la extensión ni por el MIME del navegador. Si no coinciden, se rechaza: es señal de un fichero renombrado.

| Formato | Se reconoce por | Admitido |
|---|---|---|
| PDF, PDF/A | `%PDF-` | sí; si está cifrado se avisa (no se podrá extraer su texto, #181, #717) |
| ODT, ODS, ODG | ZIP con `mimetype` ODF | sí |
| DOCX, XLSX | ZIP con `[Content_Types].xml` | sí; se guardan, no se editan en BDDAT |
| DOCM, XLSM | ídem con `vbaProject.bin` | no: se piden sin macros |
| JPEG, PNG, TIFF | cabecera | sí |
| XML, XAdES (`.xsig`), CAdES (`.csig`, `.p7s`) | `<?xml` / ASN.1 | sí, **a confirmar con muestras reales** |
| KMZ/KML, SHP, DWG | firma propia | **por decidir** con lo que llegue en los proyectos |
| ZIP genérico | `PK` sin estructura conocida | no por defecto: se pide descomprimido |
| HTML, SVG, ejecutables, desconocidos | — | no. HTML y SVG pueden llevar JavaScript contra la propia BDDAT |

Los formatos por confirmar no son urgentes (decisión de Carlos): se añaden cuando lleguen muestras.

**Qué fichero subir** (norma de uso, no la impone el sistema; criterio de Carlos, 2026-09-26). Depende de dónde sale la fecha administrativa del documento:

- **Si es la del propio documento** (un proyecto: fecha de visado o de firma del proyectista), conviene subir **el original**. Además, es el que permite detectar que el mismo fichero ya está en otro expediente (§H).
- **Si es la de registro**, conviene subir **el registrado** (con el sello de entrada de la Junta), porque es el que permite el cotejo a un tercero que audite. Hoy solo PTWANDA permite descargar uno u otro.

**Al servirlos:** PDF e imágenes se muestran en el navegador (`X-Content-Type-Options: nosniff`, CSP `sandbox`); el resto se descarga (`Content-Disposition: attachment`). El nombre de descarga es `documentos.nombre`, codificado según RFC 5987: no hay que sanear nada al guardar. **Tamaño máximo:** 500 MB por defecto (§K), escritura a trozos.

### F — Sin versiones: cambiar el contenido de un documento

**Enmienda del 2026-09-26** (argumento de Carlos). La primera redacción de este ADR tenía versiones de documentos, con purga. Se retiran:

- **El borrador `.odt` y el PDF para firma no forman parte del expediente**: son utilitarios para obtener el firmado. Poder volver a una versión anterior del borrador es una forma de meter el error en el PDF: un garabato guardado sin querer, una edición consciente posterior y un «volver atrás» a la versión con el garabato. **La edición es siempre sobre el definitivo, y el PDF sale siempre del último guardado** (§D).
- **Los documentos de fuera no tienen versiones:** un informe corregido es **otro documento**, con su fecha; igual que un reformado (ADR-044).
- **Revisado cada caso, no queda ninguno que justifique un sistema de versiones de documentos.** El único con algo parecido, las plantillas, se resuelve sin versiones (§J).

Cómo se cambia el contenido de un documento sin versiones:

- **Edición y regeneración del borrador:** cambian `fichero_ref`. **Regenerar desde la plantilla destruye los retoques hechos a mano**, así que, si el borrador se editó desde que se generó (lo dice la bitácora), la regeneración pide confirmación expresa: «vas a perder los cambios hechos a mano».
- **Sustituir por error** («subí el fichero equivocado»): cambia `fichero_ref`, con **motivo obligatorio** y bitácora, y está **prohibido si el documento está sellado o lo cita un certificado** (`sellos.motivo_sellado`). Es lo que hoy no existe: un cambio visible en lugar de un cambio de `url` sin rastro.
- **Red de seguridad, solo para el administrador:** el fichero anterior se queda sin referencias, pero la limpieza lo conserva durante los días de la papelera (§G), y la bitácora dice cuál era. Ante un desastre, un administrador puede recuperarlo. **No es un «volver atrás» del usuario**, y no tiene botón.
- **Sin purgas:** lo que ya no se usa lo recoge la limpieza.

### G — Papelera y limpieza: lo único que borra

Un proceso nocturno, con el mecanismo de tareas diarias de §H:

1. marca `sin_referencias_desde` en los ficheros a los que no apunta nada, y la quita si han vuelto a tener referencias. **Cuentan como referencia:** `documentos.fichero_ref` y `documentos.plantilla_ref` de documentos sin borrar, `generacion_fragmentos.fichero_ref`, `plantillas.fichero_ref` y `fragmentos.fichero_ref`. **No cuenta:** `documentos.origen_sha256`, que es identidad de contenido, no de almacenamiento, y solo sirve para saber si el PDF está desfasado;
2. borra del almacén (`borrar(ref)` del puerto, §B) los que llevan más de N días sin referencias, y luego su fila;
3. borra definitivamente los documentos con `borrado_en` de hace más de N días, repitiendo antes la guarda de borrado por si algo los ha referenciado entretanto;
4. lo registra todo en la bitácora. De cada fichero borrado, su **`ref`** y su `contenido_sha256`, con el nombre, el tipo y el expediente del documento que lo usó: la fila de `ficheros` desaparece, y la bitácora es lo único que conserva qué `ref` pedir a la copia de seguridad y con qué hash comprobar lo restaurado (enmienda del 2026-10-02).

Con la deduplicación, un fichero compartido por dos documentos solo se borra cuando **ninguno** lo usa. Lo resuelve la consulta, sin contadores. La comprobación periódica de integridad relee cada fichero (`leer(ref)`) y recalcula su `contenido_sha256`: si no coincide, `CORRUPTO`; si no está, `AUSENTE`. El resultado aparece en el panel del supervisor, y la `ref` dice qué fichero exacto pedir a Informática de una copia de seguridad. **Restaurar:** primero el almacén y luego la BD. Si sobran ficheros, son huérfanos y los recoge la limpieza; nunca faltan.

**La papelera** (enmienda del 2026-10-02, propuesta de Carlos). Llega en la fase 7, con la limpieza; hasta entonces «Borrar» elimina la ficha como hoy, con la misma guarda, y su fichero se queda en el almacén sin referencias hasta que lo recoja la limpieza.

- **Va a la papelera** un documento al que no referencia nada (la guarda de borrado de hoy).
- **Sigue a la vista, marcado,** hasta el borrado definitivo, y se puede **sacar de la papelera** si se borró por error. No se esconde de los listados: si uno se olvida de tratarlo, el documento aparece, que es lo esperado, en vez de desaparecer sin aviso.
- **Tres sitios lo tratan distinto:** no se ofrece para **vincular** (primero se saca de la papelera; si no, estaría vinculado y en la papelera a la vez y la limpieza lo borraría en uso); no cuenta en los **avisos de huérfanos** (el radar y el aviso de justificantes sin vincular al cerrar fase, #738), porque estar en la papelera es la decisión de no usarlo; y la limpieza **repite la guarda** antes del borrado definitivo (paso 3).
- **Su fichero** sigue la regla general del paso 1: un documento en la papelera no cuenta como referencia, así que el fichero empieza a contar al mandarlo y, si se saca, vuelve a tener referencia y la cuenta se anula. Documento y fichero caducan juntos, y la misma regla cubre los contenidos sustituidos (§F) y los ficheros compartidos.

### H — Entrada de documentos y N009

**N009, «expediente reconstruible sin BDDAT»: manifiesto siempre, exportación al finalizar** (decisión de Carlos):

- **Manifiesto por expediente, siempre.** `ALMACEN_BASE/manifiestos/<año-solicitud>/AT-123.json` (año de la solicitud del expediente, 4 cifras). La partición por año evita que `manifiestos/` crezca sin límite en un único directorio — mismo motivo que el sharding del almacén (§B). Lista cada documento con su id, nombre, tipo, fecha administrativa, tareas, **`ref` y hash de contenido** (la `ref` hace falta para encontrar el fichero con un adaptador que no sea el de filesystem, §B) y **la ruta ESFTT que le tocaría**, ya calculada como texto con `ruta_esftt_documento`, que se conserva: quien lo lea no necesita el catálogo.
- **Cuándo se rehace** (enmienda del 2026-10-01): **de noche, todos**, reescribiendo solo los que salen distintos del guardado, y **el de un expediente, justo antes de exportarlo**. `flask manifiestos [AT-N]` lo hace en el momento. No se engancha a las operaciones que cambian un expediente: serían una docena de puntos (subir, aportar, vincular, editar la ficha, cada guardado de LibreOffice, regenerar, sustituir, borrar, cambios que mueven la carpeta ESFTT), uno olvidado dejaría un manifiesto desfasado sin aviso, y cada petición escribiría en el share (#852). El desfase de hasta un día no resta nada: si se pierde la BD se restaura la copia de la noche anterior, y los cambios del día se pierden igual. Lo que aporta el manifiesto es poder leerse sin PostgreSQL, no ir más al día.
- **Tareas diarias, sin depender del sistema.** Un puesto corporativo puede no permitir programar tareas. Al llegar una petición, si la última pasada tiene más de 24 h, BDDAT la lanza en segundo plano sin hacer esperar a la petición; un bloqueo de PostgreSQL (`pg_try_advisory_lock`) hace que, con varios workers, la ejecute uno solo. Si hay `cron` (servidor Linux), lo lanza `cron` y la puesta al día no encuentra nada pendiente. Dos pasadas simultáneas no rompen nada (cada manifiesto se escribe en un temporal y se renombra); el bloqueo solo evita trabajo repetido. Nace en la fase 1 con los manifiestos; la limpieza (§G) y el proceso nocturno de ADR-021 se suman a él.
- **Exportador, independiente de BDDAT** (enmienda del 2026-10-01). Lee un manifiesto y pide cada fichero al almacén; **no consulta la BD**. Solo usa la biblioteca estándar de Python y no importa nada de `app/`: con Flask y PostgreSQL parados, quien tenga Python y lectura sobre `ALMACEN_BASE` (en la práctica Informática con la cuenta de servicio, o sobre una copia restaurada) reconstruye el árbol legible. Comprueba el hash de cada fichero al copiarlo. BDDAT lo importa a él, nunca al revés, y es **el único código que reparte documentos en carpetas**: la reconstrucción a mano, el ZIP y la exportación al finalizar pasan por él, así que el manifiesto se prueba en cada uso y no solo el día del desastre. La garantía «sin BDDAT» vale para el adaptador de filesystem; con otro, el exportador necesita su forma de leer.
- **Exportación bajo demanda:** «Exportar expediente» genera un ZIP con el árbol ESFTT legible y el manifiesto.
- **Exportación automática al finalizar el expediente:** el mismo árbol se escribe en `ARCHIVO_BASE`, de solo lectura para los usuarios. Si el expediente se reabre (por un recurso, por ejemplo), la exportación se rehace al volver a finalizar; la anterior se conserva con fecha y no se sobrescribe.

Al escribir el árbol legible, y solo entonces, se adaptan los nombres a Windows (caracteres prohibidos, nombres reservados, longitud de ruta). Hoy lo hace `rutas_esftt.py`; pasa al exportador, para que funcione sin BDDAT.

Las carpetas exportadas son libres de usar: se pueden reorganizar, enviar o estropear sin que afecte a nada, porque las del almacén no las toca nadie. **No confundir con la remisión del expediente** (#573, foliado e índice, arts. 70.2 y 70.3 LPACAP): un índice HTML con los ficheros enlazados para navegar el expediente, que lee del almacén como cualquier otro consumidor y no tiene nada que ver con este árbol de carpetas.

**Entrada de documentos en fase 1: solo subida multipart desde el navegador**, para cualquier origen (disco del usuario o carpeta de red ya montada). El registro in situ (`pool_explorador_fs` + `pool_registrar_rutas`) — la puerta trasera que este ADR cierra — desaparece sin sustituto directo: un mecanismo de «buzón» por usuario en el share se valoró y se aparca (ver Alternativas descartadas) hasta que haya datos reales de que el coste de una subida por navegador para ficheros grandes es un problema, y no solo una posibilidad.

**El mismo fichero en otro expediente** (enmienda del 2026-09-26). Caso típico: un proyecto tramitado en un expediente que hace falta en otro, por ejemplo una modificación de instalaciones en servicio que necesita el proyecto original y el de modificación.

- **Se crea una ficha nueva en el expediente B** apuntando al mismo fichero: por ADR-027 un documento pertenece a un solo expediente, y los datos de la ficha son distintos. En particular, **la fecha administrativa en B no es la de A**: en B el documento se aporta con otra fecha y otro registro. BDDAT sugiere tipo y asunto desde el documento de A, pero la fecha la pone quien lo registra.
- **Nada de lo que se haga en un expediente afecta al otro:** sellar, sustituir o borrar el documento en A no toca el de B, y el fichero solo lo borra la limpieza cuando ninguno lo usa.
- **«Aportar desde otro expediente»** es la vía principal: un listado plano de documentos de todos los expedientes, con búsqueda por tipo, nombre, expediente y fecha. El usuario elige y se crea la ficha en el expediente actual, sin volver a subir nada.
- **Aviso por hash al subir**, como ayuda: si el fichero ya existe (mismo `contenido_sha256`), BDDAT avisa («este fichero ya está en AT-123 como "Proyecto de ejecución…"») y ofrece crear la ficha con esos datos como sugerencia. Si ya existe **en el mismo expediente**, el aviso es de duplicado (N077). **Límite:** solo detecta ficheros idénticos byte a byte. Un PDF con el sello de registro de la Junta siempre es distinto del original, así que en ese caso no hay aviso posible; por eso la vía fiable es «Aportar desde otro expediente», y de ahí la norma de uso de §E.

### I — Secuenciación

Medido el 2026-09-25 contra la cadena de ADR-049: los dos trabajos **apenas se tocan**. La cadena opera sobre la ficha (fechas, tipos, vínculos, sellos, certificados); este ADR cambia lo que hay debajo. Los servicios de la cadena (`sellos`, `cert_cumplimiento_fase`, `certificados`, `actos_solicitud`, `plazos`) no tocan el disco. El único roce es `mutaciones_arbol.py`, que hoy mueve el fichero al vincular (N5 y #568 vinculan justificantes).

- **Se implementa después de N6 y antes de producción.** Esperar no encarece el cambio: no hay datos reales, y N4b y N6 no añaden consumidores del disco.
- **Regla mientras tanto:** nada nuevo de la cadena escribe ficheros en disco. Los certificados, en HTML y `bddat://`, como decidió #947. **Ampliada el 2026-10-01 a todo el desarrollo:** no entran consumidores nuevos del modelo de rutas (`ruta_absoluta()`, `FILESYSTEM_BASE`, `PLANTILLAS_BASE`, `hash_md5`, `ruta_plantilla`, `ruta_pdf`, los `mover_*` de `rutas_esftt.py`); lo nuevo que necesite un fichero lo pide por el documento. Un test con el número de apariciones permitido en cada fichero lo vigila desde la fase 0 (`tests/test_1001_consumidores_modelo_rutas.py`, #1001; el 2026-10-02, 22 ficheros y 116 apariciones), y cada fase lo baja. Cuando se retire el último símbolo, esa parte del test se borra; la otra, que solo el subsistema de almacenamiento vea la `ref` (§B), es permanente. **La regla pasa a `REGLAS_DESARROLLO.md` cuando hay algo implementado que la sostenga**, no antes: la congelación, con el test de la fase 0; la de la `ref`, en la fase 1, con el módulo de contenido. Hasta entonces vive aquí.
- **Válvula:** si en N5 el conflicto en `mutaciones_arbol.py` pesa más de lo previsto, se adelanta solo la fase 2 (vincular sin mover). Sin uso: N5 se cerró sin necesitarla, y vincular sin mover está ya en la fase 1.
- **Puerta de la fase 1** (2026-10-01): la prueba de la edición en un puesto de la Junta (§D). Las fases 1-4 no usan WebDAV, pero son las que quitan a los usuarios el acceso a las carpetas: si Writer no se puede abrir desde BDDAT en un puesto real, editar el borrador sería para siempre descargar y volver a subir, y eso hay que saberlo antes de invertir en ellas. La fase 1 empieza cuando la prueba pasa, o cuando Carlos acepta esa alternativa como definitiva. **Pasada el 2026-10-01** (#1000, §D): la fase 1 puede empezar.
- **La respuesta de Informática (#151) no frena el código, sí la producción** (2026-10-01). Con el puerto agnóstico (§B), dónde viva el almacén —carpeta solo para la cuenta de servicio, o disco del servidor con réplica nocturna (§A)— es el valor de `ALMACEN_BASE`. Solo cambiaría código si no permiten LibreOffice en el servidor (fase 6) o si ofrecen S3 o un gestor documental (un adaptador más; la fase 1 sigue valiendo).
- **Ya hecho, fuera de este ADR:** #953 (validador, PR #959) y el pedido a Informática en #151.

Fases, con tamaños estimados por comparación con los PR de la cadena (#934 N1: 56 ficheros, +2.942/−660; #948 N4: 25 ficheros, +2.074). Es orden de magnitud, no compromiso; sin versiones, algo menor que en la primera redacción:

| Fase | Contenido | Comparable a |
|---|---|---|
| 0 | Revalidar la tabla de consumidores (§M) y crear los issues; prueba de la edición en un puesto de la Junta (§D, puerta de la fase 1); test de consumidores del modelo de rutas | — |
| 1 | Almacén, `ficheros`, columnas nuevas de `documentos`, módulo de contenido (§B), detección de formato (§E), subida, descarga, lectores, «Aportar desde otro expediente», migración de datos de desarrollo con su comprobación (§L); manifiesto, exportador independiente, reconstrucción a mano y tareas diarias (§H). **Absorbe la 2 y la 3** (enmienda del 2026-10-02, abajo): todos los escritores al almacén a la vez —generar y regenerar escritos (8 casos → 2), PDF de `CERT_FIN_INSTRUCCION`, copia del anuncio edictal, sustitución con motivo—, vincular sin mover, fuera el registro in situ; y en el mismo issue se retiran el modelo de rutas (`mover_*`, MD5, rama local del validador, `ruta_absoluta()`, `FILESYSTEM_BASE`) y los botones de carpeta del pool y del árbol con su `explorer` (#853). Varios PR bajo un issue | N1 y algo más |
| 2 | Absorbida por la 1 | — |
| 2b | «Exportar expediente» (ZIP) y exportación automática al finalizar (§H): dos capas sobre el exportador, cuando las tareas de cada documento ya no cambian por debajo | pequeño |
| 3 | Absorbida por la 1 | — |
| 4 | Plantillas y fragmentos (§J); retira el motor de Word, el explorador de ficheros de la gestión de plantillas y `bddat-explorador://` con `scripts/cliente/` | mediano |
| 5 | Edición por WebDAV, sesiones en BD, botón «Editar» con `vnd.libreoffice.command:` (sin instalador en el cliente, #1000); HTTPS con el certificado corporativo | mediano |
| 6 | PDF para firma en el servidor, sincronizado con el borrador | pequeño; depende del Dockerfile (#330) |
| 7 | Papelera, limpieza, integridad, parámetros (§G, §K) | mediano, independiente |

**Por qué la fase 1 absorbe la 2 y la 3** (enmienda del 2026-10-02, revalidación de §M; decisión de Carlos). La migración (§L) deja `url = NULL` en los ficheros propios, y con eso no queda en pie nada del modelo de carpetas: `mover_a_esftt` falla al vincular un documento migrado (`os.path.dirname(None)`); lo que generaran después los escritores de rutas (escritos, PDF del `CERT_FIN_INSTRUCCION`, registro in situ) quedaría en el modelo viejo, sin migrar; y «abrir en carpeta» ya no encuentra el fichero. Por eso la fase 1 corta todos los escritores a la vez, y lo que deja muerto se retira en el mismo issue, en su último PR, sin código muerto ni botones que fallen entre fases. Los números de fase se conservan: «las fases 0-3» siguen siendo las que espera #929. El explorador de la gestión de plantillas y `bddat-explorador://` siguen en uso hasta la fase 4 y se retiran allí.

Las fases 0-4, con la 2b, van antes de producción: sin manifiesto ni exportación, retirar a los usuarios las carpetas dejaría N009 peor que hoy (enmienda del 2026-10-01; antes estaban en la fase 7). La limpieza puede esperar sin riesgo: es lo único que borra, y mientras no exista solo crece el almacén. Las fases 5-7 pueden ir al ritmo del despliegue: hasta la 5, el borrador se retoca descargándolo y volviéndolo a subir (§D), y hasta la 6, el PDF para firma lo exporta el usuario.

### J — Plantillas y fragmentos

**Hoy:** `plantillas.ruta_plantilla` apunta a un fichero bajo `PLANTILLAS_BASE/plantillas/`. **No hay subida desde el navegador**: el supervisor copia el `.odt` al share y lo elige con el explorador del servidor. **Los fragmentos no tienen tabla**: son ficheros `PLANTILLAS_BASE/fragmentos/<Nombre>.odt` buscados por nombre al encontrar `{{r Nombre }}`. Además del problema de fondo (el supervisor necesita escribir en el share), hay tres propios:

- **Si falta un fragmento, el escrito sale sin él sin que nadie lo sepa** (`generador_escritos_odt._insertar_fragmentos`: un `logger.warning` y sigue). Una resolución sin fundamentos de derecho o sin pie de recurso es un error jurídico.
- **Editar una plantilla la cambia en vivo** para todos los tramitadores, también a medio editar o con un fallo.
- **No se sabe qué plantilla produjo un escrito** (la pregunta de trazabilidad que ANALISIS_ESCALABILIDAD §4.1 dejaba sin respuesta).

**Decisión** (enmienda del 2026-09-26, propuesta de Carlos): **una sola plantilla vigente en BDDAT, y el versionado a cargo del supervisor, fuera de BDDAT.** La primera redacción tenía versiones con publicación; se retiran (alternativa K).

- **Datos:** `plantillas` conserva sus metadatos; `ruta_plantilla` se sustituye por `fichero_ref`. **Nueva** `fragmentos` (`id`, `nombre` único —la clave de `{{r Nombre }}`—, `descripcion`, `activo`, `fichero_ref`).
- **El supervisor edita en su PC, no en BDDAT:** parte de la base canónica, edita en Writer y guarda sus copias donde quiera (ese es su versionado). Para cambiar la plantilla vigente, **la sube desde el navegador**. BDDAT la valida (`validar_plantilla` y canonicidad de #727): si pasa, **sustituye a la vigente en una sola transacción**; si no, no cambia nada.
- **No hace falta bloquear la generación durante el cambio:** la sustitución es atómica, y un escrito que se genere a la vez usa la plantilla anterior o la nueva, las dos válidas. Nunca ve una plantilla a medias.
- **La señal de «plantilla en revisión» ya existe: `plantillas.activo`.** Si el supervisor sabe que la vigente está mal y no quiere que nadie genere con ella mientras la corrige, la desactiva. Los tramitadores ven «plantilla en revisión» en lugar de «Generar», y al subir la corregida la reactiva.
- **Probar antes de sustituir** (la necesidad A2, que estaba aplazada): se sube el candidato, se genera un escrito de prueba con un expediente real sin guardar nada, y se descarta o se confirma la sustitución. El candidato descartado no lo referencia nada y lo recoge la limpieza.
- **Trazabilidad, sin tablas de versiones:**
  1. cada borrador generado guarda `plantilla_ref`, y `generacion_fragmentos` las referencias de los fragmentos exactos insertados (el motor ya devuelve la lista de insertados; solo falta guardarlas);
  2. la limpieza no borra un fichero referenciado: como el borrador se conserva (congelado tras la firma, §D), **la plantilla y los fragmentos exactos que lo produjeron siguen en el almacén y se pueden descargar desde el escrito**;
  3. cada sustitución de plantilla o fragmento va a la bitácora (hash anterior, hash nuevo, quién, cuándo, motivo): es el historial dentro de BDDAT.
- **Aviso de plantilla desfasada:** si el borrador de una tarea se generó con una plantilla distinta de la vigente (`plantilla_ref` ≠ `plantillas.fichero_ref`), el editor lo indica («generado con una plantilla anterior»). El tramitador decide si regenera.
- **Fragmentos:** se sustituyen igual, subiendo el fichero. Antes de confirmar se muestra en cuántas plantillas se usa, porque el cambio las afecta a todas a la vez; que es lo que se quiere (p. ej. el pie de recurso tras un cambio legal), pero con el alcance a la vista. El nombre no se puede cambiar si alguna plantilla lo usa. Subir una plantilla exige que existan todos los fragmentos que cita. **Al generar, un fragmento que falte detiene la generación con error.**
- **Motor:** `generar_escrito` trabaja con bytes en vez de rutas. Recibe la plantilla y una función que devuelve el fragmento vigente por nombre. No toca el disco, y los tests dejan de necesitar carpetas temporales.
- **Las bases canónicas siguen en el repositorio** (`app/data/plantillas_base/`): son código y se versionan con git. Desaparece el paso de copiarlas a `PLANTILLAS_BASE` (ANALISIS_DESPLIEGUE §9).
- **El motor de Word se retira en la fase 4** (enmienda del 2026-10-02, decisión de Carlos). En la Junta no hay Word instalado y los `.docx` se abren con LibreOffice: no tiene sentido mantener un formato que no es el nativo del ecosistema. Lo que ADR-035 §2 dejó para «cuando no haya prisa» se hace aquí, porque el motor de Word usa dos cosas sin sitio en este diseño: sus fragmentos `.docx`, con el mismo nombre que los `.odt` (la tabla `fragmentos` guarda un fichero por nombre), y la carpeta `PLANTILLAS_BASE/recursos/` con las imágenes que inserta `img()`. Solo pasan al almacén las plantillas y los fragmentos `.odt`; las plantillas `.docx` no se migran.

### K — Parámetros configurables por el administrador

En `ConfiguracionSistema`, que ya existe. Cada cambio va a la bitácora. Los límites impiden que un error de configuración vacíe la papelera en un día o deje el almacén sin comprobar:

| Parámetro | Por defecto | Límite |
|---|---|---|
| Días de papelera antes del borrado definitivo | 90 | mínimo 7 |
| Tamaño máximo por fichero | 500 MB | nunca por encima del límite de despliegue (nginx/Flask) |
| Formatos admitidos | toda la lista de §E | se pueden **desactivar**, no añadir: añadir exige código que los reconozca |
| Frecuencia de la comprobación de integridad | semanal | mínimo mensual |

**No son configurables desde la aplicación** las rutas (`ALMACEN_BASE`, `BUZON_BASE`, `ARCHIVO_BASE`): son de despliegue, en variables de entorno. Cambiarlas desde la web con datos dentro lo rompería todo.

### L — Migración

- Cada documento con ruta local: se lee el fichero, se guarda en el almacén y se rellenan `fichero_ref`, `nombre` (el nombre original sin el prefijo de hash del pool, `3af1c9e0_`) y `contenido_modificado_en`. Los que no se encuentren salen en un informe.
- Cada plantilla: su fichero pasa a `fichero_ref`. Cada `.odt` de `fragmentos/`: fila en `fragmentos` con su `fichero_ref`. Los borradores ya generados quedan sin `plantilla_ref` (no hay forma fiable de saber con cuál se generaron). Esto es de la fase 4; la de los documentos, de la fase 1. Las plantillas `.docx` no se migran (§J).
- Sin producción, es un script de una tarde; se valida contra la BD de desarrollo del PC.
- **Comprobación de punta a punta** (enmienda del 2026-10-01): tras migrar, se rehacen los manifiestos, se exporta con el exportador de §H y se compara el resultado con el árbol de antes. Cada documento tiene que salir con los mismos bytes y en la misma carpeta ESFTT. Diferencias admitidas: los sufijos por choque de nombres (dependen del orden de llegada), los documentos registrados in situ (salen dentro del árbol, no donde los dejó el usuario) y los ficheros apartados por la regeneración sin referencias (no salen). Prueba con datos reales que la migración no pierde ningún documento, sin código nuevo.
- **La migración es de ida.** No hay script inverso ni camino de vuelta al modelo de carpetas (Alternativas O).

### M — Consumidores (REGLAS_DESARROLLO §Análisis de impacto previo)

Inventario del 2026-09-25 sobre `develop` en `d3bb6e0`, ajustado a la enmienda del 2026-09-26 y **revalidado en la fase 0, el 2026-10-02, sobre `develop` en `025f720`**: lo marcado «(2026-10-02)» es nuevo o corregido en la revalidación. Entre paréntesis, la fase de cada acción cuando no es la 1.

**Modelos y servicios**

| Consumidor | Acción |
|---|---|
| `app/models/documentos.py` | **Actualizar**: `url` solo `http(s)`/`bddat`; `nombre`, `fichero_ref`, `contenido_modificado_en`, `origen_sha256` (fase 6), `plantilla_ref` (fase 4), `borrado_en` (fase 7); fuera `hash_md5`, `tipo_contenido`, `ruta_absoluta()` y la rama local del validador; `resolver_url()` lee del almacén; `__str__` deja de sacar el nombre de la `url` (2026-10-02) |
| `app/models/plantillas.py` | **Actualizar** (fase 4): `ruta_plantilla` → `fichero_ref` |
| `app/models/certificados_fase.py` | **Actualizar**: fuera `ruta_pdf` (ruta absoluta en disco) |
| Modelos nuevos: `ficheros` (`ref` + `contenido_sha256` por separado, §B); `fragmentos` y `generacion_fragmentos` (fase 4); `sesiones_edicion` (fase 5) | **Crear** |
| `app/services/rutas_esftt.py` | **Actualizar**: se conserva `ruta_esftt_documento` (manifiesto); la adaptación de nombres a Windows pasa al exportador (§H); **eliminar** `mover_a_esftt`, `mover_a_pool`, `nombre_pool_unico`, `ruta_pool_documento`, `ruta_destino_esftt_fichero` y el MD5 |
| `app/services/ingesta_pool.py` | **Actualizar**: escribe en el almacén; aviso de fichero existente (§H) |
| `app/services/regeneracion_escritos.py` | **Actualizar**: 8 casos → 2; confirmación si hay retoques; fuera el apartado de ficheros |
| `app/services/generador_escritos.py`, `generador_escritos_odt.py` | **Actualizar**: el escrito generado va al almacén, fuera `guardar_documento` a ruta; bytes, fragmentos por tabla, fragmento ausente = error, `plantilla_ref` y `generacion_fragmentos`, fuera `_ruta_plantilla` (fase 4) |
| `app/services/generador_escritos_docx.py` | **Eliminar** (fase 4): se retira el motor de Word, con sus fragmentos `.docx` y `PLANTILLAS_BASE/recursos/` (§J; 2026-10-02) |
| `app/services/generador_cert.py`, `cert_fin_instruccion.py` | **Actualizar**: PDF al almacén; fuera `_borrar_pdf` (lo hace la limpieza) |
| `app/services/mutaciones_arbol.py` | **Actualizar**: fuera las llamadas a `mover_*`; la lectura del hook de #717 pasa por el almacén, y también la del justificante NOTIFICA (`parsear_documento_notifica`, #657), con el formato de `ficheros.formato` y no de la extensión (2026-10-02); la copia del anuncio edictal (`aplicar_anuncio_edicto`, #568) crea la ficha con el mismo `fichero_ref` y `nombre` en vez de copiar `url` y `hash_md5` (2026-10-02); congelar el borrador al vincular el firmado, y su PDF en la fase 6 |
| `app/services/extraccion_texto_documento.py` | **Actualizar**: lee del almacén; el formato, de `ficheros.formato` y no de la extensión (2026-10-02) |
| `app/services/context_builders/contexto_analisis_documental.py` | **Dejar** (2026-10-02, corrige «leen del almacén»): solo lee un diagnóstico `bddat://` con `resolver_url()`, que no cambia |
| `app/services/alta_expediente.py` | **Actualizar**: ingesta nueva; fuera el `os.remove` de limpieza en fallo |
| `app/services/sellos.py` | **Actualizar**: `motivo_sellado` también impide cambiar el fichero |
| `app/services/detalle_nodo.py` | **Actualizar**: `puede_abrir_carpeta` desaparece; descargar, y «Editar» en la fase 5; `_nombre_doc` lee `nombre` (2026-10-02) |
| `app/services/esquema_editable.py` | **Actualizar** (2026-10-02): `_nombre_doc` lee `nombre` en vez de la `url` |
| `app/config.py` | **Actualizar**: `FILESYSTEM_BASE` → `ALMACEN_BASE`; `ARCHIVO_BASE` (fase 2b); fuera `PLANTILLAS_BASE` (fase 4); lo mismo en `TestingConfig` (`TEST_FILESYSTEM_BASE`, `TEST_PLANTILLAS_BASE`; 2026-10-02). Sin `BUZON_BASE`: el buzón está aparcado (§A) |
| Servicios nuevos: puerto de almacenamiento + adaptador de filesystem (CAS), módulo de contenido (único que ve la `ref` fuera del puerto, §B), detección de formato, manifiesto, exportador independiente (solo biblioteca estándar, §H), tareas diarias; WebDAV (fase 5); conversión y sincronización del PDF para firma (fase 6); papelera, limpieza e integridad (fase 7) | **Crear** |

**Rutas, módulos, plantillas HTML y JS**

| Consumidor | Acción |
|---|---|
| `expedientes/routes.py`: `pool_explorador_fs`, `pool_registrar_rutas` | **Eliminar** (registro in situ; sin sustituto directo, §H) |
| `expedientes/routes.py`: `pool_abrir_en_carpeta`, `abrir_carpeta_expediente` | **Eliminar** (absorbe #853) |
| `expedientes/routes.py`: descarga, subida, `pool_editar_documento`, `pool_borrar_documento`, listado y JSON del pool | **Actualizar**: almacén; la `url` deja de ser editable (sustitución con motivo); el nombre, de `nombre` y no de la `url` (2026-10-02); borrar va a la papelera (fase 7); descarga del PDF para firma con regeneración si está desfasado (fase 6) |
| Ruta nueva: «Aportar desde otro expediente» (listado plano con búsqueda) | **Crear** |
| `app/routes/api_escritos.py` | **Actualizar**: fuera `ruta` y `uri_explorador` en la respuesta |
| `app/routes/api_expedientes.py` | **Actualizar**: `puede_abrir_carpeta`; `_nombre_documento` lee `nombre` (2026-10-02) |
| `app/routes/api_huerfanos.py` | **Actualizar**: `puede_abrir_carpeta`; el nombre, de `nombre` (2026-10-02). **Fallo silencioso** (2026-10-02): el filtro SQL `~Documento.url.like('bddat://%')` descarta las filas con `url` NULL (`NOT (NULL LIKE …)` es NULL) y dejaría vacío el radar de huérfanos sin error |
| `seguimiento_y_huerfanos/templates/…/_inspector_huerfano.html` | **Actualizar** (2026-10-02): el nombre, de `nombre` |
| `admin_plantillas/routes.py` y sus plantillas (`form.html`, `_detalle_fragmento.html`, `_editar_fragmento.html`, `_explorador_fragmento.html`, `_panel_tokens.html`) | **Actualizar** (fase 4): subida y sustitución validadas, prueba con expediente real, fragmentos con tabla; fuera explorador, `bddat-explorador://` y el motor de Word |
| `expedientes/templates/expedientes/pool_documentos.html` | **Actualizar** |
| `app/static/js/plantillas-inspector.js` | **Actualizar** (fase 4) |
| `react-src`: `Despensa.jsx`, `MenuContextual.jsx`, `Inspector.jsx`, `ElaborarEditor.jsx`, `api.js` | **Actualizar**: fuera «abrir carpeta» y la casilla B5 de abrir carpeta tras generar; «Editar» (fase 5); aviso de plantilla desfasada (fase 4) |

**Tests** (36 ficheros tocan el disco o sus símbolos, 2026-10-02)

| Consumidor | Acción |
|---|---|
| `test_667_mover_documento_esftt`, `test_926_documento_comparte_fichero` | **Eliminar**: prueban el movimiento, que desaparece. Sustituir por tests de «vincular no toca el almacén» y de deduplicación |
| `test_730_regeneracion_escritos`, `test_666_ingesta_multipart`, `test_665_ruta_esftt`, `test_365_bddat_uri` (parte local) | **Actualizar** (reescritura parcial) |
| `conftest.py` (`fs_tmp`) y los que montan carpetas: `test_928_*`, `test_657_658_notificar`, `test_717`, `test_677`, `test_428_*`, `test_373`, `test_827`, `test_838`, `test_574`, `test_367`, `test_885`, `test_442`, `test_678`, `test_341`, `test_328`, `test_591`, `test_726`, `test_568`, `test_967`, `test_968` (2026-10-02), `smoke/test_smoke_pool_documentos`, `smoke/test_smoke_plantillas_inspector` y el resto de la lista | **Actualizar**: almacén temporal en lugar de árbol de carpetas |
| `test_847_pool_recurso_no_contemplado` | **Actualizar** (2026-10-02): `puede_abrir_carpeta` |
| `test_932::test_ruta_pdf_del_certificado` | **Eliminar** con la columna (2026-10-02) |
| Los casos del motor de Word: `test_726` (nombre y MIME `.docx`), `test_727::test_docx_no_tiene_avisos_de_canonicidad` | **Eliminar** (fase 4; 2026-10-02) |
| Nuevo (2026-10-02): el radar de huérfanos lista un documento con `url` NULL (fallo silencioso de `api_huerfanos.py`) | **Crear** |
| Nuevos: almacén, sustitución y congelado, PDF sincronizado, WebDAV, formatos, limpieza (qué cuenta como referencia), integridad, sustitución de plantillas, aportar desde otro expediente | **Crear** |
| Nuevos (2026-10-01): consumidores del modelo de rutas y de la `ref` con lista de ficheros permitidos (fase 0, §I); el exportador solo importa la biblioteca estándar (fase 1, §H) | **Crear** |

**Scripts**

| Consumidor | Acción |
|---|---|
| `scripts/semilla_test.py` | **Actualizar**: variables nuevas; plantillas desde las bases del repo en vez de desactivarlas (fase 4) |
| `scripts/expedientes_dummy/limpiar_reciclables.py` | **Actualizar** |
| El resto de `scripts/expedientes_dummy/` | **Dejar** (2026-10-02): suben por la ruta multipart, que se conserva |
| `scripts/cliente/` (`bddat-explorador://`) | **Eliminar** (fase 4: la gestión de plantillas lo usa hasta entonces; 2026-10-02): el botón «Editar» no necesita instalador, usa `vnd.libreoffice.command:`, que registra el LibreOffice corporativo (§D, #1000) |
| `scripts/nube/` (`preparar_entorno.sh`, `README.md`) | **Actualizar**: variables del `.env` |
| `scripts/poc_webdav/` | **Dejar**: evidencia de §D |

**Migraciones**

| Consumidor | Acción |
|---|---|
| Históricas que tocan `documentos.url`, `hash_md5`, `ruta_plantilla`, `ruta_pdf` (inicial, `45b0d1302dd4`, `91a701524476`, 373, 402, 403, 404, 776, 849, `20c5d1e9d782`) | **Dejar** (congeladas) |
| Nueva: tablas y columnas de §C y §J, `CHECK`, bajas de columnas; script de migración de ficheros (§L) | **Crear** |

**Documentación**

| Consumidor | Acción |
|---|---|
| ADR-032, ADR-006, ADR-035 | **Dejar**, con nota de cabecera que remite aquí (hecho con este ADR; puesta al día el 2026-10-02: `fichero_ref` en vez de `fichero_sha256`, sin buzón, y el motor `.docx` de ADR-035 §2 se retira) |
| ADR-009, ADR-028, ADR-030, ADR-034, ADR-044, `historial/*` | **Dejar** (congelados) |
| `DISEÑO_GENERACION_ESCRITOS.md` (procedimiento del supervisor, B5, B6), `DISEÑO_SUBSISTEMA_DOCUMENTAL.md`, `ANALISIS_DESPLIEGUE.md` (§6, §9), `ANALISIS_ESCALABILIDAD.md` (§3.6), `INVENTARIO_BACKEND.md`, `MATRIZ_COBERTURA_BDDAT.md` (N009, N021, N077), `scripts/cliente/README.md`, `tests/README.md`, `.env.example` | **Actualizar al implementar**: hasta entonces describen lo que hay |
| `docs/guias/REGLAS_DESARROLLO.md` | **Actualizar al implementar** (2026-10-01): sección «la ficha, no el fichero» — la congelación del modelo de rutas, hecha en la fase 0 (#1001); solo el subsistema de almacenamiento ve la `ref`, en la fase 1 (§I) |

---

## Por qué

- **Una sola fuente de verdad.** La BD dice qué hay y el almacén solo guarda bytes que nadie más puede tocar. Los problemas de la lista del contexto no se parchean uno a uno: desaparecen con su causa.
- **Sustituible sin tocar el resto de BDDAT.** El almacén se habla desde un puerto de cuatro operaciones (`escribir`/`leer`/`existe`/`borrar` sobre una referencia opaca, §B); un gestor documental corporativo (p. ej. Alfresco, que ya usa la Junta) sería un adaptador nuevo, no una reescritura de los servicios que hoy dependen del almacén.
- **La custodia sigue donde está.** El almacén vive en el share corporativo, con su copia de seguridad. Como los ficheros no cambian nunca, la copia incremental es trivial, y el hash identifica qué recuperar.
- **Más sencillo, no más complejo.** Se borra más código del que se escribe: movimientos, colisiones, sufijos, la matriz de regeneración, el explorador del servidor, el registro in situ y los `explorer` del servidor. Y sin versiones no hay que gestionar historiales, purgas ni «volver atrás».
- **La edición se conserva sin la puerta trasera.** La prueba de concepto demostró que LibreOffice edita contra BDDAT sin acceso al share, con bloqueo.
- **El PDF que se firma es siempre el del último borrador guardado**, y no hay forma de que el usuario lo genere desde una versión anterior.
- **Trazabilidad que hoy no existe:** de un firmado se llega al borrador congelado, y de este a la plantilla y los fragmentos exactos que lo produjeron.
- **Agnóstico al despliegue:** funciona igual con Flask en un PC dedicado que en un servidor de Informática, sin nada que dependa de que el servidor vea el disco del usuario.

---

## Consecuencias

- **ADR-032 §1-§4 quedan sobrepasados** en cuanto se implemente este ADR. ADR-006 pierde el esquema «ruta local». ADR-035 §6 deja de ser cierto en lo del pool y de `bddat-explorador://`.
- **#953** (ya cerrado) deja de tener objeto al desaparecer las rutas locales. **#853** queda absorbido. **#852** sigue vigente: el almacén vive en el share y necesita montaje `soft`, semáforo y medición igual.
- **N009** se cubre mejor que hoy: el árbol legible ya no lo puede estropear nadie, y el manifiesto permite reconstruirlo. **N077** (duplicados) sale en parte gratis con la deduplicación por hash, con el límite de §H. **N021** (CRUD de rutas) pierde sentido: las rutas son de despliegue (§K).
- **Informática** (#151) tiene que proporcionar las tres carpetas con sus permisos, la cuenta de servicio y LibreOffice en el servidor.
- **Los usuarios** pierden el acceso libre a las carpetas de los expedientes desde el Explorador, y la edición del borrador pasa por el botón «Editar». Es el cambio de costumbre que compra la robustez. Tienen que saber que «Guardar como» crea una copia que BDDAT no ve (§D).
- **El supervisor** versiona las plantillas por su cuenta, fuera de BDDAT (§J).
- **El protocolo `bddat-explorador://`** se queda sin uso, salvo que su instalador se reutilice para lanzar Writer.

---

## Alternativas descartadas

### A. Mantener el modelo actual con parches (#953, #852, #853, auditoría de hashes)

Cada parche arregla un síntoma y deja la causa. La puerta trasera, las rutas entre plataformas y la complejidad de los movimientos siguen ahí.

### B. «Carpeta blindada»: la misma estructura, con los usuarios en solo lectura

Cierra el borrado a mano, pero no el problema de las rutas ni la complejidad de mover y renombrar. Además, la edición del `.odt` necesitaría igualmente la vía de §D. Solo tendría sentido si otras personas del servicio tuvieran que seguir trabajando sobre las carpetas al margen de BDDAT, y no es el caso.

### C. Guardar los ficheros en PostgreSQL (`bytea` o large objects)

Daría atomicidad con los metadatos. Pero con proyectos de cientos de MB, los backups de la BD se vuelven pesados (harían falta copias físicas incrementales) y la custodia pasaría al PC dedicado, en contra de ANALISIS_DESPLIEGUE §6. La decisión original de no meter los ficheros en la BD era correcta; el fallo fue dejar que los usuarios pudieran tocarlos.

### D. Almacén de objetos S3 (MinIO, Garage) con bloqueo WORM

Un cliente HTTP con timeouts evitaría el cuelgue de CIFS, y el bloqueo WORM daría inmutabilidad incluso frente a administradores. Pero es otro servicio que operar, sin equipo de sistemas, y sus datos acabarían en el disco del PC dedicado, no en el share corporativo. Revisar si Informática llega a ofrecer S3. El puerto de almacenamiento agnóstico (§B) deja esta puerta abierta sin comprometer nada ahora: un adaptador S3, o contra un gestor documental como Alfresco, implementaría las mismas cuatro operaciones sin tocar el resto de BDDAT.

### E. Gestor documental o edición en el navegador (Nextcloud, Alfresco, Collabora u OnlyOffice por WOPI)

Otro sistema que desplegar y mantener, con la custodia repartida entre dos aplicaciones. La edición por WebDAV con el LibreOffice que ya exige ADR-035 cubre la necesidad.

### F. Seguir con MD5

El hash pasa a ser la identidad del fichero en el almacén. Con colisiones de MD5 fabricables a propósito, un PDF podría hacerse pasar por otro.

### G. Espejo legible completo y permanente de todos los expedientes

Doblaría el espacio (SMB no admite enlaces fiables y habría que copiar). El manifiesto más la exportación al finalizar cubren N009 sin ese coste (decisión de Carlos).

### H. PDF para firma generado en el PC del usuario

No garantiza que el PDF sea el borrador guardado: el usuario puede retocar después de guardar.

### I. Importación automática del buzón

El tipo de documento y la fecha administrativa necesitan a una persona. Un proceso que importara solo dejaría fichas incompletas.

### J. Versiones de documentos (primera redacción de este ADR)

Tabla `documento_versiones`, una versión por sesión de edición, sustitución como versión nueva y purga configurable. Retirada el 2026-09-26: el borrador y el PDF para firma son utilitarios, y poder volver a una versión anterior del borrador es una forma de llevar al PDF un error que ya se había corregido. Los documentos de fuera no tienen versiones (un informe corregido es otro documento). La red de seguridad que quedaba —recuperar un contenido anterior ante un desastre— la da la papelera, sin exponerla al usuario (§F).

### K. Versiones de plantillas con publicación (primera redacción), o dos punteros «publicada» y «en edición»

Resolvían la edición en vivo y la trazabilidad, pero a costa de tablas de versiones, estados y un ciclo de publicación dentro de BDDAT. Editar en el PC del supervisor y sustituir de forma atómica al subir resuelve lo mismo; la trazabilidad la dan el hash guardado en cada borrador y la bitácora (§J).

### L. PDF para firma como conversión en caché, fuera de los documentos

Evitaba una ficha para el PDF, pero obligaba a inventar un mecanismo propio de almacenamiento y de descarga. Como documento más, usa la misma descarga, la misma limpieza y el mismo vínculo con la tarea; la sincronización es una columna (§D).

### M. Deshabilitar «Guardar como» en LibreOffice

Se puede con su configuración, pero la desactiva para todos los documentos del puesto, no solo para los de BDDAT. Se prefieren las mitigaciones de §D.

### N. Buzón por usuario en el share, desde la fase 1 (aparcada, no descartada)

ADR-032 justificaba mantener una vía sin subida multipart para no forzar «una vuelta innecesaria por el navegador» con ficheros que el servidor ya tiene al lado. Sigue siendo cierto para proyectos grandes, pero ese doble salto de red ocurre, como mucho, una vez por expediente (al dar de alta) — y el propio fichero grande ya cruzó la red del usuario una vez, al bajarlo de PTWANDA/BandeJA. Construir una infraestructura permanente (`BUZON_BASE/<usuario>/`, sus permisos, `_importados/<fecha>/`, el listado en la UI) para ahorrar un trámite ocasional, sin datos de que sea un problema real, no se justifica ahora. La fase 1 entra solo por subida multipart (§H); si la migración o el uso real muestran que los ficheros grandes son una fricción de verdad, se retoma esta alternativa con datos delante.

### O. Camino de vuelta al modelo de carpetas (propuesto y retirado el 2026-10-01)

Un script inverso de §L que devolviera cada fichero a su carpeta y rellenara `documentos.url`, junto con la bajada de las migraciones y un test de ida y vuelta mantenido en cada fase. Se retira porque no garantiza nada. Antes de producción no protege nada: los datos de desarrollo se tiran. Después no es realista: volver exige desplegar el código anterior a este ADR, y el desarrollo sigue construyendo sobre el modelo nuevo (el frontend de notificaciones, #929, espera a las fases 0-3), así que todo lo hecho encima se tiraría o habría que adaptarlo al modelo anterior, y en producción. Cruzado el umbral, cada paso aleja más del sistema anterior; por eso mismo este ADR se hace ahora, antes de acumular más deuda. Los riesgos conocidos tienen salida dentro del ADR, sin volver atrás: otro adaptador si Informática no da la carpeta (§A), descargar y volver a subir si la edición por WebDAV falla (§D), y la exportación legible (§H) para quien necesite carpetas. De esta alternativa queda solo la comprobación de la migración de ida (§L).
