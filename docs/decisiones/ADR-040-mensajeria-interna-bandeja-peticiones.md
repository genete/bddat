# ADR-040 — Mensajería interna: bandeja de peticiones al supervisor

**Estado:** Adoptada
**Fecha:** 2026-08-07 (§9 diferido a #773 el 2026-08-08)
**Issues:** #28 (N053 parcial, N054 mitad de cambio de rol), #773 (§9, modal de alta)
**Enmienda:** ADR-014 §5 (topbar de cuatro elementos)
**Relacionado:** ADR-020 (dock global — *no* se enmienda, ver §3), ADR-023 (list-detail
inspector), ADR-029 §1bis (emplazamiento de pantallas nuevas), ADR-034 (tabla
`notificaciones`), #684 (contrato heredado), #479 (broadcast del modo del motor)

---

## Contexto

#28 se redactó como "sistema de notificaciones internas": dos tablas
(`notificaciones` + `solicitudes_cambio_rol`), cuatro vistas y un badge en la campana
del topbar. Al analizarlo contra el código real (sesión 2026-08-07) tres de esas piezas
resultaron estar ya ocupadas o mal encuadradas:

1. **`notificaciones` está ocupada** por ADR-034 — el seguimiento del acto de notificar
   al interesado (canal, dos intentos LPACAP, fecha de puesta a disposición). En este
   dominio "notificación" es un acto jurídico con efectos de plazo.
2. **La campana del topbar está ocupada** por el dock (ADR-020 §2), cuyo tab "Avisos"
   ya usa además el término *aviso* para los toasts de sesión.
3. **El esquema propuesto tenía `usuario_id` como destinatario singular**, que no sirve
   para lo que de verdad hacen falta: peticiones dirigidas al Supervisor de guardia, no
   a una persona concreta. Anotado en su día en el comentario de #479.

Hay tres consumidores esperando: la casilla inerte "Solicitar guardado en catálogo" que
dejó #684 (`AnalizarEditor.jsx`), el `# TODO` de `perfil.solicitar_cambio_rol` (que hoy
hace `flash` y no persiste nada), y el comentario de #479.

---

## Decisión

### 1. Vocabulario: tres palabras, tres cosas distintas

| Palabra | Qué designa | Dónde vive |
|---|---|---|
| **Notificación** | Acto jurídico de notificar al interesado, con efectos de plazo | `notificaciones` (ADR-034) |
| **Aviso** | Toast de UI capturado durante la sesión, efímero | tab "Avisos" del dock (ADR-020) |
| **Mensaje** | Petición interna de un usuario al Supervisor, y su respuesta | `mensajes_internos` (esta ADR) |

La tabla se llama **`mensajes_internos`** y el vocabulario visible al usuario es
"mensajes". No se renombra `notificaciones`: el nombre correcto para lo de #28 es
"mensaje", así que liberar el otro nombre no compraría nada y costaría tocar ADR-034, su
migración, `estado_dominio.py`, `Tarea.resultado` y los checks de fase/trámite.

`peticiones_supervisor` se consideró (más literal: es lo que la tabla contiene). Se
descarta por coherencia con lo que el usuario ve en pantalla, y porque una misma fila
lleva la petición *y* la respuesta.

### 2. El destinatario no es un campo — la tabla es la bandeja del Supervisor

`mensajes_internos` **es**, por construcción, la bandeja de entrada del rol
SUPERVISOR/ADMIN. No hay `destinatario_usuario_id` ni `destinatario_rol_id`: lo que se
persiste es el **remitente**.

Esto evita el problema real que tenía el fan-out (una fila por destinatario al crear) en
este proyecto concreto: los roles son N:M y los permisos se evalúan contra el **rol
activo de sesión** (`permisos.py`), así que un usuario TRAMITADOR+SUPERVISOR recibiría
peticiones de supervisor mientras opera como tramitador, y al leerlas en un rol quedarían
leídas para siempre. Además el fan-out congela la lista: un supervisor de alta posterior
no vería las peticiones pendientes anteriores.

`remitente_usuario_id` es **NOT NULL** — ver §7 (el alta de usuario nuevo no entra por
aquí).

### 3. Una sola fila, tres estados

Una petición es **una fila** durante todo su ciclo de vida:

```
pendiente  →  hecho (+ resultado + notas)  →  acusado por el remitente
```

El Supervisor no genera una fila nueva al responder: cierra la misma. El usuario ve en un
solo objeto qué pidió y qué le contestaron, y los dos badges del sobre (§5) son dos
filtros del mismo registro. La alternativa de dos filas obligaría a reintroducir un
`destinatario_usuario_id` en la fila-respuesta — justo el campo que §2 elimina — y a
duplicar o perder el contexto del payload.

