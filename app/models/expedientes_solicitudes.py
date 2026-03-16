from app import db


class ExpedienteSolicitud(db.Model):
    """
    Whitelist: combinaciones válidas (tipo_expediente, tipo_solicitud).

    Vacío = sin restricciones (cualquier combinación permitida).
    Editado por supervisor desde UI admin (Fase 4).
    """
    __tablename__ = 'expedientes_solicitudes'
    __table_args__ = {'schema': 'public'}

    tipo_expediente_id = db.Column(
        db.Integer,
        db.ForeignKey('public.tipos_expedientes.id', name='fk_exp_sol_tipo_expediente'),
        primary_key=True,
        nullable=False
    )
    tipo_solicitud_id = db.Column(
        db.Integer,
        db.ForeignKey('public.tipos_solicitudes.id', name='fk_exp_sol_tipo_solicitud'),
        primary_key=True,
        nullable=False
    )

    tipo_expediente = db.relationship('TipoExpediente')
    tipo_solicitud = db.relationship('TipoSolicitud')

    def __repr__(self):
        return f'<ExpedienteSolicitud exp={self.tipo_expediente_id} sol={self.tipo_solicitud_id}>'
