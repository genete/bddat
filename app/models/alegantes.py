from app import db


class Alegante(db.Model):
    """
    Persona u organismo que presenta una alegación en un trámite RECEPCION_ALEGACION.

    Un alegante por trámite (UNIQUE en tramite_id).

    Si entidad_id está relleno, nombre y nif se toman de Entidad (evita duplicación).
    Si entidad_id es NULL, se usan los campos locales nombre y nif (alegante ocasional
    no registrado en el sistema).
    """
    __tablename__ = 'alegantes'
    __table_args__ = (
        db.UniqueConstraint('tramite_id', name='uq_alegante_tramite'),
        db.CheckConstraint(
            "tipo_interesado IN ('particular', 'administracion', 'asociacion', 'empresa')",
            name='ck_alegante_tipo_interesado',
        ),
        {'schema': 'public'},
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    tramite_id = db.Column(
        db.Integer,
        db.ForeignKey('public.tramites.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
        comment='FK tramites. Trámite RECEPCION_ALEGACION al que pertenece',
    )

    entidad_id = db.Column(
        db.Integer,
        db.ForeignKey('public.entidades.id'),
        nullable=True,
        comment='FK entidades. Relleno si el alegante ya existe como entidad del sistema',
    )

    nombre = db.Column(
        db.String(255),
        nullable=True,
        comment='Nombre del alegante cuando entidad_id es NULL',
    )

    nif = db.Column(
        db.String(20),
        nullable=True,
        comment='NIF del alegante cuando entidad_id es NULL',
    )

    tipo_interesado = db.Column(
        db.String(50),
        nullable=False,
        comment='Tipo de interesado: particular, administracion, asociacion, empresa',
    )

    tramite = db.relationship(
        'Tramite',
        foreign_keys=[tramite_id],
        backref=db.backref('alegante', uselist=False),
    )

    entidad = db.relationship(
        'Entidad',
        foreign_keys=[entidad_id],
        backref=db.backref('alegaciones', lazy='dynamic'),
    )

    def __repr__(self):
        return f'<Alegante tramite={self.tramite_id} tipo={self.tipo_interesado}>'

    def as_contexto_cb(self) -> dict:
        """Fragmento de contexto para plantillas de RECEPCION_ALEGACION."""
        nombre = self.entidad.nombre_completo if self.entidad else self.nombre
        nif = self.entidad.nif if self.entidad else self.nif
        return {
            'alegante_nombre': nombre,
            'alegante_nif': nif,
            'alegante_tipo_interesado': self.tipo_interesado,
        }
