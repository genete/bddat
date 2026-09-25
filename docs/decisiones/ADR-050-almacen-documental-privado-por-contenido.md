# ADR-050 — BDDAT, único dueño de los ficheros: almacén privado direccionado por contenido, versiones en BD y edición sin acceso al servidor de ficheros

**Estado:** Adoptada — sin implementar. Se implementa **después de N6** (cierre de la cadena de ADR-049) y **antes de producción** (§I)
**Fecha:** 2026-09-25
**Sobrepasa:** ADR-032 §1-§4 (entrada al pool, rutas relativas en `Documento.url`, movimiento al vincular, naming con MD5 en `pool/`). ADR-032 no queda derogado: describe lo que hay implementado hasta que este ADR se ejecute, y su nota de cabecera lo remite aquí
**Amplía:** ADR-006 (el esquema «ruta local» de `documentos.url` desaparece; `http(s)://` y `bddat://` siguen) · ADR-035 (plantillas y fragmentos pasan al almacén, con versiones y publicación; §6 «lo que no cambia» deja de ser cierto en lo del pool y del protocolo `bddat-explorador://`)
**No cambia:** ADR-010 (N:M documento-tarea) · ADR-027 (pertenencia al expediente por naturaleza, no por mecanismo de almacenamiento) · ADR-044 (reformados como documentos aparte) · el sellado de ADR-036 y de #947 (§F se apoya en él)
**Origen:** discusión del 2026-09-25 a raíz de #953 (validador de `Documento.url` dependiente del sistema operativo)
**Evidencia:** prueba de concepto en [`scripts/poc_webdav/`](../../scripts/poc_webdav/README.md): LibreOffice 24.2 abriendo, bloqueando y guardando un `.odt` contra un WebDAV mínimo en Flask
**Relacionados:** #151 (carpetas y permisos pedidos a Informática, comentario del 2026-09-25) · #852 (resiliencia del share, sigue vigente) · #853 (`explorer /select` en el servidor, lo absorbe este ADR) · #330 (entornos y despliegue) · #954 (sellado de datos en el pool) · N009, N021, N077
**Issues de implementación:** por crear al cerrar N6 (§I)

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
| **Buzón** | `BUZON_BASE/<usuario>/` | cada usuario en la suya | usuarios y BDDAT | ficheros pendientes de importar |
| **Archivo** | `ARCHIVO_BASE` | solo BDDAT | los usuarios, solo lectura | exportación legible de los expedientes finalizados (§H) |

Si la política del servidor de ficheros no permite una carpeta sin acceso de usuarios, la alternativa es el almacén en el disco del servidor de la aplicación con réplica nocturna al share. Funciona igual para BDDAT, pero saca la custodia de donde está hoy.

### B — Almacén direccionado por contenido

```
ALMACEN_BASE/
  sha256/3a/f1/3af1c9…e07b      ← 64 caracteres hexadecimales, sin extensión
  .tmp/                          ← escrituras en curso
  manifiestos/AT-123.json        ← §H
```

- **El nombre es el SHA-256 completo del contenido.** Sin extensión ni nombre original: eso vive en la BD. Sin extensión, nadie abre el fichero con doble clic, y el nombre no choca con nada de Windows (caracteres prohibidos, nombres reservados, longitud).
- **SHA-256 y no MD5.** El hash pasa a ser la identidad del fichero, no una comprobación. Fabricar dos PDF distintos con el mismo MD5 es trivial y está documentado; con MD5, uno podría hacerse pasar por el otro en el almacén. El coste de calcularlo es despreciable.
- **Dos niveles de subcarpetas** (2 + 2 caracteres): listar en SMB una carpeta con decenas de miles de ficheros es lento.
- **Escritura:**
  1. el fichero se escribe **a trozos** en `.tmp/`, calculando el hash mientras se escribe, sin cargarlo entero en memoria;
  2. `fsync`;
  3. si el destino ya existe, es el mismo contenido: se borra el temporal y se reutiliza (deduplicación);
  4. si no, se renombra, que es atómico dentro del mismo share;
  5. después, las filas de BD y el commit.

  Si el commit falla, queda un fichero sin referencias, que no hace daño y que recoge la limpieza (§G).
- **Ninguna petición web borra nada del almacén.** Solo borra el proceso de limpieza (§G).

### C — Modelo de datos

**`ficheros`**: el contenido físico. No sabe nada de expedientes, nombres ni tareas.

