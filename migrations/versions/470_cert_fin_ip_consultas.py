"""470_cert_fin_ip_consultas

Revision ID: 470_cert_fin_ip_consultas
Revises: 460_variables_motor_consultas
Create Date: 2026-05-26

Issue #470 — Reglas BLOQUEAR para la emisión de CERT_FIN_IP_CONSULTAS:

  Regla 1: CREAR ANY/ANY/RESOLUCION bloqueado si organismos_todos_terminados = false
           (todos los organismos consultados deben estar en estado terminal)

  Regla 2: CREAR ANY/ANY/RESOLUCION bloqueado si fase_ip_finalizada = false
           Y tipo_solicitud IN ['AAP+DUP', 'AAP+AAC+DUP']
           (IP obligatoria cuando la solicitud incluye DUP)
"""
from alembic import op
import sqlalchemy as sa

revision = '470_cert_fin_ip_consultas'
down_revision = ('460_variables_motor_consultas', '488_seed_tramites_tareas_registro_interesados')
branch_labels = None
depends_on = None

_SUJETO = 'ANY/ANY/RESOLUCION'


def upgrade():
    conn = op.get_bind()

    # --- Seed: fase_ip_finalizada en catalogo_variables (si no existe) ---
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa)
        VALUES (
            'fase_ip_finalizada',
            'La solicitud en contexto tiene una fase de Información Pública finalizada',
            'boolean', NULL, TRUE
        )
        ON CONFLICT (nombre) DO NOTHING
    """))

    # --- Regla 1: organismos_todos_terminados = false ---
    r1 = conn.execute(sa.text("""
        INSERT INTO public.reglas_motor
            (accion, sujeto, efecto, prioridad, activa, descripcion)
        VALUES (
            'CREAR', :sujeto, 'BLOQUEAR', 20, TRUE,
            'Hay organismos pendientes de respuesta o análisis'
        )
        RETURNING id
    """), {'sujeto': _SUJETO}).scalar()

    conn.execute(sa.text("""
        INSERT INTO public.condiciones_regla
            (regla_id, variable_id, operador, valor, orden)
        SELECT :regla_id, cv.id, 'EQ', 'false'::json, 1
        FROM public.catalogo_variables cv
        WHERE cv.nombre = 'organismos_todos_terminados'
    """), {'regla_id': r1})

    # --- Regla 2: fase_ip_finalizada = false cuando solicitud contiene DUP ---
    r2 = conn.execute(sa.text("""
        INSERT INTO public.reglas_motor
            (accion, sujeto, efecto, prioridad, activa, descripcion)
        VALUES (
            'CREAR', :sujeto, 'BLOQUEAR', 21, TRUE,
            'La fase de Información Pública no ha concluido'
        )
        RETURNING id
    """), {'sujeto': _SUJETO}).scalar()

    conn.execute(sa.text("""
        INSERT INTO public.condiciones_regla
            (regla_id, variable_id, operador, valor, orden)
        SELECT :regla_id, cv.id, 'EQ', 'false'::json, 1
        FROM public.catalogo_variables cv
        WHERE cv.nombre = 'fase_ip_finalizada'
    """), {'regla_id': r2})

    conn.execute(sa.text("""
        INSERT INTO public.condiciones_regla
            (regla_id, variable_id, operador, valor, orden)
        SELECT :regla_id, cv.id, 'IN',
               '["AAP+DUP","AAP+AAC+DUP"]'::json, 2
        FROM public.catalogo_variables cv
        WHERE cv.nombre = 'tipo_solicitud'
    """), {'regla_id': r2})


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM public.condiciones_regla
        WHERE regla_id IN (
            SELECT id FROM public.reglas_motor
            WHERE sujeto = :sujeto
              AND efecto = 'BLOQUEAR'
              AND descripcion IN (
                'Hay organismos pendientes de respuesta o análisis',
                'La fase de Información Pública no ha concluido'
              )
        )
    """), {'sujeto': _SUJETO})

    conn.execute(sa.text("""
        DELETE FROM public.catalogo_variables
        WHERE nombre = 'fase_ip_finalizada'
    """))

    conn.execute(sa.text("""
        DELETE FROM public.reglas_motor
        WHERE sujeto = :sujeto
          AND efecto = 'BLOQUEAR'
          AND descripcion IN (
            'Hay organismos pendientes de respuesta o análisis',
            'La fase de Información Pública no ha concluido'
          )
    """), {'sujeto': _SUJETO})
