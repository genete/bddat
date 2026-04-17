# Motor de reglas agnóstico — Decisiones de rediseño

> **Fecha:** 2026-04-05 · **Actualizado:** 2026-04-16
> Sesión de reflexión arquitectural. Complementa `DISEÑO_MOTOR_REGLAS.md`.
> Esquema de tablas cerrado en sesión 2026-04-16 — ver §Esquema de tablas.

---

## Decisión principal: motor agnóstico de dominio

El motor de reglas debe refactorizarse para ser completamente independiente de BDDAT.
En lugar de que el motor conozca el dominio (Fase, Tarea, Expediente, etc.) y haga
queries internos al árbol ESFTT, el flujo correcto es:

1. **BDDAT** ensambla un dict plano de variables antes de llamar al motor
2. **Motor** recibe `(accion, sujeto, tipo_sujeto_id, variables: dict)` y evalúa reglas en BD contra ese dict
3. El motor no importa modelos de BDDAT, no traversa el árbol ESFTT, no hace queries propias

```python
# BDDAT ensambla el contexto
variables = {
    'ia':                  'AAU',
    'es_modificacion':     False,
    'intermunicipal':      True,    # calculado por BDDAT: len(proyecto.municipios) > 1
    'fase_ip_cerrada':     False,   # calculado por BDDAT: query a Fase
    'tiene_doc_producido': True,    # calculado por BDDAT
    'plazo_vencido':       False,   # calculado por BDDAT: controlador de fechas
}

# Motor evalúa — sin saber de dónde vienen los valores
motor.evaluar(accion='INICIAR', sujeto='TRAMITE', tipo_sujeto_id=5, variables=variables)
```

**Principio:** es el procedimiento el que se engancha al API del motor, no al revés.
El motor es válido para cualquier tramitador (AT, subvenciones, reclamaciones).
BDDAT se adapta al API del motor.

**Por qué ahora:** las tablas `reglas_motor` y `condiciones_regla` aún no están pobladas
con reglas reales. El coste de refactorizar es mínimo ahora, altísimo después.

---

## Pieza nueva: ContextAssembler

Capa de BDDAT que, dado un evento + entidad, sube el árbol ESFTT y computa todas las
variables necesarias antes de llamar al motor. Esta capa sí conoce BDDAT a fondo.

**Diseño del ContextAssembler:** `docs/DISEÑO_CONTEXT_ASSEMBLER.md`
— diccionario de variables, tipos de naturaleza, estados de implementación y filosofía
de almacenamiento.

---

## API del Motor Agnóstico

El motor expone una sola función pública. Su firma es el contrato con el resto del sistema:

```python
resultado = motor.evaluar(
    accion:         str,            # 'INICIAR' | 'FINALIZAR' | 'BORRAR' | 'CREAR' | ...
    sujeto:         str,            # 'FASE' | 'TRAMITE' | 'TAREA' | 'SOLICITUD' | 'EXPEDIENTE'
    tipo_sujeto_id: Optional[int],  # ID en la tabla tipos_* del sujeto. NULL = aplica a todos
    variables:      dict,           # dict plano compilado por ContextAssembler
) -> EvaluacionResult
```

`tipo_sujeto_id` es una clave de filtrado, no una variable de evaluación. El motor lo usa
para hacer `WHERE tipo_sujeto_id = X OR tipo_sujeto_id IS NULL` al cargar reglas de BD.
No aparece en las condiciones ni en el resultado.

```python
@dataclass
class EvaluacionResult:
    permitido:          bool
    nivel:              str        # 'BLOQUEAR' | 'ADVERTIR' | ''
    variables_trigger:  dict       # subconjunto del dict que disparó la regla (para mostrar al usuario)
    norma_compilada:    str        # referencia compilada: "Art. 6 del Decreto-ley 26/2021..."
    url_norma:          str        # URL BOE/BOJA; '' si no existe
```

El motor no construye mensajes en lenguaje natural. La vista compila el texto a partir de
`variables_trigger` y `norma_compilada`. Sin campos de texto libre escritos por humanos.

**Contratos de comportamiento:**

