"""827_cert_fin_instruccion_bisagra

Revision ID: 827_cert_fin_instruccion
Revises: 8a18f2077c0c
Create Date: 2026-09-03

Issue #827 — ADR-043 §C y §D: la bisagra entre instrucción y resolución deja de
ser un recuento de fases y pasa a ser un documento que consta emitido.

1. `solicitudes.documento_fin_instruccion_id`
=============================================

Tercera columna de la serie que abrió ADR-041 §D bis, con la misma forma que sus
dos hermanas: entrada (`documento_solicitud_id`, art. 21.3.b) → fin de instrucción
(esta, art. 82.1) → cierre (`documento_cierre_id`, art. 40.4).

`Documento` tiene un solo FK, a expediente, así que sin esta columna no es
consultable «el certificado de ESTA solicitud». Es justo el defecto que arrastra
`cert_fin_ip_consultas._buscar_existente`, que recibe `solicitud_id` y no lo usa
—filtra por expediente + tipo—: con dos solicitudes en el mismo expediente, la
segunda reutiliza el certificado de la primera. La variable de §C lee esta FK y
nunca busca el tipo documental en el pool, para no heredar esa deuda.

No hace falta crear el tipo documental: `CERT_FIN_INSTRUCCION` existe desde #373
(`tipos_documentos` id 3, origen INTERNO) y ya figura como ENTRADA obligatoria del
ELABORAR (orden 1) de ELABORACION. Lo que faltaba era el productor, no el tipo.

2. `solicitud_tiene_cert_fin_instruccion` en catalogo_variables
===============================================================

Booleana, con `norma_id` = LPACAP. El nombre declara el ámbito a propósito
(`solicitud_tiene_…`, no `existe_cert_…`): ADR-043 §C exige las tres condiciones
—nombre, lectura por la FK propia y docstring explícito— porque el precedente
contrario existe y está activo (`organismos_todos_terminados` lee
`ctx.expediente.organismos` y sí es permeable entre solicitudes del expediente).

3. Dos reglas con sujeto explícito, no una genérica
===================================================

    CREAR  ANY/ANY/RESOLUCION                      BLOQUEAR   LPACAP 82.1
    CREAR  ANY/INTERESADO/RECONOCIMIENTO_INTERESADO BLOQUEAR  LPACAP 82.1

Una fila por fase finalizadora (`tipos_fases.es_finalizadora`: RESOLUCION id 8 y
RECONOCIMIENTO_INTERESADO id 9). El sujeto genérico `ANY/ANY/ANY` con una
condición «es finalizadora» cubriría también las futuras, pero escondería el
filtro real en una función Python y dejaría la fila ilegible para el supervisor
—permeabilidad en la permisividad, ADR-043 §C—. El precio, acordarse de añadir
fila si aparece una tercera finalizadora, lo paga el aviso de arranque de
`app/checks/catalogo_requerido.py`.

Son las primeras reglas de precedencia hacia la fase finalizadora **con norma
citada**: las 36/37/38 tienen `norma_id` NULL. Prioridad 5, por delante de las
tres: el fin de instrucción es la precondición que las engloba, y es la que el
técnico debe leer primero cuando el motor bloquee.

`RECONOCIMIENTO_INTERESADO` es la finalizadora de la solicitud INTERESADO
(`tipos_solicitudes` id 14), una solicitud paralela con vida propia. Las dos
finalizadoras nunca conviven en la misma solicitud; por eso el alcance del check
es por solicitud y no por elección entre varias opciones posibles.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '827_cert_fin_instruccion'
down_revision = '8a18f2077c0c'
branch_labels = None
depends_on = None

_VARIABLE = 'solicitud_tiene_cert_fin_instruccion'
_ETIQUETA = ('Consta emitido el certificado de fin de instrucción de la solicitud '
             'en contexto')

# (sujeto, descripción) — una fila por fase finalizadora (ADR-043 §C).
_REGLAS = [
    ('ANY/ANY/RESOLUCION',
     'No se puede abrir la fase de resolución mientras no conste emitido el '
     'certificado de fin de instrucción de la solicitud'),
    ('ANY/INTERESADO/RECONOCIMIENTO_INTERESADO',
     'No se puede abrir la fase de reconocimiento de interesado mientras no conste '
     'emitido el certificado de fin de instrucción de la solicitud'),
]


def upgrade():
    conn = op.get_bind()

    # --- 1. El ancla documental de la solicitud ------------------------------
    op.add_column(
        'solicitudes',
        sa.Column(
            'documento_fin_instruccion_id', sa.Integer(), nullable=True,
            comment='FK a DOCUMENTOS. Certificado de fin de instrucción de la '
                    'solicitud (CERT_FIN_INSTRUCCION): consta que la instrucción '
                    'terminó y habilita la fase finalizadora (art. 82.1 LPACAP, #827)',
        ),
        schema='public',
    )
    op.create_foreign_key(
        'fk_solicitudes_documento_fin_instruccion',
        'solicitudes', 'documentos',
        ['documento_fin_instruccion_id'], ['id'],
        source_schema='public', referent_schema='public',
    )
    op.create_index(
        'idx_solicitudes_doc_fin_instruccion', 'solicitudes',
        ['documento_fin_instruccion_id'], schema='public',
    )

    # --- 2. La variable que lee esa FK --------------------------------------
    norma_lpacap_id = conn.execute(sa.text(
        "SELECT id FROM public.normas WHERE codigo = 'LPACAP'"
    )).scalar()
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa)
        VALUES (:nombre, :etiqueta, 'boolean', :norma_id, TRUE)
        ON CONFLICT (nombre) DO NOTHING
    """), {'nombre': _VARIABLE, 'etiqueta': _ETIQUETA, 'norma_id': norma_lpacap_id})

    var_id = conn.execute(sa.text(
        'SELECT id FROM public.catalogo_variables WHERE nombre = :nombre'
    ), {'nombre': _VARIABLE}).scalar()

    # --- 3. Una regla por fase finalizadora ---------------------------------
    for sujeto, descripcion in _REGLAS:
        regla_id = conn.execute(sa.text("""
            INSERT INTO public.reglas_motor
                (accion, sujeto, efecto, norma_id, articulo, apartado, prioridad, activa, descripcion)
            VALUES ('CREAR', :sujeto, 'BLOQUEAR', :norma_id, '82', '1', 5, TRUE, :descripcion)
            RETURNING id
        """), {'sujeto': sujeto, 'norma_id': norma_lpacap_id,
               'descripcion': descripcion}).scalar()

        conn.execute(sa.text("""
            INSERT INTO public.condiciones_regla (regla_id, variable_id, operador, valor, orden)
            VALUES (:regla_id, :var_id, 'EQ', 'false'::jsonb, 1)
        """), {'regla_id': regla_id, 'var_id': var_id})


