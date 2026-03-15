# Analisis #167 — Generacion de escritos administrativos

> **Estado:** Puntos 1-4 completados. Pendiente punto 5 (analisis tecnico pre-implementacion).
> **Issues relacionados:** #167 (abierto), #189 (cerrado), #181 y #182 (vinculados via C3)
> **Fecha inicio analisis:** 2026-03-15
> **Sesiones:** 3 (todas 2026-03-15)

---

## Inventario de lo implementado (#189 cerrado)

| Componente | Estado | Ubicacion |
|---|---|---|
| Modelo `TipoEscrito` | HECHO | `app/models/tipos_escritos.py` |
| Modelo `ConsultaNombrada` | HECHO | `app/models/consultas_nombradas.py` |
| Migracion BD (ambas tablas) | HECHO | `migrations/versions/20c5d1e9d782*.py` |
| `ContextoBaseExpediente` (Capa 1) | HECHO | `app/services/escritos.py` |
| `generar_escrito()` (orquestador) | HECHO (parcial) | `app/services/generador_escritos.py` |
| Dependencia `docxtpl` | HECHO | `requirements.txt` (commit 6b85fcf) |
| Admin plantillas — CRUD 4 pantallas | HECHO | `app/modules/admin_plantillas/` |
| Panel de tokens copiables | HECHO | `_panel_tokens.html` |
| Protocolo URI `bddat-explorador://` | HECHO | Issue #231 |
| Config `PLANTILLAS_BASE` | HECHO | `app/config.py` |
| Plantilla de prueba .docx | HECHO | `docs_prueba/plantillas_escritos/plantillas/` |
| Guia Context Builders | HECHO (doc) | `docs/fuentesIA/GUIA_CONTEXT_BUILDERS.md` |

**Pendiente del orquestador:**
- Ejecucion de consultas nombradas: `_ejecutar_consultas()` devuelve `{}` (stub)
- Context Builders (Capa 2): arquitectura lista, cero implementaciones
- No hay endpoint que dispare la generacion desde la UI de tramitacion

---

## Decisiones sesion 2 (2026-03-15)

### Cabo 1+2: CERRADO — Estructura de `tipos_escritos` y `tipos_documentos`

Se cierran conjuntamente los cabos 1 y 2 con 6 decisiones firmes:

| # | Decision | Motivo |
|---|----------|--------|
| 1 | **Renombrar `tipos_escritos` a `plantillas`** | El nombre actual induce a confusion; es un registro de plantillas concretas, no un catalogo de tipos |
| 2 | **Anadir `tipo_expediente_id` FK nullable a `plantillas`** | Completa la E que falta en ESFTT. NULL = cualquier tipo de expediente |
| 3 | **Eliminar `campos_catalogo` de `plantillas`** | Debe ser calculo dinamico segun contexto, no dato estatico. Evita inconsistencias |
| 4 | **Anadir `origen` (INTERNO/EXTERNO/AMBOS) a `tipos_documentos`** | Impide que una plantilla apunte a un tipo de documento externo. Distinto del `origen` eliminado en #191 (aquel era en la instancia `documentos`, este es en el catalogo `tipos_documentos`) |
| 5 | **Mantener `contexto_clase`** | Necesario para Capa 2 (Context Builders) |
| 6 | **Mantener `filtros_adicionales` JSONB** | Absorbe futuro sin migracion |

> **Nota sobre decision 4:** Lo que se propone es distinto de lo eliminado en #191.
> Anadir `origen` a `tipos_documentos` (el catalogo de tipos), no a `documentos`
> (la instancia). A nivel de tipo no hay ambiguedad: una RESOLUCION es siempre
> interna, una DR_NO_DUP es siempre externa. No entra en conflicto con la decision del #191.

---

### Cabo 4: CERRADO — Filtrado dinamico de tokens por contexto ESFTT

#### Decision 1: Tablas whitelist ESFTT — cadena completa E→S→F→T

Tres tablas whitelist editables cubren la cascada completa:

- **`expedientes_solicitudes`** (PK compuesta: `tipo_expediente_id` + `tipo_solicitud_id`) — que solicitudes son validas para cada tipo de expediente
- **`solicitudes_fases`** (PK compuesta: `tipo_solicitud_id` + `tipo_fase_id`) — que fases aplican a cada tipo de solicitud
- **`fases_tramites`** (PK compuesta: `tipo_fase_id` + `tipo_tramite_id`) — que tramites son validos dentro de cada fase

Caracteristicas acordadas:
- Seed inicial desde `Estructura_fases_tramites_tareas.json`
- CRUD editable por supervisor (legislacion cambiante)
- La cascada de selectores consume estas tablas como whitelist
- Solo definen **posibilidad** ("esta combinacion tiene sentido"), no obligatoriedad ni orden
- Capa 1 tokens (12 campos base) siempre los mismos — la dinamicidad llega con Capa 2
- Infraestructura AJAX preparada para refresco futuro del panel de tokens

#### Decision 2: Tipos de solicitud combinados como entidades propias

**Problema:** La tabla M:N `solicitudes_tipos` expresa combinaciones de tipos atomicos
(AAP+AAC, AAP+AAC+DUP...) pero esta flexibilidad es innecesaria — las combinaciones
legales son finitas y cerradas. La M:N complica el filtrado en cascada y hace imposible
un FK simple desde plantillas.

**Decision:** Extender `tipos_solicitudes` con tipos combinados como entradas propias.
La tabla contendra tanto tipos atomicos (AAP, AAC, DUP...) como combinaciones legales.

Tipos combinados a anadir:

| Siglas | Descripcion |
|---|---|
| AAP_AAC | Autorizacion Administrativa Previa y de Construccion |
| AAP_AAC_DUP | AAP + AAC + Declaracion de Utilidad Publica |
| AAP_AAC_AAU | AAP + AAC + Autorizacion Ambiental Unificada |
| AAP_AAC_AAU_DUP | AAP + AAC + AAU + Declaracion de Utilidad Publica |
| AAC_DUP | AAC + Declaracion de Utilidad Publica |
| AAE_DEFINITIVA_AAT | Explotacion Definitiva + Transmision de Titularidad |

**Justificacion:**
- Las combinaciones legales son ~6. No van a crecer arbitrariamente (requiere cambio legislativo)
- Cada combinacion tiene implicaciones procedimentales distintas (fases, texto de resoluciones)
- Las plantillas necesitan un FK directo para saber que texto administrativo usar
- El filtrado en cascada se resuelve con JOINs directos contra las whitelist, sin tabla puente
- Si aparece una nueva combinacion legal, es un INSERT + actualizacion de whitelist

**Impacto en tablas existentes:**

| Tabla | Cambio |
|---|---|
| `tipos_solicitudes` | Anadir ~6 tipos combinados |
| `solicitudes` | Anadir FK `tipo_solicitud_id` directa al tipo (atomico o combinado) |
| `solicitudes_tipos` | Mantener como historico, dejar de usar para logica de negocio |
| Wizard creacion solicitudes | Selector directo en vez de multiselect de checkboxes |
| Plantillas (ex `tipos_escritos`) | FK simple a `tipo_solicitud_id` |

> **Comentario del usuario:** "Las plantillas estan intimamente relacionadas con la
> cadena ESFTT (con S=las solicitudes presentadas). Si solicito AAP, la plantilla no
> puede decir en su texto '...de acuerdo con la solicitud de Autorizacion Administrativa
> de Construccion de fecha...' Todo influye. El lenguaje administrativo requiere de
> mucha precision, especialmente las resoluciones."

> **Comentario del usuario:** "El sistema de eleccion de las solicitudes compatibles
> deberia ser simplemente un listado de tipos de solicitud donde esten ya combinadas
> las compatibles. Aunque el listado de tipos de solicitud sea mas largo, no es
> harcodear, es poner en la tabla lo que es posible y ahora mismo las posibilidades
> de combinaciones de solicitudes son unas pocas, no infinitas."

> **Comentario del usuario:** "El documento `Estructura_fases_tramites_tareas.json`
> no es absolutamente completo. Es esencialmente correcto pero no exhaustivo.
> Mi idea es que el supervisor pueda completar estas jerarquias en el futuro,
> modificarlas o crear nuevas, pues la legislacion es muy cambiante."

