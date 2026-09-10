from datetime import datetime

from sqlalchemy.dialects.postgresql import JSONB

from app import db


class Certificado(db.Model):
    """
    Certificado interno generado por el motor, vinculado al pool de documentos.

    Un registro por Documento de tipo CERT_*. El tipo concreto se deduce de
    documento.tipo_documento.codigo. El campo datos almacena el contenido
    tipo-específico en JSONB; su estructura varía por tipo:

        CERT_PLAZO_CUMPLIDO — tarea_id, fecha_vencimiento, documento_inicio_id,
            tipo_tramite, normativa, plazo_valor, plazo_unidad, fecha_inicio_computo
        CERT_FIN_INSTRUCCION — fase_id, tipo_expediente, fases_completadas,
            fundamento_juridico  (producido en #373)
        CERT_FIN_IP_CONSULTAS — fases_habilitantes, fecha_fin_ultima_fase
            (producido en issue futuro)

    URI: bddat://certificados/{id}  →  resolver_url() devuelve dict completo.

    SCOPING POR SOLICITUD/VERSIÓN (ADR-044 R5, #901):
        solicitud_id y reformado_id son NULL para casi todos los certificados —
        solo los poblados CERT_FIN_IP_CONSULTAS (y cualquier tipo futuro que
        necesite re-emitirse por solicitud y por ronda) los usan, para poder
        buscar y no confundir el certificado de una solicitud o una ronda con
        el de otra del mismo expediente. reformado_id NULL = versión inicial,
        mismo criterio que fases.reformado_id (R3).
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
        {'schema': 'public'},
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    documento_id = db.Column(
        db.Integer,
        db.ForeignKey('public.documentos.id', name='fk_certificado_documento'),
        nullable=False,
        unique=True,
        comment='FK documentos. Tipo deducido de tipo_documento.codigo',
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

    def __repr__(self):
        return f'<Certificado id={self.id} doc={self.documento_id}>'