### 4. Schema

```sql
CREATE TABLE public.mensajes_internos (
    id                    SERIAL PRIMARY KEY,
    remitente_usuario_id  INTEGER     NOT NULL REFERENCES public.usuarios(id),
    tipo                  VARCHAR(40) NOT NULL,
    datos                 JSONB       NOT NULL,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Resolución por el Supervisor
    hecho                 BOOLEAN     NOT NULL DEFAULT FALSE,
    resultado             VARCHAR(10),
    notas                 TEXT,
    hecho_por_id          INTEGER     REFERENCES public.usuarios(id),
    hecho_at              TIMESTAMPTZ,

    -- Acuse del remitente
    acusado_at            TIMESTAMPTZ,

    CONSTRAINT ck_mi_resultado  CHECK (resultado IS NULL OR resultado IN ('ATENDIDA', 'DENEGADA')),
    CONSTRAINT ck_mi_hecho      CHECK (hecho = FALSE OR (resultado IS NOT NULL AND hecho_at IS NOT NULL)),
    CONSTRAINT ck_mi_acuse      CHECK (acusado_at IS NULL OR hecho = TRUE)
);

CREATE INDEX idx_mi_pendientes ON public.mensajes_internos (created_at) WHERE hecho = FALSE;
CREATE INDEX idx_mi_remitente  ON public.mensajes_internos (remitente_usuario_id, acusado_at);
```

**`resultado` existe además de `hecho`** a propósito: sin él, el veredicto viviría solo
en la prosa libre de `notas` — no contable, no filtrable, no legible por el front sin
interpretar texto. Para "solicitar cambio de rol", saber si se concedió o se denegó es el
dato, no un adorno.

**`hecho` booleano es redundante con `hecho_at IS NOT NULL`.** Se mantiene explícito
porque es el campo del modelo mental de la interfaz (la casilla que el Supervisor marca);
`hecho_at`/`hecho_por_id` son la traza de quién y cuándo. `ck_mi_hecho` impide que
divergan.

### 5. El "qué se pide" es JSON con un servicio de codificación/render único

`tipo` + `datos` (JSONB). Cada punto del código que genera una petición sabe codificar su
payload, y el inspector sabe renderizarlo — **ambos a través del mismo servicio**
(`app/services/mensajes_internos.py`), con un registro de tipos que declara para cada uno
su codificador, su validación y su render legible. Nunca se codifica el formato en dos
sitios.

Esto **no** exige un canal de copy compartido entre Python y JS (el problema que #766
resolvió con dos constantes gemelas por convención): el inspector de ADR-023 es un
**fragmento Jinja servido por el backend** (`/<id>/fragmento`), así que productor y
renderizador son ambos Python. Un solo sitio por construcción.

Tipos previstos al cerrar #28:

