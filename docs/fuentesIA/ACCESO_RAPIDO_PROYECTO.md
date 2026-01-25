# ACCESO RÁPIDO AL PROYECTO - BDDAT

**Documento creado:** 22 de enero de 2026  
**Propósito:** Referencia rápida para IA sobre ubicación y estructura del proyecto

---

## 1. Identificación del Repositorio

**Repositorio oficial:** https://github.com/genete/bddat  
**Rama principal:** `main`  
**Propietario:** genete

**Stack tecnológico:**
- Backend: Flask (Python) con SQLAlchemy
- Base de datos: PostgreSQL
- Frontend: Bootstrap 5
- Control de versiones: Git/GitHub

---

## 2. Ubicación de Fuentes de Conocimiento

### 2.1 Documentación de Referencia Principal

**Ruta en repositorio:** `docs/fuentesIA/`

**Documentos clave:**
- `REGLAS_DESARROLLO.md` - Metodología completa de trabajo con IA
- `Tablas.md` - Documentación de estructura de base de datos
- `SOLICITUDES_TIPOS.md` - Plantilla de referencia para documentación modular
- `TIPOS_SOLICITUDES.md` - Plantilla de referencia para documentación modular
- `ACCESO_RAPIDO_PROYECTO.md` - Este documento

### 2.2 Estructura de BD Actual

**Archivo de esquema:** `schema.sql` (raíz del proyecto)
- Generado localmente por el usuario mediante script
- Subido manualmente al repositorio
- **Fuente de verdad** para consultas sobre estructura de BD
- Debe consultarse SIEMPRE antes de proponer cambios en BD

### 2.3 Changelog

**Ubicación:** `docs/CHANGELOG.md`
- Registro cronológico de cambios
- **Actualizado en la misma rama de desarrollo** antes del PR
- Formato: fecha, PR, issue, cambios por categoría

---

## 3. Principios de Trabajo Esenciales

### 3.1 Convención de Nombres (CRÍTICO)

**Regla general:** `snake_case` estricto

**Aplicable a:**
- Tablas de BD: `expedientes`, `solicitudes`, `documentos_puros`
- Campos de BD: `fecha_presentacion`, `numero_expediente`, `id_solicitante`
- Variables Python: `numero_expediente`, `fecha_creacion`, `lista_solicitudes`
- Funciones Python: `procesar_expediente()`, `validar_documento()`
- Rutas Flask: `/expedientes/<int:id_expediente>`
- Templates: `expediente_detalle.html`, `solicitud_form.html`
- Archivos: `expediente_modelo.py`, `solicitud_routes.py`

**Única excepción:**
- Clases de modelos SQLAlchemy: `CamelCase` (ej: `class Expediente`, `class Solicitud`)

### 3.2 Workflow de Desarrollo

**IA (Asistente):**
1. Crea rama de desarrollo (`feature/`, `bugfix/`, `hotfix/`, `refactor/`, `docs/`)
2. Prepara cambios con descripción detallada
3. **Espera aprobación explícita del usuario** antes de cada commit
4. Hace commit y push remoto tras OK
5. **Actualiza `docs/CHANGELOG.md` en la misma rama** antes del PR
6. Crea Pull Request (incluye changelog)
7. Hace merge del PR

**Usuario:**
1. Ejecuta `git pull` para traer cambios
2. Prueba localmente con `flask run`
3. Genera y sube `schema.sql` manualmente
4. Hace commits de migraciones locales y ajustes post-testing
5. Da OK explícito para commits y PRs

### 3.3 Formato de Commits

**Estructura:** `[CATEGORÍA] Descripción breve en imperativo`

**Categorías:**
- `[BD]` - Cambios en base de datos
- `[MODELO]` - Cambios en modelos SQLAlchemy
- `[RUTA]` - Cambios en rutas Flask
- `[TEMPLATE]` - Cambios en templates HTML
- `[STYLE]` - Cambios en CSS/JavaScript
- `[MIGA]` - Cambios en migraciones
- `[TEST]` - Pruebas y testing
- `[DOCS]` - Cambios en documentación
- `[CHANGELOG]` - Actualización de changelog
- `[MERGE]` - Merge de pull requests

**Ejemplos:**
```
[BD] Añadir tabla expedientes_auditoría
[MODELO] Crear modelo Solicitud con validaciones
[RUTA] Implementar endpoint GET /expedientes/<id>
[CHANGELOG] Documentar detección de proyectos interprovinciales
[DOCS] Actualizar documentación tablas maestras
```

---

## 4. Estructura de Directorios del Proyecto

```
bddat/
├── app/
│   ├── models/          # Modelos SQLAlchemy
│   ├── routes/          # Rutas Flask
│   ├── templates/       # Templates Jinja2
│   └── static/          # CSS, JS, imágenes
├── migrations/          # Migraciones Alembic
├── docs/
│   ├── CHANGELOG.md     # Registro de cambios
│   └── fuentesIA/       # Documentación de referencia (FUENTE DE VERDAD)
├── tests/
├── config.py
├── run.py
├── schema.sql           # Esquema BD generado localmente
└── requirements.txt
```

---

## 5. Reglas de Prioridad

1. **Los documentos en `docs/fuentesIA/` prevalecen** sobre otras fuentes de conocimiento
2. **`schema.sql` es la fuente de verdad** para la estructura de BD
3. **No hacer commits remotos sin OK explícito** del usuario
4. **Consultar `REGLAS_DESARROLLO.md`** para detalles completos del workflow
5. **Mantener `snake_case` estricto** en todo el código (excepto clases de modelos)
6. **Actualizar changelog en la misma rama** de desarrollo (no rama separada)

---

## 6. Comandos Esenciales de Consulta

### Para IA (antes de proponer cambios):
- Leer `schema.sql` para conocer estructura actual de BD
- Consultar `docs/fuentesIA/Tablas.md` para lógica de negocio
- Verificar `docs/CHANGELOG.md` para cambios recientes

### Para Usuario (verificación local):
```bash
git status
git log --oneline -5
flask run
flask db upgrade
```

---

## 7. Resumen Ejecutivo

**Pregunta rápida:** ¿Qué repositorio usamos?  
**Respuesta:** `https://github.com/genete/bddat` (rama `main`)

**Pregunta rápida:** ¿Dónde está la documentación de referencia?  
**Respuesta:** `docs/fuentesIA/` en el repositorio

**Pregunta rápida:** ¿Cuál es la fuente de verdad para BD?  
**Respuesta:** `schema.sql` (raíz del proyecto)

**Pregunta rápida:** ¿Qué convención de nombres usamos?  
**Respuesta:** `snake_case` estricto (excepto clases de modelos en `CamelCase`)

**Pregunta rápida:** ¿Puedo hacer commits remotos directamente?  
**Respuesta:** NO. Siempre esperar aprobación explícita del usuario.

**Pregunta rápida:** ¿Cómo actualizo el changelog?  
**Respuesta:** En la misma rama de desarrollo antes del PR, no en rama separada.

---

**Última actualización:** 25 de enero de 2026, 08:00 CET  
**Versión:** 1.2
