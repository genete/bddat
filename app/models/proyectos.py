from app import db
from datetime import date

class Proyecto(db.Model):
    """
    Tabla de proyectos técnicos.
    Cada expediente tiene exactamente UN proyecto (relación 1:1).
    Las versiones del proyecto (PRINCIPAL, MODIFICADO, REFUNDIDO) 
    se gestionan en la tabla documentos_proyecto.
    """
    __tablename__ = 'proyectos'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo = db.Column(db.String(500), nullable=False, default='⚠️ Falta el título del proyecto')
    descripcion = db.Column(db.String(10000), nullable=False, default='⚠️ Falta la descripción del proyecto')
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    finalidad = db.Column(db.String(500), nullable=False, default='⚠️ Falta la finalidad del proyecto')
    emplazamiento = db.Column(db.String(200), nullable=False, default='⚠️ Falta el emplazamiento')
    ia_id = db.Column(db.Integer, db.ForeignKey('estructura.tipos_ia.id'), nullable=True)
    
    # Relación con TipoIA
    ia = db.relationship('TipoIA', foreign_keys=[ia_id], backref='proyectos')
    
    def __repr__(self):
        return f'<Proyecto {self.id}: {self.titulo}>'
