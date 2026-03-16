from app import db


class SolicitudFase(db.Model):
    """
    Whitelist: combinaciones válidas (tipo_solicitud, tipo_fase).

    Vacío = sin restricciones (cualquier combinación permitida).
    Editado por supervisor desde UI admin (Fase 4).
    """
    __tablename__ = 'solicitudes_fases'
    __table_args__ = {'schema': 'public'}

    tipo_solicitud_id = db.Column(
        db.Integer,
        db.ForeignKey('public.tipos_solicitudes.id', name='fk_sol_fas_tipo_solicitud'),
        primary_key=True,
        nullable=False
    )
    tipo_fase_id = db.Column(
        db.Integer,
        db.ForeignKey('public.tipos_fases.id', name='fk_sol_fas_tipo_fase'),
        primary_key=True,
        nullable=False
    )

    tipo_solicitud = db.relationship('TipoSolicitud')
    tipo_fase = db.relationship('TipoFase')

    def __repr__(self):
        return f'<SolicitudFase sol={self.tipo_solicitud_id} fase={self.tipo_fase_id}>'