| Situación | Comportamiento |
|---|---|
| Sin reglas en BD para `(accion, sujeto, tipo_sujeto_id)` | Devuelve `PERMITIDO` — todo permitido excepto lo expresamente prohibido |
| Condición referencia variable ausente del dict | Condición = `False` (no cumplida) + `log.warning(nombre_variable)`. PERMITIDO para el usuario |
| Varias reglas activas para el mismo trío | `BLOQUEAR` > `ADVERTIR`; dentro del mismo nivel, gana la de menor `prioridad` |
| Error interno del motor | Lanza excepción — nunca devuelve `PERMITIDO` silenciosamente ante un fallo |

El motor no sabe nada de BDDAT. No importa modelos. No hace queries. Recibe el dict
y evalúa las reglas en `reglas_motor`/`condiciones_regla`. Nada más.

---

## ContextAssembler — contexto completo, agnóstico de reglas

El ContextAssembler no sabe nada de las reglas, de la acción que se evalúa, ni del
sujeto sobre el que actúa. Su único trabajo es compilar **todas** las variables del
diccionario para el contexto activo del expediente. No toma ninguna decisión en función
de qué se está evaluando — simplemente recorre el árbol ESFTT y llena la despensa.

```python
variables = context_assembler.build(expediente_id)
# → dict completo con TODAS las variables definidas en el catálogo
#   {'ia': 'AAU', 'es_modificacion': False, 'tension_nominal_kv': 220,
#    'tiene_doc_producido': True, 'plazo_vencido': False, ...}
#   Las no aplicables o no rellenadas llegan como None.
```

No hay tabla de despacho, no hay lógica condicional por sujeto o acción. La ruta
conoce la acción, el sujeto y el id — el assembler no los necesita para compilar
el contexto. El mismo dict se pasa al motor sea cual sea la acción evaluada.

El motor recibe el dict completo y usa solo las variables que sus condiciones
referencian. No puede haber una regla que referencie una variable que el
ContextAssembler no sepa computar, porque el assembler computa todas.

**Contrato compartido entre ContextAssembler y Motor:** el diccionario de variables.
`DISEÑO_CONTEXT_ASSEMBLER.md` es la única fuente de verdad de ambas piezas.
Añadir una variable nueva requiere: (1) definirla en ese diccionario, (2) implementar
su cómputo en el ContextAssembler. Solo entonces el Supervisor puede referenciarla
en una regla.

**Uso en rutas Flask — sin capa intermedia:**

```python
# La ruta llama directamente al assembler y al motor.
variables = context_assembler.build(fase.expediente_id)
resultado  = motor_reglas.evaluar('INICIAR', 'FASE', fase.tipo_fase_id, variables)
if not resultado.permitido:
    return jsonify({'norma': resultado.norma_compilada,
                    'variables': resultado.variables_trigger}), 422
```

No existe una capa EventHandler separada. El patrón es siempre dos líneas.
Si en el futuro se necesita lógica transversal (auditoría, métricas), se extrae
a una función de utilidad sin nombre arquitectural.

**Lo que es hardcodeado vs. configurable:**

| Qué | Dónde vive |
|---|---|
| Llamada al assembler + motor en la ruta | Código Python — dos líneas por evento |
| Lógica de cómputo de cada variable | Código Python — ContextAssembler |
| Las reglas y sus condiciones | BD — `reglas_motor` / `condiciones_regla` |
| Qué variables puede referenciar el Supervisor | BD — `catalogo_variables` (dropdown en UI) |

---

## Esquema de tablas — decisiones cerradas (2026-04-16)

Estas tres tablas constituyen el contrato de datos del motor. **Ningún campo es texto libre
escrito por el creador de reglas.** Todo el texto visible (al usuario y al Supervisor) se
compila en tiempo de presentación a partir de datos estructurados.

