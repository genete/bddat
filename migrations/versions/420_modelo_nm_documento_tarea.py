"""420_modelo_nm_documento_tarea

Revision ID: 420_modelo_nm_documento_tarea
Revises: 377_descripciones_tipos_doc
Create Date: 2026-05-17

Issue #420 — ADR-010. Sustituye las FK documento_usado_id/documento_producido_id
de tareas por la tabla multiusos documentos_tarea con campo rol.

Alcance: solo esquema y catálogo. Los vínculos documento_usado_id presentes en
tareas son datos de desarrollo no productivos y no se migran — se regeneran vía
seed. Sí se corrige catalogo_plazos (dato de catálogo): las entradas cuyo
campo_fecha referencia las FK eliminadas pasan al mecanismo basado en rol.
"""
from alembic import op
import sqlalchemy as sa


revision = '420_modelo_nm_documento_tarea'
down_revision = '377_descripciones_tipos_doc'
branch_labels = None
depends_on = None


# La consulta nombrada 'organismos_consulta' (#395) es dato de catálogo: su SQL
# referencia las FK eliminadas y debe pasar a navegar vía documentos_tarea.
_SQL_ORG_CONSULTA_NUEVA = """\
SELECT
    e.nombre_completo                                        AS organismo_nombre,
    e.nif                                                    AS organismo_nif,
    oe.plazo_legal_dias                                      AS organismo_plazo_legal,
    oe.estado                                                AS organismo_resultado,
    TO_CHAR(d_notif.fecha_administrativa, 'DD/MM/YYYY')      AS organismo_fecha_envio,
    TO_CHAR(d_resp.fecha_administrativa,  'DD/MM/YYYY')      AS organismo_fecha_respuesta
FROM public.organismos_expediente oe
JOIN public.entidades e
    ON e.id = oe.organismo_id
LEFT JOIN public.tramites tr
    ON tr.id = oe.tramite_id
LEFT JOIN public.tareas t_n
    ON t_n.tramite_id = tr.id
    AND t_n.tipo_tarea_id = (SELECT id FROM public.tipos_tareas WHERE codigo = 'NOTIFICAR')
LEFT JOIN public.documentos_tarea dt_n
    ON dt_n.tarea_id = t_n.id AND dt_n.rol = 'PRODUCIDO'
LEFT JOIN public.documentos d_notif
    ON d_notif.id = dt_n.documento_id
LEFT JOIN public.tareas t_a
    ON t_a.tramite_id = tr.id
    AND t_a.tipo_tarea_id = (SELECT id FROM public.tipos_tareas WHERE codigo = 'ANALIZAR')
LEFT JOIN public.documentos_tarea dt_a
    ON dt_a.tarea_id = t_a.id AND dt_a.rol = 'CONSUMIDO'
LEFT JOIN public.documentos d_resp
    ON d_resp.id = dt_a.documento_id
WHERE oe.expediente_id = :expediente_id
ORDER BY e.nombre_completo"""

_SQL_ORG_CONSULTA_VIEJA = """\
SELECT
    e.nombre_completo                                        AS organismo_nombre,
    e.nif                                                    AS organismo_nif,
    oe.plazo_legal_dias                                      AS organismo_plazo_legal,
    oe.estado                                                AS organismo_resultado,
    TO_CHAR(d_notif.fecha_administrativa, 'DD/MM/YYYY')      AS organismo_fecha_envio,
    TO_CHAR(d_resp.fecha_administrativa,  'DD/MM/YYYY')      AS organismo_fecha_respuesta
FROM public.organismos_expediente oe
JOIN public.entidades e
    ON e.id = oe.organismo_id
LEFT JOIN public.tramites tr
    ON tr.id = oe.tramite_id
LEFT JOIN public.tareas t_n
    ON t_n.tramite_id = tr.id
    AND t_n.tipo_tarea_id = (SELECT id FROM public.tipos_tareas WHERE codigo = 'NOTIFICAR')
LEFT JOIN public.documentos d_notif
    ON d_notif.id = t_n.documento_producido_id
LEFT JOIN public.tareas t_a
    ON t_a.tramite_id = tr.id
    AND t_a.tipo_tarea_id = (SELECT id FROM public.tipos_tareas WHERE codigo = 'ANALIZAR')
LEFT JOIN public.documentos d_resp
    ON d_resp.id = t_a.documento_usado_id
WHERE oe.expediente_id = :expediente_id
ORDER BY e.nombre_completo"""


