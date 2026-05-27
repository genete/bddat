# ESTRATEGIA Y VISIÓN — BDDAT

> **Propósito:** Documento de visión estable del sistema. Define actores, bloques funcionales,
> clasificación estratégica hacia producción y principios de trabajo.
> Cambia solo si cambia la estrategia, no al cerrar issues o milestones.
>
> **Última revisión:** 2026-04-11

---

## A. Visión del proyecto — qué hace BDDAT

14 bloques funcionales que componen el sistema completo:

1. **Tramitación ESFTT** — crear, editar, borrar y avanzar Solicitudes/Fases/Trámites/Tareas dentro de un expediente. El borrado está condicionado por el motor de reglas (ej: expediente comunicado al exterior no se puede borrar; tarea equivocada sin comunicar sí se puede).

2. **Sistema documental** — gestión de documentos: subida, almacenamiento en servidor de archivos (BD guarda la URL), organización automática en rutas predeterminadas según ESFTT, asociación a elementos. El sistema debe ser reconstruible sin BDDAT. Incluye incorporación de documentos firmados externamente y justificantes.

3. **Generación de escritos** — plantillas de documentos (Word/ODT/HTML), relleno automático de variables del expediente, generación de PDF/Word. Las plantillas las crea y gestiona el Supervisor. Tramitador y Administrativo generan escritos a partir de ellas.

4. **Motor de reglas** — validaciones de flujo: qué se puede crear/iniciar/cerrar y cuándo, según tipos. No bloquea silenciosamente; informa qué falta. El borrado de registros está sujeto a sus reglas.

5. **Plazos legales** — dos planos: (a) reglas de configuración (qué plazo corresponde a cada tipo de ESFTT, en días hábiles/naturales, con festivos) y (b) visibilidad (semáforos, alertas, días pendientes por actor). Incluye suspensión de plazos.

6. **Proyectos e instalaciones** — dos planos: (a) edición/modificación/visión de proyectos y sus elementos técnicos anidados (líneas, CT, subestaciones...); (b) relación de los elementos del proyecto con el estado del expediente y las resoluciones (punto denso, desarrollo posterior). GIS es 100% dependiente de Proyectos.

7. **GIS / Cartografía** — geolocalización de elementos eléctricos, visor de mapa con capas (IGN, catastro), edición de geometría. Dependiente de C.6.

8. **Configuración de reglas y estructura** — CRUD de tablas maestras (tipos de ESFTT, municipios, rutas del filesystem, plazos por tipo, reglas de tramitación). Gestionado por el Supervisor. Cambia poco (no cambia la legislación todos los días).

9. **Gestión de carga y usuarios** — asignaciones de expedientes, estadísticas de carga, exportación de datos agregados, gráficos, altas/bajas de usuarios, gestión de roles. Dominio del Supervisor.

10. **Listado inteligente** — filtros avanzados, datos agregados por expediente (plazos, tareas activas, escritos pendientes), cola de trabajo priorizada por actor. Admin tiene vista adicional de inconsistencias/huérfanos de BD.

11. **Auditoría configurable** — no hardcodeada. Panel donde Supervisor y Admin definen qué operaciones CRUD sobre qué elementos se auditan y cuándo se violan reglas del motor. Historial visible en V4 del expediente.

12. **Importación legacy** — schema `legacy` en PostgreSQL (espejo de Access, solo lectura permanente). Activación individual a `public` por el tramitador, respetando huecos de numeración AT histórica. Carga inicial única realizada por Admin.

13. **Manual de usuario** — documentación HTML enlazada. Acceso contextual desde elementos del interfaz (ayuda integrada con anclas). Supervisor, Tramitador y Administrativo son consumidores y peticionarios de mejoras via mensajería. Lo implementa el Programador con la IA.

14. **Mensajería interna** — comunicación entre usuarios: solicitudes de alta, delegación de tareas a pool de administrativos, peticiones de cambio de plantillas, avisos entre roles. No es un chat; es un sistema de avisos y delegación de tareas.

