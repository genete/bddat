from app import db

class Municipio(db.Model):
    """
    Catálogo oficial de municipios españoles.
    
    PROPÓSITO:
        Tabla maestra con municipios basados en códigos INE oficiales.
        Necesaria para gestionar afecciones territoriales de proyectos,
        determinar competencias administrativas y publicaciones obligatorias.
    
    FILOSOFÍA:
        - Basado en catálogo oficial del INE (Instituto Nacional de Estadística)
        - CODIGO es el código INE de 5 dígitos (inmutable)
        - Actualización según cambios oficiales del INE (fusiones, segregaciones)
        - Tabla maestra de referencia geográfica
    
    CAMPO CODIGO:
        - Código INE oficial de 5 dígitos
        - UNIQUE: Identificador oficial del municipio
        - Usado para integraciones con sistemas oficiales
    
    CAMPO NOMBRE:
        - Denominación oficial del municipio
        - Usado en documentos e interfaz
    
    CAMPO PROVINCIA:
        - Provincia a la que pertenece el municipio
        - Facilita filtros y búsquedas por provincia
    
    RELACIONES:
        - municipios_proyecto ← MUNICIPIOS_PROYECTO.municipio_id (afecciones territoriales)
        - Relación N:M con PROYECTOS mediante tabla puente
    
    REGLAS DE NEGOCIO:
        El municipio determina:
        - Publicaciones obligatorias en tablón de edictos municipal
        - Organismos locales a consultar
        - Competencias administrativas territoriales
    
    DATOS MAESTROS:
        Ver datos_maestros.sql para catálogo de municipios.
    
    NOTAS DE VERSIÓN:
        v3.0: Sin cambios estructurales. Tabla maestra estable.
    """
    __tablename__ = 'municipios'
    __table_args__ = {'schema': 'public'}
    
    
    id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True,
        comment='Identificador único autogenerado del municipio'
    )
    
    codigo = db.Column(
        db.String(10), 
        nullable=False, 
        unique=True,
        comment='Código INE oficial del municipio (5 dígitos)'
    )
    
    nombre = db.Column(
        db.String(200), 
        nullable=False,
        comment='Denominación oficial del municipio'
    )
    
    provincia = db.Column(
        db.String(100), 
        nullable=False,
        comment='Provincia a la que pertenece el municipio'
    )
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<Municipio {self.codigo}: {self.nombre}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return f'{self.nombre} ({self.provincia})'
