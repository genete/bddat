# Estudio de campo — DOM de PTWANDA (insumo para ptwanda-manager)

> **Estado:** En curso. Sesión de exploración inicial 2026-06-05 (acceso por certificado,
> área ENERGIA, puesto TRAMITADOR_CA). Quedan zonas por mapear (ver §12).
> **Actualización 2026-06-05:** informática ya restauró la **credencial DNI/contraseña**
> (usuario = DNI). La próxima sesión puede **definir el algoritmo general** y ejecutar una
> **prueba completa desatendida por script** (login DNI/contraseña, sin certificado).
> **Relacionado:** [DISEÑO_ECOSISTEMA_MANAGERS.md](DISEÑO_ECOSISTEMA_MANAGERS.md) ·
> [ADR-021](../decisiones/ADR-021-operaciones-externas-firma-notificacion.md)
>
> **Privacidad:** Este documento recoge **estructura y selectores**, no datos de expedientes.
> No incluye DNI, contraseñas/hashes ni datos de interesados. Los identificadores internos
> (`idInterno`, `refdoc`, nº de expediente) que aparecen son ejemplos de la sesión de prueba
> y pueden haber cambiado.

---

## 1. Propósito y alcance

PTWANDA (Plataforma de Tramitación w@ndA) es la aplicación de la Junta de Andalucía por la
que entran las solicitudes telemáticas vía VEAJA. El objetivo de **ptwanda-manager** (ver
DISEÑO_ECOSISTEMA_MANAGERS.md) es automatizar con Python + Playwright la **recepción de
solicitudes nuevas del área** y la **descarga de su documentación**, para volcarla a BDDAT.

Este documento mapea el DOM y el flujo necesario para ese scraping, de extremo a extremo:
login → búsqueda → listado → detalle → descarga de documentos.

**Alcance de la sesión inicial:** procedimiento "Solicitud autorizaciones instalaciones
eléctricas" (`ENERG_INST`), fase `SOLICITUD TELEMATICA`. Solo lectura/descarga; ninguna
operación de tramitación con efectos persistentes salvo el bloqueo inherente a abrir un
expediente (ver §11).

---

## 2. Entorno

| Dato | Valor |
|---|---|
| Host | `https://extranet.chap.junta-andalucia.es` |
| Webapp | `/veauni_ptwanda-web/` |
| Versión w@ndA | 2.5.9.4 (2026-05-13) — visible en el pie |
| Instalación | `ENERGIA` |
| Sistema | `ENER_CENTR` (derivado de la instalación) |
| Stack servidor | Struts clásico (acciones `*.action`), jQuery 3.3.1, Bootstrap 4.2.1, DataTables (1.9 en algunos listados) |

La versión conviene vigilarla (igual que en notifica-poc): un cambio puede romper el DOM.

---

## 3. Autenticación y acceso

### 3.1 Dos vías de entrada

La pantalla `indicarSistema.action` ofrece **dos formularios independientes**:

1. **DNI + contraseña** → POST a `indicarProcedimiento.action`. Campos: `txtDni`, `txtPassword`
   (+ hidden `instalacionEscogida`, `sistema`).
2. **Certificado electrónico** → form `id="pagina_inicio"`, POST a
   `/veauni_ptwanda-web/solicitarTicket`.

### 3.2 Vía certificado (mTLS) — hallazgos

- El "Acceso con Certificado Electrónico" **no es un formulario web**: dispara una negociación
  **TLS con certificado de cliente (mTLS)**. El navegador abre un **diálogo nativo** de
  selección de certificado que **NO es parte del DOM** → no se puede scrapear ni manejar con
  las herramientas DOM de Playwright (`click`, `snapshot`, `handle_dialog`).
- Comportamiento **inconsistente** observado: el primer intento mostró el popup; un segundo
  intento (mismo equipo, nueva instancia de navegador) **auto-seleccionó** el certificado sin
  popup. Causa no determinada (auto-selección de Chromium por filtro de CAs aceptadas del
  servidor vs. caché de perfil). **No se puede afirmar que sea automatizable de forma fiable.**
