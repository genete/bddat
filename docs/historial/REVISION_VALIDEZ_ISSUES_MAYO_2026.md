# Revisión de validez de issues — mayo 2026

> **Tipo:** Snapshot de auditoría arquitectónica. Congelado en la fecha de creación.
> **Fecha:** 2026-05-16
> **Alcance:** 31 issues abiertos no puramente de UI (milestones M2, M3, M4 parcial, sin-milestone).
> **Método:** Lectura del cuerpo completo de cada issue, cruzada con código en `develop`,
> las ADR-001 a ADR-007 y el historial de commits desde el 11/05/2026.
> **Documento hermano:** `ANALISIS_ESTADO_MAYO_2026.md` (estado por área).

---

## 1. Criterios de clasificación

| Situación | Significado |
|---|---|
| **Válido** | Alcance real, viable y alineado con las decisiones recientes. Implementar tal cual. |
| **Válido — reescribir cuerpo** | La necesidad es real, pero el texto del issue tiene referencias muertas o premisas desactualizadas. Reescribir antes de planificar. |
| **Requiere rediseño** | Una decisión posterior (ADR) invalida el enfoque del issue. Hay que rehacer el diseño. |
| **Parcialmente implementado** | Parte del alcance ya está cubierto por trabajo posterior. Recortar el issue a lo que falta. |
| **Para cerrar** | Superado por otro issue/ADR, o no es trabajo de desarrollo. Cerrar. |
| **Estudiar** | La premisa es dudosa o solapa con otro issue. Verificar/decidir antes de planificar. |

---

## 2. Tabla de dictamen

| # | Descripción corta | Milestone | Situación |
|---|---|---|---|
| #300 | Dirección de notificación del titular mal resuelta en escritos | M2 | **Válido** |
| #297 | Logotipo de la Junta: vinculado → incrustado | M2 | **Válido — reescribir cuerpo** |
| #318 | Tipos combinados: regla del tipo más restrictivo en metadatos/motor | M2 | **Para cerrar** |
| #332 | CI: ejecutar tests en GitHub Actions | M2 | **Válido — reescribir cuerpo** |
| #181 | Inspección automática de documentos / preclasificación | M2 | **Estudiar** |
| #362 | ESPERAR_PLAZO: certificado de plazo cumplido como doc. producido | M3 | **Válido** (→ ADR) |
| #364 | PUBLICAR cubre BOE/BOP/BOJA/prensa; NOTIFICAR solo destinatario | M3 | **Para cerrar** |
| #365 | Extender documentos.url a URI `bddat://` para decisiones ANALIZAR | M3 | **Válido — reconvertir a implementación** |
| #366 | Eliminar trámite AUDIENCIA de COMPATIBILIDAD_AMBIENTAL | M3 | **Válido** |
| #380 | Decidir destino de tabla `documentos_tarea` tras quitar INCORPORAR | M3 | **Válido — decisión bloqueante** |
| #247 | Fase de consultas a organismos y análisis técnico | M3 | **Parcialmente implementado** |
| #248 | Fase ANÁLISIS_SOLICITUD, checklist documental, requerimientos | M3 | **Requiere rediseño** |
| #374 | Tabla de interesados y trámite REGISTRO_INTERESADOS | sin-ms | **Válido** (asignar M3) |
| #377 | Seed de tipos_documentos del catálogo ESFTT (Alembic) | M3 | **Válido** |
| #378 | Seed de tipos_documentos_resultados_validos | M3 | **Válido** |
| #276 | Poblar tipos_solicitudes_compatibles | M3 | **Requiere rediseño** |
| #323 | Motor: modo global INACTIVO/SOLO_ADVERTIR/BLOQUEAR | M3 | **Válido** |
| #357 | ESPERAR_PLAZO: mecanismo de cierre formal | M3 | **Para cerrar** |
| #324 | Motor: mecanismo de escape con justificación y bitácora | M3 | **Válido — reescribir cuerpo** |
| #192 | Requisitos documentales por procedimiento | M3 | **Requiere rediseño** |
| #174 | Permisos granulares por acción y expediente | M3 | **Requiere rediseño** |
| #376 | Generalizar UI multi-documento a más tipos de tarea | sin-ms | **Válido — bloqueado por #380** |
| #304 | Script de detección del tipo de solicitud por PDF | M3 | **Válido** |
| #305 | Script de detección del tipo de expediente por PDF | M3 | **Válido** |
| #306 | Helper de cálculo de tasa y extracción de presupuesto | M3 | **Válido** |
| #294 | Estrategia: pivot normativa → motor en modo suave | M3 | **Estudiar** (mayormente ejecutado) |
| #283 | Ampliar ESTRUCTURA_FTT a todos los tipos de expediente | M3 | **Válido — reescribir cuerpo** |
| #153 | [DRAFT] Consultas en separatas — tabla entidades_consultadas | M3 | **Para cerrar** |
| #106 | Listado de códigos DIR3 | M3 | **Válido** (revisar milestone) |

