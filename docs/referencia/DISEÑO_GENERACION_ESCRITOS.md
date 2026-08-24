# DISEÑO — Generación de escritos administrativos

> **Issue principal:** #167
> **Fecha análisis:** 2026-03-15 (3 sesiones)
> **Estado:** Análisis completo. Cabos 1-5 cerrados. Implementación pendiente → #277 (M2).
> **Actualizado:** 2026-07-30 (#726) — motor ODT implementado y elección por extensión; ver §"Formato de plantilla".
> **Actualizado:** 2026-07-30 (#182) — **R10 resuelto**: los metadatos no sobreviven al pipeline; sólo el texto renderizado. Las plantillas pasan a `.odt` por **ADR-035**. Ver §"Trazabilidad — códigos embebidos" y §"Formato de plantilla".
> **Actualizado:** 2026-07-31 (#182) — **Composición, inyección real y extracción implementadas**. Las tres decisiones que quedaban abiertas (colocación, alcance de páginas, dígito de control) están cerradas. Ver §"Trazabilidad — códigos embebidos".
> **Actualizado:** 2026-06-16 (#553) — modelo de Context Builder y de tokens reencuadrado por **ADR-025**; ver §"Modelo de tokens del modal".
> **Issues relacionados:** #189 (cerrado), #181 y #182 (vinculados via C3)

---

## Lo implementado (#189 cerrado)

| Componente | Estado | Ubicación |
|---|---|---|
| Modelo `Plantilla` (renombrado desde `TipoEscrito` en #167 Fase 2) | HECHO | `app/models/plantillas.py` |
| Modelo `ConsultaNombrada` | HECHO | `app/models/consultas_nombradas.py` |
| Migración BD (ambas tablas) | HECHO | `migrations/versions/20c5d1e9d782*.py` |
| `ContextoBaseExpediente` (Capa 1) | HECHO | `app/services/escritos.py` |
| `generar_escrito()` (despacho por extensión + nombre, ruta, guardado, MIME y validación) | HECHO | `app/services/generador_escritos.py` |
| Motor de render ODT (#726) | HECHO | `app/services/generador_escritos_odt.py` |
| Motor de render DOCX (heredado, en retirada) | HECHO | `app/services/generador_escritos_docx.py` |
| Dependencia `docxtpl` (solo la rama `.docx`) | HECHO | `requirements.txt` (commit 6b85fcf) |
| Admin plantillas — CRUD 4 pantallas | HECHO | `app/modules/admin_plantillas/` |
| Panel de tokens copiables | HECHO | `_panel_tokens.html` |
| Protocolo URI `bddat-explorador://` | HECHO | Issue #231 |
| Config `PLANTILLAS_BASE` | HECHO | `app/config.py` |
| Guía Context Builders | HECHO (doc) | `docs/referencia/GUIA_CONTEXT_BUILDERS.md` |

**Pendiente:**
- Sin endpoint que dispare la generación desde la UI de tramitación

---

## Modelo plantillas — decisiones (Cabo 1+2 cerrado)

| # | Decisión | Motivo |
|---|----------|--------|
| 1 | **Renombrar `tipos_escritos` → `plantillas`** | El nombre actual induce a confusión; es un registro de plantillas concretas |
| 2 | **Añadir `tipo_expediente_id` FK nullable a `plantillas`** | Completa la E que falta en ESFTT. NULL = cualquier tipo de expediente |
| 3 | **Eliminar `campos_catalogo` de `plantillas`** | Cálculo dinámico según contexto, no dato estático — evita inconsistencias |
| 4 | **Añadir `origen` (INTERNO/EXTERNO/AMBOS) a `tipos_documentos`** | Impide que una plantilla apunte a un tipo de documento externo |
| 5 | **Mantener `contexto_clase`** | Capa 2: declara el CB **ensamblador del escrito** (no del trámite). Relación plantilla→CB **N:1** — varias plantillas comparten clase. Ver ADR-025 |
| 6 | **Mantener `filtros_adicionales` JSONB** | Absorbe futuro sin migración |
| 7 | **Añadir campo `variante` TEXT nullable a `plantillas`** | Texto libre para distinguir plantillas del mismo contexto ESFTT ("Favorable", "Denegatoria") |

**Implementación:** Issue #167 Fase 2.

---

## Nomenclatura de ficheros (Cabo 3 — rediseñado en #698, 2026-08-24)

```
{texto_tramite} {siglas_solicitud} AT-{numero_at} [V {variante}].{ext}
```

`texto_tramite` sale de `tipos_tramites.nombre_en_plantilla` — dato de
catálogo, editable por el supervisor en tablas_maestras (#171), igual que
siempre. `app/services/nombres_documentos.py::texto_tramite()` es el helper
que lo combina con lo que un campo de texto no puede expresar por sí solo:

- **Ajuste** (combina con el dato base): trámites repetibles en la misma
  fase añaden numeración de vuelta sobre el texto de catálogo —
  `REQUERIMIENTO_SUBSANACION`: "Requerimiento", "Requerimiento 2"...
- **Sustitución** (el dato de catálogo no basta): cuando hay más de un
  resultado posible y la diferencia no es de wording sino de qué acto
  administrativo es el documento, el texto sale por código a propósito —
  `COMUNICACION_INICIO_ADMISION`: "Admisión a Trámite" si el expediente es
  Renovable (Hito 1, RD-ley 23/2020 art. 1.2 in fine), "Oficio Inicio" en
  cualquier otro caso.
- **Fallback**: trámite sin `nombre_en_plantilla` poblado y sin ajuste ni
  sustitución registrados → código crudo del trámite tal cual. Nunca
  bloquea la generación — el nombre del fichero no implica nada
  administrativamente ni presupone su contenido, es solo ayuda semántica
  para cuando el documento circula fuera de BDDAT (la trazabilidad real va
  por el código embebido `BDDAT-<tarea_id>-<letra>`, #182 — ver
  §"Trazabilidad — códigos embebidos" más abajo).

Registro de ajustes/sustituciones por el par **(fase, trámite)**, nunca solo
por código de trámite: hay códigos reutilizados como vocabulario en más de
una fase (`fases_tramites`, ADR-037/#725) — p.ej. `ELABORACION` en
`RESOLUCION` y en `RECONOCIMIENTO_INTERESADO`. `tipos_tramites` tiene una
fila por código, no por (fase, código): el dato de catálogo de un trámite
compartido es el mismo en las dos fases. Para `RESOLUCION.ELABORACION`
(única implementada en #698) no hay colisión real porque
`RECONOCIMIENTO_INTERESADO.ELABORACION` no está implementado — cuando se
aborde (issue de seguimiento #809), hay que decidir ahí cómo desambiguar.

**Sin token de tarea:** la generación de escritos solo ocurre desde tareas
`ELABORAR` (único punto de entrada, #608) — un token constante no distingue
nada. **Sin token de tipo de expediente:** es un dato inmutable del
expediente, ya implícito en `AT-N`. **Sin token de fase independiente:** la
fase interviene como parte de la clave de registro de ajustes/sustituciones,
no como token propio del nombre. Las columnas `nombre_en_plantilla` de
`tipos_tareas`, `tipos_expedientes` y `tipos_fases` quedan sin consumidor de
código con este diseño, pero **no se eliminan** — se dejan tal cual por si
en el futuro hacen falta (p.ej. desambiguar por fase un trámite compartido
entre dos fases, u otro uso no previsto).

**Casuísticas pobladas (#698):** `REQUERIMIENTO_SUBSANACION`,
`COMUNICACION_INICIO_ADMISION`, `RESOLUCION.ELABORACION`. El resto de
trámites cae al fallback de código crudo mientras
`tipos_tramites.nombre_en_plantilla` siga sin poblar — se van completando
incrementalmente (issue de seguimiento #809, "poblado en código del
servicio del nombre del fichero": añadir el dato en catálogo y, solo si el
trámite concreto lo necesita, un ajuste o sustitución).

**Extensión:** la de su plantilla — `.odt` o `.docx` (#726). El escrito
generado conserva el formato del que se generó.

**Almacenamiento:** El contexto ESFTT vive en BD, no en el filesystem, y la
convención de nombres evita colisiones sin necesidad de subdirectorios. Aun
así el explorador del alta permite navegar carpetas bajo
`PLANTILLAS_BASE/plantillas/` y `ruta_plantilla` guarda la subruta completa:
las plantillas de desarrollo viven en `escritos/`.

**TODO:** Secuencial automático (sufijo ` (2)`, ` (3)`...) cuando ya existe
un documento con el mismo nombre para el mismo expediente.

**Implementación:** Issue #698 (`app/services/nombres_documentos.py`).
Reemplaza el diseño original de Issue #167 Fase 3 (comodines `ANY` sobre
5 tablas), descartado por no soportar lógica condicional cuando el dato de
catálogo no basta.

---

## Modelo de tokens del modal (Cabo 4 — reencuadrado por ADR-007 + ADR-025)

> El diseño original de este cabo (3 tablas whitelist E→S→F→T + toggle "Solo aplicables al
> contexto") quedó **obsoleto**: ADR-007 eliminó las whitelists y #552 retira el toggle huérfano.
> El modelo vigente es el siguiente.

Los tokens válidos de una plantilla son la unión de cuatro fuentes, y **solo una** depende del
contexto de la plantilla:

| Fuente | Alcance | ¿Depende del encuadramiento? |
|---|---|---|
| Capa 1 (`ContextoBaseExpediente`) | universal | No |
| Consultas nombradas | universal (`:expediente_id`, vacío-seguras) | No |
| Fragmentos `.docx` | universal (extractos repetibles) | No |
| Context Builder (Capa 2) | el CB declarado en `contexto_clase` | **Sí — por `contexto_clase`, no por los FKs ESFT** |

- Los **FKs ESFT** de la plantilla no intervienen en la generación; solo gobiernan **dónde se
  ofrece** la plantilla en ELABORAR (match NULL-comodín, `api_escritos.py`). Se eligen con
  **selects planos** (no validables en abstracto, ADR-007) — ver #552.
- La **dinamicidad de tokens** del modal se ancla a `contexto_clase`: cada CB declara sus tokens
  y el modal se re-consulta al cambiar la clase — ver #553.

**Implementación:** limpieza del alta (#552) + modal contextual (#553).

---

## Trazabilidad — códigos embebidos (C3, vincula #182 y #181)

> **R10 resuelto el 2026-07-30** (sesión de #182), midiendo el pipeline completo
> con una probeta que llevaba el mismo código por 22 vías a la vez. La conclusión
> invalida el diseño anterior de este apartado, que daba las custom properties
> por vía principal: **no llegan al PDF**. Instrumental de la prueba en
> `docs_prueba/temp/r10_*.py` (fuera de git).

**Ciclo de vida real del documento generado:**
```
GENERAR (#167)          → .docx / .odt con código embebido (#182)
   ↓
Usuario edita en Writer → sobrevive todo, incluidos los metadatos
   ↓
Exportar a PDF (Writer) → mueren custom properties, Comentarios, Categoría,
                          marcadores, docVars y el texto oculto (w:vanish);
                          sobreviven Título/Asunto/Palabras clave y todo el
                          texto renderizado
   ↓
BandeJA → Portafirmas   → reescribe el PDF con iText: BORRA Título, Palabras
                          clave, Autor y Creador, y SOBRESCRIBE Asunto con su
                          propio código (HCV=…). El texto renderizado queda
                          intacto, con las coordenadas sin mover
   ↓
INCORPORAR al pool      → inspección automática (#181) lee el código
```

**Qué sobrevive al circuito completo:** únicamente el **texto renderizado en la
página**. Cabecera, pie, cuerpo, cuadros de texto flotantes y ambos márgenes en
vertical llegan enteros y en una sola pieza; el código debe ser ASCII sin
acentos (los acentos se trocean al extraer texto del PDF, los tokens no).

**Vía de metadatos: descartada.** No es sólo que las custom properties no
lleguen al PDF — es que ninguno de los siete canales de metadatos probados
sobrevive al portafirmas.

**Dónde NO colocarlo:** el portafirmas ocupa el **margen derecho** con su banda
vertical («Es copia auténtica de documento electrónico») y la **banda inferior**
con la tabla FIRMADO POR / VERIFICACIÓN y su propio QR. El margen izquierdo
queda libre. Esto afecta también al QR que este documento proponía: la Junta ya
estampa uno, y competirían por el mismo sitio y significado.

**El «PDF firmado» no lleva firma criptográfica.** Los tres PDFs devueltos por
el circuito no tienen `/ByteRange`, ni campo de firma, ni actualización
incremental: son copias auténticas selladas con CSV, generadas por iText. La
firma vive en el sistema de la Junta, no en el fichero. Consecuencia para
cualquier diseño futuro: no se puede validar la firma leyendo el PDF.

**Protección contra edición: no disponible en .docx.** Se probaron tres
mecanismos y LibreOffice no exporta ninguno a OOXML — protección de campos
(`w:documentProtection`), bloqueo de forma (`a:spLocks`) y anclaje bloqueado
(`locked="1"`) desaparecen al guardar. En ODF sobrevive parcialmente
(`style:protect` conserva `position size`, pierde `content`).

**Requisito: dígito de control.** Un código ausente es inocuo — se detecta que
no está y el documento pasa por las heurísticas de #181. El peligro es un código
**alterado** que siga pareciendo válido: produce una asociación falsa que el
usuario confirma de buena fe. El código debe llevar verificación propia para que
una alteración no pueda producir el código válido de otra tarea.

**Código estructurado — cerrado (2026-07-31).** Formato `BDDAT-<tarea_id>-<letra>`.
El id de instancia es `tarea_id` (#711): el encuadramiento ESFTT completo del
diseño original es redundante, porque desde el id de la tarea se deduce entero.
La letra es un dígito de control módulo 23 (misma mecánica que la letra del
NIF/DNI, tabla `LETRAS_CONTROL` de `app/services/codigo_seguimiento.py`): cubre
el escenario real del issue —alteración accidental del código en el pipeline o
al editar en Writer—, no un intento deliberado de fabricar el código de otra
tarea por alguien con acceso al código fuente. Se descartó un HMAC con clave de
servidor por desproporcionado para ese riesgo.

**Colocación — cerrada (2026-07-31): pie de página, sin giro, en todas las
páginas.** De los dos candidatos que dejaba abiertos ADR-035 (margen izquierdo
vertical vs. pie sin giro), se elige el pie: es el que ya construyó el gancho
de #726 (`FRAME_CODIGO` en `generador_escritos_odt.py`), más legible, y no hubo
motivo para invertir en el cuadro girado del margen. Recorre todas las master
pages, así que aparece en todas las páginas del documento (protege también si
el documento se fotocopia o se separan páginas sueltas).

**Implementación (Issue #167 Fase 6):**
- `app/services/codigo_seguimiento.py` — `componer_codigo(tarea_id)` y
  `extraer_tarea_id(texto)`. Lógica pura, agnóstica del formato.
- `app/services/generador_escritos_odt.py` — gancho de inyección de #726, sin
  cambios: ya colocaba el código donde #182 decidió quedarse.
- `app/routes/api_escritos.py` (`POST /api/escritos/generar`) — compone el
  código con `tarea.id` y lo pasa a `generar_escrito()`. El motor `.docx` lo
  sigue ignorando con un warning (ADR-035: ningún canal de metadatos OOXML
  sobrevive al pipeline).
- Tests: `tests/test_182_codigo_seguimiento.py` — roundtrip, detección de
  alteración, y un ciclo completo con el fixture real de #732 vía soffice
  (componer → inyectar → PDF real → extraer), que cierra R10 con el algoritmo
  definitivo en vez de un string de prueba.

**#717 implementado (2026-08-01):** consumo de `extraer_tarea_id()` para el
vínculo `CONSUMIDO` sobre el diagnóstico. Al vincular el documento producido
de un ELABORAR de REQUERIMIENTO_SUBSANACION (`editar_tarea` o
`POST /api/escritos/generar` con `asignar_doc_producido=true`), se extrae el
texto del fichero local (`app/services/extraccion_texto_documento.py` — pypdf
para `.pdf`, zipfile+lxml para `.odt`) y, si el código embebido acredita que
salió de *esta* tarea, se deriva el `CONSUMIDO` sobre el diagnóstico del
trámite anterior en la fase (mismo criterio que `ContextoSubsanacion`, ahora
compartido en `invariantes_esftt.diagnostico_tramite_anterior`). Sin token
propio no se deriva nada (advertencia no bloqueante). Sin backfill a
propósito (decisión de Carlos, 2026-08-01): los documentos anteriores a #182
—AT-2004 incluido, fixture de #732— se quedan sin vínculo, protegidos por el
criterio de #711. Ver `app/services/mutaciones_arbol.py::_hook_717_elaborar_
consumido_diagnostico` y `tests/test_717_consumido_diagnostico.py`.

**Pendiente, fuera de #182 y #717:** el consumo de `extraer_tarea_id()` para
clasificar automáticamente al incorporar un documento (#181).

---

## Formato de plantilla — ODT (ADR-035)

Las plantillas y los fragmentos pasan a `.odt`, con renderizador propio y
conservando el motor `.docx` en paralelo. La decisión, sus motivos y los
requisitos que impone (LibreOffice como requisito de instalación, fin del flujo
legado de Access, plantilla base canónica) están en
`docs/decisiones/ADR-035-plantillas-escritos-odt.md` — **no duplicar aquí**.

Implementado en #726: `app/services/generador_escritos_odt.py`, con
`generador_escritos.generar_escrito` despachando por la extensión de
`plantilla.ruta_plantilla`. El contexto lo construye
`escritos.construir_contexto` y es el mismo para los dos motores.

Cabos de implementación del motor, y cómo quedaron:

- **Fragmentos.** Se insertan sustituyendo el párrafo del marcador por los
  bloques del fragmento, no dentro de él: así no hay párrafos anidados que
  reparar. Probado con negrita, cursiva y listas. Si plantillas y fragmentos
  derivan de la misma plantilla base comparten estilos y no hace falta
  fusionarlos; en otro caso se renombran los estilos automáticos del fragmento
  (LibreOffice los llama `P1`, `T1`, `L1` en todos los documentos) con prefijo
  `frg<Nombre>_` y se reescriben sus referencias.
- **Orden de las operaciones.** Los fragmentos se insertan **antes** de pasar
  Jinja2, de modo que un fragmento puede llevar tokens propios y se rellenan.
  docxtpl no lo permite.
- **Cabeceras y pies** viven en `styles.xml`. Los tokens llegan a todos porque
  Jinja2 procesa la parte completa; lo que el sistema **inserta** (el código de
  seguimiento) recorre **todas las master pages**, o no aparecería en las
  páginas que usen una distinta —caso típico: primera página diferente.
- **Tokens partidos.** El motor los recompone antes de Jinja2. En ODT llegan
  enteros mientras nadie los edite, pero cambiar el formato a media palabra en
  Writer parte el token entre varios `<text:span>`.
- **Bucles.** `{%tr %}` (fila de tabla) y `{%p %}` (párrafo) se elevan fuera de
  su bloque con la misma convención que docxtpl —la etiqueta va *delante* del
  bloque, así que `{%tr for … %}` repite la fila que la contiene—, porque es la
  que el panel de tokens enseña al supervisor y tiene que valer en los dos
  motores. Las expresiones no pueden llevar `<`, `>` ni `&`: se escapan al
  serializar y Jinja2 deja de reconocerlas (misma limitación que en docxtpl).
- **Imágenes.** Sin equivalente ODF de `InlineImage`, y de momento no hace
  falta: el logo y los rótulos fijos viven en la master page (ADR-035 §4).
  Es la única etiqueta que **no** se comporta igual en los dos formatos:
  `{{ img('logo.png', '3.5') }}` funciona en `.docx` y en `.odt` falla con
  «'img' is undefined». No la ofrece el panel de tokens, así que solo aparece
  en plantillas escritas a mano. Todo lo demás —tokens, `{{r Fragmento }}`,
  `{%tr %}`, `{%p %}`— se escribe igual en ambos; lo que cambia es quién los
  resuelve: en `.docx` el `{{r }}` acaba siendo una variable Jinja2 con un
  `Subdoc` detrás (por eso el fragmento entra *dentro* del párrafo y hay que
  reparar anidados), y en `.odt` no llega a Jinja2 porque el motor sustituye el
  párrafo antes.
- **Validación del alta** (`generador_escritos.validar_plantilla`) comprueba el
  formato y **compila la plantilla con Jinja2**, que es lo que el mensaje de
  error decía y no hacía. Los marcadores `{{r Fragmento }}` se excluyen de esa
  compilación: no son Jinja2, los resuelve el motor antes. Falta la
  comprobación de canonicidad de ADR-035 §5, que es de #727.

### Procedimiento del supervisor: crear una plantilla nueva (#727)

Ninguna plantilla nace de un `.odt` en blanco (ADR-035 §5): siempre se parte de
la base canónica correspondiente.

1. **Descargar la base.** Desde el listado de plantillas (`/plantillas/` →
   botón «Plantillas base») o desde el propio formulario de alta: **Carta**
   (oficios, requerimientos, comunicaciones — cualquier escrito con
   destinatario), **Resolución** (actos resolutorios), o **Fragmento** (bloque
   reutilizable insertado con `{{r Nombre }}` — misma hoja de estilos, sin
   cabecera ni logo, a propósito: el motor no lee el `styles.xml` del
   fragmento al insertarlo).
2. **Editarla en LibreOffice Writer.** Sustituir el texto de ejemplo, insertar
   los tokens (`{{campo}}`, `{{r Fragmento}}`, `{%tr %}`, `{%p %}` — panel de
   tokens del propio formulario) usando los estilos de párrafo con nombre ya
   definidos (`Cabecera - *`, `Formulario - *`, `BDDAT - *`) en vez de crear
   estilos nuevos. La fuente es Source Sans Pro sin margen: cambiarla no
   bloquea el guardado (se admite con aviso, ADR-035 §5) pero rompe la
   canonicidad.
3. **Guardar como `.odt`** (no `.docx`: pierde la marca de versión de
   `meta.xml` y la hoja de estilos común) y colocarlo en el servidor, dentro
   de `PLANTILLAS_BASE/plantillas/` (o su subcarpeta correspondiente). No hay
   subida desde el navegador: es una copia de fichero en el share/disco donde
   vive `PLANTILLAS_BASE` (ANALISIS_DESPLIEGUE.md §6).
4. **Registrarla en `/plantillas/nueva/`.** El botón «Seleccionar del
   servidor» abre el explorador restringido a `PLANTILLAS_BASE/plantillas/`
   con el fichero ya colocado en el paso 3. El alta valida sintaxis (Jinja2) y
   avisa de desviaciones de canonicidad (fuente ajena, estilos personalizados
   que faltan) sin bloquear el guardado.

---

## Necesidades por actor (resumen de decisiones)

### A. Supervisor — al crear/gestionar plantillas

| ID | Necesidad | Decisión |
|----|-----------|----------|
| A0 | Filtrado dinámico de tokens | Por `contexto_clase` (CB), no por ESFT. Sin whitelist (ADR-007) ni toggle (#552). Ver ADR-025 y §"Modelo de tokens del modal" |
| A1 | Validación de sintaxis de la plantilla registrada | `generador_escritos.validar_plantilla`: formato + compilación Jinja2, por extensión (#726). Canonicidad ADR-035 §5 → #727 |
| A2 | Probar plantilla con datos reales | DIFERIBLE |
| A3 | Parseo automático del .docx (detectar campos/consultas/fragmentos) | Necesario parcial (Fase 6) |
| A4 | CRUD de consultas nombradas | Necesario (Fase 5) |
| A5 | Versionado de plantillas | DIFERIBLE |

### B. Tramitador — al usar la plantilla en tarea REDACTAR

| ID | Necesidad | Decisión |
|----|-----------|----------|
| B1 | Botón "Generar escrito" en tarea REDACTAR | Botón en la card de tarea (Fase 5) |
| B2 | Selección de plantilla filtrada por contexto ESFTT | Lista con NULLs como comodines (Fase 5) |
| B3 | Preview de campos antes de generar | Valores del expediente + alerta si vacío (Fase 5) |
| B4 | Guardado con nombre sistematizado + checkboxes | Checkboxes: registrar pool + asignar doc_producido (Fase 5) |
| B5 | Abrir carpeta contenedora tras generar | Checkbox → protocolo `bddat-explorador://` (Fase 5) |
| B6 | Regeneración: sobrescritura transparente | Aviso + reemplazo binario en disco (Fase 5) |
| B8 | Generar = iniciar tarea | Si `fecha_inicio is None` → asignar `date.today()` (Fase 5) |

### C. Transversales

| ID | Necesidad | Decisión |
|----|-----------|----------|
| C1 | Ejecución de consultas nombradas | Implementar stub `_ejecutar_consultas()` (Fase 5) |
| C2 | Context Builders (Capa 2) | EN CURSO — #289. Implementados: #391, #393, #394. Bloqueado: #392. Modelo reencuadrado en ADR-025 (ensamblador del escrito) |
| C3 | Trazabilidad y código embebido | `BDDAT-<tarea_id>-<letra>` en el pie de página, todas las páginas (#182). Custom properties + QR descartado (R10) |
| C4 | Metadatos del documento generado | `fecha_administrativa=NULL`, `prioridad=0`, `asunto=` descripción plantilla + ESFTT real |
| C7 | Gestión de errores de generación | Toast con detalle del error Jinja2 (Fase 5) |

---

## Fases de implementación

Ver `docs/PLAN_ROADMAP.md` — issue #167 para el detalle completo de cada fase.

| Fase | Contenido | Complejidad | Dependencias |
|------|-----------|:-----------:|:------------:|
| 0 | Fix R6 + export `campos_catalogo` | Baja | Ninguna |
| 1 | Solicitudes: FK directa + whitelist ESFTT | Alta | Fase 0 |
| 2 | Plantillas: rename + limpieza + nuevos campos | Alta | Fase 0 |
| 3 | Nomenclatura: `nombre_en_plantilla` × 5 tablas | Baja | Ninguna |
| 4 | Admin plantillas: selectores en cascada + form completo | Media-Alta | Fases 1+2+3 |
| 5 | Motor de generación (B1-B8) | Alta | Fase 4 |
| 6 | Trazabilidad y parseo (C3, A3) | Media | Fase 5 |

Las fases 1, 2 y 3 son **independientes entre sí** y pueden ejecutarse en cualquier orden.
Las fases 4-6 son secuenciales y requieren que cicatricen las anteriores.

---

## Actualizaciones pendientes tras ejecutar migraciones (Cabo 6)

Renombrado ejecutado en #167 Fase 2. Actualización de docs completada en #278.

| Fichero | Estado |
|---------|--------|
| `docs/GUIA_CONTEXT_BUILDERS.md` | ✅ actualizado (#278) |
| `docs/PLAN_ROADMAP.md` | ✅ actualizado (#278) |
| `docs/DISEÑO_SUBSISTEMA_DOCUMENTAL.md` | ✅ ya actualizado |