- Para automatizar por certificado haría falta `clientCertificates` de Playwright (PFX +
  passphrase presentado en el handshake) o la política Chromium `AutoSelectCertificateForUrls`.
  **Ambas requieren material del certificado en la máquina donde corre el bot.**
- **Bloqueo práctico:** en el equipo de trabajo la **gestión/exportación de certificados está
  restringida por política corporativa** (no se puede abrir `certmgr.msc` ni exportar el PFX).
  Esto **descarta `clientCertificates` en este entorno**.
- Detalle interno revelador: tras autenticar por certificado, la aplicación **arrastra un hash
  de la contraseña** del usuario en un campo oculto (`txtPassword`) y continúa por el **mismo
  flujo que el login por DNI/contraseña**. (El valor del hash no se reproduce aquí.) Es decir,
  ambas vías convergen internamente.

### 3.3 Recomendación de acceso para ptwanda-manager

**Usar DNI + contraseña**, no certificado. Razones:

- Es un formulario web normal → automatizable directamente (mismo patrón que la POC
  `D:\notifica-poc` contra Notific@ PNT).
- Evita el diálogo nativo de certificado (no scrapeable) y la dependencia de exportar PFX
  (restringido en el equipo).
- **Basta UN solo usuario**: en PTWANDA la **visibilidad es por área** (ENERGIA), no por
  funcionario; el listado de expedientes del área se ve completo con una sola cuenta. No aplica
  el modelo "N credenciales de usuario" del ADR-021 §3 (ese es para firmar/notificar imputando
  al funcionario). → 1 credencial, 1 caducidad de contraseña que gestionar.
- Encaja con ADR-021 §3: credenciales externas cifradas en BD con la librería ya instalada.

> **Credencial disponible (2026-06-05):** informática restauró el acceso por DNI/contraseña
> (usuario = DNI). Queda solo confirmar en la práctica que otorga la misma **visibilidad de
> área** que el certificado (debería, es la misma cuenta) — se validará en la prueba desatendida.

---

## 4. Flujo de login (paso a paso)

| # | Página / acción | Qué hacer |
|---|---|---|
| 1 | `inicio/indicarInstalacion.action` | `select#instalacionEscogida` → `ENERGIA`. El botón `#submitInstalacion` está oculto hasta elegir; submit del form `#formInstalacion` → `indicarSistema.action` |
| 2 | `inicio/indicarSistema.action` | Rellenar form DNI (`#dni`, `#pw`) y submit (botón "Acceder con dni") → `indicarProcedimientoFirma.action` |
| 3 | `inicio/indicarProcedimientoFirma.action` (Obligaciones de uso) | Pantalla de consentimiento (Código de Conducta TIC). Botón **Aceptar** = form `#formDNI` (hidden `instalacionEscogida`, `sistema`, `txtDni`, `obligado`). Botón **Rechazar** = form `#logoutButton` (`salir=1`) |
| 4 | Selección de **puesto de trabajo** | `select#usuarioSeleccionado` → submit (botón "Acceder"). Valores con formato `CODIGO&&N` |
| 5 | `inicio/crearMenuClasico.action` | Menú principal autenticado |

**Puestos disponibles del usuario de prueba** (multi-rol). El value del `<select>` en el paso 4
es la forma corta `CODIGO&&N`:

| Puesto | value (paso 4) | Organismo |
|---|---|---|
| TRAMITADOR_CA | `TRAM_CA&&7` | Delegación Territorial … Cádiz |
| FIRMANTE_CA | `FIRM_CA&&7` | Delegación Territorial … Cádiz |
| VISTOBUENO_CA | `VB_CA&&7` | Delegación Territorial … Cádiz |
| Técnico (`[BORRAR?]`) | `TECNICO&&2` | Consejería de Industria, Energía y Minas |

