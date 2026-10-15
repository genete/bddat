# Flujo de trabajo con el PC de desarrollo Linux — pieza a pieza

Escenario fijado: un PC Linux en la red de la Consejería («PC desarrollo») con PostgreSQL, Flask,
el repositorio y **Claude Code corriendo dentro**. El PC de trabajo (Windows, misma red) es la ventana:
Claude Desktop y navegador. La nube y GitHub siguen como hoy.

*Por comprobar* = lo he leído en documentación pero no lo he probado en vuestra red.

## 1. Quién es quién

| Máquina | Qué hace | Qué guarda |
|---|---|---|
| **PC desarrollo** (Linux) | Ejecuta todo: Claude Code, PostgreSQL, Flask, tests, LibreOffice, navegador sin pantalla para capturas | Repo, `.env`, BD `bddat` y `bddat_test`, almacén y manifiestos de desarrollo, plantillas, conversaciones de Claude de esa máquina |
| **PC trabajo** (Windows) | Pantalla y teclado: Claude Desktop (sesión SSH), tu navegador, a veces una terminal SSH | Nada que no se pueda perder. Opcional: un clon del repo |
| **GitHub** | Puente entre todo | El código |
| **Nube (Claude)** | Programa con su propia BD sintética | Nada de vuestra red |

## 2. Una sesión tipo

1. Abres Claude Desktop en el PC trabajo → pestaña Code → entorno **SSH** → eliges el PC desarrollo y
   la carpeta del repo. Claude arranca *en el PC desarrollo*.
2. Pides el trabajo. Claude edita ficheros, ejecuta `pytest`, lanza migraciones, consulta la BD con
   `psql`: todo ocurre en el PC desarrollo, sin copiar nada.
3. Los cambios los revisas en el propio Desktop: indicador `+12 -1`, diff fichero a fichero,
   comentarios en línea, panel de ficheros para leer `.md`.
4. Para **ver la aplicación**: Flask escucha solo en `127.0.0.1:5000` del PC desarrollo; desde el PC
   trabajo abres un túnel (`ssh -N -L 5000:localhost:5000 desarrollo`) y entras por
   `http://localhost:5000` en tu navegador. El panel de navegador de Desktop **no** previsualiza la app
   en sesiones SSH, así que se usa tu navegador normal.
5. Para que **Claude vea la interfaz** (capturas): `scripts/nube/captura.mjs` ya hace login de dos pasos
   y captura con Playwright para Node. Habría que instalar Chromium en el PC desarrollo y permitir que
   el script corra fuera de la nube (hoy se niega salvo `BDDAT_NUBE_FORZAR=1`). *Por comprobar.*
6. Cuando está bien: commit y push a GitHub desde el PC desarrollo, PR como siempre.
7. La nube sigue siendo útil: avanza ramas con datos sintéticos. Tú, en el PC desarrollo,
   `git fetch` + checkout de esa rama y la pruebas con la BD real de desarrollo.

## 3. Pieza a pieza

**Claude Code en el PC desarrollo.** Dos formas de hablarle:
- *Claude Desktop con sesión SSH* (tu preferencia): Desktop usa el cliente `ssh` de tu PC, instala
  Claude Code en el PC desarrollo la primera vez y lo maneja desde fuera. Tienes diffs, revisión de
  código, panel de ficheros y terminal. Requisitos en el PC desarrollo: servidor SSH con el
  subsistema **SFTP** activo, `MaxSessions` no limitado a 1, ~1 GB libre en el home del usuario y
  `~/.claude/remote/` fuera de un montaje `noexec`. Hay que probarlo con vuestra versión de Desktop
  en Windows (*por comprobar*).
- *Terminal SSH + `claude`* (la CLI de tus comienzos), dentro de `tmux`. Menos cómoda para diffs, pero
  la sesión **sobrevive a desconexiones** y es la forma buena para tareas largas.
- Aviso de la documentación: con inicio de sesión de cuenta Claude, una tarea puede **pararse si caduca
  la sesión al desconectarte**. Para encargos largos, `tmux` + CLI.

**Autenticación de Claude en una máquina sin pantalla.** `claude` da una dirección web que abres en
cualquier otro equipo para iniciar sesión. Tiene que haber salida a Internet desde el PC desarrollo (§5).