### `reglas_motor`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER PK | |
| `accion` | VARCHAR | `CREAR` \| `INICIAR` \| `FINALIZAR` \| `BORRAR` |
| `sujeto` | VARCHAR | `SOLICITUD` \| `FASE` \| `TRAMITE` \| `TAREA` \| `EXPEDIENTE` |
| `tipo_sujeto_id` | INTEGER nullable | ID en la tabla `tipos_*` del sujeto. NULL = aplica a todos los tipos |
| `efecto` | VARCHAR | `BLOQUEAR` \| `ADVERTIR` |
| `norma_id` | FK → `normas` | Norma legal de referencia |
| `articulo` | VARCHAR | Artículo exacto: `"24.3"` \| `"DA4"` \| `"DF2"` |
| `apartado` | VARCHAR nullable | Sub-apartado si procede |
| `prioridad` | INTEGER | Orden de presentación cuando hay varias reglas activas del mismo trío |
| `activa` | BOOLEAN | Desactivar en lugar de borrar — preserva trazabilidad |

Sin campo `mensaje`, sin campo `descripcion`. El texto de presentación se compila desde los
campos estructurados: la vista del Supervisor genera automáticamente algo del tipo:
*"Esta regla bloquea INICIAR para FASE tipo 'Información Pública' cuando: ia_siglas en ['AAU','AAUS'] Y doc_dup_ausencia igual a false"*

### `condiciones_regla`

Una fila por variable del dict. Todas las condiciones de una regla se combinan con **AND
implícito**. Para expresar OR se crean reglas separadas (Leyes de De Morgan).

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER PK | |
| `regla_id` | FK → `reglas_motor` CASCADE | Regla a la que pertenece |
| `nombre_variable` | VARCHAR | Clave en el dict de variables |
| `operador` | VARCHAR | Ver catálogo de operadores |
| `valor` | JSON | Valor de referencia (string, número, lista para IN/BETWEEN) |
| `orden` | INTEGER | Solo informativo — no cambia semántica |

Sin `negacion` (redundante con los operadores contrarios), sin `operador_siguiente`
(eliminado al adoptar AND-only), sin `tipo_criterio` (sustituido por `nombre_variable`).

**Catálogo de operadores:**

| Operador | Semántica |
|---|---|
| `EQ` / `NEQ` | igual / distinto |
| `IN` / `NOT_IN` | en el conjunto / fuera del conjunto |
| `IS_NULL` / `NOT_NULL` | ausente / presente |
| `GT` / `GTE` | mayor que / mayor o igual que |
| `LT` / `LTE` | menor que / menor o igual que |
| `BETWEEN` / `NOT_BETWEEN` | en el rango [a,b] / fuera del rango |

### `normas`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER PK | |
| `codigo` | VARCHAR | Clave interna: `'DL26_2021'` \| `'LPACAP'` \| `'RD337_2014'` |
| `titulo` | VARCHAR | Texto completo: `'Decreto-ley 26/2021, de 14 de diciembre'` |
| `url_eli` | VARCHAR nullable | URL texto consolidado BOE/BOJA |

---

## Interfaz del Supervisor — principios de diseño

El Supervisor no es un técnico informático. Trabaja con normas y expedientes, no con
código ni esquemas de datos. El formulario de alta de reglas es la pieza más crítica
del sistema desde el punto de vista de la usabilidad — si intimida, las reglas se
definen mal o no se definen.

### Compilación en tiempo real como mecanismo de confianza

Cada campo que el Supervisor rellena actualiza inmediatamente una vista en lenguaje
natural de la regla que está construyendo. No al guardar — mientras escribe, en
tiempo real. Ejemplo:

> *Selecciona: acción = INICIAR, sujeto = FASE, tipo = Información Pública*
> → «Esta regla afecta a INICIAR para Fase de tipo Información Pública»
>
> *Añade condición: ia_siglas IN ['AAU', 'AAUS']*
> → «...cuando el instrumento ambiental sea AAU o AAUS»
>
> *Añade condición: doc_declaracion_ausencia_dup EQ false*
> → «...y el documento de declaración de ausencia de DUP no esté presente»
>
> *Selecciona efecto = BLOQUEAR, norma = Decreto-ley 26/2021, artículo = DA4*
> → «**Bloquea** la acción. Referencia: Disposición Adicional 4ª del Decreto-ley 26/2021»

El Supervisor en todo momento puede leer en lenguaje natural lo que está configurando.
Si la frase no coincide con su intención, hay un error en la regla antes de guardarla.

### Implicaciones para el diseño del formulario

