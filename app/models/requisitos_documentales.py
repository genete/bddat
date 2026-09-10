from app import db


class RequisitoDocumental(db.Model):
    """
    Catálogo de requisitos documentales que el administrado debe aportar.

    Cada fila representa un tipo de documento exigido por ley como condición
    necesaria para que la solicitud pueda tramitarse. El técnico verifica su
    presencia durante la tarea ANALIZAR de ANALISIS_DOCUMENTAL.

    CONDICIONES DE APLICACIÓN:
        Un requisito es aplicable a una solicitud concreta si se cumplen TODAS
        sus condiciones (tabla condiciones_requisito, AND implícito). Un requisito
        sin condiciones es universal — aplica a cualquier solicitud.

        Para expresar OR (mismo tipo de documento requerido bajo dos conjuntos
        de condiciones mutuamente excluyentes), se crean dos filas con el mismo
        tipo_documento_id y condiciones distintas.

    CAMPO ORDEN:
        Valor informativo para ordenar el checklist en la UI. Gestionado por el
        Supervisor mediante drag-drop; no tiene unicidad impuesta en BD.

    RELACIONES:
        condiciones  → CONDICIONES_REQUISITO (todas las condiciones de este requisito)
        usos         → DOCUMENTOS_REQUISITO (vinculaciones de documentos del pool)
        tipo_documento → TIPOS_DOCUMENTOS
        norma          → NORMAS

    INTEGRACIÓN:
        Ver app/services/requisitos.py::evaluar_requisitos para la lógica de
        evaluación de condiciones e integración con ContextoAnalisisDocumental (#495).
    """
    __tablename__ = 'requisitos_documentales'
    __table_args__ = (
        db.Index('idx_requisitos_documentales_tipo_doc', 'tipo_documento_id'),
        {'schema': 'public'}
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado'
    )

    tipo_documento_id = db.Column(
        db.Integer,
        db.ForeignKey('public.tipos_documentos.id'),
        nullable=False,
        comment='FK a tipos_documentos — tipo semántico del documento requerido'
    )

    descripcion_legal = db.Column(
        db.Text,
        nullable=True,
        comment='Descripción del requisito en lenguaje natural para el técnico'
    )

    norma_id = db.Column(
        db.Integer,
        db.ForeignKey('public.normas.id'),
        nullable=True,
        comment='FK a normas — norma que establece este requisito'
    )

    articulo = db.Column(
        db.String(20),
        nullable=True,
        comment='Artículo concreto de la norma: "4.1" | "DA2" | "DF1"'
    )

    orden = db.Column(
        db.Integer,
        nullable=False,
        default=1,
        comment='Orden de presentación en el checklist de la UI (informativo, sin unicidad)'
    )

    activo = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=db.text('true'),
        comment='Baja lógica (decisión humana del Supervisor, no automática). '
                'Los expedientes antiguos conservan su DocumentoRequisito aunque '
                'el requisito se desactive — evita huérfanos al reconstruir histórico.'
    )

    afectado_por_reformado = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=db.text('false'),
        comment='ADR-044 §E bis (R4 #899). Marcado a mano por el Supervisor — no '
                'se infiere de ninguna otra propiedad del requisito. False: la '
                'cobertura es global por solicitud, la misma vinculación vale para '
                'todas las versiones del proyecto. True: un reformado puede exigir '
                'una vinculación propia para la versión vigente (documentos_requisito. '
                'reformado_id), aunque la de la versión inicial siga contando si nada '
                'cambió (caso de origen: la tasa y su complementaria).'
    )

    # Relaciones
    tipo_documento = db.relationship('TipoDocumento')
    norma          = db.relationship('Norma')
    condiciones    = db.relationship(
        'CondicionRequisito',
        backref='requisito',
        cascade='all, delete-orphan',
        order_by='CondicionRequisito.orden',
    )
    usos = db.relationship(
        'DocumentoRequisito',
        backref='requisito',
        cascade='all, delete-orphan',
    )

    def __repr__(self):
        return f'<RequisitoDocumental id={self.id} tipo_doc={self.tipo_documento_id}>'


