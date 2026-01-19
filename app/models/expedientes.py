# En desarrollo
from app import db

class Expediente(db.Model):
    __tablename__ = 'expedientes'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    numero_at = db.Column(db.Integer, nullable=False, unique=True)
    responsable_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    tipo_expediente_id = db.Column(db.Integer, db.ForeignKey('estructura.tipos_expedientes.id'))
    heredado = db.Column(db.Boolean)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyectos.id'), nullable=False, unique=True)
    
    # Relaciones SQLAlchemy
    responsable = db.relationship('Usuario', 
                                  foreign_keys=[responsable_id],
                                  backref='expedientes_responsable')
    
    proyecto = db.relationship('Proyecto',
                              foreign_keys=[proyecto_id],
                              backref=db.backref('expediente', uselist=False))
    
    tipo_expediente = db.relationship('TipoExpediente',
                                     foreign_keys=[tipo_expediente_id],
                                     backref='expedientes')
    
    def __repr__(self):
        return f'<Expediente {self.numero_at}>'
