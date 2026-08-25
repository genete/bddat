# ADR-042 — Sub-procesos de cardinalidad variable en el árbol: organismos de CONSULTAS

**Estado:** Adoptada — pendiente de implementación (ver §Issues de implementación)
**Fecha:** 2026-08-25
**Depende de:** ADR-011 (vinculación trámites↔organismos), ADR-016 (vista de árbol del expediente), ADR-023 (list-detail + inspector universal), ADR-037 (vocabulario ESFTT vs permiso motor)
**Enmienda:** ADR-016 §1 (modelo de niveles del árbol), §2 (decorador de iteración, dejado pendiente en #500 a la espera de #471) y §16 (contrato de detalle lazy por nodo)
**Origen:** sesión de reenfoque de fase ANÁLISIS_DOCUMENTAL → CONSULTAS (2026-08-25).

---

## Contexto

La fase CONSULTAS tiene su backend prácticamente completo: modelo `OrganismoExpediente`
(#391), tabla puente `TramiteOrganismo` (#456, ADR-011), variables de motor para el cierre
(#460), certificado `CERT_FIN_IP_CONSULTAS` (#470). Lo que falta es la interfaz — #396 (panel
de organismos) y #652 (acción de crear traslado) siguen abiertos.

Al retirar `api_bc.py` por no tener consumidor (#577, posterior al último cierre de la matriz
de cobertura), su lógica de dominio se rescató literal a `app/services/consultas_organismos.py`
—`serializar_org_exp`, `crear_traslado`, `enviar_consultas`— con esta nota en la cabecera del
fichero: *"Sin consumidor HTTP hoy: quedan aquí, con sus tests, a la espera de la UI de
consultas que las reconecte."* Este ADR es esa reconexión.

### El problema de fondo: cardinalidad variable dentro de una fase

`DISEÑO_CONSULTAS_ORGANISMOS.md §1` ya señalaba el patrón: la fase CONSULTAS contiene un
número variable de organismos, y cada uno arrastra su propia cadena de trámites
(`CONSULTA_SEPARATA` → `CONSULTA_TRASLADO_TITULAR` → `CONSULTA_TRASLADO_ORGANISMO`, esta
última repetible). El árbol (ADR-016) fija **5 niveles horizontales fijos** —Expediente →
Solicitud → Fase → Trámite → Tarea— sin nivel intermedio para esto. El resultado, sin
intervención: bajo la fase CONSULTAS cuelgan tantos trámites del mismo tipo como organismos ×
vueltas haya, todos hermanos planos e indistinguibles a primera vista.

ADR-016 §2 ya dejó anotada la mitad de este problema y lo aplazó: *"la iteración —nº de vuelta
de consultas a organismos— queda fuera de v1: [...] depende de #471; se añadirá como decorador
cuando esa pieza exista"*. #471 existe desde #577 (`crear_traslado`, conteo de vueltas vía
`TramiteOrganismo`); el bloqueo técnico que justificaba el aplazamiento ya no aplica.

### El precedente: el bloque de tareas no es un nivel de dominio

`layout.js` ya resuelve un problema de forma parecida para las tareas de un trámite: el nodo
`tareas` es **sintético** —no existe tabla ni entidad "bloque de tareas"— e inyectado solo en
la capa de layout (`construirJerarquia()`, `layout.js:84-91`) para evitar que N tareas
ramifiquen horizontalmente bajo su trámite. El modelo ESFTT de 4 niveles no se toca. El
mecanismo de colapso (`colapso(dom, tieneHijos)`, `layout.js:67-69`) ya trata así tres niveles
no-hoja (solicitud, fase, trámite): omite los hijos del grafo y el nodo se pinta plegado con
badge de agregados (`NodoBase.jsx:53-58`).

Este ADR aplica el mismo principio un nivel más: un nodo sintético de agrupación entre Fase y
Trámite, derivado de un dato relacional que ya existe (`TramiteOrganismo`), no de una tabla de
dominio nueva.

---

## Decisión

### A — Nodo sintético `organismo` en el árbol

`construirJerarquia()` (`layout.js`) agrupa, para cada fase, los trámites vinculados a un
`organismo_expediente_id` (vía `TramiteOrganismo`) bajo un nodo sintético `organismo` —hijo de
la Fase, padre de esos Trámites—, colapsable con el mismo mecanismo que ya usan
solicitud/fase/trámite (`esFinalizado()` gana un caso para `'organismo'`, criterio: `estado`
en `cerrado_favorable` / `cerrado_con_condicionados` / `exonerado`). Los trámites de la fase
**sin** organismo vinculado (el propio `CERT_FIN_IP_CONSULTAS` de cierre) cuelgan directos de
la fase, como hoy.

`NodoOrganismo.jsx` reutiliza `NodoBase.jsx` igual que `NodoTramite.jsx`/`NodoFase.jsx` —una
entrada nueva en `ICONO_TIPO` (`NodoBase.jsx:12-17`), sin componente bespoke.

El título del nodo Trámite dentro de un grupo `organismo` incorpora el decorador de vuelta
("1ª" / "2ª") que ADR-016 §2 dejó pendiente, ahora sin bloqueo técnico.

**Backend:** `_serializar_fase()` (`arbol_expediente.py`) necesita el join con
`TramiteOrganismo` para particionar `fase.tramites` en "con organismo" / "sin organismo" antes
de serializar. Sin esto el frontend no tiene con qué agrupar.

### B — El detalle de fase se vuelve adaptativo por `tipo_fase.codigo`

`_detalle_fase()` (`detalle_nodo.py:260`) es hoy uniforme entre todos los tipos de fase — es la
primera vez que un tipo de fase concreto añade contenido propio al detalle lazy. Cuando
`tipo_fase.codigo == 'CONSULTAS'`, el payload gana una clave opcional `organismos`, poblada
reutilizando `serializar_org_exp()` (`consultas_organismos.py:44`), que ya devuelve
organismo/vía/estado/plazo_legal_dias/vuelta — las columnas que #396 pedía en su tabla. Es la
misma forma aditiva que ya usa `plazo` (solo presente en tareas `ESPERAR_PLAZO`).

En el frontend, `Inspector.jsx` gana un bloque `Organismos` que sigue el patrón ya existente de
`Campos`/`Plazo`/`Documentos`: se renderiza solo si el dato está presente.

Al pulsar una fila de ese bloque, la interacción es exactamente la que ya usa "Ir a tramitar"
desde seguimiento: seleccionar el nodo correspondiente en el árbol (`?nodo=`, ADR-016 §12).
Ninguna mutación ocurre desde el listado — solo navegación. La regla general del árbol como
único sitio de edición se mantiene sin excepción.

### C — Alta de organismo y envío en bloque viven en ese mismo bloque del inspector

`OrganismoExpediente` no es un nodo ESFTT creable por despensa —no cuelga del árbol de
dominio—, así que su alta no encaja como "crear hijo" de ningún nodo. Vive como acción dentro
del bloque `Organismos` del inspector de fase CONSULTAS (formulario corto: entidad
`rol_consultado=True`, vía, plazo, documento si `declaracion_responsable`), sin abrir pantalla
aparte y sin modificar el contrato de edición de ADR-023.

"Enviar consultas" (`enviar_consultas()`, #462, ya construido) es una **acción rápida de
fase** — la columna que ADR-016 §5 ya reserva por nivel. Vive como botón en ese mismo bloque.

### D — Crear traslado vía despensa del nodo Organismo, no botón bespoke

`crear_traslado()` (#471) se expone como entrada de la despensa/menú contextual del nodo
`organismo` del árbol, no como botón dentro de una vista de detalle separada (que era el plan
original de #652). Requiere que `tipos_creables.py` reconozca `'organismo'` como ámbito de
creación — el mismo mecanismo que ya sirve la despensa de cualquier otro nivel, gobernado por
el reparto de ADR-037 (vocabulario ESFTT vs permiso de motor: el motor decide si procede, la
despensa solo lista qué existe).

---

## Consecuencias

**Se gana:** el árbol sigue siendo la única superficie de edición real (§B/§D lo hacen
explícito, no solo lo mantienen por omisión); el trabajo de #396 se reduce a un bloque de
inspector + un nodo de árbol, sin pantalla nueva; #652 se resuelve con menos superficie de la
que proponía (despensa reutilizada, no componente nuevo); el decorador de vuelta pendiente
desde ADR-016 §2 se cierra de paso.

**Hay que tocar:** `layout.js` (nodo sintético + colapso), `NodoBase.jsx` (icono), backend
`arbol_expediente.py::_serializar_fase` (partición por organismo), `detalle_nodo.py::_detalle_fase`
(clave `organismos` condicional), `Inspector.jsx` (bloque `Organismos`), `tipos_creables.py`
(ámbito `organismo`).

**Riesgo asumido:** es la primera vez que el detalle de fase varía por `tipo_fase.codigo`. Si
en el futuro otra fase con sub-procesos de cardinalidad variable (`DISEÑO_CONSULTAS_ORGANISMOS.md
§1` señala el mismo patrón en ANÁLISIS_TÉCNICO, aunque hoy sin entidad que agrupar) necesitara
algo parecido, este ADR es el precedente a revisar antes de generalizar — no se generaliza aquí
sin necesidad concreta.

---

## Issues de implementación

- **#396** — nodo `organismo` del árbol (§A) + bloque `Organismos` del inspector (§B) + alta de
  organismo (§C, primera mitad). Reemplaza su alcance original de panel aparte.
- **#652** — entrada de despensa `crear_traslado` en el nodo `organismo` (§D). Reemplaza su
  alcance original de botón en panel.

No tocan este ADR: **#464** (seed real de `organismos_expediente`) y **#106** (listado DIR3) —
ninguno depende de dónde vive la UI, solo de que exista.

---

## Lo que este ADR no decide

- El diseño visual final (colores, tamaños) del nodo `organismo` — lo discutido fue un mockup
  ilustrativo, no una especificación de layout.
- Extender este patrón a `ANÁLISIS_TÉCNICO` u otras fases — el parecido estructural está
  señalado en `DISEÑO_CONSULTAS_ORGANISMOS.md §1`, pero hoy esa fase no tiene una entidad
  equivalente a `OrganismoExpediente` que agrupar.
- El poblado real de datos (#464) ni el catálogo DIR3 (#106).

---

## Alternativas descartadas

**Panel de organismos como pantalla/ruta independiente** (el diseño original de #396). Sería
volver a la "maraña de accesos cruzados" que ADR-023 vino a eliminar — detalle y edición en
rutas distintas — y duplicaría, en una pantalla nueva, exactamente lo que el inspector ya sabe
hacer con datos de fase.

**Nivel de dominio nuevo entre Fase y Trámite** (tabla real, no nodo sintético). Innecesario:
la agrupación es enteramente de presentación, derivada de `TramiteOrganismo`, que ya existe.
Tocar el modelo ESFTT de 4 niveles fijos para esto sería el mismo error que ADR-016 evitó con
el bloque de tareas.

**Botón de "crear traslado" en la vista de detalle del organismo** (plan original de #652).
Introduce un mecanismo de creación paralelo a la despensa que ya gobierna el resto del árbol,
sin necesidad: el nodo `organismo` puede tener su propia despensa sin más cambio que reconocer
el ámbito.
