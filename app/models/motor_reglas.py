from app import db


class ReglaMotor(db.Model):
    """
    Regla del motor de validación de acciones sobre ESFTT.

    PROPÓSITO:
        Define qué está prohibido o requiere advertencia cuando el usuario
        intenta una acción (CREAR, CERRAR, BORRAR) sobre una entidad ESFTT.
        Principio rector: todo permitido excepto lo expresamente prohibido.

    CAMPO EVENTO:
        Acción que el usuario intenta realizar:
        - CREAR: crear una nueva entidad
        - CERRAR: cerrar/finalizar una entidad existente
        - BORRAR: eliminar una entidad existente

    CAMPO ENTIDAD:
        Tipo de entidad sobre la que actúa:
        - SOLICITUD: crear/cerrar/borrar una solicitud (cualquier tipo via solicitudes_tipos)
        - FASE, TRAMITE, TAREA: sobre las entidades correspondientes
        - EXPEDIENTE: borrar un expediente u otras acciones sobre él
        NOTA: SOLICITUD_TIPO no es una entidad del motor. El handler de SOLICITUD
        gestiona directamente la compatibilidad de tipos via TIPOS_SOLICITUDES_COMPATIBLES.
        La N:M de solicitudes_tipos es un detalle de implementación, no una entidad de negocio.

    CAMPO TIPO_ID:
        ID en la tabla tipos_* correspondiente según entidad:
        - entidad=FASE → tipos_fases.id
        - entidad=TRAMITE → tipos_tramites.id
        - entidad=TAREA → tipos_tareas.id
        - entidad=SOLICITUD_TIPO → tipos_solicitudes.id
        - entidad=EXPEDIENTE → tipos_expedientes.id
        - NULL = la regla aplica a todos los tipos de esa entidad
        Sin FK constraint (tabla referenciada varía según entidad).

    CAMPO ACCION:
        - BLOQUEAR: impide la acción. El usuario no puede continuar.
        - ADVERTIR: informa pero permite. El usuario puede continuar.

    CAMPO PARAMS_EXTRA:
        Nombre del parámetro adicional requerido para evaluar esta regla.
        Ej: 'organismo_id' para reglas de SEPARATAS.
        NULL si no se necesitan parámetros extra.

    EVALUACIÓN:
        El motor evalúa todas las CONDICIONES_REGLA asociadas (ver CondicionRegla).
        Si todas las condiciones activas se cumplen → aplica ACCION.
        Si alguna no se cumple → acción PERMITIDA (todo permitido excepto prohibido).

    RELACIONES:
        - condiciones ← CONDICIONES_REGLA.regla_id (condiciones de esta regla)
    """
    __tablename__ = 'reglas_motor'
    __table_args__ = (
        db.CheckConstraint("evento IN ('CREAR','INICIAR','FINALIZAR','BORRAR')", name='ck_reglas_motor_evento'),
        db.CheckConstraint(
            "entidad IN ('SOLICITUD','FASE','TRAMITE','TAREA','EXPEDIENTE')",
            name='ck_reglas_motor_entidad'
        ),
        db.CheckConstraint("accion IN ('BLOQUEAR','ADVERTIR')", name='ck_reglas_motor_accion'),
        db.Index('idx_reglas_motor_lookup', 'evento', 'entidad', 'tipo_id'),
        {'schema': 'public'}
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    evento = db.Column(
        db.String(10),
        nullable=False,
        comment='Acción evaluada: CREAR | CERRAR | BORRAR'
    )

    entidad = db.Column(
        db.String(20),
        nullable=False,
        comment='Entidad sobre la que actúa: SOLICITUD | FASE | TRAMITE | TAREA | EXPEDIENTE'
    )

    tipo_id = db.Column(
        db.Integer,
        nullable=True,
        comment='ID en la tabla tipos_* según entidad. NULL = aplica a todos los tipos'
    )

    accion = db.Column(
        db.String(10),
        nullable=False,
        comment='Acción si se cumplen condiciones: BLOQUEAR | ADVERTIR'
    )

    mensaje = db.Column(
        db.String(500),
        nullable=False,
        comment='Texto mostrado al usuario cuando se activa la regla'
    )

    norma = db.Column(
        db.String(200),
        nullable=True,
        comment='Referencia normativa (ej: "Decreto-ley 26/2021, DA 4ª")'
    )

    params_extra = db.Column(
        db.String(100),
        nullable=True,
        comment='Nombre del param adicional requerido por alguna condición (ej: organismo_id)'
    )

    activa = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        comment='Permite desactivar la regla sin borrarla'
    )

    # Relaciones
    condiciones = db.relationship(
        'CondicionRegla',
        backref='regla',
        cascade='all, delete-orphan',
        order_by='CondicionRegla.orden'
    )

    def __repr__(self):
        return f'<ReglaMotor id={self.id} {self.evento}/{self.entidad} tipo={self.tipo_id} → {self.accion}>'


