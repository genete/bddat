"""968_fuentes_destinatarios — a quién se notifica en cada trámite

Revision ID: 968_fuentes_destinatarios
Revises: 966_portal_un_elaborar
Create Date: 2026-09-27

Issue #968 (N5a-2), ADR-051 §B, §C y §L.

- `notificacion_fuentes` (catálogo): qué fuentes notifica cada (tipo de fase,
  tipo de trámite), con la norma que lo exige. Sustituye a la lista provisional
  `notificaciones.FUENTES_POR_TRAMITE` de #967. Sembrada por código, nunca por
  id (REGLAS_DESARROLLO, #849), con el contenido de ADR-051 §C; los dos trámites
  de notificación de la DUP que retira N5a-3 (#969) llevan las fuentes que
  heredará su `NOTIFICACION`, como la lista provisional.
- `tramites_destinatario` (operacional): el destinatario que el usuario eligió
  para un trámite de un solo destinatario que no sale de otra tabla (§L).
- `notificaciones` gana la copia congelada del representado
  (`dest_en_nombre_de_nombre`, `dest_en_nombre_de_nif`): solo la escribe el
  servicio al copiar el destinatario, como foto fija (§B).

`norma` solo lleva los artículos leídos al diseñar ADR-051 (RD 1955/2000 arts.
128.3, 131.8 y 148.2; Ley 39/2015 arts. 21.4, 40.1 y 68.1). El resto queda
vacío: se completa con otra migración cuando se lean.
"""
from alembic import op


revision = '968_fuentes_destinatarios'
down_revision = '966_portal_un_elaborar'
branch_labels = None
depends_on = None

# Copia de `app.models.notificaciones.FUENTES`: una migración no importa código
# de la aplicación.
_FUENTES = (
    'SOLICITANTE', 'ORGANISMO_DEL_TRAMITE', 'ORGANISMOS_CONSULTADOS',
    'ORGANO_AMBIENTAL', 'PROPIETARIOS_DUP', 'INTERESADOS_RECONOCIDOS',
    'BOLETIN', 'AYUNTAMIENTO', 'MINISTERIO', 'ORGANO_SUPERIOR',
)

_LPAC_21_4 = 'Ley 39/2015, art. 21.4'
_LPAC_40_1 = 'Ley 39/2015, art. 40.1'
_LPAC_68_1 = 'Ley 39/2015, art. 68.1'
_RD_128_3 = 'RD 1955/2000, art. 128.3'
_RD_131_8 = 'RD 1955/2000, art. 131.8'
_RD_148_2 = 'RD 1955/2000, art. 148.2'

