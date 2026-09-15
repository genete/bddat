"""914_catalogo_plazos_dup — plazo de REQUERIMIENTO_RBDA_DEFINITIVA

Revision ID: 914_catalogo_plazos_dup
Revises: 914_reglas_motor_dup
Create Date: 2026-09-14

Issue #914. Solo el plazo de tarea de REQUERIMIENTO_RBDA_DEFINITIVA.ESPERAR_PLAZO
(10 días, procedimiento interno del servicio — sin respuesta en plazo, se
resuelve con la RBDA ya publicada en información pública; efecto
SIN_EFECTO_AUTOMATICO, no TENER_POR_DESISTIDO: no archiva nada, solo deja de
esperar).

NO incluye el plazo de fase de RESOLUCION_DUP (6 meses, art. 148.1 RD
1955/2000): catalogo_plazos.tipo_elemento solo admite SOLICITUD o TAREA, no
existe un tercer valor para plazo de FASE, y en las solicitudes combinadas
(AAC+DUP, AAP+AAC+DUP) hay dos plazos paralelos de la misma solicitud sin
mecanismo hoy para representarlos por separado (Solicitud.documento_cierre_id
es una columna única). Queda para #892 — ver nota en
docs/diseño/DISEÑO_RESOLUCION_DUP.md §1 (sesión 2026-09-14).
"""
from alembic import op
import sqlalchemy as sa


revision = '914_catalogo_plazos_dup'
down_revision = '914_reglas_motor_dup'
branch_labels = None
depends_on = None

_CAMINO = 'ANY/ANY/ANY/REQUERIMIENTO_RBDA_DEFINITIVA/ESPERAR_PLAZO'
_EFECTO_CODIGO = 'SIN_EFECTO_AUTOMATICO'
_NORMA_ORIGEN = ('Plazo genérico LPACAP (10 días) — procedimiento interno del '
                  'servicio, artículo exacto no verificado (#914)')


def upgrade():
    conn = op.get_bind()

    # catalogo_plazos no tiene UNIQUE sobre camino (solo PK id) — idempotencia
    # por comprobación previa, no por ON CONFLICT.
    ya_existe = conn.execute(sa.text(
        "SELECT 1 FROM public.catalogo_plazos WHERE camino = :camino"
    ), {'camino': _CAMINO}).scalar()
    if ya_existe:
        return

    efecto_id = conn.execute(sa.text(
        "SELECT id FROM public.efectos_plazo WHERE codigo = :c"
    ), {'c': _EFECTO_CODIGO}).scalar()
    if efecto_id is None:
        raise ValueError(f"Efecto '{_EFECTO_CODIGO}' no encontrado en efectos_plazo")

    conn.execute(sa.text("""
        INSERT INTO public.catalogo_plazos
            (tipo_elemento, camino, plazo_valor, plazo_unidad, efecto_vencimiento_id,
             norma_origen, orden, suspende_plazo_solicitud, campo_fecha, campo_fecha_cumplimiento)
        VALUES
            ('TAREA', :camino, 10, 'DIAS_HABILES', :efecto_id,
             :norma_origen, 10, FALSE, CAST(:campo_fecha AS jsonb), CAST(:campo_fecha_cumplimiento AS jsonb))
    """), {
        'camino': _CAMINO, 'efecto_id': efecto_id, 'norma_origen': _NORMA_ORIGEN,
        'campo_fecha': '{"rol": "CONSUMIDO"}',
        'campo_fecha_cumplimiento': '{"rol": "PRODUCIDO"}',
    })


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text(
        "DELETE FROM public.catalogo_plazos WHERE camino = :camino"
    ), {'camino': _CAMINO})
