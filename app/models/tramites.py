from app import db

class Tramite(db.Model):
    """
    Contenedor organizativo de tareas dentro de una fase.

    PROPÓSITO:
        Representa actuaciones administrativas concretas (solicitud de informe,
        anuncio BOP, recepción de alegación, etc.) realizadas durante una fase.
        Agrupa tareas atómicas bajo un patrón procedimental.

    FILOSOFÍA:
        - Contenedor organizativo de tareas
        - Estructura mínima: Solo tipo y observaciones
        - Semántica en TIPO: Patrones de tareas viven en TIPOS_TRAMITES
        - Sin documentos ni fechas propios: ambos viven en las tareas hijas
        - Sin campos de fecha propios: ver §2.bis DISEÑO_FECHAS_PLAZOS.md

    CAMPO FASE_ID:
        - NOT NULL: Todo trámite pertenece a una fase
        - FK a FASES (public schema)

    CAMPO TIPO_TRAMITE_ID:
        - NOT NULL: Define qué tipo de trámite es
        - FK a TIPOS_TRAMITES (estructura schema)
        - Determina patrón de tareas obligatorias

    ESTADOS DEDUCIBLES (properties, no columna):
        - PLANIFICADO: len(tareas) == 0
        - EN_CURSO: tareas presentes, no todas finalizadas
        - FINALIZADO: todas las tareas con tipos documentales tienen documento_producido_id
                      ESPERAR_PLAZO requiere evaluación adicional via plazos.py
                      (ver §4.1 DISEÑO_FECHAS_PLAZOS.md)

    RELACIONES:
        - fase → FASES.id (FK CASCADE, fase contenedora)
        - tipo_tramite → TIPOS_TRAMITES.id (FK, definición del trámite)
        - tareas ← TAREAS.tramite_id (tareas realizadas en este trámite)

    REGLAS DE NEGOCIO:
        - No puede finalizarse si hay tareas sin finalizar
        - Secuencias determinadas por motor de reglas
        - Trámites pueden ejecutarse en paralelo dentro de una fase
    """
    __tablename__ = 'tramites'
    __table_args__ = (
        db.Index('idx_tramites_fase', 'fase_id'),
        db.Index('idx_tramites_tipo', 'tipo_tramite_id'),
        {'schema': 'public'}
    )
    
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado del trámite'
    )
    
    fase_id = db.Column(
        db.Integer,
        db.ForeignKey('public.fases.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a FASES. Fase a la que pertenece el trámite'
    )
    
    tipo_tramite_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_tramites.id'),
        nullable=False,
        comment='FK a TIPOS_TRAMITES. Tipo de trámite'
    )
    
    observaciones = db.Column(
        db.String(2000),
        nullable=True,
        comment='Notas o comentarios adicionales del técnico'
    )
    
    # Relaciones
    fase = db.relationship('Fase', backref='tramites')
    tipo_tramite = db.relationship('TipoTramite', backref='tramites_instanciados')
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<Tramite id={self.id} tipo={self.tipo_tramite_id} fase={self.fase_id}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return f'Trámite {self.id} - {self.tipo_tramite.nombre if self.tipo_tramite else "Sin tipo"}'

    # --- Estados deducibles ---
    # La completitud se deduce de documentos en las tareas hijas, no de campos de fecha.

    @property
    def finalizado(self):
        """True si todas las tareas con tipos documentales tienen documento_producido_id
        y ninguna tarea NOTIFICAR tiene resultado INCORRECTA (#296).

        ESPERAR_PLAZO se excluye — su completitud la evalúa plazos.py via ContextAssembler.
        """
        _requieren = {'INCORPORAR', 'ANALISIS', 'REDACTAR', 'FIRMAR', 'NOTIFICAR', 'PUBLICAR'}
        for t in self.tareas:
            if not t.tipo_tarea:
                continue
            codigo = t.tipo_tarea.codigo
            if codigo in _requieren and t.documento_producido_id is None:
                return False
            if codigo == 'NOTIFICAR' and t.resultado == 'INCORRECTA':
                return False
        return True

    @property
    def planificado(self):
        """True si el trámite no tiene ninguna tarea aún."""
        return len(self.tareas) == 0

    @property
    def en_curso(self):
        """True si el trámite tiene tareas pero no está finalizado."""
        return not self.planificado and not self.finalizado

    @property
    def estado(self):
        """Estado del trámite: PLANIFICADO | EN_CURSO | FINALIZADO."""
        if self.planificado:
            return 'PLANIFICADO'
        if self.finalizado:
            return 'FINALIZADO'
        return 'EN_CURSO'
