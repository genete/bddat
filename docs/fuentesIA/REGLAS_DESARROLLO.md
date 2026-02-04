# REGLAS DE DESARROLLO CON IA - BDDAT

**Proyecto:** Sistema de tramitación administrativa de expedientes de autorización de instalaciones de alta tensión  
**Stack:** PostgreSQL + Flask (SQLAlchemy) + Bootstrap 5  
**Repositorio:** https://github.com/genete/bddat  
**Ramas principales:** `main` (producción) + `develop` (integración)  
**Documento creado:** 17 de enero de 2026  
**Última actualización:** 4 de febrero de 2026  
**Versión:** 3.3

---

## 1. Repositorio Oficial

**Ubicación:** https://github.com/genete/bddat  
**Ramas permanentes:**
- `main` - Código estable en producción, solo recibe merges de `develop`
- `develop` - Rama de integración continua, rama por defecto para desarrollo

**Descripción:** Sistema de tramitación administrativa de expedientes de autorización de instalaciones de alta tensión, construido con PostgreSQL, Flask (SQLAlchemy) y Bootstrap 5.

---

## 2. Metodología de Desarrollo

### 2.1 Workflow: GitHub Flow con Develop

**Estructura de ramas:**

```
develop ──●──●────●────●──●────●  (desarrollo continuo, rama por defecto)
           \      /    /    \  /
feature/X   ●──●─┘    /      ●┘   (ramas temporales)
bugfix/Y         ●──●─┘            (ramas temporales)
main ─────────────●─v0.1.0──●─v0.2.0  (solo versiones estables + tags)
```

**Principios:**
- **`develop`** es la rama por defecto donde se integran todos los cambios
- **`main`** solo recibe merges de `develop` cuando hay versión estable
- **Ramas temporales** (`feature/`, `bugfix/`) nacen de `develop` y vuelven a `develop`
- **Tags** se crean en `main` al completar milestones
- **Releases** se publican en GitHub al finalizar fases completas

---

### 2.2 Roles y Responsabilidades

#### Asistente (IA)

- Evalúo si el cambio requiere rama temporal o commit directo en `develop` (ver sección 12.1)
- Creo las ramas necesarias desde `develop` cuando aplica (`feature/`, `bugfix/`, etc.)
- Preparo cambios con descripción clara de ficheros afectados
- **Espero tu aprobación explícita** antes de cada commit
- Hago commits en la rama de desarrollo o en `develop` directamente (según tipo de cambio)
- Tras tus pruebas locales y OK, creo Pull Request a `develop`
- Hago merge del PR a `develop`
- **Borro la rama remota inmediatamente tras merge**
- Cuando completes un milestone, hago merge de `develop` → `main` y creo tag/release

#### Usuario (Tú)

- Realizas `git pull origin develop` para descargar cambios de integración
- Pruebas exhaustivas en local: `flask run`, formularios, migraciones, BD
- Si necesitas ajustes, los haces y ejecutas `git push origin [nombre-rama]`
- Das OK final para que IA cree el PR y haga merge
- Generas `schema.sql` localmente y lo subes manualmente
- **Borras ramas locales** tras merge del PR: `git branch -D nombre-rama`
- Verificas estado limpio del repositorio

---

### 2.3 Secuencia de Trabajo Estándar

#### Cambios Simples (Commit Directo en Develop)

**Para:** Documentación, typos, cambios en 1-2 archivos sin testing funcional

**Proceso:**
1. IA describe el cambio
2. Usuario da OK
3. IA hace commit directo en `develop`:
   ```
   [DOCS] Actualizar sección X de REGLAS_DESARROLLO
   ```
4. **FIN** - No rama temporal, no PR

---

#### Cambios Complejos (Rama Temporal + PR a Develop)

**Para:** Features, bugfixes, cambios que requieren testing

##### Fase 1: Análisis y Diseño

- Se revisan documentos en Knowledge Base y `docs/fuentesIA/`
- **IA consulta `schema.sql`** (generado por usuario localmente)
- Se identifican cambios necesarios
- Se registra claramente el alcance

##### Fase 2: Preparación Remota (por IA)

- Creo rama desde `develop`:
  - `feature/issue-XX-descripcion` - nuevas funcionalidades
  - `bugfix/issue-XX-descripcion` - corrección de errores
  - `refactor/descripcion-breve` - refactorizaciones
  - `docs/descripcion-breve` - solo documentación (si es complejo)
- Preparo código con explicación detallada
- Hago commits tras tu aprobación

##### Fase 3: Pruebas Locales (por Usuario)

