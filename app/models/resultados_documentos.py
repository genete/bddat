from app import db


class ResultadoDocumento(db.Model):
    """Resultado registrado para un documento concreto.

    Solo existe fila cuando se ha registrado un resultado explícito.
    Sin fila → el resultado se considera INDIFERENTE.
    La PK es documento_id (UNIQUE implícito: un documento = un resultado).
    """
    __tablename__ = 'resultados_documentos'
    __table_args__ = (
        db.PrimaryKeyConstraint('documento_id', name='pk_resultados_documentos'),
        {'schema': 'public'},
    )

    documento_id               = db.Column(
        db.Integer,
        db.ForeignKey('public.documentos.id', ondelete='CASCADE'),
        nullable=False,
    )
    tipo_resultado_documento_id = db.Column(
        db.Integer,
        db.ForeignKey('public.tipos_resultado_documentos.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )

    documento    = db.relationship('Documento', backref=db.backref('resultado_doc', uselist=False))
    tipo_resultado = db.relationship('TipoResultadoDocumento', backref='resultados')
