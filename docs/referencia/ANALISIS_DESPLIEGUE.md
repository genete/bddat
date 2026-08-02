# Análisis de despliegue — balance de carga y estrategia multiworker

> **Origen:** sesión de análisis 2026-07-20. Desarrolla técnicamente la
> estrategia de entornos del issue #330 (WSL → Docker → Producción) y alimenta
> la coordinación de infraestructura de #151. Es **análisis**, no decisión:
> las decisiones pendientes se listan en §8.
>
> Issues relacionados: #330 (plan de entornos), #151 (infraestructura con IT),
> #45 (SECRET_KEY), #177 (HTTPS), #178 (backups), #176 (ENS), #120 (base numero_at).

---

## 1. Motivación: balance de carga cliente/servidor

Análisis de qué máquina hace el trabajo en cada operación, para localizar el
cuello de botella real antes de decidir el despliegue.

| Operación | PostgreSQL | Flask (Python) | Cliente (navegador) |
|---|---|---|---|
| Filtrado/ordenación/paginación de listados | ✅ `WHERE` + `ORDER BY` + `LIMIT 50` con cursor | Compone query ORM, serializa JSON | Pide página al llegar al umbral de scroll |
| Renderizado de filas de listados | — | — | ✅ `ScrollInfinito` construye el DOM desde JSON |
| Filtros interactivos (teclear) | Ejecuta la query | Atiende la petición | ✅ Debounce 400 ms — mientras se teclea el servidor no recibe nada |
| Página completa (GET clásico) | Queries de contexto | ✅ Context builders + render Jinja | Pinta HTML |
| Inspector overlay (ADR-023) | Queries del detalle | ✅ Renderiza fragmento HTML | Fetch + caché de fragmentos (reabrir no repite petición) |
| Árbol del expediente | Queries jerarquía (`selectinload`) | ✅ Serializa árbol JSON + plazos con calendario hábil | ✅ Layout y pintado del grafo (xyflow), estado→color, colapsado |
| Islas React (mi-trabajo, estadísticas, diagrama, palette) | Queries | Serialización JSON | ✅ Todo el renderizado e interactividad |
| Motor de reglas | Lee reglas/excepciones | ✅ Evaluación dos barridos en Python | — |
| Generación de escritos .docx | Queries de contexto | ✅ docxtpl — **CPU-bound** | Descarga |
| Certificados PDF on-demand | Query | ✅ reportlab — **CPU-bound** | Descarga |
| Estadísticas supervisor | Queries por expediente | ✅ `construir_arbol` por expediente, agrega en Python | Renderiza panel |
| Búsqueda global / typeahead | ✅ `ILIKE '%q%'` (sin índice B-tree posible) | Compone y serializa | Debounce + pintado |
| Formularios (POST) | INSERT/UPDATE | Validación servidor + invariantes | ✅ Recopilación, validación ligera, payload |
| Subida de documentos | Metadatos | ✅ Multipart + escritura a `FILESYSTEM_BASE` — I/O-bound | Envío |
| Estáticos (bundles, CSS) | — | ✅ En dev los sirve Flask | Ejecuta |

**Diagnóstico:** el camino de lectura interactiva está bien equilibrado
(filtrado empujado a SQL, pintado empujado al cliente, debounce + caché de
fragmentos). Los riesgos de saturación **no están en Postgres** — sus queries
son sencillas e indexadas. Están en el proceso Python, por orden:

1. **Un solo proceso Python + GIL** (`run.py` → dev server Werkzeug). El
   trabajo CPU-bound (docx, PDF, árboles grandes, Jinja) se serializa: una
   generación de escrito ralentiza a todos los usuarios. Cuello de botella
   estructural. → Este documento.
2. **Vistas que multiplican `construir_arbol`** (estadísticas: 1×expediente;
   seguimiento: 1×fila). Coste conocido v1, con plan de desnormalización
   documentado en el propio servicio ("medir primero").
3. **Motor de reglas y plazos en rutas de lectura** (hipótesis 2026-07-20,
   sin medir): ha pasado de invocarse solo al crear/borrar a llamarse desde
   varios puntos solo para mostrar datos u opciones posibles, recargando las
   reglas de BD en cada evaluación. Estrategia de caché en §11.
4. **`ILIKE '%q%'`** fuerza seq-scan; crece con las tablas. Solución futura si
   se nota: índice `pg_trgm` (solo BD).
5. **`COUNT(*)` por recarga de filtros.** Menor.

---

## 2. WSGI multiworker: qué es y por qué resuelve el punto 1