---

## B. Actores del sistema

### B.1 Externos a la administración
*(interacción indirecta — el usuario funcionario es el intermediario)*

1. **Administrado / titular / solicitante** — quien promueve el expediente. Sube documentos a plataforma externa; el funcionario los incorpora a BDDAT.
2. **Organismos consultados** — reciben consultas obligatorias (REE, distribuidoras, ayuntamientos, diputaciones, Ministerio...).
3. **Organismos de publicación** — BOE, BOJA, BOP, tablón de anuncios.
4. **Alegantes** — presentan alegaciones en período de información pública.
5. **Órgano ambiental** — evaluación de impacto (puede ser externo o interno según estructura).
6. **Órganos de recursos** — tribunales, órgano de recursos de alzada, juzgados contencioso-administrativos. Solicitan el expediente completo (índice + compilación).
7. **Empresas / técnicos** — instaladores, ingenieros, proyectistas que firman documentación técnica.

### B.2 Internos de negocio

8. **Tramitador** — impulsor de expedientes. Realiza cualquier tarea sobre ESFTT (excepto borrado si las reglas no lo permiten). Toma decisiones de prioridad y acción sobre sus expedientes asignados.

9. **Supervisor** — dos funciones distintas:
   - **(A) Configuración:** administra reglas de negocio, tablas maestras, plantillas de escritos. Cambios poco frecuentes. No toca expedientes.
   - **(B) Gestión de carga:** reparto de tareas, estadísticas, exportaciones, gráficos, gestión de usuarios y roles.

10. **Administrativo** — tareas auxiliares sin capacidad de decisión del tramitador: rellena fechas de publicaciones, sube documentos a cualquier expediente, genera escritos estándar, avanza tramitación. Recoge tareas del pool de mensajería.

11. **Admin BDDAT** — rol técnico dentro de la aplicación: gestiona inconsistencias de BD, URLs rotas, documentos huérfanos, carga legacy (una sola vez), sobreescritura de emergencia en motor de reglas.

### B.3 Técnicos

12. **Administrador informático (IT)** — gestión de infraestructura a demanda o con rutinas integradas. No involucrado en el día a día.

13. **Programador / desarrollador** — mantiene y evoluciona el sistema.

14. **IA** — asiste al programador en desarrollo. Potencialmente en uso futuro (análisis, consultas).

---

## C. Persistencia del sistema

| Capa | Qué contiene | Condición |
|------|-------------|-----------|
| **PostgreSQL schema `public`** | Datos operacionales (ESFTT, entidades, proyectos, documentos, usuarios), tablas maestras, históricos y auditoría | Sistema no funciona sin esto |
| **PostgreSQL schema `legacy`** | Espejo de Access, solo lectura permanente | Solo lectura tras carga inicial |
| **Repositorio (código fuente)** | Modelos, rutas, templates Jinja2, CSS/JS, migraciones Alembic | Sistema no funciona sin esto |
| **Servidor de archivos** | Ficheros binarios de documentos del expediente. BD guarda la URL. El expediente debe ser reconstruible sin BDDAT. | Sistema funciona parcialmente sin documentos, pero son centrales al flujo |
| **Plantillas de escritos** | Ficheros base para generación de documentos (Word/ODT/HTML) | Sin ellas, la generación no funciona; el resto sí |
| **Manual de usuario** | Páginas HTML enlazadas con ayuda contextual | El sistema funciona sin él |
| **Configuración de entorno** | `.env`, nginx, gunicorn | Necesario para arrancar; no es dato de negocio |

**Decisión de arquitectura abierta:** Organización del servidor de archivos. BDDAT debe automatizar la copia del fichero desde origen (ej. carpeta de descargas) a ruta predeterminada según el ESFTT donde se inserta. Las rutas son configurables en tablas maestras. La estructura de carpetas debe ser predecible y reproducible sin BDDAT.