**Resumen:** 11 válidos · 4 reescribir cuerpo · 4 requieren rediseño · 1 parcialmente implementado ·
4 para cerrar · 2 estudiar · #365 reconvertir a implementación · #380 decisión bloqueante ·
#376 bloqueado por #380.

---

## 3. Dictamen detallado

### 3.1 Para cerrar

**#318 — Tipos combinados: regla del tipo más restrictivo.**
No es un issue de implementación: es una nota de diseño. El comportamiento en tiempo de
ejecución (evaluar una vez por tipo simple, primer BLOQUEAR gana) ya está implementado en
`evaluar_multi()` de `app/services/assembler.py` y cubierto por tests (#328). El issue solo
recuerda que, al poblar `metadatos_fechas` y `reglas_motor`, las reglas deben definirse sobre
tipos simples (`AAP`, no `AAP+AAC`). **Acción:** trasladar esa advertencia a la guía del motor
o al cuerpo de #377/#378 como checklist, y cerrar #318.

**#153 — [DRAFT] entidades_consultadas.**
Superado por completo. La tabla `entidades_consultadas` que proponía es exactamente la tabla
`organismos_expediente`, ya creada e implementada en #391 (`OrganismoExpediente`, CB
`ContextoConsultaSeparata`). El trámite `SEPARATAS` que menciona se renombró a
`CONSULTA_SEPARATA` (visible en `ESTRUCTURA_FTT.json`). El propio issue admite que "la regla
TRAMITE — CREAR SEPARATAS ha sido eliminada". **Acción:** cerrar como superado por #391/#247.

**#357 — Cierre de ESPERAR_PLAZO.**
El issue parte de una premisa hoy falsa: que ESPERAR_PLAZO *"no produce ningún documento y por
tanto nunca puede cerrarse"*. Tras ADR-004 y el diseño de #362, **toda tarea produce documento**.
ESPERAR_PLAZO cierra de dos formas: con el documento recibido como `documento_producido_id`
(Caso A — había una recepción esperada), o, si vence sin respuesta, con el `CERT_PLAZO_CUMPLIDO`
emitido como documento `bddat://` (Caso B). En ningún caso queda "huérfana de la invariante
documental". El único residuo real es de limpieza: el campo `"salida": "Ninguno"` de
ESPERAR_PLAZO en `ESTRUCTURA_FTT.json` está desactualizado —su propia nota ya cita ADR-004— y
existe un parche en `Tramite.finalizado` que excluye la tarea del cálculo. Ambas correcciones
son parte natural de la implementación de #362. **Acción:** cerrar #357; absorber las dos
correcciones de limpieza en el alcance de #362.

**#364 — PUBLICAR vs NOTIFICAR.**
La tarea atómica `PUBLICAR` **ya no existe**: fue eliminada en #371. `ESTRUCTURA_FTT.json` v6.0
lo confirma de forma explícita en dos notas (*"PUBLICAR eliminado → patrón C (#371)"*) y su
catálogo `TAREAS_ATOMICAS` tiene hoy exactamente cuatro tareas: ANALIZAR, ELABORAR, NOTIFICAR,
ESPERAR_PLAZO. #364 propone *"redefinir la semántica de las tareas atómicas NOTIFICAR y
PUBLICAR"* y mover los trámites `ANUNCIO_BOE/BOP/PRENSA` a PUBLICAR — pero esos trámites ya
están reestructurados al patrón C por #371. El cambio estructural que pedía #364 está hecho.
La distinción jurídica que plantea (notificación a destinatario identificado vs. publicación a
destinatarios difusos) sigue siendo correcta, pero hoy se expresa en los TIPOS de trámite y de
documento, no en las tareas atómicas. **Acción:** cerrar #364 como superado por #371; si queda
algún matiz jurídico de denominación sin cubrir, abrir un issue acotado.

### 3.2 Requieren rediseño

