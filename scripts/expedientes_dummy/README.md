# scripts/expedientes_dummy/

Expedientes-tipo: escenarios de tramitación **reproducibles**, construidos por el circuito real
de la aplicación (servicios y endpoints, nunca `INSERT` sueltos).

Cada uno tiene doble vida (#849):

- **En desarrollo** — se ejecutan como programa contra la base de desarrollo, para tener a mano
  un expediente donde trabajar un apartado concreto de la tramitación.
- **En tests** — `scripts/semilla_test.py` los invoca con `main(app, efectos_desarrollo=False)`
  y se convierten en la semilla de negocio de la base de tests.

---

## Catálogo de expedientes-tipo

| Código | Propósito | Alcance |
|---|---|---|
| `ANALISIS_DOC_DOS_VUELTAS` | Análisis documental con respuesta del titular dentro de plazo y dos vueltas de subsanación | Termina con `ANALISIS_SOLICITUD` completa y pendiente de cierre |
| `CONSULTAS_VARIOS_ESTADOS` | Fase de consultas con las tres separatas enviadas y cada organismo en un estado distinto | Termina con `CONSULTAS` abierta — expediente incompleto a propósito |

### ANALISIS_DOC_DOS_VUELTAS

`analisis_doc_dos_vueltas.py` — #814

Trámite `ANALISIS_DOCUMENTAL` con dos vueltas de subsanación, respuesta del titular siempre
dentro de plazo, sin fase de Información Pública / Consultas ni figura ambiental (AAP+AAC,
proyecto **exento** de instrumento ambiental).

No abre la fase `RESOLUCION`: cerrar la fase y resolver es tramitación posterior, y con el
invariante de precedencia de #823 abrirla con la fase anterior sin cerrar está prohibido.

| Parámetro | Valor | Por qué |
|---|---|---|
| `DIAS_ESCENARIO` | 45 | Días naturales que dura el escenario completo. Dos vueltas de requerimiento son unos 20; el resto es holgura para tramos con muchos festivos |
| `MARGEN_RESPUESTA_HABILES` | 3 | Días hábiles antes del vencimiento **real** en que responde el titular. El margen es lo único fijo: la fecha sale del plazo que diga el catálogo, no de un número escrito a mano |

```bash
venv/Scripts/python.exe scripts/expedientes_dummy/analisis_doc_dos_vueltas.py
```

### CONSULTAS_VARIOS_ESTADOS

`consultas_varios_estados.py` — #862

Línea aérea de 66 kV entre dos subestaciones en suelo rústico de Jerez de la Frontera
(AAP+AAC, un solo municipio), **exenta** de instrumento ambiental por longitud, tensión y
suelos que recorre: sin figura ambiental y sin información pública. El titular presenta la
declaración responsable de no necesidad de DUP. El trazado cruza una carretera provincial y
una línea de ferrocarril, así que se consulta a tres organismos.

La fase `ANALISIS_SOLICITUD` se recorre **sin defectos** —todos los requisitos aplicables
cubiertos en el primer ANALIZAR, ninguna vuelta de subsanación— y se comunica el inicio. La
fase `CONSULTAS` queda **abierta**: es un expediente incompleto a propósito, porque lo que
hace falta para trabajar en consultas es esa foto, no un expediente terminado.

Estado a día de hoy, que son 40 días hábiles desde que se notificaron las separatas (el plazo
del art. 131.1 son 30 días hábiles, así que ya venció para quien no contestó):

| Organismo | Estado | Qué ejercita |
|---|---|---|
| Ayuntamiento de Jerez | Silencio: `ESPERAR_PLAZO` **vencido**, sin ANALIZAR | Conformidad tácita pendiente de reconocer (caso A de ADR-011 §6) |
| ADIF | Ciclo cerrado: respuesta con condicionados → traslado al titular → aceptación en plazo. Organismo en `cerrado_con_condicionados` | Caso B completo, separata + traslado |
| Diputación de Cádiz | Informe desfavorable trasladado al titular; su `ESPERAR_PLAZO` **sigue corriendo**. Organismo sin `resultado` (en curso) | Traslado vivo, con el plazo de 15 días del art. 131.3 a punto de vencer |

| Parámetro | Valor | Por qué |
|---|---|---|
| `HABILES_DESDE_NOTIFICACION_SEPARATAS` | 40 | El ancla. El escenario se construye hacia atrás desde aquí, no hacia delante desde el alta: es este número el que decide qué plazos han vencido en la foto |
| `MARGEN_ADIF_HABILES` | 15 | ADIF contesta pronto para que quepan su traslado y la respuesta del titular dentro de la misma ventana |
| `MARGEN_DIPUTACION_HABILES` | 3 | Apura el plazo, y por eso su traslado sigue vivo hoy |
| `MARGEN_TITULAR_HABILES` | 5 | Respuesta del titular al traslado de ADIF |
| `HABILES_HASTA_TRASLADO` | 2 | De recibir la respuesta del organismo a notificar el traslado |

Al terminar **borra el reloj de desarrollo**: este expediente se lee «a fecha de hoy», y
dejarlo congelado en la última fecha del escenario haría que el traslado de la Diputación no
se viera correr.

```bash
venv/Scripts/python.exe scripts/expedientes_dummy/consultas_varios_estados.py
```

Dos cosas que este escenario dejó a la vista y no son suyas:

- **La declaración responsable de no DUP no se casa con nada.** El requisito `DR_NO_DUP` del
  catálogo está condicionado a `solicitud_incluye_dup = true`, así que no aparece en el
  checklist de una solicitud sin DUP. El documento entra al pool y ahí se queda.
- **Dos documentos de igual contenido comparten fichero en el pool** (misma `url`, misma
  entrada física: la ingesta no reescribe un duplicado exacto), y al llevarse el primero a su
  carpeta ESFTT el segundo se queda apuntando a un fichero que ya no existe. Por eso el script
  sube y vincula cada separata organismo a organismo en vez de subir las tres de golpe.

---

## Cómo localizar un expediente-tipo en la base

No hay catálogo de ejecuciones que mantener: **la base es la fuente de verdad**. Cada expediente
generado marca `Solicitud.observaciones` con `[DUMMY:<CODIGO>]` seguido de su propósito, y una
query por esa marca devuelve solicitud y expediente de una tacada.

```sql
-- Un expediente-tipo concreto (incluye los de ejecuciones anteriores aún vivos)
SELECT e.numero_at, e.id AS expediente_id, s.id AS solicitud_id, s.observaciones
FROM solicitudes s
JOIN expedientes e ON e.id = s.expediente_id
WHERE s.observaciones LIKE '[DUMMY:ANALISIS_DOC_DOS_VUELTAS]%'
ORDER BY e.numero_at;

-- Todos los expedientes dummy vivos, de cualquier tipo
SELECT e.numero_at, s.observaciones
FROM solicitudes s JOIN expedientes e ON e.id = s.expediente_id
WHERE s.observaciones LIKE '[DUMMY:%' ORDER BY e.numero_at;

-- Los marcados para reciclar (candidatos de limpiar_reciclables.py)
SELECT e.numero_at, s.observaciones
FROM solicitudes s JOIN expedientes e ON e.id = s.expediente_id
WHERE s.observaciones LIKE '[RECICLAR]%' ORDER BY e.numero_at;
```

La ventana de calendario en la que vive un expediente sale de sus propios documentos, que es el
dato que hace falta para colocar el reloj de desarrollo (`scripts/reloj_dev.py`, #820) antes de
trabajar con él:

```sql
SELECT min(d.fecha_administrativa), max(d.fecha_administrativa)
FROM documentos d WHERE d.expediente_id = <id>;
```

---

## Scripts

### analisis_doc_dos_vueltas.py — expediente-tipo

Ver el catálogo de arriba. Reejecutable: si ya existe un expediente con esta marca, sus
observaciones pasan a `[RECICLAR] …` (un `UPDATE` de una columna, sin cascadas) y se crea uno
nuevo desde cero.

### limpiar_reciclables.py — borrado de lo marcado

Contrapartida genérica: los scripts de expediente-tipo nunca borran, solo marcan; este borra lo
marcado. No conoce ningún expediente-tipo concreto —trabaja sobre `[RECICLAR]`—, así que sirve
para cualquiera de esta carpeta.

SQL directo, a diferencia de los scripts de creación: esto es mantenimiento de una base de
desarrollo, no un acto de tramitación. El circuito real no puede hacerlo, porque
`check_invariante('BORRAR', …)` bloquea a propósito la evidencia notificada (#722), que es justo
lo que hay que retirar.

Salvaguardas:

- **Dry-run por defecto**: sin `--borrar` solo informa.
- Un expediente solo entra si **todas** sus solicitudes están marcadas.
- Los ficheros del pool (`FILESYSTEM_BASE/AT-N/`) solo se tocan con `--con-ficheros`.
- Comprobación dinámica del esquema antes de tocar nada: si alguien añade una tabla que apunta a
  las que aquí se borran y no está contemplada, aborta en vez de dejar filas colgando.
- Una transacción por expediente: si algo falla, ese expediente queda intacto.

```bash
# Informe, sin borrar nada
venv/Scripts/python.exe scripts/expedientes_dummy/limpiar_reciclables.py

# Borrado real (pide confirmación; --si la salta)
venv/Scripts/python.exe scripts/expedientes_dummy/limpiar_reciclables.py --borrar
venv/Scripts/python.exe scripts/expedientes_dummy/limpiar_reciclables.py --borrar --at 12,13 --si
venv/Scripts/python.exe scripts/expedientes_dummy/limpiar_reciclables.py --borrar --con-ficheros --si
```

---

## Reglas al escribir un expediente-tipo nuevo

Heredadas de #814 y de los issues que las destaparon. No son estilo: cada una viene de un fallo
real.

| Regla | Por qué |
|---|---|
| **Circuito real siempre** — `app.services.alta_expediente` para el alta, `mutaciones_arbol` para fase/trámite/tarea (pasa por `motor_reglas.evaluar`), endpoints reales para checklist y diagnóstico, subida multipart para documentos | Un escenario construido a mano deja de parecerse a la aplicación en cuanto la aplicación cambia. #428: la copia del bloque ORM del wizard se quedó atrás y el expediente nacía sin ancla documental |
| **Ninguna fecha absoluta** — base anclada a `date.today()` menos lo que dura el escenario | Ningún documento nace con fecha futura (invariante del modelo desde #824) y el expediente-tipo no envejece |
| **Anclarse a `date.today()`, no al reloj simulado** | El reloj casi siempre viene de la ejecución anterior del propio script; anclarse a él congelaría el expediente en el calendario del día en que se generó por primera vez |
| **Las fechas de respuesta se derivan del vencimiento real** que calcula `plazos.obtener_estado_plazo_tarea`, nunca de un número de días escrito a mano | Si cambia el plazo del catálogo, el escenario sigue siendo válido. Patrón a copiar: `_fecha_respuesta_en_plazo` |
| **Nunca borrar**: marcar `[RECICLAR]` y dejar el borrado a `limpiar_reciclables.py` | El vestigio AT-15 permitió reconstruir qué había pasado en una ejecución defectuosa, en vez de tener que recordarlo |
| **Catálogo por clave natural**, nunca PK hardcodeada | Las PK cambian entre bases; los códigos no |
| **Doble vida**: `main(app=None, *, efectos_desarrollo=True)` | `efectos_desarrollo=False` deja fuera lo que solo tiene sentido en la máquina de desarrollo (fijar el reloj simulado, que escribe en `instance/`). El escenario construido es el mismo |

---

## Banco de documentos dummy

Los PDF que suben estos scripts viven en `tests/fixtures/documentos_dummy/`, generados por
`scripts/generar_documentos_dummy.py` (#814 parte 1) junto a `catalogo_uso.csv`, que documenta
dónde se usa cada tipo.

Están bajo `tests/` a propósito: `scripts/semilla_test.py` los usa para construir la base de
tests, así que ahí sí son fixture. El pool no distingue cómo entró un fichero —solo
`tipos_documentos.origen` clasifica externo/interno—, de modo que los documentos `INTERNO`
simulados entran por la misma subida multipart que los externos.