> Para el scraping se usa **TRAMITADOR_CA**. El "Cambiar puesto de trabajo" posterior usa otro
> form (`#submitCambiarPuesto` → `cambiarPuestoTrabajo.action`) con un value largo
> `CODIGO&&Etiqueta&&Organismo&&N`.

---

## 5. Menú principal (`crearMenuClasico.action`)

Módulos de primer nivel (`#globalnav`) para TRAMITADOR_CA:

| Módulo | Acción | Uso para el scraping |
|---|---|---|
| Alta de expediente | `modulos/altaExpediente/altaExpediente.action` | ⚠️ **NO usar** (crea expedientes) |
| **Búsqueda de expedientes indexados** | `modulos/busquedaExpedientesIndexados/accesoBusquedaExpedientes.action` | ✅ **vía del scraping** |
| Búsqueda genérica | `busqueda/irABuscadorGenerico.action` | Listados poco útiles |
| Mi Trabajo | `modulos/miTrabajo/inicioMiTrabajo.action` | No es la recepción buscada |

Otros elementos: listado de avisos (polling AJAX `avisosPteLeer.action` cada 60 s), buscador
global con autocompletado, "Desconectar" (`indicarInstalacion.action?salir=1`).

---

## 6. Búsqueda de expedientes indexados

Página: `modulos/busquedaExpedientesIndexados/accesoBusquedaExpedientes.action?r=s&opcionSeleccionada=...`

### 6.1 Formulario de búsqueda

Campos de texto: `#numExp`, `#tituloExp`, `#fechaAltaIni`, `#fechaAltaFin`, `#interesado`.
Botones: `#btn-buscar` (Buscar), `#btn-limpiar` (Limpiar).

Selectores (son **Bootstrap selectpicker**, el `<select>` nativo está oculto):

| select id | name | contenido |
|---|---|---|
| `#procedimientoSelect` | `procedimientoSelec` | procedimientos del área |
| `#faseSelect` | `faseSelec` | fases (se cargan por AJAX al elegir procedimiento) |
| `#razonesInteresSelect` | `razonInteresSel` | SOLICITANTE, REPRESENTANTE LEGAL, EMPRESA ENERGETICA, … |

**Procedimiento objetivo:** `ENERG_INST` → "Solicitud autorizaciones instalaciones eléctricas",
**value `7`**.

### 6.2 Técnica para manejar el selectpicker (importante)

`page.select_option()` **falla** (el `<select>` nativo no es "visible"). Hay que fijar el valor
por JS y disparar el evento `change` nativo (que ejecuta el `onchange` inline que lanza el AJAX):

```js
const s = document.querySelector('#procedimientoSelect');
s.value = '7';
s.dispatchEvent(new Event('change', { bubbles: true }));   // dispara mostrarComboFases.action
if (window.jQuery?.fn?.selectpicker) jQuery('#procedimientoSelect').selectpicker('refresh');
```

El `onchange` de `#procedimientoSelect` ejecuta:
`realizarPeticionAjax('#modCriteriosDeBusqueda', 'mostrarComboFases.action', '#bloqueFases')`
y análogo para `mostrarComboRazonesInteres.action` → `#bloqueRazonesInteres`. Hay que **esperar**
a que `#bloqueFases select` se rellene antes de elegir fase.

### 6.3 Fases del procedimiento ENERG_INST

(value del `<select>` de fase = id de fase)

| value | Fase | value | Fase |
|---|---|---|---|
| 113 | ESTUDIO DE REQUERIMIENTO | 118 | NOTIFICACION RESOLUCION |
| 116 | FIN PROCEDIMIENTO | 115 | RECEPCION DOCUMENTACION REQUERIMIENTO |
| 114 | FIN REQUERIMIENTO | 119 | SOLICITUD DE INFORMES |
| 109 | GESTION DE AMPLIACION DE PLAZO | **112** | **SOLICITUD TELEMATICA** |
| 117 | GESTION RESOLUCION | 120 | TRAMITACIÓN |
| | | 121 | TRAMITE DE AUDIENCIA |

