from datetime import datetime

from app import db


class CertificadoFase(db.Model):
    """
    Snapshot inmutable de la auditoría del motor al crear una fase.

    Fuente de verdad de qué reglas fueron evaluadas, cuáles dispararon y
    cuáles fueron neutralizadas por excepciones. No editable tras su creación.

    TIPO_CERT:
        Código del tipo de documento generado (ej: 'CERT_FIN_INSTRUCCION').
        Permite múltiples certificados por fase si el diseño lo requiere.

    REGLAS_EVALUADAS y VARIABLES_CTX:
        JSON inmutable — snapshot de AuditoriaResult en el momento de creación.
        No deben modificarse tras el commit inicial.

    RUTA_PDF:
        Se rellena tras la generación del PDF. NULL hasta entonces.

    DOCUMENTO_ID (#827):
        Documento del pool que materializa este certificado. Es la vuelta que le
        faltaba al vínculo —`Documento` apunta al PDF, nadie apuntaba al
        `Documento`— y la que #838 necesitará para deshacer el sello. NULL entre
        el flush del certificado y el del documento (el PDF se llama con
        `cert.id`, así que el certificado va primero) y en lo emitido antes de
        #827. `ruta_pdf` es otra cosa: la ruta física absoluta, mientras que
        `documento.url` es relativa a FILESYSTEM_BASE (ADR-032).
    """
    __tablename__ = 'certificados_fase'
    __table_args__ = (
        db.Index('idx_cert_fase_expediente', 'expediente_id'),
        db.Index('idx_cert_fase_tipo', 'tipo_cert'),
        db.Index('idx_cert_fase_documento', 'documento_id'),
        {'schema': 'public'}
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    expediente_id = db.Column(
        db.Integer,
        db.ForeignKey('public.expedientes.id', name='fk_cert_fase_expediente'),
        nullable=False,
    )

    fase_id = db.Column(
        db.Integer,
        db.ForeignKey('public.fases.id', name='fk_cert_fase_fase'),
        nullable=True,
    )

    tipo_cert = db.Column(
        db.String(50),
        nullable=False,
        comment='Código del tipo de certificado: CERT_FIN_INSTRUCCION, etc.'
    )

    fecha_generacion = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    accion = db.Column(
        db.String(10),
        nullable=False,
        comment='Snapshot de la acción auditada: CREAR, FINALIZAR…'
    )

    sujeto = db.Column(
        db.String(200),
        nullable=False,
        comment='Snapshot del sujeto calificado auditado'
    )

    reglas_evaluadas = db.Column(
        db.JSON,
        nullable=False,
        comment='list[ResultadoRegla] serializado — snapshot inmutable'
    )

    variables_ctx = db.Column(
        db.JSON,
        nullable=False,
        comment='Dict completo de variables en el momento de la auditoría'
    )

    ruta_pdf = db.Column(
        db.Text,
        nullable=True,
        comment='Ruta absoluta del PDF generado; NULL hasta que se genera'
    )

    documento_id = db.Column(
        db.Integer,
        db.ForeignKey('public.documentos.id', name='fk_cert_fase_documento'),
        nullable=True,
        comment='FK a DOCUMENTOS. Documento del pool que materializa este certificado'
    )

    expediente = db.relationship('Expediente', foreign_keys=[expediente_id])
    fase = db.relationship('Fase', foreign_keys=[fase_id], backref='certificados')
    documento = db.relationship('Documento', foreign_keys=[documento_id])

    def __repr__(self):
        return f'<CertificadoFase id={self.id} tipo={self.tipo_cert} fase={self.fase_id}>'
