# docs/fuentesIA — Índice de documentos

Documentación técnica y de diseño para uso del desarrollador y de Claude Code.
Los documentos marcados con ⚠️ deben leerse antes de actuar en su área.

---

## Reglas y workflow

| Documento | Contenido |
|---|---|
| ⚠️ `REGLAS_DESARROLLO.md` | Workflow Git, commits, ramas, migraciones. Leer siempre. |
| ⚠️ `REGLAS_ARQUITECTURA.md` | Flujo de decisiones arquitectónicas, reglas del JSON, sincronización documental. Borrador — pendiente sesión dedicada (#250). |
| `REGLAS_BASH.md` | Patrones prohibidos en Bash y workarounds. |

---

## Arquitectura general

| Documento | Contenido |
|---|---|
| ⚠️ `GUIA_GENERAL.md` | Arquitectura general y lógica de negocio. Visión de conjunto. |
| `DISEÑO_SUBSISTEMA_DOCUMENTAL.md` | Pool documental: tipos, vías de entrada, decisiones de modelo. |
| `DISEÑO_MOTOR_REGLAS.md` | Arquitectura del motor de reglas ESFTT. |
| `MOTOR_REGLAS_investigacion_legislativa.md` | Base legislativa del motor de reglas. |
| ⚠️ `Estructura_fases_tramites_tareas.json` | Estructura ESFTT: fases, trámites, tareas y patrones. Fuente de verdad estructural. Versión actual: 5.4 — pendiente actualización a 5.5 (#248). |

---

## Diseño de fases y subsistemas

| Documento | Contenido | Issue |
|---|---|---|
| `DISEÑO_ANALISIS_SOLICITUD.md` | Fase ANÁLISIS_SOLICITUD, checklist documental, INCORPORAR multi-doc, catálogo de requerimientos. | #248 |
| `DISEÑO_CONSULTAS_ORGANISMOS.md` | Fase consultas a organismos y análisis técnico. | #247 |
| `DISEÑO_DIAGRAMAS_ESFTT.md` | Diagramas de flujo ESFTT por capas (Mermaid). Bloqueado hasta #250. | #249 |

---

## Guías técnicas

| Documento | Contenido |
|---|---|
| `GUIA_CONTEXT_BUILDERS.md` | Context builders para generación de escritos: rol, estructura, relación con renderizador. |

---

## Análisis históricos — Issue #167 (generación de escritos)

Serie de análisis previos a la implementación del subsistema documental. Referencia histórica.

| Documento | Contenido |
|---|---|
| `ANALISIS_167_INDICE.md` | Índice de la serie |
| `ANALISIS_167_PUNTO_1_NECESIDADES.md` | Necesidades del subsistema |
| `ANALISIS_167_PUNTO_2_DEPENDENCIAS.md` | Dependencias identificadas |
| `ANALISIS_167_PUNTO_3_RIESGOS.md` | Riesgos |
| `ANALISIS_167_PUNTO_4_FASES.md` | Fases de implementación |
| `ANALISIS_167_PUNTO_5_PREGUNTAS.md` | Preguntas abiertas |
| `ANALISIS_167_GENERACION_ESCRITOS_ANEXOS.md` | Generación de escritos y anexos |

---

## Estudios y planificación

| Documento | Contenido |
|---|---|
| `PLAN_ESTRATEGIA.md` | Estrategia general del proyecto |
| `PLAN_ROADMAP.md` | Roadmap de funcionalidades |
| `ANALISIS_HOMOGENEIZACION_UI.md` | Estudio de homogeneización de la interfaz |
| `ANALISIS_TAREAS_INVERSO.md` | Análisis inverso de tareas |
| `numero_at_gapless.md` | Numeración AT sin huecos |
| `GUIA_ROLES.md` | Roles de usuario en el sistema |

---

## Referencias normativas

Directorio `referencias/`:

| Documento | Contenido |
|---|---|
| `Mapa Normativo AT Andalucia.md` | Mapa normativo de instalaciones AT en Andalucía |
| `Clasificacion AT Andalucia.md` | Clasificación de instalaciones AT |
| `Clasificacion AT Capa2.md` | Clasificación AT capa 2 |