**Repositorio.** Clon único en el PC desarrollo. `git` autenticado contra GitHub (clave de despliegue
o `gh auth`). El PC trabajo no necesita clon; si lo tienes, regla: *push antes de dejar un sitio, pull
antes de empezar en el otro*.

**PostgreSQL.** Instalado con `apt` (la 16 que trae Ubuntu 24.04 es la que ya prueba la nube), solo en
`localhost`. Roles `bddat_admin` y `claude_desktop`, bases `bddat` y `bddat_test`. La BD se reconstruye
con `flask db upgrade` (193 migraciones: esquema y catálogo). Consultas de Claude: `psql` por
Bash dentro de la máquina. El **MCP de PostgreSQL** es dudoso: la documentación dice que los
conectores y MCP de una sesión SSH corren a través de Desktop, es decir, en el PC trabajo y no en el
servidor. Habría que verlo; el plan B es `psql`.

**Flask.** `run.py` en `127.0.0.1:5000` como servicio de `systemd` (arranca solo, se reinicia si cae).
Recarga en caliente al editar. Nunca `debug=True` abierto a la red.

**Python.** 3.14.7 con `uv` en un `venv` (obligatorio: el código usa `uuid.uuid7`). Lo instala el guion
de aprovisionamiento, no hace falta paquete del sistema.

**LibreOffice y Node.** LibreOffice Writer para generar escritos y los tests 182 y 732 (variable
`SOFFICE=/usr/bin/soffice`). Node para compilar los bundles React (`scripts/build_react.sh`).

**Almacén y manifiestos.** Carpetas locales del PC desarrollo (`almacen_dev`, `manifiestos_dev`),
inicializadas una vez con su marca de raíz. Entran en el backup nocturno porque no están en git.

**Tests.** `pytest` contra `bddat_test` en la misma máquina, como en la nube (~30 s).

**Backups.** `pg_dump` nocturno a un segundo disco o al share de la Consejería, más copia de las carpetas
que no están en git. Prueba de restauración cada trimestre.

**Conversaciones de Claude.** Las del PC desarrollo viven en esa máquina. Se retoman desde cualquier
equipo que se conecte a ella (Desktop SSH o `claude --resume` por SSH). No están en claude.ai como las
de la nube. Si quieres que una idea nacida en la nube llegue al PC desarrollo, el vehículo es la rama
de git.

**Nube.** Igual que hoy. No ve el PC desarrollo ni conviene que lo vea.

## 4. Qué pasa cuando…

| Situación | Efecto |
|---|---|
| Falla o se reinstala el PC trabajo | Nada: instalas Desktop, entras por SSH. Era el objetivo. |
| Falla el PC desarrollo | Se pierde lo que no esté en git ni en backup. Reconstrucción: Ubuntu + guion + restaurar el último `pg_dump`. |
| Se cierra Desktop o se cae la red | Con `tmux`, la tarea sigue. Con Desktop y cuenta Claude puede pararse (§3). |
| El PC desarrollo no sale a Internet | No hay Claude dentro ni `git pull`: cae la mitad del plan (§5). |
| Quieres trabajar sin tocar la BD real | La nube, con datos sintéticos. |

## 5. Salida a Internet: no es «lo que ya tiene un PC de trabajo»

Un PC de trabajo suele salir con tu usuario de dominio (proxy autenticado o transparente). Un servidor
Linux **no tiene tu usuario de dominio**: puede quedarse sin salida aunque tu PC la tenga, o necesitar
una excepción por IP o una cuenta de servicio. Es la primera cosa que conviene dejar clara.

Destinos mínimos (a confirmar con la documentación de red de Claude Code):
`github.com`, `pypi.org`, `files.pythonhosted.org`, `registry.npmjs.org`, `api.anthropic.com`,
`claude.ai`, los espejos de `apt` (Ubuntu y, si se usa, PostgreSQL), y para capturas el CDN de
Playwright. Opcionales: `www.boe.es` y `ws040.juntadeandalucia.es` (consulta de legislación).

Si hay proxy: `HTTPS_PROXY` (y `NODE_EXTRA_CA_CERTS` si inspecciona TLS) en `~/.claude/settings.json`
del servidor, no en el perfil de la shell.

## 6. Lo que pedir al coordinador

En términos de requisitos, no de marca:

