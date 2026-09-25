from datetime import datetime

from sqlalchemy.dialects.postgresql import JSONB

from app import db


class Certificado(db.Model):
    """
    Certificado interno generado por el motor, vinculado al pool de documentos.

    Un registro por Documento de tipo CERT_*. El tipo concreto está en `tipo`
    (#932), copia de documento.tipo_doc.codigo que se fija al crear el
    certificado. El campo datos almacena el contenido tipo-específico en JSONB;
    su estructura varía por tipo:

        CERT_PLAZO_CUMPLIDO — tarea_id, fecha_vencimiento, documento_inicio_id,
            tipo_tramite, normativa, plazo_valor, plazo_unidad, fecha_inicio_computo
        CERT_FIN_INSTRUCCION — fase_id, tipo_expediente, fases_completadas,
            fundamento_juridico  (producido en #373)
        CERT_FIN_IP_CONSULTAS — fases_habilitantes, fecha_fin_ultima_fase
            (producido en issue futuro)
        CERT_CUMPLIMIENTO_FASE — documento_id y nada más (#947, ADR-049 §F): el
            documento que acredita la notificación al titular de lo que resuelve
            la fase. Sin su fecha (una sola fuente) y sin tipo, tarea ni actos,
            que se derivan del documento y de la fase y no pueden cambiar
            mientras el sello exista. Un id dentro de JSONB no es FK: lo protege
            services/sellos.py.
        CERT_CIERRE_FASE — la foto fija del informe de cierre de la fase
            finalizadora (#956, ADR-049 §F, D4): {version, expediente, solicitud,
            fase, actos, resultado, cierra_solicitud, bloques}, donde `bloques` son
            `informe_instruccion.Bloque.a_dict()` ya redactados (relato, salvado).
            Texto, no ids: la vista del emitido lo pinta tal cual y no recalcula,
            porque ADR-036 no protege los datos de los documentos de la fase en el
            pool (#954). Su documento es `fases.documento_resultado_id`.

    URI: bddat://certificados/{id}  →  resolver_url() devuelve dict completo.

    SER CERTIFICADO = TENER FILA AQUÍ, NUNCA LA URL (#947, D2):
        `Documento.url` dice dónde está el papel (hoy bddat://, «no hay papel, se
        pinta»; el día que haya PDF, su ruta). Esta fila dice qué sella, y no
        cambia al pasar a PDF. Todo código que necesite saber si un documento es
        un certificado pregunta por `doc.certificado`, no por el esquema de la
        url; así el paso a PDF solo cambia dónde está el papel.

    SCOPING POR SOLICITUD/VERSIÓN (ADR-044 R5, #901):
        solicitud_id y reformado_id son NULL salvo en CERT_FIN_IP_CONSULTAS (y
        cualquier tipo futuro que necesite re-emitirse por solicitud y por
        ronda), para poder buscar y no confundir el certificado de una solicitud
        o una ronda con el de otra del mismo expediente. reformado_id NULL =
        versión inicial, mismo criterio que fases.reformado_id (R3).

    SCOPING POR FASE (N3, ADR-049 §F, #932):
        fase_id es el tercer eje de scoping, NULL salvo en los certificados que
        cuelgan de una fase (CERT_CUMPLIMIENTO_FASE, N4; CERT_CIERRE_FASE, N4b). Sin reformado_id: las
        fases finalizadoras no se repiten por ronda (ADR-044 R5). El índice único
        parcial (fase_id, tipo) deja como mucho un certificado de cada tipo por
        fase; por eso `tipo` es columna y no se deduce por join.

        El backref es Fase.certificados_cumplimiento, no Fase.certificados: ese
        nombre ya lo ocupa CertificadoFase (tabla certificados_fase, auditoría
        del motor), que es otra cosa. Carga TODAS las filas de la fase, no solo
        las de cumplimiento: se filtra por `tipo` (sellos.certificado_cumplimiento,
        sellos.certificado_cierre).
    """
    __tablename__ = 'certificados'
    __table_args__ = (
        db.UniqueConstraint('documento_id', name='uq_certificado_documento'),
        db.Index(
            'uq_certificado_ip_consultas_no_reformado', 'solicitud_id',
            unique=True,
            postgresql_where=db.text('solicitud_id IS NOT NULL AND reformado_id IS NULL'),
        ),
        db.Index(
            'uq_certificado_ip_consultas_por_version', 'solicitud_id', 'reformado_id',
            unique=True,
            postgresql_where=db.text('solicitud_id IS NOT NULL AND reformado_id IS NOT NULL'),
        ),
        db.Index(
            'uq_certificado_fase_tipo', 'fase_id', 'tipo',
            unique=True,
            postgresql_where=db.text('fase_id IS NOT NULL'),
        ),
        {'schema': 'public'},
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    documento_id = db.Column(
        db.Integer,
        db.ForeignKey('public.documentos.id', name='fk_certificado_documento'),
        nullable=False,
        unique=True,
        comment='FK documentos. Tipo deducido de tipo_doc.codigo',
    )

    tipo = db.Column(
        db.String(50),
        nullable=False,
        comment='Código del tipo de certificado (tipos_documentos.codigo). '
                'Denormalizado desde documentos.tipo_doc_id para permitir '
                'el índice único (fase_id, tipo) sin join.',
    )

    solicitud_id = db.Column(
        db.Integer,
        db.ForeignKey('public.solicitudes.id', ondelete='RESTRICT'),
        nullable=True,
        comment='FK a SOLICITUDES. NULL salvo en certificados que necesitan scoping por '
                'solicitud (hoy, CERT_FIN_IP_CONSULTAS) — ver docstring de la clase',
    )

    reformado_id = db.Column(
        db.Integer,
        db.ForeignKey('public.reformados_proyecto.id', ondelete='RESTRICT'),
        nullable=True,
        comment='FK a REFORMADOS_PROYECTO. NULL = versión inicial (o certificado sin scoping '
                'por versión) — ver docstring de la clase',
    )

    fase_id = db.Column(
        db.Integer,
        db.ForeignKey('public.fases.id', name='fk_certificado_fase', ondelete='RESTRICT'),
        nullable=True,
        comment='FK a FASES. NULL salvo en certificados anclados a una fase '
                '(hoy, CERT_CUMPLIMIENTO_FASE, N4) — ver docstring de la clase',
    )

    generado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=db.text('now()'),
        comment='Momento de creación del registro',
    )

    datos = db.Column(
        JSONB,
        nullable=False,
        default=dict,
        server_default='{}',
        comment='Contenido tipo-específico del certificado',
    )

    documento = db.relationship(
        'Documento',
        foreign_keys=[documento_id],
        backref=db.backref('certificado', uselist=False),
    )
    solicitud = db.relationship(
        'Solicitud',
        foreign_keys=[solicitud_id],
        backref=db.backref('certificados', passive_deletes=True),
    )
    reformado = db.relationship(
        'ReformadoProyecto',
        foreign_keys=[reformado_id],
        backref=db.backref('certificados', passive_deletes=True),
    )
    fase = db.relationship(
        'Fase',
        foreign_keys=[fase_id],
        backref=db.backref('certificados_cumplimiento', passive_deletes=True),
    )

    def __repr__(self):
        return f'<Certificado id={self.id} tipo={self.tipo} doc={self.documento_id}>'
