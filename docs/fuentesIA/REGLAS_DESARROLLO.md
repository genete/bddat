# REGLAS DE DESARROLLO CON IA - BDDAT

**Proyecto:** Sistema de tramitación administrativa de expedientes de autorización de instalaciones de alta tensión  
**Stack:** PostgreSQL + Flask (SQLAlchemy) + Bootstrap 5  
**Repositorio:** https://github.com/genete/bddat  
**Rama principal:** main  
**Documento creado:** 17 de enero de 2026  
**Última actualización:** 22 de enero de 2026  
**Versión:** 2.0

---

## 1. Repositorio Oficial

**Ubicación:** https://github.com/genete/bddat  
**Rama principal:** main  
**Descripción:** Sistema de tramitación administrativa de expedientes de autorización de instalaciones de alta tensión, construido con PostgreSQL, Flask (SQLAlchemy) y Bootstrap 5.

---

## 2. Metodología de Desarrollo

### 2.1 Roles y Responsabilidades (Git)

#### Asistente (IA)

- Preparo los cambios (código, modelos, rutas, templates) de forma clara y descriptiva
- Describo exactamente qué ficheros se tocan y qué hace cada cambio
- Creo las ramas necesarias para el desarrollo (`feature/`, `bugfix/`, etc.)
- Genero los commits en la rama de desarrollo
- **Espero tu aprobación explícita** antes de cada commit
- **Realizo commits directamente en el repositorio remoto** únicamente tras tu comprobación/OK explícito
  - Ejemplo: "OK, adelante con la migración" o "Perfecto, haz el commit"
  - No hago commits "a sorpresa": siempre espero tu revisión previa
- Tras tus pruebas funcionales y tu OK, creo el Pull Request de la rama a `main`
- Tras el merge del PR, genero el changelog correspondiente y lo subo a `docs/CHANGELOG.md` en commit separado
- Mantengo coherencia con documentación existente

#### Usuario (Tú)

- Realizas `git pull` para descargar mis commits y efectúas **pruebas exhaustivas en tu entorno local**
  - Ejecutas `flask run`, pruebas formularios, migraciones, validaciones
  - Verificas que la BD se comporta correctamente
  - Confirmas resultados visualmente
- Generas el archivo `schema.sql` localmente mediante script y lo subes al repositorio manualmente
- Realizas tú los commits cuando el cambio **no puede hacerse desde remoto** o depende de tu máquina:
  - Generación de migraciones locales (cuando hay ajustes específicos)
  - Pruebas que fuerzan cambios en configuración local
  - Verificaciones finales que requieren ejecución real
  - Commits post-prueba con cambios derivados del testing
- Cuando haces commits locales, ejecutas `git push` y confirmas el resultado
- Das el OK final para que yo cree el Pull Request y haga el merge

---

### 2.2 Secuencia de Trabajo Estándar

#### Fase 1: Análisis y Diseño

- Se revisan documentos existentes en la Knowledge Base (DOCX, JSON, TXT)
- **La IA consulta el archivo `schema.sql`** que generas tú localmente mediante script y subes al repo manualmente
- Se consulta la estructura actual de la BD (tablas, campos, relaciones) desde `schema.sql`
- Se identifican cambios/mejoras necesarios
- Se registra claramente en qué consisten

#### Fase 2: Preparación Remota (por IA)

- Creo la rama necesaria para el desarrollo:
  - `feature/descripcion-breve` - nuevas funcionalidades
  - `bugfix/descripcion-breve` - corrección de errores
  - `hotfix/descripcion-breve` - correcciones urgentes en producción
  - `refactor/descripcion-breve` - refactorizaciones sin cambio funcional
  - `docs/descripcion-breve` - solo documentación
- Preparo el código/cambios con explicación detallada
- Descripción clara de archivos afectados y cambios en cada uno
- Genero los commits en la rama de desarrollo
- **Espero tu OK explícito antes de hacer cada commit remoto**
- Una vez apruebes, hago el commit y push en GitHub en la rama correspondiente

#### Fase 3: Pruebas Locales (por Usuario)

- `git pull` para descargar los cambios
- `flask run` y pruebas manuales en tu entorno
- Verificación de BD, migraciones, formularios
- Confirmación de que todo funciona como se esperaba
- Si hay ajustes inevitables, los realizas y haces `git push`

#### Fase 3.1: Pull Request y Changelog (por IA)

- Finalmente, tras las pruebas funcionales y el OK del usuario, creo el Pull Request de esa rama a la rama `main`
- Cuando el desarrollo responde a un issue, se indica en el commit y el changelog
- Tras el merge del PR a `main`, genero el changelog correspondiente
- Actualizo `docs/CHANGELOG.md` con la nueva entrada en **commit separado**
- Formato del changelog: entrada con fecha, PR, issue relacionado, cambios por categoría

