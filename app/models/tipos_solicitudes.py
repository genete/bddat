from app import db

class TipoSolicitud(db.Model):
    """
    Catálogo maestro de tipos de actos administrativos solicitables.
    
    PROPÓSITO:
        Define los tipos individuales de solicitudes administrativas según normativa
        sectorial eléctrica. Las combinaciones (AAP+AAC+DUP) se gestionan mediante
        la tabla puente solicitudes_tipos, permitiendo lógica de reglas basada en
        tipos atómicos sin duplicación.
    
    FILOSOFÍA:
        - Motor de reglas aplica lógica sobre tipos INDIVIDUALES, no combinaciones
        - Cada tipo determina fases procedimentales obligatorias
        - Define requisitos documentales específicos y plazos de resolución
        - Basado en nomenclatura legal
    
    TIPOS ESPECIALES:
        DESISTIMIENTO:
            - Afecta a otra solicitud previa (requiere SOLICITUD_AFECTADA_ID)
            - Finaliza la solicitud referenciada sin resolución de fondo
        
        RENUNCIA:
            - Similar a DESISTIMIENTO pero con efectos jurídicos diferentes
            - Requiere SOLICITUD_AFECTADA_ID NOT NULL en tabla SOLICITUDES
    
    RELACIONES:
        - solicitudes_tipos (N:M) → SOLICITUDES: Permite múltiples tipos por solicitud
        - Referenciada por motor de reglas para determinar flujos procedimentales
    
    REGLAS DE NEGOCIO:
        El TIPO_SOLICITUD_ID determina:
        - Fases obligatorias del procedimiento
        - Requisitos documentales
        - Plazos máximos de resolución
        - Silencio administrativo (positivo/negativo)
        - Validaciones de secuencia (ej: MOD requiere AAC previa)
    
    DATOS MAESTROS:
        Ver datos_maestros.sql para valores iniciales.
    
    NOTAS DE VERSIÓN:
        v3.0: Sin cambios estructurales. Tabla maestra estable.
    """
    __tablename__ = 'tipos_solicitudes'


    id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True, 
        comment='Identificador único autogenerado del tipo de solicitud'
    )
    
    siglas = db.Column(
        db.String(100), 
        nullable=False, 
        unique=True,
        comment='Código normalizado del acto administrativo (AAP, AAC, DUP, etc.)'
    )
    
    descripcion = db.Column(
        db.String(200),
        nullable=False,
        comment='Descripción completa del acto administrativo solicitado'
    )

    nombre_en_plantilla = db.Column(
        db.Text,
        nullable=True,
        comment='Nombre legible usado en nombres de documentos generados'
    )
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<TipoSolicitud {self.siglas}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return f'{self.siglas} - {self.descripcion}'
