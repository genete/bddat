from app import db


class TipoDocumentoResultadoValido(db.Model):
    """Whitelist N:M — declara qué resultados son válidos para cada tipo de documento."""
    __tablename__ = 'tipos_documentos_resultados_validos'
    __table_args__ = (
        db.PrimaryKeyConstraint('tipo_documento_id', 'tipo_resultado_documento_id',
                                name='pk_tipos_documentos_resultados_validos'),
        {'schema': 'public'},
    )

    tipo_documento_id          = db.Column(
        db.Integer,
        db.ForeignKey('public.tipos_documentos.id', ondelete='CASCADE'),
        nullable=False,
    )
    tipo_resultado_documento_id = db.Column(
        db.Integer,
        db.ForeignKey('public.tipos_resultado_documentos.id', ondelete='CASCADE'),
        nullable=False,
    )

    tipo_documento  = db.relationship('TipoDocumento',
                                      backref='resultados_validos')
    tipo_resultado  = db.relationship('TipoResultadoDocumento',
                                      backref='documentos_permitidos')
