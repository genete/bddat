from app import db


class ItemTecnico(db.Model):
    """
    Catálogo de ítems técnicos: apartados de contenido exigidos dentro del proyecto.

    A diferencia de RequisitoDocumental (verifica que un DOCUMENTO completo se haya
    aportado), cada fila aquí representa un APARTADO de contenido técnico dentro del
    proyecto (memoria, anejo de cálculos, planos, estudio de seguridad y salud...)
    exigido por RD 223/2008 (líneas AT) o RD 337/2014 (instalaciones AT). El técnico
    contrasta el proyecto contra este catálogo durante la tarea ANALIZAR.

    CONDICIONES DE APLICACIÓN:
        Mismo mecanismo que RequisitoDocumental/CondicionRequisito: un ítem es
        aplicable si se cumplen TODAS sus condiciones (tabla condiciones_item_tecnico,
        AND implícito). Un ítem sin condiciones es universal.

    CAMPO DESCRIPCION:
        Texto libre que rellena el Supervisor con el apartado exigido por la norma.
        No hay catálogo cerrado de tipos de apartado (a diferencia del
        tipo_documento_id de RequisitoDocumental) — el contenido técnico de un
        proyecto no se deja enumerar en un catálogo cerrado de antemano.

    RELACIONES:
        condiciones → CONDICIONES_ITEM_TECNICO (todas las condiciones de este ítem)
        usos       → COBERTURAS_ITEM_TECNICO (verificaciones del tramitador por solicitud)
        norma      → NORMAS

    INTEGRACIÓN (#594):
        condiciones_item_tecnico.variable_id solo referencia catalogo_variables — nunca
        activo_red/envolvente directamente. Esa indirección mantiene este catálogo
        desacoplado de cómo #591/#592 calculen aplica_rd223_2008/aplica_rd337_2014.
    """
    __tablename__ = 'items_tecnicos'
    __table_args__ = (
        {'schema': 'public'}
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado'
    )

    descripcion = db.Column(
        db.Text,
        nullable=False,
        comment='Apartado de contenido técnico exigido, texto libre (ej. "Anejo de cálculo de redes de tierra")'
    )

    norma_id = db.Column(
        db.Integer,
        db.ForeignKey('public.normas.id'),
        nullable=True,
        comment='FK a normas — norma que establece este ítem'
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
                'Las coberturas ya registradas se conservan aunque el ítem se '
                'desactive — evita huérfanos al reconstruir histórico.'
    )

    # Relaciones
    norma       = db.relationship('Norma')
    condiciones = db.relationship(
        'CondicionItemTecnico',
        backref='item_tecnico',
        cascade='all, delete-orphan',
        order_by='CondicionItemTecnico.orden',
    )
    usos = db.relationship(
        'CoberturaItemTecnico',
        backref='item_tecnico',
        cascade='all, delete-orphan',
    )

    def __repr__(self):
        return f'<ItemTecnico id={self.id} descripcion={self.descripcion[:40]!r}>'


