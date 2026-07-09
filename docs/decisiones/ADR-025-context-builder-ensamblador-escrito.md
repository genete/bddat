# ADR-025 — Context Builder como ensamblador del escrito (no del trámite)

**Estado:** Adoptada
**Fecha:** 2026-06-16
**Issue:** #553 (fase de diseño previa)
**Relacionado con:** ADR-007 (#387) — eliminación de whitelists ESFT. Fuentes de verdad afectadas: `docs/referencia/DISEÑO_GENERACION_ESCRITOS.md` y `docs/referencia/GUIA_CONTEXT_BUILDERS.md`.

---

## Contexto

La generación de escritos administrativos (`generar_escrito()`, ADR-009/010/011) compone el contexto de una plantilla `.docx` a partir de cuatro fuentes:

1. **Capa 1** — `ContextoBaseExpediente`: campos base del expediente, siempre presentes.
2. **Capa 2** — un **Context Builder (CB)** Python opcional, declarado por la plantilla en su campo `contexto_clase`.
3. **Consultas nombradas** — SQL parametrizado por `:expediente_id`; se ejecutan **todas** las activas y las no referenciadas las ignora Jinja2.
4. **Fragmentos `.docx`** — subdocumentos insertables vía `{{r nombre}}`.

La `GUIA_CONTEXT_BUILDERS.md` describía el CB como "el contexto del **trámite**": la tabla de CBs los lista por trámite y la intuición era una correspondencia 1:1 CB↔trámite. Al abordar #553 (filtrar los tokens del modal por el encuadramiento de la plantilla) se hizo necesario fijar **qué determina realmente los tokens** de una plantilla, y al hacerlo se detectaron tres hechos que contradicen ese modelo mental:

### 1. La ligadura CB↔trámite es circunstancial, no estructural

ADR-007 eliminó las whitelists fase↔trámite: una misma `tipo_tramite` puede aparecer en distintas fases (p. ej. `REQUERIMIENTO_SUBSANACION` se da tanto al subsanar la solicitud inicial como documentación técnica en instrucción). El CB se asocia, como mucho, al **tipo de trámite** (vía su lógica), nunca al ESFT completo. Y como `contexto_clase` es solo un string, **nada impide que dos plantillas distintas compartan el mismo CB** (escrito y su reiteración; o "anuncio al promotor" y "anuncio al diario", mismo trámite, escritos distintos). La relación real es **plantilla → usa → CB**, de cardinalidad N:1.

### 2. Los FKs ESFT de la plantilla no intervienen en la generación

Leído `generar_escrito()`, ninguna de las cuatro fuentes depende de los cuatro FKs ESFT de la plantilla. Capa 1 es universal; las consultas se ejecutan todas (vacío-seguras); el CB se carga **solo si `contexto_clase` está fijado**; los fragmentos se resuelven por escaneo de `{{r}}`. Los FKs ESFT solo gobiernan **dónde se ofrece** la plantilla en ELABORAR (match NULL-comodín en `api_escritos.py`). Es decir: **lo único que varía el contexto contextual de una plantilla es su `contexto_clase`**, no su encuadramiento ESFT.

### 3. El CB ya recorre todo el expediente; su ancla es la tarea, no el trámite

Los CBs existentes no se limitan a "datos locales del trámite": `ContextoAnalisisAlegaciones` recorre `solicitud.fases` agregando todos los `RECEPCION_ALEGACION`; `ContextoConsultaTrasladoOrganismo` cruza todos los `TramiteOrganismo` del organismo. Todos arrancan en `self._tarea` (la tarea de ELABORAR) y navegan desde ahí. El CB es un **navegador anclado en la tarea**, con licencia para recorrer el expediente entero.

De ahí surgió la tentación de hacer `contexto_clase` **plural** (una plantilla compone varios CBs), motivada por escritos de síntesis como la **resolución**, que necesita conocimiento de casi todo el expediente.

---

## Decisión

### 1. El CB es el ensamblador de contexto del **escrito**, no del trámite

Se reencuadra conceptualmente: un Context Builder es *el ensamblador de contexto de una plantilla (escrito), anclado en la tarea de ELABORAR, con licencia para recorrer todo el expediente*. La correspondencia con un trámite es **circunstancial** (la mayoría de escritos son 1:1 con su trámite), no una propiedad del modelo.

### 2. `contexto_clase` permanece **singular**

Una plantilla declara **un** CB. La relación plantilla→CB es N:1 (varias plantillas pueden compartir clase). No se introduce composición data-driven de múltiples CBs (ver Alternativa A).

### 3. Los tokens contextuales los determina `contexto_clase`, no el ESFT

El conjunto de tokens válidos de una plantilla = Capa 1 (universal) + consultas nombradas (universales, vacío-seguras) + fragmentos (universales) + **los tokens del CB declarado en `contexto_clase`**. Los FKs ESFT **no filtran tokens**; siguen gobernando solo la oferta en ELABORAR. Filtrar por ESFT sería además *menos* preciso que por `contexto_clase`: dos plantillas del mismo trámite con CB distinto deben ofrecer tokens distintos.

### 4. Taxonomía de anclaje — por qué no se componen CBs

Los CBs se anclan de dos formas, y esto es lo que hace insegura la composición arbitraria:

| Anclaje | Ejemplos | Navegación | ¿Componible bajo otra tarea? |
|---|---|---|---|
| **Auto-trámite** | `ConsultaTrasladoOrganismo`, `ConsultaSeparata`, `ConsultaTrasladoTitular`, `NotificacionOrganismo` | usan `tarea.tramite_id` → datos de **este** trámite | **No** — bajo otra tarea buscan "su" trámite y devuelven vacío **en silencio** |
| **Solicitud/fase-scoped** | `AnalisisAlegaciones`, `Resolucion`, `InformacionPublica`, `Subsanacion` (reclasificado en #440) | usan la tarea solo para alcanzar `solicitud`/`fase` y **agregar** | Sí, dentro de la misma solicitud |

**Nota (#440, 2026-07-09):** `Subsanacion` se reclasificó de Auto-trámite a
Solicitud/fase-scoped. Hasta #440 leía `tarea.requerimientos` (su propio
trámite) — encajaba en Auto-trámite. El fix de #440 corrige esa lectura: el
shuttle de `requerimientos_tarea` es solo borrador de trabajo (#442), no el
documento de salida. Ahora navega a `tarea.tramite.fase` y busca el
`Diagnostico` de la tarea ANALIZAR del trámite *anterior* dentro de la misma
fase — cruza de trámite, característico de Solicitud/fase-scoped.

Un CB codifica un "yo" (su trámite) en su navegación; ejecutarlo bajo la tarea de otro escrito produce datos vacíos/incorrectos sin error. La composición data-driven sería segura solo para la clase *scoped* — exactamente lo que ya cubren las consultas nombradas.

### 5. Reutilización: dos mecanismos por debajo del CB

Cuando un escrito de síntesis (p. ej. la resolución) necesita datos transversales, **no** se listan varios CBs: el CB del escrito **compone explícitamente**, correctamente anclado, tirando de:

- **Consultas nombradas** (SQL, datos tabulares, ancla `:expediente_id`) — la capa agregadora declarativa.
- **Funciones Python compartidas + `as_contexto_cb()` de los modelos** — para lógica computada/escalar (p. ej. `_doc_esperar_plazo`, `organismo.as_contexto_cb()`).

**Regla extender-vs-crear** (responde a la pregunta operativa del diseño):

- Si falta un dato **para el mismo escrito** → se **extiende** el CB existente (preferentemente delegando en un `as_contexto_cb()` del modelo o un helper).
- Si el dato es un **sub-contexto reutilizable** por otros escritos → se **extrae una función/método compartido** y ambos CBs lo llaman.
- Se crea un **CB nuevo** solo cuando hay un **escrito nuevo con anclaje propio**. La unidad de "CB nuevo" es "escrito nuevo", no "campo nuevo".

---

## Consecuencias

- **`DISEÑO_GENERACION_ESCRITOS.md`** y **`GUIA_CONTEXT_BUILDERS.md`** se actualizan para reflejar el reencuadre (CB = ensamblador del escrito; relación N:1; reutilización por consultas + funciones compartidas; regla extender-vs-crear). Este ADR es la justificación de esos cambios.
- **#553 (filtrado de tokens):** cada CB declarará explícitamente sus tokens (manifiesto estático en la clase), y el modal "Tokens disponibles" pasará a ser **contextual por `contexto_clase`** (re-fetch al cambiarlo). Capa 1, consultas y fragmentos quedan universales. El mecanismo no cambia si en el futuro se reconsiderara la pluralidad: mostraría la unión.
- **#552 (limpieza del alta):** se confirma que el encuadramiento ESFT se elige con selects planos (no validable en abstracto, ADR-007) y que no filtra tokens. La asimetría queda documentada: el ESFT es el ancla de oferta; los tokens dependen de `contexto_clase`.
- **Resolución:** su CB (`ContextoResolucion`) hoy solo aporta `sentido_acto` + bloques redaccionales. Enriquecerlo para que sintetice alegaciones/organismos/informes es trabajo de **enriquecer ese CB con agregadores compartidos**, no de convertirlo en lista de CBs. Queda como trabajo futuro, fuera de #552/#553.
- No hay cambio de esquema de BD: `contexto_clase` sigue siendo un `TEXT` nullable.

---

## Alternativas descartadas

### A. `contexto_clase` plural (composición data-driven de varios CBs)

Hacer de `contexto_clase` una lista y componer con `ctx.update` en bucle. Descartada por:

1. **Anclaje (Decisión §4):** solo es segura para CBs *scoped*; componer un CB auto-trámite bajo otra tarea devuelve vacío en silencio — el peor tipo de error.
2. **Colisión silenciosa:** `ctx.update` es "último gana"; dos CBs con la misma clave se pisan según el orden. Los prefijos de dominio (`organismo_*`, `resolucion_*`) lo mitigan pero no lo garantizan.
3. **Reinventa lo existente:** la capa componible y vacío-segura ya existe (consultas nombradas para tablas; funciones compartidas para escalares).
4. **No es necesidad del supervisor:** los CBs son código (técnico + Claude). La reutilización es de tiempo de desarrollo, donde la composición de funciones gana a la data-driven en todos los ejes salvo "configurable sin tocar código", que aquí no es requisito.

### B. Declarar aplicabilidad ESFT por token (FKs en consultas, registro ESFT por CB)

El modelo que el cuerpo de #553 asumía inicialmente. Descartado: redundante con `contexto_clase` (que ya fija el CB), exige migración y UI de gestión para un catálogo mínimo (1 consulta), y es menos preciso que anclar a `contexto_clase`.
