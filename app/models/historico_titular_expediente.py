from app import db
from datetime import datetime

class HistoricoTitularExpediente(db.Model):
    """
    Histórico de cambios de titularidad de expedientes.
    
    PROPÓSITO:
        Registra todos los cambios de titular de un expediente a lo largo del tiempo,
        manteniendo trazabilidad completa de la cadena de titularidad desde el origen.
    
    FILOSOFÍA:
        - Tabla de auditoría inmutable (solo INSERT, nunca UPDATE/DELETE)
        - Un expediente puede tener múltiples titulares a lo largo del tiempo
        - Solo un registro puede tener FECHA_HASTA = NULL (titular actual)
        - EXPEDIENTES.TITULAR_ID es snapshot desnormalizado (rendimiento)
        - Esta tabla es la fuente de verdad del histórico
        - TIMESTAMP permite múltiples cambios el mismo día (corrección errores)
    
    USO TÍPICO:
        1. Al crear expediente:
           - Se crea registro INICIAL con fecha_desde = datetime.now()
           - FECHA_HASTA = NULL (titular actual)
           - EXPEDIENTES.TITULAR_ID = titular inicial
        
        2. Al cambiar titular (aprobación solicitud cambio titularidad):
           - UPDATE registro actual: fecha_hasta = datetime.now()
           - INSERT nuevo registro: fecha_desde = datetime.now(), fecha_hasta = NULL
           - UPDATE EXPEDIENTES: titular_id = nuevo titular
        
        3. Consultar histórico:
           - WHERE expediente_id = X ORDER BY fecha_desde
           - Muestra cadena completa de titularidad
    
    CAMPOS ESPECIALES:
        FECHA_DESDE / FECHA_HASTA:
            - TIMESTAMP (no DATE) para permitir múltiples cambios el mismo día
            - Casos de uso:
              * Corrección inmediata de errores
              * Múltiples cambios en proceso de regularización
              * Auditoría precisa con hora exacta
            - FECHA_HASTA = NULL indica titular actual vigente
        
        MOTIVO:
            - INICIAL: Primer titular del expediente
            - VENTA: Compraventa de instalación
            - HERENCIA: Transmisión mortis causa
            - FUSION: Absorción/fusión empresarial
            - ESCISION: División empresarial
            - CAMBIO_TITULAR: Genérico cuando se aprueba solicitud
            - OTRO: Otros motivos (especificar en OBSERVACIONES)
        
        SOLICITUD_CAMBIO_ID:
            - NULL para registro INICIAL (no hay solicitud)
            - NOT NULL para cambios posteriores (rastrear acto administrativo)
    
    RELACIONES:
        - expediente → EXPEDIENTES (el expediente afectado)
        - titular → ENTIDADES (titular en este periodo)
        - solicitud_cambio → SOLICITUDES (acto que motivó el cambio, nullable)
    
    CONSTRAINTS:
        1. UQ_EXPEDIENTE_TITULAR_DESDE: Solo un registro por expediente+fecha_desde (timestamp)
        2. CHK_VIGENCIA_TITULAR: fecha_hasta >= fecha_desde (cuando no es NULL)
        3. IMPLÍCITO: Solo un registro con fecha_hasta = NULL por expediente
           (se gestiona mediante lógica de negocio, no constraint DB)
    
    REGLAS DE NEGOCIO:
        1. El primer registro debe tener motivo = 'INICIAL'
        2. Registros posteriores deben tener solicitud_cambio_id
        3. Al insertar nuevo titular actual:
           - Actualizar registro anterior: fecha_hasta = datetime.now()
           - Insertar nuevo registro: fecha_hasta = NULL
           - Actualizar expedientes.titular_id
        4. No se permite borrar registros (auditoría inmutable)
        5. TIMESTAMP permite corrección inmediata de errores el mismo día
    
    MÉTODOS:
        - titular_actual(expediente_id): Obtiene registro vigente
        - registrar_cambio(expediente_id, nuevo_titular_id, motivo, ...): 
          Cierra registro actual y crea uno nuevo
    
    NOTAS DE VERSIÓN:
        v3.2: Creación inicial de la tabla (Issue #64)
        v3.3: Cambio Date → DateTime para permitir múltiples cambios/día
    """
    __tablename__ = 'historico_titulares_expediente'
    __table_args__ = (
        db.UniqueConstraint(
            'expediente_id', 'fecha_desde',
            name='uq_expediente_titular_desde'
        ),
        db.CheckConstraint(
            'fecha_hasta IS NULL OR fecha_hasta >= fecha_desde',
            name='chk_vigencia_titular'
        ),
        db.Index('idx_historico_titular_expediente', 'expediente_id'),
        db.Index('idx_historico_titular_titular', 'titular_id'),
        db.Index('idx_historico_titular_vigencia', 'fecha_hasta'),
        {'schema': 'public'}
    )
    
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador técnico único autogenerado'
    )
    
    expediente_id = db.Column(
        db.Integer,
        db.ForeignKey('public.expedientes.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a EXPEDIENTES. Expediente cuya titularidad cambia'
    )
    
    titular_id = db.Column(
        db.Integer,
        db.ForeignKey('public.entidades.id'),
        nullable=False,
        comment='FK a ENTIDADES. Titular durante este periodo de vigencia'
    )
    
    fecha_desde = db.Column(
        db.DateTime,  # ← CAMBIO: Date → DateTime
        nullable=False,
        comment='Timestamp inicio vigencia. TIMESTAMP permite múltiples cambios/día para corrección de errores'
    )
    
    fecha_hasta = db.Column(
        db.DateTime,  # ← CAMBIO: Date → DateTime
        nullable=True,
        comment='Timestamp fin vigencia. NULL = titular actual vigente. NOT NULL = titular histórico'
    )
    
    solicitud_cambio_id = db.Column(
        db.Integer,
        db.ForeignKey('public.solicitudes.id'),
        nullable=True,
        comment='FK a SOLICITUDES. Solicitud que motivó el cambio de titularidad. NULL para registro INICIAL'
    )
    
    motivo = db.Column(
        db.String(50),
        nullable=True,
        comment='Motivo del cambio: INICIAL, VENTA, HERENCIA, FUSION, ESCISION, CAMBIO_TITULAR, OTRO'
    )
    
    observaciones = db.Column(
        db.Text,
        nullable=True,
        comment='Observaciones adicionales sobre el cambio de titularidad'
    )
    
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        nullable=False,
        comment='Timestamp de creación del registro (auditoría)'
    )
    
    # Relaciones SQLAlchemy
    expediente = db.relationship(
        'Expediente',
        foreign_keys=[expediente_id],
        backref='historico_titulares'
    )
    
    titular = db.relationship(
        'Entidad',
        foreign_keys=[titular_id],
        backref='historico_como_titular'
    )
    
    solicitud_cambio = db.relationship(
        'Solicitud',
        foreign_keys=[solicitud_cambio_id],
        backref='cambios_titularidad'
    )
    
    @staticmethod
    def titular_actual(expediente_id):
        """
        Obtiene el registro del titular actual vigente de un expediente.
        
        Args:
            expediente_id (int): ID del expediente
        
        Returns:
            HistoricoTitularExpediente: Registro vigente (fecha_hasta = NULL)
            None: Si no hay titular actual (situación anómala)
        
        Ejemplo:
            >>> registro = HistoricoTitularExpediente.titular_actual(expediente_id=42)
            >>> if registro:
            >>>     print(f"Titular actual: {registro.titular.nombre_completo}")
            >>>     print(f"Desde: {registro.fecha_desde}")
        """
        return HistoricoTitularExpediente.query.filter_by(
            expediente_id=expediente_id,
            fecha_hasta=None
        ).first()
    
    @staticmethod
    def registrar_cambio(expediente_id, nuevo_titular_id, fecha_cambio, 
                         motivo, solicitud_cambio_id=None, observaciones=None):
        """
        Registra un cambio de titularidad:
        1. Cierra el registro actual (fecha_hasta = fecha_cambio)
        2. Crea nuevo registro vigente (fecha_hasta = NULL)
        3. Actualiza expedientes.titular_id
        
        Args:
            expediente_id (int): ID del expediente
            nuevo_titular_id (int): ID del nuevo titular
            fecha_cambio (datetime): Timestamp efectivo del cambio
            motivo (str): VENTA, HERENCIA, FUSION, ESCISION, CAMBIO_TITULAR, OTRO
            solicitud_cambio_id (int, optional): ID de la solicitud que motivó el cambio
            observaciones (str, optional): Observaciones adicionales
        
        Returns:
            HistoricoTitularExpediente: Nuevo registro creado
        
        Raises:
            ValueError: Si no existe titular actual o fecha inválida
        
        Ejemplo:
            >>> from datetime import datetime
            >>> nuevo_registro = HistoricoTitularExpediente.registrar_cambio(
            ...     expediente_id=42,
            ...     nuevo_titular_id=15,
            ...     fecha_cambio=datetime.now(),
            ...     motivo='VENTA',
            ...     solicitud_cambio_id=120,
            ...     observaciones='Venta de instalación según escritura pública'
            ... )
            >>> db.session.commit()
        """
        from app.models.expedientes import Expediente
        
        # 1. Obtener registro actual
        registro_actual = HistoricoTitularExpediente.titular_actual(expediente_id)
        if not registro_actual:
            raise ValueError(f"No existe titular actual para expediente {expediente_id}")
        
        # 2. Validar fecha
        if fecha_cambio < registro_actual.fecha_desde:
            raise ValueError(
                f"Fecha cambio ({fecha_cambio}) anterior a fecha inicio vigencia actual "
                f"({registro_actual.fecha_desde})"
            )
        
        # 3. Cerrar registro actual
        registro_actual.fecha_hasta = fecha_cambio
        
        # 4. Crear nuevo registro vigente
        nuevo_registro = HistoricoTitularExpediente(
            expediente_id=expediente_id,
            titular_id=nuevo_titular_id,
            fecha_desde=fecha_cambio,
            fecha_hasta=None,  # Vigente actual
            solicitud_cambio_id=solicitud_cambio_id,
            motivo=motivo,
            observaciones=observaciones
        )
        db.session.add(nuevo_registro)
        
        # 5. Actualizar snapshot en expedientes
        expediente = Expediente.query.get(expediente_id)
        expediente.titular_id = nuevo_titular_id
        
        return nuevo_registro
    
    @staticmethod
    def crear_inicial(expediente_id, titular_id, fecha_desde, observaciones=None):
        """
        Crea el registro INICIAL del primer titular de un expediente.
        
        Args:
            expediente_id (int): ID del expediente
            titular_id (int): ID del titular inicial
            fecha_desde (datetime): Timestamp de inicio (típicamente datetime.now())
            observaciones (str, optional): Observaciones adicionales
        
        Returns:
            HistoricoTitularExpediente: Registro inicial creado
        
        Ejemplo:
            >>> from datetime import datetime
            >>> registro_inicial = HistoricoTitularExpediente.crear_inicial(
            ...     expediente_id=42,
            ...     titular_id=10,
            ...     fecha_desde=datetime.now(),
            ...     observaciones='Titular original del expediente'
            ... )
            >>> db.session.add(registro_inicial)
            >>> db.session.commit()
        """
        registro = HistoricoTitularExpediente(
            expediente_id=expediente_id,
            titular_id=titular_id,
            fecha_desde=fecha_desde,
            fecha_hasta=None,  # Vigente actual
            solicitud_cambio_id=None,  # No hay solicitud para registro inicial
            motivo='INICIAL',
            observaciones=observaciones
        )
        return registro
    
    def __repr__(self):
        """Representación técnica para debugging."""
        vigencia = f"{self.fecha_desde} - {self.fecha_hasta or 'actual'}"
        return f'<HistoricoTitularExpediente expediente={self.expediente_id} titular={self.titular_id} vigencia={vigencia}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        if self.fecha_hasta:
            return f'Titular {self.titular_id} ({self.fecha_desde.date()} - {self.fecha_hasta.date()})'
        else:
            return f'Titular actual {self.titular_id} (desde {self.fecha_desde.date()})'
