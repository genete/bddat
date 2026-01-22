from app import db

class TipoSolicitud(db.Model):
    """
    Tabla maestra de tipos de solicitudes individuales.
    Las combinaciones (AAP+AAC, etc.) se gestionan mediante tabla puente solicitudes_tipos.
    Motor de reglas aplica lógica sobre tipos individuales, no sobre combinaciones.
    Basada en nomenclatura legal establecida en normativa sectorial eléctrica (RD 1955/2000).
    """
    __tablename__ = 'tipos_solicitudes'
    __table_args__ = {'schema': 'estructura'}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, 
                   comment='Identificador único del tipo de solicitud')
    siglas = db.Column(db.String(100), nullable=False, unique=True,
                       comment='Siglas normalizadas del acto administrativo (AAP, AAC, DUP, etc.)')
    descripcion = db.Column(db.String(200), nullable=False,
                           comment='Descripción completa del acto administrativo solicitado')
    
    def __repr__(self):
        return f'<TipoSolicitud {self.siglas}>'
