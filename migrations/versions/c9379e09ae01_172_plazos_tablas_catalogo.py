"""172_plazos_tablas_catalogo

Revision ID: c9379e09ae01
Revises: bc4a9f1d8e02
Create Date: 2026-04-28

Cuatro tablas nuevas para el cómputo de plazos administrativos (#172):
  - efectos_plazo       — catálogo de efectos del vencimiento
  - ambitos_inhabilidad — ámbito territorial del calendario de inhábiles
  - dias_inhabiles      — calendario de festivos (PK compuesta fecha+ambito)
  - catalogo_plazos     — plazo legal por tipo de elemento ESFTT

Seeds incluidos:
  - efectos_plazo completo (10 efectos, DISEÑO_FECHAS_PLAZOS.md §2.4)
  - ambitos_inhabilidad (NACIONAL, AUTONOMICO_AND)
  - dias_inhabiles: festivos nacionales + andaluces 2025-2026 (días laborables)
  - catalogo_plazos: fases RESOLUCION_* sin [PENDIENTE] (§5.2 RD 1955/2000)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = 'c9379e09ae01'
down_revision = 'bc4a9f1d8e02'
branch_labels = None
depends_on = None


def upgrade():
    # ------------------------------------------------------------------
    # A. efectos_plazo — catálogo maestro (sin dependencias)
    # ------------------------------------------------------------------
    op.create_table(
        'efectos_plazo',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('codigo', sa.String(60), nullable=False,
                  comment='Código único: NINGUNO | SILENCIO_ESTIMATORIO | ...'),
        sa.Column('nombre', sa.String(200), nullable=False,
                  comment='Descripción legible del efecto'),
        sa.UniqueConstraint('codigo', name='uq_efectos_plazo_codigo'),
        schema='public',
    )

    op.execute(
        "INSERT INTO public.efectos_plazo (codigo, nombre) VALUES "
        "('NINGUNO', 'Sin efecto de plazo'), "
        "('SILENCIO_ESTIMATORIO', 'Silencio administrativo estimatorio'), "
        "('RESPONSABILIDAD_DISCIPLINARIA', 'Responsabilidad disciplinaria del funcionario'), "
        "('SILENCIO_DESESTIMATORIO', 'Silencio administrativo desestimatorio'), "
        "('CADUCIDAD_PROCEDIMIENTO', 'Caducidad del procedimiento por inactividad del interesado'), "
        "('PERDIDA_TRAMITE', 'Pérdida de trámite no indispensable'), "
        "('APERTURA_RECURSO', 'Apertura de la vía impugnatoria'), "
        "('PRESCRIPCION_CONDICIONADO', 'Prescripción del derecho condicionado por resolución propia'), "
        "('CONFORMIDAD_PRESUNTA', 'Conformidad presunta del organismo consultado'), "
        "('SIN_EFECTO_AUTOMATICO', 'Plazo de trámite interno sin consecuencia legal directa')"
    )

    # ------------------------------------------------------------------
    # B. ambitos_inhabilidad — catálogo de ámbitos territoriales
    # ------------------------------------------------------------------
    op.create_table(
        'ambitos_inhabilidad',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('codigo', sa.String(40), nullable=False,
                  comment='Código: NACIONAL | AUTONOMICO_AND | PROVINCIAL_CAD | ...'),
        sa.Column('nombre', sa.String(200), nullable=False,
                  comment='Nombre legible del ámbito territorial'),
        sa.UniqueConstraint('codigo', name='uq_ambitos_inhabilidad_codigo'),
        schema='public',
    )

    op.execute(
        "INSERT INTO public.ambitos_inhabilidad (codigo, nombre) VALUES "
        "('NACIONAL', 'Festivos nacionales (BOE)'), "
        "('AUTONOMICO_AND', 'Festivos autonómicos de Andalucía (BOJA)')"
    )

    # ------------------------------------------------------------------
    # C. dias_inhabiles — calendario de festivos
    # ------------------------------------------------------------------
    op.create_table(
        'dias_inhabiles',
        sa.Column('fecha', sa.Date, nullable=False,
                  comment='Fecha inhábil'),
        sa.Column('descripcion', sa.String(200), nullable=True,
                  comment='Denominación del festivo'),
        sa.Column('ambito_id', sa.Integer, nullable=False,
                  comment='FK al ámbito territorial'),
        sa.ForeignKeyConstraint(
            ['ambito_id'], ['public.ambitos_inhabilidad.id'],
            name='fk_dias_inhabiles_ambito', ondelete='RESTRICT',
        ),
        sa.PrimaryKeyConstraint('fecha', 'ambito_id', name='pk_dias_inhabiles'),
        sa.Index('idx_dias_inhabiles_fecha', 'fecha'),
        schema='public',
    )

    op.execute("""
        INSERT INTO public.dias_inhabiles (fecha, descripcion, ambito_id)
        SELECT d.fecha, d.descripcion, a.id
        FROM (VALUES
            ('2025-01-01'::date, 'Año Nuevo',                   'NACIONAL'),
            ('2025-01-06'::date, 'Epifanía del Señor',          'NACIONAL'),
            ('2025-04-17'::date, 'Jueves Santo',                'NACIONAL'),
            ('2025-04-18'::date, 'Viernes Santo',               'NACIONAL'),
            ('2025-05-01'::date, 'Fiesta del Trabajo',          'NACIONAL'),
            ('2025-08-15'::date, 'Asunción de la Virgen',       'NACIONAL'),
            ('2025-12-08'::date, 'Inmaculada Concepción',       'NACIONAL'),
            ('2025-12-25'::date, 'Natividad del Señor',         'NACIONAL'),
            ('2026-01-01'::date, 'Año Nuevo',                   'NACIONAL'),
            ('2026-01-06'::date, 'Epifanía del Señor',          'NACIONAL'),
            ('2026-04-02'::date, 'Jueves Santo',                'NACIONAL'),
            ('2026-04-03'::date, 'Viernes Santo',               'NACIONAL'),
            ('2026-05-01'::date, 'Fiesta del Trabajo',          'NACIONAL'),
            ('2026-10-12'::date, 'Día de la Hispanidad',        'NACIONAL'),
            ('2026-12-08'::date, 'Inmaculada Concepción',       'NACIONAL'),
            ('2026-12-25'::date, 'Natividad del Señor',         'NACIONAL'),
            ('2025-02-28'::date, 'Día de Andalucía',            'AUTONOMICO_AND'),
            ('2025-04-21'::date, 'Lunes de Pascua',             'AUTONOMICO_AND'),
            ('2026-04-06'::date, 'Lunes de Pascua',             'AUTONOMICO_AND')
        ) AS d(fecha, descripcion, ambito_codigo)
        JOIN public.ambitos_inhabilidad a ON a.codigo = d.ambito_codigo
    """)

    # ------------------------------------------------------------------
    # D. catalogo_plazos — plazos legales por tipo ESFTT
    # ------------------------------------------------------------------
    op.create_table(
        'catalogo_plazos',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('tipo_elemento', sa.String(20), nullable=False,
                  comment='SOLICITUD | FASE | TRAMITE | TAREA'),
        sa.Column('tipo_elemento_id', sa.Integer, nullable=False,
                  comment='ID en tipos_* correspondiente (FK polimórfica sin constraint BD)'),
        sa.Column('campo_fecha', JSONB, nullable=True,
                  comment='Referencia al Documento.fecha_administrativa de inicio'),
        sa.Column('plazo_valor', sa.Integer, nullable=False,
                  comment='Valor numérico del plazo'),
        sa.Column('plazo_unidad', sa.String(20), nullable=False,
                  comment='DIAS_HABILES | DIAS_NATURALES | MESES | ANOS'),
        sa.Column('efecto_vencimiento_id', sa.Integer, nullable=False,
                  comment='FK a efectos_plazo'),
        sa.Column('norma_origen', sa.Text, nullable=True,
                  comment='Cita de la norma que fija el plazo'),
        sa.Column('vigencia_desde', sa.Date, nullable=True,
                  comment='Inicio de vigencia. NULL = desde siempre'),
        sa.Column('vigencia_hasta', sa.Date, nullable=True,
                  comment='Fin de vigencia. NULL = indefinido'),
        sa.Column('activo', sa.Boolean, nullable=False,
                  server_default='TRUE',
                  comment='FALSE para entradas desactivadas sin borrar'),
        sa.ForeignKeyConstraint(
            ['efecto_vencimiento_id'], ['public.efectos_plazo.id'],
            name='fk_catalogo_plazos_efecto', ondelete='RESTRICT',
        ),
        sa.Index('idx_catalogo_plazos_tipo_elem', 'tipo_elemento', 'tipo_elemento_id'),
        schema='public',
    )

    op.execute("""
        INSERT INTO public.catalogo_plazos
            (tipo_elemento, tipo_elemento_id, campo_fecha, plazo_valor,
             plazo_unidad, efecto_vencimiento_id, norma_origen, activo)
        SELECT
            'FASE',
            tf.id,
            '{"fk": "documento_solicitud_id"}'::jsonb,
            plazos.valor,
            'MESES',
            ep.id,
            plazos.norma,
            TRUE
        FROM (VALUES
            ('RESOLUCION_AAP',          3, 'Art. 128 RD 1955/2000'),
            ('RESOLUCION_AAC',          3, 'Art. 131.7 RD 1955/2000'),
            ('RESOLUCION_AE',           1, 'Art. 132 RD 1955/2000 + DA 3a LSE'),
            ('RESOLUCION_AE_PROVISIONAL', 1, 'Art. 132 bis RD 1955/2000 + DA 3a LSE'),
            ('RESOLUCION_AE_DEFINITIVA',  1, 'Art. 132 ter RD 1955/2000 + DA 3a LSE'),
            ('RESOLUCION_TRANSMISION',  3, 'Art. 133 RD 1955/2000'),
            ('RESOLUCION_CIERRE',       3, 'Art. 137 RD 1955/2000')
        ) AS plazos(codigo, valor, norma)
        JOIN public.tipos_fases tf ON tf.codigo = plazos.codigo
        CROSS JOIN public.efectos_plazo ep
        WHERE ep.codigo = 'SILENCIO_DESESTIMATORIO'
    """)


def downgrade():
    op.drop_table('catalogo_plazos', schema='public')
    op.drop_table('dias_inhabiles', schema='public')
    op.drop_table('ambitos_inhabilidad', schema='public')
    op.drop_table('efectos_plazo', schema='public')