- `git checkout nombre-rama`
- `git pull origin nombre-rama`
- `flask run` y pruebas funcionales
- Si hay ajustes, los haces y ejecutas `git push origin nombre-rama`

##### Fase 4: Pull Request y Merge (por IA)

- Tras tu OK final, creo PR: `nombre-rama` → `develop`
- Referencio el issue si aplica: "Closes #XX"
- Hago merge del PR
- **Borro rama remota inmediatamente:** `git push origin --delete nombre-rama`

##### Fase 5: Limpieza (por Usuario)

- `git checkout develop`
- `git pull origin develop`
- `git branch -D nombre-rama` (borrar rama local)
- Verificar: `git branch -vv` debe mostrar solo `* develop`

---

### 2.4 Creación de Versiones Estables (Main + Tags)

**Cuándo:** Al completar un milestone completo y pasar todas las pruebas

**Proceso:**

1. **Usuario verifica** que `develop` está completamente funcional y probado
2. **Usuario da OK** para crear versión estable
3. **IA ejecuta:**
   ```bash
   # Crear PR de develop a main
   # Título: "Release v0.X.0 - Milestone X.Y completado"
   # Descripción: resumen de cambios del milestone
   
   # Merge del PR (tras aprobación usuario)
   
   # Crear tag anotado en main
   git checkout main
   git pull origin main
   git tag -a v0.X.0 -m "Milestone X.Y: [Descripción]
   
   Cambios principales:
   - Cambio 1
   - Cambio 2
   - Cambio 3"
   
   git push origin v0.X.0
   ```

4. **IA crea Release en GitHub:**
   - Tag: `v0.X.0`
   - Título: "Fase X - [Nombre del Milestone]"
   - Descripción: Changelog del milestone
   - Assets: `schema_vX.X.X.sql`, `datos_estructurales_vX.X.X.sql` (si aplica)

5. **Usuario continúa trabajando** desde `develop` para siguiente milestone

---

## 3. Milestones y Organización de Issues

### 3.1 Estructura de Milestones

Los milestones representan objetivos funcionales completos dentro de cada fase.

#### Fase 1: Fundamentos y MVP Básico

**Milestone 1.1 - Infraestructura base**
- Tags: `infrastructure`, `database`, `setup`
- Hito: "Aplicación arranca sin errores"
- Issues ejemplo: #3, #4
- Entregable: Flask funcional + BD desplegada + datos maestros

**Milestone 1.2 - Gestión de solicitantes**
- Tags: `solicitantes`, `crud-basico`, `forms`
- Hito: "Registro de personas funcional"
- Entregable: CRUD completo solicitantes/titulares + validación NIF/CIF

**Milestone 1.3 - Expedientes básicos (MVP)**
- Tags: `expedientes`, `crud-basico`, `mvp`
- Hito: "Crear y consultar expediente"
- Entregable: CRUD expedientes + asociación solicitante + listado + detalle
- **Version:** `v0.1.0` - Primera release

---

#### Fase 2: Tramitación Administrativa

**Milestone 2.1 - Control de fases**
- Tags: `fases`, `transiciones`, `workflow`
- Hito: "Flujo de tramitación operativo"
- Entregable: Cambios de fase + validaciones + registro histórico

**Milestone 2.2 - Actuaciones y trámites**
- Tags: `actuaciones`, `tramites`, `historico`
- Hito: "Registro de gestiones"
- Entregable: Registrar actuaciones + asociar trámites + histórico cronológico
- Issues ejemplo: #1 (auditoría)

**Milestone 2.3 - Notificaciones básicas**
- Tags: `notificaciones`, `alertas`, `messaging`
- Hito: "Comunicación automática"
- Entregable: Sistema notificaciones internas + alertas de fase
- Issues ejemplo: #28
- **Version:** `v0.2.0`

---

#### Fase 3: Gestión Avanzada

**Milestone 3.1 - Documentación**
- Tags: `documentos`, `adjuntos`, `storage`
- Hito: "Gestión documental operativa"
- Entregable: Upload archivos + asociación a expediente + versionado

**Milestone 3.2 - Sistema de tareas**
- Tags: `tareas`, `asignaciones`, `deadlines`
- Hito: "Seguimiento de trabajo"
- Entregable: Crear tareas + asignar responsables + control vencimientos

**Milestone 3.3 - Búsqueda y filtros**
- Tags: `busqueda`, `filtros`, `indices`
- Hito: "Consultas eficientes"
- Entregable: Búsqueda multi-criterio + filtros avanzados + índices BD
- **Version:** `v0.3.0`

