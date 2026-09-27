from app import db


class TramiteDestinatario(db.Model):
    """El destinatario elegido para un trámite (ADR-051 §L, #968).

    Para los trámites de un solo destinatario que no sale de ninguna otra tabla
    (fuentes `BOLETIN`, `AYUNTAMIENTO`, `MINISTERIO`, `ORGANO_AMBIENTAL` en su
    fase y `ORGANO_SUPERIOR`): la entidad que eligió el usuario y, si se le
    notifica por él, su representante. Una fila por trámite.

    Es lo **pretendido** (el dato del usuario, como `organismos_expediente`); la
    fila de `notificaciones` es lo **realizado**, una copia congelada con la
    dirección. La escribe solo `services.destinatarios_notificacion.registrar_seleccion`,
    desde el ELABORAR del trámite o desde su `NOTIFICAR` si no hay ELABORAR.
    """
    __tablename__ = 'tramites_destinatario'
    __table_args__ = (
        db.CheckConstraint(
            'representante_entidad_id IS NULL OR representante_entidad_id <> entidad_id',
            name='ck_tramites_destinatario_representante',
        ),
        {'schema': 'public'},
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tramite_id = db.Column(
        db.Integer,
        db.ForeignKey('public.tramites.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
    )
    entidad_id = db.Column(db.Integer, db.ForeignKey('public.entidades.id'), nullable=False)
    representante_entidad_id = db.Column(
        db.Integer,
        db.ForeignKey('public.entidades.id'),
        nullable=True,
        comment='Representante de la entidad, si se le notifica a él. NULL = directo',
    )

    tramite = db.relationship(
        'Tramite',
        backref=db.backref('destinatario_elegido', uselist=False,
                           cascade='all, delete-orphan', passive_deletes=True),
    )
    entidad = db.relationship('Entidad', foreign_keys=[entidad_id])
    representante = db.relationship('Entidad', foreign_keys=[representante_entidad_id])

    def __repr__(self):
        return f'<TramiteDestinatario tramite={self.tramite_id} entidad={self.entidad_id}>'