# (fase, trámite, ((fuente, norma), ...)) — ADR-051 §C, «Contenido sembrado».
# `orden` sale de la posición en la tupla.
_SEMBRADO = (
    ('ANALISIS_SOLICITUD', 'COMUNICACION_INICIO_ADMISION', (('SOLICITANTE', _LPAC_21_4),)),
    ('ANALISIS_SOLICITUD', 'REQUERIMIENTO_SUBSANACION', (('SOLICITANTE', _LPAC_68_1),)),
    ('DATOS_CATASTRALES', 'REMISION_ACUERDO_DATOS', (('SOLICITANTE', None),)),
    ('DATOS_CATASTRALES', 'REQUERIMIENTO_CATASTRALES', (('SOLICITANTE', None),)),
    ('DATOS_CATASTRALES', 'TOMA_RAZON_RBDA', (('SOLICITANTE', None),)),
    ('CONSULTAS', 'CONSULTA_SEPARATA', (('ORGANISMO_DEL_TRAMITE', None),)),
    ('CONSULTAS', 'CONSULTA_TRASLADO_ORGANISMO', (('ORGANISMO_DEL_TRAMITE', None),)),
    ('CONSULTAS', 'CONSULTA_TRASLADO_TITULAR', (('SOLICITANTE', None),)),
    ('INFORMACION_PUBLICA', 'ANUNCIO_TITULAR', (('SOLICITANTE', None),)),
    ('INFORMACION_PUBLICA', 'RECEPCION_ALEGACION', (('SOLICITANTE', None),)),
    ('INFORMACION_PUBLICA', 'ANUNCIO_BOJA', (('BOLETIN', None),)),
    ('INFORMACION_PUBLICA', 'ANUNCIO_BOP', (('BOLETIN', None),)),
    ('INFORMACION_PUBLICA', 'TABLON_AYUNTAMIENTOS', (('AYUNTAMIENTO', None),)),
    ('CONSULTA_MINISTERIO', 'SOLICITUD_INFORME', (('MINISTERIO', None),)),
    ('COMPATIBILIDAD_AMBIENTAL', 'SOLICITUD_COMPATIBILIDAD', (('ORGANO_AMBIENTAL', None),)),
    ('FIGURA_AMBIENTAL_EXTERNA', 'SOLICITUD_FIGURA', (('ORGANO_AMBIENTAL', None),)),
    ('AAU_AAUS_INTEGRADA', 'REMISION_RESULTADO_IP_CONSULTAS', (('ORGANO_AMBIENTAL', None),)),
    ('AAU_AAUS_INTEGRADA', 'RECEPCION_DICTAMEN', (('ORGANO_AMBIENTAL', None),)),
    ('AAU_AAUS_INTEGRADA', 'RECEPCION_PROPUESTA_INF_VINC', (('ORGANO_AMBIENTAL', None),)),
    ('AAU_AAUS_INTEGRADA', 'DISCREPANCIA_INF_VINC', (('ORGANO_SUPERIOR', None),)),
    ('RESOLUCION', 'NOTIFICACION', (
        ('SOLICITANTE', _LPAC_40_1), ('ORGANISMOS_CONSULTADOS', None),
        ('ORGANO_AMBIENTAL', None), ('INTERESADOS_RECONOCIDOS', _LPAC_40_1))),
    ('RESOLUCION_AAP', 'NOTIFICACION', (
        ('SOLICITANTE', _RD_128_3), ('ORGANISMOS_CONSULTADOS', _RD_128_3),
        ('ORGANO_AMBIENTAL', _RD_128_3), ('INTERESADOS_RECONOCIDOS', _LPAC_40_1))),
    ('RESOLUCION_AAC', 'NOTIFICACION', (
        ('SOLICITANTE', _RD_131_8), ('ORGANISMOS_CONSULTADOS', _RD_131_8),
        ('ORGANO_AMBIENTAL', None), ('INTERESADOS_RECONOCIDOS', _LPAC_40_1))),
    ('RESOLUCION_DUP', 'NOTIFICACION', (
        ('SOLICITANTE', _RD_148_2), ('ORGANISMOS_CONSULTADOS', _RD_148_2),
        ('PROPIETARIOS_DUP', _RD_148_2), ('INTERESADOS_RECONOCIDOS', _RD_148_2))),
    # Se funden en NOTIFICACION en N5a-3 (#969, ADR-051 §G).
    ('RESOLUCION_DUP', 'NOTIFICACION_ORGANISMOS', (('ORGANISMOS_CONSULTADOS', _RD_148_2),)),
    ('RESOLUCION_DUP', 'NOTIFICACION_INTERESADOS', (
        ('PROPIETARIOS_DUP', _RD_148_2), ('INTERESADOS_RECONOCIDOS', _RD_148_2))),
    ('RESOLUCION', 'PUBLICACION', (('BOLETIN', None),)),
    ('RESOLUCION_AAP', 'PUBLICACION', (('BOLETIN', None),)),
    ('RESOLUCION_DUP', 'PUBLICACION_BOE', (('BOLETIN', _RD_148_2),)),
    ('RESOLUCION_DUP', 'PUBLICACION_BOJA', (('BOLETIN', _RD_148_2),)),
    ('RESOLUCION_DUP', 'PUBLICACION_BOP', (('BOLETIN', _RD_148_2),)),
    ('RESOLUCION_DUP', 'REQUERIMIENTO_RBDA_DEFINITIVA', (('SOLICITANTE', None),)),
    ('RECONOCIMIENTO_INTERESADO', 'NOTIFICACION', (('SOLICITANTE', _LPAC_40_1),)),
)


def _literal(valor):
    if valor is None:
        return 'NULL'
    return "'" + valor.replace("'", "''") + "'"