#### Fase 4: Actualización de Documentación

- Se procurará que los documentos de referencia (como este) se subirán al repositorio en `docs/fuentesIA/`
- Intentaremos que los documentos directos en las fuentes de conocimiento sean los estrictamente esenciales
- **Los documentos en el repositorio son la fuente de la verdad** para la IA en caso de conflicto con otras fuentes
- Se registran cambios mediante los changelogs en `docs/CHANGELOG.md`:
  - Descripción de lo que cambiamos (hechos)
  - No las intenciones (eso va en documentos de diseño de las fuentes IA)

---

### 2.3 Principios de Trabajo

1. **Documentación primero:** Se diseña en documentos antes de cambiar código
2. **Incrementalidad:** Cambios pequeños, probados, sincronizados
3. **Trazabilidad:** Git es la fuente de verdad del código
4. **Conocimiento compartido:** Las fuentes de conocimiento están siempre al día
5. **Aprobación previa:** No hay commits remotos sin tu OK
6. **Responsabilidad compartida:** Cada rol tiene tareas claras y no solapadas
7. **Repositorio como fuente de verdad:** Documentos en `docs/fuentesIA/` prevalecen sobre otras fuentes

---

## 3. Convenciones de Código y Naming

### 3.1 REGLA GENERAL: snake_case

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

**Incorrecto (no hacer):**

```python
class Expediente(db.Model):
    __tablename__ = 'Expedientes'  # ❌ No
    IdExpediente = db.Column(...)  # ❌ No
    NumeroExpediente = db.Column(...)  # ❌ No
```

#### Variables y Funciones en Python

**Correcto:**

```python
def procesar_expediente(id_expediente):
    numero_expediente = expediente.numero_expediente
    fecha_creacion = datetime.now()
    lista_solicitudes = db.session.query(Solicitud).filter_by(id_expediente=id_expediente).all()
```

**Incorrecto (no hacer):**

```python
def procesarExpediente(IdExpediente):  # ❌ No
    numeroExpediente = expediente.numeroExpediente  # ❌ No
    listaSolicitudes = ...  # ❌ No
```

#### Variables JavaScript/Bootstrap

```javascript
// Correcto
const id_expediente = document.getElementById('expediente-id').value;
const fecha_presentacion = new Date(expediente.fecha_presentacion);
const numero_tramites = expedientes.length;
const formulario_datos = { ... };

// Incorrecto (no hacer)
const idExpediente = ...  // ❌ No
const fechaPresentacion = ...  // ❌ No
const numeroTramites = ...  // ❌ No
```

#### Rutas Flask

**Correcto:**

```python
@app.route('/expedientes/<int:id_expediente>')
def ver_expediente(id_expediente):
    return render_template('expediente_detalle.html', id_expediente=id_expediente)

@app.route('/solicitudes/<int:id_solicitud>/tramites')
def listar_tramites(id_solicitud):
    pass
```

**Incorrecto (no hacer):**

```python
@app.route('/expedientes/<int:IdExpediente>')  # ❌ No
def verExpediente(IdExpediente):  # ❌ No
    pass
```

#### Templates HTML/Jinja2

**Correcto:**

```html
{{ expediente.numero_expediente }}
<p>Fecha: {{ expediente.fecha_presentacion|strftime('%d/%m/%Y') }}</p>
<button id="btn_procesar" class="btn btn-primary">Procesar</button>
```

**Incorrecto (no hacer):**

```html
{{ expediente.NumeroExpediente }}  <!-- ❌ No -->
<input id="IdExpediente" ...>  <!-- ❌ No -->
```

#### Nombres de Archivos

**Correcto:**

```
expediente_modelo.py
solicitud_routes.py
expediente_detalle.html
funciones_validacion.js
tablas_maestras_config.json
```

**Incorrecto (no hacer):**

```
ExpedienteModelo.py  # ❌ No
SolicitudRoutes.py  # ❌ No
expediente-detalle.html  # Evitar guiones (excepto en id HTML)
FuncionesValidacion.js  # ❌ No
```

---

### 3.2 Excepciones Permitidas

Solo en estos casos se puede usar otro patrón:

1. **Nombres de clases de modelos:** CamelCase (ej: `class Expediente`, `class Solicitud`)
2. **Identificadores de Bootstrap/Librerías externas:** Si la librería lo exige
3. **Valores de configuración predefinidos:** Si la especificación así lo requiere
4. **Nombres de terceros:** Información del dominio (no se cambia)

---

## 4. Estructura de Carpetas del Repositorio

