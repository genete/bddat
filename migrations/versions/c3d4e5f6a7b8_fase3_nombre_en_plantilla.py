"""Fase 3 #167: ADD nombre_en_plantilla (TEXT nullable) en 5 tablas catalogo ESFTT

- ADD nombre_en_plantilla TEXT nullable en tipos_expedientes
- ADD nombre_en_plantilla TEXT nullable en tipos_solicitudes
- ADD nombre_en_plantilla TEXT nullable en tipos_fases
- ADD nombre_en_plantilla TEXT nullable en tipos_tramites
- ADD nombre_en_plantilla TEXT nullable en tipos_tareas
- UPDATE seed con valores legibles para cada tipo existente

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-16

"""
from alembic import op
import sqlalchemy as sa

revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    # --- ADD COLUMN en las 5 tablas ---
    for tabla in ('tipos_expedientes', 'tipos_solicitudes', 'tipos_fases',
                  'tipos_tramites', 'tipos_tareas'):
        op.add_column(tabla,
            sa.Column('nombre_en_plantilla', sa.Text(), nullable=True,
                      comment='Nombre legible usado en nombres de documentos generados'),
            schema='public'
        )

    # --- SEED tipos_expedientes ---
    op.execute("""
        UPDATE public.tipos_expedientes SET nombre_en_plantilla = CASE id
            WHEN 1 THEN 'Transporte'
            WHEN 2 THEN 'Distribución'
            WHEN 3 THEN 'Distribución cedida'
            WHEN 4 THEN 'Renovable'
            WHEN 5 THEN 'Autoconsumo'
            WHEN 6 THEN 'Línea Directa'
            WHEN 7 THEN 'Convencional'
            WHEN 8 THEN 'Otros'
        END
        WHERE id IN (1,2,3,4,5,6,7,8)
    """)

    # --- SEED tipos_solicitudes ---
    op.execute("""
        UPDATE public.tipos_solicitudes SET nombre_en_plantilla = CASE id
            WHEN 1  THEN 'AAP'
            WHEN 2  THEN 'AAC'
            WHEN 3  THEN 'DUP'
            WHEN 4  THEN 'AAE Provisional'
            WHEN 5  THEN 'AAE Definitiva'
            WHEN 6  THEN 'AAT'
            WHEN 7  THEN 'RAIPEE Previa'
            WHEN 8  THEN 'RAIPEE Definitiva'
            WHEN 9  THEN 'RADNE'
            WHEN 10 THEN 'Cierre'
            WHEN 11 THEN 'Desistimiento'
            WHEN 12 THEN 'Renuncia'
            WHEN 13 THEN 'Ampliación de Plazo'
            WHEN 14 THEN 'Interesado'
            WHEN 15 THEN 'Recurso'
            WHEN 16 THEN 'Corrección de Errores'
            WHEN 17 THEN 'Otro'
            WHEN 18 THEN 'AAP+AAC'
            WHEN 19 THEN 'AAP+AAC+DUP+AAE'
            WHEN 20 THEN 'AAP+AAC+RAIPEE+RADNE'
            WHEN 21 THEN 'AAT+Ampliación Plazo'
        END
        WHERE id IN (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21)
    """)

    # --- SEED tipos_fases ---
    op.execute("""
        UPDATE public.tipos_fases SET nombre_en_plantilla = CASE id
            WHEN 1  THEN 'Registro'
            WHEN 2  THEN 'Admisibilidad'
            WHEN 3  THEN 'Análisis Técnico'
            WHEN 4  THEN 'Consulta Ministerio'
            WHEN 5  THEN 'Compatibilidad Ambiental'
            WHEN 6  THEN 'Admisión a Trámite'
            WHEN 7  THEN 'Consultas'
            WHEN 8  THEN 'Información Pública'
            WHEN 9  THEN 'Figura Ambiental Externa'
            WHEN 10 THEN 'AAU/AAUS Integrada'
            WHEN 11 THEN 'Resolución'
        END
        WHERE id IN (1,2,3,4,5,6,7,8,9,10,11)
    """)

    # --- SEED tipos_tramites ---
    op.execute("""
        UPDATE public.tipos_tramites SET nombre_en_plantilla = CASE id
            WHEN 1  THEN 'Recepción Solicitud'
            WHEN 2  THEN 'Comunicación Inicio'
            WHEN 3  THEN 'Comprobación Admisibilidad'
            WHEN 4  THEN 'Requerimiento Subsanación'
            WHEN 5  THEN 'Comprobación Documental'
            WHEN 6  THEN 'Requerimiento Mejora'
            WHEN 7  THEN 'Informe Ministerio'
            WHEN 8  THEN 'Recepción Informe Ministerio'
            WHEN 9  THEN 'Compatibilidad Ambiental'
            WHEN 10 THEN 'Audiencia Incompatibilidad'
            WHEN 11 THEN 'Informe Compatibilidad'
            WHEN 12 THEN 'Análisis Admisión'
            WHEN 13 THEN 'Alegaciones Admisión'
            WHEN 14 THEN 'Separatas'
            WHEN 15 THEN 'Informe Organismo'
            WHEN 16 THEN 'Reparos'
            WHEN 17 THEN 'Anuncio BOE'
            WHEN 18 THEN 'Anuncio BOP'
            WHEN 19 THEN 'Anuncio Prensa'
            WHEN 20 THEN 'Tablón Ayuntamientos'
            WHEN 21 THEN 'Portal Transparencia'
            WHEN 22 THEN 'Alegación'
            WHEN 23 THEN 'Análisis Alegaciones'
            WHEN 24 THEN 'Figura Ambiental'
            WHEN 25 THEN 'Resolución Ambiental'
            WHEN 26 THEN 'Remisión Medio Ambiente'
            WHEN 27 THEN 'Dictamen Ambiental'
            WHEN 28 THEN 'Resolución'
            WHEN 29 THEN 'Notificación Resolución'
            WHEN 30 THEN 'Publicación Resolución'
        END
        WHERE id IN (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30)
    """)

    # --- SEED tipos_tareas ---
    op.execute("""
        UPDATE public.tipos_tareas SET nombre_en_plantilla = CASE id
            WHEN 1 THEN 'Análisis'
            WHEN 2 THEN 'Redacción'
            WHEN 3 THEN 'Firma'
            WHEN 4 THEN 'Notificación'
            WHEN 5 THEN 'Publicación'
            WHEN 6 THEN 'Espera'
            WHEN 7 THEN 'Incorporación'
        END
        WHERE id IN (1,2,3,4,5,6,7)
    """)


def downgrade():
    for tabla in ('tipos_expedientes', 'tipos_solicitudes', 'tipos_fases',
                  'tipos_tramites', 'tipos_tareas'):
        op.drop_column(tabla, 'nombre_en_plantilla', schema='public')