| Columna | Nota |
|---|---|
| `sha256` `char(64)` PK | nombre en el almacén |
| `tamano` `bigint` | |
| `formato` `text` | MIME **detectado por el contenido** (§E) |
| `creado_en`, `verificado_en` | la segunda la actualiza la comprobación de integridad |
| `estado` | `OK` · `CORRUPTO` · `AUSENTE` |
| `sin_referencias_desde` null | el reloj de la papelera (§G) |

**`documentos`** (existe): la ficha.

| Columna | Qué pasa |
|---|---|
| `id`, `expediente_id`, `tipo_doc_id`, `fecha_administrativa`, `asunto`, `prioridad`, `observaciones` | sin cambios |
| `nombre` | **nueva**: nombre visible y de descarga, editable. Hoy se deduce de la `url` |
| `version_vigente_id` | **nueva**, FK a `documento_versiones` |
| `url` | **solo** `http(s)://` y `bddat://` (ADR-006). `NULL` para un fichero propio |
| `hash_md5` | **desaparece**: el hash vive en `ficheros` |
| `borrado_en` | **nueva**: papelera |

Restricción: `CHECK ((url IS NULL) <> (version_vigente_id IS NULL))`. Un documento es un fichero propio o una referencia, nunca las dos cosas ni ninguna.

**`documento_versiones`**

| Columna | Nota |
|---|---|
| `id`, `documento_id`, `numero` | `UNIQUE (documento_id, numero)` |
| `fichero_sha256` | FK a `ficheros` |
| `nombre_original` | tal cual llegó, en UTF-8, sin sanear. Va en la versión y no en el fichero, porque el mismo contenido puede llegar con dos nombres |
| `origen` | `SUBIDA` · `BUZON` · `GENERADO` · `EDICION` · `CONVERSION` · `SUSTITUCION` · `MIGRACION` |
| `usuario_id`, `creada_en` | |
| `derivada_de_id` null | p. ej. el PDF para firma sale de la versión 5 del borrador |
| `plantilla_version_id` null | solo en `GENERADO` (§J) |
| `motivo` null | obligatorio en `SUSTITUCION` |
| `purgada_en` null | §F |

**`sesiones_edicion`**: la edición por WebDAV (§D). Está en BD y no en memoria porque, con varios workers, cada petición puede caer en uno distinto (ANALISIS_DESPLIEGUE §3).

| Columna | Nota |
|---|---|
| `documento_id`, `usuario_id` | |
| `token_hash` | se guarda el **hash** del token, no el token |
| `caduca_en` | fin de la jornada |
| `lock_token`, `lock_caduca_en` | bloqueo WebDAV |
| `abierta_en`, `cerrada_en`, `version_id` | la versión que la sesión va reescribiendo |

**No cambian:** `documentos_tarea`, `reformados_proyecto`, `certificados`, `diagnosticos`, `notificaciones`, los sellos y la bitácora apuntan a `documentos.id`, que se conserva. **Vincular un documento a una tarea es insertar una fila en `documentos_tarea`, y no mueve ningún fichero.**

**Operaciones**

| Operación | BD | Almacén |
|---|---|---|
| Subir, importar del buzón | ficha + versión 1 | escribe (o reutiliza) |
| Vincular / desvincular | fila en `documentos_tarea` | **nada** |
| Generar escrito | ficha + versión 1 `GENERADO` | escribe |
| Regenerar | versión nueva, si el contenido cambia | escribe |
| Editar en LibreOffice | sesión → versión `EDICION` | escribe |
| Preparar PDF para firma | documento propio, versión `CONVERSION` con `derivada_de_id` | escribe |
| Descargar / abrir | nada | lee |
| Sustituir por error | versión `SUSTITUCION` con motivo; prohibida si está sellado | escribe |
| Borrar | `borrado_en = now()` | **nada** |

La matriz de 8 casos de #730 se reduce a dos: mismo contenido que la versión vigente, no pasa nada; contenido distinto, versión nueva. Si la vigente se retocó a mano, se avisa antes de regenerar; los retoques no se pierden, porque quedan en la versión anterior. Desaparecen las colisiones de nombre y los ficheros apartados.

### D — Borrador, PDF para firma y firmado; edición sin acceso al share

**Tres documentos distintos, no versiones de uno** (ADR-027):