def downgrade():
    conn = op.get_bind()

    for sujeto, _descripcion in _REGLAS:
        conn.execute(sa.text("""
            DELETE FROM public.condiciones_regla
            WHERE regla_id IN (
                SELECT r.id FROM public.reglas_motor r
                JOIN public.condiciones_regla c ON c.regla_id = r.id
                JOIN public.catalogo_variables v ON v.id = c.variable_id
                WHERE r.accion = 'CREAR' AND r.sujeto = :sujeto AND v.nombre = :nombre
            )
        """), {'sujeto': sujeto, 'nombre': _VARIABLE})
        conn.execute(sa.text("""
            DELETE FROM public.reglas_motor
            WHERE accion = 'CREAR' AND sujeto = :sujeto AND descripcion = :descripcion
        """), {'sujeto': sujeto, 'descripcion': _descripcion})

    conn.execute(sa.text(
        'DELETE FROM public.catalogo_variables WHERE nombre = :nombre'
    ), {'nombre': _VARIABLE})

    op.drop_index('idx_solicitudes_doc_fin_instruccion',
                  table_name='solicitudes', schema='public')
    op.drop_constraint('fk_solicitudes_documento_fin_instruccion', 'solicitudes',
                       type_='foreignkey', schema='public')
    op.drop_column('solicitudes', 'documento_fin_instruccion_id', schema='public')
