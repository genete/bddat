from app import db
from app.models.direccion_notificacion import DireccionNotificacion


# Resultado legal de la consulta (ADR-011 §6). NULL mientras el ciclo está en
# curso — "en curso" ya no es un valor almacenado: lo deriva estado_dominio.
# estado_organismo() a partir de los trámites vinculados (ADR-042, #396).
RESULTADOS_ORGANISMO = (
    'cerrado_favorable',
    'cerrado_con_condicionados',
    'audiencia_previa',
    'exonerado',
)

VIAS_ORGANISMO = ('consulta', 'declaracion_responsable')


class OrganismoExpediente(db.Model):
    """
    Relación entre un organismo consultado y una fase CONSULTAS concreta.

    Un registro por organismo por fase (#396): la fase es la ronda de consultas
    (DISEÑO_CONSULTAS_ORGANISMOS.md §6 bis) — un modificado de proyecto puede
    obligar a repetirla, con los mismos organismos, un subconjunto, o un
    subconjunto más organismos nuevos. Cubre tanto la vía de consulta ordinaria
    (separata + trámites de traslado) como la vía de declaración responsable (el
    titular acredita disponer ya de la autorización del organismo).

    Los trámites del ciclo de consulta se vinculan a este registro mediante
    la tabla `tramites_organismos` (ADR-011 §1).

    Diseño de referencia: DISEÑO_CONSULTAS_ORGANISMOS.md §2/§6 bis, ADR-011, ADR-042
    """
    __tablename__ = 'organismos_expediente'
    __table_args__ = (
        db.UniqueConstraint('fase_id', 'organismo_id', name='uq_org_exp_fase_organismo'),
        db.CheckConstraint("via IN ('consulta', 'declaracion_responsable')", name='ck_org_exp_via'),
        db.CheckConstraint(
            "resultado IS NULL OR resultado IN ('cerrado_favorable',"
            "'cerrado_con_condicionados','audiencia_previa','exonerado')",
            name='ck_org_exp_resultado',
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

    fase_id = db.Column(
        db.Integer,
        db.ForeignKey('public.fases.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment='FK fases. Fase CONSULTAS (= la ronda) en la que se consulta a este organismo',
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

    resultado = db.Column(
        db.String(40),
        nullable=True,
        comment='Resultado legal de la consulta (ADR-011 §6). NULL mientras el ciclo está en curso',
    )

    condicionados_doc_id = db.Column(
        db.Integer,
        db.ForeignKey('public.documentos.id'),
        nullable=True,
        comment='FK documento CONDICIONADO_OFICIO. Solo cuando titular sin_respuesta en AAC tras condicionado (ADR-011 §2)',
    )

    direccion_notificacion_id = db.Column(
        db.Integer,
        db.ForeignKey('public.direcciones_notificacion.id', name='fk_org_exp_direccion_notif'),
        nullable=True,
        index=True,
        comment='FK direcciones_notificacion. Dirección elegida al añadir el organismo; NULL = usar la más reciente activa con rol CONSULTADO',
    )

    plazo_legal_dias = db.Column(
        db.Integer,
        nullable=True,
        comment='Plazo legal aplicable en días (capturado al crear la separata según tipo de expediente). 30 días general; 15 si AAP previa y solo AAC sin DUP',
    )

    # Relaciones
    expediente = db.relationship('Expediente', backref='organismos')
    fase = db.relationship('Fase', foreign_keys=[fase_id], backref='organismos')
    organismo = db.relationship('Entidad', foreign_keys=[organismo_id])
    documento = db.relationship('Documento', foreign_keys=[documento_id])
    condicionados_doc = db.relationship('Documento', foreign_keys=[condicionados_doc_id])
    direccion_notificacion = db.relationship('DireccionNotificacion', foreign_keys=[direccion_notificacion_id])

    def __repr__(self):
        return f'<OrganismoExpediente fase={self.fase_id} org={self.organismo_id} resultado={self.resultado}>'

    @property
    def consulta_completa(self) -> bool:
        """True cuando la consulta está completamente resuelta (ADR-011 §6).

        Para declaracion_responsable: completa cuando resultado es exonerado.
        Para consulta ordinaria: completa cuando el ciclo alcanzó un resultado de cierre.
        La evaluación detallada por resultado de cada trámite (casos A-D del ADR)
        se implementará cuando TramiteOrganismo.resultado esté disponible (#460).
        """
        if self.via == 'declaracion_responsable':
            return self.resultado == 'exonerado'
        return self.resultado in ('cerrado_favorable', 'cerrado_con_condicionados')

    def as_contexto_cb(self) -> dict:
        """Fragmento de contexto para plantillas de CONSULTA_SEPARATA."""
        ctx = {
            'organismo_nombre': self.organismo.nombre_completo if self.organismo else None,
            'organismo_nif': self.organismo.nif if self.organismo else None,
            'organismo_plazo_legal': self.plazo_legal_dias,
            'organismo_resultado': self.resultado,  # resultado legal; None mientras el ciclo está en curso
        }
        dir_notif = (
            self.direccion_notificacion
            or (
                DireccionNotificacion.obtener_direccion_notificacion(
                    self.organismo_id, es_consultado=True
                )
                if self.organismo_id
                else None
            )
        )
        if dir_notif:
            df = dir_notif.direccion_formateada()
            ctx.update({
                'organismo_email': dir_notif.email,
                'organismo_dir3': dir_notif.codigo_dir3,
                'organismo_sir': dir_notif.codigo_sir,
                'organismo_direccion_linea1': df['linea1'],
                'organismo_direccion_linea2': df['linea2'],
                'organismo_provincia': df['provincia'],
            })
        else:
            ctx.update({
                'organismo_email': None,
                'organismo_dir3': None,
                'organismo_sir': None,
                'organismo_direccion_linea1': None,
                'organismo_direccion_linea2': None,
                'organismo_provincia': None,
            })
        return ctx
