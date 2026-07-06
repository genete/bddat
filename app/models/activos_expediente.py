from app import db


# Eje administrativo del activo — ADR-000 de bddat-instalaciones. Es relación
# activo × expediente (no un estado del activo en sí, ver ese ADR §Frontera).
ESTADOS_ADMINISTRATIVOS_ACTIVO = (
    'solicitado', 'en_tramitacion', 'autorizado_aap',
    'autorizado_construir_aac', 'autorizado_explotar_aps',
    'inscrito', 'desestimado', 'cerrado', 'desmantelado',
)


class ActivoExpediente(db.Model):
    """
    Tabla puente activo_red × expediente (#591).

    Vincula un activo técnico (definido en activo_red, fuente de verdad
    ajena a BDDAT) con el expediente que lo tramita, y registra el estado
    administrativo de esa relación. Un mismo activo puede aparecer en varios
    expedientes a lo largo de su vida (alta, modificación, baja).
    """
    __tablename__ = 'activos_expediente'
    __table_args__ = (
        db.UniqueConstraint('activo_id', 'expediente_id', name='uq_activos_expediente_activo_exp'),
        db.CheckConstraint(
            "estado_administrativo IN ("
            + ', '.join(f"'{e}'" for e in ESTADOS_ADMINISTRATIVOS_ACTIVO)
            + ")",
            name='ck_activos_expediente_estado',
        ),
        db.Index('idx_activos_expediente_activo', 'activo_id'),
        db.Index('idx_activos_expediente_expediente', 'expediente_id'),
        {'schema': 'public'},
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    activo_id = db.Column(
        db.Uuid,
        db.ForeignKey('public.activo_red.id'),
        nullable=False,
        comment='FK activo_red. Activo técnico vinculado al expediente',
    )

    expediente_id = db.Column(
        db.Integer,
        db.ForeignKey('public.expedientes.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK expedientes',
    )

    estado_administrativo = db.Column(
        db.String(30),
        nullable=False,
        comment='Estado administrativo de la relación activo-expediente — ver ESTADOS_ADMINISTRATIVOS_ACTIVO',
    )

    activo = db.relationship('ActivoRed', backref='expedientes_vinculados')
    expediente = db.relationship('Expediente', backref='activos_expediente')

    def __repr__(self):
        return f'<ActivoExpediente activo={self.activo_id} expediente={self.expediente_id} estado={self.estado_administrativo}>'
