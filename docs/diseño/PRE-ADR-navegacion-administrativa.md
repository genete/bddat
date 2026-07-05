# PRE-ADR — Navegación administrativa: sidebar, dashboard y hub del supervisor

> **Materializado en ADR-029** (`docs/decisiones/ADR-029-navegacion-administrativa.md`,
> 2026-07-05, issues #588/#589/#590). Este documento queda como material de fondo — el
> diagnóstico línea a línea que sustenta la decisión — mismo patrón que
> `PRE-ADR-supervisor.md` respecto a ADR-028.

**Estado:** Propuesta para discusión (no implementada)
**Fecha:** 2026-07-05
**Disparador:** revisión post-merge de #583 (CRUD requisitos documentales, PR #584, `b2c2b12`)
**Candidato a:** ADR-029 (siguiente libre según la partición prevista en ADR-028 §"Partición en ADRs")

---

## Contexto

Al cerrar #583 apareció una entrada nueva de sidebar ("Requisitos documentales",
`/admin/requisitos/`) con una raíz `/admin` que no existía como concepto en la app, sin
enlace desde el hub `/supervisor/` ("Mi trabajo · Supervisor") ni desde el dashboard
principal. El catálogo de tablas estructurales (`docs/referencia/CATALOGO_TABLAS_ESTRUCTURALES.md`)
anticipa que vendrán más CRUD de este tipo (reglas del motor #170, tablas maestras #171,
catálogo de plazos). Sin un principio explícito, cada uno se añadirá por el mismo camino
ad hoc.

Este documento diagnostica la causa raíz con evidencia de código, y propone un principio
de clasificación + un plan de cierre concreto.

---

## Diagnóstico

### 1. Causa raíz de `/admin/requisitos` en vez de `/supervisor/...`

El código ya tenía **dos precedentes distintos** para "pantalla de administración":

