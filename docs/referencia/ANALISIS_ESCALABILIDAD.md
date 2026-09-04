# Análisis de escalabilidad — BDDAT

> **Qué es esto:** dónde cede la arquitectura actual si crecen el código, los
> expedientes y los usuarios. Complementa `ANALISIS_DESPLIEGUE.md`, que decide
> *dónde* se despliega; esto decide *qué hay que tocar* para que aguante.
>
> **Método y fecha:** lectura e instrumentación del repositorio a 2026-09-04.
> Las cifras de inventario y las referencias `fichero:línea` están verificadas
> contra el código. **Los tiempos y las cargas son aritmética sobre el código,
> no medición**: no hay todavía ninguna toma con datos reales. Donde se estima,
> se dice.

---

## 1. Qué NO es un problema

Verificado en código. Se documenta para no gastar esfuerzo aquí y para no
volver a plantearlo cada vez que alguien audita el proyecto desde fuera.

| Punto | Estado real |
|---|---|
| Application factory | Existe: `app/__init__.py:26`, extensiones desacopladas con `init_app()` |
| Capa de servicios | 63 ficheros, 14.655 líneas en `app/services/` |
| Blueprints por módulo funcional | `app/modules/` con auto-discovery metadata-driven (`ModuleRegistry`) |
| N+1 | Gestionado a conciencia: 95 `selectinload`/`joinedload` en 14 ficheros; la elección está razonada en `arbol_expediente.py:63-105` (ADR-016 §16) |
| Paginación | Patrón cursor `limit(limit + 1)` en 21 ficheros. **Ojo:** `.paginate()` de Flask-SQLAlchemy tiene 0 usos, pero no es un hallazgo — usan cursor propio, que para scroll infinito es mejor |
| Índices del camino caliente | `idx_solicitudes_expediente`, `idx_fases_solicitud`, `idx_tramites_fase`, `idx_tareas_tramite`, `idx_documentos_tarea_tarea` |
| Calendario de inhábiles | Se carga una vez y se pasa como `frozenset` (`plazos.py:317`); el porqué está escrito en `:414` |
| Rutas de documento | `Documento.ruta_absoluta()` es cálculo de cadenas sin I/O (ADR-032) → un listado no provoca tormenta de `stat` sobre el share |
| Reloj simulado | No toca disco en producción: `DEBUG=False` cortocircuita (`reloj_simulado.py:hoy()`) |
| Sesión | Cookie firmada; sin `SESSION_TYPE` ni almacén servidor → **la app ya es stateless** |
| Estado de proceso | Único mutable a nivel de módulo: `ModuleRegistry._metadata_cache` (`app/modules/__init__.py:21`), caché de lectura idempotente |

**Inventario:** `app/` ≈ 50.000 líneas · `tests/` 151 ficheros / 28.109 líneas ·
67 tablas · 110 FK · 114 relationships · 138 migraciones.

---

## 2. Frente mantenimiento

### 2.1 La suite de tests corre contra la BD de desarrollo

La viga que cede primero. No por el tamaño del código, sino porque **28.109
líneas de test —la segunda área más grande del repo, por delante de
`services`— dependen del estado de una máquina concreta.**

- `tests/conftest.py:8` — `create_app()` sin argumento → `DevelopmentConfig` →
  `DATABASE_URL` de desarrollo.
- **No existe `TestingConfig`** (0 ocurrencias en el repo).
- No hay `create_all()`: la suite asume esquema **y datos semilla** presentes.
  `_login_as` (`conftest.py:63`) busca `Usuario.siglas == 'CLG'` y devuelve
  `False` si no está.
- **174 `pytest.skip` repartidos por 52 de los 151 ficheros (34%).**
  `REGLAS_DESARROLLO.md` lo institucionaliza ("+ `pytest.skip` si no hay datos").
- `.github/workflows/` solo tiene `deploy-pages.yml`.

