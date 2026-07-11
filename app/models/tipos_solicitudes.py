from app import db

class TipoSolicitud(db.Model):
    """
    Catálogo maestro de tipos de actos administrativos solicitables.
    
    PROPÓSITO:
        Define los tipos de actos administrativos solicitables según normativa
        sectorial eléctrica. Las combinaciones (AAP+AAC, AAP+AAC+DUP...) NO viven
        en una tabla puente — son filas propias de este catálogo, con las siglas
        atómicas unidas por '+' (p.ej. 'AAP+AAC'). No existe modelo `SolicitudTipo`
        ni tabla `solicitudes_tipos`: se descartó esa tabla puente porque el número
        de combinaciones que permite la legislación es pequeño y cerrado. El
        separador '+' está hardcodeado en `Solicitud.tipos_simples`/`contiene_tipo()`
        (`solicitudes.py`) — antes se usaba '_', pero colisionaba con códigos que
        llevan '_' de forma nativa (no como combinador), de ahí el cambio a '+'.
        Toda combinación nueva debe seguir esa convención.

    FILOSOFÍA:
        - Motor de reglas aplica lógica sobre tipos INDIVIDUALES vía `contiene_tipo()`,
          que descompone la siglas combinada por '+' en tiempo de evaluación
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
        - solicitudes.tipo_solicitud_id → esta tabla (N:1, una sola fila por solicitud,
          las combinaciones son la propia fila combinada, no una relación N:M)
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