1. Un **equipo con Linux** (Ubuntu Server LTS): físico o **máquina virtual**. Para el desarrollo basta
   una VM.
2. **Permiso de administración (sudo) para el desarrollador** sobre ese equipo. Sin esto se pierde la
   utilidad. Si Informática exige administrarlo ella, no se podría instalar ni arreglar nada sin ticket.
3. **IP fija interna** y SSH (22) permitido desde tu PC de trabajo.
4. **Salida a Internet** a la lista de §5, con el mecanismo de proxy que corresponda.
5. Un sitio donde copiar los backups (el share, por ejemplo).
6. Aclarar quién parchea el sistema: puede ser el propio desarrollador con actualizaciones automáticas
   de seguridad.

Para desarrollo **no hace falta** abrir la aplicación a otros usuarios: solo tú, por túnel. El acceso de
usuarios finales es una fase posterior (despliegue), que ya pasa por el issue #151 con Informática.

## 7. Si no conceden Linux

Orden de preferencia de las alternativas, todas viables salvo la primera mejor:

1. **Máquina virtual Linux** en la infraestructura de la Consejería (equivale a todo lo anterior).
2. **Windows con WSL2** (vía A del análisis de despliegue): funciona, pero con arranque artesanal,
   red tras NAT y antivirus corporativo.
3. **Windows nativo**: PostgreSQL y Waitress. ADR-050 ya contempla Waitress si el servidor es Windows.
   Se pierde la igualdad con la nube.

El desarrollo en la nube sigue siendo viable en cualquier caso: lo que se pierde sin el equipo es el
entorno real para «trastear», no la capacidad de programar.

## 8. Usuarios, Internet y dominio en el PC Linux

**Quién corre cuando el PC está encendido y esperando.** Nadie ha hecho login. `systemd` lanza los
servicios configurados, cada uno con su usuario de sistema: PostgreSQL como `postgres`, Flask como un
usuario sin privilegios (p. ej. `bddat`) o como tu cuenta. `root` solo lo usan el arranque y el servicio
SSH; nada tuyo corre como root y nadie entra como root (se usa `sudo`).

**Quién necesita Internet.** Por defecto, la salida depende de la **máquina**, no del usuario de Linux:
el cortafuegos o proxy ve la IP del equipo. Necesitan Internet `apt`, `git`, `pip`, `npm` y `claude`
(con tu cuenta); Flask y PostgreSQL no. Excepción: un proxy que pida identificarse. Tres casos a
preguntar:
1. La IP del servidor tiene salida abierta o autorizada: nada más que hacer.
2. Proxy sin autenticación, basta autorizar la IP: se configura la dirección del proxy una vez.
3. Proxy con usuario y contraseña: hace falta una cuenta de servicio y guardar sus credenciales en la
   configuración. El caso incómodo.

El PC de trabajo probablemente sale con tu usuario de dominio (Kerberos o NTLM transparente); un Linux
sin dominio no puede hacerlo.

**Cómo entras por SSH.** Con una cuenta Linux de esa máquina (normalmente local, p. ej. `carlos`), con
clave SSH y sin pasar por el dominio: `ssh carlos@servidor`. Todo lo que hagas, Claude Code incluido,
corre bajo esa cuenta.

**Dominio.** Linux puede unirse a Active Directory. Entonces no te crean un usuario nuevo: usas tu
cuenta de dominio de siempre, y el equipo recibe su propia cuenta de equipo. No es imprescindible;
lo exigirá Informática si su política obliga a cuentas centralizadas y auditables (ENS, #176).
Cualquiera de las dos vías vale con una condición: **tu cuenta, local o de dominio, debe tener `sudo`**.
Claude Desktop por SSH necesita además entrar con clave, sin contraseña interactiva.

**Preguntas para el coordinador:** (1) ¿cuenta local con clave SSH o unido al dominio, con `sudo` en
ambos casos?; (2) ¿cómo sale el servidor a Internet: abierto por IP, proxy sin autenticación o proxy
con usuario?

## 9. Cómo contarlo en una frase

«Necesito un servidor Linux en la red interna, con permisos de administración para mí, donde alojar la
base de datos y la aplicación de desarrollo, para no depender de mi PC de trabajo; es además el ensayo
del servidor definitivo.»