**#192 — Requisitos documentales por procedimiento.**
ADR-007 lo dice de forma explícita en su sección "Consecuencias": *"#192 requiere rediseño:
usa FINALIZAR como punto de anclaje y propone tabla `procedimientos` que solapa con tipos
existentes."* El verbo FINALIZAR ya no existe en el motor (ADR-007 lo eliminó). La tabla
`procedimientos` que propone duplica el catálogo de tipos de solicitud. **Acción:** rediseñar
sobre el modelo actual — anclar la verificación al evento `CREAR` de la fase siguiente, y usar
los tipos ESFTT existentes en lugar de una tabla `procedimientos` nueva.

**#248 — Fase ANÁLISIS_SOLICITUD.**
El issue es un macro-issue que mezcla 6 bloques, varios ya resueltos o invalidados:
- Referencia rutas `docs/fuentesIA/` que **ya no existen** (movidas a `docs/referencia/`).
- Propone "crear tabla `documentos_tarea`" — **ya existe** (modelo `DocumentoTarea`).
- Propone tarea `INCORPORAR` multi-documento con `fecha_fin` — `INCORPORAR` fue **eliminada**
  (ADR-004) y las fechas explícitas de tarea no existen (ADR-002).
- Propone tabla `documentos_analizar` — se materializó como tabla `diagnosticos` (#392, ADR-005).
- El trámite `ANÁLISIS_DOCUMENTAL` ya tiene su CB (`ContextoAnalisisDocumental`, #392).
Lo que sigue vivo: el catálogo de requerimientos (`catalogo_requerimientos`/`requerimientos_tarea`),
el checklist documental y el campo `siglas_escritos` en `Usuario`. **Acción:** cerrar #248 y
trocearlo en issues nuevos pequeños solo para lo no implementado.

**#276 — Poblar tipos_solicitudes_compatibles.**
La tabla `tipos_solicitudes_compatibles` **ya no existe**. La creó la migración `5c4f7a4bf22d`
y la **eliminó** la migración `e40ce8475305` (Paso 6.5, #301), con el comentario explícito en
su cabecera: *"DROP TABLE tipos_solicitudes_compatibles (vacía, reemplazada por separador + en
siglas)"*. No hay modelo en `app/models` ni tabla en BD (verificado). El issue —que pide
"poblar la tabla"— carece de objeto: el mecanismo que referencia está muerto. La necesidad de
fondo sigue siendo real (declarar qué tipos de solicitud pueden coexistir activos en un mismo
expediente), pero el mecanismo correcto hoy es una **regla CREAR del motor**: el motor ya
recibe el sujeto de la acción como variable, de modo que la incompatibilidad se expresa como
regla con referencia normativa visible al técnico, no como tabla whitelist —coherente además
con la dirección de ADR-007. **Acción:** cerrar #276 y reabrir su necesidad como regla(s) del
motor dentro del trabajo de carga de reglas (#294).

**#174 — Permisos granulares.**
Reclasificado de "válido" a rediseño por una **decisión de negocio**, no por código: la
jefatura, en la presentación de la herramienta, indicó que la tramitación de un expediente
**no** debe restringirse de forma dura al usuario asignado. Cualquier persona puede tramitar
cualquier expediente; es el **cuaderno de bitácora** el que deja constancia de que alguien
ajeno a la asignación ha actuado. #174 propone lo contrario —"restricción por responsable
asignado" como permiso duro—. El enfoque debe invertirse: de control de acceso restrictivo a
**registro en bitácora** de la actuación fuera de asignación. Conecta con #1 (cuaderno de
bitácora) y con la `bitacora_escapes` de #324. **Acción:** rediseñar #174 — el modelo es
permiso blando con traza en bitácora, no permiso duro por expediente.

### 3.3 Parcialmente implementado

**#247 — Fase de consultas a organismos.**
Núcleo ya entregado por #391: tabla `organismos_expediente`, modelo `OrganismoExpediente`,
CB `ContextoConsultaSeparata`. El renombrado `ANALISIS → ANALIZAR` está hecho (visible en
`ESTRUCTURA_FTT.json`). El issue referencia rutas muertas `docs/fuentesIA/` y la tarea
`INCORPORAR` eliminada por ADR-004. Sigue pendiente: tipos de trámite `CONSULTA_TRASLADO_TITULAR`
y `CONSULTA_TRASLADO_ORGANISMO`, y las reglas de cierre de las fases CONSULTAS y ANALISIS_TECNICO.
**Acción:** reescribir el cuerpo eliminando lo hecho y las referencias muertas; recortar a las
reglas de cierre de fase y los trámites de traslado.

### 3.4 Válido — reescribir cuerpo / reconvertir

**#297 — Logotipo incrustado.**
La necesidad es real y clara (los escritos oficiales deben llevar el logo incrustado, no
enlazado). Pero el cuerpo del issue es un volcado de una conversación sobre LibreOffice Writer,
sin especificación accionable. **Acción:** sustituir el cuerpo por una spec breve: el servicio
generador (`generador_escritos.py`) debe incrustar el logo en el `.docx` producido.

**#332 — CI en GitHub Actions.**
La tarea raíz es válida. Pero referencia `tests/test_290_documentos_tarea.py` y endpoints
`/api/bc/tarea/*/incorporar/*` que #376 va a renombrar (INCORPORAR eliminado). **Acción:**
actualizar las referencias de ficheros/endpoints cuando se planifique, o redactar el workflow
de forma agnóstica al nombre de los tests.

**#365 — URI `bddat://`.**
El **diseño ya está decidido**: es la ADR-006 (fechada 11/05). El issue se etiquetó `[DISEÑO]`
pero la parte de diseño está cerrada. La implementación **no** está hecha: no existe
`resolver_url()` ni validación de esquema en el modelo `Documento` (verificado por grep).
**Acción:** reconvertir #365 de `[DISEÑO]` a `[MODELO]` — implementación de ADR-006: helper
`resolver_url()`, validación de los tres esquemas, tabla(s) destino.

**#324 — Mecanismo de escape.**
Diseño sólido, pero la tabla `bitacora_escapes` define `accion` como `CREAR | INICIAR |
FINALIZAR | BORRAR`. ADR-007 eliminó `INICIAR` y `FINALIZAR`: el enum debe quedar en
`CREAR | BORRAR`. Además, ADR-007 §Consecuencias ya describe una UX de escape (checkbox
"mostrar opciones no permitidas" en los selectores ESFTT) que conviene reconciliar con el
modal de justificación de #324. **Acción:** reescribir el cuerpo alineándolo con ADR-007.

**#283 — Ampliar ESTRUCTURA_FTT.**
El objetivo (cubrir todos los tipos de expediente) sigue válido. Pero el cuerpo referencia
`docs/ESTRUCTURA_FTT.md` (ahora en `docs/referencia/`) y lista las tareas atómicas como
`ANALIZAR, REDACTAR, FIRMAR, NOTIFICAR, PUBLICAR, ESPERAR_PLAZO, INCORPORAR`. Catálogo real
hoy (`ESTRUCTURA_FTT.json` v6.0): **cuatro tareas** — `ANALIZAR, ELABORAR, NOTIFICAR,
ESPERAR_PLAZO`. Las diferencias respecto al issue:
- `REDACTAR` + `FIRMAR` → fusionados en `ELABORAR` (ADR-003).
- `INCORPORAR` → eliminada (ADR-004); la recepción es `documento_producido` de ESPERAR_PLAZO.
- `PUBLICAR` → eliminada (#371) al detectarse que no es una tarea atómica sino una
  super-tarea representable por la secuencia `ELABORAR → NOTIFICAR → ESPERAR_PLAZO`.

**Acción:** actualizar la premisa al catálogo de cuatro tareas antes de planificar el issue.

### 3.5 Estudiar

**#181 — Inspección automática de documentos.**
Solapa fuertemente con #304 (detección de tipo de solicitud por PDF) y #305 (tipo de
expediente por PDF): los tres son análisis heurístico de PDFs con validación humana. #181
añade detección de patrón `AT-nnnnn` y detección de firma. **Acción:** decidir si #181 se
fusiona con #304/#305 como una familia única "análisis heurístico de PDF", o se mantiene
acotado a la detección de firma y de número AT.

**#294 — Estrategia pivot normativa → motor.**
Issue de estrategia, en gran parte **ya ejecutado**: de su "orden de trabajo propuesto", los
puntos 1 (plazos.py), 2 (ContextAssembler) y 3 (motor agnóstico) están implementados y
probados. Queda el punto 4 (CRUD de reglas, #170/#171) y el punto 5 (reglas una a una, que
depende de poblar `reglas_motor`). **Acción:** decidir si se cierra como ejecutado dejando
#170/#171 como herederos, o se recorta a un issue de seguimiento de la fase de carga de reglas.

**#380 — Destino de `documentos_tarea`.**
Es una **decisión de diseño bloqueante**, no resuelta: el modelo `DocumentoTarea` sigue
marcado literalmente *"NO USAR hasta que la decisión esté documentada en un ADR"*. Atención a
la contradicción: #376 da por hecho que la tabla "se conserva" (opción C del propio #380),
pero esa opción todavía no está decidida ni hay ADR. **Acción:** resolver #380 primero
(emitir ADR-008) — desbloquea #376 y aclara #357. Es prerrequisito de ambos.

### 3.6 Válidos sin reservas

- **#300** — bug concreto, código localizado (`_direccion_titular()` en `escritos.py`),
  solución descrita. Listo para implementar.
- **#362, #366** — issues de diseño coherentes con las ADR vigentes; deberían materializarse
  como ADR al resolverse. #362, además, absorbe la limpieza de #357 (ver sección 3.1).
- **#374** — diseño coherente (usa `bddat://interesados/{id}`, alineado con ADR-006).
  Sin milestone: asignar **M3**, ya que el modelo de datos puede afectar a la resolución.
- **#377, #378** — seeds en migración Alembic; dependencia (#337) cerrada. Backend puro.
- **#323** — diseño limpio; crea la tabla genérica `configuracion_sistema`. Sin dependencias.
- **#304, #305, #306** — scripts de análisis de PDF; backend puro. #306 depende de #304.
  Ver solape con #181 (sección 3.5).
- **#106** — alcance pequeño y autónomo (importar códigos DIR3). Revisar si M3 es su sitio
  o encaja mejor como dato de catálogo en M4.
- **#376** — trabajo válido, pero **bloqueado por #380** y mayoritariamente de UI
  (template + JS); no es candidato a las sesiones de backend.

---

## 4. Recomendaciones de acción

### 4.1 Acciones inmediatas sobre GitHub (limpieza, sin código)

1. **Cerrar #318, #153, #357 y #364** — superados por trabajo posterior o sin objeto (ver §3.1).
   En #318 trasladar antes su advertencia a la guía del motor; en #357 absorber su limpieza en #362.
2. **Cerrar y trocear #248** en issues pequeños solo para lo no implementado.
3. **Cerrar #276 y reabrir su necesidad como regla(s) del motor** — la tabla ya no existe.
4. **Reescribir el cuerpo** de #297, #332, #283, #324 y #365 (#365, además, reetiquetar de
   `[DISEÑO]` a implementación de ADR-006).
5. **Reescribir #247** recortándolo a lo no implementado.
6. **Marcar para rediseño** #192 (según ADR-007) y #174 (según la decisión de jefatura: permiso
   blando + bitácora, no permiso duro por expediente).
