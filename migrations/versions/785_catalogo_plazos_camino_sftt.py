"""785_catalogo_plazos_camino_sftt

Revision ID: 785_catalogo_plazos_camino
Revises: 585_baja_tabla_metadata
Create Date: 2026-08-17

Issue #785 — `catalogo_plazos` identificado por camino SFTT completo.

PROBLEMA
========

`tipo_elemento` + `tipo_elemento_codigo` no identifican sin ambigüedad una fila:
literales como `ESPERAR_PLAZO` o `RESOLUCION` se repiten en distintos puntos del
árbol SFTT. Se distinguían mediante `condiciones_plazo` sobre variables que solo
reexponían un dato de posición que el grafo de FKs ya contiene:

  - FASE/RESOLUCION  → variable `tipo_solicitud` (7 condiciones IN)
  - TAREA/ESPERAR_PLAZO → variable `tipo_tramite` (5 condiciones EQ)

`tipo_tramite` además nunca se registró como función en `app/services/variables/`
(`_REGISTRY`): por el camino general del motor siempre resolvía a None. Solo
funcionaba porque tres consumidores la reconstruían a mano saltándose el
ensamblador.

DISEÑO
======

Columna `camino`: patrón calificado ESFTT con comodín posicional `ANY`, mismo
formato y mismo matcher (`motor_reglas._sujeto_casa`) que `reglas_motor.sujeto`,
con un nivel más de profundidad. La longitud codifica el nivel:

    SOLICITUD  2 segmentos   <expediente>/<siglas>
    FASE       3             <expediente>/<siglas>/<fase>
    TRAMITE    4             …/<tramite>
    TAREA      5             …/<tramite>/<tarea>

Invariante: el último segmento NUNCA es `ANY` — es el tipo del elemento evaluado,
siempre conocido. `tipo_elemento` se conserva como prefiltro SQL barato (filtrar
por número de segmentos de un string es impracticable).

CRITERIO DE MIGRACIÓN DE DATOS
==============================

Preservar el comportamiento actual, no mejorarlo: solo se fija un segmento
concreto donde HOY existía una condición que lo discriminaba. Donde no la había,
`ANY` — porque hoy esas filas casan con cualquier valor en ese nivel.

  - FASE/RESOLUCION: las 7 filas se desdoblan en 11 (una por sigla del `IN`),
    sin `IN` en el segmento (decisión de diseño: camino estrictamente literal,
    validable sin ambigüedad).
  - TAREA/ESPERAR_PLAZO: 5 filas, el segmento de trámite sale de la condición.
  - Las condiciones que expresan supuesto legal real (`max_tension_nominal_kv`
    en SOLICITUD/AAP, `es_solicitud_aac_pura` + `tiene_solicitud_aap_favorable`
    en CONSULTAS/CONSULTA_SEPARATA) se conservan intactas: el camino dice DÓNDE
    está el plazo, las condiciones BAJO QUÉ SUPUESTO aplica.

La variable `tipo_tramite` se BORRA de `catalogo_variables` (no se desactiva):
esto es desarrollo, sus únicas 5 referencias son las condiciones que aquí se
retiran, y `activa=False` es un mecanismo que #561 va a eliminar — dejar la
primera fila aparcada del catálogo iría en dirección contraria. El propio
downgrade de `350_variable_tipo_tramite` ya la borraba.

Orden obligado: `fk_condiciones_plazo_variable` es ON DELETE RESTRICT — primero
las condiciones, después la variable.
"""
from alembic import op
import sqlalchemy as sa


revision = '785_catalogo_plazos_camino'
down_revision = '585_baja_tabla_metadata'
branch_labels = None
depends_on = None


# Nº de segmentos del camino por nivel ESFTT.
_SEGMENTOS = {'SOLICITUD': 2, 'FASE': 3, 'TRAMITE': 4, 'TAREA': 5}

# Columnas que se copian al desdoblar una fila de RESOLUCION (sin `id`).
_COLS_COPIA = (
    'tipo_elemento', 'tipo_elemento_id', 'tipo_elemento_codigo', 'campo_fecha',
    'plazo_valor', 'plazo_unidad', 'efecto_vencimiento_id', 'norma_origen',
    'vigencia_desde', 'vigencia_hasta', 'activo', 'orden',
)


def _camino_base(tipo_elemento: str, codigo: str) -> str:
    """Camino con todo ANY salvo la hoja: 'ANY/ANY/ANY/ESPERAR_PLAZO' etc."""
    n = _SEGMENTOS[tipo_elemento]
    return '/'.join(['ANY'] * (n - 1) + [codigo])


