"""966_portal_un_elaborar — PORTAL_TRANSPARENCIA a un solo ELABORAR

Revision ID: 966_portal_un_elaborar
Revises: 964_anuncios_ip_secuencias
Create Date: 2026-09-27

Issue #966. `PORTAL_TRANSPARENCIA` estaba modelado como si la Administración
notificara algo al portal y esperara un plazo (ELABORAR → NOTIFICAR →
ESPERAR_PLAZO). No es así: el administrativo abre en el portal una entrada que
expone los documentos de la información pública, y cada plazo de IP ya lo lleva
su boletín. BDDAT solo guarda la URL de esa entrada.

Queda un solo ELABORAR, como en `ESTRUCTURA_FTT.json`:
- ENTRADA: lo que se expone. `ANUNCIO_IP` siempre; el resto según el
  expediente (boletines publicados, certificado del tablón, proyecto, RBDA),
  así que opcional. Varias ENTRADA por paso desde #928.
- SALIDA: `JUSTIFICANTE_PORTAL`, la URL de la entrada del portal. Se reutiliza
  el tipo (decisión de Carlos): su nombre ya lo dice, y el prefijo
  `JUSTIFICANTE_` lo mantiene como documento crítico (#738), igual que los
  justificantes de publicación de los boletines.

Mismo orden que 964: primero `tramites_tareas_documentos`
(`fk_ttd_tramite_tarea`), después `tramites_tareas`. Si alguna fila de
`catalogo_plazos` apunta al portal, se aborta: quedaría colgando de tareas que
ya no existen. Todo se localiza por código, nunca por id.
"""
from alembic import op
import sqlalchemy as sa


revision = '966_portal_un_elaborar'
down_revision = '964_anuncios_ip_secuencias'
branch_labels = None
depends_on = None

_TRAMITE = 'PORTAL_TRANSPARENCIA'

# [(orden, tarea, [(rol, tipo_documento, obligatorio), …]), …]
# tipo_documento None = tipo abierto (polimórfico).
_ANTES = [
    (1, 'ELABORAR', [('ENTRADA', 'ANUNCIO_IP', True),
                     ('SALIDA', None, True)]),
    (2, 'NOTIFICAR', [('ENTRADA', None, True),
                      ('SALIDA', 'JUSTIFICANTE_PORTAL', False)]),
    (3, 'ESPERAR_PLAZO', [('ENTRADA', 'JUSTIFICANTE_PORTAL', False),
                          ('SALIDA', 'CERT_PLAZO_CUMPLIDO', False)]),
]

_DESPUES = [
    (1, 'ELABORAR', [('ENTRADA', 'ANUNCIO_IP', True),
                     ('ENTRADA', 'ANUNCIO_PUBLICADO', False),
                     ('ENTRADA', 'JUSTIFICANTE_BOE', False),
                     ('ENTRADA', 'JUSTIFICANTE_PRENSA', False),
                     ('ENTRADA', 'CERT_PLAZO_TABLON', False),
                     ('ENTRADA', 'DOC_PROYECTO', False),
                     ('ENTRADA', 'RBDA', False),
                     ('SALIDA', 'JUSTIFICANTE_PORTAL', True)]),
]


def _tid(conn, tabla, codigo):
    """Id de un registro de catálogo por su código; aborta si no existe."""
    resultado = conn.execute(
        sa.text(f"SELECT id FROM public.{tabla} WHERE codigo = :c"), {'c': codigo}
    ).scalar()
    if resultado is None:
        raise ValueError(f"'{codigo}' no encontrado en {tabla} — migración abortada")
    return resultado


def _reescribir(conn, pasos):
    tt_id = _tid(conn, 'tipos_tramites', _TRAMITE)
    conn.execute(sa.text(
        "DELETE FROM public.tramites_tareas_documentos WHERE tipo_tramite_id = :tt"
    ), {'tt': tt_id})
    conn.execute(sa.text(
        "DELETE FROM public.tramites_tareas WHERE tipo_tramite_id = :tt"
    ), {'tt': tt_id})
    for orden, tarea_codigo, documentos in pasos:
        conn.execute(sa.text("""
            INSERT INTO public.tramites_tareas (tipo_tramite_id, orden, tipo_tarea_id)
            VALUES (:tt, :o, :ta)
        """), {'tt': tt_id, 'o': orden, 'ta': _tid(conn, 'tipos_tareas', tarea_codigo)})
        for rol, doc_codigo, obligatorio in documentos:
            td_id = _tid(conn, 'tipos_documentos', doc_codigo) if doc_codigo else None
            conn.execute(sa.text("""
                INSERT INTO public.tramites_tareas_documentos
                    (tipo_tramite_id, orden_tarea, rol, tipo_documento_id, obligatorio)
                VALUES (:tt, :o, :rol, :td, :oblig)
            """), {'tt': tt_id, 'o': orden, 'rol': rol, 'td': td_id, 'oblig': obligatorio})


def upgrade():
    conn = op.get_bind()
    colgando = conn.execute(sa.text("""
        SELECT camino FROM public.catalogo_plazos
        WHERE split_part(camino, '/', 4) = :tramite
    """), {'tramite': _TRAMITE}).scalars().all()
    if colgando:
        raise RuntimeError(
            f'catalogo_plazos tiene filas de {_TRAMITE} ({", ".join(colgando)}), '
            f'que quedarían sin tarea — migración abortada')
    _reescribir(conn, _DESPUES)


def downgrade():
    _reescribir(op.get_bind(), _ANTES)
