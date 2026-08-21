"""778a_plazos_medida_unica

Revision ID: 778a_medida_unica
Revises: 788b_purga_plazos
Create Date: 2026-08-21

Issue #778 (migración A) — esquema de la medida única (ADR-041).

QUÉ FALTABA
===========

El servicio calculaba plazos y suspensiones por dos caminos que no se hablaban.
El de suspensiones no consultaba `catalogo_plazos` en ningún momento: tenía la
lista de trámites suspensores escrita en el código y, al no preguntar cuánto
dura nada, una suspensión sin respuesta no podía vencer. La tabla necesita dos
datos que hasta ahora vivían fuera de ella (o no existían):

1. `suspende_plazo_solicitud` — si ese plazo suspende el plazo de la solicitud.
   Cambia cuando cambia la ley y es citable a artículo concreto (art. 22.1.a y
   22.1.d), así que es dato normativo y va donde ya viven el valor del plazo y su
   efecto (test de ADR-037). Sustituye a `plazos._TRAMITES_SUSPENSION`.

   El CheckConstraint lo restringe al nivel TAREA: lo que el art. 22 suspende es
   «el plazo máximo legal para resolver un procedimiento y notificar la
   resolución» —el de la solicitud—, de modo que una fila de nivel SOLICITUD
   marcada como suspensora significaría que ese plazo se suspende a sí mismo.

2. `campo_fecha_cumplimiento` — qué documento acredita que la espera se cumplió.
   Mismo vocabulario cerrado que `campo_fecha` (#788 §2.1), que pasa a ser el
   señalador del DISPARO. Es opcional por un caso real: en TABLON_AYUNTAMIENTOS
   el disparo y el único candidato a cierre son el mismo documento (#416), así
   que esa entrada se queda sin señalador y ahí VENCIDO se lee como «la
   exposición se completó».

   Se declara `JSON`, no `JSONB`, pese a que su gemela `campo_fecha` es `JSONB`:
   la columna se lee entera y se compara en Python, nunca por operadores ni
   índices propios de `jsonb`, y el resto del proyecto usa `db.JSON` por
   portabilidad a otros motores. Pasar `campo_fecha` a `JSON` para dejar el par
   coherente es trabajo aparte — toca CRUD y migraciones anteriores.

3. `solicitudes.documento_cierre_id` — pareja de `documento_solicitud_id`: uno
   ancla la fecha de inicio del plazo de la solicitud, el otro la de fin. No vale
   `Fase(RESOLUCION).documento_resultado_id`: es la resolución, y su fecha es la
   de dictar, anterior a la de notificar (art. 21.3.b: el plazo es para «resolver
   Y notificar»). Lo que se ancla ahí es un certificado que constata que respecto
   de TODOS los interesados hubo notificación o intento acreditado (art. 40.4) —
   con varios interesados hay varios intentos, y ninguno significa por sí solo
   «la solicitud está cerrada».

4. `CERT_CIERRE_SOLICITUD` en `tipos_documentos`. Tercero de la familia de los
   `CERT_FIN_*`: certificados de constatación de un hecho agregado, que aparecen
   en `tramites_tareas_documentos` sólo como ENTRADA porque ningún trámite los
   produce. A diferencia de sus dos hermanos (#788 §9), este SÍ es ancla de un
   plazo. Quién lo emite y cuándo queda fuera de #778.

NO SE RENOMBRA `campo_fecha`
============================

Pasa a significar «señalador del disparo», pero conserva el nombre: renombrarlo
arrastraría migraciones, CRUD, JS, seeds y tests sin ganancia funcional.
"""
from alembic import op
import sqlalchemy as sa


revision = '778a_medida_unica'
down_revision = '788b_purga_plazos'
branch_labels = None
depends_on = None


