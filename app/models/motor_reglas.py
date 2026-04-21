from app import db


class Norma(db.Model):
    """
    Norma legal de referencia para las reglas del motor.
    """
    __tablename__ = 'normas'
    __table_args__ = (
        db.Index('idx_normas_codigo', 'codigo', unique=True),
        {'schema': 'public'}
    )

    id      = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo  = db.Column(db.String(30),  unique=True, nullable=False,
                        comment='Clave interna: DL26_2021 | LPACAP | RD337_2014')
    titulo  = db.Column(db.String(300), nullable=False,
                        comment='Texto completo: "Decreto-ley 26/2021, de 14 de diciembre"')
    url_eli = db.Column(db.String(500), nullable=True,
                        comment='URL texto consolidado BOE/BOJA')

    def __repr__(self):
        return f'<Norma {self.codigo}>'


class CatalogoVariable(db.Model):
    """
    Registro de variables disponibles para el motor de reglas.

    Fuente de verdad compartida entre el Variable Registry (código) y la UI
    del Supervisor (dropdown). Solo las variables con activa=True aparecen
    en el formulario de alta de reglas.

    El ciclo de vida completo está descrito en
    docs/DISEÑO_CONTEXT_ASSEMBLER.md §Ciclo de vida de una variable.
    """
    __tablename__ = 'catalogo_variables'
    __table_args__ = (
        db.Index('idx_catalogo_variables_nombre', 'nombre', unique=True),
        {'schema': 'public'}
    )

    id        = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre    = db.Column(db.String(80),  unique=True, nullable=False,
                          comment='Clave del dict de variables: tension_nominal_kv')
    etiqueta  = db.Column(db.String(150), nullable=False,
                          comment='Texto legible para el Supervisor en el formulario')
    tipo_dato = db.Column(db.String(20),  nullable=False,
                          comment='boolean | numerico | texto | fecha | enum')
    norma_id  = db.Column(db.Integer, db.ForeignKey('public.normas.id'), nullable=True,
                          comment='Norma de origen principal de la variable')
    activa    = db.Column(db.Boolean, nullable=False, default=False,
                          comment='True solo cuando la función existe en el Variable Registry')

    norma = db.relationship('Norma')

    def __repr__(self):
        return f'<CatalogoVariable {self.nombre} activa={self.activa}>'


