from app import db


class FaseTramite(db.Model):
    """
    Whitelist: combinaciones válidas (tipo_fase, tipo_tramite).

    Seed inicial desde Estructura_fases_tramites_tareas.json (30 pares).
    Editado por supervisor desde UI admin (Fase 4).
    """
    __tablename__ = 'fases_tramites'
    __table_args__ = {'schema': 'public'}

    tipo_fase_id = db.Column(
        db.Integer,
        db.ForeignKey('public.tipos_fases.id', name='fk_fas_tram_tipo_fase'),
        primary_key=True,
        nullable=False
    )
    tipo_tramite_id = db.Column(
        db.Integer,
        db.ForeignKey('public.tipos_tramites.id', name='fk_fas_tram_tipo_tramite'),
        primary_key=True,
        nullable=False
    )

    tipo_fase = db.relationship('TipoFase')
    tipo_tramite = db.relationship('TipoTramite')

    def __repr__(self):
        return f'<FaseTramite fase={self.tipo_fase_id} tramite={self.tipo_tramite_id}>'
