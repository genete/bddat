# Estudio: editar los escritos si el puesto de la Junta pasa a Microsoft 365

> Borrador de trabajo (2026-11-01). Solo lectura del repositorio y búsquedas web; no se ha
> tocado ningún ADR ni código. **Limitación importante:** `learn.microsoft.com` y
> `news.microsoft.com` no resuelven desde esta sesión de la nube (red restringida), así que
> **no he podido leer las páginas primarias de Microsoft**: lo que sigue se apoya en los
> resúmenes del buscador. Cada afirmación lleva su grado de confianza. Para leerlas, hay que
> permitir esos hosts en la configuración de red del entorno.

---

## 1. En llano

**Qué pasa.** ADR-035 y ADR-050 se diseñaron sobre una premisa: *en la Junta no hay Word, los
`.docx` se abren con LibreOffice* (ADR-050 §J). La ADA te ha dicho que la tendencia es la
contraria, y lo que he encontrado la respalda: en marzo de 2026 la Junta y Microsoft
firmaron un protocolo para extender Microsoft 365 a ~44.500 empleados públicos.

**Qué se rompe.** Tres cosas, que conviene no mezclar:

1. **El formato** (`.odt` frente a `.docx`): lo que genera BDDAT y lo que edita el usuario.
2. **La superficie de edición**: el botón «Editar» abre LibreOffice por WebDAV
   (`vnd.libreoffice.command:`). Sin LibreOffice en el puesto, no hay botón.
3. **Dónde vive el almacén**: tu intuición de que podría acabar en la nube de Microsoft.

**La idea central de este estudio:** el 2 y el 3 **son decisiones independientes**. Para que
el usuario edite en Word hace falta que *una copia de trabajo* esté en Microsoft 365; no hace
falta que *el almacén de referencia* lo esté. Si se separan, el almacén sigue siendo
inmutable y direccionado por hash (ADR-050 §B), y Microsoft 365 queda confinado a un
«adaptador de edición» sustituible. Es la misma jugada que ya hiciste con el almacén,
aplicada a la edición.

---

## 2. Qué dice hoy el diseño y qué premisa cae

