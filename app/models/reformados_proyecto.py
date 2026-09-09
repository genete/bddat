from app import db


# Origen del reformado (ADR-044 §C): los dos supuestos de la LPACAP por los que un
# proyecto cambia durante la instrucción. No es catálogo administrable —son la
# norma—, así que van en un CHECK, igual que `via` en organismos_expediente. El
# `tipo` de la tabla que esta sustituye era un varchar libre sin CHECK, y esa fue
# una de las razones de retirarla.
ORIGENES_REFORMADO = (
    'VOLUNTARIO',   # art. 76.1 LPACAP: lo aporta el interesado por su cuenta
    'REQUERIDO',    # art. 68.3 LPACAP: lo recaba el órgano, con acta sucinta al procedimiento
)


class ReformadoProyecto(db.Model):
    """
    Un corte en la línea temporal de los DOC_PROYECTO del expediente (ADR-044 §C).

    QUÉ ES UNA VERSIÓN:
        No es una entidad: es el tramo documental entre dos cortes. La versión
        inicial es todo lo anterior al primer reformado; la versión N, lo que va
        del reformado N al siguiente. Así un proyecto que llega en varios ficheros
        —tomo I, tomo II, planos— cae en su tramo sin clasificación propia.

    QUÉ ES UN REFORMADO:
        El documento que cambia el proyecto con entidad suficiente para obligar a
        rehacer fases preceptivas. El reformado **es** ese documento, con el patrón
        de anclas documentales de ADR-041 §D bis: «este documento obliga a rehacer
        fases» no necesita booleano que el técnico pueda contradecir ni literal
        hardcodeado — la fila existe o no existe.

        El proyecto original NO tiene fila aquí: ya está representado en PROYECTOS
        (título, fecha técnica, descripción, emplazamiento). Esta tabla no parte en
        dos algo simétrico, rellena el hueco que faltaba.

    LO QUE NO LLEVA, Y POR QUÉ:
        - orden / número de reformado: se deriva de
          ORDER BY documentos.fecha_administrativa, id (la fecha es obligatoria
          para DOC_PROYECTO precisamente por esto).
        - etiqueta: se compone — «REFORMADO DE PROYECTO de fecha 12/03/2026».
        - observaciones: ya están en DOCUMENTOS.
        - quién lo declaró y cuándo: es un acto con consecuencias, y su sitio es la
          bitácora.

    ALTA Y REVERSIÓN:
        Puerta única: la ingesta en el pool. Al entrar un DOC_PROYECTO el sistema
        pregunta si produce reformado (por defecto no). No hay CRUD manual de esta
        tabla, y la reversión alcanza solo al último corte.

    RELACIONES:
        - documento → DOCUMENTOS.id (FK UNIQUE): el ancla. El backref
          `Documento.reformado_proyecto` lo consulta la guarda del pool, que se
          construye solo con backrefs a propósito (#838).
    """
    __tablename__ = 'reformados_proyecto'
    __table_args__ = (
        db.CheckConstraint(
            "origen IN ('VOLUNTARIO', 'REQUERIDO')",
            name='ck_reformado_origen',
        ),
        {'schema': 'public'},
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    documento_id = db.Column(
        db.Integer,
        db.ForeignKey('public.documentos.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
        comment='FK UNIQUE a DOCUMENTOS. El documento que abre la versión; un documento no abre dos cortes',
    )

    origen = db.Column(
        db.String(20),
        nullable=False,
        comment='VOLUNTARIO (art. 76.1 LPACAP) o REQUERIDO por la Administración (art. 68.3)',
    )

    documento = db.relationship(
        'Documento',
        backref=db.backref('reformado_proyecto', uselist=False),
    )

    def __repr__(self):
        return f'<ReformadoProyecto doc={self.documento_id} origen={self.origen}>'

    def __str__(self):
        """Lo que leen los organismos en el oficio de consulta."""
        fecha = self.documento.fecha_administrativa if self.documento else None
        return f'REFORMADO DE PROYECTO de fecha {fecha.strftime("%d/%m/%Y")}' if fecha \
            else 'REFORMADO DE PROYECTO'
