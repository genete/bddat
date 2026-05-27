# Análisis de estado BDDAT — mayo 2026

> **Tipo:** Snapshot de situación. Congelado en la fecha de creación.
> **Fecha original:** 2026-05-13 — **Actualizado:** 2026-05-16
> **Alcance:** Código en rama `develop` + issues cerrados entre 13/05 y 16/05.
> **Método:** Lectura directa del código (modelos, servicios, rutas, templates) cruzada con issues abiertos.
> **Documento hermano:** `REVISION_VALIDEZ_ISSUES_MAYO_2026.md` — dictamen de validez issue a issue
> (cuáles están obsoletos, requieren rediseño o están ya implementados). Consultarlo antes de
> planificar cualquier issue listado en la sección 5.

---

## 1. Imagen general

El proyecto está más avanzado de lo que sugiere el historial de issues cerrados. El core técnico (motor de reglas, plazos, generador de escritos, API de tramitación BC) es sólido y bien integrado. Lo que falta tiende a ser: datos de catálogo configurados normativamente, partes específicas de UI de segundo orden, e infraestructura de despliegue.

**Desde el 13/05** se cerraron los issues #391–#394 (4 Context Builders nuevos), #395 (seed organismos_consulta), #386 (semáforos de plazo BC — era el hueco de mayor gravedad identificado el 13/05) y el ADR-007 elimina definitivamente las whitelists E-S-F-T junto con los verbos INICIAR/FINALIZAR del motor (#387).

---

## 2. Estado por área

### ÁREA 1 — Tramitación ESFTT (Bloque 1, M1)

