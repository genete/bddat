# Implementación #347 — Defensividad del backend ante catálogo ausente o BD no disponible

> Documento estratégico. Generado 2026-04-30. Actualizar al cerrar cada sesión.

---

## Contexto

Tres tipos de fallo estructural no están cubiertos hoy:

| Tipo | Causa | Síntoma actual |
|---|---|---|
| Infraestructura | BD caída o tabla inexistente | `OperationalError` / `ProgrammingError` → HTTP 500 sin cuerpo JSON |
| Registro ausente | Tabla existe, falta un registro esperado | SQLAlchemy devuelve `None` → `AttributeError` 10 líneas después |
| FK frágil | `catalogo_plazos.tipo_elemento_id` es INTEGER; un borrado+reinserción cambia el ID | Plazos incorrectos silenciosos |

El motor de reglas resolvió el tercer problema desde el principio usando el campo `sujeto` (patrón string estable, ver `motor_reglas.py:96`). `catalogo_plazos` es el único sitio del proyecto con FK polimórfica por entero.

**Desbloquea:** #348 (seeds en migraciones — `flask db upgrade` sobre BD vacía → 100 % funcional).

---

## Decisiones técnicas aprobadas

| # | Decisión | Elección |
|---|----------|----------|
| A | Campo estable en `catalogo_plazos` | `tipo_elemento_codigo VARCHAR(50) NOT NULL` — almacena el `.siglas` (SOLICITUD) o `.codigo` (FASE/TRAMITE/TAREA) del tipo correspondiente |
| B | Columna `tipo_elemento_id` | Conservar por ahora (no borrar en este issue). Marcar como deprecated en comentario. Eliminar en issue posterior una vez verificado. |
| C | Índices a sustituir | Eliminar `idx_catalogo_plazos_tipo_elem` e `idx_catalogo_plazos_tipo_orden`. Crear `idx_catalogo_plazos_tipo_codigo` y `idx_catalogo_plazos_tipo_orden_v2` usando `tipo_elemento_codigo`. |
| D | Navegación ORM en `plazos.py` | `_get_tipo_elemento_id` → `_get_tipo_elemento_codigo`. Navega la relación del elemento (lazy load ya existente) en lugar de leer el campo `_id`. |
| E | Fichero del manifiesto | `app/checks/catalogo_requerido.py`. El dict `REGISTROS_REQUERIDOS` mapea clase modelo → lista de códigos esperados. |
| F | Comportamiento en arranque con BD incompleta | La app **sigue arrancando** pero loguea ERROR con la lista exacta de lo que falta. No bloquea arranque en desarrollo. |
| G | Manejador global de errores de BD | En `app/__init__.py` — captura `OperationalError` y `ProgrammingError`, devuelve HTTP 503 con JSON `{"error": "...", "code": "DB_ERROR"}`. Complementa (no sustituye) el manejo en cada servicio. |
| H | Degradación en servicios | `plazos.py` y `seguimiento.py`: capturar `ProgrammingError` + guard `if None` → `log.warning` + devolver valor degradado. Patrón a documentar en `REGLAS_DESARROLLO.md`. |

---

## División en sesiones

### Sesión 1 — Fix FK frágil: migración + modelo + plazos.py

**Objetivo:** `catalogo_plazos` pasa a usar `tipo_elemento_codigo` como discriminador estable.

**Ficheros:**
- `migrations/versions/XXX_347_catalogo_plazos_codigo.py` (NUEVO)
- `app/models/catalogo_plazos.py` (añadir columna, actualizar índices, marcar deprecated)
- `app/services/plazos.py` (reemplazar `_get_tipo_elemento_id` → `_get_tipo_elemento_codigo`)