| `tipo` | Origen | Payload |
|---|---|---|
| `CAMBIO_ROL` | Mi Perfil (N054) | rol solicitado + justificación |
| `ALTA_CATALOGO_REQUERIMIENTO` | Shuttle de ANALIZAR (contrato de #684) | texto propuesto + categoría |

N055 (cambios de plantillas), N056 (avisos técnicos) y N070 (mejoras del manual) son un
`tipo` nuevo y un `crear()` de una línea cada uno cuando toque — no requieren tocar el
schema ni el servicio.

### 6. Emplazamiento: sobre nuevo en el topbar, no la campana

**Enmienda a ADR-014 §5** (topbar de cuatro elementos: marca · búsqueda · notificaciones
· menú usuario). Pasa a cinco: se añade un **icono de sobre** junto a la campana.

La campana **no** se toca: sigue siendo el toggle del dock (ADR-020 §2), y ADR-020 no se
enmienda. El motivo por el que el buzón no es un tercer tab del dock es estructural, no
de gusto: el dock está diseñado para «un stream de líneas tipo consola» (ADR-020
§Contexto) y esto es un **list-detail con inspector** (ADR-023) — un listado con scroll
infinito no cabe en un panel ancho-y-bajo de 25vh. Sobre y campana son cosas distintas y
se ven distintas.

El CRUD **no lleva `metadata.json`**: no es página-destino de rol ni objeto de dominio
(ADR-029 §1bis), y se alcanza solo por el sobre del topbar. Precedente exacto: Mi Perfil,
alcanzable solo por el menú de usuario (ADR-029, nota de implementación #589, punto 3).
Sin entrada de sidebar, sin tarjeta de dashboard.

La pantalla reutiliza infraestructura existente sin añadir patrones: `lista_v2_base.html`
+ `ScrollInfinito` en modo `selection: { fragmentUrl }` (ADR-023) + `_detalle_fragmento` /
`_editar_fragmento`, con `inspector:saved` → `reload()` ya cableado.

### 7. Badge bimodal del sobre

Un solo número, calculado según el rol activo:

| Rol activo | Qué cuenta | Qué ve en el CRUD |
|---|---|---|
| Con `gestionar_mensajes_internos` | Peticiones `hecho = FALSE` (de todos) **+** propias resueltas sin acusar | Todas |
| Sin ese permiso | Propias resueltas sin acusar (`hecho = TRUE AND acusado_at IS NULL`) | Solo las suyas |

El acuse del remitente es **explícito** (inline en la fila o desde el inspector), no
implícito por abrir el listado. Para el Supervisor, marcar `hecho` *es* el acuse: no hay
un "leído" aparte — una petición dirigida al rol la atiende uno y queda atendida para
todos.

El filtrado por remitente se aplica **en el endpoint según permiso**, nunca por parámetro
que envíe el front.

### 8. Permisos

```python
'acceder_mensajes_internos':   {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
'gestionar_mensajes_internos': {'ADMIN', 'SUPERVISOR'},
```

Patrón `acceder`/`gestionar` de ADR-013: todos entran y ven las suyas; solo
SUPERVISOR/ADMIN ven las de todos y pueden marcar `hecho`/`resultado`/`notas`.

### 9. El alta de usuario nuevo no entra por el buzón

Quien no tiene cuenta no puede escribir en `mensajes_internos` — y **no se abre ninguna
ruta sin `@login_required`** para que pueda. Un formulario público exigiría captcha o
rate limiting, que hoy no existen en el proyecto, para cubrir un caso que en una
administración no ocurre así: el funcionario que entra no visita BDDAT antes de tener
credenciales.

En su lugar, el enlace muerto «Contactar con soporte técnico (próximamente)» del login
(`login_v0.html`, `href="#"`) pasa a abrir un **modal informativo** que indica a quién
escribir y qué datos mínimos aportar para el alta. Informativo y con "Aceptar" — no
persiste nada.

El patrón ya existe y se copia, no se inventa: el modal «Acerca de» de `footer.html`
(disparado con `data-bs-toggle="modal"`), que el login **ya tiene disponible** porque
`base_login.html` incluye ese partial y carga Bootstrap. El markup del modal nuevo vive en
`login_v0.html`, no en `footer.html`: solo tiene sentido antes de tener cuenta, así que no
procede colgarlo del shell autenticado.

Dato pendiente de Carlos, no inventado aquí: **la dirección de correo destino** y la lista
exacta de datos mínimos. Los campos candidatos derivados del modelo `Usuario` son siglas de
la Junta (p. ej. `LGC005`), nombre y apellidos, email, unidad territorial/provincia
(`unidad_organo`) y rol pretendido.

**El modal no entra en #28 — se difiere a #773** (decisión de Carlos al implementar #28,
2026-08-08). El diseño de este apartado no cambia; lo que cambia es cuándo. El modelo
`Usuario` va a ampliarse con los campos que exigen la automatización de bandeja y Notific@,
y la lista de "datos mínimos" debe salir del modelo **ya ampliado**: escribirla contra el
actual dejaría en producción un modal pidiendo datos incompletos para dar de alta a
alguien. La dependencia es de contenido, no de código — el modal es HTML estático.

N054 ("Solicitar alta o cambio de rol") queda por tanto cubierta **solo en su mitad de
cambio de rol** dentro de #28. La mitad de alta se cubre con el modal informativo de #773,
que es un cauce real aunque no sea un mecanismo de BDDAT.

### 10. El broadcast del modo del motor (#479) queda fuera, motivadamente

Un aviso de sistema a todos los usuarios activos **no encaja estructuralmente** en esta
tabla: no tiene remitente y no se "hace". Y su único caso real ya está resuelto: #479
dejó un semáforo permanente en el topbar con polling cada ~60s, visible a los 4 roles.
Un mensaje en el buzón no añadiría nada y obligaría a inventar un `leido` por persona
(tabla de lecturas) para el caso de menor valor del conjunto.

Si algún día aparece un broadcast que sí lo merezca, entra por una tabla de lecturas
—nunca por fan-out, por lo de §2— y probablemente en una tabla distinta de esta.

El comentario de #479 queda así resuelto por decisión, no por olvido.

---

## Por qué

- **El vocabulario es lo primero** porque el término equivocado contamina el sitio más
  sensible del proyecto: "notificación" tiene efectos de plazo en este dominio. Llamar
  notificación a un aviso de interfaz habría sido barato de escribir y caro de deshacer.
- **La tabla como bandeja** (sin campo destinatario) es más simple que cualquier XOR o
  fan-out, y es la única de las tres opciones que no choca con roles N:M + rol activo de
  sesión.
- **Una fila con tres estados** mantiene juntos petición y respuesta, que es como el
  usuario piensa el objeto, y hace que los dos badges sean dos filtros en vez de dos
  conceptos.
- **`tipo` + JSON con servicio único** es lo que permite que N055/N056/N070 cuesten una
  línea cada uno. Y el hecho de que el inspector sea Jinja del backend hace que el "no
  codificar en dos sitios" sea estructural, no una convención que haya que recordar.
- **Sobre ≠ campana** porque son contenidos de naturaleza distinta (persistente y
  accionable vs. efímero y de sesión) y porque un list-detail no cabe en el dock.
- **Sin superficie pública** para el alta: el coste (captcha, rate limiting, spam) es real
  y el caso de uso no lo es.

---

## Consecuencias

- **`solicitudes_cambio_rol` no se crea.** El issue #28 la pedía como segunda tabla; su
  contenido es un `tipo` + payload de `mensajes_internos`, y su `estado` es
  `hecho` + `resultado`.
- **`perfil.solicitar_cambio_rol`** deja de ser un `flash` sin efecto: pasa a abrir un
  modal con selector de rol + justificación y a crear la fila. Es el `# TODO` de
  `app/modules/perfil/routes.py` cerrado.
- **La casilla "Solicitar guardado en catálogo"** de `AnalizarEditor.jsx` se habilita y
  crea un mensaje `ALTA_CATALOGO_REQUERIMIENTO`. **No** pasa por el endpoint de #440 (eso
  sigue siendo escritura directa en el catálogo, exclusiva de quien puede curarlo); el
  requerimiento se añade igualmente como texto libre en la tarea.
