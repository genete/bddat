# ADR-029 — Navegación administrativa: sidebar y dashboard 1:1, hub del supervisor universal

**Estado:** Adoptada
**Fecha:** 2026-07-05
**Issues:** #588 (hub universal), #589 (dashboard 1:1), #590 (retirar prefijo `/admin`)
**Enmienda:** ADR-028 §1

> **Nota de implementación (2026-07-13, #588).** Al implementar se generalizó el
> principio de esta ADR un paso más: si el acceso deja de depender del rol, el nombre
> de la ruta tampoco debería llevarlo. Dos ajustes sobre lo escrito abajo:
> 1. El permiso final se llamó `acceder_gestion_control` (no `acceder_supervision`) y la
>    URL del hub pasó de `/supervisor/` a `/gestion_y_control/` — coherente con el nuevo
>    nombre del permiso y con el label "Control y Gestión" ya decidido en §2. El nombre
>    interno del blueprint Flask (`supervisor`) no cambió — cambiar `url_prefix` no
>    rompe `url_for()`, renombrar el blueprint sí sería más profundo (mismo criterio que
>    §4 ya aplicaba a `admin_plantillas`/`admin_requisitos`).
> 2. Se resolvió de paso el caso 2 de la "Deuda conocida" de ADR-017 (heterogeneidad de
>    URLs de «Mi trabajo»): el contenido administrativo de `mi_trabajo` (cola + subir
>    documento) se extrajo a un módulo propio y universal, `tareas_y_subidas`
>    (`acceder_tareas_y_subidas`, 4 roles) — su escritura, `gestionar_tareas`, ya era
>    universal desde ADR-017 §6, solo la navegación la escondía tras el rol
>    ADMINISTRATIVO. `mi_trabajo.index` queda como dispatcher puro y simétrico para los
>    tres roles. El caso 3 (TRAMITADOR → `/expedientes/seguimiento/`) sigue abierto, sin
>    tocar: no es un blueprint propio que renombrar, es una vista prestada de otro
>    dominio — ver ADR-017 para el detalle completo.

> **Nota de implementación (2026-07-13, #589).** Tres ajustes sobre lo escrito abajo,
> acordados con Carlos al implementar:
> 1. **El criterio de clasificación de §1 se revisa** — ver §1bis, nueva sección. La
>    "consulta diaria" resultó subjetiva e inconsistente con cómo ya se habían clasificado
>    Ítems técnicos (#594) y Tipos de documento (#621). Plantillas, Requisitos documentales
>    y Catálogo de requerimientos pierden su `metadata.json`/entrada de sidebar y pasan a
>    ser solo tarjeta del hub (Requisitos ya tenía tarjeta desde #588; Plantillas y
>    Catálogo de requerimientos la ganan ahora).
> 2. **El bug de "rol-en-crudo" no vivía solo en `index_v1.html`** como describe el
>    Contexto — la fuente real es el context processor compartido `inject_module_nav`
>    (`app/__init__.py`), que además alimenta el sidebar y (vía `palette_nav()`,
>    `app/utils/react_islas.py`) el Command Palette. Los tres consumían
>    `current_user.roles` (todos los roles asignados) en vez de
>    `session.get('rol_activo_nombre')` — se corrige en la fuente única, no en cada
>    consumidor.
> 3. **"Mi Perfil" no se incorpora a `module_nav`**, al contrario de lo que preveía §3: con
>    el criterio revisado (punto 1) no encaja como página-destino de rol ni objeto de
>    dominio, y unirse a `module_nav` lo habría hecho aparecer también en el sidebar (mismo
>    mecanismo para ambas superficies) — indeseado, hoy solo vive en el topbar. Se migra el
>    código a `app/modules/perfil/` (consistencia de autodescubrimiento) pero **sin**
>    `metadata.json` — sigue como segunda excepción hardcodeada en el dashboard, junto a
>    "Inicio".

---

## Contexto

Al cerrar #583 (CRUD de `requisitos_documentales`) apareció una entrada nueva de sidebar bajo
`/admin/requisitos/`, sin enlace desde el hub del supervisor (`/supervisor/`, ADR-028) ni
desde el dashboard principal. El catálogo de tablas estructurales
(`docs/referencia/CATALOGO_TABLAS_ESTRUCTURALES.md`) anticipa más CRUD de este tipo (reglas
del motor #170, tablas maestras #171, catálogo de plazos) — sin un principio explícito, cada
uno se habría añadido por el mismo camino ad hoc: copiar el módulo hermano más parecido sin
releer las decisiones de navegación vigentes.

### Causa raíz de `/admin/requisitos`

El código tenía dos precedentes distintos para "pantalla de administración":

| Precedente | Patrón | Origen |
|---|---|---|
| `admin_plantillas` (#545) | Módulo propio, `metadata.json` propio, sidebar propio, prefijo `/admin/plantillas` | Anterior a ADR-013/017/028 — el propio ADR-013 lo cita como ejemplo del modelo restrictivo antiguo |
| `supervisor` (#579, ADR-028) | Blueprint dedicado, sin `metadata.json` a propósito, alcanzable solo vía "Mi trabajo" | Posterior — diseñado para "capa de administración sobre tablas ya vivas" |

#583 copió el patrón de UI de `admin_plantillas` (acierto: listado+inspector, ADR-023) pero
también su emplazamiento de navegación (módulo propio, `/admin/*`) sin derivarlo de ADR-028,
que ya había fijado dónde vive este tipo de CRUD: como tarjeta del bloque GESTIÓN del hub.
`/admin` no es un concepto real de la app — no hay blueprint `admin` ni hub `/admin/` — es
solo un prefijo heredado de un patrón que ADR-013/017/028 ya habían sustituido sin retirar a
sus dos ocupantes.

### Tres superficies de navegación sin coordinar

El sidebar se genera desde `ModuleRegistry.get_navigation()` (`app/modules/__init__.py`),
agregando el `metadata.json` de cada módulo. El dashboard
(`app/templates/dashboard/index_v1.html`) y el hub del supervisor
(`app/modules/supervisor/templates/supervisor/index.html`) eran listas de tarjetas
mantenidas a mano, cada una con su propio criterio de qué mostrar. Habían divergido: el
dashboard no tenía tarjeta de Entidades, Plantillas ni Requisitos (solo existían en sidebar);
el hub nunca listó Requisitos documentales pese a ser exactamente lo que aloja.

Además, `index_v1.html` decidía qué tarjetas mostrar mirando `current_user.roles` (todos los
roles asignados en BD) en vez de `session.rol_activo_nombre` (el rol activo, que es lo que
`tiene_permiso()` y el resto de la app comprueban — ver `_topbar.html`, `permisos.py`). Efecto:
un usuario multi-rol veía tarjetas que su rol activo no podía abrir, y rebotaba con el toast
"No tiene permisos suficientes para acceder a esta sección". La tarjeta "Tareas" tenía además
un bug de cableado propio: se mostraba a los 4 roles pero enlazaba siempre a
`expedientes.seguimiento` (el seguimiento del TRAMITADOR), sin sentido para SUPERVISOR/ADMIN.

### Colisión entre ADR-013 y ADR-028

ADR-013 fija que la visibilidad es universal por defecto y que toda excepción debe declararse
explícitamente (DNI, estadísticas individuales nombradas). ADR-028, al no darle entrada de
sidebar al hub del supervisor, creó de facto una tercera excepción — pero sin declararla como
tal: ningún párrafo de ADR-028 dice "esto se oculta a propósito, por esta razón". Quedó
inalcanzable por omisión de navegación, no por una decisión de visibilidad tomada
conscientemente. El panel de estadísticas (#579/#580) heredó ese mismo permiso de entrada
(`acceder_supervision`) en vez de recibir su propio `acceder_X`, pese a que ADR-013 ya había
aclarado por escrito que un recuento agregado (expedientes por técnico, por estado) no es la
"estadística individual" que hay que restringir.

---

## Decisión

### 1. Principio de clasificación para pantallas nuevas

> **`[SUPERSEDIDO parcialmente, #589]`** El criterio original ("¿la consultan a diario
> roles no-supervisores?") se sustituye por el de §1bis — ver nota de implementación
> al inicio del documento. Se conserva aquí como registro de la primera decisión.

Para decidir dónde vive una pantalla administrativa nueva, una sola pregunta:

> **¿La consultan a diario roles no-supervisores como parte de su trabajo (aunque no la
> editen), o es una herramienta de configuración que solo el supervisor visita para ajustar
> el sistema?**

| Respuesta | Patrón |
|---|---|
| Consulta diaria de cualquier rol | Entrada propia de sidebar (`metadata.json`), `acceder_X` universal + `gestionar_X` restringido. Ej.: Expedientes, Entidades, Usuarios, Proyectos, Plantillas, Requisitos documentales |
| Configuración pura del supervisor | Tarjeta dentro del hub (`/gestion_y_control/`, bloque Control o Gestión), sin `metadata.json` propio. Ej.: reglas del motor (#170), tablas maestras (#171), plazos legales, operaciones masivas (#295) |
| El supervisor administra algo que ya tiene entrada propia | No sustituye la entrada — se añade también como tarjeta del hub, a modo de atajo (patrón ya usado por Usuarios) |

No hay vista con contenido genuinamente exclusivo del supervisor más allá de las dos
excepciones que ya declara ADR-013 (DNI; una futura vista de rendimiento individual nombrado,
que ni siquiera existe). El hub en sí mismo tampoco lo es: se pensó como "página propia por
rol" (simétrica a la cola del ADMINISTRATIVO o el seguimiento del TRAMITADOR), pero a
diferencia de esas, no aloja contenido personal de nadie — es agregado del dominio.

### 1bis. Revisión del criterio: "consulta diaria" era frágil  `[#589]`

Al aplicar §1 retroactivamente a Plantillas y Requisitos documentales (ambos anteriores a
esta ADR, con entrada propia heredada) saltó la grieta: los dos módulos más recientes
construidos ya bajo esta ADR — Ítems técnicos (#594) y Tipos de documento (#621) — se
diseñaron **a propósito sin entrada propia** citando este mismo §1, pese a que Tipos de
documento se usa en cada subida de documento — probablemente más "a diario" que Plantillas.
Nadie había verificado si Plantillas/Requisitos seguían mereciendo su entrada o solo la
conservaban por herencia de un patrón anterior a esta ADR (#545, #583). "Consulta diaria" no
es falsable de forma consistente — cualquier catálogo puede argumentarse como "consultado a
diario" por alguien.

**Criterio revisado**, estructural en vez de subjetivo — entrada propia de sidebar
**solo** para:

1. Las páginas-destino de rol a las que redirige "Mi trabajo": `Tareas y Subidas`
   (ADMINISTRATIVO), `Control y Gestión` (SUPERVISOR/ADMIN), y el futuro hub del
   TRAMITADOR (deuda abierta de ADR-017, sin construir).
2. Los objetos de dominio reales sobre los que gira la aplicación: `Expedientes`,
   `Proyectos`, `Entidades`, `Usuarios`.

Todo lo demás —Plantillas, Requisitos documentales, Catálogo de requerimientos, Tablas
maestras, Configuración del motor, Ítems técnicos, Tipos de documento, Plazos legales— son
catálogos o configuración: visibles y alcanzables (ADR-013 sigue vigente, nada se oculta),
pero **solo como tarjeta del hub**, nunca como entrada de sidebar ni de dashboard. Sidebar pasa
de 11 entradas a 8; cualquier catálogo futuro cae en el patrón sin debate — no hay zona gris
que discutir caso a caso.

**Consecuencia en el Command Palette (Ctrl+K).** Los atajos "IR A" (`palette_nav()`) se
derivan de la misma fuente (`ModuleRegistry.get_navigation()`) — Plantillas, Requisitos
documentales y Catálogo de requerimientos pierden su atajo genérico. Para Plantillas no hay
pérdida real: la búsqueda por nombre (`/api/search`, `_buscar_plantillas()`) es un mecanismo
completamente aparte que no lee `metadata.json` — sigue intacta. Requisitos documentales y
Catálogo de requerimientos nunca tuvieron búsqueda por nombre (no están en `BUSCADORES`) — tras
el cambio quedan sin ningún atajo rápido, solo alcanzables por el hub o URL directa. Extender
`api_search.py` a más catálogos (búsqueda global de verdad, no solo 4 tipos) se identifica
como necesidad real pero **queda fuera de #589** — es otro issue, sin filear todavía.

### 2. Universalizar el acceso al hub del supervisor + entrada "Control y Gestión"

**Enmienda ADR-028 §1** ("blueprint supervisor dedicado, deliberadamente sin metadata.json
[así no genera una segunda entrada de sidebar]"). Se resuelve la colisión con ADR-013 a favor
del principio más fundacional: si no hay una razón declarada para ocultar algo, no se oculta
— tampoco indirectamente por no darle puerta de entrada.

```python
# app/utils/permisos.py — renombrado a acceder_gestion_control en implementación
# (ver nota de implementación al inicio de este documento)
'acceder_gestion_control': {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
```

No hace falta permiso nuevo: ni el hub ni Estadísticas mutan nada — son lectura pura. La
escritura real vive en las hojas (Usuarios → `gestionar_usuarios`, Requisitos →
`gestionar_requisitos_documentales`, y lo mismo aplicará a reglas del motor, plazos y
operaciones masivas cuando se construyan — sus `gestionar_X` ya están reservados en
`permisos.py`). Si en el futuro aparece contenido genuinamente sensible dentro del hub, se le
da su propio permiso estrecho en ese momento (mismo patrón que `ver_dni_usuarios`) — no se
vuelve a tapar el hub entero por precaución.

El hub gana `metadata.json` propio, con label **"Control y Gestión"** — no "Configuración":
reutiliza el vocabulario que ya tienen los dos bloques internos (ADR-028 §1: CONTROL /
GESTIÓN), evita que la etiqueta del contenedor choque con la tarjeta interior "Configuración
del motor", y representa mejor lo que hay dentro (CONTROL incluye Estadísticas y las futuras
Auditoría/Informes, que no son "configuración" en sentido estricto). Con esta entrada,
Estadísticas no necesita la suya propia — se alcanza entrando en "Control y Gestión" (ya
existe como tarjeta del bloque CONTROL).

Redundancia asumida, no accidental: para SUPERVISOR/ADMIN, "Mi trabajo" y "Control y Gestión"
llevan al mismo sitio (`supervisor.index`) — mismo patrón que ya tiene Usuarios (alcanzable
por sidebar directo y por tarjeta del hub).

### 3. Dashboard como proyección 1:1 del sidebar

El dashboard deja de ser una superficie de navegación independiente. Es una vista de
bienvenida sobre la misma lista que consume el sidebar (`ModuleRegistry.get_navigation()`).
Cada módulo con `metadata.json` aporta exactamente una tarjeta y exactamente una entrada de
sidebar; el orden de las tarjetas sigue el mismo campo `order`. Esto cierra de raíz el bug de
rol-en-crudo: al generarse desde `module_nav`, hereda el mismo filtro por rol activo que ya
usa el sidebar.

Se añade `navigation.description` a cada `metadata.json` para que sidebar y dashboard
compartan literalmente el mismo texto (no solo la misma ruta) — el sidebar puede ignorarlo o
usarlo de tooltip, el dashboard lo muestra como subtítulo de la tarjeta.

**Única excepción legítima: "Inicio".** Es la propia página del dashboard — un enlace a sí
misma no aporta nada. Ninguna otra tarjeta se hardcodea fuera de `module_nav`.

**Principio general:** si el mismo destino se enlaza desde más de una superficie (topbar,
sidebar, dashboard, tarjeta de un hub...), todas deben apuntar al mismo mecanismo canónico
(módulo + `metadata.json`) — no vale que una superficie lo trate como módulo de primera clase
y otra lo enlace por libre. Por esto, "Mi Perfil" (hoy en `app/routes/perfil.py`, patrón
antiguo sin `metadata.json`) se migra a `app/modules/perfil/`.

> **`[REVISADO, #589]`** El resto de esta frase ("en vez de hardcodearse como una segunda
> excepción junto a 'Inicio'") queda sin efecto — ver nota de implementación al inicio del
> documento, punto 3, y §1bis. El código se migra por consistencia de autodescubrimiento,
> pero Perfil no entra en `module_nav`: bajo el criterio revisado no es página-destino de rol
> ni objeto de dominio, y haría que apareciera también en el sidebar (mismo mecanismo para
> ambas superficies). Sigue siendo, a propósito, la segunda excepción hardcodeada del
> dashboard junto a "Inicio".

Tarjetas que se retiran del dashboard actual, con la función ya cubierta en otro sitio
(verificado, no solo asumido):

| Tarjeta | Por qué se retira |
|---|---|
| Mis Expedientes | Ya es un filtro (`responsable=yo`) sobre Expedientes, no un destino propio |
| Nuevo Expediente | El listado ya tiene su propio botón "Nuevo" (`expedientes/listado_v2.html`); verificado que el wizard, al terminar, redirige a `expedientes.listado_v2` (`wizard_expediente.py`) — economía de clics para altas sucesivas ya garantizada |
| Tareas | Duplica "Mi trabajo"; además mal cableada (ver Contexto) |
| Estadísticas / Configuración | Se funden en la nueva entrada "Control y Gestión" (§2) |

### 4. `/admin` se reserva para lo exclusivo de ADMIN

El prefijo `/admin/*` no corresponde a ningún concepto real de la app — no hay blueprint
`admin` ni rol con vista propia distinta de SUPERVISOR. Se reserva para el día en que exista
contenido genuinamente exclusivo del rol ADMIN (ver Generalización). `admin_plantillas` y
`admin_requisitos` pierden ese prefijo — su lectura ya es universal, no son casos de ADMIN
exclusivo. Cambiar `url_prefix` no rompe `url_for()` (usa el nombre de endpoint, no la URL
literal); renombrar además blueprint/directorio es un paso más profundo y opcional, a decidir
en la implementación (#590).

---

## Generalización — si `ADMIN` necesita algo propio en el futuro

Mismo principio que "Mi trabajo" (ADR-017): una única entrada de navegación que se resuelve
por rol activo, no una entrada nueva por rol. Hoy no hay ningún caso concreto de contenido
exclusivo de ADMIN (solo permisos puntuales más restrictivos, como
`eliminar_requisitos_documentales`) — no se crea la abstracción hasta que exista. El prefijo
`/admin` (§4) queda reservado para cuando llegue ese caso.

---

## Por qué

- **Cierra una colisión real entre dos ADR adoptadas**, no solo un flequillo de navegación —
  ADR-013 y ADR-028 apuntaban en direcciones distintas y nadie lo había puesto por escrito.
- **Una sola fuente de verdad para "qué se puede navegar"**: antes eran tres listas
  independientes (sidebar, dashboard, hub) que ya habían divergido; con `module_nav` como
  única fuente, divergir exige un cambio consciente, no un olvido.
- **Corrige dos bugs reales de paso** (rol-en-crudo del dashboard; tarjeta "Tareas" mal
  cableada) sin necesidad de un issue aparte — comparten causa y solución con el resto.
- **Escala**: los próximos CRUD (#170, #171, plazos, #295) ya tienen dónde caer sin inventar
  nada — el criterio de clasificación (§1) decide, no la costumbre de copiar al hermano más
  cercano.

---

## Cómo implementar

Repartido en tres issues por unidad de PR:

1. **#588** — Universalizar el permiso de entrada (renombrado a `acceder_gestion_control`),
   `metadata.json` del hub ("Control y Gestión", URL `/gestion_y_control/`), tarjeta de
   Requisitos documentales en GESTIÓN, y extracción de `tareas_y_subidas` como módulo
   universal propio (resuelve de paso el caso 2 de la deuda de ADR-017).
2. **#589** — Dashboard generado desde `module_nav`, campo `navigation.description`,
   migración de `perfil` a `app/modules/`, retirada de tarjetas obsoletas.
3. **#590** — Retirar el prefijo `/admin` de Plantillas y Requisitos documentales.

Cada uno lleva su propio smoke test (ADR-019) y verificación manual Playwright MCP por rol.

---

## Alternativa descartada

**Dar a Estadísticas una entrada de sidebar propia, independiente del hub.** Considerada
(era la propuesta inicial del PRE-ADR). Descartada porque duplicaría la entrada del hub sin
necesidad: universalizando el hub entero, Estadísticas ya es alcanzable sin inventar una
puerta nueva — y evita otra entrada más de sidebar para un contenido que ya vive dentro de
"Control y Gestión".

---

## Notas aparcadas

**El nombre "Dashboard".** Observación de nomenclatura, no de función: un dashboard en
sentido estricto (el "salpicadero", no el "cuadro de mandos") muestra información de estado,
no accesos directos. La página `Inicio` es en realidad un lanzador de accesos, aunque su
título interno diga "Dashboard" y su `<h1>` diga "Panel de Control" — ese nombre describiría
mejor a Estadísticas. No cambia nada de lo decidido aquí (el grid de tarjetas 1:1 sigue
siendo la solución correcta de accesos); si se retoma, sería un rediseño de propósito de esa
vista en concreto, no un ajuste de sidebar ni de `metadata.json`.

---

## Referencias

- ADR-013 — `docs/decisiones/ADR-013-permisos-blandos-generalizados.md`
- ADR-014 — `docs/decisiones/ADR-014-layout-app-unificado.md`
- ADR-017 — `docs/decisiones/ADR-017-vista-mi-trabajo-administrativo.md`
- ADR-028 — `docs/decisiones/ADR-028-vista-supervisor.md` (enmendada §1)
- `docs/diseño/PRE-ADR-navegacion-administrativa.md` — material de fondo, diagnóstico
  completo con evidencia línea a línea
- `docs/referencia/CATALOGO_TABLAS_ESTRUCTURALES.md`