> ⚠️ El **nombre de la fase en el buscador difiere del que aparece en la columna "Fase" del
> listado de resultados** (a confirmar el mapeo exacto). Filtrar por el **value/id** (112), no
> por el texto.

Tras fijar procedimiento + fase, pulsar `#btn-buscar`.

---

## 7. Listado de resultados

Tabla `id="tablaResultadosBusqueda"` (DataTables, **paginado**). El total real está en el
contador `#tablaResultadosBusqueda_info` ("Mostrando del 1 al 10 de **27** registros") — **no
fiarse de las filas visibles**; iterar la tabla completa (ver técnica DataTables en §9.2).

**26 columnas.** Las relevantes para ptwanda-manager:

| # | Columna | Uso |
|---|---|---|
| 1 | **Nº expediente** | identificador → candidato a `plataforma_codigo` en BDDAT |
| 3 | **Fase** | nombre "de listado" (≠ nombre del buscador) |
| 5 | Nombre o Razón social | interesado |
| 6 | **Usuarios Asignados** | **clave: vacío = no asignado** (objetivo de recepción) |
| 12 | **Fecha de Solicitud** | detectar entradas nuevas |
| 25 | DNI/NIE/NIF | interesado |
| 26 | **Acciones** | botón con `onclick="tramitarExpediente(<idInterno>)"` |

(Resto de columnas: apellidos, población/municipio/provincia, y un bloque de columnas de
autorizaciones/desistimientos AAP/AAC/AAU/AE, cierres, transmisión, utilidad pública.)

- **`tramitarExpediente(<idInterno>)`** abre el detalle del expediente. ⚠️ **Bloquea** el
  expediente (ver §11). El `idInterno` (ej. de sesión: `12227`) es **distinto** del Nº de
  expediente visible.
- Para localizar un expediente concreto: buscar la fila cuyo texto contenga el Nº y extraer el
  `idInterno` de su `onclick`.

---

## 8. Detalle del expediente

`tramitarExpediente()` navega (misma pestaña) a
`accesoEscritorioPestana/entradaExpedientePestana.action`.

Pestañas del detalle (cargan contenido por AJAX con `cargarModuloPortlet(accion, capa, idx)`):

| Pestaña | Acción AJAX |
|---|---|
| Tareas y documentos permitidos | `modulos/bloquesPermitidos/listarBloquesPermitidos.action` (es la **tramitación del usuario**, no lo aportado) |
| **Documentos asociados** | `modulos/docsAsociadosExpediente/listarDocumentos.action` ← **lo que llega del interesado** |
| Tareas asociadas | — |
| Interesados en el expediente | — |
| Usuarios asignados | `modulos/usuariosAsignados/inicio.action` |

Iconos de acción del detalle (varios abren `abreVentana(...)`): Adjuntar documento
(⚠️ subida, no tocar), Notificación de documentos, Tramitación Masiva, Resumen del expediente,
Pago Telemático, etc.

---

## 9. Documentos asociados (tabla `#documentos`)

La tabla de documentos aportados está en `id="documentos"` (DataTables **1.9**), columnas:

```
Fecha | Usuario | Tipo del documento (Nombre) | Estado | Registro | Acciones
```

### 9.1 Acciones por documento — el `refdoc`

Cada documento se identifica por un **`refdoc`** (id de instancia). Las 4 acciones por fila
comparten ese `refdoc`:

| Acción | URL (relativa a la webapp) |
|---|---|
| **Descargar** | `modulos/docsAsociadosExpediente/descargarDocumento.action?refdoc=<refdoc>` |
| Descargar informe de registro | `modulos/docsAsociadosExpediente/verDocumentoFirmadoYRegistrado.action?refdoc=<refdoc>` |
| Observaciones | `modulos/docsAsociadosExpediente/mostrarObservaciones.action?refdoc=<refdoc>` |
| Registro @ries | `modulos/registro/abrirRegistro.action?refdoc=<refdoc>&refexp=<idInterno>` |

En la UI estas acciones van envueltas en `javascript:abrirVentanaPopUp('...')` — **el scraper
no debe usar el popup** (ver §10).

