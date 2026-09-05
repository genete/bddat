"""Modelo InteresadoExpediente — tabla de interesados por expediente (#374).

`documento_acreditativo_id` es el documento que acredita la condición de
interesado, y del que sale su fecha administrativa
(`documento_acreditativo.fecha_administrativa`). Vale igual para los cinco
`tipo_origen`: la solicitud acredita al TITULAR, el oficio de consulta al
ORGANISMO_CONSULTADO, el escrito de personación al INTERESADO_RECONOCIDO.

Sigue siendo nullable, y ya no «de forma transitoria» (#428): para el TITULAR lo
rellena el servicio de alta con `Solicitud.documento_solicitud_id`, pero los otros
cuatro `tipo_origen` no están implementados y no habría quién rellenase su fila.
El NOT NULL espera a que existan.
"""
from app import db

TIPOS_ORIGEN_INTERESADO = (
    'TITULAR',
    'ORGANISMO_CONSULTADO',
    'MEDIO_AMBIENTE',
    'INTERESADO_RECONOCIDO',
    'DUP',
)


class InteresadoExpediente(db.Model):
    """
    Interesado registrado en un expediente concreto.

    Un registro por interesado por expediente. El campo tipo_origen identifica
    cómo fue reconocido: como titular inicial, como organismo consultado, como
    Medio Ambiente, como interesado reconocido en el procedimiento o como DUP.
    """
    __tablename__ = 'interesados_expediente'
    __table_args__ = (
        db.CheckConstraint(
            "tipo_origen IN ('TITULAR','ORGANISMO_CONSULTADO','MEDIO_AMBIENTE',"
            "'INTERESADO_RECONOCIDO','DUP')",
            name='ck_interesados_expediente_tipo_origen',
        ),
        db.Index('idx_interesados_expediente_expediente', 'expediente_id'),
        db.Index('idx_interesados_expediente_entidad', 'entidad_id'),
        {'schema': 'public'},
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    expediente_id = db.Column(
        db.Integer,
        db.ForeignKey('public.expedientes.id', ondelete='CASCADE'),
        nullable=False,
    )

    entidad_id = db.Column(
        db.Integer,
        db.ForeignKey('public.entidades.id'),
        nullable=True,
    )

    nombre = db.Column(db.String(255), nullable=True)
    nif = db.Column(db.String(20), nullable=True)

    tipo_origen = db.Column(db.String(30), nullable=False)

    documento_acreditativo_id = db.Column(
        db.Integer,
        db.ForeignKey('public.documentos.id'),
        nullable=True,
    )

    activo = db.Column(db.Boolean, nullable=False, default=True)

    # Relaciones
    expediente = db.relationship('Expediente', backref='interesados')
    entidad = db.relationship('Entidad', foreign_keys=[entidad_id], backref='interesados_expediente')
    documento_acreditativo = db.relationship(
        'Documento', foreign_keys=[documento_acreditativo_id])

    def __repr__(self):
        return f'<InteresadoExpediente exp={self.expediente_id} tipo={self.tipo_origen} entidad={self.entidad_id}>'