---

### Principio de escape — Principio transversal de diseno

> **Comentario del usuario:** "Despues de anos tramitando expedientes, me encuentro la
> necesidad de realizar ciertos tramites que no estan exactamente recogidos en el flujo
> normal. Una alegacion fuera de contexto, cambio de rumbo del expediente en medio de la
> tramitacion de la IP, etc. En el motor de reglas, en el listado en cascada, etc., en
> definitiva en todos los lugares donde se impide realizar ciertas cosas, se debe dejar
> una via de escape para poder por ejemplo crear una FTT de un tipo donde no toca, de
> forma que no haya callejon sin salida. Por supuesto estas acciones de escape se
> documentan en la bitacora que esta prevista para estos casos."

Cristaliza como principio de diseno transversal a todo el sistema:
- **Toda cascada, filtro y regla debe tener via de escape**
- El usuario puede elegir opciones "fuera de contexto" con advertencia visual
- Toda accion de escape se registra en bitacora
- **Nunca crear callejones sin salida**

Aplica a: selectores en cascada ESFTT, motor de reglas, filtrado de plantillas,
y cualquier mecanismo futuro que restrinja opciones.

---

## Puntos del analisis (ficheros separados)

| Punto | Fichero | Contenido |
|:-----:|---------|-----------|
| 1 | [ANALISIS_167_PUNTO_1_NECESIDADES.md](ANALISIS_167_PUNTO_1_NECESIDADES.md) | Mapa de necesidades A0-A5, B1-B8, C1-C8 |
| 2 | [ANALISIS_167_PUNTO_2_DEPENDENCIAS.md](ANALISIS_167_PUNTO_2_DEPENDENCIAS.md) | Matriz de impacto, migraciones, modelos, rutas, templates, JS |
| 3 | [ANALISIS_167_PUNTO_3_RIESGOS.md](ANALISIS_167_PUNTO_3_RIESGOS.md) | Riesgos R1-R10, inconsistencias I1-I5 |
| 4 | [ANALISIS_167_PUNTO_4_FASES.md](ANALISIS_167_PUNTO_4_FASES.md) | Fases 0-6, diagrama, estado Flask por parada |
| Anexos | [ANALISIS_167_GENERACION_ESCRITOS_ANEXOS.md](ANALISIS_167_GENERACION_ESCRITOS_ANEXOS.md) | Comentarios literales del usuario sesiones 1-2 |

## Cabos sueltos — sesiones dedicadas pendientes

### Cabo 1+2: ~~Estructura de `tipos_escritos` y `tipos_documentos`~~ — CERRADO

Resuelto en sesion 2 con 6 decisiones firmes (ver seccion "Decisiones sesion 2").

### Cabo 3: ~~Sistematizacion de nombres de archivos~~ — CERRADO

Afecta a B4 y C8. Resuelto en sesion 3.

#### Convencion de nomenclatura

Separador: espacio. El nombre se compone concatenando los `nombre_en_plantilla`
de cada nivel ESFTT separados por espacios. BDDAT siempre compone el nombre,
nunca lo parsea — el nombre es solo para legibilidad humana, no para logica interna.

**Requisito previo:** Anadir campo `nombre_en_plantilla` en cada tabla tipo_
(`tipos_tareas`, `tipos_tramites`, `tipos_fases`, `tipos_solicitudes`, `tipos_expedientes`).
Texto corto legible que aparecera en los nombres de fichero.
Puede contener espacios (ej: "Requerimiento subsanacion").

**Nombre de plantilla** (sistema lo construye, supervisor lo acepta o ajusta):

```
{tarea} {tramite} {fase} {solicitud} {expediente} [V {variante}].docx
```

Reglas para NULLs (comodines):
- NULL al final de la cadena → se omite
- NULL en medio de dos valores reales → se sustituye por `ANY`

El campo **variante** es texto libre que el supervisor introduce en el formulario
para distinguir plantillas del mismo contexto ESFTT (ej: "Favorable", "Denegatoria",
"Condicionada"). Resuelve el problema de las multiples plantillas sin inflar
el interfaz con campos para cada posibilidad.

