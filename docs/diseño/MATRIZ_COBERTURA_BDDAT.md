# Matriz de cobertura — BDDAT

> **Naturaleza de este documento:** vivo, se actualiza en cada issue cerrado (o en
> cualquier cambio real de código que afecte a una fila). Es el "plan maestro" —
> por cada necesidad, cuánto está cubierto y qué falta para el 100%. Sin nombres
> ni números de issue: eso vive en GitHub, se busca por label `necesidad:N0XX`
> cuando toque decidir "trabajad esta celda ya".
> **Fuente del %:** código real (`app/`, `migrations/`, `scripts/`, config de
> despliegue) — nunca issues ni documentos de diseño, que quedan desactualizados
> con frecuencia en este proyecto.
> **Última auditoría completa:** 2026-07-08 (primera pasada — 6 agentes en
> paralelo sobre el código + auditoría directa de infraestructura/datos
> estructurales).
> Columna 1 (Id) compartida con `DETALLE_NECESIDADES_BDDAT.md` — acude allí para
> el alcance completo de cualquier necesidad.

---

## Lectura rápida

Antes de la tabla completa, lo que más destaca de esta primera pasada:

- **Peor de lo que "está abierto" sugería:** varios mecanismos que la memoria del
  proyecto daba por vivos resultaron estar desconectados de la ruta real que usa
  el usuario — el backend existe, pero nadie puede llegar a él desde la interfaz.
  Ver N012/N013 (modal de generar escrito huérfano), N017 (escape de motor sin
  conectar a la ruta viva), N040 (cambio de titularidad sin ningún caller).
- **Un ADR "Adoptado" con 0% de implementación real:** N057 — ADR-027 dice
  "Adoptada" en su cabecera, pero su propio plan de implementación nunca se
  ejecutó en código.
- **Una interfaz que miente:** N054 — el botón de "solicitar cambio de rol"
  muestra un mensaje de éxito aunque no persiste nada (`# TODO` explícito en el
  código).
