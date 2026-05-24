"""456_tramites_organismos

Revision ID: 456_tramites_organismos
Revises: 448_seed_plazos_resolucion
Create Date: 2026-05-24

Issue #456 — ADR-011: vinculación trámites↔organismos y criterios de completitud CONSULTAS.

Cambios de esquema:
  1. Nueva tabla `tramites_organismos` (id, tramite_id UNIQUE FK→tramites, organismo_expediente_id FK→organismos_expediente).
  2. Drop columna `tramite_id` (+ FK fk_org_exp_tramite + UC uq_org_exp_tramite) de `organismos_expediente`.
  3. Drop columna `num_iteraciones_organismo` de `organismos_expediente`.
  4. Añadir columna `condicionados_doc_id` (nullable FK→documentos) a `organismos_expediente`.
  5. Seed tipo_documento `CONDICIONADO_OFICIO`.
  6. GRANT SELECT en `tramites_organismos` al rol claude_desktop.
"""
from alembic import op
import sqlalchemy as sa


revision = '456_tramites_organismos'
down_revision = '448_seed_plazos_resolucion'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Nueva tabla tramites_organismos
    op.create_table(
        'tramites_organismos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tramite_id', sa.Integer(), nullable=False,
                  comment='FK tramites (UNIQUE — un trámite pertenece a un solo organismo)'),
        sa.Column('organismo_expediente_id', sa.Integer(), nullable=False,
                  comment='FK organismos_expediente. Organismo al que pertenece el trámite'),
        sa.PrimaryKeyConstraint('id', name='pk_tramites_organismos'),
        sa.ForeignKeyConstraint(['tramite_id'], ['public.tramites.id'],
                                name='fk_tramorg_tramite', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organismo_expediente_id'], ['public.organismos_expediente.id'],
                                name='fk_tramorg_organismo_expediente', ondelete='CASCADE'),
        sa.UniqueConstraint('tramite_id', name='uq_tramorg_tramite'),
        schema='public',
    )
    op.create_index('idx_tramorg_organismo', 'tramites_organismos',
                    ['organismo_expediente_id'], schema='public')

    # 2. Drop tramite_id de organismos_expediente
    op.drop_constraint('uq_org_exp_tramite', 'organismos_expediente', schema='public', type_='unique')
    op.drop_constraint('fk_org_exp_tramite', 'organismos_expediente', schema='public', type_='foreignkey')
    op.drop_column('organismos_expediente', 'tramite_id', schema='public')

    # 3. Drop num_iteraciones_organismo de organismos_expediente
    op.drop_column('organismos_expediente', 'num_iteraciones_organismo', schema='public')

    # 4. Añadir condicionados_doc_id a organismos_expediente
    op.add_column(
        'organismos_expediente',
        sa.Column('condicionados_doc_id', sa.Integer(), nullable=True,
                  comment='FK documentos (CONDICIONADO_OFICIO). Solo cuando titular sin_respuesta en AAC tras condicionado'),
        schema='public',
    )
    op.create_foreign_key(
        'fk_org_exp_condicionados_doc',
        'organismos_expediente', 'documentos',
        ['condicionados_doc_id'], ['id'],
        source_schema='public', referent_schema='public',
    )

    # 5. Seed CONDICIONADO_OFICIO
    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO public.tipos_documentos (codigo, nombre, origen)
        VALUES ('CONDICIONADO_OFICIO',
                'Condicionados incorporados de oficio por falta de respuesta del titular',
                'INTERNO')
        ON CONFLICT (codigo) DO NOTHING
    """))

    # 6. Grant SELECT al rol claude_desktop
    op.execute("GRANT SELECT ON public.tramites_organismos TO claude_desktop")

    # 7. Actualizar consulta nombrada organismos_consulta (#395) para usar tramites_organismos
    _SQL_NUEVO = (
        "SELECT\n"
        "    e.nombre_completo                                        AS organismo_nombre,\n"
        "    e.nif                                                    AS organismo_nif,\n"
        "    oe.plazo_legal_dias                                      AS organismo_plazo_legal,\n"
        "    oe.estado                                                AS organismo_resultado,\n"
        "    TO_CHAR(d_notif.fecha_administrativa, 'DD/MM/YYYY')      AS organismo_fecha_envio,\n"
        "    TO_CHAR(d_resp.fecha_administrativa,  'DD/MM/YYYY')      AS organismo_fecha_respuesta\n"
        "FROM public.organismos_expediente oe\n"
        "JOIN public.entidades e\n"
        "    ON e.id = oe.organismo_id\n"
        "LEFT JOIN public.tramites_organismos torg\n"
        "    ON torg.organismo_expediente_id = oe.id\n"
        "LEFT JOIN public.tramites tr\n"
        "    ON tr.id = torg.tramite_id\n"
        "LEFT JOIN public.tareas t_n\n"
        "    ON t_n.tramite_id = tr.id\n"
        "    AND t_n.tipo_tarea_id = (SELECT id FROM public.tipos_tareas WHERE codigo = 'NOTIFICAR')\n"
        "LEFT JOIN public.documentos_tarea dt_n\n"
        "    ON dt_n.tarea_id = t_n.id AND dt_n.rol = 'PRODUCIDO'\n"
        "LEFT JOIN public.documentos d_notif\n"
        "    ON d_notif.id = dt_n.documento_id\n"
        "LEFT JOIN public.tareas t_a\n"
        "    ON t_a.tramite_id = tr.id\n"
        "    AND t_a.tipo_tarea_id = (SELECT id FROM public.tipos_tareas WHERE codigo = 'ANALIZAR')\n"
        "LEFT JOIN public.documentos_tarea dt_a\n"
        "    ON dt_a.tarea_id = t_a.id AND dt_a.rol = 'CONSUMIDO'\n"
        "LEFT JOIN public.documentos d_resp\n"
        "    ON d_resp.id = dt_a.documento_id\n"
        "WHERE oe.expediente_id = :expediente_id\n"
        "ORDER BY e.nombre_completo"
    )
    conn.execute(sa.text(
        "UPDATE public.consultas_nombradas SET sql = :sql WHERE nombre = 'organismos_consulta'"
    ), {"sql": _SQL_NUEVO})


def downgrade():
    op.execute("REVOKE SELECT ON public.tramites_organismos FROM claude_desktop")

    conn = op.get_bind()

    # Restaurar SQL de organismos_consulta a la versión anterior a #456
    _SQL_ANTERIOR = (
        "SELECT\n"
        "    e.nombre_completo                                        AS organismo_nombre,\n"
        "    e.nif                                                    AS organismo_nif,\n"
        "    oe.plazo_legal_dias                                      AS organismo_plazo_legal,\n"
        "    oe.estado                                                AS organismo_resultado,\n"
        "    TO_CHAR(d_notif.fecha_administrativa, 'DD/MM/YYYY')      AS organismo_fecha_envio,\n"
        "    TO_CHAR(d_resp.fecha_administrativa,  'DD/MM/YYYY')      AS organismo_fecha_respuesta\n"
        "FROM public.organismos_expediente oe\n"
        "JOIN public.entidades e\n"
        "    ON e.id = oe.organismo_id\n"
        "LEFT JOIN public.tramites tr\n"
        "    ON tr.id = oe.tramite_id\n"
        "LEFT JOIN public.tareas t_n\n"
        "    ON t_n.tramite_id = tr.id\n"
        "    AND t_n.tipo_tarea_id = (SELECT id FROM public.tipos_tareas WHERE codigo = 'NOTIFICAR')\n"
        "LEFT JOIN public.documentos_tarea dt_n\n"
        "    ON dt_n.tarea_id = t_n.id AND dt_n.rol = 'PRODUCIDO'\n"
        "LEFT JOIN public.documentos d_notif\n"
        "    ON d_notif.id = dt_n.documento_id\n"
        "LEFT JOIN public.tareas t_a\n"
        "    ON t_a.tramite_id = tr.id\n"
        "    AND t_a.tipo_tarea_id = (SELECT id FROM public.tipos_tareas WHERE codigo = 'ANALIZAR')\n"
        "LEFT JOIN public.documentos_tarea dt_a\n"
        "    ON dt_a.tarea_id = t_a.id AND dt_a.rol = 'CONSUMIDO'\n"
        "LEFT JOIN public.documentos d_resp\n"
        "    ON d_resp.id = dt_a.documento_id\n"
        "WHERE oe.expediente_id = :expediente_id\n"
        "ORDER BY e.nombre_completo"
    )
    conn.execute(sa.text(
        "UPDATE public.consultas_nombradas SET sql = :sql WHERE nombre = 'organismos_consulta'"
    ), {"sql": _SQL_ANTERIOR})

    conn.execute(sa.text(
        "DELETE FROM public.tipos_documentos WHERE codigo = 'CONDICIONADO_OFICIO'"
    ))

    op.drop_constraint('fk_org_exp_condicionados_doc', 'organismos_expediente',
                       schema='public', type_='foreignkey')
    op.drop_column('organismos_expediente', 'condicionados_doc_id', schema='public')

    op.add_column(
        'organismos_expediente',
        sa.Column('num_iteraciones_organismo', sa.Integer(), nullable=False, server_default='0',
                  comment='Contador de trámites CONSULTA_TRASLADO_ORGANISMO creados'),
        schema='public',
    )
    op.add_column(
        'organismos_expediente',
        sa.Column('tramite_id', sa.Integer(), nullable=True,
                  comment='FK al trámite CONSULTA_SEPARATA asociado. NULL hasta que se crea'),
        schema='public',
    )
    op.create_foreign_key(
        'fk_org_exp_tramite',
        'organismos_expediente', 'tramites',
        ['tramite_id'], ['id'],
        source_schema='public', referent_schema='public',
    )
    op.create_unique_constraint('uq_org_exp_tramite', 'organismos_expediente',
                                ['tramite_id'], schema='public')

    op.drop_index('idx_tramorg_organismo', table_name='tramites_organismos', schema='public')
    op.drop_table('tramites_organismos', schema='public')
