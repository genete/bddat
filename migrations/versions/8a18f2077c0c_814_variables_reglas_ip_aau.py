"""814_variables_reglas_ip_aau

Revision ID: 8a18f2077c0c
Revises: 396_regla_segunda_ronda_consultas
Create Date: 2026-08-28 08:41:19.978759

Issue #814 — completa el cuadro de exención de Información Pública (IP) que
DL 26/2021 DF 4ª condiciona a "sin DUP Y sin AAU". La regla id=38 (BLOQUEAR
RESOLUCION si fase IP no finalizada) solo cubría la mitad de esa condición
(tipo_solicitud IN [...DUP]). Esta migración:

1. Registra en catalogo_variables 3 variables ya escritas en código pero sin
   fila (app/services/variables/dato.py): sin_linea_aerea,
   max_tension_nominal_kv, solo_suelo_urbano_urbanizable — Decreto 9/2011
   DA 1ª. Y una nueva: instrumento_ambiental (texto: AAI/AAU/AAUS/CA/EXENTO,
   lee Proyecto.ia.siglas — app/services/variables/calculado.py), mismo
   patrón que la variable ya existente 'tipo_solicitud'.

2. Reemplaza la condición `tipo_solicitud IN ['AAP+DUP','AAP+AAC+DUP']` de la
   regla id=38 por `solicitud_incluye_dup EQ true` (variable ya existente y
   activa, calculado.py:155) — cubre CUALQUIER combinación con DUP, no solo
   las 2 listadas a mano (p. ej. 'AAC+DUP', antes no cubierta: efecto
   colateral deseado, no un cambio de alcance no relacionado).

3. Regla nueva hermana de la #38 (mismo sujeto/acción/efecto, condición
   distinta — patrón OR-por-reglas-separadas, ver CondicionRegla docstring):
   BLOQUEAR RESOLUCION si fase IP no finalizada Y instrumento_ambiental=AAU.
   motor_reglas.evaluar() recorre TODAS las reglas que casan (accion,sujeto)
   y bloquea si CUALQUIERA dispara sin excepción — no hace falta fusionar
   ambas condiciones en una sola regla.

Fuera de alcance (ver comentario #814 en GitHub): requiere_aaus y su regla
hermana, hito_aau_obtenida como bloqueo de la propia AAP/AAU.
"""
import json

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a18f2077c0c'
down_revision = '396_regla_segunda_ronda_consultas'
branch_labels = None
depends_on = None

_VARIABLES = [
    ('sin_linea_aerea',
     'Instalación sin ninguna línea aérea', 'boolean', 'D9_2011'),
    ('max_tension_nominal_kv',
     'Tensión nominal máxima de la instalación (kV)', 'numerico', 'D9_2011'),
    ('solo_suelo_urbano_urbanizable',
     'Recorrido íntegro en suelo urbano o urbanizable', 'boolean', 'D9_2011'),
    ('instrumento_ambiental',
     'Instrumento ambiental aplicable (AAI/AAU/AAUS/CA/EXENTO)', 'texto', None),
]

_CODIGO_TIPO_SOLICITUD_ANTERIOR = ['AAP+DUP', 'AAP+AAC+DUP']