**Migración — `upgrade()`:**
```python
# 1. Añadir columna nullable inicialmente
op.add_column('catalogo_plazos',
    sa.Column('tipo_elemento_codigo', sa.String(50), nullable=True,
              comment='Código estable del tipo (siglas en SOLICITUD, codigo en el resto). '
                      'Reemplaza tipo_elemento_id como discriminador — ver #347'),
    schema='public'
)

# 2. Backfill por tipo
conn = op.get_bind()
conn.execute(sa.text("""
    UPDATE public.catalogo_plazos cp
    SET tipo_elemento_codigo = ts.siglas
    FROM public.tipos_solicitudes ts
    WHERE cp.tipo_elemento = 'SOLICITUD' AND cp.tipo_elemento_id = ts.id
"""))
conn.execute(sa.text("""
    UPDATE public.catalogo_plazos cp
    SET tipo_elemento_codigo = tf.codigo
    FROM public.tipos_fases tf
    WHERE cp.tipo_elemento = 'FASE' AND cp.tipo_elemento_id = tf.id
"""))
conn.execute(sa.text("""
    UPDATE public.catalogo_plazos cp
    SET tipo_elemento_codigo = tt.codigo
    FROM public.tipos_tramites tt
    WHERE cp.tipo_elemento = 'TRAMITE' AND cp.tipo_elemento_id = tt.id
"""))
conn.execute(sa.text("""
    UPDATE public.catalogo_plazos cp
    SET tipo_elemento_codigo = tarea.codigo
    FROM public.tipos_tareas tarea
    WHERE cp.tipo_elemento = 'TAREA' AND cp.tipo_elemento_id = tarea.id
"""))

# 3. Verificar que el backfill es completo antes de añadir NOT NULL
conn.execute(sa.text("""
    DO $$ BEGIN
        IF EXISTS (
            SELECT 1 FROM public.catalogo_plazos WHERE tipo_elemento_codigo IS NULL
        ) THEN RAISE EXCEPTION 'Backfill incompleto: filas sin tipo_elemento_codigo'; END IF;
    END $$
"""))
op.alter_column('catalogo_plazos', 'tipo_elemento_codigo', nullable=False, schema='public')

# 4. Sustituir índices
op.drop_index('idx_catalogo_plazos_tipo_elem',  table_name='catalogo_plazos', schema='public')
op.drop_index('idx_catalogo_plazos_tipo_orden', table_name='catalogo_plazos', schema='public')
op.create_index('idx_catalogo_plazos_tipo_codigo',
    'catalogo_plazos', ['tipo_elemento', 'tipo_elemento_codigo'], schema='public')
op.create_index('idx_catalogo_plazos_tipo_orden_v2',
    'catalogo_plazos', ['tipo_elemento', 'tipo_elemento_codigo', 'orden'], schema='public')
```

**Migración — `downgrade()`:**
```python
op.drop_index('idx_catalogo_plazos_tipo_codigo',   table_name='catalogo_plazos', schema='public')
op.drop_index('idx_catalogo_plazos_tipo_orden_v2', table_name='catalogo_plazos', schema='public')
op.create_index('idx_catalogo_plazos_tipo_elem',  'catalogo_plazos', ['tipo_elemento', 'tipo_elemento_id'], schema='public')
op.create_index('idx_catalogo_plazos_tipo_orden', 'catalogo_plazos', ['tipo_elemento', 'tipo_elemento_id', 'orden'], schema='public')
op.drop_column('catalogo_plazos', 'tipo_elemento_codigo', schema='public')
```

**Cambios en `catalogo_plazos.py`:**
```python
# Añadir campo
tipo_elemento_codigo = db.Column(
    db.String(50), nullable=False,
    comment='Código estable del tipo (siglas/codigo). Reemplaza tipo_elemento_id — ver #347',
)

# Marcar tipo_elemento_id como deprecated
tipo_elemento_id = db.Column(
    db.Integer, nullable=False,
    comment='[DEPRECATED #347] Usar tipo_elemento_codigo. Se elimina en issue posterior.',
)

# Actualizar __table_args__ para usar los nuevos índices
__table_args__ = (
    db.Index('idx_catalogo_plazos_tipo_codigo',   'tipo_elemento', 'tipo_elemento_codigo'),
    db.Index('idx_catalogo_plazos_tipo_orden_v2', 'tipo_elemento', 'tipo_elemento_codigo', 'orden'),
    {'schema': 'public'},
)

# Actualizar __repr__
def __repr__(self):
    return f'<CatalogoPlazo {self.tipo_elemento}:{self.tipo_elemento_codigo} {self.plazo_valor}{self.plazo_unidad}>'
```