**Implementado:**
- Modelos completos: Expediente, Solicitud, Fase, Trámite, Tarea con relaciones bidireccionales
- API BC completa (`api_bc.py`): crear, editar, borrar para los 5 niveles ESFTT, integrado con motor de reglas e invariantes
- Vistas BC (5 niveles) con templates HTML
- Wizard de alta de expediente (3 pasos)
- El estado de tarea/trámite/fase es **deducido** del árbol documental (sin campo estado explícito, por diseño ADR-002); las acciones de validación son por `editar_tarea`/`editar_fase`
- **[NUEVO 16/05]** ADR-007: eliminadas whitelists E-S-F-T y verbos INICIAR/FINALIZAR del motor (#387). El motor ya no valida relaciones de tipo entre niveles — la lógica de qué tipos son válidos pasa a ser responsabilidad de la UI/formularios.

**Pendiente:**
- Tareas multi-documento: cada tarea solo admite un documento_usado y uno documento_producido; extender está pendiente (#376, sin milestone)

### ÁREA 2 — Sistema documental (Bloque 2, M1)

**Implementado:**
- Pool documental: listado, registro desde filesystem, URLs externas, descarga, edición de metadatos, borrado condicionado a referencias activas
- Explorador de filesystem integrado con protección path traversal
- Asociación documento↔tarea (documento_usado_id, documento_producido_id en la edición de tarea)

**Pendiente:**
- Sin selector funcional de tipo de documento en la UI al registrar (#379, M4)
- Flujo de asociación fragmentado: subir al pool → ir a la tarea → asignar; sin posibilidad de hacerlo en un solo gesto (#367, M3)
- Tabla `documentos_tarea` (multi-documento) con diseño abierto (#380, M3)

### ÁREA 3 — Generación de escritos (Bloque 3, M2)

**Implementado:**
- Servicio generador completo (docxtpl + corrección de párrafos anidados en cabeceras/pies, ZIP parcheado)
- Capa 1 de contexto (`ContextoBaseExpediente`)
- CRUD de plantillas para Supervisor con explorador de ficheros
- Consultas nombradas como contexto dinámico
- Fragmentos reutilizables (`{{r Nombre}}`)
- API de escritos (`api_escritos.py`) para generar desde la vista de tarea
- **[NUEVO 16/05]** Context Builders (Capa 2) — paquete `app/services/context_builders/` estructurado (#289):
  - `ContextoConsultaSeparata` (#391) — consulta a organismo + `OrganismoExpediente`
  - `ContextoAnalisisDocumental` (#392) — análisis documental + modelo `Diagnostico`
  - `ContextoRecepcionAlegacion` (#393) — recepción de alegación + modelo `Alegante`
  - `ContextoAnalisisAlegaciones` (#394) — análisis de alegaciones
  - Seed `organismos_consulta` en ConsultaNombrada (#395)

**Pendiente:**
- Bug en resolución de dirección de notificación del titular (#300, M2)
- Logotipo de la Junta enlazado en lugar de incrustado (#297, M2) — afecta a documentos oficiales
- CBs pendientes de implementar: tipos de escrito para fases de resolución (RES), información pública (IP), subsanación — sin issues creados aún
- `ContextoAnalisisDocumental` marcado como "Bloqueado" en la guía (tabla `diagnosticos` diseñada pero pendiente de validar integración)

### ÁREA 4 — Motor de reglas (Bloque 4, M3)

**Implementado:**
- Motor agnóstico completo: sujeto con wildcards ANY, condiciones AND, excepciones, prioridades
- `evaluar()` y `auditar()` (para certificados)
- ContextAssembler compilando variables desde el árbol ESFTT
- Variable `tipo_sujeto_solicitado` añadida al catálogo (#388)
- **[NUEVO 16/05]** Eliminadas whitelists E-S-F-T y verbos INICIAR/FINALIZAR del motor (ADR-007, #387). Motor simplificado.

**Pendiente:**
- Las reglas en BD son mínimas o inexistentes — el motor dice PERMITIDO sin reglas configuradas (intencionado: arranque en modo suave)
- Sin UI de CRUD de reglas para el Supervisor (#170, M3)
- Sin switch de modo global INACTIVO/SOLO_ADVERTIR/BLOQUEAR (#323, M3)

### ÁREA 5 — Plazos (Bloque 5, M3)

**Implementado:**
- Cálculo completo art. 30 LPACAP: días hábiles, naturales, meses y años
- Suspensiones inferidas del árbol documental (art. 22 LPACAP) — sin tabla propia (#173)
- Catálogo de plazos en BD con condiciones
- Integrado en el servicio de seguimiento (pistas PENDIENTE_PLAZOS, PENDIENTE_SUBSANAR)
- CLI de importación de inhábiles + banner de alerta en el header para admins (#339)
- **[NUEVO 16/05]** Semáforos de plazo en vistas BC de tarea y fase (#386) — era el hueco de mayor gravedad identificado el 13/05

**Pendiente:**
- Tarea ESPERAR_PLAZO sin mecanismo de cierre formal (#357, M3)
- Sin UI de gestión del catálogo de plazos (sin issue específico)

### ÁREA 6 — Listado inteligente y seguimiento (Bloque 10, M2)

**Implementado:**
- Listado V2 con scroll infinito, filtros básicos (búsqueda, responsable, tipo de expediente)
- Vista de seguimiento con pistas de estado por tipo de fase (SOL, CONSULTAS, MA, IP, RES)
- Servicio de seguimiento con algoritmo de prioridad (8 estados, escalado jerárquico)
- API de seguimiento

**Pendiente:**
- Diagrama de tramitación (ReactFlow) no integrado con datos reales (#320, M2)
- Vista de auditoría por técnico/pista (#256, M2)
- Campo tecnología en Proyecto para filtro (#279, M2)
- Sin cola de trabajo priorizada visible por tramitador

### ÁREA 7 — Configuración de tablas maestras para Supervisor (Bloque 8, M3)

**Implementado:**
- CRUD de usuarios (con validaciones de seguridad: no autodesactivación, no quitar último ADMIN)
- CRUD de plantillas de escritos
- Días inhábiles: CLI (`flask inhabiles importar`) + banner de aviso (#339)

**Pendiente:**
- Sin CRUD web de tipos ESFTT (#171, M3)
- Sin CRUD de reglas del motor (#170, M3)
- Sin CRUD de catálogo de plazos (sin issue)
- ~~Sin CRUD de tablas de whitelist ESFTT~~ — **eliminadas por ADR-007**

### ÁREA 8 — Gestión de carga y usuarios (Bloque 9, M2)

**Implementado:**
- CRUD de usuarios completo
- El responsable del expediente se puede cambiar desde la edición del expediente (uno a uno)

**Pendiente:**
- Sin vista de asignación de carga masiva (Supervisor distribuye expedientes)
- Sin estadísticas de carga por técnico
- Sin exportación de datos (#76, M5)

### ÁREA 9 — Infraestructura de producción (M4)

Sin tocar en su totalidad: `SECRET_KEY` (#45), HTTPS (#177), backup (#178), ENS (#176), infraestructura definida (#151), importación legacy (#105, #175), base de `numero_at` (#120), CI/tests (#332, #317).

### ÁREA 10 — Proyectos e instalaciones (Bloque 6, M3-M5)

- Modelo básico implementado (título, descripción, finalidad, emplazamiento, municipios, tipo IA)
- Sin elementos técnicos anidados (líneas AT, CT, subestaciones) — sin issue ni diseño
- GIS (#27, M5)

---

## 3. Huecos no cubiertos por ningún issue abierto

| Hueco | Gravedad para MVP | Observación |
|---|---|---|
| ~~Semáforos de plazo en la vista BC~~ | ~~Alta~~ | **RESUELTO — #386 cerrado el 15/05** |
| CBs de fases RES, IP, subsanación | Alta | El sistema solo tiene CBs para consultas y alegaciones. Sin CBs no hay escritos específicos para resolución e información pública. Sin issues. |
| UI de configuración del catálogo de plazos | Media | El Supervisor solo puede configurarlo directamente en BD. Sin UI ni issue. |
| Asignación masiva de expedientes por Supervisor | Media | Solo se puede hacer uno a uno desde la edición del expediente. Sin vista dedicada ni issue. |
| Elementos técnicos del proyecto (líneas, CT, subestaciones) | Baja (M3+) | Sin diseño ni issue. Necesario para Proyectos e instalaciones avanzado. |
| `titular_direccion` en escritos (#300) | Media | Bug conocido pero sin solución aún. Afecta todos los escritos generados. |

---

## 4. Issues cuya posición en el roadmap merece revisión

| Issue | Milestone actual | Posible reclasificación | Motivo |
|---|---|---|---|
| #300 — Bug dirección titular en escritos | M2 | — | Sigue pendiente; afecta todos los documentos |
| #297 — Logotipo incrustado | M2 | — | Sigue pendiente; afecta documentos oficiales |
| #379 — Tipos documentos en UI | M4 | M2 | Sin tipos seleccionables, la gestión documental queda incompleta desde el primer día |
| #376 — UI multi-documento | sin milestone | M3 | Relacionado con tipos de tarea; necesita clasificarse |
| #374 — Tabla interesados | sin milestone | diseño previo + M3 | Modelo de datos que puede afectar la arquitectura de ESFTT |
| #344 — SETUP_PC desactualizado | sin milestone | M4 | Afecta a la reproducción del entorno de desarrollo |

---

## 5. Tareas de backend y migración pendientes (sin UI) — inventario completo

> Esta sección se añade el 16/05 para orientar las próximas sesiones hacia trabajo
> de backend puro antes de abordar nuevas vistas.
> Fuente: listado completo de issues abiertos en GitHub a 16/05/2026.

### Grupo A — Context Builders restantes (sin issue abierto aún)

Continuación natural de #289. Cada CB es una sesión: modelo + migración + CB + tests.

| CB pendiente | Trámite / fase | Datos nuevos previsibles |
|---|---|---|
| `ContextoNotificacionOrganismo` | CONSULTAS — notificación | Organismo, plazo legal, fecha límite — ejemplo ya en GUIA_CONTEXT_BUILDERS |
| `ContextoResolucion` | RES | Campos de acuerdo/denegación |
| `ContextoInformacionPublica` | IP | Fechas publicación, BOE/BOJA, período de exposición |
| `ContextoSubsanacion` | SOL — subsanación | Requerimientos, plazo concedido |

### Grupo B — Bugs M2 sin tocar

| Issue | Descripción |
|---|---|
| #300 | ContextoBaseExpediente: dirección de notificación del titular resuelta incorrectamente |
| #297 | Logotipo de la Junta enlazado en lugar de incrustado (cambio en el generador) |

### Grupo C — Diseño pendiente de ADR / decisión técnica (M3)

Estos no se pueden implementar hasta tener el diseño acordado. Son bloqueantes para lo que viene después.

| Issue | Descripción |
|---|---|
| #362 | ESPERAR_PLAZO: certificado de plazo cumplido como documento_producido_id |
| #364 | PUBLICAR vs NOTIFICAR: distinción BOE/BOP/BOJA/prensa vs destinatario identificado |
| #365 | Extender documentos.url a URI de BD para decisiones de ANALIZAR |
| #366 | Eliminar trámite AUDIENCIA de COMPATIBILIDAD_AMBIENTAL (duplicado de RECEPCION_INFORME) |
| #380 | Decidir destino de tabla documentos_tarea tras eliminar INCORPORAR |
| #247 | Diseño completo de la fase de consultas a organismos y análisis técnico |
| #248 | Diseño de la fase ANÁLISIS_SOLICITUD: checklist documental e ítems de requerimiento |
| #374 | Diseño de tabla de interesados y trámite REGISTRO_INTERESADOS (sin milestone) |

### Grupo D — Seeds y migraciones de catálogo (M3, pure backend)

No requieren UI. Desbloquean el funcionamiento real del sistema.

| Issue | Descripción |
|---|---|
| #377 | Seed de tipos_documentos del catálogo ESFTT (migración Alembic) |
| #378 | Seed de tipos_documentos_resultados_validos por tipo de notificación |
| #276 | Poblar tipos_solicitudes_compatibles con el técnico del servicio |
| — | Añadir reglas reales al motor (actualmente vacío → siempre PERMITIDO) |
| — | Completar datos normativos en catálogo de plazos |

### Grupo E — Motor de reglas y servicios M3 (pure backend)

| Issue | Descripción |
|---|---|
| #323 | Motor: modo global INACTIVO / SOLO_ADVERTIR / BLOQUEAR |
| #357 | ESPERAR_PLAZO: mecanismo de cierre formal (tarea huérfana de invariante documental) |
| #324 | Motor: mecanismo de escape con justificación y bitácora (DB + lógica) |
| #192 | Modelo: requisitos documentales por procedimiento (documentos_procedimiento) |
| #318 | Tipos combinados: regla del tipo más restrictivo al poblar metadatos_fechas y motor |

### Grupo F — Modelos y diseño de datos (M3, sin milestone)

| Issue | Descripción |
|---|---|
| #376 | Generalizar multi-documento a todos los tipos de tarea que lo necesitan |
| #174 | Permisos granulares por acción y expediente |

### Grupo G — Scripts y servicios avanzados (M3)

Trabajo de backend independiente, sin bloqueo de UI.

| Issue | Descripción |
|---|---|
| #304 | Script de detección del tipo de solicitud por análisis del PDF |
| #305 | Script de detección del tipo de expediente por análisis del proyecto |
| #306 | Helper de cálculo de tasa y extracción de presupuesto del proyecto |

### No clasificado como backend pero relevante (M2)

| Issue | Descripción | Nota |
|---|---|---|
| #318 | Tipos combinados: regla del tipo más restrictivo | Afecta al motor, posiblemente solo datos |
| #332 | CI: ejecutar tests en GitHub Actions | Infra, independiente del resto |

---

## 6. Síntesis actualizada (16/05)

**El motor técnico está construido.** Lo más sofisticado (motor de reglas con excepciones, plazos con suspensiones art. 22, generador de escritos con subdocs, seguimiento con pistas) está implementado y bien integrado entre sí. El ADR-007 simplificó el motor eliminando la complejidad de las whitelists.

**Avances significativos desde el 13/05:**
- Semáforo de plazo en vistas BC resuelto (era el hueco de mayor gravedad para el tramitador)
- 4 Context Builders nuevos — los más complejos (organismos, alegaciones) ya están
- Modelo de datos enriquecido: `OrganismoExpediente`, `Diagnostico`, `Alegante`
- Motor simplificado con ADR-007

**El cuello de botella sigue siendo backend antes que UI:**
- Los CBs restantes (RES, IP, subsanación) son la prioridad natural — sin ellos el generador de escritos no sirve para los tipos de escrito más frecuentes
- Los bugs M2 (#300, #297) son simples y deberían cerrarse antes de cualquier nueva UI
- La UI pendiente (CRUD de reglas, diagrama ReactFlow, cola de trabajo) no aporta valor hasta que el backend esté completo

**Estrategia recomendada para próximas sesiones:** Grupo A (CBs) → Grupo B (bugs M2) → Grupo C (motor, M3) → UI.