### 9.2 Iteración de TODAS las filas (DataTables 1.9)

La tabla **pagina**: las filas visibles pueden ser menos que las reales (ej. de sesión: se veían
4, había **8**). Para obtener todas sin depender de la paginación, usar la API 1.9 `fnGetNodes`:

```js
const trs = window.jQuery('#documentos').dataTable().fnGetNodes(); // todos los <tr>
// por cada tr: leer celdas y extraer refdoc del href de la acción "Descargar"
```

(Defensivo: si fuese DataTables 1.10+, usar `$('#documentos').DataTable().rows().nodes()`.)

### 9.3 Clasificación por tipo — PENDIENTE / problema abierto

El texto de la columna tiene formato **`TIPO (nombre del fichero real)`**. El texto completo
está en el atributo `title` de la celda (en el DOM aparece truncado con "…").

**No existe un id de tipo expuesto** en esta vista: ni `data-*`, ni código numérico, ni en
`title`. El único id es `refdoc` (instancia, no tipo). Y el **texto de tipo es ambiguo**: varios
documentos dispares (un PDF, un ZIP de capas SIG, otro ZIP de gestión) comparten el tipo
*"Documentación voluntaria no catalogada"*.

→ **Clasificar por el texto de tipo no es fiable.** Opciones a decidir al implementar:
clasificar por el nombre real del fichero + heurísticas; o aceptar que "no catalogada" requiere
intervención humana (encaja con el reparto por jefatura del DISEÑO_ECOSISTEMA). La pestaña
"Tareas y documentos permitidos" **no** sirve para esto (es la tramitación del usuario, no lo
aportado).

Ejemplo de los tipos observados en un expediente de solicitud telemática: "SOLICITUD DE
AUTORIZACIONES DE INSTALACIONES ELÉCTRICAS DE ANDALUCÍA", "Hoja de cálculo…", "Justificante del
pago de la tasa", "Acreditación de la representación legal", "Documentación impuesta por la
normativa sectorial", "Documentación voluntaria no catalogada" (×3). Hay **dos asientos de
registro** distintos en el mismo expediente (aportación inicial vía `VEACHAP` y añadidos
posteriores vía `SEN_TR_OWN`).

---

## 10. Descarga de documentos (confirmada end-to-end)

El endpoint de descarga es un **GET simple**:

```
GET …/modulos/docsAsociadosExpediente/descargarDocumento.action?refdoc=<refdoc>
```

### 10.1 La "especialidad" de los formatos es del navegador, no del endpoint

El servidor responde con **`Content-Disposition: inline` para TODOS** los formatos. El
comportamiento molesto en la UI lo causa **el navegador**:

- PDF (`inline`) → el navegador lo **renderiza en visor** → requiere una acción extra para guardar.
- ZIP / ODS (`inline`) → el navegador **no sabe renderizarlo** → cae a descarga directa.

### 10.2 Solución para el scraper: petición HTTP directa

Hacer la petición al endpoint con la **sesión autenticada** (no `window.open`). Una request
programática recibe **los bytes** sin importar el `Content-Disposition`:

- `page.request.get(url)` (reusa cookies del contexto), o
- `fetch(url, {credentials:'include'})` dentro de la página.

Esto **unifica** el tratamiento de PDF / ZIP / ODS y elimina visor, popups y "estado de la
ventana". Patrón equivalente al `expect_download` de notifica-poc, pero más simple.

### 10.3 Verificación realizada (2026-06-05)

Descarga real de dos documentos del expediente de prueba a `docs_prueba/temp/`:

| refdoc | Content-Type | Content-Disposition | Tamaño | Magic bytes | OK |
|---|---|---|---|---|---|
| (PDF) | `application/pdf` | `inline` | 582 979 B | `25 50 44 46` = `%PDF-1.4` | ✅ |
| (ZIP) | `application/zip` | `inline` | 4 304 B | `50 4b 03 04` = `PK..` | ✅ |

