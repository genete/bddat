from app import db


class TramiteTareaDocumento(db.Model):
    """
    Mapa semántico: qué documento consume (ENTRADA) y produce (SALIDA)
    cada tarea atómica de cada trámite.

    tipo_documento_id = NULL significa polimórfico: en runtime acepta
    cualquier tipo válido para ese rol. Ver plan #346 §3.

    PK: `id` autoincremental (#928, N1) — antes era la compuesta
    (tipo_tramite_id, orden_tarea, rol), que solo admitía una fila por paso.
    El índice único funcional `uq_ttd_paso_tipo_documento` ocupa su lugar como
    guarda de duplicados: impide dos filas del mismo (tramite, orden, rol) con
    el mismo `tipo_documento_id` (o dos polimórficas, vía `COALESCE(…, 0)`),
    pero admite varias filas ENTRADA distintas en el mismo paso — el
    documento a notificar y los justificantes previos de NOTIFICAR conviven
    ahí.
    """
    __tablename__ = 'tramites_tareas_documentos'
    __table_args__ = (
        db.Index(
            'uq_ttd_paso_tipo_documento',
            'tipo_tramite_id', 'orden_tarea', 'rol', db.text('COALESCE(tipo_documento_id, 0)'),
            unique=True,
        ),
        db.ForeignKeyConstraint(
            ['tipo_tramite_id', 'orden_tarea'],
            ['public.tramites_tareas.tipo_tramite_id', 'public.tramites_tareas.orden'],
            name='fk_ttd_tramite_tarea',
        ),
        {'schema': 'public'}
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado (#928, sustituye a la PK compuesta)'
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
