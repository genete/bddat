# ROADMAP — BDDAT · Estado de implementación

> **Propósito:** Estado vivo del proyecto. Se actualiza al cerrar issues y milestones.
> La verbosidad (qué falta, cómo hacerlo) vive en los issues de GitHub, no aquí.
> La visión estratégica y clasificación de bloques está en `ESTRATEGIA_ROADMAP.md`.
>
> **Última actualización:** 2026-02-27

---

## Estado de partida (operativo a 2026-02-27)

- Modelos SQLAlchemy completos: Expediente, Solicitud, Fase, Trámite, Tarea, Entidad, Proyecto, Usuario + maestros
- Autenticación Flask-Login + RBAC (4 roles)
- V0 Login, V1 Dashboard, V2 Listado scroll infinito
- V4 Detalle/Edición para Expedientes y Entidades
- V3 Tramitación acordeón con carga lazy (~90%)
- Edición de campos de Solicitud/Fase/Trámite/Tarea vía modales (sin creación ni borrado)
- Wizard de creación de expedientes (3 pasos)
- API REST expedientes con paginación cursor
- Componentes JS: SelectorBusqueda, ScrollInfinito, AcordeonLazy
- Tablas BD motor de reglas: `reglas_motor`, `condiciones_regla`, `tipos_solicitudes_compatibles`
- Modelos Python motor de reglas: ReglaMotor, CondicionRegla, TipoSolicitudCompatible

---

## M1 — Bloqueantes

**Descripción:** Tramitación ESFTT completa (CRUD de Solicitud/Fase/Trámite/Tarea) + sistema documental + importación legacy.
**Estado:** EN CURSO

Issues activos: #150, #149, #148, #147, #121

---

## M2 — Necesarios

**Descripción:** Generación de escritos, configuración de tablas maestras, gestión de carga/usuarios, listado inteligente.
**Estado:** PENDIENTE

Issues activos: #106

---

## M3 — Motor de reglas y plazos

**Descripción:** Motor de reglas completo (evaluador + configuración) + plazos legales con suspensión.
**Estado:** EN CURSO — diseño completo, implementación pendiente

Diseño: `docs/fuentesIA/MOTOR_REGLAS_arquitectura.md`
Issues activos: #152, #74

---

## M4 — Pre-producción

**Descripción:** Condiciones técnicas de despliegue: infraestructura, seguridad, numeración AT.
**Estado:** PENDIENTE

Issues activos: #151, #45, #120

---

## M5 — Post-producción

**Descripción:** Proyectos/instalaciones, GIS, auditoría configurable, mensajería interna, manual de usuario, importación legacy avanzada.
**Estado:** PENDIENTE

Issues activos: #76, #75, #27, #28, #85, #105, #4, #1

---

## Decisiones de arquitectura abiertas

| Decisión | Opciones | Afecta a |
|----------|----------|----------|
| Almacenamiento de documentos | Filesystem local / S3-compatible / PostgreSQL bytea | M1 (sistema documental) |
| Motor de plantillas | python-docx (Word) / Jinja2 sobre ODT / WeasyPrint (HTML→PDF) | M2 (generación escritos) |
| Firma electrónica | @firma JdA integrada / flujo manual en dos pasos | M2 (escritos) |
| Modelo de elementos eléctricos | Genérico con JSON / Tablas específicas por tipo | M5 (proyectos) |
| PostGIS vs coordenadas simples | PostGIS / lat+lon numérico | M5 (GIS) |
| Plazos: suspensión | Modelo de eventos de suspensión / solo fecha_limite estática | M3 (plazos) |
| Reglas de tramitación | Editables en producción por Supervisor / solo por técnico | M3 (motor), M2 (config) |
| Notificaciones externas | Email directo / Notific@ JdA / manual | M5 |
| Integración registro de entrada | SIGEM JdA / registro propio / ninguno | M1 (documental) |
| Legacy | Inventario pendiente: estructura, volumen, documentos | M1 (#121) |