Ambos bytes válidos. Confirma que la vía de request directa funciona para cualquier formato.

---

## 11. Bloqueo y liberación — REGLA DE ORO

- `tramitarExpediente()` **bloquea el expediente para el usuario actual**, coincida o no con el
  usuario asignado.
- **No hay botón de "liberar".** El bloqueo se suelta **navegando a INICIO** (no es necesario
  hacer logout; lo que libera es navegar a la página de inicio).
- ⚠️ **Cerrar el navegador en seco deja el expediente BLOQUEADO indefinidamente.** (Caso real:
  un expediente quedó bloqueado por un usuario de otra provincia con visibilidad interprovincial.)

**Implicación para el scraper:** el ciclo por expediente debe garantizar el cierre ordenado:

```python
try:
    abrir_expediente(id_interno)      # tramitarExpediente → bloquea
    docs = listar_documentos()         # fnGetNodes
    for d in docs:
        descargar(d.refdoc)            # request directa
finally:
    navegar_a_inicio()                 # SIEMPRE libera, pase lo que pase
# nunca browser.close() con un expediente abierto sin pasar por navegar_a_inicio()
```

> Nota: las acciones `inicio/crearMenuClasico.action` y `crearMenuList.action` dieron
> `ERR_EMPTY_RESPONSE` al navegarlas por GET directo durante la sesión (coincidió con una caída
> del servidor). En condiciones normales la navegación a inicio se hace por los enlaces de la
> propia app. A confirmar la URL/forma exacta de "navegar a inicio" para el cierre ordenado.

---

## 12. Pendientes de mapear / confirmar (próximas sesiones)

- [x] Credencial **DNI/contraseña** restaurada (usuario = DNI) — 2026-06-05.
- [ ] **Próxima sesión:** definir el **algoritmo general** y ejecutar una **prueba completa
      desatendida por script** (login DNI/contraseña → búsqueda → listado → detalle → descarga →
      liberar navegando a inicio). Confirmar de paso la visibilidad de área y los campos exactos
      del login (paso 2 de §4).
- [ ] **Clasificación por tipo de documento** (§9.3): decidir estrategia estable.
- [ ] Mapeo exacto **nombre de fase en buscador ↔ nombre en columna del listado**.
- [ ] **Paginación del listado** de resultados: ¿client-side (todo en DOM) o server-side? Cómo
      recorrer las 27+ filas.
- [ ] Forma canónica de **"navegar a inicio"** para el cierre ordenado (§11).
- [ ] Expediente **sin asignar**: comprobar si el detalle/documentos se comporta igual que en uno
      asignado.
- [ ] **`verDocumentoFirmadoYRegistrado`** vs `descargarDocumento`: qué aporta cada uno (justificante
      de registro con CSV vs documento "limpio").

---

## 13. Esbozo de arquitectura del scraper (orientativo)

Estilo `NotificaClient` de `D:\notifica-poc` (Playwright async, gestor de contexto):

```
class PtwandaClient:
    login(usuario, password)              # §3.3, §4  (instalación ENERGIA, puesto TRAMITADOR_CA)
    buscar(procedimiento, fase)           # §6  (selectpicker: set value + change; esperar AJAX fases)
    listar_expedientes(filtro_no_asignado)# §7  (iterar tablaResultadosBusqueda; col "Usuarios Asignados")
    abrir_expediente(id_interno)          # §8  (tramitarExpediente; ⚠️ bloquea)
    listar_documentos()                   # §9  (fnGetNodes; refdoc + tipo + registro)
    descargar(refdoc, destino)            # §10 (page.request.get; uniforme PDF/ZIP/ODS)
    liberar()                             # §11 (navegar a inicio; SIEMPRE en finally)
```

Credenciales cifradas en BD (ADR-021 §3). Una sola cuenta de área (§3.3). Scheduler nocturno
(DISEÑO_ECOSISTEMA_MANAGERS.md): comparar Nº de expediente con los ya registrados e ingerir solo
los nuevos.
