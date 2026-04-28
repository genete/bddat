from app import db


class TipoResultadoDocumento(db.Model):
    __tablename__ = 'tipos_resultado_documentos'
    __table_args__ = (
        db.UniqueConstraint('codigo', name='uq_tipos_resultado_documentos_codigo'),
        {'schema': 'public'},
    )

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo      = db.Column(db.String(50), nullable=False,
                            comment='Código único: INDIFERENTE | CORRECTA | INCORRECTA')
    nombre      = db.Column(db.String(200), nullable=False,
                            comment='Descripción legible del resultado')
    efecto_tarea = db.Column(db.String(20), nullable=False,
                             comment='Efecto que produce en la tarea propietaria del documento')