def upgrade():
    conn = op.get_bind()

    # --- 1. Columna nueva, nullable de momento --------------------------------
    op.add_column(
        'catalogo_plazos',
        sa.Column('camino', sa.String(250), nullable=True,
                  comment='Patrón calificado ESFTT con comodín ANY: '
                          'ANY/ANY/ANY/REQUERIMIENTO_SUBSANACION/ESPERAR_PLAZO. '
                          'La hoja (último segmento) nunca es ANY.'),
        schema='public',
    )

    # --- 2. Camino base: todo ANY salvo la hoja -------------------------------
    filas = conn.execute(sa.text(
        'SELECT id, tipo_elemento, tipo_elemento_codigo FROM public.catalogo_plazos'
    )).fetchall()

    for fila_id, tipo_elemento, codigo in filas:
        if tipo_elemento not in _SEGMENTOS:
            raise RuntimeError(
                f'catalogo_plazos id={fila_id}: tipo_elemento desconocido {tipo_elemento!r}'
            )
        conn.execute(
            sa.text('UPDATE public.catalogo_plazos SET camino = :camino WHERE id = :id'),
            {'camino': _camino_base(tipo_elemento, codigo), 'id': fila_id},
        )

    # --- 3. FASE/RESOLUCION: desdoblar el IN de tipo_solicitud ----------------
    # Segmento 2 (siglas de la solicitud) pasa de condición a camino.
    resolucion = conn.execute(sa.text("""
        SELECT cp.id, c.valor
        FROM public.catalogo_plazos cp
        JOIN public.condiciones_plazo c ON c.catalogo_plazo_id = cp.id
        JOIN public.catalogo_variables cv ON c.variable_id = cv.id
        WHERE cp.tipo_elemento = 'FASE' AND cv.nombre = 'tipo_solicitud'
        ORDER BY cp.id
    """)).fetchall()

    cols = ', '.join(_COLS_COPIA)
    for fila_id, siglas_json in resolucion:
        siglas = siglas_json if isinstance(siglas_json, list) else [siglas_json]
        if not siglas:
            raise RuntimeError(f'catalogo_plazos id={fila_id}: condición tipo_solicitud sin valores')

        # La primera sigla se queda en la fila original; el resto se clonan.
        for sigla in siglas[1:]:
            conn.execute(
                sa.text(f"""
                    INSERT INTO public.catalogo_plazos ({cols}, camino)
                    SELECT {cols}, :camino
                    FROM public.catalogo_plazos WHERE id = :id
                """),
                {'camino': f'ANY/{sigla}/RESOLUCION', 'id': fila_id},
            )

        conn.execute(
            sa.text('UPDATE public.catalogo_plazos SET camino = :camino WHERE id = :id'),
            {'camino': f'ANY/{siglas[0]}/RESOLUCION', 'id': fila_id},
        )

    # --- 4. TAREA/ESPERAR_PLAZO: el trámite pasa de condición a camino --------
    esperar = conn.execute(sa.text("""
        SELECT cp.id, cp.tipo_elemento_codigo, c.valor
        FROM public.catalogo_plazos cp
        JOIN public.condiciones_plazo c ON c.catalogo_plazo_id = cp.id
        JOIN public.catalogo_variables cv ON c.variable_id = cv.id
        WHERE cp.tipo_elemento = 'TAREA' AND cv.nombre = 'tipo_tramite'
        ORDER BY cp.id
    """)).fetchall()

    for fila_id, codigo_tarea, tramite in esperar:
        if isinstance(tramite, list):
            raise RuntimeError(
                f'catalogo_plazos id={fila_id}: condición tipo_tramite multivalor '
                f'({tramite!r}) — desdoblar a mano, este seed no lo contempla'
            )
        conn.execute(
            sa.text('UPDATE public.catalogo_plazos SET camino = :camino WHERE id = :id'),
            {'camino': f'ANY/ANY/ANY/{tramite}/{codigo_tarea}', 'id': fila_id},
        )

    # --- 5. Retirar las condiciones que hacían de FK disfrazada ---------------
    # Solo tipo_solicitud/tipo_tramite: las de supuesto legal real se conservan.
    conn.execute(sa.text("""
        DELETE FROM public.condiciones_plazo
        WHERE variable_id IN (
            SELECT id FROM public.catalogo_variables
            WHERE nombre IN ('tipo_solicitud', 'tipo_tramite')
        )
    """))

    # --- 6. Borrar la variable tipo_tramite (ver docstring) -------------------
    # tipo_solicitud NO se borra: tiene función real en _REGISTRY y la usan
    # condiciones_requisito (#192).
    conn.execute(sa.text(
        "DELETE FROM public.catalogo_variables WHERE nombre = 'tipo_tramite'"
    ))

    # --- 7. Cerrar el esquema -------------------------------------------------
    op.alter_column('catalogo_plazos', 'camino', nullable=False, schema='public')

    op.drop_index('idx_catalogo_plazos_tipo_elem', table_name='catalogo_plazos', schema='public')
    op.drop_index('idx_catalogo_plazos_tipo_orden', table_name='catalogo_plazos', schema='public')
    op.drop_index('idx_catalogo_plazos_tipo_codigo', table_name='catalogo_plazos', schema='public')
    op.drop_index('idx_catalogo_plazos_tipo_codigo_orden', table_name='catalogo_plazos', schema='public')

    op.drop_column('catalogo_plazos', 'tipo_elemento_codigo', schema='public')
    op.drop_column('catalogo_plazos', 'tipo_elemento_id', schema='public')

    op.create_index('idx_catalogo_plazos_tipo_orden', 'catalogo_plazos',
                    ['tipo_elemento', 'orden'], schema='public')
    op.create_index('idx_catalogo_plazos_camino', 'catalogo_plazos',
                    ['camino'], schema='public')