class ReglaMotor(db.Model):
    """
    Regla del motor de validación agnóstico.

    El motor evalúa si una acción sobre un sujeto ESFTT está permitida.
    Principio rector: todo permitido excepto lo expresamente prohibido.

    CAMPOS CLAVE:
        accion:         CREAR|INICIAR|FINALIZAR|BORRAR
        sujeto:         SOLICITUD|FASE|TRAMITE|TAREA|EXPEDIENTE
        tipo_sujeto_id: ID en tipos_* del sujeto. NULL = aplica a todos los tipos.
        efecto:         BLOQUEAR|ADVERTIR

    EVALUACIÓN:
        El motor carga las reglas activas para (accion, sujeto, tipo_sujeto_id).
        Para cada regla evalúa sus condiciones (CondicionRegla) contra el dict de
        variables compilado por el Variable Registry. AND implícito entre condiciones.
        Si todas se cumplen → aplica efecto. BLOQUEAR tiene prioridad sobre ADVERTIR.
    """
    __tablename__ = 'reglas_motor'
    __table_args__ = (
        db.CheckConstraint("accion IN ('CREAR','INICIAR','FINALIZAR','BORRAR')", name='ck_reglas_motor_accion'),
        db.CheckConstraint("sujeto IN ('SOLICITUD','FASE','TRAMITE','TAREA','EXPEDIENTE')", name='ck_reglas_motor_sujeto'),
        db.CheckConstraint("efecto IN ('BLOQUEAR','ADVERTIR')", name='ck_reglas_motor_efecto'),
        db.Index('idx_reglas_motor_lookup', 'accion', 'sujeto', 'tipo_sujeto_id'),
        {'schema': 'public'}
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    accion = db.Column(
        db.String(10), nullable=False,
        comment='Acción evaluada: CREAR | INICIAR | FINALIZAR | BORRAR'
    )
    sujeto = db.Column(
        db.String(20), nullable=False,
        comment='Sujeto sobre el que actúa: SOLICITUD | FASE | TRAMITE | TAREA | EXPEDIENTE'
    )
    tipo_sujeto_id = db.Column(
        db.Integer, nullable=True,
        comment='ID en tipos_* del sujeto. NULL = aplica a todos los tipos'
    )
    efecto = db.Column(
        db.String(10), nullable=False,
        comment='Efecto si se cumplen condiciones: BLOQUEAR | ADVERTIR'
    )
    norma_id = db.Column(
        db.Integer, db.ForeignKey('public.normas.id'), nullable=True,
        comment='FK a normas — norma legal de la regla'
    )
    articulo = db.Column(
        db.String(20), nullable=True,
        comment='Artículo exacto: "24.3" | "DA4" | "DF2"'
    )
    apartado = db.Column(
        db.String(20), nullable=True,
        comment='Sub-apartado si procede'
    )
    prioridad = db.Column(
        db.Integer, nullable=False, default=0,
        comment='Orden entre reglas del mismo (accion, sujeto, tipo_sujeto_id)'
    )
    activa = db.Column(
        db.Boolean, nullable=False, default=True,
        comment='Desactivar en lugar de borrar — preserva trazabilidad'
    )

    norma      = db.relationship('Norma')
    condiciones = db.relationship(
        'CondicionRegla',
        backref='regla',
        cascade='all, delete-orphan',
        order_by='CondicionRegla.orden'
    )

    def __repr__(self):
        return f'<ReglaMotor id={self.id} {self.accion}/{self.sujeto} tipo={self.tipo_sujeto_id} → {self.efecto}>'


class CondicionRegla(db.Model):
    """
    Condición individual de una ReglaMotor.

    Evalúa una variable del dict contra un valor de referencia con un operador.
    Todas las condiciones de la misma regla se combinan con AND implícito.
    Para expresar OR se crean reglas separadas.

    OPERADORES:
        EQ / NEQ            igual / distinto
        IN / NOT_IN         en el conjunto / fuera del conjunto
        IS_NULL / NOT_NULL  ausente / presente
        GT / GTE / LT / LTE comparaciones numéricas
        BETWEEN / NOT_BETWEEN  rango [a, b] — valor es lista [min, max]
    """
    __tablename__ = 'condiciones_regla'
    __table_args__ = (
        db.CheckConstraint(
            "operador IN ('EQ','NEQ','IN','NOT_IN','IS_NULL','NOT_NULL','GT','GTE','LT','LTE','BETWEEN','NOT_BETWEEN')",
            name='ck_condiciones_regla_operador'
        ),
        db.Index('idx_condiciones_regla_regla',    'regla_id'),
        db.Index('idx_condiciones_regla_variable', 'variable_id'),
        {'schema': 'public'}
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    regla_id = db.Column(
        db.Integer,
        db.ForeignKey('public.reglas_motor.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a reglas_motor'
    )
    variable_id = db.Column(
        db.Integer,
        db.ForeignKey('public.catalogo_variables.id'),
        nullable=False,
        comment='FK a catalogo_variables — variable evaluada'
    )
    operador = db.Column(
        db.String(20), nullable=False,
        comment='Operador de comparación (ver catálogo en docstring)'
    )
    valor = db.Column(
        db.JSON, nullable=True,
        comment='Valor de referencia. Lista para IN/BETWEEN, None para IS_NULL/NOT_NULL'
    )
    orden = db.Column(
        db.Integer, nullable=False, default=1,
        comment='Orden informativo dentro de la regla'
    )

    variable = db.relationship('CatalogoVariable')

    def __repr__(self):
        nombre = self.variable.nombre if self.variable else f'var_id={self.variable_id}'
        return f'<CondicionRegla id={self.id} regla={self.regla_id} {nombre} {self.operador} {self.valor!r}>'


class TipoSolicitudCompatible(db.Model):
    """
    Pares de tipos de solicitud que pueden coexistir en una misma solicitud.

    Whitelist de combinaciones válidas. Una solicitud puede tener múltiples
    tipos (N:M via SolicitudTipo) pero no todas las combinaciones son válidas.
    Ej: AAP+AAC es compatible; AAP+AAE NO lo es.

    CONSTRAINT tipo_a_id < tipo_b_id:
        Evita duplicados simétricos — al insertar, siempre el ID menor en tipo_a_id.
    """
    __tablename__ = 'tipos_solicitudes_compatibles'
    __table_args__ = (
        db.CheckConstraint('tipo_a_id < tipo_b_id', name='ck_compatibles_orden'),
        db.Index('idx_compatibles_tipo_a', 'tipo_a_id'),
        db.Index('idx_compatibles_tipo_b', 'tipo_b_id'),
        {'schema': 'public'}
    )

    tipo_a_id = db.Column(
        db.Integer, db.ForeignKey('tipos_solicitudes.id'),
        primary_key=True,
        comment='FK a TIPOS_SOLICITUDES. Siempre el ID menor del par'
    )
    tipo_b_id = db.Column(
        db.Integer, db.ForeignKey('tipos_solicitudes.id'),
        primary_key=True,
        comment='FK a TIPOS_SOLICITUDES. Siempre el ID mayor del par'
    )
    nota = db.Column(
        db.String(200), nullable=True,
        comment='Explicación de la compatibilidad / referencia normativa'
    )

    tipo_a = db.relationship('TipoSolicitud', foreign_keys=[tipo_a_id])
    tipo_b = db.relationship('TipoSolicitud', foreign_keys=[tipo_b_id])

    def __repr__(self):
        return f'<TipoSolicitudCompatible {self.tipo_a_id}↔{self.tipo_b_id}>'
