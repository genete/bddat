from app import db

class SolicitudTipo(db.Model):
    """
    Tabla puente N:M entre solicitudes y tipos de solicitudes.
    
    PROPÓSITO:
        Permite que una solicitud tenga múltiples tipos simultáneamente
        (ej: AAP+AAC+DUP se almacena como 3 registros en esta tabla).
        Facilita motor de reglas basado en tipos individuales sin duplicación.
    
    FILOSOFÍA:
        - Relación N:M explícita (no db.Table, sino modelo completo con PK)
        - Cada combinación de solicitud+tipo es única (UNIQUE constraint)
        - Motor de reglas procesa cada tipo individualmente
        - Evita duplicación de lógica para combinaciones (AAP+AAC vs AAP+DUP)
    
    EJEMPLO:
        Solicitud que requiere AAP + AAC + DUP:
        - Registro 1: solicitudid=100, tiposolicitudid=1 (AAP)
        - Registro 2: solicitudid=100, tiposolicitudid=2 (AAC)
        - Registro 3: solicitudid=100, tiposolicitudid=3 (DUP)
        
        Motor de reglas aplica lógica sobre cada tipo individual.
    
    CONSTRAINT UNIQUE:
        - (solicitudid, tiposolicitudid) debe ser única
        - Impide asignar el mismo tipo dos veces a una solicitud
        - Protección a nivel de base de datos independiente del interfaz
        - Si se intenta duplicar: ERROR de violación de constraint
    
    RELACIONES:
        - solicitud → SOLICITUDES.id (FK, solicitud que contiene estos tipos)
        - tipo_solicitud → TIPOS_SOLICITUDES.id (FK, tipo individual)
    
    ÍNDICES:
        - idx_solicitudes_tipos_solicitud: Búsqueda rápida de tipos por solicitud
        - idx_solicitudes_tipos_tipo: Búsqueda de solicitudes por tipo
        - UNIQUE (solicitudid, tiposolicitudid): Evita duplicados
    
    REGLAS DE NEGOCIO:
        - No pueden existir duplicados (solicitud + tipo únicos)
        - Una solicitud puede tener N tipos
        - Un tipo puede estar en N solicitudes
        - Al eliminar solicitud, se eliminan sus registros aquí (CASCADE)
    
    CORRECCIÓN v3.1:
        - Movida de schema 'estructura' a schema 'public'
        - Razón: Es tabla OPERACIONAL (datos de instancias), no maestra (catálogos)
        - Issue #21: https://github.com/genete/bddat/issues/21
    """
    __tablename__ = 'solicitudes_tipos'
    __table_args__ = (
        db.UniqueConstraint('solicitudid', 'tiposolicitudid', 
                           name='solicitudes_tipos_solicitudid_tiposolicitudid_key'),
        db.Index('idx_solicitudes_tipos_solicitud', 'solicitudid'),
        db.Index('idx_solicitudes_tipos_tipo', 'tiposolicitudid'),
        {'schema': 'public'}  # CORRECCIÓN: Movida de 'estructura' a 'public' (Issue #21)
    )
    
    id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True,
        comment='Identificador único autogenerado del registro puente'
    )
    
    solicitudid = db.Column(
        db.Integer,
        db.ForeignKey('public.solicitudes.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a SOLICITUDES. Solicitud que contiene este tipo'
    )
    
    tiposolicitudid = db.Column(
        db.Integer,
        db.ForeignKey('estructura.tipos_solicitudes.id'),
        nullable=False,
        comment='FK a TIPOS_SOLICITUDES. Tipo individual asignado a la solicitud'
    )
    
    # Relaciones explícitas
    solicitud = db.relationship('Solicitud', foreign_keys=[solicitudid], backref='solicitud_tipos')
    tipo_solicitud = db.relationship('TipoSolicitud', foreign_keys=[tiposolicitudid])
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<SolicitudTipo solicitud={self.solicitudid} tipo={self.tiposolicitudid}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return f'Solicitud {self.solicitudid} - Tipo {self.tiposolicitudid}'