Flask es una *aplicación* WSGI, no un servidor. `run.py` la sirve con el
servidor de desarrollo de Werkzeug (un proceso). Un servidor WSGI de
producción (gunicorn) arranca un proceso maestro con **N procesos hijos
("workers")**, cada uno con copia completa e independiente de la app, y
reparte las peticiones entre ellos.

No reduce el trabajo total — lo paraleliza y aísla:

- **Esquiva el GIL:** N workers = N intérpretes = N núcleos utilizables. El
  GIL sigue existiendo, pero uno por proceso.
- **Aislamiento:** un escrito pesado bloquea solo su worker; los demás siguen
  sirviendo listados.
- **Robustez:** worker muerto → el maestro lo reemplaza sin caída; reciclado
  periódico de workers corta fugas de memoria lentas.

---

## 3. Consecuencias para el código (auditoría 2026-07-20)

Los tres riesgos clásicos del multiproceso están **ya resueltos** en BDDAT:

| Riesgo clásico | Estado |
|---|---|
| Estado compartido en memoria de proceso | ✅ No existe. Modo global del motor en BD (`ConfiguracionSistema`); sin cachés de módulo ni `lru_cache` |
| Sesiones ligadas a un proceso | ✅ Cookies firmadas (la sesión viaja en el navegador); cualquier worker atiende cualquier petición |
| Carrera en numeración de expedientes | ✅ Tabla contador con `UPDATE … RETURNING` atómico (`wizard_expediente.py`) — Postgres serializa |

Lo que falta (casi todo artefacto de despliegue, no código de aplicación):

1. **`wsgi.py`** de producción (sin `debug`, sin reloader). `run.py` ya expone
   `app` a nivel de módulo, casi vale tal cual.