**Milestone 3.4 - Visualización cartográfica**
- Tags: `postgis`, `maps`, `geolocation`
- Hito: "Visor geográfico operativo"
- Entregable: PostGIS + Leaflet + visualización instalaciones + coordenadas editables
- Issues ejemplo: #27
- **Version:** `v0.4.0` (opcional si es muy grande)

---

#### Fase 4: Optimización y Producción

**Milestone 4.1 - Reporting**
- Tags: `reporting`, `dashboards`, `analytics`
- Hito: "Informes y estadísticas"
- Entregable: Panel estadísticas + informes predefinidos + exportación Excel/PDF

**Milestone 4.2 - Auditoría**
- Tags: `auditoria`, `logging`, `seguridad`
- Hito: "Trazabilidad completa"
- Entregable: Log acciones + histórico cambios + control permisos por rol

**Milestone 4.3 - Despliegue producción**
- Tags: `deployment`, `performance`, `backup`
- Hito: "Sistema en producción"
- Entregable: Configuración producción + backup automatizado + monitorización + docs usuario
- **Version:** `v1.0.0` - Primera versión producción

---

### 3.2 Tags de Issues Recomendados

**Por tipo:**
- `bug`, `enhancement`, `feature`, `documentation`, `refactor`

**Por área funcional:**
- `expedientes`, `solicitantes`, `actuaciones`, `documentos`, `tareas`, `notificaciones`, `maps`

**Por prioridad:**
- `mvp` (mínimo viable), `critical`, `high`, `medium`, `low`

**Por fase:**
- `fase-1`, `fase-2`, `fase-3`, `fase-4`

**Por estado técnico:**
- `database`, `backend`, `frontend`, `api`, `forms`, `validation`

---

## 4. Convenciones de Código y Naming

### 4.1 REGLA GENERAL: snake_case

En este proyecto se usa **snake_case** como convención general: tablas, columnas, variables, funciones, rutas, plantillas y nombres de fichero.

**Nota:** La insistencia estricta en snake_case es principalmente para Perplexity AI. Otras IAs pueden no requerir el mismo nivel de énfasis, pero se recomienda mantener consistencia.

#### Base de Datos (PostgreSQL)

```sql
-- Tablas
CREATE TABLE expedientes (...);
CREATE TABLE solicitudes (...);
CREATE TABLE documentos_puros (...);
CREATE TABLE tablas_maestras (...);

-- Campos
ALTER TABLE expedientes ADD COLUMN fecha_presentacion TIMESTAMP;
ALTER TABLE expedientes ADD COLUMN numero_expediente VARCHAR(50);
ALTER TABLE solicitudes ADD COLUMN id_solicitante INTEGER;
```

**Regla:** Nunca `Expedientes`, `SolicitudId`, `FechaPresentacion`. Siempre `expedientes`, `solicitud_id`, `fecha_presentacion`.

#### Modelos Python (SQLAlchemy)

**Clases de modelos: CamelCase (única excepción permitida)**

```python
class Expediente(db.Model):
    __tablename__ = 'expedientes'
    id_expediente = db.Column(db.Integer, primary_key=True)
    numero_expediente = db.Column(db.String(50), unique=True)
    fecha_presentacion = db.Column(db.DateTime)
    id_solicitante = db.Column(db.Integer, db.ForeignKey('solicitantes.id_solicitante'))

class Solicitud(db.Model):
    __tablename__ = 'solicitudes'
    # ...
```

**Correcto:**
- Nombre de clase: `CamelCase` (ej: `Expediente`, `Solicitud`, `DocumentoPuro`)
- Todo lo demás (atributos, métodos, variables): `snake_case`

#### Variables y Funciones en Python

```python
def procesar_expediente(id_expediente):
    numero_expediente = expediente.numero_expediente
    fecha_creacion = datetime.now()
    lista_solicitudes = db.session.query(Solicitud).filter_by(id_expediente=id_expediente).all()
```

#### Variables JavaScript

```javascript
const id_expediente = document.getElementById('expediente-id').value;
const fecha_presentacion = new Date(expediente.fecha_presentacion);
const numero_tramites = expedientes.length;
```

#### Rutas Flask

```python
@app.route('/expedientes/<int:id_expediente>')
def ver_expediente(id_expediente):
    return render_template('expediente_detalle.html', id_expediente=id_expediente)
```

#### Nombres de Archivos

```
expediente_modelo.py
solicitud_routes.py
expediente_detalle.html
funciones_validacion.js
```

---

## 5. Estructura de Carpetas del Repositorio

