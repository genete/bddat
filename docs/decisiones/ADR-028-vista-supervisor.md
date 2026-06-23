# ADR-028 — Vista del Supervisor: bloques de Control y Gestión

**Estado:** Vigente — marco y rama Control fijados (sesión 23-jun); bloques en construcción
**Fecha:** 2026-06-22 (rev. 2026-06-23)
**Issue:** #579 (contenedor "Mi trabajo del supervisor")

> **Naturaleza de este documento.** Nace de reencajar el material preparatorio
> `docs/diseño/PRE-ADR-supervisor.md` (04-jun, 4 ejes A/B/C/D) en la estructura de
> **dos bloques** acordada en sesión (22-jun), incorporando el **estado real del código
> verificado**. No todo está cerrado: cada apartado marca `[FIJADO]` (decisión tomada) o
> `[ABIERTO]` (a refinar en esta u otra sesión). El objetivo es **fijar lo decidible** y
> dejar el resto acotado, no en blanco.
>
> El PRE-ADR queda como **material de fondo** (informes y operaciones masivas tienen allí
> más detalle y preguntas abiertas que no se repiten aquí).

---

## Contexto

### Quién es el supervisor en BDDAT  `[FIJADO]`

Del estudio de usuario, el PRE-ADR y la sesión del 22-jun:

- **Rol de control transversal.** Ve todos los expedientes de todos los técnicos. **No tiene
  expedientes propios y NO tramita** (decisión confirmada 22-jun). Su vista es agregada, no
  individual — a diferencia del administrativo (ADR-017), que sí actúa sobre hojas del árbol.
- **Configurador del sistema.** Modifica reglas del motor, catálogos estructurales, plazos
  legales y el modo global de operación **sin tocar código**.
- **Productor de informes / estadísticas.** Fue la petición nº 1 del estudio de usuario
  (§8.1 "varita mágica": *estadísticas automáticas para supervisor y servicios centrales*).
- **Ejecutor de operaciones masivas** (cambios de titularidad sobre agrupaciones, asignación
  en lote, migración legacy) — eje heredado del PRE-ADR, ver §Gestión.

### Estado real del código (verificado 22-jun)  `[FIJADO]`

Corrige una lectura previa errónea (se creía que la configuración del motor estaba bloqueada
por "terminar el motor"). **No es así:** los modelos existen y el motor evalúa en runtime.
Lo que falta en todos los casos de gestión es la **capa de administración (UI CRUD)** encima
de tablas ya vivas — no depende de completar ningún motor.

