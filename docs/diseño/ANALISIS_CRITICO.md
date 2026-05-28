# Análisis crítico cruzado — Fase 3

> Cruza auditoría UI (fase 1), estudio de usuario (fase 2) e inventario backend (fase 2.5).
> Es el primer documento opinado de la serie. No contiene mockups ni plan de implementación — eso es la fase 4.
> Fecha del corte: 2026-05-28.

---

## 1. Cómo leer este documento

Tres bloques:

- **§2 Hallazgos cruzados** — siete tensiones que emergen al superponer los tres insumos. Cada una se enuncia, se contrasta y se opina. Son la materia prima para las decisiones de fase 4.
- **§3 Referencias** — qué patrones concretos de aplicaciones contemporáneas son aplicables a BDDAT, qué descartar y por qué. No se proponen mockups aquí, solo se identifica el lenguaje visual.
- **§4 Principios de diseño aterrizados** — diez criterios que la fase 4 usará para decidir cuando haya alternativas. Cada uno está respaldado por los hallazgos.

Cierra con **§5 Decisiones pendientes** (preguntas que esta fase **no** contesta) y **§6 Fuera de alcance** (acotación explícita).

---

## 2. Hallazgos cruzados

### 2.1 La cabecera de expediente está sin construir, aunque todo el dato existe

**Lo que dice cada insumo:**
- **Backend**: `seguimiento.estado_solicitud()` calcula estado por pista en 5 categorías y devuelve color, contador y nota de tarea activa. `plazos.obtener_estado_plazo()` produce semáforo con días restantes. `Solicitud.estado`, `Fase.estado`, `Tramite.estado`, `Tarea.estado` son properties listas para consumir. Todo invocable hoy.
- **UI**: 5 templates `tramitacion_bc_*.html` anidados con breadcrumbs. La cabecera muestra número AT, titular y poco más. El "estado" hay que reconstruirlo navegando.
- **Usuario**: "memoria frágil — cuando retomo el expediente tengo que repasar el mismo en el servidor de archivos, releer los documentos, y encuadrar su estado cada vez". La varita mágica nº 2 es exactamente "estado del expediente accesible de un vistazo".
- **Presentación POC**: S08 vende "estado de un vistazo" — pero la implementación lo aplica al **listado**, no a la cabecera dentro del expediente.

**Lectura crítica:** Hay un hueco visible entre lo que el backend sabe decir y lo que la UI muestra. No hace falta inventar nada estructural — hace falta componer una cabecera densa de expediente que llame a los servicios que ya existen. Es la **victoria más asimétrica** del revamping: máximo valor percibido (varita mágica nº 2 del usuario) con esfuerzo backend cero, solo composición UI.

**Implicación para fase 4:** la cabecera consolidada de expediente es candidato a primer entregable visible. Cualquier mockup debe empezar por aquí.

---

### 2.2 El árbol BC profundo es UI sobre-explicada para un dato compacto

**Lo que dice cada insumo:**
- **Backend**: el árbol ESFTT es jerárquico estricto (Expediente → Solicitud → Fase → Trámite → Tarea), pero cada nivel tiene **pocos hijos típicos**: una solicitud tiene 3-6 fases; una fase 2-5 trámites; un trámite 2-4 tareas. La estructura cabe entera en una vista vertical de una pantalla 1080p.
- **UI**: 5 templates anidados con navegación estrictamente descendente. Cada nivel repite enlaces "volver al expediente" y "abrir pool". Sin navegación lateral entre hermanos. JS específicos `v3-breadcrumbs-crear/edicion/acciones`.
- **Usuario**: no se pronunció directamente, pero el patrón de trabajo "lote" implica saltar entre expedientes con frecuencia — la profundidad de navegación intra-expediente es coste neto.
- **Presentación POC**: S05 vende el ESFTT como "mapa del expediente". Promete (S10 columna 2) un **diagrama interactivo del árbol** que sustituiría parcialmente la navegación por breadcrumbs.

