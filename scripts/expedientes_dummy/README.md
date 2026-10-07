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
| `REFORMADO_ANALISIS_Y_CONSULTAS` | Dos versiones de proyecto (ADR-044): `ANALISIS_SOLICITUD` y `CONSULTAS` cortadas por el mismo reformado | Un organismo enquistado en la `CONSULTAS` de la v1 (hueco vivo, §I) que ninguna fase posterior salda; la v2 (reformado) repite ese organismo y añade uno nuevo, ambas fases limpias (§F) |
| `RESOLUCION_CON_ORGANISMOS` | Consultas cerradas (favorable, condicionado con traslado aceptado, silencio reconocido), resolución notificada a solicitante representado y a los tres organismos | Único que llega a cerrar `RESOLUCION`: `CERT_FIN_INSTRUCCION`, botón «añadir los que faltan», `CERT_CUMPLIMIENTO_FASE` y `CERT_CIERRE_FASE` |

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

Al terminar **deja fijado el reloj de desarrollo** en la última fecha de su escenario — al
revés que `CONSULTAS_VARIOS_ESTADOS`, que lo borra. Es deliberado: el escenario se lee desde
su propio presente. El síntoma de haberlo olvidado es que la aplicación no deja fechar en el
presente; se comprueba y se deshace con `flask reloj show` / `flask reloj clear`.

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

- **La condición del requisito `DR_NO_DUP` estaba invertida** — se exigía cuando la solicitud
  incluía DUP, y es al revés. Corregido en #863; desde entonces la declaración que presenta el
  titular se casa como un requisito más del checklist.