```
bddat/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── expediente.py
│   │   ├── solicitud.py
│   │   └── documento.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── expedientes.py
│   │   ├── solicitudes.py
│   │   └── documentos.py
│   ├── templates/
│   │   ├── expediente_detalle.html
│   │   ├── expediente_lista.html
│   │   └── solicitud_form.html
│   └── static/
│       ├── css/
│       │   └── estilo.css
│       └── js/
│           └── funciones_expediente.js
├── migrations/
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── *.py
├── docs/
│   ├── CHANGELOG.md
│   └── fuentesIA/
│       ├── REGLAS_DESARROLLO.md
│       └── [otros documentos de referencia]
├── tests/
├── config.py
├── run.py
├── schema.sql
└── requirements.txt
```

---

## 5. Workflow de Commits

### 5.1 Commits que Hace la IA

**Ejemplos de cambios que puedo subir directamente (previa tu aprobación):**

- Nuevos modelos SQLAlchemy completos
- Nuevas rutas Flask sin dependencias complejas
- Templates HTML/Jinja2 nuevos o modificados
- Cambios en CSS/JavaScript
- Actualización de requirements.txt
- Cambios de configuración
- Cambios en .gitignore u otros archivos de configuración
- **Actualización de `docs/CHANGELOG.md`** tras merge de PR

**Proceso:**

1. Creo la rama de desarrollo correspondiente
2. Preparo el cambio con descripción clara
3. Te muestro exactamente qué archivos se tocan
4. **Espero tu aprobación explícita para cada commit**
5. Una vez apruebes, hago: `git add [archivos]` → `git commit -m "..."` → `git push`
6. Tras tus pruebas y tu OK final, creo el Pull Request a `main`
7. Tras el merge, actualizo el changelog en commit separado

---

### 5.2 Commits que Hace el Usuario

**Ejemplos de cambios que haces localmente:**

- Migraciones locales (`flask db migrate`)
- Pruebas de cambios que requieren `flask run`
- Ajustes post-testing
- Cambios en .env o configuración local
- Scripts de inicialización local
- Verificación y fixes derivados de testing
- **Generación y subida de `schema.sql`** mediante script local

**Proceso:**

1. Haces `git pull` para traer mis cambios
2. Ejecutas pruebas en local
3. Si necesitas cambios, los haces y ejecutas `git add` → `git commit` → `git push`
4. Confirmas que el push fue exitoso

---

### 5.3 Mensajes de Commit

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
- `[CHANGELOG]` - Actualización de changelog
- `[MERGE]` - Merge de pull requests

**Ejemplos:**

```
[BD] Añadir tabla expedientes_auditoría
[MODELO] Crear modelo Solicitud con validaciones
[RUTA] Implementar endpoint GET /expedientes/<id>
[TEMPLATE] Mejorar formulario solicitud con validación cliente
[STYLE] Ajustar colores botones Bootstrap
[MIGA] Actualizar estructura de migraciones
[TEST] Pruebas locales de flujo expediente
[DOCS] Actualizar documentación tablas maestras
[CHANGELOG] Añadir entrada PR #18 fix email duplicado
[MERGE] Merge feature/nueva-funcionalidad a main
```

---

## 6. Checklist Antes de Cambios (IA) y Antes de Commits (Usuario)

### 6.1 Verificación IA (Antes de Solicitarte OK)

- [ ] Rama de desarrollo creada con nombre apropiado
- [ ] Cambio está documentado y explicado
- [ ] Afecta solo a archivos necesarios
- [ ] Nombres en snake_case (excepto clases de modelos en CamelCase)
- [ ] Código sigue convenciones del proyecto
- [ ] No hay archivos innecesarios
- [ ] Mensaje de commit es descriptivo con categoría correcta entre `[]`
- [ ] He consultado `schema.sql` para cambios de BD

---

### 6.2 Verificación Usuario (Antes de git push)

- [ ] `git pull` completado correctamente
- [ ] `flask run` funciona sin errores
- [ ] Base de datos responde correctamente
- [ ] Formularios se cargan y funcionan
- [ ] Migraciones ejecutadas: `flask db upgrade`
- [ ] Carpeta `migrations/` incluida en el commit
- [ ] No hay archivos `.pyc`, `__pycache__`, `.env`
- [ ] Todos los nombres en snake_case (excepto clases)
- [ ] Mensaje de commit es descriptivo con categoría entre `[]`

---

## 7. Cambios Documentales y Changelogs

### 7.1 Changelogs

Los cambios documentales se realizan mediante los changelogs en `docs/CHANGELOG.md`:

- Se describen **los cambios realizados** (hechos), no las intenciones
- Se actualizan tras cada merge de PR a `main`
- Se hace en commit separado con categoría `[CHANGELOG]`
- Formato: fecha, PR, issue relacionado, cambios por categoría (BD, Modelos, Rutas, Templates, etc.)