**Lectura crítica:** Los 5 niveles son verdad **conceptual** del dominio, pero no son la mejor representación **operativa**. El usuario no necesita "estar en" un nivel — necesita ver el árbol entero y actuar sobre cualquier nodo. La UI BC actual es ceremonia: pide cinco clics para llegar donde un árbol expandible llega en cero.

**El POC React** (issue #320) apunta exactamente a esto, pero con datos mockeados. La decisión de fase 4 es si el árbol completo desplaza a los breadcrumbs como navegación primaria, o si convive.

**Implicación para fase 4:** evaluar reemplazar las 5 vistas BC por **una sola vista de expediente con árbol expandible + panel de detalle del nodo seleccionado**. El backend lo soporta (datos jerárquicos completos, properties de estado por nivel). Decisión: árbol como `<details>` HTML, ReactFlow productivo, o tree view custom.

---

### 2.3 Las cinco capas geológicas no son neutrales

**Lo que dice cada insumo:**
- **UI**: 5 capas conviven en producción — v0 (login), v1 (dashboard), v2 (listados), v3/BC (tramitación), React POC (demo). Más una "capa base" sin sufijo para detalles, formularios, wizard. 13 CSS y 16 JS reflejan la misma estratificación.
- **Backend**: indiferente — los servicios son agnósticos al template que los consume.
- **Usuario**: no percibe las capas directamente, pero sufre la **inconsistencia visual** que generan (citado indirectamente en fase 2 al hablar de "interfaz limpia y organizada").
- **Presentación POC**: S04 vende "imagen corporativa coherente". Las capturas en `presentacion/assets/` muestran principalmente v2 y v3 — v0 y v1 quedan fuera del relato comercial.

**Lectura crítica:** No todas las capas tienen el mismo destino:
- **v0 (login) y v1 (dashboard):** intencionales y aislados — pantallas singulares con su propio CSS. **Pueden quedarse** como están con un refresh visual ligero.
- **v2 (listados):** patrón maduro y reusable (`lista_v2_base.html` + JS scroll infinito + filtros). **Es la base sobre la que construir** — no se toca; se completa migrando lo que falta (#281).
- **v3/BC (tramitación):** es la capa más reciente y la más ceremoniosa. Si §2.2 prospera, **gran parte muere** y es reemplazada.
- **React POC:** está aislado en `demo/`. La decisión (fase 4) es si se promueve a producción.
- **Capa base sin sufijo:** detalles, formularios, wizard. Son los más estables. El revamping les aplica el nuevo sistema visual sin cambios estructurales grandes.

**Implicación para fase 4:** el revamping **no es un rediseño global desde cero**. Es una operación quirúrgica: matar v3/BC, consolidar v2, refrescar v0/v1, decidir React, redefinir sistema visual común que cubra todo.

---

### 2.4 La vista del administrativo: agujero de producto vendido pero no diseñado

**Lo que dice cada insumo:**
- **Backend**: el modelo soporta perfectamente la operativa del administrativo (notificaciones, publicaciones, plazos por documento). Permisos: el rol `ADMINISTRATIVO` existe en `PERMISOS` pero solo aparece como `acceder_expediente` y `ver_todos_proyectos`. No tiene endpoint propio.
- **UI**: **no existe vista específica del administrativo**. Comparte interfaz con tramitador, lo cual es subóptimo dado su flujo distinto.
- **Usuario**: lo identifica como perfil de **4-6 personas** cuyo trabajo cambia más radicalmente con BDDAT que el del tramitador. Hoy "anota notificaciones en carpeta para que el tramitador las copie". Con BDDAT debería actuar directamente en BDDAT y el dato fluir.
- **Presentación POC**: S08 bullet 6 **lo promete públicamente** con 🚧 "pendiente de implementar": "vista propia con todos los expedientes y solicitudes: fechas y plazos de IP, respuestas de titulares y organismos. Pueden acceder directamente a la tarea concreta sin pasar por el expediente completo".

**Lectura crítica:** Esta es la promesa más arriesgada del POC. Si el revamping no la cumple, queda como bullet falso en una presentación oficial. Pero **diseñarla bien requiere entrevistar a los administrativos**, no inferir desde fuera. El estudio de usuario fase 2 fue con un supervisor (Carlos) — no con un administrativo.

La vista del administrativo no es "una versión recortada de la del tramitador". Es **un panel de tareas-pendientes-de-acción-administrativa** que cruza todos los expedientes: "qué hay que notificar hoy", "qué publicaciones tengo pendientes", "qué justificantes acabo de recibir y debo registrar". Su pivote no es el expediente, es la **tarea administrativa transversal**.

**Implicación para fase 4:** antes de diseñar esta vista, **mini-estudio de usuario con un administrativo real** (puede ser 30 minutos en la oficina, no requiere otra ronda formal). El backend ya soporta; el diseño no debe inventarse a ciegas.

---

### 2.5 Búsqueda y filtros: cultura Calc traducible a UI moderna

**Lo que dice cada insumo:**
- **Backend**: hay endpoints API por blueprint (`api_expedientes`, `api_seguimiento`) que aceptan filtros. No hay endpoint de **búsqueda global** unificada.
- **UI**: filtros laterales en listados v2. Sin búsqueda global. La búsqueda por número de expediente requiere ir al listado correcto y filtrar.
- **Usuario**: "El dato principal de búsqueda en Access y Calc es el número de expediente". Filtros típicos: tipo titular (Edistribución/otras/resto), estado pendiente, etiqueta FIN para ocultar cerrados. **"Una sola vista con filtros muy potentes"** > múltiples vistas predefinidas.
- **Presentación POC**: no aborda búsqueda directamente.
- **Issues**: #75 "Búsqueda global de expedientes" está en M5 (post-MVP).

**Lectura crítica:** La búsqueda global está mal-priorizada (post-MVP) frente a lo que el estudio de usuario reveló (operación primaria de localización). Pero el patrón a aplicar es claro: **command palette tipo Linear/GitHub** activable con `Ctrl+K` que acepte:
- Número de expediente directo (`13/2023` → ir al expediente)
- Nombre de proyecto / municipio / titular (búsqueda fuzzy)
- Acciones rápidas ("nuevo expediente", "ir a seguimiento")

Para filtros, la cultura Calc del usuario favorece un modelo de **filtros guardables**: cada usuario construye su vista habitual ("mis solicitudes pendientes de notificar"), la guarda y la reabre. Implementación backend mínima: 1 tabla `filtros_guardados(usuario_id, nombre, query_params JSONB)`. UI: dropdown de "mis filtros".

**Implicación para fase 4:** subir #75 de M5 a M2 con scope acotado (command palette básico). Plantear filtros guardables como patrón transversal de los listados v2.

---

### 2.6 El motor de reglas es un canal de UX sin explotar

**Lo que dice cada insumo:**
- **Backend**: `motor_reglas.evaluar()` devuelve `EvaluacionResult` con `norma_compilada`, `url_norma`, `motivo`, `puede_escapar`. El motor está diseñado para **explicar** sus bloqueos con base legal visible (ADR-007 explícitamente: "la norma debe ser visible para el técnico").
- **UI**: actualmente no hay patrón establecido para mostrar mensajes del motor. Issue #322 ("Mensajes motor siempre via toast") está en M3 sin resolver.
- **Usuario**: "calidad sube y se homogeniza" si el sistema guía. Toleraría perfectamente alertas si son útiles y explicables.
- **Presentación POC**: no aborda el patrón visual del motor.
- **Issues**: #479 "Selector modo global del motor en panel del supervisor" (M3) — admin del motor también pendiente de UI.

**Lectura crítica:** El motor produce **información de UX rica** que la UI no muestra todavía. Cada bloqueo o advertencia trae norma compilada, artículo, URL al BOE/BOJA y motivo editorial. Un patrón estable de "toast con norma + enlace" convertiría cada interrupción del motor en un **micro-momento educativo**, no en una fricción ciega.

Más allá del toast: el motor `auditar()` recorre todas las reglas sin short-circuit. Eso permite un **panel de auditoría del motor** invocable bajo demanda en un expediente ("qué reglas aplican, qué pasan, qué no") — útil para el supervisor y para el técnico curioso.

**Implicación para fase 4:** el revamping debe definir el **patrón visual del motor** (toast con título + descripción + norma compilada + enlace) como componente reutilizable. #322 sube a prioridad media. El "panel del modo motor" (#479) puede esperar.

---

### 2.7 Pool de documentos: integración con explorador del SO ya lista

**Lo que dice cada insumo:**
- **Backend**: `Documento.resolver_url()` despacha por esquema (ruta local, http(s), `bddat://`). Endpoints `pool_abrir_en_carpeta` ya existen. Hay incluso **instalador Windows** del handler URL `bddat://` (`scripts/cliente/`) para que el navegador abra documentos en el visor nativo.
- **UI**: el pool de documentos es una vista accesible desde los 5 templates BC (puerta omnipresente). Botón "abrir carpeta" presente pero poco visible.
- **Usuario**: **"siempre es bueno abrir la carpeta del expediente. De hecho lo tengo en una macro en Calc"**. El atajo a la carpeta del documento consumido es suficiente para verificar notificaciones externas.
- **Issues**: #195 "URI bddat:// para abrir ficheros desde navegador remoto" en M5 — pero el handler ya está construido.

**Lectura crítica:** El backend está **más avanzado que la UI** en este caso. La pieza que falta es ergonomía: que "abrir carpeta del expediente" sea **un atajo persistente en la cabecera**, accesible desde cualquier vista — exactamente como la macro de Calc del usuario, pero universal. Y que el pool de documentos sea **un panel lateral**, no una vista a la que se navega (eliminaría una de las dos puertas duplicadas de §2.2 en auditoría UI).

**Implicación para fase 4:** botón "abrir carpeta" persistente en la cabecera de expediente. Pool como panel lateral colapsable (no vista separada). #195 sale de M5: el trabajo ya está hecho, falta documentarlo y registrar el handler en producción.

---

## 3. Referencias — aplicación concreta a BDDAT

De las apps propuestas en fase 0, no todas son aplicables a un sistema de tramitación administrativa. Filtro lo que aporta de cada una con foco concreto.

### 3.1 Linear — modelo dominante para el flujo de tramitador

**Qué importar:**
- **Command palette (`Ctrl+K`)** como entrada universal: búsqueda + acciones + navegación.
- **Densidad sin claustrofobia**: 14px base, line-height 1.4, padding tabular reducido. Es lo que el usuario llama "interfaz limpia y organizada".
- **Estados con colores semánticos** discretos — no decorativos. Coherente con los semáforos del listado de seguimiento (que el POC ya implementa).
- **Sidebar persistente** con secciones agrupadas. Sustituye los enlaces repetidos de los 5 templates BC por navegación constante.
- **Keyboard-first opcional**: atajos pero no obligatorios. Coherente con el "mix" de perfiles del usuario.

**Qué descartar:**
- El **modelo de "issues" puro** (asignable a una persona, con estados lineales). Los expedientes son árboles, no listas.
- La **estética muy oscura** de Linear: la JdA exige luz, colores corporativos verde y sus derivados.

### 3.2 Stripe Dashboard — densidad de datos + formularios formales

**Qué importar:**
- **Jerarquía tipográfica para datos densos**: títulos secundarios pequeños, valores grandes, etiquetas en gris. Aplica a la cabecera de expediente de §2.1.
- **Formularios con `<fieldset>` agrupados, labels arriba, hints inline**. Sustituye los formularios actuales de wizard y detalles, que son densos pero poco organizados.
- **Tabla con acción contextual al hover** — no checkbox masivo por defecto (que el usuario descartó en fase 2 al decir que no necesita acciones masivas salvo en 2 casos).
- **Modales para acciones puntuales** (edición rápida, cambio de estado).

**Qué descartar:**
- El **dashboard con métricas financieras grandes** — no es lo que BDDAT necesita. Las estadísticas para jefatura (varita mágica nº 1) son tabulares, no de número grande.

### 3.3 GitHub — tablas densas + búsqueda + comentarios

**Qué importar:**
- **Listados muy densos** con badges de estado, contadores y filtros laterales. La capa v2 ya va por aquí; falta refinar.
- **Búsqueda con tokens** (`is:open author:carlos`) — opcional pero coherente con la "cultura de filtros" del usuario.
- **Bitácora como timeline de eventos** (issue activity stream). Aplica directamente al cuaderno de bitácora cuando se instrumente más (§13.1 inventario backend).
- **Patrón `@mention`** si en el futuro hay notificaciones internas (#28).

**Qué descartar:**
- **Markdown en todos los campos** — los escritos administrativos no se redactan en markdown. Sí podría aplicar a notas internas y campos de bitácora.

### 3.4 Sentry — caso análogo: item con muchos eventos y estados

**Por qué encaja:** un "issue" de Sentry es estructuralmente parecido a un expediente de BDDAT: entidad con muchos eventos en el tiempo, estado evolutivo, equipo asignable, breadcrumbs de cómo se llegó al estado actual.

**Qué importar:**
- **Cabecera con resumen ejecutivo permanente** (estado, asignado, hace cuánto, frecuencia) — sustituye exactamente lo que falta en BDDAT (§2.1).
- **Timeline lateral o inferior** de eventos del item. Aplica a la bitácora del expediente.
- **Tags y categorización ligera** — los expedientes ya tienen tipo, podrían añadirse etiquetas libres (con cuidado: el usuario advirtió en fase 2 contra "campos libres genéricos").

**Qué descartar:**
- Stack traces — irrelevante.
- Concepto de "resolved/unresolved" binario — BDDAT tiene estados graduales.

### 3.5 Lo que NO se importa

- **Vercel Dashboard**: minimalismo bonito pero demasiado vacío para una app de tramitación densa.
- **Supabase Studio**: muy técnica, estética desarrollador. La JdA no es ese público.
- **Notion**: orientación a documento personal, no a flujo de trabajo de muchos usuarios.
- **Retool / Internal**: pensadas para "build-it-yourself", no encajan con un producto consolidado.

---

## 4. Principios de diseño aterrizados

Diez criterios de decisión. Cada vez que en fase 4 haya alternativas, se elige la que cumple más principios.

### 4.1 Densidad sí, simplismo no

Tipografía 13-14px base, line-height 1.4, padding reducido. La condescendencia es enemiga — el usuario lo dijo: *"no quiero que hagas un interfaz para tontos, quiero que la facilidad y curva de aprendizaje rápido sea gracias a la limpieza y organización del interfaz"*. Origen: §3.1, estudio usuario 6.4.

### 4.2 El sistema empuja con semáforos, no espera disciplina

Estados visibles, alertas de plazos vencidos, indicadores de "esto te toca a ti". La memoria del usuario es frágil — la UI debe ser **memoria externa fiable**. Origen: §2.1, estudio usuario 5.1.

### 4.3 Una vista única con filtros potentes y guardables

No múltiples vistas predefinidas. El usuario filtra desde Calc, y eso es la cultura local. El revamping refuerza el patrón, no lo sustituye. Origen: §2.5, estudio usuario 4.3.

### 4.4 Búsqueda global por número de expediente como operación primaria

`Ctrl+K` o equivalente, siempre disponible, en cualquier vista. Acepta número directo, busca fuzzy en proyecto/municipio/titular. Sustituye la práctica actual de "ir al listado y filtrar". Origen: §2.5, estudio usuario 4.4.

### 4.5 Estructura discreta e indexable, no campos libres genéricos

Donde haga falta narrativa, bitácora datada con autor. Donde se pueda estructurar, se estructura. El usuario fue explícito: *"campos libres que no se rellenan, que no se indexan, que no sirven"*. Origen: estudio usuario 5.3.

### 4.6 Convivencia con otras apps, no kiosko

BDDAT no es la única ventana del tramitador. Botón "abrir carpeta" omnipresente. El handler `bddat://` para integración inversa (navegador → explorador). Tamaños de ventana flexibles (1280-1920). Origen: §2.7, estudio usuario 2.5.

### 4.7 Identidad JdA mantenida, lenguaje aplicado modernizado

Colores corporativos, tipografía y componentes JA siguen. Lo que cambia es la **densidad, la organización tipográfica y la consistencia entre capas**. S04 del POC es contrato vinculante. Origen: §3.1, presentación POC S04.

### 4.8 Mismo flujo DyT/Renovables, distinta velocidad — no bifurcar UI

El estudio de usuario fue explícito: mismo flujo, distinto ritmo. La UI no se bifurca por subgrupo. Lo que sí varía: el perfil ADMINISTRATIVO tiene su propia vista (§2.4), distinto del TRAMITADOR. Origen: estudio usuario 4.8.

### 4.9 El motor explica lo que prohíbe

Cada bloqueo o advertencia muestra norma compilada + enlace al BOE/BOJA + motivo editorial. La UI propaga la riqueza de `EvaluacionResult` sin pérdida. Origen: §2.6, ADR-007, ADR-012.

### 4.10 El revamping no rehace lo que el backend ya sabe — compone

La cabecera de expediente, los semáforos de plazo, el listado por pistas: el backend ya los calcula. El trabajo de la fase 4 es **componer en UI lo que el motor produce**. Resistir la tentación de añadir lógica de negocio en plantillas. Origen: §2.1, §2.6.

---

## 5. Decisiones pendientes — preguntas que esta fase NO contesta

La fase 3 identifica las preguntas críticas y deja que la fase 4 las responda. Listado priorizado:

### 5.1 Stack JS — ¿Jinja consolidado o híbrido Jinja+React?

**Contexto:** `react-diagramas/` es un POC funcional con `@xyflow/react` integrado vía bundle IIFE. Issue #320 está listo para promover el diagrama a producción.

**Opciones:**
- **A. Jinja puro + JS vanilla** (estado actual mejorado). Sin React. El diagrama se hace con SVG/Canvas vanilla o se descarta como POC.
- **B. Híbrido Jinja + React por componente.** Jinja para layout y formularios; React para componentes interactivos (árbol de expediente, command palette, vistas complejas).
- **C. SPA React completa.** Backend solo expone APIs JSON; UI íntegra en React. Cambio de paradigma profundo.

**Recomendación previa (no decisión):** B. La densidad de interacción de algunas vistas (árbol, command palette, filtros guardables) justifica React; el resto (formularios, listados, detalles) está bien en Jinja y reutiliza el stack actual. C es desproporcionado para el equipo y la escala. A renuncia a una pieza valiosa.

### 5.2 Árbol del expediente — ¿reemplaza a los breadcrumbs o convive?

**Contexto:** §2.2. Los 5 templates BC son la capa más ceremoniosa. El árbol expandible cubre el mismo dato en menos clics.

**Opciones:**
- **A. Reemplazo total:** una sola vista de expediente con árbol + panel de detalle del nodo seleccionado.
- **B. Coexistencia:** árbol como vista alternativa, breadcrumbs como ruta de actuación.
- **C. Statu quo + mejoras menores en BC.**

**Recomendación previa:** A. La coexistencia mantiene mantenimiento doble.

### 5.3 Pool de documentos — ¿panel lateral o vista propia?

**Contexto:** §2.7. Hoy es vista omnipresente; podría ser panel lateral colapsable.

**Opciones:**
- **A. Panel lateral persistente** colapsable, accesible desde cualquier subvista del expediente.
- **B. Mantener como vista pero accesible con `[` o atajo.**

**Recomendación previa:** A. Elimina las "puertas duplicadas" detectadas en auditoría UI.

### 5.4 Sidebar vs. navbar superior

**Contexto:** Hoy hay navbar superior. Las apps de referencia (Linear, GitHub, Stripe) usan sidebar persistente.

**Opciones:**
- **A. Sidebar izquierda persistente** colapsable, navbar superior reducida a usuario + búsqueda + acciones globales.
- **B. Sidebar contextual por área** (la sidebar cambia según la sección).
- **C. Mantener navbar superior con mejor organización.**

**Recomendación previa:** A con elementos de B. Una sidebar fija para áreas principales (Expedientes / Entidades / Plantillas / Admin) y secciones contextuales dentro de un expediente.

### 5.5 Sistema de diseño — ¿qué bibliotecas?

**Contexto:** Hoy es Bootstrap 5 + CDN JdA. Apps modernas usan Tailwind + Headless UI / Radix, o sistemas custom.

**Opciones:**
- **A. Mantener Bootstrap + JdA + custom CSS** para ajustes finos.
- **B. Migrar a Tailwind manteniendo paleta JdA** (las clases utilitarias permiten densidad sin sobrecarga).
- **C. Híbrido:** Bootstrap para layouts, custom CSS para componentes finos.

**Recomendación previa:** A o C. Migrar a Tailwind es trabajo grande sin victoria visible al usuario. Bootstrap 5 con custom CSS dirigido cubre el revamping.

### 5.6 Vista del administrativo — ¿qué patrón?

**Contexto:** §2.4. Promesa pública sin diseño. Requiere mini-estudio con un administrativo real.

**Pregunta a contestar antes de fase 4:** ¿se hace ese mini-estudio antes de los mockups, o se diseña una primera versión por inferencia y se itera con feedback real?

**Recomendación previa:** mini-estudio antes (30 minutos, baja inversión).

### 5.7 Tests UI — ¿se introducen?

**Contexto:** El backend tiene 50 tests pytest. La UI no tiene tests automatizados.

**Opciones:**
- **A. Mantener UI sin tests automatizados** — aceptar riesgo, testing manual con Playwright MCP en sesiones de desarrollo.
- **B. Introducir tests de integración mínimos** (smoke tests de cada vista, login, generación de escrito).
- **C. Tests E2E con Playwright** del flujo crítico del tramitador.

**Recomendación previa:** B mínimo. C como ambición a 6 meses.

---

## 6. Fuera de alcance del revamping

Por claridad, lo que **no** intenta el revamping:

- **Migración legacy** (#175, #105): el revamping no rediseña la importación desde Access. Se respeta el flag `heredado` y se aplican las reglas visuales de "expediente heredado" (banner, acciones reducidas), pero el wizard de importación es trabajo aparte.
- **ENS, HTTPS, infraestructura producción** (#176, #177, #178): pre-producción técnica, no UI.
- **Integración con BandeJA / Notifica / PortaFirmas:** decisión fuera del proyecto (requiere ADA). Se respeta el principio "BDDAT no es kiosko" — enlaces hacia esas herramientas pero no absorción.
- **PostGIS / cartografía** (#27): post-MVP, fuera del alcance del revamping.
- **Sistema de ayuda / manual de usuario** (#228): se valorará si el revamping reduce su necesidad. No es entregable de la fase 4.
- **Migración de Bootstrap a Tailwind** u otro framework: ver §5.5.

---

## 7. Cierre y enlace a fase 4

Esta fase deja sobre la mesa:

- **7 hallazgos cruzados** con lectura crítica.
- **5 referencias filtradas** con qué importar y qué descartar.
- **10 principios de diseño** como criterio de decisión.
- **7 decisiones técnicas pendientes** con recomendación previa pero sin cerrar.
- **6 áreas explícitamente fuera de alcance**.

La fase 4 produce:

1. **Decisiones cerradas** sobre §5 (con o sin mini-estudio del administrativo).
2. **Sistema de diseño** consolidado: paleta, tipografía, spacing, componentes base.
3. **Mockups o wireframes** de las pantallas piloto (candidatas: cabecera de expediente §2.1, listado con command palette §2.5, vista de árbol §2.2, vista del administrativo §2.4).
4. **Plan de implementación incremental** trozado en issues nuevos o rescatados del backlog M2/M3 actual.

Antes de arrancar fase 4 se recomienda:
- Validar los principios §4 con el usuario (Carlos) — son la base de todo lo que viene.
- Decidir si se hace el mini-estudio con un administrativo (§5.6).
- Acordar el orden de los entregables visibles (la cabecera de expediente es candidato natural a ser el primero).
