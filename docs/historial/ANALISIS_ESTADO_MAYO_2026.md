# Análisis de estado BDDAT — mayo 2026

> **Tipo:** Snapshot de situación. Congelado en la fecha de creación.
> **Fecha:** 2026-05-13
> **Alcance:** Código en rama `develop` + issues abiertos en GitHub.
> **Método:** Lectura directa del código (modelos, servicios, rutas, templates) cruzada con issues abiertos.

---

## 1. Imagen general

El proyecto está más avanzado de lo que sugiere el historial de issues cerrados. El core técnico (motor de reglas, plazos, generador de escritos, API de tramitación BC) es sólido y bien integrado. Lo que falta tiende a ser: datos de catálogo configurados normativamente, partes específicas de UI de segundo orden, e infraestructura de despliegue.

---

## 2. Estado por área

### ÁREA 1 — Tramitación ESFTT (Bloque 1, M1)

**Implementado:**
- Modelos completos: Expediente, Solicitud, Fase, Trámite, Tarea con relaciones bidireccionales
- API BC completa (`api_bc.py`): crear, editar, borrar e iniciar/finalizar para los 5 niveles ESFTT, integrado con motor de reglas e invariantes
- Vistas BC (5 niveles) con templates HTML
- Wizard de alta de expediente (3 pasos)
- El estado de tarea/trámite/fase es **deducido** del árbol documental (sin campo estado explícito, por diseño ADR-002); las acciones iniciar/finalizar son validaciones, la mutación real es por `editar_tarea`/`editar_fase`

