from app import db

class Solicitud(db.Model):
    """
    Actos administrativos solicitados por el peticionario.
    
    PROPÓSITO:
        Representa actos administrativos individuales (AAP, AAC, DUP, etc.)
        solicitados por el promotor. Permite gestión individualizada de cada
        solicitud con su estado propio, independiente del expediente global.
    
    FILOSOFÍA:
        - Una solicitud tiene UN ÚNICO TIPO (atómico o combinado) vía tipo_solicitud_id
        - Los tipos combinados (AAP_AAC, AAP_AAC_DUP, etc.) se definen en TIPOS_SOLICITUDES
        - Motor de reglas compara por siglas exactas; el supervisor lista variantes en las reglas
        - Cada solicitud es una instancia independiente con estado y trazabilidad propios

    CAMPO TIPO_SOLICITUD_ID:
        - NOT NULL: Toda solicitud tiene exactamente un tipo (atómico o combinado)
        - FK a TIPOS_SOLICITUDES (public schema)
        - Reemplaza la tabla puente solicitudes_tipos (eliminada en #167 Fase 1)

    CAMPO EXPEDIENTE_ID:
        - NOT NULL: Toda solicitud pertenece a un expediente
        - FK a EXPEDIENTES (public schema)
    
    CAMPO ENTIDAD_ID:
        - NOT NULL: Identifica al solicitante (promotor/titular)
        - FK a ENTIDADES (public schema)
        - Puede diferir del titular del expediente (cambios de titularidad)
        - Permite rastrear quién solicitó cada acto administrativo
    
    CAMPO SOLICITUD_AFECTADA_ID:
        - NULLABLE: Solo para DESISTIMIENTO o RENUNCIA
        - Referencia a otra SOLICITUD previa que se desiste/renuncia
        - Permite rastrear dependencias entre solicitudes

    CAMPO DOCUMENTO_SOLICITUD_ID:
        - NOT NULL desde #428: FK al escrito de solicitud en el pool
        - La fecha administrativa de ese documento es la fecha de inicio del cómputo de plazos
        - Obligatorio porque sin él no hay fecha desde la que computar: el plazo del
          art. 128 RD 1955/2000 consta SIN_PLAZO y las suspensiones del art. 22 LPACAP
          se restan contra nada. No es un dato pendiente de rellenar, es un
          procedimiento cuyo plazo principal no ha empezado y nadie se entera
        - Lo escriben las dos únicas vías por las que nace una solicitud:
          `app/services/alta_expediente.py` (expediente nuevo, el escrito se sube con
          el alta) y `mutaciones_arbol.crear_solicitud` (solicitud adicional, el
          escrito se elige del pool)
        - Ver §2.bis DISEÑO_FECHAS_PLAZOS.md

    CAMPO DOCUMENTO_FIN_INSTRUCCION_ID (#827, ADR-043 §D):
        - NULLABLE: FK al certificado de fin de instrucción (CERT_FIN_INSTRUCCION)
        - Tercera columna de la serie de ADR-041 §D bis, entre las otras dos:
          entrada (art. 21.3.b) → fin de instrucción (art. 82.1) → cierre (art. 40.4)
        - Es la bisagra entre instrucción y resolución: la fase finalizadora no se
          abre porque el sistema recuente fases, sino porque consta emitido este
          certificado («Instruidos los procedimientos, e inmediatamente antes de
          redactar la propuesta de resolución…»). Lo comprueban dos reglas de
          `reglas_motor` con sujeto explícito, vía la variable
          `solicitud_tiene_cert_fin_instruccion`
        - Por qué FK y no búsqueda por tipo en el pool: `Documento` solo tiene FK a
          expediente, de modo que buscar CERT_FIN_INSTRUCCION en el pool confunde
          dos solicitudes del mismo expediente — el defecto real de
          `cert_fin_ip_consultas._buscar_existente`, que este ancla no hereda
        - Tampoco cuelga de una fase: ninguna representa el conjunto de la
          instrucción (`CertificadoFase.fase_id` queda NULL para este certificado)

    CAMPO DOCUMENTO_CIERRE_ID (#778, ADR-041 §D bis):
        - NULLABLE: FK al certificado de cierre de la solicitud (CERT_CIERRE_SOLICITUD)
        - Pareja de DOCUMENTO_SOLICITUD_ID: uno ancla la fecha de inicio del plazo
          para resolver y notificar, este la de fin
        - NO es Fase(RESOLUCION).documento_resultado_id: ese es la resolución, y su
          fecha es la de dictar, anterior a la de notificar. El art. 21.3.b obliga a
          «resolver Y notificar», y el 40.4 fija que basta la notificación —o el
          intento debidamente acreditado— respecto de todos los interesados. Con
          varios interesados hay varios intentos y ninguno significa por sí solo
          «la solicitud está cerrada»: lo que se ancla aquí es el certificado que
          constata el hecho agregado, con la fecha del último de esos actos
        - Mientras no exista el certificado, el plazo de la solicitud no alcanza
          CUMPLIDO (plazos.py) — es el mismo comportamiento que una fase en
          PDTE_CIERRE: todo hecho, falta formalizar

    CAMPO ESTADO (property derivada, no columna):
        - EN_TRAMITE: alguna fase no está finalizada
        - RESUELTA: todas las fases finalizadas Y motor confirma existencia de resolución exigida
        - El resultado final (RESUELTA_FAVORABLE, RESUELTA_ARCHIVADA, etc.) se deriva
          del resultado de las fases que el motor obliga a existir
        - Ver §311 P4 en DISEÑO_MOTOR_AGNOSTICO.md
    
    RELACIONES:
        - expediente → EXPEDIENTES.id (FK, expediente contenedor)
        - entidad → ENTIDADES.id (FK, solicitante)
        - tipo_solicitud → TIPOS_SOLICITUDES.id (FK, tipo atómico o combinado)
        - solicitud_afectada → SOLICITUDES.id (FK self-referencia, para DESISTIMIENTO/RENUNCIA)

    REGLAS DE NEGOCIO:
        - DESISTIMIENTO/RENUNCIA: Requiere SOLICITUD_AFECTADA_ID NOT NULL
        - MOD: Debe existir AAC previa en el expediente (validar en interfaz)
        - Estado RESUELTA: requiere confirmación del motor (ver CAMPO ESTADO)
    """
    __tablename__ = 'solicitudes'
    __table_args__ = (
        db.Index('idx_solicitudes_expediente', 'expediente_id'),
        db.Index('idx_solicitudes_entidad', 'entidad_id'),
        db.Index('idx_solicitudes_doc_solicitud', 'documento_solicitud_id'),
        db.Index('idx_solicitudes_doc_cierre', 'documento_cierre_id'),
        db.Index('idx_solicitudes_doc_fin_instruccion', 'documento_fin_instruccion_id'),
        {'schema': 'public'}
    )
    
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado de la solicitud'
    )
    
    expediente_id = db.Column(
        db.Integer,
        db.ForeignKey('public.expedientes.id', use_alter=True, name='fk_solicitudes_expediente'),
        nullable=False,
        comment='FK a EXPEDIENTES. Expediente al que pertenece la solicitud'
    )
    
    entidad_id = db.Column(
        db.Integer,
        db.ForeignKey('public.entidades.id', use_alter=True, name='fk_solicitudes_entidad'),
        nullable=False,
        comment='FK a ENTIDADES. Solicitante (promotor/titular) de la solicitud'
    )
    
    tipo_solicitud_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_solicitudes.id', name='fk_solicitudes_tipo_solicitud'),
        nullable=False,
        comment='FK a TIPOS_SOLICITUDES. Tipo atómico o combinado (#167 Fase 1)'
    )

    solicitud_afectada_id = db.Column(
        db.Integer,
        db.ForeignKey('public.solicitudes.id'),
        nullable=True,
        comment='FK a SOLICITUDES. Para DESISTIMIENTO/RENUNCIA, solicitud que se desiste'
    )

    documento_solicitud_id = db.Column(
        db.Integer,
        db.ForeignKey('public.documentos.id', name='fk_solicitudes_documento_solicitud'),
        nullable=False,
        comment='FK a DOCUMENTOS. Escrito que abre la solicitud; su fecha_administrativa '
                'es la de registro de entrada y arranca el plazo para resolver (#428)'
    )

    documento_fin_instruccion_id = db.Column(
        db.Integer,
        db.ForeignKey('public.documentos.id', name='fk_solicitudes_documento_fin_instruccion'),
        nullable=True,
        comment='FK a DOCUMENTOS. Certificado de fin de instrucción de la solicitud '
                '(CERT_FIN_INSTRUCCION): consta que la instrucción terminó y habilita '
                'la fase finalizadora (art. 82.1 LPACAP, #827)'
    )

    documento_cierre_id = db.Column(
        db.Integer,
        db.ForeignKey('public.documentos.id', name='fk_solicitudes_documento_cierre'),
        nullable=True,
        comment='FK a DOCUMENTOS. Certificado de cierre de la solicitud: ancla la fecha '
                'de fin del plazo para resolver y notificar (#778)'
    )

    observaciones = db.Column(
        db.String(2000),
        nullable=True,
        comment='Notas o comentarios adicionales del técnico'
    )

    # Relaciones
    expediente = db.relationship('Expediente', backref='solicitudes')
    entidad = db.relationship('Entidad', backref='solicitudes')
    tipo_solicitud = db.relationship('TipoSolicitud')
    solicitud_afectada = db.relationship('Solicitud', remote_side=[id], backref='solicitudes_dependientes')
    # Las tres anclas documentales de la solicitud (ADR-041 §D bis): entrada →
    # fin de instrucción → cierre. Cada una con su `backref` porque el pool
    # necesita saber, desde el documento, si alguna solicitud lo usa como ancla:
    # `_documento_es_referenciado` se construye solo con backrefs a propósito, para
    # que una FK nueva a `documentos` se vea desde el modelo y no haya que
    # acordarse de escribir SQL en la ruta (#838).
    documento_solicitud = db.relationship(
        'Documento', foreign_keys=[documento_solicitud_id],
        backref='anclado_en_solicitud')
    documento_cierre = db.relationship(
        'Documento', foreign_keys=[documento_cierre_id],
        backref='anclado_en_cierre')
    documento_fin_instruccion = db.relationship(
        'Documento', foreign_keys=[documento_fin_instruccion_id],
        backref='anclado_en_fin_instruccion')
    
    # Properties
    @property
    def tipos_simples(self) -> list:
        """Descompone siglas combinadas en lista de tipos simples.

        'AAP+AAC' → ['AAP', 'AAC']  |  'AAP' → ['AAP']
        """
        if not self.tipo_solicitud:
            return []
        return self.tipo_solicitud.siglas.split('+')

    def contiene_tipo(self, siglas: str) -> bool:
        """True si esta solicitud incluye el tipo simple dado."""
        return siglas in self.tipos_simples

    @property
    def estado(self):
        """Estado de la solicitud.

        EN_TRAMITE si alguna fase no está finalizada, o si no hay ninguna fase
        finalizadora cerrada entre las que hay (#848: "todas las fases cerradas"
        no es "resuelta" cuando ninguna de ellas es la que resuelve — es un
        momento normal, entre fases, de cualquier tramitación).

        RESUELTA_<código> cuando TODAS las fases finalizadoras que tenga la
        solicitud están cerradas y coinciden en resultado_fase.codigo. Universal,
        no "la última creada" (ADR-044 R5): con una sola finalizadora —el caso
        de hoy— es exactamente el comportamiento anterior. Con más de una
        —AAP+AAC+DUP puede resolver en dos actos independientes, ADR-045 §B—
        ninguna de las dos supersede a la otra, así que "coger la más reciente"
        daría por resuelto un acto que en realidad sigue abierto.

        RESUELTA_DISCREPANTE cuando todas están cerradas pero sus resultados NO
        coinciden. Sigue empezando por RESUELTA a propósito (no rompe el
        guardián de invariantes_esftt que impide reabrir fases de una solicitud
        ya resuelta y notificada), pero no inventa cuál de los dos resultados
        "vale": representar de verdad el doble acto de ADR-045 (dos resultados,
        dos anclas de cierre) es su propio issue futuro. Aquí solo se evita
        camuflar la discrepancia bajo un RESUELTA mudo.

        El llamador debe confirmar via motor de reglas (accion=FINALIZAR, rule id=5)
        que existe la resolución exigida por el tipo de solicitud (#311 P4).

        Sobre `self.fases`, no una consulta aparte: sigue siendo una computación
        pura sobre la relación cargada, testable con stubs sin BD (bloque C de
        `test_296_senal_resultado.py`). Para que no vea una colección vieja justo
        después de crear o cerrar una fase en la misma sesión, quien crea fases
        (`crear_fase`) tiene que asignarlas por la relación, no por el FK a pelo
        —ver comentario en `mutaciones_arbol.crear_fase`—.
        """
        if not self.fases or not all(f.finalizada for f in self.fases):
            return 'EN_TRAMITE'
        fases_fin = [f for f in self.fases if f.tipo_fase and f.tipo_fase.es_finalizadora]
        if not fases_fin:
            return 'EN_TRAMITE'
        codigos = {f.resultado_fase.codigo for f in fases_fin if f.resultado_fase}
        if len(codigos) == 1:
            return 'RESUELTA_' + codigos.pop()
        if len(codigos) > 1:
            return 'RESUELTA_DISCREPANTE'
        return 'RESUELTA'

    @property
    def activa(self):
        """True si la solicitud está en tramitación."""
        return self.estado == 'EN_TRAMITE'
    
    @property
    def es_desistimiento_o_renuncia(self):
        """True si tiene solicitud_afectada_id. Heurística — no verifica el tipo real.
        Pendiente: cruzar contra tipo_solicitud cuando el motor esté implementado."""
        return self.solicitud_afectada_id is not None
    
    def __repr__(self):
        return f'<Solicitud id={self.id} expediente={self.expediente_id} entidad={self.entidad_id}>'

    def __str__(self):
        return f'Solicitud {self.id}'