| Pieza | Backend / modelo | UI de gestión | Estado |
|---|---|---|---|
| CRUD tablas estructurales (`tipos_fases/tramites/tareas`) | ✅ se usan en runtime | ❌ | Falta UI |
| CRUD reglas motor (`ReglaMotor`, `CondicionRegla`, `CatalogoVariable`, `Norma`) | ✅ el motor evalúa en producción (`api_expedientes.py`) | ❌ | Falta UI |
| CRUD plazos legales (`catalogo_plazos`, `condiciones_plazo`, `efectos_plazo`, `dias_inhabiles`) | ✅ modelos existen | ❌ | Falta UI |
| Selector modo global motor | ✅ backend `configuracion_sistema` (#323) | ❌ | Falta UI (#479) |
| Gestión de usuarios | ✅ + API `listar_usuarios` + editar/toggle | parcial | Casi hecho |
| Panel de estadísticas | ❌ no hay agregados | ❌ dashboard = solo navegación (`index_v1.html`) | Falta todo |

---

## Decisión

### 1. Una vista propia del supervisor organizada en dos bloques  `[FIJADO]`

El universo del supervisor se ordena en **dos bloques gruesos**, que reencajan los cuatro
ejes del PRE-ADR:

| Bloque | Naturaleza | Absorbe ejes del PRE-ADR |
|---|---|---|
| **CONTROL** | Lectura / visualización: estadísticas, supervisión, informes | Eje A (supervisión y auditoría) + Eje B (informes bajo demanda) |
| **GESTIÓN** | Escritura / administración: CRUDs de configuración, usuarios, operaciones masivas | Eje C (configuración del sistema) + Eje D (operaciones masivas) |

El criterio del reparto es **leer vs. escribir**: Control no muta datos del dominio (agrega y
exporta); Gestión administra catálogos, usuarios y datos en lote.

> `[FIJADO 23-jun, #579]` **Layout y entrada.** La vista nuclear de partida es un **hub de
> dos columnas** (Control · Gestión): cada herramienta es una tarjeta que navega a su hoja, y
> los huecos sin construir se muestran como "pronto" con su issue (el hub sirve de mapa del
> roadmap). Sin tabs anidados. La entrada de sidebar **no se duplica**: se reusa la entrada
> role-adaptive **"Mi trabajo"** (ADR-013); `mi_trabajo.index` para SUPERVISOR/ADMIN redirige
> al hub `supervisor.index`. El hub es la **pantalla por defecto** del supervisor (aterrizaje
> post-login y cambio de rol ya cableados). Se implementa en un **blueprint `supervisor`
> dedicado, deliberadamente sin `metadata.json`** (así no genera una segunda entrada de
> sidebar). El layout `base_app.html` aguanta el hub en modo workbench ligero sin rediseño
> (DECISIONES_UI §caso 6).

---

### Bloque CONTROL

#### 2. Panel de estadísticas  `[FIJADO contenido y alcance v1; ABIERTO ejes pendientes]`

Métricas pedidas explícitamente (sesión 22-jun):

- **Expedientes por estado** — diagrama de tartas sobre el total.
- **Plazos vencidos** — gráfico de barras.
- **Plazos según dependencia** — vista que distingue **exterior vs. interior** (de quién se
  espera el producido). `[ABIERTO]` definición exacta de "exterior/interior" y su origen de datos.
- **Estadísticas de usuarios** — por técnico: expedientes **asignados, completados, totales**
  (y derivados de carga).

Apoyos existentes: el núcleo `estado_dominio` (#558, cerrado) ya proyecta estados de forma
canónica — los agregados se construyen sobre él, no sobre lógica nueva.

**Aspecto y alcance v1** `[FIJADO 23-jun, #579]`: la hoja es un panel de **gráficos
agregados** (no la tabla operativa, que es auditoría §3). v1 = fila de **KPIs** (total · en
trámite · plazos vencidos · finalizados), **tarta de expedientes por estado** (los 10 estados
canónicos del núcleo agrupados por banda de color de `COLOR`) y **barras de carga por técnico**
(completados vs. en trámite, vía `responsable_id`). "Plazos vencidos" entra como KPI numérico
hasta fijar su eje (`[ABIERTO]` técnico o pista); la vista exterior/interior queda aparcada.
**Render:** isla React + **Recharts**, con pase de tematizado a la paleta JdA documentado
(REGLAS §React). Backend: servicio agregado que cuenta `estado_expediente` sobre todos los
expedientes. Construcción en sesión propia.

#### 3. Vista de auditoría (#256)  `[FIJADO — issue existente]`

Agregados por **técnico × pista × estado**, plazos vencidos, antigüedad media por estado.
Es el núcleo de la supervisión operativa. Construible ya (su dependencia, `estado_dominio`,
está cerrada). Solapa parcialmente con §2 (estadísticas de usuarios) — `[ABIERTO]` delimitar
qué va en "auditoría" (tabla operativa, navegable) y qué en "estadísticas" (gráficos agregados).

#### 4. Semáforos y alertas de vencimientos (#74)  `[ABIERTO]`

Hoy en M5. Usuario principal: supervisor. Se nutre del cómputo de plazos. Encaja como capa
de alerta sobre §2/§3.

#### 5. Informes y exportaciones bajo demanda (eje B del PRE-ADR)  `[ABIERTO]`

Heredado del PRE-ADR sin cerrar. Conceptos: informes de estado de situación para servicios
centrales, exportación Excel/CSV (#76, hoy M5) y a PDF (formato de presentación oficial).
Preguntas abiertas (qué informes concretos, plantillas, formato) → ver PRE-ADR §5.

---

### Bloque GESTIÓN

#### 6. CRUD de configuración del motor  `[FIJADO — issues existentes]`

Capa de administración sobre tablas **ya vivas** (ver tabla de estado real):

- **Tablas estructurales** — tipos de Fase, Trámite, Tarea (**#171**).
- **Reglas del motor** — `reglas_motor`, `condiciones_regla`, con `CatalogoVariable`/`Norma`
  (**#170**).
- **Modo global del motor** — selector BLOQUEAR / SOLO_ADVERTIR / INACTIVO (**#479**;
  backend en #323).

#### 7. CRUD de plazos legales  `[FIJADO la necesidad, HUECO de issue]`

Administración de `catalogo_plazos`, `condiciones_plazo`, `efectos_plazo`, `dias_inhabiles`.
Los modelos existen; **no hay issue de CRUD** (los #172/#173/#190 eran de *cómputo* de plazos,
no de su administración). → **Crear issue.**

#### 8. Gestión de usuarios y permisos  `[FIJADO — casi implementado]`

Ya existe (listado, editar, toggle estado vía API). Pendientes conocidos: **#227** (bug:
supervisor puede desactivar ADMIN vía toggle) y **#281** (migración del listado a V2).
`[ABIERTO]` si la administración de **permisos** (dict `PERMISOS`, ADR-013) necesita UI propia
o se gestiona por rol.

#### 9. Operaciones masivas (eje D del PRE-ADR)  `[ABIERTO]`

Heredado del PRE-ADR sin cerrar:

- Cambios de titularidad sobre agrupaciones solares — 30-40 expedientes (**#295**).
- Asignación masiva de expedientes a técnico (estudio usuario §7.4) — **HUECO de issue**.
- Migración legacy en lote (#105, estudio usuario §7.4).

Preguntas abiertas (frecuencia, volumen, si es entidad nueva o lote) → ver PRE-ADR §5.

---

## Por qué

- **Refleja la realidad del rol:** el supervisor controla y configura, no tramita — los dos
  bloques separan limpiamente lo que lee de lo que administra.
- **Aprovecha lo que ya existe:** la gestión es una capa de UI sobre modelos vivos; no espera
  a "terminar el motor". Eso adelanta su construibilidad respecto a la lectura previa.
- **Cumple la petición nº 1 del estudio de usuario** (estadísticas automáticas).
- **Coherente con ADR-013** (permisos blandos) y ADR-017 (vista propia de rol): misma sidebar,
  vista propia como pantalla de entrada, restricciones expresadas como permisos.

---

## Permisos implicados  `[ABIERTO]`

Posible ampliación de ADR-013 con permisos de grano grueso: `configurar_sistema`,
`generar_informes`, `operar_masivo`. A concretar al implementar cada bloque.

---

## Partición en ADRs / orden de trabajo  `[ABIERTO]`

Este ADR-028 actúa hoy como **paraguas**. Según crezca, los bloques pueden derivar en ADRs
propios (siguientes libres desde **ADR-029**). Posible partición:

| Futuro ADR | Bloque / contenido | Issues |
|---|---|---|
| ADR-028 (este) | Marco de dos bloques + decisiones fijadas | #579 (contenedor) |
| ¿ADR-029? | Configuración del sistema (Gestión §6-7) | #170, #171, #479, +plazos |
| ¿ADR-030? | Estadísticas + auditoría (Control §2-4) | #256, #74, +stats usuarios |
| ¿ADR-031? | Informes y exportaciones (Control §5) | #76, +nuevos |
| ¿ADR-032? | Operaciones masivas (Gestión §9) | #295, #105, +asignación masiva |

`[ABIERTO]` decidir si conviene partir o mantener uno solo; y el orden de construcción entre
bloques (la Gestión es construible ya; el Control de estadísticas también, sobre `estado_dominio`).

---

## Huecos sin issue detectados  `[FIJADO — acción pendiente]`

1. **CRUD de plazos legales** (§7) — modelos existen, sin issue de administración.
2. **Estadísticas de usuarios** (§2) — asignados/completados/totales, no capturado.
3. **Vista de plazos por dependencia** exterior/interior (§2) — no capturado.
4. **Asignación masiva de expedientes a técnico** (§9) — no capturado.

---

## Material de fondo

- `docs/diseño/PRE-ADR-supervisor.md` — ejes A/B/C/D, menciones en docs de diseño, preguntas
  abiertas detalladas de informes y operaciones masivas.
- ADR-013 (permisos blandos), ADR-014 (layout `base_app`), ADR-016 (árbol), ADR-017 ("Mi
  trabajo" del administrativo — gemelo de rol), ADR-021 (operaciones externas).
- `docs/diseño/DECISIONES_UI.md` §caso 6 (dashboard del supervisor con gráficos).