def downgrade():
    """Restaura el esquema anterior derivando los datos del camino.

    No es reversible byte a byte: las 11 filas de RESOLUCION vuelven con una
    condición IN de un solo valor cada una en vez de las 7 originales con IN
    multivalor. Funcionalmente equivalente.
    """
    conn = op.get_bind()

    op.drop_index('idx_catalogo_plazos_camino', table_name='catalogo_plazos', schema='public')
    op.drop_index('idx_catalogo_plazos_tipo_orden', table_name='catalogo_plazos', schema='public')

    op.add_column('catalogo_plazos',
                  sa.Column('tipo_elemento_id', sa.Integer(), nullable=True), schema='public')
    op.add_column('catalogo_plazos',
                  sa.Column('tipo_elemento_codigo', sa.String(60), nullable=True), schema='public')

    # Hoja del camino → tipo_elemento_codigo
    conn.execute(sa.text("""
        UPDATE public.catalogo_plazos
        SET tipo_elemento_codigo = split_part(camino, '/', array_length(string_to_array(camino,'/'),1))
    """))

    # tipo_elemento_id desde la tabla de tipos correspondiente (0 si no resuelve)
    for nivel, tabla, campo in (
        ('SOLICITUD', 'tipos_solicitudes', 'siglas'),
        ('FASE',      'tipos_fases',       'codigo'),
        ('TRAMITE',   'tipos_tramites',    'codigo'),
        ('TAREA',     'tipos_tareas',      'codigo'),
    ):
        conn.execute(sa.text(f"""
            UPDATE public.catalogo_plazos cp
            SET tipo_elemento_id = COALESCE(
                (SELECT t.id FROM public.{tabla} t WHERE t.{campo} = cp.tipo_elemento_codigo), 0)
            WHERE cp.tipo_elemento = :nivel
        """), {'nivel': nivel})

    op.alter_column('catalogo_plazos', 'tipo_elemento_id', nullable=False, schema='public')
    op.alter_column('catalogo_plazos', 'tipo_elemento_codigo', nullable=False, schema='public')

    # Recrear la variable tipo_tramite
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa)
        VALUES ('tipo_tramite',
                'Código del tipo de trámite activo en el contexto evaluado',
                'texto', NULL, TRUE)
        ON CONFLICT (nombre) DO NOTHING
    """))

    # TAREA: segmento 4 del camino → condición tipo_tramite EQ
    conn.execute(sa.text("""
        INSERT INTO public.condiciones_plazo (catalogo_plazo_id, variable_id, operador, valor, orden)
        SELECT cp.id, cv.id, 'EQ', to_jsonb(split_part(cp.camino, '/', 4)), 1
        FROM public.catalogo_plazos cp
        CROSS JOIN public.catalogo_variables cv
        WHERE cp.tipo_elemento = 'TAREA'
          AND cv.nombre = 'tipo_tramite'
          AND split_part(cp.camino, '/', 4) <> 'ANY'
    """))

    # FASE: segmento 2 del camino → condición tipo_solicitud IN [valor]
    conn.execute(sa.text("""
        INSERT INTO public.condiciones_plazo (catalogo_plazo_id, variable_id, operador, valor, orden)
        SELECT cp.id, cv.id, 'IN', jsonb_build_array(split_part(cp.camino, '/', 2)), 1
        FROM public.catalogo_plazos cp
        CROSS JOIN public.catalogo_variables cv
        WHERE cp.tipo_elemento = 'FASE'
          AND cv.nombre = 'tipo_solicitud'
          AND split_part(cp.camino, '/', 2) <> 'ANY'
    """))

    op.drop_column('catalogo_plazos', 'camino', schema='public')

    op.create_index('idx_catalogo_plazos_tipo_elem', 'catalogo_plazos',
                    ['tipo_elemento', 'tipo_elemento_id'], schema='public')
    op.create_index('idx_catalogo_plazos_tipo_orden', 'catalogo_plazos',
                    ['tipo_elemento', 'tipo_elemento_id', 'orden'], schema='public')
    op.create_index('idx_catalogo_plazos_tipo_codigo', 'catalogo_plazos',
                    ['tipo_elemento', 'tipo_elemento_codigo'], schema='public')
    op.create_index('idx_catalogo_plazos_tipo_codigo_orden', 'catalogo_plazos',
                    ['tipo_elemento', 'tipo_elemento_codigo', 'orden'], schema='public')
