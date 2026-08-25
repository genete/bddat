"""782_fix_norma_origen_placeholders

Revision ID: b29f4e7f3d6b
Revises: 6d7becf5d82b
Create Date: 2026-08-25 08:13:31.902882

Issue #782 — sustituye los 5 PLACEHOLDER de norma_origen en catalogo_plazos
(tipo_elemento='TAREA') por la cita verificada contra el texto vigente del
BOE (LPACAP y RD 1955/2000).

id=5 REQUERIMIENTO_SUBSANACION — Art. 68.1 LPACAP confirmado, sin cambio de
    plazo_valor/unidad.
id=7 SOLICITUD_INFORME — el placeholder citaba art. 80.2 LPACAP (informe
    facultativo genérico) por lectura del propio nombre del trámite. Pero es
    el único trámite con ese código en tipos_tramites (id=4), vive en la
    fase CONSULTA_MINISTERIO ("exclusivo instalaciones de transporte") y no
    tiene relación con el 80.2: es el informe preceptivo de la DGPEM del
    art. 114 RD 1955/2000, plazo de 2 meses (no 10 días), "se prosiguen las
    actuaciones" si no se emite — coherente con el efecto SIN_EFECTO_AUTOMATICO
    que la fila ya tenía. Camino explicitado a la fase real en vez de ANY,
    siguiendo el criterio de #785 (camino real, no comodín que funciona por
    casualidad de nombre único).
id=8,9,10 ANUNCIO_BOE/BOP/PRENSA — el placeholder citaba art. 131 RD 1955/2000
    (condicionados técnicos de la AAC) para BOP y PRENSA, que no es el trámite
    correcto. Verificado contra el BOE:
    - Art. 125.1 RD 1955/2000 ordena publicar el mismo anuncio de información
      pública en BOP/DOCA Y en BOE a la vez → misma cita para BOE y BOP.
    - Art. 144 RD 1955/2000 (información pública de la DUP) es el único que
      exige además publicación "en uno de los diarios de mayor circulación" →
      cita de PRENSA.
    plazo_unidad corregida de DIAS_NATURALES a DIAS_HABILES: ni el art. 125 ni
    el 144 declaran "naturales" expresamente, y LPACAP art. 30.2 unifica a
    hábiles salvo declaración expresa en contrario (ya señalado como criterio
    general en el hallazgo NBLM de LPACAP, contradicciones §4).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b29f4e7f3d6b'
down_revision = '6d7becf5d82b'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        UPDATE public.catalogo_plazos
        SET norma_origen = 'Art. 68.1 LPACAP'
        WHERE id = 5
          AND norma_origen = 'PLACEHOLDER - pendiente cita exacta (Art. 68.1 LPACAP)'
    """)

    op.execute("""
        UPDATE public.catalogo_plazos
        SET camino = 'ANY/ANY/CONSULTA_MINISTERIO/SOLICITUD_INFORME/ESPERAR_PLAZO',
            plazo_valor = 2,
            plazo_unidad = 'MESES',
            norma_origen = 'Art. 114 RD 1955/2000'
        WHERE id = 7
          AND camino = 'ANY/ANY/ANY/SOLICITUD_INFORME/ESPERAR_PLAZO'
          AND norma_origen = 'PLACEHOLDER - pendiente cita exacta (Art. 80.2 LPACAP)'
    """)

    op.execute("""
        UPDATE public.catalogo_plazos
        SET plazo_unidad = 'DIAS_HABILES',
            norma_origen = 'Art. 125.1 RD 1955/2000'
        WHERE id = 8
          AND norma_origen = 'PLACEHOLDER - pendiente cita exacta (Art. 83 LPACAP / Art. 131 RD1955/2000)'
    """)

    op.execute("""
        UPDATE public.catalogo_plazos
        SET plazo_unidad = 'DIAS_HABILES',
            norma_origen = 'Art. 125.1 RD 1955/2000'
        WHERE id = 9
          AND norma_origen = 'PLACEHOLDER - pendiente cita exacta (Art. 131 RD1955/2000 ANUNCIO_BOP)'
    """)

    op.execute("""
        UPDATE public.catalogo_plazos
        SET plazo_unidad = 'DIAS_HABILES',
            norma_origen = 'Art. 144 RD 1955/2000'
        WHERE id = 10
          AND norma_origen = 'PLACEHOLDER - pendiente cita exacta (Art. 131 RD1955/2000 ANUNCIO_PRENSA)'
    """)


def downgrade():
    op.execute("""
        UPDATE public.catalogo_plazos
        SET norma_origen = 'PLACEHOLDER - pendiente cita exacta (Art. 68.1 LPACAP)'
        WHERE id = 5
          AND norma_origen = 'Art. 68.1 LPACAP'
    """)

    op.execute("""
        UPDATE public.catalogo_plazos
        SET camino = 'ANY/ANY/ANY/SOLICITUD_INFORME/ESPERAR_PLAZO',
            plazo_valor = 10,
            plazo_unidad = 'DIAS_HABILES',
            norma_origen = 'PLACEHOLDER - pendiente cita exacta (Art. 80.2 LPACAP)'
        WHERE id = 7
          AND camino = 'ANY/ANY/CONSULTA_MINISTERIO/SOLICITUD_INFORME/ESPERAR_PLAZO'
          AND norma_origen = 'Art. 114 RD 1955/2000'
    """)

    op.execute("""
        UPDATE public.catalogo_plazos
        SET plazo_unidad = 'DIAS_NATURALES',
            norma_origen = 'PLACEHOLDER - pendiente cita exacta (Art. 83 LPACAP / Art. 131 RD1955/2000)'
        WHERE id = 8
          AND norma_origen = 'Art. 125.1 RD 1955/2000'
    """)

    op.execute("""
        UPDATE public.catalogo_plazos
        SET plazo_unidad = 'DIAS_NATURALES',
            norma_origen = 'PLACEHOLDER - pendiente cita exacta (Art. 131 RD1955/2000 ANUNCIO_BOP)'
        WHERE id = 9
          AND norma_origen = 'Art. 125.1 RD 1955/2000'
    """)

    op.execute("""
        UPDATE public.catalogo_plazos
        SET plazo_unidad = 'DIAS_NATURALES',
            norma_origen = 'PLACEHOLDER - pendiente cita exacta (Art. 131 RD1955/2000 ANUNCIO_PRENSA)'
        WHERE id = 10
          AND norma_origen = 'Art. 144 RD 1955/2000'
    """)
