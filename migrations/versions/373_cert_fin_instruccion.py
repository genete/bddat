"""373_cert_fin_instruccion — tabla certificados_fase + CERT_FIN_INSTRUCCION

Revision ID: 373_cert_fin_instruccion
Revises: 370_seed_tramites_tareas
Create Date: 2026-05-13

Issue #373 — Certificado automático de fin de instrucción:
- Añade columna doc_consumido_tipo_id a tramites_tareas
- Crea tabla certificados_fase (snapshot inmutable de auditoría)
- Seed CERT_FIN_INSTRUCCION en tipos_documentos
- Actualiza tramites_tareas para ELABORACION: elimina ANALIZAR, ELABORAR
  consume CERT_FIN_INSTRUCCION
"""
from alembic import op
import sqlalchemy as sa


revision = '373_cert_fin_instruccion'
down_revision = '370_seed_tramites_tareas'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1. Nueva columna en tramites_tareas
    op.add_column(
        'tramites_tareas',
        sa.Column(
            'doc_consumido_tipo_id',
            sa.Integer,
            sa.ForeignKey('public.tipos_documentos.id',
                          name='fk_tram_tareas_doc_consumido_tipo'),
            nullable=True,
        ),
        schema='public',
    )

    # 2. Crear tabla certificados_fase
    op.create_table(
        'certificados_fase',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('expediente_id', sa.Integer,
                  sa.ForeignKey('public.expedientes.id',
                                name='fk_cert_fase_expediente'),
                  nullable=False),
        sa.Column('fase_id', sa.Integer,
                  sa.ForeignKey('public.fases.id',
                                name='fk_cert_fase_fase'),
                  nullable=True),
        sa.Column('tipo_cert', sa.String(50), nullable=False),
        sa.Column('fecha_generacion', sa.DateTime, nullable=False),
        sa.Column('accion', sa.String(10), nullable=False),
        sa.Column('sujeto', sa.String(200), nullable=False),
        sa.Column('reglas_evaluadas', sa.JSON, nullable=False),
        sa.Column('variables_ctx', sa.JSON, nullable=False),
        sa.Column('ruta_pdf', sa.Text, nullable=True),
        schema='public',
    )
    op.create_index('idx_cert_fase_expediente', 'certificados_fase',
                    ['expediente_id'], schema='public')
    op.create_index('idx_cert_fase_tipo', 'certificados_fase',
                    ['tipo_cert'], schema='public')

    # 3. Seed CERT_FIN_INSTRUCCION
    conn.execute(sa.text("""
        INSERT INTO public.tipos_documentos (codigo, nombre, origen)
        VALUES ('CERT_FIN_INSTRUCCION', 'Certificado de fin de instrucción', 'INTERNO')
        ON CONFLICT (codigo) DO NOTHING
    """))

    # 4. Actualizar tramites_tareas para ELABORACION:
    #    - Eliminar la fila de ANALIZAR
    #    - Ajustar el orden de ELABORAR a 1 con doc_consumido_tipo_id = CERT_FIN_INSTRUCCION

    tt_id = conn.execute(sa.text(
        "SELECT id FROM public.tipos_tramites WHERE codigo = 'ELABORACION'"
    )).scalar()
    ta_analizar_id = conn.execute(sa.text(
        "SELECT id FROM public.tipos_tareas WHERE codigo = 'ANALIZAR'"
    )).scalar()
    ta_elaborar_id = conn.execute(sa.text(
        "SELECT id FROM public.tipos_tareas WHERE codigo = 'ELABORAR'"
    )).scalar()
    td_cert_id = conn.execute(sa.text(
        "SELECT id FROM public.tipos_documentos WHERE codigo = 'CERT_FIN_INSTRUCCION'"
    )).scalar()

    if tt_id is None:
        raise ValueError("tipos_tramites.codigo='ELABORACION' no encontrado — migración abortada")
    if ta_analizar_id is None:
        raise ValueError("tipos_tareas.codigo='ANALIZAR' no encontrado — migración abortada")
    if ta_elaborar_id is None:
        raise ValueError("tipos_tareas.codigo='ELABORAR' no encontrado — migración abortada")
    if td_cert_id is None:
        raise ValueError("tipos_documentos.codigo='CERT_FIN_INSTRUCCION' no encontrado — migración abortada")

    # Eliminar fila ANALIZAR (orden=1) de ELABORACION
    conn.execute(sa.text("""
        DELETE FROM public.tramites_tareas
        WHERE tipo_tramite_id = :tt_id
          AND tipo_tarea_id   = :ta_id
    """), {'tt_id': tt_id, 'ta_id': ta_analizar_id})

    # Ajustar ELABORAR a orden=1 y añadir doc_consumido_tipo_id
    conn.execute(sa.text("""
        UPDATE public.tramites_tareas
        SET orden = 1,
            doc_consumido_tipo_id = :td_id
        WHERE tipo_tramite_id = :tt_id
          AND tipo_tarea_id   = :ta_id
    """), {'tt_id': tt_id, 'ta_id': ta_elaborar_id, 'td_id': td_cert_id})


def downgrade():
    conn = op.get_bind()

    # Revertir tramites_tareas para ELABORACION
    tt_id = conn.execute(sa.text(
        "SELECT id FROM public.tipos_tramites WHERE codigo = 'ELABORACION'"
    )).scalar()
    ta_analizar_id = conn.execute(sa.text(
        "SELECT id FROM public.tipos_tareas WHERE codigo = 'ANALIZAR'"
    )).scalar()
    ta_elaborar_id = conn.execute(sa.text(
        "SELECT id FROM public.tipos_tareas WHERE codigo = 'ELABORAR'"
    )).scalar()

    if tt_id and ta_analizar_id and ta_elaborar_id:
        # Restaurar ANALIZAR orden=1
        conn.execute(sa.text("""
            INSERT INTO public.tramites_tareas (tipo_tramite_id, orden, tipo_tarea_id)
            VALUES (:tt_id, 1, :ta_id)
            ON CONFLICT DO NOTHING
        """), {'tt_id': tt_id, 'ta_id': ta_analizar_id})

        # Restaurar ELABORAR a orden=2, quitar doc_consumido_tipo_id
        conn.execute(sa.text("""
            UPDATE public.tramites_tareas
            SET orden = 2,
                doc_consumido_tipo_id = NULL
            WHERE tipo_tramite_id = :tt_id
              AND tipo_tarea_id   = :ta_id
        """), {'tt_id': tt_id, 'ta_id': ta_elaborar_id})

    # Eliminar CERT_FIN_INSTRUCCION
    conn.execute(sa.text("""
        DELETE FROM public.tipos_documentos WHERE codigo = 'CERT_FIN_INSTRUCCION'
    """))

    # Eliminar tabla certificados_fase
    op.drop_index('idx_cert_fase_tipo', 'certificados_fase', schema='public')
    op.drop_index('idx_cert_fase_expediente', 'certificados_fase', schema='public')
    op.drop_table('certificados_fase', schema='public')

    # Eliminar columna de tramites_tareas
    op.drop_constraint('fk_tram_tareas_doc_consumido_tipo', 'tramites_tareas',
                       type_='foreignkey', schema='public')
    op.drop_column('tramites_tareas', 'doc_consumido_tipo_id', schema='public')
