> **Indice:** [ANALISIS_167_INDICE.md](ANALISIS_167_INDICE.md)

## 3) Riesgos e inconsistencias

Analisis sistematico de riesgos tecnicos, inconsistencias con el codigo actual
y puntos que requieren decision explicita antes de implementar.

### 3.1 Riesgos criticos — Bloquean implementacion si no se resuelven

#### R1. Cambio semantico en motor de reglas: tipos atomicos vs. combinados

**Problema:** La funcion `_criterio_existe_tipo_solicitud()` en `motor_reglas.py` (linea 458)
comprueba si una solicitud tiene un tipo atomico concreto via la tabla puente M:N:

```python
# Actual (motor_reglas.py:462-466)
resultado = (db.session.query(SolicitudTipo)
             .join(TipoSolicitud, SolicitudTipo.tiposolicitudid == TipoSolicitud.id)
             .filter(SolicitudTipo.solicitudid == ctx.solicitud.id,
                     TipoSolicitud.siglas == siglas)
             .first())
```

Una solicitud AAP+AAC tiene DOS filas en `solicitudes_tipos` (una para AAP, otra para AAC).
La regla `EXISTE_TIPO_SOLICITUD:AAP` devuelve `True` para esa solicitud.

**Tras el cambio:** `Solicitud.tipo_solicitud_id` apunta a un tipo combinado `AAP_AAC`.
La comparacion directa `solicitud.tipo_solicitud.siglas == 'AAP'` devolveria `False`.

Actualmente no hay reglas JSON que invoquen este criterio (solo esta registrado en Python),
pero la implementacion DEBE reescribirse porque `SolicitudTipo` desaparece. La reescritura
requiere decidir la semantica de la comparacion con tipos combinados.

**Opciones de diseno:**

| Opcion | Mecanismo | Pros | Contras |
|--------|-----------|------|---------|
| A | `'AAP' in siglas.split('_')` | Simple | Fragil si las siglas usan `_` internamente |
| B | Tabla auxiliar `tipo_solicitud_componentes` | Consulta inversa exacta | Tabla adicional, complejidad |
| C | Usar siglas combinadas en las reglas (`AAP_AAC`) | Semantica limpia | Cada combinacion necesita regla propia |
| D | Campo `componentes` JSON en `tipos_solicitudes` | Flexible | Requiere parsear JSON en cada evaluacion |

> **Recomendacion:** Opcion C. Una solicitud AAP_AAC es un procedimiento distinto de AAP
> — tiene fases y plazos propios. Las reglas deben reflejar esa realidad. Opcion A como
> fallback si hay reglas que deben matchear "cualquier solicitud que incluya AAP".

**Decision necesaria antes de implementar:** Cual es la semantica correcta de
`EXISTE_TIPO_SOLICITUD` con tipos combinados.

---

#### R2. Atomicidad migracion + codigo al eliminar `solicitudes_tipos`

**Problema:** La tabla `solicitudes_tipos` tiene queries activas en 4 ficheros:

| Fichero | Funcion | Lineas | Tipo de uso |
|---------|---------|--------|-------------|
| `services/motor_reglas.py` | `_criterio_existe_tipo_solicitud()` | 462-466 | JOIN + filter |
| `routes/vista3.py` | `_get_solicitudes_con_stats()` | 160-161 | JOIN + filter |
| `routes/vista3.py` | `crear_solicitud()` / eliminar | 491, 519 | INSERT / DELETE |
| `routes/wizard_expediente.py` | `crear_expediente_completo()` | 357-360 | INSERT en bucle |
| `routes/api_expedientes.py` | endpoint tipos por solicitud | 420-421 | JOIN + filter |

Si la migracion elimina la tabla antes de que el codigo deje de usarla, cualquier
acceso a esas rutas lanza `ProgrammingError: relation "solicitudes_tipos" does not exist`.

**Mitigacion:** Una sola migracion que:
1. Crea `Solicitud.tipo_solicitud_id` (nullable inicialmente)
2. Backfill: para cada solicitud, deduce el tipo combinado desde `solicitudes_tipos`
3. Convierte `tipo_solicitud_id` a NOT NULL
4. DROP `solicitudes_tipos`

El deploy de codigo (5 ficheros) y migracion debe ser atomico. En entorno dev
esto es trivial (se ejecuta todo junto), pero debe documentarse para evitar
estados intermedios.

---

#### R3. Backfill de `tipo_solicitud_id` en solicitudes existentes

