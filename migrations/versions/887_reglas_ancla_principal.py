"""887_reglas_ancla_principal

Revision ID: 887_reglas_ancla
Revises: 887_ancla_principal
Create Date: 2026-09-09

Las dos variables y las dos reglas que impiden seguir la solicitud mientras el
proyecto no tenga documento principal anclado (#887, ADR-044 §D).

**Dos reglas, no una**, porque el fundamento normativo es distinto según lo que se
pida y `reglas_motor.articulo` se cita al bloquear:

  - AAP → RD 1955/2000 art. 123.1: «A la solicitud se acompañará un anteproyecto de
    la instalación» (memoria, planos, presupuesto, separatas).
  - AAC → RD 1955/2000 art. 130.1: la solicitud se presenta «junto con el proyecto
    de ejecución elaborado conforme a los Reglamentos técnicos en la materia».

El sujeto calificado hace el encuadre, como en #780 (`Renovable/AAP/ANY`), y no hace
falta variable de tipo de solicitud. Una solicitud combinada AAP+AAC queda cubierta
igual: `auditar_multi`/`evaluar_multi` evalúan el motor una vez por cada tipo simple
de `Solicitud.tipos_simples` y hacen AND de los resultados.

DUP no lleva regla propia: su documentación específica es la relación de bienes y
derechos (art. 143 y ss.), no el proyecto, y en la práctica acompaña siempre a una
AAP o AAC que ya queda cubierta por las dos de aquí.

Condiciones de cada regla, en AND:

  1. tipo_sujeto_solicitado NEQ 'ANALISIS_SOLICITUD' — variable genérica (#388),
     mismo uso que #582 y #780: el análisis documental es donde la falta se detecta
     y se requiere, así que no se bloquea a sí mismo.
  2. proyecto_sin_principal EQ true — variable nueva de dato.
  3. expediente_heredado EQ false — la excepción de los migrados del sistema
     anterior, como condición de la regla y no como bypass repetido fase tras fase.

Las dos variables se registran en `app/services/variables/dato.py` en el commit
anterior a esta migración, para que `activa=TRUE` solo se marque cuando la función
ya existe (orden de #780, no el de #582).

El escape no necesita diseño: `puede_escapar` es el comportamiento genérico de toda
regla BLOQUEAR (`app/services/motor_reglas.py`), y cubre el expediente extraordinario
que haya que sacar adelante sin el proyecto identificado, con justificación en
bitácora.
"""
from alembic import op
import sqlalchemy as sa

revision = '887_reglas_ancla'
down_revision = '887_ancla_principal'
branch_labels = None
depends_on = None


DESCRIPCIONES = {
    'AAP': (
        'No se puede tramitar ninguna fase posterior a ANÁLISIS_SOLICITUD de una AAP '
        'sin haber identificado cuál de los documentos del expediente es el proyecto '
        '(RD 1955/2000, art. 123.1: la solicitud se acompaña del anteproyecto)'
    ),
    'AAC': (
        'No se puede tramitar ninguna fase posterior a ANÁLISIS_SOLICITUD de una AAC '
        'sin haber identificado cuál de los documentos del expediente es el proyecto '
        '(RD 1955/2000, art. 130.1: la solicitud se presenta junto con el proyecto de '
        'ejecución)'
    ),
}
ARTICULOS = {'AAP': ('123', '1'), 'AAC': ('130', '1')}


def upgrade():
    conn = op.get_bind()

    # 1. Las dos variables de dato
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa)
        SELECT 'proyecto_sin_principal',
               'El proyecto del expediente no tiene documento principal anclado',
               'boolean', n.id, TRUE
        FROM public.normas n WHERE n.codigo = 'RD1955_2000'
        ON CONFLICT (nombre) DO NOTHING
    """))
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, activa)
        VALUES ('expediente_heredado',
                'El expediente viene migrado del sistema anterior (datos incompletos posibles)',
                'boolean', TRUE)
        ON CONFLICT (nombre) DO NOTHING
    """))

    # 2. Una regla por tipo de solicitud, cada una con su artículo
    for siglas in ('AAP', 'AAC'):
        articulo, apartado = ARTICULOS[siglas]
        result = conn.execute(sa.text("""
            INSERT INTO public.reglas_motor
                (accion, sujeto, efecto, norma_id, articulo, apartado, prioridad, activa, descripcion)
            SELECT 'CREAR', :sujeto, 'BLOQUEAR', n.id, :articulo, :apartado, 10, TRUE, :descripcion
            FROM public.normas n WHERE n.codigo = 'RD1955_2000'
            RETURNING id
        """), {
            'sujeto': f'ANY/{siglas}/ANY',
            'articulo': articulo,
            'apartado': apartado,
            'descripcion': DESCRIPCIONES[siglas],
        })
        regla_id = result.scalar()

        conn.execute(sa.text("""
            INSERT INTO public.condiciones_regla (regla_id, variable_id, operador, valor, orden)
            SELECT :regla_id, cv.id, 'NEQ', '"ANALISIS_SOLICITUD"'::json, 1
            FROM public.catalogo_variables cv WHERE cv.nombre = 'tipo_sujeto_solicitado'
        """), {'regla_id': regla_id})
        conn.execute(sa.text("""
            INSERT INTO public.condiciones_regla (regla_id, variable_id, operador, valor, orden)
            SELECT :regla_id, cv.id, 'EQ', 'true'::json, 2
            FROM public.catalogo_variables cv WHERE cv.nombre = 'proyecto_sin_principal'
        """), {'regla_id': regla_id})
        conn.execute(sa.text("""
            INSERT INTO public.condiciones_regla (regla_id, variable_id, operador, valor, orden)
            SELECT :regla_id, cv.id, 'EQ', 'false'::json, 3
            FROM public.catalogo_variables cv WHERE cv.nombre = 'expediente_heredado'
        """), {'regla_id': regla_id})


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM public.condiciones_regla
        WHERE regla_id IN (
            SELECT id FROM public.reglas_motor
            WHERE accion = 'CREAR' AND efecto = 'BLOQUEAR'
              AND sujeto IN ('ANY/AAP/ANY', 'ANY/AAC/ANY')
              AND articulo IN ('123', '130')
              AND norma_id = (SELECT id FROM public.normas WHERE codigo = 'RD1955_2000')
        )
    """))
    conn.execute(sa.text("""
        DELETE FROM public.reglas_motor
        WHERE accion = 'CREAR' AND efecto = 'BLOQUEAR'
          AND sujeto IN ('ANY/AAP/ANY', 'ANY/AAC/ANY')
          AND articulo IN ('123', '130')
          AND norma_id = (SELECT id FROM public.normas WHERE codigo = 'RD1955_2000')
    """))
    conn.execute(sa.text("""
        DELETE FROM public.catalogo_variables
        WHERE nombre IN ('proyecto_sin_principal', 'expediente_heredado')
    """))
