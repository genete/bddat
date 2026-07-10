# Análisis: traslado de diagnóstico ANALIZAR → ELABORAR vía Context Builders

**Fecha:** 2026-07-10
**Estado:** Snapshot estático. No es referencia activa — no describe cómo debe
construirse nada nuevo, documenta lo que ya existe y por qué es correcto.
**Propósito:** Cerrar el hueco de definición de `docs/CONTEXTO_ACTUAL.md`
(ADR-031 §7 punto 4): ¿tienen los trámites con tarea ELABORAR su Context
Builder (CB) correctamente enganchado al diagnóstico que produce la tarea
ANALIZAR, cuando corresponde? Precedente: `ContextoSubsanacion` leía
`tarea.requerimientos` (borrador del shuttle) en vez del documento de salida
real — bug #406, corregido en #440.

---

## Índice

1. [Método](#1-método)
2. [Taxonomía ANCLAJE de los 10 CB](#2-taxonomía-anclaje-de-los-10-cb)
3. [Dónde sí aplica el patrón: ANÁLISIS_DOCUMENTAL → REQUERIMIENTO_SUBSANACIÓN](#3-dónde-sí-aplica-el-patrón-análisis_documental--requerimiento_subsanación)
4. [Dónde no aplica: cadena CONSULTA_SEPARATA → TRASLADO_TITULAR → TRASLADO_ORGANISMO](#4-dónde-no-aplica-cadena-consulta_separata--traslado_titular--traslado_organismo)
5. [Confirmación del diseño (Carlos)](#5-confirmación-del-diseño-carlos)
6. [Resto de trámites con ANALIZAR](#6-resto-de-trámites-con-analizar)
7. [Notas laterales (no accionables)](#7-notas-laterales-no-accionables)
8. [Conclusión](#8-conclusión)

---

## 1. Método

- Catálogo de trámites/tareas: `docs/referencia/ESTRUCTURA_FTT.json` (fuente
  de verdad).
- Lectura completa de los 10 CB en `app/services/context_builders/`.
- Lectura de `app/models/diagnosticos.py`, `app/services/diagnosticos.py`,
  `app/routes/api_expedientes.py` (endpoint que completa ANALIZAR),
  `app/models/organismos_expediente.py`, `app/models/tramites_organismos.py`.
- `docs/referencia/GUIA_CONTEXT_BUILDERS.md`, ADR-025, migración 346.

## 2. Taxonomía ANCLAJE de los 10 CB

ADR-025 §4 distingue dos formas de anclaje. Clasificación derivada leyendo el
código (mecánica, sin ambigüedad en ningún caso):

| CB | Ancla real (código) | ANCLAJE |
|---|---|---|
| `ContextoConsultaTrasladoOrganismo` | `TramiteOrganismo.filter_by(tramite_id=self._tarea.tramite_id)` | auto_tramite |
| `ContextoConsultaSeparata` | ídem | auto_tramite |
| `ContextoConsultaTrasladoTitular` | ídem | auto_tramite |
| `ContextoNotificacionOrganismo` | ídem | auto_tramite |
| `ContextoRecepcionAlegacion` | `self._tarea.tramite.alegante` | auto_tramite |
| `ContextoAnalisisDocumental` | `self._tarea.tramite.tareas` (su propio ANALIZAR) | auto_tramite |
| `ContextoAnalisisAlegaciones` | `tarea.tramite.fase.solicitud` → agrega todas las fases | scoped |
| `ContextoResolucion` | `tarea.tramite.fase` → `resultado_fase`/`resolucion` | scoped |
| `ContextoInformacionPublica` | `tarea.tramite.fase` → `informacion_publica` | scoped |
| `ContextoSubsanacion` | `tarea.tramite.fase` → trámite anterior en la fase (#440) | scoped |

Esta tabla es también el contenido base del issue #607 (formalizar `ANCLAJE`
como atributo de clase + corregir huecos de `GUIA_CONTEXT_BUILDERS.md`).

## 3. Dónde sí aplica el patrón: ANÁLISIS_DOCUMENTAL → REQUERIMIENTO_SUBSANACIÓN

`ContextoSubsanacion.get_contexto()` navega a `tarea.tramite.fase`, busca el
trámite anterior por id dentro de la misma fase, localiza su tarea ANALIZAR y
lee `documento_producido.diagnostico.as_contexto_cb()` — la salida real, ya
consolidada. Expone `requerimientos` (lista de defectos con texto y orden)
como token. Correcto desde #440.

Es el **único** caso en los 10 CB donde un ELABORAR necesita — y consigue —
la sustancia textual (`defectos`) de un `Diagnostico` producido por un
ANALIZAR de otro trámite.

## 4. Dónde no aplica: cadena CONSULTA_SEPARATA → TRASLADO_TITULAR → TRASLADO_ORGANISMO

Hipótesis inicial de este análisis (descartada, ver §5): que estos tres CB
deberían replicar el patrón de `ContextoSubsanacion`, leyendo el
`Diagnostico` del ANALIZAR anterior. Evidencia reunida antes de descartarla:

- **Captura:** `app/routes/api_expedientes.py:46-50` distingue dos grupos de
  trámites con ANALIZAR:
  ```python
  # Trámites cuya tarea ANALIZAR lleva las secciones extendidas del contenedor
  # (#442: check documental #495, check técnico #581, requerimientos #440).
  # El resto de trámites cuya tarea ANALIZAR produce un DIAGNOSTICO (CONSULTA_SEPARATA,
  # AUDIENCIA...) solo necesita el núcleo común (resultado + producir documento).
  _TRAMITES_CON_SECCIONES_ANALISIS = {'ANALISIS_DOCUMENTAL', 'REQUERIMIENTO_SUBSANACION'}
  ```
  Para CONSULTA_SEPARATA y las dos consultas de traslado, completar ANALIZAR
  solo captura `resultado` (favorable/condicionado/desfavorable) vía
  `POST .../tarea/<id>/analizar`. `defectos` llega vacío (viene de
  `consolidar_defectos()`, el checklist de #442, no aplicable aquí).

- **Reenvío:** los tres CB llaman a `OrganismoExpediente.as_contexto_cb()`
  (`app/models/organismos_expediente.py:126-133`), que expone:
  ```python
  'organismo_resultado': self.estado,  # estado interno del motor; no usar en plantillas de escritos
  ```
  Ninguno de los tres lee el `Diagnostico` del trámite anterior.

Por sí sola esta evidencia parecía un hallazgo — el propio código marca ese
campo como "no usar en plantillas de escritos" y es lo único que se usa. Pero
ver §5: no es un bug, es la ausencia deliberada de necesidad.

## 5. Confirmación del diseño (Carlos)

El traslado de lo dicho por una parte (organismo o titular) a la otra **no se
hace resumiendo vía CB/tokens**: se hace trasladando el **documento recibido
en bruto**, sin digerir, como documento consumido/notificado. Mecanismo:
tabla `tramites_tareas_documentos` (migración 346, "mapa semántico de
documentos por tarea"), que formaliza qué documento consume cada tarea de
cada trámite — p. ej. el comentario en `ContextoConsultaTrasladoOrganismo`:
*"Respuesta del titular: primer doc consumido por ELABORAR (obligatorio en
migración 346)"*.

`Diagnostico.resultado` (favorable/condicionado/desfavorable) sí se produce
siempre (ADR-010 lo exige), y queda disponible pero no es necesario aquí: su
consumidor real es el motor, para decidir si el ciclo organismo↔titular
continúa o cierra — no el contenido del escrito. Podría usarse en el futuro
como token adicional (traducido a lenguaje administrativo, bien
posicionado en la plantilla) pero no es un hueco, es una posibilidad abierta
sin necesidad actual.

**Conclusión de esta sección:** el patrón "CB del ELABORAR lee el
`Diagnostico` del ANALIZAR anterior" es dominio exclusivo de
ANÁLISIS_DOCUMENTAL → REQUERIMIENTO_SUBSANACIÓN. Ningún otro trámite del
catálogo lo necesita estructuralmente.

## 6. Resto de trámites con ANALIZAR

Revisados contra `ESTRUCTURA_FTT.json`: `RECEPCION_INFORME` (CONSULTA_MINISTERIO
y COMPATIBILIDAD_AMBIENTAL), `COMUNICACION_AUDIENCIA`, `RECEPCION_FIGURA`,
`RECEPCION_DICTAMEN`, `RECEPCION_PROPUESTA_INF_VINC`,
`RECEPCION_INFORME_VINCULANTE`, `REGISTRO_INTERESADOS`,
`RECEPCION_INFORME_OPERADOR`. Todos patrón A puro (solo ANALIZAR, sin
ELABORAR de traslado inmediatamente después). Su diagnóstico dirige al motor
(bloquear/continuar/archivar), no alimenta un escrito que deba citarlo — no
presentan el mismo patrón a auditar.

Caso aparte, **ya conocido y no nuevo de esta sesión**: `ANALISIS_ALEGACIONES`
→ `RESOLUCION`. ADR-025 (Consecuencias) ya documenta que `ContextoResolucion`
"hoy solo aporta `sentido_acto` + bloques redaccionales" y que enriquecerlo
con alegaciones/consultas queda como trabajo futuro, fuera de #552/#553.

## 7. Notas laterales (no accionables)

- La BD de desarrollo conectada durante esta sesión solo tenía 5 filas en
  `plantillas` (de 10 CB implementados). Carlos confirma que no es un
  problema — la falta de fila/plantilla `.docx` es contenido pendiente de
  crear, no un defecto de código.
- `app/models/organismos_expediente.py:120` (docstring de `consulta_completa`)
  referencia "`TramiteOrganismo.resultado` disponible (#460)" como solución
  prevista. Comprobado: #460 está cerrado pero implementó otra cosa
  (variables `organismos_todos_terminados` / `organismo_supera_iteraciones`
  para el motor). El comentario quedó desactualizado — no se actúa sobre
  esto en esta sesión, queda anotado por si se retoma `organismos_expediente.py`.

## 8. Conclusión

Hueco de definición de ADR-031 §7 punto 4 cerrado. No genera issue
implementable propio — los 10 CB están correctamente enganchados donde
corresponde. Único efecto colateral: #607 (mantenimiento — formalizar
`ANCLAJE` + corregir la tabla y el estado de `ContextoAnalisisDocumental` en
`GUIA_CONTEXT_BUILDERS.md`).

---

## Referencias

- ADR-025 — `docs/decisiones/ADR-025-context-builder-ensamblador-escrito.md`
- ADR-031 — `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`
- `docs/referencia/GUIA_CONTEXT_BUILDERS.md`
- `docs/referencia/ESTRUCTURA_FTT.json`
- #406, #440 (fix de `ContextoSubsanacion`) · #607 (issue derivado de esta sesión)
- Migración `346_tramites_tareas_documentos.py`
