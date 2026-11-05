from app import db


class Plantilla(db.Model):
    """
    Catálogo de plantillas para generación de escritos administrativos.

    CONTENIDO Y FORMATO:
        El fichero vive en el almacén (`fichero_ref`, ADR-050 §J) y se sube desde el
        navegador. Su formato —.odt, el de referencia (ADR-035), o .docx, que se mantiene
        mientras la ADA no decida— es el de su fila de `ficheros`: elige el motor de
        render. No hay columna que lo declare aquí.

    ACTIVO:
        Pausa del supervisor, no «oculta»: solo la escribe él. Sin fichero no puede estar
        activa (CHECK `ck_plantillas_activa_con_fichero`). Que se pueda usar se calcula
        —activa, con fichero y contenido en buen estado—, en
        `contenido.motivo_no_usable`.

    PROPÓSITO:
        Cada registro vincula una plantilla con su contexto ESFTT
        (tipo de expediente, solicitud, fase, trámite) y con el tipo de documento
        que se creará en el pool del expediente al generar el escrito.

    RELACIÓN CON tipos_documentos:
        tipo_documento_id determina el TipoDocumento que se asignará al
        Documento generado. Permite al motor de reglas evaluar el criterio
        EXISTE_DOCUMENTO_TIPO sobre el expediente.

    CONTEXTO ESFTT:
        Las cuatro FKs de contexto son nullable. NULL significa "aplica a
        cualquier valor de esa dimensión". Permite expresar plantillas
        transversales (ej: un requerimiento válido para cualquier fase).

    VARIANTE:
        Texto libre para distinguir plantillas del mismo contexto ESFTT
        (ej: "Favorable", "Denegatoria", "Con condicionado").

    CONTEXTO_CLASE:
        Nombre de la clase Python del Context Builder (Capa 2).
        NULL = solo se usa ContextoBaseExpediente (Capa 1).

    RENOMBRADA en #167 Fase 2 desde tipos_escritos.
    """
    __tablename__ = 'plantillas'
    __table_args__ = (
        db.UniqueConstraint('codigo', name='uq_plantillas_codigo'),
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
        comment='Descripción ampliada de la plantilla'
    )

    fichero_ref = db.Column(
        db.Text,
        db.ForeignKey('public.ficheros.ref', name='fk_plantillas_fichero_ref'),
        nullable=True,
        comment='Contenido de la plantilla en el almacén (ADR-050 §J). Solo lo usa el subsistema de almacenamiento'
    )

    variante = db.Column(
        db.Text,
        nullable=True,
        comment='Texto libre para distinguir plantillas del mismo contexto ESFTT (Favorable, Denegatoria…)'
    )

    tipo_documento_id = db.Column(
        db.Integer,
        db.ForeignKey('public.tipos_documentos.id', name='fk_plantillas_tipo_documento'),
        nullable=False,
        comment='FK tipos_documentos — tipo que se asignará al documento generado'
    )

    tipo_expediente_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_expedientes.id', name='fk_plantillas_tipo_expediente'),
        nullable=True,
        comment='FK tipos_expedientes. NULL = aplica a cualquier tipo de expediente'
    )

    tipo_solicitud_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_solicitudes.id', name='fk_plantillas_tipo_solicitud'),
        nullable=True,
        comment='FK tipos_solicitudes. NULL = aplica a cualquier tipo de solicitud'
    )

    tipo_fase_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_fases.id', name='fk_plantillas_tipo_fase'),
        nullable=True,
        comment='FK tipos_fases. NULL = aplica a cualquier fase'
    )

    tipo_tramite_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_tramites.id', name='fk_plantillas_tipo_tramite'),
        nullable=True,
        comment='FK tipos_tramites. NULL = aplica a cualquier trámite'
    )

    contexto_clase = db.Column(
        db.Text,
        nullable=True,
        comment='Nombre de clase Python del Context Builder. NULL = solo Capa 1'
    )

    filtros_adicionales = db.Column(
        db.JSON,
        nullable=False,
        default=dict,
        server_default='{}',
        comment='Variables de negocio futuras (tensión, tecnología…). Vacío por ahora.'
    )

    activo = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default='true',
        comment=('Pausa del supervisor (ADR-050 §J): FALSE = no se usa para generar, aunque se '
                 'conserve. Solo la escribe el supervisor y sin fichero no puede estar activa (CHECK). '
                 'Que se pueda usar se calcula: activa, con fichero y su contenido en buen estado')
    )

    # Relaciones
    tipo_documento  = db.relationship('TipoDocumento',  foreign_keys=[tipo_documento_id])
    tipo_expediente = db.relationship('TipoExpediente', foreign_keys=[tipo_expediente_id])
    tipo_solicitud  = db.relationship('TipoSolicitud',  foreign_keys=[tipo_solicitud_id])
    tipo_fase       = db.relationship('TipoFase',       foreign_keys=[tipo_fase_id])
    tipo_tramite    = db.relationship('TipoTramite',    foreign_keys=[tipo_tramite_id])

    def __repr__(self):
        return f'<Plantilla {self.codigo}>'

    def __str__(self):
        return self.nombre
