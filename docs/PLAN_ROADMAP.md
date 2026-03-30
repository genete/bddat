# ROADMAP — BDDAT · Estado de implementación

> **Propósito:** Estado vivo del proyecto. Se actualiza al cerrar issues y milestones.
> La verbosidad (qué falta, cómo hacerlo) vive en los issues de GitHub, no aquí.
> La visión estratégica y clasificación de bloques está en `PLAN_ESTRATEGIA.md`.
>
> **Última actualización:** 2026-03-12

---

## Estado de partida (operativo a 2026-03-01)

- Modelos SQLAlchemy completos: Expediente, Solicitud, Fase, Trámite, Tarea, Entidad, Proyecto, Usuario + maestros
- Autenticación Flask-Login + RBAC (4 roles)
- V0 Login, V1 Dashboard, V2 Listado scroll infinito
- V4 Detalle/Edición para Expedientes y Entidades
- V3 Tramitación: esqueleto breadcrumbs operativo (#157) — navegación por los 5 niveles con URL propia, CRUD pendiente
- Wizard de creación de expedientes (3 pasos)
- API REST expedientes con paginación cursor
- Componentes JS: SelectorBusqueda, ScrollInfinito, AcordeonLazy
- Tablas BD motor de reglas: `reglas_motor`, `condiciones_regla`, `tipos_solicitudes_compatibles`
- Modelos Python motor de reglas: ReglaMotor, CondicionRegla, TipoSolicitudCompatible
- Evaluador motor de reglas: `app/services/motor_reglas.py` — evaluar(evento, entidad, ...) con checks hardcoded + criterios BD

---

## M1 — Bloqueantes

**Descripción:** Tramitación ESFTT completa (CRUD de Solicitud/Fase/Trámite/Tarea) + sistema documental.
**Estado:** ✅ COMPLETADO (2026-03-12)

Issues activos: ninguno

---

## M2 — Necesarios

**Descripción:** Generación de escritos, gestión de usuarios, listado inteligente de trabajo.
**Estado:** EN CURSO

**Pendiente:**
- Generación de escritos administrativos conectada a tramitación (#167) — fases:
  - **Fase 0** (commit directo develop): fix `Documento.__str__` (R6) + export `campos_catalogo`
  - **Fase 1** `feature/167-fase-1-tipo-solicitud-directo`: solicitudes FK directa + whitelist ESFTT (3 tablas)
  - **Fase 2** `feature/167-fase-2-rename-plantillas`: rename `tipos_escritos`→`plantillas` + limpieza + nuevos campos
  - **Fase 3** `feature/167-fase-3-nombre-en-plantilla`: añadir `nombre_en_plantilla` × 5 tablas tipo_
  - **Fase 4** `feature/167-fase-4-admin-cascada`: admin plantillas con selectores en cascada E→S→F→T
  - **Fase 5** `feature/167-fase-5-generacion`: motor de generación completo (B1-B8) desde tarea REDACTAR
  - **Fase 6** `feature/167-fase-6-trazabilidad`: códigos embebidos + parseo automático
  - Fases 1, 2 y 3 son **independientes entre sí**. Fases 4-6 son secuenciales.
  - Diseño completo: `docs/DISEÑO_GENERACION_ESCRITOS.md`
- Gestión de usuarios — adaptar a vistas V4 (#168)
- Listado inteligente multi-pista con deducción automática de estados (#169) — servicio `app/services/seguimiento.py`
- Semáforos y alertas de vencimiento (#74)
- Arquitectura generación de escritos: plantillas + context builders (#189)
- Inspección automática de documentos — preclasificación asistida (#181)
- Códigos de clasificación embebidos en PDFs internos firmados (#182)
- Revisar color thead V2 y cabecera tramitación BC (#203)
- Columnas dinámicas en metadata.json — Fase 3 frontend (#204)
- Clase CSS estandarizada para listados embebidos y theads internos (#205)
- Refactor FiltrosExpedientes → FiltrosListado genérica (#206)
- Auditoría de datos asociados en vistas de detalle (#213)
- Refactorizar control de usuario en navbar (#216)

Issues activos: #74, #167, #168, #169, #181, #182, #189, #203, #204, #205, #206, #213, #216

---

## M3 — Motor de reglas y plazos

**Descripción:** Motor de reglas completo (evaluador + configuración por Supervisor) + plazos legales con suspensión + permisos granulares.
**Estado:** EN CURSO — evaluador implementado, pendiente UI de configuración y plazos

Diseño: `docs/DISEÑO_MOTOR_REGLAS.md`

**Pendiente:**
- CRUD de reglas del motor — interfaz Supervisor (#170)
- CRUD de tablas maestras estructurales — tipos Fase/Trámite/Tarea (#171)
- Plazos legales en días hábiles con calendario de festivos (#172)
- Suspensión de plazos por causas tasadas (#173)
- Permisos granulares por acción y expediente (#174)

Issues cerrados: #152 (evaluador — PR #154, 2026-02-28), #85 (duplicado de #174)
Issues activos: #170, #171, #172, #173, #174, #190

---

## M4 — Pre-producción

**Descripción:** Condiciones técnicas de despliegue: infraestructura, seguridad, numeración AT, datos legacy.
**Estado:** PENDIENTE

**Pendiente:**
- Infraestructura de despliegue (#151)
- SECRET_KEY y variables de entorno en producción (#45)
- Establecer base numero_at (#120)
- Wizard de importación de expedientes y entidades legacy (#175)
- Adecuación al ENS (#176)
- HTTPS y certificado digital (#177)
- Política de backup y recuperación de BD (#178)
- Migración Access → PostgreSQL schema legacy (#105)

Issues activos: #45, #105, #120, #151, #175, #176, #177, #178

---

## M5 — Post-producción

**Descripción:** GIS, DIR3, auditoría/bitácora, mensajería interna, búsqueda global, exportación, solicitud de acceso.
**Estado:** PENDIENTE

Issues activos: #1, #4, #27, #28, #75, #76, #106, #192, #195

---

## Decisiones de arquitectura abiertas

| Decisión | Opciones | Afecta a |
|----------|----------|----------|
| Almacenamiento de documentos | Filesystem local / S3-compatible / PostgreSQL bytea | M1 (sistema documental) |
| Motor de plantillas | python-docx (Word) / Jinja2 sobre ODT / WeasyPrint (HTML→PDF) | M2 (generación escritos) |
| Firma electrónica | @firma JdA integrada / flujo manual en dos pasos | M2 (escritos) |
| Estados de pista listado inteligente | Deducidos automáticamente de ESFTT vía `seguimiento.py` | M2 (#169) |
| Modelo de elementos eléctricos | Genérico con JSON / Tablas específicas por tipo | M5 (proyectos) |
| PostGIS vs coordenadas simples | PostGIS / lat+lon numérico | M5 (GIS) |
| Plazos: suspensión | Modelo de eventos de suspensión / solo fecha_limite estática | M3 (#173) |
| Permisos granulares | Por acción+expediente en tablas / roles fijos ampliados | M3 (#174) |
| Notificaciones externas | Email directo / Notific@ JdA / manual | M5 |
| Integración registro de entrada | BandeJA JdA / registro propio / ninguno | M2 (escritos, #167) |
| Legacy | Inventario pendiente: estructura, volumen, documentos | M4 (#105, #175) |