---

## D. Tabla 1 — Actores de negocio × Funciones → Interfaz web/flujo

| Función | Admin BDDAT | Supervisor | Tramitador | Administrativo |
|---|---|---|---|---|
| **Tramitación ESFTT** | — | — | V3 acordeón: crea, edita, avanza, cierra ESFTT; borrado condicionado por motor de reglas | V3: tareas auxiliares asignadas (rellenar fechas, avanzar estado de tareas concretas) |
| **Sistema documental** | Panel técnico: gestión de URLs rotas, documentos huérfanos | V3/V4: consulta y descarga | V3 + modal: incorpora fichero desde carpeta local, BDDAT copia a ruta según ESFTT y registra URL | V3 + modal: igual que tramitador para documentos auxiliares |
| **Generación de escritos** | — | Panel supervisión: crea, modifica y gestiona repositorio de plantillas; revisa borradores | V3: genera escrito desde plantilla, descarga borrador y versión firmada; solicita cambios via mensajería | V3: genera escritos y avanza tramitación; solicita cambios via mensajería |
| **Motor de reglas** | Panel técnico: sobreescritura de emergencia | Panel supervisión (A): configura reglas por tipo de expediente | Recibe avisos y validaciones inline; borrado sujeto a reglas | Recibe avisos si sus acciones los disparan |
| **Plazos legales** | — | Panel supervisión (A): define plazos y festivos por tipo ESFTT; (B): dashboard de alertas de toda la unidad | V2 semáforo + V3 detalle: plazos y vencimientos de sus expedientes | V2: información de plazos (lectura) |
| **Proyectos e instalaciones** | — | V4 proyecto: revisión | V4 proyecto + tab instalación: describe y edita elementos técnicos anidados | V4 proyecto: datos básicos (denominación, municipio...) |
| **GIS / Cartografía** | — | Visor mapa: vista global | Tab mapa en V4 proyecto: edita geometría, visualiza | — |
| **Config. reglas y estructura** | Panel técnico: sobreescritura de emergencia técnica | Panel supervisión (A): CRUD tablas maestras (tipos, municipios, rutas filesystem, plazos, reglas de tramitación) | — | — |
| **Gestión de carga y usuarios** | — | Panel supervisión (B): asignaciones, estadísticas, exportación, gráficos, gestión de usuarios y roles | — | — |
| **Listado inteligente** | Panel técnico: inconsistencias y huérfanos de BD | V2 avanzado: filtros, asignación, cola de trabajo de la unidad, exportación, estadísticas | V2: sus expedientes + cola de trabajo personal | V2: todos los expedientes para localizar donde actuar |
| **Auditoría configurable** | Panel técnico: logs técnicos del sistema | Panel supervisión: define qué operaciones/elementos se auditan; V4 expediente (tab historial) | V4 expediente (tab historial): historial de sus expedientes | — |
| **Importación legacy** | Panel técnico: carga única Access → schema `legacy` (solo lectura permanente) | — | V3: revisa y completa expedientes heredados asignados | Rellena campos básicos de expedientes heredados |
| **Manual de usuario** | — | Consulta; petición de mejoras via mensajería | Consulta + ayuda contextual desde ❓ en elementos del interfaz; petición de mejoras via mensajería | Consulta + ayuda contextual; petición de mejoras via mensajería |
| **Índice y compilación** | — | V4 expediente: genera para cualquier expediente | V4 expediente: genera índice + PDF compilado | — |
| **Mensajería interna** | Recibe avisos técnicos del sistema | Recibe solicitudes de alta, peticiones de cambio de plantillas, mensajes de unidad; gestiona pool de tareas | Envía/recibe mensajes; delega tareas al pool de administrativos; solicita cambios de plantillas | Recibe tareas del pool, las recoge y completa; solicita cambios de plantillas |

---

