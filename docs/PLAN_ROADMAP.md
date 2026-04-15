# ROADMAP — BDDAT · Estado de implementación

> **Propósito:** Estado vivo del proyecto. Generado automáticamente desde GitHub.
> La verbosidad (qué falta, cómo hacerlo) vive en los issues de GitHub, no aquí.
> La visión estratégica y clasificación de bloques está en `PLAN_ESTRATEGIA.md`.
>
> **Generado:** 2026-04-11 · `python scripts/gen_roadmap.py`

---


## M1 — Bloqueantes

**Descripción:** Sin esto no hay producción viable. El sistema no reemplaza ningún proceso real o el abandono del sistema anterior es inviable.
**Estado:** ✅ COMPLETADO (25 cerrados)

_Sin issues abiertos._

---


## M2 — Necesarios

**Descripción:** El workaround temporal no aguanta más de semanas tras el arranque. Producción posible con workaround, pero no escala.
**Estado:** EN CURSO (26 cerrados)

**Issues abiertos:**
- #181 — [DOCS] Inspección automática de documentos — preclasificación asistida `enhancement`
- #182 — [DOCS] Códigos de clasificación embebidos en PDFs internos firmados `enhancement`
- #213 — [UI] Auditoría de datos asociados en vistas de detalle `ui`
- #256 — [UI] Vista de auditoría de expedientes — agregados por técnico y estado de pista `ui`
- #279 — [BD/UI] Añadir campo tecnologia en Proyecto — filtro en seguimiento `frontend` `backend`
- #281 — [REFACTOR] Migrar vistas Plantillas y Usuarios a arquitectura listado V2 `frontend` `backend` `ui`
- #285 — [UI/BE] Diagrama interactivo ESFTT de expediente — generación dinámica con Mermaid `frontend` `backend`
- #289 — [BE] Context Builders (Capa 2) para generación de escritos `backend`
- #290 — [BE/UI] Tarea INCORPORAR: tabla documentos_tarea (multi-doc, v5.5) `frontend` `backend`

---


## M3 — Motor de reglas y plazos

**Descripción:** Implementación post-producción, pero el diseño arquitectónico debe estar cerrado antes de arrancar para no forzar refactorizaciones de M1/M2.
**Estado:** EN CURSO (1 cerrados)

**Issues abiertos:**
- #106 — Listado códigos DIR3
- #153 — [DRAFT] Consultas a organismos en separatas — tabla entidades_consultadas
- #170 — [ADMIN] CRUD de reglas del motor — interfaz de configuración para Supervisor `enhancement`
- #171 — [ADMIN] CRUD de tablas maestras estructurales (tipos de Fase, Trámite y Tarea) `enhancement`
- #172 — [NEGOCIO] Plazos legales — cómputo en días hábiles con calendario de festivos `enhancement`
- #173 — [NEGOCIO] Suspensión de plazos legales `enhancement`
- #174 — [SEGURIDAD] Permisos granulares — control de acceso por acción y expediente `enhancement`
- #190 — [SERVICIO] Criterio PLAZO_ESTADO en motor de reglas — delegación a plazos.py
- #192 — [MODELO][SERVICIO] Requisitos documentales por procedimiento (documentos_procedimiento) `enhancement`
- #247 — [DISEÑO] Fase de consultas a organismos y análisis técnico `enhancement`
- #248 — [DISEÑO] Fase ANÁLISIS_SOLICITUD, checklist documental e items de requerimiento `enhancement`
- #276 — [BD] Poblar tipos_solicitudes_compatibles con el técnico del servicio `backend`
- #283 — [DOCS] Ampliar ESTRUCTURA_FTT a todos los tipos de expediente y validar tareas atómicas `documentation`
- #294 — [ESTRATEGIA] Pivot normativa → implementación motor: arranque en modo suave con reglas incrementales

---


## M4 — Pre-producción

**Descripción:** Condiciones técnicas sin las que no se puede desplegar: infraestructura, seguridad, datos legacy. No es funcionalidad, es requisito de despliegue.
**Estado:** EN CURSO (1 cerrados)