**Nombre de documento generado** (sistema lo construye con datos reales del expediente):

Los niveles que eran NULL/ANY en la plantilla se rellenan con los valores reales
del expediente concreto.

**Almacenamiento de plantillas:** Directorio plano en `PLANTILLAS_BASE/`.
El contexto ESFTT vive en la BD (tabla `plantillas`), no en el filesystem.
La convencion de nombres evita colisiones sin necesidad de subdirectorios.

**Ejemplos:**

| Plantilla | Documento generado |
|---|---|
| `Redactar Elaboracion Resolucion V Favorable.docx` | `Redactar Elaboracion Resolucion AAP+AAC AT-13465-24 V Favorable.docx` |
| `Redactar Requerimiento subsanacion.docx` | `Redactar Requerimiento subsanacion AAP+AAC AT-13465-24.docx` |
| `Notificar Traslado condicionados Consultas ANY Transporte.docx` | `Notificar Traslado condicionados Consultas AAP+AAC+DUP AT-13465-24.docx` |
| `Redactar Elaboracion Resolucion ANY Transporte V Denegatoria.docx` | `Redactar Elaboracion Resolucion AAP+AAC AT-13465-24 V Denegatoria.docx` |

**TODO implementacion:** Secuencial automatico (`_2`, `_3`) cuando ya existe un documento
con el mismo nombre para el mismo expediente (ej: segundo requerimiento de subsanacion).
Pendiente de definir mecanismo exacto.

### Cabo 4: ~~Filtrado dinamico de tokens por contexto ESFTT~~ — CERRADO

Resuelto en sesion 3 (ver seccion "Decisiones sesion 2", actualizada).
- Cadena completa E→S→F→T con 3 tablas whitelist
- Tipos de solicitud combinados como entidades propias en `tipos_solicitudes`
- Principio de escape como principio transversal

### Cabo 5: ~~Nota sobre dependencias del #189~~ — CERRADO

El issue #189 (cerrado) dice `python-docx-template` como dependencia, pero el paquete
real es `docxtpl`. El commit 6b85fcf anadio correctamente las tres dependencias:
`docxtpl==0.20.2`, `python-docx==1.2.0`, `lxml==6.0.2`. El codigo es correcto;
solo el texto del issue tiene la discrepancia. No requiere accion.

### Cabo 6: Actualizar documentacion tras ejecutar migraciones — PENDIENTE (no bloqueante)

Al ejecutar las migraciones derivadas de este analisis, actualizar los .md que
referencian nombres antiguos. **No antes** — el codigo aun usa los nombres actuales.

| Fichero | Conceptos a actualizar |
|---|---|
| `docs/fuentesIA/GUIA_CONTEXT_BUILDERS.md` | `campos_catalogo`, `tipos_escritos`, ejemplo de migracion INSERT |
| `docs/fuentesIA/ARQUITECTURA_DOCUMENTOS.md` | `campos_catalogo`, `tipos_escritos` |
| `docs/fuentesIA/ROADMAP.md` | `tipos_escritos` |
| Issue #189 (cuerpo) | Estructura `tipos_escritos` obsoleta (renombrar a `plantillas`, eliminar `campos_catalogo`, anadir `tipo_expediente_id`, campo `variante`) |

---

## Proximos pasos

**Puntos 1-4 completados.** Cabos 1-5 cerrados. Cabo 6 diferido a Fase 2.

Pendiente (analisis tecnico pre-implementacion, sin intervencion del usuario):
1. ~~Completar punto 1) Mapa de necesidades~~ — HECHO
2. ~~Completar punto 2) Dependencias con otros modulos~~ — HECHO
3. ~~Completar punto 3) Riesgos e inconsistencias~~ — HECHO
4. ~~Completar punto 4) Orden logico de decisiones de diseno~~ — HECHO
5. Completar punto 5) Preguntas sin respuesta
6. Al ejecutar migraciones: actualizar documentacion (Cabo 6)
7. Solo entonces: tocar codigo

---

## Anexos

Comentarios literales del usuario de las sesiones 1 y 2 (2026-03-15):
ver `docs/fuentesIA/ANALISIS_167_GENERACION_ESCRITOS_ANEXOS.md`