## E. Tabla 2 — Infraestructura × Actores técnicos → Interfaz técnica

| Infraestructura | IT Admin | Programador | IA |
|---|---|---|---|
| **Servidor de aplicación** | Instala SO, nginx; gestiona procesos (systemd); aplica actualizaciones de seguridad del SO | Configura gunicorn y entorno virtual; gestiona arranque/parada de la app | Asiste en configuración de nginx, scripts de arranque |
| **Base de datos PostgreSQL** | Instala PostgreSQL; crea usuarios y schemas; monitoriza rendimiento; aplica actualizaciones de PG | Crea y aplica migraciones Alembic; gestiona schemas `public` y `legacy`; queries de diagnóstico | Asiste en diseño de migraciones, optimización de queries, diagnóstico |
| **Servidor de archivos** | Crea estructura de carpetas raíz; establece permisos y cuota de disco | Configura rutas base en `.env`; implementa tablas de rutas en BD | Asiste en diseño de la estructura de carpetas |
| **Backups** | Configura y ejecuta backups automáticos (BD + documentos + servidor); política de retención — integrado en su sistema habitual | Documenta qué necesita backup; verifica restauración | Asiste en diseño de estrategia de backup |
| **Seguridad y acceso** | Certificados SSL, firewall, usuarios del servidor, política de contraseñas, acceso SSH | Gestiona `.env` y secrets; revisión de seguridad de la aplicación | Asiste en revisión de seguridad del código |
| **Despliegue de la aplicación** | A demanda: reinicia servicios si falla algo en producción | Git pull en producción, restart gunicorn/nginx, aplica migraciones pendientes, verifica logs post-deploy | Asiste en scripts de deploy y checklist de despliegue |
| **Herramientas de desarrollo** | — | Python/venv, Git, IDE, cliente PostgreSQL, navegador; Claude Code CLI | Claude Code: asistencia directa en el entorno de desarrollo |
| **Dependencias del sistema** | Instala en servidor libs nativas que la app requiere (LibreOffice headless u otras) | Gestiona `requirements.txt`; resuelve conflictos de versiones; documenta dependencias del SO | Asiste en selección de librerías y resolución de dependencias |
| **Monitorización** | Configura alertas de recursos (disco, CPU, RAM); monitoriza disponibilidad del servicio | Gestiona logs de Flask; configura nivel de logging; revisa errores en producción | Asiste en interpretación de logs y diagnóstico de errores |
| **Base de datos legacy** | Proporciona acceso al fichero Access (mdb/accdb); una sola vez | Escribe y ejecuta script de importación a schema `legacy`; gestiona permisos de solo lectura | Asiste en el script de migración y mapeo de campos |

---

## F. Decisiones de arquitectura abiertas

> La columna *Afecta a* puede estar desactualizada — es un dato operacional
> que debería vivir en los issues y documentos de diseño pertinentes.
> Consultarlos para el estado real de cada decisión.

| Decisión | Opciones | Afecta a |
|---|---|---|
| Motor de plantillas de escritos | python-docx (Word) / Jinja2 sobre ODT / WeasyPrint (HTML→PDF) | Bloque 3 |
| Almacenamiento físico de documentos | Filesystem local / NAS / S3-compatible | Bloques 2, 3 |
| Rutas del filesystem | Estructura de carpetas configurable en tablas maestras; BDDAT automatiza la copia | Bloque 2, 8 |
| Modelo de elementos eléctricos | Genérico con JSON / Tablas específicas por tipo | Bloque 6, 7 |
| PostGIS vs coordenadas simples | PostGIS completo / lat+lon numérico | Bloque 7 |
| Plazos: suspensión | Modelo de eventos de suspensión/reanudación / solo fecha_límite estática | Bloque 5 |
| Auditoría: granularidad | Configurable por supervisor/admin en panel / hardcodeada | Bloque 11 |
| Mensajería interna | Modelo propio en BD / librería externa | Bloque 14 |

