<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Guía Completa: Configurar BDDAT en un PC Nuevo

## 1. Instalación de Software Base

### PostgreSQL

1. Descargar e instalar PostgreSQL desde [postgresql.org](https://www.postgresql.org/download/)
2. Durante la instalación, configurar:
    - Usuario: `postgres`
    - Contraseña: (la que elijas)
    - Puerto: `5432` (por defecto)
3. Anotar las credenciales para usarlas después

### Python

1. Descargar Python 3.9+ desde [python.org](https://www.python.org/downloads/)
2. **Importante**: Marcar "Add Python to PATH" durante la instalación
3. Verificar instalación:

```bash
python --version
pip --version
```


### Git

- **Opción A - Git CLI**: Descargar desde [git-scm.com](https://git-scm.com/)
- **Opción B - SourceTree**: Descargar desde [sourcetreeapp.com](https://www.sourcetreeapp.com/)

***

## 2. Clonar el Repositorio

```bash
# Con Git CLI
git clone https://github.com/genete/bddat.git
cd bddat

# Cambiar a rama develop
git checkout develop
```

O con SourceTree: clonar repositorio y cambiar a rama `develop`.

***

## 3. Configurar PostgreSQL

### Paso 1: Crear usuario PostgreSQL para la aplicación

Conectar a PostgreSQL como superusuario `postgres`:

```bash
psql -U postgres
```

Dentro de psql, ejecutar:

```sql
-- Crear usuario específico para la aplicación
CREATE USER bddat_admin WITH PASSWORD 'tu_password_seguro_aqui';

-- Dar privilegios de crear bases de datos
ALTER USER bddat_admin CREATEDB;

-- Salir de psql
\q
```

**Anotar estas credenciales** para usarlas en el archivo `.env`.

### Paso 2: Crear base de datos como el usuario bddat_admin

```bash
# Conectar como bddat_admin
psql -U bddat_admin -d postgres
```

```sql
-- Crear base de datos
CREATE DATABASE bddat;

-- Salir
\q
```

O alternativamente desde la línea de comandos:

```bash
createdb -U bddat_admin bddat
```


### Paso 3: Verificar que todo está correcto

```bash
# Conectar a la BD bddat como bddat_admin
psql -U bddat_admin -d bddat
```

```sql
-- Deberías estar conectado sin errores
\l  -- Lista bases de datos
\q  -- Salir
```


***

## 4. Configurar Entorno Python

### Crear entorno virtual

```bash
# En la carpeta raíz del proyecto bddat
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate
```

Deberías ver `(venv)` al inicio del prompt de tu terminal.

### Instalar dependencias

```bash
pip install -r requirements.txt
```

Esto instalará Flask, SQLAlchemy, Alembic, psycopg2, Flask-Login, etc.

***

## 5. Configurar Variables de Entorno

Crear archivo `.env` en la raíz del proyecto (mismo nivel que `run.py`):

```env
# Conexión a PostgreSQL usando el usuario bddat_admin
DATABASE_URL=postgresql://bddat_admin:tu_password_seguro_aqui@localhost:5432/bddat

# Clave secreta Flask (generar una aleatoria)
SECRET_KEY=genera-una-clave-secreta-segura-aqui

# Entorno de desarrollo
FLASK_ENV=development
FLASK_DEBUG=True
```

**Importante**: Usar las credenciales del usuario `bddat_admin` creado en el paso 3.

Para generar una clave secreta segura:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```


***

## 6. Verificar Configuración de Flask

```bash
flask --version
```

Debería mostrar Flask y Python instalados.

***

## 7. Crear TODAS las Tablas con Alembic

```bash
# Aplicar migraciones
flask db upgrade
```

Esto crea automáticamente:

- **Esquema `estructura`** con tablas: `municipios`, `tipos_ia`, `tipos_fases`, `tipos_tramites`, `tipos_tareas`, `tipos_solicitudes`, `tipos_expedientes`, `tipos_resultados_fases`
- **Esquema `public`** con tablas: `usuarios`, `roles`, `usuarios_roles`, `expedientes`, `proyectos`, `municipios_proyecto`, `solicitudes`, `solicitudes_tipos`, `documentos`, `documentos_proyecto`, `fases`, `tramites`, `tareas`
- Todas las relaciones, índices y constraints

**Las tablas están creadas pero VACÍAS** (sin datos).

***

## 8. Cargar Datos Maestros

### Cargar datos estructurales

```bash
psql -U bddat_admin -d bddat -f datos_estructurales.sql
```

O desde pgAdmin:

1. Conectar con usuario `bddat_admin`
2. Clic derecho en base de datos `bddat` → Query Tool
3. Abrir archivo `datos_estructurales.sql`
4. Ejecutar (botón play o F5)

Esto inserta:

- 773 municipios de Andalucía con códigos INE
- Provincias
- Tipos de instalaciones AT
- Tipos de instrumentos ambientales (AAI, AAU, AAUS, CA, EXENTO)
- Tipos de fases, trámites, tareas, solicitudes


### Cargar roles del sistema

```bash
psql -U bddat_admin -d bddat -f datos_roles.sql
```

Esto inserta los 4 roles:

- ADMIN (Administrador del sistema)
- SUPERVISOR (Supervisor de tramitación)
- TRAMITADOR (Tramitador de expedientes)
- ADMINISTRATIVO (Personal administrativo)


### Verificar que los datos se cargaron

```sql
-- Conectar a la BD
psql -U bddat_admin -d bddat

-- Verificar municipios
SELECT COUNT(*) FROM estructura.municipios;  -- Debe devolver 773

-- Verificar roles
SELECT * FROM public.roles;  -- Debe mostrar 4 roles

-- Salir
\q
```


***

## 9. Crear Usuario Aplicación con Rol ADMIN

### Opción A: Usar script preparado (recomendado)

```bash
psql -U bddat_admin -d bddat -f crear_usuario_admin.sql
```

Este script crea automáticamente un usuario con rol ADMIN asignado.

**Después saltar al paso 10.**

***

### Opción B: Crear manualmente paso a paso

#### Paso 1: Generar password hash

```bash
flask shell
```

Dentro de Flask shell:

```python
from werkzeug.security import generate_password_hash
password_hash = generate_password_hash('tu_password_aqui')
print(password_hash)
exit()
```

Copiar el hash generado (comienza con `$2b$12$...` o similar).

***

#### Paso 2: Crear usuario en la base de datos

```bash
# Conectar a PostgreSQL
psql -U bddat_admin -d bddat
```

```sql
-- Crear usuario (ajustar datos personales)
INSERT INTO public.usuarios (siglas, nombre, apellido1, apellido2, email, activo, password_hash)
VALUES ('ADM', 'Admin', 'Sistema', NULL, 'admin@bddat.com', true, 'pegar_hash_completo_aqui');

-- Verificar que se creó
SELECT id, siglas, nombre, email FROM public.usuarios WHERE email = 'admin@bddat.com';
-- Anotar el ID que devuelve (normalmente será 1)
```


***

#### Paso 3: **CRÍTICO** - Asignar rol ADMIN al usuario

```sql
-- Asignar rol ADMIN (ajustar usuario_id si no es 1)
INSERT INTO public.usuarios_roles (usuario_id, rol_id)
VALUES (
    (SELECT id FROM public.usuarios WHERE email = 'admin@bddat.com'),
    (SELECT id FROM public.roles WHERE nombre = 'ADMIN')
);
```


***

#### Paso 4: **VERIFICACIÓN OBLIGATORIA** - Confirmar que el rol se asignó

```sql
-- VERIFICACIÓN CRÍTICA
SELECT 
    u.id,
    u.siglas,
    u.nombre,
    u.email,
    r.nombre as rol
FROM public.usuarios u
LEFT JOIN public.usuarios_roles ur ON u.id = ur.usuario_id
LEFT JOIN public.roles r ON ur.rol_id = r.id
WHERE u.email = 'admin@bddat.com';
```

**Resultado esperado**:

```
 id | siglas | nombre |      email       |  rol  
----+--------+--------+------------------+-------
  1 | ADM    | Admin  | admin@bddat.com  | ADMIN
```

**⚠️ CRÍTICO**: La columna `rol` NO debe ser NULL.

Si aparece NULL:

```
 id | siglas | nombre |      email       | rol  
----+--------+--------+------------------+------
  1 | ADM    | Admin  | admin@bddat.com  | NULL   ← PROBLEMA
```

**Entonces** ejecutar nuevamente el INSERT del Paso 3.

***

#### Salir de psql

```sql
\q
```


***

## 10. Levantar la Aplicación Flask

```bash
# Asegurarse de estar en el entorno virtual activado (debe verse "(venv)")
python run.py

# O alternativamente:
flask run
```

Deberías ver en la terminal:

```
 * Running on http://127.0.0.1:5000
 * Running on http://localhost:5000
```

Si hay errores de conexión a BD, verificar:

- PostgreSQL está corriendo
- Usuario `bddat_admin` tiene permisos
- DATABASE_URL en `.env` es correcto (usuario, contraseña, puerto)

***

## 11. Acceder desde el Navegador

1. Abrir navegador
2. Ir a: **`http://localhost:5000`**
3. Hacer login con las credenciales creadas:
    - Email: `admin@bddat.com` (o el que hayas puesto)
    - Password: el password original (no el hash)
4. **Verificar que aparecen las fichas del dashboard**:
    - Tramitación (Mis expedientes, Listado expedientes, Nuevo expediente, etc.)
    - Configuración (Tablas maestras, Gestión estructura)
    - Datos Legacy
    - Sistema

**Si las fichas NO aparecen** → Ir a la sección de problemas comunes.

***

## 12. Verificación y Solución de Problemas Comunes

### Problema 1: Dashboard vacío (sin fichas) ⚠️

**Síntoma**: El menú se ve bien, pero la zona "Bloques del Dashboard" está vacía. Solo aparece "Bienvenido/a, Nombre Usuario".

**Causa**: El usuario no tiene roles asignados en la tabla `usuarios_roles`.

**Diagnóstico**:

```bash
psql -U bddat_admin -d bddat
```

```sql
SELECT u.nombre, u.email, r.nombre as rol
FROM public.usuarios u
LEFT JOIN public.usuarios_roles ur ON u.id = ur.usuario_id
LEFT JOIN public.roles r ON ur.rol_id = r.id
WHERE u.email = 'admin@bddat.com';
```

**Si `rol` es NULL**:

```sql
-- Asignar rol ADMIN
INSERT INTO public.usuarios_roles (usuario_id, rol_id)
VALUES (
    (SELECT id FROM public.usuarios WHERE email = 'admin@bddat.com'),
    (SELECT id FROM public.roles WHERE nombre = 'ADMIN')
);

-- Verificar nuevamente
SELECT u.nombre, r.nombre as rol
FROM public.usuarios u
LEFT JOIN public.usuarios_roles ur ON u.id = ur.usuario_id
LEFT JOIN public.roles r ON ur.rol_id = r.id
WHERE u.email = 'admin@bddat.com';
```

**Después de insertar el rol:**

1. **Cerrar sesión** en la aplicación (menú usuario → Cerrar Sesión)
2. **Volver a iniciar sesión**
3. Flask recargará los roles desde la BD
4. El dashboard debería mostrar las fichas

***

### Problema 2: Error de autenticación PostgreSQL

**Síntoma**:

```
FATAL: password authentication failed for user "bddat_admin"
```

**Solución**:

1. Verificar password en archivo `.env`
2. Resetear password del usuario:
```bash
psql -U postgres
```

```sql
ALTER USER bddat_admin WITH PASSWORD 'nuevo_password';
\q
```

3. Actualizar `.env` con el nuevo password
4. Reiniciar Flask

***

### Problema 3: Usuario bddat_admin no tiene permisos

**Síntoma**:

```
ERROR: permission denied for schema estructura
```

**Solución**:

```bash
psql -U postgres -d bddat
```

```sql
-- Dar permisos completos al usuario bddat_admin
GRANT ALL PRIVILEGES ON DATABASE bddat TO bddat_admin;
GRANT ALL PRIVILEGES ON SCHEMA public TO bddat_admin;
GRANT ALL PRIVILEGES ON SCHEMA estructura TO bddat_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO bddat_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA estructura TO bddat_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO bddat_admin;

\q
```


***

### Problema 4: Faltan datos maestros

**Diagnóstico**:

```bash
psql -U bddat_admin -d bddat
```

```sql
SELECT COUNT(*) FROM estructura.municipios;  -- Debe ser 773
SELECT COUNT(*) FROM estructura.tipos_ia;    -- Debe ser 5
SELECT COUNT(*) FROM public.roles;           -- Debe ser 4
```

**Solución**: Si los conteos son 0 o menores:

```bash
psql -U bddat_admin -d bddat -f datos_estructurales.sql
psql -U bddat_admin -d bddat -f datos_roles.sql
```


***

## 13. Resumen Completo del Flujo

```
1. Instalar PostgreSQL + Python + Git
2. Crear usuario PostgreSQL: CREATE USER bddat_admin WITH PASSWORD '...';
3. Dar privilegios: ALTER USER bddat_admin CREATEDB;
4. Crear BD: CREATE DATABASE bddat; (como bddat_admin)
5. Clonar repositorio: git clone + git checkout develop
6. Crear entorno virtual: python -m venv venv
7. Activar entorno: venv\Scripts\activate
8. Instalar dependencias: pip install -r requirements.txt
9. Crear .env con DATABASE_URL (usuario bddat_admin)
10. ✅ Aplicar migraciones: flask db upgrade
11. ✅ Cargar datos: psql -U bddat_admin -f datos_estructurales.sql
12. ✅ Cargar roles: psql -U bddat_admin -f datos_roles.sql
13. Generar password hash: flask shell → generate_password_hash()
14. Crear usuario app: INSERT INTO usuarios
15. ⚠️ Asignar rol: INSERT INTO usuarios_roles
16. ✅ Verificar rol: SELECT ... LEFT JOIN (no debe ser NULL)
17. Levantar Flask: python run.py
18. Abrir http://localhost:5000
19. Login con credenciales
20. ✅ Verificar fichas del dashboard
```


***

## 14. Checklist Final

- [ ] PostgreSQL instalado y corriendo
- [ ] Usuario PostgreSQL `bddat_admin` creado con password
- [ ] Base de datos `bddat` creada
- [ ] Python 3.9+ instalado
- [ ] Repositorio clonado (rama develop)
- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas
- [ ] Archivo `.env` con `DATABASE_URL` correcto (usuario bddat_admin)
- [ ] Migraciones aplicadas: `flask db upgrade`
- [ ] `datos_estructurales.sql` cargado (773 municipios)
- [ ] `datos_roles.sql` cargado (4 roles)
- [ ] Usuario aplicación creado con password hash
- [ ] **Rol ADMIN asignado en `usuarios_roles`**
- [ ] **Verificado con SELECT que rol = 'ADMIN' (no NULL)**
- [ ] Flask levanta sin errores
- [ ] Login funciona
- [ ] **Dashboard muestra fichas**

***

## 15. Tiempo Estimado

**Total**: 30-45 minutos

***

¡Con esta guía completa y corregida deberías tener todo funcionando! La clave es crear el usuario PostgreSQL `bddat_admin` primero y usarlo en toda la configuración.
<span style="display:none">[^1]</span>

<div align="center">⁂</div>

[^1]: ACCESO_RAPIDO_PROYECTO.md