**Problema:** El modelo `solicitudes.py` tiene un comentario explicito (linea 65):
`"v3.0: ELIMINADO tipo_solicitud_id (movido a SOLICITUDES_TIPOS N:M)"`.
El campo existio, fue eliminado, y ahora se restaura.

Aunque estamos en entorno de desarrollo, SI existen solicitudes de prueba
creadas via wizard. Estas solicitudes tienen sus tipos SOLO en `solicitudes_tipos`.

**Casuistica del backfill:**

| Caso | Ejemplo | Mapeo |
|------|---------|-------|
| Solicitud con 1 tipo atomico | Solo AAP | FK directa a `AAP` |
| Solicitud con N tipos atomicos | AAP + AAC | Buscar tipo combinado `AAP_AAC` |
| Combinacion no prevista | Combinacion sin tipo combinado definido | **Requiere decision** |

**Mitigacion:** Script en la migracion que haga el mapeo automatico:
- Obtener los tipos atomicos de cada solicitud desde `solicitudes_tipos`
- Si es un solo tipo, mapeo directo
- Si son N tipos, buscar tipo combinado que contenga exactamente esos componentes
- Los casos no mapeables se loguean como WARNING para revision manual

---

### 3.2 Riesgos altos — Requieren atencion durante implementacion

#### R4. Amplitud del rename `tipos_escritos` → `plantillas`

**Problema:** El rename afecta simultaneamente multiples capas:

| Capa | Elementos a renombrar |
|------|-----------------------|
| Tabla PostgreSQL | `tipos_escritos` → `plantillas` |
| Constraints FK | `fk_tipos_escritos_*` (x4) |
| Constraint unique | `uq_tipos_escritos_codigo` |
| Clase Python | `TipoEscrito` → `Plantilla` |
| Fichero Python | `tipos_escritos.py` → `plantillas.py` |
| Imports directos | `__init__.py` (linea 25), `admin_plantillas/routes.py` (linea 26) |
| Variables en rutas | `tipo`/`tipo_escrito` → `plantilla` (routes + templates) |
| Strings en mensajes | `generador_escritos.py` (lineas 86, 117) |

**Riesgo:** Olvidar una referencia produce `ImportError`, `AttributeError` o query
contra tabla inexistente. Los errores no se detectan hasta que se ejecuta la ruta concreta.

**Mitigacion:** Busqueda exhaustiva post-rename con grep de `tipo.escrito` y `tipos.escritos`.
No dejar alias de retrocompatibilidad — en entorno dev los errores deben ser ruidosos.

---

#### R5. Principio de escape — declarado pero sin diseno de implementacion