**Cambios en `plazos.py`:**
```python
# Reemplazar _TIPO_ID_CAMPO por _TIPO_CODIGO_REL
_TIPO_CODIGO_REL = {
    'SOLICITUD': ('tipo_solicitud', 'siglas'),
    'FASE':      ('tipo_fase',      'codigo'),
    'TRAMITE':   ('tipo_tramite',   'codigo'),
    'TAREA':     ('tipo_tarea',     'codigo'),
}

# Reemplazar _get_tipo_elemento_id
def _get_tipo_elemento_codigo(elemento, tipo_elemento: str) -> Optional[str]:
    rel_name, attr = _TIPO_CODIGO_REL.get(tipo_elemento, (None, None))
    if not rel_name:
        return None
    tipo_obj = getattr(elemento, rel_name, None)
    return getattr(tipo_obj, attr, None) if tipo_obj else None

# En obtener_estado_plazo: sustituir tipo_elemento_id por tipo_elemento_codigo
tipo_elemento_codigo = _get_tipo_elemento_codigo(elemento, tipo_elemento)
if tipo_elemento_codigo is None:
    return _SIN_PLAZO

catalogo = _seleccionar_catalogo(tipo_elemento, tipo_elemento_codigo, variables_dict)

# En _seleccionar_catalogo: actualizar firma y filter
def _seleccionar_catalogo(tipo_elemento: str, tipo_codigo: str, variables_dict: dict):
    ...
    .filter_by(tipo_elemento=tipo_elemento, tipo_elemento_codigo=tipo_codigo, activo=True)
    ...
    log.warning('plazos: ninguna entrada satisface condiciones para %s/%s',
                tipo_elemento, tipo_codigo)
```

**Nota sobre migraciones de seed anteriores:** Las migraciones existentes (90655e484fb2, etc.) hacen `INSERT ... SELECT tf.id FROM tipos_fases WHERE codigo = '...'` — insertan `tipo_elemento_id` pero no `tipo_elemento_codigo` (que no existe aún). El backfill de la nueva migración resuelve las filas existentes correctamente. Las seeds futuras deben incluir `tipo_elemento_codigo` y omitir `tipo_elemento_id`.

**Tests:**
- `tests/test_347_plazos_codigo.py` (NUEVO):
  - `test_get_tipo_elemento_codigo_fase`: fixture con Fase mock → devuelve `tipo_fase.codigo`
  - `test_get_tipo_elemento_codigo_none`: elemento sin tipo_fase (relación None) → devuelve None → `obtener_estado_plazo` devuelve SIN_PLAZO
  - `test_seleccionar_catalogo_por_codigo`: BD de test con entrada `tipo_elemento_codigo='CONSULTAS'` → la selecciona correctamente
  - `test_seleccionar_catalogo_codigo_ausente`: BD de test sin entrada para el código → devuelve None, no excepción

