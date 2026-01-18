from app import db

class TipoIA(db.Model):
    """
    Tabla maestra de tipos de instrumentos ambientales.
    Valores: AAU, AAUS, CA, No sujeto
    """
    __tablename__ = 'tipos_ia'
    __table_args__ = {'schema': 'estructura'}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    siglas = db.Column(db.String(10), nullable=False, unique=True)
    descripcion = db.Column(db.String(200), nullable=True)
    
    def __repr__(self):
        return f'<TipoIA {self.siglas}>'
