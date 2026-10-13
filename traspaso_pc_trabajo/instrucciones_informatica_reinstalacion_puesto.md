# Reinstalación del puesto de desarrollo BDDAT — instrucciones para Informática

Puesto: PC de trabajo con el disco del sistema (C:) averiado. El disco de datos **D:** está bien y
contiene el proyecto en `D:\BDDAT`. Se pide dejar el PC con el software de abajo, sin tocar D:.

## 0. Antes de empezar (importante)

1. **No formatear, reparticionar ni reasignar letra a D:.** Debe seguir siendo `D:` y la carpeta
   `D:\BDDAT` debe quedar tal cual. Rutas fijas del proyecto dependen de ello (`D:/BDDAT/...`).
2. Si al instalar Windows el disco de datos cambia de letra, devolverlo a `D:`
   (Administración de discos → clic derecho en la partición → «Cambiar la letra de unidad»).
3. En D:\BDDAT hay carpetas que **no están en el repositorio** (solo existen ahí): `.env`,
   `docs_prueba\`, `almacen_dev\`, `manifiestos_dev\`. Si es posible, copiarlas a otro soporte antes.
4. **La carpeta de datos de PostgreSQL (la base de datos de desarrollo) está en D:** (carpeta con un
   fichero `PG_VERSION` dentro). **Hay que conservarla intacta**: no borrarla, no reinicializarla y no
   dejar que el instalador de PostgreSQL la use como carpeta nueva. Antes de nada, hacer una copia de
   la carpeta entera (con PostgreSQL parado, o con el equipo recién arrancado sin servicio) a otro soporte.
   El contenido de `PG_VERSION` (por ejemplo `18`) es la **versión mayor que hay que instalar** (§2).

## 1. Software a instalar

| Programa | Versión | Notas |
|---|---|---|
| **Python** | **3.14.x (64 bits)**, instalador clásico de python.org («Windows installer (64-bit)») | **Marcar «Add python.exe to PATH»** (y «py launcher»). Debe ser 3.14: el código usa `uuid.uuid7`, que no existe en 3.13. Instalación «solo para mi usuario» es suficiente y deja Python en el PATH **del usuario**. |
| **PostgreSQL** | **La misma versión mayor que indique `PG_VERSION`** de la carpeta de datos de D: (previsiblemente 18; instalador EDB). Una versión distinta **no puede abrir esa carpeta**. | Componentes: *PostgreSQL Server* y *Command Line Tools*; pgAdmin opcional; omitir Stack Builder. Puerto **5432**. Servicio de arranque automático. **Solo escucha en localhost** (valor por defecto): no abrir el firewall. Codificación: ver §2. |
| **Git para Windows** | última | Incluye *Git Bash*; opción «Git from the command line and also from 3rd-party software». Se usa `bash` en todo el flujo del proyecto. |
| **Node.js** | **22 LTS** (o superior LTS) | Con `npm` en el PATH. Para compilar los bundles React y para el MCP de Playwright. |
| **LibreOffice** | última estable, con *Writer* | Ruta por defecto `C:\Program Files\LibreOffice\program\soffice.com` (los tests y scripts la esperan ahí). |
| **Google Chrome** (o Edge) | última | Lo usa el MCP de Playwright para verificar la interfaz. |
| **Claude Code** | última | Instalación de usuario, sin administrador. |

PATH **del usuario** (sin necesidad de administrador):

- Python: lo añade el instalador.
- PostgreSQL: añadir `C:\Program Files\PostgreSQL\18\bin` (para `psql`, `pg_dump`, `pg_restore`).
- Git y Node: los añaden sus instaladores.

## 2. PostgreSQL: detalles de la instalación

La base de datos **ya existe** en D: con sus roles, contraseñas y catálogo. No hay que crear nada: hay
que reinstalar el programa y apuntarlo a esa carpeta.

1. Instalar PostgreSQL (misma versión mayor, §1) con una carpeta de datos **nueva y vacía** de
   prueba (la que proponga el instalador). No elegir como carpeta de datos la de D:.
2. Parar el servicio y **apuntarlo a la carpeta de D:**. Con el servicio parado, desde un terminal
   de administrador:
   ```
   "C:\Program Files\PostgreSQL\<N>\bin\pg_ctl.exe" unregister -N postgresql-x64-<N>
   "C:\Program Files\PostgreSQL\<N>\bin\pg_ctl.exe" register -N postgresql-x64-<N> -D "D:\<ruta>\data" -S auto
   ```
   (`<N>` = versión mayor; el nombre del servicio puede variar: comprobarlo en `services.msc`).
   Dar permiso de lectura/escritura sobre la carpeta de D: a la cuenta del servicio (por defecto
   `NT AUTHORITY\NetworkService`).
3. Arrancar el servicio. Si no arranca, el motivo está en `D:\<ruta>\data\log\` (o en el visor de
   eventos). Un cierre brusco del disco se recupera solo al arrancar.
4. **La contraseña de `postgres` en esa base es la de siempre**, no una nueva: el instalador no la
   cambia porque no ha inicializado nada. La conservo yo. Si se hubiera perdido, se puede restablecer
   poniendo `trust` temporalmente en `pg_hba.conf` para `127.0.0.1`.
5. **Red:** `listen_addresses = 'localhost'` y puerto 5432 (lo que traiga la carpeta; no hace falta
   abrir el firewall).
6. Si el arranque con la carpeta de D: diera problemas insalvables, **parar y avisarme antes de
   reinicializar nada**: en ese caso reconstruyo la base desde las migraciones.

## 3. Acceso a Internet / proxy

Desde este PC hay que poder llegar a (por proxy si procede): `github.com`, `pypi.org`,
`files.pythonhosted.org`, `registry.npmjs.org`, `claude.ai` y `api.anthropic.com`. Si hace falta
configurar el proxy para `pip`, `npm` y `git`, indicarme los valores.

## 4. Opcional (mejora la velocidad)

- Excluir del análisis en tiempo real del antivirus: `D:\BDDAT\venv`, `D:\BDDAT\react-src\node_modules`
  y la carpeta de datos de PostgreSQL.
- Rutas largas: `git config --system core.longpaths true` (y `LongPathsEnabled=1` en el registro).
- PowerShell: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (solo si se activan entornos
  virtuales desde PowerShell; desde Git Bash no hace falta).

## 5. Comprobación de Informática (en un terminal nuevo, sin administrador)

```
python --version          -> Python 3.14.x
where python              -> la ruta del usuario va la primera
git --version
node --version            -> v22.x o superior
npm --version
psql --version            -> psql (PostgreSQL) 18.x
pg_dump --version
"C:\Program Files\LibreOffice\program\soffice.com" --version
```

Y comprobar que `D:\BDDAT` abre y contiene `run.py`, `app\`, `migrations\`.

---

# Lo que hago yo después (referencia propia, no es para Informática)

Con la contraseña de `postgres`, desde Git Bash en `/d/BDDAT`:

0. **Primero, comprobar la base recuperada** (`psql -U postgres -h localhost`): `\du` (deben estar
   `bddat_admin` y `claude_desktop`), `\l` (deben estar `bddat` y `bddat_test`) y
   `SELECT count(*) FROM expedientes;`. Después `pg_dump -U postgres -Fc bddat > D:\BDDAT\bddat_recuperada.dump`
   como copia de seguridad inmediata. Si todo está, **saltar los pasos 1, 4 y 6** (solo `flask db upgrade`
   si hubiera migraciones pendientes: `flask db current`). Si faltara algo, seguir los pasos 1 a 6.
1. **Roles y base** (solo si la base no se recuperó; `psql -U postgres -h localhost`):
   ```sql
   CREATE ROLE bddat_admin LOGIN PASSWORD '<clave>' CREATEDB;
   CREATE ROLE claude_desktop NOLOGIN;
   CREATE DATABASE bddat OWNER bddat_admin ENCODING 'UTF8' TEMPLATE template0;
   ```
   - `CREATEDB` hace falta porque `preparar_bd_test.py --recrear` borra y crea `bddat_test`.
   - `claude_desktop` debe existir **antes** de las migraciones: 32 de ellas hacen `GRANT … TO claude_desktop`.
   - Si `CREATE DATABASE` se queja de la configuración regional, añadir `LC_COLLATE` y `LC_CTYPE`
     iguales a los del clúster. La suite pasa en la nube con `C.UTF-8`, así que el código no depende
     del orden alfabético concreto.
   - *Interpretación:* en el PC, `claude_desktop` era el usuario del MCP de PostgreSQL (solo lectura).
     Si se quiere reponer: `ALTER ROLE claude_desktop LOGIN PASSWORD '…'`.
2. **Entorno virtual nuevo.** El `venv` de D: apunta al Python antiguo (que estaba en C:), así que
   no sirve: `rm -rf venv && python -m venv venv && venv/Scripts/python.exe -m pip install -r requirements.txt`.
3. **`.env`:** revisar contraseñas de `DATABASE_URL` y `TEST_DATABASE_URL`, y que las rutas
   `D:/BDDAT/...` sigan siendo válidas. Si LibreOffice quedó en otra ruta, fijar `SOFFICE`.
4. **Esquema y catálogos:** `venv/Scripts/python.exe -m flask db upgrade`. Las 193 migraciones
   reconstruyen el esquema y el catálogo (91 de ellas insertan datos). Los datos de operación
   (expedientes, notificaciones…) se pierden con la base, y por vuestras reglas no condicionan nada.
5. **Almacén y manifiestos:** comprobar que `D:\BDDAT\almacen_dev\ALMACEN.txt` y
   `D:\BDDAT\manifiestos_dev\MANIFIESTOS.txt` siguen ahí. Si están, no hay que inicializar nada.
6. **Primer usuario:** hay `scripts/crear_usuario_admin.sql` (necesita un hash real de contraseña).
   Verificar con Claude que sigue siendo el camino vigente antes de usarlo.
7. **Tests:** `venv/Scripts/python.exe scripts/preparar_bd_test.py --recrear` y `pytest`.
8. **Bundles React** (están en `.gitignore`): `bash scripts/build_react.sh`.
9. **Git:** `git config user.name/user.email`, iniciar sesión en GitHub, y `git status` +
   `git log origin/develop..` por si hubiera trabajo sin subir.
10. **Claude local — lo que se perdió en C:** la configuración de usuario (`~/.claude.json`: servidores
    MCP de PostgreSQL, Playwright y Windows) y las memorias locales del proyecto (por ejemplo
    `project_login_dos_pasos`). El `.claude/settings.json`, los hooks y las reglas del repositorio sí
    están (en D:) y vuelven solos. Hay que volver a dar de alta los MCP y reponer las memorias que
    importen.