- **Nada de campos de texto libre** para definir la regla — todo son selects, dropdowns
  y valores del catálogo. El lenguaje natural lo genera el sistema, no lo escribe el usuario.
- **Variables como dropdown del catálogo** (`catalogo_variables`). Si la variable que
  el Supervisor necesita no aparece, significa que falta código — no que pueda escribirla
  a mano.
- **Operadores en texto natural** en el selector: no "EQ" sino "igual a"; no "NOT_IN"
  sino "fuera del conjunto".
- **Artículo de la norma**: campo de texto libre controlado (corto, formato validado:
  `"24.3"`, `"DA4"`, `"DF2"`). El único campo sin dropdown — no hay forma de catalogar
  todos los artículos posibles de todas las normas.
- **Vista previa persistente** en la parte derecha o inferior del formulario, siempre
  visible, se actualiza en cada cambio sin necesidad de acción del usuario.

### El formulario como barrera de calidad

Una regla mal definida puede bloquear expedientes legítimos o permitir acciones
indebidas. El formulario es la última oportunidad para detectarlo antes de que entre
en producción. La vista en lenguaje natural es precisamente esa barrera: si el
Supervisor puede leer la regla y entenderla, puede validar que es correcta.

---

## Problemas que resuelve respecto al diseño actual

| Problema con diseño actual | Solución con motor agnóstico |
|---|---|
| `intermunicipal` requería query especial en el motor | ContextAssembler lo computa y pasa como variable |
| `documentos_tarea` (INCORPORAR multi-doc) no accesible al motor | ContextAssembler pasa `tiene_docs_incorporar: True` |
| No existía `VARIABLE_TRAMITE` ni `VARIABLE_FASE` como criterios | Desaparecen — todo son variables del dict |
| `_TIPOS_REQUIEREN_DOC_PRODUCIDO` hardcodeado en motor | ContextAssembler lo computa según tipo de tarea |
| Plazos/fechas inaccesibles al motor | ContextAssembler pasa `plazo_vencido`, `dias_transcurridos`, etc. |
| `solicitud.estado` sin integridad referencial | Pasa como variable; su validez la gestiona BDDAT |

---

## Modificabilidad de fechas de inicio y fin — preguntas abiertas

Las fechas `fecha_inicio` y `fecha_fin` de las entidades SFTT no son necesariamente
invariantes absolutas. Una posible lectura es que son modificables siempre que sean
coherentes con los elementos del interior del contenedor y con los hechos factuales
invariantes del expediente.

Si las modificaciones se propagan desde el interior hacia el exterior — modifico la
tarea, luego el trámite que la contiene, luego la fase — y esas fechas son operacionales
(cuándo ocurrió el trabajo) y no administrativas (cuándo se emitió un acto formal), la
modificación podría ser legítima sin violar ninguna regla de negocio real.

Esto abre una distinción que no está resuelta en el diseño:

**¿Las fechas de SFTT son administrativas u operacionales?**
Una fecha administrativa es un hecho jurídico: la fecha en que se notificó una
resolución, en que se abrió un trámite de información pública. No se modifica sin
consecuencias legales. Una fecha operacional es la fecha en que el tramitador registró
que empezó o terminó un trabajo interno. Es más corregible.

**El principio "todo permitido excepto lo expresamente prohibido" complica esto.**
Bajo ese principio, un usuario podría crear e iniciar varios contenedores en paralelo
como preparación o como estructura provisional del procedimiento, sin que nada
administrativo haya ocurrido realmente. En ese caso, "DESINICIAR" no estaría
deshaciendo un acto administrativo — estaría limpiando una estructura preparatoria.
¿Tiene `fecha_inicio` el mismo peso jurídico en todos los contextos, o depende de
si hay hechos factuales consolidados dentro del contenedor?

**Preguntas sin responder:**
- ¿Existe una distinción real entre fecha operacional y fecha administrativa en SFTT,
  o toda fecha de inicio/fin tiene la misma naturaleza jurídica?
- ¿Es la coherencia con el interior suficiente como condición, o hacen falta condiciones
  adicionales (rastro externo, documentos emitidos, notificaciones enviadas)?
