from app import db


class TipoEscrito(db.Model):
    """
    Catálogo de tipos de escritos administrativos generables.

    PROPÓSITO:
        Cada registro vincula una plantilla .docx con su contexto ESFTT
        (tipo de solicitud, fase, trámite) y con el tipo de documento que se
        creará en el pool del expediente al generar el escrito.

    RELACIÓN CON tipos_documentos:
        tipo_documento_id determina el TipoDocumento que se asignará al
        Documento generado. Esto permite al motor de reglas evaluar el criterio
        EXISTE_DOCUMENTO_TIPO sobre el expediente.

    CONTEXTO ESFTT:
        Las tres FKs (tipo_solicitud_id, tipo_fase_id, tipo_tramite_id) son
        nullable. NULL significa "aplica a cualquier valor de esa dimensión".
        Permite expresar plantillas transversales (ej: un requerimiento válido
        para cualquier fase).

    FILTROS_ADICIONALES:
        JSONB vacío por ahora. Absorberá en el futuro variables de negocio
        dinámicas (tipo de suelo, tensión, tecnología renovable, potencia...)
        sin alterar el esquema de la tabla.

    CAMPOS_CATALOGO:
        [{campo, descripcion}] — Lista de campos disponibles para mostrar en la
        UI del contextualizador. Ayuda al supervisor a copiar el token correcto
        sin conocer el código Python.

    CONTEXTO_CLASE:
        Nombre de la clase Python del Context Builder (Capa 2).
        NULL = solo se usa ContextoBaseExpediente (Capa 1).
    """
    __tablename__ = 'tipos_escritos'
    __table_args__ = (
        db.UniqueConstraint('codigo', name='uq_tipos_escritos_codigo'),
        {'schema': 'public'}
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado'
    )

    codigo = db.Column(
        db.Text,
        nullable=False,
        comment='Slug estable para referencias en código: REQUERIMIENTO_SUBSANACION'
    )

    nombre = db.Column(
        db.Text,
        nullable=False,
        comment='Nombre legible para la UI'
    )

    descripcion = db.Column(
        db.Text,
        nullable=True,
        comment='Descripción ampliada del tipo de escrito'
    )

    ruta_plantilla = db.Column(
        db.Text,
        nullable=False,
        comment='Ruta relativa a PLANTILLAS_BASE/plantillas/'
    )

    tipo_documento_id = db.Column(
        db.Integer,
        db.ForeignKey('public.tipos_documentos.id', name='fk_tipos_escritos_tipo_documento'),
        nullable=False,
        comment='FK tipos_documentos — tipo que se asignará al documento generado'
    )

    contexto_clase = db.Column(
        db.Text,
        nullable=True,
        comment='Nombre de clase Python del Context Builder. NULL = solo Capa 1'
    )

    campos_catalogo = db.Column(
        db.JSON,
        nullable=True,
        comment='[{campo, descripcion}] — campos disponibles para la UI del contextualizador'
    )

    tipo_solicitud_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_solicitudes.id', name='fk_tipos_escritos_tipo_solicitud'),
        nullable=True,
        comment='FK tipos_solicitudes. NULL = aplica a cualquier tipo de solicitud'
    )

    tipo_fase_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_fases.id', name='fk_tipos_escritos_tipo_fase'),
        nullable=True,
        comment='FK tipos_fases. NULL = aplica a cualquier fase'
    )

    tipo_tramite_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_tramites.id', name='fk_tipos_escritos_tipo_tramite'),
        nullable=True,
        comment='FK tipos_tramites. NULL = aplica a cualquier trámite'
    )

    filtros_adicionales = db.Column(
        db.JSON,
        nullable=False,
        default=dict,
        server_default='{}',
        comment='Variables de negocio futuras (tensión, tecnología...). Vacío por ahora.'
    )

    activo = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default='true',
        comment='FALSE = oculta en tarea REDACTAR pero conservada para histórico'
    )

    # Relaciones
    tipo_documento = db.relationship('TipoDocumento', foreign_keys=[tipo_documento_id])
    tipo_solicitud = db.relationship('TipoSolicitud', foreign_keys=[tipo_solicitud_id])
    tipo_fase      = db.relationship('TipoFase',      foreign_keys=[tipo_fase_id])
    tipo_tramite   = db.relationship('TipoTramite',   foreign_keys=[tipo_tramite_id])

    def __repr__(self):
        return f'<TipoEscrito {self.codigo}>'

    def __str__(self):
        return self.nombre