class CondicionRequisito(db.Model):
    """
    Condición individual de un RequisitoDocumental.

    Misma semántica que CondicionRegla: evalúa una variable del dict de contexto
    contra un valor de referencia con un operador. Todas las condiciones del mismo
    requisito se combinan con AND implícito. Para expresar OR, crear dos requisitos
    separados con el mismo tipo_documento_id.

    La variable referenciada debe estar activa en catalogo_variables y tener
    función registrada en el Variable Registry para que el evaluador pueda
    obtener su valor.

    OPERADORES SOPORTADOS (paridad con CondicionRegla, #601):
        EQ / NEQ            igual / distinto
        IN / NOT_IN         en el conjunto / fuera del conjunto
        IS_NULL / NOT_NULL  ausente / presente
        GT / GTE / LT / LTE comparaciones numéricas
        BETWEEN / NOT_BETWEEN  rango [a, b] — valor es lista [min, max]
    """
    __tablename__ = 'condiciones_requisito'
    __table_args__ = (
        db.CheckConstraint(
            "operador IN ('EQ','NEQ','IN','NOT_IN','IS_NULL','NOT_NULL',"
            "'GT','GTE','LT','LTE','BETWEEN','NOT_BETWEEN')",
            name='ck_condiciones_requisito_operador'
        ),
        db.Index('idx_condiciones_requisito_requisito', 'requisito_id'),
        db.Index('idx_condiciones_requisito_variable',  'variable_id'),
        {'schema': 'public'}
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado'
    )

    requisito_id = db.Column(
        db.Integer,
        db.ForeignKey('public.requisitos_documentales.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a requisitos_documentales'
    )

    variable_id = db.Column(
        db.Integer,
        db.ForeignKey('public.catalogo_variables.id'),
        nullable=False,
        comment='FK a catalogo_variables — variable evaluada'
    )

    operador = db.Column(
        db.String(20),
        nullable=False,
        comment='Operador de comparación (ver catálogo en el docstring de la clase)'
    )

    valor = db.Column(
        db.JSON,
        nullable=True,
        comment='Valor de referencia. Lista para IN/NOT_IN/BETWEEN/NOT_BETWEEN, None para IS_NULL/NOT_NULL'
    )

    orden = db.Column(
        db.Integer,
        nullable=False,
        default=1,
        comment='Orden informativo dentro del requisito (presentación en UI)'
    )

    variable = db.relationship('CatalogoVariable')

    def __repr__(self):
        nombre = self.variable.nombre if self.variable else f'var_id={self.variable_id}'
        return (
            f'<CondicionRequisito id={self.id} req={self.requisito_id} '
            f'{nombre} {self.operador} {self.valor!r}>'
        )


class DocumentoRequisito(db.Model):
    """
    Vinculación entre un requisito documental y el documento del pool que lo satisface.

    El técnico, durante la tarea ANALIZAR de ANALISIS_DOCUMENTAL, asocia cada
    requisito aplicable a la solicitud con un documento concreto del pool del
    expediente. Esta tabla registra esa decisión.

    Un mismo documento del pool puede cubrir el mismo requisito en solicitudes
    distintas del expediente (reutilización). Por ejemplo, el CIF aportado en la
    solicitud 1 puede cubrir el mismo requisito en la solicitud 2.

    UNICIDAD (ADR-044 §E bis, R4 #899):
        Dos índices únicos parciales sustituyen al UniqueConstraint simple de
        antes de R4 — Postgres no deduplica NULL en un índice multi-columna,
        así que hace falta uno específico para ese caso:
            uq_documentos_requisito_no_afectado (requisito_id, solicitud_id)
                WHERE reformado_id IS NULL — la vinculación de la versión
                inicial, o la única de un requisito no afectado por reformado.
            uq_documentos_requisito_por_version (requisito_id, solicitud_id,
                reformado_id) — una fila más por versión para un requisito
                afectado (RequisitoDocumental.afectado_por_reformado).
        Un requisito afectado puede tener así una fila NULL (versión inicial)
        y una fila por cada reformado en el que se pidió complementaria.

    EVALUACIÓN:
        Ver app/services/requisitos.py::evaluar_requisitos.
    """
    __tablename__ = 'documentos_requisito'
    __table_args__ = (
        db.Index(
            'uq_documentos_requisito_no_afectado', 'requisito_id', 'solicitud_id',
            unique=True, postgresql_where=db.text('reformado_id IS NULL'),
        ),
        db.Index(
            'uq_documentos_requisito_por_version',
            'requisito_id', 'solicitud_id', 'reformado_id',
            unique=True,
        ),
        db.Index('idx_documentos_requisito_requisito',  'requisito_id'),
        db.Index('idx_documentos_requisito_solicitud',  'solicitud_id'),
        db.Index('idx_documentos_requisito_documento',  'documento_id'),
        db.Index('idx_documentos_requisito_reformado',  'reformado_id'),
        {'schema': 'public'}
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado'
    )

    requisito_id = db.Column(
        db.Integer,
        db.ForeignKey('public.requisitos_documentales.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a requisitos_documentales'
    )

    solicitud_id = db.Column(
        db.Integer,
        db.ForeignKey('public.solicitudes.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a solicitudes — solicitud en la que se cubre el requisito'
    )

    documento_id = db.Column(
        db.Integer,
        db.ForeignKey('public.documentos.id'),
        nullable=False,
        comment='FK a documentos — documento del pool que satisface el requisito'
    )

    reformado_id = db.Column(
        db.Integer,
        db.ForeignKey('public.reformados_proyecto.id', ondelete='RESTRICT'),
        nullable=True,
        comment='FK a REFORMADOS_PROYECTO (ADR-044 §E bis, R4 #899). NULL = versión '
                'inicial, o único valor posible si el requisito no está afectado por '
                'reformado. ON DELETE RESTRICT: mismo criterio que fases.reformado_id, '
                'el corte no puede borrarse mientras una vinculación cuelgue de él.'
    )

    # Relaciones
    solicitud = db.relationship('Solicitud')
    documento = db.relationship('Documento')
    reformado = db.relationship(
        'ReformadoProyecto',
        backref=db.backref('documentos_requisito_cubiertos', passive_deletes=True),
    )

    def __repr__(self):
        return (
            f'<DocumentoRequisito id={self.id} '
            f'req={self.requisito_id} sol={self.solicitud_id} doc={self.documento_id}>'
        )
