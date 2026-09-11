# PRE-ADR — Resolución de solicitudes con DUP: el doble acto

> **Naturaleza de este documento:** Material preparatorio de una sesión de diseño en curso.
> No toma decisiones definitivas — recoge lo hablado, señala qué ya existe (verificado
> contra código y BD, no supuesto) y deja las preguntas abiertas para cuando se cierre. El
> output será un ADR formal (candidato a **ADR-046**, siguiente libre tras ADR-045) que
> enmiende ADR-045 §"Lo que este ADR no decide".

**Estado:** Propuesta para discusión (no implementada)
**Fecha:** 2026-09-11 (sesión iniciada; documento vivo, se actualiza en sesiones sucesivas)
**Disparador:** sesión de decisión sobre el "Próximo" de `CONTEXTO_ACTUAL.md` tras cerrar la
cadena ADR-044 — retoma ADR-045 §"Lo que este ADR no decide" (dos vías evaluadas sin elegir:
dos fases finalizadoras vs. dos solicitudes hermanas)

---

## 1. Ya cerrado en esta sesión

- `ESTRUCTURA_ESF.md`/`.json` v2.3: combinación `AAP+DUP` completada (fase `RESOLUCION`
  única, sin desdoblar — nota de acto DUP diferido hasta AAC en solicitud posterior).
- #911 — implementación en `tipos_solicitudes`/`ESTRUCTURA_FTT` de ese hueco.
- #912 — el listado de seguimiento (`codigo_finalizadora`) solo mira la primera fase
  finalizadora por `id`, no reproduce `RESUELTA_DISCREPANTE` (mismo defecto que #901 ya
  corrigió en la property `Solicitud.estado`, pero no en este filtro).
- Pendiente, anotado para cuando entremos en FTT (no antes): trámites catastrales —
  solicitud/entrega de datos de catastro para la relación de bienes y derechos del
  art. 143.3, sin cobertura expresa en RD 1955/2000 ni en la Ley de Expropiación Forzosa.
- Aparcado, fuera de este análisis: pie de recurso por plantilla — sale con los context
  builders de cada plantilla, cuando toque. El RECURSO como acto que abre solicitud en el
  expediente ya existe como tipo_solicitud propio (`RECURSO`), no es parte de este problema.

## 2. El problema

Una solicitud con DUP combinada (`AAP+AAC+DUP`, `AAC+DUP`, `AAP+DUP`) es **una sola fila**
de `solicitudes` (un solo `solicitud_id`) que, por ADR-045 §B, produce **dos actos
resolutorios** que no pueden ser el mismo documento ni compartir pie de recurso: uno de
autorización (AAP y/o AAC, delegación DG) y otro de DUP (delegación Consejería). Hay que
decidir cómo se encaja eso en el modelo de fases/trámites de BDDAT.

## 3. Alternativas evaluadas

### 3.1 Subfases dentro de una única fase `RESOLUCION` (descartada)

La fase `RESOLUCION` se queda como está (una sola). Los trámites se dividen en dos grupos
—"todo menos DUP" y "DUP"—, con cardinalidad duplicada pero organizados en dos subfases,
patrón similar a como `CONSULTAS` admite varios `CONSULTA_SEPARATA` (uno por organismo).

El precedente de `CONSULTAS`/`CONSULTA_SEPARATA` no es exactamente equiparable — ahí se
repite **el mismo trámite** N veces (cardinalidad variable, ADR-042), no se parte la fase en
dos grupos heterogéneos con base legal, plazo y órgano distintos. Si la fase sigue siendo
una, arrastra problemas ya conocidos porque BDDAT los tiene resueltos a nivel de **fase**,
no de grupo de trámites dentro de una fase:

- `Fase.documento_resultado_id` es un único campo — con dos actos, ¿cuál de los dos
  documentos de resultado se guarda ahí? Es el mismo problema que tenía
  `Solicitud.documento_cierre_id` antes de que #901 lo resolviera subiendo el criterio a
  "todas las finalizadoras cerradas" — con subfases dentro de una sola `Fase`, ese defecto
  se reintroduce un nivel más abajo.