- **ADR-014 §5** pasa de cuatro a cinco elementos de topbar.
- **ADR-020 no cambia.** La campana, el dock y sus dos tabs quedan como están.
- **El enlace muerto del login sigue muerto de momento** — el modal informativo se difiere
  a #773 (ver §9), a la espera de la ampliación del modelo `Usuario`.
- **N053 no llega al 100%**: este diseño cubre "petición dirigida al Supervisor", no
  "empujar una tarea concreta a una persona concreta" (eso es UI de la cola de tareas) ni
  un aviso genérico con destinatario libre.

---

## Alternativas descartadas

### A. Renombrar `notificaciones` → `notificaciones_administrativas`

Liberaría el nombre para el buzón. Descartada: el nombre correcto para el buzón es
"mensaje", así que el rename no compra nada y cuesta tocar ADR-034, su migración,
`estado_dominio.py`, `Tarea.resultado` y los checks de fase/trámite.

### B. Destinatario XOR `usuario_id` | `rol_id`

Propuesta intermedia entre el fan-out del issue y la decisión de §2. Descartada por
abstracción prematura: en cuanto la tabla *es* la bandeja del Supervisor, el campo no
tiene nada que discriminar.

### C. Fan-out: una fila por destinatario al crear

Lo que insinuaba el esquema original del issue. Descartada por §2: choca con roles N:M +
rol activo de sesión, y congela la lista de destinatarios en el momento del envío.

### D. Tercer tab "Mensajes" en el dock

Considerada y descartada en la propia sesión: el dock es un stream de líneas tipo consola
(ADR-020 §Contexto) y esto es un list-detail con scroll infinito e inspector editable.
Habría metido una pantalla de trabajo en un panel diseñado para logs.

### E. Formulario público de alta, sin login

Descartada por §9: exige captcha o rate limiting inexistentes hoy, para un caso que no
ocurre así en la práctica.

### F. `hecho` sin `resultado`

Considerada (era la formulación inicial). Descartada: dejaría el veredicto solo en la
prosa de `notas`, no contable ni filtrable, en el caso —cambio de rol— donde el veredicto
es precisamente el dato.

---

## Referencias

- ADR-014 §5 — `docs/decisiones/ADR-014-layout-app-unificado.md` (enmendada)
- ADR-020 — `docs/decisiones/ADR-020-dock-global.md`
- ADR-023 — `docs/decisiones/ADR-023-list-detail-inspector-universal.md`
- ADR-029 §1bis — `docs/decisiones/ADR-029-navegacion-administrativa.md`
- ADR-034 — `docs/decisiones/ADR-034-ciclo-vida-notificacion-dos-documentos.md`
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — Bloque 13 (N053-N056, N070)