- **El propio código ya se declara incompleto:** el hub del Supervisor
  (`app/modules/supervisor/templates/supervisor/index.html`) tiene varias
  tarjetas marcadas `is-soon` con su issue de referencia (#170/#479 motor,
  #256 auditoría, #74 semáforos, #76 informes, #295 operaciones masivas) — no
  hace falta abrir el código para saber que esas piezas no están: lo dice la
  propia pantalla.
- **Mensajería interna (Bloque 13) y Manual (Bloque 12): 0-15% real**, confirmado
  con evidencia negativa exhaustiva, no por falta de búsqueda.
- **Mejor de lo esperado:** N067 (festivos) tiene un comando real
  (`flask inhabiles importar`) contra la API oficial de la Junta, con aviso
  proactivo si falta el año siguiente — no es solo un fichero subido a mano.
- **5 necesidades nuevas** aparecieron auditando código que no tenían fila propia
  (N073-N077 en `DETALLE_NECESIDADES_BDDAT.md`) — la más llamativa: una columna
  `hash_md5` para detectar documentos duplicados que nadie calcula nunca (N077).
- **1 duplicado encontrado y resuelto:** N014 y N055 eran la misma necesidad
  escrita dos veces — retirada N014.

---

## Bloque 1 — Tramitación ESFTT

| Id | % Cobertura | Qué falta |
|---|---|---|
| N001 | 95% | Nada funcionalmente relevante — es la zona más madura del código (CRUD completo de los 4 niveles ESFTT + isla React sobre ADR-016). |
| N002 | 90% | Confirmados permisos y la cola dedicada del Administrativo; sin verificar el detalle interno de esa cola ni su UI consumidora al 100%. |
| N003 | 90% | El borrado consulta correctamente al motor antes de ejecutarse, con escape justificado y registrado en bitácora. Hallazgo colateral sin resolver: `api_bc.py` sigue montado como blueprint activo pese a estar documentado como código muerto — sin confirmar si recibe tráfico real. |
| N069 | 95% | Nada relevante — wizard de 3 pasos completo con commit transaccional único. |
| N072 | 20% | Lo que existe es un log automático de sistema *por usuario* (feed de actividad, no narrativo). Falta: vista/endpoint filtrado por expediente, capacidad de anotación libre del Tramitador no ligada a un bypass del motor, y UI de consulta para Supervisor/Administrativo. |
| N073 | 50% | El modelo y un consumidor real (verificación de representación en el wizard de alta) están confirmados. Sin verificar si existe una pantalla de gestión (alta/consulta/revocación) del catálogo de autorizaciones fuera de ese consumo puntual. |

## Bloque 2 — Sistema documental

| Id | % Cobertura | Qué falta |
|---|---|---|
| N004 | 50% | La organización automática en carpeta solo existe para documentos generados por el propio sistema (escritos); lo que Tramitador/Administrativo incorporan a mano solo se registra donde ya estuviera, sin mover ni copiar nada. |
| N006 | 100% | Nada — consulta, descarga y protección contra path traversal cubiertas. |
| N007 | 0% | No existe ningún mecanismo que compruebe accesibilidad de URLs/ficheros de forma proactiva, ni por expediente ni global — solo hay comprobaciones reactivas puntuales al pedir un documento concreto. |
| N008 | 75% | Mecanismo de incorporación genérico + catálogo de tipos `JUSTIFICANTE_*` ya existen. Falta cualquier verificación real de que el documento lleve una firma válida — hoy es solo clasificación por tipo. |
| N009 | 25% | La convención de carpeta predecible solo se aplica a documentos generados por el sistema. Falta forzarla también en la incorporación manual, y generar un manifest/índice en disco por expediente — sin BD, una carpeta es hoy un montón de ficheros sin diferenciar. |
| N076 | 50% | La señal de "sin vincular a tarea" existe y se muestra como columna en el listado general de documentos del pool. Falta una vista dedicada de triage (radar) que la use como filtro/prioridad, no solo como dato de contexto. |
| N077 | 0% | La columna de verificación de integridad existe en el modelo pero ningún punto de código la calcula nunca — funcionalidad diseñada y nunca conectada. |

## Bloque 3 — Generación de escritos

| Id | % Cobertura | Qué falta |
|---|---|---|
| N010 | 90% | CRUD de plantillas completo. Falta CRUD de consultas nombradas reutilizables en plantillas — hoy solo se pueden dar de alta por BD/migración directa. |
| N011 | 0% | No existe ninguna rutina de análisis estático de la plantilla; el único aviso de "hueco" es reactivo, al fallar la generación contra un expediente real. |
| N012 | 50% | El backend de generación está prácticamente completo y es sofisticado. El modal/wizard que lo dispara desde la interfaz existe como fichero pero no está enganchado a ninguna vista real — hoy un Tramitador no puede llegar a esta función desde la UI. |
| N013 | 50% | Mismo caso que N012 — mismo backend, mismo modal sin enganchar. |

## Bloque 4 — Motor de reglas y configuración estructural

| Id | % Cobertura | Qué falta |
|---|---|---|
| N015 | 85% | El motor evalúa y nunca degrada a "permitido" en silencio; los bloqueos llegan con motivo y norma legibles. Sin verificar exhaustivamente que absolutamente todos los puntos de cierre llamen al invariante correspondiente. |
| N016 | 15% | El modelo de reglas y el motor de evaluación están completos y en uso real — pero cero interfaz de alta/edición/baja. El propio hub del Supervisor lo marca "próximamente" (#170/#479). |
| N017 | 40% | El escape de emergencia (saltar el motor con justificación registrada en bitácora) está construido y funciona en el servicio — pero la ruta actualmente en uso no extrae ni pasa ese parámetro. Es reconexión, no reconstrucción. |
| N018 | 20% | La lectura y aplicación del modo global (bloquear/advertir/inactivo) está viva en el flujo real. Falta el selector de escritura — hoy solo se puede cambiar directamente en BD. |
| N019 | 0% | El catálogo se puebla solo por migración; cero interfaz de gestión. |
| N020 | 0% | Lo único que existe es búsqueda de autocompletado para formularios (solo lectura) — no hay ninguna gestión de cambios sobre la tabla. |
| N021 | 0% | Las rutas del filesystem son variables de entorno leídas una vez al arrancar; no hay ni siquiera un modelo de datos que sostenga un futuro CRUD. |
| N022 | 0% | No existe ningún mecanismo de sobreescritura equivalente al del motor (N017) aplicado al catálogo estructural. |

## Bloque 5 — Plazos legales

| Id | % Cobertura | Qué falta |
|---|---|---|
| N023 | 5% | El catálogo de plazos es rico y está en uso real en el cálculo, pero cero interfaz de configuración — peor situación que N016: ni siquiera tiene un issue de referencia asignado en el propio hub. |
| N024 | 55% | El dato de plazo/vencimiento por tarea es correcto y se agrega hasta expediente, pero vive embebido en el árbol y el listado general — falta una vista dedicada de "mis vencimientos". |
| N025 | 20% | Solo hay un número agregado suelto dentro del panel de estadísticas. El dashboard de alertas dedicado sigue marcado "próximamente" (#74) en el propio hub. |
| N026 | 50% | Comparte la misma infraestructura de lectura que N024 — la diferencia es solo de permisos de rol, no de funcionalidad. Sin verificar el detalle de qué ve exactamente el Administrativo frente al Tramitador. |
| N027 | 70% | El cálculo de intervalos de suspensión es automático (se infiere del árbol documental, sin toggle manual) y ya se aplica al plazo real. Falta una superficie visual explícita que diga "este elemento tiene una suspensión activa" — hoy es invisible salvo por ver que la fecha límite es más tardía. |
| N067 | 80% | Existe un comando real que importa el calendario desde la API oficial de la Junta de Andalucía, con aviso proactivo si falta el año siguiente. Sigue siendo un comando de servidor (CLI), no un botón en la interfaz web. |
| N068 | 90% | Motor de cálculo de plazo muy sólido (los 4 tipos de unidad, prórroga a hábil, suspensiones). Sin verificación exhaustiva de casos límite (fin de mes, años bisiestos) contra tests automatizados. |

## Bloque 6 — Proyectos e instalaciones

| Id | % Cobertura | Qué falta |
|---|---|---|
| N028 | 10% | La edición de elementos técnicos anidados (líneas, CT, subestaciones) está **explícitamente deshabilitada en la interfaz** ("Próximamente"). Solo existe un esqueleto de identidad/contención sin ningún campo técnico ni formulario. |
| N029 | 100% | Nada — todos los campos editables del proyecto tienen representación en el formulario, incluida la edición de municipios. |
| N030 | 10% | Pendiente de que Carlos decida qué significa esta necesidad — ver `DETALLE_NECESIDADES_BDDAT.md`, Hallazgo 3: bajo ninguna lectura razonable hay hoy una acción distintiva de "revisar/auditar proyecto" separada de la visibilidad general o del mecanismo de N074 (que hoy ejecuta el Tramitador, no el Supervisor). |
| N031 | 10% | El hueco de esquema para vincular activos técnicos al estado administrativo del expediente ya existe en el modelo — pero nada escribe en él, y las resoluciones no enlazan con ningún elemento técnico concreto. |
| N074 | 90% | CRUD completo del catálogo de apartados técnicos exigidos por normativa (alta, edición con condiciones anidadas, activar/desactivar). Sin verificar matices menores de UI. |

## Bloque 7 — GIS / Cartografía

| Id | % Cobertura | Qué falta |
|---|---|---|
| N032 | 0% | Todo — sin modelo de geometría, sin librería de mapas, sin ruta ni template. Confirmado tras descartar falsos positivos de búsqueda. |
| N033 | 0% | Todo — ninguna vista muestra expedientes/proyectos sobre un mapa, para ningún rol. |

## Bloque 8 — Gestión de carga y usuarios

| Id | % Cobertura | Qué falta |
|---|---|---|
| N034 | 50% | La asignación de un expediente a la vez, desde su formulario individual, funciona. Falta selección múltiple / asignación en lote — el propio hub del Supervisor lo marca "próximamente" (#295). |
| N036 | 90% | Alta, edición, activar/desactivar usuarios y asignación de roles, con protecciones (no autodesactivarse, no quitar el último Admin). El catálogo de tipos de rol en sí es fijo por diseño (probablemente intencional, no un hueco real). |
| N037 | 50% | KPIs, desglose por estado y por técnico ya construidos y visibles (isla React de estadísticas). Falta desglose por pista y por antigüedad — el propio hub lo marca "próximamente" (#256). |
| N038 | 0% | Todo — sin servicio, sin ruta, solo una tarjeta "próximamente" (#76) en el hub. |
| N039 | 0% | Todo — ningún exportador de datos agregados encontrado en el código. |
| N040 | 0% | El modelo de histórico de titulares está completo, con el método que haría el cambio — pero sin ningún punto del código que lo invoque. Ni siquiera existe el cambio individual conectado a una ruta, y mucho menos el masivo. |

## Bloque 9 — Listado inteligente

| Id | % Cobertura | Qué falta |
|---|---|---|
| N041 | 75% | Filtros, paginación y estado por pista de cada solicitud, construidos y en uso. Falta un contador dedicado de "escritos pendientes" — hoy se infiere indirectamente de los códigos de pista. |
| N042 | 30% (verificación incompleta) | La única cola de trabajo real encontrada es la del Administrativo, no la del Tramitador — y ninguna de las dos ordena por urgencia/plazo, solo por antigüedad de alta. No se descartó del todo que exista algo específico para Tramitador fuera de los puntos de partida explorados. |
| N043 | 75% (verificación incompleta) | Probablemente reutiliza el mismo listado de seguimiento que Supervisor/Tramitador (coherente con el patrón de fuente única de verdad del proyecto), pero no se confirmó si existe alguna vista específicamente optimizada para el Administrativo. |
| N044 | 25% | Solo cubre catálogo estructural (códigos de tipos ausentes), comprobado una vez al arrancar y visible solo en el log del servidor — no huérfanos/referencias rotas genéricos de BD, y no consultable bajo demanda desde la aplicación. |

## Bloque 10 — Auditoría configurable

| Id | % Cobertura | Qué falta |
|---|---|---|
| N045 | 0% | No existe ningún panel de configuración. El registro en bitácora está hardcoded a dos casos muy concretos (escape de motor, acceso a expediente ajeno) — la inmensa mayoría de mutaciones normales no se auditan hoy. |
| N046 | 15% | El único endpoint de consulta filtra por usuario ("mis últimas 50 acciones"), no por expediente. Reconstruir el historial de un expediente concreto exigiría además un join que hoy no existe, porque las mutaciones se registran por tabla afectada, no por expediente. |
| N047 | 0% | Todo — logging estándar de Python sin persistencia estructurada ni panel de consulta. |
| N075 | 85% | Construido y funcionando: aviso automático + registro en bitácora cuando un Tramitador actúa sobre expediente ajeno. Sin verificar matices de UI del indicador. |

## Bloque 11 — Importación legacy

| Id | % Cobertura | Qué falta |
|---|---|---|
| N048 | 0% | Confirmado sin ambigüedad — sin schema `legacy`, sin segundo bind de base de datos, sin script de importación desde Access. La única mención de "legacy" en el código es texto descriptivo aspiracional en un seed de roles. |
| N049 | 15% | La parte de respetar huecos de numeración histórica está resuelta (contador gapless con instrucción de arranque documentada). La operación de "activar" en sí no existe — coherente con que no hay ningún dato legacy real que activar (N048 = 0%). |
| N050 | 35% | El formulario genérico de edición de expediente permite completar los mismos campos que tendría uno heredado, pero no está pensado ni verificado para ese caso — y hoy no hay ningún expediente real al que aplicarlo. |

## Bloque 12 — Manual de usuario

| Id | % Cobertura | Qué falta |
|---|---|---|
| N051 | 0% | Todo — confirmado con búsqueda negativa exhaustiva. Ninguna ruta `/manual`, `/ayuda` ni `/help` registrada. |
| N071 | 0% | Todo — ningún contenido ni mecanismo de autoría/mantenimiento del manual en código. |

## Bloque 13 — Mensajería interna

| Id | % Cobertura | Qué falta |
|---|---|---|
| N053 | 15% | La cola compartida de tareas es autoservicio (cualquiera se autoasigna trabajo pendiente) — falta la mitad "dirigida": que alguien empuje una tarea concreta a una persona concreta, y una capacidad de aviso con destinatario. Ninguna de las dos tiene persistencia hoy. |
| N054 | 15% | La ruta está enganchada y alcanzable desde la interfaz, pero el backend no hace nada real: muestra un mensaje de éxito sin persistir ninguna solicitud (`# TODO` explícito en el propio código). |
| N055 | 0% | Todo — ningún canal de petición dirigido al Supervisor, en ningún punto del código. |
| N056 | 0% | Todo — sin segmentación de avisos técnicos a Admin BDDAT en ningún punto. |
| N070 | 0% | Depende de que exista el manual (N051/N071) y un canal de mensajería funcional (N053-056) — ninguno de los dos existe hoy. |

## Bloque 14 — Índice y compilación de expediente

| Id | % Cobertura | Qué falta |
|---|---|---|
| N057 | 0% | ADR-027 figura como "Adoptada" pero su plan de implementación nunca se ejecutó: no existe la columna que decide qué documentos integran el expediente, no existe la consulta que los recopila, no existe generador de dossier alguno (foliado, índice numerado, empaquetado). El diseño existe; el código no. |

## Bloque 15 — Infraestructura técnica y operación

| Id | % Cobertura | Qué falta |
|---|---|---|
| N058 | 10% | Solo el entrypoint mínimo de desarrollo (`run.py`) y dependencias declaradas. Sin gestión de procesos de producción (gunicorn/systemd) en el repo. |
| N059 | 45% | La gestión de esquema vía migraciones Alembic está muy madura (~90 migraciones). La gestión del propio servidor de BD (usuarios, rendimiento, actualizaciones del motor) es responsabilidad externa al repo, sin rastro aquí. |
| N060 | 0% | Todo — y ni siquiera el diseño está cerrado: el propio documento de estrategia lo marca como "decisión de arquitectura abierta". |
| N061 | 0% | Todo — ningún script de backup en el repositorio. |
| N062 | 20% | Buena higiene de código (secretos vía variables de entorno, `.env` excluido de git). El propio `SECURITY.md` declara explícitamente que SSL, firewall y credenciales de producción son responsabilidad del despliegue, no del repositorio. |
| N063 | 15% | El único procedimiento documentado es manual (clonar, crear venv, migrar, arrancar). El único workflow de CI/CD del repo despliega una presentación estática, no la aplicación. |
| N064 | 0% | Todo — sin endpoint de salud ni integración con ningún servicio de monitorización encontrada. |
| N065 | 0% | No es una carencia de desarrollo — es un acto puntual de IT (entregar el fichero Access) que ocurrirá cuando toque la migración real, no algo que el código pueda resolver. |

## Bloque 16 — Datos estructurales mínimos para producción

| Id | % Cobertura | Qué falta |
|---|---|---|
| N066 | 35% | El mecanismo de carga de datos reales vía migración existe y se ha usado de forma sostenida (decenas de migraciones de seed para tipos, plazos, normas, organismos). Falta: (a) no se detectó ninguna migración que cargue el catálogo completo de municipios andaluces — la tabla se crea vacía; (b) la completitud del contenido normativo frente a lo que exige la legislación por tipo de trámite no está verificada — es el eje "motor-contenido normativo" que sigue pendiente de su propia auditoría en profundidad. |

---

## Necesidades sin cobertura evaluada aquí

- **N030** — cobertura provisional (10%) sujeta a que Carlos resuelva qué significa la fila (ver Hallazgo 3 de `DETALLE_NECESIDADES_BDDAT.md`).
- **N042, N043** — % marcado explícitamente como verificación incompleta por el agente que los auditó; confirmar antes de tratarlos como definitivos si se van a usar para decidir prioridad.

## Referencia rápida — necesidades a 0%

N007, N011, N019, N020, N021, N022, N032, N033, N038, N039, N040, N045, N047,
N048, N051, N055, N056, N057, N060, N061, N064, N065, N070, N071, N077 — 25 de
73 necesidades activas sin ninguna cobertura real detectada.

---

Metodología completa de esta auditoría (6 agentes en paralelo por bloques
temáticos + auditoría directa de infraestructura y datos estructurales) y
evidencia detallada (archivo:línea) de cada fila: sesión de diseño 2026-07-08.
No se traslada aquí para no romper la naturaleza de "plan maestro" de este
documento — disponible bajo petición.