- `Fase.pdte_cierre` y `_check_completitud_cierre` (#723) ya calculan "fase completa" sobre
  `Tramite.planificado`/`finalizado` sin noción de agrupación — habría que enseñarles a
  discriminar por subgrupo.
- `catalogo_plazos` indexa por tipo de fase; dos plazos reales (3 meses autorización, 6
  meses DUP — art. 148.1, y es precisamente lo que #892 tiene que resolver) bajo una sola
  fase exige inventar un discriminador ahí también.
- Órgano/firmante distinto (DG vs. Consejería) por acto, sobre una fase que en el modelo es
  una unidad.

### 3.2 Desdoblar en dos fases finalizadoras: `RESOLUCION` y `RESOLUCION_DUP` — **elegida**

Cada acto es una fase real, con sus propios trámites (reutilizados o nuevos), su propio
`documento_resultado_id`, su propia fecha de cierre, su propio plazo en `catalogo_plazos`.

No hay que montar nada nuevo — el mecanismo ya existe y está construido:

- `Solicitud.estado` (ADR-044 R5, #901) **ya** exige que **todas** las fases finalizadoras
  de la solicitud estén cerradas antes de dar la solicitud por resuelta, y ya devuelve
  `RESUELTA_DISCREPANTE` si los resultados no coinciden. Funciona sin tocarlo: no distingue
  cuántas fases finalizadoras hay ni de qué tipo, solo cuenta cierres. Esto no es un
  precedente ya recorrido — es una pieza de arquitectura diseñada a propósito para este
  escenario (el propio ADR-044 R5 lo dice: "ADR-045 descubrió durante el diseño... una
  solicitud puede resolver en dos actos independientes"), pero nadie ha recorrido aún el
  camino completo (árbol, dos fases hermanas de tipo distinto en la misma solicitud,
  certificados). Es terreno nuevo, no terreno probado.
- `RECONOCIMIENTO_INTERESADO` **no** es precedente válido de "dos finalizadoras en la misma
  solicitud" — es la finalizadora de otra solicitud (`INTERESADO`).
- `Fase.documento_resultado_id`, `pdte_cierre`, `planificado`/`finalizado` — todo lo que ya
  gobierna el ciclo de vida de una fase se aplica sin inventar nada, porque cada acto es una
  fase de verdad.
- **Dónde actúa el bloqueo de #891:** no es que `RESOLUCION_DUP` no pueda **cerrarse** sin
  AAC — es que no puede **emitirse**. La regla actúa sobre la tarea `ELABORAR` del trámite
  `ELABORACION` de `RESOLUCION_DUP` (redactar/emitir el acto), patrón
  `BLOQUEAR CREAR/PRODUCIR` ya usado en el motor (ADR-044 §D), no sobre un check aparte de
  "fase completa". El no-cierre es consecuencia de eso, no el punto de enganche.

**Decisión:** la alternativa 3.2 es la técnicamente superior — reutiliza mecanismos ya
construidos y verificados en producción (ADR-044 R5/#901, `Fase.documento_resultado_id`,
`catalogo_plazos` por tipo de fase) en vez de construir un ciclo de vida de "subfase" nuevo
con su propio cierre, documento de resultado y plazo por dentro de una fase que el modelo
trata como unidad. **Confirmada por Carlos.**

## 4. Flecos resueltos de la vía elegida (3.2)

### 4.1 Naming del tipo de fase nuevo

`TipoFase` (`app/models/tipos_fases.py`) tiene cuatro campos de nombre, audiencias
distintas: `codigo` (inmutable, clave de lógica en motor/`catalogo_plazos`), `nombre`
(interfaz), `abrev` (breadcrumb, ≤20 car.), `nombre_en_plantilla` (pensado para nombre de
fichero — ver 4.1.2).

**Decidido:**

| Campo | Valor | Nota |
|---|---|---|
| `codigo` | `RESOLUCION_DUP` | Sin choque en `tipos_fases` (9 filas). Prefijo `RESOLUCION_*` para finalizadoras que son actos resolutorios. |
| `nombre` | "Resolución de Declaración de Utilidad Pública" | Semánticamente correcto (es una resolución), no calca la descripción de la solicitud DUP (`tipos_solicitudes` id=3). |
| `abrev` | "RES_DUP" | Reserva "DUP" para la solicitud, se distingue de ella. |
| `nombre_en_plantilla` | `NULL` | Confirmado inútil hoy — ver 4.1.2. |

**Colateral — ¿renombrar también `RECONOCIMIENTO_INTERESADO`?** También es una resolución:
- `nombre` → "Resolución de Reconocimiento de Interesado": sin objeción, seguro (el texto
  actual solo aparece en `ESTRUCTURA_FTT.json` y en el seed de migración, ningún código
  Python lo compara como string).
- `codigo` → `RESOLUCION_RECONOCIMIENTO_INTERESADO`: **descartado**. El código actual está
  hardcodeado como clave de lógica en `catalogo_requerido.py:52`,
  `informe_instruccion.py:105` (`_FASE_FINALIZADORA_POR_SIGLAS`), y en un dato real de
  `reglas_motor` (id 1788, `sujeto='ANY/INTERESADO/RECONOCIMIENTO_INTERESADO'`). Coste real
  sobre algo ya en producción por ganancia puramente estética — no se toca. El prefijo
  `RESOLUCION_*` se aplica solo hacia adelante, en `RESOLUCION_DUP`.

#### 4.1.1 Cabo suelto de implementación: nombre de fichero duplicado

`RESOLUCION.ELABORACION` ya tiene `tipos_tramites.nombre_en_plantilla = 'Resolución'`
fijado por migración. Si `RESOLUCION_DUP` reutiliza el mismo `tipo_tramite` código
`ELABORACION` (patrón habitual — `tipos_tramites` tiene una fila por código, no por par
fase+código), los dos documentos generarían el mismo nombre de fichero. Solución ya
prevista por `nombres_documentos.py`: entrada en `_SUSTITUCIONES` para el par
`('RESOLUCION_DUP', 'ELABORACION')`, mismo mecanismo que ya usa
`COMUNICACION_INICIO_ADMISION`. Trabajo de implementación, conectado con #809.

#### 4.1.2 `tipos_fases.nombre_en_plantilla`: huérfano, confirmado

No se usa en ningún sitio — ni como token de contenido del escrito ni en el nombre del
fichero. El nombre real del fichero lo compone `componer_nombre_documento()`
(`generador_escritos.py:131-177`):
`{texto del trámite} {siglas/nombre_en_plantilla de la solicitud} AT-{numero_at} [V variante].ext`
— el "texto del trámite" sale de `tipos_tramites.nombre_en_plantilla`, no de `tipos_fases`.

Origen histórico: el commit `069a0cf` (issue #167 "Fase 3", marzo 2026) añadió la columna
simétricamente en las 5 tablas ESFTT (`tipos_expedientes`, `tipos_solicitudes`,
`tipos_fases`, `tipos_tramites`, `tipos_tareas`), diseño original pensado como nombre de
fichero compuesto por la contribución de cada nivel — nunca token de contenido (eso es
mecanismo distinto: context builders). Cuando se implementó de verdad el servicio (#698,
`nombres_documentos.py`), se recortó a solo 2 de los 5 niveles (`tipo_tramite` +
`tipo_solicitud` + `AT-numero`). `tipo_fase`, `tipo_expediente` y `tipo_tarea` quedaron con
el dato del seed original pero sin consumidor real — deuda de un recorte de alcance no
limpiado, ajena a la DUP.

### 4.2 Dos fases hermanas en el árbol / seguimiento

- **Árbol: sin problema.** `arbol_expediente.py:265` ordena fases por `id`, sin trato
  especial de `es_finalizadora`. `es_finalizadora` no aparece ni una vez en
  `app/static/js` — el frontend no tiene lógica especial para finalizadoras. Aparecer como
  hermanas con nombre/abrev distintos no rompe nada aquí.
- **Listado de seguimiento: laguna real, ya arreglada con issue propio.**
  `api_seguimiento.py:95-107` (`codigo_finalizadora`) coge solo la primera finalizadora por
  `id` para el resultado con el que se filtra/muestra la solicitud — mismo defecto que #901
  ya corrigió en la property `Solicitud.estado`, pero no en este filtro. **Issue: #912.**

### 4.3 Qué impide cerrar la solicitud sin `RESOLUCION_DUP`

Las fases no las crea el sistema, las crea el usuario, cuando quiera — no hay fleco de
"cuándo se crea la fase". El fleco real: qué impide que la solicitud se dé por resuelta si
el tramitador nunca llega a crear (o cerrar) `RESOLUCION_DUP`.

**Verificado: ese mecanismo no existe hoy.** `_check_finalizar` (`invariantes_esftt.py:811`,
sujeto `SOLICITUD`) solo mira las fases que **existen**, no las que el tipo de solicitud
**exige**. Igual `Solicitud.estado` (`models/solicitudes.py:248-258`). Con solo `RESOLUCION`
cerrada y `RESOLUCION_DUP` nunca creada, la solicitud se daría por `RESUELTA_FAVORABLE` sin
más — el acto DUP no se echaría en falta.

Primer análisis: requisito legal (modelo legal, cita normativa) → debería ir a
`reglas_motor`, no a invariante. Verificado con datos: `SELECT DISTINCT accion FROM
reglas_motor` → **solo `CREAR`**, 100% de las filas — el motor no tiene hoy manera de
engancharse al momento de cerrar/finalizar. Esto llevaba a pensar que hacía falta ampliar
la arquitectura del motor (ADR propio) antes de poder resolver esto.

**Redirección (Carlos): el patrón ya existe, para `CERT_FIN_INSTRUCCION`, reutilizable para
`#801`.** `informe_instruccion.py:97-106`:

```python
# Qué fase finalizadora habilita el certificado en cada solicitud — es el sujeto
# contra el que se audita. Las dos finalizadoras nunca conviven en la misma
# solicitud (ADR-043 §C): RECONOCIMIENTO_INTERESADO es la de la solicitud
# INTERESADO...; el resto resuelve por RESOLUCION.
_FASE_FINALIZADORA_POR_SIGLAS = {'INTERESADO': 'RECONOCIMIENTO_INTERESADO'}
_FASE_FINALIZADORA_DEFECTO = 'RESOLUCION'
```

Es exactamente el mapa "tipo de solicitud → fase finalizadora contra la que auditar" — pero
es **1:1**, construido explícitamente sobre la premisa "las dos finalizadoras nunca conviven
en la misma solicitud (ADR-043 §C)", que ADR-045 rompe. Tendría que evolucionar a listas
(`'AAP+AAC+DUP': ['RESOLUCION', 'RESOLUCION_DUP']`) y su consumidor auditar todas, no una.

**Red de seguridad ya existente:** un guardián de arranque
(`catalogo_requerido.py:151-219`, `_validar_finalizadoras_con_regla`) vigila esto. Al dar de
alta `RESOLUCION_DUP` como `es_finalizadora=True`, avisaría automáticamente de dos huecos:
(1) falta una fila `reglas_motor` (`accion=CREAR, articulo=82, apartado=1`) que la nombre —
la regla de precedencia del art. 82.1 que impide crear indebidamente tras la finalizadora—,
alcanzable con el motor tal como es hoy (solo `CREAR`, no hace falta ampliarlo); (2) falta
en `_FASE_FINALIZADORA_POR_SIGLAS`.

**Conclusión revisada:** no hace falta ampliar `reglas_motor` a `FINALIZAR` ni un ADR de
arquitectura del motor. Hace falta: (a) nueva fila `reglas_motor` CREAR/82.1 para
`RESOLUCION_DUP`; (b) evolucionar `_FASE_FINALIZADORA_POR_SIGLAS` a listas; (c) decidir si
la auditoría contra esa lista vive en `CERT_FIN_INSTRUCCION` (certifica que la instrucción
terminó, habilita crear la finalizadora), en `#801`/`CERT_CIERRE_SOLICITUD` (certifica que
el plazo de la solicitud está cumplido, hoy solo valida notificaciones — sería ampliar su
alcance) o en ambos, con propósito distinto cada uno. **No cerrado del todo — matiz
pendiente:** #801 no lo cubre automáticamente hoy (su alcance actual es notificaciones), es
la ampliación natural, no algo ya hecho.

## 5. Pendiente — sin abordar todavía

- **ESTRUCTURA_FTT de `RESOLUCION_DUP`**: trámites ELABORACION/NOTIFICACION/PUBLICACION,
  con publicación BOE (no BOJA) y notificación a titulares de bienes y derechos
  (ADR-045 §F, conecta con #431).
- **Arquitectura del motor para acciones distintas de `CREAR`** (§4.3) — probablemente su
  propio frente de diseño, no una regla suelta.