_TIPO_DOC = 'CERT_CIERRE_SOLICITUD'
_TIPO_DOC_NOMBRE = 'Certificado de cierre de la solicitud'
_TIPO_DOC_DESC = (
    'Certificado que constata que, respecto de todos los interesados, hubo '
    'notificación de la resolución o intento de notificación debidamente '
    'acreditado (art. 40.4 LPACAP), con lo que se entiende cumplida la '
    'obligación de resolver y notificar en plazo (art. 21.3.b). Ancla el fin '
    'del cómputo del plazo de la solicitud. Fecha administrativa: la del '
    'último de esos actos, retroactiva respecto de la emisión del certificado.'
)


def upgrade():
    # --- 1. catalogo_plazos: la marca de suspensión y el señalador de cierre ---
    op.add_column(
        'catalogo_plazos',
        sa.Column(
            'suspende_plazo_solicitud', sa.Boolean(), nullable=False,
            server_default=sa.text('FALSE'),
            comment='TRUE si este plazo suspende el plazo de la solicitud '
                    '(art. 22.1 LPACAP). Sustituye a _TRAMITES_SUSPENSION (#778)',
        ),
        schema='public',
    )
    op.add_column(
        'catalogo_plazos',
        sa.Column(
            'campo_fecha_cumplimiento', sa.JSON(), nullable=True,
            comment='Referencia al Documento.fecha_administrativa que acredita el '
                    'cumplimiento: {"fk":"documento_cierre_id"} (SOLICITUD) o '
                    '{"rol":"CONSUMIDO|PRODUCIDO"[,"tipo_documento":"..."]} (TAREA). '
                    'NULL = el plazo nunca alcanza CUMPLIDO (#778)',
        ),
        schema='public',
    )
    op.create_check_constraint(
        'ck_catalogo_plazos_suspende_solo_tarea',
        'catalogo_plazos',
        "NOT suspende_plazo_solicitud OR tipo_elemento = 'TAREA'",
        schema='public',
    )

    # --- 2. solicitudes: el ancla de fin del cómputo -------------------------
    op.add_column(
        'solicitudes',
        sa.Column(
            'documento_cierre_id', sa.Integer(), nullable=True,
            comment='FK a DOCUMENTOS. Certificado de cierre de la solicitud: ancla '
                    'la fecha de fin del plazo para resolver y notificar (#778)',
        ),
        schema='public',
    )
    op.create_foreign_key(
        'fk_solicitudes_documento_cierre',
        'solicitudes', 'documentos',
        ['documento_cierre_id'], ['id'],
        source_schema='public', referent_schema='public',
    )
    op.create_index(
        'idx_solicitudes_doc_cierre', 'solicitudes', ['documento_cierre_id'],
        schema='public',
    )

    # --- 3. Tipo documental del certificado de cierre ------------------------
    op.get_bind().execute(
        sa.text("""
            INSERT INTO public.tipos_documentos (codigo, nombre, descripcion, origen)
            VALUES (:codigo, :nombre, :descripcion, 'INTERNO')
            ON CONFLICT (codigo) DO NOTHING
        """),
        {'codigo': _TIPO_DOC, 'nombre': _TIPO_DOC_NOMBRE, 'descripcion': _TIPO_DOC_DESC},
    )


def downgrade():
    op.get_bind().execute(
        sa.text('DELETE FROM public.tipos_documentos WHERE codigo = :codigo'),
        {'codigo': _TIPO_DOC},
    )

    op.drop_index('idx_solicitudes_doc_cierre', table_name='solicitudes', schema='public')
    op.drop_constraint('fk_solicitudes_documento_cierre', 'solicitudes',
                       type_='foreignkey', schema='public')
    op.drop_column('solicitudes', 'documento_cierre_id', schema='public')

    op.drop_constraint('ck_catalogo_plazos_suspende_solo_tarea', 'catalogo_plazos',
                       type_='check', schema='public')
    op.drop_column('catalogo_plazos', 'campo_fecha_cumplimiento', schema='public')
    op.drop_column('catalogo_plazos', 'suspende_plazo_solicitud', schema='public')
