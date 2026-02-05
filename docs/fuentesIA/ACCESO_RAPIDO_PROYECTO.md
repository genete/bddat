# ACCESO RÁPIDO AL PROYECTO - BDDAT

**Repositorio:** https://github.com/genete/bddat (rama `main`)

Sistema de gestión de expedientes para la tramitación administrativa de instalaciones de alta tensión en Andalucía.

**Stack tecnológico:** PostgreSQL + Flask (SQLAlchemy) + Bootstrap 5

---

## 📋 ARCHIVOS IMPORTANTES

### Definición y Datos
- **`schema.sql`** - Esquema completo de la base de datos
- **`datos_estructurales.sql`** - Datos maestros (municipios, tipos de expedientes, fases, trámites, etc.)

### Código Fuente
- **Carpeta `app/models/`** - Modelos SQLAlchemy (lógica de negocio)
- **Carpeta `app/routes/`** - Rutas Flask (endpoints de la API)
- **Carpeta `app/templates/`** - Formularios y vistas HTML con Bootstrap 5
- **Carpeta `app/static/js/`** - Controles y validaciones JavaScript

### Documentación
- **`docs/fuentesIA/`** - Documentación de referencia para IA
  - `REGLAS_DESARROLLO.md` - Metodología de trabajo. **IMPORTANTE: CONSULTAR ANTES DE EMPEZAR A TRABAJAR EN EL REPOSITORIO**

---

## 🗂️ ESTRUCTURA DE BASE DE DATOS

**Esquemas PostgreSQL:**
- **`estructura`**: Tablas maestras y de configuración (municipios, tipos, catálogos)
- **`tramitacion`**: Datos operacionales (expedientes, solicitudes, actuaciones)

**Características:**
- Gestión completa del ciclo de vida de expedientes
- Control de fases y trámites administrativos
- Gestión de solicitantes y titulares
- Registro de actuaciones y documentación
- Sistema de tareas y seguimiento

---

## 🔧 CONVENCIÓN DE NOMBRES

**Regla general:** `snake_case` estricto

**Aplicable a:**
- Tablas: `expedientes`, `solicitudes`, `documentos_puros`
- Campos: `fecha_presentacion`, `numero_expediente`, `id_solicitante`
- Variables y funciones Python: `numero_expediente`, `procesar_expediente()`
- Rutas: `/expedientes/<int:id_expediente>`
- Templates: `expediente_detalle.html`, `solicitud_form.html`

**Única excepción:**
- Clases SQLAlchemy: `CamelCase` (ej: `class Expediente`, `class Solicitud`)

---

**Última actualización:** 25 de enero de 2026  
**Versión:** 2.0