7. **Asignar milestone M3** a #374.

### 4.2 Orden sugerido de trabajo de backend (post-limpieza)

1. **#380** — emitir ADR-008 sobre `documentos_tarea`. Desbloquea #376. Decisión, no código.
2. **#377 → #378** — seeds de catálogo. Backend puro, dependencia cerrada.
3. **#365** — implementar ADR-006 (`resolver_url()`, esquemas de URL).
4. **#362** — resolver como ADR (certificado de plazo) y aplicar las correcciones en
   `ESTRUCTURA_FTT.json`; absorbe la limpieza que describía #357 (campo `salida` de
   ESPERAR_PLAZO, parche en `Tramite.finalizado`). **#366** — eliminar trámite AUDIENCIA.
5. **#323** — modo global del motor + tabla `configuracion_sistema`.
6. **CBs restantes** (RES, IP, subsanación, notificación a organismo) — sin issue aún.
7. **#304/#305/#306** — scripts de análisis de PDF, tras decidir el solape con #181.
8. **#192, #324** — rediseñar/alinear antes de implementar. **#174 y #276** — requieren una
   decisión previa (modelo de bitácora / reglas del motor) antes de cualquier código.

### 4.3 Observación arquitectónica

El patrón dominante de obsolescencia es claro: los issues de diseño anteriores al 11/05
(#192, #247, #248, #153, #283) quedaron desfasados por la ráfaga de ADRs 002-007. Las ADR
consolidaron decisiones que esos issues aún no reflejan: eliminación de INCORPORAR (004),
fusión REDACTAR+FIRMAR (003), ESFTT sin fechas (002), eliminación de whitelists y verbos
INICIAR/FINALIZAR (007). **Antes de planificar cualquier issue de diseño previo a esa fecha,
contrastarlo con las siete ADR.** Los issues posteriores al 11/05 (#362, #365, #374) sí nacen
alineados.

El caso de **#364** es un aviso adicional: nació alineado, pero un issue posterior (#371)
eliminó la tarea atómica `PUBLICAR` sobre la que se apoyaba. No solo las ADR invalidan issues
abiertos — también el trabajo reciente puede hacerlo. La regla práctica se amplía: contrastar
todo issue de diseño contra las ADR **y** contra los issues estructurales cerrados después de
su creación. La tarea `PUBLICAR` y la tabla `tipos_solicitudes_compatibles` (#276) son los dos
elementos que más issues abiertos arrastran como referencia obsoleta.