```
bddat/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── templates/
│   └── static/
│       ├── css/
│       └── js/
├── migrations/
│   └── versions/
├── docs/
│   └── fuentesIA/
│       ├── REGLAS_DESARROLLO.md
│       ├── GuiaGeneralNueva.md
│       └── [otros documentos]
├── tests/
├── utils/
├── config.py
├── run.py
├── schema.sql
├── datos_estructurales.sql
└── requirements.txt
```

---

## 6. Workflow Detallado

### 6.1 Cambios Simples (Commit Directo en Develop)

**Para:** Documentación, typos, cambios en 1-2 archivos sin testing funcional

**Proceso:**
1. IA describe el cambio
2. Usuario da OK
3. IA hace commit directo en `develop`:
   ```
   [DOCS] Actualizar sección X de REGLAS_DESARROLLO
   ```
4. **FIN** - No rama, no PR

---

### 6.2 Cambios Complejos (Rama Temporal + PR a Develop)

**Para:** Features, bugfixes, cambios que requieren testing

#### Paso 1: Creación de Rama (IA)

```bash
# IA crea rama desde develop
git checkout develop
git pull origin develop
git checkout -b feature/issue-XX-descripcion
git push origin feature/issue-XX-descripcion
```

**Convención de nombres de rama:**
- `feature/issue-XX-descripcion` - nueva funcionalidad
- `bugfix/issue-XX-descripcion` - corrección bug
- `refactor/descripcion-breve` - refactorización sin cambio funcional
- `docs/descripcion-breve` - documentación compleja

#### Paso 2: Desarrollo (IA)

- Preparo cambios en la rama
- Describo archivos afectados
- Espero aprobación explícita
- Hago commits tras cada OK:
  ```
  [MODELO] Crear modelo Solicitud con validaciones
  [RUTA] Implementar endpoint POST /solicitudes
  [TEMPLATE] Crear formulario solicitud_form.html
  ```

#### Paso 3: Pruebas Locales (Usuario)

```bash
git checkout feature/issue-XX-descripcion
git pull origin feature/issue-XX-descripcion
flask run
# Pruebas exhaustivas...
```

Si necesitas ajustes:
```bash
git add [archivos]
git commit -m "[TEST] Ajustar validación tras pruebas"
git push origin feature/issue-XX-descripcion
```

#### Paso 4: Pull Request (IA)

Tras tu OK final:
- Creo PR: `feature/issue-XX-descripcion` → `develop`
- Título: Breve descripción de la funcionalidad
- Descripción: Objetivo, cambios principales, issues relacionados
- Hago merge del PR (squash o merge commit según preferencia)

#### Paso 5: Limpieza (IA + Usuario)

**IA:**
```bash
git push origin --delete feature/issue-XX-descripcion
```

**Usuario:**
```bash
git checkout develop
git pull origin develop
git branch -D feature/issue-XX-descripcion
git branch -vv  # Verificar limpieza
```

---

### 6.3 Creación de Versiones Estables (Develop → Main)

**Trigger:** Milestone completado y todas las pruebas pasadas

**Proceso:**

#### Paso 1: Verificación (Usuario)

- Confirmas que `develop` está 100% funcional
- Todas las pruebas pasadas
- Milestone cerrado en GitHub
- Das OK para crear versión estable

#### Paso 2: Merge a Main (IA)

```bash
# Crear PR de develop a main
# Título: "Release v0.X.0 - Milestone X.Y: [Nombre]"
# Descripción: Resumen de funcionalidades del milestone

# Merge del PR (tras tu aprobación)
```

#### Paso 3: Crear Tag (IA)

```bash
git checkout main
git pull origin main
git tag -a v0.X.0 -m "Milestone X.Y: [Descripción]

Funcionalidades principales:
- Funcionalidad 1
- Funcionalidad 2
- Funcionalidad 3

Issues cerrados: #XX, #YY, #ZZ"

git push origin v0.X.0
```

#### Paso 4: Crear Release en GitHub (IA)

- **Tag:** v0.X.0
- **Título:** "Fase X - [Nombre del Milestone]"
- **Descripción:** Resumen ejecutivo del milestone con funcionalidades clave
- **Assets:** 
  - `schema_v0.X.0.sql` (si cambia BD)
  - `datos_estructurales_v0.X.0.sql` (si cambian datos maestros)

#### Paso 5: Continuar Desarrollo (Usuario)

```bash
git checkout develop
git pull origin develop
# Continuar con siguiente milestone
```

---

## 7. Mensajes de Commit

