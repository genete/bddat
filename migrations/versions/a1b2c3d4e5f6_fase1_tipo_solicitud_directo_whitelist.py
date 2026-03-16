"""fase1_tipo_solicitud_directo_whitelist

Revision ID: a1b2c3d4e5f6
Revises: 20c5d1e9d782
Create Date: 2026-03-16

Fase 1 de #167:
- Crear tablas whitelist: expedientes_solicitudes, solicitudes_fases, fases_tramites
- Insertar tipos de solicitud combinados (AAP_AAC, etc.)
- Añadir FK directa tipo_solicitud_id en solicitudes
- Backfill desde solicitudes_tipos
- Drop tabla solicitudes_tipos
- Seed fases_tramites desde JSON de estructura
"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = '20c5d1e9d782'
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # PASO 1 — Crear tablas whitelist (sin datos aún)
    # =========================================================================
    op.create_table(
        'expedientes_solicitudes',
        sa.Column('tipo_expediente_id', sa.Integer(), nullable=False),
        sa.Column('tipo_solicitud_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['tipo_expediente_id'], ['public.tipos_expedientes.id'],
            name='fk_exp_sol_tipo_expediente'
        ),
        sa.ForeignKeyConstraint(
            ['tipo_solicitud_id'], ['public.tipos_solicitudes.id'],
            name='fk_exp_sol_tipo_solicitud'
        ),
        sa.PrimaryKeyConstraint('tipo_expediente_id', 'tipo_solicitud_id',
                                name='pk_expedientes_solicitudes'),
        schema='public'
    )

    op.create_table(
        'solicitudes_fases',
        sa.Column('tipo_solicitud_id', sa.Integer(), nullable=False),
        sa.Column('tipo_fase_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['tipo_solicitud_id'], ['public.tipos_solicitudes.id'],
            name='fk_sol_fas_tipo_solicitud'
        ),
        sa.ForeignKeyConstraint(
            ['tipo_fase_id'], ['public.tipos_fases.id'],
            name='fk_sol_fas_tipo_fase'
        ),
        sa.PrimaryKeyConstraint('tipo_solicitud_id', 'tipo_fase_id',
                                name='pk_solicitudes_fases'),
        schema='public'
    )

    op.create_table(
        'fases_tramites',
        sa.Column('tipo_fase_id', sa.Integer(), nullable=False),
        sa.Column('tipo_tramite_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['tipo_fase_id'], ['public.tipos_fases.id'],
            name='fk_fas_tram_tipo_fase'
        ),
        sa.ForeignKeyConstraint(
            ['tipo_tramite_id'], ['public.tipos_tramites.id'],
            name='fk_fas_tram_tipo_tramite'
        ),
        sa.PrimaryKeyConstraint('tipo_fase_id', 'tipo_tramite_id',
                                name='pk_fases_tramites'),
        schema='public'
    )

    # =========================================================================
    # PASO 2 — Insertar tipos de solicitud combinados
    # La sigla de un combinado = siglas de los tipos componentes ordenados por id,
    # unidos con '_'. Mismo algoritmo que el backfill del paso 4.
    # =========================================================================
    op.execute("""
        INSERT INTO public.tipos_solicitudes (siglas, descripcion) VALUES
        ('AAP_AAC',
         'Autorización Administrativa Previa + Autorización Administrativa de Construcción'),
        ('AAP_AAC_DUP_AAE_DEFINITIVA',
         'AAP + AAC + Declaración de Utilidad Pública + Autorización de Explotación Definitiva'),
        ('AAP_AAC_RAIPEE_PREVIA_RADNE_INTERESADO',
         'AAP + AAC + Inscripción Previa RAIPEE + RADNE + Condición de Interesado'),
        ('AAT_AMPLIACION_PLAZO',
         'Autorización de Transmisión de Titularidad + Ampliación de Plazo de Ejecución')
    """)

    # =========================================================================
    # PASO 3 — Añadir tipo_solicitud_id nullable a solicitudes
    # =========================================================================
    op.add_column(
        'solicitudes',
        sa.Column('tipo_solicitud_id', sa.Integer(), nullable=True,
                  comment='FK a TIPOS_SOLICITUDES. Tipo directo (atómico o combinado)'),
        schema='public'
    )
    op.create_foreign_key(
        'fk_solicitudes_tipo_solicitud',
        'solicitudes', 'tipos_solicitudes',
        ['tipo_solicitud_id'], ['id'],
        source_schema='public', referent_schema='public'
    )

    # =========================================================================
    # PASO 4 — Backfill: deducir tipo_solicitud_id desde solicitudes_tipos
    # Construye la sigla combinada concatenando siglas ordenadas por id con '_'.
    # El resultado debe existir en tipos_solicitudes.siglas (insertado en paso 2).
    # =========================================================================
    op.execute("""
        UPDATE public.solicitudes s
        SET tipo_solicitud_id = ts_match.id
        FROM (
            SELECT
                st.solicitudid,
                string_agg(ts.siglas, '_' ORDER BY ts.id) AS combo
            FROM public.solicitudes_tipos st
            JOIN public.tipos_solicitudes ts ON ts.id = st.tiposolicitudid
            GROUP BY st.solicitudid
        ) combos
        JOIN public.tipos_solicitudes ts_match ON ts_match.siglas = combos.combo
        WHERE s.id = combos.solicitudid
    """)

    # Verificar backfill completo antes de hacer NOT NULL
    op.execute("""
        DO $$
        DECLARE n_sin_mapear INTEGER;
        BEGIN
            SELECT COUNT(*) INTO n_sin_mapear
            FROM public.solicitudes s
            WHERE s.tipo_solicitud_id IS NULL
              AND EXISTS (
                  SELECT 1 FROM public.solicitudes_tipos st
                  WHERE st.solicitudid = s.id
              );
            IF n_sin_mapear > 0 THEN
                RAISE EXCEPTION
                    'Backfill incompleto: % solicitudes con tipos en solicitudes_tipos sin mapeo en tipos_solicitudes.',
                    n_sin_mapear;
            END IF;
        END $$
    """)

    # =========================================================================
    # PASO 5 — Hacer tipo_solicitud_id NOT NULL
    # =========================================================================
    op.alter_column(
        'solicitudes', 'tipo_solicitud_id',
        nullable=False,
        schema='public'
    )

    # =========================================================================
    # PASO 6 — Drop tabla solicitudes_tipos (punto de no retorno)
    # =========================================================================
    op.drop_table('solicitudes_tipos', schema='public')

    # =========================================================================
    # PASO 7 — Seed fases_tramites desde estructura JSON
    # =========================================================================
    op.execute("""
        INSERT INTO public.fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES
        (1, 1), (1, 2),
        (2, 3), (2, 4),
        (3, 5), (3, 6),
        (4, 7), (4, 8),
        (5, 9), (5, 10), (5, 11),
        (6, 12), (6, 13),
        (7, 14), (7, 15), (7, 16),
        (8, 17), (8, 18), (8, 19), (8, 20), (8, 21), (8, 22), (8, 23),
        (9, 24), (9, 25),
        (10, 26), (10, 27),
        (11, 28), (11, 29), (11, 30)
    """)


def downgrade():
    # Recrear solicitudes_tipos
    op.create_table(
        'solicitudes_tipos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('solicitudid', sa.Integer(), nullable=False),
        sa.Column('tiposolicitudid', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['solicitudid'], ['public.solicitudes.id'],
                                name='solicitudes_tipos_solicitudid_fkey',
                                ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tiposolicitudid'], ['public.tipos_solicitudes.id'],
                                name='solicitudes_tipos_tiposolicitudid_fkey'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('solicitudid', 'tiposolicitudid',
                            name='solicitudes_tipos_solicitudid_tiposolicitudid_key'),
        schema='public'
    )
    op.create_index('idx_solicitudes_tipos_solicitud', 'solicitudes_tipos',
                    ['solicitudid'], schema='public')
    op.create_index('idx_solicitudes_tipos_tipo', 'solicitudes_tipos',
                    ['tiposolicitudid'], schema='public')

    # Restaurar solo tipos individuales (combinados no son reversibles)
    op.execute("""
        INSERT INTO public.solicitudes_tipos (solicitudid, tiposolicitudid)
        SELECT s.id, s.tipo_solicitud_id
        FROM public.solicitudes s
        WHERE s.tipo_solicitud_id IS NOT NULL
          AND s.tipo_solicitud_id <= 17
    """)

    op.drop_constraint('fk_solicitudes_tipo_solicitud', 'solicitudes',
                       schema='public', type_='foreignkey')
    op.drop_column('solicitudes', 'tipo_solicitud_id', schema='public')

    op.execute("DELETE FROM public.tipos_solicitudes WHERE id > 17")

    op.drop_table('fases_tramites', schema='public')
    op.drop_table('solicitudes_fases', schema='public')
    op.drop_table('expedientes_solicitudes', schema='public')
