"""396_organismos_fase_resultado

Revision ID: 396_organismos_fase_resultado
Revises: 783_tenida_por_desistida
Create Date: 2026-08-26

Issue #396 — dos cambios de contrato en `organismos_expediente`, previos a la
UI del nodo `organismo` (ADR-042):

1. Columna `fase_id` (FK fases.id) + UNIQUE(fase_id, organismo_id) en lugar de
   (expediente_id, organismo_id). El registro nace ligado a la fase CONSULTAS
   en la que se acuerda consultar al organismo, no al expediente en abstracto:
   sin esto, un organismo sin trámites (recién dado de alta, o exonerado por
   declaración responsable) no tiene padre determinable en el árbol
   (ADR-042 §A), y un modificado de proyecto que obligue a una segunda ronda
   de consultas no puede volver a consultar al mismo organismo (UNIQUE previo
   por expediente lo impedía). DISEÑO_CONSULTAS_ORGANISMOS.md §2/§6 bis.

2. `estado` → `resultado`: la columna deja de modelar el ciclo de vida
   (pendiente/separata_enviada/en_tramitacion — eso ya lo deriva
   estado_dominio.estado_organismo() de los trámites vinculados) y pasa a
   guardar solo el resultado legal de la consulta. Se queda con los 4 valores
   terminales, NULL mientras el ciclo está en curso. DISEÑO_CONSULTAS_ORGANISMOS.md §7.

Arrastra una actualización de la consulta nombrada `organismos_consulta`
(seed #395, reescrita en #456) que lee `oe.estado AS organismo_resultado`.

Tabla vacía en desarrollo (0 filas) — sin backfill necesario.
"""
from alembic import op
import sqlalchemy as sa


revision = '396_organismos_fase_resultado'
down_revision = '783_tenida_por_desistida'
branch_labels = None
depends_on = None


_SQL_ANTERIOR = """\
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
LEFT JOIN public.tramites_organismos torg
    ON torg.organismo_expediente_id = oe.id
LEFT JOIN public.tramites tr
    ON tr.id = torg.tramite_id
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

_SQL_NUEVO = _SQL_ANTERIOR.replace(
    'oe.estado                                                AS organismo_resultado,',
    'oe.resultado                                             AS organismo_resultado,',
)


def upgrade():
    # 1. fase_id — FK + índice. NOT NULL directo: tabla vacía, sin backfill.
    op.add_column(
        'organismos_expediente',
        sa.Column('fase_id', sa.Integer(), nullable=False,
                  comment='FK fases. Fase CONSULTAS (= la ronda) en la que se consulta a este organismo'),
        schema='public',
    )
    op.create_foreign_key(
        'fk_org_exp_fase', 'organismos_expediente', 'fases',
        ['fase_id'], ['id'], source_schema='public', referent_schema='public',
        ondelete='CASCADE',
    )
    op.create_index('idx_org_exp_fase', 'organismos_expediente', ['fase_id'], schema='public')

    # 2. UNIQUE (expediente_id, organismo_id) → (fase_id, organismo_id)
    op.drop_constraint('uq_org_exp_expediente_organismo', 'organismos_expediente',
                       schema='public', type_='unique')
    op.create_unique_constraint(
        'uq_org_exp_fase_organismo', 'organismos_expediente',
        ['fase_id', 'organismo_id'], schema='public',
    )

    # 3. estado → resultado: nullable, sin default, CHECK admite NULL.
    op.drop_constraint('ck_org_exp_estado', 'organismos_expediente', schema='public', type_='check')
    op.alter_column(
        'organismos_expediente', 'estado',
        new_column_name='resultado', nullable=True, server_default=None,
        schema='public',
    )
    op.create_check_constraint(
        'ck_org_exp_resultado', 'organismos_expediente',
        "resultado IS NULL OR resultado IN ('cerrado_favorable',"
        "'cerrado_con_condicionados','audiencia_previa','exonerado')",
        schema='public',
    )

    # 4. Actualizar consulta nombrada organismos_consulta (#395/#456)
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE public.consultas_nombradas SET sql = :sql WHERE nombre = 'organismos_consulta'"
    ), {"sql": _SQL_NUEVO})


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE public.consultas_nombradas SET sql = :sql WHERE nombre = 'organismos_consulta'"
    ), {"sql": _SQL_ANTERIOR})

    op.drop_constraint('ck_org_exp_resultado', 'organismos_expediente', schema='public', type_='check')
    op.alter_column(
        'organismos_expediente', 'resultado',
        new_column_name='estado', nullable=False, server_default='pendiente',
        schema='public',
    )
    op.create_check_constraint(
        'ck_org_exp_estado', 'organismos_expediente',
        "estado IN ('pendiente','separata_enviada','en_tramitacion',"
        "'cerrado_favorable','cerrado_con_condicionados','audiencia_previa','exonerado')",
        schema='public',
    )

    op.drop_constraint('uq_org_exp_fase_organismo', 'organismos_expediente',
                       schema='public', type_='unique')
    op.create_unique_constraint(
        'uq_org_exp_expediente_organismo', 'organismos_expediente',
        ['expediente_id', 'organismo_id'], schema='public',
    )

    op.drop_index('idx_org_exp_fase', table_name='organismos_expediente', schema='public')
    op.drop_constraint('fk_org_exp_fase', 'organismos_expediente', schema='public', type_='foreignkey')
    op.drop_column('organismos_expediente', 'fase_id', schema='public')