class CondicionItemTecnico(db.Model):
    """
    Condición individual de un ItemTecnico.

    Gemela exacta de CondicionRequisito — misma semántica, mismos operadores,
    mismo AND implícito entre condiciones del mismo ítem.

    OPERADORES SOPORTADOS (paridad con CondicionRegla, #660):
        EQ / NEQ            igual / distinto
        IN / NOT_IN         en el conjunto / fuera del conjunto
        IS_NULL / NOT_NULL  ausente / presente
        GT / GTE / LT / LTE comparaciones numéricas
        BETWEEN / NOT_BETWEEN  rango [a, b] — valor es lista [min, max]
    """
    __tablename__ = 'condiciones_item_tecnico'
    __table_args__ = (
        db.CheckConstraint(
            "operador IN ('EQ','NEQ','IN','NOT_IN','IS_NULL','NOT_NULL',"
            "'GT','GTE','LT','LTE','BETWEEN','NOT_BETWEEN')",
            name='ck_condiciones_item_tecnico_operador'
        ),
        db.Index('idx_condiciones_item_tecnico_item', 'item_tecnico_id'),
        db.Index('idx_condiciones_item_tecnico_variable', 'variable_id'),
        {'schema': 'public'}
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado'
    )

    item_tecnico_id = db.Column(
        db.Integer,
        db.ForeignKey('public.items_tecnicos.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a items_tecnicos'
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
        comment='Orden informativo dentro del ítem (presentación en UI)'
    )

    variable = db.relationship('CatalogoVariable')

    def __repr__(self):
        nombre = self.variable.nombre if self.variable else f'var_id={self.variable_id}'
        return (
            f'<CondicionItemTecnico id={self.id} item={self.item_tecnico_id} '
            f'{nombre} {self.operador} {self.valor!r}>'
        )


class CoberturaItemTecnico(db.Model):
    """
    Verificación de un ItemTecnico contra el contenido del proyecto, por solicitud.

    El técnico, durante la tarea ANALIZAR, contrasta el proyecto con cada ítem
    técnico aplicable y registra el resultado. A diferencia de DocumentoRequisito
    (vincula un documento_id concreto), aquí no se indexa contra un documento —
    DocumentoProyecto.tipo='ANEXO' es plano (no distingue Anexo I de Anexo II), así
    que una FK no aportaría precisión real frente a una referencia en texto libre.

    MÁQUINA DE ESTADOS (2 campos, 3 estados reales — #594):
        Sin fila            → NO REVISADO (pendiente; estado por defecto, sin fila)
        texto='' , cubierto=False → NO REVISADO (equivalente explícito)
        texto='' , cubierto=True  → inválido: la UI deshabilita el checkbox mientras
                                     texto esté vacío, este estado no debe alcanzarse
        texto=X  , cubierto=False → DESFAVORABLE (revisado, no cumple; X explica dónde
                                     se buscó y por qué no está)
        texto=X  , cubierto=True  → FAVORABLE (revisado, cumple; X indica la ubicación,
                                     ej. "apartado 3.5 del anexo II")

    UNICIDAD:
        (item_tecnico_id, solicitud_id) — un ítem queda verificado exactamente una
        vez por solicitud (mismo criterio que DocumentoRequisito: el contenido del
        proyecto puede evolucionar entre solicitudes vía DocumentoProyecto
        MODIFICADO/REFUNDIDO, así que la verificación no se comparte a nivel de
        proyecto/expediente).
    """
    __tablename__ = 'coberturas_item_tecnico'
    __table_args__ = (
        db.UniqueConstraint(
            'item_tecnico_id', 'solicitud_id',
            name='uq_coberturas_item_tecnico_item_sol'
        ),
        db.Index('idx_coberturas_item_tecnico_item', 'item_tecnico_id'),
        db.Index('idx_coberturas_item_tecnico_solicitud', 'solicitud_id'),
        {'schema': 'public'}
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado'
    )

    item_tecnico_id = db.Column(
        db.Integer,
        db.ForeignKey('public.items_tecnicos.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a items_tecnicos'
    )

    solicitud_id = db.Column(
        db.Integer,
        db.ForeignKey('public.solicitudes.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a solicitudes — solicitud en la que se verifica el ítem'
    )

    texto = db.Column(
        db.Text,
        nullable=True,
        comment='Ubicación/justificación en lenguaje natural rellenada por el '
                'tramitador al contrastar, ej. "apartado 3.5 del anexo II". '
                'Vacío = no revisado.'
    )

    cubierto = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=db.text('false'),
        comment='Veredicto de cumplimiento. Solo tiene sentido junto a texto '
                'relleno — ver máquina de estados en el docstring de la clase.'
    )

    # Relaciones
    solicitud = db.relationship('Solicitud')

    def __repr__(self):
        return (
            f'<CoberturaItemTecnico id={self.id} '
            f'item={self.item_tecnico_id} sol={self.solicitud_id} cubierto={self.cubierto}>'
        )