**Pendiente:**
- Las whitelists de relación E→S, S→F, F→T no están completas normativamente en BD: sin esos datos el tramitador no sabe qué tipos de fase puede crear en qué tipo de solicitud (#360, #335 — M3)
- Tareas multi-documento: cada tarea solo admite un documento_usado y uno documento_producido; extender está pendiente (#376, sin milestone)

### ÁREA 2 — Sistema documental (Bloque 2, M1)

**Implementado:**
- Pool documental: listado, registro desde filesystem, URLs externas, descarga, edición de metadatos, borrado condicionado a referencias activas
- Explorador de filesystem integrado con protección path traversal
- Asociación documento↔tarea (documento_usado_id, documento_producido_id en la edición de tarea)

**Pendiente:**
- Sin selector funcional de tipo de documento en la UI al registrar (#379, M4 — posiblemente mal clasificado)
- Flujo de asociación fragmentado: subir al pool → ir a la tarea → asignar; sin posibilidad de hacerlo en un solo gesto (#367, M3)
- Tabla `documentos_tarea` (multi-documento) con diseño abierto sin destino claro tras eliminar INCORPORAR (#380, M3)

### ÁREA 3 — Generación de escritos (Bloque 3, M2)

**Implementado:**
- Servicio generador completo (docxtpl + corrección de párrafos anidados en cabeceras/pies, ZIP parcheado)
- Capa 1 de contexto (ContextoBaseExpediente)
- CRUD de plantillas para Supervisor con explorador de ficheros
- Consultas nombradas como contexto dinámico
- Fragmentos reutilizables (`{{r Nombre}}`)
- API de escritos (`api_escritos.py`) para generar desde la vista de tarea

**Pendiente:**
- **Context Builders (Capa 2)** no implementados (#289, M2) — sin ellos las plantillas solo usan datos genéricos del expediente, no los específicos por tipo de solicitud/fase/trámite
- Bug en resolución de dirección de notificación del titular (#300, M2)
- Logotipo de la Junta enlazado en lugar de incrustado (#297, M2) — afecta a documentos oficiales

### ÁREA 4 — Motor de reglas (Bloque 4, M3)

**Implementado:**
- Motor agnóstico completo: sujeto con wildcards ANY, condiciones AND, excepciones, prioridades
- `evaluar()` y `auditar()` (para certificados)
- ContextAssembler compilando variables desde el árbol ESFTT
- Integrado en la API BC en todas las acciones CREAR/INICIAR/FINALIZAR/BORRAR

**Pendiente:**
- Las reglas en BD son mínimas o inexistentes — el motor dice PERMITIDO sin reglas configuradas (intencionado: arranque en modo suave)
- Sin UI de CRUD de reglas para el Supervisor (#170, M3)
- Sin switch de modo global INACTIVO/SOLO_ADVERTIR/BLOQUEAR (#323, M3)

### ÁREA 5 — Plazos (Bloque 5, M3)

**Implementado:**
- Cálculo completo art. 30 LPACAP: días hábiles, naturales, meses y años
- Suspensiones inferidas del árbol documental (art. 22 LPACAP) — sin tabla propia
- Catálogo de plazos en BD con condiciones
- Integrado en el servicio de seguimiento (pistas PENDIENTE_PLAZOS, PENDIENTE_SUBSANAR)
- CLI de importación de inhábiles; alerta de calendario en el header para admins

**Pendiente:**
- Sin semáforos en la vista BC de tramitación — el estado de plazo no es visible al tramitar, solo en el listado de seguimiento
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
- Días inhábiles: CLI (`flask inhabiles importar`), sin UI web

**Pendiente:**
- Sin CRUD web de tipos ESFTT (#171, M3)
- Sin CRUD de reglas del motor (#170, M3)
- Sin CRUD de catálogo de plazos (sin issue)
- Sin CRUD de tablas de whitelist ESFTT (expedientes_solicitudes, solicitudes_fases, fases_tramites)

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
| Semáforos de plazo en la vista BC | Alta | El #74 (M5) solo cubre el dashboard. El tramitador trabajando en una tarea no ve el estado de plazo de su fase. |
| UI de configuración del catálogo de plazos | Media | El Supervisor solo puede configurarlo directamente en BD. Sin UI ni issue. |
| Asignación masiva de expedientes por Supervisor | Media | Solo se puede hacer uno a uno desde la edición del expediente. Sin vista dedicada ni issue. |
| Elementos técnicos del proyecto (líneas, CT, subestaciones) | Baja (M3+) | Sin diseño ni issue. Necesario para Proyectos e instalaciones avanzado. |

---

## 4. Issues cuya posición en el roadmap merece revisión

| Issue | Milestone actual | Posible reclasificación | Motivo |
|---|---|---|---|
| #379 — Tipos documentos en UI | M4 | M2 | Sin tipos de documento seleccionables, la gestión documental queda incompleta desde el primer día |
| #74 — Semáforos en dashboard | M5 | M2 | Los plazos son información operativa diaria del tramitador |
| #376 — UI multi-documento | sin milestone | M3 | Relacionado con tipos de tarea; necesita clasificarse |
| #374 — Tabla interesados | sin milestone | diseño previo + M3 | Modelo de datos que puede afectar la arquitectura de ESFTT |
| #344 — SETUP_PC desactualizado | sin milestone | M4 | Afecta a la reproducción del entorno de desarrollo |

---

## 5. Síntesis

**El motor técnico está construido.** Lo más sofisticado (motor de reglas con excepciones, plazos con suspensiones, generador de escritos con subdocs, seguimiento con pistas) está implementado y bien integrado entre sí.

**El cuello de botella para producción mínima es de datos y UI de segundo orden:**
- Las whitelists normativas ESFTT (qué tipos de solicitud/fase/trámite son válidos en cada contexto) están en BD pero incompletas normativamente.
- Varios issues M2 críticos para la usabilidad real (Context Builders, diagrama de tramitación, semáforos de plazo) están a medias.
- La infraestructura de producción (M4) está sin tocar.

**El camino más corto a producción mínima:** completar datos de catálogo ESFTT → resolver issues M2 críticos (CB Capa 2, dirección, logotipo) → preparar infraestructura M4 → importación legacy.
