# scripts/expedientes_dummy/interfaz/

Expedientes-tipo **por la interfaz** (#1106): guiones [Playwright](https://playwright.dev/python/) que tramitan un
expediente como lo haría una persona. Son la contraparte de los módulos de `scripts/expedientes_dummy/`, que
construyen el mismo escenario **por la API** (servicios y endpoints desde Python, #814).

Herramienta **a demanda**: fuera de pytest y de la semilla de tests.

## Para qué sirven

1. **Como una prueba con escenarios reales.** La pregunta que contestan es «¿lo que he tocado se estropea en la
   interfaz?». Si se estropea por un bug, el guion lo localiza y se corrige el producto; si es un cambio legal, se
   actualiza el guion. Que se «desgaste» con la aplicación es el beneficio, no un riesgo: es como un test, pero con
   escenarios reales y no inventados. Nada avisa solo (no está en la semilla): se ejecuta cuando se quiere saber.
2. **Tener un expediente a mano** sin tocar la BD por debajo, y el «Ensayo» del tramo 4 de `docs/CONTEXTO_ACTUAL.md`.
3. **Base de vídeos tutoriales** (fase posterior): reproducir la interacción de forma sistemática permite grabarla y
   editarla con pausas y rótulos. Cada paso tiene nombre y pasa por `Sesion.paso()`, que es donde colgar el rótulo y
   la pausa; con `--desde` / `--hasta` un minitutorial puede ser un tramo del escenario.

## Ejecutar

Desde la **raíz del repositorio**, con la aplicación arrancada. Una sola vez, `playwright` (no está en
`requirements.txt` a propósito) y su navegador:

```bash
venv/Scripts/python.exe -m pip install playwright
venv/Scripts/python.exe -m playwright install chromium
```

```bash
venv/Scripts/python.exe -m scripts.expedientes_dummy.interfaz.analisis_doc_dos_vueltas --lista
venv/Scripts/python.exe -m scripts.expedientes_dummy.interfaz.analisis_doc_dos_vueltas --nuevo --usuario <SIGLAS> --password <CLAVE>
venv/Scripts/python.exe -m scripts.expedientes_dummy.interfaz.analisis_doc_dos_vueltas --visible --lento 400 --hasta vincular_presentacion
```

| Opción | Qué hace |
|---|---|
| `--lista` | muestra los pasos y sale |
| `--nuevo` | empieza un expediente nuevo: recicla el de la ejecución anterior (`--sin-reciclar` lo evita) y arranca en el alta |
| `--desde X` / `--hasta Y` | primer y último paso; sin `--desde` se retoma en el primero que falta |
| `--usuario`, `--password`, `--rol` | credenciales (o las variables `BDDAT_UI_USUARIO` y `BDDAT_UI_PASSWORD`). Con varios roles, `--rol` elige (login de dos pasos). En la BD de la nube, los usuarios de la semilla (`scripts/nube/README.md`) |
| `--url` | dirección de la aplicación (`http://127.0.0.1:5000`) |
| `--visible`, `--lento MS` | ver el navegador y pausar entre acciones (por defecto, en segundo plano) |
| `--dias N` | cuántos días atrás empieza el calendario (45); la fecha base es hoy − N |
| `--responsable`, `--titular` | texto del desplegable o de la lista del alta (por defecto, el responsable es el usuario del login y el titular, el primero de la lista) |

Salidas: `docs_prueba/ui_dummy/<tipo>/` (git la ignora): `estado.json` (el expediente y los pasos hechos, con los ids
de lo creado), `diario.json`, `capturas/` (una por paso y una `FALLO-…` si algo falla) y `aria-*.yml`.

**Cada ejecución CREA DATOS REALES y deja fijado el reloj de desarrollo** en la fecha de la última respuesta del
titular («Usar fecha real» en la barra superior lo quita). Los pasos son sucesivos sobre el mismo expediente y no se
repiten sobre él. Si un paso falla a medias, lo ya hecho en él no se deshace: se arregla a mano (o se apunta el paso
como hecho en `estado.json`) antes de reanudar.

### Requisitos de la BD

- Migraciones al día (`flask db current` = head). Sin ellas, p. ej., falta `diagnosticos.sentido`, el listado del pool
  da 503 y el diagnóstico falla.
- Las plantillas DEMO que usa el escenario (las registra el script, se quitan con `--quitar`; ver
  `scripts/plantillas_demo.py`):
  `venv/Scripts/python.exe scripts/plantillas_demo.py --claves REQUERIMIENTO_SUBSANACION COMUNICACION_INICIO_ADMISION`
- El tipo de expediente «Distribución», instrumento `EXENTO`, provincia Sevilla, municipio «Mairena del Aljarafe», tipo
  de solicitud `AAP+AAC` y un titular. Si faltan, el paso del alta falla con un mensaje y una captura.

En la nube: `CHROMIUM_PATH=/opt/pw-browsers/chromium` (el Chromium del contenedor) y, tras
`bash scripts/nube/arrancar_app.sh`, los usuarios de la semilla de la nube.

## Estructura

```
interfaz/
├── lib/              común; NO importa `app`: vale contra cualquier URL
│   ├── sesion.py       navegador, login de dos pasos, diario de pasos, capturas, opciones comunes
│   ├── contexto.py     sesión + expediente + ids de lo creado, y su estado en disco
│   ├── arbol.py        lienzo, inspector y despensa; subidas, vínculos, checklist, reloj, plazos
│   ├── documentos.py   los PDF dummy (`pdf_dummy`), en memoria y distintos en cada subida
│   ├── pasos.py        piezas reutilizables entre expedientes-tipo
│   ├── alta.py         el formulario de alta, parametrizable (`DatosAlta`)
│   └── ejecutor.py     --lista / --desde / --hasta / --nuevo
├── explorar.py       captura y árbol de accesibilidad de una ruta, para escribir guiones nuevos
└── analisis_doc_dos_vueltas/
    ├── escenario.py    la historia: marca, parámetros, tipos de documento, datos del alta y lista de pasos
    └── __main__.py     el punto de entrada (`-m …analisis_doc_dos_vueltas`)
```

La librería no usa `_comun.py` porque este importa `app` y necesita la BD en la misma máquina; la de interfaz solo
necesita la URL. Los documentos son los de `scripts/generar_documentos_dummy.py`: sin carpeta de PDF.

## Escribir un expediente-tipo nuevo

1. Una carpeta nueva con `__init__.py`, `escenario.py` y `__main__.py` (copiar el de `analisis_doc_dos_vueltas/`).
2. `escenario.py` expone `CODIGO`, `CARPETA`, `MARCA`, `DIAS_ESCENARIO`, `datos_alta(fecha_base, opts)` y `PASOS`
   (`[(nombre, función(c)), …]`, sin el alta). Un paso es una función que recibe el `Contexto` y compone piezas de
   `lib/pasos.py` (o de `lib/arbol.py`); cada pieza abre sus acciones con `c.s.paso(nombre, estrategia)`.
3. **Marca propia** en las observaciones: `[DUMMY:<CODIGO>_UI]`. La semilla de tests busca su expediente por
   `LIKE '[DUMMY:<CODIGO>]%'`; con la misma marca que el script de la API creería que ya existe y no lo construiría.
4. **Ninguna fecha absoluta**: la base es hoy − `DIAS_ESCENARIO`. Las fechas de respuesta salen de la «Fecha límite» que
   enseña el inspector (`responder_en_plazo`), nunca de un número de días escrito a mano. Una fecha administrativa
   futura es un invariante del modelo desde #824.
5. **Los tipos de documento, por su NOMBRE del catálogo** (el de los desplegables y el título de los requisitos del
   checklist): es lo único del escenario que depende de datos del catálogo y se declara en una tabla al principio.
6. Para localizar algo nuevo, `explorar.py` da su árbol de accesibilidad (`aria-<nombre>.yml`); si no hay forma
   accesible, es un hallazgo para #1105, no un `data-testid`:

   ```bash
   venv/Scripts/python.exe -m scripts.expedientes_dummy.interfaz.explorar --usuario <SIGLAS> --password <CLAVE> --ruta "expedientes/{id}/arbol" --nombre arbol
   ```

   La ruta va **sin barra inicial**: Git Bash (Windows) convierte un argumento que empieza por `/` en una ruta de disco.
   `{id}` es el expediente de la última ejecución del guion.
7. Mantener el mismo nombre de paso y los mismos parámetros que el script de la API cuando haga lo mismo: dos caminos
   que construyen lo mismo terminan divergiendo. La comprobación (abajo) es manual.

## Cómo se localiza (sin `data-testid`)

Todo con roles, etiquetas, ids de contenedor y los `data-id` de React Flow. Lo que costó y cómo se resolvió; los
puntos donde convendría arreglar la accesibilidad del producto están en #1105.

| Pieza | Cómo |
|---|---|
| Actuar sobre un nodo | `…/arbol?nodo=<id>`, no pinchar el lienzo (el inspector abierto tapa el centro y a veces la esquina de los nodos). El id de lo recién creado se lee de esa URL: al crear, el inspector salta al nodo nuevo |
| La solicitud | su id NO es el del expediente: se lee del lienzo (`data-id` que empieza por `solicitud-`) |
| Crear fase, trámite o tarea | despensa: los tipos son `<div>`, no botones (`get_by_text(exact)` dentro del inspector) + «Crear». El aviso «Elemento creado» se cierra con su botón para que el siguiente no se confunda con él |
| Selectores del alta (provincia, municipio, titular) | `SelectorBusqueda` por id de contenedor; la lista se reinserta en `<body>` (`ul.sb-lista.show`) y sus `<li>` no tienen roles |
| Fechas | `EntradaFecha` por id de contenedor (`#ef-fecha`, `#ef-registro`): el mismo placeholder sale dos veces |
| Requisito del checklist | fila `div.border-bottom` con el título exacto en `.fw-semibold` y el estado en `.badge` |
| Documentos de una tarea | clic en el documento del pool (`aria-pressed`) y «+ Consumido» / «+ Producido»; luego «Guardar». «Subir y vincular» solo sube y deja el documento seleccionado |
| Subir el mismo contenido otra vez | la aplicación avisa «Este fichero ya está…» y pide «Subir igualmente»: cada subida lleva un comentario final distinto |
| NOTIFICAR | el oficio entra como consumido y el justificante como producido (su tipo fija el canal); el «Resultado» se marca en una segunda edición, con su propio «Guardar» («Notificación registrada») |
| ESPERAR_PLAZO | el oficio consumido dispara el plazo; el inspector enseña «Fecha límite: aaaa-mm-dd» |
| Tras «Guardar» | el árbol se repinta y el inspector puede cerrarse: se reabre la tarea antes de comprobar o de seguir |
| Fin del diagnóstico | el botón pasa a «Produciendo…» al instante; el fin es «Documento producido — el resultado queda bloqueado» |
| Escrito generado | las plantillas del desplegable cargan tras abrir el editor, y el aviso «Escrito generado» a veces no se ve: el fin es el enlace al `.odt` en la lista. El `.odt` se lee como zip (`unzip` no existe en Windows) |
| El listado del pool | puede dar 503 sin que la subida falle (BD sin migrar): no se usa para comprobar |
| Tensión del proyecto | la columna es numérica: el campo devuelve «20.00» |

## Reciclado

`limpiar_reciclables.py` es genérico: no conoce ningún expediente-tipo, trabaja sobre `[RECICLAR]` y recorre y borra lo
que depende del expediente. Con `--nuevo`, el guion marca `[RECICLAR]` en las observaciones de la solicitud del
expediente de la ejecución anterior (el campo es editable desde el inspector), **solo si empiezan por la marca del
escenario**. Después:

```bash
venv/Scripts/python.exe scripts/expedientes_dummy/limpiar_reciclables.py            # informe, sin borrar
venv/Scripts/python.exe scripts/expedientes_dummy/limpiar_reciclables.py --borrar   # borrado real (pide confirmación)
```

Límite: un expediente creado desde otra máquina, o sin `estado.json`, no se recicla solo.

## Comprobar que la interfaz y la API construyen lo mismo

Con el script de la API (`scripts/expedientes_dummy/analisis_doc_dos_vueltas.py`) y este guion ya ejecutados, el
árbol ha de coincidir (los AT son los de cada uno; la interfaz añade el borrador `.odt` de cada ELABORAR):

```sql
SELECT tt.codigo AS tramite, ta.codigo AS tarea,
       sum((e.numero_at = <AT_API>)::int) AS api, sum((e.numero_at = <AT_UI>)::int) AS interfaz
FROM solicitudes s JOIN expedientes e ON e.id = s.expediente_id
JOIN fases f ON f.solicitud_id = s.id JOIN tramites t ON t.fase_id = f.id
JOIN tipos_tramites tt ON tt.id = t.tipo_tramite_id
JOIN tareas a ON a.tramite_id = t.id JOIN tipos_tareas ta ON ta.id = a.tipo_tarea_id
WHERE e.numero_at IN (<AT_API>, <AT_UI>)
GROUP BY tt.codigo, ta.codigo ORDER BY tt.codigo, ta.codigo;

SELECT e.numero_at, n.canal, n.resultado, count(*)
FROM notificaciones n JOIN tareas a ON a.id = n.tarea_id JOIN tramites t ON t.id = a.tramite_id
JOIN fases f ON f.id = t.fase_id JOIN solicitudes s ON s.id = f.solicitud_id
JOIN expedientes e ON e.id = s.expediente_id
WHERE e.numero_at IN (<AT_API>, <AT_UI>) GROUP BY 1, 2, 3 ORDER BY 1;
```

## Fuera de este guion (decisiones aplazadas)

- `fecha_hoy` de los escritos generados sale de `date.today()`, no del reloj de desarrollo: el borrador de la 2.ª
  vuelta dice la fecha de hoy aunque el reloj esté semanas atrás.
- Las plantillas `DEMO_` solo usan la capa 1 (`numero_at`, `titular_nombre`, `fecha_hoy`): no ejercitan los tokens del
  context builder (`defectos_*`, `actos`).
