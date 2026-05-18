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
    """
    __tablename__ = 'certificados'
    __table_args__ = (
        db.UniqueConstraint('documento_id', name='uq_certificado_documento'),
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

    def __repr__(self):
        return f'<Certificado id={self.id} doc={self.documento_id}>'
