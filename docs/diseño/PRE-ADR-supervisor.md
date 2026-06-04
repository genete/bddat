# PRE-ADR — Vistas y capacidades del Supervisor

> **Naturaleza de este documento:** Material preparatorio para sesión de diseño.
> No toma decisiones — las recoge, las ordena y las deja abiertas para debatir.
> El output de esa sesión será uno o varios ADRs formales.
> Fecha de redacción: 2026-06-04

---

## 1. Quién es el supervisor en BDDAT

Del estudio de usuario y las sesiones de diseño previas:

- **Rol de control transversal**: el supervisor ve todos los expedientes de todos los
  técnicos, no tiene expedientes propios. Su vista es agregada, no individual.
- **Productor de informes**: recibe peticiones de servicios centrales, directivos y
  organismos externos pidiendo el estado de situación de los expedientes (cuántos
  en tramitación, cuántos en plazo, cuántos vencidos, distribución por tipo, etc.).
  Esto no es tarea del tramitador — es trabajo de BDDAT a golpe de botón y script
  inducido por el supervisor.
- **Configurador del sistema**: puede modificar las reglas del motor, los catálogos
  estructurales y el modo global de operación sin tocar código.
- **Ejecutor de operaciones masivas**: asignar expedientes a técnicos en lote,
  cambios de titularidad sobre agrupaciones de 30-40 expedientes, migración legacy.