**Ubicación:** `docs/CHANGELOG.md` (archivo único acumulativo)

**Estructura:**
- Índice con enlaces a cada entrada
- Entradas en orden cronológico inverso (más reciente arriba)
- Cada entrada con nivel de título `##`
- Subsecciones por tipo de cambio con nivel `###`

---

### 7.2 Documentación de Diseño

Cuando se realiza un cambio importante en el código que afecte a:

- Estructura de tablas
- Lógica de negocio
- Flujos administrativos
- Nuevas entidades o relaciones

**Procedimiento:**

1. Se actualiza el documento correspondiente en `docs/fuentesIA/`
2. Se especifica claramente:
   - Qué cambió exactamente
   - Por qué cambió
   - Fecha del cambio
   - Versión afectada
   - Impacto en otras tablas/lógica

**Nota:** Los documentos en el repositorio (`docs/fuentesIA/`) son la fuente de verdad para la IA en caso de conflicto con otras fuentes de conocimiento.

---

## 8. Sincronización y Comunicación

### 8.1 Estado del Repositorio

**Después de cada sesión:**

**Tú ejecutas (para confirmar estado limpio):**

```bash
git status
git log --oneline -5
```

**Resultado esperado:** `nothing to commit, working tree clean`

---

### 8.2 Resolución de Conflictos

Si hay conflictos en `git pull`:

1. Avísame inmediatamente con el detalle del conflicto
2. Describimos juntos qué cambio prevalece
3. Tú resuelves localmente (si es código que ejecutaste)
4. O yo preparo la resolución (si es código que subí)

---

### 8.3 Ramas y Pull Requests

**Rama principal:** `main`

**Ramas de desarrollo:** Se crean según necesidad con prefijos:
- `feature/` - nuevas funcionalidades
- `bugfix/` - corrección de errores
- `hotfix/` - correcciones urgentes
- `refactor/` - refactorizaciones
- `docs/` - solo documentación

**Workflow:**
1. IA crea rama de desarrollo
2. IA hace commits en la rama (con aprobación usuario)
3. Usuario prueba localmente
4. Usuario da OK final
5. IA crea Pull Request a `main`
6. IA hace merge del PR
7. IA actualiza changelog en commit separado

---

## 9. Herramientas y Comandos Esenciales

### 9.1 Git (Usuario)

**Ver estado:**
```bash
git status
git log --oneline -10
```

**Traer cambios remotos:**
```bash
git pull origin main
```

**Crear/subir cambios locales:**
```bash
git add [archivo]
git commit -m "[CATEGORÍA] Descripción"
git push origin main
```

**Ver diferencias:**
```bash
git diff
git diff --staged
```

---

### 9.2 Flask y BD (Usuario)

**Activar entorno virtual:**
```bash
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

**Aplicar migraciones:**
```bash
flask db upgrade
```

**Crear migración:**
```bash
flask db migrate -m "Descripción del cambio"
```

**Ejecutar servidor:**
```bash
flask run
```

---

### 9.3 Ver Cambios en Remoto (IA)

**Verificar que el push fue exitoso:**
```bash
git log --oneline -5
git status
```

---

## 10. Resumen de Responsabilidades

| Actividad | IA | Usuario |
|-----------|-------|------|
| Preparar cambios de código | ✅ | |
| Crear ramas de desarrollo | ✅ | |
| Describir cambios claramente | ✅ | |
| Consultar schema.sql para cambios BD | ✅ | |
| Esperar aprobación previa | ✅ | |
| Hacer commits remotos (tras OK) | ✅ | |
| Crear Pull Requests | ✅ | |
| Hacer merge de PRs | ✅ | |
| Actualizar changelogs | ✅ | |
| Actualizar documentación en docs/fuentesIA/ | ✅ | |
| Hacer git pull | | ✅ |
| Generar schema.sql y subirlo | | ✅ |
| Probar en local (flask run) | | ✅ |
| Hacer migraciones locales | | ✅ |
| Hacer commits de testing/ajustes | | ✅ |
| Hacer git push (cambios locales) | | ✅ |
| Dar OK para commits y PRs | | ✅ |

---

## 11. Contacto y Sincronización Final

**Repositorio remoto:** https://github.com/genete/bddat  
**Rama de trabajo:** main  
**Sincronización:** Después de cada sesión de desarrollo  
**Documentación:** Actualizada en `docs/fuentesIA/` y `docs/CHANGELOG.md`  
**Aprobación de cambios:** Explícita y previa a commits remotos  

---

**Documento creado:** 17 de enero de 2026, 21:24 CET  
**Última actualización:** 22 de enero de 2026, 11:40 CET  
**Versión:** 2.0  
**Referencia:** Repositorio oficial genete/bddat en GitHub