- ¿DESINICIAR y DESFINALIZAR son eventos del motor con sus propias reglas, o son
  operaciones de corrección de datos con su propio mecanismo fuera del motor?
- Si el contenedor tiene `fecha_inicio` pero ninguno de sus hijos ha sido iniciado ni
  tiene documentos, ¿es su `fecha_inicio` un hecho administrativo o solo un marcador
  operacional corregible?

---

## Deuda técnica identificada en diseño actual

### Criterios BDDAT-específicos a eliminar del motor
- `EXISTE_FASE_CERRADA` — el motor conoce el modelo Fase
- `EXISTE_TAREA_TIPO` — el motor conoce el modelo Tarea
- `_check_finalizar_tarea` — hardcoded con lógica de BDDAT
- `EXISTE_DOCUMENTO_TIPO`, `EXISTE_DOC_ORGANISMO` — stubs pendientes

### Valores inline sin integridad referencial
- `Solicitud.estado` — VARCHAR con `EN_TRAMITE|RESUELTA|DESISTIDA|ARCHIVADA`, sin FK a tabla.
  Si cambia en Python, los registros en `condiciones_regla` quedan huérfanos sin detección.
- `_TIPOS_REQUIEREN_DOC_PRODUCIDO` / `_TIPOS_REQUIEREN_DOC_USADO` — sets hardcodeados
  en `motor_reglas.py`; son propiedades funcionales de `TipoTarea` que deberían estar en BD.

### Estados derivados (@property) sin criterio genérico
Los `@property` (`planificada`, `en_curso`, `ejecutada`) son el contrato correcto del modelo.
El problema es que el motor actual no puede referenciarlos en reglas configurables.
Con el rediseño agnóstico esto deja de ser problema: ContextAssembler los computa y los pasa.

---

## Controlador de fechas — diseño cerrado

**Estado:** Diseño completado en `docs/DISEÑO_FECHAS_PLAZOS.md` (sesión 2026-04-01/02).
`docs/NORMATIVA_PLAZOS.md` es la fuente de verdad normativa (LPACAP + sectorial AT).

**Decisiones adoptadas:**
1. `PLAZO_DIAS`/`TIPO_DIAS` de ESPERAR_PLAZO → catálogo de plazos en tabla propia (`§3.2`)
2. Motor evalúa `plazo_vencido` como condición informativa; el bloqueo formal queda pendiente de §4
3. Fecha de vencimiento se persiste en `fecha_limite` con semántica cerrada (`§3.5`)
4. `plazos.py` es capa separada — no parte del ContextAssembler (`§4`)

---

## Issues M2 afectados

### #290 — INCORPORAR multi-doc (tabla documentos_tarea)
**Estado: desbloqueado** — diseño del controlador de fechas completado (`docs/DISEÑO_FECHAS_PLAZOS.md`).
La validación de FINALIZAR para INCORPORAR migrará del motor actual
(`doc_producido_id IS NULL → BLOQUEAR`) al ContextAssembler (`tiene_docs_incorporar`).
Pendiente de implementar junto con el rediseño del motor agnóstico.

### #279 — Campos extra en Proyecto (tecnología, kV, kVA, tipo suelo...)
**Estado: requiere diseño previo.** Preguntas abiertas:
- ¿Qué campos van en `Proyecto` y cuáles en tabla catálogo propia?
- ¿Tipo de suelo es enum o tabla `tipos_suelo`?
- ¿Tensión/potencia son numéricos libres o rangos normalizados?
- ¿Qué reglas del motor los necesitan?

Con motor agnóstico, cualquier campo nuevo en `Proyecto` es automáticamente accesible
via ContextAssembler — no requiere cambios en el motor.

### #289 — Context Builders (Capa 2 generación escritos)
**Estado: bloqueado** por #279 y falta de datos reales. Los builders beben de campos
extra de proyecto que aún no existen.

---

## Orden de trabajo recomendado

Seis pasos, de más interior a más exterior. Actualizado sesión 2026-04-16 (no hay EventHandler, esquema tablas cerrado):