- **Estadísticas automáticas**: fue la petición número 1 en el estudio de usuario
  (§8.1 "varita mágica" — *"estadísticas automáticas para supervisor y servicios
  centrales"*).

---

## 2. Issues existentes relacionados

### M2 — Necesarios

| # | Título | Notas |
|---|---|---|
| **#256** | [UI] Vista de auditoría de expedientes — agregados por técnico y estado de pista | Conteo por técnico × pista × estado; plazos vencidos; antigüedad media. Usuario principal: supervisor. Es el núcleo de la vista de supervisión. |

### M3 — Motor de reglas y plazos

| # | Título | Notas |
|---|---|---|
| **#170** | [ADMIN] CRUD de reglas del motor — interfaz para Supervisor | Configurar reglas_motor, condiciones_regla. Solo SUPERVISOR/ADMIN. |
| **#171** | [ADMIN] CRUD de tablas maestras estructurales (tipos Fase, Trámite, Tarea) | Catálogos estructurales. Solo SUPERVISOR/ADMIN. |
| **#479** | [UI] Selector de modo global del motor | BLOQUEAR / SOLO_ADVERTIR / INACTIVO. Backend ya implementado en #323. |

### M4 — Pre-producción

| # | Título | Notas |
|---|---|---|
| **#227** | [BUG] SUPERVISOR puede desactivar usuario ADMIN | Bug de permisos en el toggle del listado de usuarios. |
| **#295** | [NEGOCIO] Cambios de titularidad masivos en agrupaciones solares | 30-40 expedientes en una operación. Modelo actual los trata individualmente — inviable. Preguntas abiertas sobre si es operación masiva o entidad nueva (agrupación). |

### M5 — Post-producción

| # | Título | Notas |
|---|---|---|
| **#76** | Exportación listado expedientes (Excel/CSV) | Issue detallado con propuesta técnica. Diseñado desde el principio para supervisor. Hoy en M5 pero su naturaleza es de informe — podría subir de milestone si se decide que los informes son críticos. |

---

## 3. Menciones en documentos de diseño existentes

- **DECISIONES_UI.md §layout validación caso 6**: *"Dashboard del supervisor con
  gráficos"* — el layout `base_app.html` aguanta este caso en modo "workbench ligero"
  sin rediseño. Pendiente de materializar en vista real.
- **ESTUDIO_USUARIO §7.4**: acciones masivas identificadas:
  *"asignación de expedientes a usuario desde supervisor; migración legacy en lote"*.
- **ESTUDIO_USUARIO §8.1** (top 3 varita mágica): *"Estadísticas automáticas para
  supervisor y servicios centrales"* — petición número 1 del equipo.
- **ANALISIS_CRITICO**: el supervisor conoce el flujo administrativo en lo que afecta
  a BDDAT — es la fuente de verdad para el diseño de vistas de rol.

---

## 4. Ejes conceptuales identificados

El universo del supervisor agrupa capacidades heterogéneas. Una forma de ordenarlas:

### Eje A — Supervisión y auditoría (quién hace qué, cómo va el trabajo)

- Vista de auditoría (#256): carga por técnico, plazos, cuellos de botella.
- Semáforos de vencimientos (#74 — hoy M5, usuario principal supervisor).
- Vista de seguimiento global (hoy existe parcialmente).
- Exportación de listados para análisis externo (#76).

### Eje B — Generación de informes bajo demanda

- Informes de estado de situación para servicios centrales.
- Informes estadísticos por período, tipo de expediente, municipio, etc.
- Exportación a PDF (distinto de Excel/CSV — formato de presentación oficial).
- "A golpe de botón y script inducido por el supervisor" — concepto nuevo, sin issue.

### Eje C — Configuración del sistema

- Motor de reglas (#170): CRUD de reglas y condiciones.
- Tablas maestras (#171): tipos de Fase, Trámite, Tarea.
- Modo global del motor (#479): selector BLOQUEAR/ADVERTIR/INACTIVO.
- (Futuro) Configuración de plantillas, plazos legales, catálogos de notificación.

### Eje D — Operaciones masivas

- Cambios de titularidad sobre agrupaciones solares (#295): 30-40 expedientes.
- Asignación masiva de expedientes a técnico (identificada en estudio usuario §7.4).
- Migración legacy en lote (identificada en estudio usuario §7.4).
- (Futuro) Otras operaciones transversales que la tramitación individual no cubre.

---

## 5. Preguntas abiertas para la sesión de diseño

### Sobre el layout y la experiencia de usuario

1. ¿El supervisor tiene una vista propia de entrada (como "Mi trabajo" del admin) o
   accede a las mismas vistas que los demás roles con más capacidades visibles?
2. ¿Los ejes A, B, C, D viven en una sola vista con tabs/secciones o en vistas
   separadas accesibles desde la sidebar?
3. ¿El "dashboard con gráficos" del caso 6 de DECISIONES_UI es la vista principal del
   supervisor, o es solo una de las vistas?

### Sobre informes y exportaciones (Eje B)

4. ¿Qué informes concretos se piden desde servicios centrales/directivos? ¿Cuáles son
   los más frecuentes? ¿Tienen una plantilla establecida (Word, PDF con logo, tabla
   normalizada)?
5. ¿El PDF de informe se genera con los mismos datos que el Excel, o tiene formato
   diferente (portada, secciones narrativas, gráficos)?
6. ¿Los informes son siempre del listado de expedientes, o también hay informes de
   plazos, de documentos, de estados del motor?
7. ¿La exportación a PDF aplica solo a informes de supervisor o también al expediente
   individual (compilación de expediente para recurso — estudio usuario §7.5)?

### Sobre operaciones masivas (Eje D)

8. ¿El cambio de titularidad masivo (#295) es una operación puntual (cuando llega una
   agrupación solar) o ocurre con cierta frecuencia? ¿Con qué volumen real?
9. ¿La "asignación masiva de expedientes" es redistribución de carga entre técnicos,
   o es asignación inicial de expedientes sin responsable?
10. ¿Qué otras operaciones transversales se hacen hoy en el sistema legacy que BDDAT
    no cubre?

### Sobre la estructura de ADRs

11. ¿Separamos la vista de supervisión (Eje A) del panel de configuración (Eje C)?
    Son usuarios similares pero propósitos muy distintos.
12. ¿Los informes bajo demanda (Eje B) merecen su propio ADR o van en la vista de
    supervisión?
13. ¿Las operaciones masivas (Eje D) son un ADR separado o parte de la vista del
    supervisor?

---

## 6. Posible partición en ADRs

Una propuesta inicial para debatir en sesión — puede colapsar o expandir:

| ADR | Título tentativo | Ejes | Issues absorbidos |
|---|---|---|---|
| **ADR-022** | Vista de supervisión y auditoría | A | #256, #74 (parcial) |
| **ADR-023** | Generación de informes y exportaciones | B | #76, (nuevos) |
| **ADR-024** | Panel de configuración del sistema | C | #170, #171, #479 |
| **ADR-025** | Operaciones masivas transversales | D | #295, (nuevos) |

Alternativa compacta (si B es pequeño): fusionar ADR-022 + ADR-023 en uno.

---

## 7. Relaciones con otros ADRs

- **ADR-013** (permisos blandos): el supervisor tiene permisos amplios. Los nuevos
  ejes pueden requerir permisos adicionales (`generar_informes`, `configurar_sistema`,
  `operar_masivo`).
- **ADR-016** (árbol del expediente): la compilación de expediente para recurso
  (estudio usuario §7.5) parte de la vista del árbol — el supervisor la induciría
  desde su vista pero el mecanismo es el árbol.
- **ADR-021** (operaciones externas): el supervisor podría ver el estado global de
  la cola de operaciones externas (cuántas pendientes, cuántas fallidas) — conexión
  natural con la vista de auditoría.
- **ADR-018** (command palette): el supervisor es el usuario que más se beneficia del
  acceso rápido a cualquier expediente desde cualquier vista.
