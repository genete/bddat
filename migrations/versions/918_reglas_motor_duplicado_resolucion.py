"""918_reglas_motor_duplicado_resolucion — duplicado quirúrgico de RESOLUCION

Revision ID: 918_reglas_motor_duplicado_resolucion
Revises: 918_regla_exclusion_mutua_resolucion
Create Date: 2026-09-17

Issue #918, ADR-047 §C. Las 5 reglas con sujeto='ANY/ANY/RESOLUCION' (ids
36, 37, 38, 1718, 1787) se duplican íntegras — mismas condiciones, mismo
norma_id/articulo/apartado/prioridad/descripcion, solo cambia el sujeto —
para RESOLUCION_AAP y RESOLUCION_AAC. Sin herencia (mismo criterio que
ADR-046 §E, RESOLUCION_DUP): un tipo de fase finalizadora nuevo no hereda
ciegamente los bloqueos de otro.

10 filas nuevas (5 reglas × 2 sujetos). La regla 1787 (art. 82.1 LPACAP,
certificado de fin de instrucción) también satisface aquí el guardián de
`catalogo_requerido.py` que exige una regla CREAR/82.1 por cada tipo de
fase `es_finalizadora`.
"""
import json

from alembic import op
import sqlalchemy as sa


revision = '918_reglas_motor_duplicado_resolucion'
down_revision = '918_regla_exclusion_mutua_resolucion'
branch_labels = None
depends_on = None

# Calco literal de reglas_motor ids 36, 37, 38, 1718, 1787 (sujeto='ANY/ANY/RESOLUCION')
_REGLAS_BASE = [
    {
        'descripcion': 'No se puede abrir la fase de resolución con un requerimiento de '
                       'subsanación sin respuesta',
        'norma_id': None, 'articulo': None, 'apartado': None, 'prioridad': 10,
        'condiciones': [('tramite_requerimiento_sin_respuesta', 'EQ', True)],
    },
    {
        'descripcion': 'Hay organismos pendientes de respuesta o análisis',
        'norma_id': None, 'articulo': None, 'apartado': None, 'prioridad': 20,
        'condiciones': [('organismos_todos_terminados', 'EQ', False)],
    },
    {
        'descripcion': 'La fase de Información Pública no ha concluido',
        'norma_id': None, 'articulo': None, 'apartado': None, 'prioridad': 21,
        'condiciones': [
            ('fase_ip_finalizada', 'EQ', False),
            ('solicitud_incluye_dup', 'EQ', True),
        ],
    },
    {
        'descripcion': 'La instalación requiere Autorización Ambiental Unificada (AAU) y '
                       'la fase de Información Pública no ha concluido',
        'norma_id': 8, 'articulo': 'DF 4ª', 'apartado': None, 'prioridad': 21,
        'condiciones': [
            ('fase_ip_finalizada', 'EQ', False),
            ('instrumento_ambiental', 'EQ', 'AAU'),
        ],
    },
    {
        'descripcion': 'No se puede abrir la fase de resolución mientras no conste emitido '
                       'el certificado de fin de instrucción de la solicitud. Pida el '
                       'certificado desde la solicitud: si algo falta, el informe dirá qué '
                       'y por qué.',
        'norma_id': 6, 'articulo': '82', 'apartado': '1', 'prioridad': 5,
        'condiciones': [('solicitud_tiene_cert_fin_instruccion', 'EQ', False)],
    },
]

_SUJETOS_DESTINO = ['ANY/ANY/RESOLUCION_AAP', 'ANY/ANY/RESOLUCION_AAC']


def upgrade():
    conn = op.get_bind()

    for sujeto in _SUJETOS_DESTINO:
        for regla in _REGLAS_BASE:
            regla_id = conn.execute(sa.text("""
                INSERT INTO public.reglas_motor
                    (accion, sujeto, efecto, norma_id, articulo, apartado, prioridad,
                     activa, descripcion)
                VALUES ('CREAR', :sujeto, 'BLOQUEAR', :norma_id, :articulo, :apartado,
                        :prioridad, TRUE, :descripcion)
                RETURNING id
            """), {
                'sujeto': sujeto,
                'norma_id': regla['norma_id'],
                'articulo': regla['articulo'],
                'apartado': regla['apartado'],
                'prioridad': regla['prioridad'],
                'descripcion': regla['descripcion'],
            }).scalar()

            for orden, (variable, operador, valor) in enumerate(regla['condiciones'], start=1):
                conn.execute(sa.text("""
                    INSERT INTO public.condiciones_regla
                        (regla_id, variable_id, operador, valor, orden)
                    SELECT :regla_id, cv.id, :operador, CAST(:valor AS json), :orden
                    FROM public.catalogo_variables cv WHERE cv.nombre = :variable
                """), {
                    'regla_id': regla_id, 'operador': operador,
                    'valor': json.dumps(valor), 'orden': orden, 'variable': variable,
                })


def downgrade():
    conn = op.get_bind()

    for sujeto in _SUJETOS_DESTINO:
        for regla in _REGLAS_BASE:
            conn.execute(sa.text("""
                DELETE FROM public.condiciones_regla
                WHERE regla_id IN (
                    SELECT id FROM public.reglas_motor
                    WHERE sujeto = :sujeto AND accion = 'CREAR' AND efecto = 'BLOQUEAR'
                      AND descripcion = :descripcion
                )
            """), {'sujeto': sujeto, 'descripcion': regla['descripcion']})
            conn.execute(sa.text("""
                DELETE FROM public.reglas_motor
                WHERE sujeto = :sujeto AND accion = 'CREAR' AND efecto = 'BLOQUEAR'
                  AND descripcion = :descripcion
            """), {'sujeto': sujeto, 'descripcion': regla['descripcion']})
