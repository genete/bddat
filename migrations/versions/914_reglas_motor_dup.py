"""914_reglas_motor_dup — duplicado quirúrgico de las 5 reglas de RESOLUCION

Revision ID: 914_reglas_motor_dup
Revises: 914_tramites_tareas_docs
Create Date: 2026-09-14

Issue #914, ADR-046 §E: RESOLUCION_DUP necesita las mismas condiciones de
instrucción completa que RESOLUCION, pero no se hereda — se duplican las
filas de reglas_motor con sujeto 'ANY/ANY/RESOLUCION_DUP' (decisión
explícita: futuros tipos de resolución no comparten necesariamente estos
bloqueos, y una herencia ciega los arrastraría sin control).

Origen exacto (BD real, sesión 2026-09-14) — ids 36, 37, 38, 1718, 1787 de
ANY/ANY/RESOLUCION, mismas condiciones, mismas variables ya existentes en
catalogo_variables (no se crea ninguna variable nueva):
  36   BLOQUEAR  prioridad 10             tramite_requerimiento_sin_respuesta = true
  37   BLOQUEAR  prioridad 20             organismos_todos_terminados = false
  38   BLOQUEAR  prioridad 21             fase_ip_finalizada = false AND solicitud_incluye_dup = true
  1718 BLOQUEAR  prioridad 21  DF 4ª      fase_ip_finalizada = false AND instrumento_ambiental = 'AAU'
  1787 BLOQUEAR  prioridad 5   82.1       solicitud_tiene_cert_fin_instruccion = false

La última (1787) es también la regla CREAR/82.1 que exige el guardián de
catalogo_requerido.py para toda fase con es_finalizadora=True (#827) —
RESOLUCION_DUP la necesita igual que RESOLUCION y RECONOCIMIENTO_INTERESADO.
"""
from alembic import op
import sqlalchemy as sa


revision = '914_reglas_motor_dup'
down_revision = '914_tramites_tareas_docs'
branch_labels = None
depends_on = None

_SUJETO = 'ANY/ANY/RESOLUCION_DUP'

# (prioridad, norma_codigo, articulo, apartado, descripcion, [(variable, operador, valor_jsonb), ...])
_REGLAS = [
    (10, None, None, None,
     'No se puede abrir la fase de resolución de DUP con un requerimiento de '
     'subsanación sin respuesta',
     [('tramite_requerimiento_sin_respuesta', 'EQ', 'true')]),
    (20, None, None, None,
     'Hay organismos pendientes de respuesta o análisis',
     [('organismos_todos_terminados', 'EQ', 'false')]),
    (21, None, None, None,
     'La fase de Información Pública no ha concluido',
     [('fase_ip_finalizada', 'EQ', 'false'),
      ('solicitud_incluye_dup', 'EQ', 'true')]),
    (21, 'DL_26_2021', 'DF 4ª', None,
     'La instalación requiere Autorización Ambiental Unificada (AAU) y la '
     'fase de Información Pública no ha concluido',
     [('fase_ip_finalizada', 'EQ', 'false'),
      ('instrumento_ambiental', 'EQ', '"AAU"')]),
    (5, 'LPACAP', '82', '1',
     'No se puede abrir la fase de resolución de DUP mientras no conste '
     'emitido el certificado de fin de instrucción de la solicitud',
     [('solicitud_tiene_cert_fin_instruccion', 'EQ', 'false')]),
]


def _var_id(conn, nombre):
    id_ = conn.execute(sa.text(
        'SELECT id FROM public.catalogo_variables WHERE nombre = :n'
    ), {'n': nombre}).scalar()
    if id_ is None:
        raise ValueError(f"Variable '{nombre}' no encontrada en catalogo_variables")
    return id_


def _norma_id(conn, codigo):
    if codigo is None:
        return None
    id_ = conn.execute(sa.text(
        'SELECT id FROM public.normas WHERE codigo = :c'
    ), {'c': codigo}).scalar()
    if id_ is None:
        raise ValueError(f"Norma '{codigo}' no encontrada en normas")
    return id_


def upgrade():
    conn = op.get_bind()

    for prioridad, norma_codigo, articulo, apartado, descripcion, condiciones in _REGLAS:
        regla_id = conn.execute(sa.text("""
            INSERT INTO public.reglas_motor
                (accion, sujeto, efecto, norma_id, articulo, apartado, prioridad, activa, descripcion)
            VALUES ('CREAR', :sujeto, 'BLOQUEAR', :norma_id, :articulo, :apartado, :prioridad, TRUE, :descripcion)
            RETURNING id
        """), {'sujeto': _SUJETO, 'norma_id': _norma_id(conn, norma_codigo),
               'articulo': articulo, 'apartado': apartado,
               'prioridad': prioridad, 'descripcion': descripcion}).scalar()

        for orden, (variable, operador, valor) in enumerate(condiciones, start=1):
            conn.execute(sa.text("""
                INSERT INTO public.condiciones_regla (regla_id, variable_id, operador, valor, orden)
                VALUES (:regla_id, :var_id, :operador, CAST(:valor AS jsonb), :orden)
            """), {'regla_id': regla_id, 'var_id': _var_id(conn, variable),
                   'operador': operador, 'valor': valor, 'orden': orden})


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        DELETE FROM public.condiciones_regla
        WHERE regla_id IN (SELECT id FROM public.reglas_motor WHERE sujeto = :sujeto)
    """), {'sujeto': _SUJETO})
    conn.execute(sa.text(
        "DELETE FROM public.reglas_motor WHERE sujeto = :sujeto"
    ), {'sujeto': _SUJETO})
