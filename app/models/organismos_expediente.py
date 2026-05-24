from app import db


ESTADOS_ORGANISMO = (
    'pendiente',
    'separata_enviada',
    'en_tramitacion',
    'cerrado_favorable',
    'cerrado_con_condicionados',
    'audiencia_previa',
    'exonerado',
)

VIAS_ORGANISMO = ('consulta', 'declaracion_responsable')


class OrganismoExpediente(db.Model):
    """
    Relación entre un organismo consultado y un expediente concreto.

    Un registro por organismo por expediente. Cubre tanto la vía de consulta
    ordinaria (separata + trámites de traslado) como la vía de declaración
    responsable (el titular acredita disponer ya de la autorización del organismo).

    Los trámites del ciclo de consulta se vinculan a este registro mediante
    la tabla `tramites_organismos` (ADR-011 §1).

    Diseño de referencia: DISEÑO_CONSULTAS_ORGANISMOS.md §2, ADR-011
    """
    __tablename__ = 'organismos_expediente'
    __table_args__ = (
        db.UniqueConstraint('expediente_id', 'organismo_id', name='uq_org_exp_expediente_organismo'),
        db.CheckConstraint("via IN ('consulta', 'declaracion_responsable')", name='ck_org_exp_via'),
        db.CheckConstraint(
            "estado IN ('pendiente','separata_enviada','en_tramitacion',"
            "'cerrado_favorable','cerrado_con_condicionados','audiencia_previa','exonerado')",
            name='ck_org_exp_estado',
        ),
        {'schema': 'public'},
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    expediente_id = db.Column(
        db.Integer,
        db.ForeignKey('public.expedientes.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment='FK expedientes. Expediente al que pertenece la consulta',
    )

    organismo_id = db.Column(
        db.Integer,
        db.ForeignKey('public.entidades.id'),
        nullable=False,
        index=True,
        comment='FK entidades (rol_consultado=True). Organismo consultado',
    )

    via = db.Column(
        db.String(30),
        nullable=False,
        default='consulta',
        comment='Vía de resolución: consulta (trámite normal) o declaracion_responsable',
    )

    documento_id = db.Column(
        db.Integer,
        db.ForeignKey('public.documentos.id'),
        nullable=True,
        comment='Documento de declaración responsable (solo si via=declaracion_responsable)',
    )

    estado = db.Column(
        db.String(40),
        nullable=False,
        default='pendiente',
        comment='Estado del ciclo de vida del organismo en el expediente',
    )

    condicionados_doc_id = db.Column(
        db.Integer,
        db.ForeignKey('public.documentos.id'),
        nullable=True,
        comment='FK documento CONDICIONADO_OFICIO. Solo cuando titular sin_respuesta en AAC tras condicionado (ADR-011 §2)',
    )

    plazo_legal_dias = db.Column(
        db.Integer,
        nullable=True,
        comment='Plazo legal aplicable en días (capturado al crear la separata según tipo de expediente). 30 días general; 15 si AAP previa y solo AAC sin DUP',
    )

    # Relaciones
    expediente = db.relationship('Expediente', backref='organismos')
    organismo = db.relationship('Entidad', foreign_keys=[organismo_id])
    documento = db.relationship('Documento', foreign_keys=[documento_id])
    condicionados_doc = db.relationship('Documento', foreign_keys=[condicionados_doc_id])

    def __repr__(self):
        return f'<OrganismoExpediente exp={self.expediente_id} org={self.organismo_id} estado={self.estado}>'

    @property
    def consulta_completa(self) -> bool:
        """True cuando la consulta está completamente resuelta (ADR-011 §6).

        Para declaracion_responsable: completa cuando estado es exonerado.
        Para consulta ordinaria: completa cuando el ciclo alcanzó un estado de cierre.
        La evaluación detallada por resultado de cada trámite (casos A-D del ADR)
        se implementará cuando TramiteOrganismo.resultado esté disponible (#460).
        """
        if self.via == 'declaracion_responsable':
            return self.estado == 'exonerado'
        return self.estado in ('cerrado_favorable', 'cerrado_con_condicionados')

    def as_contexto_cb(self) -> dict:
        """Fragmento de contexto para plantillas de CONSULTA_SEPARATA."""
        return {
            'organismo_nombre': self.organismo.nombre_completo if self.organismo else None,
            'organismo_nif': self.organismo.nif if self.organismo else None,
            'organismo_plazo_legal': self.plazo_legal_dias,
            'organismo_resultado': self.estado,  # estado interno del motor; no usar en plantillas de escritos
        }