2. **Endurecer configuración:** `SECRET_KEY` tiene fallback de desarrollo en
   `config.py` — en producción debe ser error de arranque si falta (**#45**).
   Todos los workers deben compartir la misma clave (vía entorno).
3. **Pool de conexiones:** total = workers × pool_size. Con 4 workers y pool
   por defecto cabe de sobra en `max_connections=100`, pero hacer la cuenta.
4. **Logging:** N procesos sobre el mismo fichero rotativo da problemas. En
   Docker se disuelve solo: stdout → `docker logs`.
5. **Estáticos:** servirlos el proxy inverso, no los workers Python.
6. **Regla hacia adelante:** *estado compartido va a BD, nunca a variable de
   módulo*. Es lo único que puede romper el multiworker silenciosamente
   (funcionaría en dev con 1 proceso y divergiría entre workers en producción).

---

## 4. Vía A — PC dedicado Windows 11 + Docker sobre WSL2

**Confirmado: gunicorn multiworker funciona correctamente ahí.** WSL2 es un
kernel Linux real en VM ligera; `fork()` funciona; los workers son procesos
Linux genuinos repartidos entre los núcleos asignados a la VM.

El modelo operativo es el idiomático de #330: imagen con todo dentro,
sustituir, arrancar; rollback = etiqueta de imagen anterior. Regla de oro:
**contenedor desechable — todo lo que deba sobrevivir vive fuera** (volúmenes).

Condicionantes específicos de esta vía:

- **Licencia Docker Desktop:** de pago para organizaciones >250 empleados (la
  Junta lo es). Solución limpia: **Docker Engine directamente en WSL2**, sin
  Docker Desktop (libre y gratuito).
- **Arranque sin sesión:** WSL2 y dockerd no arrancan solos al reiniciar
  Windows. Requiere tarea programada al inicio del sistema y verificar que
  sobrevive a un reinicio sin login (Windows Update reinicia solo).
- **Exposición del puerto a la LAN:** WSL2 vive tras NAT propio. Requiere modo
  *mirrored networking* (W11) o `portproxy` persistente para que los clientes
  lleguen a gunicorn.
- **`FILESYSTEM_BASE`:** el montaje CIFS del share corporativo (ver §6, común
  a ambas vías) tiene aquí una fragilidad añadida: debe hacerse *dentro* de la
  VM de WSL2, cuyo propio ciclo de vida ya depende de tareas programadas
  artesanales — un eslabón más en la cadena de arranque.

## 5. Vía B — PC dedicado con Linux nativo

Preferencia ya expresada en #330 ("preferentemente Linux nativo"). Frente a la
vía A elimina las capas duplicadas y las dos debilidades operativas:

| Vía A: W11 + WSL2 | Vía B: Linux nativo |
|---|---|
| Windows 11 completo (GUI, Defender, updates: 3–5 GB RAM en reposo) | Ubuntu Server headless (300–500 MB en reposo) |
| + VM WSL2 (segundo kernel, RAM reservada, devolución perezosa) | — |
| + Docker Engine dentro de la VM | Docker Engine como proceso normal (coste de virtualización cero) |
| Red de contenedores tras NAT (portproxy/mirrored) | Red nativa |
| Arranque tras reboot: tarea programada artesanal | systemd arranca Docker y contenedores de serie |
| Antivirus corporativo escaneando I/O de Postgres/gunicorn | Normalmente sin antivirus |
| Docker Desktop de pago (o Engine-en-WSL2 manual) | Sin problema de licencias |

**Administración remota (vía B):** SSH — gratuito e integrado en ambos
extremos (cliente OpenSSH incluido en Windows 10/11: `ssh usuario@ip`).
Complementos gratuitos: claves SSH en lugar de contraseña, VS Code +
Remote-SSH, `scp`/WinSCP para ficheros, Cockpit (web) si se quiere panel
visual. No se necesita escritorio remoto gráfico ni software de pago.
**Toda la pila (gunicorn, Docker Engine, nginx, PostgreSQL, Ubuntu) es
software libre: cero euros en licencias.**

**Almacenamiento de expedientes:** la vía B **no elimina** la dependencia del
share corporativo (§6) — también aquí hay que montarlo por CIFS. La diferencia
es de robustez, no de fondo: en Linux nativo el montaje es ciudadano de primera
(`fstab`/unidad systemd con `_netdev`, fichero de credenciales protegido,
reintento automático), sin la capa VM de por medio.

**Rendimiento:** para decenas de usuarios sobre el hardware de §7 ambas vías
funcionan sin que los usuarios lo noten — la ganancia de recursos de Linux es
real pero es el tercer argumento; los decisivos son los operativos (arranque
autónomo y red) y las licencias. El RAM que no gasta el SO acaba en caché de
ficheros, que acelera Postgres.

---

## 6. El almacenamiento de expedientes es del servidor de archivos corporativo (invariante, común a ambas vías)

Los expedientes se guardan y **custodian** en el servidor de archivos
corporativo (`\\HACACL0102\energia\ALTA TENSION\...`, ver comentario en
`config.py`), que ya tiene su sistema de copias de seguridad montado. Llevarlos
al disco del PC dedicado ni es posible ni es conveniente: se perdería la
custodia y el backup institucional a cambio de eliminar una dependencia de red.
**No es una debilidad a eliminar — es la arquitectura correcta**, y además es
el patrón estándar en la propia infraestructura de la Junta: la máquina que
corre la aplicación y la que sirve los datos son (y seguirán siendo) máquinas
distintas, también si algún día la app pasa a un servidor mantenido por
informática.

Consecuencias permanentes, independientes de la vía elegida:

- La app depende de **dos máquinas**: caída del servidor de archivos ≠ caída de
  BDDAT, pero las operaciones documentales (subir, descargar, generar escritos)
  fallarán mientras dure. Conviene verificar que la app **degrada con mensaje
  claro** en ese escenario en lugar de romperse entera (misma filosofía
  defensiva que ya se aplica al catálogo).
- Montaje CIFS con **cuenta de servicio de dominio** (no credenciales
  personales) y disponible en el arranque, en cualquiera de las dos vías.
- El rendimiento de escritura sobre SMB es peor que disco local, pero los
  ficheros son pequeños (docx/pdf de KB–pocos MB) y el patrón de acceso es
  esporádico: asumible. Verificar empíricamente al desplegar, no optimizar
  antes.
- `PLANTILLAS_BASE` es caso aparte: casi solo lectura y sin requisito de
  custodia — puede vivir en local si simplifica.

## 7. Hardware de destino (primera instancia)

PC dedicado, recursos confirmados 2026-07-20:

- Intel Core i7-12700 (12ª gen, 12 núcleos / 20 hilos)
- 32 GB RAM
- Windows 11 Pro 25H2 (estado inicial; ver decisión pendiente §7)

Sobrado para la carga esperada (servicio interno, decenas de usuarios
concurrentes como máximo). Orientación de workers gunicorn: empezar con 4–6 y
medir, no aplicar fórmulas genéricas (2×núcleos+1 sobredimensionaría el pool
de conexiones sin beneficio).

Segunda instancia posible: servidor del edificio (SO desconocido — ver §7).

---

## 8. Decisiones pendientes

1. **SO del PC dedicado:** mantener W11 + Docker en WSL2 (vía A, con sus tres
   apuntalamientos: Engine sin Desktop, arranque, portproxy) o instalar Linux
   nativo (vía B). Este análisis favorece la vía B; la A es viable.
2. **Detalles del montaje del share corporativo** (la ubicación en sí no es
   decisión — es invariante, §6): cuenta de servicio con la que se monta,
   comportamiento de la app cuando el share no está disponible (degradación
   con mensaje vs error), y verificación empírica del rendimiento SMB.
3. **PostgreSQL:** en contenedor dentro del compose (recomendado: misma
   máquina, sin cruzar frontera Windows/Linux, arranque coordinado) o nativo.
4. **SO del servidor del edificio** (desconocido a fecha de este análisis):
   condiciona si el salto posterior es trivial (Linux/Docker) o repite el
   análisis de la vía A. Averiguar con IT (#151). Nota: WSL2 requiere Windows
   Server 2022+ — en un Server 2019 la vía A no funciona.

## 9. Artefactos a crear al ejecutar (amplía las tareas de #330)

- `Dockerfile` + `.dockerignore` (base `python:3.x-slim`, gunicorn como CMD)
- `docker-compose.yml` — servicios `app` + `db`, volumen de datos Postgres,
  montaje CIFS del share de expedientes (§6), `PLANTILLAS_BASE` local o CIFS,
  variables de entorno
- `wsgi.py` + configuración de producción endurecida (§3.1–3.2, con #45)
- Entrypoint que ejecute `flask db upgrade` al arrancar (la sustitución del
  contenedor aplica sola las migraciones pendientes)
- Estrategia de backup del volumen Postgres (`pg_dump` programado hacia fuera
  del contenedor) (#178). Los documentos no entran: su backup ya lo da el
  servidor de archivos corporativo (§6)
- Ya recogidos en #330 y previos al contenedor: `Documento.url` a ruta
  relativa, separador de rutas en `admin_plantillas`, auditoría de scripts de
  poblado
- Copiar las tres plantillas base canónicas (#727) desde `app/data/plantillas_base/`
  (repo) a `PLANTILLAS_BASE/plantillas/` en la instalación real. La descarga desde
  el admin no depende de ello (sirve directo del repo), pero Carlos confirmó que
  la copia sigue haciendo falta aparte
- **Salvaguarda para que la suite de tests nunca corra contra la BD de
  producción** (discusión 2026-08-02, a raíz de #715): hoy `DevelopmentConfig`
  y `ProductionConfig` (`app/config.py`) leen la misma variable `DATABASE_URL`
  sin ninguna comprobación adicional — la separación es hoy 100% disciplina
  operativa (qué `.env` hay a mano al lanzar `pytest`), no una garantía del
  código. Los smoke tests y los tests de invariantes escriben transaccionalmente
  contra la BD real conectada (rollback por SAVEPOINT, ver `tests/conftest.py`
  `app_ctx`) — el rollback deshace filas e índices, pero **no** los contadores
  `SERIAL` (`nextval()` no es transaccional en PostgreSQL, a propósito): tras
  cada ejecución quedan huecos en los ids, inocuo en cualquier entorno (rango
  `INTEGER`, ~2.100 millones) pero indeseable en la BD real si ocurriera por
  error. Antes de desplegar, añadir una barrera explícita — p. ej. fixture
  `autouse` en `tests/conftest.py` que aborte la sesión si el nombre de la BD
  conectada no coincide con un patrón esperado de desarrollo/test, o
  `ProductionConfig` rechazando arrancar en modo `TESTING`.

---

## 10. Reparto servidor/cliente: qué es trasladable y qué no (discusión 2026-07-20)

Pregunta: ¿hay carga que hoy es del servidor y podría pasarse al cliente?
Respuesta corta: muy poca, y por razones precisas — no las intuitivas.

**No trasladable:**

- **Generación de escritos y certificados (docx/PDF).** La razón NO es la
  custodia: el acto de custodia (escribir en el share y registrar en BD)
  podría recibir bytes generados por el cliente, igual que recibe los
  documentos subidos. Las razones reales:
  1. **Dependencia no controlada:** en el contenedor, docxtpl/reportlab están
     disponibles por definición; en N PCs cliente serían bundles JS a
     desplegar y mantener.
  2. **Duplicación del motor de plantillas:** las plantillas están en sintaxis
     docxtpl/Jinja2; los motores JS (p. ej. docxtemplater) usan otra — dos
     dialectos de plantilla o dos juegos que mantener ("dos verdades").
  3. **El viaje no se ahorra:** el navegador no puede escribir en `W:\`
     (sandbox — que el usuario tenga la unidad mapeada no se lo da al JS de
     una página); los bytes irían cliente→Flask→share igualmente, y el
     servidor seguiría compilando y enviando el contexto (queries nombradas +
     ContextoBase). Solo se movería el render final, la fracción menor del
     trabajo.
- **Cálculo de estados, árbol y plazos.** Principio "sin tercera verdad"
  (ADR-016; docstring de `estadisticas_supervisor`): el servidor manda estado
  semántico y el cliente solo lo mapea a presentación. Moverlo a JS es
  duplicar reglas de negocio en dos lenguajes que divergirían.
- **Queries y filtrado de listados grandes.** Ya están donde deben: en
  Postgres, junto a los datos.

**Trasladable (mejoras oportunistas al tocar cada vista, no frente propio):**

1. **Catálogos y listados pequeños:** cargar una vez y filtrar en cliente —
   elimina el `ILIKE` por pausa de tecleo en tablas maestras y listados admin
   de pocas centenas de filas estables. No aplica a expedientes/entidades
   (miles de filas, datos vivos).
2. **Caché HTTP (`ETag`/`Cache-Control`) en endpoints de catálogo:** la
   respuesta habitual pasa a ser un 304 sin cuerpo (query y serialización
   evitadas).
3. **Fragmentos del inspector como JSON** en los de más tráfico — ahorra
   render Jinja; ganancia pequeña, solo si una medición lo señala.

Descartado: precargar en cliente un índice de expedientes para el Command
Palette (frescura de datos + el índice visible depende del rol; `api_search`
con debounce ya es barato).

## 11. Motor de reglas y plazos en rutas de lectura: estrategia de caché

**Diagnóstico (verificado en código):** el motor ha pasado de portero de
mutaciones a decorador de lecturas — `tipos_creables` se llama desde
`api_expedientes` para pintar opciones por nodo, y el assembler usa
`auditar`/`evaluar_multi` para los estados ESFTT que se muestran. Cada
evaluación recarga las reglas de BD con `joinedload`
(`motor_reglas.py:196` y `:266`).

**Descomposición del coste por evaluación** — tres componentes muy distintos:

1. **Cargar reglas** (reglas + condiciones + excepciones): dato puro, cambia
   rarísimo en producción → cacheable al 100 %.
2. **Compilar sujeto y variables** (estado vivo del expediente, assembler):
   queries por expediente en cada llamada → NO cacheable más allá de la
   petición.
3. **Evaluar** (dos barridos, operadores): trivial en CPU.

**Estrategia propuesta — caché en servidor, no en cliente:**

- **Caché de reglas por worker con versión en BD:** contador `motor_version`
  (p. ej. en `ConfiguracionSistema`), incrementado por cualquier edición de
  reglas/excepciones/catálogo de plazos. Cada worker mantiene el juego de
  reglas compilado en memoria y lo reconstruye al ver cambiar la versión
  (semántica dirty→rebuild). Los "clientes" a invalidar son 4–6 workers en la
  misma máquina, no N navegadores por la LAN. Cada evaluación pasa de dos
  queries con joins a un lookup en memoria.
  - *Compatibilidad con la regla de §3.6* ("estado compartido va a BD"): es un
    caché read-through cuya fuente de verdad sigue siendo BD, con invalidación
    explícita por versión — no es estado de negocio en memoria.
- **`ETag` derivado de `motor_version`** en endpoints cuya respuesta dependa
  solo de reglas (no de estado vivo): caché en cliente sin evaluar nada en JS.

**Por qué NO evaluación de reglas en JavaScript** (evaluado y descartado):

- Requeriría el gemelo JS de `operadores.py` y de los dos barridos — tercera
  verdad.
- Sería solo consultivo: el servidor re-evalúa en el POST real de todas
  formas; solo se ahorrarían llamadas de pintado, que necesitan las variables
  (componente 2) que el servidor tendría que compilar y enviar igualmente. El
  ahorro neto queda en el componente 3, el trivial.
- Plazos: calendario hábil y suspensiones están centralizados en servidor a
  propósito (decisión ADR-016 recogida en `arbol_expediente`). Replicarlos en
  cliente es duplicar un subsistema entero.

**Prerequisito antes de construir nada:** log de tiempos en
`evaluar`/`auditar` con uso real ("medir primero", doctrina ya escrita en
`estadisticas_supervisor`). Si el coste dominante es cargar reglas, el caché
por worker lo elimina; si es compilar variables, el caché no ayuda y habría
que mirar el assembler.