def upgrade():
    # --- documentos_tarea: añadir rol y reconstruir constraints ---
    op.add_column(
        'documentos_tarea',
        sa.Column('rol', sa.String(length=12), nullable=False,
                  comment='Rol del vínculo: CONSUMIDO (entrada) | PRODUCIDO (salida)'),
        schema='public',
    )
    op.create_check_constraint(
        'ck_documentos_tarea_rol', 'documentos_tarea',
        "rol IN ('CONSUMIDO', 'PRODUCIDO')", schema='public',
    )
    op.drop_constraint('uq_documentos_tarea', 'documentos_tarea',
                       schema='public', type_='unique')
    op.create_unique_constraint(
        'uq_documentos_tarea_rol', 'documentos_tarea',
        ['tarea_id', 'documento_id', 'rol'], schema='public',
    )
    # Un documento tiene un único productor (sustituye al UNIQUE de
    # tareas.documento_producido_id).
    op.create_index(
        'uq_documento_un_productor', 'documentos_tarea', ['documento_id'],
        unique=True, schema='public',
        postgresql_where=sa.text("rol = 'PRODUCIDO'"),
    )
    # Una tarea produce a lo sumo un documento.
    op.create_index(
        'uq_tarea_un_producido', 'documentos_tarea', ['tarea_id'],
        unique=True, schema='public',
        postgresql_where=sa.text("rol = 'PRODUCIDO'"),
    )
    op.execute('GRANT SELECT ON public.documentos_tarea TO claude_desktop')

    # --- catalogo_plazos: campo_fecha pasa de fk a rol ---
    op.execute("""
        UPDATE public.catalogo_plazos
        SET campo_fecha = (campo_fecha - 'fk')
                          || jsonb_build_object('rol', 'CONSUMIDO')
        WHERE campo_fecha ->> 'fk' = 'documento_usado_id'
    """)
    op.execute("""
        UPDATE public.catalogo_plazos
        SET campo_fecha = (campo_fecha - 'fk')
                          || jsonb_build_object('rol', 'PRODUCIDO')
        WHERE campo_fecha ->> 'fk' = 'documento_producido_id'
    """)

    # --- consultas_nombradas: SQL de 'organismos_consulta' vía documentos_tarea ---
    op.get_bind().execute(
        sa.text("UPDATE public.consultas_nombradas SET sql = :sql "
                "WHERE nombre = 'organismos_consulta'"),
        {'sql': _SQL_ORG_CONSULTA_NUEVA},
    )

    # --- tareas: eliminar las FK simples a documentos ---
    op.drop_index('idx_tareas_documento_usado', table_name='tareas', schema='public')
    op.drop_column('tareas', 'documento_producido_id', schema='public')
    op.drop_column('tareas', 'documento_usado_id', schema='public')


def downgrade():
    op.add_column(
        'tareas',
        sa.Column('documento_usado_id', sa.Integer(), nullable=True,
                  comment='FK a DOCUMENTOS. Documento usado como input de la tarea'),
        schema='public',
    )
    op.add_column(
        'tareas',
        sa.Column('documento_producido_id', sa.Integer(), nullable=True,
                  comment='FK UNIQUE a DOCUMENTOS. Documento generado como output de la tarea'),
        schema='public',
    )
    op.create_foreign_key(
        'tareas_documento_usado_id_fkey', 'tareas', 'documentos',
        ['documento_usado_id'], ['id'],
        source_schema='public', referent_schema='public',
    )
    op.create_foreign_key(
        'tareas_documento_producido_id_fkey', 'tareas', 'documentos',
        ['documento_producido_id'], ['id'],
        source_schema='public', referent_schema='public',
    )
    op.create_unique_constraint(
        'tareas_documento_producido_id_key', 'tareas',
        ['documento_producido_id'], schema='public',
    )
    op.create_index('idx_tareas_documento_usado', 'tareas',
                    ['documento_usado_id'], schema='public')

    op.execute("""
        UPDATE public.catalogo_plazos
        SET campo_fecha = (campo_fecha - 'rol')
                          || jsonb_build_object('fk', 'documento_usado_id')
        WHERE campo_fecha ->> 'rol' = 'CONSUMIDO'
    """)
    op.execute("""
        UPDATE public.catalogo_plazos
        SET campo_fecha = (campo_fecha - 'rol')
                          || jsonb_build_object('fk', 'documento_producido_id')
        WHERE campo_fecha ->> 'rol' = 'PRODUCIDO'
    """)

    op.get_bind().execute(
        sa.text("UPDATE public.consultas_nombradas SET sql = :sql "
                "WHERE nombre = 'organismos_consulta'"),
        {'sql': _SQL_ORG_CONSULTA_VIEJA},
    )

    op.drop_index('uq_tarea_un_producido', table_name='documentos_tarea', schema='public')
    op.drop_index('uq_documento_un_productor', table_name='documentos_tarea', schema='public')
    op.drop_constraint('uq_documentos_tarea_rol', 'documentos_tarea',
                       schema='public', type_='unique')
    op.create_unique_constraint(
        'uq_documentos_tarea', 'documentos_tarea',
        ['tarea_id', 'documento_id'], schema='public',
    )
    op.drop_constraint('ck_documentos_tarea_rol', 'documentos_tarea',
                       schema='public', type_='check')
    op.drop_column('documentos_tarea', 'rol', schema='public')
