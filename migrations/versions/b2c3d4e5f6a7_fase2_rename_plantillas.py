"""Fase 2 #167: Renombrar tipos_escritos a plantillas + campos nuevos

- RENAME TABLE tipos_escritos → plantillas (con PK, UQ y FKs)
- ADD tipo_expediente_id FK nullable en plantillas
- DROP campos_catalogo en plantillas
- ADD variante TEXT nullable en plantillas
- ADD origen VARCHAR(10) NOT NULL DEFAULT 'AMBOS' en tipos_documentos

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-16
"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # ── Paso 1: Renombrar tabla ──────────────────────────────────────────────
    op.rename_table('tipos_escritos', 'plantillas', schema='public')

    # ── Paso 2: Renombrar secuencia asociada al id serial ───────────────────
    op.execute('ALTER SEQUENCE public.tipos_escritos_id_seq RENAME TO plantillas_id_seq')

    # ── Paso 3: Renombrar PK ─────────────────────────────────────────────────
    op.execute(
        'ALTER TABLE public.plantillas '
        'RENAME CONSTRAINT tipos_escritos_pkey TO plantillas_pkey'
    )

    # ── Paso 4: Renombrar UQ ─────────────────────────────────────────────────
    op.execute(
        'ALTER TABLE public.plantillas '
        'RENAME CONSTRAINT uq_tipos_escritos_codigo TO uq_plantillas_codigo'
    )

    # ── Paso 5: Renombrar FKs ────────────────────────────────────────────────
    for old, new in [
        ('fk_tipos_escritos_tipo_documento', 'fk_plantillas_tipo_documento'),
        ('fk_tipos_escritos_tipo_solicitud', 'fk_plantillas_tipo_solicitud'),
        ('fk_tipos_escritos_tipo_fase',      'fk_plantillas_tipo_fase'),
        ('fk_tipos_escritos_tipo_tramite',   'fk_plantillas_tipo_tramite'),
    ]:
        op.execute(
            f'ALTER TABLE public.plantillas RENAME CONSTRAINT {old} TO {new}'
        )

    # ── Paso 6: ADD tipo_expediente_id FK nullable ───────────────────────────
    op.add_column('plantillas', sa.Column(
        'tipo_expediente_id',
        sa.Integer(),
        nullable=True,
        comment='FK tipos_expedientes. NULL = aplica a cualquier tipo de expediente',
    ), schema='public')
    op.create_foreign_key(
        'fk_plantillas_tipo_expediente',
        'plantillas', 'tipos_expedientes',
        ['tipo_expediente_id'], ['id'],
        source_schema='public', referent_schema='public',
    )

    # ── Paso 7: DROP campos_catalogo (export previo en Fase 0) ───────────────
    op.drop_column('plantillas', 'campos_catalogo', schema='public')

    # ── Paso 8: ADD variante TEXT nullable ───────────────────────────────────
    op.add_column('plantillas', sa.Column(
        'variante',
        sa.Text(),
        nullable=True,
        comment='Texto libre para distinguir plantillas del mismo contexto ESFTT (Favorable, Denegatoria…)',
    ), schema='public')

    # ── Paso 9: ADD origen en tipos_documentos ───────────────────────────────
    op.add_column('tipos_documentos', sa.Column(
        'origen',
        sa.String(10),
        nullable=False,
        server_default='AMBOS',
        comment='Origen del documento: INTERNO (generado por administración), EXTERNO (aportado por interesado), AMBOS',
    ), schema='public')
    op.create_check_constraint(
        'ck_tipos_documentos_origen',
        'tipos_documentos',
        "origen IN ('INTERNO', 'EXTERNO', 'AMBOS')",
        schema='public',
    )

    # ── Paso 10: Seed origen para tipos existentes ───────────────────────────
    op.execute("UPDATE public.tipos_documentos SET origen = 'AMBOS'   WHERE codigo = 'OTROS'")
    op.execute("UPDATE public.tipos_documentos SET origen = 'EXTERNO' WHERE codigo = 'DR_NO_DUP'")


def downgrade():
    # Paso 10 + 9: DROP origen en tipos_documentos
    op.drop_constraint('ck_tipos_documentos_origen', 'tipos_documentos', schema='public', type_='check')
    op.drop_column('tipos_documentos', 'origen', schema='public')

    # Paso 8: DROP variante
    op.drop_column('plantillas', 'variante', schema='public')

    # Paso 7: ADD campos_catalogo de vuelta (null, sin datos — se perdieron al hacer DROP)
    op.add_column('plantillas', sa.Column(
        'campos_catalogo',
        sa.JSON(),
        nullable=True,
        comment='[{campo, descripcion}] — restaurado por downgrade, sin datos',
    ), schema='public')

    # Paso 6: DROP tipo_expediente_id
    op.drop_constraint('fk_plantillas_tipo_expediente', 'plantillas', schema='public', type_='foreignkey')
    op.drop_column('plantillas', 'tipo_expediente_id', schema='public')

    # Paso 5: Renombrar FKs de vuelta
    for old, new in [
        ('fk_plantillas_tipo_tramite',   'fk_tipos_escritos_tipo_tramite'),
        ('fk_plantillas_tipo_fase',      'fk_tipos_escritos_tipo_fase'),
        ('fk_plantillas_tipo_solicitud', 'fk_tipos_escritos_tipo_solicitud'),
        ('fk_plantillas_tipo_documento', 'fk_tipos_escritos_tipo_documento'),
    ]:
        op.execute(
            f'ALTER TABLE public.plantillas RENAME CONSTRAINT {old} TO {new}'
        )

    # Paso 4: Renombrar UQ de vuelta
    op.execute(
        'ALTER TABLE public.plantillas '
        'RENAME CONSTRAINT uq_plantillas_codigo TO uq_tipos_escritos_codigo'
    )

    # Paso 3: Renombrar PK de vuelta
    op.execute(
        'ALTER TABLE public.plantillas '
        'RENAME CONSTRAINT plantillas_pkey TO tipos_escritos_pkey'
    )

    # Paso 2: Renombrar secuencia de vuelta
    op.execute('ALTER SEQUENCE public.plantillas_id_seq RENAME TO tipos_escritos_id_seq')

    # Paso 1: Renombrar tabla de vuelta
    op.rename_table('plantillas', 'tipos_escritos', schema='public')