**Issues abiertos:**
- #45 — ⚠️ Cambiar SECRET_KEY antes de producción `critical` `production` `security`
- #105 — Migración BDD Alta Tensión (Access 2000) → PostgreSQL schema `legacy` `database` `legacy`
- #120 — Establecer base numero_at antes de produccion para separar expedientes nuevos de legacy `infrastructure`
- #151 — ⚠️ Definir infraestructura de soporte para despliegue a producción `production`
- #175 — [DATOS] Wizard de importación de expedientes y entidades legacy `enhancement`
- #176 — [SEGURIDAD] Adecuación al Esquema Nacional de Seguridad (ENS) `enhancement`
- #177 — [INFRA] HTTPS y certificado digital en producción `enhancement`
- #178 — [INFRA] Política de backup y recuperación de la base de datos `enhancement`
- #193 — [DOCS] Detector de URLs huérfanas en el pool — restauración conservando metadatos
- #227 — [BUG] SUPERVISOR puede desactivar usuario ADMIN via toggle del listado `bug`
- #243 — Metadatos estructurados en documentos como insumo para plantillas `enhancement`

---


## M5 — Post-producción

**Descripción:** Puede añadirse tras el arranque sin comprometer la misión principal. Valor real pero fuera del camino crítico inicial.
**Estado:** EN CURSO (1 cerrados)

**Issues abiertos:**
- #1 — Crear cuaderno de bitácora `enhancement`
- #4 — Permitir a los usuarios no registrados, solicitar acceso `enhancement`
- #27 — Implementar visualización cartográfica de instalaciones con PostGIS + Leaflet/OpenLayers `enhancement`
- #28 — Sistema de Notificaciones Internas y Solicitudes de Cambio de Rol `enhancement` `feature`
- #74 — Semáforos y alertas de vencimientos en dashboard `enhancement` `future` `ui` `post-MVP`
- #75 — Búsqueda global de expedientes (titular, AT, solicitante) `enhancement` `feature` `future` `post-MVP`
- #76 — Exportación listado expedientes (Excel/CSV) `enhancement` `feature` `future` `post-MVP`
- #195 — [POOL] #194 URI personalizado bddat:// para abrir ficheros desde navegador remoto
- #228 — [DOCS] Sistema de ayuda/manual de usuario `documentation`
- #240 — [UI][INFRA] Centralizar inicialización de tooltips con MutationObserver — eliminar reinits manuales dispersos `enhancement`
- #246 — Incrustar documento de entrada como subdocumento en plantillas generadoras `enhancement`
- #249 — [DISEÑO] Diagramas de flujo ESFTT por capas (Mermaid) `enhancement`
- #272 — [MODEL] Validación completa NIF/NIE con algoritmo oficial `backend`
- #273 — [UI] Footer — componente de estadísticas globales `frontend` `ui`
- #292 — [SPIKE] Infraestructura presenta: Reveal.js + manual de usuario → GitHub Pages desde develop `documentation`

---


## Decisiones de arquitectura abiertas

> Tabla orientativa — puede estar desactualizada. Consultar el documento
> de diseño correspondiente para el estado real de cada decisión.

| Decisión | Opciones |
|----------|----------|
| Almacenamiento de documentos | Filesystem local / S3-compatible / PostgreSQL bytea |
| Motor de plantillas | python-docx (Word) / Jinja2 sobre ODT / WeasyPrint (HTML→PDF) |
| Firma electrónica | @firma JdA integrada / flujo manual en dos pasos |
| Modelo de elementos eléctricos | Genérico con JSON / Tablas específicas por tipo |
| PostGIS vs coordenadas simples | PostGIS / lat+lon numérico |
| Plazos: suspensión | Modelo de eventos de suspensión / solo fecha_limite estática |
| Permisos granulares | Por acción+expediente en tablas / roles fijos ampliados |
| Notificaciones externas | Email directo / Notific@ JdA / manual |
| Integración registro de entrada | BandeJA JdA / registro propio / ninguno |
| Legacy | Inventario pendiente: estructura, volumen, documentos |
