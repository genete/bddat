# Servidor Linux dedicado para BDDAT (BD + Flask) — análisis

Fecha: 2026-10-13. Es **análisis, no decisión**: no se ha tocado código ni configuración. Lo que no
está comprobado va marcado como *interpretación* o *por comprobar*.

## 1. El objetivo, en llano

Hoy la base de datos de desarrollo y el servidor Flask viven en tu PC de trabajo. Cuando ese PC falla
(como ahora con C:), te quedas sin entorno real. La idea es mover **PostgreSQL y Flask a un PC Linux
dedicado**, que sea además el ensayo del servidor final (sin entrar en producción), y trabajar contra
él desde el PC del trabajo o desde casa. La pregunta es si el flujo actual (Claude local + Claude en la
nube) sobrevive a eso.

## 2. Veredicto

**Sí, sobrevive, y el repositorio ya apunta ahí.** Tres hechos comprobados:

1. **La nube ya es ese servidor, en pequeño.** Cada sesión en la nube levanta PostgreSQL 16, Python
   3.14.7, LibreOffice y la app completa en Linux, y la suite pasa. En `app/` no he encontrado
   llamadas propias de Windows (`startfile`, `msvcrt`, `winreg`; búsqueda por esos nombres, no una
   auditoría completa: #330 menciona además un separador de rutas pendiente en `admin_plantillas`). Lo
   atado a Windows que sí he localizado está en scripts y configuración (§6).
2. **Ya está decidido como dirección.** `docs/referencia/ANALISIS_DESPLIEGUE.md` (#330) prefiere
   «Linux nativo» (vía B) frente a Windows 11 + WSL2, con Docker Engine, SSH, gunicorn y nginx, y
   nombra un PC dedicado (i7-12700, 32 GB). Lo que propones es adelantar esa vía como entorno de
   desarrollo.
3. **Ya hay un guion de aprovisionamiento.** `scripts/nube/preparar_entorno.sh` hace justo lo que
   hay que hacer en el servidor (Python 3.14.7 con `uv`, PostgreSQL 16, roles, `.env`, BD de tests,
   LibreOffice). Hoy se niega a correr fuera de la nube, pero admite `BDDAT_NUBE_FORZAR=1`. Habría que
   adaptarlo (supone root y el clúster Debian); *no lo he probado en una máquina real*.

**Lo que decide si funciona no es técnico**: es dónde está la máquina y qué red ve (§4).

## 3. Cómo encaja cada pieza del flujo

```
 PC trabajo (Windows)           PC casa
   navegador, terminal            navegador, terminal
        │ SSH / túnel                │ VPN → SSH / túnel
        └────────────┬───────────────┘
                     ▼
        Servidor Linux dedicado (Ubuntu Server LTS)
          PostgreSQL ── bddat, bddat_test
          Flask (desarrollo) ── repo en git + venv
          almacén y manifiestos de desarrollo (disco local)
          [después] compose «pre»: gunicorn + nginx + PostgreSQL
                     ▲
                     │ git push / pull
                  GitHub ◄──── Claude en la nube (BD sintética propia)
```

| Pieza | ¿Sigue funcionando? | Cómo |
|---|---|---|
| Claude en la nube (código, tests, capturas) | **Sí, sin cambios** | Sigue con su BD sintética. No ve el servidor. |
| Nube → servidor real | **No directamente, ni conviene** | La nube sale desde servidores de Anthropic: habría que exponer tu servidor a Internet y permitir ese host en la red del entorno. El puente es **git**: la nube sube rama, tú haces `git pull` en el servidor y pruebas con datos reales. |
| Claude local | **Sí, de dos formas** (abajo) | |
| Navegador (tuyo) | Sí | `http://servidor:5000`, o `http://localhost:5000` con túnel SSH. |
| MCP de PostgreSQL | Sí | Por túnel SSH (`ssh -L 5432:localhost:5432 servidor`): el puerto de la BD no se abre a la red. |
| MCP de Playwright | Sí | El navegador está en tu PC y apunta a la URL del servidor. |
| Windows MCP, `flask_console.py` | No aplican | Son del PC Windows. Ya hoy se prescinde de ellos en la nube. |

**Claude local, dos formas:**

- **(1) Claude Code dentro del servidor, entrando por SSH** (recomendada). El repo, la BD y Flask
  están en el mismo sitio: no hay que sincronizar nada, y desde el trabajo o desde casa ves lo mismo
  (con `tmux` la sesión sobrevive a desconexiones). El PC solo pone terminal y navegador. **Requiere
  que el servidor pueda salir a Internet** (Anthropic, GitHub, PyPI) — *por comprobar*.
- **(2) Claude Code en tu PC y el servidor solo como BD + Flask.** Tendrías dos copias del repo
  (`D:` y servidor) y habría que sincronizarlas por git en cada vuelta. Solo si (1) no es posible.

## 4. Lo que hay que averiguar antes (decide el plan)

1. **¿Dónde está la máquina?**
   - **En la red de la Consejería** (la del plan #151). Desde el trabajo: SSH directo a la IP interna
     (el cliente OpenSSH viene con Windows). Desde casa: la VPN corporativa, si existe; hay que pedir
     a Informática que permita SSH y el puerto de la app. Es el escenario más limpio y el más parecido
     a producción.
   - **En tu casa.** Desde casa es trivial (misma LAN). Desde el trabajo es lo difícil: un PC
     corporativo normalmente no deja instalar un cliente VPN propio (Tailscale, WireGuard) ni sacar
     SSH a Internet. *Interpretación:* probablemente no sea viable sin permiso de Informática. Además,
     nada con datos reales de expedientes en casa.
2. **¿Tiene salida a Internet?** Para `git`, `pip`, `apt` y Claude. Sin ella, la forma (1) cae.
3. **¿Quién autoriza instalar Linux** en un equipo de la red de la Consejería?

## 5. Docker o no

| Opción | A favor | En contra |
|---|---|---|
| **Nativo** (apt: PostgreSQL; venv con `uv`; systemd) | Lo más simple de mantener y de depurar. Flask con recarga en caliente. Claude ejecuta comandos directos. Es lo que ya hace `preparar_entorno.sh`. | No ensaya el despliegue final. |
| **Todo en Docker** (compose: app + db) | Es el destino de #330: imagen, `flask db upgrade` al arrancar, vuelta atrás por etiqueta. | **No existe todavía** `Dockerfile`, `wsgi.py` ni `docker-compose.yml` (§9 del análisis de despliegue). Iterar sobre código dentro del contenedor añade fricción diaria. |
| **Híbrido** | Desarrollo nativo ahora; cuando existan los artefactos de #330, un compose «pre» en otro puerto, con gunicorn + nginx + PostgreSQL, que es el ensayo del servidor final. | Dos instancias que mantener. |

**Recomendación:** nativo ahora; compose «pre» cuando exista el Dockerfile de #330. El PC dedicado del plan
(i7-12700, 32 GB; `ANALISIS_DESPLIEGUE.md` §7) aguanta las dos. Docker Engine, no Docker Desktop (Desktop es de pago en
organizaciones de más de 250 empleados).

## 6. Qué en el repositorio asume Windows (para cuando se decida)

Esto sería la «tabla de consumidores» de una futura issue, no una propuesta de cambio todavía:

| Dónde | Qué asume |
|---|---|
| `.claude/settings.json` | Permisos con `D:/BDDAT/venv/Scripts/python.exe`; hooks con `python` y `/d/BDDAT` como respaldo. |
| `.claude/launch.json` | `venv/Scripts/python`. |
| `scripts/flask_console.py` | tkinter y `D:\BDDAT` fijos. |
| `fabricar_*.py`, `tests/test_182_*`, `tests/test_732_*` | `SOFFICE` por defecto `C:\Program Files\LibreOffice\...`; ya se puede cambiar con la variable de entorno `SOFFICE`. |
| `.env.example` | Rutas `D:/BDDAT/...`. |
| `scripts/cliente/` | Manejador del explorador de Windows: no aplica. |
| **`run.py`** | **`app.run(..., debug=True)` fijo.** Con `FLASK_HOST=0.0.0.0` el depurador interactivo de Werkzeug queda accesible desde la red (ejecución de código, protegida solo por un PIN). Ver §7. |

## 7. Seguridad mínima del servidor

- **No exponer `run.py` con `debug=True` a la red.** Dos salidas: escuchar solo en `127.0.0.1` y entrar
  por túnel SSH (nada que abrir), o servir con gunicorn detrás de nginx.
- SSH solo con clave, sin contraseña ni acceso de root. `ufw`: solo 22 (y el puerto de la app si se
  expone) desde la red permitida. PostgreSQL solo en `localhost`.
- `SECRET_KEY` propia en el `.env` (el código tiene un respaldo `dev-secret-fallback`).
- `SQLALCHEMY_ECHO=false` en el servidor (por defecto es `true` y llena el log).

## 8. Mantenimiento de la máquina

La regla de fondo: **la máquina debe ser desechable**. Si cae otro disco, reconstruirla es ejecutar un
guion, no recordar pasos. Lo que no esté en git o en una copia, se pierde.

| Cada | Qué |
|---|---|
| Siempre (automático) | `unattended-upgrades` para parches de seguridad; `smartd` (smartmontools) que avisa **antes** de que un disco falle; `systemd` con `Restart=on-failure` para la app; `journald` rota los logs. |
| Cada noche | `pg_dump` de `bddat` a **otro disco**; copia de lo que no está en git: `.env`, `almacen_dev/`, `manifiestos_dev/`, `docs_prueba/plantillas_escritos/`. |
| Cada semana | Copia **fuera de la máquina** (otro equipo o el share de la Consejería). |
| Cada mes (~15 min) | `apt upgrade` y reinicio si hay kernel nuevo; `df -h`; comprobar que los backups se han hecho. |
| Cada trimestre | **Restaurar** un backup en una base de prueba. Un backup que no se ha restaurado no es un backup. |
| Cada año | Salto de versión mayor de PostgreSQL (dump/restore planificado) o de Ubuntu LTS. |

Hardware: dos discos (espejo, o segundo disco con copia nocturna) y, si se puede, un SAI. Es lo que
habría evitado el susto de ahora.

## 9. Plan por fases (si se decide)

0. Resolver §4 (ubicación, Internet, permiso).
1. Ubuntu Server LTS + PostgreSQL + Python 3.14.7 (`uv`) + `.env` + `flask db upgrade` + app
   escuchando en `127.0.0.1` con túnel. Es el grueso: adaptar `preparar_entorno.sh`.
2. Backups, `systemd`, `ufw`, claves SSH, `smartd`.
3. Claude Code en el servidor y parametrizar lo de §6.
4. Compose «pre» cuando exista el Dockerfile de #330.

## 10. ¿A o B? Mi recomendación

**A se hace igual, completa, y B corre en paralelo como proyecto.** Razones:

- El PC se va a reinstalar de todos modos, y es la única vía para trabajar en local en las próximas
  semanas. B depende de tres cosas que no controlas (permiso, red, VPN).
- Casi todo lo de A lo necesitas **también con B**: tu PC seguiría siendo el terminal y el navegador,
  y necesita Git, Python, Node, Chrome y Claude Code. Solo PostgreSQL y LibreOffice pasarían a ser
  del servidor.
- PostgreSQL en el PC no estorba: cuando B funcione queda como base local de tests (`bddat_test`,
  más rápida que cruzar la red) o se desinstala.

**Se puede omitir PostgreSQL de la petición a Informática solo si** las tres respuestas de §4 son «sí»
y el servidor va a estar listo en pocos días.

## 11. Lo que se ha perdido con C: y lo que no

- **No se pierde:** el código (D:, y GitHub), el `.env`, `docs_prueba/`, `almacen_dev/` y
  `manifiestos_dev/` (si estaban en D:, como indica `.env.example`).
- **Tampoco se pierde la BD de desarrollo** (confirmado: su carpeta de datos estaba en D:). Se
  recupera reinstalando la misma versión mayor de PostgreSQL y apuntando el servicio a esa carpeta
  (ver instrucciones para Informática, §2). Con la BD intacta, la prioridad de A sube: es lo que
  restablece el entorno tal cual estaba. Plan B si no arranca: reconstruir desde las 193 migraciones.
- **Sí se pierde:** la configuración de usuario de Claude local (MCP de PostgreSQL, Playwright y
  Windows) y las memorias locales del proyecto, más el `venv` (apunta al Python antiguo y se recrea).
- **Riesgo vivo:** `.env`, `docs_prueba/`, `almacen_dev/`, `manifiestos_dev/` y la carpeta de datos de
  PostgreSQL **no están en git** y D: es ahora su única copia. Conviene copiarlos antes de que nadie toque los discos.