1. **Borrador `.odt`**: auxiliar, no forma parte del expediente (#608). Identidad de #730: tarea + rol + tipo de la plantilla. Tiene versiones.
2. **PDF para firma**: sale de una versión concreta del borrador (`derivada_de_id`). Existe para llevarlo al Portafirmas.
3. **PDF firmado**: documento del expediente, PRODUCIDO de la tarea. Una versión. Sellado.

**El PDF para firma lo genera el servidor** (decisión de Carlos: «preferentemente el servidor»), con `soffice --headless --convert-to pdf`, en segundo plano si tarda. Es la única forma de garantizar que el PDF es exactamente la versión guardada. Exige LibreOffice en la imagen del servidor (pedido en #151) con las fuentes permitidas por ADR-035 §5.

**Enlace firmado ↔ origen.** El Portafirmas reescribe el PDF, así que su hash no coincide. El código del pie (`BDDAT-<tarea>-<letra>`, #182) da la tarea, y dentro de ella se toma la última conversión anterior a la subida. Resultado: **firmado ← PDF para firma ← versión N del borrador ← plantilla vK + fragmentos vM** (§J).

**Edición: WebDAV servido por BDDAT.** El botón «Editar» abre el `.odt` en LibreOffice desde una URL con token (`/dav/<token>/<nombre>.odt`). Guardar hace un `PUT` que BDDAT convierte en versión. La prueba de concepto (`scripts/poc_webdav/`) lo verificó con LibreOffice 24.2 y fija cuatro requisitos de implementación:

1. **`getlastmodified` estable**, la fecha de la versión vigente. LibreOffice la compara al abrir, tras el `LOCK` y antes del `PUT`; si cambia, **aborta el guardado sin enviarlo** (`ErrorCodeIOException 0x11b`).
2. **Una versión por sesión de edición**, no por `PUT`. Guardar sin cambios reescribe `styles.xml` y `settings.xml`, así que el hash no evita versiones vacías. Los guardados intermedios de una sesión reemplazan al anterior.
3. **Conceder los 180 s de bloqueo que pide LibreOffice.** Renueva cuando le quedan ~30 s; con un bloqueo más corto entra en una lluvia de renovaciones. Si se cuelga, el bloqueo caduca solo: mejor que los `.~lock` del share, que alguien tiene que borrar a mano.
4. **Verbos:** `OPTIONS`, `PROPFIND` (`Depth: 0`, también sobre la carpeta padre), `GET`, `LOCK`, `PUT`, `UNLOCK`. Se rechazan `DELETE`, `MOVE`, `COPY`, `MKCOL` y `PROPPATCH`: el almacén nunca pierde nada por esta vía.

Un segundo usuario que abre un documento bloqueado lo ve en solo lectura. Un token caducado no abre. **Alternativa sin nada instalado:** descargar, editar y volver a subir; BDDAT reconoce la tarea por el código del pie.

**Pendiente de verificar en un puesto Windows real** (no bloquea el diseño; lo hace la fase 5, §I): los diálogos gráficos, el autoguardado, cómo lanzar Writer desde el botón (`vnd.libreoffice.command:` si la versión instalada lo registra, o un protocolo propio con el instalador de `scripts/cliente/`) y HTTPS con el certificado corporativo.

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

**Al servirlos:** PDF e imágenes se muestran en el navegador (`X-Content-Type-Options: nosniff`, CSP `sandbox`); el resto se descarga (`Content-Disposition: attachment`). El nombre de descarga es `documentos.nombre`, codificado según RFC 5987: no hay que sanear nada al guardar. **Tamaño máximo:** 500 MB por defecto (§K), escritura a trozos.

### F — Para qué sirven las versiones, y cuándo se purgan

- **Documentos de fuera:** una versión casi siempre. Un informe corregido es **otro documento**, con su fecha, no una versión; igual que un reformado (ADR-044). La única versión 2 legítima es «subí el fichero equivocado»: `SUSTITUCION`, con motivo obligatorio y bitácora, conservando la anterior y **prohibida si el documento está sellado o citado por un certificado** (`sellos.motivo_sellado`). Es lo que hoy no existe: un cambio visible y reversible en lugar de un cambio de `url` sin rastro.
- **Borradores `.odt`:** donde las versiones tienen sentido de verdad.
- **Purga de borradores.** Se hace por orden, no por espacio: un `.odt` de la plantilla base ocupa unos 160 KB.
  1. Los guardados intermedios de una sesión no llegan a ser versión (§D).
  2. Con el firmado vinculado y sellado **y la fase cerrada** (el Portafirmas puede rechazar y hacer volver a editar), se marcan como purgables las versiones del borrador **salvo la que originó el firmado**: es el original editable del acto, útil para una corrección de errores. La versión 1 generada se conserva si así se configura (§K).
  3. El PDF para firma se purga a la vez: ya existe el firmado, y su versión de origen sigue ahí.
  4. Purgar es poner `purgada_en`. El fichero lo borra la limpieza pasado el plazo de gracia, así que una purga equivocada se puede deshacer.

### G — Papelera y limpieza: lo único que borra

Un proceso programado, nocturno:

1. marca `sin_referencias_desde` en los ficheros sin versión viva ni documento sin borrar, y la quita si han vuelto a tener referencias;
2. borra del almacén los que llevan más de N días sin referencias, y luego su fila;
3. borra definitivamente los documentos con `borrado_en` de hace más de N días;
4. lo registra todo en la bitácora.

Con la deduplicación, un fichero compartido por dos documentos solo se borra cuando **ninguno** lo usa. Lo resuelve la consulta, sin contadores. La comprobación periódica de integridad relee cada fichero y recalcula su SHA-256: si no coincide, `CORRUPTO`; si no está, `AUSENTE`. El resultado aparece en el panel del supervisor, y el hash dice qué fichero exacto pedir a Informática de una copia de seguridad. **Restaurar:** primero el almacén y luego la BD. Si sobran ficheros, son huérfanos y los recoge la limpieza; nunca faltan.

### H — N009, «expediente reconstruible sin BDDAT»: manifiesto siempre, exportación al finalizar

Decisión de Carlos:

- **Manifiesto por expediente, siempre.** `ALMACEN_BASE/manifiestos/AT-123.json` se rehace cuando cambia el expediente. Lista cada documento con su nombre, tipo, fecha administrativa, SHA-256 de la versión vigente, tareas y **la ruta ESFTT que le tocaría**, calculada con `ruta_esftt_documento`, que se conserva. Con el almacén y los manifiestos, un script corto reconstruye el árbol legible sin BDDAT ni PostgreSQL.
- **Exportación bajo demanda:** «Exportar expediente» genera un ZIP con el árbol ESFTT legible y el manifiesto.
- **Exportación automática al finalizar el expediente:** el mismo árbol se escribe en `ARCHIVO_BASE`, de solo lectura para los usuarios. Si el expediente se reabre (por un recurso, por ejemplo), la exportación se rehace al volver a finalizar; la anterior se conserva con fecha y no se sobrescribe.

Al escribir el árbol legible, y solo entonces, se adaptan los nombres a Windows (caracteres prohibidos, nombres reservados, longitud de ruta), como hoy en `rutas_esftt.py`.

**Buzón.** Sustituye al registro in situ (`pool_explorador_fs` + `pool_registrar_rutas`), que es justo la puerta trasera. Conserva lo que ADR-032 quiso mantener al descartar «solo subida por navegador»: no obligar a pasar por el navegador ficheros que ya están en el share. BDDAT lista el buzón del usuario, el usuario elige ficheros y metadatos, BDDAT los copia al almacén y mueve el original a `_importados/<fecha>/`. La importación la dispara el usuario, no un proceso automático, porque tipo y fecha necesitan a una persona.

### I — Secuenciación

Medido el 2026-09-25 contra la cadena de ADR-049: los dos trabajos **apenas se tocan**. La cadena opera sobre la ficha (fechas, tipos, vínculos, sellos, certificados); este ADR cambia lo que hay debajo. Los servicios de la cadena (`sellos`, `cert_cumplimiento_fase`, `certificados`, `actos_solicitud`, `plazos`) no tocan el disco. El único roce es `mutaciones_arbol.py`, que hoy mueve el fichero al vincular (N5 y #568 vinculan justificantes).

- **Se implementa después de N6 y antes de producción.** Esperar no encarece el cambio: no hay datos reales, y N4b y N6 no añaden consumidores del disco.
- **Regla mientras tanto:** nada nuevo de la cadena escribe ficheros en disco. Los certificados, en HTML y `bddat://`, como decidió #947.
- **Válvula:** si en N5 el conflicto en `mutaciones_arbol.py` pesa más de lo previsto, se adelanta solo la fase 2 (vincular sin mover).
- **Ya hecho, fuera de este ADR:** #953 (validador, PR #959) y el pedido a Informática en #151.

Fases, con tamaños estimados por comparación con los PR de la cadena (#934 N1: 56 ficheros, +2.942/−660; #948 N4: 25 ficheros, +2.074). Es orden de magnitud, no compromiso:

| Fase | Contenido | Comparable a |
|---|---|---|
| 0 | Revalidar la tabla de consumidores (§M) y crear los issues | — |
| 1 | Almacén, `ficheros`, `documento_versiones`, subida, descarga, lectores, migración de datos de desarrollo | N1 |
| 2 | Vincular sin mover; regeneración de 8 casos → 2; PDF de `CERT_FIN_INSTRUCCION` al almacén | N2b (más borrar que escribir) |
| 3 | Fuera explorador del servidor, registro in situ y `explorer`; buzón | mediano |
| 4 | Plantillas y fragmentos (§J) | N4, con más interfaz |
| 5 | Edición por WebDAV, sesiones en BD, lanzador en el cliente; verificación en Windows | mediano |
| 6 | PDF para firma en el servidor | pequeño; depende del Dockerfile (#330) |
| 7 | Manifiestos, exportación, limpieza, integridad, parámetros (§K) | mediano, independiente |

Las fases 0-4 van antes de producción. Las fases 5-7 pueden ir al ritmo del despliegue: hasta la 5, el borrador se retoca descargándolo y volviéndolo a subir (§D), y hasta la 6, el PDF para firma lo exporta el usuario.

### J — Plantillas y fragmentos

**Hoy:** `plantillas.ruta_plantilla` apunta a un fichero bajo `PLANTILLAS_BASE/plantillas/`. **No hay subida desde el navegador**: el supervisor copia el `.odt` al share y lo elige con el explorador del servidor. **Los fragmentos no tienen tabla**: son ficheros `PLANTILLAS_BASE/fragmentos/<Nombre>.odt` buscados por nombre al encontrar `{{r Nombre }}`. Además del problema de fondo (el supervisor necesita escribir en el share), hay tres propios:

- **Si falta un fragmento, el escrito sale sin él sin que nadie lo sepa** (`generador_escritos_odt._insertar_fragmentos`: un `logger.warning` y sigue). Una resolución sin fundamentos de derecho o sin pie de recurso es un error jurídico.
- **Editar una plantilla la cambia en vivo** para todos los tramitadores, también a medio editar o con un fallo.
- **No se sabe qué versión de la plantilla produjo un escrito** (la pregunta de trazabilidad que ANALISIS_ESCALABILIDAD §4.1 dejaba sin respuesta).

**Decisión:** mismo almacén, versiones **con publicación**: una versión nueva no entra en uso hasta que alguien la publica.

- `plantillas` conserva sus metadatos; `ruta_plantilla` se sustituye por `version_publicada_id`. **Nueva** `fragmentos` (`id`, `nombre` único —la clave de `{{r Nombre }}`—, `descripcion`, `activo`, `version_publicada_id`). **Nuevas** `plantilla_versiones` y `fragmento_versiones`, con la forma de `documento_versiones` más `estado` (`BORRADOR` · `PUBLICADA` · `RETIRADA`) y `validacion` (JSON: resultado de `validar_plantilla` y de la canonicidad de #727). Pueden ser una sola tabla con dos FK excluyentes; separadas se leen mejor.
- **Ciclo del supervisor:** crear (descarga la base canónica, edita en Writer, **sube desde el navegador**; versión 1 en `BORRADOR`, validada) → editar (WebDAV, §D; la publicada no se toca) → probar (genera con un expediente real sin guardar nada: la necesidad A2, que estaba aplazada) → publicar (solo si la validación pasa; la anterior queda `RETIRADA`) → volver atrás (publicar una versión anterior).
- **Fragmentos:** se publican igual. Antes de publicar se muestra en cuántas plantillas publicadas se usa: publicar un fragmento las cambia todas a la vez, que es lo que se quiere (p. ej. el pie de recurso tras un cambio legal), pero con el alcance a la vista. El nombre no se puede cambiar si alguna plantilla publicada lo usa. Publicar una plantilla exige que existan y estén publicados todos los fragmentos que cita. **Al generar, un fragmento que falte detiene la generación con error.**
- **Trazabilidad:** la versión `GENERADO` del borrador guarda `plantilla_version_id`, y una tabla `generacion_fragmentos (documento_version_id, fragmento_version_id)` las versiones exactas insertadas. El motor ya devuelve la lista de insertados; solo falta guardarla.
- **Motor:** `generar_escrito` trabaja con bytes en vez de rutas. Recibe la plantilla y una función que devuelve el fragmento publicado por nombre. No toca el disco, y los tests dejan de necesitar carpetas temporales.
- **Las bases canónicas siguen en el repositorio** (`app/data/plantillas_base/`): son código y se versionan con git. Desaparece el paso de copiarlas a `PLANTILLAS_BASE` (ANALISIS_DESPLIEGUE §9).
- **Purga:** las versiones publicadas alguna vez no se purgan nunca (son la trazabilidad de los escritos y pesan poco); los borradores nunca publicados, con los parámetros de §K.

### K — Parámetros configurables por el administrador

En `ConfiguracionSistema`, que ya existe. Cada cambio va a la bitácora. Los límites impiden que un error de configuración vacíe la papelera en un día o deje el almacén sin comprobar:

| Parámetro | Por defecto | Límite |
|---|---|---|
| Días de papelera antes del borrado definitivo | 90 | mínimo 7 |
| Cuándo se purgan las versiones del borrador | al cerrar la fase | a elegir: al cerrar la fase · N días tras sellarse el firmado · nunca |
| Conservar la versión 1 generada | no | — |
| Tamaño máximo por fichero | 500 MB | nunca por encima del límite de despliegue (nginx/Flask) |
| Formatos admitidos | toda la lista de §E | se pueden **desactivar**, no añadir: añadir exige código que los reconozca |
| Frecuencia de la comprobación de integridad | semanal | mínimo mensual |

**No son configurables desde la aplicación** las rutas (`ALMACEN_BASE`, `BUZON_BASE`, `ARCHIVO_BASE`): son de despliegue, en variables de entorno. Cambiarlas desde la web con datos dentro lo rompería todo.

### L — Migración

- Cada documento con ruta local: se lee el fichero, se guarda en el almacén y se crea la versión 1 `MIGRACION`, con el nombre original sin el prefijo de hash del pool (`3af1c9e0_`). Los que no se encuentren salen en un informe.
- Cada plantilla: su fichero pasa a versión 1 `PUBLICADA`. Cada `.odt` de `fragmentos/`: fila en `fragmentos` más versión 1 `PUBLICADA`.
- Sin producción, es un script de una tarde; se valida contra la BD de desarrollo del PC.

### M — Consumidores (REGLAS_DESARROLLO §Análisis de impacto previo)

Inventario del 2026-09-25 sobre `develop` en `d3bb6e0`. **Se revalida en la fase 0** antes de escribir código: la cadena de ADR-049 sigue avanzando.

**Modelos y servicios**

| Consumidor | Acción |
|---|---|
| `app/models/documentos.py` | **Actualizar**: `url` solo `http(s)`/`bddat`; `nombre`, `version_vigente_id`, `borrado_en`; fuera `hash_md5`, `ruta_absoluta()` y la rama local del validador; `resolver_url()` lee del almacén |
| `app/models/plantillas.py` | **Actualizar**: `ruta_plantilla` → `version_publicada_id` |
| `app/models/certificados_fase.py` | **Actualizar**: fuera `ruta_pdf` (ruta absoluta en disco) |
| Modelos nuevos: `ficheros`, `documento_versiones`, `sesiones_edicion`, `fragmentos`, `plantilla_versiones`, `fragmento_versiones`, `generacion_fragmentos` | **Crear** |
| `app/services/rutas_esftt.py` | **Actualizar**: se conserva `ruta_esftt_documento` (manifiesto y exportación); **eliminar** `mover_a_esftt`, `mover_a_pool`, `nombre_pool_unico`, `ruta_pool_documento`, `ruta_destino_esftt_fichero` y el MD5 |
| `app/services/ingesta_pool.py` | **Actualizar**: escribe en el almacén |
| `app/services/regeneracion_escritos.py` | **Actualizar**: 8 casos → 2; fuera el apartado de ficheros |
| `app/services/generador_escritos.py`, `generador_escritos_odt.py`, `generador_escritos_docx.py` | **Actualizar**: bytes, fragmentos por tabla, fragmento ausente = error; fuera `guardar_documento` a ruta y `_ruta_plantilla` |
| `app/services/generador_cert.py`, `cert_fin_instruccion.py` | **Actualizar**: PDF al almacén; fuera `_borrar_pdf` (lo hace la limpieza) |
| `app/services/mutaciones_arbol.py` | **Actualizar**: fuera las llamadas a `mover_*`; la lectura del hook de #717 pasa por el almacén |
| `app/services/extraccion_texto_documento.py`, `context_builders/contexto_analisis_documental.py` | **Actualizar**: leen del almacén |
| `app/services/alta_expediente.py` | **Actualizar**: ingesta nueva; fuera el `os.remove` de limpieza en fallo |
| `app/services/sellos.py` | **Actualizar**: `motivo_sellado` también impide versiones nuevas |
| `app/services/detalle_nodo.py` | **Actualizar**: `puede_abrir_carpeta` desaparece; «Editar» / descargar |
| `app/config.py` | **Actualizar**: `FILESYSTEM_BASE` → `ALMACEN_BASE`, `BUZON_BASE`, `ARCHIVO_BASE`; fuera `PLANTILLAS_BASE` |
| Servicios nuevos: almacén, WebDAV, conversión a PDF, limpieza, integridad, manifiesto y exportación, detección de formato | **Crear** |

**Rutas, módulos, plantillas HTML y JS**

| Consumidor | Acción |
|---|---|
| `expedientes/routes.py`: `pool_explorador_fs`, `pool_registrar_rutas` | **Eliminar** (buzón) |
| `expedientes/routes.py`: `pool_abrir_en_carpeta`, `abrir_carpeta_expediente` | **Eliminar** (absorbe #853) |
| `expedientes/routes.py`: descarga, subida, `pool_editar_documento`, `pool_borrar_documento` | **Actualizar**: almacén; la `url` deja de ser editable (sustitución con motivo); borrar va a la papelera |
| `app/routes/api_escritos.py` | **Actualizar**: fuera `ruta` y `uri_explorador` en la respuesta |
| `app/routes/api_expedientes.py`, `api_huerfanos.py` | **Actualizar**: `puede_abrir_carpeta` |
| `admin_plantillas/routes.py` y sus plantillas (`form.html`, `_detalle_fragmento.html`, `_editar_fragmento.html`, `_explorador_fragmento.html`, `_panel_tokens.html`) | **Actualizar**: subida, versiones, publicación; fuera explorador y `bddat-explorador://` |
| `expedientes/templates/expedientes/pool_documentos.html` | **Actualizar** |
| `app/static/js/plantillas-inspector.js` | **Actualizar** |
| `react-src`: `Despensa.jsx`, `MenuContextual.jsx`, `Inspector.jsx`, `ElaborarEditor.jsx`, `api.js` | **Actualizar**: «abrir carpeta» → «Editar» / descargar; fuera la casilla B5 de abrir carpeta tras generar |

**Tests** (35 ficheros tocan el disco o sus símbolos)

| Consumidor | Acción |
|---|---|
| `test_667_mover_documento_esftt`, `test_926_documento_comparte_fichero` | **Eliminar**: prueban el movimiento, que desaparece. Sustituir por tests de «vincular no toca el almacén» y de deduplicación |
| `test_730_regeneracion_escritos`, `test_666_ingesta_multipart`, `test_665_ruta_esftt`, `test_365_bddat_uri` (parte local) | **Actualizar** (reescritura parcial) |
| `conftest.py` (`fs_tmp`) y los que montan carpetas: `test_928_*`, `test_657_658_notificar`, `test_717`, `test_677`, `test_428_*`, `test_373`, `test_827`, `test_838`, `test_574`, `test_367`, `test_885`, `test_442`, `test_678`, `test_341`, `test_328`, `test_591`, `test_726`, `smoke/test_smoke_pool_documentos`, `smoke/test_smoke_plantillas_inspector` y el resto de la lista | **Actualizar**: almacén temporal en lugar de árbol de carpetas |
| Nuevos: almacén, versiones, WebDAV, formatos, limpieza, integridad, publicación de plantillas | **Crear** |

**Scripts**

| Consumidor | Acción |
|---|---|
| `scripts/semilla_test.py` | **Actualizar**: variables nuevas; plantillas desde las bases del repo en vez de desactivarlas |
| `scripts/expedientes_dummy/limpiar_reciclables.py` | **Actualizar** |
| `scripts/cliente/` (`bddat-explorador://`) | **Eliminar**, o reutilizar su instalador para el lanzador de «Editar» (fase 5) |
| `scripts/nube/` (`preparar_entorno.sh`, `README.md`) | **Actualizar**: variables del `.env` |
| `scripts/poc_webdav/` | **Dejar**: evidencia de §D |

**Migraciones**

| Consumidor | Acción |
|---|---|
| Históricas que tocan `documentos.url`, `hash_md5`, `ruta_plantilla`, `ruta_pdf` (inicial, `45b0d1302dd4`, `91a701524476`, 373, 402, 403, 404, 776, 849, `20c5d1e9d782`) | **Dejar** (congeladas) |
| Nueva: tablas de §C y §J, `CHECK`, bajas de columnas; script de migración de ficheros (§L) | **Crear** |

**Documentación**

| Consumidor | Acción |
|---|---|
| ADR-032, ADR-006, ADR-035 | **Dejar**, con nota de cabecera que remite aquí (hecho con este ADR) |
| ADR-009, ADR-028, ADR-030, ADR-034, ADR-044, `historial/*` | **Dejar** (congelados) |
| `DISEÑO_GENERACION_ESCRITOS.md` (procedimiento del supervisor, B5, B6), `DISEÑO_SUBSISTEMA_DOCUMENTAL.md`, `ANALISIS_DESPLIEGUE.md` (§6, §9), `ANALISIS_ESCALABILIDAD.md` (§3.6), `INVENTARIO_BACKEND.md`, `MATRIZ_COBERTURA_BDDAT.md` (N009, N021, N077), `scripts/cliente/README.md`, `tests/README.md`, `.env.example` | **Actualizar al implementar**: hasta entonces describen lo que hay |

---

## Por qué

- **Una sola fuente de verdad.** La BD dice qué hay y el almacén solo guarda bytes que nadie más puede tocar. Los problemas de la lista del contexto no se parchean uno a uno: desaparecen con su causa.
- **La custodia sigue donde está.** El almacén vive en el share corporativo, con su copia de seguridad. Como los ficheros no cambian nunca, la copia incremental es trivial, y el hash identifica qué recuperar.
- **Más sencillo, no más complejo.** Se borra más código del que se escribe: movimientos, colisiones, sufijos, la matriz de regeneración, el explorador del servidor, el registro in situ y los `explorer` del servidor.
- **La edición se conserva sin la puerta trasera.** La prueba de concepto demostró que LibreOffice edita contra BDDAT sin acceso al share, con bloqueo y versiones.
- **Trazabilidad que hoy no existe:** de un firmado se llega a la versión del borrador, la de la plantilla y las de los fragmentos que lo produjeron.
- **Agnóstico al despliegue:** funciona igual con Flask en un PC dedicado que en un servidor de Informática, sin nada que dependa de que el servidor vea el disco del usuario.

---

## Consecuencias

- **ADR-032 §1-§4 quedan sobrepasados** en cuanto se implemente este ADR. ADR-006 pierde el esquema «ruta local». ADR-035 §6 deja de ser cierto en lo del pool y de `bddat-explorador://`.
- **#953** (ya cerrado) deja de tener objeto al desaparecer las rutas locales. **#853** queda absorbido. **#852** sigue vigente: el almacén vive en el share y necesita montaje `soft`, semáforo y medición igual.
- **N009** se cubre mejor que hoy: el árbol legible ya no lo puede estropear nadie, y el manifiesto permite reconstruirlo. **N077** (duplicados) sale gratis con la deduplicación por hash. **N021** (CRUD de rutas) pierde sentido: las rutas son de despliegue (§K).
- **Informática** (#151) tiene que proporcionar las tres carpetas con sus permisos, la cuenta de servicio y LibreOffice en el servidor.
- **Los usuarios** pierden el acceso libre a las carpetas de los expedientes desde el Explorador, y la edición del borrador pasa por el botón «Editar». Es el cambio de costumbre que compra la robustez.
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

Un cliente HTTP con timeouts evitaría el cuelgue de CIFS, y el bloqueo WORM daría inmutabilidad incluso frente a administradores. Pero es otro servicio que operar, sin equipo de sistemas, y sus datos acabarían en el disco del PC dedicado, no en el share corporativo. Revisar si Informática llega a ofrecer S3.

### E. Gestor documental o edición en el navegador (Nextcloud, Alfresco, Collabora u OnlyOffice por WOPI)

Otro sistema que desplegar y mantener, con la custodia repartida entre dos aplicaciones. La edición por WebDAV con el LibreOffice que ya exige ADR-035 cubre la necesidad.

### F. Seguir con MD5

El hash pasa a ser la identidad del fichero en el almacén. Con colisiones de MD5 fabricables a propósito, un PDF podría hacerse pasar por otro.

### G. Espejo legible completo y permanente de todos los expedientes

Doblaría el espacio (SMB no admite enlaces fiables y habría que copiar). El manifiesto más la exportación al finalizar cubren N009 sin ese coste (decisión de Carlos).

### H. PDF para firma generado en el PC del usuario

No garantiza que el PDF sea la versión guardada: el usuario puede retocar después de guardar.

### I. Importación automática del buzón

El tipo de documento y la fecha administrativa necesitan a una persona. Un proceso que importara solo dejaría fichas incompletas.
