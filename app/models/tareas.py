from app import db

class Tarea(db.Model):
    """
    Unidad de trabajo registrable con entrada/salida documental.

    PROPÓSITO:
        Representa operaciones atómicas (analizar, elaborar, notificar,
        esperar plazo) que se realizan dentro de un trámite. Son las unidades
        mínimas de trabajo con entrada/salida documental clara.

    FILOSOFÍA:
        - Unidad de trabajo registrable con entrada/salida clara
        - Relación unidireccional: TAREA → DOCUMENTO (no al revés)
        - Documento agnóstico: el documento no sabe de tareas
        - Los vínculos a documentos viven en la tabla DOCUMENTOS_TAREA con un
          campo `rol` (CONSUMIDO | PRODUCIDO), no en FK propias (ADR-010, #420)
        - Un documento, un productor: solo una tarea puede producir un documento
        - Un documento, múltiples consumidores: varias tareas pueden usarlo

    CAMPO TRAMITE_ID:
        - NOT NULL: toda tarea pertenece a un trámite
        - FK a TRAMITES (public schema)

    CAMPO TIPO_TAREA_ID:
        - NOT NULL: define qué tipo de tarea atómica es
        - FK a TIPOS_TAREAS (public schema)
        - 4 tipos posibles: ANALIZAR, ELABORAR, NOTIFICAR, ESPERAR_PLAZO

    VÍNCULOS DOCUMENTALES (vía DOCUMENTOS_TAREA):
        - Documentos consumidos: 0..N por tarea (rol CONSUMIDO)
        - Documento producido: 0..1 por tarea (rol PRODUCIDO)

    CAMPO NOTAS:
        - Campo libre para información adicional
        - ESPERAR_PLAZO: el plazo NO vive aquí — viene de `catalogo_plazos` por
          tipo de trámite.

    SEMÁNTICA SEGÚN TIPO:
        - ANALIZAR:      consume 1..N (documentos analizados), produce 1 (DIAGNOSTICO)
        - ELABORAR:      consume 0..N (DIAGNOSTICO de ANALIZAR previo), produce 1
        - NOTIFICAR:     consume 1..N (documentos notificados), produce 1 (justificante)
        - ESPERAR_PLAZO: consume 0..1 (justificante que inicia el cómputo),
                         produce 0..1 (CERT_PLAZO_CUMPLIDO — Caso B — o doc externo — Caso A)

    RELACIONES:
        - tramite → TRAMITES.id (FK CASCADE, trámite contenedor)
        - tipo_tarea → TIPOS_TAREAS.id (FK, tipo atómico)
        - vinculos_documento ← DOCUMENTOS_TAREA (vínculos con rol)

    REGLAS DE NEGOCIO:
        - Los documentos vinculados deben pertenecer al mismo expediente
        - Unicidad "un documento, un productor" garantizada en DOCUMENTOS_TAREA
        - Sin campos de fecha propios: ver §2.bis DISEÑO_FECHAS_PLAZOS.md
    """
    __tablename__ = 'tareas'
    __table_args__ = (
        db.Index('idx_tareas_tramite', 'tramite_id'),
        db.Index('idx_tareas_tipo', 'tipo_tarea_id'),
        {'schema': 'public'}
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado de la tarea'
    )

    tramite_id = db.Column(
        db.Integer,
        db.ForeignKey('public.tramites.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a TRAMITES. Trámite al que pertenece la tarea'
    )

    tipo_tarea_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_tareas.id'),
        nullable=False,
        comment='FK a TIPOS_TAREAS. Tipo de tarea atómica (4 tipos posibles)'
    )

    notas = db.Column(
        db.String(2000),
        nullable=True,
        comment='Observaciones o información adicional (referencia publicación, remitente, etc.). NO usar para plazos — viven en catalogo_plazos.'
    )

    # Relaciones
    tramite = db.relationship('Tramite', backref='tareas')
    tipo_tarea = db.relationship('TipoTarea', backref='tareas_instanciadas')
    vinculos_documento = db.relationship(
        'DocumentoTarea',
        back_populates='tarea',
        cascade='all, delete-orphan',
        order_by='DocumentoTarea.id',
    )

    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<Tarea id={self.id} tipo={self.tipo_tarea_id} tramite={self.tramite_id}>'

    def __str__(self):
        """Representación legible para interfaz."""
        return f'Tarea {self.id} - {self.tipo_tarea.nombre if self.tipo_tarea else "Sin tipo"}'

    # --- Accesores documentales (vía DOCUMENTOS_TAREA) ---

    @property
    def documentos_consumidos(self):
        """Lista de documentos de entrada de la tarea (rol CONSUMIDO)."""
        return [v.documento for v in self.vinculos_documento if v.rol == 'CONSUMIDO']

    @property
    def documento_producido(self):
        """Documento de salida de la tarea (rol PRODUCIDO), o None."""
        for v in self.vinculos_documento:
            if v.rol == 'PRODUCIDO':
                return v.documento
        return None

    # --- Estados deducibles ---
    # La completitud se deduce de documentos, no de campos de fecha.

    @property
    def ejecutada(self):
        """True si la tarea está completa (tiene documento producido)."""
        return any(v.rol == 'PRODUCIDO' for v in self.vinculos_documento)

    @property
    def planificada(self):
        """True si la tarea no tiene ningún documento vinculado aún."""
        return len(self.vinculos_documento) == 0

    @property
    def en_curso(self):
        """True si la tarea tiene documentos de entrada pero no ha producido salida."""
        return not self.planificada and not self.ejecutada

    @property
    def ejecutada_con_doc(self):
        """Alias de ejecutada — idéntico desde que la completitud se deduce del documento."""
        return self.ejecutada

    @property
    def resultado(self):
        """Resultado de la notificación: CORRECTA | INCORRECTA | None.

        Solo aplica a tareas NOTIFICAR. Lee de notificaciones por tarea_id, no
        por documento (ADR-034, #657/#658 — corrige ADR-008): la fila puede
        existir sin documento producido (camino A, "Registrar envío") o con
        documento pero sin resultado aún. None = sin fila, o fila sin
        resultado registrado (pendiente del justificante definitivo).
        """
        notif = self.notificacion
        return notif.resultado if notif else None

    @property
    def estado(self):
        """Estado de la tarea: PLANIFICADA | EN_CURSO | EJECUTADA."""
        if self.planificada:
            return 'PLANIFICADA'
        if self.ejecutada:
            return 'EJECUTADA'
        return 'EN_CURSO'