1. ✅ **MRA — API + esquema tablas** — firma `evaluar(accion, sujeto, tipo_sujeto_id, variables)`, `EvaluacionResult` con `variables_trigger`/`norma_compilada`/`url_norma`, tablas `normas`/`reglas_motor`/`condiciones_regla`/`catalogo_variables` cerradas. Sin capa EventHandler — patrón dos líneas en ruta Flask.
2. **MRA — implementación motor** — refactor `motor_reglas.py`: nueva firma, nuevo `EvaluacionResult`, eliminar imports BDDAT y criterios específicos (`EXISTE_FASE_CERRADA`, `EXISTE_TAREA_TIPO`, `_check_finalizar_tarea`)
3. **Migración manual** — crear tablas `normas`, `reglas_motor`, `condiciones_regla`, `catalogo_variables` (esquema cerrado en §Esquema de tablas). Sin tabla `disparadores`.
4. **Variables — recatalogación** — revisar `DISEÑO_CONTEXT_ASSEMBLER.md`, decidir primeras variables implementables para el primer sprint; seed de `catalogo_variables`; resolver modelo de BD de `Proyecto`/`Solicitud` para variables `dato` → issue #279
5. **ContextAssembler — implementación** — `app/services/context_assembler.py` con las variables del paso 4; integrar `plazos.py`
6. **Fuego real** — seed `normas` + 2-3 reglas + condiciones; wiring dos líneas en 2-3 rutas Flask; prueba con expediente real

Issues afectados (no desbloquear hasta paso 5):
- **#279** — campos extra Proyecto (tensión, potencia, tipo suelo): modelo de BD se define en paso 4
- **#290** — INCORPORAR multi-doc: implementar tras paso 2 (refactor motor)
- **#289** — Context Builders: bloqueado por #279 y datos reales

---

## Advertencia: el refactor tiene riesgos reales

Esta sección recoge una reflexión crítica sobre si el rediseño es realmente lo correcto ahora,
para no tomarlo como decisión automática en la próxima sesión.

### Lo que sí es claramente mejor

El motor actual mezcla lógica de evaluación con conocimiento del dominio BDDAT. Eso no es
una opinión de arquitectura — es un problema práctico: cada vez que aparece una variable nueva
(intermunicipal, multi-doc, plazos) hay que tocar el motor. Con el diseño agnóstico desaparece.

El momento es el mejor posible: `reglas_motor` está vacía. Si se espera a tener 50 reglas en BD
referenciando `EXISTE_FASE_CERRADA`, el coste de migración es mucho mayor.

### Lo que hay que tener claro antes de ejecutar

**El ContextAssembler no es más simple que lo que tenemos.** Es la misma complejidad, reubicada.
El motor actual sube el árbol ESFTT y evalúa condiciones. El ContextAssembler sube el árbol ESFTT
y computa variables. La lógica es equivalente — lo que cambia es quién la contiene y dónde vive.
Eso tiene valor arquitectural, pero no reduce líneas de código ni elimina casos especiales.

**Riesgo concreto:** hacer el refactor del motor sin tener el diseño del ContextAssembler definido
significa desmontar algo que funciona sin tener claro qué lo reemplaza.

### La alternativa incremental

Existe un camino que da el 80% del beneficio con el 20% del trabajo:

1. Añadir `VARIABLE_SOLICITUD` y `VARIABLE_TRAMITE` como criterios genéricos — elimina la
   asimetría actual sin refactorizar la arquitectura
2. Mover `_TIPOS_REQUIEREN_DOC_PRODUCIDO` a columnas en `tipos_tareas` — saca lógica de
   dominio del motor sin tocar el diseño
3. Migrar `Solicitud.estado` a FK — resuelve el problema de integridad referencial

No es tan elegante, pero es ejecutable sin diseñar el ContextAssembler primero.

### Conclusión

Hacer el refactor completo **solo si** el diseño del ContextAssembler está cerrado antes:
qué variables existen, cómo se declaran, qué puede configurar el Supervisor.
Sin ese diseño, el refactor es un salto al vacío. Si el diseño no está listo, el camino
incremental es más prudente.

**Próxima sesión:** explorar la casuística real de BDDAT para definir el alcance del
ContextAssembler: qué variables necesita computar, de dónde las obtiene, y qué parte
debe poder editar el Supervisor.
