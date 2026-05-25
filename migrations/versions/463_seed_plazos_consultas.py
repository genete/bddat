"""463_seed_plazos_consultas

Revision ID: 463_seed_plazos_consultas
Revises: 460_variables_motor_consultas
Create Date: 2026-05-25

Issue #463 — Seed `catalogo_plazos` para los tres tipos de trámite de
la fase CONSULTAS: CONSULTA_SEPARATA (dos entradas con condiciones de
prioridad), CONSULTA_TRASLADO_TITULAR y CONSULTA_TRASLADO_ORGANISMO.

DISEÑO
======

Las 4 entradas utilizan:
  - tipo_elemento = 'TRAMITE'
  - campo_fecha = {"via_tarea_tipo": "NOTIFICAR", "rol": "PRODUCIDO"}
    El plazo arranca cuando la tarea NOTIFICAR produce el oficio.
    Patrón ya manejado por _resolver_campo_fecha en plazos.py.

CONSULTA_SEPARATA tiene dos entradas ordenadas por prioridad (orden):
  1. 15 días — condiciones: es_solicitud_aac_pura EQ true
                             + tiene_solicitud_aap_favorable EQ true
     Fundamento: art. 131.1 párr. 2 RD 1955/2000 (plazo reducido para AAC
     pura cuando ya existe AAP favorable previa).
  2. 30 días — sin condiciones (fallback general)
     Fundamento: arts. 127.2 / 131.1 RD 1955/2000.

CONSULTA_TRASLADO_TITULAR — 15 días, efecto SIN_EFECTO_AUTOMATICO.
  El efecto real depende del resultado del organismo precedente (caso D
  ADR-011); el tramitador lo gestiona manualmente.
  Fundamento: arts. 127.3 / 131.3 RD 1955/2000.

CONSULTA_TRASLADO_ORGANISMO — 15 días, efecto CONFORMIDAD_PRESUNTA.
  Silencio del organismo ante los reparos del titular = conformidad tácita.
  Fundamento: arts. 127.4 / 131.4 RD 1955/2000.

Normas: NORMATIVA_PLAZOS.md §2.2; DIAS sin calificar = hábiles (LPACAP art. 30.2).
"""
import json

from alembic import op
import sqlalchemy as sa


revision = '463_seed_plazos_consultas'
down_revision = '460_variables_motor_consultas'
branch_labels = None
depends_on = None


_CAMPO_FECHA = json.dumps({"via_tarea_tipo": "NOTIFICAR", "rol": "PRODUCIDO"})

# Cada entrada: (tipo_elemento_codigo, plazo_valor, plazo_unidad, efecto_codigo,
#                norma_origen, orden, condiciones)
# condiciones: lista de (nombre_variable, operador, valor) — puede ser []
_PLAZOS_CONSULTAS = [
    (
        'CONSULTA_SEPARATA', 15, 'DIAS_HABILES', 'CONFORMIDAD_PRESUNTA',
        'Art. 131.1 párr. 2 RD 1955/2000', 10,
        [
            ('es_solicitud_aac_pura', 'EQ', True),
            ('tiene_solicitud_aap_favorable', 'EQ', True),
        ],
    ),
    (
        'CONSULTA_SEPARATA', 30, 'DIAS_HABILES', 'CONFORMIDAD_PRESUNTA',
        'Arts. 127.2 / 131.1 RD 1955/2000', 20,
        [],
    ),
    (
        'CONSULTA_TRASLADO_TITULAR', 15, 'DIAS_HABILES', 'SIN_EFECTO_AUTOMATICO',
        'Arts. 127.3 / 131.3 RD 1955/2000', 10,
        [],
    ),
    (
        'CONSULTA_TRASLADO_ORGANISMO', 15, 'DIAS_HABILES', 'CONFORMIDAD_PRESUNTA',
        'Arts. 127.4 / 131.4 RD 1955/2000', 10,
        [],
    ),
]


def upgrade():
    conn = op.get_bind()

    for codigo, valor, unidad, efecto_codigo, norma, orden, condiciones in _PLAZOS_CONSULTAS:
        plazo_id = conn.execute(sa.text("""
            INSERT INTO public.catalogo_plazos
                (tipo_elemento, tipo_elemento_id, tipo_elemento_codigo, campo_fecha,
                 plazo_valor, plazo_unidad,
                 efecto_vencimiento_id, norma_origen, orden, activo)
            SELECT
                'TRAMITE',
                tt.id,
                :codigo,
                CAST(:campo_fecha AS jsonb),
                :valor,
                :unidad,
                ep.id,
                :norma,
                :orden,
                TRUE
            FROM public.tipos_tramites tt
            CROSS JOIN public.efectos_plazo ep
            WHERE tt.codigo = :codigo
              AND ep.codigo = :efecto_codigo
            RETURNING id
        """), {
            'codigo': codigo,
            'campo_fecha': _CAMPO_FECHA,
            'valor': valor,
            'unidad': unidad,
            'efecto_codigo': efecto_codigo,
            'norma': norma,
            'orden': orden,
        }).scalar()

        if plazo_id is None:
            raise RuntimeError(
                f"No se pudo insertar plazo {codigo} orden={orden}; "
                f"verificar existencia de tipos_tramites.{codigo} y "
                f"efectos_plazo.{efecto_codigo}"
            )

        for i, (nombre_var, operador, valor_cond) in enumerate(condiciones, start=1):
            conn.execute(sa.text("""
                INSERT INTO public.condiciones_plazo
                    (catalogo_plazo_id, variable_id, operador, valor, orden)
                SELECT
                    :plazo_id,
                    cv.id,
                    :operador,
                    CAST(:valor AS jsonb),
                    :orden_cond
                FROM public.catalogo_variables cv
                WHERE cv.nombre = :nombre_var
            """), {
                'plazo_id': plazo_id,
                'operador': operador,
                'valor': json.dumps(valor_cond),
                'orden_cond': i,
                'nombre_var': nombre_var,
            })


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM public.condiciones_plazo
        WHERE catalogo_plazo_id IN (
            SELECT id FROM public.catalogo_plazos
            WHERE tipo_elemento = 'TRAMITE'
              AND tipo_elemento_codigo IN (
                  'CONSULTA_SEPARATA',
                  'CONSULTA_TRASLADO_TITULAR',
                  'CONSULTA_TRASLADO_ORGANISMO'
              )
        )
    """))

    conn.execute(sa.text("""
        DELETE FROM public.catalogo_plazos
        WHERE tipo_elemento = 'TRAMITE'
          AND tipo_elemento_codigo IN (
              'CONSULTA_SEPARATA',
              'CONSULTA_TRASLADO_TITULAR',
              'CONSULTA_TRASLADO_ORGANISMO'
          )
    """))