El aislamiento por SAVEPOINT (`conftest.py:30-41`, ganado a pulso en #641) es
bueno, pero resuelve el problema equivocado: aísla *transaccionalmente*, no
*ambientalmente*. La consecuencia es que **un tercio de la suite puede
autodesactivarse en silencio y salir verde igual**, y hoy nadie sabe cuántos de
esos 174 skips están saltando.

Cede cuando entra una segunda persona, o cuando se quiera usar la suite como
puerta del despliegue en contenedor (§9 de `ANALISIS_DESPLIEGUE.md`). Es además
**precondición de #317 / #332**: una CI que apunte a la BD de desarrollo no es
CI. Relacionado: #836 (el fixture `client` no pasa por `app_ctx`).

### 2.2 Duplicación `app/routes/api_*.py` ↔ `app/modules/*/`

**16 de 23 APIs tienen módulo gemelo**: `api_entidades`↔`entidades`,
`api_catalogo_plazos`↔`catalogo_plazos`, `api_expedientes`↔`expedientes`,
`api_proyectos`↔`proyectos`, `api_usuarios`↔`usuarios`,
`api_plantillas`↔`admin_plantillas`, `api_items_tecnicos`↔`items_tecnicos`,
`api_normas_variables`↔`normas_variables`,
`api_tipos_documentos`↔`tipos_documentos`, `api_efectos_plazo`↔`efectos_plazo`,
`api_firmantes_portafirmas`↔`firmantes_portafirmas`,
`api_mensajes_internos`↔`mensajes_internos`, `api_tablas_maestras`↔
`tablas_maestras`, `api_catalogo_requerimientos`↔`catalogo_requerimientos`, y
`api_seguimiento` + `api_huerfanos` ↔ `seguimiento_y_huerfanos`.

Sin gemelo: `administrativo`, `bitacora`, `escritos`, `municipios`,
`reglas_motor`, `requisitos_documentales`, `search`.

Cada dominio se toca en dos sitios con dos convenciones de blueprint distintas.
No duele con 22 módulos; duele con 40. El riesgo real no es el tecleo sino la
"tercera verdad" que `estadisticas_supervisor.py:16` presume de evitar.

**No hay acción propuesta todavía** — es un punto a vigilar, no una tarea.

### 2.3 138 migraciones escritas a mano sobre 67 tablas

`flask db migrate` está prohibido por un bug de `include_schemas`
(`REGLAS_DESARROLLO.md`). Es un impuesto por cambio que crece con el número de
tablas, con la causa raíz sin arreglar. Mínimo razonable: un check de deriva
modelo↔migración en CI, aunque el autogenerate siga prohibido.

### 2.4 `create_app()` — no trocear todavía

306 líneas, ~30 blueprints legacy, 4 context processors, 6 filtros Jinja. Pero
solo 4 commits en todo el historial visible lo tocan, y **ninguno para añadir un
blueprint**: lo nuevo entra por `ModuleRegistry` sin tocar código central. El
troceo no está justificado hoy. Revisar si vuelve a crecer.

---

## 3. Frente rendimiento

### 3.1 Panel del supervisor — degradación gradual con el dato

`estadisticas_supervisor.calcular_estadisticas()`:

- `:65-70` carga **todos** los expedientes sin límite. Es la única consulta del
  sistema sin paginar.
- `:81-82` itera y llama `construir_arbol(exp.id)` **una vez por expediente**.
- Cada árbol son ~12-15 consultas (la cadena `selectinload` de
  `arbol_expediente.py:75-99`).

Estimación: 100 expedientes ≈ 1.500 consultas por carga; 1.000 ≈ 15.000.

**Ya está documentado por el equipo** (`estadisticas_supervisor.py:19-23`,
ADR-028 §2), con el remedio diseñado —denormalizar el estado agregado— y la
regla correcta: *"NO se optimiza a ciegas: medir primero"*. **Lo que falta no es
la solución, es el número:** a cuántos expedientes deja de ser usable.

### 3.2 Concurrencia: el techo son los workers, no la CPU

Coste de generar un escrito, leído del código:

- **No hay LibreOffice en runtime.** `soffice` aparece 8 veces en el repo,
  ninguna en `app/` (solo `tests/` y `scripts/fabricar_*`).
- Ensamblado = `zipfile` + `lxml` sobre `content.xml`/`styles.xml`
  (`generador_escritos_odt.py:100-113`) → centenares de ms, no segundos.
- Contexto = puñado de queries ORM (`escritos.py:192` + `context_builders/`).
- Escritura = `open(ruta,'wb')` sobre el share (`generador_escritos.py:187`).

**El riesgo no es el promedio, es la cola.** Un montaje CIFS `hard` (el defecto)
reintenta indefinidamente: si el share hipa, el worker se queda colgado. Con
workers síncronos y los 4-6 que planifica `ANALISIS_DESPLIEGUE.md:206`, **el
techo de peticiones simultáneas es 4-6 para toda la aplicación**.

Y la exposición es más amplia que "generar escrito": cuelga igual cualquier
petición que toque el share — `os.scandir` del explorador
(`expedientes/routes.py:630`, `admin_plantillas/routes.py:316`),
`os.path.isfile` (`routes.py:1100`), `resolver_url()`, extracción de texto. No
hacen falta seis generaciones simultáneas: bastan seis personas navegando
documentos. **Y los reintentos aceleran el colapso**, porque cuando la app no
responde la gente vuelve a pulsar y cada clic ocupa otro worker.

### 3.3 El timeout no se puede poner en Python — va en el montaje

Punto técnico crítico, porque la implementación evidente no funciona.

Un hilo bloqueado en `write()` contra un CIFS montado `hard` está en espera
**ininterrumpible** (estado D en Linux):

- `signal.alarm` / SIGALRM **no dispara**: el manejador de Python solo corre
  cuando el intérprete recupera el control, y no lo recupera hasta que la
  syscall retorne.
- `ThreadPoolExecutor(...).result(timeout=N)` es **peor que no hacer nada**:
  devuelve el control pero el hilo sigue colgado ocupando plaza del pool para
  siempre. Convierte "6 workers bloqueados" en "6 hilos filtrados" — mismo
  apagón, más difícil de diagnosticar.
- En Linux ni `SIGKILL` saca a un proceso de estado D.

**Solo `soft` funciona:** el kernel se rinde tras el timeout y devuelve `EIO`,
que en Python es un `OSError` capturable → 503 con mensaje. Contrastar las
opciones exactas (`soft`, `timeo`, `retrans`, `handletimeout`) contra el
`mount.cifs(8)` del kernel que se despliegue.

Complemento obligatorio: **escribir a temporal y renombrar**, para no dejar un
`.odt` truncado en el share si la escritura muere a medias.

Nota para la decisión pendiente §8.1 de `ANALISIS_DESPLIEGUE.md`: accediendo a
una UNC desde Windows/WSL2 estas palancas son peores o inexistentes. Es un
argumento adicional a favor de la vía B (Linux nativo).

### 3.4 Principio: no convertir el fallo de una dependencia en fallo propio

Hay que mantener separadas dos cosas que parecen la misma:

- **Share lento** → problema de sistemas. Arreglar red o almacenamiento;
  parchearlo en la app sería maquillaje que impide que se arregle nunca.
- **Share no disponible** → resiliencia de aplicación. Ninguna obra de sistemas
  lo elimina: habrá mantenimiento, failover, rotación de credenciales.

**El proyecto ya tomó esta decisión para Postgres:** `app/__init__.py:290-304`
captura `OperationalError`/`ProgrammingError` y devuelve un 503 limpio;
`REGLAS_DESARROLLO.md` lo eleva a regla general ("capturar, degradar, loguear,
no propagar"); y `ANALISIS_DESPLIEGUE.md:185-187` ya pide lo mismo para el share
con esas palabras ("misma filosofía defensiva que ya se aplica al catálogo").
Aplicar esto al share no es un parche nuevo: es extender a la segunda
dependencia remota un principio que ya está escrito para la primera.

**Condición innegociable:** el código defensivo **debe registrar la duración** de
las operaciones de share. Si no, oculta el problema de sistemas en vez de
exponerlo. Con medición, "el share va lento" deja de ser una degradación
invisible y pasa a ser un hecho que se le puede llevar a IT.

### 3.5 Patrones de industria y qué transfiere

1. **Espera acotada en toda llamada remota** — universal, no negociable.
2. **Bulkhead / compartimentación** (Hystrix, Netflix): pool acotado por
   dependencia, para que agotar uno no consuma toda la capacidad. Es el que
   responde directamente al riesgo de §3.2: un semáforo de N plazas alrededor de
   las operaciones de share hace que una caída degrade *una función* en vez de
   tumbar la aplicación. ~20 líneas. **Máximo valor por esfuerzo.**
3. **Circuit breaker** — corta la pila de reintentos. No hace falta todavía.
4. **No escribir en un FS de red desde la capa web**: almacén de objetos con API
   HTTP (S3/MinIO/Azure Blob). Nombra la incomodidad de fondo con precisión:
   **un cliente HTTP tiene timeouts, backoff y pool en su contrato; una syscall
   POSIX de fichero no tiene timeout en el suyo.**

**Proporcionado aquí:** opciones de montaje + semáforo + `gthread` + medición.
No: circuit breaker. No: cola de tareas. No: almacén de objetos.

### 3.6 `explorer /select` en el servidor — rompe con el segundo usuario

`app/modules/expedientes/routes.py:1106` y `:1137`:

```python
subprocess.Popen(f'explorer /select,"{ruta_abs}"', shell=True)
```

Abre el Explorador **en el servidor**. El propio docstring lo reconoce
("requiere que Flask corra en el mismo PC que el navegador"). Con varios
usuarios: en Linux no existe `explorer`; en Windows abre una ventana en el
escritorio del servidor que nadie ve, y deja un proceso por clic. Hay que
sustituirlo por una descarga vía `send_file`. **No figura en los artefactos a
crear de `ANALISIS_DESPLIEGUE.md §9`.**

---

## 4. Sacar la generación de documentos del ciclo de petición

Por niveles, del más barato al más caro. **La recomendación es hacer 1-3 antes
de desplegar y no hacer el 4 hasta que una medición lo pida.**

1. **Workers con hilos** — `gunicorn -w 4 --threads 8 --worker-class gthread`.
   De 4-6 peticiones simultáneas a 32. **Verificado seguro**: el único estado
   mutable compartido es `ModuleRegistry._metadata_cache`, y la sesión de
   Flask-SQLAlchemy ya es thread-local.
2. **Pool de conexiones** — con hilos deja de ser opcional. Hoy hay **cero
   configuración** (`ENGINE_OPTIONS`, `pool_pre_ping`, `pool_recycle`: 0
   ocurrencias). Sin `pool_pre_ping`, un cortafuegos corporativo que mate TCP
   ocioso produce 500 intermitentes tras periodos de inactividad.
   `pool_size=10, max_overflow=5, pool_pre_ping=True, pool_recycle=1800` →
   4×(10+5) = 60 conexiones, con `max_connections` de Postgres a 150.
3. **Montaje `soft` + semáforo + medición** (§3.3-3.5).
4. **Asíncrono de verdad — solo si medir lo pide.** El diseño actual lo pone
   fácil: `_respuesta_generado` (`api_escritos.py:232`) devuelve metadatos
   (`doc_id`, `nombre_fichero`, `ruta`), **no los bytes**. Migración: `202` +
   `Documento` en estado `GENERANDO` + polling (ya existe para el semáforo del
   motor). Para la cola, **una tabla en el Postgres que ya hay** con
   `SELECT ... FOR UPDATE SKIP LOCKED` — no Redis ni Celery: cero
   infraestructura nueva que operar en un PC dedicado sin equipo de sistemas.

### 4.1 Descartado: montar el documento en el cliente

Idea evaluada y descartada **para el camino autoritativo**: que el servidor
recopile los tokens y el navegador ensamble el `.odt`/`.docx`.

Mueve el coste barato y deja el caro:

- **Lo que quita:** ~200 ms de CPU en un i7-12700 de 12 núcleos. Saturar esa CPU
  exigiría ~60 generaciones por segundo sostenidas.
- **Lo que no quita:** el navegador no puede escribir en el share, así que el
  documento vuelve al servidor y se escribe igual. La escritura CIFS —la única
  parte con cola sin techo— queda intacta, y encima se añaden dos viajes de red
  durante los cuales el worker sigue ocupado.
- **Lo que cuesta:** reimplementar en JS los 544 lines de
  `generador_escritos_odt.py` (inserción de fragmentos a nivel de bloque,
  renombrado de estilos con prefijo `frg` para no colisionar con los P1/T1/L1 de
  LibreOffice, namespaces), más el camino `.docx` de `docxtpl` con docxtemplater
  (licencia comercial en varias features) y un Jinja2 de navegador (Nunjucks no
  es Jinja2 en los bordes, y `validar_plantilla` —`generador_escritos.py:192`—
  valida con el Jinja2 real).
- **Segunda fuente de verdad** para el código jurídicamente más sensible del
  sistema, no cubrible por la suite pytest.
- **Trazabilidad:** son actos administrativos. Ensamblados en el navegador del
  tramitador, con el bundle JS que tenga cacheado, "qué versión produjo este
  documento" se queda sin respuesta. `Documento.hash_md5` acredita los bytes
  recibidos, no el procedimiento que los generó.
- No compone con el nivel 4: un trabajo en segundo plano no corre en un
  navegador cerrado.

**Dónde la idea sí vale:** el *preview*. `/api/escritos/preview`
(`api_escritos.py:124-152`) hoy devuelve solo `campos`, nombre y ruta, sin
render; un preview WYSIWYG en cliente sería legítimo —desechable, no
autoritativo, muy interactivo—. Segundo candidato: los `.docx` de #608, que el
propio código declara "auxiliar de trabajo, no un acto" y que no disparan cambio
de estado (`react-src/src/expediente-arbol/api.js:256`).

---

## 5. Ejercicio de tensión: 1.000 usuarios simultáneos

No es un escenario real —es más gente de la que puede tocar estos expedientes en
toda Andalucía—, pero señala qué piezas son portantes.

**Datos del repo que deciden la respuesta:**

- Polling a **60 s**: `motor-estado.js:7` y `mensajes-badge.js:12`
  (`INTERVALO_MS = 60000`), contra `/configuracion-motor/estado` y
  `/api/mensajes-internos/badge`.
- **Sesión stateless** (§1) → escala horizontalmente sin tocar nada.

**Carga estimada:** 1.000 × 2 polls / 60 s = **33 req/s**, más interacción real
(≈15% activos, 1 acción/25 s) ≈ 6 req/s → **≈40 req/s sostenidos, el 85% de
ellos polling**. La concurrencia necesaria es `req/s × latencia`: a 50 ms son 2
peticiones simultáneas; a 200 ms, 8. Con `gthread` 4×8 = 32 plazas, sobra. El
overhead de Flask (~1 ms) es ruido.

**Postgres** no se despeina por volumen de consultas; el riesgo es la
**topología de conexiones**, porque usa un proceso del SO por conexión. Una
instancia son 60; tres, 180. Pasando de ~200 → **PgBouncer en modo transacción**.

**Lo que sí se rompe, y no es Flask ni Postgres:**

1. El panel del supervisor (§3.1).
2. **Los context processors pasan a ser el camino más caliente**:
   `inject_modo_motor` (`app/__init__.py:142-147`) ejecuta
   `ConfiguracionSistema.get()` en **cada petición autenticada** para un valor
   que cambia una vez al mes → 40 consultas/s regaladas. Ídem el chequeo de
   `DiaInhabil` para admins en `inject_module_nav`. Caché trivial.
3. **Los dos endpoints de polling pasan a ser lo más ejecutado del sistema**
   (33 req/s constantes). Tienen que ser lo más barato que haya: el badge
   necesita índice para su COUNT, y el estado del motor debería salir de caché.

**Escalera:** (1) ya hecho: stateless + APIs paginadas · (2) cachear
config/catálogos, indexar el badge, `gthread` + pool · (3) denormalizar el
dashboard · (4) nginx sirviendo estáticos + N instancias · (5) PgBouncer por
encima de ~200 conexiones · (6) SSE en lugar de polling.

Sobre el (6): **el polling es lo único de la arquitectura que crece linealmente
con los usuarios aunque nadie haga nada.** Irrelevante a 1.000; sería lo primero
que habría que cambiar a 10.000. Los propios comentarios de `motor-estado.js:1-5`
anotan que no hay infraestructura de push.

**Veredicto:** de las seis piezas portantes, **cinco son configuración y solo una
es código** (el dashboard), que además ya está diagnosticada con remedio escrito.
