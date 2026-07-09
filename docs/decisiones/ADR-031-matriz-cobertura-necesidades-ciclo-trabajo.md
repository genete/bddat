# ADR-031 — Matriz de cobertura de necesidades (rol/producto) y ciclo de trabajo diario

**Estado:** Adoptada
**Fecha:** 2026-07-08
**Issue:** pendiente de crear
**Relacionado con:** ADR-030 (dataset ficticio y matriz de cobertura de mecanismo del
motor/plazos/variables) — mismo principio, aplicado aquí a un eje distinto: qué
necesita cada rol, no qué combinaciones soporta el motor.

---

## Contexto

`docs/diseño/PRE-ADR-matriz-cobertura-roles-motor.md` partió de un problema de
foco: con M2-M3 avanzados, cada paso destapaba más pendientes de los que
resolvía. La clasificación de issues por zona o por bloque, por bien hecha que
esté, es **lineal sobre lo que ya es issue** — no contesta a:

> ¿Qué más necesita el supervisor/tramitador/administrativo/admin para su
> trabajo? ¿Qué parte del core del motor está incompleta?

Un hueco que nadie ha filed todavía es invisible a cualquier etiquetado, por
fino que sea. ADR-030 ya resolvió este mismo problema para el eje de
**mecanismo** del motor de reglas y plazos, con un principio (§9):

> "Hacer el análisis solo de una parte del mapa y dejar el resto sin
> identificar se considera peor que dejar huecos explícitos y señalizados."

