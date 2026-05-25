"""451_seed_normas_ampliacion

Revision ID: 451_seed_normas_ampliacion
Revises: 455_variables_motor_analisis
Create Date: 2026-05-25

Issue #451 — Ampliar catálogo `normas` con las 7 normas citadas en docs de diseño.

Prerequisito de #323 (seed reglas_motor): las reglas necesitarán FK a normas.id.

Normas existentes (seed_normas_base): id=3 RD1955_2000, id=4 D9_2011.
Este seed añade ids 5-11.

Fuentes de títulos:
  - LSE, LPACAP, RD_1183_2020, RD_244_2019, RD_88_2026: BOE estatal
  - DL_2_2018, DL_26_2021: BOJA sedeboja (IDs 26974 y 33520)
"""
from alembic import op


revision = '451_seed_normas_ampliacion'
down_revision = '455_variables_motor_analisis'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        INSERT INTO public.normas (id, codigo, titulo, url_eli) VALUES
        (5,  'LSE',          'Ley 24/2013, de 26 de diciembre, del Sector Eléctrico',                                                                                                              NULL),
        (6,  'LPACAP',       'Ley 39/2015, de 1 de octubre, del Procedimiento Administrativo Común de las Administraciones Públicas',                                                              NULL),
        (7,  'DL_2_2018',    'Decreto-ley 2/2018, de 26 de junio, de simplificación de normas en materia de energía y fomento de las energías renovables en Andalucía',                           NULL),
        (8,  'DL_26_2021',   'Decreto-ley 26/2021, de 14 de diciembre, por el que se adoptan medidas de simplificación administrativa y mejora de la calidad regulatoria para la reactivación económica en Andalucía', NULL),
        (9,  'RD_1183_2020', 'Real Decreto 1183/2020, de 29 de diciembre, de acceso y conexión a las redes de transporte y distribución de energía eléctrica',                                    NULL),
        (10, 'RD_244_2019',  'Real Decreto 244/2019, de 5 de abril, por el que se regulan las condiciones administrativas, técnicas y económicas del autoconsumo de energía eléctrica',           NULL),
        (11, 'RD_88_2026',   'Real Decreto 88/2026, de 11 de febrero, por el que se aprueba el Reglamento general de suministro, comercialización y agregación de energía eléctrica',             NULL)
        ON CONFLICT (codigo) DO NOTHING
    """)


def downgrade():
    op.execute("DELETE FROM public.normas WHERE id IN (5, 6, 7, 8, 9, 10, 11)")
