# Detalle de necesidades — BDDAT

> **Naturaleza de este documento:** fijo, se toca poco — como un ADR. Define **qué**
> es cada necesidad del sistema, no su estado de implementación ni la forma concreta
> de interfaz que la resuelve (eso es decisión de diseño, cambia con el tiempo).
> **Estado:** En revisión iterativa con Carlos, necesidad a necesidad. Los ids son
> permanentes desde ahora — no se renumeran; se añaden o se retiran (ver "Ids
> retirados"). Ampliado 2026-07-08 con 5 necesidades descubiertas al auditar el
> código real para construir `MATRIZ_COBERTURA_BDDAT.md` (N073-N077). Ampliado
> 2026-07-09 con 4 necesidades descubiertas durante el etiquetado retroactivo
> `necesidad:N0XX` de issues abiertos (ADR-031) — N078-N081. Ampliado
> 2026-08-05 con N085 (#728, ADR-039 — datos del órgano propio).
> **Fecha:** 2026-08-05

---

## 0. Cómo se usa este documento

- Cada fila tiene un **id plano y permanente** (`N001, N002...`), asignado una sola
  vez y nunca reasignado. El id **no codifica bloque ni milestone** — esos son
  columnas propias de cada fila, no parte de la clave. Si el CEO decide adelantar,
  posponer, fusionar o dividir bloques, solo cambian esas columnas; el id (y el
  label de GitHub `necesidad:N019` que lo use) no se mueve.
- El id es la **columna 1 compartida** con `MATRIZ_COBERTURA_BDDAT.md` (próximo
  documento — % cobertura + qué falta).
- Cuatro campos por fila: **necesidad** (qué hace falta, en términos de capacidad —
  no de pantalla ni de versión de UI), **quién** la necesita, **bloque** (agrupación
  funcional, referencia a `PLAN_ESTRATEGIA.md` §A) y **milestone**.
- No contiene número de issue, estado de implementación, ni referencia al documento
  de origen por fila. Este documento fija el presente; de dónde venía cada necesidad
  en su día no es un dato que haya que mantener ni volver a consultar.
- Cobertura necesidad↔issue es 1:1 en el sentido de que cada necesidad se cubre
  (total o parcialmente) con el trabajo real hecho, no con la clasificación de
  empresa del momento — por eso bloque/milestone viven aparte del id.

---

## Bloque 1 — Tramitación ESFTT

| Id | Necesidad | Quién | Bloque | Milestone |
|---|---|---|---|---|
| N001 | Crear, editar, avanzar y cerrar Solicitudes/Fases/Trámites/Tareas de un expediente | Tramitador | 1 — Tramitación ESFTT | M1 |
| N002 | Realizar tareas auxiliares asignadas dentro de la tramitación, sin capacidad de decisión | Administrativo | 1 — Tramitación ESFTT | M1 |
| N003 | Borrado de elementos ESFTT condicionado por el motor de reglas | Tramitador (depende de Bloque 4) | 1 — Tramitación ESFTT | M1 |
| N069 | Apertura de expedientes (alta / wizard de creación) | Tramitador/Administrativo | 1 — Tramitación ESFTT | M1 |
| N072 | Bitácora narrativa del expediente (anotaciones datadas con autor) | Tramitador (Supervisor/Administrativo consultan) | 1 — Tramitación ESFTT | M1 |
| N073 | Gestionar autorizaciones de representación: quién puede actuar en nombre de un titular en la tramitación | Tramitador/Administrativo | 1 — Tramitación ESFTT | M1 |
| N081 | Gestionar el catálogo de organismos administrativos (DIR3) y su vínculo con interesados institucionales del expediente | Tramitador/Administrativo | 1 — Tramitación ESFTT | M2 |

---

## Bloque 2 — Sistema documental

| Id | Necesidad | Quién | Bloque | Milestone |
|---|---|---|---|---|
| N004 | Incorporar documentos al expediente, con organización automática en ruta predeterminada y registro de su localización | Tramitador/Administrativo | 2 — Sistema documental | M1 |
| N006 | Consultar y descargar documentos del expediente | Todos | 2 — Sistema documental | M1 |
| N007 | Auditoría automática de URLs a documentos rotas, globales o por expediente | Todos | 2 — Sistema documental | M1 |
| N008 | Incorporar documentos firmados externamente y justificantes | Tramitador/Administrativo | 2 — Sistema documental | M1 |
| N009 | Expediente documental reconstruible sin BDDAT — estructura predecible fuera de BD | Todos | 2 — Sistema documental | M1 |
| N076 | Detectar documentos del pool sin vincular a ninguna tarea de tramitación ("radar de huérfanos") | Tramitador/Administrativo | 2 — Sistema documental | M1 |
| N077 | Detectar documentos duplicados en el pool del expediente (verificación de integridad) | Tramitador/Administrativo | 2 — Sistema documental | M1 |
| N078 | Mantener el catálogo de requisitos documentales exigidos por normativa, con condiciones de aplicabilidad según el trámite/instalación | Supervisor | 2 — Sistema documental | M3 |
| N082 | Mantener el catálogo de tipos de documento (código identificador inmutable tras el alta, usado en el motor de reglas y en el código, mismo régimen que los tipos ESFTT de N019) | Supervisor | 2 — Sistema documental | M3 |
| N084 | Extraer datos estructurados (fecha, estado de notificación) de un justificante externo para auto-rellenar y verificar su registro, reduciendo trabajo manual y errores de asociación al expediente equivocado | Tramitador/Administrativo | 2 — Sistema documental | M2 |

---

## Bloque 3 — Generación de escritos

| Id | Necesidad | Quién | Bloque | Milestone |
|---|---|---|---|---|
| N010 | Crear, modificar y gestionar plantillas de escritos | Supervisor | 3 — Generación de escritos | M2 |
| N011 | Detección de plantillas con tokens vacíos (aviso de hueco antes de generar) | Supervisor (con ayuda de una rutina BDDAT) | 3 — Generación de escritos | M2 |
| N012 | Generar escrito desde plantilla y descargar versión borrador/firmada | Tramitador | 3 — Generación de escritos | M2 |
| N013 | Generar escritos estándar y avanzar tramitación | Administrativo | 3 — Generación de escritos | M2 |
| N079 | Mantener el catálogo de requerimientos administrativos exigibles al interesado, con su contenido normativo | Supervisor | 3 — Generación de escritos | M3 |
| N080 | Exponer las variables del motor de reglas y catálogos estructurales en las plantillas de escritos, como documento adaptativo al contexto del expediente | Supervisor (define plantilla) / Tramitador (recibe escrito resultante) | 3 — Generación de escritos | M4 |
| N085 | Mantener los datos institucionales del órgano propio (Consejería, Delegación Territorial por provincia, sede, firmantes por cargo) para la cabecera/pie de los escritos generados y la automatización de envío a Port@firmas | Supervisor | 3 — Generación de escritos | M3 |

---

## Bloque 4 — Motor de reglas y configuración estructural

> Fusión de los antiguos bloques "Motor de reglas" y "Config. reglas y estructura":
> conviven en el mismo panel de configuración del Supervisor.

| Id | Necesidad | Quién | Bloque | Milestone |
|---|---|---|---|---|
| N015 | Validación de flujo en tiempo real: qué se puede crear/iniciar/cerrar y cuándo, sin bloqueo silencioso | Tramitador/Administrativo | 4 — Motor y config. estructural | M3/M5 (estudio previo a M1) |
| N016 | Configurar reglas del motor por tipo de expediente | Supervisor | 4 — Motor y config. estructural | M3/M5 (estudio previo a M1) |
| N017 | Sobreescritura de emergencia sobre el motor | Admin BDDAT | 4 — Motor y config. estructural | M3/M5 |
| N018 | Selector de modo global del motor (bloquear / advertir / inactivo) | Supervisor | 4 — Motor y config. estructural | M3/M5 |
| N019 | CRUD de tipos de ESFTT (Fase/Trámite/Tarea/Solicitud) | Supervisor | 4 — Motor y config. estructural | M2 |
| N020 | Gestión de cambios en municipios (fusión/escisión, recarga correcta de la tabla) | Admin BDDAT | 4 — Motor y config. estructural | M2 |
| N021 | CRUD de rutas del filesystem | Admin BDDAT | 4 — Motor y config. estructural | M2 |
| N022 | Sobreescritura técnica de emergencia sobre catálogo estructural | Admin BDDAT | 4 — Motor y config. estructural | M2 |
| N083 | CRUD propio del catálogo de `Norma` y `CatalogoVariable` (hoy solo lectura en selects); `Norma` se usa además como cita normativa fuera del motor (plazos, requisitos documentales, apartados técnicos, generación de certificados) | Supervisor | 4 — Motor y config. estructural | M3/M5 (estudio previo a M1) |

---

## Bloque 5 — Plazos legales

| Id | Necesidad | Quién | Bloque | Milestone |
|---|---|---|---|---|
| N023 | Configurar plazos por tipo de ESFTT | Supervisor | 5 — Plazos legales | M3/M5 (estudio previo a M1) |
| N024 | Consultar plazos y vencimientos de expedientes propios | Tramitador | 5 — Plazos legales | M3/M5 |
| N025 | Dashboard de alertas de plazos de toda la unidad | Supervisor | 5 — Plazos legales | M3/M5 |
| N026 | Consultar información de plazos | Administrativo | 5 — Plazos legales | M3/M5 |
| N027 | Sistema de suspensión de plazos (activa/cerrada) | Transversal — cliente Tramitador y Administrativo | 5 — Plazos legales | M3/M5 |
| N067 | Cargar y mantener el calendario oficial de festivos | Admin BDDAT | 5 — Plazos legales | M3/M5 |
| N068 | Motor de cálculo de plazo pendiente según días hábiles y suspensiones | Transversal — sirve a quienes consultan plazos | 5 — Plazos legales | M3/M5 |

---

## Bloque 6 — Proyectos e instalaciones

| Id | Necesidad | Quién | Bloque | Milestone |
|---|---|---|---|---|
| N028 | Editar proyecto y elementos técnicos anidados (líneas, CT, subestaciones...) | Tramitador | 6 — Proyectos e instalaciones | M3 |
| N029 | Editar datos básicos de proyecto (denominación, municipio...) — edición posterior a la creación | Tramitador | 6 — Proyectos e instalaciones | M3 |
| N031 | Relacionar elementos del proyecto con el estado del expediente y sus resoluciones | Sin asignar — "punto denso, desarrollo posterior" | 6 — Proyectos e instalaciones | M3 |
| N074 | Mantener el catálogo de apartados de contenido técnico exigidos por normativa, con condiciones de aplicabilidad según la instalación | Supervisor | 6 — Proyectos e instalaciones | M3 |

---

## Bloque 7 — GIS / Cartografía

| Id | Necesidad | Quién | Bloque | Milestone |
|---|---|---|---|---|
| N032 | Editar geometría y visualizar mapa | Tramitador | 7 — GIS / Cartografía | Opcional (dependiente de Bloque 6) |
| N033 | Consultar vista global de mapa | Supervisor | 7 — GIS / Cartografía | Opcional |

---

## Bloque 8 — Gestión de carga y usuarios

| Id | Necesidad | Quién | Bloque | Milestone |
|---|---|---|---|---|
| N034 | Asignar expedientes a técnicos (uno o varios, mismo interfaz) | Supervisor | 8 — Gestión de carga y usuarios | M2 |
| N036 | Gestionar altas/bajas de usuarios y roles | Supervisor | 8 — Gestión de carga y usuarios | M2 |
| N037 | Consultar estadísticas de carga interna (por técnico/pista/estado, plazos vencidos, antigüedad) | Supervisor | 8 — Gestión de carga y usuarios | M2 |
| N038 | Generar informes de estado de situación bajo demanda para servicios centrales | Supervisor | 8 — Gestión de carga y usuarios | M2 |
| N039 | Exportar datos agregados (Excel/CSV) | Supervisor | 8 — Gestión de carga y usuarios | M2 |
| N040 | Cambiar titularidad de forma masiva en agrupaciones | Supervisor | 8 — Gestión de carga y usuarios | M2 |

---

## Bloque 9 — Listado inteligente

| Id | Necesidad | Quién | Bloque | Milestone |
|---|---|---|---|---|
| N041 | Filtrar y consultar datos agregados por expediente (plazos, tareas activas, escritos pendientes) | Supervisor/Tramitador | 9 — Listado inteligente | M2 |
| N042 | Consultar cola de trabajo priorizada | Tramitador | 9 — Listado inteligente | M2 |
| N043 | Consultar vista global de expedientes para localizar dónde actuar | Administrativo | 9 — Listado inteligente | M2 |
| N044 | Consultar inconsistencias y huérfanos de BD | Admin BDDAT | 9 — Listado inteligente | M2 |

---

## Bloque 10 — Auditoría configurable

| Id | Necesidad | Quién | Bloque | Milestone |
|---|---|---|---|---|
| N045 | Definir qué operaciones/elementos se auditan | Supervisor/Admin | 10 — Auditoría configurable | M3/M5 |
| N046 | Consultar historial por expediente | Tramitador | 10 — Auditoría configurable | M3/M5 |
| N047 | Consultar logs técnicos del sistema | Admin BDDAT | 10 — Auditoría configurable | M3/M5 |
| N075 | Advertir en el momento y dejar constancia automática cuando se actúa sobre un expediente fuera de la propia asignación | Tramitador (advertido); Supervisor/Admin (consultan la constancia) | 10 — Auditoría configurable | M3/M5 |

---

## Bloque 11 — Importación legacy

| Id | Necesidad | Quién | Bloque | Milestone |
|---|---|---|---|---|
| N048 | Cargar datos legacy (Access → schema `legacy`, solo lectura permanente) | Admin BDDAT | 11 — Importación legacy | M1 |
| N049 | Activar expediente legacy individualmente, respetando huecos de numeración AT histórica | Tramitador | 11 — Importación legacy | M1 |
| N050 | Completar campos básicos de expedientes heredados | Tramitador/Administrativo | 11 — Importación legacy | M1 |

---

## Bloque 12 — Manual de usuario

| Id | Necesidad | Quién | Bloque | Milestone |
|---|---|---|---|---|
| N051 | Consultar documentación con ayuda contextual | Supervisor/Tramitador/Administrativo | 12 — Manual de usuario | M3/M5 |
| N071 | Generar y mantener el contenido del manual de usuario | Programador (con IA) | 12 — Manual de usuario | M3/M5 |

---

## Bloque 13 — Mensajería interna

| Id | Necesidad | Quién | Bloque | Milestone |
|---|---|---|---|---|
| N053 | Enviar avisos y delegar tareas al pool de administrativos (no es chat) | Tramitador/Administrativo | 13 — Mensajería interna | M3/M5 |
| N054 | Solicitar alta o cambio de rol | Todos | 13 — Mensajería interna | M3/M5 |
| N055 | Solicitar cambios de plantillas | Tramitador/Administrativo | 13 — Mensajería interna | M3/M5 |
| N056 | Recibir avisos técnicos del sistema | Admin BDDAT | 13 — Mensajería interna | M3/M5 |
| N070 | Solicitar mejoras del manual | Supervisor/Tramitador/Administrativo | 13 — Mensajería interna | M3/M5 |

---

## Bloque 14 — Índice y compilación de expediente

> No es uno de los 14 bloques de §A — apareció como fila propia en Tabla 1 (§D) y de
> forma independiente como aspiración del usuario. No es necesario para el arranque
> en producción, pero sí para poder enviar el expediente completo al exterior
> (recurso de alzada, contencioso) sin depender de que el receptor entre en BDDAT.

| Id | Necesidad | Quién | Bloque | Milestone |
|---|---|---|---|---|
| N057 | Compilar expediente completo (documentos + bitácora + estado) en dossier exportable, autocontenido, para envío al exterior | Supervisor/Tramitador | 14 — Índice y compilación | M5 |

---

## Bloque 15 — Infraestructura técnica y operación

> Necesidades de la aplicación y su ciclo completo (desarrollo → despliegue →
> operación), no del programador como individuo. Visible aunque su cobertura no
> vaya a materializarse siempre en un issue de producto.

| Id | Necesidad | Quién | Bloque | Milestone |
|---|---|---|---|---|
| N058 | Servidor de aplicación operativo, actualizado y con procesos gestionados | IT Admin/Programador | 15 — Infraestructura técnica | M4 |
| N059 | Base de datos PostgreSQL gestionada (usuarios, schemas, rendimiento, actualizaciones) | IT Admin/Programador | 15 — Infraestructura técnica | M4 |
| N060 | Servidor de archivos con estructura, permisos y cuota | IT Admin/Programador | 15 — Infraestructura técnica | M4 |
| N061 | Backups verificados (BD + documentos + servidor) con política de retención | IT Admin/Programador | 15 — Infraestructura técnica | M4 |
| N062 | Seguridad y acceso (SSL, firewall, gestión de secrets, contraseñas) | IT Admin/Programador | 15 — Infraestructura técnica | M4 |
| N063 | Despliegue reproducible de la aplicación | Programador | 15 — Infraestructura técnica | M4 |
| N064 | Monitorización y alertas de disponibilidad | IT Admin/Programador | 15 — Infraestructura técnica | M4 |
| N065 | Acceso a base de datos legacy para la carga inicial | IT Admin | 15 — Infraestructura técnica | M4 |

---

## Bloque 16 — Datos estructurales mínimos para producción

> **Placeholder deliberado, no desglosado.** No existe hoy un documento equivalente
> a la Tabla 1 (§D) del que derivar filas sin inventar contenido. Desglosarlo de
> verdad es el eje "motor — contenido normativo" que
> `PRE-ADR-matriz-cobertura-roles-motor.md` §5 ya señaló como pendiente y distinto
> del eje de rol (filas por trámite/norma, no por rol). Esta fila deja constancia de
> que el hueco existe y está identificado, sin fingir un detalle que no se tiene.

| Id | Necesidad | Quién | Bloque | Milestone |
|---|---|---|---|---|
| N066 | Catálogo estructural mínimo cargado para producción: tipos de ESFTT/trámite/tarea reales, reglas de motor con contenido normativo real, plazos legales reales por tipo, municipios completos | Admin/Supervisor | 16 — Datos estructurales mínimos | M4 |

---

## Hallazgos y preguntas abiertas de este borrador

1. **Asimetría de detalle entre roles** — Supervisor tiene un documento propio
   (`PRE-ADR-supervisor.md`) que ya desglosó sus necesidades en ejes; Tramitador,
   Administrativo y Admin BDDAT no tienen equivalente. Es esperable que necesiten
   más división al revisarlos — se irá viendo.
2. **Bloque 16 es un marcador de una sola fila** — confirmar si se queda así hasta
   la sesión dedicada al eje motor-contenido normativo, o si se profundiza ya.
3. **N046 vs N072 (bitácora/historial)** — auditoría de código confirma que
   *no son* el mismo mecanismo hoy: `bitacora` es un log automático de sistema
   (operación + tabla + registro_id), sin ningún modelo de anotación narrativa
   con autor en ningún punto del código. Se mantienen separadas por describir
   necesidades de datos distintas, con una advertencia: si ambas se construyen,
   es previsible que converjan en la misma pantalla de "historial del
   expediente" — decisión de diseño para cuando toque implementar, no de este
   documento.
4. **`api_bc.py` — discrepancia con memoria de proyecto** — *resuelto en #577*.
   Dos auditorías de código independientes (Bloques 1 y 4) encontraron que
   `app/routes/api_bc.py` seguía registrado como blueprint activo en
   `app/__init__.py` y seguía conteniendo lógica viva (incluido el paso de
   `justificacion` al motor, que la ruta actualmente en uso —`api_expedientes.py`—
   no expone). Ambas cosas eran ciertas y no se contradecían con "muerto desde
   #519": el blueprint estaba montado pero ninguna superficie lo llamaba, y la
   lógica viva de dentro no era la de sus rutas sino la del trámite de consultas
   (organismos, traslados, envío de separatas) más los helpers de bypass, que
   `api_expedientes.py` sí importaba. #577 retira las rutas y el registro, y
   rescata lo vivo a `app/services/consultas_organismos.py` y
   `app/utils/api_respuestas.py`.
5. **N017 y N022 — ¿la misma necesidad aplicada a dos objetivos?** — Carlos
   señala (2026-07-08) que ambas son, en esencia, "tocar algo de emergencia que
   se salte cualquier regla, motor o de cualquier otro tipo" — una operación SQL
   directa contra la BD, no una funcionalidad de la aplicación. Pregunta abierta
   suya, sin resolver aquí: si eso ni siquiera requiere codificarse (sería
   entonces un caso como N065 — necesidad real pero resuelta fuera del código,
   nunca al 100% por la vía de desarrollo), o si merece fusionarse en una sola
   fila. No se fusiona unilateralmente porque el propio Carlos no lo tiene
   decidido.

---

## Ids retirados

Los ids no se reasignan ni se rellenan huecos — se documentan aquí para que un
hueco en la numeración no se lea como un error.

| Id | Motivo |
|---|---|
| N005 | Fusionada en N004. ADR-027 no distingue documentos "auxiliares": la pertenencia al expediente es propiedad del tipo de documento, no de quién lo incorpora — Tramitador y Administrativo cubren la misma necesidad. |
| N035 | Fusionada en N034. Asignar uno o varios expedientes es el mismo interfaz, no dos necesidades distintas. |
| N052 | Trasladada a N070 (Bloque 13 — Mensajería interna). Sin mensajería interna, "solicitar mejoras del manual" no tiene ningún mecanismo real en BDDAT — es un caso más del mismo patrón que N054/N055, no una necesidad aparte del Bloque 12. |
| N014 | Duplicada de N055 (Bloque 13). Confirmado por auditoría de código (sesión 2026-07-08): mismo texto, mismos actores, cero diferencia funcional encontrada — ninguna de las dos tiene mecanismo real hoy. Se mantiene N055 porque "solicitar cambios" es, por naturaleza, un caso de mensajería (Bloque 13), no de escritos (Bloque 3). |
| N030 | Retirada por decisión directa de Carlos (2026-07-08): "no sé qué es". La auditoría de código había encontrado que bajo ninguna lectura razonable existe hoy una acción distintiva de "revisar/auditar proyecto" del Supervisor — pero en vez de forzar una redefinición, se retira sin más. |

---

Basado en `PLAN_ESTRATEGIA.md` (§A/§D/§E/§G), el detalle ya existente para
Supervisor (`PRE-ADR-supervisor.md`), `ESTUDIO_USUARIO.md` y ADR-027 — sesión
2026-07-08. N073-N077 descubiertas por auditoría directa de código (`app/`),
misma sesión — ver `MATRIZ_COBERTURA_BDDAT.md` para su cobertura. N078-N081
descubiertas el 2026-07-09 al mapear los 96 issues abiertos contra este
documento para el etiquetado retroactivo `necesidad:N0XX` (ADR-031 §"Próximos
pasos") — bloque asignado por Carlos, sin motivación explícita por ser
deducible del patrón de necesidades hermanas del mismo bloque. Pendiente de
auditar su % real en `MATRIZ_COBERTURA_BDDAT.md`. N085 añadida el 2026-08-05
al cerrar #728 (ADR-039): el issue detectó que los escritos generados
necesitan datos del órgano emisor (consejería, sede, firmantes) que no
encajaban en ninguna necesidad existente — N081 es el catálogo DIR3 de
organismos *externos*, no los datos de la propia casa.
