# REGLAS DE DESARROLLO CON IA - BDDAT

**Proyecto:** Sistema de tramitación administrativa de expedientes de autorización de instalaciones de alta tensión  
**Stack:** PostgreSQL + Flask (SQLAlchemy) + Bootstrap 5  
**Repositorio:** https://github.com/genete/bddat  
**Ramas principales:** `main` (producción) + `develop` (integración)  
**Documento creado:** 17 de enero de 2026  
**Última actualización:** 27 de enero de 2026  
**Versión:** 3.1

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
- **Actualizo `docs/CHANGELOG.md` en la misma rama de desarrollo** antes del PR
- Hago merge del PR a `develop` **preservando historial completo de commits**
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
- **Actualizo `docs/CHANGELOG.md` en la misma rama**

##### Fase 3: Pruebas Locales (por Usuario)

- `git checkout nombre-rama`
- `git pull origin nombre-rama`
- `flask run` y pruebas funcionales
- Si hay ajustes, los haces y ejecutas `git push origin nombre-rama`

##### Fase 4: Pull Request y Merge (por IA)

- Tras tu OK final, creo PR: `nombre-rama` → `develop`
- Referencio el issue si aplica: "Closes #XX"
- Hago merge del PR **preservando todos los commits** (changelog incluido)
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

[... resto del documento sin cambios hasta la sección 12.3 ...]

### 12.3 Configuración Recomendada en GitHub

**Una sola vez, configurar:**

1. **Settings → Branches:**
   - Default branch: `develop`
   
2. **Settings → General → Pull Requests:**
   - ☑️ Automatically delete head branches
   - ☐ Allow squash merging (**DESMARCAR** - queremos preservar historial completo)
   - ☑️ Allow merge commits (este es el método que usamos)

**Resultado:**
- PRs se crean por defecto hacia `develop`
- Ramas se borran automáticamente tras merge
- **Todos los commits individuales se preservan** en el historial

---

[... resto del contenido idéntico ...]

**Documento creado:** 17 de enero de 2026, 21:24 CET  
**Última actualización:** 27 de enero de 2026, 20:05 CET  
**Versión:** 3.1  
**Referencia:** Repositorio oficial genete/bddat en GitHub