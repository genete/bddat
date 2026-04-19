from app import db


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
        variables compilado por el ContextAssembler. AND implícito entre condiciones.
        Si todas se cumplen → aplica efecto. BLOQUEAR tiene prioridad sobre ADVERTIR.

    NORMA:
        norma_compilada es campo temporal hasta que se cree la tabla normas (paso 3).
        En paso 3 se añade norma_id FK + articulo + apartado y se elimina este campo.
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
    norma_compilada = db.Column(
        db.String(300), nullable=True,
        comment='Referencia normativa compilada (temporal hasta tabla normas en paso 3)'
    )
    prioridad = db.Column(
        db.Integer, nullable=False, default=0,
        comment='Orden entre reglas del mismo (accion, sujeto, tipo_sujeto_id)'
    )
    activa = db.Column(
        db.Boolean, nullable=False, default=True,
        comment='Desactivar en lugar de borrar — preserva trazabilidad'
    )

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
        db.Index('idx_condiciones_regla_variable', 'nombre_variable'),
        {'schema': 'public'}
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    regla_id = db.Column(
        db.Integer,
        db.ForeignKey('public.reglas_motor.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a REGLAS_MOTOR'
    )
    nombre_variable = db.Column(
        db.String(80), nullable=False,
        comment='Clave en el dict de variables del ContextAssembler'
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

    def __repr__(self):
        return f'<CondicionRegla id={self.id} regla={self.regla_id} {self.nombre_variable} {self.operador} {self.valor!r}>'


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