def upgrade():
    conn = op.get_bind()

    for nombre, etiqueta, tipo_dato, codigo_norma in _VARIABLES:
        norma_id = None
        if codigo_norma:
            norma_id = conn.execute(sa.text(
                "SELECT id FROM public.normas WHERE codigo = :c"
            ), {'c': codigo_norma}).scalar()
        conn.execute(sa.text("""
            INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa)
            VALUES (:nombre, :etiqueta, :tipo_dato, :norma_id, TRUE)
            ON CONFLICT (nombre) DO NOTHING
        """), {'nombre': nombre, 'etiqueta': etiqueta, 'tipo_dato': tipo_dato, 'norma_id': norma_id})

    # 2. Regla id=38: tipo_solicitud IN [...] -> solicitud_incluye_dup EQ true
    var_dup_id = conn.execute(sa.text(
        "SELECT id FROM public.catalogo_variables WHERE nombre = 'solicitud_incluye_dup'"
    )).scalar()
    conn.execute(sa.text("""
        UPDATE public.condiciones_regla
        SET variable_id = :var_id, operador = 'EQ', valor = 'true'::jsonb
        WHERE regla_id = 38 AND variable_id = (
            SELECT id FROM public.catalogo_variables WHERE nombre = 'tipo_solicitud'
        )
    """), {'var_id': var_dup_id})

    # 3. Regla nueva hermana — bloquea RESOLUCION si IP no finalizada y requiere AAU
    norma_dl26_id = conn.execute(sa.text(
        "SELECT id FROM public.normas WHERE codigo = 'DL_26_2021'"
    )).scalar()
    nueva_regla_id = conn.execute(sa.text("""
        INSERT INTO public.reglas_motor (accion, sujeto, efecto, norma_id, articulo, prioridad, activa, descripcion)
        VALUES ('CREAR', 'ANY/ANY/RESOLUCION', 'BLOQUEAR', :norma_id, 'DF 4ª', 21, TRUE,
                'La instalación requiere Autorización Ambiental Unificada (AAU) y la fase de Información Pública no ha concluido')
        RETURNING id
    """), {'norma_id': norma_dl26_id}).scalar()

    var_ip_id = conn.execute(sa.text(
        "SELECT id FROM public.catalogo_variables WHERE nombre = 'fase_ip_finalizada'"
    )).scalar()
    var_ia_id = conn.execute(sa.text(
        "SELECT id FROM public.catalogo_variables WHERE nombre = 'instrumento_ambiental'"
    )).scalar()

    conn.execute(sa.text("""
        INSERT INTO public.condiciones_regla (regla_id, variable_id, operador, valor, orden)
        VALUES (:regla_id, :var_id, 'EQ', 'false'::jsonb, 1)
    """), {'regla_id': nueva_regla_id, 'var_id': var_ip_id})
    conn.execute(sa.text("""
        INSERT INTO public.condiciones_regla (regla_id, variable_id, operador, valor, orden)
        VALUES (:regla_id, :var_id, 'EQ', '"AAU"'::jsonb, 2)
    """), {'regla_id': nueva_regla_id, 'var_id': var_ia_id})


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM public.condiciones_regla
        WHERE regla_id = (
            SELECT id FROM public.reglas_motor
            WHERE sujeto = 'ANY/ANY/RESOLUCION' AND accion = 'CREAR'
              AND descripcion LIKE 'La instalación requiere Autorización Ambiental Unificada%'
        )
    """))
    conn.execute(sa.text("""
        DELETE FROM public.reglas_motor
        WHERE sujeto = 'ANY/ANY/RESOLUCION' AND accion = 'CREAR'
          AND descripcion LIKE 'La instalación requiere Autorización Ambiental Unificada%'
    """))

    var_tipo_sol_id = conn.execute(sa.text(
        "SELECT id FROM public.catalogo_variables WHERE nombre = 'tipo_solicitud'"
    )).scalar()
    conn.execute(sa.text("""
        UPDATE public.condiciones_regla
        SET variable_id = :var_id, operador = 'IN', valor = CAST(:valor AS jsonb)
        WHERE regla_id = 38 AND variable_id = (
            SELECT id FROM public.catalogo_variables WHERE nombre = 'solicitud_incluye_dup'
        )
    """), {'var_id': var_tipo_sol_id, 'valor': json.dumps(_CODIGO_TIPO_SOLICITUD_ANTERIOR)})

    for nombre, _etiqueta, _tipo_dato, _codigo_norma in _VARIABLES:
        conn.execute(sa.text("""
            DELETE FROM public.catalogo_variables WHERE nombre = :nombre
        """), {'nombre': nombre})