def upgrade():
    lista = ', '.join(f"'{f}'" for f in _FUENTES)

    op.execute(f"""
        CREATE TABLE public.notificacion_fuentes (
            id SERIAL PRIMARY KEY,
            tipo_fase_id INTEGER NOT NULL REFERENCES public.tipos_fases(id),
            tipo_tramite_id INTEGER NOT NULL REFERENCES public.tipos_tramites(id),
            fuente VARCHAR(30) NOT NULL,
            norma TEXT,
            orden SMALLINT NOT NULL,
            CONSTRAINT uq_notificacion_fuentes UNIQUE (tipo_fase_id, tipo_tramite_id, fuente),
            CONSTRAINT ck_notificacion_fuentes_fuente CHECK (fuente IN ({lista}))
        )
    """)
    op.execute("""
        COMMENT ON TABLE public.notificacion_fuentes IS
        'Qué fuentes (roles) notifica cada (tipo de fase, tipo de trámite), con la norma que lo exige (ADR-051 §C). Solo roles, nunca entidades'
    """)
    op.execute("""
        COMMENT ON COLUMN public.notificacion_fuentes.fuente IS
        'Rol a notificar: lista cerrada en código (app.models.notificaciones.FUENTES), cada una con su consulta y su dirección'
    """)
    op.execute("""
        COMMENT ON COLUMN public.notificacion_fuentes.norma IS
        'Artículo que exige notificar a esa fuente. NULL = pendiente de citar'
    """)
    op.execute("GRANT SELECT ON public.notificacion_fuentes TO claude_desktop")

    filas = []
    for fase, tramite, fuentes in _SEMBRADO:
        for orden, (fuente, norma) in enumerate(fuentes, start=1):
            filas.append(f"('{fase}', '{tramite}', '{fuente}', {_literal(norma)}, {orden})")
    op.execute(f"""
        INSERT INTO public.notificacion_fuentes
            (tipo_fase_id, tipo_tramite_id, fuente, norma, orden)
        SELECT tf.id, tt.id, v.fuente, v.norma, v.orden
        FROM (VALUES {', '.join(filas)}) AS v(fase, tramite, fuente, norma, orden)
        JOIN public.tipos_fases tf ON tf.codigo = v.fase
        JOIN public.tipos_tramites tt ON tt.codigo = v.tramite
    """)
    # Un código que no exista dejaría la fila fuera sin error (#849): se cuenta.
    esperadas = len(filas)
    op.execute(f"""
        DO $$
        BEGIN
            IF (SELECT COUNT(*) FROM public.notificacion_fuentes) <> {esperadas} THEN
                RAISE EXCEPTION 'notificacion_fuentes: se esperaban {esperadas} filas';
            END IF;
        END $$
    """)

    op.execute("""
        CREATE TABLE public.tramites_destinatario (
            id SERIAL PRIMARY KEY,
            tramite_id INTEGER NOT NULL UNIQUE
                REFERENCES public.tramites(id) ON DELETE CASCADE,
            entidad_id INTEGER NOT NULL REFERENCES public.entidades(id),
            representante_entidad_id INTEGER REFERENCES public.entidades(id),
            CONSTRAINT ck_tramites_destinatario_representante
                CHECK (representante_entidad_id IS NULL OR representante_entidad_id <> entidad_id)
        )
    """)
    op.execute("""
        COMMENT ON TABLE public.tramites_destinatario IS
        'Destinatario elegido por el usuario para un trámite de un solo destinatario que no sale de otra tabla (ADR-051 §L). Lo pretendido; notificaciones guarda lo realizado'
    """)
    op.execute("""
        COMMENT ON COLUMN public.tramites_destinatario.representante_entidad_id IS
        'Representante de la entidad, si se le notifica a él. NULL = directo'
    """)
    op.execute("GRANT SELECT ON public.tramites_destinatario TO claude_desktop")

    op.execute("""
        ALTER TABLE public.notificaciones
        ADD COLUMN dest_en_nombre_de_nombre TEXT,
        ADD COLUMN dest_en_nombre_de_nif VARCHAR(20)
    """)
    op.execute("""
        COMMENT ON COLUMN public.notificaciones.dest_en_nombre_de_nombre IS
        'Nombre del representado, copiado al fijar el destinatario (foto fija, nunca se edita)'
    """)
    op.execute("""
        COMMENT ON COLUMN public.notificaciones.dest_en_nombre_de_nif IS
        'NIF del representado, copiado al fijar el destinatario (foto fija, nunca se edita)'
    """)
    # Filas ya con representado: se completa la copia desde la entidad.
    op.execute("""
        UPDATE public.notificaciones n
        SET dest_en_nombre_de_nombre = e.nombre_completo,
            dest_en_nombre_de_nif = e.nif
        FROM public.entidades e
        WHERE e.id = n.en_nombre_de_entidad_id
    """)


def downgrade():
    op.execute("""
        ALTER TABLE public.notificaciones
        DROP COLUMN dest_en_nombre_de_nif,
        DROP COLUMN dest_en_nombre_de_nombre
    """)
    op.execute('DROP TABLE public.tramites_destinatario')
    op.execute('DROP TABLE public.notificacion_fuentes')
