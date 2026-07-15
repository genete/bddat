# Matriz de cobertura — BDDAT

> **Naturaleza de este documento:** vivo, se actualiza en cada issue cerrado (o en
> cualquier cambio real de código que afecte a una fila). Es el "plan maestro" —
> por cada necesidad, cuánto está cubierto y qué falta para el 100%. Sin nombres
> ni números de issue: eso vive en GitHub, se busca por label `necesidad:N0XX`
> cuando toque decidir "trabajad esta celda ya".
> **Fuente del %:** código real (`app/`, `migrations/`, `scripts/`, config de
> despliegue) — nunca issues ni documentos de diseño, que quedan desactualizados
> con frecuencia en este proyecto. Todo % está respaldado por evidencia directa
> de código, verificada — no hay filas con "pendiente de verificar".
> **Origen:** auditoría inicial de código (sesión de diseño 2026-07-08). Ciclo de
> trabajo que gobierna esta matriz: ADR-031. Historial de cambios fila a fila:
> `git log` sobre este fichero.
> Columna "Necesidad" es una copia legible de `DETALLE_NECESIDADES_BDDAT.md` —
> ese documento sigue siendo la fuente de verdad si hace falta más contexto.

---

## Bloque 1 — Tramitación ESFTT

| Id | Necesidad | % Cobertura | Qué falta |
|---|---|---|---|
| N001 | Crear, editar, avanzar y cerrar Solicitudes/Fases/Trámites/Tareas de un expediente | 97% | Nada funcionalmente relevante — CRUD completo de los 4 niveles ESFTT + isla React (ADR-016). El "avanzar" de la tarea ANALIZAR queda completo con su checklist de diagnóstico: documental (#495) + técnico (#581) + requerimientos (#440) → `Diagnostico.defectos` (#442), único documento de salida. |
| N002 | Realizar tareas auxiliares asignadas dentro de la tramitación, sin capacidad de decisión | 90% | Permisos y cola dedicada del Administrativo confirmados (`gestionar_tareas` incluye ADMINISTRATIVO, excluido explícitamente de crear/editar/borrar estructura; endpoint `/api/administrativo/cola`). |
| N003 | Borrado de elementos ESFTT condicionado por el motor de reglas | 90% | El borrado consulta al motor antes de ejecutarse, con escape justificado (Tramitador) registrado en bitácora. Nota aparte, sin afectar este %: `api_bc.py` sigue montado como blueprint activo pese a documentarse como código muerto — ver Hallazgo 4 de `DETALLE_NECESIDADES_BDDAT.md`. |
| N069 | Apertura de expedientes (alta / wizard de creación) | 95% | Nada relevante — wizard de 3 pasos completo con commit transaccional único. |
| N072 | Bitácora narrativa del expediente (anotaciones datadas con autor) | 20% | Lo que existe es un log automático de sistema *por usuario* (feed de actividad, no narrativo). Falta: vista/endpoint filtrado por expediente, capacidad de anotación libre del Tramitador no ligada a un bypass del motor, y UI de consulta para Supervisor/Administrativo. |
| N073 | Gestionar autorizaciones de representación: quién puede actuar en nombre de un titular en la tramitación | 95% | Pantalla de gestión completa (conceder, revocar, restaurar autorización) con validaciones (no autoautorización, no duplicar autorización activa), más consumo real en el wizard de alta. Nada relevante pendiente. |
| N081 | Gestionar el catálogo de organismos administrativos (DIR3) y su vínculo con interesados institucionales del expediente | 40% | Modelos maduros (`OrganismoExpediente`, `InteresadoExpediente`, campo `codigo_dir3`) en uso real para generar escritos automáticos (context builders + plantilla `.docx` de notificación a organismo). Cero interfaz de gestión manual — la única ruta encontrada vive en `api_bc.py` (blueprint cuestionado, ver Hallazgo 4 de `DETALLE_NECESIDADES_BDDAT.md`), y no hay listado de códigos DIR3 (#106, #396 abiertos). |

## Bloque 2 — Sistema documental

| Id | Necesidad | % Cobertura | Qué falta |
|---|---|---|---|
| N004 | Incorporar documentos al expediente, con organización automática en ruta predeterminada y registro de su localización | 50% | La organización automática en carpeta solo existe para documentos generados por el propio sistema (escritos); lo que Tramitador/Administrativo incorporan a mano solo se registra donde ya estuviera, sin mover ni copiar nada. |
| N006 | Consultar y descargar documentos del expediente | 100% | Nada — consulta, descarga y protección contra path traversal cubiertas. |
| N007 | Auditoría automática de URLs a documentos rotas, globales o por expediente | 0% | No existe ningún mecanismo que compruebe accesibilidad de URLs/ficheros de forma proactiva, ni por expediente ni global — solo hay comprobaciones reactivas puntuales al pedir un documento concreto. |
| N008 | Incorporar documentos firmados externamente y justificantes | 75% | Mecanismo de incorporación genérico + catálogo de tipos `JUSTIFICANTE_*` ya existen. Falta cualquier verificación real de que el documento lleve una firma válida — hoy es solo clasificación por tipo. |
| N009 | Expediente documental reconstruible sin BDDAT — estructura predecible fuera de BD | 25% | La convención de carpeta predecible solo se aplica a documentos generados por el sistema. Falta forzarla también en la incorporación manual, y generar un manifest/índice en disco por expediente — sin BD, una carpeta es hoy un montón de ficheros sin diferenciar. |
| N076 | Detectar documentos del pool sin vincular a ninguna tarea de tramitación ("radar de huérfanos") | 50% | La señal de "sin vincular a tarea" existe y se muestra como columna en el listado general de documentos del pool. Falta una vista dedicada de triage (radar) que la use como filtro/prioridad, no solo como dato de contexto. |
| N077 | Detectar documentos duplicados en el pool del expediente (verificación de integridad) | 0% | La columna de verificación de integridad existe en el modelo pero ningún punto de código la calcula nunca — funcionalidad diseñada y nunca conectada. |
| N078 | Mantener el catálogo de requisitos documentales exigidos por normativa, con condiciones de aplicabilidad según el trámite/instalación | 75% | CRUD completo (#583/#584: modelo `RequisitoDocumental`/`CondicionRequisito`/`DocumentoRequisito`, módulo `admin_requisitos`). El motor que evalúa las condiciones (`app/services/requisitos.py`) solo soporta EQ/NEQ/IN/NOT_IN/IS_NULL/NOT_NULL — GT/GTE/LT/LTE/BETWEEN/NOT_BETWEEN se ignoran en silencio (bug confirmado, #601 abierto). Contenido normativo real sin poblar (#408 abierto). |
| N082 | Mantener el catálogo de tipos de documento (código identificador inmutable tras el alta, usado en el motor de reglas y en el código, mismo régimen que los tipos ESFTT de N019) | 100% | Nada — CRUD completo (#621: alta y edición, código bloqueado tras el alta). Sin baja por decisión explícita, no aplazada: el modelo no tiene columna `activo`. |

## Bloque 3 — Generación de escritos

| Id | Necesidad | % Cobertura | Qué falta |
|---|---|---|---|
| N010 | Crear, modificar y gestionar plantillas de escritos | 90% | CRUD de plantillas completo. Falta CRUD de consultas nombradas reutilizables en plantillas — hoy solo se pueden dar de alta por BD/migración directa. |
| N011 | Detección de plantillas con tokens vacíos (aviso de hueco antes de generar) | 0% | No existe ninguna rutina de análisis estático de la plantilla; el único aviso de "hueco" es reactivo, al fallar la generación contra un expediente real. |
| N012 | Generar escrito desde plantilla y descargar versión borrador/firmada | 95% | Ciclo completo verificado (#608): generar desde plantilla, preview, vinculación automática como consumido, ciclo hasta PENDIENTE_FIRMA. Falta: conversión DOCX→PDF manual fuera de BDDAT (no prioritario); trazabilidad por token embebido sin implementar (#181/#182). |
| N013 | Generar escritos estándar y avanzar tramitación | 95% | Mismo backend y UI que N012 (la distinción por rol es artificiosa, pendiente fusionar necesidades). |
| N079 | Mantener el catálogo de requerimientos administrativos exigibles al interesado, con su contenido normativo | 70% | CRUD completo y verificado en código (#593/#597: módulo `catalogo_requerimientos`, permisos `acceder/gestionar/archivar_catalogo_requerimientos`, smoke test). Poblado normativo en 0% — la única migración (405) crea el esquema, sin contenido real (#441 abierto). |
| N080 | Exponer las variables del motor de reglas y catálogos estructurales en las plantillas de escritos, como documento adaptativo al contexto del expediente | 0% | `CatalogoVariable` (`app/models/motor_reglas.py`) existe y está en uso real del motor de reglas y del Context Assembler (`assembler.py`) — pero ningún punto de `generador_escritos.py`/`escritos.py` lo consume. Cero conexión con la generación de escritos hoy (#556 sin construir, #561/#587 sin resolver). |

## Bloque 4 — Motor de reglas y configuración estructural

| Id | Necesidad | % Cobertura | Qué falta |
|---|---|---|---|
| N015 | Validación de flujo en tiempo real: qué se puede crear/iniciar/cerrar y cuándo, sin bloqueo silencioso | 85% | El motor evalúa y nunca degrada a "permitido" en silencio; los bloqueos llegan con motivo y norma legibles (HTTP 422 explícito), y los invariantes de cierre están hardcoded con mensajes propios. |
| N016 | Configurar reglas del motor por tipo de expediente | 90% | CRUD completo (#170: `reglas_motor`+`condiciones_regla`+`excepciones_motor`+`condiciones_excepcion`, selector guiado en cascada del patrón `sujeto` — nivel + hasta 4 selects reales + ANY, nunca texto libre — integrado en `/configuracion-motor/` junto al modo global). Sin baja física — solo lógica (`activa`), mismo criterio que el resto de catálogos normativos. Falta: auditoría de completitud del contenido normativo real ya cargado frente a lo que exige la legislación (no verificada en este issue). El CRUD propio de `Norma`/`CatalogoVariable` se ha separado como necesidad propia — ver N083. |
| N017 | Sobreescritura de emergencia sobre el motor | 0% | Esta necesidad es del Admin BDDAT resolviendo una situación en la que el Tramitador ya no puede salir por la vía normal (justificación) — no debe confundirse con esa vía normal, que es de Tramitador y ya está cubierta en N003. No existe en la aplicación ningún mecanismo de intervención directa sobre el motor a nivel Admin; hoy solo sería posible mediante acceso directo a la base de datos, fuera de la aplicación. Ver Hallazgo 5 de `DETALLE_NECESIDADES_BDDAT.md` (relación con N022). |
| N018 | Selector de modo global del motor (bloquear / advertir / inactivo) | 20% | La lectura y aplicación del modo global está viva en el flujo real de creación. Falta el selector de escritura — hoy solo se puede cambiar directamente en BD. |
| N019 | CRUD de tipos de ESFTT (Fase/Trámite/Tarea/Solicitud) | 90% | CRUD completo de las 5 tablas ESFTT (ampliado por Carlos a incluir también Expediente, #171): módulo único `tablas_maestras` con pestañas, campo identificador inmutable tras el alta (protege capa 2 y capa 3), editor anidado de `tramites_tareas`/`tramites_tareas_documentos` para la secuencia del Trámite. Tarea sin alta por diseño (catálogo cerrado, no es hueco). Falta: baja lógica (`activo`) aplazada, pendiente de decisión de Carlos. |
| N020 | Gestión de cambios en municipios (fusión/escisión, recarga correcta de la tabla) | 0% | Lo único que existe es búsqueda de autocompletado para formularios (solo lectura) — no hay ninguna gestión de cambios sobre la tabla. |
| N021 | CRUD de rutas del filesystem | 0% | Las rutas del filesystem son variables de entorno leídas una vez al arrancar; no hay ni siquiera un modelo de datos que sostenga un futuro CRUD. |
| N022 | Sobreescritura técnica de emergencia sobre catálogo estructural | 0% | Misma naturaleza que N017 aplicada al catálogo estructural en vez de al motor: hoy sería una intervención directa en BD, sin ningún mecanismo en la aplicación. Ver Hallazgo 5 de `DETALLE_NECESIDADES_BDDAT.md`. |
| N083 | CRUD propio del catálogo de `Norma` y `CatalogoVariable` | 0% | Todo — no existe ninguna ruta ni módulo de administración para alta/edición manual de `Norma` ni `CatalogoVariable` (`app/models/motor_reglas.py`); hoy la única vía es migración/BD directa. Confirmado por auditoría de código: ambos modelos se consumen en modo solo lectura desde `configuracion_motor`, `catalogo_plazos`, `admin_requisitos`, `items_tecnicos`, `entidades` y en generación de escritos/certificados (`assembler.py`, `generador_cert.py`, `cert_pdf.py`), sin ningún punto de escritura. |

## Bloque 5 — Plazos legales

| Id | Necesidad | % Cobertura | Qué falta |
|---|---|---|---|
| N023 | Configurar plazos por tipo de ESFTT | 90% | CRUD completo y verificado en código (#632/#633: `catalogo_plazos`+`condiciones_plazo` con selector en cascada ESFTT→tipo→campo_fecha y los 6 operadores del CHECK constraint; `efectos_plazo` con baja física condicionada por uso). Mismo patrón que N019: sin baja lógica formal en `catalogo_plazos`, usa el toggle `activo` del resto de catálogos normativos. |
| N024 | Consultar plazos y vencimientos de expedientes propios | 55% | El dato de plazo/vencimiento por tarea es correcto y se agrega hasta expediente (árbol + listado de seguimiento), pero falta una vista dedicada de "mis vencimientos". |
| N025 | Dashboard de alertas de plazos de toda la unidad | 20% | Solo hay un número agregado suelto dentro del panel de estadísticas. El dashboard de alertas dedicado sigue marcado "próximamente" (#74) en el propio hub del Supervisor. |
| N026 | Consultar información de plazos | 50% | Comparte la misma infraestructura de lectura que N024 (árbol + listado de seguimiento) — la diferencia es de permisos de rol, no de funcionalidad distinta. |
| N027 | Sistema de suspensión de plazos (activa/cerrada) | 70% | El cálculo de intervalos de suspensión es automático (se infiere del árbol documental, sin toggle manual) y ya desplaza la fecha límite real. Comprobado directamente en el árbol React (`Semaforo.jsx`, `NodoTareas.jsx`): el bloque de la tarea ESPERAR_PLAZO no muestra un estado "suspendido" explícito, solo la barra de color derivada del plazo ya ajustado — el efecto está, la señal visual distintiva de "esto está suspendido ahora mismo" no. |
| N067 | Cargar y mantener el calendario oficial de festivos | 80% | Existe un comando (`flask inhabiles importar`) que carga el calendario desde la API oficial de la Junta de Andalucía, con aviso proactivo en toda la aplicación si falta el año siguiente. Sigue siendo un comando de servidor, no un botón en la interfaz web. |
| N068 | Motor de cálculo de plazo pendiente según días hábiles y suspensiones | 90% | Motor de cálculo sólido: los 4 tipos de unidad de plazo, prórroga a hábil, suspensiones aplicadas al cálculo real, usado en producción por árbol, listado y estadísticas. |

## Bloque 6 — Proyectos e instalaciones

| Id | Necesidad | % Cobertura | Qué falta |
|---|---|---|---|
| N028 | Editar proyecto y elementos técnicos anidados (líneas, CT, subestaciones...) | 10% | La edición de elementos técnicos anidados está **explícitamente deshabilitada en la interfaz** ("Próximamente"). Solo existe un esqueleto de identidad/contención sin ningún campo técnico ni formulario. |
| N029 | Editar datos básicos de proyecto (denominación, municipio...) | 100% | Nada — todos los campos editables del proyecto tienen representación en el formulario, incluida la edición de municipios. |
| N031 | Relacionar elementos del proyecto con el estado del expediente y sus resoluciones | 10% | El hueco de esquema para vincular activos técnicos al estado administrativo del expediente ya existe en el modelo — pero nada escribe en él, y las resoluciones no enlazan con ningún elemento técnico concreto. |
| N074 | Mantener el catálogo de apartados de contenido técnico exigidos por normativa, con condiciones de aplicabilidad según la instalación | 90% | CRUD completo del catálogo (alta, edición con condiciones anidadas, activar/desactivar). Nada relevante pendiente. |

## Bloque 7 — GIS / Cartografía

| Id | Necesidad | % Cobertura | Qué falta |
|---|---|---|---|
| N032 | Editar geometría y visualizar mapa | 0% | Todo — sin modelo de geometría, sin librería de mapas, sin ruta ni template. Confirmado tras descartar falsos positivos de búsqueda. |
| N033 | Consultar vista global de mapa | 0% | Todo — ninguna vista muestra expedientes/proyectos sobre un mapa, para ningún rol. |

## Bloque 8 — Gestión de carga y usuarios

| Id | Necesidad | % Cobertura | Qué falta |
|---|---|---|---|
| N034 | Asignar expedientes a técnicos (uno o varios, mismo interfaz) | 100% | Nada — asignación individual (cualquier expediente, incluida desasignación) y asignación masiva (selección múltiple sobre expedientes sin asignar, desde el listado) cubiertas (#612). La reasignación masiva de un expediente que ya tiene técnico queda deliberadamente fuera — decisión de diseño para evitar pisar sin querer el trabajo ya asignado de otro técnico, no un hueco; esa vía sigue siendo exclusivamente individual. |
| N036 | Gestionar altas/bajas de usuarios y roles | 90% | Alta, edición, activar/desactivar usuarios y asignación de roles, con protecciones (no autodesactivarse, no quitar el último Admin). El catálogo de los 4 tipos de rol en sí es fijo por diseño (son los 4 actores de negocio que fija `PLAN_ESTRATEGIA.md` §B, no un catálogo abierto) — no es un hueco real. |
| N037 | Consultar estadísticas de carga interna (por técnico/pista/estado, plazos vencidos, antigüedad) | 50% | KPIs, desglose por estado y por técnico ya construidos y visibles (isla React de estadísticas). Falta desglose por pista y por antigüedad — el propio hub lo marca "próximamente" (#256). |
| N038 | Generar informes de estado de situación bajo demanda para servicios centrales | 0% | Todo — sin servicio, sin ruta, solo una tarjeta "próximamente" (#76) en el hub. |
| N039 | Exportar datos agregados (Excel/CSV) | 0% | Todo — ningún exportador de datos agregados encontrado en el código. |
| N040 | Cambiar titularidad de forma masiva en agrupaciones | 0% | El modelo de histórico de titulares está completo, con el método que haría el cambio — pero sin ningún punto del código que lo invoque. Ni siquiera existe el cambio individual conectado a una ruta, y mucho menos el masivo. |

## Bloque 9 — Listado inteligente

| Id | Necesidad | % Cobertura | Qué falta |
|---|---|---|---|
| N041 | Filtrar y consultar datos agregados por expediente (plazos, tareas activas, escritos pendientes) | 75% | Filtros, paginación y estado por pista de cada solicitud, construidos y en uso. Falta un contador dedicado de "escritos pendientes" — hoy se infiere indirectamente de los códigos de pista. |
| N042 | Consultar cola de trabajo priorizada | 75% | El listado de seguimiento filtrado a "mis expedientes" (`ver=mis`, mismo endpoint que usa N043 para Administrativo) es la vista real del Tramitador: cada solicitud lleva un color por pista calculado con lógica de prioridad real (el estado más urgente entre los abiertos gana la celda). Lo que falta: el orden de las filas en sí no está ordenado por urgencia, solo por antigüedad de alta — la priorización hoy es visual (color), no de orden. |
| N043 | Consultar vista global de expedientes para localizar dónde actuar | 75% | Mismo listado de seguimiento que N042, filtrado a "todos" (`ver=todos`) en vez de "mis" — el Administrativo ve el mismo estado por pista de cualquier expediente. No hay una vista distinta ni más simplificada específica para este rol; reutiliza la misma fuente de verdad que Supervisor/Tramitador. |
| N044 | Consultar inconsistencias y huérfanos de BD | 25% | Solo cubre catálogo estructural (códigos de tipos ausentes), comprobado una vez al arrancar y visible solo en el log del servidor — no huérfanos/referencias rotas genéricos de BD, y no consultable bajo demanda desde la aplicación. |

## Bloque 10 — Auditoría configurable

| Id | Necesidad | % Cobertura | Qué falta |
|---|---|---|---|
| N045 | Definir qué operaciones/elementos se auditan | 0% | No existe ningún panel de configuración. El registro en bitácora está hardcoded a dos casos muy concretos (escape de motor, acceso a expediente ajeno) — la inmensa mayoría de mutaciones normales no se auditan hoy. |
| N046 | Consultar historial por expediente | 15% | El único endpoint de consulta filtra por usuario ("mis últimas 50 acciones"), no por expediente. Reconstruir el historial de un expediente concreto exigiría además un cruce que hoy no existe, porque las mutaciones se registran por tabla afectada, no por expediente. |
| N047 | Consultar logs técnicos del sistema | 0% | Todo — logging estándar de Python sin persistencia estructurada ni panel de consulta. |
| N075 | Advertir en el momento y dejar constancia automática cuando se actúa sobre un expediente fuera de la propia asignación | 85% | Construido y funcionando: aviso automático (indicador visible en el layout) + registro en bitácora cuando un Tramitador actúa sobre expediente ajeno. |

## Bloque 11 — Importación legacy

| Id | Necesidad | % Cobertura | Qué falta |
|---|---|---|---|
| N048 | Cargar datos legacy (Access → schema `legacy`, solo lectura permanente) | 0% | Confirmado sin ambigüedad — sin schema `legacy`, sin segundo bind de base de datos, sin script de importación desde Access. La única mención de "legacy" en el código es texto descriptivo aspiracional en un seed de roles. |
| N049 | Activar expediente legacy individualmente, respetando huecos de numeración AT histórica | 15% | La parte de respetar huecos de numeración histórica está resuelta (contador gapless con instrucción de arranque documentada). La operación de "activar" en sí no existe — coherente con que no hay ningún dato legacy real que activar (N048 = 0%). |
| N050 | Completar campos básicos de expedientes heredados | 35% | El formulario genérico de edición de expediente permite completar los mismos campos que tendría uno heredado, pero no está pensado ni verificado para ese caso — y hoy no hay ningún expediente real al que aplicarlo. |

## Bloque 12 — Manual de usuario

| Id | Necesidad | % Cobertura | Qué falta |
|---|---|---|---|
| N051 | Consultar documentación con ayuda contextual | 0% | Todo — confirmado con búsqueda negativa exhaustiva. Ninguna ruta `/manual`, `/ayuda` ni `/help` registrada. |
| N071 | Generar y mantener el contenido del manual de usuario | 0% | Todo — ningún contenido ni mecanismo de autoría/mantenimiento del manual en código. |

## Bloque 13 — Mensajería interna

| Id | Necesidad | % Cobertura | Qué falta |
|---|---|---|---|
| N053 | Enviar avisos y delegar tareas al pool de administrativos (no es chat) | 15% | La cola compartida de tareas es autoservicio (cualquiera se autoasigna trabajo pendiente) — falta la mitad "dirigida": que alguien empuje una tarea concreta a una persona concreta, y una capacidad de aviso con destinatario. Ninguna de las dos tiene persistencia hoy. |
| N054 | Solicitar alta o cambio de rol | 15% | La ruta está enganchada y alcanzable desde la interfaz, pero el backend no hace nada real: muestra un mensaje de éxito sin persistir ninguna solicitud (`# TODO` explícito en el propio código). |
| N055 | Solicitar cambios de plantillas | 0% | Todo — ningún canal de petición dirigido al Supervisor, en ningún punto del código. |
| N056 | Recibir avisos técnicos del sistema | 0% | Todo — sin segmentación de avisos técnicos a Admin BDDAT en ningún punto. |
| N070 | Solicitar mejoras del manual | 0% | Depende de que exista el manual (N051/N071) y un canal de mensajería funcional (N053-056) — ninguno de los dos existe hoy. |

## Bloque 14 — Índice y compilación de expediente

| Id | Necesidad | % Cobertura | Qué falta |
|---|---|---|---|
| N057 | Compilar expediente completo (documentos + bitácora + estado) en dossier exportable, autocontenido, para envío al exterior | 0% | ADR-027 figura como "Adoptada" pero su plan de implementación nunca se ejecutó: no existe la columna que decide qué documentos integran el expediente, no existe la consulta que los recopila, no existe generador de dossier alguno (foliado, índice numerado, empaquetado). El diseño existe; el código no. |

## Bloque 15 — Infraestructura técnica y operación

| Id | Necesidad | % Cobertura | Qué falta |
|---|---|---|---|
| N058 | Servidor de aplicación operativo, actualizado y con procesos gestionados | 10% | Solo el entrypoint mínimo de desarrollo (`run.py`) y dependencias declaradas. Sin gestión de procesos de producción (gunicorn/systemd) en el repo. |
| N059 | Base de datos PostgreSQL gestionada (usuarios, schemas, rendimiento, actualizaciones) | 45% | La gestión de esquema vía migraciones Alembic está muy madura (~90 migraciones). La gestión del propio servidor de BD (usuarios, rendimiento, actualizaciones del motor) es responsabilidad externa al repo, sin rastro aquí. |
| N060 | Servidor de archivos con estructura, permisos y cuota | 0% | Todo — y ni siquiera el diseño está cerrado: el propio documento de estrategia lo marca como "decisión de arquitectura abierta". |
| N061 | Backups verificados (BD + documentos + servidor) con política de retención | 0% | Todo — ningún script de backup en el repositorio. |
| N062 | Seguridad y acceso (SSL, firewall, gestión de secrets, contraseñas) | 20% | Buena higiene de código (secretos vía variables de entorno, `.env` excluido de git). El propio `SECURITY.md` declara explícitamente que SSL, firewall y credenciales de producción son responsabilidad del despliegue, no del repositorio. |
| N063 | Despliegue reproducible de la aplicación | 15% | El único procedimiento documentado es manual (clonar, crear venv, migrar, arrancar). El único workflow de CI/CD del repo despliega una presentación estática, no la aplicación. |
| N064 | Monitorización y alertas de disponibilidad | 0% | Todo — sin endpoint de salud ni integración con ningún servicio de monitorización encontrada. |
| N065 | Acceso a base de datos legacy para la carga inicial | 0% | No es una carencia de desarrollo — es un acto puntual de IT (entregar el fichero Access) que ocurrirá cuando toque la migración real, no algo que el código pueda resolver. |

## Bloque 16 — Datos estructurales mínimos para producción

| Id | Necesidad | % Cobertura | Qué falta |
|---|---|---|---|
| N066 | Catálogo estructural mínimo cargado para producción: tipos de ESFTT/trámite/tarea reales, reglas de motor con contenido normativo real, plazos legales reales por tipo, municipios completos | 35% | El mecanismo de carga de datos reales vía migración existe y se ha usado de forma sostenida (decenas de migraciones de seed para tipos, plazos, normas, organismos). Falta: (a) ninguna migración carga el catálogo completo de municipios andaluces — la tabla se crea vacía; (b) la completitud del contenido normativo frente a lo que exige la legislación por tipo de trámite es el eje "motor-contenido normativo" que sigue pendiente de su propia auditoría en profundidad. |

