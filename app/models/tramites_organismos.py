from app import db


class TramiteOrganismo(db.Model):
    """
    Vínculo entre un trámite de consulta y el organismo al que pertenece.

    Permite que CONSULTA_SEPARATA, CONSULTA_TRASLADO_ORGANISMO y
    CONSULTA_TRASLADO_TITULAR identifiquen unívocamente su organismo_expediente
    en expedientes con múltiples organismos consultados.

    El UNIQUE en tramite_id garantiza que cada trámite pertenece a un solo
    organismo. Un organismo puede tener N trámites (SEPARATA + 0-2 TRASLADOs).

    Diseño de referencia: ADR-011 §1
    """
    __tablename__ = 'tramites_organismos'
    __table_args__ = (
        db.UniqueConstraint('tramite_id', name='uq_tramorg_tramite'),
        {'schema': 'public'},
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    tramite_id = db.Column(
        db.Integer,
        db.ForeignKey('public.tramites.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
        comment='FK tramites (UNIQUE — un trámite pertenece a un solo organismo)',
    )

    organismo_expediente_id = db.Column(
        db.Integer,
        db.ForeignKey('public.organismos_expediente.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment='FK organismos_expediente. Organismo al que pertenece el trámite',
    )

    # Relaciones
    tramite = db.relationship('Tramite', foreign_keys=[tramite_id])
    organismo_expediente = db.relationship(
        'OrganismoExpediente',
        foreign_keys=[organismo_expediente_id],
        backref=db.backref('tramites_organismo', lazy='dynamic'),
    )

    def __repr__(self):
        return (
            f'<TramiteOrganismo tramite={self.tramite_id} '
            f'org_exp={self.organismo_expediente_id}>'
        )
