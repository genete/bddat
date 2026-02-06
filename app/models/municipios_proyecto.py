from app import db

class MunicipioProyecto(db.Model):
    """
    Relación muchos a muchos entre proyectos y municipios afectados.
    
    PROPÓSITO:
        Gestiona la relación N:M entre proyectos técnicos y municipios afectados.
        Esencial para determinar publicaciones, consultas a ayuntamientos y análisis
        territorial de las instalaciones.
    
    FILOSOFÍA:
        - Relación N:M pura: un proyecto afecta N municipios, un municipio tiene N proyectos
        - UNIQUE constraint: un municipio no se vincula dos veces al mismo proyecto
        - Modelo completo con PK (no db.Table) para control y auditoría futura
    
    CAMPO MUNICIPIO_ID:
        - NOT NULL: Municipio afectado por el proyecto
        - FK a tabla maestra MUNICIPIOS (estructura)
        - Municipio por donde discurre o donde se ubica la instalación
    
    CAMPO PROYECTO_ID:
        - NOT NULL: Proyecto técnico que afecta al municipio
        - FK a PROYECTOS (public)
        - CASCADE en delete: si se elimina proyecto, se eliminan sus municipios
    
    CONSTRAINT UNIQUE:
        - (municipio_id, proyecto_id) debe ser única
        - Impide duplicados a nivel de base de datos
        - Protección independiente del interfaz
    
    USO ADMINISTRATIVO:
        Derivaciones automáticas:
        - Determinar ayuntamientos a consultar
        - Publicaciones en tablones municipales (INFORMACION_PUBLICA)
        - Generación de separatas por término municipal
        - Evaluación ambiental (distinta si afecta >1 municipio)
    
    CONSULTAS TÍPICAS:
        - Municipios de un expediente: EXPEDIENTES → PROYECTOS → MUNICIPIOS
        - Expedientes de un municipio: MUNICIPIOS → PROYECTOS → EXPEDIENTES
    
    RELACIONES:
        - municipio → MUNICIPIOS.id (FK, catálogo maestro)
        - proyecto → PROYECTOS.id (FK CASCADE, proyecto técnico)
    
    ÍNDICES:
        - idx_municipios_proyecto_proyecto: Buscar municipios por proyecto
        - idx_municipios_proyecto_municipio: Buscar proyectos por municipio
        - UNIQUE (municipio_id, proyecto_id): Evitar duplicados
    
    NOTAS DE VERSIÓN:
        v3.0: Sin cambios estructurales. Relación N:M mantenida.
    """
    __tablename__ = 'municipios_proyecto'
    __table_args__ = (
        db.UniqueConstraint('municipio_id', 'proyecto_id', 
                           name='municipios_proyecto_municipio_proyecto_key'),
        db.Index('idx_municipios_proyecto_proyecto', 'proyecto_id'),
        db.Index('idx_municipios_proyecto_municipio', 'municipio_id'),
        {'schema': 'public'}
    )
    
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado del registro puente'
    )
    
    municipio_id = db.Column(
        db.Integer,
        db.ForeignKey('municipios.id'),
        nullable=False,
        comment='FK a MUNICIPIOS. Municipio afectado por el proyecto'
    )
    
    proyecto_id = db.Column(
        db.Integer,
        db.ForeignKey('public.proyectos.id', referent_schema='public', ondelete='CASCADE', use_alter=True, name='fk_municipios_proyecto_proyecto'),
        nullable=False,
        comment='FK a PROYECTOS. Proyecto técnico que afecta al municipio'
    )
    
    # Relaciones
    municipio = db.relationship('Municipio', backref='proyectos_afectados')
    proyecto = db.relationship('Proyecto', backref='municipios_afectados')
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<MunicipioProyecto municipio={self.municipio_id} proyecto={self.proyecto_id}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return f'Proyecto {self.proyecto_id} → Municipio {self.municipio_id}'