Este ADR aplica el mismo principio al eje de **necesidad por rol/producto**, con
una restricción adicional que la sesión de diseño dejó explícita: el resultado
no puede repetir el fallo de `PLAN_ROADMAP.md`, eliminado dos veces (podado en
2026-02, borrado definitivamente 13 días después de automatizarse — issue
#327) por "duplicar GitHub sin aportar las dependencias entre issues, que
sería su único valor añadido". Cualquier documento que copie estado o
contenido de GitHub decae igual — el valor de esta matriz está exactamente en
lo que GitHub no puede dar: huecos sin issue y % de cobertura real, no en
ninguna copia de lo que ya vive allí.

`PLAN_ESTRATEGIA.md` §H documentaba además una disciplina de "issues mínimos"
(2-3 activos simultáneos, se abren los siguientes solo al cerrar un bloque) que
dejó de seguirse — a fecha de esta sesión había 96 issues abiertos repartidos
en 4 milestones. Este ADR la retoma, apoyada en la matriz en vez de en
intuición.

---

## Decisión

### 1. Dos documentos, dos cadencias

- **`docs/diseño/DETALLE_NECESIDADES_BDDAT.md`** — estable, se toca poco (como
  un ADR). Define **qué** es cada necesidad: id, descripción a nivel de
  capacidad, quién la necesita, bloque funcional, milestone.
- **`docs/diseño/MATRIZ_COBERTURA_BDDAT.md`** — vivo, se actualiza en cada
  issue cerrado que toque una fila. Define **cuánto** está cubierta cada
  necesidad hoy: % + qué falta.

Separar ambos evita que el documento que se lee "siempre" (o casi) cargue con
contenido que cambia semana a semana, y evita que el documento de definición
se contamine con el estado del momento.

### 2. Id permanente, independiente de bloque y milestone

Cada necesidad tiene un id plano y secuencial (`N001, N002...`), asignado una
sola vez y nunca reasignado ni renumerado. El id **no codifica** bloque ni
milestone — son columnas propias de cada fila. Si una necesidad cambia de
milestone, se fusiona su bloque con otro, o se reclasifica, solo cambian esas
columnas: el id (y cualquier label de GitHub que lo use) no se mueve. Es el
mismo criterio que un índice de tabla de base de datos: estable aunque cambien
los datos de la fila.

### 3. Qué se excluye deliberadamente de cada documento, y por qué

| Se excluye | De dónde | Por qué |
|---|---|---|
| Forma de interfaz (pantalla, versión V2/V3/V4, componente técnico) | `DETALLE_NECESIDADES_BDDAT.md` | Es decisión de diseño, cambia con el tiempo; la necesidad describe la capacidad, no cómo se resuelve hoy. |
| Documento de origen por fila | `DETALLE_NECESIDADES_BDDAT.md` | Citar la fuente invita a releerla como si fuera la verdad vigente — y son documentos que quedan desactualizados con frecuencia en este proyecto. El documento fija el presente; de dónde venía cada necesidad no es un dato que haya que mantener. |
| Número o nombre de issue en la celda | `MATRIZ_COBERTURA_BDDAT.md` | Es exactamente lo que mató a `PLAN_ROADMAP.md` — duplicar GitHub sin aportar valor. El issue se busca en el momento (§5), no se arrastra como puntero que se pudre. |
| Lenguaje de incertidumbre ("pendiente de verificar", "sin confirmar") | `MATRIZ_COBERTURA_BDDAT.md` | Un documento de cabecera para decisión no puede llevar dudas sin resolver — si algo está en duda, se verifica en código antes de escribir el %, no se escribe la duda. |

### 4. Retirada y adición de necesidades

Los ids nunca se borran silenciosamente. Una necesidad retirada (duplicada,
fusionada, o descartada por decisión directa) se documenta en la sección "Ids
retirados" de `DETALLE_NECESIDADES_BDDAT.md` con el motivo — el hueco en la
numeración es intencional, no un error. Las necesidades nuevas (descubiertas
al auditar código, o detectadas de cualquier otra forma) se añaden con el
siguiente id libre, sin reordenar las existentes.

### 5. Cobertura: fuente única el código real

El % de cada fila se determina leyendo el código (`app/`, `migrations/`,
`scripts/`, configuración de despliegue) — nunca issues de GitHub ni
documentos de diseño. Un issue cerrado no implica cobertura 100%: puede haber
quedado parcial, o el mecanismo construido puede no estar conectado a ninguna
vista real. Se verifica lo que hay, no lo que se pretendía construir.

### 6. Mapeo necesidad↔issue: labels de GitHub, no markdown

Cada necesidad se vincula a sus issues (abiertos o cerrados) mediante un label
`necesidad:N0XX` en GitHub, no mediante una lista mantenida a mano en ningún
documento. Consulta bajo demanda: `gh issue list --label necesidad:N0XX
--state all`. Esto evita el mismo problema que el punto 3: un puntero en
markdown se desincroniza en cuanto se abre o cierra un issue sin acordarse de
tocar el documento; un label vive pegado al issue y GitHub lo mantiene
sincronizado gratis.

### 7. Ciclo diario de trabajo

```
┌─────────────────────────── CICLO DE REPOSICIÓN (raro) ───────────────────────────┐
│  Matriz (filtrada por milestone) → CEO elige celda → gh issue list --label       │
│  (busca qué ya existe, celda puede ser mixta)                                    │
│       │                                                                          │
│       ├─ issues rescatables → etiquetar y mover a Próximos (2-3 activos)         │
│       │                                                                          │
│       └─ hueco sin issue, descrito con sustancia → anotar en Próximos como       │
│          tarea de DEFINICIÓN (marcada como tal, no como issue implementable)    │
│                                                                                   │
│  Ambas ramas conviven en Próximos — no son excluyentes dentro de una celda      │
└───────────────────────────────────┬───────────────────────────────────────────────┘
                                     ▼
              ┌───────────── CICLO DIARIO (cada sesión) ─────────────┐
              │  Leer CONTEXTO_ACTUAL → tomar primero de Próximos →  │
              │  plan de Claude → implementar → verificar en código  │
              │  → actualizar Matriz → actualizar CONTEXTO_ACTUAL    │
              │  (confirma Carlos) → ¿queda algo en Próximos?        │
              └──────────────┬─────────────────────────┬────────────┘
                         sí, queda                  no queda
                              │                          │
                              └──────── repetir ◄─────────┘
                                                          │
                                                          ▼
                                          vuelve al ciclo de reposición
```

**Ciclo diario (cada sesión):**

1. Leer `docs/CONTEXTO_ACTUAL.md` (ya es regla existente en `CLAUDE.md`).
2. Tomar el primero de **Próximos** — se abre en modo plan de Claude antes de
   implementar (`PLAN_ESTRATEGIA.md` §H).
3. Implementar.
4. Al cerrar el issue: identificar qué necesidad(es) tocaba por su label,
   verificar en código el % real, actualizar la fila en
   `MATRIZ_COBERTURA_BDDAT.md`, mover el issue de **Próximos** a **Hecho** en
   `CONTEXTO_ACTUAL.md` **con confirmación de Carlos** (regla ya existente en
   `CLAUDE.md`). Si aparece una necesidad no descrita, se añade con id nuevo
   (punto 4).
5. Repetir desde el paso 2 mientras quede algo en Próximos.

**Nota (2026-07-09):** el ciclo original distinguía un campo "Actual" separado
de "Próximos". Se retira: el propio mecanismo (el documento solo se toca al
cerrar un issue, momento en el que "Actual" y "propuesta de próximo Actual"
ocurrían en el mismo paso) hacía que "Actual" fuera siempre indistinguible de
"el primero de Próximos" — nunca aportaba una decisión que Próximos no
contuviera ya. `CONTEXTO_ACTUAL.md` queda con solo **Hecho** y **Próximos**
(≤3), como ya reflejaba de facto el punto 8 de este ADR.

**Ciclo de reposición (solo cuando Próximos se vacía):**

1. Mirar `MATRIZ_COBERTURA_BDDAT.md` filtrada por milestone (M1/M2 incompletos
   primero, salvo decisión explícita de adelantar algo).
2. Carlos elige la celda — decisión de CEO, no automatizable.
3. Buscar qué ya existe abierto en el backlog para esa necesidad, con o sin
   label todavía (`gh issue list --label necesidad:N0XX --state all`, más una
   revisión manual si el label aún no se aplicó — punto 6).
4. **Bifurcación** según lo que devuelva el paso 3 — puede ser mixta: dentro de
   la misma celda, unas necesidades tienen issue y otras no.
   - **Hay issues rescatables** — etiquetarlos (si falta el label) y moverlos a
     Próximos, hasta completar 2-3 activos.
   - **Queda hueco sin issue** (parcial o total) — no se crean issues dentro de
     este mismo pase de reposición: redactar un issue es trabajo real (alcance,
     prerrequisitos, criterios de aceptación), no una etiqueta de 30 segundos.
     El hueco se anota en Próximos como **tarea de definición**, marcada
     explícitamente como tal (no como issue listo para implementar) — ver nota
     2026-07-09 más abajo sobre qué distingue una anotación válida de un
     puntero vacío.
5. Entran en Próximos (issues rescatados + huecos de definición marcados como
   tales) → vuelta al ciclo diario. Un hueco de definición no se "implementa"
   en modo plan — su sesión busca primero qué ya existe (repetir el paso 3
   para ese hueco concreto: puede que el director lo describa de memoria y ya
   haya algo sin label todavía) y solo entonces abre issue(s) nuevos si hace
   falta.

**Nota (2026-07-09):** corrección de Carlos tras usar el ciclo por primera vez,
matizada en una segunda ronda el mismo día. Lo que el punto 4 original
prohíbe **no es describir un hueco** en Próximos — es escribir un **puntero
vacío sin información** ("N0XX: pendiente de issue"), el mismo antipatrón que
mató a `PLAN_ROADMAP.md` (duplicar GitHub sin aportar nada, §1 de este ADR).
Si el director describe un hueco con sustancia (qué falta, por qué, dónde
mirar), esa descripción **sí** se escribe en Próximos — es información real
que de otro modo se pierde, no un recordatorio vacío. La situación habitual de
reposición es **mixta**: la celda elegida trae algunos issues rescatables y
dejar otras necesidades sin cubrir; Próximos entonces lleva ambas cosas,
issues y huecos, distinguibles a simple vista. Lo que sigue vigente sin
cambios: la sesión que retome un hueco de definición no empieza redactando el
issue a ciegas — repite primero la búsqueda en el backlog (paso 3), porque el
director puede haber descrito el hueco de memoria sin comprobar si ya existe
algo parcial sin etiquetar.

### 8. Retoma la disciplina de "issues mínimos" de `PLAN_ESTRATEGIA.md` §H

Resuelve la pregunta que había quedado abierta en
`PRE-ADR-matriz-cobertura-roles-motor.md` §8.6: no es "mapa de cobertura **o**
disciplina de issues mínimos" — son las dos. La matriz da el panorama (dónde
hace falta mirar); la disciplina de 2-3 issues activos evita que el backlog
vuelva a crecer sin control. Sigue sin usarse GitHub Projects/Kanban — el
"tablero" es, de facto, la sección Próximos de `CONTEXTO_ACTUAL.md`.

