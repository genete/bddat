from app import db

class TipoExpediente(db.Model):
    __tablename__ = 'tipos_expedientes'
    __table_args__ = {'schema': 'estructura'}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tipo = db.Column(db.String(100))
    descripcion = db.Column(db.String(200))
    
    def __repr__(self):
        return f'<TipoExpediente {self.id}: {self.tipo}>'