# PRE-ADR — Matriz de cobertura de completitud: roles y motor

> **Naturaleza de este documento:** Material preparatorio para sesión de diseño.
> No toma decisiones — recoge lo hablado, señala qué ya existe y deja las preguntas
> abiertas para esa sesión. El output será uno o varios ADRs formales (candidato a
> **ADR-031**, siguiente libre tras ADR-030).

**Estado:** Propuesta para discusión (no implementada)
**Fecha:** 2026-07-08
**Disparador:** sesión sobre clasificación de issues y mapas de foco (ver
[[project_clasificacion_issues_4bloques]] y [[project_adr030_coverage_matrix_pattern]]
en memoria de proyecto)

---

## 1. De dónde viene esto

La sesión partió de un problema de foco: con M2-M3 avanzados, la sensación de "final
del túnel borroso" — cada paso destapa más pendientes de los que resuelve. Se exploró
un mapa Mermaid del código (blueprints/módulos) y una clasificación de los 96 issues
abiertos por zona funcional. Carlos señaló el fallo de fondo: esa clasificación es
**lineal sobre lo que ya es issue** — organiza el backlog, pero no contesta a las
preguntas que de verdad producen la visión borrosa:

> ¿Qué más necesita el supervisor/tramitador/administrativo/admin para su trabajo?
> ¿Qué parte del core del motor está incompleta?

Se acordó una clasificación ortogonal a los milestones para el backlog existente
(4 bloques: rol / tramitación directa / mantenimiento / residual —
[[project_clasificacion_issues_4bloques]]), pero esa clasificación **no resuelve** las
dos preguntas de arriba: un issue tracker, por bien organizado que esté, solo expone
huecos que ya se convirtieron en issue. Un hueco que nadie ha filed todavía es invisible
a cualquier etiquetado, por fino que sea.