| Precedente | Patrón | Origen |
|---|---|---|
| `admin_plantillas` (`/admin/plantillas`) | Módulo propio, `metadata.json` propio, sidebar propio | **Anterior** a ADR-013/017/028 — el propio ADR-013 lo cita como ejemplo del modelo restrictivo antiguo ("`/admin/plantillas` redirige al perfil si no eres ADMIN/SUPERVISOR") |
| `supervisor` (`/supervisor/`) | Blueprint dedicado, **sin** `metadata.json` a propósito, alcanzable solo vía "Mi trabajo" | **Posterior** — ADR-028 (#579), diseñado específicamente para "capa de administración sobre tablas ya vivas" |

Al construir #583 (`app/modules/admin_requisitos/routes.py:1-16`) se documentó explícitamente
copiar el patrón de UI de `admin_plantillas` ("mismo patrón ADR-023... que admin_plantillas")
— acierto, es el patrón de listado+inspector correcto. Pero junto con el patrón de UI se
copió también su **emplazamiento de navegación** (módulo propio, `/admin/*`, `metadata.json`
propio) sin re-derivarlo de ADR-028, que ya había fijado dónde vive exactamente este tipo de
CRUD: como tarjeta del bloque **GESTIÓN** del hub del supervisor. `requisitos_documentales`
es, por naturaleza, justo lo que ADR-028 llama "capa de administración sobre tablas ya
vivas" — la misma familia que reglas del motor o tablas maestras.

`/admin` no es un concepto real de la app: no hay rol `ADMIN` con vista propia distinta de
`SUPERVISOR`, no hay blueprint `admin`, no hay hub `/admin/`. Es solo un prefijo que quedó
de un patrón que las ADR posteriores ya sustituyeron sin retirar sus dos ocupantes.

### 2. Tres superficies de navegación sin coordinar

Hoy existen **tres listas independientes** de "qué se puede navegar", mantenidas a mano por
separado:

| Superficie | Fuente | Mecanismo de permiso |
|---|---|---|
| Sidebar | `ModuleRegistry.get_navigation()` (`app/modules/__init__.py:68-102`), agregando el `metadata.json` de cada módulo | `metadata.json` → `permissions.list` por rol |
| Dashboard (`index_v1.html`) | Tarjetas escritas a mano | `{% if 'SUPERVISOR' in user_roles or... %}` — **chequeo de rol en crudo en template**, justo lo que prohíbe `REGLAS_DESARROLLO.md` §Control de acceso |
| Hub supervisor (`supervisor/index.html`) | Tarjetas escritas a mano | Ninguno propio — hereda el permiso de acceso al hub |

Las tres han divergido ya: el dashboard no tiene tarjeta de Entidades, Plantillas ni
Requisitos (existen solo en sidebar); Usuarios sí está en las tres; Proyectos y Mis
Expedientes están en dashboard pero no en sidebar como módulos propios. No es un problema
que haya introducido #583 — es preexistente — pero #583 es el síntoma que lo hizo visible:
cada superficie nueva que se olvida actualizar deja huecos silenciosos.

Pista adicional en el propio `order` del sidebar: Expedientes(10)·Entidades(20)·Usuarios(30)
saltan a Plantillas(80)·Requisitos(81) — hay un hueco (40-79) que sugiere que alguien ya
intuía una frontera entre "catálogo operativo" y "administración", pero nunca se escribió
la regla; cada módulo nuevo solo estima un número que "parezca bien".

### 3. La brecha entre el hub y sus hojas

`supervisor/index.html` bloque GESTIÓN (líneas 76-118) lista Configuración del motor, Plazos
legales, Usuarios y permisos, Operaciones masivas. Requisitos documentales no está — el hub
nunca se tocó al cerrar #583. Es exactamente el síntoma que describes ("sin enlace desde Mi
trabajo · Supervisor").

### 4. El dashboard mira todos los roles asignados, no el rol activo

`app/templates/dashboard/index_v1.html` decide qué tarjetas mostrar con
`current_user.roles` — la relación M:N completa (`app/models/usuarios.py:262`), es decir,
**todos los roles que tiene asignados el usuario en BD**, sin relación con cuál está activo
en sesión. El patrón correcto ya existe en `app/templates/layout/_topbar.html:51-52`
(`session.get('rol_activo_nombre')`) y es el que usa `tiene_permiso()` internamente
(`app/utils/permisos.py:79-84`). El dashboard es la única plantilla de navegación que no lo
sigue (confirmado: no aparece en la lista de ficheros que referencian `rol_activo_nombre`).

Efecto observable: un usuario con más de un rol asignado (login multi-rol) ve la tarjeta
Estadísticas/Configuración **aunque su rol activo no sea SUPERVISOR/ADMIN**, porque el
`{% if %}` del template solo mira si SUPERVISOR/ADMIN está *entre sus roles asignados*, no
si es el activo. Al clicar, el backend sí comprueba el rol activo (`require_permiso`) y
redirige a `/perfil` con el toast "No tiene permisos suficientes para acceder a esta
sección" (`app/decorators.py:19`). De ahí el síntoma: tarjeta visible, entrada bloqueada.

Mismo bug, de paso, en la tarjeta "Usuarios" del dashboard (línea 49): está gateada a
SUPERVISOR/ADMIN aunque `acceder_usuarios` ya es universal desde ADR-013 — un TRAMITADOR con
un único rol asignado ni siquiera ve la tarjeta, pese a poder entrar perfectamente por el
sidebar. Confirma que el dashboard lleva tiempo desincronizado del modelo de permisos real,
no es algo que introduzca esta conversación.

---

## La pregunta del supervisor: ¿qué es realmente exclusivo?

Repasando ADR-013 (que ya zanjó esto en mayo): la presunción por defecto es **visibilidad
universal**; exclusividad es la excepción y debe justificarse. Las únicas dos excepciones
que ADR-013 documenta explícitamente:

1. DNI de compañeros — dato personal concreto.
2. **"Estadísticas explícitas del trabajo individual de otros tramitadores"** — y el propio
   ADR-013 aclara a continuación: *"La lista de expedientes asignados a otros tramitadores
   **no** se considera estadística — sigue siendo visible."* Es decir: contar expedientes
   asignados/completados por técnico (justo lo que muestra hoy "carga por técnico" del panel)
   **ya estaba pre-aprobado como visible** en mayo. Lo que ADR-013 reserva es una futura vista
   de rendimiento individual con juicio de valor, no un recuento.

Con ese criterio, repaso lo que existe hoy:

| Vista | ¿Exclusiva por doctrina? | Razón |
|---|---|---|
| KPIs agregados, expedientes por estado, plazos vencidos | No | Agregado del dominio, no de personas |
| Carga por técnico (barras) | No | Ya cubierto por la excepción-que-no-es-excepción de ADR-013 §4 |
| Requisitos documentales, Plantillas, Usuarios (lectura) | No | Ya implementado correctamente como `acceder_X` universal |
| CRUD motor/plazos/masivas (escritura) | Solo la mutación, no la vista | Patrón `gestionar_X` ya establecido |
| El **hub** `/supervisor/` en sí mismo | No *(corregido, ver B.2)* | Se pensó inicialmente como "página propia por rol", simétrica a la cola de ADMINISTRATIVO o el seguimiento del TRAMITADOR — pero a diferencia de esas, aquí no hay contenido personal de nadie: es agregado del dominio. Gana entrada de sidebar propia en B.2; lo único que sigue siendo por rol es a dónde te lleva "Mi trabajo", no si el hub es visitable |

**Conclusión: hoy no hay ninguna vista con contenido genuinamente exclusivo del supervisor
más allá de las dos excepciones ya escritas en ADR-013 (DNI; una futura vista de rendimiento
nombrado que ni siquiera existe).** El panel de estadísticas actual (`/supervisor/estadisticas`,
`app/modules/supervisor/routes.py:35-44`) está detrás de `acceder_supervision` = `{ADMIN,
SUPERVISOR}` (`app/utils/permisos.py:33`) — el mismo permiso que abre el hub entero. Es un
**descuido mecánico**, no una decisión: al construir el hub (#579) se le dio una única
puerta de entrada (`acceder_supervision`) y sus hojas heredaron esa misma puerta en vez de
recibir cada una su propio par `acceder_X`/`gestionar_X`, que es el patrón que sí se siguió
en Plantillas, Usuarios y Requisitos. ADR-013 ya había resuelto por escrito que esto debía
ser visible; la implementación de #579/#580 no llegó a aplicar esa parte de la decisión.

**Qué mal hace que lo vean todos:** ninguno identificado. Al contrario — es coherente con el
principio fundacional de ADR-013 ("evitar manazas, no ojos") y con la razón cultural que dio
el propio usuario entonces: el conocimiento compartido facilita aprendizaje y continuidad.

---

## Principio de clasificación propuesto

Para decidir dónde vive una pantalla nueva, una sola pregunta:

> **¿La consultan a diario roles no-supervisores como parte de su trabajo (aunque no la
> editen), o es una herramienta de configuración que solo el supervisor visita para ajustar
> el sistema?**

| Respuesta | Patrón | Ejemplos ya construidos |
|---|---|---|
| Consulta diaria de cualquier rol | Entrada propia de sidebar (`metadata.json`), `acceder_X` universal + `gestionar_X` restringido | Expedientes, Entidades, Usuarios, Proyectos, **Plantillas, Requisitos documentales** |
| Configuración pura del supervisor | Tarjeta dentro de `/supervisor/` (bloque Control o Gestión), **sin** `metadata.json` propio — se llega solo por la entrada única "Mi trabajo" | Usuarios y permisos *(ver nota)*, y lo que vendrá: reglas del motor #170, tablas maestras #171, plazos legales, operaciones masivas #295 |
| El supervisor administra algo que **ya** tiene entrada propia | No sustituye la entrada — se añade también como tarjeta en el hub, a modo de atajo | Usuarios ya sigue este doble patrón hoy: sidebar directo **y** tarjeta en GESTIÓN |

Bajo este criterio, **Requisitos documentales y Plantillas están bien en el sidebar** — un
técnico consulta "¿qué necesito aportar?" o "¿qué plantilla uso?" en su trabajo diario, igual
que consulta Usuarios o Entidades. Lo que falta no es quitarlos del sidebar — es añadirles la
tarjeta correspondiente en GESTIÓN (como ya tiene Usuarios), y decidir qué hacer con el
prefijo `/admin`.

Los que **no** encajan como entrada de sidebar propia son los que aún no existen: reglas del
motor, tablas maestras, plazos, operaciones masivas — un TRAMITADOR no "consulta" una regla
del motor como destino de navegación (aunque, por ADR-013, pueda verla si llega a ella por
otro camino, p. ej. el motor explicando qué prohíbe con enlace a la norma).

---

## Propuesta de cierre

### A — Requisitos documentales (#583) — cerrar la brecha con el hub

Añadir tarjeta en el bloque GESTIÓN de `supervisor/index.html`, mismo patrón que Usuarios:

```html
<a class="sup-tool" href="{{ url_for('admin_requisitos.listado') }}">
  <span class="sup-tool__icon"><i class="fas fa-clipboard-check"></i></span>
  <span class="sup-tool__body">
    <span class="sup-tool__title">Requisitos documentales</span>
    <span class="sup-tool__desc">Catálogo de documentos exigibles y sus condiciones</span>
  </span>
</a>
```

Mantener la entrada de sidebar tal cual (correcta, ver principio arriba).

### B — Abrir `/supervisor/` en modo lectura universal + entrada propia "Control y Gestión"

**Resuelto en conversación (2026-07-05).**

**B.1 — Permiso.** Universalizar `acceder_supervision` (una línea) en vez de crear un
`acceder_estadisticas` aislado:

```python
# app/utils/permisos.py:33 — un solo valor cambia
'acceder_supervision': {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
```

No hace falta permiso nuevo: ni el hub (`supervisor.index`) ni Estadísticas mutan nada por sí
mismos — son lectura pura. La escritura real vive en las hojas (Usuarios → `gestionar_usuarios`,
Requisitos → `gestionar_requisitos_documentales`, y lo mismo aplicará a reglas del motor,
plazos y operaciones masivas cuando se construyan — sus `gestionar_X` ya están reservados en
`permisos.py:36-43`). Si en el futuro aparece contenido genuinamente sensible dentro del hub,
se le da su propio permiso estrecho en ese momento (mismo patrón que `ver_dni_usuarios`) — no
se vuelve a tapar el hub entero por precaución.

**B.2 — Entrada de sidebar propia: "Control y Gestión".** Esto **enmienda ADR-028 §1**
("blueprint supervisor dedicado, deliberadamente sin metadata.json"). No es un simple cambio
de opinión — es la resolución de una **colisión entre dos decisiones previas** que nadie había
puesto una al lado de la otra hasta ahora: ADR-013 fija que la visibilidad es universal por
defecto y que toda excepción debe declararse explícitamente (DNI, estadísticas individuales
nombradas). ADR-028, al no darle entrada de sidebar al hub, creó de facto una tercera
excepción — pero **sin declararla como tal**: ningún párrafo de ADR-028 dice "esto se oculta a
propósito, por esta razón". Quedó inalcanzable por omisión de navegación, no por una decisión
de visibilidad tomada conscientemente. Entre las dos, gana la más fundacional: si no hay una
razón declarada para ocultarlo, no se oculta — tampoco indirectamente vía "no tiene puerta".

Nombre elegido: **"Control y Gestión"**, no "Configuración". Reutiliza el vocabulario que ya
tienen los dos bloques internos del hub (ADR-028 §1: CONTROL / GESTIÓN); evita que la etiqueta
del contenedor choque con la tarjeta interior "Configuración del motor" (`supervisor/index.html:88`);
y representa mejor lo que hay dentro — CONTROL incluye Estadísticas y las futuras Auditoría/
Informes, que no son "configuración" en sentido estricto.

Con esta entrada, Estadísticas no necesita la suya propia: se alcanza entrando en "Control y
Gestión" (ya existe como tarjeta del bloque CONTROL, `supervisor/index.html:41-47`).

**Redundancia asumida, no accidental:** para SUPERVISOR/ADMIN, "Mi trabajo" y "Control y
Gestión" llevan al mismo sitio (`supervisor.index`). Aceptado con los ojos abiertos — mismo
patrón que ya tiene Usuarios (alcanzable por sidebar directo y por tarjeta del hub).

### C — Regla para los próximos CRUD (#170, #171, plazos, #295)

Cuando se construyan: card en GESTIÓN, sin `metadata.json` propio, y **cada hoja con su
propio `acceder_X`/`gestionar_X`** — nunca heredando `acceder_supervision`. Los permisos
`acceder_reglas_motor`/`acceder_catalogo_plazos`/`acceder_tablas_maestras` ya existen en
`permisos.py:36-43` como universales, reservados exactamente para esto — el patrón ya estaba
anticipado, solo falta no romperlo como pasó con estadísticas.

### D — Dashboard y sidebar: 1:1 estricto, misma semántica y mismo orden

**Regla fijada (2026-07-05):** el dashboard deja de ser una superficie de navegación
independiente. Es una vista de bienvenida sobre la **misma lista** que ya consume el
sidebar (`ModuleRegistry.get_navigation()`, la variable `module_nav`) — no una colección de
tarjetas mantenida a mano. Cada módulo con `metadata.json` aporta **exactamente una** tarjeta
y **exactamente una** entrada de sidebar; el orden de las tarjetas sigue el mismo campo
`order`. Esto además cierra de raíz el bug del punto 4 (chequeo de rol en crudo): al generarse
desde `module_nav`, hereda el mismo filtro por rol activo que ya usa el sidebar.

**Consecuencia de esquema** (propuesta mía, a revisar): hoy `navigation.label` es el único
texto compartido; el dashboard además necesita una frase descriptiva ("Consulta y gestión de
expedientes"). Para que las dos superficies sean la misma semántica y no solo la misma ruta,
añadir `navigation.description` a cada `metadata.json` — el sidebar puede ignorarla o usarla
de tooltip, el dashboard la muestra como subtítulo de la tarjeta. Sin este campo, "misma
semántica" quedaría a medias (mismo label, descripción inventada aparte en cada plantilla).

**Qué pasa con cada tarjeta actual** (verificado contra el código):

| Tarjeta hoy | Bajo la regla 1:1 | Evidencia |
|---|---|---|
| Expedientes | Se mantiene | Módulo real, `order:10` |
| Usuarios | Se mantiene (de paso corrige el bug del punto 4 para este caso concreto) | Módulo real, `order:30` |
| Proyectos | Se mantiene | Módulo real, `order:15` |
| Mis Expedientes | Se retira como tarjeta propia | Ya es un filtro (`responsable=yo`) sobre Expedientes (`app/routes/dashboard.py:19-26`), no un destino propio — vive como control dentro del listado |
| Nuevo Expediente | Se retira como tarjeta propia, sin sustituto en sidebar | El listado ya tiene botón "Nuevo" propio (`expedientes/listado_v2.html:7-11`, confirmado). **Verificado además** (`app/routes/wizard_expediente.py:342-346`): al terminar el paso 3, el commit redirige a `expedientes.listado_v2` — la economía de clics para altas sucesivas ya está garantizada por el propio wizard, sin cambio de código necesario |
| Mi Perfil | Se añade — requiere migrar `perfil` a `app/modules/` primero, ver nota abajo | Hoy vive en `app/routes/perfil.py` (patrón antiguo), no en `app/modules/`; no tiene `metadata.json` |
| Tareas (→ seguimiento) | Se retira como tarjeta propia | Duplica lo que hará "Mi trabajo"; confirmado además que hoy está mal cableada — el `{% if %}` incluye a SUPERVISOR/ADMIN pero el enlace siempre apunta a `expedientes.seguimiento` (el seguimiento del TRAMITADOR), nunca a ningún panel propio del supervisor |
| Configuración / Estadísticas (→ hub supervisor) | Se funden en **una sola entrada nueva**, "Control y Gestión" | Ver B.2 — deja de llamarse "Configuración" a secas; Estadísticas no necesita entrada propia, se alcanza entrando ahí |
| *(faltan hoy)* Mi trabajo, Plantillas, Entidades, Requisitos documentales, **Control y Gestión** | Se añaden | Módulos reales u homólogos (`order` 5, 80, 20, 81, *nuevo*) sin tarjeta en el dashboard actual |
| Inicio | No aplica — única excepción de raíz | Es la propia página del dashboard; un enlace a sí misma no aporta nada |

**Resuelto — la pregunta que el 1:1 había reabierto:** Estadísticas no necesita entrada propia
ni queda huérfana de acceso promovido — se resuelve en B.2 dándole entrada propia al hub
entero ("Control y Gestión"), universal para los 4 roles.

**Mi Perfil — migración, no excepción nueva.** `perfil` vive hoy en `app/routes/perfil.py`
(patrón antiguo: registrado a mano en `app/__init__.py:71`, sin `metadata.json`), a diferencia
de Usuarios/Entidades/Expedientes/Proyectos/Plantillas/Requisitos, que viven en `app/modules/`
y se descubren solos. Para que "Mi Perfil" entre en el mismo 1:1 real (y no como una segunda
excepción hardcodeada junto a "Inicio"), se migra a `app/modules/perfil/` con su propio
`metadata.json` — mueve también la carpeta de templates (`app/templates/perfil/` →
`app/modules/perfil/templates/perfil/`). El enlace "Editar perfil" que ya existe en el
dropdown del topbar (`_topbar.html:72-77`) no cambia: sigue siendo un `url_for('perfil.index')`
directo — apunta al mismo endpoint, que ahora además tiene una entrada canónica en `module_nav`.

**Principio general (no solo para Perfil):** si el mismo destino se enlaza desde más de una
superficie (topbar, sidebar, dashboard, tarjeta de un hub...), todas esas superficies deben
apuntar al mismo mecanismo canónico (módulo + `metadata.json`) — no vale que una superficie lo
trate como módulo de primera clase y otra lo enlace por libre. "Inicio" sigue siendo la única
excepción legítima, porque no es un destino más: es la propia página contenedora, no puede
enlazarse a sí misma.

**Nota aparcada — el nombre "Dashboard".** Observación de nomenclatura, no de función: un
dashboard en sentido estricto (el "salpicadero", no el "cuadro de mandos") muestra información
de estado, no accesos directos. La página `Inicio`/`index_v1.html` de hoy es en realidad un
lanzador de accesos (aunque su título interno diga "Dashboard" y su `<h1>` diga "Panel de
Control") — el nombre "dashboard" describiría mejor a Estadísticas, que sí es información
agregada. No cambia nada de lo decidido aquí (el grid de tarjetas 1:1 sigue siendo la solución
correcta de accesos); si se retoma, sería un rediseño de propósito de esa vista en concreto,
no un ajuste de sidebar ni de `metadata.json`.

### E — El prefijo `/admin`: reencuadrar, no aparcar

**Corrección (2026-07-05): esto no estaba aparcado, quedó pendiente de esta ronda.** El
criterio no es solo "ningún módulo nuevo usa `/admin/*`" — es más preciso: **`/admin` se
reserva para lo que sea genuinamente exclusivo del rol ADMIN** (distinto de SUPERVISOR), tal
como se plantea en "Generalización" más abajo. Hoy sus dos ocupantes (`admin_plantillas`,
`admin_requisitos`) no son eso — son `acceder_X` universal / `gestionar_X` restringido a
ADMIN+SUPERVISOR, exactamente como Usuarios o Entidades. Son "rutas mal formadas en nombre":
el prefijo afirma una exclusividad que no existe.

Acción: renombrar el `url_prefix` de los dos módulos, sin el prefijo `/admin` — mismo patrón
que Entidades/Usuarios/Proyectos/Expedientes (nombre de recurso, sin prefijo de categoría). En
Flask esto es barato: `url_for()` usa el nombre de endpoint, no la URL literal, así que cambiar
solo `url_prefix` no rompe ningún enlace interno — el coste real es bookmarks externos y, si
los hubiera, registros de bitácora con la ruta literal. Renombrar además el nombre de
blueprint/directorio (`app/modules/admin_requisitos/` → `app/modules/requisitos_documentales/`)
es un paso más profundo y opcional — `ModuleRegistry` lo descubre por escaneo de directorio, así
que tampoco exige registro manual, pero sí tocaría cualquier `url_for('admin_requisitos.…')` que
exista en otros templates. La profundidad (solo `url_prefix`, o también blueprint/directorio) se
elige al escribir el issue.

`/admin` queda libre para el día en que exista contenido genuinamente exclusivo de ADMIN (ver
"Generalización" abajo) — hoy no hay ningún caso concreto, no se crea nada nuevo ahí.

---

## Generalización — si `ADMIN` necesita algo propio en el futuro

Mismo principio: si `ADMIN` (hoy superset de `SUPERVISOR` solo en permisos puntuales como
`eliminar_requisitos_documentales`) llega a tener una vista que `SUPERVISOR` no debe ver, el
patrón a seguir es el mismo que ya usa "Mi trabajo" (ADR-017): **una única entrada de
navegación que se resuelve por rol activo**, no una entrada nueva por rol. Hoy no hay ningún
caso concreto — no crear la abstracción hasta que exista (mismo criterio que ya aplica
`DECISIONES_UI.md` a otras extensiones del layout).

---

## Decidido en esta ronda (ya no está abierto)

- Estadísticas no se promueve por separado — se llega vía "Control y Gestión" (B.2).
- Campo `navigation.description`: sí, se añade a `metadata.json` (punto D).
- Nombre del contenedor del hub: **"Control y Gestión"** (B.2) — enmienda ADR-028 §1.
- `perfil`: se migra a `app/modules/perfil/`, no se hardcodea como excepción (punto D).
- Prefijo `/admin`: se reencuadra activamente, no se aparca (E revisada).
- Nuevo Expediente: se elimina del dashboard sin sustituto — el wizard ya vuelve al listado
  tras crear, verificado en código.

## Abierto — decisiones que te corresponden a ti

1. **Alcance de esta sesión**: este documento dice qué y por qué, pero tocar
   `permisos.py`/rutas/templates/`metadata.json` entra en "Análisis de impacto previo" de
   `REGLAS_DESARROLLO.md` — tabla de consumidores antes de escribir código. Dado que "una
   sesión = un issue", propongo abrir issue(s) nuevos para lo que decidas ejecutar (posible
   candidato a ADR-029 formal) en vez de implementarlo en esta misma conversación.
2. **Prioridad relativa** entre A/B/C/D/E — ¿todo en un mismo issue o repartido?
3. **Detalles menores de implementación** (no bloquean el acuerdo, se fijan al escribir el
   issue): valores de `order` para "Control y Gestión" y "Mi perfil"; texto final del nuevo
   `url_prefix` de Plantillas/Requisitos; profundidad del renombrado de E (solo `url_prefix`,
   o también nombre de blueprint/directorio).

---

## Referencias

- ADR-013 — `docs/decisiones/ADR-013-permisos-blandos-generalizados.md`
- ADR-014 — `docs/decisiones/ADR-014-layout-app-unificado.md`
- ADR-017 — `docs/decisiones/ADR-017-vista-mi-trabajo-administrativo.md` (§"Deuda conocida")
- ADR-028 — `docs/decisiones/ADR-028-vista-supervisor.md`
- `docs/referencia/CATALOGO_TABLAS_ESTRUCTURALES.md`
- Código: `app/modules/__init__.py`, `app/utils/permisos.py`, `app/modules/supervisor/`,
  `app/modules/admin_requisitos/`, `app/templates/dashboard/index_v1.html`,
  `app/templates/layout/_sidebar.html`
