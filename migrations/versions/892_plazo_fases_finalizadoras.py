"""892_plazo_fases_finalizadoras — plazo propio de RESOLUCION_DUP/AAP/AAC

Revision ID: 892_plazo_fases_finalizadoras
Revises: 891_regla_orden_dup_aac
Create Date: 2026-09-17

Issue #892, ADR-048. Dos correcciones distintas sobre catalogo_plazos:

1. Cita normativa inexistente en la fila SOLICITUD/ANY/DUP (id histórico 112,
   localizada aquí por camino, no por id — REGLAS_DESARROLLO.md): el art. 145
   RD 1955/2000 es "Alegaciones", párrafo único, sin apartado 4. El plazo de
   resolución de la DUP está en el art. 148.1 ("en todo caso... seis meses
   desde la fecha en que la solicitud haya tenido entrada"), verificado contra
   el texto consolidado del BOE en la sesión de este issue.

2. Plazo propio para las fases finalizadoras RESOLUCION_DUP, RESOLUCION_AAP y
   RESOLUCION_AAC (ADR-046/047), que hoy no tienen ninguno: el CheckConstraint
   de tipo_elemento solo admitía SOLICITUD y TAREA (#788). ADR-048 reabre esa
   exclusión, acotada a fases finalizadoras — son el acto (la autorización, la
   declaración), no taxonomía ESFTT. Las tres filas nuevas:

     RESOLUCION_DUP  6 meses  Art. 148.1 RD 1955/2000
     RESOLUCION_AAP  3 meses  Art. 128   RD 1955/2000
     RESOLUCION_AAC  3 meses  Art. 131.7 RD 1955/2000

   campo_fecha={'fk': 'documento_solicitud_id'}: la fase no tiene esa FK
   propia, plazos.py._resolver_campo_fecha sube a Fase.solicitud desde ADR-048.
   campo_fecha_cumplimiento queda NULL a propósito (issue de cierre propio por
   fase pendiente de abrir) — el plazo de estas fases solo alcanza EN_PLAZO o
   VENCIDO, nunca CUMPLIDO, mismo patrón que TABLON_AYUNTAMIENTOS.

   No se retira ni modifica ninguna fila SOLICITUD existente (108-112,
   1855-1857): siguen alimentando el plazo global de la solicitud que usa
   COMUNICACION_INICIO_ADMISION — retirarlas rompería ese documento para las
   solicitudes de DUP sola. Las filas nuevas son un mecanismo aditivo.

Fuera de alcance (confirmado en sesión con Carlos): plazo propio para el AAP+AAC
"resuelto partido" fuera de las dos filas de FASE ya cubiertas aquí no aplica —
RESOLUCION_AAP/RESOLUCION_AAC son las mismas fases tanto si la solicitud es
AAP+AAC como AAP+AAC+DUP, el camino no distingue por tipo_solicitud a propósito
(el plazo del art. 128/131.7 no cambia según con qué se combine). Superficie de
UI (mostrar el plazo de fase en el árbol/inspector) y diseño del cierre propio
por fase quedan para issues aparte.
"""
from alembic import op
import sqlalchemy as sa


revision = '892_plazo_fases_finalizadoras'
down_revision = '891_regla_orden_dup_aac'
branch_labels = None
depends_on = None

_CONSTRAINT = 'ck_catalogo_plazos_tipo_elemento'
_CONSTRAINT_ANTES = "tipo_elemento IN ('SOLICITUD', 'TAREA')"
_CONSTRAINT_DESPUES = "tipo_elemento IN ('SOLICITUD', 'FASE', 'TAREA')"

_CAMINO_DUP_SOLA = 'ANY/DUP'
_NORMA_ANTES = 'Art. 145.4 RD 1955/2000'
_NORMA_DESPUES = 'Art. 148.1 RD 1955/2000'
_PLAZO_ANTES = 3
_PLAZO_DESPUES = 6

# (camino, plazo_valor, norma_origen)
_FASES_FINALIZADORAS = [
    ('ANY/ANY/RESOLUCION_DUP', 6, 'Art. 148.1 RD 1955/2000'),
    ('ANY/ANY/RESOLUCION_AAP', 3, 'Art. 128 RD 1955/2000'),
    ('ANY/ANY/RESOLUCION_AAC', 3, 'Art. 131.7 RD 1955/2000'),
]


def upgrade():
    conn = op.get_bind()

    op.drop_constraint(_CONSTRAINT, 'catalogo_plazos', schema='public', type_='check')
    op.create_check_constraint(
        _CONSTRAINT, 'catalogo_plazos', _CONSTRAINT_DESPUES, schema='public',
    )

    actualizadas = conn.execute(sa.text("""
        UPDATE public.catalogo_plazos
        SET norma_origen = :norma, plazo_valor = :valor
        WHERE tipo_elemento = 'SOLICITUD' AND camino = :camino
    """), {'norma': _NORMA_DESPUES, 'valor': _PLAZO_DESPUES, 'camino': _CAMINO_DUP_SOLA})
    if actualizadas.rowcount == 0:
        raise RuntimeError(
            f"No se encontró la fila SOLICITUD/{_CAMINO_DUP_SOLA} a corregir — "
            "verificar que el seed 448 sigue sembrando ese camino"
        )

    efecto_id = conn.execute(sa.text(
        "SELECT id FROM public.efectos_plazo WHERE codigo = 'SILENCIO_DESESTIMATORIO'"
    )).scalar()
    if efecto_id is None:
        raise ValueError("Efecto 'SILENCIO_DESESTIMATORIO' no encontrado en efectos_plazo")

    for camino, valor, norma in _FASES_FINALIZADORAS:
        ya_existe = conn.execute(sa.text(
            "SELECT 1 FROM public.catalogo_plazos WHERE camino = :camino"
        ), {'camino': camino}).scalar()
        if ya_existe:
            continue

        conn.execute(sa.text("""
            INSERT INTO public.catalogo_plazos
                (tipo_elemento, camino, plazo_valor, plazo_unidad, efecto_vencimiento_id,
                 norma_origen, orden, suspende_plazo_solicitud, campo_fecha, campo_fecha_cumplimiento)
            VALUES
                ('FASE', :camino, :valor, 'MESES', :efecto_id,
                 :norma, 40, FALSE, CAST(:campo_fecha AS jsonb), NULL)
        """), {
            'camino': camino, 'valor': valor, 'efecto_id': efecto_id, 'norma': norma,
            'campo_fecha': '{"fk": "documento_solicitud_id"}',
        })


def downgrade():
    conn = op.get_bind()

    for camino, _valor, _norma in _FASES_FINALIZADORAS:
        conn.execute(sa.text(
            "DELETE FROM public.catalogo_plazos WHERE camino = :camino AND tipo_elemento = 'FASE'"
        ), {'camino': camino})

    conn.execute(sa.text("""
        UPDATE public.catalogo_plazos
        SET norma_origen = :norma, plazo_valor = :valor
        WHERE tipo_elemento = 'SOLICITUD' AND camino = :camino
    """), {'norma': _NORMA_ANTES, 'valor': _PLAZO_ANTES, 'camino': _CAMINO_DUP_SOLA})

    op.drop_constraint(_CONSTRAINT, 'catalogo_plazos', schema='public', type_='check')
    op.create_check_constraint(
        _CONSTRAINT, 'catalogo_plazos', _CONSTRAINT_ANTES, schema='public',
    )
