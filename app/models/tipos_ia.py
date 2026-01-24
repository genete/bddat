from app import db

class TipoIA(db.Model):
    """
    Catálogo de tipos de instrumentos ambientales aplicables.
    
    PROPÓSITO:
        Define los instrumentos ambientales según normativa vigente que determinan
        los trámites ambientales necesarios para cada proyecto de instalación eléctrica.
    
    FILOSOFÍA:
        - Tabla maestra de configuración ambiental
        - Valores definidos por normativa autonómica
        - Actualizada según cambios legislativos
        - Valores definidos en datos_maestros.sql (fuente de verdad)
    
    RELACIONES:
        - proyectos ← PROYECTOS.ia_id (instrumento aplicable al proyecto)
    
    REGLAS DE NEGOCIO:
        El TIPO_IA determina las fases ambientales obligatorias, trámites
        necesarios y documentación requerida según motor de reglas.
    
    DATOS MAESTROS:
        Ver datos_maestros.sql para valores iniciales (5 tipos: AAI, AAU, 
        AAUS, CA, NO_SUJETO).
    
    NOTAS DE VERSIÓN:
        v3.0: Sin cambios estructurales. Tabla maestra estable.
    """
    __tablename__ = 'tipos_ia'
    __table_args__ = {'schema': 'estructura'}
    
    id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True,
        comment='Identificador único autogenerado del tipo de instrumento ambiental'
    )
    
    siglas = db.Column(
        db.String(10), 
        nullable=False, 
        unique=True,
        comment='Código del instrumento ambiental (ver datos_maestros.sql)'
    )
    
    descripcion = db.Column(
        db.String(200), 
        nullable=True,
        comment='Denominación completa del instrumento ambiental'
    )
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<TipoIA {self.siglas}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return f'{self.siglas} - {self.descripcion}' if self.descripcion else self.siglas
