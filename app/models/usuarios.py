from app import db

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    siglas = db.Column(db.String(50), nullable=False, default='NULO')
    nombre = db.Column(db.String(100), nullable=False, default='Usuario')
    apellido1 = db.Column(db.String(50), nullable=False, default='no asignado')
    apellido2 = db.Column(db.String(50))
    activo = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Usuario {self.siglas} - {self.nombre} {self.apellido1}>'