**Problema:** El principio de escape se declaro como transversal ("toda cascada, filtro
y regla debe tener via de escape") pero no se ha definido COMO se implementa en UI.

Los selectores en cascada ESFTT (A0) filtran opciones segun whitelist. Si el supervisor
necesita una combinacion no prevista, el selector no debe ser un callejon sin salida.

**Opciones de implementacion:**

| Opcion | Mecanismo | Implicacion en API |
|--------|-----------|---------------------|
| Toggle "Mostrar todos" | Switch en cada selector que desactiva filtro | Endpoint devuelve `{compatibles, otros}` |
| Entrada "Otros..." | Opcion fija al final que abre selector completo | Segundo endpoint sin filtro |
| Bypass global | Checkbox que desbloquea todos los selectores | Parametro `?sin_filtro=1` |

**Impacto:** Afecta al diseno de los endpoints AJAX de cascada ANTES de implementarlos.
El endpoint `GET /api/.../tipos-solicitud?tipo_expediente_id=X` debe devolver tambien
las opciones fuera de whitelist si hay mecanismo de escape.

**Decision necesaria:** Mecanismo concreto antes de implementar A0.

> **Recomendacion:** Opcion 1 (toggle). El endpoint devuelve dos listas (`compatibles` +
> `otros`). El JS renderiza con estilo diferenciado (badge de advertencia en los `otros`).
> Sencillo, no requiere endpoints adicionales y el escape es explicito.

---

#### R6. Bug preexistente: `__str__` en modelo `Documento` referencia campo eliminado

**Problema:** El campo `nombre_display` fue eliminado de la tabla `documentos` en la
migracion del #191 (`fd2bc02d2474`). El propio modelo lo documenta en linea 87:
`"v4.1: ELIMINADOS origen, nombre_display"`. Pero `__str__` aun lo referencia:

```python
# documentos.py:172-174
def __str__(self):
    """Representación legible para interfaz."""
    return self.nombre_display or f'Documento {self.id}'
```

**Impacto:** `AttributeError` cuando Python convierte un `Documento` a string
(logging, f-strings, mensajes de error). No afecta al rendering de templates porque
la ruta `pool_documentos` calcula `nombre_display` como clave de dict desde la URL
(`expedientes/routes.py:549-559`), no desde el modelo.

**Accion:** Corregir `__str__` antes de iniciar implementacion del #167. La generacion
(B4) registra documentos en pool → si hay logging que use `str(documento)`, crash.
Es un fix independiente, no incluir en la migracion de #167.

---

### 3.3 Riesgos medios — Gestionables con precaucion

#### R7. Eliminacion de `campos_catalogo` → ventana sin tokens de Capa 2

**Problema:** Actualmente `_build_tokens()` en `admin_plantillas/routes.py` (linea 87-89)
fusiona `CAMPOS_BASE` (12 campos fijos de Capa 1) con `tipo_escrito.campos_catalogo`
(campos adicionales definidos por plantilla). Al eliminar `campos_catalogo`, el panel
de tokens mostrara SOLO los 12 campos base hasta que se implemente Capa 2
(Context Builders).

**Impacto:** Si ya hay plantillas registradas con `campos_catalogo` rellenado,
el supervisor pierde visibilidad de esos tokens en la interfaz. Las plantillas
seguiran funcionando si los tokens existen en el contexto, pero no se mostraran
en el panel copiable.

**Mitigacion:** Antes de ejecutar la migracion, exportar los `campos_catalogo`
existentes como referencia para la futura implementacion de Context Builders.
Consulta: `SELECT codigo, nombre, campos_catalogo FROM tipos_escritos WHERE campos_catalogo IS NOT NULL`.

---

#### R8. Seed de whitelist desde JSON incompleto

**Problema:** El usuario confirmo que `Estructura_fases_tramites_tareas.json`
"no es absolutamente completo" y "es esencialmente correcto pero no exhaustivo".

El seed inicial de las 3 tablas whitelist (`expedientes_solicitudes`,
`solicitudes_fases`, `fases_tramites`) estara incompleto por definicion.
Las combinaciones faltantes haran que los selectores en cascada no ofrezcan
ciertas opciones validas.

**Mitigacion:**
- El principio de escape (R5) mitiga esto si se implementa
- El CRUD de whitelist editable por supervisor (previsto en C4) permite completar
- Priorizar que el CRUD de whitelist este disponible desde el primer momento,
  no como fase posterior

---

#### R9. Cadena de downgrade en Alembic

**Problema:** La migracion `20c5d1e9d782` crea la tabla `tipos_escritos`. Si una nueva
migracion renombra la tabla a `plantillas`, el downgrade de `20c5d1e9d782` intentaria
`DROP TABLE tipos_escritos` sobre una tabla que ya no existe con ese nombre.

**Mitigacion:** No tocar migraciones antiguas. La nueva migracion que renombra tiene
su propio downgrade que revierte el rename. La cadena completa de downgrades
(revertir TODO hasta el inicio) puede no funcionar, pero eso es aceptable en
entorno de desarrollo sin despliegues en produccion.

---

#### R10. Supervivencia del codigo embebido en pipeline .docx → PDF

**Problema:** La trazabilidad C3 define dos vias: custom properties (principal)
y QR en pie de pagina (fallback). El pipeline completo es:
`.docx` → edicion en Writer → portafirmas → `.pdf` firmado.

| Via | Edicion Writer | Conversion a PDF | Portafirmas |
|-----|:-:|:-:|:-:|
| Custom properties | Preservadas | **Depende del conversor** | **Desconocido** |
| QR en pie de pagina | Preservado (es imagen) | Preservado | Preservado |

**Riesgo:** Si las custom properties no sobreviven la conversion PDF del portafirmas,
la via principal de trazabilidad se pierde silenciosamente. El QR seria la unica
via fiable.

**Mitigacion:** Probar el pipeline completo con un documento real antes de invertir
esfuerzo en la implementacion de custom properties. Si no sobreviven, el QR pasa
de "fallback" a "via principal" y las custom properties pasan a "complemento local".

---

### 3.4 Inconsistencias detectadas en el analisis

#### I1. Endpoints de generacion en `vista3.py` vs. deprecacion de Vista 3

**Inconsistencia:** La seccion B1-B6 define endpoints como
`POST /api/vista3/tarea/<id>/generar` y `GET /api/vista3/tarea/<id>/plantillas`.
Pero la seccion 2.6 dice que la vista de acordeones (Vista 3) esta DEPRECADA
y los cambios se implementaran en la vista breadcrumb BC.

**Resolucion necesaria:** Decidir donde van los endpoints de generacion:
- En `routes/vista3.py` (incoherente con deprecacion)
- En un fichero API dedicado (ej: `routes/api_escritos.py`)
- En el futuro fichero de vista BC

Actualizar las rutas en el mapa de necesidades tras decidir.

---

#### I2. Nomenclatura de ficheros — ambiguedad del separador espacio

**Observacion:** La convencion de Cabo 3 usa espacio como separador entre niveles ESFTT,
pero `nombre_en_plantilla` puede contener espacios internos ("Requerimiento subsanacion").
Ejemplo: `Redactar Requerimiento subsanacion Resolucion AAP_AAC AT-13465-24.docx`
— no es parseable para distinguir "Requerimiento subsanacion" (un tramite) de dos
niveles separados.

El documento establece que "BDDAT siempre compone, nunca parsea" — correcto y coherente.

**Impacto actual:** Ninguno. Documentar la limitacion para que futuras funcionalidades
(ej: buscador de documentos por componentes del nombre) no asuman parseabilidad.

---

#### I3. Secuencial automatico (`_2`, `_3`) sin mecanismo definido

**Observacion:** Cabo 3 menciona "secuencial automatico cuando ya existe un documento
con el mismo nombre" pero no define:
- Donde se comprueba (filesystem directo? BD? ambos?)
- Formato exacto (antes de `.docx`? despues de variante?)
- Comportamiento ante acceso concurrente (dos usuarios generan simultaneamente)

**Resolucion necesaria:** Definir mecanismo concreto antes de implementar B4.

> **Propuesta:** Comprobar en filesystem. Sufijo ` (2)`, ` (3)` antes de `.docx`.
> Sin lock especial — la probabilidad de colision en acceso concurrente es minima
> dado el volumen de usuarios esperado.

---

#### I4. FK `plantilla_id` en tabla `documentos` — sin decidir

**Observacion:** La seccion C3 dice "pendiente de decidir si la FK justifica la migracion".
Sin FK, la unica trazabilidad plantilla→documento es el codigo embebido.
Si el documento se edita y se pierde el codigo (usuario borra el QR, o las custom
properties no sobreviven la conversion), no hay forma de saber que plantilla lo genero.

> **Recomendacion:** Anadir `plantilla_id` FK nullable en `documentos`. Es una columna
> mas en una migracion que ya toca varias tablas. El coste es minimo y la redundancia
> aporta verificacion cruzada (C3 ya lo menciona como posibilidad).

---

#### I5. `filtros_adicionales` JSONB sin schema de validacion

**Observacion:** La decision 6 de Cabo 1+2 mantiene `filtros_adicionales` para
"absorber futuro sin migracion". Pero no define que claves son validas,
que tipo tiene cada valor, ni quien lee este campo.

**Impacto actual:** Ninguno — no hay codigo que lea `filtros_adicionales`.
Documentar que necesita schema explicito antes del primer uso.

---

### 3.5 Resumen cuantitativo de riesgos

| Nivel | Cant. | IDs | Requiere decision previa |
|-------|:-----:|-----|:------------------------:|
| Critico | 3 | R1, R2, R3 | Si (todos) |
| Alto | 3 | R4, R5, R6 | R5 (decidir escape), R6 (fix previo) |
| Medio | 4 | R7, R8, R9, R10 | No (gestionables) |
| Inconsistencia | 5 | I1-I5 | I1 y I3 (si) |

**Decisiones bloqueantes antes de implementar:**

1. **R1:** Semantica de `EXISTE_TIPO_SOLICITUD` con tipos combinados
2. **R3:** Estrategia de backfill de `tipo_solicitud_id` (script en migracion)
3. **R5:** Mecanismo concreto del principio de escape en selectores en cascada
4. **I1:** Ubicacion de endpoints de generacion (vista3.py, API dedicada, o vista BC)
5. **I3:** Mecanismo de secuencial automatico para nombres duplicados

**Acciones previas a la implementacion (no requieren decision):**

6. **R6:** Corregir `__str__` en `Documento` (fix independiente)
7. **R7:** Exportar `campos_catalogo` existentes antes de DROP

---