---

## G. Clasificación de los 14 bloques — Camino a producción

> **Criterio de clasificación:** qué ocurre si el sistema entra en producción *sin* ese bloque.
>
> - **Bloqueante** → milestone M1. Sin él, producción es imposible o el abandono del sistema anterior es inviable.
> - **Necesario** → milestone M2. Producción posible con workaround, pero el workaround no aguanta más de semanas.
> - **Post-producción** → milestones M3/M5. Puede añadirse después de arrancar sin comprometer la misión principal.
> - **Pre-producción técnica** → milestone M4. No es funcionalidad; son condiciones de despliegue (infraestructura, seguridad, legacy).
> - **Opcional** — aporta valor pero no está en el camino crítico de ningún milestone.
>
> **Nota sobre Motor de Reglas (4) y Plazos (5):** No son bloqueantes para el arranque —los
> funcionarios llevan décadas tramitando sin enforcement automático, y la GuíaGeneral establece
> explícitamente una Fase 2 sin restricciones activas. Sin embargo, **su estudio arquitectónico
> es previo a producción**: las decisiones de modelo de datos y estructura de tramitación (1) y
> documental (2) deben ser compatibles con el motor futuro. Estudiar ≠ implementar.
>
> **Issues nuevos:** cada issue debe incluir en su propia descripción la justificación
> de por qué pertenece al milestone asignado. Este documento clasifica bloques funcionales,
> no issues individuales.

---

### G.1 Bloqueantes — sin esto no hay producción viable

| # | Bloque | Por qué bloquea |
|---|--------|-----------------|
| 1 | **Tramitación ESFTT** | Es el núcleo. Sin crear/avanzar/cerrar Solicitudes/Fases/Trámites/Tareas el sistema no reemplaza ningún proceso real. |
| 2 | **Sistema documental** | El expediente administrativo *son* sus documentos. Sin gestión de ficheros no hay expediente válido, no hay prueba de actuación, no hay notificación. |
| 12 | **Importación legacy** | Si se lanza producción sin legacy, se operan dos sistemas en paralelo indefinidamente y el sistema antiguo nunca muere. Los expedientes en curso son reales y no pueden quedar fuera del nuevo sistema. |

**Dependencia interna:** el diseño de (1) y (2) debe ser compatible con el motor de reglas (4) y los plazos (5) que vendrán después. El estudio de ambos es necesario antes de fijar la arquitectura de tramitación, aunque su implementación sea posterior.

---

### G.2 Necesarios — el workaround no aguanta

| # | Bloque | Workaround temporal | Por qué no aguanta |
|---|--------|--------------------|--------------------|
| 3 | **Generación de escritos** | Generar el documento fuera (Word manual) y subirlo como fichero | Derrota el propósito del sistema; introduce errores humanos en variables y numeración; no escala |
| 8 | **Configuración de reglas y estructura** | El técnico gestiona tablas maestras directamente en BD | El Supervisor no puede operar autónomamente; cualquier cambio de tipo o regla depende del programador |
| 9 | **Gestión de carga y usuarios** | Existe interfaz básica; el Supervisor opera con lo que hay | El reparto de expedientes y estadísticas de carga son operativos desde el primer día; sin ellos el Supervisor trabaja a ciegas |
| 10 | **Listado inteligente** | El listado V2 actual muestra datos básicos | Sin plazos agregados, tareas vencidas y cola priorizada, el tramitador no puede gestionar su trabajo diario eficientemente |

---

### G.3 Post-producción — añadir después de arrancar

