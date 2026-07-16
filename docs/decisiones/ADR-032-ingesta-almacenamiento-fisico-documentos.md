# ADR-032 — Ingesta y almacenamiento físico de documentos: rutas relativas, entrada fija al pool, encaje por vinculación

**Estado:** Adoptada
**Fecha:** 2026-07-16
**Issues:** #664 (A, rutas relativas) · #665 (B, pool + convención de carpetas) · #666 (C, ingesta multipart) · #667 (D, mover al vincular)
**Relacionado con:** ADR-006 (URIs `bddat://`, `resolver_url()`) · ADR-010 (N:M documento-tarea) · ADR-027 (pertenencia documental al EXPEDIENTE) · #180 (creación histórica del pool, origen de la regresión corregida aquí) · #572 (bloqueado hasta esta sesión, ahora ortogonal y desbloqueable en paralelo)

---

## Contexto

Sesión de definición de alcance amplio (apuntada por Carlos el 2026-07-14, ver `docs/CONTEXTO_ACTUAL.md`) sobre organización documental, previa a tocar cualquier pieza suelta del bloque (#572, estructura física de carpetas, N004, N009, N021).

### De un concepto a dos

Cuando se diseñó el pool en #180, existía un único concepto: **el documento ya está en su ubicación definitiva**. El usuario lo descarga de BandeJA o PTWANDA y lo copia a mano a la carpeta del expediente bajo `FILESYSTEM_BASE`; lo único que falta es **localizar su URL** para poder invocarlo después (abrir, vincular a tarea, abrir carpeta contenedora). Como el navegador no expone la ruta local real de un fichero elegido con su diálogo nativo (restricción de seguridad del propio navegador — no del servidor), se resolvió con un explorador de ficheros ad-hoc en JS que navega el filesystem del servidor (`pool_explorador_fs`) y registra la ruta señalada (`pool_registrar_rutas`), sin copiar ni mover nada.

Esta sesión revela un **segundo concepto** que #180 no contempló: el documento **no está necesariamente en su ubicación definitiva** cuando el usuario quiere incorporarlo — puede estar recién descargado en su PC local, sin organizar todavía. Para ese caso no sirve "localizar una URL ya existente"; hace falta un mecanismo de **entrada real de bytes** (subida multipart estándar del navegador — `<input type="file">`), indiferente a si el origen que el usuario navegó en el diálogo era una carpeta del servidor o su disco local.

### La regresión de rutas absolutas

La ruta **relativa** a `FILESYSTEM_BASE` fue la intención desde el origen de #180 (permitir migrar de servidor sin romper referencias — germen de N021). El commit `3a57a8a` ("Pivot: subida real de ficheros al servidor", 2026-03-07 17:19) la implementó así (`url_relativa`) para el mecanismo de subida real que existía entonces. Tres horas después, `a41c80b` ("Reemplazar upload por explorador del servidor de ficheros", 20:35 el mismo día) sustituyó ese mecanismo por el explorador ad-hoc y, como efecto colateral no deliberado del cambio — no mencionado en el commit como decisión — la escritura pasó a `ruta_abs` (absoluta). El docstring de esa función, escrito en ese mismo commit, arrastra desde entonces la contradicción intacta: dice que el parámetro de entrada "es relativa a FILESYSTEM_BASE" y en la frase siguiente que "almacena la ruta absoluta normalizada".

Verificado en BD de desarrollo (2026-07-16): de 88 `documentos.url` con valor, solo **1** es absoluta — y esa única fila viene del generador de escritos internos (`ruta_destino_documento`, patrón `FILESYSTEM_BASE/AT-N/nombre.docx`), no de `pool_registrar_rutas`. Las 27 filas con ruta relativa vienen de `scripts/seed_demo.py` (dataset ficticio, ADR-030), con una convención `expedientes/AT-N/entrada|salida/fecha_nombre.ext` escrita a mano que nunca se conectó al código real. Conclusión: corregir la regresión no requiere migrar datos reales de producción — es una corrección de dos funciones de escritura y una fila.

---

## Decisión

### 1. Dos mecanismos de entrada al pool, según dónde está el documento

- **Registrar in situ** (existente, sin cambio de mecanismo) — el documento ya está en su ubicación definitiva, en cualquier punto bajo `FILESYSTEM_BASE`. Se localiza y registra su URL vía el explorador ad-hoc (`pool_explorador_fs` + `pool_registrar_rutas`). Nunca copia ni mueve.
- **Subida al pool** (nuevo) — el documento no está necesariamente en su ubicación definitiva. Diálogo nativo del navegador (`<input type="file">`, multipart estándar), sin explorador ad-hoc — aquí no hace falta conocer la ruta de origen, solo los bytes. Es indiferente si el origen navegado era una carpeta del servidor o el disco local del usuario: **siempre se copia** al punto de entrada fijo `AT-N/pool/<prefijo-hash-md5>_<nombre-original>` (ruta relativa).

Tras la entrada por cualquiera de los dos mecanismos, las operaciones posteriores son idénticas e indiferentes al origen: asignar a tarea, abrir, abrir carpeta contenedora (navegador o invocación de shell).

### 2. `Documento.url` (esquema local) siempre relativa a `FILESYSTEM_BASE`

Nunca absoluta. La resolución a ruta absoluta ocurre solo en el momento de uso, extendiendo `Documento.resolver_url()` (ADR-006) con este caso — mismo patrón ya usado para despachar `bddat://`. Corrige la regresión de `a41c80b` (#180): recupera la intención original de #180, no introduce un concepto nuevo. El validador `@validates('url')` de `Documento` rechaza cualquier ruta absoluta o fuera de `FILESYSTEM_BASE` para el esquema local.

### 3. Encaje: mover al vincularse por primera vez a una tarea

Al crearse el primer `DocumentoTarea` sobre un documento (rol `PRODUCIDO` —único por diseño, ADR-010— o primer `CONSUMIDO`), se mueve desde su ubicación de entrada (`pool/` u otra) a una carpeta legible derivada de los códigos inmutables de catálogo (`tipos_fases.codigo`, `tipos_tramites.codigo`, `tipos_tareas.codigo` — mismo contrato de inmutabilidad que ya exige N082 para el propio catálogo). Vinculaciones posteriores a otras tareas (multi-consumo, ADR-010 permite N tareas consumidoras) no repiten el movimiento: la primera vinculación fija la ubicación, las siguientes solo referencian — igual que en la tramitación real (p. ej. la respuesta de un organismo no se mueve porque una tarea de traslado la consuma, ya está en su sitio).

Patrón seguro de movimiento: copiar a destino → actualizar `Documento.url` y hacer `commit` → borrar el origen solo tras `commit` exitoso. Si el `commit` falla, queda como mucho una copia huérfana en destino (limpiable sin urgencia) y el documento nunca pierde su referencia válida.

Queda abierto, a fijar durante la implementación del Issue D: si el documento pierde su único vínculo (desvinculación, borrado de tarea), si vuelve a `pool/` para que la carpeta física siga siendo espejo fiel del estado huérfano/vinculado (ADR-027 §2).

### 4. Naming en el pool: hash de contenido

`AT-N/pool/<prefijo-hash-md5>_<nombre-original-saneado>` evita colisiones de nombre y, como beneficio colateral, adelanta la detección de duplicados (N077): mismo contenido, mismo hash, sin necesidad de abrir ficheros. Al salir del pool hacia la carpeta ESFTT legible (punto 3), se recupera el nombre original — el hash solo tiene sentido mientras el documento está sin clasificar.

Algoritmo de naming (#666):

- **Hash:** MD5 completo (32 hex) del contenido, almacenado en `Documento.hash_md5`. No SHA-256 — con el volumen real por expediente (decenas de documentos, nunca miles) MD5 es sobrado para evitar colisiones de contenido, y evita rutas más largas de lo necesario.
- **Prefijo en el nombre:** solo los primeros N caracteres del hash (git-style; N por defecto 8), no el hash completo — el nombre debe seguir siendo reconocible a simple vista en el explorador de Windows. Si el prefijo coincide con el de un fichero ya existente en el pool **con contenido distinto** (colisión real, no duplicado), se extiende un carácter más y se reintenta, recursivamente hasta agotar los 32 caracteres; en ese caso extremo se añade un carácter aleatorio.
- **Duplicado exacto** (mismo hash completo ya presente): la escritura a disco es un no-op — no se duplica el fichero físico — pero si el usuario ha pedido explícitamente subirlo, se crea igualmente el registro `Documento` correspondiente (sin bloquear ni marcar de forma especial; el filtro de negocio completo de N077 queda para más adelante).
- **Nombre original: nunca se trunca por longitud.** Windows no acorta nombres al escribir — un `open()` con ruta demasiado larga falla con error explícito, no corrompe el nombre en silencio. Truncar aquí de forma preventiva, sin certeza de que el límite se vaya a alcanzar, destruiría de forma irrecuperable la parte del nombre que el punto 3 promete devolver íntegra al salir del pool — y protegería el segmento equivocado: si la longitud fuera a ser un problema, pegaría más fuerte en la ruta ESFTT (varios segmentos con padding) que en `AT-N/pool/`, la más corta de todo el árbol. Si algún día hace falta una estrategia de truncado, se decide en #667 con la ruta de destino real delante. El saneado del nombre original se limita a lo estrictamente correctivo: quitar componentes de ruta (`basename`, previene path traversal), sustituir caracteres inválidos en Windows (`\ / : * ? " < > |`, mismo patrón que el segmento organismo del punto 3), recortar espacios/puntos finales y evitar nombres reservados (`CON`, `NUL`, `COM1`…). Un fallo de escritura por ruta excesivamente larga se captura y se reporta como error legible al usuario.

---

## Por qué

- **ADR-027 ya desacopla pertenencia de mecanismo de almacenamiento** ("no por... el mecanismo de almacenamiento") — el `pool/` físico como espejo del estado huérfano/vinculado es la traslación literal de ese principio a disco, no una invención nueva.
- **N009** (expediente reconstruible sin BD) exige que la estructura de carpetas sea predecible por sí sola — de ahí que la convención se derive de códigos de catálogo inmutables y no de nombres libres elegidos por cada persona.
- **Mantener los dos mecanismos de entrada** (no forzar multipart siempre) evita una vuelta innecesaria por el navegador para ficheros que el servidor ya tiene al lado — el caso típico de PTWANDA/BandeJA ya copiados a mano a la carpeta de red.
- **La subida multipart es agnóstica al despliegue**: funciona igual si Flask corre en el PC del usuario (modelo actual) que si algún día se centraliza en un servidor remoto, a diferencia del explorador ad-hoc, que depende de que el proceso Flask vea el disco de quien esté al otro lado del navegador.

---

## Cómo implementar

Resumen — checklist detallado en cada issue, todos milestone M2:

- **#664 (Issue A)** — Rutas relativas a `FILESYSTEM_BASE` (corrección de la regresión de #180): extender `resolver_url()`, actualizar escritores (`pool_registrar_rutas`, `ruta_destino_documento`, `generador_cert.py`) y lectores, validador, migrar la única fila real afectada.
- **#665 (Issue B)** — `pool/` por expediente + convención de carpetas por código de catálogo: servicio de cálculo de ruta ESFTT legible a partir de `tipos_fases.codigo`/`tipos_tramites.codigo`/`tipos_tareas.codigo`. Solo cálculo, no mueve nada todavía.
- **#666 (Issue C)** — Ingesta multipart al pool: endpoint `request.files`, naming con hash MD5 (prefijo abreviado extensible, §4), UI junto al "elegir del servidor" ya existente.
- **#667 (Issue D)** — Mover al vincular por primera vez a una tarea: hook en alta de `DocumentoTarea`, patrón seguro copiar→commit→borrar, regla de primera vinculación gana.

Dependencias: #664 → #665 → {#666, #667} (#666 y #667 en paralelo entre sí una vez estén #664 y #665).

---

## Consecuencias

- **#572** (ADR-027, migración `integra_expediente` + consulta `documentos_del_expediente`) queda confirmado como ortogonal a esta decisión — es puro BD, no toca `Documento.url` ni el filesystem. Desbloqueable en paralelo, pendiente de que Carlos lo reactive explícitamente.
- Sin impacto retroactivo real: la corrección de rutas (Issue A) migra una única fila en BD de desarrollo (ver Contexto).
- El explorador ad-hoc (`pool_explorador_fs`) y su restricción a navegar solo dentro de `FILESYSTEM_BASE` se mantienen sin cambios — la subida multipart no lo sustituye, lo complementa.

---

## Alternativas descartadas

### A. Detectar si el origen del fichero subido está bajo `FILESYSTEM_BASE`, copiando solo si no lo está

Descartada. Añade una rama de lógica innecesaria para distinguir algo que la subida multipart no puede ni necesita saber (el navegador no expone la ruta de origen). Siempre copiar al pool es más simple y uniforme; el explorador in situ ya cubre sin ambigüedad el caso "ya está en su sitio, no hace falta copiar".

### B. Multipart como único mecanismo de entrada, eliminando el explorador in situ

Descartada por Carlos. Forzaría una vuelta innecesaria por el navegador (leer bytes al cliente y reenviarlos por HTTP) para ficheros que el servidor ya tiene al lado — el caso típico de PTWANDA/BandeJA ya copiados a mano a la carpeta de red. Se mantienen ambos mecanismos, cada uno para su caso.

### C. Mover al vincular en cada consumo (no solo el primero)

Descartada. Un documento puede tener múltiples `DocumentoTarea` con rol `CONSUMIDO` (ADR-010) a lo largo de fases distintas. Mover en cada vinculación generaría movimientos en cascada sin criterio de "ubicación correcta" estable. La primera vinculación (o la producción, que es única) fija la ubicación; el resto solo referencia.
