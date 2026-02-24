# ROADMAP — BDDAT · Visión Completa del Alcance

> **Propósito de este documento:** Definir el QUÉ completo del sistema, sin compromisos de tiempo.
> Las dependencias entre áreas y el orden de implementación se deciden por separado.
> Los detalles tácticos (subtareas, bugs) van en GitHub Issues.
>
> **Última revisión:** 2026-02-24

---

## Estado de partida (implementado a fecha de revisión)

### Implementado y operativo
- Modelos SQLAlchemy completos: Expediente, Solicitud, Fase, Trámite, Tarea, Entidad, Proyecto, Usuario + maestros
- Autenticación Flask-Login + RBAC (4 roles)
- V0 Login, V1 Dashboard, V2 Listado scroll infinito
- V4 Detalle/Edición para Expedientes y Entidades
- V3 Tramitación acordeón con carga lazy (Issue #145, ~90%)
- Edición de campos de Solicitud/Fase/Trámite/Tarea vía modales (pero no creación ni borrado)
- Wizard de creación de expedientes (3 pasos)
- API REST expedientes con paginación cursor
- Componentes JS: SelectorBusqueda, ScrollInfinito, AcordeonLazy

### Lo que NO existe todavía (nada de esto está empezado salvo mención expresa)
Ver secciones A–E a continuación.

---

## A. Tramitación — trabajo del usuario tramitador

### A.1 CRUD completo de ESFTT (Expediente / Solicitud / Fase / Trámite / Tarea)

**Estado actual:** Solo existe edición de campos básicos vía modales. No hay creación ni borrado de ningún nivel.

#### Expediente
- [ ] Borrar expediente (solo ADMIN — ver sección B.3)
- [ ] Cambio de titular (con registro en HistoricoTitularExpediente)
- [ ] Cambio de responsable/tramitador asignado
- [ ] Cambio de tipo de expediente (con validación de compatibilidad de solicitudes)

#### Solicitud
- [ ] Crear nueva solicitud sobre un expediente (con validación de estado del expediente)
- [ ] Cambiar estado: EN_TRAMITE → RESUELTA / DESISTIDA / ARCHIVADA
- [ ] Vincular solicitud_afectada_id (para desistimientos/renuncias)
- [ ] Borrar solicitud (con validación: solo si no tiene fases o están todas pendientes)

#### Fase
- [ ] Crear nueva fase sobre una solicitud (tipo seleccionable según reglas — ver A.4)
- [ ] Iniciar fase (fecha_inicio) con validaciones
- [ ] Cerrar/finalizar fase (fecha_fin + resultado_fase_id obligatorio)
- [ ] Borrar fase (solo si está pendiente y sin trámites)
- [ ] Reordenar fases (si el modelo permite múltiples de mismo tipo)

#### Trámite
- [ ] Crear nuevo trámite sobre una fase (tipo seleccionable)
- [ ] Iniciar trámite (fecha_inicio)
- [ ] Cerrar trámite (fecha_fin)
- [ ] Borrar trámite (solo si está pendiente y sin tareas)

#### Tarea
- [ ] Crear nueva tarea sobre un trámite (tipo fijo según TipoTarea: ANALISIS, REDACTAR, FIRMAR, NOTIFICAR, PUBLICAR, ESPERAR_PLAZO, INCORPORAR)
- [ ] Iniciar tarea (fecha_inicio)
- [ ] Finalizar tarea (fecha_fin + validaciones según tipo — ver A.4)
- [ ] Borrar tarea (solo si está pendiente)

**Decisión abierta:** El orden de crear las operaciones CRUD tiene dependencia crítica con A.4 (motor de estados): sin definir cuándo se puede crear un elemento no deberíamos implementar la UI de creación.

---

### A.2 Sistema documental

**Estado actual:** Los modelos tienen campos `documento_usado_id` y `documento_producido_id` en Tarea, y `documento_resultado_id` en Fase, pero no hay interfaz de gestión de documentos. La tabla `Documento` existe pero no hay forma de añadir registros.

#### Gestión básica de documentos
- [ ] Upload de documentos (formulario con fichero adjunto)
- [ ] Almacenamiento físico (decisión de arquitectura: filesystem local / S3-compatible / BD como bytea)
- [ ] Metadatos por documento: tipo, título, número de registro, fecha, remitente/destinatario
- [ ] Download / visualización (PDF en navegador o descarga)
- [ ] Borrado lógico de documento (mantener histórico)

#### Asociación de documentos a ESFTT
- [ ] Asociar documento a una tarea como documento de entrada (`documento_usado_id`)
- [ ] Asociar documento a una tarea como documento producido (`documento_producido_id`)
- [ ] Asociar documento a una fase como documento resultado (`documento_resultado_id`)
- [ ] Asociar documentos de proyecto (`DocumentoProyecto` — modelo existe, sin UI)
- [ ] Listado de documentos por expediente (vista global de toda la documentación)

#### Registro de entrada
- [ ] Número de registro de entrada/salida (integración con SIGEM o registro propio)
- [ ] Fecha y canal de presentación
- [ ] Acuse de recibo

**Decisión abierta:** ¿Almacenamiento local (filesystem del servidor) o externo (S3/MinIO)? ¿Integración con gestor documental JdA (Alfresco/Documentum)?

---

### A.3 Generación de escritos y resoluciones

**Estado actual:** No existe nada. Es el área más compleja técnicamente.

#### Gestión de plantillas
- [ ] Repositorio de plantillas de documentos (Word/ODT como base)
- [ ] Subida y versionado de plantillas por tipo de tarea / tipo de trámite
- [ ] Catálogo de variables disponibles: campos de Expediente, Solicitud, Fase, Trámite, Entidad, Proyecto...
- [ ] Editor de mapeo variable ↔ campo del sistema (sin necesidad de editar plantilla)

#### Generación de documentos
- [ ] Motor de sustitución de variables en plantilla (python-docx, Jinja2 sobre ODT, o similar)
- [ ] Generación de PDF a partir de plantilla cumplimentada (LibreOffice headless, weasyprint, etc.)
- [ ] Numeración automática de documentos (series por tipo: RESOLUCIÓN, REQUERIMIENTO, COMUNICACIÓN...)
- [ ] Preview antes de generar (renderizado borrador)
- [ ] El documento generado se asocia automáticamente a la tarea correspondiente

#### Flujo de firma y publicación
- [ ] Integración con sistema de firma electrónica (ver E.4)
- [ ] Marcado del documento como "firmado" + almacenamiento del firmado
- [ ] Generación de justificante de notificación / publicación
- [ ] Gestión de acuses de recibo de notificaciones

**Decisión abierta:** ¿Motor de plantillas Word (python-docx) u ODT (Jinja2 sobre XML)? ¿Firma electrónica integrada (@firma JdA) o firma manual en dos pasos?

---

### A.4 Motor de estados y transiciones (reglas de tramitación)

**Estado actual:** El estado de cada elemento (PENDIENTE / EN_CURSO / COMPLETADO) se deduce de si `fecha_inicio` y `fecha_fin` son NULL. No hay validaciones de transición ni reglas sobre qué se puede hacer y cuándo. Todo está "hardcodeado" (o más bien, ausente).

#### Modelo de estados
- [ ] Definir máquina de estados explícita para Solicitud, Fase, Trámite, Tarea (campo `estado` propio o calculado + transiciones)
- [ ] Reglas: una Fase no puede iniciarse si la Fase anterior obligatoria no está COMPLETADA
- [ ] Reglas: un Trámite no puede cerrarse si hay Tareas no FINALIZADAS
- [ ] Reglas: una Tarea de tipo FIRMAR no puede iniciarse sin `documento_producido_id` en la tarea REDACTAR previa
- [ ] Comportamiento educativo: no bloquear silenciosamente, sino informar qué falta (tooltips, avisos inline)

#### Tablas de configuración (configurables por Supervisor — ver B.1)
- [ ] `reglas_secuencia_fases`: para cada TipoExpediente × TipoSolicitud, qué fases son obligatorias y en qué orden
- [ ] `reglas_composicion_tramites`: para cada TipoTramite, qué tareas lo componen y en qué orden
- [ ] `reglas_documentacion`: para cada TipoTarea, qué tipo de documento se requiere como entrada/salida
- [ ] `reglas_flujo_solicitudes`: estados posibles y transiciones permitidas por TipoSolicitud

#### Inicialización automática de estructura
- [ ] Al crear una Solicitud de un tipo dado, pre-generar automáticamente la estructura de Fases/Trámites/Tareas según las reglas configuradas (o permitir hacerlo con un botón)
- [ ] Validar en creación manual que los tipos seleccionados son coherentes con las reglas

**Dependencia crítica:** A.1 (CRUD) no debería implementarse completamente sin antes tener definidas las reglas de A.4. Sin reglas, los controles de creación no pueden validar nada.

---

### A.5 Listado inteligente de expedientes con datos agregados

**Estado actual:** El listado V2 muestra datos básicos del expediente (número, tipo, titular, municipio). No hay datos calculados ni información de estado agregado.

#### Sistema de plazos
- [ ] Definir modelo de plazo: `fecha_limite` calculada por tipo de tarea/fase y fechas de inicio
- [ ] Tipos de plazo: días naturales, días hábiles, meses (con calendario de festivos)
- [ ] Plazo legal configurable por TipoFase / TipoTramite (en tablas de configuración)
- [ ] Cálculo automático de `fecha_limite` al crear/iniciar Fase o Trámite
- [ ] Campo `dias_restantes` calculado en tiempo real
- [ ] Alertas visuales: verde (a tiempo), naranja (menos de X días), rojo (vencido)

#### Datos agregados en listado
- [ ] Por expediente: número de Fases en curso, pendientes, completadas
- [ ] Por expediente: número de Tareas vencidas (fecha_limite < hoy)
- [ ] Por expediente: número de escritos pendientes de firma
- [ ] Por expediente: número de escritos pendientes de notificación
- [ ] Por expediente: número de ESPERAR_PLAZO activos y cuántos vencidos
- [ ] Por expediente: si hay alguna respuesta de administrado u organismo pendiente de incorporar

#### Columnas y filtros del listado
- [ ] Columnas configurables por usuario (mostrar/ocultar)
- [ ] Filtros: estado, tipo, titular, municipio, responsable, rango de fechas, plazo vencido (sí/no)
- [ ] Ordenación por cualquier columna
- [ ] Exportación del listado filtrado (Excel / CSV)

#### Priorización y cola de trabajo
- [ ] Vista "Mi trabajo": filtrado automático a expedientes del usuario logado con tareas activas
- [ ] Ordenación por urgencia (plazos más próximos primero)
- [ ] Indicador de "expedientes sin actividad en X días"

---

## B. Supervisor y Administrador

### B.1 Interfaz de configuración del sistema (tablas de negocio y reglas)

**Estado actual:** No existe ninguna interfaz. Los datos maestros (TipoExpediente, TipoFase, etc.) solo se gestionan directamente en BD.

#### Gestión de tablas maestras
- [ ] CRUD de TipoExpediente, TipoSolicitud, TipoFase, TipoTramite, TipoTarea
- [ ] CRUD de TipoResultadoFase
- [ ] Gestión de Municipios (actualización del catálogo municipal)
- [ ] Gestión de plantillas de documentos (ver A.3)

#### Configuración de reglas de tramitación (ver A.4)
- [ ] Editor visual de `reglas_secuencia_fases`: para cada TipoExpediente, definir qué fases y en qué orden
- [ ] Editor de `reglas_composicion_tramites`: qué tareas componen cada trámite
- [ ] Editor de `reglas_documentacion`: qué documentos requiere cada tarea
- [ ] Vista previa de la estructura resultante antes de guardar cambios

**Decisión abierta:** ¿Las reglas son editables en producción por el Supervisor sin intervención técnica? ¿Con validación previa o con efecto inmediato?

---

### B.2 Gestión de usuarios (actualización de patrones)

**Estado actual:** Interfaz funcional pero con patrones V2 antiguo, no sigue el mismo estilo que el resto del sistema.

- [ ] Rediseñar listado de usuarios siguiendo patrón V2 actual (thead sticky, scroll infinito)
- [ ] Rediseñar detalle/edición de usuario siguiendo patrón V4 (modo ver/editar, sin salto layout)
- [ ] Gestión de roles desde la misma vista V4 (asignar/quitar roles)
- [ ] Activar/desactivar usuario (borrado lógico, sin borrado real)
- [ ] Historial de último acceso

---

### B.3 Operaciones administrativas

**Estado actual:** No existe ninguna interfaz de administración.

#### Operaciones sobre expedientes
- [ ] Borrar expediente (con confirmación, auditoría y posibilidad de restauración)
- [ ] Fusionar expedientes (casos de duplicados — raro pero necesario)
- [ ] Reasignar expedientes de un tramitador a otro (cambio masivo de responsable_id)
- [ ] Exportar expediente completo (toda su estructura SFTT + documentos)

#### Operaciones sobre el sistema
- [ ] Panel de estado del sistema (espacio en disco, documentos huérfanos, tareas bloqueadas)
- [ ] Limpieza de datos: documentos sin asociar, sesiones expiradas
- [ ] Exportación masiva de datos (para backup o migración)

---

## C. Proyectos — ampliar alcance

### C.1 Estructura jerárquica de elementos eléctricos

**Estado actual:** El modelo `Proyecto` tiene solo campos descriptivos (título, descripción, municipio, referencias administrativas). No hay ninguna estructura de elementos.

El sistema necesita representar la instalación eléctrica objeto del expediente, que puede ser:

#### Tipos de instalaciones de alta tensión
- Líneas eléctricas aéreas: trazado, tensión, longitud, sección conductores, apoyos
- Líneas eléctricas subterráneas: trazado, tensión, longitud, tipo cable, profundidad
- Subestaciones de transformación: tensiones entrada/salida, potencia, equipos
- Centros de transformación: tipo (interior/intemperie/prefabricado), potencia, tensión
- Elementos de conexión y seccionamiento: interruptores, seccionadores, reactancias

#### Modelo de datos propuesto
- [ ] Nueva entidad `ElementoElectrico`: tipo, denominación, tensión nominal, potencia, características técnicas
- [ ] Relación jerárquica entre elementos (una línea tiene apoyos, una subestación tiene transformadores)
- [ ] Asociación `Proyecto` → N elementos (un proyecto puede describir varios elementos)
- [ ] Tablas maestras: `TipoElementoElectrico`, `TipoConexion`, parámetros técnicos por tipo

#### Interfaz
- [ ] Tab "Instalación" en la vista de Proyecto: árbol de elementos con CRUD
- [ ] Ficha de elemento con campos técnicos específicos por tipo (formulario dinámico)
- [ ] Relaciones entre elementos (tabla de adyacencia o similar)

**Decisión abierta:** ¿Modelo genérico de elementos con atributos dinámicos (JSON) o tablas específicas por tipo de instalación? El modelo genérico es más flexible pero más complejo de validar.

---

### C.2 Sistema de Información Geográfica (GIS)

**Estado actual:** No existe. Referenciado como Milestone 3.4 en el roadmap anterior.

#### Prerrequisitos
- C.1 debe estar definido: los elementos eléctricos son los que tienen geometría
- Decisión sobre si usar PostGIS o coordenadas simples

#### Con PostGIS
- [ ] Extensión PostGIS en PostgreSQL
- [ ] Campo `geom` en `ElementoElectrico` (punto para CT/subestaciones, línea para trazados)
- [ ] Importación de geometrías (KML, GeoJSON, shapefile)
- [ ] Exportación a KML/GeoJSON

#### Visor de mapa
- [ ] Integración Leaflet en vista de Proyecto (tab "Mapa")
- [ ] Capas: instalaciones del expediente actual + instalaciones cercanas (contexto)
- [ ] Edición de geometría en mapa (dibujo de punto/línea)
- [ ] Superposición de capas de referencia (catastro, IGN, MDT)

**Decisión abierta:** ¿PostGIS completo o almacenar coordenadas como campos numéricos simples (lat/lon)? PostGIS es más potente pero añade complejidad operacional. Para consultas espaciales (intersecciones, búsqueda por radio) PostGIS es necesario.

---

## D. Expedientes heredados (legacy)

**Estado actual:** El campo `Expediente.heredado = TRUE` existe, pero no hay ningún proceso de importación.

#### Análisis y extracción de datos legacy
- [ ] Inventario del sistema anterior (estructura, formatos, volumen de datos)
- [ ] Mapeo de campos: sistema antiguo → BDDAT (puede requerir transformaciones)
- [ ] Identificación de datos incompletos o incompatibles con el nuevo modelo

#### Proceso de importación
- [ ] Script de importación por lotes (con log de errores y aciertos)
- [ ] Validación antes de importar: datos mínimos obligatorios, FK válidas
- [ ] Importación de documentos digitalizados asociados
- [ ] Marcado automático como `heredado = TRUE`

#### Reconciliación post-importación
- [ ] Revisión manual de expedientes importados con datos incompletos
- [ ] Asignación de responsable a expedientes huérfanos
- [ ] Interfaz de búsqueda específica para expedientes heredados (posiblemente con campos extra)

**Decisión abierta:** ¿Importar solo datos estructurados o también documentos escaneados? ¿Con qué nivel de completitud mínimo se acepta un expediente heredado?

---

## E. Áreas identificadas por análisis (posiblemente no en scope inicial)

> Estas áreas no fueron mencionadas explícitamente pero emergen de analizar los requisitos anteriores.
> Requieren decisión sobre si están en scope y cuándo.

### E.1 Sistema de plazos legales (parcialmente en A.5)

Aunque se menciona en A.5, merece análisis propio porque afecta a toda la arquitectura:

- [ ] Calendario de días hábiles (festivos nacionales, autonómicos y locales)
- [ ] Configuración de plazo legal por TipoFase y TipoTramite (en días hábiles o naturales)
- [ ] Cálculo automático de `fecha_limite` al iniciar una Fase o Trámite
- [ ] Suspensión de plazos (cuando se envía requerimiento, el plazo se suspende hasta respuesta)
- [ ] Alertas proactivas (notificación al tramitador cuando quedan X días)

**Nota técnica:** La suspensión de plazos es compleja; requiere registrar eventos de suspensión/reanudación por cada Fase/Trámite.

---

### E.2 Asignación y gestión de carga de trabajo

- [ ] `responsable_id` en Expediente existe; ¿se propaga a Fase/Trámite/Tarea o se hereda?
- [ ] Interface para el Supervisor: ver expedientes por tramitador, reasignar
- [ ] Vista "carga de trabajo": cuántos expedientes y tareas activas por usuario
- [ ] Asignación directa de una Tarea específica a un usuario diferente al responsable del expediente

---

### E.3 Comunicaciones externas con administrados y organismos

La tarea NOTIFICAR implica comunicarse con el titular/terceros. ¿Cómo se registra esto?

- [ ] Registro de notificaciones enviadas (fecha, destinatario, medio, referencia)
- [ ] Canal de notificación: correo postal, sede electrónica, email
- [ ] Integración con Notific@ (plataforma JdA de notificaciones electrónicas) — decisión de alcance
- [ ] Registro de acuses de recibo y fechas de notificación efectiva

---

### E.4 Firma electrónica

La tarea FIRMAR implica que alguien firma el documento. En la Administración Pública:

- [ ] Integración con @firma (plataforma de firma de JdA / MINHAP)
- [ ] O alternativamente: flujo de firma manual en dos pasos (tramitador prepara, firmante aprueba)
- [ ] Gestión de delegaciones de firma (quién puede firmar qué tipo de documento)
- [ ] Sello de tiempo y validez del certificado

**Decisión crítica:** ¿Integración real con @firma (complejidad alta, necesaria en producción) o flujo simplificado (archivo firmado subido manualmente)? Puede implementarse en dos fases.

---

### E.5 Auditoría de cambios de estado en ESFTT

El modelo actual solo tiene `HistoricoTitularExpediente`. No hay trazabilidad del resto:

- [ ] Tabla `HistoricoEstadoSolicitud`: quién cambió el estado, cuándo, de qué a qué
- [ ] Tabla `HistoricoEstadoFase`: quién inició/cerró, fecha_inicio/fin, resultado
- [ ] Señales `before_update` en Fase y Tarea para registrar cambios de estado
- [ ] Vista de línea de tiempo por expediente (timeline de eventos)

---

### E.6 Manual de usuario y documentación técnica

- [ ] Manual de usuario final (tramitador, supervisor, administrador)
- [ ] Guía de configuración del sistema (tablas de reglas)
- [ ] Documentación técnica de la API
- [ ] Guía de despliegue y administración del servidor

---

## Dependencias clave entre áreas

```
A.4 (motor de estados)
  ← bloquea parcialmente → A.1 (CRUD ESFTT)
  ← bloquea → B.1 (configuración reglas)

A.2 (sistema documental)
  ← bloquea → A.3 (generación escritos)
  ← bloquea → A.1 (CRUD tareas completo: FIRMAR, NOTIFICAR, INCORPORAR)

C.1 (elementos eléctricos)
  ← bloquea → C.2 (GIS)

E.1 (plazos legales)
  ← necesario para → A.5 (listado inteligente)

A.3 (generación escritos)
  ← puede integrarse con → E.4 (firma electrónica)
  ← depende de → A.2 (almacenamiento de documentos generados)

D (legacy)
  ← requiere que esté estable → A.1 + A.2 (para que los datos importados sean válidos)
```

---

## Decisiones de arquitectura abiertas

| Decisión | Opciones | Afecta a |
|----------|----------|----------|
| Almacenamiento de documentos | Filesystem local / S3-compatible / PostgreSQL bytea | A.2, A.3 |
| Motor de plantillas | python-docx (Word) / Jinja2 sobre ODT / WeasyPrint (HTML→PDF) | A.3 |
| Firma electrónica | @firma JdA integrada / flujo manual en dos pasos | A.3, E.4 |
| Modelo de elementos eléctricos | Genérico con JSON / Tablas específicas por tipo | C.1, C.2 |
| PostGIS vs coordenadas simples | PostGIS / lat+lon numérico | C.2 |
| Plazos: suspensión | Modelo de eventos de suspensión / solo fecha_limite estática | E.1, A.5 |
| Reglas de tramitación | Editables en producción por Supervisor / solo por técnico | A.4, B.1 |
| Notificaciones externas | Email directo / Notific@ JdA / manual | E.3 |
| Integración registro de entrada | SIGEM JdA / registro propio / ninguno | A.2 |
| Legacy | ¿Qué sistema? ¿Qué datos? ¿Documentos? | D |
