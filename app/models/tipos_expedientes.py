from app import db

class TipoExpediente(db.Model):
    """
    Catálogo de tipos de expedientes según clasificación normativa.
    
    PROPÓSITO:
        Define la clasificación de expedientes según tipo de instalación eléctrica
        (transporte, distribución, renovable, autoconsumo, etc.).
        Determina procedimientos aplicables según legislación sectorial eléctrica.
    
    FILOSOFÍA:
        - La semántica procedimental vive aquí, no en campos de EXPEDIENTES
        - Tabla maestra estable que define reglas de negocio procedimentales
        - Valores definidos en datos_maestros.sql (fuente de verdad)
    
    RELACIONES:
        - expedientes ← EXPEDIENTES.tipo_expediente_id (clasificación)
        - Usado por motor de reglas para determinar flujos procedimentales
    
    REGLAS DE NEGOCIO:
        El TIPO_EXPEDIENTE_ID es clave para el motor de reglas que determina:
        - Solicitudes aplicables (AAP, AAC, DUP, etc.)
        - Fases obligatorias del procedimiento
        - Organismos a consultar
        - Requisitos documentales
    
    DATOS MAESTROS:
        Ver datos_maestros.sql para valores iniciales (8 tipos definidos).
    
    NOTAS DE VERSIÓN:
        v3.0: Sin cambios estructurales. Tabla maestra estable.
    """
    __tablename__ = 'tipos_expedientes'
    __table_args__ = {'schema': 'estructura'}
    
    id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True,
        comment='Identificador único autogenerado del tipo de expediente'
    )
    
    tipo = db.Column(
        db.String(100),
        comment='Denominación del tipo según clasificación normativa'
    )
    
    descripcion = db.Column(
        db.String(200),
        comment='Descripción detallada de características y particularidades procedimentales'
    )
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<TipoExpediente {self.id}: {self.tipo}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return self.tipo or f'TipoExpediente #{self.id}'