**Criterio de cierre:** `flask db upgrade/downgrade` limpio; `pytest tests/test_347_plazos_codigo.py tests/test_190_plazos_contrato.py` verde (los tests de #172 no deben romperse).

**Tiempo estimado:** ~3 h

---

### Sesión 2 — Manifiesto + validación en arranque

**Objetivo:** el sistema conoce qué registros espera antes de intentar usarlos.

**Ficheros:**
- `app/checks/__init__.py` (NUEVO — módulo vacío)
- `app/checks/catalogo_requerido.py` (NUEVO — manifiesto)
- `app/__init__.py` (añadir llamada a `validar_catalogo`)

**Tarea previa obligatoria:** hacer un `grep` sistemático de los códigos hardcodeados en el código Python para construir el manifiesto completo. Buscar en:
- `app/services/invariantes_esftt.py` — sets de tipos de tarea
- `app/services/seguimiento.py` — dict `PISTAS`
- `app/services/variables/calculado.py` — comparaciones `.codigo ==`
- `app/services/assembler.py` — comparaciones de tipo
- `app/__init__.py` — dict `_icono_tarea_tipo`
- `app/services/plazos.py` — `_TIPO_CODIGO_REL`

**Estructura de `catalogo_requerido.py`:**
```python
"""
Manifiesto de registros estructurales que el código Python espera encontrar en BD.

Actualizar aquí cada vez que el código use un nuevo código de catálogo.
La validación de arranque compara este dict contra la BD real.
"""
from app.models.tipos_fases     import TipoFase
from app.models.tipos_tramites  import TipoTramite
from app.models.tipos_tareas    import TipoTarea
from app.models.tipos_solicitudes import TipoSolicitud
from app.models.efectos_plazo   import EfectoPlazo

# (modelo, campo_codigo): [lista de valores esperados]
REGISTROS_REQUERIDOS: dict[tuple, list[str]] = {
    (TipoTarea, 'codigo'): [
        'ANALIZAR', 'REDACTAR', 'FIRMAR', 'NOTIFICAR',
        'PUBLICAR', 'ESPERAR_PLAZO', 'INCORPORAR',
    ],  # ANALIZAR, no ANALISIS — ver bug #349
    (TipoFase, 'codigo'): [
        'ANALISIS_SOLICITUD', 'CONSULTAS', 'CONSULTA_MINISTERIO',
        'COMPATIBILIDAD_AMBIENTAL', 'FIGURA_AMBIENTAL_EXTERNA',
        'AAU_AAUS_INTEGRADA', 'INFORMACION_PUBLICA', 'RESOLUCION',
        # completar con el grep antes de implementar
    ],
    (TipoTramite, 'codigo'): [
        'PUBLICACION',
        # completar con el grep antes de implementar
    ],
    (TipoSolicitud, 'siglas'): [
        'AAC', 'AAP',
    ],
    (EfectoPlazo, 'codigo'): [
        'NINGUNO', 'SILENCIO_ESTIMATORIO', 'SILENCIO_DESESTIMATORIO',
        'CONFORMIDAD_PRESUNTA', 'SIN_EFECTO_AUTOMATICO',
        'RESPONSABILIDAD_DISCIPLINARIA', 'CADUCIDAD_PROCEDIMIENTO',
        'PERDIDA_TRAMITE', 'APERTURA_RECURSO', 'PRESCRIPCION_CONDICIONADO',
    ],
}


def validar_catalogo() -> list[str]:
    """
    Comprueba que todos los registros del manifiesto existen en BD.
    Devuelve lista de strings describiendo lo que falta. Lista vacía = OK.
    Llama dentro de app_context activo.
    """
    from sqlalchemy.exc import OperationalError, ProgrammingError
    errores = []
    for (modelo, campo), codigos in REGISTROS_REQUERIDOS.items():
        for codigo in codigos:
            try:
                existe = modelo.query.filter(
                    getattr(modelo, campo) == codigo
                ).first()
                if existe is None:
                    errores.append(
                        f'{modelo.__tablename__}.{campo}={codigo!r} → no encontrado'
                    )
            except (OperationalError, ProgrammingError) as exc:
                errores.append(
                    f'{modelo.__tablename__} → tabla no accesible: {exc}'
                )
                break  # no iterar más sobre una tabla que no existe
    return errores
```

**Cambio en `app/__init__.py`** — al final de `create_app`, antes del `return app`:
```python
# Validación de catálogo estructural en arranque (#347)
import logging as _logging
_log_check = _logging.getLogger('catalogo.check')
with app.app_context():
    from app.checks.catalogo_requerido import validar_catalogo
    errores = validar_catalogo()
    if errores:
        for e in errores:
            _log_check.error('Registro estructural faltante: %s', e)
        _log_check.error(
            '%d registro(s) estructural(es) faltante(s). '
            'Ejecutar flask db upgrade y verificar seeds.', len(errores)
        )
```

**Tests:**
- `tests/test_347_manifiesto.py` (NUEVO):
  - `test_validar_catalogo_ok`: BD de test completa → lista vacía
  - `test_validar_catalogo_falta_tipo_tarea`: borrar `TipoTarea.codigo='ANALISIS'` → lista contiene el error esperado, sin excepción
  - `test_validar_catalogo_tabla_no_existe`: mock que lanza `ProgrammingError` en primer query → lista contiene error de tabla, no traceback
  - `test_validar_catalogo_multiples_fallos`: borrar dos registros → dos entradas en la lista

**Criterio de cierre:** tests verdes; arrancar Flask con BD incompleta produce logs ERROR sin crashear.

**Tiempo estimado:** ~2.5 h

---

### Sesión 3 — Manejador global + degradación en servicios + convención

**Objetivo:** ninguna ruta API devuelve HTTP 500 sin cuerpo; ningún servicio propaga excepción no controlada al upstream.

**Ficheros:**
- `app/__init__.py` (añadir manejadores de error)
- `app/services/plazos.py` (guards para `OperationalError` y `None` en `_obtener_inhabiles_bd`)
- `app/services/seguimiento.py` (guards en accesos a relaciones ORM)
- `docs/guias/REGLAS_DESARROLLO.md` (nueva sección sobre patrón defensivo)

**Manejadores en `app/__init__.py`** — dentro de `create_app`:
```python
from sqlalchemy.exc import OperationalError, ProgrammingError

@app.errorhandler(OperationalError)
@app.errorhandler(ProgrammingError)
def handle_db_error(error):
    log.error('Error de base de datos: %s', error)
    db.session.rollback()
    return jsonify({
        'error': 'Servicio de base de datos no disponible',
        'code':  'DB_ERROR',
    }), 503
```

**Guards en `plazos.py`** — función `_obtener_inhabiles_bd`:
```python
def _obtener_inhabiles_bd(fecha_ini: date, fecha_fin: date) -> frozenset:
    try:
        registros = DiaInhabil.query.filter(...).all()
        return frozenset(r.fecha for r in registros)
    except (OperationalError, ProgrammingError):
        log.warning('plazos: tabla dias_inhabiles no accesible — usando calendario sin inhábiles')
        return frozenset()
```

**Guards en `seguimiento.py`** — los accesos a `f.tipo_fase.codigo` y `tarea.tipo_tarea.codigo` deben protegerse. Buscar en el fichero todas las navegaciones de relación lazy y añadir guards. Patrón:
```python
# Antes (frágil si tipo_fase es None):
codigo = fase.tipo_fase.codigo

# Después (defensivo):
tipo_fase = getattr(fase, 'tipo_fase', None)
if tipo_fase is None:
    log.warning('seguimiento: fase %s sin tipo_fase — usando PENDIENTE_TRAMITAR', fase.id)
    return PENDIENTE_TRAMITAR_PISTA
codigo = tipo_fase.codigo
```

**Sección en `REGLAS_DESARROLLO.md`** — añadir apartado «Patrón defensivo para accesos a catálogo»:
- Siempre guard `if resultado is None` tras `.first()`
- Siempre `try/except (OperationalError, ProgrammingError)` en queries a tablas de catálogo
- Devolver valor degradado con `log.warning`, nunca propagar
- Añadir el código al manifiesto `app/checks/catalogo_requerido.py` cuando se use un nuevo código

**Tests:**
- `tests/test_347_error_handlers.py` (NUEVO):
  - `test_db_error_devuelve_503_json`: mock que lanza `OperationalError` en una ruta API → HTTP 503 + `{"code": "DB_ERROR"}`
  - `test_plazos_inhabiles_tabla_no_existe`: mock `DiaInhabil.query` lanza `ProgrammingError` → `obtener_estado_plazo` devuelve SIN_PLAZO, no traceback
  - `test_seguimiento_tipo_fase_none`: Fase con `tipo_fase=None` → `estado_solicitud` devuelve resultado degradado, no `AttributeError`

**Criterio de cierre:** `pytest tests/test_347_*.py` verde; ninguna ruta de seguimiento devuelve HTTP 500 sin cuerpo JSON cuando falta un catálogo.

**Tiempo estimado:** ~2.5 h

---

### Sesión 4 — Documentación y cierre

**Ficheros:**
- `docs/referencia/DISEÑO_FECHAS_PLAZOS.md` — actualizar §3.2 para reflejar `tipo_elemento_codigo`; eliminar deuda técnica si existía
- `docs/CONTEXTO_ACTUAL.md` — marcar #347 cerrado, proponer próximo
- Este fichero `IMPLEMENTACION_347.md` — marcar sesiones completadas

**Tiempo estimado:** ~1 h

---

## Resumen de tiempos

| Sesión | Tema | Horas estimadas |
|--------|------|-----------------|
| 1 | Fix FK frágil: migración + modelo + plazos.py | 3.0 |
| 2 | Manifiesto + validación en arranque | 2.5 |
| 3 | Manejador global + degradación + convención | 2.5 |
| 4 | Documentación y cierre | 1.0 |
| | **Total** | **9.0 h** |

Margen real estimado: **11-13 h**.

---

## Riesgos

- **Backfill incompleto:** si existe algún `tipo_elemento` con valor inesperado (ej. `'EXPEDIENTE'`), la migración lanzará la excepción del `DO $$` y no avanzará. Hay que revisar valores distintos de los 4 conocidos antes de lanzar la migración en producción:
  ```sql
  SELECT DISTINCT tipo_elemento FROM public.catalogo_plazos;
  ```
- **Lazy load en `_get_tipo_elemento_codigo`:** si el elemento se carga sin `joinedload` de la relación tipo, navegar `elemento.tipo_fase` dispara una query adicional. Verificar en los tests que no genera N+1 problemático. Si sí, añadir `joinedload` en los callers.
- **Tests de #172 rotos:** `_get_tipo_elemento_id` desaparece. Cualquier test que lo llame directamente o que fabrique un objeto con solo `tipo_fase_id` (sin el objeto relación) necesita actualización. Revisarlos antes de empezar la Sesión 1.
- **Manifiesto incompleto:** si el grep de códigos hardcodeados en la Sesión 2 no es exhaustivo, la validación de arranque no detectará todos los huecos. Importante: el grep cubre solo el estado actual del código — cada vez que se añade un nuevo código en una PR futura, hay que actualizar `catalogo_requerido.py`.

---

## Cabos sueltos → issues potenciales

1. **Eliminar `tipo_elemento_id`** de `catalogo_plazos` — queda pendiente para issue posterior. Condición: verificar en producción que nada lo sigue usando.
2. **UI Supervisor para `catalogo_plazos`** — si el supervisor puede editar filas, el formulario debe trabajar con `tipo_elemento_codigo`, no con `tipo_elemento_id`. Issue de UI separado.
3. **Validación en CI** — el check de `validar_catalogo()` en arranque es manual (log). Debería convertirse en un test de integración que corra en CI con BD de test completa. Issue #348 o posterior.
4. **Grep automático de códigos** — a largo plazo, el manifiesto podría generarse semi-automáticamente analizando el AST del código. No urgente.