Investigando el origen de `PLAN_ROADMAP.md` (citado más abajo) apareció un patrón que
ya se repitió dos veces antes de `CONTEXTO_ACTUAL.md`: un `ROADMAP.md` manual creció a
419 líneas con checklists internos (podado en 2026-02) y, ya automatizado desde la API
de GitHub (`gen_roadmap.py`), se eliminó 13 días después de creado (issue #327) por
"duplicar GitHub sin aportar las dependencias entre issues, que sería su único valor
añadido". Cita de la sesión: *"este proyecto es como una hidra, cuantas más cabezas
cortas más le crecen."*

---

## 2. La conexión con ADR-030

ADR-030 (`docs/decisiones/ADR-030-dataset-ficticio-y-matriz-cobertura.md`) ya resolvió
exactamente este problema para otro eje: la cobertura de **mecanismo** del motor de
reglas y plazos. Su §9 fija el principio:

> "Hacer el análisis solo de una parte del mapa y dejar el resto sin identificar se
> considera peor que dejar huecos explícitos y señalizados."

Y construye matrices dimensión×valor (12 operadores, unidades de plazo, variables,
invariantes...) donde cada celda tiene un lugar reservado — implementada o placeholder
documentado, nunca ausente sin más.

Este documento propone aplicar el mismo principio a dos ejes que ADR-030 **no** cubre:

| Eje | Qué mide | Cubierto por ADR-030? |
|---|---|---|
| **Rol** | Qué necesita cada actor (Supervisor/Tramitador/Administrativo/Admin) para hacer su trabajo | No — ADR-030 es mecanismo de motor/plazos/variables, no superficie de producto por rol |
| **Motor — contenido normativo** | Cuántas `reglas_motor`/`catalogo_plazos` reales existen frente a lo que exige la legislación por tipo de expediente | No — ADR-030 cubre que el *mecanismo* soporte cada operador/unidad; no cuántas filas de negocio hacen falta |

---

## 3. Hallazgo clave: la matriz de rol ya existe, no hay que inventarla

`docs/referencia/PLAN_ESTRATEGIA.md` §D — **"Tabla 1 — Actores de negocio × Funciones →
Interfaz web/flujo"** — es, literalmente, la matriz que falta: **14 bloques funcionales
× 4 actores** (Admin BDDAT, Supervisor, Tramitador, Administrativo), con la interfaz o
flujo esperado en cada celda. Fechada 2026-04-11, "cambia solo si cambia la estrategia,
no al cerrar issues".

Lo que falta **no es construir esta matriz** — ya está, a nivel de intención de diseño.
Falta una pasada de auditoría que anote, celda a celda, el **estado real**: implementado
/ parcial / placeholder / sin issue conocido — y qué issue(s) lo cubren si existen.

### Muestra ilustrativa (sin verificar en detalle — es el trabajo de la sesión)

| Función (fila de PLAN_ESTRATEGIA) | Actor | Celda esperada | Hipótesis de estado real |
|---|---|---|---|
| Config. reglas y estructura | Supervisor | CRUD tablas maestras, motor, plazos, rutas filesystem | Mixto: municipios ya implementado (`api_municipios.py`); reglas del motor y tablas maestras abiertas (#170, #171); `catalogo_plazos` CRUD — **sin issue localizado** en el pase de esta sesión |
| Mensajería interna | Todos | Sistema de avisos y delegación de tareas (no chat) | Sin cobertura real hoy; el issue más cercano (#28, M5) es "Notificaciones internas y solicitudes de cambio de rol" — alcance menor al descrito en PLAN_ESTRATEGIA |
| Auditoría configurable | Supervisor/Admin | Panel para definir qué se audita y cuándo | Hoy solo existe bitácora fija (#530 la mejora, no la hace configurable) — hueco de alcance mayor al del issue existente |

Estas tres filas ya sugieren el patrón esperado: no es que falte una fila entera sin
tocar, es que **la celda existente subestima el alcance** que pide el documento de
estrategia, y el hueco entre ambos no tiene issue propio.

---

## 4. Los milestones ya están anclados a las necesidades — PLAN_ESTRATEGIA §G

Confirmado al releer el documento completo: **los milestones no son un agrupador
independiente de las necesidades — son la propia clasificación de los 14 bloques**.
`PLAN_ESTRATEGIA.md` §G ("Clasificación de los 14 bloques — Camino a producción") fija
el criterio ("qué ocurre si el sistema entra en producción *sin* ese bloque") y asigna
cada bloque a M1 (Bloqueantes: Tramitación, Documental, Legacy), M2 (Necesarios:
Escritos, Config/maestras, Carga/usuarios, Listado), M3/M5 (Post-producción: Motor,
Plazos, Proyectos, Auditoría, Manual, Mensajería), M4 (Pre-producción técnica —
infraestructura/seguridad/legacy, no es un bloque funcional) y Opcional (GIS). **La
clasificación de issues por milestone sigue valiendo tal cual** — no hace falta
sustituirla, solo cruzarla con la matriz de rol/motor de este documento.

La "frontera permeable" M2↔M3 que se percibe en el día a día está documentada, no es un
descuido — §G lo dice explícitamente:

> "Motor de Reglas (4) y Plazos (5)... no son bloqueantes para el arranque... Sin
> embargo, su estudio arquitectónico es previo a producción: las decisiones de modelo
> de datos y estructura de tramitación (1) y documental (2) deben ser compatibles con
> el motor futuro. **Estudiar ≠ implementar.**"

Y la secuencia G.5 confirma la lectura tranquilizadora sobre M4: *"estudiar arquitectura
de (4) y (5) → implementar los 3 bloqueantes → resolver los 4 necesarios → arranque en
producción → añadir post-producción por orden de demanda real"* — M4 (condiciones
técnicas de despliegue) se sitúa, por diseño, después de cerrar M1+M2 y de que el
*estudio* (no la implementación completa) de M3 esté cerrado. Esto es el criterio
documentado, no una dependencia verificada issue-a-issue en GitHub — esa verificación
mecánica sigue sin existir (ver hallazgo colateral, §6).

---

## 5. Segundo eje — motor: contenido normativo, no mecanismo

ADR-030 certifica que el motor **sabe operar** con cualquier combinación de operador,
efecto, unidad de plazo, variable. No certifica que **existan ya** las filas de negocio
(`reglas_motor`, `catalogo_plazos`) que la legislación real exige por tipo de
expediente/trámite. Candidato de entrada para esta matriz, a verificar en la sesión:
`docs/referencia/NORMATIVA_MAPA_PROCEDIMENTAL.md` — si ya cruza trámites contra norma,
es la base; si no, es la primera pieza a construir de este eje.

---

## 6. Hallazgo colateral: deriva del principio de "issues mínimos" (PLAN_ESTRATEGIA §H)

`PLAN_ESTRATEGIA.md` §H ("Mecánica de trabajo con GitHub") documenta una filosofía
original que hoy no se está siguiendo:

> "Los issues se crean solo cuando se va a implementar algo en los próximos días. No se
> crean issues 'para el futuro' ni issues interconectados en cadena." · "Cuando se
> cierra un bloque o milestone, se abren los 2-3 issues del siguiente."

Y justifica ahí mismo por qué **no** se usa GitHub Projects/Kanban: *"con la filosofía
de issues mínimos (2-3 activos simultáneamente), un tablero Kanban estaría casi siempre
vacío y añadiría mantenimiento sin valor. Los milestones con porcentaje de completitud
ya cubren el seguimiento necesario."*

Hoy hay **96 issues abiertos** repartidos en 4 milestones activos — muy lejos de "2-3
simultáneos". La premisa bajo la que se descartó Projects/Kanban ya no se sostiene, sin
que se haya vuelto a evaluar la decisión. Esto es un hallazgo paralelo a la matriz de
cobertura (no la sustituye): puede que parte del "efecto hidra" no sea solo falta de
mapa, sino deriva de una disciplina de creación de issues que sí funcionaba y se dejó de
aplicar. La sesión de la matriz debería, como mínimo, decidir explícitamente si se
retoma esa disciplina, se sustituye por el mapa de cobertura, o conviven ambas.

---

## 7. Qué NO es este documento

- No reclasifica los issues existentes — eso ya está resuelto en
  [[project_clasificacion_issues_4bloques]].
- No es una auditoría de arquitectura de código (islas React, tests, servicios, checks,
  modelos, rutas) — descartado explícitamente en la conversación que originó este
  documento; fuera de alcance aquí.
- No sustituye `docs/diseño/ESTUDIO_USUARIO.md` — es complementario: ese estudio ya
  hizo este ejercicio para el eje del Supervisor (ver `PRE-ADR-supervisor.md` §1-4,
  "varita mágica" §8.1); este documento propone repetirlo para Tramitador,
  Administrativo y Admin y cruzarlo con PLAN_ESTRATEGIA §D/§G.

---

## 8. Preguntas abiertas para la sesión

1. ¿Se audita PLAN_ESTRATEGIA §D completo (14 filas × 4 actores = 56 celdas) en una
   sola pasada, o se prioriza primero las filas que tocan el foco actual (M3)?
2. ¿`NORMATIVA_MAPA_PROCEDIMENTAL.md` sirve tal cual como base del eje motor-contenido,
   o necesita ampliarse antes de auditar?
3. ¿Cada hueco encontrado sin issue se convierte en issue de inmediato, o se acumula en
   una lista de huecos aparte hasta cerrar la pasada completa de una matriz?
4. ¿Este ejercicio es una foto fija de cara a M4→M5, o se repite en cada cierre de
   milestone como parte de su criterio de salida?
5. ¿Extender `ESTUDIO_USUARIO.md` a los tres roles que faltan es prerequisito de esta
   sesión, o se hace en paralelo, celda a celda, según se audita PLAN_ESTRATEGIA?
6. Sobre el hallazgo del §6: ¿se retoma la disciplina de "2-3 issues activos" de
   PLAN_ESTRATEGIA §H, se considera superada por el propio mapa de cobertura, o ambas
   cosas se necesitan a la vez (mapa para ver el panorama, disciplina para no volver a
   perderlo de vista)?

---

## Referencias

- ADR-030 — `docs/decisiones/ADR-030-dataset-ficticio-y-matriz-cobertura.md`
- `docs/referencia/PLAN_ESTRATEGIA.md` §D (Tabla 1, rol), §G (clasificación de bloques
  por milestone), §H (mecánica de trabajo con GitHub, issues mínimos)
- `docs/guias/GUIA_ROLES.md` — permisos por rol a nivel de BD, base distinta pero
  relacionada (permiso ≠ capacidad de producto)
- `docs/diseño/ESTUDIO_USUARIO.md` y `docs/diseño/PRE-ADR-supervisor.md` §1-4
- `docs/referencia/NORMATIVA_MAPA_PROCEDIMENTAL.md` (a verificar en sesión)
- Issue #327 (`gh issue view 327`) — motivo real de la eliminación de PLAN_ROADMAP.md
- Memoria: [[project_clasificacion_issues_4bloques]], [[project_adr030_coverage_matrix_pattern]]