class CondicionRegla(db.Model):
    """
    Condición individual que compone una ReglaMotor.

    PROPÓSITO:
        Cada regla tiene una o más condiciones. Si TODAS se cumplen (AND por defecto)
        → la regla se activa y se aplica su acción.
        Si alguna no se cumple → la regla no se activa → acción permitida.

    CAMPO TIPO_CRITERIO:
        Tipo de evaluación. Catálogo:
        - EXISTE_DOCUMENTO_TIPO    params: {tipo_doc_codigo, ambito}
        - EXISTE_DOC_ORGANISMO     params: {tipo_doc_codigo} + param organismo_id
        - EXISTE_FASE_CERRADA      params: {tipo_fase_codigo}
        - EXISTE_FASE_CON_RESULTADO  params: {tipo_fase_codigo, resultado_codigos:[]}
        - VARIABLE_EXPEDIENTE      params: {campo, operador, valor}
        - TIPO_FASE_PADRE_ES       params: {tipo_fase_codigo}
        - EXISTE_TAREA_TIPO        params: {tipo_tarea_codigo, cerrada, requiere_doc_producido}
        - EXISTE_TRAMITE_TIPO      params: {tipo_tramite_codigo, cerrado, requiere_doc_producido}
        - ESTADO_SOLICITUD         params: {estado}
        - EXISTE_TIPO_SOLICITUD    params: {tipo_solicitud_codigo}

    CAMPO NEGACION:
        Si TRUE, invierte el resultado de la condición.
        Ej: EXISTE_FASE_CERRADA con negacion=TRUE evalúa
        "NO existe fase cerrada" → TRUE si no hay fase cerrada.

    CAMPO OPERADOR_SIGUIENTE:
        Operador lógico con la siguiente condición de la misma regla.
        La última condición lo ignora. Por defecto AND.

    CAMPO PARAMETROS:
        JSON con los parámetros específicos del tipo_criterio.
        El evaluador los lee según el tipo_criterio declarado.
    """
    __tablename__ = 'condiciones_regla'
    __table_args__ = (
        db.CheckConstraint(
            "operador_siguiente IN ('AND','OR')",
            name='ck_condiciones_regla_operador'
        ),
        db.Index('idx_condiciones_regla_regla', 'regla_id'),
        db.Index('idx_condiciones_regla_criterio', 'tipo_criterio'),
        {'schema': 'public'}
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    regla_id = db.Column(
        db.Integer,
        db.ForeignKey('public.reglas_motor.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a REGLAS_MOTOR. Regla a la que pertenece esta condición'
    )

    tipo_criterio = db.Column(
        db.String(40),
        nullable=False,
        comment='Tipo de evaluación (ver catálogo en docstring)'
    )

    parametros = db.Column(
        db.JSON,
        nullable=False,
        comment='Parámetros JSON específicos del tipo_criterio'
    )

    negacion = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment='Si TRUE, invierte el resultado de esta condición (NOT)'
    )

    orden = db.Column(
        db.Integer,
        nullable=False,
        default=1,
        comment='Orden de evaluación dentro de la regla (informativo)'
    )

    operador_siguiente = db.Column(
        db.String(5),
        nullable=False,
        default='AND',
        comment='Operador lógico con la siguiente condición: AND | OR'
    )

    def __repr__(self):
        neg = 'NOT ' if self.negacion else ''
        return f'<CondicionRegla id={self.id} regla={self.regla_id} {neg}{self.tipo_criterio}>'


class TipoSolicitudCompatible(db.Model):
    """
    Pares de tipos de solicitud que pueden coexistir en una misma solicitud.

    PROPÓSITO:
        Whitelist de combinaciones válidas. Una solicitud puede tener múltiples
        tipos (N:M via SolicitudTipo) pero no todas las combinaciones son válidas.
        Ej: AAP+AAC es compatible; AAP+AAE NO lo es.

    DISEÑO:
        Whitelist (pares permitidos), no blacklist (pares prohibidos).
        Justificación: la mayoría de los 136 pares posibles (17 tipos) son inválidos.
        Definir los ~16 válidos es más seguro y legible.

    CONSTRAINT tipo_a_id < tipo_b_id:
        Evita duplicados simétricos: el par (AAP,AAC) y (AAC,AAP) son el mismo.
        Al insertar, siempre poner el ID menor en tipo_a_id.

    EVALUACIÓN:
        Al añadir un tipo T a una solicitud que ya tiene tipos T1, T2...:
        Verificar que existe registro compatible para cada par (T, Ti).
        Si algún par no está en la tabla → acción bloqueada.
    """
    __tablename__ = 'tipos_solicitudes_compatibles'
    __table_args__ = (
        db.CheckConstraint('tipo_a_id < tipo_b_id', name='ck_compatibles_orden'),
        db.Index('idx_compatibles_tipo_a', 'tipo_a_id'),
        db.Index('idx_compatibles_tipo_b', 'tipo_b_id'),
        {'schema': 'public'}
    )

    tipo_a_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_solicitudes.id'),
        primary_key=True,
        comment='FK a TIPOS_SOLICITUDES. Siempre el ID menor del par'
    )

    tipo_b_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_solicitudes.id'),
        primary_key=True,
        comment='FK a TIPOS_SOLICITUDES. Siempre el ID mayor del par'
    )

    nota = db.Column(
        db.String(200),
        nullable=True,
        comment='Explicación de la compatibilidad / referencia normativa'
    )

    # Relaciones
    tipo_a = db.relationship('TipoSolicitud', foreign_keys=[tipo_a_id])
    tipo_b = db.relationship('TipoSolicitud', foreign_keys=[tipo_b_id])

    def __repr__(self):
        return f'<TipoSolicitudCompatible {self.tipo_a_id}↔{self.tipo_b_id}>'