- **Dos documentos de igual contenido compartían fichero en el pool**, y al llevarse el primero
  a su carpeta ESFTT el segundo se quedaba apuntando a un fichero que ya no existía. Por eso el
  script sube y vincula cada separata organismo a organismo en vez de subir las tres de golpe.
  Resuelto por ADR-050 (#1007): el contenido vive en el almacén y vincular no mueve nada. El
  orden de subida se queda para no cambiar la semilla.

### REFORMADO_ANALISIS_Y_CONSULTAS

`reformado_analisis_y_consultas.py` — #903

Primer expediente-tipo que ejercita `reformados_proyecto` (ADR-044) por el circuito
real. Línea aérea de 66 kV en Jerez de la Frontera (AAP+AAC, un solo municipio),
exenta de instrumento ambiental — mismo perfil que `CONSULTAS_VARIOS_ESTADOS`, para
que el foco quede en la mecánica de reformados y no en variedad administrativa.

Dos versiones de proyecto, con `ANALISIS_SOLICITUD` y `CONSULTAS` cortadas por el
mismo reformado:

| | v1 (`reformado_id` NULL) | v2 (reformado) |
|---|---|---|
| `ANALISIS_SOLICITUD` | Checklist limpio, diagnóstico favorable. No se cierra formalmente (como los otros dos expedientes-tipo) | Segunda fase del mismo tipo, permitida por §F. Checklist limpio por el fallback de R4 a la versión inicial — no hace falta aportar nada nuevo |
| `CONSULTAS` | Ayuntamiento de Jerez consultado, **nunca contesta** — silencio, plazo vencido, sin `ANALIZAR`. Es el hueco vivo: el organismo enquistado de §I, que nada en el escenario resuelve | Segunda fase del mismo tipo, permitida por §F. El Ayuntamiento **repetido** (nueva separata, nuevo ciclo, esta vez favorable) + ADIF **nuevo**, también favorable — `UNIQUE(fase_id, organismo_id)` sin conflicto entre rondas |

El reformado es voluntario: el titular reencauza el tramo final para evitar una
servidumbre de vuelo y el nuevo trazado pasa a cruzar la línea de ferrocarril.

| Parámetro | Valor | Por qué |
|---|---|---|
| `DIAS_ESCENARIO` | 200 | La `CONSULTAS` de la v1 necesita quedar vencida (30 días hábiles) con margen antes de declarar el reformado, y aún queda sitio para una `ANALISIS_SOLICITUD` y una `CONSULTAS` completas de la v2 con dos organismos |
| `HABILES_HASTA_VENCIMIENTO_V1` | 40 | Días hábiles desde que se notifica la separata de la v1 hasta declarar el reformado — vencido con margen sobre los 30 del art. 131.1 |
| `MARGEN_RESPUESTA_ORGANISMO_HABILES` | 15 | Días hábiles antes del vencimiento real en que responde cada organismo de la v2 |
| `HABILES_HASTA_TRASLADO` | 2 | De recibir la respuesta del organismo a notificar el traslado al titular |
| `MARGEN_RESPUESTA_TITULAR_HABILES` | 5 | Respuesta del titular al traslado, en las dos rondas de la v2 |

Necesitó un fixture nuevo, `doc_proyecto_reformado.pdf` (además del banco generado por
`scripts/generar_documentos_dummy.py`): con el modelo de carpetas, el pool no duplicaba un
fichero con el mismo contenido (ver el hallazgo de arriba sobre `DOC_SEPARATA`), y para
cuando se subía el segundo `DOC_PROYECTO` el primero ya se había movido a su carpeta ESFTT.
Desde ADR-050 (#1007) eso ya no pasa; el fixture se queda para no cambiar la semilla.

Al terminar **borra el reloj de desarrollo**: el organismo enquistado de la v1 sigue
vencido se mire desde la fecha que se mire, y las fechas ya cerradas de la v2 no
dependen de qué diga el reloj simulado.

```bash
venv/Scripts/python.exe scripts/expedientes_dummy/reformado_analisis_y_consultas.py
```

### RESOLUCION_CON_ORGANISMOS

`resolucion_con_organismos.py` — #971

Mismo perfil que `CONSULTAS_VARIOS_ESTADOS` y `REFORMADO_ANALISIS_Y_CONSULTAS` (línea
aérea 66 kV en Jerez de la Frontera, AAP+AAC, exenta de instrumento ambiental), pero es
el único de los cuatro que **llega a cerrar `RESOLUCION`**: los otros tres se quedan en
`ANALISIS_SOLICITUD` o con `CONSULTAS` abierta a propósito. Nace de la cadena de ADR-049
entre #968 (N5a-2) y #969 (N5a-3): antes de #968 no existían el botón ni las fuentes de
notificación; #969 lo usará para comprobar que solo la notificación al solicitante
cumple el plazo del acto.

El solicitante actúa **representado** (`solicitudes.representante_entidad_id`, #967):
la comunicación de inicio y la resolución se notifican a su representante, en su nombre.
Las tres consultas se cierran, con los tres desenlaces del Caso A-D de ADR-011 §6 que
`CONSULTAS_VARIOS_ESTADOS` deja pendientes:

| Organismo | Desenlace |
|---|---|
| Ayuntamiento de Jerez | Silencio, plazo vencido, sin `ANALIZAR` — conformidad tácita (Caso A) |
| ADIF | Responde con condicionados; traslado notificado y aceptado por el representante — `cerrado_con_condicionados` |
| Diputación de Cádiz | Responde favorable; traslado notificado y aceptado por el representante — `cerrado_favorable` |

**El silencio del Ayuntamiento no tiene vía limpia de cierre en el catálogo actual**
(#982, detectado al escribir este expediente-tipo): no existe `CERT_PLAZO_CUMPLIDO`
para `CONSULTA_SEPARATA`, así que su `ESPERAR_PLAZO` nunca llega a `ejecutada` y cerrar
`CONSULTAS` exige forzar el escape de `editar_fase` con `justificacion`. Queda en
bitácora, documentado en el propio script. #971 sigue adelante con él (decisión de
Carlos); #982 es la mejora de catálogo pendiente para que deje de hacer falta.

`ANALISIS_SOLICITUD` y `CONSULTAS` se cierran de verdad (`editar_fase`) — a diferencia
de los otros tres expedientes-tipo, que no lo hacen. Después: `CERT_FIN_INSTRUCCION`
consolidado, `RESOLUCION` con `ELABORACION` (produce el documento `RESOLUCION`) y
`NOTIFICACION` poblada con el botón «añadir las notificaciones que faltan» (una para el
solicitante —a su representante— y una por cada organismo consultado, sin excluir al
del silencio), y los dos certificados de fase (`CERT_CUMPLIMIENTO_FASE`,
`CERT_CIERRE_FASE`, con la frase de confirmación `'cerrar finalizadora'`).

| Parámetro | Valor | Por qué |
|---|---|---|
| `HABILES_DESDE_NOTIFICACION_SEPARATAS` | 60 | El ancla, como en `CONSULTAS_VARIOS_ESTADOS`, pero con más margen: aquí el escenario sigue después de vencer el plazo del Ayuntamiento hasta cerrar la resolución |
| `MARGEN_ADIF_HABILES` / `MARGEN_DIPUTACION_HABILES` | 25 | Ambos responden con margen holgado para que, tras el traslado y su aceptación, quede sitio de sobra hasta `hoy` para cerrar fases, consolidar la instrucción y notificar la resolución |
| `MARGEN_TITULAR_HABILES` | 5 | Respuesta del representante a cada traslado |
| `HABILES_HASTA_TRASLADO` | 2 | De recibir la respuesta del organismo a notificar el traslado |

Al terminar **borra el reloj de desarrollo**, como `CONSULTAS_VARIOS_ESTADOS`: la
resolución queda notificada y cerrada «a fecha de hoy».

```bash
venv/Scripts/python.exe scripts/expedientes_dummy/resolucion_con_organismos.py
```

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
- Los contenidos del almacén no se tocan: solo los borra la limpieza (fase 7 de ADR-050).
- Comprobación dinámica del esquema antes de tocar nada: si alguien añade una tabla que apunta a
  las que aquí se borran y no está contemplada, aborta en vez de dejar filas colgando.
- Una transacción por expediente: si algo falla, ese expediente queda intacto.

```bash
# Informe, sin borrar nada
venv/Scripts/python.exe scripts/expedientes_dummy/limpiar_reciclables.py

# Borrado real (pide confirmación; --si la salta)
venv/Scripts/python.exe scripts/expedientes_dummy/limpiar_reciclables.py --borrar
venv/Scripts/python.exe scripts/expedientes_dummy/limpiar_reciclables.py --borrar --at 12,13 --si
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
| **Cerrar cada NOTIFICAR con `_comun.notificar()`**, que asegura el destinatario antes de vincular (`fijar_destinatario_de`) | Desde #967 una `NOTIFICAR` sin destinatario no admite vínculos (ADR-051 §B). Desde #968 nace ya con él cuando el servicio de destinatarios lo sabe (el solicitante —o su representante— o el organismo del trámite) y aquí solo se refresca; si el destinatario se elige a mano y nadie lo eligió, el script aborta en vez de adivinarlo |
| **Engancharlo a la semilla**: añadir el módulo a `_modulos_expediente_tipo()` en `scripts/semilla_test.py` | Es lo que impide que el escenario se pudra en silencio: si un cambio de la aplicación lo rompe, `preparar_bd_test.py --recrear` falla, en vez de esperar a que alguien lo ejecute a mano. De paso queda disponible para los tests que lo necesiten |

---

## Banco de documentos dummy

Los PDF que suben estos scripts viven en `tests/fixtures/documentos_dummy/`, generados por
`scripts/generar_documentos_dummy.py` (#814 parte 1) junto a `catalogo_uso.csv`, que documenta
dónde se usa cada tipo. Tras cambiar `tramites_tareas_documentos` basta con
`--solo-csv`: el modo completo reescribe todos los PDF y borra `doc_proyecto_reformado.pdf`,
que no genera él (#964).

Están bajo `tests/` a propósito: `scripts/semilla_test.py` los usa para construir la base de
tests, así que ahí sí son fixture. El pool no distingue cómo entró un fichero —solo
`tipos_documentos.origen` clasifica externo/interno—, de modo que los documentos `INTERNO`
simulados entran por la misma subida multipart que los externos.