---

## Alcance y límites

- El eje **motor — contenido normativo** (`reglas_motor`/`catalogo_plazos`
  reales frente a lo que exige la legislación por trámite) queda **fuera** de
  este ADR. Vive como una única fila placeholder (Bloque 16,
  `DETALLE_NECESIDADES_BDDAT.md`) hasta que se audite en profundidad en su
  propia sesión — filas por trámite/norma, no por rol, así que necesita su
  propio diseño de matriz.
- Este ADR no fija el contenido actual de la matriz (qué % tiene cada fila hoy)
  — eso es precisamente lo que el punto 1 aparta a un documento vivo. El
  histórico de cómo se llegó al primer barrido completo (6 agentes en
  paralelo auditando código, sesión 2026-07-08) queda en el historial de
  commits, no aquí.

---

## Próximos pasos (fuera de este ADR)

- Primera vuelta real del ciclo de reposición: Carlos elige las primeras
  celdas de foco desde `MATRIZ_COBERTURA_BDDAT.md`.

---

## Referencias

- `docs/diseño/PRE-ADR-matriz-cobertura-roles-motor.md` — origen de este ADR.
- `docs/decisiones/ADR-030-dataset-ficticio-y-matriz-cobertura.md` §9 —
  principio de placeholder explícito del que este ADR hereda.
- `docs/referencia/PLAN_ESTRATEGIA.md` §H — disciplina de "issues mínimos" que
  se retoma; §G — milestones, columna reutilizada en la matriz.
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md`, `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`
  — documentos vivos que este ADR gobierna.
- Issue #327 (`gh issue view 327`) — motivo real de la eliminación de
  `PLAN_ROADMAP.md`, razón por la que la matriz excluye issues en celda.
