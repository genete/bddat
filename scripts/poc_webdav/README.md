# scripts/poc_webdav/ — Prueba de concepto: editar un `.odt` por WebDAV con LibreOffice

> **Origen:** discusión del 2026-09-25 sobre el almacenamiento de documentos
> (a raíz de #953). La propuesta es que BDDAT sea el único que guarda los ficheros,
> en un almacén privado direccionado por contenido y con versiones en BD, y que
> los usuarios dejen de necesitar acceso al servidor de ficheros. La pieza con más
> riesgo era editar el `.odt` antes de firmar sin ese acceso. Esta prueba contesta
> a una pregunta: **¿puede LibreOffice abrir y guardar un documento servido por
> Flask, con autenticación por token en la URL y sin tocar el share?**
>
> **No es código de BDDAT.** No importa nada de `app/` y no toca la BD.
>
> **Decisión que respalda:** [ADR-050](../../docs/decisiones/ADR-050-almacen-documental-privado-por-contenido.md)
> §D. Los hallazgos de abajo pasan allí como requisitos de implementación.

## Resultado

**Sí.** LibreOffice 24.2.7 abre, bloquea, guarda y desbloquea un `.odt` contra
un WebDAV mínimo escrito en Flask (~350 líneas con el registro de peticiones,
sin dependencias nuevas). Cada
guardado entra como versión nueva en un almacén direccionado por contenido. El
fichero original no se toca nunca.

| # | Escenario | Resultado |
|---|---|---|
| 1 | Abrir por `http://…/dav/<token>/<nombre>.odt`, editar y guardar | ✅ `PUT` → versión nueva atribuida al usuario del token |
| 2 | Un segundo usuario abre mientras el primero edita | ✅ recibe `423` al bloquear y LibreOffice abre **en solo lectura**; su `store()` falla |
| 3 | Reabrir en otro puesto | ✅ se lee la última versión |
| 4 | Esquema nativo `vnd.sun.star.webdav://` | ✅ igual que `http://` |
| 5 | Token caducado | ✅ `403`, no abre |
| 6 | `GET` sirve el blob vigente, con el SHA-256 verificado al leer | ✅ |
| 7 | Edición larga (95 s con un bloqueo de 60 s) | ✅ LibreOffice renueva el bloqueo solo; el otro usuario sigue viéndolo bloqueado y el guardado final entra |

## Hallazgos que condicionan el diseño

1. **`getlastmodified` tiene que ser estable.** LibreOffice la lee al abrir, justo
   después del `LOCK` y otra vez antes del `PUT`. Si cambia (la primera versión de
   la prueba devolvía «ahora»), da el fichero por modificado por otro y **aborta
   el guardado** sin llegar a enviar el `PUT` (`ErrorCodeIOException 0x11b`, Io
   Abort). Tiene que ser la fecha de la versión vigente. Es el error más fácil de
   cometer y el que menos pistas da.
2. **Guardar sin cambios no produce los mismos bytes.** LibreOffice reescribe
   `styles.xml` y `settings.xml` (`comparar_versiones.py`), así que el SHA-256 no
   sirve para evitar versiones vacías. El almacén no se ve afectado: cada fichero
   distinto es un blob más y los idénticos se deduplican. Lo que sí afecta es al
   modelo de versiones: conviene una **versión por sesión de edición** (del
   `LOCK` al `UNLOCK`), no una por `PUT`. Los guardados intermedios de la misma
   sesión reemplazan al anterior, y sus blobs quedan para el recolector.
3. **El bloqueo WebDAV sustituye con ventaja a los `.~lock.*#` del share.**
   LibreOffice pide `Timeout: Second-180` y renueva cuando quedan unos 30 s: con
   un techo de 30 s renueva cada segundo; con 60 s, cada 30 s. **El servidor debe
   conceder lo que se pide (180 s)** y no menos, o provoca una lluvia de
   renovaciones. Si LibreOffice se cuelga, el bloqueo caduca solo en ≤ 3 min. En
   el share, un `.~lock` huérfano bloquea hasta que alguien lo borra a mano.
4. **Verbos que usa de verdad:** `OPTIONS`, `PROPFIND` (siempre `Depth: 0`,
   también sobre la carpeta padre antes del `PUT`), `GET`, `LOCK` (alta y
   renovación con `If:`), `PUT` (con `If: (<locktoken>)`) y `UNLOCK`. No ha pedido
   `PROPPATCH`, `MOVE`, `COPY`, `DELETE` ni `MKCOL`: el servidor los rechaza y el
   almacén nunca borra nada por esta vía. Al haber `LOCK`, LibreOffice no intenta
   crear ficheros `.~lock` en el servidor.
5. **Pide propiedades propias** (`http://ucb.openoffice.org/dav/props/`:
   `IsReadOnly`, `BaseURI`, `TargetURL`, `CreatableContentsInfo`). Basta con no
   devolverlas: sigue funcionando.
6. **La autenticación por token en la ruta funciona sin cambios en el cliente.**
   Ni cookies ni cabecera `Authorization`, así que no aparece ningún diálogo de
   credenciales. Con un token caducado el usuario verá un error genérico de
   LibreOffice, no un mensaje propio: el token debería durar la jornada y
   regenerarse desde el botón «Editar».

## Prueba en un puesto de la Junta (#1000, 2026-10-01)

Prueba manual, con pantallas reales, en un puesto Windows 11 con el LibreOffice
corporativo **7.6.7.2**. El servidor corre con el Python del venv de BDDAT. Los
escenarios los maneja una persona desde la página de botones de `servidor.py`
(`/`), sin `cliente_lo.py`.

| Caso | Escenario | Resultado |
|---|---|---|
| 1 | Botón del navegador (`vnd.libreoffice.command:ofe\|u\|<url>`) → Writer → Ctrl+S | ✅ Sin credenciales; `LOCK` → `PUT` → `UNLOCK` al cerrar |
| 1 | Segundo LibreOffice (otro perfil) sobre el mismo documento | ✅ `LOCK` 423 → aviso «Otro usuario ha bloqueado este archivo» → solo lectura |
| 1 | Autorrecuperación cada minuto, 2 min sin guardar | Ningún `PUT`: la copia va al perfil del usuario, no al servidor |
| 1 | «Guardar una copia», y después Ctrl+S | ✅ No suelta el bloqueo; el Ctrl+S llega |
| 1 | «Guardar como» con otro nombre en la carpeta WebDAV | ⚠️ Ningún `PUT` y ningún aviso (ver hallazgo 8) |
| 1 | Token caducado | ✅ `OPTIONS`/`HEAD` 403: no abre |
| 1 | «Guardar como» al disco, y después Ctrl+S | ✅ `UNLOCK` inmediato; el Ctrl+S ya no llega, como prevé ADR-050 §D |
| 2 | El mismo puesto contra su IP de red | ✅ Igual que contra `127.0.0.1`; proxy de LibreOffice en «Sistema» |
| 3 | Segunda máquina por la VPN (LibreOffice 26.2), dos usuarios a la vez | ✅ Bloqueo y solo lectura entre máquinas |
| 3 | Edición de más de 3 minutos desde la segunda máquina | ✅ Renueva el bloqueo sin que se note y el guardado entra |

Hallazgos (siguen la numeración de arriba):

7. **El lanzador no necesita instalador.** El MSI de LibreOffice registra
   `vnd.libreoffice.command` en `HKLM\SOFTWARE\Classes`, y con él funciona el
   botón en el puesto y en la segunda máquina. El navegador pide confirmación
   para abrir LibreOffice la primera vez desde cada dirección.
8. **«Guardar como» dentro de la carpeta WebDAV.** El diálogo de Windows ni
   ofrece esa carpeta: propone «Documentos». Con los diálogos de LibreOffice sí
   se llega, y solo muestra el documento del token. Al guardar con otro nombre,
   la 7.6 consulta la carpeta sin barra final (`/dav/<token>`); Flask contesta
   con una redirección 308, y LibreOffice abandona en silencio: no hay `PUT` ni
   aviso. El documento sigue apuntando al servidor. Con la 24.2 el resultado
   fue un 403 con error visible. El servidor real tiene que responder a la
   carpeta con y sin barra.
9. **La 7.6 usa `HEAD`** (token caducado, comprobaciones del diálogo de
   guardar), además de los verbos del hallazgo 4.
10. **«Más detalles» en el aviso de bloqueo muestra el `owner` que devuelve el
    servidor** («Nombre de usuario: ana»), no el de LibreOffice. En la 7.6 los
    botones de ese aviso salen sin traducir («Open R/O», «Open Copy»,
    «Notify»); en la 26.2 salen traducidos.
11. **Token caducado.** El error es el genérico de LibreOffice («Error al leer
    los datos desde Internet… HEAD => HTTP/1.1 403 FORBIDDEN»): muestra la
    línea de estado, no el cuerpo, así que el texto no se puede personalizar.

## Lo que esta prueba NO ha verificado

- **El registro de `vnd.libreoffice.command` en otros puestos de la Junta.**
  Solo se ha mirado en el de la prueba.
- **HTTPS** con el certificado corporativo: LibreOffice usa su propio libcurl y
  OpenSSL (lo muestra en su User-Agent) y hay que ver qué almacén de
  certificados de confianza consulta en Windows.
- **Integración en BDDAT:** el token saldría de la sesión Flask (usuario +
  documento + caducidad, en BD y no en memoria, por el multiworker de
  ANALISIS_DESPLIEGUE §3). Los bloqueos también tendrían que vivir en BD.

## Ficheros

| Fichero | Rol |
|---|---|
| `servidor.py` | Flask: almacén direccionado por contenido (`blobs/<sha256>`), versiones en JSON, token en la URL, WebDAV mínimo con `LOCK`. Registra cada petición en `peticiones.jsonl`. En `/`, la página de botones con el bloqueo y las versiones (#1000). |
| `cliente_lo.py` | Maneja LibreOffice por UNO. Cada escenario arranca su propio `soffice` con perfil propio, como puestos distintos. |
| `ejecutar.sh` | Arranca el servidor sobre un directorio limpio, ejecuta los escenarios y para el servidor. |
| `resumen_peticiones.py` | Resume `peticiones.jsonl` (`-v` muestra los cuerpos XML). |
| `comparar_versiones.py` | Compara dos versiones entrada a entrada del ZIP del `.odt`. |

## Reproducir

Requiere LibreOffice con Writer (`libreoffice-writer`) y el módulo `uno`
(`python3-uno` en Debian/Ubuntu), más Flask para el mismo intérprete.

```bash
scripts/poc_webdav/ejecutar.sh /tmp/poc_webdav                       # escenarios 1-6
POC_LOCK_MAX=60 POC_ESPERA_LARGA=95 scripts/poc_webdav/ejecutar.sh /tmp/poc_webdav   # + edición larga
python scripts/poc_webdav/resumen_peticiones.py /tmp/poc_webdav
```

Si hay un proxy HTTP en el entorno, `ejecutar.sh` ya exporta `NO_PROXY` para
`127.0.0.1`: sin eso, LibreOffice y urllib intentan salir por el proxy.

**Prueba manual en Windows** (#1000), con el venv de BDDAT y la página de
botones en `http://<host>:5077/`:

```bash
venv/Scripts/python.exe scripts/poc_webdav/servidor.py <dir_datos> app/data/plantillas_base/carta_base.odt 5077
POC_HOST=<ip_del_puesto> venv/Scripts/python.exe scripts/poc_webdav/servidor.py <dir_datos> app/data/plantillas_base/carta_base.odt 5077
POC_HOST=0.0.0.0 POC_URL_HOST=<ip_del_puesto> venv/Scripts/python.exe scripts/poc_webdav/servidor.py <dir_datos> app/data/plantillas_base/carta_base.odt 5077
venv/Scripts/python.exe -X utf8 scripts/poc_webdav/resumen_peticiones.py <dir_datos>
```

Un segundo usuario en el mismo puesto es otro LibreOffice con perfil propio:
`soffice.exe -env:UserInstallation=file:///<carpeta_perfil> "<url de beto>"`.