**Formato:** `[CATEGORÍA] Descripción breve en imperativo`

**Categorías disponibles:**

- `[BD]` - Cambios en base de datos
- `[MODELO]` - Cambios en modelos SQLAlchemy
- `[RUTA]` - Cambios en rutas Flask
- `[TEMPLATE]` - Cambios en templates HTML
- `[STYLE]` - Cambios en CSS/JavaScript
- `[MIGA]` - Cambios en migraciones
- `[TEST]` - Pruebas y testing
- `[DOCS]` - Cambios en documentación
- `[MERGE]` - Merge de pull requests
- `[RELEASE]` - Preparación de releases

**Ejemplos:**

```
[BD] Añadir tabla expedientes_auditoria
[MODELO] Crear modelo Solicitud con validaciones NIF/CIF
[RUTA] Implementar endpoint GET /expedientes/<id>
[TEMPLATE] Crear formulario solicitud con validación Bootstrap
[STYLE] Ajustar colores mensajes informativos con hover
[MIGA] Añadir campo geom_punto a tabla proyectos
[TEST] Verificar flujo completo creación expediente
[DOCS] Actualizar REGLAS_DESARROLLO con workflow develop
[MERGE] Merge feature/issue-3-mejorar-mensajes a develop
[RELEASE] Preparar release v0.1.0 - MVP expedientes
```

---

## 8. Historial de Cambios

**Fuente de verdad:** Pull Requests cerrados en GitHub

