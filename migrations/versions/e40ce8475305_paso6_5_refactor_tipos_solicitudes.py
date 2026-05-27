"""paso6_5_refactor_tipos_solicitudes

Revision ID: e40ce8475305
Revises: f58e0e31f0b2
Create Date: 2026-04-23 18:31:47.591083

Refactoriza tipos_solicitudes para separador + en combinados y elimina tabla obsoleta.

Cambios:
  - tipos_solicitudes IDs 4,5: AAE_ → AE_ (siglas correctas para AE provisional/definitiva)
  - tipos_solicitudes ID 18: AAP_AAC → AAP+AAC
  - tipos_solicitudes ID 19: combo inválido → AAP+AAC+DUP
  - tipos_solicitudes ID 20: combo inválido → AAC+DUP
  - tipos_solicitudes ID 21: combo inválido → AE_DEFINITIVA+AAT
  - DROP TABLE tipos_solicitudes_compatibles (vacía, reemplazada por separador + en siglas)

Las solicitudes existentes no se modifican — los tipos que cambian de significado
quedan como casos de test de combinaciones inusuales para el motor.
"""
from alembic import op
import sqlalchemy as sa


revision = 'e40ce8475305'
down_revision = 'f58e0e31f0b2'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Renombrar siglas de tipos atómicos: AAE_ → AE_
    op.execute("""
        UPDATE public.tipos_solicitudes SET
            siglas = 'AE_PROVISIONAL',
            descripcion = 'Autorización de Explotación Provisional para Pruebas'
        WHERE id = 4
    """)
    op.execute("""
        UPDATE public.tipos_solicitudes SET
            siglas = 'AE_DEFINITIVA',
            descripcion = 'Autorización de Explotación Definitiva'
        WHERE id = 5
    """)

    # 2. Renombrar tipo combinado 18: separador _ → +
    op.execute("""
        UPDATE public.tipos_solicitudes SET
            siglas = 'AAP+AAC',
            descripcion = 'Autorización Administrativa Previa + Autorización Administrativa de Construcción'
        WHERE id = 18
    """)

    # 3. Reutilizar ID 19 para AAP+AAC+DUP (válido: art. 143.2 RD 1955/2000)
    op.execute("""
        UPDATE public.tipos_solicitudes SET
            siglas = 'AAP+AAC+DUP',
            descripcion = 'Autorización Administrativa Previa + Construcción + Declaración de Utilidad Pública'
        WHERE id = 19
    """)

    # 4. Reutilizar ID 20 para AAC+DUP (válido: DUP posterior a AAP ya obtenida)
    op.execute("""
        UPDATE public.tipos_solicitudes SET
            siglas = 'AAC+DUP',
            descripcion = 'Autorización Administrativa de Construcción + Declaración de Utilidad Pública'
        WHERE id = 20
    """)

    # 5. Reutilizar ID 21 para AE_DEFINITIVA+AAT (cesión promotor→compañía)
    op.execute("""
        UPDATE public.tipos_solicitudes SET
            siglas = 'AE_DEFINITIVA+AAT',
            descripcion = 'Autorización de Explotación Definitiva + Autorización de Transmisión de Titularidad'
        WHERE id = 21
    """)

    # 6. Eliminar tabla ya no necesaria (estaba vacía; el separador + reemplaza su función)
    op.drop_index('idx_compatibles_tipo_a', table_name='tipos_solicitudes_compatibles', schema='public')
    op.drop_index('idx_compatibles_tipo_b', table_name='tipos_solicitudes_compatibles', schema='public')
    op.drop_table('tipos_solicitudes_compatibles', schema='public')


def downgrade():
    # 6. Recrear tipos_solicitudes_compatibles
    op.create_table(
        'tipos_solicitudes_compatibles',
        sa.Column('tipo_a_id', sa.Integer, primary_key=True,
                  comment='FK a TIPOS_SOLICITUDES. Siempre el ID menor del par'),
        sa.Column('tipo_b_id', sa.Integer, primary_key=True,
                  comment='FK a TIPOS_SOLICITUDES. Siempre el ID mayor del par'),
        sa.Column('nota', sa.String(200), nullable=True,
                  comment='Explicación de la compatibilidad / referencia normativa'),
        sa.CheckConstraint('tipo_a_id < tipo_b_id', name='ck_compatibles_orden'),
        sa.ForeignKeyConstraint(['tipo_a_id'], ['public.tipos_solicitudes.id']),
        sa.ForeignKeyConstraint(['tipo_b_id'], ['public.tipos_solicitudes.id']),
        schema='public',
    )
    op.create_index('idx_compatibles_tipo_a', 'tipos_solicitudes_compatibles', ['tipo_a_id'], schema='public')
    op.create_index('idx_compatibles_tipo_b', 'tipos_solicitudes_compatibles', ['tipo_b_id'], schema='public')

    # 5. Restaurar ID 21
    op.execute("""
        UPDATE public.tipos_solicitudes SET
            siglas = 'AAT_AMPLIACION_PLAZO',
            descripcion = 'Autorización de Transmisión de Titularidad + Ampliación de Plazo de Ejecución'
        WHERE id = 21
    """)

    # 4. Restaurar ID 20
    op.execute("""
        UPDATE public.tipos_solicitudes SET
            siglas = 'AAP_AAC_RAIPEE_PREVIA_RADNE_INTERESADO',
            descripcion = 'AAP + AAC + Inscripción Previa RAIPEE + RADNE + Condición de Interesado'
        WHERE id = 20
    """)

    # 3. Restaurar ID 19
    op.execute("""
        UPDATE public.tipos_solicitudes SET
            siglas = 'AAP_AAC_DUP_AAE_DEFINITIVA',
            descripcion = 'AAP + AAC + Declaración de Utilidad Pública + Autorización de Explotación Definitiva'
        WHERE id = 19
    """)

    # 2. Restaurar ID 18
    op.execute("""
        UPDATE public.tipos_solicitudes SET
            siglas = 'AAP_AAC',
            descripcion = 'Autorización Administrativa Previa + Autorización Administrativa de Construcción'
        WHERE id = 18
    """)

    # 1. Restaurar IDs 4 y 5
    op.execute("""
        UPDATE public.tipos_solicitudes SET
            siglas = 'AAE_DEFINITIVA',
            descripcion = 'Autorización de Explotación Definitiva'
        WHERE id = 5
    """)
    op.execute("""
        UPDATE public.tipos_solicitudes SET
            siglas = 'AAE_PROVISIONAL',
            descripcion = 'Autorización de Explotación Provisional para Pruebas'
        WHERE id = 4
    """)
