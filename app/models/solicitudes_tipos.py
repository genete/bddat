from app import db

class SolicitudTipo(db.Model):
    """
    Tabla puente que relaciona solicitudes con sus tipos individuales.
    Una solicitud puede tener múltiples tipos (AAP+AAC+DUP → 3 registros).
    Permite motor de reglas basado en tipos individuales sin duplicación de lógica.
    """
    __tablename__ = 'solicitudes_tipos'
    __table_args__ = (
        db.UniqueConstraint('solicitudid', 'tiposolicitudid', 
                           name='solicitudes_tipos_solicitudid_tiposolicitudid_key'),
        db.Index('idx_solicitudes_tipos_solicitud', 'solicitudid'),
        db.Index('idx_solicitudes_tipos_tipo', 'tiposolicitudid'),
        {'schema': 'estructura'}
    )
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    solicitudid = db.Column(db.Integer, nullable=False,
                           comment='FK a estructura.solicitudes(id)')
    tiposolicitudid = db.Column(db.Integer, nullable=False,
                               comment='FK a estructura.tipos_solicitudes(id)')
    
    def __repr__(self):
        return f'<SolicitudTipo solicitud={self.solicitudid} tipo={self.tiposolicitudid}>'
