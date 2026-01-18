from app import db

class TipoExpediente(db.Model):
    __tablename__ = 'tipos_expedientes'
    __table_args__ = {'schema': 'estructura'}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # Campos adicionales se añadirán posteriormente
    
    def __repr__(self):
        return f'<TipoExpediente {self.id}>'