| # | Bloque | Justificación | Prioridad estudio previo |
|---|--------|---------------|--------------------------|
| 4 | **Motor de reglas** | Los funcionarios operan sin enforcement automático hoy. La Fase 2 es explícitamente permisiva. Implementación progresiva: primero informativo, luego restrictivo si se decide. | **Alta** — su arquitectura debe estar definida antes de producción para no forzar refactorizaciones |
| 5 | **Plazos legales** | Los plazos se gestionan manualmente hoy. Las alertas visuales aportan valor desde el primer día pero no son requisito legal del sistema informático. | **Alta** — el modelo de datos (suspensiones, días hábiles) debe diseñarse en paralelo con (1) y (2) |
| 6 | **Proyectos e instalaciones** | El expediente puede tramitarse con datos básicos de proyecto ya existentes. Los elementos técnicos anidados son necesarios para resoluciones técnicas y GIS, no para el flujo procedimental inicial. | Media |
| 11 | **Auditoría configurable** | En el arranque basta con auditoría básica. La granularidad configurable es una mejora operativa, no un requisito inicial. | Baja |
| 13 | **Manual de usuario** | Sustituible en el arranque por formación presencial. Crítico a medio plazo para reducir dependencia del programador. | Baja |
| 14 | **Mensajería interna** | El email corporativo cubre la comunicación inicial. La mensajería añade eficiencia (pool de tareas, delegación) pero no es el día uno. | Baja |

---

### G.4 Opcional — valor real, no en el camino crítico

| # | Bloque | Justificación |
|---|--------|---------------|
| 7 | **GIS / Cartografía** | Dependiente de que Proyectos e instalaciones (#6) esté maduro. Ningún trámite administrativo se bloquea por no tener mapa. |

---

### G.5 Resumen visual

```
BLOQUEANTES          NECESARIOS           POST-PRODUCCIÓN           OPCIONAL
──────────────       ──────────────       ──────────────────────    ────────
1. Tramitación       3. Escritos          4. Motor reglas  [*]      7. GIS
2. Documental        8. Config/maestras   5. Plazos        [*]
12. Legacy           9. Carga/usuarios    6. Proyectos
                     10. Listado          11. Auditoría
                                          13. Manual
                                          14. Mensajería

[*] Implementación post-producción, pero estudio arquitectónico PREVIO a producción.
```

**Secuencia mínima viable:** estudiar arquitectura de (4) y (5) → implementar los 3 bloqueantes → resolver los 4 necesarios → arranque en producción → añadir post-producción por orden de demanda real.

---

## H. Mecánica de trabajo con GitHub

### Principios

- Los milestones se crean cuando el bloque está suficientemente estudiado. Pueden crearse
  todos al mismo tiempo una vez el roadmap está analizado.
- Los issues se crean solo cuando se va a implementar algo en los próximos días.
  No se crean issues "para el futuro" ni issues interconectados en cadena.
- Siempre se abre el issue ANTES de implementar, en modo plan de Claude, para
  valorar pros/contras y el mini-plan de implementación.
- Cuando se cierra un bloque o milestone, se abren los 2-3 issues del siguiente.

### GitHub Projects / Kanban — decisión: no usar

Con la filosofía de issues mínimos (2-3 activos simultáneamente), un tablero
Kanban estaría casi siempre vacío y añadiría mantenimiento sin valor.
Los milestones con porcentaje de completitud ya cubren el seguimiento necesario.

### Qué vive dónde

| Dónde | Qué contiene |
|-------|-------------|
| **PLAN_ESTRATEGIA.md** | Visión, actores, clasificación de bloques, principios de trabajo. Cambia solo si cambia la estrategia. |
| **PLAN_ROADMAP.md** | Estado actual por milestone: issues abiertos por milestone. Generado con `python scripts/gen_roadmap.py`. |
| **Issues GitHub** | El mini-plan de un bloque concreto: qué se hace, cómo, checklist y justificación del milestone. Verbosidad aquí, no en ROADMAP. |
| **Milestones GitHub** | Agrupación de issues. La descripción del milestone define el criterio de clasificación. |
| **`.issues/M*.md`** | Contexto on-demand de issues abiertos (título + cuerpo). Generado con `python scripts/gen_issues.py`. Gitignored. |