| Dónde | Qué fija | ¿Sobrevive sin LibreOffice en el puesto? |
|---|---|---|
| ADR-035 §1 | Plantillas y borradores en `.odt` | **No**, salvo que el supervisor y el tramitador tengan LibreOffice |
| ADR-035 req. 1 | «LibreOffice pasa a ser requisito de instalación de BDDAT» | **No**: es justo lo que la ADA desaconseja |
| ADR-035 req. 2 | Un `.odt` que vuelva a BDDAT *no* debe abrirse con Word; «no se soporta ese camino» | **Se invierte**: Word pasa a ser el camino principal |
| ADR-035 «Por qué» | Se eligió ODT porque el editor es Writer y la protección de objetos (`style:protect`) no sobrevive a la traducción a OOXML | La razón **desaparece** si el editor deja de ser Writer |
| ADR-050 §D | Edición por WebDAV de BDDAT + `vnd.libreoffice.command:` (#1000, probado en un puesto) | **No** en puestos sin LibreOffice |
| ADR-050 §D | PDF para firma con `soffice --headless` **en el servidor** | **Sí**, pero con un riesgo de fidelidad (§5.3) |
| ADR-050 §D | «Alternativa sin nada instalado: descargar, editar y volver a subir» | **Sí**; hoy es el plan B, pasaría a ser el suelo mínimo |
| ADR-050 §J / fase 4 | Retirar el motor de Word (`generador_escritos_docx`, docxtpl) | **Conviene suspenderlo** hasta decidir (§6) |
| ADR-050 alternativa E | Se descartó Collabora/OnlyOffice/Nextcloud por WOPI («otro sistema que mantener») | **Hay que reabrirla**: la premisa que la descartó (LibreOffice basta) ha cambiado |
| ADR-050 §B | Almacén detrás de un puerto + adaptador; `comprobaciones_admitidas()` | **Sí**, está pensado para esto |

---

## 3. Lo que he averiguado

### 3.1 La Junta y Microsoft 365 — confianza **alta** (varias fuentes)
- Marzo de 2026: protocolo Junta–Microsoft para extender Microsoft 365 a 44.500 empleados de la
  Administración General, con Copilot Chat
  ([Microsoft News](https://news.microsoft.com/source/emea/features/la-junta-de-andalucia-adoptara-microsoft-365-como-plataforma-de-trabajo-con-el-fin-de-impulsar-una-administracion-mas-colaborativa-segura-e-innovadora/?lang=es),
  [Interempresas](https://www.interempresas.net/Smart_Cities/625708-Andalucia-extendera-Microsoft-365-a-44500-empleados-publicos.html),
  [Última Hora](https://www.ultimahora.es/noticias/comunidades/2026/03/13/2588301/junta-andalucia-extendera-microsoft-365-brindara-empleados-publicos-acceso-herramientas-ia.html)).
- Julio de 2025: acuerdo marco de 53,2 M€ para contratar productos y servicios Microsoft
  ([Última Hora](https://www.ultimahora.es/noticias/comunidades/2025/07/25/2437513/junta-lanza-acuerdo-marco-millones-para-contratar-servicios-productos-microsoft.html)).
- Un pliego de la ADA dice que promueve el software libre pero conserva licencias de Office
  porque recibe documentos en ese formato
  ([doc. 176919](https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec_documentacion/rest/descargar/documento/176919)).
  Otro documento habla de ofimática «monopuesto» en puestos sin trabajo colaborativo, con
  vistas a Office 365 progresivo
  ([doc. 241227](https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec_documentacion/rest/descargar/documento/241227)).
- **Despliegue real hoy** (resúmenes del buscador, sin leer la fuente): unos 8.500 empleados ya
  usan Microsoft 365 y la ADA prevé llegar a los 44.500 «antes de julio de 2027»
  ([INAP](https://laadministracionaldia.inap.es/noticia.asp?id=1520888) da ~8.000). Es decir,
  **al menos un año de parque mixto**, y eso sin contar un posible retroceso.
- **Carlos dice** que la noticia aclara el versionado en la nube y que el acuerdo es por dos
  años prorrogable dos más. **No lo he podido contrastar:** `interempresas.net` no resuelve desde
  esta sesión y los resúmenes del buscador no mencionan ni la duración ni el versionado.
- **No he encontrado** ninguna fuente que diga que *no habrá instalación de escritorio*. Lo que
  tú dices que te dijo la ADA («sin instalación, en el navegador») lo tomo como dato tuyo, no
  lo he podido contrastar. Es la pregunta nº 1 para la ADA (§7).

### 3.2 Word para la web desde una aplicación propia

| Vía | Veredicto | Confianza |
|---|---|---|
| **WOPI propio** (BDDAT como *host* de Word para la web de Microsoft) | **No abierta en el programa público; no descartada.** La única puerta documentada es el Cloud Storage Partner Program, para ISV cuyo negocio es el almacenamiento: «no está abierto a clientes de Microsoft 365 directamente», exige almacenar los ficheros en una nube *del partner*, servir a más de un cliente externo y **no admite licencias de gobierno** ([CSPP](https://learn.microsoft.com/en-us/microsoft-365/cloud-storage-partner-program/online), [requisitos WOPI](https://learn.microsoft.com/en-us/microsoft-365/cloud-storage-partner-program/online/wopi-requirements)). **No he encontrado ninguna excepción documentada**, pero tampoco puedo descartar que la Junta la negocie bilateralmente en su acuerdo con Microsoft, ni una vía por un partner (ownCloud ofrece a sus clientes Enterprise un proxy WOPI hacia Microsoft 365, según una presentación de 2022). Es pregunta para la ADA / Microsoft, no una conclusión mía. *(Corregido el 2026-11-01: la primera redacción decía «Cerrada».)* Distinto es WOPI con **Collabora u OnlyOffice** como cliente: ahí BDDAT sí puede ser *host* sin permiso de nadie | Alta en lo que dice el programa; **baja** en que no haya otra vía |
| **SharePoint / OneDrive + Microsoft Graph** (el fichero vive en la nube M365 de la Junta; BDDAT lo sube por Graph y abre su `webUrl`) | **Viable.** Es la vía «normal» | Alta en lo general; media en los detalles |
| **SharePoint Embedded** (contenedores propios de la app, dentro del tenant del cliente, con Graph) | **Viable y pensada para esto**, pero con facturación Azure de consumo (almacenamiento, transacciones, salida), roles de administrador en el tenant y usuarios en Entra ID; hay contenedor de prueba sin facturación ([visión general](https://learn.microsoft.com/sharepoint/dev/embedded/overview), [facturación](https://learn.microsoft.com/en-us/sharepoint/dev/embedded/concepts/admin-exp/billing)) | Media |
| **Word de escritorio sobre WebDAV de BDDAT** (`ms-word:ofe\|u\|<url>`) | **Sin verificar y con indicios contrarios.** Un hilo reporta que en Windows Word ignora `ofe` y abre en lectura/escritura sea cual sea; otro, que un `LOCK` fallido no impide abrir. No he encontrado documentación de Microsoft | **Baja** |

**Cómo se edita en la práctica con SharePoint Embedded** (media): `driveItem.webUrl` abre el
fichero en Word para la web, con coautoría, autoguardado e historial de versiones. **Word para
la web se abre en una pestaña nueva y hoy no se puede incrustar en un iframe**; la edición
corre en el dominio de Microsoft
([Abrir ficheros Office desde tu app](https://learn.microsoft.com/en-us/sharepoint/dev/embedded/build/open-office-files),
[Q&A](https://learn.microsoft.com/en-us/answers/questions/5669186/is-there-a-supported-way-to-embed-editable-sharepo),
[Visual Studio Magazine, 26/10/2026](https://visualstudiomagazine.com/articles/2026/10/26/sharepoint-embedded-update-details-scaling-limits-permissions-and-office-co-authoring.aspx)).
Un repositorio de GitHub afirma lo contrario; es no oficial y no verificado.

### 3.3 Formatos — confianza **alta**
- **Word para la web puede editar `.odt`, pero con diferencias de formato**, y Word de escritorio
  al guardar en ODT **elimina la protección de documento y los derechos IRM**, con marcas de
  agua y temas no soportados
  ([Microsoft](https://support.microsoft.com/en-gb/office/use-word-to-open-or-save-a-document-in-the-opendocument-text-odt-format-20e5189f-86f8-4d8f-ae74-ea06b7df3b0e),
  [diferencias ODT/DOCX](https://support.microsoft.com/en-US/Word/differences-between-the-opendocument-text-odt-format-and-the-word-docx-format-used-by-word-for-the-w)).
  Es exactamente lo que ADR-035 §«Contexto» midió con Writer pero al revés: **el viaje de ida y
  vuelta por un editor que no es el nativo deshace la protección**. Conclusión: con Word, el
  borrador tiene que ser `.docx`.
- **Graph convierte a PDF** (`GET /drive/items/{id}/content?format=pdf`) y la lista de formatos
  de origen incluye `.odt` y `.docx`
  ([Graph](https://learn.microsoft.com/en-us/graph/api/driveitem-get-content-format)). Hay
  fallos conocidos (documentos cifrados o con IRM).

### 3.4 Almacenamiento en Microsoft 365 como adaptador — confianza **alta**
- **No hay SHA-256 utilizable en unidades de empresa.** Graph marca `sha256Hash` como «no
  soportada, no usar»; el hash fiable es `quickXorHash`, propietario y no criptográfico, con
  fragmento de cálculo publicado por Microsoft
  ([hashes](https://learn.microsoft.com/en-us/graph/api/resources/hashes)).
  Encaja con `comprobaciones_admitidas()` de ADR-050 §B: el adaptador declararía `quickXorHash`
  y calcularía ese algoritmo para la comprobación de la subida. El `contenido_sha256` de BDDAT
  (deduplicación, trazabilidad) no cambia, porque lo calcula BDDAT.
- **Notificaciones de cambio:** una suscripción sobre la raíz de la unidad solo admite
  `updated`; sobre un elemento concreto, `created`/`updated`/`deleted`. Fuente de segunda mano
  ([espejo de la documentación](https://github.com/microsoftgraph/microsoft-graph-docs-contrib/blob/main/api-reference/v1.0/api/subscription-post-subscriptions.md));
  **a verificar**. Nada leído sobre consultas *delta*.

### 3.5 ENS — confianza **media**
Microsoft anuncia certificado de conformidad ENS **nivel alto** para Microsoft 365 y Azure
([Microsoft España, 2022](https://news.microsoft.com/es-es/2022/10/10/microsoft-certifica-50-nuevos-servicios-de-azure-dynamics-365-y-microsoft-365-en-conformidad-con-el-nivel-alto-del-esquema-nacional-de-seguridad/),
guía CCN-STIC 885A). No he encontrado nada sobre residencia de datos / EU Data Boundary.
**No es un análisis jurídico**: qué categoría tiene un borrador de resolución y si puede estar
en esa nube lo decide el DPD / la ADA.

---

## 4. Las vías para editar, comparadas

| | A. LibreOffice + WebDAV (diseño actual) | B. Word web vía Graph/SPE | C. Descargar–editar–subir | D. Editor web propio (Collabora/OnlyOffice por WOPI) |
|---|---|---|---|---|
| Formato del borrador | `.odt` | `.docx` | cualquiera (lo que genere BDDAT) | `.odt` o `.docx` |
| Lo que exige al puesto | LibreOffice | solo navegador + cuenta M365 | cualquier editor | solo navegador |
| Dónde está el contenido mientras se edita | BDDAT (almacén) | **nube M365** (copia de trabajo) | PC del usuario | servidor de la Junta |
| Cómo vuelve a BDDAT | `PUT` WebDAV en cada Ctrl+S | hay que **traerlo**: webhook, *delta*, sondeo o botón «Terminé» | el usuario lo sube | `PutFile` WOPI directo |
| Bloqueo / «otro usuario edita» | LOCK WebDAV (ya probado) | coautoría de M365 (no hay bloqueo duro) | ninguno | WOPI Lock |
| Versiones internas | ninguna | **historial de SharePoint** (convive con «sin versiones» solo en la copia de trabajo) | ninguna | las de BDDAT |
| Depende de la ADA | no | **sí**: registro de aplicación en Entra, consentimiento de admin, sitio/contenedor, facturación (SPE) | no | no (pero «otro sistema que mantener») |
| Probable en la nube de Claude | **sí** (LibreOffice instalado) | **no** el flujo real; solo contra un simulador | sí | sí (contenedor Docker, si hay red) |
| Estado | probado en #1000 | sin probar | ya previsto en ADR-050 §D | sin probar; reabre la alternativa E |

---

## 5. Efectos por pieza

### 5.1 Plantillas y formato (lo de mayor coste)
Si el editor de borradores es Word, los borradores son `.docx`. Y **el supervisor es el primero
que lo nota**: su flujo es *descargar la base canónica → editarla → subirla*. Si no tiene
LibreOffice, no puede editar `carta_base.odt` sin degradarla (§3.3).

Piezas que están hechas solo para ODT y habría que rehacer o duplicar para OOXML:
`generador_escritos_odt.py` (549 líneas, motor propio), `plantilla_canonica_odt.py` y la
comprobación de canonicidad #727 (`advertencias_plantilla` devuelve `[]` para `.docx`), las
tres bases en `app/data/plantillas_base/` y los `scripts/fabricar_*.py`, el panel de tokens y
la guía del supervisor. Lo que **ya existe** para `.docx`: `generador_escritos_docx.py`
(docxtpl) y su validador.

Dos caminos, a decidir cuando se sepa qué usa el supervisor:
- **Todo a `.docx`**: plantillas, bases canónicas, borradores. Es coherente, pero retira la
  razón de ser de ADR-035 y obliga a rehacer la canonicidad. El motor docxtpl ya está; sus
  parches de párrafos anidados vuelven a importar.
- **Plantillas en `.odt`, borrador entregado en `.docx`** (convertir en el servidor con
  `soffice --headless`). Mantiene el motor propio, pero el supervisor sigue necesitando
  LibreOffice, y se pierde fidelidad en la conversión. Solo sirve si el supervisor *sí* lo tiene.

### 5.2 El almacén
- **Adaptador Graph/SharePoint para el almacén de referencia: posible**, no necesario.
  Habría que resolver: la `ref` sería el identificador del elemento; el hash de comprobación,
  `quickXorHash`; límites y *throttling* (429, `Retry-After`); subida en sesiones para ficheros
  grandes; autenticación de aplicación con certificado; y que «un contenido ya escrito no se
  modifica nunca» (§B) exige no reutilizar elementos (SharePoint sí permite sobrescribir).
- **Efecto sobre el exportador y los manifiestos (§H):** su razón de ser es «poder volver al
  papel sin BDDAT». Con el almacén de referencia en Microsoft 365 necesitan Microsoft 365 para
  leer, lo que desmonta la salvaguarda. Argumento a favor de no mover el almacén de referencia.
- **Recomendación de estructura:** almacén de referencia donde esté decidido; **copia de
  trabajo** en M365 solo mientras dura la edición. Al terminar, BDDAT lee el `.docx`, calcula su
  `contenido_sha256`, lo escribe en el almacén por el camino de siempre (§B, pasos 1-6) y borra
  la copia de trabajo (o la conserva N días).

### 5.3 El PDF para firma (la pieza más delicada)
Hoy `soffice --headless --convert-to pdf` lo hace el servidor (§D). Si el borrador sale de
Word, **LibreOffice renderiza un `.docx` con diferencias** (fuentes, saltos, cabeceras de
primera página). Para un acto administrativo que se firma, el PDF debe parecerse a lo que el
tramitador vio. Opciones: conversión de Graph (usa el motor de Word; el documento ya está en
M365), conversión local con comprobación visual, o fijar fuentes y base como hace ADR-035 §5.
**Convendría ponerlo detrás de un puerto**, como el almacén. Sin verificar: cuánto difiere en
nuestros escritos reales.

### 5.4 La sesión de edición (ADR-050 §D)
Todo lo que se construyó en torno al `PUT` de WebDAV cambia de naturaleza con Word web:
- **No hay «Guardar»** que BDDAT reciba: hay autoguardado en Microsoft. BDDAT tiene que
  *detectar* el cambio (webhook, *delta*, sondeo) o pedir al usuario «Terminé, traer cambios».
- **Desaparece el problema de «Guardar como»** del §D (en la web no existe igual), pero
  aparece el de **no saber cuándo se terminó** y el de la **coautoría**: dos tramitadores
  pueden editar a la vez, algo que hoy el bloqueo evita.
- `getlastmodified` estable, bloqueos de 180 s, verbos WebDAV: nada de eso aplica a la vía B.
  Seguiría aplicando a la vía A para quien tenga LibreOffice.

### 5.5 Identidad
La vía B necesita que cada tramitador exista en Entra ID y tenga permiso sobre la copia de
trabajo. Con permisos delegados BDDAT debe iniciar sesión contra Entra por OIDC; con permisos
de aplicación, compartir enlaces con usuarios concretos. **Hace falta saber cómo se
autentican hoy y mañana los usuarios de BDDAT** (no lo he mirado).

### 5.6 La nube de Claude y las pruebas
- **Sigue funcionando** lo que corre en servidor: LibreOffice (generación y PDF), docxtpl, el
  motor propio, el almacén en disco, la vía C.
- **Deja de ser comprobable** la vía B real: no hay tenant, ni credenciales, ni (de momento)
  acceso de red a `graph.microsoft.com`, y el inicio de sesión de Microsoft con MFA no se
  automatiza. Se testea el adaptador contra un servidor Graph simulado; la prueba real la
  haces tú desde el PC con un tenant de desarrollo.
- **Para los guiones Playwright:** el paso «el usuario edita el borrador» se resuelve con la
  vía C (descargar, modificar el `.docx` con `python-docx`, subir). Es independiente de
  Microsoft en ambos entornos, y es una razón más para que la vía C exista siempre.

---

## 6. Qué haría con las fases de ADR-050

| Fase | Contenido | Efecto |
|---|---|---|
| 4 | Plantillas y fragmentos al almacén; **retira el motor de Word** | **Suspender la retirada del motor `.docx`** hasta decidir. Meter las plantillas en el almacén no se ve afectado |
| 5 | Edición WebDAV, congelado del borrador | **No empezar sin decidir.** Rediseñar como «puerto de edición» con adaptadores intercambiables |
| 6 | PDF sincronizado | Poner el conversor detrás de un puerto |
| 2b, 7 | Manifiestos, papelera | Sin efecto |

Un **puerto de edición** análogo al del almacén: operaciones `abrir(documento) → URL`,
`estado(sesión)`, `recoger(sesión) → bytes`, `cerrar(sesión)`. Adaptadores: WebDAV-LibreOffice
(el de #1000), Graph-Word, y manual (descargar/subir). Las filas `sesiones_edicion` y la
bitácora de «un cambio por sesión» sirven a los tres.

---

## 7. Preguntas, por orden de utilidad

**A la ADA:**
1. ¿Qué llevará el puesto del tramitador y del supervisor: Microsoft 365 Apps de escritorio, solo
   Word web, o ambos? ¿Seguirá LibreOffice en alguno?
2. ¿Pueden darnos un registro de aplicación en su Entra ID con permisos sobre un sitio
   SharePoint (o un contenedor SharePoint Embedded) para BDDAT? ¿Quién paga el consumo?
3. ¿Dónde se aloja BDDAT y puede el servidor llegar a `graph.microsoft.com`?
4. ¿Cómo se autentican los usuarios de BDDAT en producción (Entra, Cl@ve, otro)?
5. ¿Puede un borrador de resolución (antes de firmar) residir temporalmente en esa nube? Es
   pregunta para el DPD / la ADA, no técnica.

**A ti:**
6. ¿El supervisor edita las plantillas en Word o en LibreOffice? De eso depende todo el §5.1.

---

## 8. Lo que no sé y cómo comprobarlo barato

| Duda | Cómo se comprueba | Dónde |
|---|---|---|
| ¿Word abre y guarda bien un `.docx` generado por nuestro motor (cabecera de primera página, tokens, pie con el código de seguimiento)? | Generar uno con docxtpl y abrirlo en Word web y de escritorio | tu PC |
| ¿Cuánto difiere el PDF de LibreOffice del de Word en un `.docx` real? | Dos conversiones del mismo fichero, comparadas | cloud + PC |
| ¿Funciona el ciclo subir → `webUrl` → editar → descargar con Graph? | Tenant de desarrollo de Microsoft 365 y un script | tu PC |
| ¿Word de escritorio edita por WebDAV de BDDAT? | Prueba con la prueba de concepto de #1000 | PC con Word |
| ¿Se puede incrustar la edición en un iframe (SPE)? | Documentación actualizada (octubre 2026) | permitir `learn.microsoft.com` |

---

## 9. Decisión de Carlos (2026-11-01) y mi recomendación

**Decisión, transcrita:** no se rompe el sistema de edición remota con LibreOffice. Instalarlo
es gratis, su mantenimiento no es un coste importante y la compatibilidad hacia atrás de `.odt`
es robusta. Motivo de fondo: la colaboración Junta–Microsoft es por dos años prorrogable dos
más, es la segunda vez que se intenta, las licencias son caras y las decisiones políticas
cambian. **Plan ante desastre** (obligación de desinstalar LibreOffice en los puestos): migrar
las plantillas a `.docx` y estudiar el cambio a WOPI «si hay o lo que nos dejen». Su previsión
es que a futuro no haya LibreOffice ni Office de escritorio, solo web.
*(Los dos años + dos y que sea el segundo intento son datos de Carlos: no he podido leer la
noticia ni contrastarlo, ver nota al pie del §3.1.)*

**Lo que sigue de este documento (a partir de aquí) es mi recomendación original, anterior a
la decisión; léase ya a su luz.** Lo que no cambia: el radio de un «desastre» es pequeño.
El servidor sigue con LibreOffice (PDF y generación), el almacén y el motor `.odt` no se ven
afectados; solo se rompen **dos puntos**: el botón «Editar» del tramitador y la edición de
plantillas por el supervisor.

1. **No tocar nada ahora.** Registrar en un ADR (o en una enmienda) que la premisa de ADR-035
   req. 1-2 y ADR-050 §J ha cambiado, sin decidir aún.
2. **Mantener el motor `.docx`** y no retirarlo en la fase 4.
3. **Diseñar la edición como puerto**, con la vía C siempre disponible y la A para quien tenga
   LibreOffice. La B (Word web) se enchufa cuando la ADA responda.
4. **No mover el almacén de referencia a Microsoft 365** sin una razón propia; usar M365 como
   superficie de edición temporal. Si la ADA lo impone, el diseño ya lo admite (§5.2).
5. **Reabrir la alternativa E** (Collabora/OnlyOffice): es la única vía de «editar en el
   navegador, sin instalar nada» que no saca el contenido de la Junta y conserva `.odt`.
   *No la he investigado en esta sesión*; el coste de mantener un servicio más fue lo que la
   descartó.
6. **Contestar antes que construir:** las preguntas 1 y 6 cambian el plan entero.

---

## 10. Contraste con una respuesta de Gemini (aportada por Carlos, 2026-11-01)

Fichero: «Forma correcta de edición en línea desde BDDAT». **No he podido abrir ninguna de las
fuentes que cita** (Stack Overflow, McKenna Consultants, ClearPeaks, Medium: hosts fuera de la
red de la sesión); lo evalúo contra lo que ya tenía.

**Coincide con la vía B de §3.2/§4 y aclara la duda del WOPI.** Si el documento *vive en
SharePoint*, SharePoint ya es el *host* WOPI y Word para la web el cliente: BDDAT no implementa
WOPI, usa Microsoft Graph (autenticación Entra ID/MSAL, localizar el fichero, obtener su URL de
edición). Es decir, el «WOPI propio» del §3.2 es la vía en la que BDDAT guarda el fichero; la
otra no necesita pedir nada. **Consecuencia para el plan ante desastre de Carlos:** lo que habría
que pedir a la ADA no es «WOPI», sino un registro de aplicación en su Entra ID y un sitio
SharePoint (o contenedor SharePoint Embedded). Es la pregunta 2 del §7, afinada.

**Tres puntos que no daría por buenos:**
1. **Iframe.** Ofrece incrustar la URL en un `<iframe>`. Lo que encontré dice lo contrario para
   SharePoint Embedded: Word para la web «se abre en una pestaña nueva y hoy no es incrustable»
   (§3.2). La cita que pone es la del programa CSPP, que describe cómo un *host WOPI* incrusta
   Office, no cómo se incrusta un `webUrl` de SharePoint. Contar con pestaña nueva.
2. **`createLink` con `type: edit, scope: organization`.** Genera un enlace con el que
   *cualquier persona de la organización* puede editar. Para borradores de resolución es el
   valor por defecto equivocado. Lo coherente es dar permiso a usuarios concretos (el `webUrl` del
   elemento ya abre el editor a quien lo tiene) o un enlace limitado a personas; los valores
   exactos de `scope` y su disponibilidad, **sin verificar**.
3. **Permiso `Files.ReadWrite.All`.** Da lectura y escritura sobre *todos* los ficheros a los que
   el usuario accede. Microsoft recomienda ámbitos estrechos (`Sites.Selected`,
   `FileStorageContainer.Selected`). Un administrador de la ADA no lo concedería.

**Lo que no cubre, que es lo difícil:** cómo se entera BDDAT de que se ha editado y recoge el
resultado (§5.4); copia de trabajo frente a almacén de referencia (§5.2); fidelidad del PDF
(§5.3); el historial de versiones propio de SharePoint; el consentimiento de administrador en un
tenant que gestiona la ADA (la respuesta habla de «tu empresa»); y la cuestión ENS/DPD. La
alternativa Power Apps no aplica a BDDAT.