**Ver historial completo:** [Pull Requests cerrados](https://github.com/genete/bddat/pulls?q=is%3Apr+is%3Aclosed+sort%3Aupdated-desc)

**No se mantiene archivo CHANGELOG.md** porque:
- ✅ GitHub ya tiene toda la información (commits, diffs, conversaciones)
- ✅ Búsqueda y filtros superiores (por milestone, etiqueta, autor, fecha)
- ✅ Elimina trabajo manual redundante
- ✅ Evita desincronizaciones

**Nota:** Decisión tomada 04/02/2026 tras análisis de coste/beneficio.

---

## 9. Gestión de Tags y Releases

### 9.1 Tags Semánticos

**Formato:** `vMAJOR.MINOR.PATCH`

**Criterios:**
- `MAJOR` (1.0.0): Cambios que rompen compatibilidad, Fase completada
- `MINOR` (0.1.0): Nuevas funcionalidades, Milestone completado
- `PATCH` (0.1.1): Hotfixes, correcciones menores

**Ejemplos:**
- `v0.1.0` - Milestone 1.3 completado (MVP expedientes)
- `v0.2.0` - Milestone 2.3 completado (notificaciones)
- `v0.2.1` - Hotfix validación NIF en producción
- `v1.0.0` - Fase 4 completada (sistema en producción)

### 9.2 Releases en GitHub

**Cuándo crear:**
- Al finalizar cada milestone importante (1.3, 2.3, 3.4, 4.3)
- Al completar cada fase completa
- Solo en hotfixes críticos que requieren distribución urgente

**Contenido:**
- Basado en tag específico
- Descripción ejecutiva del milestone/fase
- Listado de funcionalidades clave
- Issues cerrados
- Assets SQL si cambia estructura BD

---

## 10. Comandos Git Esenciales

### 10.1 Usuario (trabajo local)

**Sincronizar con develop:**
```bash
git checkout develop
git pull origin develop
```

**Trabajar en rama de feature:**
```bash
git checkout feature/issue-XX-descripcion
git pull origin feature/issue-XX-descripcion
# ... hacer cambios ...
git add [archivos]
git commit -m "[CATEGORÍA] Descripción"
git push origin feature/issue-XX-descripcion
```

**Limpiar tras merge:**
```bash
git checkout develop
git pull origin develop
git branch -D feature/issue-XX-descripcion
```

**Verificar estado:**
```bash
git status
git branch -vv
git log --oneline -10
```

---

### 10.2 IA (trabajo remoto)

**Crear rama:**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/issue-XX-descripcion
git push origin feature/issue-XX-descripcion
```

**Commit en rama:**
```bash
git add [archivos]
git commit -m "[CATEGORÍA] Descripción"
git push origin feature/issue-XX-descripcion
```

**Borrar rama tras merge:**
```bash
git push origin --delete feature/issue-XX-descripcion
```

**Crear tag:**
```bash
git checkout main
git pull origin main
git tag -a v0.X.0 -m "Mensaje del tag"
git push origin v0.X.0
```

---

## 11. Uso de Git Stash

### 11.1 Cuándo Usar Stash

**Casos válidos:**
- Necesitas cambiar de rama urgentemente con trabajo sin terminar
- Experimento que no quieres commitear todavía
- Necesitas hacer `git pull` con cambios locales no commiteados

**NO usar stash como:**
- Sistema de versionado (para eso están los commits)
- Almacenamiento de código "por si acaso" (para eso están las ramas)

### 11.2 Comandos Básicos

```bash
# Guardar cambios temporalmente
git stash save "WIP: formulario solicitud a medias"

# Listar stashes
git stash list

# Recuperar último stash (lo elimina)
git stash pop

# Aplicar stash sin eliminarlo
git stash apply stash@{0}

# Eliminar stash
git stash drop stash@{1}

# Limpiar todos los stashes
git stash clear
```

### 11.3 Ejemplo de Uso

```bash
# Trabajando en feature/formulario-actuaciones
# Llega bug urgente que arreglar

git stash save "WIP: validación formulario actuaciones"
git checkout develop
git checkout -b bugfix/issue-XX-validacion-nif

# ... arreglar bug, commit, PR, merge ...

git checkout feature/formulario-actuaciones
git stash pop  # Recuperar trabajo

# ... continuar con formulario ...
```

---

## 12. Gestión de Ramas

### 12.1 Cuándo Crear Rama Temporal vs Commit Directo en Develop

#### Commit Directo en Develop (sin rama ni PR)

**Usar para cambios simples que:**
- Modifican 1-2 archivos solamente
- No requieren testing funcional (solo revisión de texto/docs)
- Son actualizaciones de documentación pura
- Son typos o correcciones menores en código sin lógica
- No afectan modelos, BD o flujo de negocio

**Ejemplos:**
- Actualizar `REGLAS_DESARROLLO.md`
- Corregir typo en comentario de código
- Actualizar `README.md`
- Ajustar `.gitignore`
- Actualizar documentación en `docs/fuentesIA/`
- Cambios en archivos de configuración menores

**Proceso:**
1. IA describe cambio
2. Usuario da OK
3. IA hace commit directo en `develop`
4. **No rama, no PR**

---

#### Rama Temporal + PR (workflow completo)

**Usar para cambios complejos que:**
- Modifican 3+ archivos
- Requieren testing funcional (`flask run`)
- Afectan modelos, rutas, templates conjuntamente
- Implican migraciones de BD
- Pueden tener efectos secundarios
- Necesitan revisión detallada
- Implementan features de issues

**Ejemplos:**
- Nuevas features completas
- Cambios en modelos SQLAlchemy
- Nuevas rutas + templates coordinados
- Refactorizaciones de lógica
- Migraciones de base de datos
- Issues que requieren múltiples commits

**Proceso:** Ver sección 6.2

---

### 12.2 Regla de Oro: Repositorio Limpio

**Principio fundamental:**
> Toda rama temporal creada debe terminar mergeada o explícitamente descartada. NUNCA dejar ramas huérfanas.

**Limpieza obligatoria tras merge:**

**IA (inmediatamente):**
```bash
git push origin --delete nombre-rama
```

**Usuario (tras actualizar develop):**
```bash
git checkout develop
git pull origin develop
git branch -D nombre-rama
```

**Resultado esperado:**
- ✅ Solo ramas permanentes: `main`, `develop`
- ✅ Solo ramas temporales activas en desarrollo
- ✅ Historial claro en PRs de GitHub

---

### 12.3 Configuración Recomendada en GitHub

**Una sola vez, configurar:**

1. **Settings → Branches:**
   - Default branch: `develop`
   
2. **Settings → General → Pull Requests:**
   - ☑️ Automatically delete head branches
   - ☐ Allow squash merging (**DESMARCAR** - preservar historial completo de commits)
   - ☑️ Allow merge commits (este es el método que usamos)

**Resultado:**
- PRs se crean por defecto hacia `develop`
- Ramas se borran automáticamente tras merge
- **Todos los commits individuales se preservan en el historial**

---

## 13. Checklist Pre-Commit

### 13.1 IA (antes de solicitar OK)

- [ ] Evaluado: ¿rama temporal o commit directo?
- [ ] Rama creada con nombre apropiado (si aplica)
- [ ] Cambio documentado y explicado
- [ ] Nombres en snake_case (excepto clases en CamelCase)
- [ ] Consultado `schema.sql` para cambios BD
- [ ] Código sigue convenciones del proyecto
- [ ] Mensaje de commit con categoría correcta

---

### 13.2 Usuario (antes de git push)

- [ ] `git pull` completado
- [ ] `flask run` funciona sin errores
- [ ] BD responde correctamente
- [ ] Formularios funcionan
- [ ] Migraciones aplicadas: `flask db upgrade`
- [ ] No hay archivos `.pyc`, `__pycache__`, `.env`
- [ ] Nombres en snake_case
- [ ] Mensaje de commit descriptivo

---

## 14. Resumen de Responsabilidades

| Actividad | IA | Usuario |
|-----------|-------|------|
| Evaluar: rama vs commit directo | ✅ | |
| Crear ramas temporales desde develop | ✅ | |
| Hacer commits remotos (tras OK) | ✅ | |
| Crear PRs a develop | ✅ | |
| Merge PRs a develop | ✅ | |
| Borrar ramas remotas tras merge | ✅ | |
| Crear PRs de develop a main (releases) | ✅ | |
| Crear tags en main | ✅ | |
| Crear GitHub Releases | ✅ | |
| Hacer git pull | | ✅ |
| Probar en local (flask run) | | ✅ |
| Generar schema.sql y subirlo | | ✅ |
| Hacer migraciones locales | | ✅ |
| Commits de testing/ajustes | | ✅ |
| Git push (cambios locales) | | ✅ |
| Borrar ramas locales tras merge | | ✅ |
| Dar OK para commits y PRs | | ✅ |
| Dar OK para releases | | ✅ |
| Verificar repositorio limpio | | ✅ |

---

## 15. Estrategia de Versionado

### 15.1 Milestones → Versiones

| Milestone | Versión | Fase | Release |
|-----------|---------|------|---------|
| 1.1 | - | Fase 1 | No |
| 1.2 | - | Fase 1 | No |
| 1.3 | **v0.1.0** | Fase 1 | ✅ MVP |
| 2.1 | - | Fase 2 | No |
| 2.2 | - | Fase 2 | No |
| 2.3 | **v0.2.0** | Fase 2 | ✅ |
| 3.1 | - | Fase 3 | No |
| 3.2 | - | Fase 3 | No |
| 3.3 | **v0.3.0** | Fase 3 | ✅ |
| 3.4 | **v0.4.0** | Fase 3 | ✅ (PostGIS) |
| 4.1 | - | Fase 4 | No |
| 4.2 | - | Fase 4 | No |
| 4.3 | **v1.0.0** | Fase 4 | ✅ PRODUCCIÓN |

### 15.2 Hotfixes

**Si hay bug crítico en `main`:**

```bash
# IA crea rama desde main
git checkout main
git checkout -b hotfix/fix-validacion-nif
# ... arreglar ...
# PR a main + PR a develop (o cherry-pick)
# Tag nuevo: v0.1.1 (incrementa PATCH)
```

---

## 16. Transición del Workflow Actual

### 16.1 Estado Actual (25 enero 2026)

- ✅ 1 rama: `main`
- ✅ GitHub Flow básico funcionando
- ✅ Ramas temporales se borran correctamente tras merge
- ❌ Sin rama `develop`
- ❌ Sin tags ni releases
- ❌ Sin milestones asignados a issues

### 16.2 Pasos de Migración

**Paso 1: Crear rama develop (ahora)**

```bash
# IA ejecuta:
git checkout main
git pull origin main
git checkout -b develop
git push origin develop
```

**Paso 2: Configurar develop como rama por defecto en GitHub**

Settings → Branches → Default branch → cambiar a `develop`

**Paso 3: Crear milestones en GitHub**

Issues → Milestones → New milestone:
- Milestone 1.1 - Infraestructura base (fecha estimada)
- Milestone 1.2 - Gestión solicitantes (fecha estimada)
- Milestone 1.3 - Expedientes básicos MVP (fecha estimada)

**Paso 4: Reasignar issues existentes**

- Issue #3 → Milestone 1.1
- Issue #4 → Milestone 1.1
- Issue #1 → Milestone 2.2
- Issue #28 → Milestone 2.3
- Issue #27 → Milestone 3.4

**Paso 5: Partir de develop para nuevos cambios**

A partir de ahora:
- Trabajo diario en `develop` o ramas desde `develop`
- `main` solo recibe merges al completar milestones
- Tags y releases solo en `main`

---

## 17. Documentación y Fuentes de Verdad

### 17.1 Jerarquía de Documentación

**Orden de prevalencia (mayor a menor):**

1. **Código en el repositorio** (`app/`, `schema.sql`, `migrations/`)
2. **Documentación en repositorio** (`docs/fuentesIA/`)
3. **Pull Requests en GitHub** (historial completo)
4. **Otras fuentes de conocimiento de IA**

### 17.2 Documentos Clave en Repositorio

- `docs/fuentesIA/REGLAS_DESARROLLO.md` - Este documento
- `docs/fuentesIA/GuiaGeneralNueva.md` - Plan general del proyecto
- `docs/fuentesIA/ACCESO_RAPIDO_PROYECTO.md` - Referencia rápida
- `schema.sql` - Definición completa BD (generado por usuario)

---

## 18. Principios de Trabajo

1. **Documentación primero:** Diseñar antes de codificar
2. **Incrementalidad:** Cambios pequeños, probados, sincronizados
3. **Trazabilidad:** Git es la fuente de verdad del código
4. **Aprobación previa:** No commits remotos sin OK explícito del usuario
5. **Repositorio limpio:** Borrado inmediato de ramas tras merge
6. **Develop como hub:** Todo cambio pasa por `develop` antes de `main`
7. **Main siempre estable:** Solo código probado y versionado
8. **Milestones claros:** Issues organizados por objetivos funcionales

---

## 19. Documentación de Decisiones Arquitectónicas

### 19.1 ¿Por qué documentar decisiones?

Cuando tomamos decisiones arquitectónicas importantes, no solo debemos implementarlas, sino también **documentar el razonamiento** detrás de ellas.

**Beneficios:**
- Mantener el contexto de **POR QUÉ** se tomó una decisión
- Evitar revisar las mismas alternativas en el futuro
- Facilitar onboarding de nuevos desarrolladores
- Proporcionar trazabilidad histórica
- Ayudar a asistentes IA a entender mejor las decisiones previas

---

### 19.2 ¿Cuándo documentar?

Documenta cuando:
- ✅ Se evalúan **múltiples alternativas técnicas** (ej: vistas vs tablas, REST vs GraphQL)
- ✅ La decisión **afecta la arquitectura** del sistema (ej: estructura de base de datos, patrones de diseño)
- ✅ Existen **trade-offs importantes** a considerar (ej: rendimiento vs mantenibilidad)
- ✅ Se **rechaza un enfoque** que podría parecer "obvio" o "estándar"
- ✅ La decisión tendrá **impacto a largo plazo** en el proyecto

---

### 19.3 ¿Dónde documentar?

**En los issues de GitHub**, como comentarios en el issue relacionado.

**NO crear documentos separados** para cada decisión (aumenta overhead de mantenimiento).

**Opcionalmente**, si la decisión es muy relevante, crear un issue específico etiquetado con `documentation` que referencie la discusión original.

---

### 19.4 Formato Recomendado

Usa esta estructura en los comentarios del issue:

```markdown
## 💬 Análisis de Alternativas de Diseño

### Contexto
[Explicar el problema que se está resolviendo]

### Opciones Evaluadas
1. **Opción A**: [Descripción breve]
2. **Opción B**: [Descripción breve]

---

## Opción 1: [Nombre]

### Estructura
[Código, diagramas, ejemplos]

### ✅ Ventajas
- [Ventaja 1]
- [Ventaja 2]

### ❌ Desventajas
- [Desventaja 1]
- [Desventaja 2]

---

## Opción 2: [Nombre]

[Misma estructura que Opción 1]

---

## ⚖️ Comparación

[Tabla comparativa si es útil]

---

## 🎯 Decisión Final

### ✅ Se adopta: **[Opción elegida]**

### Razones
1. [Razón 1]
2. [Razón 2]

### Implicaciones
- [Implicación 1: qué hay que cambiar/crear]
- [Implicación 2: efectos en otras partes del sistema]

### Próximos Pasos
- [ ] [Acción 1]
- [ ] [Acción 2]
```

---

### 19.5 Ejemplo Real

Ver issue [#62](https://github.com/genete/bddat/issues/62), comentarios sobre "Análisis de Alternativas de Diseño" donde se documenta la decisión de usar tablas inversas vs vistas actualizables para el modelo de entidades.

---

### 19.6 Herramientas para Escalabilidad Futura

Si el proyecto crece mucho, considerar herramientas formales como:
- [ADR (Architecture Decision Records)](https://adr.github.io/)
- Documentación en `docs/decisions/` con archivos Markdown numerados

Pero **para BDDAT, documentar en issues es suficiente** por ahora.

---

**Documento creado:** 17 de enero de 2026, 21:24 CET  
**Última actualización:** 4 de febrero de 2026, 06:41 CET  
**Versión:** 3.3  
**Referencia:** Repositorio oficial genete/bddat en GitHub