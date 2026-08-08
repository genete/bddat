"""28_mensajes_internos

Revision ID: 28_mensajes_internos
Revises: 768_grant_fases_tramites
Create Date: 2026-08-08

Issue #28 — Crea mensajes_internos: bandeja de peticiones dirigidas al
Supervisor. Ver ADR-040 §4.

La tabla *es* la bandeja del rol SUPERVISOR/ADMIN: no hay destinatario, se
persiste el remitente (ADR-040 §2). Una petición es UNA fila con tres estados
(ADR-040 §3):

    pendiente  ->  hecho (+ resultado + notas)  ->  acusado por el remitente

Los tres CHECK impiden estados imposibles: un resultado fuera del vocabulario,
un `hecho` sin veredicto ni traza temporal, y un acuse sobre algo aún sin
resolver.

Los dos índices son parciales/compuestos a propósito, uno por cada consulta
real de la interfaz: la bandeja del Supervisor (pendientes por antigüedad) y el
badge del remitente (propias sin acusar).

Sin datos de partida: la tabla se llena con el uso.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '28_mensajes_internos'
down_revision = '768_grant_fases_tramites'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'mensajes_internos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('remitente_usuario_id', sa.Integer(), nullable=False,
                  comment='FK usuarios. Quien pide. NOT NULL: el alta de usuario nuevo no entra por aquí (ADR-040 §9)'),
        sa.Column('tipo', sa.String(40), nullable=False,
                  comment='Tipo de petición. Gobierna la forma de DATOS y su render (registro de app/services/mensajes_internos.py)'),
        sa.Column('datos', postgresql.JSONB(), nullable=False,
                  comment='Payload de la petición, con la forma que declare su TIPO en el registro del servicio'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()'),
                  comment='Momento del envío de la petición'),

        # Resolución por el Supervisor
        sa.Column('hecho', sa.Boolean(), nullable=False, server_default='false',
                  comment='TRUE cuando el Supervisor la ha resuelto. Es la casilla que marca en la interfaz'),
        sa.Column('resultado', sa.String(10), nullable=True,
                  comment='Veredicto: ATENDIDA | DENEGADA. NULL mientras HECHO=False'),
        sa.Column('notas', sa.Text(), nullable=True,
                  comment='Explicación libre del Supervisor al resolver. El veredicto contable va en RESULTADO'),
        sa.Column('hecho_por_id', sa.Integer(), nullable=True,
                  comment='FK usuarios. Quién resolvió (traza: la petición va al rol, la atiende una persona)'),
        sa.Column('hecho_at', sa.DateTime(timezone=True), nullable=True,
                  comment='Cuándo se resolvió'),

        # Acuse del remitente
        sa.Column('acusado_at', sa.DateTime(timezone=True), nullable=True,
                  comment='Cuándo el remitente acusó la respuesta. Explícito, nunca implícito por abrir el listado'),

        sa.PrimaryKeyConstraint('id', name='pk_mensajes_internos'),
        sa.ForeignKeyConstraint(['remitente_usuario_id'], ['public.usuarios.id'],
                                name='fk_mensaje_interno_remitente'),
        sa.ForeignKeyConstraint(['hecho_por_id'], ['public.usuarios.id'],
                                name='fk_mensaje_interno_hecho_por'),
        sa.CheckConstraint("resultado IS NULL OR resultado IN ('ATENDIDA', 'DENEGADA')",
                           name='ck_mi_resultado'),
        sa.CheckConstraint('hecho = FALSE OR (resultado IS NOT NULL AND hecho_at IS NOT NULL)',
                           name='ck_mi_hecho'),
        sa.CheckConstraint('acusado_at IS NULL OR hecho = TRUE',
                           name='ck_mi_acuse'),
        schema='public',
    )

    # Bandeja del Supervisor: pendientes, las más antiguas primero
    op.execute(
        'CREATE INDEX idx_mi_pendientes ON public.mensajes_internos (created_at) '
        'WHERE hecho = FALSE'
    )
    # Badge del remitente: las suyas sin acusar
    op.create_index('idx_mi_remitente', 'mensajes_internos',
                    ['remitente_usuario_id', 'acusado_at'], schema='public')

    op.execute("GRANT SELECT ON public.mensajes_internos TO claude_desktop")


def downgrade():
    op.drop_index('idx_mi_remitente', table_name='mensajes_internos', schema='public')
    op.execute('DROP INDEX IF EXISTS public.idx_mi_pendientes')
    op.drop_table('mensajes_internos', schema='public')
