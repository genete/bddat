# En desarrollo
from app import db

class Expediente(db.Model):
    __tablename__ = 'expedientes'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    numero_at = db.Column(db.Integer, nullable=False, unique=True)
    responsable_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    tipo_expediente_id = db.Column(db.Integer, db.ForeignKey('tipos_expedientes.id'))
    heredado = db.Column(db.Boolean)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyectos.id'), nullable=False, unique=True)
    
    def __repr__(self):
        return f'<Expediente {self.numero_at}>'