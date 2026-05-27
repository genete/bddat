from app import db


class TramiteTareaDocumento(db.Model):
    """
    Mapa semántico: qué documento consume (ENTRADA) y produce (SALIDA)
    cada tarea atómica de cada trámite.

    tipo_documento_id = NULL significa polimórfico: en runtime acepta
    cualquier tipo válido para ese rol. Ver plan #346 §3.
    """
    __tablename__ = 'tramites_tareas_documentos'
    __table_args__ = (
        db.PrimaryKeyConstraint(
            'tipo_tramite_id', 'orden_tarea', 'rol',
            name='pk_ttd'
        ),
        {'schema': 'public'}
    )

    tipo_tramite_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_tramites.id', name='fk_ttd_tipo_tramite'),
        nullable=False
    )
    orden_tarea = db.Column(
        db.SmallInteger,
        nullable=False,
        comment='Coincide con tramites_tareas.orden para el mismo tipo_tramite_id'
    )
    rol = db.Column(
        db.Text,
        nullable=False,
        comment='ENTRADA | SALIDA'
    )
    tipo_documento_id = db.Column(
        db.Integer,
        db.ForeignKey('public.tipos_documentos.id', name='fk_ttd_tipo_documento'),
        nullable=True,
        comment='NULL = polimórfico (cualquier tipo válido en runtime)'
    )
    obligatorio = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default='true'
    )

    tipo_tramite = db.relationship('TipoTramite', backref='tareas_documentos')
    tipo_documento = db.relationship(
        'TipoDocumento',
        foreign_keys=[tipo_documento_id],
        backref='tareas_documentos'
    )

    def __repr__(self):
        return (
            f'<TramiteTareaDocumento tramite={self.tipo_tramite_id} '
            f'orden={self.orden_tarea} rol={self.rol}>'
        )
